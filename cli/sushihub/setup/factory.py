# factory.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Composition root: assemble the pipeline with platform-specific dependencies.

This is the one place that knows which concrete implementations to wire together
(Dependency Inversion in practice). Everything downstream depends only on the
abstractions, so swapping a package manager or dependency source for a test fake
happens here, not in the steps.
"""

from __future__ import annotations

from functools import partial

from sushicore.provision import home as provision_home
from sushicore.provision import probe, selection
from sushicore.provision.dependency_home import DependencyHome
from sushicore.provision.sinks import WorkspaceSink

from .. import console
from ..config import (
    DEFAULT_ACTIVE_TOOLCHAIN,
    TOOLCHAINS,
    Config,
    deps_dir,
    load_config,
    workspace_root,
)
from ..services.data import (
    DataInstaller,
    DataPlacer,
    DataReport,
    DataSource,
    DataStore,
    Downloader,
    HttpDownloader,
    WorkspaceDataSource,
)
from .data_step import DataStep
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
from .steps import (
    ConfigureStep,
    DetectStep,
    InstallDepsStep,
    UninstallStep,
    report_readiness,
)

STEP_NAMES = ("detect", "install", "configure", "provision")

#: The folder of the dependency root that holds the data store: ``dependencies/data``.
K_DATA_STORE = "data"

#: The dependency root of this workspace, which every provisioning object of a run reads.
K_HOME = DependencyHome(deps_dir)

#: What hub says where the shared provisioning code names the command that drives it.
_HUB_WORDING = {
    "program": "hub",
    "rerun_command": "hub install",
    "removal_hint": "(`hub remove --all` does it for you).",
    "fallback_hint": "Re-run `hub install --customize` and also pick intel-llvm as a fallback.",
    "refresh_command": "hub install --refresh-toolchains",
}


def _validated_toolchain(toolchain: str) -> str:
    """Return *toolchain*, or raise ``ValueError`` when it is not one of ``TOOLCHAINS``."""
    if toolchain not in TOOLCHAINS:
        raise ValueError(f"Unknown toolchain '{toolchain}'. Choose one of {', '.join(TOOLCHAINS)}.")
    return toolchain


def _managers_for(cfg: Config) -> list[IPackageManager]:
    """Return the package managers this platform installs through, in preference order."""
    if cfg.is_windows:
        return [WingetManager(console=console),
                DirectDownloadWindowsManager(console=console, home=K_HOME),
                VcpkgManager(cfg, console=console, home=K_HOME)]
    # VcpkgManager serves Linux for Dependency.vcpkg_fallback_ports; see cli/README.md.
    return [AptManager(console=console), DnfManager(console=console), YumManager(console=console),
            PacmanManager(console=console), ZypperManager(console=console),
            VcpkgManager(cfg, console=console, home=K_HOME)]


def derived_selection(source: IDependencySource, cfg: Config) -> ToolchainSelection:
    """Return what a bare ``hub install`` installs for *source* on this machine.

    The toolchains follow sushicore's rule. The GPU component is on whatever the
    modules declare; ``docs/design/GPU_BACKEND_PROVISIONING/README.md`` §3 says why.
    """
    present = {name: found
               for name, found, _detail in probe.toolchain_status(cfg, False, home=K_HOME)}
    return selection.derive(source, present).merged({"gpu": True})


def build_pipeline(
    *,
    only: str = "provision",
    selection: dict[str, bool] | None = None,
    dry_run: bool = False,
    refresh_toolchains: bool = False,
    cfg: Config | None = None,
    source: IDependencySource | None = None,
    managers: list[IPackageManager] | None = None,
    data: bool = True,
    data_source: DataSource | None = None,
    downloader: Downloader | None = None,
) -> tuple[InstallPipeline, InstallContext]:
    """Build the installer pipeline and its execution context.

    ``only`` selects a single step ('detect'|'install'|'configure') or all three
    in that order ('provision'), followed by the data step. By default one toolchain per
    capability the present modules require is provisioned, and none when the machine
    already holds one. ``selection`` overrides that per
    component (keys: ``install_intel_llvm``, ``install_acpp``, ``oneapi``,
    ``gpu``), as gathered by ``hub install --customize``. ``data`` is false for
    ``hub install --no-data``: the data step is left out and the inventory lists no data package.
    ``source``/``managers``/``data_source``/``downloader`` can be injected for tests.
    """
    cfg = cfg or load_config()
    source = source or TomlDependencySource()
    managers = managers if managers is not None else _managers_for(cfg)

    derived = derived_selection(source, cfg)
    sel = (derived.merged(selection) if selection else derived).as_dict()
    active_toolchain = _validated_toolchain(DEFAULT_ACTIVE_TOOLCHAIN)

    data_source = data_source or WorkspaceDataSource()
    placer = DataPlacer()
    report = DataReport(data_source, placer, console)
    all_steps = {
        "detect":    DetectStep(source, managers,
                                after_inventory=partial(report_readiness, source),
                                data_rows=report.rows if data else None, console=console,
                                toolchain_status=partial(probe.toolchain_status, home=K_HOME)),
        "install":   InstallDepsStep(source, managers, console=console),
        "configure": ConfigureStep(WorkspaceSink(workspace_root()), console=console),
    }

    if only == "provision":
        ordered = list(all_steps.values())
        if data:
            store = DataStore(provision_home.root(home=K_HOME) / K_DATA_STORE, downloader or HttpDownloader())
            ordered.append(DataStep(data_source, DataInstaller(store, placer, console),
                                    placer, console))
    elif only in all_steps:
        ordered = [all_steps[only]]
    else:
        raise ValueError(f"Unknown step '{only}'. Choose from {STEP_NAMES}.")

    ctx = InstallContext(
        cfg=cfg, selection=ToolchainSelection(**sel), consumer="sushistack",
        active_toolchain=active_toolchain,
        refresh_toolchains=refresh_toolchains, dry_run=dry_run, home=K_HOME,
        **_HUB_WORDING,
    )
    return InstallPipeline(ordered, console=console), ctx


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

    step = UninstallStep(source, managers, WorkspaceSink(workspace_root()), console=console,
                         dependency_home=K_HOME)
    ctx = InstallContext(cfg=cfg, selection=ToolchainSelection(gpu=gpu), consumer="sushistack",
                         dry_run=dry_run, everything=everything, home=K_HOME, **_HUB_WORDING)
    return InstallPipeline([step], console=console), ctx
