"""What `hub link` records, where it records it, and which names it refuses."""

from __future__ import annotations

import pytest

from sushicore.workspace import WORKSPACE_CLI_DIR
from sushistack.config import MODULES_FILE, registered_modules
from sushistack.services import modules

from .test_presence import Recorder


@pytest.fixture
def cfg_dir(tmp_path, monkeypatch):
    """Point the link registry at a throwaway sushihub/cli directory.

    SUSHISTACK_HOME moves with it. Patching ``config_dir`` alone is not enough:
    ``_write_link`` merges onto whatever ``registered_modules()`` answers, and that
    reads the workspace root rather than ``config_dir()``. Left pinned to the
    repository root by the suite's conftest, every write here would merge onto the
    developer's own modules.local.toml -- green on a machine that happens to have
    the right links, red anywhere else.
    """
    target = tmp_path / WORKSPACE_CLI_DIR
    target.mkdir(parents=True)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.setattr(modules, "config_dir", lambda: target)
    return target


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line `hub link` prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_the_registry_file_carries_a_modules_table(cfg_dir, tmp_path):
    """_write_link writes a commented [modules] table naming the checkout."""
    modules._write_link("sushiruntime", tmp_path / "checkouts" / "sushiruntime")
    text = (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")
    assert "[modules]" in text
    assert "Managed by `hub link`" in text
    assert "sushiruntime" in text


def test_entries_are_written_in_name_order(cfg_dir, tmp_path):
    """Two links land sorted by module name, whatever order they were written in."""
    modules._write_link("sushiruntime", tmp_path / "a")
    modules._write_link("sushiai", tmp_path / "b")
    body = (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")
    assert body.index("sushiai") < body.index("sushiruntime")


def test_relinking_replaces_the_path_rather_than_repeating_it(cfg_dir, tmp_path):
    """Linking the same module twice leaves one entry, pointing at the newer path."""
    modules._write_link("sushiblas", tmp_path / "old")
    modules._write_link("sushiblas", tmp_path / "new")
    text = (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")
    assert text.count("sushiblas") == 1
    assert "new" in text


def test_the_registry_reads_back_what_link_wrote(cfg_dir, tmp_path):
    """registered_modules returns the name-to-path map _write_link recorded."""
    checkout = tmp_path / "checkouts" / "sushiai"
    modules._write_link("sushiai", checkout)
    assert registered_modules() == {"sushiai": str(checkout).replace("\\", "/")}


def test_link_refuses_sushicore(cfg_dir, recorder, tmp_path):
    """sushicore ships in the repository, so linking it is an error before any write."""
    assert modules.link("sushicore", str(tmp_path)) == 1
    assert recorder.said(
        "sushicore ships inside this repository and cannot be linked. Edit it in "
        "place, at `sushicore/`."
    )
    assert not (cfg_dir / MODULES_FILE).exists()


def test_link_refuses_a_name_outside_the_catalog(cfg_dir, recorder, tmp_path):
    """An unknown module is reported with the catalog's choices and nothing is written."""
    assert modules.link("sushiwater", str(tmp_path)) == 1
    assert recorder.said("Unknown module 'sushiwater'. Choose from: sushiruntime, "
                         "sushiengine, sushiai, sushiblas, sushidsp, sushitrack "
                         "(or their aliases: sr, se, sa, sb, sd, st).")
    assert not (cfg_dir / MODULES_FILE).exists()


def test_link_refuses_a_path_that_is_not_there(cfg_dir, recorder, tmp_path):
    """A missing directory is reported and nothing is written."""
    assert modules.link("sushiruntime", str(tmp_path / "nowhere")) == 1
    assert not (cfg_dir / MODULES_FILE).exists()


def test_link_takes_an_alias_and_records_the_full_name(cfg_dir, recorder, tmp_path):
    """`hub link sr <path>` records sushiruntime and skips provisioning when asked."""
    checkout = tmp_path / "sushiruntime"
    (checkout / ".git").mkdir(parents=True)
    assert modules.link("sr", str(checkout), skip_install=True,
                        provision=lambda dry: pytest.fail("provision ran")) == 0
    assert "sushiruntime" in (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")


def test_a_dry_run_writes_nothing(cfg_dir, recorder, tmp_path):
    """A dry run reports the link it would make and leaves the registry absent."""
    checkout = tmp_path / "sushiblas"
    (checkout / ".git").mkdir(parents=True)
    assert modules.link("sushiblas", str(checkout), dry_run=True, skip_install=True) == 0
    assert not (cfg_dir / MODULES_FILE).exists()
    assert recorder.said(f"(dry-run) would link sushiblas -> {checkout.resolve()}")
