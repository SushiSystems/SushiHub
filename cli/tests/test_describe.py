# test_describe.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The catalogue is what the Typer app already knows, written down."""

import json

import click
import pytest
import typer
from typer.main import get_command
from typer.testing import CliRunner

from sushihub.cli import app
from sushihub.describe import catalogue

pytestmark = pytest.mark.small


def _params(name: str) -> dict:
    """Index the parameters of the catalogue command *name* by parameter name."""
    command = next(c for c in catalogue(app)["commands"] if c["name"] == name)
    return {p["name"]: p for p in command["params"]}


def _visible_names(group: click.Group, prefix: str = "") -> set[str]:
    """List the visible leaf commands under *group* as the catalogue names them."""
    names: set[str] = set()
    for name, command in group.commands.items():
        if command.hidden:
            continue
        if isinstance(command, click.Group):
            names |= _visible_names(command, f"{prefix}{name} ")
        else:
            names.add(f"{prefix}{name}")
    return names


def test_every_registered_command_appears_once_sorted():
    names = [c["name"] for c in catalogue(app)["commands"]]
    assert names == sorted(set(names))
    assert {"init", "home", "status", "add", "link", "install-cli", "update", "install",
            "sync", "doctor", "remove"} <= set(names)


def test_add_describes_its_modules_argument():
    modules = _params("add")["modules"]
    assert modules["kind"] == "argument" and modules["multiple"] is True


def test_add_describes_its_dry_run_flag():
    dry_run = _params("add")["dry_run"]
    assert dry_run["flags"] == ["--dry-run"] and dry_run["type"] == "boolean"


def test_add_help_carries_no_markup():
    add = next(c for c in catalogue(app)["commands"] if c["name"] == "add")
    assert "[cyan]" not in add["help"]


@pytest.mark.parametrize(("group", "children"), [
    ("gui", {"gui build", "gui test", "gui run", "gui clean"}),
    ("docs", {"docs bundle"}),
])
def test_a_nested_group_is_listed_by_its_children(group, children):
    names = [c["name"] for c in catalogue(app)["commands"]]
    assert children <= set(names)
    assert group not in names
    assert names == sorted(names)


def test_gui_build_describes_its_type_choice():
    build_type = _params("gui build")["build_type"]
    assert build_type["type"] == "choice"
    assert build_type["choices"] == ["debug", "release", "relwithdebinfo"]


def test_gui_build_describes_its_clean_flag_as_boolean():
    assert _params("gui build")["clean"]["type"] == "boolean"


def test_gui_build_describes_its_define_flag_as_repeatable():
    define = _params("gui build")["define"]
    assert define["multiple"] is True and define["flags"] == ["-D"]


def test_the_catalogue_names_the_program_and_applies_every_command_to_all_presences():
    document = catalogue(app)
    assert document["program"] == "hub"
    assert all(c["applies_to"] == ["cloned", "linked", "binary"] for c in document["commands"])


def test_a_hidden_command_is_left_out_of_the_catalogue():
    """A hidden command does not appear in the catalogue."""
    tool = typer.Typer(name="tool")
    tool.command("shown")(lambda: None)
    tool.command("old", hidden=True)(lambda: None)

    assert [c["name"] for c in catalogue(tool)["commands"]] == ["shown"]


def test_describe_prints_the_catalogue_as_one_compact_utf8_line():
    """--describe writes UTF-8 JSON on a single line ended by one newline."""
    result = CliRunner().invoke(app, ["--describe"])

    text = result.stdout_bytes.decode("utf-8")
    assert result.exit_code == 0
    assert text.endswith("\n") and text.count("\n") == 1
    assert json.loads(text)["program"] == "hub"


def test_describe_lists_every_visible_command_and_no_hidden_one():
    """--describe names exactly the visible commands of the Typer app."""
    document = json.loads(CliRunner().invoke(app, ["--describe"]).stdout)
    names = {c["name"] for c in document["commands"]}

    assert names == _visible_names(get_command(app))


def test_no_command_help_repeats_a_stale_count_or_the_old_sushicore_delivery():
    """The help of init, add, install-cli and sync carries none of the four stale claims."""
    helps = " ".join(c["help"] for c in catalogue(app)["commands"])
    pages = " ".join(" ".join(CliRunner().invoke(app, [name, "--help"]).output.split())
                     for name in ("add", "install-cli", "init", "sync"))

    assert "install missing deps, then update" not in helps
    assert "Five of the six" not in pages
    assert "ships in this repository" not in pages
    assert "after cloning sushihub" not in pages
