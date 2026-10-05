# test_entry_point.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""`hub`'s entry point turns a failure the user can act on into one line and exit code 1."""

from __future__ import annotations

import json
import sys

import keyring.errors
import pytest
from sushicore.root_options import version_line
from typer.testing import CliRunner

from sushihub import DISTRIBUTION, cli, console
from sushihub.config import CHECKOUT_CLI_DIR, WORKSPACE_MARKER, workspace_file
from sushihub.services import session
from sushihub.services.identity import SushiAccount
from sushihub.services.token_store import KeyringStore


def _main(monkeypatch, capsys, *args: str) -> tuple[int, list[str], list[str]]:
    """Runs ``main()`` with *args* and returns its exit code, stdout lines and stderr lines."""
    monkeypatch.setattr(sys, "argv", ["hub", *args])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    captured = capsys.readouterr()
    return (caught.value.code,
            [line for line in captured.out.splitlines() if line.strip()],
            [line for line in captured.err.splitlines() if line.strip()])


def _one_message(lines: list[str]) -> str:
    """Returns the printed text unwrapped, asserting it is one error and no traceback."""
    text = "".join(lines)
    assert text.count("ERROR") == 1 and "Traceback" not in text
    return text


@pytest.fixture(autouse=True)
def fresh_console():
    """Drops the console a run built on the captured streams, so no later test prints to it."""
    yield
    console.set_machine(False)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Makes a throwaway workspace and runs the test inside it."""
    (tmp_path / WORKSPACE_MARKER).mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def nowhere(tmp_path, monkeypatch):
    """Runs the test in a directory that is not inside any workspace."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_a_malformed_theme_config_gives_one_line_and_exit_one(workspace, monkeypatch, capsys):
    """A theme file that does not parse ends in one error message and exit code 1."""
    legacy = workspace / CHECKOUT_CLI_DIR
    legacy.mkdir(parents=True)
    (legacy / "config.toml").write_text("[cli\ntheme = ", encoding="utf-8")

    code, out, err = _main(monkeypatch, capsys, "home")

    assert code == 1
    assert "config.toml" in _one_message(out + err)


def test_a_malformed_workspace_file_gives_one_line_and_exit_one(workspace, monkeypatch, capsys):
    """A workspace.toml that does not parse is reported without a traceback."""
    workspace_file(workspace).write_text("[tool\n", encoding="utf-8")

    code, out, err = _main(monkeypatch, capsys, "doctor")

    assert code == 1
    assert "workspace.toml" in "".join(out + err)
    assert "Traceback" not in "".join(out + err)


def test_a_malformed_theme_config_under_json_still_ends_in_one_result(
        workspace, monkeypatch, capsys):
    """The failed result event is emitted even when the console's own config is unreadable."""
    legacy = workspace / CHECKOUT_CLI_DIR
    legacy.mkdir(parents=True)
    (legacy / "config.toml").write_text("[cli\ntheme = ", encoding="utf-8")

    code, out, _err = _main(monkeypatch, capsys, "--json", "home")

    events = [json.loads(line) for line in out]
    assert code == 1
    assert [event["event"] for event in events] == ["line", "result"]
    assert events[-1] == {"event": "result", "ok": False, "payload": {}}


def test_a_command_outside_a_workspace_gives_one_line_and_exit_one(nowhere, monkeypatch, capsys):
    """A command that needs a workspace says so once and exits 1."""
    code, out, err = _main(monkeypatch, capsys, "home")

    assert code == 1
    assert "hub init" in _one_message(out + err)


def test_a_command_outside_a_workspace_under_json_ends_in_one_failed_result(
        nowhere, monkeypatch, capsys):
    """Under --json the same failure is one error line event and one failed result."""
    code, out, _err = _main(monkeypatch, capsys, "--json", "home")

    events = [json.loads(line) for line in out]
    assert code == 1
    assert [event["event"] for event in events] == ["line", "result"]
    assert events[0]["level"] == "error"
    assert events[-1] == {"event": "result", "ok": False, "payload": {}}


def test_gui_without_its_sources_under_json_ends_in_one_failed_result(
        workspace, monkeypatch, capsys):
    """A workspace without the desktop sources ends `hub gui` in exactly one result event."""
    code, out, _err = _main(monkeypatch, capsys, "--json", "gui", "clean")

    events = [json.loads(line) for line in out]
    assert code == 1
    assert [event["event"] for event in events].count("result") == 1
    assert events[-1]["ok"] is False


def test_a_successful_command_exits_zero(workspace, monkeypatch, capsys):
    """main() exits 0 after a command that succeeded."""
    code, out, _err = _main(monkeypatch, capsys, "--json", "home")

    assert code == 0
    assert json.loads(out[-1])["ok"] is True


@pytest.mark.parametrize("command", ["logout", "whoami", "license", "login"])
def test_an_account_command_without_a_keyring_gives_one_line_and_exit_one(
        workspace, monkeypatch, capsys, command):
    """Each account command reports a missing keyring backend as one error line."""
    def refuse(*_args, **_kwargs):
        """Fails the way keyring does on a machine with no backend."""
        raise keyring.errors.NoKeyringError("No recommended backend was available.")

    for name in ("get_password", "set_password", "delete_password"):
        monkeypatch.setattr(keyring, name, refuse)
    client = SushiAccount("http://127.0.0.1:9", KeyringStore(), now=lambda: 0.0)
    monkeypatch.setattr(session, "client", lambda: client)

    code, out, _err = _main(monkeypatch, capsys, "--json", command)

    events = [json.loads(line) for line in out]
    assert code == 1
    assert [event["level"] for event in events if event["event"] == "line"] == ["error"]
    assert events[-1] == {"event": "result", "ok": False, "payload": {}}


def test_version_prints_the_distribution_and_exits_zero():
    """--version prints the distribution with its installed version and runs no command."""
    result = CliRunner().invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == version_line(DISTRIBUTION)
    assert result.output.startswith("sushihub ")


def test_version_is_listed_on_the_help_screen():
    """The root help names --version."""
    assert "--version" in CliRunner().invoke(cli.app, ["--help"]).output


def test_the_module_entry_runs_main():
    """`python -m sushihub` goes through the same main() as the console script."""
    import sushihub.__main__ as module_entry

    assert module_entry.main is cli.main
