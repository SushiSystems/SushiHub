"""What the module catalog answers today: its members, their aliases and their expansion."""

from __future__ import annotations

import pytest

from sushistack.services import modules

from .test_presence import Recorder


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line the catalog prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_the_catalog_holds_the_six_modules_of_today():
    """Six modules are registered; wave 2 drops sushidsp and sushitrack from this list."""
    assert list(modules.MODULES) == [
        "sushiruntime",
        "sushiengine",
        "sushiai",
        "sushiblas",
        "sushidsp",
        "sushitrack",
    ]


def test_every_entry_names_its_repository_and_directory():
    """A catalog entry carries a github URL and a directory equal to its name."""
    for name, entry in modules.MODULES.items():
        assert entry.name == name
        assert entry.directory == name
        assert entry.repo == f"https://github.com/sushisystems/{name}.git"


def test_sushiengine_is_the_one_module_sold_as_a_binary():
    """BINARY_MODULE names sushiengine and nothing else."""
    assert modules.BINARY_MODULE == "sushiengine"
    assert modules.BINARY_MODULE in modules.MODULES


def test_sushicore_is_not_a_catalog_member():
    """sushicore ships inside the repository, so the catalog never lists it."""
    assert modules.SUSHICORE_NAME not in modules.MODULES


def test_every_module_has_a_two_letter_alias():
    """Each alias maps to a catalog member and no module is left without one."""
    assert set(modules._ALIASES.values()) == set(modules.MODULES)
    assert modules._ALIASES["sr"] == "sushiruntime"
    assert modules._ALIASES["se"] == "sushiengine"


def test_an_empty_list_means_every_module():
    """Passing nothing, or 'all', expands to the whole catalog in order."""
    assert modules._resolve_names(None) == list(modules.MODULES)
    assert modules._resolve_names([]) == list(modules.MODULES)
    assert modules._resolve_names(["all"]) == list(modules.MODULES)


def test_aliases_expand_to_module_names():
    """A list of aliases comes back as the names they stand for, in the order given."""
    assert modules._resolve_names(["se", "sr"]) == ["sushiengine", "sushiruntime"]


def test_a_name_outside_the_catalog_is_refused(recorder):
    """An unknown name returns None and the message names it and the choices."""
    assert modules._resolve_names(["sushiwater"]) is None
    assert recorder.said("sushiwater")
    assert recorder.said("sushiruntime")


def test_the_gitignore_lines_cover_every_module_and_the_local_files():
    """`hub init` ignores the dependency tree, every module directory and both local files."""
    lines = modules._GITIGNORE_LINES
    assert "/dependencies/" in lines
    for name in modules.MODULES:
        assert f"/{name}/" in lines
    assert "/sushihub/cli/config.local.toml" in lines
    assert "/sushihub/cli/modules.local.toml" in lines
