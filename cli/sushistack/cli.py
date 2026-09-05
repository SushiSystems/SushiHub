"""SushiStack developer CLI (`ss`).

The umbrella that provisions one shared dependency tree for the whole stack and
manages the module checkouts (sushiruntime, sushiengine, sushiai, sushiblas, sushidsp)
that live inside the workspace. Each module keeps its own CLI — `sr`, `se`,
`sa`, `sb`, `sd` — for building and testing; `ss` only owns downloading, installing,
and module lifecycle.

Thin Typer layer: commands parse arguments and delegate to the service layer in
``sushistack.services``. Every command ends through :func:`_finish`, which emits
the one ``result`` event the JSON contract in ``sushihub/contract/README.md``
requires and then exits.
"""

from __future__ import annotations

import json
from typing import List, Optional

import typer

from . import console
from .describe import catalogue
from .services import modules as modules_svc
from .services import setup as setup_svc

app = typer.Typer(
    name="ss",
    help="SushiStack CLI — one shared dependency tree and module manager for the stack.",
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
        typer.echo(json.dumps(catalogue(app), ensure_ascii=False))
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


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
@app.command("init")
def init():
    """Turn the current directory into a SushiStack workspace.

    Writes the [cyan].sushistack[/cyan] marker, ensures [cyan].gitignore[/cyan]
    excludes the shared [cyan]dependencies/[/cyan] tree and module checkouts, and
    creates the dependency directory. Run this once after cloning sushistack.
    """
    _finish(modules_svc.init())


@app.command("home")
def home():
    """Print the resolved workspace root and dependency directory."""
    from .config import deps_dir, workspace_root
    root, deps = workspace_root(), deps_dir()
    console.info(str(root))
    console.info(f"dependencies: {deps}")
    _finish(0, {"workspace": str(root), "dependencies": str(deps)})


@app.command("status")
def status(
    json_output: bool = typer.Option(
        False, "--json", help="Print machine-readable JSON instead of a table."),
):
    """Show which modules are cloned and whether dependencies are present."""
    if json_output:
        console.set_machine(True)
    _finish(modules_svc.status(json_output=json_output))


# --------------------------------------------------------------------------- #
# modules
# --------------------------------------------------------------------------- #
@app.command("add")
def add(
    modules: List[str] = typer.Argument(
        ..., help="Modules to clone: sushiruntime | sushiengine | sushiai | sushiblas | sushidsp | all."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't clone or install."),
    skip_install: bool = typer.Option(
        False, "--skip-install", help="Do not run the dependency install afterwards."),
):
    """Clone one or more stack modules into the workspace, with what they need.

    Each module that arrives brings its own dependencies; they are provisioned
    once at the end unless [bold]--skip-install[/bold] is given.
    """
    _finish(modules_svc.add(modules, dry_run=dry_run, skip_install=skip_install))


@app.command("link")
def link(
    module: str = typer.Argument(
        ..., help="Module name: sushiruntime | sushiengine | sushiai | sushiblas | sushidsp."),
    path: str = typer.Argument(..., help="Path to an existing checkout of that module."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't write the link."),
    skip_install: bool = typer.Option(
        False, "--skip-install", help="Do not run the dependency install afterwards."),
):
    """Register an existing checkout (outside the workspace) as a module.

    For developers whose working repos live elsewhere: `ss` then aggregates that
    checkout's dependencies and tracks it, with no second clone. The module's own
    CLI resolves the shared deps via SUSHISTACK_HOME. What the linked module
    declares is provisioned afterwards unless [bold]--skip-install[/bold] is given.
    """
    _finish(modules_svc.link(module, path, dry_run=dry_run, skip_install=skip_install))


@app.command("install-cli")
def install_cli(
    modules: List[str] = typer.Argument(
        ..., help="Modules whose CLI to install: sushiruntime | sushiengine | "
                  "sushiai | sushiblas | sushidsp | all."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't install."),
):
    """Install a module's developer CLI (`sr`, `se`, `sa`, `sb`, `sd`) into an isolated pipx venv.

    The single install seam for the stack: no module ships its own bootstrap
    script. This installs the module's [cyan]cli/[/cyan] package and injects the
    shared [cyan]sushicore[/cyan] presentation layer that ships in this repository.

    Always installed editable, against the checkout it was invoked from -- a
    non-editable install would freeze the CLI at whatever revision existed at
    install time, so `git pull`s on the checkout would silently stop reaching it.
    """
    from .services import cli_install as cli_install_svc
    _finish(cli_install_svc.install_cli(modules, dry_run=dry_run))


@app.command("update")
def update(
    modules: Optional[List[str]] = typer.Argument(
        None, help="Modules to update (omit for all present modules)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't pull."),
):
    """Fast-forward (`git pull`) the workspace and the present modules (cloned or linked)."""
    _finish(modules_svc.update(modules, dry_run=dry_run))


# --------------------------------------------------------------------------- #
# dependencies
# --------------------------------------------------------------------------- #
@app.command("install")
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


@app.command("sync")
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't change."),
):
    """Bring the workspace up to date: install missing deps, then update modules."""
    _finish(modules_svc.sync(dry_run=dry_run))


@app.command("doctor")
def doctor():
    """Inventory tools, compilers, and dependencies; report what is missing."""
    _finish(setup_svc.run("detect", dry_run=False))


@app.command("remove")
def remove(
    all: bool = typer.Option(
        False, "--all",
        help="[bold red]Wipe everything[/bold red]: vcpkg ports, downloaded "
             "toolchains (intel/llvm + AdaptiveCpp + oneAPI, several GB), and the "
             "portable cmake/ninja — the whole dependencies/ tree."),
    gpu: bool = typer.Option(False, "--gpu", help="Include GPU-only deps in removal."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed."),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt for --all."),
):
    """Remove provisioned dependencies. Use [bold]--all[/bold] to reclaim the lot."""
    _finish(setup_svc.uninstall(gpu=gpu, dry_run=dry_run, everything=all, assume_yes=yes))


if __name__ == "__main__":
    app()
