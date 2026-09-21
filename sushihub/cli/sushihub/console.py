"""CLI output for the SushiHub CLI.

Thin wrapper around :mod:`sushicore` — the actual theme/icon/renderer logic
(and its `[cli]` config schema) lives there and is shared with every module
CLI in the stack — sushiruntime, sushiengine, sushiai and sushiblas. See
sushicore's README to change colors.

The console is built on first use, not on import, so a command that needs no
workspace (`hub --help`, `hub --describe`) still runs outside one. Every name this
module exposes resolves through :class:`~sushicore.cli_console.LazyConsole`:
``console`` for the raw Rich console, ``info``/``success``/``warn``/``error``,
``command``, ``header``, ``fail_panel``, ``accent``, and the machine-readable
four, ``table``, ``progress``, ``result`` and ``prompt``.
"""

from __future__ import annotations

from sushicore.cli_console import LazyConsole

from .config import legacy_cli_dir

_lazy = LazyConsole(legacy_cli_dir)


def set_machine(flag: bool) -> None:
    """Select the renderer for this run: JSON events when *flag*, Rich otherwise.

    Discards any console built earlier, so the choice holds even when a previous
    run in the same process already printed. Call it while parsing the command
    line, before anything reaches the terminal.
    """
    global _lazy
    _lazy = LazyConsole(legacy_cli_dir)
    _lazy.machine = flag


def is_machine() -> bool:
    """Report whether this run renders JSON events rather than a terminal."""
    return _lazy.machine


def __getattr__(name: str):
    """Resolve a console attribute, building the console on the first one."""
    return _lazy.attribute(name)
