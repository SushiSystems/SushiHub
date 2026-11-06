# test_self_update.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""`hub update` updates `hub` itself the way `hub` was installed.

An install from the index is upgraded with pipx; an editable install tracks a
checkout and is pulled. Neither branch may reach the network or the machine's
real pipx, so both are answered by the in-memory ports.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sushicore.console_memory import RecordingConsole

from sushihub.config import WORKSPACE_MARKER
from sushihub.services import modules
from sushihub.services.memory.git import GitCall, InMemoryGit
from sushihub.services.memory.pipx import InMemoryPipx
from sushihub.services.memory.ports import memory_ports
from sushihub.services.pipx import Install

pytestmark = pytest.mark.medium


@pytest.fixture
def workspace(tmp_path, monkeypatch) -> Path:
    """A throwaway workspace with no module in it and no git tree."""
    (tmp_path / WORKSPACE_MARKER).mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    return tmp_path


def _checkout(root: Path) -> Path:
    """Make *root* look like a git checkout holding the CLI package."""
    (root / ".git").mkdir(parents=True)
    package = root / "sushihub" / "cli"
    package.mkdir(parents=True)
    return package


def _update(workspace: Path, *, held: dict[str, Install], dry_run: bool = False,
            exit_code: int = 0):
    """Run `hub update all` against the in-memory ports; return git, pipx and the console."""
    git, pipx, out = InMemoryGit(), InMemoryPipx(held=held, exit_code=exit_code), RecordingConsole()
    modules.update(["all"], dry_run=dry_run, ports=memory_ports(console=out, git=git, pipx=pipx))
    return git, pipx, out


def _said(out: RecordingConsole, fragment: str) -> bool:
    """Whether any line the console recorded contains *fragment*."""
    return any(fragment in call.text for call in out.calls)


def test_an_index_install_is_upgraded_with_pipx(workspace):
    """pipx holds `hub` by name, so pipx upgrades it."""
    _git, pipx, _out = _update(workspace, held={"sushihub": Install(None)})
    assert pipx.upgrades == ["sushihub"]


def test_an_index_install_is_not_pulled_with_git(workspace):
    """An install from the index has no checkout, so git is never run."""
    git, _pipx, _out = _update(workspace, held={"sushihub": Install(None)})
    assert git.calls == []


def test_an_editable_install_pulls_its_own_checkout(workspace, tmp_path_factory):
    """The checkout pipx recorded is pulled, not the workspace it was asked about."""
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    package = _checkout(elsewhere)
    git, _pipx, _out = _update(workspace, held={"sushihub": Install(package)})
    assert git.calls == [GitCall(("pull", "--ff-only"), elsewhere)]


def test_an_editable_install_is_not_upgraded_with_pipx(workspace, tmp_path_factory):
    """An editable install tracks a checkout, so pipx upgrades nothing."""
    package = _checkout(tmp_path_factory.mktemp("elsewhere"))
    _git, pipx, _out = _update(workspace, held={"sushihub": Install(package)})
    assert pipx.upgrades == []


@pytest.mark.parametrize("editable", [False, True], ids=["index", "editable"])
def test_neither_branch_runs_under_dry_run(workspace, tmp_path_factory, editable):
    """A dry run says what it would do and touches nothing."""
    source = _checkout(tmp_path_factory.mktemp("elsewhere")) if editable else None
    git, pipx, _out = _update(workspace, held={"sushihub": Install(source)}, dry_run=True)
    assert (git.calls, pipx.upgrades) == ([], [])


def test_a_workspace_that_is_no_checkout_is_left_alone(workspace):
    """pipx knows no `hub` and the workspace is no git tree, so nothing happens."""
    git, pipx, _out = _update(workspace, held={})
    assert (git.calls, pipx.upgrades) == ([], [])


def test_an_editable_install_outside_a_checkout_warns(workspace, tmp_path_factory):
    """A recorded source with no .git above it is reported."""
    loose = tmp_path_factory.mktemp("loose") / "cli"
    loose.mkdir()
    _git, _pipx, out = _update(workspace, held={"sushihub": Install(loose)})
    assert _said(out, "not a git checkout")


def test_an_editable_install_outside_a_checkout_is_not_pulled(workspace, tmp_path_factory):
    """A recorded source with no .git above it is not pulled blindly."""
    loose = tmp_path_factory.mktemp("loose") / "cli"
    loose.mkdir()
    git, pipx, _out = _update(workspace, held={"sushihub": Install(loose)})
    assert (git.calls, pipx.upgrades) == ([], [])


def test_a_failed_upgrade_warns_rather_than_raising(workspace):
    """pipx returning non-zero must not stop the rest of `hub update`."""
    _git, _pipx, out = _update(workspace, held={"sushihub": Install(None)}, exit_code=1)
    assert _said(out, "self-update failed")
