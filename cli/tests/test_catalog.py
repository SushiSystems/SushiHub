"""What the module catalog answers today: its members, their aliases and their expansion."""

from __future__ import annotations

import pytest

from sushihub.services import modules
from sushihub.services.catalog import CATALOG, load_catalog

from .test_presence import Recorder


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line the catalog prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_the_catalog_holds_the_four_stack_modules():
    """Four modules are registered, in the order every command lists them."""
    assert CATALOG.names() == [
        "sushiruntime",
        "sushiengine",
        "sushiai",
        "sushiblas",
    ]


def test_every_entry_names_its_repository_and_directory():
    """A catalog entry carries a github URL and a directory equal to its name."""
    for name in CATALOG:
        entry = CATALOG[name]
        assert entry.name == name
        assert entry.directory == name
        assert entry.repo == f"https://github.com/sushisystems/{name}.git"


def test_sushiengine_is_the_one_module_sold_as_a_binary():
    """Exactly one entry carries distribution = binary, and it is sushiengine."""
    sold = [n for n in CATALOG if CATALOG[n].is_binary]
    assert sold == ["sushiengine"]


def test_sushicore_is_not_a_catalog_member():
    """sushicore ships inside the repository, so the catalog never lists it."""
    assert modules.SUSHICORE_NAME not in CATALOG


def test_every_module_has_a_two_letter_alias():
    """Each alias maps to a catalog member and no module is left without one."""
    assert set(CATALOG.aliases().values()) == set(CATALOG.names())
    assert CATALOG.aliases()["sr"] == "sushiruntime"
    assert CATALOG.aliases()["se"] == "sushiengine"


def test_an_empty_list_means_every_module():
    """Passing nothing, or 'all', expands to the whole catalog in order."""
    assert modules._resolve_names(None) == CATALOG.names()
    assert modules._resolve_names([]) == CATALOG.names()
    assert modules._resolve_names(["all"]) == CATALOG.names()


def test_aliases_expand_to_module_names():
    """A list of aliases comes back as the names they stand for, in the order given."""
    assert modules._resolve_names(["se", "sr"]) == ["sushiengine", "sushiruntime"]


def test_a_name_outside_the_catalog_is_refused(recorder):
    """An unknown name returns None and the message names it and the choices."""
    assert modules._resolve_names(["sushiwater"]) is None
    assert recorder.said("sushiwater")
    assert recorder.said("sushiruntime")


def test_the_gitignore_lines_cover_every_module_and_the_workspace_directory():
    """`hub init` ignores the dependency tree, every module directory and .sushistack/."""
    lines = modules._GITIGNORE_LINES
    assert "/dependencies/" in lines
    for name in CATALOG:
        assert f"/{name}/" in lines
    assert "/.sushistack/" in lines


def test_the_gitignore_lines_name_no_file_a_new_workspace_never_writes():
    """The pre-2026-09-22 local files are not written any more, so they are not ignored."""
    lines = modules._GITIGNORE_LINES
    assert "/cli/config.local.toml" not in lines
    assert "/cli/modules.local.toml" not in lines


def test_sushidsp_and_sushitrack_are_not_stack_modules():
    """The two products that share no dependency with the stack are not in the catalog."""
    assert CATALOG.resolve("sushidsp") is None
    assert CATALOG.resolve("sushitrack") is None
    assert CATALOG.resolve("sd") is None
    assert CATALOG.resolve("st") is None


def test_the_catalog_resolves_a_name_and_an_alias_to_the_same_module():
    """resolve answers the module name for both spellings and None for neither."""
    assert CATALOG.resolve("sushiruntime") == "sushiruntime"
    assert CATALOG.resolve("sr") == "sushiruntime"
    assert CATALOG.resolve("sushiwater") is None


def test_the_packaged_catalog_is_readable_as_package_data():
    """The catalog loads through importlib.resources, as an installed wheel must."""
    assert load_catalog().names() == CATALOG.names()
