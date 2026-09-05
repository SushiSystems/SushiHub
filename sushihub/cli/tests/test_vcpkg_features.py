"""A port asked for with a feature list is the port vcpkg lists without one."""

from types import SimpleNamespace

import pytest

from sushistack.config import Config
from sushistack.setup import package_managers
from sushistack.setup.package_managers import VcpkgManager

#: One line of `vcpkg list --triplet x64-windows` output for an installed imgui.
LISTED = "imgui:x64-windows                        1.92.8    Dear ImGui\n"


@pytest.fixture
def manager(monkeypatch):
    """Return a Windows VcpkgManager whose `vcpkg list` reports imgui alone."""
    monkeypatch.setattr(VcpkgManager, "available", lambda self: True)
    monkeypatch.setattr(
        package_managers.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=LISTED))
    return VcpkgManager(Config(platform="windows"))


def test_a_port_with_features_is_seen_as_installed(manager):
    assert manager.is_installed("imgui[glfw-binding,opengl3-binding]")


def test_a_bare_port_name_still_matches(manager):
    assert manager.is_installed("imgui")


def test_a_port_that_is_not_listed_is_not_installed(manager):
    assert not manager.is_installed("glfw3[wayland]")
