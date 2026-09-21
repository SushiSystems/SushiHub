"""What `hub doctor` prints around its inventory table, and what `--json` still carries."""

from __future__ import annotations

import json
import re

import pytest
from sushicore import build_console

from sushihub import config as hub_config
from sushihub import console as hub_console
from sushihub.setup import steps as steps_module
from sushihub.setup.pipeline import InstallContext
from sushihub.setup.steps import DetectStep

from .conftest import MemorySource

_COLUMNS = ["Component", "Status", "Owner", "Detail"]
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

_OK_ROW = ("cmake", "OK", "shared", "/usr/bin/cmake")
_MISSING_ROW = ("adaptivecpp", "MISSING", "sushiruntime", "AdaptiveCpp (acpp)")
_NOT_NEEDED_ROW = ("cuda", "NOT NEEDED", "sushiruntime", "no present module declares it")
_ROWS = [_OK_ROW, _MISSING_ROW, _NOT_NEEDED_ROW]


class _FixedConsole:
    """Stands in for the hub's lazy console with one console built by the test."""

    def __init__(self, built, machine: bool) -> None:
        """Hold the console to serve and whether it renders JSON events."""
        self._built = built
        self.machine = machine

    def attribute(self, name: str):
        """Resolve a console attribute the way ``LazyConsole.attribute`` does."""
        if name == "console":
            return self._built.console
        return getattr(self._built, name)


def _use_console(monkeypatch, *, machine: bool) -> None:
    """Route the hub's console to a fake 100-column colour terminal, or to JSON events."""
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    built = build_console([], machine=machine)
    monkeypatch.setattr(hub_console, "_lazy", _FixedConsole(built, machine))


@pytest.fixture
def run_doctor(monkeypatch, fake_cfg):
    """Return a function that runs the detect step over given rows, off the machine."""

    def run(rows):
        """Run the step over *rows* and return its result."""
        monkeypatch.setattr(DetectStep, "inventory_rows", lambda self, ctx, all_deps: list(rows))
        monkeypatch.setattr(DetectStep, "_report_readiness", lambda self, ctx, all_deps: None)
        monkeypatch.setattr(steps_module, "refresh_windows_path", lambda: None)
        monkeypatch.setattr(hub_config, "deps_dir", lambda: "/deps")
        return DetectStep(MemorySource([])).run(InstallContext(cfg=fake_cfg))

    return run


def _human_lines(capsys) -> list[str]:
    """Return the printed lines with their colour codes stripped."""
    return [_ANSI.sub("", line).rstrip() for line in capsys.readouterr().out.splitlines()]


def _events(capsys) -> list[dict]:
    """Parse the event lines the run wrote to stdout."""
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]


def _index_of(lines: list[str], needle: str) -> int:
    """Return the index of the first line containing *needle*."""
    return next(i for i, line in enumerate(lines) if needle in line)


def test_summarize_counts_each_status_under_its_own_text():
    counts, _ = DetectStep.summarize_inventory([*_ROWS, ("git", "OK", "shared", "/usr/bin/git")])
    assert counts == {"OK": 2, "MISSING": 1, "NOT NEEDED": 1}


def test_summarize_leaves_out_a_status_no_row_carries():
    counts, missing = DetectStep.summarize_inventory([_OK_ROW, _NOT_NEEDED_ROW])
    assert counts == {"OK": 1, "NOT NEEDED": 1} and missing == []


def test_summarize_counts_an_unforeseen_status_under_its_own_text():
    counts, _ = DetectStep.summarize_inventory([("x", "STALE", "shared", ""), _OK_ROW])
    assert counts == {"OK": 1, "STALE": 1}


def test_summarize_returns_the_missing_rows_in_table_order():
    other = ("ninja", "MISSING", "shared", "portable ninja")
    _, missing = DetectStep.summarize_inventory([other, _OK_ROW, _MISSING_ROW])
    assert missing == [other, _MISSING_ROW]


def test_doctor_prints_groups_then_summary_then_attention_list(monkeypatch, capsys, run_doctor):
    _use_console(monkeypatch, machine=False)
    run_doctor(_ROWS)
    lines = _human_lines(capsys)
    assert "shared" in lines and "sushiruntime" in lines
    order = [_index_of(lines, text) for text in (
        "Environment inventory", "sushiruntime", "1 OK | 1 missing | 1 not needed",
        "Needs attention", "adaptivecpp  AdaptiveCpp (acpp)", "Run `hub install`")]
    assert order == sorted(order)
    assert not any("cuda  " in line for line in lines[order[3]:])


def test_doctor_prints_no_attention_list_when_nothing_is_missing(monkeypatch, capsys, run_doctor):
    _use_console(monkeypatch, machine=False)
    run_doctor([_OK_ROW, _NOT_NEEDED_ROW])
    text = "\n".join(_human_lines(capsys))
    assert "1 OK | 1 not needed" in text
    assert "missing" not in text and "Needs attention" not in text and "hub install" not in text


def test_doctor_keeps_brackets_in_a_missing_detail_on_a_terminal(monkeypatch, capsys, run_doctor):
    _use_console(monkeypatch, machine=False)
    run_doctor([("hdf5", "MISSING", "sushiengine", "HDF5 (hdf5[core,zlib])")])
    assert "hdf5  HDF5 (hdf5[core,zlib])" in "\n".join(_human_lines(capsys))


def test_doctor_json_table_event_is_the_ungrouped_one(monkeypatch, capsys, run_doctor):
    _use_console(monkeypatch, machine=True)
    run_doctor(_ROWS)
    hub_console.table(_COLUMNS, [list(row) for row in _ROWS], title="Environment inventory")
    tables = [event for event in _events(capsys) if event["event"] == "table"]
    assert len(tables) == 2 and tables[0] == tables[1]
    assert tables[0]["columns"] == _COLUMNS and tables[0]["rows"] == [list(r) for r in _ROWS]
    assert "group_by" not in tables[0]


def test_doctor_json_carries_summary_and_attention_as_line_events(monkeypatch, capsys, run_doctor):
    _use_console(monkeypatch, machine=True)
    run_doctor(_ROWS)
    lines = [(e["level"], e["message"]) for e in _events(capsys) if e["event"] == "line"]
    assert ("info", "1 OK | 1 missing | 1 not needed") in lines
    assert ("warn", "Needs attention") in lines
    assert ("info", "adaptivecpp  AdaptiveCpp (acpp)") in lines


def test_doctor_json_message_holds_a_bracketed_detail_unescaped(monkeypatch, capsys, run_doctor):
    _use_console(monkeypatch, machine=True)
    run_doctor([("hdf5", "MISSING", "sushiengine", "HDF5 (hdf5[core,zlib])")])
    messages = [e["message"] for e in _events(capsys) if e["event"] == "line"]
    assert "hdf5  HDF5 (hdf5[core,zlib])" in messages


@pytest.mark.parametrize("machine", [False, True])
def test_doctor_reports_success_whatever_is_missing(monkeypatch, run_doctor, machine):
    _use_console(monkeypatch, machine=machine)
    assert run_doctor(_ROWS).name == "OK"
