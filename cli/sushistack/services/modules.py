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
    "/cli/config.local.toml",
    "/cli/modules.local.toml",
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


def add(names: list[str] | None, dry_run: bool = False) -> int:
    """Clone one or more modules into the workspace. Return exit code."""
    console.header("SushiStack Add")
    resolved = _resolve_names(names)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        console.info("Dry-run: showing actions without cloning or installing.")

    linked = registered_modules()
    failed = False
    for name in resolved:
        if name in linked:
            console.info(f"{name}: linked to {linked[name]} (use `ss link` to change); skipping clone.")
            if not dry_run:
                _install_module_cli(name, module_dest(root, name), root)
            continue
        mod = MODULES[name]
        dest = root / mod.directory
        if (dest / ".git").is_dir():
            console.info(f"{name}: already cloned at {dest}")
            if not dry_run:
                _install_module_cli(name, dest, root)
            continue
        if dry_run:
            console.info(f"{name}: (dry-run) would clone {mod.repo} -> {dest}")
            continue
        console.info(f"{name}: cloning {mod.repo} -> {dest}")
        if _run_git(["clone", mod.repo, str(dest)], cwd=root) != 0:
            console.error(f"{name}: clone failed.")
            failed = True
            continue
        # Install the module's own CLI (sr/se/…) so it's usable right after add.
        _install_module_cli(name, dest, root)
    if failed:
        return 1
    if not dry_run:
        console.success("Modules ready. Build them with their own CLI "
                        "(`sr`, `se`, `sa`, `sb`).")
    return 0


def link(name: str, path: str, dry_run: bool = False) -> int:
    """Register an existing checkout as a module, in place (no clone). Return code.

    For developers whose working repos live outside the workspace tree: links the
    module to that path so `ss` aggregates its dependency fragment and tracks it.
    The module's own CLI still resolves the shared deps via SUSHISTACK_HOME.
    """
    console.header("SushiStack Link")
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
    if dry_run:
        console.info(f"(dry-run) would link {name} -> {target}")
        return 0
    _write_link(name, target)
    console.success(f"Linked {name} -> {target}")
    fragment = target / MODULE_MANIFEST_REL
    if not fragment.is_file():
        console.info(f"Note: cli/{fragment.name} not found there; this module adds no deps.")
    console.info("Run `ss install` to pick up its dependencies.")
    return 0


def update(names: list[str] | None, dry_run: bool = False) -> int:
    """git pull the modules that are present (cloned or linked). Return exit code."""
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

    failed = False
    any_present = False
    for name in resolved:
        dest = module_dest(root, name)
        if not (dest / ".git").is_dir():
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


def _status_rows(root: Path, linked: dict[str, str]) -> list[tuple[str, str, str]]:
    """Build (module, location, state) rows for both the table and JSON views."""
    rows = []
    for name, mod in MODULES.items():
        dest = module_dest(root, name)
        if name in linked:
            state = "linked" if (dest / ".git").is_dir() else "linked (missing)"
            location = str(dest)
        else:
            state = "cloned" if (dest / ".git").is_dir() else "absent"
            location = mod.directory
        rows.append((name, location, state))

    # The shared CLI presentation layer. Not a build module, but shown so a
    # damaged checkout is visible: it ships in this repository, so the only two
    # states are present and missing.
    cli_dir = sushicore_dir(root)
    rows.append((SUSHICORE_NAME, SUSHICORE_NAME if cli_dir else "",
                 "in-repo" if cli_dir else "missing"))
    return rows


def status(json_output: bool = False) -> int:
    """Report which modules are present and where dependencies live."""
    root = workspace_root()
    linked = registered_modules()
    rows = _status_rows(root, linked)
    deps = deps_dir()
    deps_present = deps.is_dir() and any(deps.iterdir())

    if json_output:
        import json

        payload = {
            "workspace": str(root),
            "modules": [
                {"name": name, "location": location, "state": state}
                for name, location, state in rows
            ],
            "dependencies": {"path": str(deps), "present": deps_present},
        }
        console.console.print(json.dumps(payload, indent=2))
        return 0

    from rich.table import Table

    console.header("SushiStack Status")
    console.info(f"Workspace: {root}")

    table = Table(show_header=True, header_style=console.accent)
    table.add_column("Module")
    table.add_column("Location")
    table.add_column("State")
    for name, location, state in rows:
        table.add_row(name, location or "—", state if state != "absent" else "—")
    console.console.print(table)

    if deps_present:
        console.info(f"Dependencies: {deps} (present). Verify with `ss doctor`.")
    else:
        console.info(f"Dependencies: {deps} (empty). Provision with `ss install`.")
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
