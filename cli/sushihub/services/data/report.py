# report.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Turns the state of each data package into the rows `hub doctor` prints."""

from __future__ import annotations

from typing import final

from ..ports import ConsolePort
from .errors import DataPackageError
from .file_state import FileState
from .package import DataPackage
from .placement import DataPlacer
from .ports import DataSource

#: One row of the inventory table: component, status, owner, detail.
Row = tuple[str, str, str, str]

#: The status text of each state, in the words the toolchain rows use.
K_STATUS = {FileState.INTACT: "OK", FileState.MISSING: "MISSING", FileState.CORRUPT: "CORRUPT"}


@final
class DataReport:
    """Reports each declared package as present, missing or corrupt, with its owner.

    Args:
        source: Lists the packages the present modules declare.
        placer: Reads the copy at each destination.
        console: Where a fragment that declares a table wrongly is reported.
    """

    def __init__(self, source: DataSource, placer: DataPlacer, console: ConsolePort) -> None:
        """Holds the source, the placer and the console."""
        self._source = source
        self._placer = placer
        self._console = console

    def rows(self) -> list[Row]:
        """Returns one row per package, empty when a fragment declares a table wrongly."""
        try:
            return [self._row(package) for package in self._source.packages()]
        except DataPackageError as error:
            self._console.warn(str(error))
            return []

    def _row(self, package: DataPackage) -> Row:
        """Returns the row of *package*."""
        try:
            state = self._placer.state(package)
            where = self._placer.destination(package)
        except DataPackageError as error:
            return (package.name, K_STATUS[FileState.CORRUPT], package.owner, str(error))
        detail = {
            FileState.INTACT: f"present at {where}",
            FileState.MISSING: f"not at {where}; `hub install` fetches it",
            FileState.CORRUPT: f"{where} differs from the pinned size or SHA-256; "
                               "`hub install` replaces it",
        }[state]
        return (package.name, K_STATUS[state], package.owner, detail)
