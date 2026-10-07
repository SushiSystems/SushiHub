# tool_paths.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Rewrites the tool paths of a workspace file from one dependency root to another."""

from __future__ import annotations

import os
from pathlib import Path

from sushicore.config_base import write_toml_document
from sushicore.workspace import WORKSPACE_HEADER, read_toml


def rewrite_tool_paths(target: Path, old_root: Path, new_root: Path) -> int:
    """Point every ``[tool]`` value of *target* that lies under *old_root* at *new_root*.

    Both ``[tool]`` and its ``[tool.<platform>]`` tables are covered, and every other
    table is written back as it was. A file with no such value is not written.

    Returns:
        How many values changed.
    """
    document = read_toml(target)
    tool, changed = _moved_table(document.get("tool", {}), old_root, new_root)
    if changed:
        write_toml_document(target, {**document, "tool": tool}, WORKSPACE_HEADER)
    return changed


def _moved_table(table: dict, old_root: Path, new_root: Path) -> tuple[dict, int]:
    """Return *table* with its paths moved, nested tables included, and the change count."""
    moved: dict = {}
    changed = 0
    for key, value in table.items():
        if isinstance(value, dict):
            moved[key], inner = _moved_table(value, old_root, new_root)
            changed += inner
        elif isinstance(value, str):
            moved[key] = _moved_path(value, old_root, new_root)
            changed += moved[key] != value
        else:
            moved[key] = value
    return moved, changed


def _moved_path(value: str, old_root: Path, new_root: Path) -> str:
    """Return *value* with a leading *old_root* replaced by *new_root*, else unchanged.

    The roots are compared the way the file system compares names, so a drive
    letter in another case still matches on Windows.
    """
    old = old_root.as_posix().rstrip("/")
    path = value.replace("\\", "/")
    head, rest = path[:len(old)], path[len(old):]
    if os.path.normcase(head) != os.path.normcase(old) or rest[:1] not in ("", "/"):
        return value
    return new_root.as_posix().rstrip("/") + rest
