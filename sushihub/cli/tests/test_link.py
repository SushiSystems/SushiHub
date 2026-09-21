"""What `hub link` records, where it records it, and which names it refuses."""

from __future__ import annotations

import pytest

from sushihub.config import WORKSPACE_MARKER, workspace_file
from sushihub.services import links, modules

from .test_presence import Recorder


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """Point the link registry at a throwaway workspace and return its file.

    SUSHISTACK_HOME is what moves it: both ``links.write`` and
    ``links.registered`` resolve the workspace root. Left pinned to the
    repository root by the suite's conftest, every write here would merge onto
    the developer's own registry -- green on a machine that happens to have the
    right links, red anywhere else.
    """
    (tmp_path / WORKSPACE_MARKER).mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    return workspace_file(tmp_path)


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line `hub link` prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_the_registry_file_carries_a_modules_table(registry, tmp_path):
    """links.write writes a [modules] table naming the checkout."""
    links.write("sushiruntime", tmp_path / "checkouts" / "sushiruntime")
    text = registry.read_text(encoding="utf-8")
    assert "[modules]" in text
    assert "sushiruntime" in text


def test_entries_are_written_in_name_order(registry, tmp_path):
    """Two links land sorted by module name, whatever order they were written in."""
    links.write("sushiruntime", tmp_path / "a")
    links.write("sushiai", tmp_path / "b")
    body = registry.read_text(encoding="utf-8")
    assert body.index("sushiai") < body.index("sushiruntime")


def test_relinking_replaces_the_path_rather_than_repeating_it(registry, tmp_path):
    """Linking the same module twice leaves one entry, pointing at the newer path."""
    links.write("sushiblas", tmp_path / "old")
    links.write("sushiblas", tmp_path / "new")
    text = registry.read_text(encoding="utf-8")
    assert text.count("sushiblas") == 1
    assert "new" in text


def test_the_registry_reads_back_what_link_wrote(registry, tmp_path):
    """links.registered returns the name-to-path map links.write recorded."""
    checkout = tmp_path / "checkouts" / "sushiai"
    links.write("sushiai", checkout)
    assert links.registered() == {"sushiai": str(checkout).replace("\\", "/")}


def test_link_refuses_sushicore(registry, recorder, tmp_path):
    """sushicore ships in the repository, so linking it is an error before any write."""
    assert modules.link("sushicore", str(tmp_path)) == 1
    assert recorder.said(
        "sushicore is not a stack module: it is a package every Sushi CLI "
        "installs from PyPI. To work on it, install your checkout over the "
        "release with `pip install -e <path>`."
    )
    assert not registry.exists()


def test_link_refuses_a_name_outside_the_catalog(registry, recorder, tmp_path):
    """An unknown module is reported with the catalog's choices and nothing is written."""
    assert modules.link("sushiwater", str(tmp_path)) == 1
    assert recorder.said("Unknown module 'sushiwater'. Choose from: sushiruntime, "
                         "sushiengine, sushiai, sushiblas "
                         "(or their aliases: sr, se, sa, sb).")
    assert not registry.exists()


def test_link_refuses_a_path_that_is_not_there(registry, recorder, tmp_path):
    """A missing directory is reported and nothing is written."""
    assert modules.link("sushiruntime", str(tmp_path / "nowhere")) == 1
    assert not registry.exists()


def test_link_takes_an_alias_and_records_the_full_name(registry, recorder, tmp_path):
    """`hub link sr <path>` records sushiruntime and skips provisioning when asked."""
    checkout = tmp_path / "sushiruntime"
    (checkout / ".git").mkdir(parents=True)
    assert modules.link("sr", str(checkout), skip_install=True,
                        provision=lambda dry: pytest.fail("provision ran")) == 0
    assert "sushiruntime" in registry.read_text(encoding="utf-8")


def test_a_dry_run_writes_nothing(registry, recorder, tmp_path):
    """A dry run reports the link it would make and leaves the registry absent."""
    checkout = tmp_path / "sushiblas"
    (checkout / ".git").mkdir(parents=True)
    assert modules.link("sushiblas", str(checkout), dry_run=True, skip_install=True) == 0
    assert not registry.exists()
    assert recorder.said(f"(dry-run) would link sushiblas -> {checkout.resolve()}")
