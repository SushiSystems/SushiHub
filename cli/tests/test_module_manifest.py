# test_module_manifest.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reading the manifest a module writes about itself.

The file is written by hand in another repository, so most of what matters here
is what the reader refuses. `docs/reference/MODULE_MANIFEST.md` fixes the shape.
"""

from __future__ import annotations

import re

import pytest

from sushihub.services.module_manifest import MANIFEST_FILE, parse, read

COMPLETE = """
[module]
name = "sushiruntime"
alias = "sr"
distribution = "source"
repo = "https://github.com/sushisystems/sushiruntime.git"
fragment = "cli/sushistack.deps.toml"
"""



def _checkout(root, name: str, body: str):
    """Create a checkout directory *name* under *root* carrying a manifest."""
    directory = root / name
    directory.mkdir(parents=True)
    (directory / MANIFEST_FILE).write_text(body, encoding="utf-8")
    return directory


@pytest.mark.medium
def test_a_manifest_file_reads_into_the_module_its_text_describes(tmp_path):
    """The checkout's manifest is read, and its directory name is the one the name must equal."""
    directory = _checkout(tmp_path, "sushiruntime", COMPLETE)

    assert read(directory) == parse(COMPLETE, "sushiruntime")


@pytest.mark.medium
def test_a_checkout_without_a_manifest_answers_none(tmp_path):
    """Absence is the ordinary case and not an error; the catalog answers instead."""
    directory = tmp_path / "sushiai"
    directory.mkdir()

    assert read(directory) is None


@pytest.mark.medium
def test_a_refused_manifest_file_names_its_path(tmp_path):
    """An error about a file says which file."""
    directory = _checkout(tmp_path, "sushiai", 'name = "sushiai"\n')

    with pytest.raises(ValueError, match=re.escape(str(directory / MANIFEST_FILE))):
        read(directory)


@pytest.mark.small
def test_a_complete_manifest_parses_into_a_module():
    """Every key lands on the same Module the catalog produces."""
    module = parse(COMPLETE, "sushiruntime")

    assert module.name == "sushiruntime"
    assert module.alias == "sr"
    assert module.distribution == "source"
    assert module.repo == "https://github.com/sushisystems/sushiruntime.git"
    assert module.directory == "sushiruntime"
    assert module.fragment == "cli/sushistack.deps.toml"


@pytest.mark.small
def test_the_optional_keys_have_the_conventional_answers():
    """A module that is never cloned by name omits repo; fragment has one home."""
    module = parse("""
[module]
name = "sushidsp"
alias = "sd"
distribution = "source"
""", "sushidsp")

    assert module.repo == ""
    assert module.fragment == "cli/sushistack.deps.toml"


@pytest.mark.small
def test_a_missing_required_key_names_itself():
    """A file that does not say what the module is called cannot be believed."""
    with pytest.raises(ValueError) as caught:
        parse('[module]\nname = "sushiblas"\nalias = "sb"\n', "sushiblas")

    assert "distribution" in str(caught.value)


@pytest.mark.small
def test_a_name_that_disagrees_with_the_directory_is_refused():
    """Every module's cmake resolves a sibling by the directory, so the two must agree."""
    with pytest.raises(ValueError) as caught:
        parse("""
[module]
name = "sushiruntime"
alias = "sb"
distribution = "source"
""", "sushiblas")

    assert "sushiblas" in str(caught.value)
    assert "sushiruntime" in str(caught.value)


@pytest.mark.small
def test_an_unknown_key_is_ignored():
    """A newer module may add a key an older `hub` has never heard of."""
    module = parse("""
[module]
name = "sushiai"
alias = "sa"
distribution = "source"
minimum_hub = "2.0"
""", "sushiai")

    assert module.alias == "sa"


@pytest.mark.small
def test_an_unknown_table_is_refused():
    """A section the reader drops is a section nobody knows is missing."""
    with pytest.raises(ValueError) as caught:
        parse("""
[module]
name = "sushiai"
alias = "sa"
distribution = "source"

[build]
generator = "Ninja"
""", "sushiai")

    assert "build" in str(caught.value)


@pytest.mark.small
def test_a_file_without_the_module_table_is_refused():
    """The one table the format is made of cannot be the one that is missing."""
    with pytest.raises(ValueError) as caught:
        parse('name = "sushiai"\n', "sushiai")

    assert "module" in str(caught.value)
