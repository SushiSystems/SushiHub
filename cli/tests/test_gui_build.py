# test_gui_build.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""`hub gui` drives the desktop application through the shared cmake machinery.

No test here runs cmake, ninja or ctest. The driver is a recorder that keeps the
argument lists it was handed, so what is proved is the command line the CLI would
have spawned.
"""

import os
from pathlib import Path

import pytest
from sushicore.errors import SushiCoreError

from sushihub.config import WORKSPACE_MARKER
from sushihub.errors import GuiSourcesMissingError
from sushihub.gui_config import K_REPOSITORY_URL, GuiConfig, gui_root

pytestmark = pytest.mark.medium


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Build a throwaway workspace carrying gui and a marker directory."""
    (tmp_path / WORKSPACE_MARKER).mkdir()
    gui = tmp_path / "gui"
    gui.mkdir(parents=True)
    (gui / "CMakeLists.txt").write_text("", encoding="utf-8")
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    return tmp_path


def test_gui_root_is_the_application_directory_of_the_workspace(workspace):
    assert gui_root(workspace) == workspace / "gui"


def test_gui_root_defaults_to_the_workspace_the_environment_names(workspace):
    assert gui_root() == workspace / "gui"


def test_gui_root_refuses_a_workspace_without_the_application_sources(workspace):
    """A missing CMakeLists.txt raises the hub error, which the entry point reports."""
    (workspace / "gui" / "CMakeLists.txt").unlink()
    with pytest.raises(GuiSourcesMissingError) as caught:
        gui_root(workspace)
    assert isinstance(caught.value, SushiCoreError)


def test_the_missing_sources_hint_names_the_clone_and_not_an_update(workspace):
    """The hint sends the person to `git clone`, never to `hub update`."""
    (workspace / "gui" / "CMakeLists.txt").unlink()
    with pytest.raises(GuiSourcesMissingError) as caught:
        gui_root(workspace)
    assert "git clone" in str(caught.value) and "hub update" not in str(caught.value)


def test_the_missing_sources_hint_names_the_repository_only_by_its_clone_url(workspace):
    """The hint carries the clone URL and no second repository name beside it."""
    (workspace / "gui" / "CMakeLists.txt").unlink()
    with pytest.raises(GuiSourcesMissingError) as caught:
        gui_root(workspace)
    assert K_REPOSITORY_URL in str(caught.value)
    assert "repository" not in str(caught.value)


@pytest.mark.small
def test_the_compiler_is_left_to_cmake_when_none_is_configured():
    assert GuiConfig(platform="windows").resolved_compiler(Path("unused")) == ""


@pytest.mark.small
def test_an_explicit_compiler_still_wins():
    cfg = GuiConfig(platform="windows", cxx="C:/tools/clang++.exe")
    assert cfg.resolved_compiler(Path("unused")) == "C:/tools/clang++.exe"


class RecordingDriver:
    """Stand-in for CMakeDriver that keeps each call instead of spawning one."""

    def __init__(self, configured: bool = False) -> None:
        """Record into empty logs; *configured* says the tree needs no configure."""
        self.configures: list[list[str]] = []
        self.compiles: list[str | None] = []
        self.ctests: list[tuple] = []
        self.cleaned: list[Path] = []
        self.events: list[str] = []
        self._configured = configured

    def cmake(self, cfg) -> str:
        """Name the cmake executable the argv starts with."""
        return "cmake"

    def needs_configure(self, build_dir, generator, *, expect=None, root=None) -> bool:
        """Report whether the tree must be configured before it is built."""
        return not self._configured

    def configure(self, args, cwd, env=None) -> int:
        """Record one configure command line."""
        self.configures.append(list(args))
        self.events.append("configure")
        return 0

    def compile(self, cfg, build_dir, cwd, env, *, config=None, targets=()) -> int:
        """Record the configuration one build was asked for."""
        self.compiles.append(config)
        return 0

    def ctest_run(self, cfg, build_dir, env, *, label_regex=None, filter=None,
                  repeat=0, jobs=None) -> int:
        """Record the selection one test run was asked for."""
        self.ctests.append((label_regex, filter, repeat, jobs))
        return 0

    def clean_tree(self, build_dir) -> None:
        """Record one removal of a build tree."""
        self.cleaned.append(build_dir)
        self.events.append("clean")


class RecordingRunner:
    """Stand-in for the process runner that keeps each command line instead of spawning it."""

    def __init__(self) -> None:
        """Record into an empty log."""
        self.commands: list[list[str]] = []

    def run(self, cmd, cwd, env=None) -> int:
        """Record one command line."""
        self.commands.append(list(cmd))
        return 0


def _env(cfg, build_dir):
    """Stand in for the vcvars snapshot with a fixed environment."""
    return {"PATH": "fake"}


@pytest.fixture
def provisioned(workspace, monkeypatch):
    """Add the vcpkg tree `hub install` provisions to the throwaway workspace.

    The packaged defaults turn vcpkg off on Linux, where apt holds the libraries, so the
    platform is pinned to Windows: this test checks the vcpkg wiring, not the host's defaults.
    """
    monkeypatch.setattr("platform.system", lambda: "Windows")
    (workspace / "dependencies" / "vcpkg").mkdir(parents=True)
    return workspace


def _configure_of(driver) -> list[str]:
    """Return the single configure command line the driver recorded."""
    assert len(driver.configures) == 1
    return driver.configures[0]


def test_the_configure_points_cmake_at_the_provisioned_vcpkg_tree(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    assert gui.build(driver=driver, env_loader=_env) == 0
    argv = _configure_of(driver)
    vcpkg = provisioned / "dependencies" / "vcpkg"
    assert f"-DCMAKE_TOOLCHAIN_FILE={vcpkg}/scripts/buildsystems/vcpkg.cmake" in argv
    assert f"-DVCPKG_ROOT={vcpkg}" in argv


def test_the_configure_turns_manifest_mode_off(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(driver=driver, env_loader=_env)
    assert "-DVCPKG_MANIFEST_MODE=OFF" in _configure_of(driver)


def test_the_configure_turns_the_application_tests_on(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(driver=driver, env_loader=_env)
    assert "-DSUSHIHUB_GUI_BUILD_TESTS=ON" in _configure_of(driver)


def test_the_configure_names_the_source_and_the_build_directory(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(driver=driver, env_loader=_env)
    root = provisioned / "gui"
    assert _configure_of(driver)[:6] == [
        "cmake", "-S", str(root), "-B", str(root / "build" / "hub"), "-G"]


def test_the_configure_names_the_build_type(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(gui.BuildType.release, driver=driver, env_loader=_env)
    assert "-DCMAKE_BUILD_TYPE=Release" in _configure_of(driver)


def test_the_compile_is_asked_for_the_same_build_type(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(gui.BuildType.release, driver=driver, env_loader=_env)
    assert driver.compiles == ["Release"]


def test_the_configure_names_no_compiler_when_none_is_configured(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(driver=driver, env_loader=_env)
    assert not [a for a in _configure_of(driver) if a.startswith("-DCMAKE_CXX_COMPILER")]


def test_a_caller_define_comes_after_every_default(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(defines=["SUSHIHUB_GUI_BUILD_TESTS=OFF"], driver=driver, env_loader=_env)
    argv = _configure_of(driver)
    assert argv[-1] == "-DSUSHIHUB_GUI_BUILD_TESTS=OFF"


def test_a_define_without_a_value_is_refused(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    assert gui.build(defines=["SUSHIHUB_GUI_BUILD_TESTS"], driver=driver, env_loader=_env) == 2
    assert driver.configures == []


def test_clean_removes_the_tree_before_configuring(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    gui.build(clean=True, driver=driver, env_loader=_env)
    assert driver.cleaned == [provisioned / "gui" / "build" / "hub"]
    assert driver.events == ["clean", "configure"]


def test_test_passes_the_filter_the_repeat_and_the_jobs_through_with_no_label(provisioned):
    from sushihub.services import gui

    (provisioned / "gui" / "build" / "hub").mkdir(parents=True)
    driver = RecordingDriver()
    assert gui.test(filter="Catalogue.*", repeat=3, jobs=2, driver=driver,
                    env_loader=_env) == 0
    assert driver.ctests == [(None, "Catalogue.*", 3, 2)]


@pytest.mark.parametrize("command", [
    lambda gui, driver: gui.test(driver=driver, env_loader=_env),
    lambda gui, driver: gui.run(env_loader=_env),
], ids=["test", "run"])
def test_a_command_refuses_before_the_first_build(provisioned, capsys, command):
    from sushihub.services import gui

    driver = RecordingDriver()
    assert command(gui, driver) == 1
    assert driver.ctests == []
    captured = capsys.readouterr()
    assert "hub gui build" in captured.out + captured.err


def test_run_launches_the_application_by_default(provisioned):
    """With no target named, the program launched is the application itself."""
    from sushihub.services import gui

    build_dir = provisioned / "gui" / "build" / "hub"
    build_dir.mkdir(parents=True)
    program = build_dir / ("sushihub_gui.exe" if os.name == "nt" else "sushihub_gui")
    program.write_text("", encoding="utf-8")
    program.chmod(0o755)
    runner = RecordingRunner()
    assert gui.run(runner=runner, env_loader=_env) == 0
    assert [Path(command[0]) for command in runner.commands] == [program]


def test_clean_removes_the_build_directory(provisioned):
    from sushihub.services import gui

    driver = RecordingDriver()
    assert gui.clean(driver=driver) == 0
    assert driver.cleaned == [provisioned / "gui" / "build" / "hub"]
