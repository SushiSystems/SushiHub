# ports.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Declares the two ports data packages reach the outside through.

The network adapter is :class:`~.http_downloader.HttpDownloader`; the workspace adapter is
:class:`~.workspace_source.WorkspaceDataSource`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from .package import DataPackage


class Downloader(Protocol):
    """Fetches the file a data package names."""

    def fetch(self, package: DataPackage, dest: Path,
              on_progress: Callable[[int, int], None] | None = None) -> tuple[int, str]:
        """Writes the file at ``package.url`` to *dest* and returns its size and SHA-256.

        Args:
            package: The package to fetch.
            dest: The file to write; its parent directory exists.
            on_progress: Called after every chunk with the bytes written and the declared total.

        Raises:
            DataFetchError: The server or the network refused.
        """
        ...


class DataSource(Protocol):
    """Lists the data packages the present modules declare."""

    def packages(self) -> list[DataPackage]:
        """Returns every declared package in fragment order.

        Raises:
            DataFragmentError: A fragment declares a table wrongly.
        """
        ...
