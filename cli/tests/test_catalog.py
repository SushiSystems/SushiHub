# test_catalog.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the module catalog answers today: its members and their aliases."""

from __future__ import annotations

import pytest

from sushihub.services.catalog import CATALOG

pytestmark = pytest.mark.small

MODULES = ["sushilog", "sushiprofiler", "sushiruntime", "sushiengine",
           "sushiai", "sushiblas", "sushitrack", "sushidsp"]

#: The libraries each module links that the catalog lists ahead of it.
K_LINKS = {
    "sushiruntime": ["sushilog", "sushiprofiler"],
    "sushiengine": ["sushilog", "sushiprofiler", "sushiruntime"],
    "sushiai": ["sushilog", "sushiprofiler", "sushiruntime"],
    "sushiblas": ["sushilog", "sushiprofiler", "sushiruntime"],
    "sushitrack": ["sushilog", "sushiprofiler"],
    "sushidsp": ["sushilog", "sushiprofiler"],
}
K_LINK_ROWS = [(module, upstream) for module, upstreams in K_LINKS.items()
               for upstream in upstreams]


def test_the_catalog_holds_the_eight_stack_modules():
    """Eight modules are registered, whatever their order."""
    assert sorted(CATALOG.names()) == sorted(MODULES)


@pytest.mark.parametrize("module, upstream", K_LINK_ROWS)
def test_the_catalog_lists_a_library_ahead_of_the_module_that_links_it(module, upstream):
    """Every library a module links comes before it in the order commands list them.

    SushiBLAS, which SushiEngine and SushiAI link too, is listed after them, so those two edges
    are not promised.
    """
    names = CATALOG.names()
    assert names.index(upstream) < names.index(module)


@pytest.mark.parametrize("name", MODULES)
def test_every_entry_names_its_repository_and_directory(name):
    """A catalog entry carries a github URL and a directory equal to its name."""
    entry = CATALOG[name]
    assert (entry.name, entry.directory, entry.repo) == (
        name, name, f"https://github.com/sushisystems/{name}.git")


@pytest.mark.parametrize("name, sold", [
    ("sushilog", False), ("sushiprofiler", False), ("sushiruntime", False),
    ("sushiengine", True), ("sushiai", False), ("sushiblas", False),
    ("sushitrack", False), ("sushidsp", False),
])
def test_sushiengine_is_the_one_module_sold_as_a_binary(name, sold):
    """Only sushiengine carries distribution = binary."""
    assert CATALOG[name].is_binary is sold


def test_sushicore_is_not_a_catalog_member():
    """sushicore ships inside the repository, so the catalog never lists it."""
    assert "sushicore" not in CATALOG


@pytest.mark.parametrize("alias, name", [
    ("sl", "sushilog"), ("sp", "sushiprofiler"), ("sr", "sushiruntime"), ("se", "sushiengine"),
    ("sa", "sushiai"), ("sb", "sushiblas"), ("st", "sushitrack"), ("sd", "sushidsp"),
])
def test_every_module_has_its_two_letter_alias(alias, name):
    """Each module is reached by one alias of exactly two letters."""
    assert (len(alias), CATALOG.aliases().get(alias)) == (2, name)


@pytest.mark.parametrize("alias", CATALOG.aliases())
def test_no_alias_is_longer_than_two_letters(alias):
    """A three-letter alias would not be the alias the name promises."""
    assert len(alias) == 2


@pytest.mark.parametrize("given, expected", [
    ("sushidsp", "sushidsp"), ("sd", "sushidsp"),
    ("sushitrack", "sushitrack"), ("st", "sushitrack"),
    ("sushiruntime", "sushiruntime"), ("sr", "sushiruntime"),
    ("sushiwater", None),
])
def test_the_catalog_resolves_a_name_and_an_alias_to_the_same_module(given, expected):
    """resolve answers the module name for both spellings and None for neither."""
    assert CATALOG.resolve(given) == expected
