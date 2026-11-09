# store.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The machine's store of data packages: ``<root>/<sha256>/<file name>``, one copy per digest."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable, final

from .errors import DataVerificationError
from .file_state import FileState, inspect_file
from .package import DataPackage
from .ports import Downloader


@final
class DataStore:
    """Keeps each verified package once per machine and fetches the ones it lacks.

    Args:
        root: The store's directory, ``dependencies/data``.
        downloader: What fetches a package that is not stored.
    """

    def __init__(self, root: Path, downloader: Downloader) -> None:
        """Holds the store's directory and the downloader."""
        self._root = root
        self._downloader = downloader

    def path_of(self, package: DataPackage) -> Path:
        """Returns where *package* is, or would be, stored."""
        return self._root / package.sha256 / package.file_name

    def ensure(self, package: DataPackage,
               on_progress: Callable[[int, int], None] | None = None) -> tuple[Path, bool]:
        """Returns the stored copy of *package*, fetching it first when none is intact.

        A download lands in a temporary file beside its final place and is renamed into it only
        once its size and SHA-256 match; a failed one is deleted.

        Args:
            package: The package to make available.
            on_progress: Called after every chunk of a download with the bytes and the total.

        Returns:
            The stored file, and whether this call downloaded it.

        Raises:
            DataFetchError: The download was refused.
            DataVerificationError: The download's size or SHA-256 differs from the pinned one.
        """
        target = self.path_of(package)
        if inspect_file(target, package) is FileState.INTACT:
            return target, False
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, partial_name = tempfile.mkstemp(prefix=".part-", dir=target.parent)
        os.close(descriptor)
        partial = Path(partial_name)
        try:
            size, found = self._downloader.fetch(package, partial, on_progress)
            self._require_match(package, size, found)
            os.replace(partial, target)
        finally:
            partial.unlink(missing_ok=True)
        return target, True

    @staticmethod
    def _require_match(package: DataPackage, size: int, found: str) -> None:
        """Raises unless *size* and *found* are the ones *package* pins.

        Raises:
            DataVerificationError: One or both differ; the message gives expected and found.
        """
        problems = []
        if size != package.size:
            problems.append(f"size expected {package.size} bytes, found {size}")
        if found != package.sha256:
            problems.append(f"sha256 expected {package.sha256}, found {found}")
        if problems:
            raise DataVerificationError(
                f"{package.name}: the download of {package.url} was deleted; "
                + "; ".join(problems) + ".")
