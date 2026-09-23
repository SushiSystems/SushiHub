"""InstallDepsStep reaches `provision_adapters_for_run` only when GPU work is selected.

``provision_gpu_adapters`` itself is tested in sushicore
(``tests/provision/test_gpu_provisioning.py``); this file covers only the
hub-owned wiring in ``steps.py`` that decides when to call it.
"""

from __future__ import annotations

import pathlib

import pytest

from sushihub.config import Config
from sushihub.setup import steps as steps_mod
from sushihub.setup.package_managers import LinuxPackageManager
from sushihub.setup.package_managers import install_gpu_stack as _real_install_gpu_stack
from sushihub.setup.pipeline import InstallContext, StepResult
from sushihub.setup.steps import InstallDepsStep, provision_adapters_for_run

from .conftest import MemorySource


@pytest.fixture(autouse=True)
def _plain_console():
    """Force the human-readable console renderer for every test in this file.

    ``sushihub.console`` builds one console lazily and keeps it for the
    process; a test elsewhere that switches it to the JSON renderer leaves
    that choice in place for every test that runs after it. Resetting it here
    keeps this file's console assertions independent of test order.
    """
    from sushihub import console
    console.set_machine(False)
    yield


def test_provision_adapters_for_run_skips_without_a_resolved_llvm_root(monkeypatch, capsys):
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(
        "sushihub.setup.steps.provision_gpu_adapters",
        lambda cfg, registry, root, builder, dry_run: calls.append(root),
    )
    ctx = InstallContext(cfg=Config(platform="linux"))

    provision_adapters_for_run(ctx)

    assert calls == []
    assert "GPU adapter build skipped" in capsys.readouterr().out


def test_provision_adapters_for_run_uses_the_resolved_llvm_root(monkeypatch, tmp_path):
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(
        "sushihub.setup.steps.provision_gpu_adapters",
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


def test_run_windows_with_no_gpu_provisions_nothing(monkeypatch, tmp_path, capsys):
    _patch_heavy_windows_steps(monkeypatch, str(tmp_path))
    monkeypatch.setattr(steps_mod, "install_gpu_stack", _real_install_gpu_stack)
    calls: list[InstallContext] = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource([]), managers=[])
    ctx = InstallContext(cfg=Config(platform="windows"), gpu=True, gpu_vendor="none")

    step._run_windows(ctx)

    assert calls == []
    assert "No discrete GPU detected" in capsys.readouterr().out


def test_run_linux_with_no_gpu_provisions_nothing(monkeypatch, tmp_path, capsys):
    _patch_heavy_linux_steps(monkeypatch, str(tmp_path))
    monkeypatch.setattr(steps_mod, "install_gpu_stack", _real_install_gpu_stack)
    calls: list[InstallContext] = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource([]), managers=[_FakeAptManager()])
    ctx = InstallContext(cfg=Config(platform="linux"), gpu=True, gpu_vendor="none")

    step._run_linux(ctx)

    assert calls == []
    assert "No discrete GPU detected" in capsys.readouterr().out
