"""Where `hub` decides the workspace, its config directory and its dependency tree are."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.workspace import WORKSPACE_CLI_DIR
from sushistack.config import (
    WORKSPACE_MARKER,
    config_dir,
    deps_dir,
    workspace_root,
)


@pytest.fixture
def unpinned(monkeypatch, tmp_path):
    """Drop the SUSHISTACK_HOME the suite's conftest pins and sit in an empty directory."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.delenv("SUSHISTACK_DEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_the_environment_variable_names_the_workspace(unpinned, monkeypatch, tmp_path):
    """SUSHISTACK_HOME wins over anything the current directory would say."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(elsewhere))
    assert workspace_root() == elsewhere.resolve()


def test_the_marker_is_found_by_walking_up(unpinned):
    """A .sushistack marker in an ancestor makes that ancestor the root."""
    (unpinned / WORKSPACE_MARKER).write_text("", encoding="utf-8")
    nested = unpinned / "sushiruntime" / "cli"
    nested.mkdir(parents=True)
    assert workspace_root(nested) == unpinned.resolve()


def test_the_manifests_tree_is_a_marker_of_its_own(unpinned):
    """The repository's own sushihub/cli/manifests signature marks a workspace."""
    (unpinned / WORKSPACE_CLI_DIR / "manifests").mkdir(parents=True)
    assert workspace_root(unpinned) == unpinned.resolve()


def test_no_marker_anywhere_exits(unpinned):
    """Resolution outside a workspace raises SystemExit naming the marker."""
    with pytest.raises(SystemExit) as caught:
        workspace_root(unpinned)
    assert WORKSPACE_MARKER in str(caught.value)


def test_the_config_directory_is_the_hub_cli_directory(unpinned):
    """config_dir resolves to <root>/sushihub/cli, inside the repository tree."""
    assert config_dir(unpinned) == unpinned / WORKSPACE_CLI_DIR
    assert config_dir(unpinned) == unpinned / Path("sushihub") / "cli"


def test_dependencies_default_to_one_tree_under_the_root(unpinned, monkeypatch):
    """deps_dir is <root>/dependencies when nothing overrides it."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(unpinned))
    assert deps_dir() == unpinned.resolve() / "dependencies"


def test_the_dependency_override_wins(unpinned, monkeypatch, tmp_path):
    """SUSHISTACK_DEPS_DIR replaces the tree under the root."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(unpinned))
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(tmp_path / "elsewhere"))
    assert deps_dir() == tmp_path / "elsewhere"


def test_dependencies_fall_back_to_a_user_path_outside_a_workspace(unpinned, monkeypatch):
    """Outside a workspace deps_dir lands under a per-user SushiStack directory."""
    monkeypatch.setenv("LOCALAPPDATA", str(unpinned / "local"))
    assert deps_dir() == unpinned / "local" / "SushiStack" / "dependencies"
