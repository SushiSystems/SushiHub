# listed_packages.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides a data source that lists the packages a test hands it."""

from __future__ import annotations

from sushihub.services.data import DataPackage


class ListedPackages:
    """The in-memory :class:`~sushihub.services.data.DataSource`: lists what it was given."""

    def __init__(self, *packages: DataPackage) -> None:
        """Hold the packages to list."""
        self._packages = list(packages)

    def packages(self) -> list[DataPackage]:
        """Return the held packages."""
        return list(self._packages)


class RefusedFragment:
    """A data source whose fragment declares a table wrongly."""

    def __init__(self, error: Exception) -> None:
        """Hold the error to raise."""
        self._error = error

    def packages(self) -> list[DataPackage]:
        """Raise the held error."""
        raise self._error
