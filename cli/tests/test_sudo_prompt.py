# test_sudo_prompt.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests when the hub asks for the sudo password before its progress display starts."""

from __future__ import annotations

import types

import pytest

from sushihub.setup import sudo_prompt

pytestmark = pytest.mark.small


class _Runner:
    """Records the commands it is asked to run."""

    commands: list[list[str]] = []

    def __init__(self, *_arguments: object) -> None:
        """Take what the real runner takes and keep nothing."""

    def run(self, command: list[str], _cwd, *, stdin=None) -> int:
        """Record *command* and report success."""
        self.commands.append(command)
        return 0


@pytest.fixture
def prompted(monkeypatch):
    """Return the commands run by a prime on a machine with sudo, a terminal and no superuser."""
    _Runner.commands = []
    monkeypatch.setattr(sudo_prompt, "os", types.SimpleNamespace(name="posix"))
    monkeypatch.setattr(sudo_prompt, "is_root", lambda: False)
    monkeypatch.setattr(sudo_prompt.shutil, "which", lambda _name: "/usr/bin/sudo")
    monkeypatch.setattr(sudo_prompt.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(sudo_prompt, "Runner", _Runner)
    monkeypatch.setattr(sudo_prompt.console, "warn", lambda _text: None)
    return _Runner.commands


def test_the_password_is_asked_once_with_a_validating_sudo(prompted):
    sudo_prompt.prime_sudo()
    assert prompted == [["sudo", "-p", sudo_prompt.K_SUDO_PROMPT, "-v"]]


def test_nothing_is_asked_of_the_superuser(prompted, monkeypatch):
    monkeypatch.setattr(sudo_prompt, "is_root", lambda: True)
    sudo_prompt.prime_sudo()
    assert prompted == []


def test_nothing_is_asked_where_sudo_is_not_installed(prompted, monkeypatch):
    monkeypatch.setattr(sudo_prompt.shutil, "which", lambda _name: None)
    sudo_prompt.prime_sudo()
    assert prompted == []


def test_nothing_is_asked_on_windows(prompted, monkeypatch):
    monkeypatch.setattr(sudo_prompt, "os", types.SimpleNamespace(name="nt"))
    sudo_prompt.prime_sudo()
    assert prompted == []
