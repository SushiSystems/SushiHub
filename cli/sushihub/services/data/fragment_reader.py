# fragment_reader.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the ``[data.<name>]`` tables of a dependency fragment.

sushicore's fragment reader sees ``[data]`` as one more dependency and keeps nothing of it, so
hub reads the tables itself. The table is specified in docs/design/HUB/DATA_PACKAGES.md.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .errors import DataFragmentError
from .package import K_DATA_TABLE, DataPackage

#: The keys every table must carry.
K_REQUIRED_KEYS = ("url", "sha256", "bytes", "licence", "destination")

#: The URL schemes a package may be fetched with.
K_SCHEMES = ("http", "https")

#: The file names the store accepts: no separator, drive colon or space.
K_FILE_NAME = re.compile(r"[\w.+%~-]+")

#: The shape of a SHA-256 written as hex.
K_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


def read_data_packages(fragment: Path, owner: str, checkout: Path) -> list[DataPackage]:
    """Returns the data packages the fragment at *fragment* declares, in file order.

    Args:
        fragment: A module's ``cli/sushistack.deps.toml``.
        owner: The module that owns the fragment.
        checkout: The module's checkout, which each ``destination`` is relative to.

    Raises:
        DataFragmentError: The file does not parse, ``data`` is not a table of tables, or a
            table lacks a required key or holds a wrong value; the message names the table.
    """
    try:
        with fragment.open("rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise DataFragmentError(f"{fragment}: cannot be read: {error}") from error
    tables = document.get(K_DATA_TABLE, {})
    if not isinstance(tables, dict):
        raise DataFragmentError(
            f"{fragment}: 'data' is a {type(tables).__name__}, and it holds one "
            "[data.<name>] table per file.")
    return [_read_table(fragment, owner, checkout, name, table) for name, table in tables.items()]


def _read_table(fragment: Path, owner: str, checkout: Path, name: str,
                table: object) -> DataPackage:
    """Returns the package ``[data.<name>]`` declares.

    Raises:
        DataFragmentError: *table* is not a table, lacks a required key, or holds a bad value.
    """
    where = f"{fragment}: [data.{name}]"
    if not isinstance(table, dict):
        raise DataFragmentError(f"{where} is a {type(table).__name__}, and it is a table.")
    for key in K_REQUIRED_KEYS:
        if key not in table:
            raise DataFragmentError(f"{where} has no '{key}'; the keys {', '.join(K_REQUIRED_KEYS)} "
                                    "are required.")
    url = _read_text(where, table, "url")
    file_name = PurePosixPath(urlparse(url).path).name
    if (urlparse(url).scheme not in K_SCHEMES or file_name == ".."
            or not K_FILE_NAME.fullmatch(file_name)):
        raise DataFragmentError(
            f"{where} url is {url!r}, and it is an http or https address of a file whose name "
            "holds letters, digits and . _ + % ~ - only.")
    sha256 = _read_text(where, table, "sha256").lower()
    if not K_SHA256_HEX.fullmatch(sha256):
        raise DataFragmentError(f"{where} sha256 is {sha256!r}, and a SHA-256 is 64 hex digits.")
    size = table["bytes"]
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise DataFragmentError(f"{where} bytes is {size!r}, and it is a count of bytes.")
    required = table.get("required", False)
    if not isinstance(required, bool):
        raise DataFragmentError(f"{where} required is {required!r}, and it is true or false.")
    return DataPackage(
        name=name, owner=owner, checkout=checkout, url=url, sha256=sha256, size=size,
        licence=_read_text(where, table, "licence"),
        destination=_read_text(where, table, "destination"),
        description=str(table.get("description", "")), required=required)


def _read_text(where: str, table: dict, key: str) -> str:
    """Returns the non-empty string *table* holds under *key*.

    Raises:
        DataFragmentError: The value is not a string, or is empty.
    """
    value = table[key]
    if not isinstance(value, str) or not value.strip():
        raise DataFragmentError(f"{where} {key} is {value!r}, and it is a non-empty string.")
    return value
