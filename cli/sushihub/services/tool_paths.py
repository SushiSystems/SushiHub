# tool_paths.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Rewrites the tool paths of a workspace file from one dependency root to another."""

from __future__ import annotations

import os
from pathlib import Path

from sushicore.config_base import write_toml_document
from sushicore.workspace import WORKSPACE_HEADER, read_toml


def rewrite_tool_paths(target: Path, old_root: Path, new_root: Path) -> int:
    """Point every ``[tool]`` value of the workspace file *target* under *old_root* at *new_root*.

    A file with no such value is not written. See :func:`moved_document`.

    Returns:
        How many values changed.
    """
    moved, changed = moved_document(read_toml(target), old_root, new_root)
    if changed:
        write_toml_document(target, moved, WORKSPACE_HEADER)
    return changed


def moved_document(document: dict, old_root: Path, new_root: Path) -> tuple[dict, int]:
    """Return a workspace *document* with its ``[tool]`` paths under *old_root* moved to *new_root*.

    Both ``[tool]`` and its ``[tool.<platform>]`` tables are covered, and every other table is
    returned as it was.

    Returns:
        The moved document and how many values changed.
    """
    tool, changed = _moved_table(document.get("tool", {}), old_root, new_root)
    return {**document, "tool": tool}, changed


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
