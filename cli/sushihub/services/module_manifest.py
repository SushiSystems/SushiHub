# module_manifest.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads `sushi-module.toml`, the manifest a module writes about itself.

The file becomes a :class:`~.catalog.Module` or is refused. The format is fixed in
docs/reference/MODULE_MANIFEST.md; where a manifest meets a catalog entry is in
cli/README.md, "Notes on the source".
"""

from __future__ import annotations

from pathlib import Path

from .catalog import Module

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


#: The manifest's name, at a module's repository root.
MANIFEST_FILE = "sushi-module.toml"

#: The one table the format is made of.
MODULE_TABLE = "module"

#: Keys a module must declare; the rest have conventional answers.
REQUIRED_KEYS = ("name", "alias", "distribution")


def read(root: Path) -> Module | None:
    """Return the module ``<root>/sushi-module.toml`` describes, or None.

    Args:
        root: A module checkout's root directory.

    Returns:
        The module the manifest describes, or None when the file is absent,
        which is the ordinary case for a module the catalog already knows.

    Raises:
        ValueError: The file is there and cannot be believed; see :func:`parse`.
    """
    path = root / MANIFEST_FILE
    if not path.is_file():
        return None
    return parse(path.read_text(encoding="utf-8"), root.name, str(path))


def parse(text: str, directory: str, source: str = MANIFEST_FILE) -> Module:
    """Return the module the manifest *text* describes.

    Args:
        text: The manifest's TOML text.
        directory: The name of the directory the manifest sits in, which ``name`` must equal.
        source: What an error names as the place the text came from.

    Raises:
        ValueError: The text cannot be believed: it is not TOML, a required key is missing,
            ``name`` disagrees with *directory*, or a table the reader does not know is
            present. An unknown *key* is ignored instead, so a newer module can add one.
    """
    document = tomllib.loads(text)

    unknown = [name for name in document if name != MODULE_TABLE]
    if unknown:
        raise ValueError(
            f"{source}: unknown table(s) {', '.join(sorted(unknown))}. A reader that drops a "
            f"table it does not know is how a whole section goes missing in silence.")
    if MODULE_TABLE not in document:
        raise ValueError(f"{source}: no [{MODULE_TABLE}] table, which is what this format is.")

    table = document[MODULE_TABLE]
    absent = [key for key in REQUIRED_KEYS if not table.get(key)]
    if absent:
        raise ValueError(f"{source}: [{MODULE_TABLE}] declares no {', '.join(absent)}.")

    name = str(table["name"])
    if name != directory:
        raise ValueError(
            f"{source}: declares the name '{name}' in a directory called '{directory}'. Every "
            f"module's cmake resolves a sibling by its directory, so the two must agree.")

    return Module(
        name=name,
        repo=str(table.get("repo", "")),
        directory=name,
        alias=str(table["alias"]),
        distribution=str(table["distribution"]),
        fragment=str(table.get("fragment", Module.fragment)),
    )
