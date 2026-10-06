# console.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Exposes the SushiHub console, built on first use over :mod:`sushicore`.

Every name this module exposes resolves through :class:`~sushicore.cli_console.LazyConsole`.
The names, and why the console is built late, are in cli/README.md, "Notes on the source".
"""

from __future__ import annotations

from pathlib import Path

from sushicore import build_console
from sushicore.cli_console import LazyConsole
from sushicore.errors import SushiCoreError

from .config import find_workspace_root, legacy_cli_dir


def _theme_dir() -> Path:
    """Returns the directory the `[cli]` theme is read from.

    Raises:
        SystemExit: Outside a workspace, which is how
            :class:`~sushicore.cli_console.LazyConsole` is told there is none.
    """
    root = find_workspace_root()
    if root is None:
        raise SystemExit(0)
    return legacy_cli_dir(root)


_lazy = LazyConsole(_theme_dir)


def set_machine(flag: bool) -> None:
    """Select the renderer for this run: JSON events when *flag*, Rich otherwise.

    Discards any console built earlier, so the choice holds even when a previous
    run in the same process already printed. Call it while parsing the command
    line, before anything reaches the terminal.
    """
    global _lazy
    _lazy = LazyConsole(_theme_dir)
    _lazy.machine = flag


def is_machine() -> bool:
    """Report whether this run renders JSON events rather than a terminal."""
    return _lazy.machine


def current():
    """Return the sushicore Console this run prints through, building it on first use."""
    return _lazy.get()


def report_failure(message: str) -> None:
    """Prints one error line and, under ``--json``, the ``result`` event that ends the stream.

    A console whose own configuration cannot be read is replaced by one built
    from no configuration, so the failure is still reported in this run's mode.
    """
    try:
        printer = current()
    except SushiCoreError:
        printer = build_console((), machine=is_machine())
    printer.error(message)
    if is_machine():
        printer.result(False, {})


def __getattr__(name: str):
    """Resolve a console attribute, building the console on the first one."""
    return _lazy.attribute(name)
