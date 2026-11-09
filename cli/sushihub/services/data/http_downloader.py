# http_downloader.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The network adapter of :class:`~.ports.Downloader`: one plain GET under hub's own name."""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from typing import Callable, final

from ... import DISTRIBUTION, __version__
from .. import releases
from .errors import DataFetchError
from .package import DataPackage

#: The client name every request carries; never a browser's.
K_USER_AGENT = f"{DISTRIBUTION}/{__version__}"


@final
class HttpDownloader:
    """Streams a package's URL to a file through :func:`~sushihub.services.releases.download`.

    Args:
        http: What opens the URL; ``urllib.request.urlopen`` when None.
    """

    def __init__(self, http: Callable | None = None) -> None:
        """Holds the opener to use."""
        self._http = http if http is not None else urllib.request.urlopen

    def fetch(self, package: DataPackage, dest: Path,
              on_progress: Callable[[int, int], None] | None = None) -> tuple[int, str]:
        """Writes the file at ``package.url`` to *dest* and returns its size and SHA-256.

        Raises:
            DataFetchError: The server answered with an error status, or the connection failed.
        """
        digest = hashlib.sha256()
        try:
            size = releases.download(
                package.url, dest, on_progress=on_progress, http=self._http,
                headers={"User-Agent": K_USER_AGENT}, digest=digest)
        except OSError as error:
            raise DataFetchError(f"{package.name}: {package.url} could not be fetched: "
                                 f"{error}") from error
        return size, digest.hexdigest()
