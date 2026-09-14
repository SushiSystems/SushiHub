"""The CUDA backend: NVIDIA's toolkit, located and provisioned per platform.

The Linux locator carries today's apt install code unchanged in behaviour. The
Windows locator only ever reports what it finds; it never installs, because no
silent, unattended CUDA installer exists for Windows.
"""

from __future__ import annotations

import glob
import os
import pathlib
import shutil
import typing

from ... import console
from .. import probe
from ..apt import is_root, os_release, sudo_bash
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall

if typing.TYPE_CHECKING:
    from ...config import Config

# Mirrors probe.py's own glob list: neither the apt CUDA toolkit nor a manual
# install adds itself to PATH, so a fresh machine needs these well-known roots
# checked directly.
_NVCC_GLOBS_LINUX = [
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
]

# Ubuntu tag ceiling for NVIDIA's CUDA 12.6 apt repo. See
# docs/reference/KNOWN_ISSUES.md, "Raising the CUDA pin above 12.6 breaks
# Pascal builds far from the cause".
_CUDA126_MAX_UBUNTU_TAG = "ubuntu2404"


def _apt_distro_tag() -> str:
    """NVIDIA/ROCm-style distro tag for repo URLs, e.g. 'ubuntu2204'. '' if unknown."""
    rel = os_release()
    idv = rel.get("ID", "").lower()
    ver = rel.get("VERSION_ID", "").replace(".", "")
    if idv in ("ubuntu", "debian") and ver:
        return f"{idv}{ver}"
    return ""


def _cuda_repo_tag() -> str:
    """Distro tag for NVIDIA's CUDA apt repo, clamped to one that ships 12.6.

    Returns '' if the distro is unrecognised. For Ubuntu releases newer than the
    last one with cuda-toolkit-12-6 published, fall back to that release's repo.
    """
    tag = _apt_distro_tag()
    if not tag:
        return ""
    if tag.startswith("ubuntu"):
        try:
            ver = int(tag[len("ubuntu"):])
        except ValueError:
            return tag
        if ver > int(_CUDA126_MAX_UBUNTU_TAG[len("ubuntu"):]):
            console.info(f"NVIDIA has no CUDA 12.6 repo for {tag}; using "
                         f"{_CUDA126_MAX_UBUNTU_TAG} (Pascal-capable, runs on newer Ubuntu).")
            return _CUDA126_MAX_UBUNTU_TAG
    return tag


class LinuxCudaLocator:
    """Finds and installs the CUDA toolkit from NVIDIA's official apt repo."""

    def locate(self, cfg: "Config") -> ToolkitInstall | None:
        """Return the CUDA toolkit root found via PATH or a well-known glob."""
        nvcc = shutil.which("nvcc") or self._glob_nvcc()
        if not nvcc:
            return None
        root = pathlib.Path(nvcc).resolve().parent.parent
        return ToolkitInstall(root=root, version=None)

    def _glob_nvcc(self) -> str:
        """Return the newest nvcc found under the well-known CUDA install globs."""
        for pattern in _NVCC_GLOBS_LINUX:
            hits = sorted(glob.glob(pattern))
            if hits:
                return hits[-1]
        return ""

    def provision(self, cfg: "Config", dry_run: bool) -> bool:
        """Install the pinned NVIDIA CUDA toolkit from NVIDIA's official apt repo.

        Adds NVIDIA's ``cuda-keyring`` network repo and installs the pinned
        ``cuda-toolkit-12-6`` package, not the unversioned ``cuda-toolkit``
        meta-package. See docs/reference/KNOWN_ISSUES.md, "Raising the CUDA
        pin above 12.6 breaks Pascal builds far from the cause", for why the
        pin and the Ubuntu tag clamp both exist. Best-effort and non-fatal.
        """
        if probe.binary_works("nvcc"):
            console.info("CUDA toolkit already present (nvcc found).")
            return True
        tag = _cuda_repo_tag()
        if not tag:
            console.warn("Unrecognised distro for the NVIDIA CUDA repo; install the "
                         "CUDA 12.x toolkit manually (https://developer.nvidia.com/cuda-downloads).")
            return False
        sudo = "" if is_root() else "sudo "
        keyring_url = (f"https://developer.download.nvidia.com/compute/cuda/repos/"
                       f"{tag}/x86_64/cuda-keyring_1.1-1_all.deb")
        steps = (
            f"tmp=$(mktemp -d) && cd \"$tmp\" && "
            f"curl -fsSLO {keyring_url} && "
            f"{sudo}dpkg -i cuda-keyring_1.1-1_all.deb && "
            f"{sudo}apt-get update && "
            f"{sudo}apt-get install -y cuda-toolkit-12-6"
        )
        if not sudo_bash(steps, dry_run):
            console.warn("CUDA toolkit install failed. Install CUDA 12.x manually "
                         "(https://developer.nvidia.com/cuda-downloads); the build will "
                         "otherwise fall back to the CPU/OpenCL path.")
            return False
        return True


class WindowsCudaLocator:
    """Reads the CUDA toolkit already installed by NVIDIA's own Windows installer."""

    def locate(self, cfg: "Config") -> ToolkitInstall | None:
        """Return the toolkit root from CUDA_PATH, when bin/nvcc.exe exists there."""
        raw = os.environ.get("CUDA_PATH", "")
        if not raw:
            return None
        root = pathlib.Path(os.path.normpath(raw))
        if not (root / "bin" / "nvcc.exe").is_file():
            return None
        return ToolkitInstall(root=root, version=None)

    def provision(self, cfg: "Config", dry_run: bool) -> bool:
        """Report an existing install, or print manual install instructions.

        No CUDA installer for Windows runs unattended, so this backend never
        installs anything there. It always returns True: per the design's failure
        section, an absent toolkit here is an ordinary outcome, not a failure.
        """
        found = self.locate(cfg)
        if found is not None:
            console.info(f"CUDA toolkit already present at {found.root}.")
            return True
        console.warn("CUDA toolkit not found. Install CUDA Toolkit 12.6 from NVIDIA's "
                     "archive (https://developer.nvidia.com/cuda-12-6-0-download-archive) "
                     "as administrator.")
        return True


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the CUDA toolkit root to the Unified Runtime CUDA adapter build."""
    return {"CUDAToolkit_ROOT": str(install.root)}


CUDA = GpuBackendSpec(
    vendor="cuda",
    probe_vendor="nvidia",
    locator=PlatformLocator("CUDA", {
        "linux": LinuxCudaLocator(),
        "windows": WindowsCudaLocator(),
    }),
    adapter_option="UR_BUILD_ADAPTER_CUDA",
    adapter_definitions=_adapter_definitions,
    adapter_target="ur_adapter_cuda",
    adapter_binaries=("ur_adapter_cuda", "umf"),
)
