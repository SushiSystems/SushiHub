"""SushiHub developer CLI (`hub`).

The umbrella that provisions one shared dependency tree for the whole stack and
manages the module checkouts named in `catalog.toml` that live inside the workspace. Each
module keeps its own CLI — `sr`, `se`, `sa`, `sb` — for building and testing; `hub` only owns
downloading, installing, and module lifecycle.

Thin Typer layer: commands parse arguments and delegate to the service layer in
``sushihub.services``. Every command ends through :func:`_finish`, which emits
the one ``result`` event the JSON contract in ``contract/README.md``
requires and then exits.
"""

from __future__ import annotations

import json
import sys
from typing import List, Optional

import typer
from sushicore.typer_help import help_group

from . import console
from .config import upgrade_workspace, workspace_root
from .describe import catalogue
from .services.catalog import CATALOG
from .services import gui as gui_svc
from .services import modules as modules_svc
from .services import setup as setup_svc
from .services import status_report

K_WORKSPACE = "Workspace"
K_MODULES = "Modules"
K_DEPENDENCIES = "Dependencies"
K_DESKTOP_APP = "Desktop app"
K_ACCOUNT = "Account"

_help_group = help_group(console.current)

app = typer.Typer(
    name="hub",
    cls=_help_group,
    help="SushiHub CLI — one shared dependency tree and module manager for the stack.",
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False, "--json", is_eager=True,
        help="One JSON event per line on stdout; nothing else there."),
    describe: bool = typer.Option(
        False, "--describe", is_eager=True,
        help="Print the command catalogue as JSON and exit."),
):
    """Select the output mode before any command body runs."""
    console.set_machine(json_output)
    if describe:
        # The catalogue is UTF-8 whatever the console's code page, like every JSON event.
        text = json.dumps(catalogue(app), ensure_ascii=False)
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)
    _upgrade_if_old()


def _upgrade_if_old() -> None:
    """Convert a pre-2026-09-22 workspace before the subcommand body runs.

    Outside a workspace there is nothing to convert, and `hub init` must still
    run there, so an unresolved root is not an error.
    """
    try:
        root = workspace_root()
    except SystemExit:
        return
    upgrade_workspace(root)


def _finish(rc: int, payload: dict | None = None) -> None:
    """Emit the result event and exit with *rc*.

    Args:
        rc: The exit code; zero is the ``ok`` the result event reports.
        payload: What the command computed, an empty object when it computed nothing.

    Raises:
        typer.Exit: Always; this is how a command body returns.
    """
    console.result(rc == 0, payload or {})
    raise typer.Exit(rc)


# --------------------------------------------------------------------------- #
# workspace
# --------------------------------------------------------------------------- #
@app.command(
    "init",
    rich_help_panel=K_WORKSPACE,
    epilog="hub init  # Mark this directory as a workspace",
)
def init():
    """Turn the current directory into a SushiStack workspace.

    Writes the [cmd].sushistack[/cmd] marker, ensures [cmd].gitignore[/cmd]
    excludes the shared [cmd]dependencies/[/cmd] tree and module checkouts, and
    creates the dependency directory. Run this once after cloning sushihub.
    """
    _finish(modules_svc.init())


@app.command(
    "home",
    rich_help_panel=K_WORKSPACE,
    epilog="hub home",
)
def home():
    """Print the resolved workspace root and dependency directory."""
    from .config import deps_dir, workspace_root
    root, deps = workspace_root(), deps_dir()
    console.info(str(root))
    console.info(f"dependencies: {deps}")
    _finish(0, {"workspace": str(root), "dependencies": str(deps)})


@app.command(
    "status",
    rich_help_panel=K_WORKSPACE,
    epilog="hub status\n"
           "hub status --check-updates  # Fetch each checkout first",
)
def status(
    json_output: bool = typer.Option(
        False, "--json", help="Print machine-readable JSON instead of a table."),
    check_updates: bool = typer.Option(
        False, "--check-updates",
        help="Fetch every checkout and ask Sushi Account for newer releases first."),
):
    """Show which modules are cloned and whether dependencies are present."""
    if json_output:
        console.set_machine(True)
    report = status_report.build_status(check_updates)
    for warning in report.warnings:
        console.warn(warning)
    _finish(status_report.render(report.payload), report.payload)


# --------------------------------------------------------------------------- #
# modules

# The module names and aliases every command's help repeats, built from the catalog so a
# change to catalog.toml reaches `hub --help` and `hub --describe` without an edit here.
_MODULE_NAMES = " | ".join(CATALOG.names())
_MODULE_ALIASES = "`, `".join(CATALOG.aliases())
# --------------------------------------------------------------------------- #
@app.command(
    "add",
    rich_help_panel=K_MODULES,
    epilog="hub add sr  # Bring sushiruntime in\n"
           "hub add all --dry-run  # Show the plan only\n"
           "hub add se --binary  # Install sushiengine from its release",
)
def add(
    modules: List[str] = typer.Argument(
        ..., help=f"Modules to bring in: {_MODULE_NAMES} | all."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't clone or install."),
    skip_install: bool = typer.Option(
        False, "--skip-install", help="Do not run the dependency install afterwards."),
    binary: bool = typer.Option(
        False, "--binary",
        help="Install sushiengine from its release even when its source is in reach."),
):
    """Bring one or more stack modules into the workspace, with what they need.

    Five of the six are cloned. sushiengine is cloned when this machine's Git
    identity reaches its repository, and downloaded as a compiled release, with
    its licence file, when it does not or when [bold]--binary[/bold] is given.
    Each module that arrives by clone brings its own dependencies; they are
    provisioned once at the end unless [bold]--skip-install[/bold] is given.
    """
    _finish(modules_svc.add(modules, dry_run=dry_run, skip_install=skip_install,
                            binary=binary))


@app.command(
    "link",
    rich_help_panel=K_MODULES,
    epilog="hub link se ../sushiengine  # Register an existing checkout",
)
def link(
    module: str = typer.Argument(
        ..., help=f"Module name: {_MODULE_NAMES}."),
    path: str = typer.Argument(..., help="Path to an existing checkout of that module."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't write the link."),
    skip_install: bool = typer.Option(
        False, "--skip-install", help="Do not run the dependency install afterwards."),
):
    """Register an existing checkout (outside the workspace) as a module.

    For developers whose working repos live elsewhere: `hub` then aggregates that
    checkout's dependencies and tracks it, with no second clone. The module's own
    CLI resolves the shared deps via SUSHISTACK_HOME. What the linked module
    declares is provisioned afterwards unless [bold]--skip-install[/bold] is given.
    """
    _finish(modules_svc.link(module, path, dry_run=dry_run, skip_install=skip_install))


@app.command(
    "install-cli",
    rich_help_panel=K_MODULES,
    epilog="hub install-cli sr",
)
def install_cli(
    modules: List[str] = typer.Argument(
        ..., help=f"Modules whose CLI to install: {_MODULE_NAMES} | all."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't install."),
):
    """Install a module's developer CLI into an isolated pipx venv.

    The single install seam for the stack: no module ships its own bootstrap
    script. This installs the module's [cmd]cli/[/cmd] package and injects the
    shared [cmd]sushicore[/cmd] presentation layer that ships in this repository.

    Always installed editable, against the checkout it was invoked from -- a
    non-editable install would freeze the CLI at whatever revision existed at
    install time, so `git pull`s on the checkout would silently stop reaching it.
    """
    from .services import cli_install as cli_install_svc
    _finish(cli_install_svc.install_cli(modules, dry_run=dry_run))


@app.command(
    "update",
    rich_help_panel=K_MODULES,
    epilog="hub update\n"
           "hub update sr --dry-run",
)
def update(
    modules: Optional[List[str]] = typer.Argument(
        None, help="Modules to update (omit for all present modules)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't pull."),
):
    """Bring the workspace and every present module up to date.

    A checkout, cloned or linked, is fast-forwarded with [cmd]git pull[/cmd]. A
    binary install asks Sushi Account for the latest release and downloads it when the
    version differs from the installed one.
    """
    _finish(modules_svc.update(modules, dry_run=dry_run))


# --------------------------------------------------------------------------- #
# dependencies
# --------------------------------------------------------------------------- #
@app.command(
    "install",
    rich_help_panel=K_DEPENDENCIES,
    epilog="hub install\n"
           "hub install --customize  # Pick toolchains interactively\n"
           "hub install --dry-run",
)
def install(
    customize: bool = typer.Option(
        False, "--customize",
        help="Pick which components to install in an interactive TUI instead of "
             "what the present modules declare."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't change."),
    yes: bool = typer.Option(
        False, "--yes", "-y",
        help="Assume yes on the LLVM-download prompt, for unattended runs."),
    refresh_toolchains: bool = typer.Option(
        False, "--refresh-toolchains",
        help="Re-download the SYCL toolchain even if one is already installed."),
):
    """Provision the shared dependencies into the workspace's dependencies/ tree.

    Installs what the present modules declare. Use [bold]--customize[/bold] to add
    or drop a toolchain.
    """
    selection = None
    if customize:
        from .services import customize as customize_svc
        from .setup.dependency_source import TomlDependencySource
        from .setup.selection import selection_from_source
        defaults = selection_from_source(TomlDependencySource()).as_dict()
        selection = customize_svc.choose_components(defaults)
        if selection is None:
            _finish(1)
    _finish(setup_svc.run("provision", dry_run=dry_run, selection=selection,
                          assume_yes=yes, refresh_toolchains=refresh_toolchains))


@app.command(
    "sync",
    rich_help_panel=K_MODULES,
    epilog="hub sync",
)
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't change."),
):
    """Bring the workspace up to date: install missing deps, then update modules."""
    _finish(modules_svc.sync(dry_run=dry_run))


@app.command(
    "doctor",
    rich_help_panel=K_DEPENDENCIES,
    epilog="hub doctor",
)
def doctor():
    """Inventory tools, compilers, and dependencies; report what is missing."""
    _finish(setup_svc.run("detect", dry_run=False))


@app.command(
    "remove",
    rich_help_panel=K_DEPENDENCIES,
    epilog="hub remove --all --dry-run  # Show what --all would remove",
)
def remove(
    all: bool = typer.Option(
        False, "--all",
        help="[bold][error]Wipe everything[/error][/bold]: vcpkg ports, downloaded "
             "toolchains (intel/llvm + AdaptiveCpp + oneAPI, several GB), and the "
             "portable cmake/ninja — the whole dependencies/ tree."),
    gpu: bool = typer.Option(False, "--gpu", help="Include GPU-only deps in removal."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed."),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt for --all."),
):
    """Remove provisioned dependencies. Use [bold]--all[/bold] to reclaim the lot."""
    _finish(setup_svc.uninstall(gpu=gpu, dry_run=dry_run, everything=all, assume_yes=yes))


# --------------------------------------------------------------------------- #
# the desktop application
# --------------------------------------------------------------------------- #
gui_app = typer.Typer(
    name="gui",
    cls=_help_group,
    help="Build, test and run the desktop application under gui.",
    rich_markup_mode="rich",
)
app.add_typer(gui_app, name="gui", rich_help_panel=K_DESKTOP_APP)


@gui_app.command(
    "build",
    epilog="hub gui build --type release\n"
           "hub gui build --clean",
)
def gui_build(
    build_type: gui_svc.BuildType = typer.Option(
        gui_svc.BuildType.debug, "--type", help="The configuration to build."),
    clean: bool = typer.Option(
        False, "--clean", help="Remove the build tree before configuring."),
    define: Optional[List[str]] = typer.Option(
        None, "-D", metavar="VAR=VALUE", help="Extra cmake cache entry; repeatable."),
):
    """Configure and compile the desktop application.

    Builds into [cmd]gui/build/hub[/cmd] under the Visual Studio
    environment on Windows, against the vcpkg tree `hub install` provisions.
    """
    _finish(gui_svc.build(build_type, clean=clean, defines=define))


@gui_app.command(
    "test",
    epilog="hub gui test --filter <pattern>\n"
           "hub gui test --repeat 5",
)
def gui_test(
    filter: Optional[str] = typer.Option(
        None, "--filter", help="Run only the tests whose name matches this pattern."),
    repeat: int = typer.Option(
        0, "--repeat", help="Re-run each test until it fails or this many runs pass."),
):
    """Run the desktop application's tests through CTest."""
    _finish(gui_svc.test(filter=filter, repeat=repeat))


@gui_app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    epilog="hub gui run",
)
def gui_run(
    ctx: typer.Context,
    target: Optional[str] = typer.Argument(
        None, help="Executable to launch; the application itself when omitted."),
):
    """Launch a program the desktop application's build tree holds.

    Arguments after [cmd]--[/cmd] go to that program.
    """
    _finish(gui_svc.run(target, ctx.args))


@gui_app.command(
    "clean",
    epilog="hub gui clean",
)
def gui_clean():
    """Remove the desktop application's build tree."""
    _finish(gui_svc.clean())


@app.command(
    "login",
    rich_help_panel=K_ACCOUNT,
    epilog="hub login",
)
def login():
    """Sign in to Sushi Account and keep the session in the credential store.

    Prints a code, opens Sushi Account's device page in the browser, and waits there
    until you approve it.
    """
    from .services import session as session_svc
    _finish(*session_svc.login())


@app.command(
    "logout",
    rich_help_panel=K_ACCOUNT,
    epilog="hub logout",
)
def logout():
    """Forget the stored Sushi Account session on this machine."""
    from .services import session as session_svc
    _finish(*session_svc.logout())


@app.command(
    "whoami",
    rich_help_panel=K_ACCOUNT,
    epilog="hub whoami",
)
def whoami():
    """Print the Sushi Account this machine is signed in as."""
    from .services import session as session_svc
    _finish(*session_svc.whoami())


@app.command(
    "license",
    rich_help_panel=K_ACCOUNT,
    epilog="hub license",
)
def license():
    """Print the licences the signed-in Sushi Account holds."""
    from .services import session as session_svc
    _finish(*session_svc.license())


if __name__ == "__main__":
    app()
