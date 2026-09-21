"""Reading `sushi-module.toml`, the manifest a module writes about itself.

A checkout carrying one describes itself, so `hub` can recognise it without a
catalog entry. This module turns the file into a :class:`~.catalog.Module` or
refuses it; which of the two wins when both a manifest and a catalog entry exist
is decided where both are in scope, not here.

The format is fixed in docs/reference/MODULE_MANIFEST.md.
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
        ValueError: The file is there and cannot be believed: a required key is
            missing, ``name`` disagrees with the directory, or a table the reader
            does not know is present. An unknown *key* is ignored instead, so a
            newer module can add one.
    """
    path = root / MANIFEST_FILE
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        document = tomllib.load(handle)

    unknown = [name for name in document if name != MODULE_TABLE]
    if unknown:
        raise ValueError(
            f"{path}: unknown table(s) {', '.join(sorted(unknown))}. A reader that drops a "
            f"table it does not know is how a whole section goes missing in silence.")
    if MODULE_TABLE not in document:
        raise ValueError(f"{path}: no [{MODULE_TABLE}] table, which is what this format is.")

    table = document[MODULE_TABLE]
    absent = [key for key in REQUIRED_KEYS if not table.get(key)]
    if absent:
        raise ValueError(f"{path}: [{MODULE_TABLE}] declares no {', '.join(absent)}.")

    name = str(table["name"])
    if name != root.name:
        raise ValueError(
            f"{path}: declares the name '{name}' in a directory called '{root.name}'. Every "
            f"module's cmake resolves a sibling by its directory, so the two must agree.")

    return Module(
        name=name,
        repo=str(table.get("repo", "")),
        directory=name,
        alias=str(table["alias"]),
        distribution=str(table["distribution"]),
        fragment=str(table.get("fragment", Module.fragment)),
    )
