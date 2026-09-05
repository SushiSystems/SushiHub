"""The schemas are the contract; a stream that violates them is a defect."""

import json
from pathlib import Path

import jsonschema
import pytest

CONTRACT = Path(__file__).resolve().parents[2] / "sushihub" / "contract"


def _schema(name):
    """Load the named schema from ``sushihub/contract/``."""
    return json.loads((CONTRACT / name).read_text(encoding="utf-8"))


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
