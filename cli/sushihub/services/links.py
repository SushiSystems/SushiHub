# links.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The link registry: modules pointed at existing checkouts outside the workspace.

``hub link`` records a module's path in ``[modules]`` of
``<workspace>/.sushistack/workspace.toml``; this module reads and writes that
table through :mod:`sushicore.workspace`.
"""

from __future__ import annotations

from pathlib import Path

from sushicore.workspace import registered_modules, write_module

from ..config import find_workspace_root, workspace_root


def registered() -> dict[str, str]:
    """Return name -> path for modules linked via ``hub link``, empty outside a workspace."""
    home = find_workspace_root()
    return {} if home is None else registered_modules(home)


def write(name: str, path: Path) -> None:
    """Record (or update) a module -> path entry in ``[modules]``, keeping every other table."""
    write_module(workspace_root(), name, path)
