# test_json_streams.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The schemas are the contract; a stream that violates them is a defect."""

import inspect
import json
import os
import webbrowser
from pathlib import Path

import jsonschema
import pytest
from typer.testing import CliRunner

from sushihub import console
from sushihub.cli import app
from sushihub.config import WORKSPACE_MARKER
from sushihub.services.token_store import KeyringStore, Tokens

from .support.contract_files import contract_schema

pytestmark = pytest.mark.medium


def _runner() -> CliRunner:
    """Build a runner that keeps stderr out of stdout on either Click generation."""
    if "mix_stderr" in inspect.signature(CliRunner.__init__).parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()


def _run(args, cwd):
    """Invoke ``hub`` in-process from *cwd*, with *cwd* as the workspace.

    ``hub init`` marks the directory the process runs in, not ``SUSHISTACK_HOME``,
    so the run happens inside the throwaway workspace and never in the checkout.
    """
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        return _runner().invoke(app, args, env={**os.environ, "SUSHISTACK_HOME": str(cwd)})
    finally:
        os.chdir(previous)


def _events(result):
    """Parse the event lines a run wrote to stdout."""
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


@pytest.fixture
def workspace(tmp_path):
    """Build a throwaway workspace: the marker alone, since the tool ships its own data."""
    (tmp_path / WORKSPACE_MARKER).mkdir()
    gui = tmp_path / "gui"
    gui.mkdir(parents=True)
    (gui / "CMakeLists.txt").write_text("", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("event", [
    {"event": "line", "level": "info", "message": "m"},
    {"event": "command", "command": "c"},
    {"event": "header", "title": "t"},
    {"event": "panel", "title": "t", "body": "b"},
    {"event": "table", "title": "", "columns": ["a"], "rows": [["1"]]},
    {"event": "progress", "label": "l", "index": 1, "count": 2, "fraction": None},
    {"event": "result", "ok": True, "payload": {}},
    {"event": "prompt", "id": "prompt-1", "message": "m", "default": None},
], ids=lambda event: event["event"])
def test_events_schema_accepts_each_kind(event):
    jsonschema.Draft202012Validator(contract_schema("events.schema.json")).validate(event)


@pytest.mark.parametrize("event", [
    {"event": "line", "level": "debug", "message": "m"},
    {"event": "header", "title": "t", "extra": 1},
], ids=["unknown level", "unknown key"])
def test_events_schema_rejects_what_it_does_not_know(event):
    validator = jsonschema.Draft202012Validator(contract_schema("events.schema.json"))
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(event)


def test_describe_schema_accepts_the_documented_example():
    v = jsonschema.Draft202012Validator(contract_schema("describe.schema.json"))
    v.validate({"program": "hub", "version": "1.0.0", "contract": "1", "commands": [
        {"name": "add", "help": "h", "applies_to": ["cloned", "linked", "binary"], "params": [
            {"name": "modules", "kind": "argument", "type": "string", "multiple": True, "required": True,
             "default": None, "choices": None, "flags": [], "help": "x"}]}]})


@pytest.fixture
def human_console_after():
    """Return the console to the terminal renderer once the test has chosen JSON."""
    yield
    console.set_machine(False)


def test_set_machine_before_first_print_switches_to_json(workspace, monkeypatch, capsys,
                                                         human_console_after):
    monkeypatch.setenv("SUSHISTACK_HOME", str(workspace))
    console.set_machine(True)
    console.info("hello")
    assert json.loads(capsys.readouterr().out.strip())["event"] == "line"


def test_describe_prints_a_valid_catalogue(workspace):
    r = _run(["--describe"], workspace)
    assert r.exit_code == 0
    jsonschema.Draft202012Validator(contract_schema("describe.schema.json")).validate(json.loads(r.stdout))


def test_home_under_json_ends_with_a_result_carrying_the_paths(workspace):
    r = _run(["--json", "home"], workspace)
    events = _events(r)
    assert events[-1]["event"] == "result" and events[-1]["ok"] is True
    assert events[-1]["payload"]["workspace"] == str(workspace)


def test_status_under_json_emits_a_table_and_a_result(workspace):
    r = _run(["--json", "status"], workspace)
    events = _events(r)
    kinds = [e["event"] for e in events]
    assert "table" in kinds and kinds[-1] == "result"
    assert "modules" in events[-1]["payload"]


def expect_valid_events(result) -> list[dict]:
    """Assert every event of the run fits the schema and return them."""
    validator = jsonschema.Draft202012Validator(contract_schema("events.schema.json"))
    events = _events(result)
    assert events, result.stderr
    for event in events:
        validator.validate(event)
    return events


@pytest.mark.parametrize("args", [
    ["init"], ["home"], ["status"], ["add", "sushiruntime", "--dry-run", "--skip-install"],
    ["update", "--dry-run"], ["link", "sushiruntime", ".", "--dry-run"], ["gui", "clean"],
])
def test_every_read_only_command_streams_valid_events(workspace, args):
    events = expect_valid_events(_run(["--json", *args], workspace))
    assert events[-1]["event"] == "result"


@pytest.fixture
def signed_in(fake_id, backend, monkeypatch):
    """Point the four Sushi Account commands at the fake server with a live session.

    The server is reached through SUSHI_ACCOUNT_URL and the session lives in the in-memory
    credential store; the browser is the one stdlib name replaced, so no window opens.
    """
    monkeypatch.setenv("SUSHI_ACCOUNT_URL", fake_id.url)
    monkeypatch.setattr(webbrowser, "open", lambda uri: True)
    KeyringStore().save(Tokens("access-1", "refresh-1", 1e12))
    return fake_id


@pytest.mark.parametrize("args", [["login"], ["logout"], ["whoami"], ["license"]])
def test_every_sushi_id_command_streams_valid_events(workspace, signed_in, args):
    signed_in.state.approved = True
    events = expect_valid_events(_run(["--json", *args], workspace))
    assert events[-1]["event"] == "result" and events[-1]["ok"] is True


def test_login_under_json_reports_each_poll_and_ends_with_the_email(workspace, signed_in):
    KeyringStore().clear()
    signed_in.state.approved = True
    signed_in.state.slow_down_once = True
    events = _events(_run(["--json", "login"], workspace))
    polls = [e for e in events if e["event"] == "progress"]
    assert [e["index"] for e in polls] == [1, 2]
    assert all(e["label"] == "login" and e["count"] == 0 for e in polls)
    assert events[-1]["payload"] == {"email": "dev@sushisystems.io"}


def test_whoami_under_json_emits_a_table_and_the_account(workspace, signed_in):
    events = _events(_run(["--json", "whoami"], workspace))
    table = [e for e in events if e["event"] == "table"][0]
    assert table["columns"] == ["Field", "Value"]
    assert events[-1]["payload"]["email"] == "dev@sushisystems.io"


def test_license_under_json_emits_a_table_and_the_licences(workspace, signed_in):
    events = _events(_run(["--json", "license"], workspace))
    table = [e for e in events if e["event"] == "table"][0]
    assert table["columns"] == ["Product", "Holder", "Expires"]
    assert table["rows"] == [["sushiengine", "account", "2027-03-01"],
                             ["sushiai", "org", "never"]]
    assert [item["product"] for item in events[-1]["payload"]["licenses"]] == [
        "sushiengine", "sushiai"]


def test_logout_under_json_clears_the_store(workspace, signed_in):
    events = _events(_run(["--json", "logout"], workspace))
    assert events[-1] == {"event": "result", "ok": True, "payload": {}}
    assert KeyringStore().load() is None
