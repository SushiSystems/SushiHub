# test_pin_report.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What `hub pins` reports over a workspace whose modules pin the same library at two versions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from sushihub import cli, console
from sushihub.errors import HubError
from sushihub.services import pin_report
from sushihub.services.catalog import library_repo
from sushihub.services.memory.git import InMemoryGit

from .support.workspace_files import workspace_at

pytestmark = pytest.mark.medium

K_COMMIT = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture(autouse=True)
def fresh_console():
    """Drops the console a run built on the captured streams, so no later test prints to it."""
    yield
    console.set_machine(False)


def _module(root: Path, name: str, runtime: str | None = None, core: str | None = None) -> None:
    """Make a cloned module that pins sushiruntime at *runtime* and requires *core*, as given."""
    checkout = root / name
    (checkout / ".git").mkdir(parents=True)
    (checkout / "cli").mkdir()
    if runtime is not None:
        (checkout / "cli" / "sushistack.deps.toml").write_text(
            f'[module]\ndepends_on = ["sushiruntime"]\n\n[sushisystems.sushiruntime]\nversion = "{runtime}"\ncommit = "{K_COMMIT}"\n',
            encoding="utf-8")
    if core is not None:
        (checkout / "cli" / "pyproject.toml").write_text(
            f'[project]\ndependencies = [\n    "{core}",\n]\n', encoding="utf-8")


def _hub(monkeypatch, capsys, *args: str) -> tuple[int, str]:
    """Run `hub pins` with *args* and return its exit code and standard output."""
    monkeypatch.setattr(sys, "argv", ["hub", "pins", *args])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    return caught.value.code, capsys.readouterr().out


def test_a_library_pinned_at_two_versions_is_listed_and_exits_one(tmp_path, monkeypatch, capsys):
    """SushiBLAS at v0.5.1 and SushiAI at v0.5.2 are one split of sushiruntime."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiblas", runtime="v0.5.1")
    _module(tmp_path, "sushiai", runtime="v0.5.2")
    code, _ = _hub(monkeypatch, capsys)
    report = pin_report.collect(tmp_path)
    assert code == 1
    assert [(s.dependency, s.modules_by_version) for s in report.splits] == [
        ("sushiruntime", {"v0.5.1": ("sushiblas",), "v0.5.2": ("sushiai",)})]


def test_modules_on_one_version_exit_zero(tmp_path, monkeypatch, capsys):
    """Two modules at the same tag leave no split."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiblas", runtime="v0.5.2")
    _module(tmp_path, "sushiai", runtime="v0.5.2")
    code, _ = _hub(monkeypatch, capsys)
    assert code == 0
    assert pin_report.collect(tmp_path).splits == ()


def test_a_sushicore_requirement_split_is_detected(tmp_path, monkeypatch, capsys):
    """Two lower bounds, 0.10.4 and 0.13.2, split sushicore."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiblas", core="sushicore>=0.18.0")
    _module(tmp_path, "sushiai", core="sushicore>=0.18.0")
    code, _ = _hub(monkeypatch, capsys)
    assert code == 1
    assert [s.dependency for s in pin_report.collect(tmp_path).splits] == ["sushicore"]


def test_a_sushicore_range_split_is_detected(tmp_path, monkeypatch, capsys):
    """`>=0.10.4,<0.11` and `>=0.13.2,<0.14` split sushicore by their lower bounds."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiblas", core="sushicore>=0.10.4,<0.11")
    _module(tmp_path, "sushiai", core="sushicore>=0.13.2,<0.14")
    code, _ = _hub(monkeypatch, capsys)
    splits = pin_report.collect(tmp_path).splits
    assert code == 1
    assert [(s.dependency, s.modules_by_version) for s in splits] == [
        ("sushicore", {"0.10.4": ("sushiblas",), "0.13.2": ("sushiai",)})]


def test_latest_reads_the_tag_through_the_git_port(tmp_path, monkeypatch, capsys):
    """`hub pins --latest --json` takes each library's latest tag from the in-memory git."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiblas", runtime="v0.5.2")
    git = InMemoryGit().latest(library_repo("sushiruntime"), "v0.6.0")
    monkeypatch.setattr(cli, "_git", lambda: git)
    code, out = _hub(monkeypatch, capsys, "--latest", "--json")
    payloads = [event["payload"] for event in map(json.loads, (l for l in out.splitlines() if l.startswith("{")))
                if isinstance(event.get("payload"), dict) and "pins" in event["payload"]]
    assert code == 0
    assert payloads[-1]["pins"][0]["latest"] == "v0.6.0"


def test_json_carries_each_pin_and_each_split(tmp_path, monkeypatch, capsys):
    """The JSON run prints the pins and the splits it found."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiblas", runtime="v0.5.1")
    _module(tmp_path, "sushiai", runtime="v0.5.2")
    _, out = _hub(monkeypatch, capsys, "--json")
    payloads = [event["payload"] for event in map(json.loads, (l for l in out.splitlines() if l.startswith("{")))
                if isinstance(event.get("payload"), dict) and "pins" in event["payload"]]
    assert payloads[-1]["splits"] == [{"dependency": "sushiruntime",
                                       "versions": {"v0.5.1": ["sushiblas"],
                                                    "v0.5.2": ["sushiai"]}}]


def test_a_fragment_that_pins_without_depending_is_refused_as_a_hub_error(tmp_path, monkeypatch):
    """The reader's ValueError reaches the entry point as a one-line HubError."""
    workspace_at(tmp_path, monkeypatch)
    _module(tmp_path, "sushiai", runtime="v0.5.2")
    fragment = tmp_path / "sushiai" / "cli" / "sushistack.deps.toml"
    fragment.write_text(fragment.read_text(encoding="utf-8").replace('["sushiruntime"]', "[]"),
                        encoding="utf-8")
    with pytest.raises(HubError):
        pin_report.collect(tmp_path)
