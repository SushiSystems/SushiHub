# test_manifest_precedence.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A checkout that describes itself, with and without a catalog entry.

This is what wave 6 exists to make true: `hub` knows a module because the module
said what it is, not only because `hub` shipped with its name.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sushicore.console_memory import RecordingConsole

from sushihub.config import WORKSPACE_MARKER
from sushihub.services import links, modules, presence
from sushihub.services.catalog import CATALOG
from sushihub.services.memory.ports import memory_ports
from sushihub.services.module_manifest import MANIFEST_FILE

pytestmark = pytest.mark.medium


def _describes(directory: Path, name: str, alias: str, distribution: str = "source") -> Path:
    """Create *directory* carrying a manifest that names it."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / MANIFEST_FILE).write_text(
        f'[module]\nname = "{name}"\nalias = "{alias}"\ndistribution = "{distribution}"\n',
        encoding="utf-8")
    return directory


def test_a_checkout_the_catalog_never_heard_of_is_known(tmp_path):
    """The acceptance criterion: no catalog entry, and `hub` knows it anyway."""
    _describes(tmp_path / "sushiwater", "sushiwater", "sw")

    known, problems = presence.workspace_modules(tmp_path)

    assert "sushiwater" not in CATALOG
    assert "sushiwater" in known
    assert known["sushiwater"].alias == "sw"
    assert problems == []


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


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Make a throwaway workspace the link registry writes into, apart from the checkouts."""
    root = tmp_path / "ws"
    (root / WORKSPACE_MARKER).mkdir(parents=True)
    monkeypatch.setenv("SUSHISTACK_HOME", str(root))
    return root


def _link(name: str, checkout: Path, out: RecordingConsole) -> int:
    """Run `hub link` for *name* over *checkout*, printing into *out*, without an install."""
    return modules.link(name, str(checkout), skip_install=True,
                        provision=lambda dry_run: 0, ports=memory_ports(console=out))


def test_link_accepts_a_checkout_that_describes_itself(tmp_path, workspace):
    """`hub link` stopped being a catalog gate for a module that names itself."""
    checkout = _describes(tmp_path / "sushidsp", "sushidsp", "sd")
    (checkout / ".git").mkdir()

    assert _link("sushidsp", checkout, RecordingConsole()) == 0
    assert links.registered() == {"sushidsp": checkout.resolve().as_posix()}


def test_link_refuses_a_checkout_that_describes_a_different_module(tmp_path, workspace):
    """A manifest naming something else is a mistake, not a rename."""
    checkout = _describes(tmp_path / "sushidsp", "sushidsp", "sd")
    out = RecordingConsole()

    assert _link("sushiwater", checkout, out) == 1
    assert "describes itself as 'sushidsp'" in out.texts("error")[0]


@pytest.mark.parametrize("name", ["sushiblas", "sb"], ids=["catalog name", "alias"])
def test_link_refuses_a_catalog_module_for_a_checkout_that_describes_another(
        tmp_path, workspace, name):
    """Neither a catalog name nor its alias excuses a checkout that says it is something else."""
    checkout = _describes(tmp_path / "sushidsp", "sushidsp", "sd")

    assert _link(name, checkout, RecordingConsole()) == 1
    assert links.registered() == {}


def test_link_accepts_a_catalog_name_when_the_checkout_agrees(tmp_path, workspace):
    """A manifest that names the same module changes nothing about a catalog link."""
    checkout = _describes(tmp_path / "sushiruntime", "sushiruntime", "sr")

    assert _link("sushiruntime", checkout, RecordingConsole()) == 0
    assert links.registered() == {"sushiruntime": checkout.resolve().as_posix()}


def test_link_reports_an_unreadable_manifest_under_a_catalog_name(tmp_path, workspace):
    """A manifest that cannot be believed stops a catalog link the way it stops any other."""
    checkout = tmp_path / "sushiruntime"
    checkout.mkdir()
    (checkout / MANIFEST_FILE).write_text('[module]\nname = "sushiruntime"\n', encoding="utf-8")
    out = RecordingConsole()

    assert _link("sushiruntime", checkout, out) == 1
    assert len(out.texts("error")) == 1 and links.registered() == {}
