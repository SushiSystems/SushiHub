"""``provision_gpu_adapters`` reads one commit and drives one build per located backend."""

from __future__ import annotations

import pathlib

import pytest

from sushistack.config import Config
from sushistack.setup import steps as steps_mod
from sushistack.setup.gpu_backends.backend import GpuBackendSpec, ToolkitInstall
from sushistack.setup.gpu_backends.provisioning import provision_gpu_adapters
from sushistack.setup.gpu_backends.registry import Registry
from sushistack.setup.package_managers import LinuxPackageManager
from sushistack.setup.pipeline import InstallContext, StepResult
from sushistack.setup.steps import InstallDepsStep, provision_adapters_for_run

from .conftest import MemorySource

_COMMIT = "d5f649b706f63b5c74e1929bc95db8de91085560"


@pytest.fixture(autouse=True)
def _plain_console():
    """Force the human-readable console renderer for every test in this file.

    ``sushistack.console`` builds one console lazily and keeps it for the
    process; a test elsewhere that switches it to the JSON renderer leaves
    that choice in place for every test that runs after it. Resetting it here
    keeps this file's console assertions independent of test order.
    """
    from sushistack import console
    console.set_machine(False)
    yield


class _FakeLocator:
    """Reports a fixed install, or none, for one backend."""

    def __init__(self, install: ToolkitInstall | None) -> None:
        """Store the install this locator always reports."""
        self._install = install

    def locate(self, cfg) -> ToolkitInstall | None:
        """Return the stored install."""
        return self._install

    def provision(self, cfg, dry_run: bool) -> bool:  # pragma: no cover - unused here
        """Never called by provisioning; present only to satisfy the protocol."""
        return True


def _spec(vendor: str, install: ToolkitInstall | None) -> GpuBackendSpec:
    """Build one GpuBackendSpec whose locator reports *install*."""
    return GpuBackendSpec(
        vendor=vendor,
        probe_vendor=f"{vendor}vendor",
        locator=_FakeLocator(install),
        adapter_option=f"UR_BUILD_ADAPTER_{vendor.upper()}",
        adapter_definitions=lambda install: {},
        adapter_target=f"ur_adapter_{vendor}",
        adapter_binaries=(f"ur_adapter_{vendor}",),
    )


class _FakeBuilder:
    """Records every spec it was asked to build and reports a fixed outcome per vendor."""

    def __init__(self, outcomes: dict[str, bool]) -> None:
        """Store which vendor's build should succeed or fail."""
        self._outcomes = outcomes
        self.built: list[str] = []

    def build(self, spec, install, toolchain_root, commit, dry_run) -> bool:
        """Record the call and return the outcome configured for this vendor."""
        self.built.append(spec.vendor)
        return self._outcomes.get(spec.vendor, True)


def _cfg() -> Config:
    """A Linux configuration; the commit reader is faked, so no real clang++ runs."""
    return Config(platform="linux")


def test_a_missing_commit_builds_nothing(tmp_path):
    registry = Registry((_spec("cuda", ToolkitInstall(root=tmp_path, version=None)),))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: None,
    )

    assert builder.built == []


def test_a_backend_with_no_located_toolkit_is_skipped(tmp_path):
    registry = Registry((
        _spec("cuda", None),
        _spec("rocm", ToolkitInstall(root=tmp_path, version=None)),
    ))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: _COMMIT,
    )

    assert builder.built == ["rocm"]


def test_one_built_and_one_failed_are_both_called_and_neither_raises(tmp_path, capsys):
    registry = Registry((
        _spec("cuda", ToolkitInstall(root=tmp_path, version=None)),
        _spec("rocm", ToolkitInstall(root=tmp_path, version=None)),
    ))
    builder = _FakeBuilder({"cuda": True, "rocm": False})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: _COMMIT,
    )

    assert builder.built == ["cuda", "rocm"]
    assert capsys.readouterr().out == ""


def test_a_locator_that_raises_is_swallowed_and_warned(tmp_path, capsys):
    class _BrokenLocator:
        def locate(self, cfg):
            raise OSError("disk unreadable")

    spec = GpuBackendSpec(
        vendor="cuda", probe_vendor="nvidia", locator=_BrokenLocator(),
        adapter_option="UR_BUILD_ADAPTER_CUDA", adapter_definitions=lambda install: {},
        adapter_target="ur_adapter_cuda", adapter_binaries=("ur_adapter_cuda",),
    )
    registry = Registry((spec,))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: _COMMIT,
    )

    assert builder.built == []
    out = capsys.readouterr().out
    assert "GPU adapter provisioning failed" in out
    assert "OSError" in out
    assert "disk unreadable" in out


def test_a_missing_commit_warns(tmp_path, capsys):
    registry = Registry((_spec("cuda", ToolkitInstall(root=tmp_path, version=None)),))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: None,
    )

    assert builder.built == []
    assert "Could not read the intel/llvm commit" in capsys.readouterr().out


def test_a_missing_commit_in_dry_run_prints_the_dry_run_line_instead_of_a_warning(
        tmp_path, capsys):
    registry = Registry((_spec("cuda", ToolkitInstall(root=tmp_path, version=None)),))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=True,
        commit_reader=lambda path: None,
    )

    out = capsys.readouterr().out
    assert "would read the compiler commit" in out
    assert "Could not read" not in out


# --------------------------------------------------------------------------- #
# steps.py: both platforms call the one extracted function with the installed
# root, so it is proved once here rather than through two full pipeline runs.
# --------------------------------------------------------------------------- #

def test_provision_adapters_for_run_skips_without_a_resolved_llvm_root(monkeypatch, capsys):
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(
        "sushistack.setup.steps.provision_gpu_adapters",
        lambda cfg, registry, root, builder, dry_run: calls.append(root),
    )
    ctx = InstallContext(cfg=Config(platform="linux"))

    provision_adapters_for_run(ctx)

    assert calls == []
    assert "GPU adapter build skipped" in capsys.readouterr().out


def test_provision_adapters_for_run_uses_the_resolved_llvm_root(monkeypatch, tmp_path):
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(
        "sushistack.setup.steps.provision_gpu_adapters",
        lambda cfg, registry, root, builder, dry_run: calls.append(root),
    )
    ctx = InstallContext(cfg=Config(platform="linux"))
    ctx.resolved_paths["llvm_root"] = str(tmp_path)

    provision_adapters_for_run(ctx)

    assert calls == [tmp_path]


# --------------------------------------------------------------------------- #
# Both platform install steps must reach `provision_adapters_for_run`, and only
# when `ctx.gpu` is set. The heavy sub-steps (tools, vcpkg, toolchains, oneAPI)
# are monkeypatched, following the pattern the rest of this file uses for
# `provision_gpu_adapters` itself.
# --------------------------------------------------------------------------- #

class _FakeAptManager(LinuxPackageManager):
    """An always-available apt manager that installs nothing for real."""

    name = "apt"

    def available(self) -> bool:
        """Report present, unconditionally."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report every package as already installed."""
        return True

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Record no work and report success."""
        return True


def _patch_heavy_windows_steps(monkeypatch, llvm_root: str) -> None:
    """Stub every Windows sub-step except the GPU block, and mark the toolchain resolved."""
    monkeypatch.setattr(InstallDepsStep, "_install_portable_tools",
                        lambda self, ctx, direct: True)
    monkeypatch.setattr(InstallDepsStep, "_install_git",
                        lambda self, ctx, winget, direct: True)
    monkeypatch.setattr(InstallDepsStep, "_install_vcpkg_ports",
                        lambda self, ctx, vcpkg: ([], True))
    monkeypatch.setattr(InstallDepsStep, "_install_vs_build_tools",
                        lambda self, ctx, winget: True)
    monkeypatch.setattr(InstallDepsStep, "_install_toolchains",
                        lambda self, ctx, mgr, vcpkg: ctx.resolved_paths.update(
                            {"llvm_root": llvm_root}))
    monkeypatch.setattr(InstallDepsStep, "_install_oneapi", lambda self, ctx: True)
    monkeypatch.setattr(steps_mod, "install_gpu_stack", lambda cfg, vendor, dry_run: True)
    monkeypatch.setattr(steps_mod.probe, "detect_gpu_vendor", lambda: "nvidia")


def test_run_windows_reaches_provision_adapters_for_run_when_gpu_is_selected(
        monkeypatch, tmp_path):
    _patch_heavy_windows_steps(monkeypatch, str(tmp_path))
    calls: list[InstallContext] = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource([]), managers=[])
    ctx = InstallContext(cfg=Config(platform="windows"), gpu=True)

    result = step._run_windows(ctx)

    assert result is StepResult.OK
    assert calls == [ctx]


def test_run_windows_skips_provision_adapters_for_run_without_gpu(monkeypatch, tmp_path):
    _patch_heavy_windows_steps(monkeypatch, str(tmp_path))
    calls: list[InstallContext] = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource([]), managers=[])
    ctx = InstallContext(cfg=Config(platform="windows"), gpu=False)

    step._run_windows(ctx)

    assert calls == []


def _patch_heavy_linux_steps(monkeypatch, llvm_root: str) -> None:
    """Stub the toolchain install so `ctx.resolved_paths["llvm_root"]` is set."""
    monkeypatch.setattr(InstallDepsStep, "_install_toolchains",
                        lambda self, ctx, mgr, vcpkg: ctx.resolved_paths.update(
                            {"llvm_root": llvm_root}))
    monkeypatch.setattr(steps_mod, "install_gpu_stack", lambda cfg, vendor, dry_run: True)
    monkeypatch.setattr(steps_mod.probe, "detect_gpu_vendor", lambda: "nvidia")


def test_run_linux_reaches_provision_adapters_for_run_when_gpu_is_selected(
        monkeypatch, tmp_path):
    _patch_heavy_linux_steps(monkeypatch, str(tmp_path))
    calls: list[InstallContext] = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource([]), managers=[_FakeAptManager()])
    ctx = InstallContext(cfg=Config(platform="linux"), gpu=True)

    result = step._run_linux(ctx)

    assert result is StepResult.OK
    assert calls == [ctx]


def test_run_linux_skips_provision_adapters_for_run_without_gpu(monkeypatch, tmp_path):
    _patch_heavy_linux_steps(monkeypatch, str(tmp_path))
    calls: list[InstallContext] = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource([]), managers=[_FakeAptManager()])
    ctx = InstallContext(cfg=Config(platform="linux"), gpu=False)

    step._run_linux(ctx)

    assert calls == []
