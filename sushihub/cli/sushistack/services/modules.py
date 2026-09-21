"""Module + workspace management for the SushiStack umbrella.

SushiStack is the workspace the user clones first; the stack's modules
(sushiruntime, sushiengine, …) are git checkouts that live *inside* it, cloned by
``hub add``. This service owns that lifecycle — initialising the workspace, cloning
and updating modules, and reporting status — while the dependency engine in
``sushistack.setup`` owns everything under ``dependencies/``.
"""

from __future__ import annotations

from pathlib import Path

from .. import console
from ..config import WORKSPACE_MARKER, create_workspace_file, deps_dir, workspace_root
from ..setup.dependency_source import MODULE_MANIFEST_REL
from . import binary as binary_svc
from . import git_ops, links, pipx
from .catalog import CATALOG
from .presence import Presence, describe, module_dir, presence_of

# sushicore is the shared CLI presentation layer, not a stack build module: it
# ships no dependency fragment, is never built, and stays out of CATALOG so it is
# excluded from `hub add all`, readiness, and dependency aggregation. It lives
# inside this repository (see `sushicore/`), so there is nothing to clone and no
# checkout for anyone to manage -- cloning SushiStack already produced it.
SUSHICORE_NAME = "sushicore"


# Lines `hub init` ensures are present in the workspace .gitignore: the shared
# dependency tree and every module checkout are build artifacts of the workspace,
# not part of it.
_GITIGNORE_LINES = [
    "# Managed by `hub init`: shared dependencies and cloned modules are not tracked.",
    "/dependencies/",
    *(f"/{CATALOG[n].directory}/" for n in CATALOG),
    "/.sushistack/",
]


def sushicore_dir(root: Path) -> Path | None:
    """Resolve the in-repo sushicore package, or None if it is missing.

    sushicore ships inside this repository, so this is a fixed path, not a
    search: ``<workspace>/sushicore``. :mod:`.status_report` uses it to report
    whether the checkout is present; it is no longer used to locate anything to
    inject, since ``sushicore`` is now an ordinary PyPI dependency.
    """
    pkg = root / SUSHICORE_NAME
    return pkg if (pkg / "pyproject.toml").is_file() else None


def _install_module_cli(name: str, dest: Path) -> bool:
    """Install a cloned module's own CLI (`sr`, `se`, …) so it is ready to use.

    Mirrors how the umbrella installs its own `hub` CLI: pipx-install the module's
    `cli/` package, editable against the checkout, so a later `git pull` keeps
    reaching it. Best-effort — a module without a `cli/` package, or a pipx we
    can't locate, is a warning, not a hard failure.
    """
    cli_dir = dest / "cli"
    if not (cli_dir / "pyproject.toml").is_file():
        console.info(f"{name}: no cli/ package to install; skipping CLI install.")
        return True

    if pipx.command() is None:
        console.warn(f"{name}: pipx not found; skipping CLI install. Install it "
                     f"later with `pipx install {cli_dir}`.")
        return False

    console.info(f"{name}: installing its CLI with pipx ({cli_dir}).")
    if pipx.install(cli_dir, editable=True) != 0:
        console.error(f"{name}: CLI install failed.")
        return False
    return True


def _resolve_names(names: list[str] | None) -> list[str] | None:
    """Expand a user module list ('all' or names) to concrete module names.

    Returns None on an unknown name (after reporting it), so callers can abort.
    """
    if not names or names == ["all"]:
        return CATALOG.names()
    resolved = [(n, CATALOG.resolve(n)) for n in names]
    unknown = [given for given, found in resolved if found is None]
    if unknown:
        console.error(f"Unknown module(s): {', '.join(unknown)}. "
                      f"Choose from: {', '.join(CATALOG.names())} (or their aliases: "
                      f"{', '.join(CATALOG.aliases())}; or 'all').")
        return None
    return [found for _, found in resolved]


def init() -> int:
    """Turn the current directory into a SushiStack workspace. Return exit code."""
    console.header("SushiStack Init")
    root = Path.cwd().resolve()

    if (root / WORKSPACE_MARKER).is_dir():
        console.info(f"Already a SushiStack workspace: {root}")
    else:
        console.success(f"Marked workspace root: {create_workspace_file(root)}")

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
    console.info("Next: `hub install` to provision deps, then `hub add sushiruntime`.")
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
    linked = links.registered()
    brought_in = False
    failed = False
    for name in resolved:
        if name in linked:
            console.info(f"{name}: linked to {linked[name]} (use `hub link` to change); skipping clone.")
            if not dry_run:
                _install_module_cli(name, module_dir(root, name, linked))
            continue
        mod = CATALOG[name]
        dest = root / mod.directory
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            _, text = describe(root, name, linked)
            console.info(f"{name}: {text} at {dest}; nothing to clone.")
            continue
        if state is Presence.CLONED:
            console.info(f"{name}: already cloned at {dest}")
            if not dry_run:
                _install_module_cli(name, dest)
            continue
        if mod.is_binary and (binary or not git_ops.source_reachable(mod.repo)):
            if dry_run:
                console.info(f"{name}: (dry-run) would install its release -> {dest}")
                continue
            if not binary_svc.add(name, dest, requested=binary):
                failed = True
            continue
        if binary:
            sold = [n for n in CATALOG if CATALOG[n].is_binary]
            console.error(f"{name}: only {', '.join(sold)} is sold as a binary; every "
                          "other module is cloned. Drop --binary.")
            failed = True
            continue
        if dry_run:
            console.info(f"{name}: (dry-run) would clone {mod.repo} -> {dest}")
            brought_in = True
            continue
        console.info(f"{name}: cloning {mod.repo} -> {dest}")
        if git_ops.run(["clone", mod.repo, str(dest)], cwd=root) != 0:
            console.error(f"{name}: clone failed.")
            failed = True
            continue
        brought_in = True
        # Install the module's own CLI (sr/se/…) so it's usable right after add.
        _install_module_cli(name, dest)
    if failed:
        return 1
    if brought_in and skip_install:
        console.info("Skipped the dependency install; run `hub install` to pick up "
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
    module to that path so `hub` aggregates its dependency fragment and tracks it.
    The module's own CLI still resolves the shared deps via SUSHISTACK_HOME. The
    linked module's dependencies are provisioned afterwards, unless the link was
    already there or *skip_install* is set.

    @param provision Runs the provision pipeline; injected by tests.
    """
    console.header("SushiStack Link")
    provision = provision or _provision
    resolved = CATALOG.resolve(name)
    if name == SUSHICORE_NAME:
        console.error(f"{SUSHICORE_NAME} is not a stack module: it is a package every "
                      "Sushi CLI installs from PyPI. To work on it, install your "
                      "checkout over the release with `pip install -e <path>`.")
        return 1
    if resolved is None:
        console.error(f"Unknown module '{name}'. Choose from: "
                      f"{', '.join(CATALOG.names())} (or their aliases: "
                      f"{', '.join(CATALOG.aliases())}).")
        return 1
    name = resolved
    target = Path(path).expanduser().resolve()
    if not target.is_dir():
        console.error(f"Path does not exist: {target}")
        return 1
    if not (target / ".git").is_dir():
        console.warn(f"{target} is not a git checkout; linking anyway.")
    already_linked = links.registered().get(name) == str(target)
    if dry_run:
        console.info(f"(dry-run) would link {name} -> {target}")
        if already_linked or skip_install:
            return 0
        return provision(True)
    links.write(name, target)
    console.success(f"Linked {name} -> {target}")
    fragment = target / MODULE_MANIFEST_REL
    if not fragment.is_file():
        console.info(f"Note: cli/{fragment.name} not found there; this module adds no deps.")
    if already_linked or skip_install:
        console.info("Run `hub install` to pick up its dependencies.")
        return 0
    return provision(False)


def update(names: list[str] | None, dry_run: bool = False) -> int:
    """Bring every present module up to date. Return exit code.

    A checkout, cloned or linked, is fast-forwarded with git. A binary install
    asks Sushi Account for the latest release and downloads it when its version
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
    # a git checkout too. Pull it here so a single `hub update` reaches every fix,
    # not just the ones in modules — otherwise an editable-installed `hub` goes
    # stale until someone remembers to pull the umbrella by hand.
    _self_update(root, dry_run=dry_run)

    linked = links.registered()
    failed = False
    any_present = False
    for name in resolved:
        dest = module_dir(root, name, linked)
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            any_present = True
            if dry_run:
                console.info(f"{name}: (dry-run) would ask Sushi Account for a newer release ({dest})")
                continue
            if not binary_svc.update(name, dest):
                failed = True
            continue
        if state is Presence.ABSENT:
            if names and names != ["all"]:
                console.warn(f"{name}: not present (run `hub add {name}` or `hub link {name} <path>`).")
            continue
        any_present = True
        if dry_run:
            console.info(f"{name}: (dry-run) would git pull ({dest})")
            continue
        console.info(f"{name}: git pull ({dest})")
        if git_ops.run(["pull", "--ff-only"], cwd=dest) != 0:
            console.error(f"{name}: update failed.")
            failed = True
    if not any_present:
        console.info("No modules present yet. Add one with `hub add sushiruntime`.")
    return 1 if failed else 0


def _self_update(root: Path, dry_run: bool) -> None:
    """Fast-forward the SushiStack workspace repo itself (the ``hub`` source tree).

    ``hub sync``/``hub update`` only pull the *modules* (sushiruntime, ...); the
    workspace root — where `cli/` and its setup pipeline actually live — is a git
    checkout too, and a stale one means every fix here (e.g. a CUDA pin change)
    silently never reaches an editable-installed `hub` until someone thinks to
    pull it by hand. Best-effort: a failure here must not block the rest of sync.
    """
    if not (root / ".git").is_dir():
        return
    if dry_run:
        console.info(f"sushistack: (dry-run) would git pull ({root})")
        return
    console.info(f"sushistack: git pull ({root})")
    if git_ops.run(["pull", "--ff-only"], cwd=root) != 0:
        console.warn("sushistack: self-update failed; continuing with the "
                      "current checkout. Pull it by hand if `hub` behaves stale.")


def sync(dry_run: bool) -> int:
    """Bring the workspace to a working state in one shot.

    Fast-forwards the workspace and every present module first (via `hub update`),
    then provisions any missing dependencies (everything, like `hub install`) so
    the provision pipeline runs with today's fixes rather than whatever was
    checked out last. Module cloning stays explicit (`hub add`) so `sync` never
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
