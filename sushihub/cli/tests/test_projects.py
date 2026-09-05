"""The registry of projects the desktop application opens."""

from __future__ import annotations

import pytest

from sushistack.services import projects
from sushistack.services.projects import PROJECTS_FILE, Project

from .test_presence import Recorder


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """Point the registry at a throwaway config directory and return its root."""
    config = tmp_path / "sushihub" / "cli"
    monkeypatch.setattr(projects, "config_dir", lambda: config)
    return tmp_path


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line the three commands print."""
    spy = Recorder()
    monkeypatch.setattr(projects, "console", spy)
    return spy


def a_project(root, name: str = "moonlight"):
    """Make a directory that looks like a project and return its path."""
    path = root / "work" / name
    path.mkdir(parents=True)
    return path


def test_the_registry_is_empty_before_anything_is_added(registry):
    assert projects.list_projects() == []


def test_the_file_lives_beside_the_module_registry(registry):
    projects.add_project(a_project(registry))
    assert (registry / "sushihub" / "cli" / PROJECTS_FILE).is_file()
    assert PROJECTS_FILE == "projects.local.toml"


def test_add_project_derives_the_name_from_the_directory(registry):
    path = a_project(registry)
    assert projects.add_project(path) == Project("moonlight", str(path))
    assert projects.list_projects() == [Project("moonlight", str(path))]


def test_add_project_takes_the_name_it_is_given(registry):
    path = a_project(registry)
    assert projects.add_project(path, name="night").name == "night"
    assert [p.name for p in projects.list_projects()] == ["night"]


def test_add_project_refuses_a_path_that_is_not_a_directory(registry):
    missing = registry / "nowhere"
    with pytest.raises(NotADirectoryError):
        projects.add_project(missing)
    assert projects.list_projects() == []


def test_add_project_replaces_an_entry_of_the_same_name(registry):
    first = a_project(registry, "moonlight")
    second = registry / "elsewhere" / "moonlight"
    second.mkdir(parents=True)
    projects.add_project(first)
    projects.add_project(second)
    assert projects.list_projects() == [Project("moonlight", str(second))]


def test_projects_are_listed_by_name(registry):
    for name in ("zephyr", "moonlight"):
        projects.add_project(a_project(registry, name))
    assert [p.name for p in projects.list_projects()] == ["moonlight", "zephyr"]


def test_remove_project_drops_it_and_says_whether_it_was_there(registry):
    projects.add_project(a_project(registry))
    assert projects.remove_project("moonlight") is True
    assert projects.list_projects() == []
    assert projects.remove_project("moonlight") is False


def test_a_path_with_a_space_survives_the_round_trip(registry):
    path = registry / "work" / "night sky"
    path.mkdir(parents=True)
    projects.add_project(path)
    assert projects.list_projects() == [Project("night sky", str(path))]


def test_show_prints_a_row_per_project_and_carries_them_as_its_payload(
        registry, recorder):
    path = a_project(registry)
    projects.add_project(path)
    (registry / "work" / "gone").mkdir()
    projects.add_project(registry / "work" / "gone")
    (registry / "work" / "gone").rmdir()

    code, payload = projects.show()
    assert code == 0
    assert recorder.tables[-1][0] == ["Name", "Path", "Exists"]
    assert recorder.tables[-1][1] == [["gone", str(registry / "work" / "gone"), "no"],
                                      ["moonlight", str(path), "yes"]]
    assert payload == {"projects": [
        {"name": "gone", "path": str(registry / "work" / "gone"), "exists": False},
        {"name": "moonlight", "path": str(path), "exists": True}]}


def test_show_says_so_when_the_registry_is_empty(registry, recorder):
    assert projects.show() == (0, {"projects": []})
    assert recorder.said("No projects registered")


def test_add_reports_the_project_it_recorded(registry, recorder):
    path = a_project(registry)
    assert projects.add(str(path)) == (0, {"name": "moonlight", "path": str(path)})
    assert recorder.said("moonlight")


def test_add_reports_a_path_that_is_not_a_directory(registry, recorder):
    code, payload = projects.add(str(registry / "nowhere"))
    assert code == 1 and payload == {}
    assert recorder.said("not a directory")


def test_remove_reports_a_name_the_registry_does_not_hold(registry, recorder):
    code, payload = projects.remove("moonlight")
    assert code == 1 and payload == {}
    assert recorder.said("moonlight")


def test_remove_reports_the_name_it_dropped(registry, recorder):
    projects.add_project(a_project(registry))
    assert projects.remove("moonlight") == (0, {"name": "moonlight"})
    assert projects.list_projects() == []
