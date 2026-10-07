# test_docs_command.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""`hub docs bundle` builds the documentation bundle of the SushiHub checkout it runs in."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
from typer.testing import CliRunner

from sushihub import cli, console
from sushihub.describe import catalogue
from sushihub.errors import HubError

from .test_json_streams import _schema

K_FILES = {
    "docs/publish.toml": (
        'name = "sample"\n'
        'title = "Sample"\n'
        'summary = "A sample repository."\n'
        'sections = ["guides"]\n'
    ),
    "docs/README.md": "# Manual\n\n- [Starting](guides/STARTING.md)\n",
    "docs/guides/STARTING.md": "# Starting\n\nRun it.\n",
}
K_ARCHIVE = "build/docs/bundle/docs-bundle-1.2.3.tar.gz"


def _git(root: Path, *arguments: str) -> None:
    """Runs git in *root* with a fixed identity and no signing."""
    command = [
        "git", "-c", "user.name=t", "-c", "user.email=t@t.io", "-c", "commit.gpgsign=false",
        *arguments,
    ]
    subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)


def _main(monkeypatch, capsys, *args: str) -> tuple[int, list[str], list[str]]:
    """Runs ``main()`` with *args* and returns its exit code, stdout lines and stderr lines."""
    monkeypatch.setattr(sys, "argv", ["hub", *args])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    captured = capsys.readouterr()
    return (caught.value.code,
            [line for line in captured.out.splitlines() if line.strip()],
            [line for line in captured.err.splitlines() if line.strip()])


@pytest.fixture(autouse=True)
def fresh_console():
    """Drops the console a run built on the captured streams, so no later test prints to it."""
    yield
    console.set_machine(False)


@pytest.fixture
def checkout(tmp_path, monkeypatch) -> Path:
    """Returns a one-commit checkout that holds a publish list, outside any workspace."""
    root = tmp_path / "checkout"
    for relative, text in K_FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "sample")
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    return root


@pytest.fixture
def nowhere(tmp_path, monkeypatch) -> Path:
    """Runs the test in a directory that is inside neither a workspace nor a checkout."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_bundle_without_a_release_exits_two_and_names_the_option():
    """`hub docs bundle` refuses to run without --release and says which option is missing."""
    result = CliRunner().invoke(cli.app, ["docs", "bundle"])

    assert result.exit_code == 2
    assert "--release" in result.output


def test_bare_docs_prints_the_group_help_and_exits_two():
    """`hub docs` builds nothing by itself: it lists `bundle` and exits 2."""
    result = CliRunner().invoke(cli.app, ["docs"])

    assert result.exit_code == 2
    assert "bundle" in result.output


def test_the_catalogue_lists_docs_bundle_and_not_the_bare_group():
    """--describe carries `docs bundle` alone, since `hub docs` runs nothing."""
    names = [command["name"] for command in catalogue(cli.app)["commands"]]

    assert "docs bundle" in names
    assert "docs" not in names


def test_checkout_root_is_the_nearest_ancestor_that_holds_a_publish_list(checkout):
    """The lookup walks up from a folder inside the checkout to the checkout's root."""
    assert cli.checkout_root(checkout / "docs" / "guides") == checkout.resolve()


def test_checkout_root_outside_a_checkout_raises_the_hub_error(tmp_path):
    """A folder with no publish list above it is refused with hub's own error."""
    with pytest.raises(HubError, match="SushiHub checkout"):
        cli.checkout_root(tmp_path)


def test_bundle_outside_a_checkout_gives_one_line_and_exit_one(nowhere, monkeypatch, capsys):
    """Outside a SushiHub checkout the command says where it must run and exits 1."""
    code, out, err = _main(monkeypatch, capsys, "docs", "bundle", "--release", "1.2.3")

    text = " ".join(" ".join(out + err).split())
    assert code == 1
    assert text.count("ERROR") == 1 and "Traceback" not in text
    assert "SushiHub checkout" in text and "inside one" in text


def test_bundle_outside_a_checkout_under_json_ends_in_one_failed_result(
        nowhere, monkeypatch, capsys):
    """Under --json the same refusal is one error line event and one failed result."""
    code, out, _err = _main(monkeypatch, capsys, "--json", "docs", "bundle", "--release", "1.2.3")

    events = [json.loads(line) for line in out]
    assert code == 1
    assert [event["event"] for event in events] == ["line", "result"]
    assert events[0] == {"event": "line", "level": "error", "message": cli.K_NO_CHECKOUT}
    assert events[-1] == {"event": "result", "ok": False, "payload": {}}


def test_bundle_writes_the_archive_of_the_checkout_it_runs_in(checkout, monkeypatch, capsys):
    """Run from a folder inside a checkout, the command writes that checkout's bundle."""
    monkeypatch.chdir(checkout / "docs")

    code, out, err = _main(monkeypatch, capsys, "docs", "bundle", "--release", "1.2.3")

    assert code == 0, out + err
    assert (checkout / K_ARCHIVE).is_file()
    assert (checkout / (K_ARCHIVE + ".sha256")).is_file()
    assert "sha256" in " ".join(out + err)


def test_bundle_under_json_streams_valid_events_and_ends_in_one_result(
        checkout, monkeypatch, capsys):
    """Under --json the archive and its digest are success lines and one ok result ends them."""
    monkeypatch.chdir(checkout)

    code, out, _err = _main(monkeypatch, capsys, "--json", "docs", "bundle", "--release", "1.2.3")

    events = [json.loads(line) for line in out]
    validator = jsonschema.Draft202012Validator(_schema("events.schema.json"))
    for event in events:
        validator.validate(event)
    assert code == 0
    assert [event["event"] for event in events] == ["line", "line", "result"]
    assert [event["level"] for event in events[:2]] == ["success", "success"]
    assert "docs-bundle-1.2.3.tar.gz (1 pages)" in events[0]["message"]
    assert events[1]["message"].startswith("sha256 ")
    assert events[-1] == {"event": "result", "ok": True, "payload": {}}
