"""The schemas are the contract; a stream that violates them is a defect."""

import inspect
import json
import os
from pathlib import Path

import jsonschema
import pytest
from typer.testing import CliRunner

from sushistack.cli import app

CONTRACT = Path(__file__).resolve().parents[2] / "sushihub" / "contract"
MANIFESTS = Path(__file__).resolve().parents[1] / "manifests"


def _schema(name):
    """Load the named schema from ``sushihub/contract/``."""
    return json.loads((CONTRACT / name).read_text(encoding="utf-8"))


def _runner() -> CliRunner:
    """Build a runner that keeps stderr out of stdout on either Click generation."""
    if "mix_stderr" in inspect.signature(CliRunner.__init__).parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()


def _run(args, cwd):
    """Invoke ``ss`` in-process with *cwd* as the workspace."""
    return _runner().invoke(app, args, env={**os.environ, "SUSHISTACK_HOME": str(cwd)})


def _events(result):
    """Parse the event lines a run wrote to stdout."""
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


@pytest.fixture
def workspace(tmp_path):
    """Build a throwaway workspace with the marker, the base manifest and a config."""
    (tmp_path / ".sushistack").write_text("marker\n", encoding="utf-8")
    (tmp_path / "cli" / "manifests").mkdir(parents=True)
    (tmp_path / "cli" / "manifests" / "base.deps.toml").write_text(
        (MANIFESTS / "base.deps.toml").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "cli" / "config.toml").write_text(
        '[cli]\ntheme = "default"\n', encoding="utf-8")
    return tmp_path


def test_events_schema_accepts_each_kind():
    v = jsonschema.Draft202012Validator(_schema("events.schema.json"))
    for ev in [
        {"event": "line", "level": "info", "message": "m"},
        {"event": "command", "command": "c"},
        {"event": "header", "title": "t"},
        {"event": "panel", "title": "t", "body": "b"},
        {"event": "table", "title": "", "columns": ["a"], "rows": [["1"]]},
        {"event": "progress", "label": "l", "index": 1, "count": 2, "fraction": None},
        {"event": "result", "ok": True, "payload": {}},
        {"event": "prompt", "id": "prompt-1", "message": "m", "default": None},
    ]:
        v.validate(ev)


def test_events_schema_rejects_an_unknown_key_and_level():
    v = jsonschema.Draft202012Validator(_schema("events.schema.json"))
    with pytest.raises(jsonschema.ValidationError):
        v.validate({"event": "line", "level": "debug", "message": "m"})
    with pytest.raises(jsonschema.ValidationError):
        v.validate({"event": "header", "title": "t", "extra": 1})


def test_describe_schema_accepts_the_documented_example():
    v = jsonschema.Draft202012Validator(_schema("describe.schema.json"))
    v.validate({"program": "ss", "version": "1.0.0", "contract": "1", "commands": [
        {"name": "add", "help": "h", "applies_to": ["cloned", "linked", "binary"], "params": [
            {"name": "modules", "kind": "argument", "type": "string", "multiple": True, "required": True,
             "default": None, "choices": None, "flags": [], "help": "x"}]}]})


def test_set_machine_before_first_print_switches_to_json(capsys):
    import importlib

    from sushistack import console as c

    importlib.reload(c)
    c.set_machine(True)
    c.info("hello")
    assert json.loads(capsys.readouterr().out.strip())["event"] == "line"


def test_describe_prints_a_valid_catalogue(workspace):
    r = _run(["--describe"], workspace)
    assert r.exit_code == 0
    jsonschema.Draft202012Validator(_schema("describe.schema.json")).validate(json.loads(r.stdout))


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


@pytest.mark.parametrize("args", [
    ["init"], ["home"], ["status"], ["add", "sushiruntime", "--dry-run", "--skip-install"],
    ["update", "--dry-run"], ["link", "sushiruntime", ".", "--dry-run"],
])
def test_every_read_only_command_streams_valid_events(workspace, args):
    r = _run(["--json", *args], workspace)
    v = jsonschema.Draft202012Validator(_schema("events.schema.json"))
    events = _events(r)
    assert events, r.stderr
    for ev in events:
        v.validate(ev)
    assert events[-1]["event"] == "result"
