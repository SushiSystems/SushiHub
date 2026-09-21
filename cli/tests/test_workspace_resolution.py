"""Where `hub` decides the workspace, its own file, its defaults and its dependency tree."""

from __future__ import annotations

import pytest

from sushihub.config import (
    CHECKOUT_CLI_DIR,
    DEFAULTS_FILE,
    WORKSPACE_MARKER,
    deps_dir,
    packaged_defaults,
    workspace_file,
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
    """A .sushistack marker directory in an ancestor makes that ancestor the root."""
    (unpinned / WORKSPACE_MARKER).mkdir()
    nested = unpinned / "sushiruntime" / "cli"
    nested.mkdir(parents=True)
    assert workspace_root(nested) == unpinned.resolve()


def test_the_old_marker_file_still_resolves(unpinned):
    """A pre-2026-09-22 marker file resolves, so upgrade_workspace can reach it."""
    (unpinned / WORKSPACE_MARKER).write_text("# old marker\n", encoding="utf-8")
    assert workspace_root(unpinned) == unpinned.resolve()


def test_the_manifests_tree_no_longer_marks_a_workspace(unpinned):
    """A workspace is no longer a checkout, so cli/manifests marks nothing."""
    (unpinned / CHECKOUT_CLI_DIR / "manifests").mkdir(parents=True)
    with pytest.raises(SystemExit):
        workspace_root(unpinned)


def test_no_marker_anywhere_exits(unpinned):
    """Resolution outside a workspace raises SystemExit naming the marker."""
    with pytest.raises(SystemExit) as caught:
        workspace_root(unpinned)
    assert WORKSPACE_MARKER in str(caught.value)


def test_the_workspace_file_sits_inside_the_marker_directory(unpinned):
    """workspace_file resolves to <root>/.sushistack/workspace.toml."""
    assert workspace_file(unpinned) == unpinned / WORKSPACE_MARKER / "workspace.toml"


def test_the_defaults_come_from_the_package_not_the_workspace(unpinned):
    """packaged_defaults resolves outside any workspace and names a readable file."""
    with packaged_defaults() as defaults:
        assert defaults.name == DEFAULTS_FILE
        assert "[identity]" in defaults.read_text(encoding="utf-8")
        assert unpinned not in defaults.parents


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
