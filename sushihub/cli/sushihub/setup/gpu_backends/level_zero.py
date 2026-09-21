"""The Level Zero backend: Intel's GPU compute stack, located on Linux.

No Windows install of this stack exists for this project's toolchain, so the
Windows side reports "not provided" rather than pretending to look.
"""

from __future__ import annotations

import ctypes.util
import pathlib
import typing

from ... import console
from ..apt import ensure_intel_oneapi_repo, is_root, sudo_bash
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall

if typing.TYPE_CHECKING:
    from ...config import Config

# Checked when ctypes.util.find_library misses, e.g. under a linker cache that
# has not been refreshed since the loader was installed.
_ZE_LOADER_LIB_DIRS = (
    "/usr/lib/x86_64-linux-gnu",
    "/usr/lib64",
    "/usr/lib",
)
_ZE_LOADER_GLOB = "libze_loader.so*"


def _find_ze_loader() -> pathlib.Path | None:
    """Return the directory holding libze_loader, or None when it is absent.

    ``find_library`` names are always POSIX paths (this locator only ever
    runs on Linux), so parsing goes through :class:`pathlib.PurePosixPath`
    rather than :class:`pathlib.Path`, whose flavour follows the host OS.
    """
    found = ctypes.util.find_library("ze_loader")
    if found:
        path = pathlib.PurePosixPath(found)
        return pathlib.Path(str(path.parent)) if path.is_absolute() else pathlib.Path("/usr/lib")
    for directory in _ZE_LOADER_LIB_DIRS:
        if next(pathlib.Path(directory).glob(_ZE_LOADER_GLOB), None) is not None:
            return pathlib.Path(directory)
    return None


class LinuxLevelZeroLocator:
    """Finds and installs the Intel GPU compute stack (Level Zero + OpenCL)."""

    def locate(self, cfg: "Config") -> ToolkitInstall | None:
        """Return the directory holding the Level Zero loader, or None.

        Level Zero names no toolkit root the way ``CUDA_PATH`` does; the loader
        is a shared library reached through the linker, not a directory the
        adapter build needs to be told about (its ``adapter_definitions`` is
        empty for exactly this reason). This still reports an install once the
        loader is found, so the caller has something to name as present.
        """
        directory = _find_ze_loader()
        if directory is None:
            return None
        return ToolkitInstall(root=directory, version=None)

    def provision(self, cfg: "Config", dry_run: bool) -> bool:
        """Install the Intel GPU compute stack (Level Zero + OpenCL) for Intel GPUs.

        The oneAPI apt repo (configured by :func:`ensure_intel_oneapi_repo`) ships the
        Level Zero loader; install it plus the Intel GPU OpenCL runtime so an Intel
        GPU is exposed as a SYCL device. Best-effort / non-fatal.
        """
        if not ensure_intel_oneapi_repo(dry_run):
            return False
        sudo = "" if is_root() else "sudo "
        steps = (
            f"{sudo}apt-get update && "
            f"{sudo}apt-get install -y level-zero intel-oneapi-runtime-opencl "
            f"intel-oneapi-runtime-libs"
        )
        if not sudo_bash(steps, dry_run):
            console.warn("Intel GPU runtime install failed; the build will fall back "
                         "to the CPU/OpenCL path.")
            return False
        return True


LEVEL_ZERO = GpuBackendSpec(
    vendor="level_zero",
    probe_vendor="intel",
    locator=PlatformLocator("Level Zero", {
        "linux": LinuxLevelZeroLocator(),
    }),
    adapter_option="UR_BUILD_ADAPTER_L0",
    adapter_definitions=lambda install: {},
    adapter_target="ur_adapter_level_zero",
    adapter_binaries=("ur_adapter_level_zero", "umf"),
)
