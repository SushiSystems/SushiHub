"""hub's help screen groups its commands under five headings and carries examples."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from sushihub.cli import app

K_GROUPS = {
    "Workspace": ["init", "home", "status"],
    "Modules": ["add", "link", "install-cli", "update", "sync"],
    "Dependencies": ["install", "doctor", "remove"],
    "Account": ["login", "logout", "whoami", "license"],
    "Desktop app": ["gui"],
}


def _run(*args: str) -> str:
    """Return the output of one hub invocation, asserting it exited zero."""
    result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


def _commands_by_heading(page: str) -> dict[str, list[str]]:
    """Return the first word of each row, keyed by the heading above it.

    A row starts two columns in; a wrapped description sits deeper and is skipped.
    """
    grouped: dict[str, list[str]] = {}
    heading = ""
    for line in page.splitlines():
        if line and not line.startswith(" "):
            heading = line.rstrip()
            grouped[heading] = []
        elif line.startswith("  ") and not line.startswith("   "):
            grouped[heading].append(line.split()[0])
    return grouped


def test_root_help_lists_the_five_groups_with_the_sub_app_last():
    lines = [line.rstrip() for line in _run("--help").splitlines()]
    positions = [lines.index(heading) for heading in K_GROUPS]
    assert positions == sorted(positions)


@pytest.mark.parametrize("heading", list(K_GROUPS))
def test_every_command_sits_under_its_own_group(heading):
    listed = _commands_by_heading(_run("--help"))[heading]
    assert [name for name in listed if name in K_GROUPS[heading]] == K_GROUPS[heading]


def test_no_command_is_listed_under_a_group_it_does_not_belong_to():
    grouped = _commands_by_heading(_run("--help"))
    for heading, names in K_GROUPS.items():
        assert set(grouped[heading]) == set(names)


def test_a_command_help_carries_examples():
    out = _run("add", "--help")
    assert "Examples" in out and "hub add sr" in out


def test_a_gui_command_help_carries_examples():
    out = _run("gui", "build", "--help")
    assert "Examples" in out and "hub gui build" in out
