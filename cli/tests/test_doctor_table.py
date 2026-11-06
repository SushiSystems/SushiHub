# test_doctor_table.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What `hub doctor` prints around its inventory table, and what `--json` still carries."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from sushicore import build_console, provision
from sushicore.provision import home as provision_home
from sushicore.provision import steps as provision_steps

from sushihub import console as hub_console
from sushihub.setup.pipeline import InstallContext
from sushihub.setup.steps import DetectStep

from .conftest import MemorySource

pytestmark = pytest.mark.small

_COLUMNS = ["Component", "Status", "Owner", "Detail"]
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

_OK_ROW = ("cmake", "OK", "shared", "/usr/bin/cmake")
_MISSING_ROW = ("adaptivecpp", "MISSING", "sushiruntime", "AdaptiveCpp (acpp)")
_NOT_NEEDED_ROW = ("cuda", "NOT NEEDED", "sushiruntime", "no present module declares it")
_ROWS = [_OK_ROW, _MISSING_ROW, _NOT_NEEDED_ROW]


@pytest.fixture
def bind_console(monkeypatch):
    """Return a function that points sushicore's provision output at a console built for a test.

    The binding made for the session is put back after the test.
    """
    def bind(*, machine: bool) -> None:
        """Bind a fake 100-column colour terminal, or JSON events when *machine*."""
        monkeypatch.setenv("COLUMNS", "100")
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.delenv("NO_COLOR", raising=False)
        built = build_console([], machine=machine)
        provision.bind_console(lambda: built)

    yield bind
    provision.bind_console(lambda: hub_console)
    provision_home.bind_root(None)


@pytest.fixture
def run_doctor(monkeypatch, fake_cfg):
    """Return a function that runs the detect step over given rows, off the machine."""

    def run(rows):
        """Run the step over *rows* and return its result."""
        monkeypatch.setattr(provision_steps, "refresh_windows_path", lambda: None)
        provision_home.bind_root(lambda: Path("/deps"))
        step = DetectStep(MemorySource([]), inventory=lambda ctx, all_deps: list(rows))
        return step.run(InstallContext(cfg=fake_cfg, rerun_command="hub install"))

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


def _in_order(lines: list[str], *needles: str) -> bool:
    """Report whether the first line holding each needle comes after the one before it."""
    positions = [_index_of(lines, needle) for needle in needles]
    return positions == sorted(positions)


def test_doctor_prints_each_owner_group_under_the_inventory_title(bind_console, capsys, run_doctor):
    bind_console(machine=False)
    run_doctor(_ROWS)
    lines = _human_lines(capsys)
    assert "shared" in lines and "sushiruntime" in lines
    assert _in_order(lines, "Environment inventory", "sushiruntime")


def test_doctor_prints_the_summary_after_the_groups(bind_console, capsys, run_doctor):
    bind_console(machine=False)
    run_doctor(_ROWS)
    assert _in_order(_human_lines(capsys), "sushiruntime", "1 OK | 1 missing | 1 not needed")


def test_doctor_prints_the_attention_list_after_the_summary(bind_console, capsys, run_doctor):
    bind_console(machine=False)
    run_doctor(_ROWS)
    assert _in_order(_human_lines(capsys), "1 OK | 1 missing | 1 not needed", "Needs attention",
                     "adaptivecpp  AdaptiveCpp (acpp)", "Run `hub install`")


def test_doctor_leaves_a_row_nothing_needs_out_of_the_attention_list(bind_console, capsys,
                                                                     run_doctor):
    bind_console(machine=False)
    run_doctor(_ROWS)
    lines = _human_lines(capsys)
    assert not any("cuda  " in line for line in lines[_index_of(lines, "Needs attention"):])


def test_doctor_prints_no_attention_list_when_nothing_is_missing(bind_console, capsys, run_doctor):
    bind_console(machine=False)
    run_doctor([_OK_ROW, _NOT_NEEDED_ROW])
    text = "\n".join(_human_lines(capsys))
    assert "1 OK | 1 not needed" in text
    assert "missing" not in text and "Needs attention" not in text and "hub install" not in text


def test_doctor_keeps_brackets_in_a_missing_detail_on_a_terminal(bind_console, capsys, run_doctor):
    bind_console(machine=False)
    run_doctor([("hdf5", "MISSING", "sushiengine", "HDF5 (hdf5[core,zlib])")])
    assert "hdf5  HDF5 (hdf5[core,zlib])" in "\n".join(_human_lines(capsys))


def test_doctor_json_table_event_is_the_ungrouped_one(bind_console, capsys, run_doctor):
    bind_console(machine=True)
    run_doctor(_ROWS)
    tables = [event for event in _events(capsys) if event["event"] == "table"]
    assert len(tables) == 1
    assert tables[0]["columns"] == _COLUMNS and tables[0]["rows"] == [list(r) for r in _ROWS]
    assert "group_by" not in tables[0]


def test_doctor_json_carries_the_summary_as_a_line_event(bind_console, capsys, run_doctor):
    bind_console(machine=True)
    run_doctor(_ROWS)
    lines = [(e["level"], e["message"]) for e in _events(capsys) if e["event"] == "line"]
    assert ("info", "1 OK | 1 missing | 1 not needed") in lines


def test_doctor_json_carries_the_attention_list_as_line_events(bind_console, capsys, run_doctor):
    bind_console(machine=True)
    run_doctor(_ROWS)
    lines = [(e["level"], e["message"]) for e in _events(capsys) if e["event"] == "line"]
    assert ("warn", "Needs attention") in lines
    assert ("info", "adaptivecpp  AdaptiveCpp (acpp)") in lines


def test_doctor_json_message_holds_a_bracketed_detail_unescaped(bind_console, capsys, run_doctor):
    bind_console(machine=True)
    run_doctor([("hdf5", "MISSING", "sushiengine", "HDF5 (hdf5[core,zlib])")])
    messages = [e["message"] for e in _events(capsys) if e["event"] == "line"]
    assert "hdf5  HDF5 (hdf5[core,zlib])" in messages


@pytest.mark.parametrize("machine", [False, True])
def test_doctor_reports_success_whatever_is_missing(bind_console, run_doctor, machine):
    bind_console(machine=machine)
    assert run_doctor(_ROWS).name == "OK"
