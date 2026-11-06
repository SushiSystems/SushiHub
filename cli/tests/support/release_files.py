# release_files.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides the release archives and the unpacked installs a test lays out on disk."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from sushihub.services import presence

K_MANIFEST = {"product": "sushiengine", "version": "1.4.2", "platform": "windows-x64",
              "bundled": {"sushiruntime": "0.9.0"}, "signature": "base64"}


def zip_bytes(members: dict[str, str]) -> bytes:
    """Build a zip archive in memory out of a name-to-text map."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for name, text in members.items():
            bundle.writestr(name, text)
    return buffer.getvalue()


def release_members(**overrides) -> dict[str, str]:
    """The members a well-formed release archive carries."""
    return {presence.RELEASE_MANIFEST: json.dumps({**K_MANIFEST, **overrides}),
            "bin/se.txt": "the engine"}


def binary_install(path: Path, version: str = "1.4.2") -> None:
    """Unpack a fake binary install at *path*: a directory and a release manifest."""
    path.mkdir(parents=True, exist_ok=True)
    (path / presence.RELEASE_MANIFEST).write_text(
        json.dumps({"product": path.name, "version": version,
                    "platform": "windows-x64",
                    "bundled": {"sushiruntime": "0.9.0"},
                    "signature": "base64"}),
        encoding="utf-8")
