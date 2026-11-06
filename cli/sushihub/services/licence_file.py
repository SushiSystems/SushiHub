# licence_file.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes and reads the licence token `hub` keeps beside a binary install.

Sushi Account issues one token per product; `hub` writes it bare and reads its expiry back.
Nothing here verifies the token. The shapes are in ``contract/sushi-account.md``, section
"Releases and the licence file"; the reason is in cli/README.md, "Notes on the source".
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from .identity import LicenceToken

# The file a binary install carries beside its release manifest.
LICENCE_FILE = "sushi-licence.jwt"


def store_licence(root: Path, token: LicenceToken) -> str:
    """Write the licence *token* bare into the install at *root*.

    Args:
        root: The unpacked install's directory.
        token: The token Sushi Account issued.

    Returns:
        The expiry Sushi Account declared, as an iso-8601 string.

    Raises:
        OSError: The file could not be written.
    """
    (root / LICENCE_FILE).write_text(token.token, encoding="utf-8")
    return token.expires_at


def read_licence_expiry(root: Path) -> str | None:
    """Return when the licence at *root* stops being valid.

    Reads the ``exp`` claim out of the token's payload without checking the
    signature, which is the engine's job and needs Sushi Account's JWKS.

    Args:
        root: The install's directory.

    Returns:
        The expiry as an iso-8601 string in UTC, or None when the file is
        absent, is not a JWT, or names no ``exp``.
    """
    try:
        token = (root / LICENCE_FILE).read_text(encoding="utf-8")
    except OSError:
        return None
    return licence_expiry(token)


def licence_expiry(token: str) -> str | None:
    """Return when the licence *token* stops being valid, from its ``exp`` claim.

    Args:
        token: The licence file's text, a JWT.

    Returns:
        The expiry as an iso-8601 string in UTC, or None when *token* is not a JWT or names no
        ``exp``.
    """
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    try:
        payload = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        expiry = float(json.loads(payload)["exp"])
    except (ValueError, TypeError, KeyError):
        return None
    return datetime.fromtimestamp(expiry, timezone.utc).isoformat()
