"""Composition root: assemble the pipeline with platform-specific dependencies.

This is the one place that knows which concrete implementations to wire together
(Dependency Inversion in practice). Everything downstream depends only on the
abstractions, so swapping a package manager or dependency source for a test fake
happens here, not in the steps.
"""

from __future__ import annotations

from functools import partial

from sushicore.provision.sinks import WorkspaceSink

from ..config import DEFAULT_ACTIVE_TOOLCHAIN, TOOLCHAINS, Config, load_config, workspace_root
from .dependency_source import IDependencySource, TomlDependencySource
from .package_managers import (
    AptManager,
    DirectDownloadWindowsManager,
    DnfManager,
    IPackageManager,
    PacmanManager,
    VcpkgManager,
    WingetManager,
    YumManager,
    ZypperManager,
)
from .pipeline import InstallContext, InstallPipeline, ToolchainSelection
from .selection import selection_from_source
from .steps import (
    ConfigureStep,
    DetectStep,
    InstallDepsStep,
    UninstallStep,
    VerifyStep,
    report_readiness,
)

STEP_NAMES = ("detect", "install", "configure", "verify", "provision", "all")


def _validated_toolchain(toolchain: str) -> str:
    """Return *toolchain*, or raise ``ValueError`` when it is not one of ``TOOLCHAINS``."""
    if toolchain not in TOOLCHAINS:
        raise ValueError(f"Unknown toolchain '{toolchain}'. Choose one of {', '.join(TOOLCHAINS)}.")
    return toolchain


def _managers_for(cfg: Config) -> list[IPackageManager]:
    """Return the package managers this platform installs through, in preference order."""
    if cfg.is_windows:
        return [WingetManager(), DirectDownloadWindowsManager(), VcpkgManager(cfg)]
    # VcpkgManager also serves Linux: it is the only route for ports with no apt
    # package at all (vk-bootstrap, cgltf — see Dependency.vcpkg_fallback_ports).
    return [AptManager(), DnfManager(), YumManager(), PacmanManager(), ZypperManager(),
            VcpkgManager(cfg)]


def build_pipeline(
    *,
    only: str = "all",
    selection: dict[str, bool] | None = None,
    dry_run: bool = False,
    refresh_toolchains: bool = False,
    cfg: Config | None = None,
    source: IDependencySource | None = None,
    managers: list[IPackageManager] | None = None,
) -> tuple[InstallPipeline, InstallContext]:
    """Build the installer pipeline and its execution context.

    ``only`` selects a single step ('detect'|'install'|'configure'|'verify') or a
    combo ('provision'|'all'). By default the toolchains the present modules
    declare are provisioned, and nothing else. ``selection`` overrides that per
    component (keys: ``install_intel_llvm``, ``install_acpp``, ``oneapi``,
    ``gpu``), as gathered by ``hub install --customize``. ``source``/``managers``
    can be injected for tests.
    """
    cfg = cfg or load_config()
    source = source or TomlDependencySource()
    managers = managers if managers is not None else _managers_for(cfg)

    derived = selection_from_source(source)
    sel = (derived.merged(selection) if selection else derived).as_dict()
    active_toolchain = _validated_toolchain(DEFAULT_ACTIVE_TOOLCHAIN)

    all_steps = {
        "detect":    DetectStep(source, managers,
                                after_inventory=partial(report_readiness, source)),
        "install":   InstallDepsStep(source, managers),
        "configure": ConfigureStep(WorkspaceSink(workspace_root())),
        "verify":    VerifyStep(),
    }

    if only == "all":
        ordered = [
            all_steps["detect"],
            all_steps["install"],
            all_steps["configure"],
            all_steps["verify"],
        ]
    elif only == "provision":
        # `hub install`: detect + install + write config, but no verify. The
        # workspace has no single project to build, so VerifyStep (which compiles
        # and smoke-tests a checkout) is left to each module's own CLI
        # (`sr`, `se`, `sa`, `sb`).
        ordered = [
            all_steps["detect"],
            all_steps["install"],
            all_steps["configure"],
        ]
    elif only in all_steps:
        ordered = [all_steps[only]]
    else:
        raise ValueError(f"Unknown step '{only}'. Choose from {STEP_NAMES}.")

    ctx = InstallContext(
        cfg=cfg, selection=ToolchainSelection(**sel), consumer="sushistack",
        active_toolchain=active_toolchain,
        refresh_toolchains=refresh_toolchains, dry_run=dry_run,
    )
    return InstallPipeline(ordered), ctx


def build_uninstall_pipeline(
    *,
    gpu: bool = False,
    dry_run: bool = False,
    everything: bool = False,
    cfg: Config | None = None,
    source: IDependencySource | None = None,
    managers: list[IPackageManager] | None = None,
) -> tuple[InstallPipeline, InstallContext]:
    """Build a single-step pipeline that removes what the installer placed."""
    cfg = cfg or load_config()
    source = source or TomlDependencySource()
    managers = managers if managers is not None else _managers_for(cfg)

    step = UninstallStep(source, managers, WorkspaceSink(workspace_root()))
    ctx = InstallContext(cfg=cfg, selection=ToolchainSelection(gpu=gpu), consumer="sushistack",
                         dry_run=dry_run, everything=everything)
    return InstallPipeline([step]), ctx
