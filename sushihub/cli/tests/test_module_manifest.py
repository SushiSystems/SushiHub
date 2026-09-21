"""Reading the manifest a module writes about itself.

The file is written by hand in another repository, so most of what matters here
is what the reader refuses. `docs/reference/MODULE_MANIFEST.md` fixes the shape.
"""

from __future__ import annotations

import pytest

from sushistack.services.module_manifest import MANIFEST_FILE, read


def _checkout(root, name: str, body: str):
    """Create a checkout directory *name* under *root* carrying a manifest."""
    directory = root / name
    directory.mkdir(parents=True)
    (directory / MANIFEST_FILE).write_text(body, encoding="utf-8")
    return directory


def test_a_complete_manifest_reads_into_a_module(tmp_path):
    """Every key lands on the same Module the catalog produces."""
    directory = _checkout(tmp_path, "sushiruntime", """
[module]
name = "sushiruntime"
alias = "sr"
distribution = "source"
repo = "https://github.com/sushisystems/sushiruntime.git"
fragment = "cli/sushistack.deps.toml"
""")

    module = read(directory)

    assert module.name == "sushiruntime"
    assert module.alias == "sr"
    assert module.distribution == "source"
    assert module.repo == "https://github.com/sushisystems/sushiruntime.git"
    assert module.directory == "sushiruntime"
    assert module.fragment == "cli/sushistack.deps.toml"


def test_the_optional_keys_have_the_conventional_answers(tmp_path):
    """A module that is never cloned by name omits repo; fragment has one home."""
    directory = _checkout(tmp_path, "sushidsp", """
[module]
name = "sushidsp"
alias = "sd"
distribution = "source"
""")

    module = read(directory)

    assert module.repo == ""
    assert module.fragment == "cli/sushistack.deps.toml"


def test_a_checkout_without_a_manifest_answers_none(tmp_path):
    """Absence is the ordinary case and not an error; the catalog answers instead."""
    directory = tmp_path / "sushiai"
    directory.mkdir()

    assert read(directory) is None


def test_a_missing_required_key_names_itself(tmp_path):
    """A file that does not say what the module is called cannot be believed."""
    directory = _checkout(tmp_path, "sushiblas", '[module]\nname = "sushiblas"\nalias = "sb"\n')

    with pytest.raises(ValueError) as caught:
        read(directory)

    assert "distribution" in str(caught.value)


def test_a_name_that_disagrees_with_the_directory_is_refused(tmp_path):
    """Every module's cmake resolves a sibling by the directory, so the two must agree."""
    directory = _checkout(tmp_path, "sushiblas", """
[module]
name = "sushiruntime"
alias = "sb"
distribution = "source"
""")

    with pytest.raises(ValueError) as caught:
        read(directory)

    assert "sushiblas" in str(caught.value)
    assert "sushiruntime" in str(caught.value)


def test_an_unknown_key_is_ignored(tmp_path):
    """A newer module may add a key an older `hub` has never heard of."""
    directory = _checkout(tmp_path, "sushiai", """
[module]
name = "sushiai"
alias = "sa"
distribution = "source"
minimum_hub = "2.0"
""")

    assert read(directory).alias == "sa"


def test_an_unknown_table_is_refused(tmp_path):
    """A section the reader drops is a section nobody knows is missing."""
    directory = _checkout(tmp_path, "sushiai", """
[module]
name = "sushiai"
alias = "sa"
distribution = "source"

[build]
generator = "Ninja"
""")

    with pytest.raises(ValueError) as caught:
        read(directory)

    assert "build" in str(caught.value)


def test_a_file_without_the_module_table_is_refused(tmp_path):
    """The one table the format is made of cannot be the one that is missing."""
    directory = _checkout(tmp_path, "sushiai", 'name = "sushiai"\n')

    with pytest.raises(ValueError) as caught:
        read(directory)

    assert "module" in str(caught.value)
