# file_state.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tells whether a file on disk is the one a data package pins."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from ..releases import sha256_of
from .package import DataPackage


class FileState(Enum):
    """How a file on disk stands against the size and digest a package pins."""

    MISSING = "missing"
    INTACT = "intact"
    CORRUPT = "corrupt"


def inspect_file(path: Path, package: DataPackage) -> FileState:
    """Reports whether the file at *path* is absent, the one *package* pins, or something else.

    The size is compared first, so a file of the wrong length is never read.

    Args:
        path: The file to examine.
        package: The package whose size and SHA-256 it must have.
    """
    if not path.is_file():
        return FileState.MISSING
    if path.stat().st_size != package.size:
        return FileState.CORRUPT
    return FileState.INTACT if sha256_of(path) == package.sha256 else FileState.CORRUPT
