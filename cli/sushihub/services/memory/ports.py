# ports.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds a :class:`~sushihub.services.ports.Ports` whose every port is held in memory."""

from __future__ import annotations

from sushicore.console_memory import RecordingConsole

from ..identity import Account
from ..ports import Ports
from .account import InMemoryAccount
from .git import InMemoryGit
from .host import FixedHost
from .pipx import InMemoryPipx

#: The platform :func:`memory_ports` names unless told otherwise.
DEFAULT_PLATFORM = "linux-x64"


def memory_ports(*, console: RecordingConsole | None = None, git: InMemoryGit | None = None,
                 pipx: InMemoryPipx | None = None, account: InMemoryAccount | None = None,
                 platform: str = DEFAULT_PLATFORM) -> Ports:
    """Returns ports that record and answer in memory; each one not given is a fresh adapter.

    The account not given is signed out and holds nothing.
    """
    held = account if account is not None else InMemoryAccount(Account("", "", ()))
    return Ports(console=console if console is not None else RecordingConsole(),
                 git=git if git is not None else InMemoryGit(),
                 pipx=pipx if pipx is not None else InMemoryPipx(),
                 account=lambda: held, host=FixedHost(platform))
