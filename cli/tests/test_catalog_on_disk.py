# test_catalog_on_disk.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Where the catalog meets files: its package data and the module lists the commands expand."""

from __future__ import annotations

import pytest
from sushicore.console_memory import RecordingConsole

from sushihub.services import modules
from sushihub.services.catalog import CATALOG, load_catalog
from sushihub.services.memory.git import InMemoryGit
from sushihub.services.memory.ports import memory_ports

from .test_add_binary import out, said, workspace  # noqa: F401  shared fixtures

pytestmark = pytest.mark.medium


def dry_run_add(names, out: RecordingConsole, git: InMemoryGit | None = None) -> int:
    """Run `hub add --dry-run` for *names* printing through *out*."""
    return modules.add(names, dry_run=True, provision=lambda dry_run: 0,
                       ports=memory_ports(console=out, git=git))


def modules_touched(out: RecordingConsole) -> list[str]:
    """The modules a dry run named, in the order it named them."""
    return [text.split(":")[0] for text in out.texts("info") if "(dry-run)" in text]


def test_the_packaged_catalog_is_readable_as_package_data():
    """The catalog loads through importlib.resources, as an installed wheel must."""
    assert load_catalog().names() == CATALOG.names()


@pytest.mark.parametrize("names", [None, [], ["all"]])
def test_an_empty_list_means_every_module(workspace, out, names):
    """Passing nothing, or 'all', expands to the whole catalog in order."""
    assert dry_run_add(names, out) == 0
    assert modules_touched(out) == CATALOG.names()


def test_aliases_expand_to_module_names(workspace, out):
    """A list of aliases acts on the modules they stand for, in the order given."""
    dry_run_add(["se", "sr"], out)
    assert modules_touched(out) == ["sushiengine", "sushiruntime"]


def test_a_name_outside_the_catalog_is_refused(workspace, out):
    """An unknown name stops the command, and the message names it and the choices."""
    git = InMemoryGit()
    assert dry_run_add(["sushiwater"], out, git) == 1
    assert said(out, "sushiwater") and said(out, "sushiruntime")
    assert git.calls == []
