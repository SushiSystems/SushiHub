"""`ss gui` drives the desktop application through the shared cmake machinery.

No test here runs cmake, ninja or ctest. The driver is a recorder that keeps the
argument lists it was handed, so what is proved is the command line the CLI would
have spawned.
"""

from pathlib import Path

import pytest

from sushicore.workspace import WORKSPACE_CLI_DIR
from sushistack.gui_config import GuiConfig, gui_root, load_gui_config


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Build a throwaway workspace carrying sushihub/gui and a config directory."""
    (tmp_path / ".sushistack").write_text("marker\n", encoding="utf-8")
    (tmp_path / WORKSPACE_CLI_DIR).mkdir(parents=True)
    gui = tmp_path / "sushihub" / "gui"
    gui.mkdir(parents=True)
    (gui / "CMakeLists.txt").write_text("", encoding="utf-8")
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    return tmp_path


def test_gui_root_is_the_application_directory_of_the_workspace(workspace):
    assert gui_root(workspace) == workspace / "sushihub" / "gui"


def test_gui_root_defaults_to_the_workspace_the_environment_names(workspace):
    assert gui_root() == workspace / "sushihub" / "gui"


def test_gui_root_exits_when_the_application_carries_no_cmakelists(workspace):
    (workspace / "sushihub" / "gui" / "CMakeLists.txt").unlink()
    with pytest.raises(SystemExit):
        gui_root(workspace)


def test_the_compiler_is_left_to_cmake_when_none_is_configured(workspace):
    assert GuiConfig(platform="windows").resolved_compiler(Path(workspace)) == ""


def test_an_explicit_compiler_still_wins(workspace):
    cfg = GuiConfig(platform="windows", cxx="C:/tools/clang++.exe")
    assert cfg.resolved_compiler(Path(workspace)) == "C:/tools/clang++.exe"


def test_run_launches_the_application_by_default():
    """The run target comes from the profile, never from the workspace's shared [tool] table."""
    from sushistack.gui_config import GUI_PROFILE

    assert GUI_PROFILE.default_target == "sushihub_gui"


class RecordingDriver:
    """Stand-in for CMakeDriver that keeps each call instead of spawning one."""

    def __init__(self, configured: bool = False) -> None:
        """Record into empty logs; *configured* says the tree needs no configure."""
        self.configures: list[list[str]] = []
        self.compiles: list[str | None] = []
        self.ctests: list[tuple] = []
        self.cleaned: list[Path] = []
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
        return 0

    def compile(self, cfg, build_dir, cwd, env, *, config=None, targets=()) -> int:
        """Record the configuration one build was asked for."""
        self.compiles.append(config)
        return 0

    def ctest_run(self, cfg, build_dir, env, *, label_regex=None, filter=None,
                  repeat=0) -> int:
        """Record the selection one test run was asked for."""
        self.ctests.append((label_regex, filter, repeat))
        return 0

    def clean_tree(self, build_dir) -> None:
        """Record one removal of a build tree."""
        self.cleaned.append(build_dir)


def _env(cfg, build_dir):
    """Stand in for the vcvars snapshot with a fixed environment."""
    return {"PATH": "fake"}


@pytest.fixture
def provisioned(workspace):
    """Add the vcpkg tree `ss install` provisions to the throwaway workspace."""
    (workspace / "dependencies" / "vcpkg").mkdir(parents=True)
    return workspace


def _configure_of(driver) -> list[str]:
    """Return the single configure command line the driver recorded."""
    assert len(driver.configures) == 1
    return driver.configures[0]


def test_the_configure_points_cmake_at_the_provisioned_vcpkg_tree(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    assert gui.build(driver=driver, env_loader=_env) == 0
    argv = _configure_of(driver)
    vcpkg = provisioned / "dependencies" / "vcpkg"
    assert f"-DCMAKE_TOOLCHAIN_FILE={vcpkg}/scripts/buildsystems/vcpkg.cmake" in argv
    assert f"-DVCPKG_ROOT={vcpkg}" in argv


def test_the_configure_turns_manifest_mode_off_and_tests_on(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    gui.build(driver=driver, env_loader=_env)
    argv = _configure_of(driver)
    assert "-DVCPKG_MANIFEST_MODE=OFF" in argv
    assert "-DSUSHIHUB_GUI_BUILD_TESTS=ON" in argv


def test_the_configure_names_the_build_type_and_the_build_directory(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    gui.build(gui.BuildType.release, driver=driver, env_loader=_env)
    argv = _configure_of(driver)
    root = provisioned / "sushihub" / "gui"
    assert argv[:6] == ["cmake", "-S", str(root), "-B", str(root / "build" / "ss"), "-G"]
    assert "-DCMAKE_BUILD_TYPE=Release" in argv
    assert driver.compiles == ["Release"]


def test_the_configure_names_no_compiler_when_none_is_configured(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    gui.build(driver=driver, env_loader=_env)
    assert not [a for a in _configure_of(driver) if a.startswith("-DCMAKE_CXX_COMPILER")]


def test_a_caller_define_comes_after_every_default(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    gui.build(defines=["SUSHIHUB_GUI_BUILD_TESTS=OFF"], driver=driver, env_loader=_env)
    argv = _configure_of(driver)
    assert argv[-1] == "-DSUSHIHUB_GUI_BUILD_TESTS=OFF"


def test_a_define_without_a_value_is_refused(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    assert gui.build(defines=["SUSHIHUB_GUI_BUILD_TESTS"], driver=driver, env_loader=_env) == 2
    assert driver.configures == []


def test_clean_removes_the_tree_before_configuring(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    gui.build(clean=True, driver=driver, env_loader=_env)
    assert driver.cleaned == [provisioned / "sushihub" / "gui" / "build" / "ss"]
    assert len(driver.configures) == 1


def test_test_passes_the_filter_and_the_repeat_through_with_no_label(provisioned):
    from sushistack.services import gui

    (provisioned / "sushihub" / "gui" / "build" / "ss").mkdir(parents=True)
    driver = RecordingDriver()
    assert gui.test(filter="Catalogue.*", repeat=3, driver=driver, env_loader=_env) == 0
    assert driver.ctests == [(None, "Catalogue.*", 3)]


def test_test_refuses_before_the_first_build(provisioned, capsys):
    from sushistack.services import gui

    driver = RecordingDriver()
    assert gui.test(driver=driver, env_loader=_env) == 1
    assert driver.ctests == []
    captured = capsys.readouterr()
    assert "ss gui build" in captured.out + captured.err


def test_run_refuses_before_the_first_build(provisioned, capsys):
    from sushistack.services import gui

    assert gui.run(env_loader=_env) == 1
    captured = capsys.readouterr()
    assert "ss gui build" in captured.out + captured.err


def test_clean_removes_the_build_directory(provisioned):
    from sushistack.services import gui

    driver = RecordingDriver()
    assert gui.clean(driver=driver) == 0
    assert driver.cleaned == [provisioned / "sushihub" / "gui" / "build" / "ss"]
