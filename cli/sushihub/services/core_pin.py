# core_pin.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Moves the `sushicore` requirement of every module CLI of the workspace, and of this one.

`sushicore` is a Python package, so its pin is the exact requirement in a `cli/pyproject.toml`,
not a `[sushisystems.<name>]` table. The rule is skills/module-install in SushiSkills, boundary 3.
"""

from __future__ import annotations

import re
from pathlib import Path

from .. import console
from ..config import workspace_root
from .module_fragments import present_modules

#: The library name `hub pin` takes for the Python package.
K_LIBRARY = "sushicore"

#: A release number, with or without the leading `v` of its tag.
K_VERSION = re.compile(r"v?(\d+\.\d+\.\d+)")

#: The `sushicore` requirement string of a dependency list, whatever operator it carries.
K_REQUIREMENT = re.compile(r'"sushicore\s*(?:==|>=|<=|~=|>|<)\s*([0-9][^"\s,;]*)"')

#: Where a module keeps the requirements of its CLI.
K_PYPROJECT = Path("cli") / "pyproject.toml"


def rewrite_requirement(text: str, version: str) -> str:
    """Return a `pyproject.toml` text with its `sushicore` requirement set to `==<version>`.

    Raises:
        ValueError: When the text has no `sushicore` requirement.
    """
    if K_REQUIREMENT.search(text) is None:
        raise ValueError("no sushicore requirement")
    return K_REQUIREMENT.sub(f'"sushicore=={version}"', text)


def move_core_pin(root: Path, version: str, dry_run: bool) -> list[tuple[str, str]]:
    """Set `sushicore==<version>` in the CLI of every module at *root*, and in the hub's own.

    Returns:
        Each project whose requirement changed and the requirement it moved from.
    """
    checkouts = {"sushihub": root, **present_modules(root)}
    moved: list[tuple[str, str]] = []
    for name, checkout in checkouts.items():
        pyproject = checkout / K_PYPROJECT
        if not pyproject.is_file():
            continue
        text = pyproject.read_bytes().decode("utf-8")
        found = K_REQUIREMENT.search(text)
        if found is None or found.group(0) == f'"sushicore=={version}"':
            continue
        if not dry_run:
            pyproject.write_bytes(rewrite_requirement(text, version).encode("utf-8"))
        moved.append((name, found.group(0).strip('"')))
    return moved


def pin(version: str, dry_run: bool) -> int:
    """Move `sushicore` to *version* in every module CLI of the workspace. Returns the exit code."""
    parsed = K_VERSION.fullmatch(version)
    if parsed is None:
        console.error(f"sushicore: '{version}' is not a release number such as 0.9.8 or v0.9.8.")
        return 1
    number = parsed.group(1)
    moved = move_core_pin(workspace_root(), number, dry_run)
    if not moved:
        console.info(f"sushicore: no CLI of the workspace requires another version than {number}.")
        return 0
    verb = "would move" if dry_run else "moved"
    for name, old in moved:
        console.info(f"{name}: {verb} {old} to sushicore=={number}.")
    if not dry_run:
        console.success(f"{len(moved)} CLI(s) now require sushicore=={number}; commit each module.")
    return 0
