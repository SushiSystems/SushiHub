"""A checkout that describes itself, with and without a catalog entry.

This is what wave 6 exists to make true: `hub` knows a module because the module
said what it is, not only because `hub` shipped with its name.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sushistack.services import links, modules, presence
from sushistack.services.catalog import CATALOG
from sushistack.services.module_manifest import MANIFEST_FILE


def _describes(directory: Path, name: str, alias: str, distribution: str = "source") -> Path:
    """Create *directory* carrying a manifest that names it."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / MANIFEST_FILE).write_text(
        f'[module]\nname = "{name}"\nalias = "{alias}"\ndistribution = "{distribution}"\n',
        encoding="utf-8")
    return directory


def test_a_checkout_the_catalog_never_heard_of_is_known(tmp_path):
    """The acceptance criterion: no catalog entry, and `hub` knows it anyway."""
    _describes(tmp_path / "sushidsp", "sushidsp", "sd")

    known, problems = presence.workspace_modules(tmp_path)

    assert "sushidsp" not in CATALOG
    assert "sushidsp" in known
    assert known["sushidsp"].alias == "sd"
    assert problems == []


def test_the_catalog_still_answers_for_a_checkout_that_says_nothing(tmp_path):
    """A module with no manifest is exactly as known as it was before."""
    known, _ = presence.workspace_modules(tmp_path)

    assert list(known)[:len(CATALOG.names())] == CATALOG.names()


def test_the_checkout_wins_when_both_describe_it(tmp_path):
    """What is on disk is what the CLI was installed from, so it is the truth."""
    _describes(tmp_path / "sushiruntime", "sushiruntime", "srx")

    known, _ = presence.workspace_modules(tmp_path)

    assert CATALOG["sushiruntime"].alias == "sr"
    assert known["sushiruntime"].alias == "srx"


def test_the_catalog_keeps_its_order_and_the_rest_follow_by_name(tmp_path):
    """Two commands listing modules must list them the same way twice."""
    _describes(tmp_path / "zzz", "zzz", "z")
    _describes(tmp_path / "aaa", "aaa", "a")

    known, _ = presence.workspace_modules(tmp_path)

    assert list(known) == CATALOG.names() + ["aaa", "zzz"]


def test_a_linked_checkout_outside_the_root_is_read_too(tmp_path):
    """`hub link` points at a checkout elsewhere; its manifest counts the same."""
    elsewhere = _describes(tmp_path / "elsewhere" / "sushidsp", "sushidsp", "sd")
    root = tmp_path / "ws"
    root.mkdir()

    known, _ = presence.workspace_modules(root, {"sushidsp": str(elsewhere)})

    assert "sushidsp" in known


def test_a_manifest_that_will_not_read_is_reported_rather_than_raised(tmp_path):
    """One broken neighbour must not stop `hub status` describing the rest."""
    broken = tmp_path / "sushidsp"
    broken.mkdir()
    (broken / MANIFEST_FILE).write_text('[module]\nname = "sushidsp"\n', encoding="utf-8")

    known, problems = presence.workspace_modules(tmp_path)

    assert list(known) == CATALOG.names()
    assert len(problems) == 1
    assert "sushidsp" in problems[0]


class _Silent:
    """Swallow what a command prints, so no test writes to the real console.

    Under pytest's capture the shared Rich console can hold a stream that is
    already closed, which is a property of the harness rather than of `hub`.
    """

    def __getattr__(self, _name):
        return lambda *a, **k: None


@pytest.fixture(autouse=True)
def quiet(monkeypatch):
    """Give every test in this module a console that prints nothing."""
    monkeypatch.setattr(modules, "console", _Silent())


def test_link_accepts_a_checkout_that_describes_itself(tmp_path, monkeypatch):
    """`hub link` stopped being a catalog gate for a module that names itself."""
    checkout = _describes(tmp_path / "sushidsp", "sushidsp", "sd")
    (checkout / ".git").mkdir()
    written: dict[str, str] = {}
    monkeypatch.setattr(links, "registered", lambda: {})
    monkeypatch.setattr(links, "write", lambda name, path: written.update({name: str(path)}))
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)

    code = modules.link("sushidsp", str(checkout), skip_install=True,
                        provision=lambda dry_run: 0)

    assert code == 0
    assert written == {"sushidsp": str(checkout)}


def test_link_refuses_a_checkout_that_describes_a_different_module(tmp_path, monkeypatch):
    """A manifest naming something else is a mistake, not a rename."""
    checkout = _describes(tmp_path / "sushidsp", "sushidsp", "sd")
    monkeypatch.setattr(links, "registered", lambda: {})

    assert modules.link("sushitrack", str(checkout), skip_install=True,
                        provision=lambda dry_run: 0) == 1


def test_link_reports_a_manifest_that_will_not_read(tmp_path, monkeypatch):
    """A refused manifest reaches the user as a message, not a traceback."""
    checkout = tmp_path / "sushidsp"
    checkout.mkdir()
    (checkout / MANIFEST_FILE).write_text('[module]\nname = "sushidsp"\n', encoding="utf-8")
    monkeypatch.setattr(links, "registered", lambda: {})

    assert modules.link("sushidsp", str(checkout), skip_install=True,
                        provision=lambda dry_run: 0) == 1


def test_link_still_refuses_a_checkout_that_says_nothing(tmp_path, monkeypatch):
    """The catalog stays closed to a directory that makes no claim."""
    checkout = tmp_path / "stranger"
    checkout.mkdir()
    monkeypatch.setattr(links, "registered", lambda: {})

    assert modules.link("stranger", str(checkout), skip_install=True,
                        provision=lambda dry_run: 0) == 1
