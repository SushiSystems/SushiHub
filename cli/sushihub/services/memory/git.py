# git.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds a git client that records each command and answers scripted exit codes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GitCall:
    """One git command a client was asked to run.

    Attributes:
        args: The words after `git`.
        cwd: The folder the command was to run in.
    """

    args: tuple[str, ...]
    cwd: Path


class InMemoryGit:
    """Records each git command in order and answers the exit codes scripted in advance.

    A command with no script left exits 0. A repository counts as reachable only when it was
    named to :meth:`reach`, and a tag is found only when it was named to :meth:`tag`.
    """

    def __init__(self) -> None:
        """Starts with no recorded commands, no scripted codes and no reachable repository."""
        self.calls: list[GitCall] = []
        self.asked: list[str] = []
        self._codes: list[int] = []
        self._reachable: set[str] = set()
        self._tags: dict[tuple[str, str], str] = {}

    def script(self, exit_code: int) -> "InMemoryGit":
        """Queues the exit code of the next unanswered command and returns this client."""
        self._codes.append(exit_code)
        return self

    def reach(self, repo: str) -> "InMemoryGit":
        """Makes *repo* reachable and returns this client."""
        self._reachable.add(repo)
        return self

    def tag(self, repo: str, version: str, commit: str) -> "InMemoryGit":
        """Makes the tag *version* of *repo* point at *commit* and returns this client."""
        self._tags[(repo, version)] = commit
        return self

    def run(self, args: list[str], cwd: Path) -> int:
        """Records the command and returns the next scripted exit code, or 0."""
        self.calls.append(GitCall(tuple(args), Path(cwd)))
        return self._codes.pop(0) if self._codes else 0

    def source_reachable(self, repo: str) -> bool:
        """Records the question and returns whether *repo* was made reachable."""
        self.asked.append(repo)
        return repo in self._reachable

    def tag_commit(self, repo: str, version: str) -> str | None:
        """Returns the commit the tag was made to point at, or None when it was not."""
        return self._tags.get((repo, version))
