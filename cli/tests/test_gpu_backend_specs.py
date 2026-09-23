"""``install_gpu_stack`` dispatches through hub's own package-manager registry.

Each vendor spec's own contract (CUDA/ROCm/Level Zero locate and provision) is
tested in sushicore (``tests/provision/test_gpu_backend_specs.py``); this file
covers only ``package_managers.install_gpu_stack``, which stays in hub.
"""

from __future__ import annotations

from types import SimpleNamespace

from sushihub.setup import package_managers
from sushihub.setup.gpu_backends.registry import Registry


def _fake_console(**overrides):
    """Build a console stand-in that records calls instead of touching the real one.

    Rebinding a vendor module's own ``console`` name, rather than patching
    :mod:`sushihub.console` itself, keeps its lazily built Rich console
    (and the stdout it captured at construction) untouched for every other
    test in the process, in particular the CLI's JSON-stream tests.
    """
    base = SimpleNamespace(info=lambda *a, **k: None, warn=lambda *a, **k: None,
                            error=lambda *a, **k: None, command=lambda *a, **k: None)
    for name, fn in overrides.items():
        setattr(base, name, fn)
    return base


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
    from sushihub.setup.gpu_backends.backend import GpuBackendSpec

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
