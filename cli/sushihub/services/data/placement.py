# placement.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Copies a stored package to the place its module reads it, inside the module's checkout."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import final

from .errors import DataDestinationError
from .file_state import FileState, inspect_file
from .package import DataPackage


@final
class DataPlacer:
    """Resolves a package's ``destination`` and puts a verified copy there."""

    def destination(self, package: DataPackage) -> Path:
        """Returns the absolute path *package* is read from.

        Raises:
            DataDestinationError: The path, once resolved, is outside the module's checkout or
                is the checkout itself.
        """
        root = package.checkout.resolve()
        target = (root / package.destination).resolve()
        if root not in target.parents:
            raise DataDestinationError(
                f"{package.name}: destination {package.destination!r} leaves the checkout "
                f"{root}; a destination is a file path inside it.")
        return target

    def state(self, package: DataPackage) -> FileState:
        """Returns how the copy at the destination stands against the pinned size and digest."""
        return inspect_file(self.destination(package), package)

    def place(self, package: DataPackage, stored: Path) -> bool:
        """Copies *stored* to the destination unless an intact copy is already there.

        The copy is written beside the destination and renamed over it, so a reader never
        sees half a file.

        Args:
            package: The package being placed.
            stored: Its verified copy in the store.

        Returns:
            Whether a copy was made.

        Raises:
            DataDestinationError: The destination leaves the checkout.
        """
        target = self.destination(package)
        if inspect_file(target, package) is FileState.INTACT:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, partial_name = tempfile.mkstemp(prefix=".part-", dir=target.parent)
        os.close(descriptor)
        partial = Path(partial_name)
        try:
            shutil.copyfile(stored, partial)
            os.replace(partial, target)
        finally:
            partial.unlink(missing_ok=True)
        return True
