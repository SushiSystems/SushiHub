# errors.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The failures data packages report; each one is a line `hub` prints for that package."""

from __future__ import annotations

from ...errors import HubError


class DataPackageError(HubError):
    """Reports a data package that could not be read, fetched, verified or placed."""


class DataFragmentError(DataPackageError):
    """Reports a ``[data.<name>]`` table a fragment declares wrongly."""


class DataFetchError(DataPackageError):
    """Reports a download that the publisher's server or the network refused."""


class DataVerificationError(DataPackageError):
    """Reports a download whose size or SHA-256 differs from the one the fragment pins."""


class DataDestinationError(DataPackageError):
    """Reports a ``destination`` that leaves the module's checkout."""
