# host.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds a release host that names a fixed platform."""

from __future__ import annotations


class FixedHost:
    """Names the platform it was given, whatever the machine is.

    Args:
        platform: The platform string, such as ``linux-x64``.
    """

    def __init__(self, platform: str) -> None:
        """Keeps *platform*."""
        self._platform = platform

    def platform(self) -> str:
        """Returns the platform this host was given."""
        return self._platform
