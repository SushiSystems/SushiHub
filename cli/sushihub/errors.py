# errors.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The failures `hub` reports to its entry point as one line.

Every class derives from :class:`HubError`, which derives from sushicore's base, so
:func:`sushicore.entry.run` turns each into a message and exit code 1.
"""

from __future__ import annotations

from sushicore.errors import SushiCoreError


class HubError(SushiCoreError):
    """Reports a failure of `hub` the user can act on."""


class WorkspaceNotFoundError(HubError):
    """Reports a command run outside any SushiStack workspace."""


class GuiSourcesMissingError(HubError):
    """Reports a workspace that carries no desktop application sources."""


class SushiAccountError(HubError):
    """Reports a Sushi Account call that could not be carried through."""
