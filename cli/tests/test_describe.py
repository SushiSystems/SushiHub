# test_describe.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The catalogue is what the Typer app already knows, written down."""

import json

import jsonschema
import typer
from typer.testing import CliRunner

from sushihub import DISTRIBUTION
from sushihub.cli import app
from sushihub.describe import ALL_PRESENCE, catalogue

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


def test_the_catalogue_is_the_shared_one_with_hubs_distribution_and_presences():
    """hub's catalogue is sushicore's, called with hub's distribution and presences."""
    from sushicore import describe as core

    assert catalogue(app) == core.catalogue(app, distribution=DISTRIBUTION,
                                            applies_to=ALL_PRESENCE)
    assert all(c["applies_to"] == ["cloned", "linked", "binary"]
               for c in catalogue(app)["commands"])


def test_a_hidden_command_is_left_out_of_the_catalogue():
    """A hidden command does not appear in the catalogue."""
    tool = typer.Typer(name="tool")
    tool.command("shown")(lambda: None)
    tool.command("old", hidden=True)(lambda: None)

    assert [c["name"] for c in catalogue(tool)["commands"]] == ["shown"]


def test_describe_prints_the_catalogue_as_one_compact_utf8_line():
    """--describe writes the catalogue as compact UTF-8 JSON and one newline."""
    result = CliRunner().invoke(app, ["--describe"])

    assert result.exit_code == 0
    expected = json.dumps(catalogue(app), ensure_ascii=False).encode("utf-8") + b"\n"
    assert result.stdout_bytes == expected


def test_describe_lists_every_visible_command_and_no_hidden_one():
    """--describe names exactly the twenty-one commands the help screen shows."""
    document = json.loads(CliRunner().invoke(app, ["--describe"]).stdout)

    assert {c["name"] for c in document["commands"]} == {
        "init", "home", "status", "docs bundle",
        "add", "link", "install-cli", "update", "sync",
        "install", "doctor", "remove", "migrate",
        "gui build", "gui test", "gui run", "gui clean",
        "login", "logout", "whoami", "license",
    }


def test_no_command_help_repeats_a_stale_count_or_the_old_sushicore_delivery():
    """The help of init, add, install-cli and sync carries none of the four stale claims."""
    helps = " ".join(c["help"] for c in catalogue(app)["commands"])
    pages = " ".join(" ".join(CliRunner().invoke(app, [name, "--help"]).output.split())
                     for name in ("add", "install-cli", "init", "sync"))

    assert "install missing deps, then update" not in helps
    assert "Five of the six" not in pages
    assert "ships in this repository" not in pages
    assert "after cloning sushihub" not in pages
