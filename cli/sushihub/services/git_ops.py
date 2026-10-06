# git_ops.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Git primitives: running a command and asking whether a remote is reachable.

Every module checkout `hub` manages goes through these two calls, so a caller
never shells out to git on its own. The policy above them — what to pull, when
to fall back to a binary release — stays with its callers in
:mod:`sushihub.services.modules`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import console

#: Seconds `git ls-remote` may take before the source counts as out of reach.
REACHABLE_TIMEOUT = 15


def run(args: list[str], cwd: Path) -> int:
    """Run a git command, streaming its output. Return its exit code."""
    try:
        return subprocess.run(["git", *args], cwd=str(cwd)).returncode
    except FileNotFoundError:
        console.error("git not found on PATH. Install git and try again.")
        return 1


def source_reachable(repo: str) -> bool:
    """Report whether this machine's Git identity can read *repo*.

    Asks the remote for its default branch and nothing else, so a private
    repository the credentials do not open answers a non-zero exit code rather
    than a clone that fails halfway.

    Args:
        repo: The clone URL to ask about.
    """
    try:
        return subprocess.run(
            ["git", "ls-remote", "--exit-code", "-h", repo, "HEAD"],
            capture_output=True, timeout=REACHABLE_TIMEOUT).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
