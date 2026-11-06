# pins.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Moves the pin of one Sushi library in every module of the workspace that pins it.

The rule is skills/dependencies in SushiSkills, "A Sushi library as a dependency", rule 5.
"""

from __future__ import annotations

import re
from pathlib import Path

from .. import console
from ..config import workspace_root
from . import core_pin
from .catalog import CATALOG
from .git_ops import K_COMMIT
from .module_fragments import workspace_pins
from .ports import Ports

#: The opening of a pin table under its deprecated name, `[sushi.<name>]`.
K_DEPRECATED_HEADER = re.compile(r"^\[sushi\.", re.MULTILINE)


def rewrite_pin(text: str, name: str, version: str, commit: str) -> str:
    """Return a fragment's text with the `[sushisystems.<name>]` table set to *version* and *commit*.

    Only the two keys change, and comments and every other line stay as written, except that a
    fragment still on the deprecated `[sushi.<name>]` tables has every one renamed, since a file
    holding both names is refused.
    """
    text = K_DEPRECATED_HEADER.sub("[sushisystems.", text)
    table = re.compile(rf"^\[sushisystems\.{re.escape(name)}\]\s*$(.*?)(?=^\[|\Z)",
                       re.MULTILINE | re.DOTALL)
    match = table.search(text)
    if match is None:
        raise ValueError(f"no [sushisystems.{name}] table")
    body = re.sub(r'^(version\s*=\s*)"[^"]*"', rf'\g<1>"{version}"', match.group(1), flags=re.MULTILINE)
    body = re.sub(r'^(commit\s*=\s*)"[^"]*"', rf'\g<1>"{commit}"', body, flags=re.MULTILINE)
    return text[:match.start(1)] + body + text[match.end(1):]


def move_pin(root: Path, name: str, version: str, commit: str, dry_run: bool) -> list[tuple[str, str]]:
    """Set library *name* to *version* and *commit* in every fragment of the workspace pinning it.

    Returns:
        Each module whose pin changed and the version it moved from.
    """
    moved: list[tuple[str, str]] = []
    for module, fragment, pin in workspace_pins(root):
        if pin.name != name or (pin.version, pin.commit) == (version, commit):
            continue
        if not dry_run:
            text = fragment.read_text(encoding="utf-8")
            fragment.write_text(rewrite_pin(text, name, version, commit), encoding="utf-8")
        moved.append((module, pin.version))
    return moved


def pin(name: str, version: str, commit: str | None, dry_run: bool,
        ports: Ports | None = None) -> int:
    """Move library *name* to *version* in every module of the workspace that pins it.

    The commit is the one the tag points at in the library's repository, unless *commit* names
    it. `sushicore` is a Python package and takes the version only. Returns the exit code.

    @param ports What the command prints and reads tags through; this machine's when None.
    """
    if name == core_pin.K_LIBRARY:
        return core_pin.pin(version, dry_run)
    ports = ports or Ports.machine(console)
    out = ports.console
    if commit is None:
        repo = CATALOG[name].repo if name in CATALOG else f"https://github.com/sushisystems/{name}.git"
        commit = ports.git.tag_commit(repo, version)
        if commit is None:
            out.error(f"{name}: no tag {version} found in {repo}. Check the tag, or pass "
                      "--commit with its full hash when the repository is out of reach.")
            return 1
    if not K_COMMIT.fullmatch(commit):
        out.error(f"{name}: '{commit}' is not a full 40-character commit hash.")
        return 1
    moved = move_pin(workspace_root(), name, version, commit, dry_run)
    if not moved:
        out.info(f"{name}: no module of the workspace pins it at another version.")
        return 0
    verb = "would move" if dry_run else "moved"
    for module, old in moved:
        out.info(f"{module}: {verb} {name} from {old} to {version} ({commit[:12]}).")
    if not dry_run:
        out.success(f"{len(moved)} fragment(s) now pin {name} {version}; commit each module.")
    return 0
