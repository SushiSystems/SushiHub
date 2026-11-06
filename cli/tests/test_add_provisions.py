# test_add_provisions.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Bringing a module in brings its dependencies with it."""

from __future__ import annotations

import pytest

from sushihub.services import links, modules
from sushihub.services.memory.git import InMemoryGit
from sushihub.services.memory.pipx import InMemoryPipx
from sushihub.services.memory.ports import memory_ports

from .support.console_text import said
from .support.release_files import binary_install

pytestmark = pytest.mark.medium


def test_add_provisions_once_after_a_new_clone(workspace, out):
    """A module that was cloned triggers one provisioning run, not a dry one."""
    calls = []
    rc = modules.add(["sushiruntime"], provision=lambda dry_run: calls.append(dry_run) or 0,
                     ports=memory_ports(console=out))
    assert rc == 0 and calls == [False]


def test_add_skips_provision_when_nothing_new(workspace, out):
    """A module already cloned brings nothing new, so nothing is provisioned."""
    (workspace / "sushiruntime" / ".git").mkdir(parents=True)
    calls = []
    modules.add(["sushiruntime"], provision=lambda dry_run: calls.append(dry_run) or 0,
                ports=memory_ports(console=out))
    assert calls == []


def test_add_honours_skip_install(workspace, out):
    """skip_install clones the module and provisions nothing."""
    calls = []
    git = InMemoryGit()
    modules.add(["sushiruntime"], skip_install=True,
                provision=lambda dry_run: calls.append(dry_run) or 0,
                ports=memory_ports(console=out, git=git))
    assert (calls, [call.args[0] for call in git.calls]) == ([], ["clone"])


def test_add_with_skip_install_says_to_run_hub_install(workspace, out):
    """The skipped provisioning is named, with the command that does it later."""
    modules.add(["sushiruntime"], skip_install=True, provision=lambda dry_run: 0,
                ports=memory_ports(console=out))
    assert said(out, "run `hub install` to pick up what the new modules need.")


def test_add_leaves_a_binary_module_alone(workspace, out):
    """A binary install is neither cloned nor provisioned."""
    binary_install(workspace / "sushiengine", "1.4.2")
    calls = []
    git = InMemoryGit()
    rc = modules.add(["sushiengine"], provision=lambda dry_run: calls.append(dry_run) or 0,
                     ports=memory_ports(console=out, git=git))
    assert (rc, git.calls, calls) == (0, [], [])


def test_add_skips_a_linked_module_naming_its_path_and_installs_its_cli(workspace, out):
    """A linked module is not cloned; its link path is named and its CLI is installed."""
    checkout = workspace / "elsewhere" / "sushiruntime"
    (checkout / "cli").mkdir(parents=True)
    (checkout / "cli" / "pyproject.toml").write_text("", encoding="utf-8")
    links.write("sushiruntime", checkout)
    git = InMemoryGit()
    pipx = InMemoryPipx()
    modules.add(["sushiruntime"], provision=lambda dry_run: 0,
                ports=memory_ports(console=out, git=git, pipx=pipx))
    assert said(out, f"sushiruntime: linked to {checkout.resolve().as_posix()}")
    assert (git.calls, pipx.installs) == ([], [(checkout.resolve() / "cli", True)])


def test_add_reports_a_failed_clone_and_exits_one(workspace, out):
    """A clone that exits non-zero is reported and the command returns 1."""
    rc = modules.add(["sushiruntime"], provision=lambda dry_run: pytest.fail("provisioned"),
                     ports=memory_ports(console=out, git=InMemoryGit().script(128)))
    assert rc == 1
    assert said(out, "sushiruntime: clone failed.")
