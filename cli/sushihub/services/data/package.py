# package.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds one data package as a module's fragment declares it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

#: The fragment table whose sub-tables are data packages: ``[data.<name>]``.
K_DATA_TABLE = "data"


@dataclass(frozen=True, slots=True)
class DataPackage:
    """One file a module's tests or tools read, pinned by size and SHA-256.

    Attributes:
        name: The ``<name>`` of the ``[data.<name>]`` table.
        owner: The module that declared it.
        checkout: The module's checkout, which ``destination`` is relative to.
        url: The publisher's address of the file.
        sha256: The lower-case hexadecimal digest of the file.
        size: The length of the file in bytes.
        licence: The publisher's licence or terms, in one line.
        destination: Where the module reads the file, relative to ``checkout``.
        description: What the file is for; empty when the table says nothing.
        required: Whether a failure to fetch it fails ``hub install``.
    """

    name: str
    owner: str
    checkout: Path
    url: str
    sha256: str
    size: int
    licence: str
    destination: str
    description: str = ""
    required: bool = False

    @property
    def file_name(self) -> str:
        """Returns the last segment of the URL's path, which names the file in the store."""
        return PurePosixPath(urlparse(self.url).path).name
