# pipx.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds a pipx client that records installs and upgrades and answers from a fixed table."""

from __future__ import annotations

from pathlib import Path

from ..pipx import Install


class InMemoryPipx:
    """Records each install and upgrade and reports the installs it was given.

    Args:
        available: What :meth:`available` reports.
        held: How pipx holds each distribution, by name.
        exit_code: The exit code every install and upgrade returns.
    """

    def __init__(self, *, available: bool = True, held: dict[str, Install] | None = None,
                 exit_code: int = 0) -> None:
        """Starts with no recorded install or upgrade."""
        self._available = available
        self._held = dict(held or {})
        self._exit_code = exit_code
        self.installs: list[tuple[Path, bool]] = []
        self.upgrades: list[str] = []

    def available(self) -> bool:
        """Returns the availability this client was given."""
        return self._available

    def install(self, pkg_dir: Path, *, editable: bool) -> int:
        """Records the package directory and the editable flag and returns the exit code."""
        self.installs.append((Path(pkg_dir), editable))
        return self._exit_code

    def installed(self, name: str) -> Install | None:
        """Returns how *name* is held, or None when it was not given."""
        return self._held.get(name)

    def upgrade(self, name: str) -> int:
        """Records the name and returns the exit code."""
        self.upgrades.append(name)
        return self._exit_code
