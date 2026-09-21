"""Concrete pipeline steps.

Each step has a single responsibility and depends only on abstractions:
``DetectStep`` inventories the machine, ``InstallDepsStep`` installs missing
manifest packages through injected package managers, ``ConfigureStep`` writes
``config.local.toml`` from probed tool paths, ``VerifyStep`` builds and
smoke-tests through the project service, and ``UninstallStep`` tears down
everything the installer placed on the system.
"""

from __future__ import annotations

import dataclasses
import shutil
import subprocess
from pathlib import Path

from .. import console
from ..config import config_dir
from . import probe
from .probe import binary_works
from .dependency_source import SHARED_OWNER, Dependency, IDependencySource
from .ordering import owner_order
from .gpu_backends.adapter_builder import AdapterBuilder, SubprocessCommandRunner
from .gpu_backends.provisioning import provision_gpu_adapters
from .gpu_backends.registry import DEFAULT_REGISTRY
from .package_managers import (
    IPackageManager,
    LinuxPackageManager,
    WINGET_ID_TO_CMD,
    _tools_dir,
    ensure_intel_oneapi_repo,
    install_gpu_stack,
    refresh_windows_path,
)
from .pipeline import InstallContext, Step, StepResult
from . import toolchains

# System toolchain installed through the toolchain manager (not via the manifest
# since these tools must exist before vcpkg/pip can run).
_LINUX_TOOLCHAIN_APT = ["build-essential", "cmake", "ninja-build", "git"]


def provision_adapters_for_run(ctx: InstallContext) -> None:
    """Build every located GPU backend's Unified Runtime adapter for this run.

    Reads the intel/llvm root from ``ctx.resolved_paths["llvm_root"]``, refreshes
    PATH and re-probes the local config, then builds against the refreshed copy.
    """
    llvm_root = ctx.resolved_paths.get("llvm_root")
    if not llvm_root:
        console.info("No intel/llvm toolchain installed; GPU adapter build skipped.")
        return
    refresh_windows_path()
    probed = probe.resolve_local_config(ctx.cfg, gpu=ctx.gpu)
    cfg = dataclasses.replace(ctx.cfg, **probed) if probed else ctx.cfg
    builder = AdapterBuilder(cfg=cfg, runner=SubprocessCommandRunner())
    provision_gpu_adapters(cfg, DEFAULT_REGISTRY, Path(llvm_root), builder, ctx.dry_run)


def _resolve_gpu_vendor(ctx: InstallContext) -> str:
    """Return the GPU vendor the detect step recorded, probing the machine when it did not."""
    ctx.gpu_vendor = ctx.gpu_vendor or probe.detect_gpu_vendor() or "none"
    return ctx.gpu_vendor


def _check_cmd_ok(cmd: list[str]) -> bool:
    """True if *cmd* runs and exits 0 (its tool is present and the check passes)."""
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except (OSError, FileNotFoundError):
        return False


def _dep_installed(dep: Dependency, mgr: IPackageManager | None, platform: str,
                   vcpkg: IPackageManager | None = None) -> bool:
    if dep.check_cmd and _check_cmd_ok(dep.check_cmd):
        return True
    pkgs = dep.packages_for(platform)
    if pkgs:
        return mgr is not None and all(mgr.is_installed(p) for p in pkgs)
    fallback = dep.vcpkg_fallback_ports(platform)
    if fallback:
        return vcpkg is not None and all(vcpkg.is_installed(p) for p in fallback)
    return False


def _first_available(managers: list[IPackageManager]) -> IPackageManager | None:
    for mgr in managers:
        if mgr.available():
            return mgr
    return None


#: The three statuses an inventory row can carry.
_OK = "OK"
_MISSING = "MISSING"
_NOT_NEEDED = "NOT NEEDED"

#: What each discrete-GPU vendor implies for the compute SDK that gets installed.
_VENDOR_SDK = {
    "amd":  "AMD — installs ROCm (HIP)",
    "intel": "Intel — installs Level Zero + Intel OpenCL",
    "none": "no discrete GPU — CPU (SPIR/OpenCL) path",
}

#: NVIDIA's row names how each platform installs the toolkit (see cuda.py).
_VENDOR_SDK_NVIDIA = {
    "windows": "NVIDIA — installs CUDA toolkit (NVIDIA installer, one UAC prompt)",
    "linux":   "NVIDIA — installs CUDA toolkit (NVIDIA apt repo)",
}


def _status(present: bool) -> str:
    """Return the status a probed component reports."""
    return _OK if present else _MISSING


class DetectStep(Step):
    """Inventory tools and dependencies; fill ``ctx.detected``."""

    name = "detect"

    def __init__(self, source: IDependencySource,
                 managers: list[IPackageManager] | None = None, *,
                 toolchain_status=probe.toolchain_status,
                 gpu_vendor=probe.detect_gpu_vendor) -> None:
        """Wire the dependency source, the package managers and the machine probes.

        @param toolchain_status Reads the SYCL toolchains off the machine.
        @param gpu_vendor       Reads the discrete-GPU vendor off the machine.
        """
        self._source = source
        self._managers = managers or []
        self._toolchain_status = toolchain_status
        self._gpu_vendor = gpu_vendor

    def _dep_manager(self, plat: str) -> IPackageManager | None:
        """The manager that knows whether a manifest dep is installed."""
        if plat == "windows":
            return next((m for m in self._managers if m.name == "vcpkg"), None)
        linux = ("apt", "dnf", "yum", "pacman", "zypper")
        return next((m for m in self._managers
                     if m.name in linux and m.available()), None)

    def _vcpkg_manager(self) -> IPackageManager | None:
        """The vcpkg manager, if wired in — the Linux fallback for apt-less ports."""
        return next((m for m in self._managers if m.name == "vcpkg"), None)

    def _base_tool_rows(self, ctx: InstallContext,
                        owner_of) -> list[tuple[str, str, str, str]]:
        """Probe the tools a build invokes directly and return their rows.

        Some of them live off PATH (in the deps folder, or as a vcpkg port like
        pkgconf), so the configured path is consulted before one is reported
        missing.
        """
        cfg = ctx.cfg
        configured = {
            "cmake":     cfg.expand(cfg.cmake_exe)    if cfg.cmake_exe    else "",
            "ninja":     cfg.expand(cfg.ninja_exe)    if cfg.ninja_exe    else "",
            "pkg-config": cfg.expand(cfg.pkgconf_exe) if cfg.pkgconf_exe  else "",
            "doxygen":   cfg.expand(cfg.doxygen_exe)  if cfg.doxygen_exe  else "",
        }
        rows: list[tuple[str, str, str, str]] = []
        for tool in ("python3" if cfg.platform != "windows" else "python",
                     "git", "cmake", "ninja", "pkg-config", "doxygen"):
            path = shutil.which(tool) or ""
            if not path and configured.get(tool) and Path(configured[tool]).is_file():
                path = configured[tool]
            ctx.detected[tool] = bool(path)
            rows.append((tool, _status(bool(path)), owner_of(tool), path))
        return rows

    def _sycl_compiler_row(self, ctx: InstallContext) -> tuple[str, str, str, str]:
        """Probe the SYCL compiler a build would use and return its row.

        The intel/llvm bundle and acpp live off PATH, so the paths ``hub install``
        recorded are consulted when PATH holds nothing.
        """
        compiler, where = probe.find_sycl_compiler(ctx.cfg)
        if compiler is None:
            compiler, where = probe.find_configured_toolchain(ctx.cfg)
        ctx.detected["sycl_compiler"] = compiler is not None
        return ("SYCL compiler (active)", _status(compiler is not None), "sushiruntime",
                f"{compiler or '-'} {where or ''}".strip())

    def _toolchain_rows(self, ctx: InstallContext, declared: set[str],
                        owner_of) -> list[tuple[str, str, str, str]]:
        """Return a row per SYCL toolchain (and CUDA), recording what is present.

        These are installed by the toolchain installer rather than apt or vcpkg,
        so they are probed here instead of in the manifest loop. One that no
        present module declares reads NOT NEEDED, while ``ctx.detected`` still
        records whether it happens to be on the machine.
        """
        rows: list[tuple[str, str, str, str]] = []
        for name, present, detail in self._toolchain_status(ctx.cfg, ctx.gpu):
            ctx.detected[name] = present
            if name in declared:
                rows.append((name, _status(present), owner_of(name), detail))
            else:
                rows.append((name, _NOT_NEEDED, owner_of(name),
                             detail or "no present module declares it"))
        return rows

    def _dependency_rows(self, ctx: InstallContext,
                         all_deps: list[Dependency]) -> list[tuple[str, str, str, str]]:
        """Return a row per declared dependency, recording the installable ones.

        A dependency that names no package for this platform is nothing to
        install here, so it reads NOT NEEDED and stays out of ``ctx.detected``,
        where the readiness report would otherwise count it as unmet. The rest
        are checked exactly as ``install-deps`` checks them, so detect and
        install agree.
        """
        plat = ctx.cfg.platform
        dep_mgr = self._dep_manager(plat)
        vcpkg_mgr = self._vcpkg_manager()
        installable = {d.name for d in self._source.selected(plat, ctx.gpu)}

        rows: list[tuple[str, str, str, str]] = []
        for dep in all_deps:
            if dep.name not in installable:
                rows.append((dep.name, _NOT_NEEDED, dep.owner,
                             f"{dep.description} (nothing to install on {plat})"))
                continue
            if dep_mgr is not None or vcpkg_mgr is not None:
                present = _dep_installed(dep, dep_mgr, plat, vcpkg_mgr)
            else:
                present = bool(dep.check_cmd) and _check_cmd_ok(dep.check_cmd)
            ctx.detected[dep.name] = present
            pkgs = ", ".join(dep.packages_for(plat) or dep.vcpkg_fallback_ports(plat))
            rows.append((dep.name, _status(present), dep.owner,
                         f"{dep.description} ({pkgs})"))
        return rows

    def _gpu_vendor_row(self, ctx: InstallContext) -> tuple[str, str, str, str]:
        """Probe the discrete-GPU vendor and return its row."""
        vendor = self._gpu_vendor()
        ctx.gpu_vendor = vendor
        ctx.detected["nvidia_gpu"] = vendor == "nvidia"
        if vendor == "nvidia":
            detail = _VENDOR_SDK_NVIDIA.get(ctx.cfg.platform, _VENDOR_SDK_NVIDIA["linux"])
        else:
            detail = _VENDOR_SDK.get(vendor, vendor)
        return ("GPU vendor", _status(vendor != "none"), SHARED_OWNER, detail)

    def inventory_rows(self, ctx: InstallContext,
                       all_deps: list[Dependency]) -> list[tuple[str, str, str, str]]:
        """Probe the machine and return ``(component, status, owner, detail)`` rows.

        Rows are grouped by owner in :func:`ordering.owner_order`, and a
        component is reported once: the first row to claim a name keeps it.
        Everything that was actually probed lands in ``ctx.detected``, so the
        readiness report stays truthful.
        """
        owner_by_name = {dep.name: dep.owner for dep in all_deps}
        declared = {dep.name for dep in all_deps if dep.owner != SHARED_OWNER}

        def owner_of(name: str) -> str:
            return owner_by_name.get(name, SHARED_OWNER)

        collected = list(self._base_tool_rows(ctx, owner_of))
        if "sushiruntime" in {dep.owner for dep in all_deps}:
            collected.append(self._sycl_compiler_row(ctx))
        collected.extend(self._toolchain_rows(ctx, declared, owner_of))
        collected.extend(self._dependency_rows(ctx, all_deps))
        collected.append(self._gpu_vendor_row(ctx))

        unique: dict[str, tuple[str, str, str, str]] = {}
        for row in collected:
            unique.setdefault(row[0], row)

        by_owner: dict[str, list[tuple[str, str, str, str]]] = {}
        for row in unique.values():
            by_owner.setdefault(row[2], []).append(row)
        return [row for owner in owner_order(self._source, by_owner)
                for row in by_owner[owner]]

    def run(self, ctx: InstallContext) -> StepResult:
        refresh_windows_path()  # reflect tools the bootstrap installer just added

        # Building the list here also populates the source's depends_on map, which
        # the row ordering and the readiness report below both read.
        all_deps = self._source.all()

        console.table(
            ["Component", "Status", "Owner", "Detail"],
            [list(row) for row in self.inventory_rows(ctx, all_deps)],
            title="Environment inventory",
        )

        from ..config import deps_dir
        console.info(f"Vendored dependencies go in one folder: {deps_dir()}")
        console.info("Remove the whole install by deleting that folder "
                     "(`hub remove --all` does it for you).")
        if ctx.cfg.platform == "windows":
            console.info("System prerequisites kept outside that folder: the C++ "
                         "host compiler (Visual Studio Build Tools + Windows SDK), "
                         "git, and the toolkit for the detected GPU.")
        else:
            console.info("System prerequisites kept outside that folder: the host "
                         "compiler (gcc) plus the -dev packages (hwloc, gtest, "
                         "opencl), git, and the toolkit for the detected GPU.")

        self._report_readiness(ctx, all_deps)
        return StepResult.OK

    def _effective_required(self, module: str, all_deps: list[Dependency]) -> list[Dependency]:
        """The required dependencies a module needs to build.

        A module needs the shared build/toolchain infrastructure, its own
        required dependencies, and — transitively — the required dependencies of
        every module it declares it builds on (``[module] depends_on``).
        """
        want: dict[str, Dependency] = {}
        seen: set[str] = set()

        def visit(m: str) -> None:
            if m in seen:
                return
            seen.add(m)
            for dep in all_deps:
                if dep.required and dep.owner == m:
                    want[dep.name] = dep
            for upstream in self._source.depends_on(m):
                visit(upstream)

        visit(module)
        for dep in all_deps:  # shared infrastructure applies to every module
            if dep.required and dep.owner == SHARED_OWNER:
                want[dep.name] = dep
        return list(want.values())

    def _missing_requirements(self, ctx: InstallContext,
                              required: list[Dependency]) -> list[str]:
        """Unmet requirement labels among *required*, honouring any-of groups.

        Dependencies sharing a ``provides`` tag are interchangeable alternatives
        (e.g. the SYCL toolchains): the group is satisfied when *any* member is
        present, and only reported missing — as "a or b or c" — when none are.
        A dependency the current platform never checked (no package, no toolchain,
        no check) is treated as satisfied: nothing to install here.
        """
        groups: dict[str, list[Dependency]] = {}
        for dep in required:
            groups.setdefault(dep.provides or dep.name, []).append(dep)

        missing: list[str] = []
        for members in groups.values():
            checked = [m for m in members if m.name in ctx.detected]
            if not checked:
                continue  # not applicable on this platform
            if any(ctx.detected.get(m.name) for m in members):
                continue  # any-of satisfied
            missing.append(" or ".join(m.name for m in members))
        return missing

    def _report_readiness(self, ctx: InstallContext, all_deps: list[Dependency]) -> None:
        """Print a plain-English, per-module readiness summary under the table.

        For every known stack module, in the order a build would need them: how
        it is present, and for a module built from source whether the
        dependencies it needs (its own plus the modules it builds on) are
        present. A binary install builds nothing, so it needs nothing.
        """
        from ..config import workspace_root
        from ..services import links
        from ..services.catalog import CATALOG
        from ..services.modules import module_dest
        from ..services.presence import Presence, describe, presence_of

        try:
            root = workspace_root()
        except SystemExit:
            return

        linked = links.registered()
        console.info("Module readiness:")
        for name in owner_order(self._source, CATALOG):
            dest = module_dest(root, name)
            state = presence_of(root, name, linked)
            if state is Presence.BINARY:
                _, text = describe(root, name, linked)
                console.console.print(
                    f"  [green]{name}: {text}, nothing to build[/green]")
                continue
            if state is Presence.ABSENT:
                verb = "linked but missing at" if name in linked else "not cloned yet"
                hint = f" ({dest})" if name in linked else f" (hub add {name})"
                console.console.print(f"  [dim]{name}: {verb}{hint}[/dim]")
                continue
            missing = self._missing_requirements(
                ctx, self._effective_required(name, all_deps))
            if missing:
                console.console.print(
                    f"  [yellow]{name}: needs {', '.join(missing)}[/yellow]")
            else:
                console.console.print(f"  [green]{name}: ready to build[/green]")


class InstallDepsStep(Step):
    """Install missing manifest dependencies and system toolchain."""

    name = "install-deps"

    def __init__(self, source: IDependencySource,
                 managers: list[IPackageManager]) -> None:
        self._source = source
        self._managers = managers

    def _manager(self, name: str) -> IPackageManager | None:
        for m in self._managers:
            if m.name == name:
                return m
        return None

    def run(self, ctx: InstallContext) -> StepResult:
        if ctx.cfg.platform == "windows":
            return self._run_windows(ctx)
        return self._run_linux(ctx)

    # -- SYCL toolchains (shared) --------------------------------------------- #

    def _install_toolchains(self, ctx: InstallContext,
                            mgr: IPackageManager | None,
                            vcpkg: IPackageManager | None) -> None:
        """Install the SYCL toolchains this run selected.

        Which toolchains run is gated by ``ctx.install_intel_llvm`` /
        ``ctx.install_acpp`` (set from ``--customize``'s selection in
        ``factory.build_pipeline``, both True by default). Installed paths are
        recorded on ``ctx.resolved_paths`` so ConfigureStep can write them.
        Failures are non-fatal when another toolchain remains, but the sole
        selected toolchain failing leaves nothing to build with, so that case
        warns loudly.
        """
        if ctx.install_intel_llvm:
            llvm = toolchains.install_intel_llvm(
                ctx.cfg, ctx.dry_run, refresh=ctx.refresh_toolchains)
            if llvm:
                ctx.resolved_paths["llvm_root"] = llvm
            else:
                console.warn("intel/llvm bundle not installed; the intel-llvm "
                             "toolchain will be unavailable.")

        if ctx.install_acpp:
            acpp = toolchains.install_adaptivecpp(
                ctx.cfg, mgr, vcpkg, ctx.dry_run,
                assume_yes=ctx.assume_acpp_llvm)
            if acpp:
                ctx.resolved_paths["acpp_exe"] = acpp
            elif not ctx.install_intel_llvm:
                console.warn("AdaptiveCpp is the only toolchain selected but it did "
                             "not install; the project will not build. Re-run "
                             "`hub install --customize` and also pick intel-llvm as "
                             "a fallback.")

    # -- Linux ---------------------------------------------------------------- #

    def _run_linux(self, ctx: InstallContext) -> StepResult:
        linux_managers = ["apt", "dnf", "yum", "pacman", "zypper"]
        mgr = next(
            (self._manager(n) for n in linux_managers
             if self._manager(n) and self._manager(n).available()),  # type: ignore[union-attr]
            None,
        )
        if mgr is None:
            msg = ("No supported package manager found (apt, dnf, yum, pacman, zypper). "
                   "Install python3, pip, git, cmake, and ninja manually, then re-run.")
            if ctx.dry_run:
                console.warn(f"(dry-run) {msg}")
                return StepResult.SKIPPED
            console.error(msg)
            return StepResult.FAILED
        assert isinstance(mgr, LinuxPackageManager)  # linux_managers only holds these

        console.info(f"Using package manager: {mgr.name}")
        vcpkg = self._manager("vcpkg")

        # Translate the generic apt toolchain list to native package names.
        pkgs: list[str] = list(mgr.translate_apt(_LINUX_TOOLCHAIN_APT))
        vcpkg_ports: list[str] = []
        for dep in self._source.selected("linux", ctx.gpu):
            if _dep_installed(dep, mgr, "linux", vcpkg):
                console.info(f"{dep.name}: already installed, skipping.")
                continue
            if dep.linux_apt:
                pkgs.extend(mgr.translate_apt(dep.linux_apt))
            else:
                # No apt package at all (vk-bootstrap, cgltf, …) — the only route
                # is vcpkg (see Dependency.vcpkg_fallback_ports).
                vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))

        pkgs = _dedup(pkgs)
        vcpkg_ports = _dedup(vcpkg_ports)

        ok = True
        if pkgs:
            console.info(f"Installing via {mgr.name}: {', '.join(pkgs)}")
            ok = mgr.install(pkgs, ctx.dry_run)
            ctx.installed.extend(pkgs)
        else:
            console.info("No apt packages to install.")

        if vcpkg_ports:
            if vcpkg is None:
                console.warn(f"No vcpkg manager available; cannot install "
                             f"{', '.join(vcpkg_ports)} (no apt package exists for "
                             f"these on Linux). Install them manually.")
                ok = False
            else:
                console.info(f"Installing via vcpkg: {', '.join(vcpkg_ports)}")
                ok = vcpkg.install(vcpkg_ports, ctx.dry_run) and ok
                ctx.installed.extend(vcpkg_ports)

        if not pkgs and not vcpkg_ports:
            console.info("All packages already present.")

        self._install_toolchains(ctx, mgr=mgr, vcpkg=None)

        # Intel oneAPI DPC++ — installed by default (part of "everything"), like
        # the Dockerfile's oneAPI apt route. The compiler package lives only in
        # Intel's apt repo, so configure that repo first (mirroring the Dockerfile)
        # and then install; `mgr.install` runs `apt-get update` so the new repo is
        # picked up. Failure is non-fatal: intel-llvm/AdaptiveCpp already provide a
        # working SYCL compiler, so a missing oneAPI must not fail the whole run.
        if ctx.oneapi and mgr.name == "apt":
            console.info("oneAPI: configuring the Intel apt repository and installing "
                         "intel-oneapi-compiler-dpcpp-cpp.")
            if ensure_intel_oneapi_repo(ctx.dry_run):
                if not mgr.install(["intel-oneapi-compiler-dpcpp-cpp"], ctx.dry_run):
                    console.warn("oneAPI compiler install failed; continuing "
                                 "(intel-llvm/AdaptiveCpp remain available).")
        elif ctx.oneapi:
            console.warn(f"oneAPI on {mgr.name} is not automated; install the "
                         "Intel oneAPI DPC++ compiler manually.")

        # GPU compute SDK, chosen by the detected vendor (NVIDIA->CUDA, AMD->ROCm,
        # Intel->Level Zero). Installed only on apt; the adapter build below
        # runs for every manager.
        vendor = _resolve_gpu_vendor(ctx) if ctx.gpu else "none"
        if ctx.gpu and mgr.name == "apt":
            if not install_gpu_stack(ctx.cfg, vendor, ctx.dry_run) and vendor != "none":
                message = (f"GPU compute SDK for '{vendor}' was not installed — "
                           f"the build will fall back to the CPU (SPIR/OpenCL) path. "
                           f"See the log above for the failing command.")
                console.error(message)
                ctx.warnings.append(message)
        elif ctx.gpu and vendor == "none":
            install_gpu_stack(ctx.cfg, vendor, ctx.dry_run)
        elif ctx.gpu:
            console.warn(f"GPU SDK auto-install for '{vendor}' is only "
                         f"automated on apt; install it manually on {mgr.name}.")

        if vendor != "none":
            provision_adapters_for_run(ctx)
        return StepResult.OK if ok else StepResult.FAILED

    # -- Windows -------------------------------------------------------------- #

    def _run_windows(self, ctx: InstallContext) -> StepResult:
        refresh_windows_path()  # see cmake/git the bootstrap script just installed
        winget = self._manager("winget")
        direct = self._manager("direct-download")
        vcpkg  = self._manager("vcpkg")

        tool_ok = self._install_portable_tools(ctx, direct)
        tool_ok = self._install_git(ctx, winget, direct) and tool_ok

        ports, lib_ok = self._install_vcpkg_ports(ctx, vcpkg)
        if lib_ok is None:  # vcpkg required but missing
            return StepResult.FAILED

        tool_ok = self._install_vs_build_tools(ctx, winget) and tool_ok

        # Lean SYCL toolchains (intel-llvm bundle + AdaptiveCpp), like the
        # Dockerfile's default. oneAPI is installed below only with --oneapi.
        self._install_toolchains(ctx, mgr=None, vcpkg=vcpkg)

        # GPU compute SDK, chosen by the detected vendor, then its adapter build.
        if ctx.gpu:
            vendor = _resolve_gpu_vendor(ctx)
            install_gpu_stack(ctx.cfg, vendor, ctx.dry_run)
            if vendor != "none":
                provision_adapters_for_run(ctx)

        tool_ok = self._install_oneapi(ctx) and tool_ok

        return StepResult.OK if (tool_ok and lib_ok) else StepResult.FAILED

    def _install_portable_tools(self, ctx: InstallContext,
                                direct: IPackageManager | None) -> bool:
        """cmake/ninja/doxygen: always portable into the deps folder, never winget.

        Keeps the whole install one deletable directory. The direct-download
        manager extracts them under deps/tools and skips anything already on PATH.
        """
        portable = ["Kitware.CMake", "Ninja-build.Ninja", "DimitriVanHeesch.Doxygen"]
        missing = [pkg for pkg in portable if not shutil.which(WINGET_ID_TO_CMD.get(pkg, ""))]
        if missing and direct:
            console.info("Installing CMake, Ninja, and Doxygen portably into the deps folder ...")
            return direct.install(missing, ctx.dry_run)
        if not missing:
            console.info("cmake + ninja + doxygen already present, skipping.")
        return True

    def _install_git(self, ctx: InstallContext, winget: IPackageManager | None,
                     direct: IPackageManager | None) -> bool:
        """git is a bootstrap prerequisite (clones the repo and acpp) — stays system-wide."""
        if shutil.which("git"):
            return True
        if winget and winget.available():
            console.info("Installing git via winget ...")
            return winget.install(["Git.Git"], ctx.dry_run)
        if direct:
            return direct.install(["Git.Git"], ctx.dry_run)
        console.warn("git not found and no installer available; install it manually.")
        return True

    def _install_vcpkg_ports(self, ctx: InstallContext,
                             vcpkg: IPackageManager | None) -> tuple[list[str], bool | None]:
        """Install the manifest's C++ library ports via vcpkg.

        Returns ``(ports, ok)``; ``ok`` is ``None`` if ports were needed but
        vcpkg itself is missing, distinct from ``False`` (vcpkg ran and failed).
        """
        ports: list[str] = []
        for dep in self._source.selected("windows", ctx.gpu):
            if vcpkg and _dep_installed(dep, vcpkg, "windows"):
                console.info(f"{dep.name}: already installed, skipping.")
                continue
            ports.extend(dep.windows_vcpkg)
        ports = _dedup(ports)

        if not ports:
            return ports, True
        if vcpkg is None:
            console.error("vcpkg manager missing; cannot install C++ libs.")
            return ports, None
        console.info(f"Installing via vcpkg: {', '.join(ports)}")
        ok = vcpkg.install(ports, ctx.dry_run)
        ctx.installed.extend(ports)
        return ports, ok

    def _install_vs_build_tools(self, ctx: InstallContext,
                                winget: IPackageManager | None) -> bool:
        """Visual Studio 2022 Build Tools (C++ workload) — only if winget is present."""
        if not (winget and winget.available()):
            return True
        if winget.is_installed("Microsoft.VisualStudio.2022.BuildTools"):
            return True
        if ctx.dry_run:
            console.info("(dry-run) skipping VS Build Tools install.")
            return True

        vs_cmd = [
            "winget", "install",
            "--id", "Microsoft.VisualStudio.2022.BuildTools", "-e",
            "--accept-package-agreements", "--accept-source-agreements",
            "--override",
            "--add Microsoft.VisualStudio.Workload.VCTools "
            "--includeRecommended --quiet --wait --norestart",
        ]
        with console.console.status(
            "[header]Installing Visual Studio Build Tools "
            "(C++ workloads) — this may take 10–20 minutes.",
            spinner="bouncingBar",
        ):
            rc = subprocess.run(vs_cmd).returncode
        if rc != 0:
            console.warn("Visual Studio Build Tools install failed or was cancelled.")
            return False
        console.success("Visual Studio Build Tools installed.")
        return True

    def _install_oneapi(self, ctx: InstallContext) -> bool:
        """Intel oneAPI DPC++ — opt-in (``--oneapi``), skipped if icx-cl is already present."""
        if not (ctx.oneapi and not ctx.detected.get("sycl_compiler", False)):
            return True
        if ctx.dry_run:
            console.info("(dry-run) skipping Intel oneAPI install.")
            return True

        installer = self._download_oneapi_installer()
        if installer is None:
            return False
        return self._run_oneapi_installer(installer)

    def _download_oneapi_installer(self) -> Path | None:
        oneapi_url = (
            "https://registrationcenter-download.intel.com/akdlm/IRC_NAS/"
            "bae85ab1-cfcd-4251-8d42-a0c27949ea33/"
            "intel-oneapi-toolkit-2026.0.0.193_offline.exe"
        )
        installer = Path.home() / "intel-oneapi-toolkit-offline.exe"
        if installer.is_file():
            return installer
        console.info("Downloading Intel oneAPI Installer (~4 GB) from Intel servers ...")
        dl_rc = subprocess.run(["curl", "-L", "-o", str(installer), oneapi_url]).returncode
        if dl_rc != 0:
            console.error("Failed to download Intel oneAPI installer.")
            return None
        return installer

    def _run_oneapi_installer(self, installer: Path) -> bool:
        oneapi_cmd = [
            str(installer), "-s", "-a", "--silent", "--eula", "accept",
            "-p=NEED_VS2022_INTEGRATION=1",
        ]
        with console.console.status(
            "[header]Installing Intel oneAPI Toolkit silently "
            "— this may take 10–20 minutes.",
            spinner="bouncingBar",
        ):
            try:
                rc = subprocess.run(oneapi_cmd).returncode
            except OSError as exc:
                if getattr(exc, "winerror", None) != 740:
                    console.warn(f"Intel oneAPI installer failed to launch: {exc}")
                    return False
                console.info(
                    "Intel oneAPI requires administrator privileges. "
                    "A UAC prompt will appear — approve it to continue."
                )
                try:
                    ps_cmd = (
                        f"$p = Start-Process -FilePath '{str(installer)}'"
                        f" -ArgumentList '-s','-a','--silent','--eula','accept'"
                        f",'-p=NEED_VS2022_INTEGRATION=1'"
                        f" -Verb RunAs -Wait -PassThru; exit $p.ExitCode"
                    )
                    rc = subprocess.run(
                        ["powershell", "-Command", ps_cmd], timeout=1200,
                    ).returncode
                except Exception as exc2:
                    console.error(f"Elevated oneAPI launch failed: {exc2}")
                    return False
        if rc != 0:
            console.warn("Intel oneAPI Toolkit installation failed.")
            return False
        console.success("Intel oneAPI Toolkit installed.")
        return True


class ConfigureStep(Step):
    """Probe installed tools and write ``config.local.toml``."""

    name = "configure"

    def run(self, ctx: InstallContext) -> StepResult:
        from ..config import set_toolchain

        refresh_windows_path()  # probe needs to see freshly-installed tools
        values = probe.resolve_local_config(ctx.cfg, gpu=ctx.gpu)
        ctx.resolved_paths = values

        target = config_dir() / "config.local.toml"

        if ctx.dry_run:
            if ctx.active_toolchain:
                console.info(f"(dry-run) would set active toolchain to "
                             f"'{ctx.active_toolchain}'.")
            if values:
                console.info(f"(dry-run) would write {target}:")
                console.console.print(
                    probe.render_local_config(ctx.cfg.platform, values), markup=False)
            return StepResult.OK

        if not values and not ctx.active_toolchain:
            console.info("No machine-specific paths to write; defaults suffice.")
            return StepResult.SKIPPED

        if values:
            content = probe.render_local_config(ctx.cfg.platform, values)
            if target.is_file():
                backup = target.with_suffix(".toml.bak")
                shutil.copyfile(target, backup)
                console.info(f"Backed up existing config to {backup.name}")
            target.write_text(content, encoding="utf-8")
            console.success(f"Wrote {target}")

        # Pin the profile's toolchain last: set_toolchain rewrites the file while
        # preserving the [tool.<platform>] table just written above.
        if ctx.active_toolchain:
            set_toolchain(ctx.active_toolchain)
            console.success(f"Active SYCL toolchain set to '{ctx.active_toolchain}'.")
        return StepResult.OK


class VerifyStep(Step):
    """Build and smoke-test through the existing project service."""

    name = "verify"

    def run(self, ctx: InstallContext) -> StepResult:
        if ctx.dry_run:
            console.info("(dry-run) skipping build/verify.")
            return StepResult.SKIPPED

        from ..services import project as project_svc
        from ..services.project import BuildType, Suite

        no_cuda = not ctx.gpu and ctx.cfg.platform != "windows"
        rc = project_svc.build(BuildType.release, distributed=False,
                               no_cuda=no_cuda, clean=False)
        if rc != 0:
            console.error("Build failed during verification.")
            return StepResult.FAILED

        rc = project_svc.test(Suite.functional, distributed=False,
                              filter=None, asan=False, repeat=0)
        if rc != 0:
            console.warn("Functional smoke test reported failures.")
            return StepResult.FAILED

        console.success("Build + smoke test passed. Project is ready.")
        return StepResult.OK


class UninstallStep(Step):
    """Remove packages and files that the installer placed on this system.

    With ``ctx.everything`` set, also removes toolchain binaries (cmake, git,
    ninja) that were downloaded by the direct-download manager. This is a
    destructive operation and cannot be undone automatically.
    """

    name = "uninstall"

    def __init__(self, source: IDependencySource,
                 managers: list[IPackageManager]) -> None:
        self._source = source
        self._managers = managers

    def _manager(self, name: str) -> IPackageManager | None:
        for m in self._managers:
            if m.name == name:
                return m
        return None

    def run(self, ctx: InstallContext) -> StepResult:
        if ctx.cfg.platform == "windows":
            return self._run_windows(ctx)
        return self._run_linux(ctx)

    def _run_linux(self, ctx: InstallContext) -> StepResult:
        linux_names = ["apt", "dnf", "yum", "pacman", "zypper"]
        mgr = next(
            (self._manager(n) for n in linux_names
             if self._manager(n) and self._manager(n).available()),  # type: ignore[union-attr]
            None,
        )
        assert mgr is None or isinstance(mgr, LinuxPackageManager)  # linux_names only holds these
        vcpkg = self._manager("vcpkg")
        pkgs: list[str] = []
        vcpkg_ports: list[str] = []
        for dep in self._source.selected("linux", ctx.gpu):
            pkgs.extend(mgr.translate_apt(dep.linux_apt) if mgr else dep.linux_apt)
            vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))
        pkgs = _dedup(pkgs)
        vcpkg_ports = _dedup(vcpkg_ports)

        if mgr and pkgs:
            console.info(f"Removing via {mgr.name}: {', '.join(pkgs)}")
            mgr.remove(pkgs, ctx.dry_run)

        if vcpkg and vcpkg_ports:
            console.info(f"Removing vcpkg ports: {', '.join(vcpkg_ports)}")
            vcpkg.remove(vcpkg_ports, ctx.dry_run)

        if ctx.everything:
            self._remove_installed_toolchains(ctx)
        self._remove_config(ctx)
        return StepResult.OK

    def _run_windows(self, ctx: InstallContext) -> StepResult:
        vcpkg = self._manager("vcpkg")

        ports: list[str] = []
        for dep in self._source.selected("windows", ctx.gpu):
            ports.extend(dep.windows_vcpkg)
        ports = _dedup(ports)

        if vcpkg and ports:
            console.info(f"Removing vcpkg ports: {', '.join(ports)}")
            vcpkg.remove(ports, ctx.dry_run)

        # Remove the ninja binary and portable cmake we extracted to the tools dir.
        tools = _tools_dir()
        ninja_exe = tools / "ninja.exe"
        if ninja_exe.is_file():
            if ctx.dry_run:
                console.info(f"(dry-run) would remove {ninja_exe}")
            else:
                ninja_exe.unlink()
                console.info(f"Removed {ninja_exe}")
        cmake_dir = tools / "cmake"
        if cmake_dir.is_dir():
            if ctx.dry_run:
                console.info(f"(dry-run) would remove {cmake_dir}")
            else:
                shutil.rmtree(cmake_dir, ignore_errors=True)
                console.info(f"Removed {cmake_dir}")
        doxygen_dir = tools / "doxygen"
        if doxygen_dir.is_dir():
            if ctx.dry_run:
                console.info(f"(dry-run) would remove {doxygen_dir}")
            else:
                shutil.rmtree(doxygen_dir, ignore_errors=True)
                console.info(f"Removed {doxygen_dir}")
        if tools.is_dir() and not any(tools.iterdir()) and not ctx.dry_run:
            tools.rmdir()

        if ctx.everything:
            # Wipe the whole shared dependency tree (portable cmake/ninja, the
            # SYCL toolchains, and vcpkg all live there). We deliberately do NOT
            # touch the system git/cmake the bootstrap installer may have placed —
            # those are the user's, not part of the dependencies/ tree.
            self._remove_installed_toolchains(ctx)

        self._remove_config(ctx)
        return StepResult.OK

    def _remove_installed_toolchains(self, ctx: InstallContext) -> None:
        """Delete the entire vendored deps folder (the one-folder install).

        Everything `sr setup` downloads — the intel/llvm bundle (~1 GB),
        AdaptiveCpp, portable cmake/ninja, and the vcpkg tree — lives under one
        directory, so ``--everything`` reclaims it all in a single rmtree. Only
        done with ``--everything`` since it is the heaviest, least-reversible part.
        """
        from ..config import deps_dir
        dep_dir = deps_dir()
        if not dep_dir.is_dir():
            return
        if ctx.dry_run:
            console.info(f"(dry-run) would remove the whole deps folder at {dep_dir}")
            return
        shutil.rmtree(dep_dir, ignore_errors=True)
        console.success(f"Removed the vendored deps folder at {dep_dir}")

    def _remove_config(self, ctx: InstallContext) -> None:
        target = config_dir() / "config.local.toml"
        if target.is_file():
            if ctx.dry_run:
                console.info(f"(dry-run) would remove {target}")
            else:
                target.unlink()
                console.success(f"Removed {target}")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
