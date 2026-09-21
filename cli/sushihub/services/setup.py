"""`hub install` service: thin wrapper that runs the installer pipeline.

The CLI command parses flags, this builds the pipeline via the composition root,
runs it, and maps success to an exit code. All the real logic lives in the
``sushihub.setup`` package.
"""

from __future__ import annotations

from .. import console
from ..setup import build_pipeline, build_uninstall_pipeline
from ..setup.selection import ToolchainSelection


def run(step: str = "all", dry_run: bool = False,
        selection: dict[str, bool] | None = None, assume_yes: bool = False,
        refresh_toolchains: bool = False) -> int:
    """Run one step (or the whole pipeline) and return a process exit code.

    What the present modules declare is provisioned; ``selection`` (from
    --customize) overrides that per component. ``assume_yes`` pre-answers the
    LLVM-download consent prompt so unattended runs (CI, scripted installs) don't
    need a TTY to proceed.
    """
    detect_only = step == "detect"
    console.header("SushiHub Doctor" if detect_only else "SushiHub Install")
    if dry_run:
        console.info("Dry-run: showing actions without changing the system.")

    try:
        pipeline, ctx = build_pipeline(only=step, selection=selection, dry_run=dry_run,
                                      refresh_toolchains=refresh_toolchains)
    except (ValueError, FileNotFoundError) as exc:
        console.error(str(exc))
        return 1

    if not detect_only:
        names = ToolchainSelection.from_context(ctx).components()
        console.info(f"Installing: {', '.join(names) or 'base tools only'}.")

    # Gather consent for the heavy Windows LLVM download up front — before the
    # progress spinner starts — so the prompt is actually answerable.
    if (not dry_run and step in ("all", "install", "provision") and ctx.install_acpp
            and ctx.cfg.is_windows):
        from ..setup.toolchains import (
            LLVM_WINDOWS_VERSION, _confirm_timeout, _find_windows_llvm,
        )
        if _find_windows_llvm() is None:
            if assume_yes:
                console.info("--yes: proceeding with the LLVM download without prompting.")
                ctx.assume_acpp_llvm = True
            else:
                ctx.assume_acpp_llvm = _confirm_timeout(
                    f"[bold][warn]AdaptiveCpp needs LLVM {LLVM_WINDOWS_VERSION} "
                    "(a ~2-3 GB download) to build on Windows.[/warn][/bold]\n"
                    "Install it now into the deps folder?",
                    default=False,
                )
            if not ctx.assume_acpp_llvm:
                console.info("Skipping the LLVM download. Re-run `hub install` to retry, "
                             "or `hub install --customize` and deselect AdaptiveCpp.")

    # Prime sudo up front (Linux, non-root) so the password prompt happens here,
    # attached to the terminal, rather than being swallowed by the live progress
    # spinner during `install-deps` (where it would just time out).
    if not dry_run and not detect_only and not ctx.cfg.is_windows:
        from ..setup.package_managers import prime_sudo
        prime_sudo()

    ok = pipeline.run(ctx, show_progress=not detect_only)
    if ok:
        console.success("Inventory complete." if detect_only else "Install completed.")
        if step in ("all", "provision", "configure"):
            console.info("Next: `hub add sushiruntime` then build it with `sr build`, "
                         "or `hub status` to see what is installed.")
        return 0
    console.error("Inventory failed." if detect_only else "Install did not complete. See messages above.")
    return 1


def uninstall(
    gpu: bool = False,
    dry_run: bool = False,
    everything: bool = False,
    assume_yes: bool = False,
) -> int:
    """Remove packages and config files placed by `hub install`. Return exit code."""
    console.header("SushiHub Remove")
    if dry_run:
        console.info("Dry-run: showing actions without changing the system.")
    if everything:
        console.warn(
            "--all wipes the whole shared dependencies/ tree (toolchains, vcpkg, "
            "portable cmake/ninja). Your system git/cmake are NOT touched."
        )
        if not dry_run and not assume_yes:
            if console.prompt("Are you sure? (y/N)", "n").strip().lower() not in ("y", "yes"):
                console.info("Aborted.")
                return 1

    try:
        pipeline, ctx = build_uninstall_pipeline(
            gpu=gpu, dry_run=dry_run, everything=everything,
        )
    except (ValueError, FileNotFoundError) as exc:
        console.error(str(exc))
        return 1

    ok = pipeline.run(ctx)
    if ok:
        console.success("Uninstall completed.")
        return 0
    console.error("Uninstall did not complete cleanly. See messages above.")
    return 1
