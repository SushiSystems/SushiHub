# modules.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Manages the workspace and its modules: init, add, link, update and sync.

The dependency engine in ``sushihub.setup`` owns everything under ``dependencies/``. See
cli/README.md, "Notes on the source".
"""

from __future__ import annotations

from pathlib import Path

from .. import DISTRIBUTION, console
from ..config import WORKSPACE_MARKER, create_workspace_file, deps_dir, workspace_root
from ..setup.dependency_source import MODULE_MANIFEST_REL
from . import binary as binary_svc
from . import fetched_sources, links, module_manifest
from .catalog import CATALOG
from .ports import ConsolePort, Ports
from .presence import Presence, describe, module_dir, presence_of

# sushicore is not a stack module and stays out of CATALOG; see cli/README.md.
SUSHICORE_NAME = "sushicore"


# The lines `hub init` keeps present in the workspace .gitignore.
_GITIGNORE_LINES = [
    "# Managed by `hub init`: shared dependencies and cloned modules are not tracked.",
    "/dependencies/",
    *(f"/{CATALOG[n].directory}/" for n in CATALOG),
    "/.sushistack/",
]


def _install_module_cli(name: str, dest: Path, ports: Ports | None = None) -> bool:
    """Install a cloned module's own CLI (`sr`, `se`, …) so it is ready to use.

    Mirrors how the umbrella installs its own `hub` CLI: pipx-install the module's
    `cli/` package, editable against the checkout, so a later `git pull` keeps
    reaching it. Best-effort — a module without a `cli/` package, or a pipx we
    can't locate, is a warning, not a hard failure.
    """
    ports = ports or Ports.machine(console)
    out = ports.console
    cli_dir = dest / "cli"
    if not (cli_dir / "pyproject.toml").is_file():
        out.info(f"{name}: no cli/ package to install; skipping CLI install.")
        return True

    if not ports.pipx.available():
        out.warn(f"{name}: pipx not found; skipping CLI install. Install it "
                     f"later with `pipx install {cli_dir}`.")
        return False

    out.info(f"{name}: installing its CLI with pipx ({cli_dir}).")
    if ports.pipx.install(cli_dir, editable=True) != 0:
        out.error(f"{name}: CLI install failed.")
        return False
    return True


def _resolve_names(names: list[str] | None, out: ConsolePort | None = None) -> list[str] | None:
    """Expand a user module list ('all' or names) to concrete module names.

    Returns None on an unknown name (after reporting it), so callers can abort.
    """
    out = out if out is not None else console
    if not names or names == ["all"]:
        return CATALOG.names()
    resolved = [(n, CATALOG.resolve(n)) for n in names]
    unknown = [given for given, found in resolved if found is None]
    if unknown:
        out.error(f"Unknown module(s): {', '.join(unknown)}. "
                      f"Choose from: {', '.join(CATALOG.names())} (or their aliases: "
                      f"{', '.join(CATALOG.aliases())}; or 'all').")
        return None
    return [found for _, found in resolved]


def init(ports: Ports | None = None) -> int:
    """Turn the current directory into a SushiStack workspace. Return exit code.

    @param ports What the command prints through; this machine's when None.
    """
    out = (ports or Ports.machine(console)).console
    out.header("SushiHub Init")
    root = Path.cwd().resolve()

    if (root / WORKSPACE_MARKER).is_dir():
        out.info(f"Already a SushiStack workspace: {root}")
    else:
        out.success(f"Marked workspace root: {create_workspace_file(root)}")

    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    missing = [ln for ln in _GITIGNORE_LINES if ln not in existing]
    if missing:
        prefix = "" if existing.endswith("\n") or not existing else "\n"
        with gitignore.open("a", encoding="utf-8") as fh:
            fh.write(prefix + "\n".join(missing) + "\n")
        out.success("Updated .gitignore (dependencies/ and module checkouts).")

    deps_dir().mkdir(parents=True, exist_ok=True)
    out.info(f"Dependencies will install into: {deps_dir()}")
    out.info("Next: `hub install` to provision deps, then `hub add sushiruntime`.")
    return 0


def _provision(dry_run: bool) -> int:
    """Provision the dependencies the present modules declare. Return exit code."""
    from . import setup as setup_svc

    return setup_svc.run("provision", dry_run=dry_run)


def _clone(name: str, repo: str, dest: Path, root: Path, ports: Ports | None = None) -> bool:
    """Clone module *name* into *dest*, from the copy its `setup` fetched when there is one."""
    ports = ports or Ports.machine(console)
    out = ports.console
    copy = fetched_sources.newest_copy(name)
    if copy is not None:
        out.info(f"{name}: cloning from the copy setup fetched, {copy.path} -> {dest}")
        return fetched_sources.clone_from_copy(copy, repo, dest, root, ports=ports)
    out.info(f"{name}: cloning {repo} -> {dest}")
    return ports.git.run(["clone", repo, str(dest)], cwd=root) == 0


def add(names: list[str] | None, dry_run: bool = False, skip_install: bool = False,
        binary: bool = False, provision=None, ports: Ports | None = None) -> int:
    """Bring one or more modules into the workspace. Return exit code.

    A module is cloned. sushiengine alone has a second form: it is cloned when this
    machine's Git identity reaches its repository and *binary* was not asked
    for, and downloaded as a compiled release otherwise; a release brings its
    own dependencies, so it never runs the provision pipeline.

    @param binary Install sushiengine from its release even when the source is
        within reach.
    @param provision Runs the provision pipeline; injected by tests.
    @param ports What the command reaches the outside through; this machine's when None.
    """
    ports = ports or Ports.machine(console)
    out = ports.console
    out.header("SushiHub Add")
    resolved = _resolve_names(names, out)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        out.info("Dry-run: showing actions without cloning or installing.")

    provision = provision or _provision
    linked = links.registered()
    brought_in = False
    failed = False
    for name in resolved:
        if name in linked:
            out.info(f"{name}: linked to {linked[name]} (use `hub link` to change); skipping clone.")
            if not dry_run:
                _install_module_cli(name, module_dir(root, name, linked), ports)
            continue
        mod = CATALOG[name]
        dest = root / mod.directory
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            _, text = describe(root, name, linked)
            out.info(f"{name}: {text} at {dest}; nothing to clone.")
            continue
        if state is Presence.CLONED:
            out.info(f"{name}: already cloned at {dest}")
            if not dry_run:
                _install_module_cli(name, dest, ports)
            continue
        if mod.is_binary and (binary or not ports.git.source_reachable(mod.repo)):
            if dry_run:
                out.info(f"{name}: (dry-run) would install its release -> {dest}")
                continue
            if not binary_svc.add(name, dest, requested=binary, ports=ports):
                failed = True
            continue
        if binary:
            sold = [n for n in CATALOG if CATALOG[n].is_binary]
            out.error(f"{name}: only {', '.join(sold)} is sold as a binary; every "
                          "other module is cloned. Drop --binary.")
            failed = True
            continue
        if dry_run:
            out.info(f"{name}: (dry-run) would clone {mod.repo} -> {dest}")
            brought_in = True
            continue
        if not _clone(name, mod.repo, dest, root, ports):
            out.error(f"{name}: clone failed.")
            failed = True
            continue
        brought_in = True
        # Install the module's own CLI (sr/se/…) so it's usable right after add.
        _install_module_cli(name, dest, ports)
    if failed:
        return 1
    if brought_in and skip_install:
        out.info("Skipped the dependency install; run `hub install` to pick up "
                     "what the new modules need.")
    elif brought_in:
        rc = provision(dry_run)
        if rc != 0:
            return rc
    if not dry_run:
        aliases = ", ".join(f"`{alias}`" for alias in CATALOG.aliases())
        out.success(f"Modules ready. Build them with their own CLI ({aliases}).")
    return 0


def link(name: str, path: str, dry_run: bool = False, skip_install: bool = False,
         provision=None, ports: Ports | None = None) -> int:
    """Register an existing checkout as a module, in place (no clone). Return code.

    For developers whose working repos live outside the workspace tree: links the
    module to that path so `hub` aggregates its dependency fragment and tracks it.
    The module's own CLI still resolves the shared deps via SUSHISTACK_HOME. The
    linked module's dependencies are provisioned afterwards, unless the link was
    already there or *skip_install* is set.

    @param provision Runs the provision pipeline; injected by tests.
    @param ports What the command reaches the outside through; this machine's when None.
    """
    out = (ports or Ports.machine(console)).console
    out.header("SushiHub Link")
    provision = provision or _provision
    resolved = CATALOG.resolve(name)
    if name == SUSHICORE_NAME:
        out.error(f"{SUSHICORE_NAME} is not a stack module: it is a package every "
                      "Sushi CLI installs from PyPI. To work on it, install your "
                      "checkout over the release with `pip install -e <path>`.")
        return 1
    target = Path(path).expanduser().resolve()
    if not target.is_dir():
        out.error(f"Path does not exist: {target}")
        return 1
    try:
        described = module_manifest.read(target)
    except ValueError as refused:
        out.error(str(refused))
        return 1
    if resolved is None:
        if described is None:
            out.error(
                f"Unknown module '{name}'. Choose from: "
                f"{', '.join(CATALOG.names())} (or their aliases: "
                f"{', '.join(CATALOG.aliases())}). A checkout outside that list is linkable "
                f"when it carries a {module_manifest.MANIFEST_FILE} naming itself; see "
                f"docs/reference/MODULE_MANIFEST.md.")
            return 1
        if described.name != name and described.alias != name:
            out.error(f"{target} describes itself as '{described.name}', not '{name}'.")
            return 1
        resolved = described.name
        out.info(f"{described.name}: linking a checkout that describes itself; "
                     f"the catalog does not list it.")
    elif described is not None and described.name != resolved:
        out.error(f"{target} describes itself as '{described.name}', not '{resolved}'.")
        return 1
    name = resolved
    if not (target / ".git").is_dir():
        out.warn(f"{target} is not a git checkout; linking anyway.")
    already_linked = links.registered().get(name) == str(target)
    if dry_run:
        out.info(f"(dry-run) would link {name} -> {target}")
        if already_linked or skip_install:
            return 0
        return provision(True)
    links.write(name, target)
    out.success(f"Linked {name} -> {target}")
    fragment = target / MODULE_MANIFEST_REL
    if not fragment.is_file():
        out.info(f"Note: cli/{fragment.name} not found there; this module adds no deps.")
    if already_linked or skip_install:
        out.info("Run `hub install` to pick up its dependencies.")
        return 0
    return provision(False)


def update(names: list[str] | None, dry_run: bool = False, ports: Ports | None = None) -> int:
    """Bring every present module up to date. Return exit code.

    A checkout, cloned or linked, is fast-forwarded with git. A binary install
    asks Sushi Account for the latest release and downloads it when its version
    differs from the installed one, then writes the licence again.

    @param ports What the command reaches the outside through; this machine's when None.
    """
    ports = ports or Ports.machine(console)
    out = ports.console
    out.header("SushiHub Update")
    resolved = _resolve_names(names, out)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        out.info("Dry-run: showing actions without pulling.")

    # hub itself is brought up to date before any module; see cli/README.md.
    _self_update(root, dry_run, ports)

    linked = links.registered()
    failed = False
    any_present = False
    for name in resolved:
        dest = module_dir(root, name, linked)
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            any_present = True
            if dry_run:
                out.info(f"{name}: (dry-run) would ask Sushi Account for a newer release ({dest})")
                continue
            if not binary_svc.update(name, dest, ports=ports):
                failed = True
            continue
        if state is Presence.ABSENT:
            if names and names != ["all"]:
                out.warn(f"{name}: not present (run `hub add {name}` or `hub link {name} <path>`).")
            continue
        any_present = True
        if dry_run:
            out.info(f"{name}: (dry-run) would git pull ({dest})")
            continue
        out.info(f"{name}: git pull ({dest})")
        if ports.git.run(["pull", "--ff-only"], cwd=dest) != 0:
            out.error(f"{name}: update failed.")
            failed = True
    if not any_present:
        out.info("No modules present yet. Add one with `hub add sushiruntime`.")
    return 1 if failed else 0


def _checkout_of(package_dir: Path) -> Path | None:
    """The git checkout *package_dir* sits in, or None when it sits in none."""
    for candidate in (package_dir, *package_dir.parents):
        if (candidate / ".git").is_dir():
            return candidate
    return None


def _self_update(root: Path, dry_run: bool, ports: Ports | None = None) -> None:
    """Bring `hub` itself up to date, the way `hub` was installed.

    An install from the index is upgraded with pipx. An editable install tracks a
    checkout, so that checkout is pulled instead -- and it is the one pipx
    recorded, which since the workspace stopped being a clone is not necessarily
    *root*. Best-effort throughout: a failure here must not block the rest of sync.

    Args:
        root: The workspace root, used only as the fallback checkout for a `hub`
            pipx does not know about.
        dry_run: Say what would happen and change nothing.
        ports: What the update reaches the outside through.
    """
    ports = ports or Ports.machine(console)
    out = ports.console
    install = ports.pipx.installed(DISTRIBUTION)
    if install is None:
        _pull_checkout(root, dry_run, ports)
        return
    if install.editable:
        checkout = _checkout_of(install.source)
        if checkout is None:
            out.warn(f"{DISTRIBUTION}: installed from {install.source}, which is "
                         "not a git checkout; nothing to update.")
            return
        _pull_checkout(checkout, dry_run, ports)
        return
    if dry_run:
        out.info(f"{DISTRIBUTION}: (dry-run) would upgrade from PyPI")
        return
    out.info(f"{DISTRIBUTION}: upgrading from PyPI")
    if ports.pipx.upgrade(DISTRIBUTION) != 0:
        out.warn(f"{DISTRIBUTION}: self-update failed; continuing with the "
                     "installed version. Run `pipx upgrade sushihub` by hand if "
                     "`hub` behaves stale.")


def _pull_checkout(root: Path, dry_run: bool, ports: Ports | None = None) -> None:
    """Fast-forward the checkout `hub` runs from, when it is one.

    A `hub` installed from the index has no checkout; this is the other branch,
    and it says nothing at all when *root* is not a git tree, because that is the
    ordinary case for a workspace created by `hub init`.
    """
    ports = ports or Ports.machine(console)
    out = ports.console
    if not (root / ".git").is_dir():
        return
    if dry_run:
        out.info(f"{DISTRIBUTION}: (dry-run) would git pull ({root})")
        return
    out.info(f"{DISTRIBUTION}: git pull ({root})")
    if ports.git.run(["pull", "--ff-only"], cwd=root) != 0:
        out.warn(f"{DISTRIBUTION}: self-update failed; continuing with the "
                     "current checkout. Pull it by hand if `hub` behaves stale.")


def sync(dry_run: bool, ports: Ports | None = None) -> int:
    """Bring the workspace to a working state in one shot.

    Fast-forwards the workspace and every present module first (via `hub update`),
    then provisions any missing dependencies (everything, like `hub install`) so
    the provision pipeline runs with today's fixes rather than whatever was
    checked out last. Module cloning stays explicit (`hub add`) so `sync` never
    pulls in repos the user did not ask for.

    @param ports What the command reaches the outside through; this machine's when None.
    """
    from . import setup as setup_svc

    ports = ports or Ports.machine(console)
    ports.console.header("SushiHub Sync")
    if dry_run:
        _self_update(workspace_root(), dry_run, ports)
        return setup_svc.run("provision", dry_run=dry_run)
    rc = update(["all"], ports=ports)
    if rc != 0:
        return rc
    return setup_svc.run("provision", dry_run=dry_run)
