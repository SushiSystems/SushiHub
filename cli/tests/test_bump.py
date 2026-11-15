# test_bump.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How `hub bump` moves a library in every module that takes it, lowest tier first."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sushihub import cli, console
from sushihub.services import bump
from sushihub.services.catalog import CATALOG
from sushihub.services.memory.git import InMemoryGit

from .support.workspace_files import workspace_at

K_OLD = "0123456789abcdef0123456789abcdef01234567"
K_NEW = "89abcdef0123456789abcdef0123456789abcdef"
K_LOG_REPO = CATALOG["sushilog"].repo


class FakeRunner:
    """Records every command and answers with scripted exit codes."""

    def __init__(self, failing: str = "") -> None:
        self.calls: list[tuple[list[str], Path]] = []
        self._failing = failing

    def run(self, args: list[str], cwd: Path) -> tuple[int, str]:
        """Record the call; fail the check of the module named *failing*."""
        self.calls.append((args, cwd))
        if cwd.name == self._failing and "check_all" in " ".join(args):
            return 1, "ok line\nFAIL: changelog entry missing\n"
        return 0, ""


def _module(root: Path, name: str, depends_on: list[str], check: bool = True) -> Path:
    """Write a cloned module pinning sushilog at the old commit."""
    checkout = root / name
    (checkout / ".git").mkdir(parents=True)
    (checkout / "cli").mkdir()
    deps = ", ".join(f'"{d}"' for d in ["sushilog", *depends_on])
    (checkout / "cli" / "sushistack.deps.toml").write_text(
        f'[module]\ndepends_on = [{deps}]\n\n'
        f'[sushisystems.sushilog]\nversion = "v0.1.0"\ncommit = "{K_OLD}"\n', encoding="utf-8")
    if check:
        (checkout / "tools").mkdir()
        (checkout / "tools" / "check_all.py").write_text("", encoding="utf-8")
    return checkout


@pytest.fixture
def three_tiers(tmp_path, monkeypatch):
    """ai builds on blas, blas on runtime; all three pin sushilog v0.1.0."""
    root = workspace_at(tmp_path, monkeypatch)
    _module(root, "sushiai", ["sushiblas"])
    _module(root, "sushiblas", ["sushiruntime"])
    _module(root, "sushiruntime", [])
    return root


def _git() -> InMemoryGit:
    """Return a git that knows sushilog v0.2.0."""
    return InMemoryGit().tag(K_LOG_REPO, "v0.2.0", K_NEW)


@pytest.mark.small
def test_bump_moves_pins_lowest_tier_first(three_tiers):
    """runtime moves before blas, blas before ai, and every fragment carries the new pin."""
    runner = FakeRunner()
    results = bump.bump(three_tiers, "sushilog", "v0.2.0", False, _git(), runner)
    assert [r.module for r in results] == ["sushiruntime", "sushiblas", "sushiai"]
    assert [cwd.name for _, cwd in runner.calls] == ["sushiruntime", "sushiblas", "sushiai"]
    for name in ("sushiruntime", "sushiblas", "sushiai"):
        text = (three_tiers / name / "cli" / "sushistack.deps.toml").read_text(encoding="utf-8")
        assert f'version = "v0.2.0"\ncommit = "{K_NEW}"' in text
    assert all(r.check_passed and r.old_pin == "v0.1.0" for r in results)


@pytest.mark.small
def test_bump_dry_run_writes_and_runs_nothing(three_tiers):
    """A dry run returns the plan and leaves every file and process alone."""
    before = {p: p.read_bytes() for p in three_tiers.rglob("*.toml")}
    runner = FakeRunner()
    results = bump.bump(three_tiers, "sushilog", "v0.2.0", True, _git(), runner)
    assert [r.module for r in results] == ["sushiruntime", "sushiblas", "sushiai"]
    assert runner.calls == []
    assert {p: p.read_bytes() for p in three_tiers.rglob("*.toml")} == before


@pytest.mark.small
def test_bump_reports_a_failing_check(three_tiers):
    """A red check is a result with its first failing line, not an exception."""
    results = bump.bump(three_tiers, "sushilog", "v0.2.0", False, _git(), FakeRunner("sushiblas"))
    failed = [r for r in results if r.check_passed is False]
    assert [(r.module, r.detail) for r in failed] == [
        ("sushiblas", "FAIL: changelog entry missing")]


@pytest.mark.small
def test_bump_rejects_an_unknown_tag(three_tiers):
    """A tag the library does not have stops the bump before any file changes."""
    with pytest.raises(bump.BumpError):
        bump.bump(three_tiers, "sushilog", "v9.9.9", False, _git(), FakeRunner())


@pytest.mark.small
def test_core_bump_syncs_every_repository(tmp_path, monkeypatch):
    """sushicore moves each CLI requirement and syncs the tools of every taker."""
    root = workspace_at(tmp_path, monkeypatch)
    (root / "cli").mkdir()
    (root / "cli" / "pyproject.toml").write_text(
        'dependencies = ["sushicore==0.9.0"]\n', encoding="utf-8")
    runtime = _module(root, "sushiruntime", [], check=False)
    (runtime / "cli" / "pyproject.toml").write_text(
        'dependencies = ["sushicore==0.9.0"]\n', encoding="utf-8")
    blas = _module(root, "sushiblas", ["sushiruntime"], check=False)
    (blas / "tools").mkdir()
    (blas / "tools" / "settings.py").write_text('K_TOOLING_PACKAGE = "sushicore"\n',
                                                encoding="utf-8")
    runner = FakeRunner()
    results = bump.bump(root, "sushicore", "v0.9.8", False, InMemoryGit(), runner)
    assert {r.module for r in results} == {"sushihub", "sushiruntime", "sushiblas"}
    assert all(r.synced for r in results)
    syncs = [args for args, _ in runner.calls if "sushicore.shared_tools" in args]
    assert len(syncs) == 3 and all(args[-2:] == ["--tag", "v0.9.8"] for args in syncs)
    assert '"sushicore==0.9.8"' in (runtime / "cli" / "pyproject.toml").read_text(encoding="utf-8")


@pytest.mark.medium
def test_hub_bump_dry_run_lists_every_module_and_writes_nothing(three_tiers, monkeypatch, capsys):
    """`hub bump sushilog v0.2.0 --dry-run` exits 0, names each module and leaves each fragment."""
    monkeypatch.setattr(cli, "_git", _git)
    monkeypatch.setattr(sys, "argv", ["hub", "bump", "sushilog", "v0.2.0", "--dry-run"])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    out = capsys.readouterr().out
    console.set_machine(False)
    assert caught.value.code == 0
    assert all(name in out for name in ("sushiruntime", "sushiblas", "sushiai"))
    text = (three_tiers / "sushiai" / "cli" / "sushistack.deps.toml").read_text(encoding="utf-8")
    assert f'commit = "{K_OLD}"' in text