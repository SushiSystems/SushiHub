# console_text.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides readers and spies for what a command printed."""

from __future__ import annotations

from sushicore.console_memory import RecordingConsole


def said(console: RecordingConsole, text: str) -> bool:
    """Report whether any line the console recorded contains *text*."""
    return any(text in call.text for call in console.calls)


class Recorder:
    """Stands in for the console and keeps every line and table it was given."""

    def __init__(self) -> None:
        """Start with no lines and no tables, and answer ``console.console`` with itself."""
        self.lines: list[str] = []
        self.tables: list[tuple[list[str], list[list[str]]]] = []
        self.console = self

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Record one table, and its cells as printed lines."""
        self.tables.append((columns, rows))
        self.lines.extend(str(cell) for row in rows for cell in row)

    def __getattr__(self, name: str):
        """Return a call that records its first argument as a printed line."""
        def record(*args, **kwargs) -> None:
            self.lines.extend(str(a) for a in args)
        return record

    def said(self, text: str) -> bool:
        """Report whether any recorded line contains *text*."""
        return any(text in line for line in self.lines)
