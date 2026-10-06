# describe.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The command catalogue `hub --describe` prints.

The serialisation is :func:`sushicore.describe.catalogue`; this module adds what only `hub`
knows, the distribution it is installed as and the forms of module presence a command
applies to. ``contract/describe.schema.json`` fixes the shape.
"""

from __future__ import annotations

import typer
from sushicore import describe

from . import DISTRIBUTION

#: The forms of module presence a command can apply to.
ALL_PRESENCE = ("cloned", "linked", "binary")


def catalogue(app: typer.Typer) -> dict:
    """Serialises *app*'s visible commands, sorted by name, as the contract's catalogue."""
    return describe.catalogue(app, distribution=DISTRIBUTION, applies_to=ALL_PRESENCE)
