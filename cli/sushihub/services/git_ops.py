# git_ops.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Git primitives: running a command, asking whether a remote is reachable and reading a tag.

Every module checkout `hub` manages goes through these calls, so a caller
never shells out to git on its own. The policy above them — what to pull, when
to fall back to a binary release — stays with its callers in
:mod:`sushihub.services.modules`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .. import console

#: Seconds `git ls-remote` may take before the source counts as out of reach.
REACHABLE_TIMEOUT = 15

#: A full commit hash.
K_COMMIT = re.compile(r"[0-9a-f]{40}")

#: Seconds `git ls-remote` may take to read a tag.
K_LS_REMOTE_TIMEOUT = 30


class ProcessGit:
    """Runs git as a child process; the machine adapter of :class:`~.ports.GitClient`."""

    def run(self, args: list[str], cwd: Path) -> int:
        """Runs `git <args>` in *cwd*, streaming its output, and returns its exit code."""
        try:
            return subprocess.run(["git", *args], cwd=str(cwd)).returncode
        except FileNotFoundError:
            console.error("git not found on PATH. Install git and try again.")
            return 1

    def source_reachable(self, repo: str) -> bool:
        """Returns whether this machine's Git identity can read *repo*.

        Asks the remote for its default branch and nothing else, so a private repository the
        credentials do not open answers a non-zero exit code rather than a clone that fails
        halfway.
        """
        try:
            return subprocess.run(
                ["git", "ls-remote", "--exit-code", "-h", repo, "HEAD"],
                capture_output=True, timeout=REACHABLE_TIMEOUT).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def tag_commit(self, repo: str, version: str) -> str | None:
        """Returns the commit the tag *version* of *repo* points at, or None when not found.

        An annotated tag answers with the commit it peels to, not the tag object.
        """
        try:
            completed = subprocess.run(
                ["git", "ls-remote", "--tags", repo, f"refs/tags/{version}",
                 f"refs/tags/{version}^{{}}"],
                capture_output=True, text=True, timeout=K_LS_REMOTE_TIMEOUT)
        except (OSError, subprocess.SubprocessError):
            return None
        refs = dict(reversed(line.split("	", 1))
                    for line in completed.stdout.splitlines() if "	" in line)
        commit = refs.get(f"refs/tags/{version}^{{}}") or refs.get(f"refs/tags/{version}")
        return commit if commit and K_COMMIT.fullmatch(commit) else None
