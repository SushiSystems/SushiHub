# fetched_sources.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Takes over the copies a module's own `setup` fetched: clones from them and clears unused ones.

The rule is skills/dependencies in SushiSkills, "A Sushi library as a dependency", rule 6.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from sushicore.provision import home

from .. import console
from . import git_ops
from .module_fragments import workspace_pins

#: The parts of a release tag, compared as numbers so v0.10.0 sorts after v0.9.1.
K_TAG_NUMBERS = re.compile(r"\d+")


@dataclass(frozen=True, slots=True)
class FetchedCopy:
    """One library `setup` cloned at one release tag."""

    name: str
    version: str
    path: Path


def _version_key(version: str) -> tuple[int, ...]:
    """Return a tag's numbers, so tags sort by release order."""
    return tuple(int(part) for part in K_TAG_NUMBERS.findall(version))


def fetched_copies() -> list[FetchedCopy]:
    """Return every copy under the machine's `sources/` folder, by name then release order."""
    sources = home.sources_dir()
    if not sources.is_dir():
        return []
    copies = [FetchedCopy(library.name, version.name, version)
              for library in sorted(sources.iterdir()) if library.is_dir()
              for version in library.iterdir() if (version / ".git").exists()]
    return sorted(copies, key=lambda copy: (copy.name, _version_key(copy.version)))


def newest_copy(name: str) -> FetchedCopy | None:
    """Return the newest fetched copy of library *name*, or None when there is none."""
    copies = [copy for copy in fetched_copies() if copy.name == name]
    return copies[-1] if copies else None


def unused_copies(root: Path) -> list[FetchedCopy]:
    """Return the fetched copies whose library and tag no module of the workspace pins."""
    pinned = {(pin.name, pin.version) for _, _, pin in workspace_pins(root)}
    return [copy for copy in fetched_copies() if (copy.name, copy.version) not in pinned]


def clone_from_copy(copy: FetchedCopy, repo: str, dest: Path, cwd: Path) -> bool:
    """Clone *dest* from *copy*, then point its remote at *repo* and fetch its history.

    The clone needs no network; the fetch does, and when it fails the checkout keeps only the
    copy's tag until `hub update` runs online.

    Returns:
        Whether the clone succeeded.
    """
    if git_ops.run(["clone", str(copy.path), str(dest)], cwd=cwd) != 0:
        return False
    git_ops.run(["remote", "set-url", "origin", repo], cwd=dest)
    unshallow = ["--unshallow"] if (dest / ".git" / "shallow").exists() else []
    if git_ops.run(["fetch", *unshallow, "--tags", "origin"], cwd=dest) != 0:
        console.warn(f"{copy.name}: cloned from {copy.path}, but the fetch from {repo} failed; "
                     f"the checkout holds only {copy.version} until `hub update` runs online.")
    return True


def _clear_read_only(function, path, _error) -> None:
    """Make *path* writable and retry *function*, since git keeps its objects read-only."""
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _remove_tree(path: Path) -> None:
    """Delete *path* and everything under it, read-only files included."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_read_only)
    else:
        shutil.rmtree(path, onerror=_clear_read_only)


def remove_copies(copies: list[FetchedCopy]) -> None:
    """Delete each copy's folder, and its library folder when that is left empty."""
    for copy in copies:
        _remove_tree(copy.path)
        library = copy.path.parent
        if library.is_dir() and not any(library.iterdir()):
            library.rmdir()


def clean(root: Path, dry_run: bool) -> int:
    """Remove every fetched copy no module of the workspace pins. Returns the exit code."""
    copies = unused_copies(root)
    if not copies:
        console.info("No fetched copy is unused.")
        return 0
    for copy in copies:
        console.info(f"{copy.name} {copy.version}: {'would remove' if dry_run else 'removing'} {copy.path}")
    if not dry_run:
        remove_copies(copies)
        console.success(f"Removed {len(copies)} fetched copy(s).")
    return 0
