"""Each vendor's spec answers the contract; Windows CUDA locates from CUDA_PATH."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from sushistack.setup import apt as apt_mod
from sushistack.setup import package_managers
from sushistack.setup.gpu_backends import cuda as cuda_mod
from sushistack.setup.gpu_backends import level_zero as level_zero_mod
from sushistack.setup.gpu_backends import rocm as rocm_mod
from sushistack.setup.gpu_backends import windows_installer
from sushistack.setup.gpu_backends.backend import NotProvided, ToolkitInstall
from sushistack.setup.gpu_backends.cuda import CUDA
from sushistack.setup.gpu_backends.level_zero import LEVEL_ZERO
from sushistack.setup.gpu_backends.registry import Registry
from sushistack.setup.gpu_backends.rocm import ROCM


# --------------------------------------------------------------------------- #
# CUDA
# --------------------------------------------------------------------------- #

def test_cuda_spec_declares_the_adapter_build_inputs():
    assert CUDA.vendor == "cuda"
    assert CUDA.probe_vendor == "nvidia"
    assert CUDA.adapter_option == "UR_BUILD_ADAPTER_CUDA"
    assert CUDA.adapter_target == "ur_adapter_cuda"
    assert CUDA.adapter_binaries == ("ur_adapter_cuda", "umf")
    root = pathlib.Path("/opt/cuda")
    install = ToolkitInstall(root=root, version="12.6")
    assert CUDA.adapter_definitions(install) == {"CUDAToolkit_ROOT": str(root)}


def test_windows_cuda_locator_finds_the_toolkit_from_cuda_path(tmp_path, monkeypatch):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "nvcc.exe").write_text("")
    monkeypatch.setenv("CUDA_PATH", str(tmp_path))
    cfg = SimpleNamespace(platform="windows")

    install = CUDA.locator.locate(cfg)

    assert install == ToolkitInstall(root=pathlib.Path(str(tmp_path)), version=None)


def test_windows_cuda_locator_reports_nothing_without_nvcc_exe(tmp_path, monkeypatch):
    monkeypatch.setattr(windows_installer.RegistryMachineEnvironment, "read",
                        lambda self, name: None)
    monkeypatch.setenv("CUDA_PATH", str(tmp_path))
    cfg = SimpleNamespace(platform="windows")

    assert CUDA.locator.locate(cfg) is None


def test_windows_cuda_locator_reports_nothing_without_cuda_path(monkeypatch):
    monkeypatch.setattr(windows_installer.RegistryMachineEnvironment, "read",
                        lambda self, name: None)
    monkeypatch.delenv("CUDA_PATH", raising=False)
    cfg = SimpleNamespace(platform="windows")

    assert CUDA.locator.locate(cfg) is None


def test_windows_cuda_provision_reports_an_existing_install(tmp_path, monkeypatch):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "nvcc.exe").write_text("")
    monkeypatch.setenv("CUDA_PATH", str(tmp_path))
    cfg = SimpleNamespace(platform="windows")

    assert CUDA.locator.provision(cfg, dry_run=False) is True


def _fake_console(**overrides):
    """Build a console stand-in that records calls instead of touching the real one.

    Rebinding a vendor module's own ``console`` name, rather than patching
    :mod:`sushistack.console` itself, keeps its lazily built Rich console
    (and the stdout it captured at construction) untouched for every other
    test in the process, in particular the CLI's JSON-stream tests.
    """
    base = SimpleNamespace(info=lambda *a, **k: None, warn=lambda *a, **k: None,
                            error=lambda *a, **k: None, command=lambda *a, **k: None)
    for name, fn in overrides.items():
        setattr(base, name, fn)
    return base


def test_linux_cuda_provision_skips_the_install_only_when_nvcc_runs(monkeypatch):
    """I1: the pinned-install decision is HEAD's `binary_works("nvcc")`, not `locate`."""
    calls: list[str] = []
    monkeypatch.setattr(cuda_mod.probe, "binary_works", lambda cmd: cmd == "nvcc")
    monkeypatch.setattr(cuda_mod, "console", _fake_console(info=lambda msg: calls.append(msg)))
    cfg = SimpleNamespace(platform="linux")

    assert cuda_mod.LinuxCudaLocator().provision(cfg, dry_run=True) is True
    assert calls == ["CUDA toolkit already present (nvcc found)."]


def test_linux_cuda_provision_installs_when_nvcc_does_not_run(monkeypatch):
    """A toolkit `locate` can see (a stale /usr/local/cuda-13.0) must not skip
    the pinned 12.6 install: only a working `nvcc` does that.
    """
    commands: list[str] = []
    monkeypatch.setattr(cuda_mod.probe, "binary_works", lambda cmd: False)
    monkeypatch.setattr(
        cuda_mod.LinuxCudaLocator, "locate",
        lambda self, cfg: ToolkitInstall(root=pathlib.Path("/usr/local/cuda-13.0"), version=None),
    )
    monkeypatch.setattr(cuda_mod, "os_release", lambda: {"ID": "ubuntu", "VERSION_ID": "24.04"})
    monkeypatch.setattr(cuda_mod, "is_root", lambda: False)
    monkeypatch.setattr(apt_mod, "console", _fake_console(command=lambda cmd: commands.append(cmd)))

    assert cuda_mod.LinuxCudaLocator().provision(cfg=SimpleNamespace(platform="linux"),
                                                  dry_run=True) is True
    assert commands  # the pinned apt install ran, not skipped


# --------------------------------------------------------------------------- #
# ROCm
# --------------------------------------------------------------------------- #

def test_rocm_spec_declares_the_adapter_build_inputs():
    assert ROCM.vendor == "rocm"
    assert ROCM.probe_vendor == "amd"
    assert ROCM.adapter_option == "UR_BUILD_ADAPTER_HIP"
    assert ROCM.adapter_target == "ur_adapter_hip"
    assert ROCM.adapter_binaries == ("ur_adapter_hip", "umf")
    root = pathlib.Path("/opt/rocm")
    install = ToolkitInstall(root=root, version=None)
    assert ROCM.adapter_definitions(install) == {"UR_HIP_ROCM_DIR": str(root)}


# --------------------------------------------------------------------------- #
# Level Zero
# --------------------------------------------------------------------------- #

def test_level_zero_spec_declares_the_adapter_build_inputs():
    assert LEVEL_ZERO.vendor == "level_zero"
    assert LEVEL_ZERO.probe_vendor == "intel"
    assert LEVEL_ZERO.adapter_option == "UR_BUILD_ADAPTER_L0"
    assert LEVEL_ZERO.adapter_target == "ur_adapter_level_zero"
    assert LEVEL_ZERO.adapter_binaries == ("ur_adapter_level_zero", "umf")
    install = ToolkitInstall(root=pathlib.Path("/usr"), version=None)
    assert LEVEL_ZERO.adapter_definitions(install) == {}


# --------------------------------------------------------------------------- #
# Platform coverage
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("spec", [CUDA, ROCM, LEVEL_ZERO])
def test_every_backend_reports_not_provided_on_darwin(spec):
    cfg = SimpleNamespace(platform="darwin")

    assert spec.locator.locate(cfg) is None
    assert isinstance(spec.locator._for(cfg), NotProvided)
    assert spec.locator.provision(cfg, dry_run=True) is True


# --------------------------------------------------------------------------- #
# install_gpu_stack dispatches through the registry
# --------------------------------------------------------------------------- #

class _RecordingLocator:
    """A locator that records whether it was asked to provision."""

    def __init__(self) -> None:
        """Start with no recorded call."""
        self.provisioned_with: tuple | None = None

    def locate(self, cfg):
        """Report no toolkit; this fake never needs to be found."""
        return None

    def provision(self, cfg, dry_run: bool) -> bool:
        """Record the call and report success."""
        self.provisioned_with = (cfg, dry_run)
        return True


def test_install_gpu_stack_dispatches_through_the_registry(monkeypatch):
    from sushistack.setup.gpu_backends.backend import GpuBackendSpec

    locator = _RecordingLocator()
    fake_spec = GpuBackendSpec(
        vendor="fake",
        probe_vendor="fakevendor",
        locator=locator,
        adapter_option="UR_BUILD_ADAPTER_FAKE",
        adapter_definitions=lambda install: {},
        adapter_target="ur_adapter_fake",
        adapter_binaries=("ur_adapter_fake",),
    )
    fake_registry = Registry((fake_spec,))
    monkeypatch.setattr(package_managers, "DEFAULT_REGISTRY", fake_registry)

    cfg = SimpleNamespace(platform="linux")
    result = package_managers.install_gpu_stack(cfg, "fakevendor", dry_run=True)

    assert result is True
    assert locator.provisioned_with == (cfg, True)


def test_install_gpu_stack_reports_no_gpu_for_an_unregistered_vendor(monkeypatch):
    calls: list[str] = []
    fake_registry = Registry(())
    monkeypatch.setattr(package_managers, "DEFAULT_REGISTRY", fake_registry)
    monkeypatch.setattr(package_managers, "console",
                         _fake_console(info=lambda msg: calls.append(msg)))

    cfg = SimpleNamespace(platform="linux")
    assert package_managers.install_gpu_stack(cfg, "none", dry_run=True) is True
    assert calls == ["No discrete GPU detected; using the CPU (SPIR/OpenCL) path only."]


# --------------------------------------------------------------------------- #
# M2: Linux dry-run commands pinned to HEAD's text
# --------------------------------------------------------------------------- #

def test_cuda_linux_provision_command_matches_head(monkeypatch):
    commands: list[str] = []
    monkeypatch.setattr(cuda_mod.probe, "binary_works", lambda cmd: False)
    monkeypatch.setattr(cuda_mod, "os_release", lambda: {"ID": "ubuntu", "VERSION_ID": "24.04"})
    monkeypatch.setattr(cuda_mod, "is_root", lambda: False)
    monkeypatch.setattr(apt_mod, "console", _fake_console(command=lambda cmd: commands.append(cmd)))

    cfg = SimpleNamespace(platform="linux")
    assert cuda_mod.LinuxCudaLocator().provision(cfg, dry_run=True) is True

    assert commands == [
        "tmp=$(mktemp -d) && cd \"$tmp\" && "
        "curl -fsSLO https://developer.download.nvidia.com/compute/cuda/repos/"
        "ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb && "
        "sudo dpkg -i cuda-keyring_1.1-1_all.deb && "
        "sudo apt-get update && "
        "sudo apt-get install -y cuda-toolkit-12-6"
    ]


def test_rocm_linux_provision_command_matches_head(monkeypatch):
    commands: list[str] = []
    monkeypatch.setattr(rocm_mod.shutil, "which", lambda cmd: None)
    monkeypatch.setattr(rocm_mod, "os_release",
                         lambda: {"ID": "ubuntu", "VERSION_CODENAME": "noble"})
    monkeypatch.setattr(rocm_mod, "is_root", lambda: False)
    monkeypatch.setattr(apt_mod, "console", _fake_console(command=lambda cmd: commands.append(cmd)))

    cfg = SimpleNamespace(platform="linux")
    assert rocm_mod.LinuxRocmLocator().provision(cfg, dry_run=True) is True

    assert commands == [
        "sudo mkdir -p --mode=0755 /etc/apt/keyrings && "
        "curl -fsSL https://repo.radeon.com/rocm/rocm.gpg.key "
        "| sudo gpg --dearmor -o /etc/apt/keyrings/rocm.gpg && "
        'echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] '
        'https://repo.radeon.com/rocm/apt/latest noble main" '
        "| sudo tee /etc/apt/sources.list.d/rocm.list && "
        "sudo apt-get update && "
        "sudo apt-get install -y rocm-hip-runtime-dev"
    ]


def test_level_zero_linux_provision_command_matches_head(monkeypatch):
    commands: list[str] = []
    monkeypatch.setattr(level_zero_mod, "ensure_intel_oneapi_repo", lambda dry_run: True)
    monkeypatch.setattr(level_zero_mod, "is_root", lambda: False)
    monkeypatch.setattr(apt_mod, "console", _fake_console(command=lambda cmd: commands.append(cmd)))

    cfg = SimpleNamespace(platform="linux")
    assert level_zero_mod.LinuxLevelZeroLocator().provision(cfg, dry_run=True) is True

    assert commands == [
        "sudo apt-get update && "
        "sudo apt-get install -y level-zero intel-oneapi-runtime-opencl "
        "intel-oneapi-runtime-libs"
    ]


# --------------------------------------------------------------------------- #
# M3: the Level Zero locator finds a real shared library, not an executable
# --------------------------------------------------------------------------- #

def test_level_zero_locator_finds_the_loader_via_find_library(monkeypatch):
    monkeypatch.setattr(level_zero_mod.ctypes.util, "find_library",
                         lambda name: "/usr/lib/x86_64-linux-gnu/libze_loader.so.1")
    cfg = SimpleNamespace(platform="linux")

    install = LEVEL_ZERO.locator.locate(cfg)

    assert install == ToolkitInstall(
        root=pathlib.Path("/usr/lib/x86_64-linux-gnu"), version=None,
    )


def test_level_zero_locator_falls_back_to_the_known_lib_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(level_zero_mod.ctypes.util, "find_library", lambda name: None)
    fake_dir = tmp_path / "lib"
    fake_dir.mkdir()
    (fake_dir / "libze_loader.so.1").write_text("")
    monkeypatch.setattr(level_zero_mod, "_ZE_LOADER_LIB_DIRS", (str(fake_dir),))
    cfg = SimpleNamespace(platform="linux")

    install = LEVEL_ZERO.locator.locate(cfg)

    assert install == ToolkitInstall(root=fake_dir, version=None)


def test_level_zero_locator_reports_nothing_when_the_loader_is_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(level_zero_mod.ctypes.util, "find_library", lambda name: None)
    monkeypatch.setattr(level_zero_mod, "_ZE_LOADER_LIB_DIRS", (str(tmp_path),))
    cfg = SimpleNamespace(platform="linux")

    assert LEVEL_ZERO.locator.locate(cfg) is None


# --------------------------------------------------------------------------- #
# M4: ROCm reads ROCM_PATH before falling back to /opt/rocm
# --------------------------------------------------------------------------- #

def test_rocm_locator_prefers_rocm_path_over_the_default(monkeypatch):
    monkeypatch.setattr(rocm_mod.shutil, "which", lambda cmd: "/custom/rocm/bin/hipcc")
    monkeypatch.setenv("ROCM_PATH", "/custom/rocm")
    cfg = SimpleNamespace(platform="linux")

    install = ROCM.locator.locate(cfg)

    assert install == ToolkitInstall(root=pathlib.Path("/custom/rocm"), version=None)


def test_rocm_locator_falls_back_to_opt_rocm_without_rocm_path(monkeypatch):
    monkeypatch.setattr(rocm_mod.shutil, "which", lambda cmd: "/usr/bin/hipcc")
    monkeypatch.delenv("ROCM_PATH", raising=False)
    cfg = SimpleNamespace(platform="linux")

    install = ROCM.locator.locate(cfg)

    assert install == ToolkitInstall(root=pathlib.Path("/opt/rocm"), version=None)
