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


def test_the_loaded_config_runs_the_application_by_default(workspace):
    assert load_gui_config().target_bin == "sushihub_gui"
