# installer.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Brings each declared data package into the store and to the place its module reads it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, final

from ..ports import ConsolePort
from ..releases import report_progress
from .errors import DataPackageError
from .package import DataPackage
from .placement import DataPlacer
from .store import DataStore


@dataclass(frozen=True, slots=True)
class PackageResult:
    """What installing one package came to.

    Attributes:
        package: The package.
        error: The message of the failure, or None when the package is in place.
    """

    package: DataPackage
    error: str | None = None


@final
class DataInstaller:
    """Installs packages one after another; a failure fails that package alone.

    Args:
        store: The machine's store.
        placer: Puts a stored file where its module reads it.
        console: Where each package's outcome and the download progress are printed.
    """

    def __init__(self, store: DataStore, placer: DataPlacer, console: ConsolePort) -> None:
        """Holds the store, the placer and the console."""
        self._store = store
        self._placer = placer
        self._console = console

    def install(self, packages: list[DataPackage]) -> list[PackageResult]:
        """Installs every package in order and returns one result for each."""
        return [self._install_one(package) for package in packages]

    def _install_one(self, package: DataPackage) -> PackageResult:
        """Stores and places *package*, printing what happened, and returns its result."""
        try:
            destination = self._placer.destination(package)
            stored, downloaded = self._store.ensure(package, self._progress(package))
            placed = self._placer.place(package, stored)
        except DataPackageError as error:
            self._console.error(str(error))
            return PackageResult(package, str(error))
        origin = "downloaded" if downloaded else "from the store"
        self._console.info(
            f"{package.name}: {origin}, " + (f"placed at {destination}" if placed
                                              else f"already at {destination}"))
        return PackageResult(package)

    def _progress(self, package: DataPackage) -> Callable[[int, int], None]:
        """Returns the callback that prints a download's progress under the ``download`` label."""
        return lambda done, total: report_progress(
            self._console, done, total or package.size)
