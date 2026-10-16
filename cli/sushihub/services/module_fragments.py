# module_fragments.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Finds the modules a workspace holds and the dependency fragment of each."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sushicore.deps_fragment import SushiPin, pins_at

from . import links, module_manifest
from .catalog import CATALOG, Module
from .presence import Presence, module_dir, presence_of


def present_modules(root: Path) -> dict[str, Path]:
    """Return name -> checkout for every catalog or linked module the workspace at *root* holds."""
    linked = links.registered()
    names = list(dict.fromkeys([*CATALOG.names(), *linked]))
    return {name: module_dir(root, name, linked) for name in names
            if presence_of(root, name, linked) in (Presence.CLONED, Presence.LINKED)}


def fragment_of(name: str, checkout: Path) -> Path:
    """Return the dependency fragment of module *name* at *checkout*.

    Its manifest names it; without one the catalog entry does, then the conventional path.
    """
    manifest = module_manifest.read(checkout)
    if manifest is not None:
        return checkout / manifest.fragment
    return checkout / (CATALOG[name].fragment if name in CATALOG else Module.fragment)


def workspace_pins(root: Path) -> Iterator[tuple[str, Path, SushiPin]]:
    """Yield each module of the workspace, its fragment and each Sushi library it pins."""
    for name, checkout in present_modules(root).items():
        fragment = fragment_of(name, checkout)
        for pin in pins_at(fragment):
            yield name, fragment, pin
