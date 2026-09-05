"""The catalogue is what the Typer app already knows, written down."""

import jsonschema

from sushistack.cli import app
from sushistack.describe import catalogue

from .test_json_streams import _schema


def test_catalogue_validates_against_its_schema():
    jsonschema.Draft202012Validator(_schema("describe.schema.json")).validate(catalogue(app))


def test_every_registered_command_appears_once_sorted():
    names = [c["name"] for c in catalogue(app)["commands"]]
    assert names == sorted(names)
    assert {"init", "home", "status", "add", "link", "install-cli", "update", "install",
            "sync", "doctor", "remove"} <= set(names)


def test_add_is_described_with_its_argument_and_flags():
    add = next(c for c in catalogue(app)["commands"] if c["name"] == "add")
    by_name = {p["name"]: p for p in add["params"]}
    assert by_name["modules"]["kind"] == "argument" and by_name["modules"]["multiple"] is True
    assert by_name["dry_run"]["flags"] == ["--dry-run"] and by_name["dry_run"]["type"] == "boolean"
    assert "[cyan]" not in add["help"]


def test_a_nested_group_is_listed_by_its_children():
    names = [c["name"] for c in catalogue(app)["commands"]]
    assert {"gui build", "gui test", "gui run", "gui clean"} <= set(names)
    assert "gui" not in names
    assert names == sorted(names)


def test_gui_build_is_described_with_its_type_choice_and_its_defines():
    build = next(c for c in catalogue(app)["commands"] if c["name"] == "gui build")
    by_name = {p["name"]: p for p in build["params"]}
    assert by_name["build_type"]["type"] == "choice"
    assert by_name["build_type"]["choices"] == ["debug", "release", "relwithdebinfo"]
    assert by_name["clean"]["type"] == "boolean"
    assert by_name["define"]["multiple"] is True and by_name["define"]["flags"] == ["-D"]
