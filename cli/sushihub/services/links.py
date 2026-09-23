"""The link registry: modules pointed at existing checkouts outside the workspace.

``hub link`` records a module's path in ``[modules]`` of
``<workspace>/.sushistack/workspace.toml``; this module reads and writes that
table through :mod:`sushicore.workspace`.
"""

from __future__ import annotations

from pathlib import Path

from sushicore.workspace import registered_modules, write_module

from ..config import workspace_root


def registered() -> dict[str, str]:
    """Return name -> path for modules linked via ``hub link``, empty outside a workspace."""
    try:
        home = workspace_root()
    except SystemExit:
        return {}
    return registered_modules(home)


def write(name: str, path: Path) -> None:
    """Record (or update) a module -> path entry in ``[modules]``, keeping every other table."""
    write_module(workspace_root(), name, path)
