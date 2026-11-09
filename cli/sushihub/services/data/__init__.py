# __init__.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Data packages: files `hub install` downloads, verifies and places for a module."""

from __future__ import annotations

from .errors import (
    DataDestinationError,
    DataFetchError,
    DataFragmentError,
    DataPackageError,
    DataVerificationError,
)
from .file_state import FileState, inspect_file
from .fragment_reader import read_data_packages
from .http_downloader import HttpDownloader
from .installer import DataInstaller, PackageResult
from .package import K_DATA_TABLE, DataPackage
from .placement import DataPlacer
from .ports import DataSource, Downloader
from .report import DataReport
from .store import DataStore
from .workspace_source import WorkspaceDataSource

__all__ = [
    "DataDestinationError",
    "DataFetchError",
    "DataFragmentError",
    "DataInstaller",
    "DataPackage",
    "DataPackageError",
    "DataPlacer",
    "DataReport",
    "DataSource",
    "DataStore",
    "DataVerificationError",
    "Downloader",
    "FileState",
    "HttpDownloader",
    "K_DATA_TABLE",
    "PackageResult",
    "WorkspaceDataSource",
    "inspect_file",
    "read_data_packages",
]
