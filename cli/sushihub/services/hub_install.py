"""How `hub` itself is installed on this machine, read from disk.

The installers write the ``sh`` alias under a marker comment into the shell's
rc file or the PowerShell profile; this module finds that marker and reports
where. It reads the home directory it is given and nothing else, so the
status payload's ``hub`` block is the same on every call. See
contract/README.md, "The status payload".
"""

from __future__ import annotations

import sys
from pathlib import Path

#: The comment both install scripts put above the alias; test_hub_install pins them together.
ALIAS_MARKER = "# sushi hub alias"

#: The name the installers alias `hub` to.
ALIAS_NAME = "sh"

#: The command the console script installs.
COMMAND = "hub"

#: Files under the home directory an installer may have written the alias into, in lookup order.
_RC_FILES = (
    Path(".bashrc"),
    Path(".zshrc"),
    Path("Documents") / "PowerShell" / "profile.ps1",
    Path("Documents") / "WindowsPowerShell" / "profile.ps1",
)


def _alias(home: Path) -> dict | None:
    """Return the alias object for the first rc file under *home* carrying the marker."""
    for relative in _RC_FILES:
        path = home / relative
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if ALIAS_MARKER in text:
            return {"name": ALIAS_NAME, "defined_in": str(path)}
    return None


def read_hub_install(home: Path) -> dict:
    """Describe the running `hub` install.

    Args:
        home: The user's home directory, whose rc files and profiles are searched.

    Returns:
        The ``hub`` block of the status payload without ``source`` and
        ``latest_version``: the command, the alias or None, and the channel,
        ``frozen`` inside a frozen executable and ``editable`` otherwise.
    """
    return {
        "command": COMMAND,
        "alias": _alias(home),
        "channel": "frozen" if getattr(sys, "frozen", False) else "editable",
    }
