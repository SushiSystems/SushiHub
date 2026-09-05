"""Module + workspace management for the SushiStack umbrella.

SushiStack is the workspace the user clones first; the stack's modules
(sushiruntime, sushiengine, …) are git checkouts that live *inside* it, cloned by
``ss add``. This service owns that lifecycle — initialising the workspace, cloning
and updating modules, and reporting status — while the dependency engine in
``sushistack.setup`` owns everything under ``dependencies/``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .. import console
from ..config import (
    MODULES_FILE,
    WORKSPACE_MARKER,
    config_dir,
    deps_dir,
    registered_modules,
    workspace_root,
)
from ..setup.dependency_source import MODULE_MANIFEST_REL
from . import licence_file, releases, session
from .identity import ReleaseInfo, SushiId, SushiIdError
from .presence import Presence, describe, presence_of, read_release
from .releases import ReleaseCorrupt


@dataclass(frozen=True)
class Module:
    """One stack module: its short name, clone URL, and on-disk directory."""

    name: str          # short name used on the CLI: runtime | engine | ai | blas
    repo: str          # git clone URL
    directory: str     # directory name created under the workspace root


# The known stack modules. Names are the exact program names — there is no
# program called "runtime", it is "sushiruntime" — so no one confuses them. The
# directory matches the name because that is what every module's own
# cmake/Runtime.cmake (and sushiai's cmake/BLAS.cmake) resolves a sibling
# checkout by: a flat <workspace>/<module> layout is what makes their
# add_subdirectory fallback find the dependency.
MODULES: dict[str, Module] = {
    "sushiruntime": Module("sushiruntime", "https://github.com/sushisystems/sushiruntime.git", "sushiruntime"),
    "sushiengine":  Module("sushiengine",  "https://github.com/sushisystems/sushiengine.git",  "sushiengine"),
    "sushiai":      Module("sushiai",      "https://github.com/sushisystems/sushiai.git",      "sushiai"),
    "sushiblas":    Module("sushiblas",    "https://github.com/sushisystems/sushiblas.git",    "sushiblas"),
    "sushidsp":     Module("sushidsp",     "https://github.com/sushisystems/sushidsp.git",     "sushidsp"),
}

# sushicore is the shared CLI presentation layer, not a stack build module: it
# ships no dependency fragment, is never built, and stays out of MODULES so it is
# excluded from `ss add all`, readiness, and dependency aggregation. It lives
# inside this repository (see `sushicore/`), so there is nothing to clone and no
# checkout for anyone to manage -- cloning SushiStack already produced it.
SUSHICORE_NAME = "sushicore"

# The one module sold rather than published: it is cloned by whoever has access
# to its repository and downloaded as a compiled release by everyone else. The
# other four are open source and have a single path, the clone. See
# docs/agent/specs/2026-09-05-hub-design.md, §3.
BINARY_MODULE = "sushiengine"

# How long `git ls-remote` may take to answer before the source counts as out of
# reach, in seconds.
REACHABLE_TIMEOUT = 15


# Short aliases for the module names, matching each module's own CLI program
# name (sushiruntime -> `sr`, sushiengine -> `se`, ...), so `ss add sr` works
# the same as `ss add sushiruntime`.
_ALIASES: dict[str, str] = {
    "sr": "sushiruntime",
    "se": "sushiengine",
    "sa": "sushiai",
    "sb": "sushiblas",
    "sd": "sushidsp",
}

# Lines `ss init` ensures are present in the workspace .gitignore: the shared
# dependency tree and every module checkout are build artifacts of the workspace,
# not part of it.
_GITIGNORE_LINES = [
    "# Managed by `ss init`: shared dependencies and cloned modules are not tracked.",
    "/dependencies/",
    *(f"/{m.directory}/" for m in MODULES.values()),
    "/sushihub/cli/config.local.toml",
    "/sushihub/cli/modules.local.toml",
    "/sushihub/cli/projects.local.toml",
]


def module_dest(root: Path, name: str) -> Path:
    """Where module *name* lives: its linked external path, else inside the workspace.

    A module registered via ``ss link`` resolves to that checkout; otherwise it is
    the conventional ``<workspace>/<directory>`` that ``ss add`` clones into.
    """
    linked = registered_modules().get(name)
    if linked:
        return Path(linked)
    return root / MODULES[name].directory


def sushicore_dir(root: Path) -> Path | None:
    """Resolve the in-repo sushicore package to inject, or None if it is missing.

    sushicore ships inside this repository, so this is a fixed path, not a search:
    ``<workspace>/sushicore``. It stays a function (and stays nullable) because it
    is still injected as a separate distribution -- it is published to no index,
    so pipx cannot resolve it as an ordinary dependency -- and a corrupt or
    partial checkout should be reported rather than crash the caller.
    """
    pkg = root / SUSHICORE_NAME
    return pkg if (pkg / "pyproject.toml").is_file() else None


def _write_link(name: str, path: Path) -> None:
    """Record (or update) a module->path entry in modules.local.toml."""
    registry = dict(registered_modules())
    registry[name] = str(path)
    target = config_dir() / MODULES_FILE
    lines = [
        "# Managed by `ss link`: modules pointed at existing checkouts outside the",
        "# workspace tree. `ss` reads these to aggregate their dependency fragments",
        "# and track them alongside cloned modules.",
        "",
        "[modules]",
    ]
    for key in sorted(registry):
        lines.append(f'{key} = "{str(registry[key]).replace(chr(92), "/")}"')
    lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")


def _run_git(args: list[str], cwd: Path) -> int:
    """Run a git command, streaming its output. Return its exit code."""
    try:
        return subprocess.run(["git", *args], cwd=str(cwd)).returncode
    except FileNotFoundError:
        console.error("git not found on PATH. Install git and try again.")
        return 1


def _source_reachable(repo: str) -> bool:
    """Report whether this machine's Git identity can read *repo*.

    Asks the remote for its default branch and nothing else, so a private
    repository the credentials do not open answers a non-zero exit code rather
    than a clone that fails halfway.

    Args:
        repo: The clone URL to ask about.
    """
    try:
        return subprocess.run(
            ["git", "ls-remote", "--exit-code", "-h", repo, "HEAD"],
            capture_output=True, timeout=REACHABLE_TIMEOUT).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _install_binary(name: str, dest: Path, client: SushiId,
                    info: ReleaseInfo | None = None) -> bool:
    """Unpack a release of *name* at *dest* and write its licence beside it.

    Args:
        name: The module, which is also the product slug Sushi ID knows.
        dest: Where the module lives in the workspace.
        client: A Sushi ID client with a live session.
        info: The release to install; the latest one when None.

    Returns:
        Whether both landed. A refusal from Sushi ID, a download that does not
        match what was declared and a directory that will not be written are all
        reported here and answered with False.
    """
    try:
        release = releases.install_release(name, dest, client, console, info=info)
        expires_at = licence_file.write_licence(dest, client, name)
    except (SushiIdError, ReleaseCorrupt, OSError) as error:
        console.error(f"{name}: {error}")
        return False
    console.success(f"{name}: installed binary {release.version} ({release.platform}) "
                    f"at {dest}; licence valid to {expires_at}.")
    return True


def _add_binary(name: str, dest: Path, requested: bool) -> bool:
    """Install *name* from its release, having found no other way to bring it in.

    Args:
        name: The module to install.
        dest: Where the module lives in the workspace.
        requested: Whether the binary form was asked for with ``--binary``
            rather than chosen because the source is out of reach.

    Returns:
        Whether the module is installed afterwards.
    """
    client = session.client()
    if client.access_token() is None:
        if requested:
            console.error(f"{name}: a binary install needs a Sushi ID licence. "
                          "Run `ss login` first.")
        else:
            console.error(
                f"{name}: neither way in is open. The source needs a Git identity with "
                f"access to {MODULES[name].repo}; the binary needs a licence, which "
                "`ss login` signs you in for.")
        return False
    return _install_binary(name, dest, client)


def _update_binary(name: str, dest: Path) -> bool:
    """Reinstall *name* when Sushi ID holds a release newer than the one at *dest*.

    Args:
        name: The module to refresh.
        dest: The unpacked install.

    Returns:
        Whether the install is the latest release afterwards. One that already
        was counts as success and downloads nothing.
    """
    client = session.client()
    if client.access_token() is None:
        console.error(f"{name}: a binary install is refreshed through Sushi ID. "
                      "Run `ss login` first.")
        return False
    try:
        info = client.resolve_release(name, releases.host_platform())
    except SushiIdError as error:
        console.error(f"{name}: {error}")
        return False
    installed = read_release(dest)
    if installed is not None and installed.version == info.version:
        console.info(f"{name}: binary {installed.version} is the latest release.")
        return True
    was = installed.version if installed else "an unreadable install"
    console.info(f"{name}: {was} -> {info.version}; downloading.")
    return _install_binary(name, dest, client, info=info)


def _pipx_cmd() -> list[str] | None:
    """Return a command that runs pipx, or None if pipx can't be found.

    `ss` itself was installed by pipx, so pipx is normally on PATH; fall back to
    `python -m pipx` under whichever interpreter has it. We never sys.executable
    here — that is `ss`'s own isolated pipx venv, which has no pipx module.
    """
    exe = shutil.which("pipx")
    if exe:
        return [exe]
    for py in ("python3", "python"):
        found = shutil.which(py)
        if found and subprocess.run(
            [found, "-m", "pipx", "--version"], capture_output=True
        ).returncode == 0:
            return [found, "-m", "pipx"]
    return None


def _cli_package_name(cli_dir: Path, module: str) -> str:
    """Read the CLI's distribution name from pyproject, else fall back to <name>-cli."""
    try:
        if sys.version_info >= (3, 11):
            import tomllib as toml
        else:
            import tomli as toml  # type: ignore[no-redirect]
        with (cli_dir / "pyproject.toml").open("rb") as fh:
            name = toml.load(fh).get("project", {}).get("name")
        if name:
            return str(name)
    except Exception:
        pass
    return f"{module}-cli"


def _install_module_cli(name: str, dest: Path, root: Path) -> bool:
    """Install a cloned module's own CLI (`sr`, `se`, …) so it is ready to use.

    Mirrors how the umbrella installs its own `ss` CLI: pipx-install the module's
    `cli/` package, then inject the shared sushicore presentation layer (which is
    not a resolvable pip dependency). Best-effort — a module without a `cli/`
    package, or a pipx we can't locate, is a warning, not a hard failure.
    """
    cli_dir = dest / "cli"
    if not (cli_dir / "pyproject.toml").is_file():
        console.info(f"{name}: no cli/ package to install; skipping CLI install.")
        return True

    pipx = _pipx_cmd()
    if pipx is None:
        console.warn(f"{name}: pipx not found; skipping CLI install. Install it "
                     f"later with `pipx install {cli_dir}`.")
        return False

    console.info(f"{name}: installing its CLI with pipx ({cli_dir}).")
    if subprocess.run([*pipx, "install", "--force", str(cli_dir)]).returncode != 0:
        console.error(f"{name}: CLI install failed.")
        return False

    # sushicore isn't published to any index, so pipx can't resolve it as a normal
    # dependency; inject it (editable) into the venv pipx just created.
    cli_shared = sushicore_dir(root)
    if cli_shared is None:
        console.warn(f"{name}: sushicore is missing from "
                     f"{root / SUSHICORE_NAME}; the CLI may fail to start. It ships "
                     "with this repository -- `git checkout -- sushicore` to restore it.")
        return False
    pkg = _cli_package_name(cli_dir, name)
    if subprocess.run(
        [*pipx, "inject", pkg, "--editable", str(cli_shared)]
    ).returncode != 0:
        console.warn(f"{name}: failed to inject sushicore into {pkg}.")
        return False
    return True


def _resolve_names(names: list[str] | None) -> list[str] | None:
    """Expand a user module list ('all' or names) to concrete module names.

    Returns None on an unknown name (after reporting it), so callers can abort.
    """
    if not names or names == ["all"]:
        return list(MODULES)
    resolved = [_ALIASES.get(n, n) for n in names]
    unknown = [n for n in resolved if n not in MODULES]
    if unknown:
        console.error(f"Unknown module(s): {', '.join(unknown)}. "
                      f"Choose from: {', '.join(MODULES)} (or their aliases: "
                      f"{', '.join(_ALIASES)}; or 'all').")
        return None
    return resolved


def init() -> int:
    """Turn the current directory into a SushiStack workspace. Return exit code."""
    console.header("SushiStack Init")
    root = Path.cwd().resolve()

    marker = root / WORKSPACE_MARKER
    if marker.is_file():
        console.info(f"Already a SushiStack workspace: {root}")
    else:
        marker.write_text(
            "# SushiStack workspace marker. `ss` locates the workspace by walking\n"
            "# up to this file. Delete it to detach this directory.\n",
            encoding="utf-8",
        )
        console.success(f"Marked workspace root: {root}")

    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    missing = [ln for ln in _GITIGNORE_LINES if ln not in existing]
    if missing:
        prefix = "" if existing.endswith("\n") or not existing else "\n"
        with gitignore.open("a", encoding="utf-8") as fh:
            fh.write(prefix + "\n".join(missing) + "\n")
        console.success("Updated .gitignore (dependencies/ and module checkouts).")

    deps_dir().mkdir(parents=True, exist_ok=True)
    console.info(f"Dependencies will install into: {deps_dir()}")
    console.info("Next: `ss install` to provision deps, then `ss add sushiruntime`.")
    return 0


def _provision(dry_run: bool) -> int:
    """Provision the dependencies the present modules declare. Return exit code."""
    from . import setup as setup_svc

    return setup_svc.run("provision", dry_run=dry_run)


def add(names: list[str] | None, dry_run: bool = False, skip_install: bool = False,
        binary: bool = False, provision=None) -> int:
    """Bring one or more modules into the workspace. Return exit code.

    Four of the five modules are cloned. sushiengine is cloned when this
    machine's Git identity reaches its repository and *binary* was not asked
    for, and downloaded as a compiled release otherwise; a release brings its
    own dependencies, so it never runs the provision pipeline.

    @param binary Install sushiengine from its release even when the source is
        within reach.
    @param provision Runs the provision pipeline; injected by tests.
    """
    console.header("SushiStack Add")
    resolved = _resolve_names(names)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        console.info("Dry-run: showing actions without cloning or installing.")

    provision = provision or _provision
    linked = registered_modules()
    brought_in = False
    failed = False
    for name in resolved:
        if name in linked:
            console.info(f"{name}: linked to {linked[name]} (use `ss link` to change); skipping clone.")
            if not dry_run:
                _install_module_cli(name, module_dest(root, name), root)
            continue
        mod = MODULES[name]
        dest = root / mod.directory
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            _, text = describe(root, name, linked)
            console.info(f"{name}: {text} at {dest}; nothing to clone.")
            continue
        if state is Presence.CLONED:
            console.info(f"{name}: already cloned at {dest}")
            if not dry_run:
                _install_module_cli(name, dest, root)
            continue
        if name == BINARY_MODULE and (binary or not _source_reachable(mod.repo)):
            if dry_run:
                console.info(f"{name}: (dry-run) would install its release -> {dest}")
                continue
            if not _add_binary(name, dest, requested=binary):
                failed = True
            continue
        if binary:
            console.error(f"{name}: only {BINARY_MODULE} is sold as a binary; every "
                          "other module is cloned. Drop --binary.")
            failed = True
            continue
        if dry_run:
            console.info(f"{name}: (dry-run) would clone {mod.repo} -> {dest}")
            brought_in = True
            continue
        console.info(f"{name}: cloning {mod.repo} -> {dest}")
        if _run_git(["clone", mod.repo, str(dest)], cwd=root) != 0:
            console.error(f"{name}: clone failed.")
            failed = True
            continue
        brought_in = True
        # Install the module's own CLI (sr/se/…) so it's usable right after add.
        _install_module_cli(name, dest, root)
    if failed:
        return 1
    if brought_in and skip_install:
        console.info("Skipped the dependency install; run `ss install` to pick up "
                     "what the new modules need.")
    elif brought_in:
        rc = provision(dry_run)
        if rc != 0:
            return rc
    if not dry_run:
        console.success("Modules ready. Build them with their own CLI "
                        "(`sr`, `se`, `sa`, `sb`).")
    return 0


def link(name: str, path: str, dry_run: bool = False, skip_install: bool = False,
         provision=None) -> int:
    """Register an existing checkout as a module, in place (no clone). Return code.

    For developers whose working repos live outside the workspace tree: links the
    module to that path so `ss` aggregates its dependency fragment and tracks it.
    The module's own CLI still resolves the shared deps via SUSHISTACK_HOME. The
    linked module's dependencies are provisioned afterwards, unless the link was
    already there or *skip_install* is set.

    @param provision Runs the provision pipeline; injected by tests.
    """
    console.header("SushiStack Link")
    provision = provision or _provision
    name = _ALIASES.get(name, name)
    if name == SUSHICORE_NAME:
        console.error(f"{SUSHICORE_NAME} ships inside this repository and cannot be "
                      "linked. Edit it in place, at `sushicore/`.")
        return 1
    if name not in MODULES:
        console.error(f"Unknown module '{name}'. Choose from: "
                      f"{', '.join(MODULES)} (or their aliases: {', '.join(_ALIASES)}).")
        return 1
    target = Path(path).expanduser().resolve()
    if not target.is_dir():
        console.error(f"Path does not exist: {target}")
        return 1
    if not (target / ".git").is_dir():
        console.warn(f"{target} is not a git checkout; linking anyway.")
    already_linked = registered_modules().get(name) == str(target)
    if dry_run:
        console.info(f"(dry-run) would link {name} -> {target}")
        if already_linked or skip_install:
            return 0
        return provision(True)
    _write_link(name, target)
    console.success(f"Linked {name} -> {target}")
    fragment = target / MODULE_MANIFEST_REL
    if not fragment.is_file():
        console.info(f"Note: cli/{fragment.name} not found there; this module adds no deps.")
    if already_linked or skip_install:
        console.info("Run `ss install` to pick up its dependencies.")
        return 0
    return provision(False)


def update(names: list[str] | None, dry_run: bool = False) -> int:
    """Bring every present module up to date. Return exit code.

    A checkout, cloned or linked, is fast-forwarded with git. A binary install
    asks Sushi ID for the latest release and downloads it when its version
    differs from the installed one, then writes the licence again.
    """
    console.header("SushiStack Update")
    resolved = _resolve_names(names)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        console.info("Dry-run: showing actions without pulling.")

    # The workspace repo itself (this CLI's own source, cli/ + setup pipeline) is
    # a git checkout too. Pull it here so a single `ss update` reaches every fix,
    # not just the ones in modules — otherwise an editable-installed `ss` goes
    # stale until someone remembers to pull the umbrella by hand.
    _self_update(root, dry_run=dry_run)

    linked = registered_modules()
    failed = False
    any_present = False
    for name in resolved:
        dest = module_dest(root, name)
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            any_present = True
            if dry_run:
                console.info(f"{name}: (dry-run) would ask Sushi ID for a newer release ({dest})")
                continue
            if not _update_binary(name, dest):
                failed = True
            continue
        if state is Presence.ABSENT:
            if names and names != ["all"]:
                console.warn(f"{name}: not present (run `ss add {name}` or `ss link {name} <path>`).")
            continue
        any_present = True
        if dry_run:
            console.info(f"{name}: (dry-run) would git pull ({dest})")
            continue
        console.info(f"{name}: git pull ({dest})")
        if _run_git(["pull", "--ff-only"], cwd=dest) != 0:
            console.error(f"{name}: update failed.")
            failed = True
    if not any_present:
        console.info("No modules present yet. Add one with `ss add sushiruntime`.")
    return 1 if failed else 0


def _status_rows(root: Path, linked: dict[str, str]) -> list[dict]:
    """Build one row per module for both the table and the JSON payload.

    Args:
        root: Workspace root.
        linked: Module name to path, as ``ss link`` recorded it.

    Returns:
        A row per module carrying its name, where it lives, the state the table
        prints, its :class:`~sushistack.services.presence.Presence` value, and
        the version a binary install reports (None for every other form).
    """
    rows = []
    for name in MODULES:
        state = presence_of(root, name, linked)
        location, text = describe(root, name, linked)
        release = read_release(module_dest(root, name)) if state is Presence.BINARY else None
        rows.append({"name": name, "location": location, "state": text,
                     "presence": state.value,
                     "version": release.version if release else None})

    # The shared CLI presentation layer. Not a build module, but shown so a
    # damaged checkout is visible: it ships in this repository, so the only two
    # states are present and missing -- and it arrived with the clone of the
    # workspace, which is the presence it reports.
    cli_dir = sushicore_dir(root)
    rows.append({"name": SUSHICORE_NAME,
                 "location": SUSHICORE_NAME if cli_dir else "",
                 "state": "in-repo" if cli_dir else "missing",
                 "presence": (Presence.CLONED if cli_dir else Presence.ABSENT).value,
                 "version": None})
    return rows


def status_payload() -> dict:
    """Collect the workspace, its modules and the dependency tree as one structure.

    Returns:
        The ``result`` payload of ``ss status``: the workspace path, one entry per
        module with its location, state, presence and version, and where the
        dependencies live.
    """
    root = workspace_root()
    deps = deps_dir()
    return {
        "workspace": str(root),
        "modules": _status_rows(root, registered_modules()),
        "dependencies": {
            "path": str(deps),
            "present": deps.is_dir() and any(deps.iterdir()),
        },
    }


def status(payload: dict) -> int:
    """Print the status *payload* built by :func:`status_payload`. Return exit code."""
    console.header("SushiStack Status")
    console.info(f"Workspace: {payload['workspace']}")
    console.table(
        ["Module", "Location", "State"],
        [[module["name"], module["location"] or "—",
          "—" if module["state"] == "absent" else module["state"]]
         for module in payload["modules"]],
        title="SushiStack Status",
    )
    deps = payload["dependencies"]
    if deps["present"]:
        console.info(f"Dependencies: {deps['path']} (present). Verify with `ss doctor`.")
    else:
        console.info(f"Dependencies: {deps['path']} (empty). Provision with `ss install`.")
    return 0


def _self_update(root: Path, dry_run: bool) -> None:
    """Fast-forward the SushiStack workspace repo itself (the ``ss`` source tree).

    ``ss sync``/``ss update`` only pull the *modules* (sushiruntime, ...); the
    workspace root — where `cli/` and its setup pipeline actually live — is a git
    checkout too, and a stale one means every fix here (e.g. a CUDA pin change)
    silently never reaches an editable-installed `ss` until someone thinks to
    pull it by hand. Best-effort: a failure here must not block the rest of sync.
    """
    if not (root / ".git").is_dir():
        return
    if dry_run:
        console.info(f"sushistack: (dry-run) would git pull ({root})")
        return
    console.info(f"sushistack: git pull ({root})")
    if _run_git(["pull", "--ff-only"], cwd=root) != 0:
        console.warn("sushistack: self-update failed; continuing with the "
                      "current checkout. Pull it by hand if `ss` behaves stale.")


def sync(dry_run: bool) -> int:
    """Bring the workspace to a working state in one shot.

    Fast-forwards the workspace and every present module first (via `ss update`),
    then provisions any missing dependencies (everything, like `ss install`) so
    the provision pipeline runs with today's fixes rather than whatever was
    checked out last. Module cloning stays explicit (`ss add`) so `sync` never
    pulls in repos the user did not ask for.
    """
    from . import setup as setup_svc

    console.header("SushiStack Sync")
    if dry_run:
        _self_update(workspace_root(), dry_run)
        return setup_svc.run("provision", dry_run=dry_run)
    rc = update(["all"])
    if rc != 0:
        return rc
    return setup_svc.run("provision", dry_run=dry_run)
