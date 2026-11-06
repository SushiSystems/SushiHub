# test_init.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What `hub init` leaves on disk: the marker, the .gitignore lines and the dependency tree."""

from __future__ import annotations

import pytest
from sushicore.console_memory import RecordingConsole

from sushicore.workspace import read_toml
from sushihub.config import WORKSPACE_MARKER, workspace_file
from sushihub.services import modules
from sushihub.services.catalog import CATALOG
from sushihub.services.memory.ports import memory_ports

pytestmark = pytest.mark.medium


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Run `hub init` in a throwaway directory whose dependency tree is also throwaway."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(tmp_path / "dependencies"))
    return tmp_path


@pytest.fixture
def out() -> RecordingConsole:
    """The console `hub init` prints through."""
    return RecordingConsole()


def init(out: RecordingConsole) -> int:
    """Run `hub init` printing through *out*."""
    return modules.init(ports=memory_ports(console=out))


def gitignore_lines(workspace) -> list[str]:
    """Read the lines of the workspace .gitignore."""
    return (workspace / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_init_writes_the_marker_directory(workspace, out):
    """The marker is a directory holding a versioned workspace.toml."""
    assert init(out) == 0
    assert (workspace / WORKSPACE_MARKER).is_dir()
    assert read_toml(workspace_file(workspace))["workspace"]["version"] == "1"


def test_init_creates_the_dependency_tree(workspace, out):
    """The dependency directory exists afterwards, empty."""
    init(out)
    assert (workspace / "dependencies").is_dir()


@pytest.mark.parametrize("line", ["/dependencies/", "/.sushistack/"])
def test_init_ignores_the_dependency_tree_and_the_workspace_directory(workspace, out, line):
    """A fresh .gitignore carries each of these lines exactly once."""
    init(out)
    assert gitignore_lines(workspace).count(line) == 1


@pytest.mark.parametrize("name", CATALOG.names())
def test_init_ignores_every_module_directory(workspace, out, name):
    """A fresh .gitignore carries a line for each catalog module, exactly once."""
    init(out)
    assert gitignore_lines(workspace).count(f"/{name}/") == 1


@pytest.mark.parametrize("line", ["/cli/config.local.toml", "/cli/modules.local.toml"])
def test_init_ignores_no_file_a_new_workspace_never_writes(workspace, out, line):
    """The pre-2026-09-22 local files are not written any more, so they are not ignored."""
    init(out)
    assert line not in gitignore_lines(workspace)


def test_init_separates_its_lines_from_an_existing_file(workspace, out):
    """An existing .gitignore with no trailing newline keeps its last line intact."""
    (workspace / ".gitignore").write_text("build/", encoding="utf-8")
    init(out)
    lines = gitignore_lines(workspace)
    assert lines[0] == "build/"
    assert "/dependencies/" in lines


def test_a_second_init_adds_nothing(workspace, out):
    """Running init twice leaves the .gitignore byte-identical and says so."""
    init(out)
    first = (workspace / ".gitignore").read_text(encoding="utf-8")
    assert init(out) == 0
    assert (workspace / ".gitignore").read_text(encoding="utf-8") == first
    assert f"Already a SushiStack workspace: {workspace.resolve()}" in out.texts("info")
