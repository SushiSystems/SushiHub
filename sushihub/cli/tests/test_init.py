"""What `hub init` leaves on disk: the marker, the .gitignore lines and the dependency tree."""

from __future__ import annotations

import pytest

from sushicore.workspace import read_toml
from sushistack.config import WORKSPACE_MARKER, workspace_file
from sushistack.services import modules

from .test_presence import Recorder


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Run `hub init` in a throwaway directory whose dependency tree is also throwaway."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(modules, "deps_dir", lambda: tmp_path / "dependencies")
    return tmp_path


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line `hub init` prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_init_writes_the_marker_directory(workspace, recorder):
    """The marker is a directory holding a versioned workspace.toml."""
    assert modules.init() == 0
    assert (workspace / WORKSPACE_MARKER).is_dir()
    assert read_toml(workspace_file(workspace))["workspace"]["version"] == "1"


def test_init_creates_the_dependency_tree(workspace, recorder):
    """The dependency directory exists afterwards, empty."""
    modules.init()
    assert (workspace / "dependencies").is_dir()


def test_init_writes_every_gitignore_line(workspace, recorder):
    """A fresh .gitignore carries each managed line exactly once."""
    modules.init()
    text = (workspace / ".gitignore").read_text(encoding="utf-8")
    for line in modules._GITIGNORE_LINES:
        assert text.count(line) == 1


def test_init_separates_its_lines_from_an_existing_file(workspace, recorder):
    """An existing .gitignore with no trailing newline keeps its last line intact."""
    (workspace / ".gitignore").write_text("build/", encoding="utf-8")
    modules.init()
    lines = (workspace / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "build/"
    assert "/dependencies/" in lines


def test_a_second_init_adds_nothing(workspace, recorder):
    """Running init twice leaves the .gitignore byte-identical and says so."""
    modules.init()
    first = (workspace / ".gitignore").read_text(encoding="utf-8")
    assert modules.init() == 0
    assert (workspace / ".gitignore").read_text(encoding="utf-8") == first
    assert recorder.said(f"Already a SushiStack workspace: {workspace.resolve()}")
