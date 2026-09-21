"""An old workspace becomes a new one, and the one file it produces is shared without loss."""

from __future__ import annotations

from sushicore.workspace import read_toml
from sushihub.config import CHECKOUT_CLI_DIR, WORKSPACE_MARKER, upgrade_workspace, workspace_file


def _old_workspace(root):
    """Build a pre-2026-09-22 workspace: a marker file and the two data files."""
    (root / WORKSPACE_MARKER).write_text("# old marker\n", encoding="utf-8")
    cli = root / CHECKOUT_CLI_DIR
    cli.mkdir(parents=True)
    (cli / "modules.local.toml").write_text(
        '[modules]\nsushiai = "D:/Projects/sushiai"\n', encoding="utf-8")
    (cli / "config.local.toml").write_text(
        '[tool]\ntoolchain = "intel-llvm"\n\n[tool.windows]\ngenerator = "Ninja"\n',
        encoding="utf-8")
    return root


def test_the_marker_file_becomes_a_directory(tmp_path):
    """Upgrading replaces the file with a directory holding workspace.toml."""
    _old_workspace(tmp_path)
    assert upgrade_workspace(tmp_path) is True
    assert (tmp_path / WORKSPACE_MARKER).is_dir()
    assert workspace_file(tmp_path).is_file()


def test_both_tables_move_across(tmp_path):
    """The link registry and the tool section survive the move."""
    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    doc = read_toml(workspace_file(tmp_path))
    assert doc["modules"] == {"sushiai": "D:/Projects/sushiai"}
    assert doc["tool"]["toolchain"] == "intel-llvm"
    assert doc["tool"]["windows"]["generator"] == "Ninja"
    assert doc["workspace"]["version"] == "1"


def test_the_originals_are_left_alone(tmp_path):
    """Nothing is deleted, so the step is undone by removing the directory."""
    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    assert (tmp_path / CHECKOUT_CLI_DIR / "modules.local.toml").is_file()
    assert (tmp_path / CHECKOUT_CLI_DIR / "config.local.toml").is_file()


def test_upgrading_twice_changes_nothing(tmp_path):
    """A workspace already in the new shape is left exactly as it is."""
    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    before = workspace_file(tmp_path).read_text(encoding="utf-8")
    assert upgrade_workspace(tmp_path) is False
    assert workspace_file(tmp_path).read_text(encoding="utf-8") == before


def test_a_workspace_with_no_old_data_still_upgrades(tmp_path):
    """A marker file with nothing beside it becomes a directory with a version alone."""
    (tmp_path / WORKSPACE_MARKER).write_text("# old marker\n", encoding="utf-8")
    assert upgrade_workspace(tmp_path) is True
    doc = read_toml(workspace_file(tmp_path))
    assert doc["workspace"]["version"] == "1"
    assert "modules" not in doc


def test_a_link_written_after_an_upgrade_keeps_the_tool_paths(tmp_path, monkeypatch):
    """The two writers share one file, so neither erases what the other stored."""
    from sushihub.services import links

    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    links.write("sushiblas", tmp_path / "sushiblas")
    doc = read_toml(workspace_file(tmp_path))
    assert doc["tool"]["toolchain"] == "intel-llvm"
    assert doc["tool"]["windows"]["generator"] == "Ninja"
    assert set(doc["modules"]) == {"sushiai", "sushiblas"}


def test_hub_remove_empties_the_tool_table_and_keeps_the_registry(tmp_path, monkeypatch):
    """`hub remove` reclaims what the install wrote and leaves the links alone."""
    from sushihub.config import Config
    from sushihub.setup.pipeline import InstallContext
    from sushihub.setup.steps import UninstallStep

    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    UninstallStep(source=None, managers=[])._remove_config(
        InstallContext(cfg=Config(platform="windows")))
    doc = read_toml(workspace_file(tmp_path))
    assert doc["tool"] == {}
    assert doc["modules"] == {"sushiai": "D:/Projects/sushiai"}
    assert doc["workspace"]["version"] == "1"


def test_a_dry_run_of_hub_remove_leaves_the_tool_table(tmp_path, monkeypatch):
    """The dry run reports the section it would clear and writes nothing."""
    from sushihub.config import Config
    from sushihub.setup.pipeline import InstallContext
    from sushihub.setup.steps import UninstallStep

    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    before = workspace_file(tmp_path).read_text(encoding="utf-8")
    UninstallStep(source=None, managers=[])._remove_config(
        InstallContext(cfg=Config(platform="windows"), dry_run=True))
    assert workspace_file(tmp_path).read_text(encoding="utf-8") == before
