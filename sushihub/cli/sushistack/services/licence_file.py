"""The licence token `hub` writes beside a binary install.

Sushi ID issues one token per product; `hub` writes it, bare, into the module's
own directory and reads its expiry back to report. Nothing here verifies the
token: the engine does that offline against Sushi ID's JWKS at start-up, which
is why the file holds the token and nothing around it.

The shapes are in ``sushihub/contract/sushi-id.md``, section "Releases and the
licence file".
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from .identity import SushiId

# The file a binary install carries beside its release manifest.
LICENCE_FILE = "sushi-licence.jwt"


def write_licence(root: Path, client: SushiId, product: str) -> str:
    """Fetch the licence token for *product* and write it into the install at *root*.

    Args:
        root: The unpacked install's directory.
        client: A Sushi ID client with a live session.
        product: The product slug, which is the module name.

    Returns:
        The expiry Sushi ID declared, as an iso-8601 string.

    Raises:
        NoLicence: The account holds no live licence for *product*.
        SushiIdError: Sushi ID refused the request otherwise.
        OSError: The file could not be written.
    """
    token = client.licence_token(product)
    (root / LICENCE_FILE).write_text(token.token, encoding="utf-8")
    return token.expires_at


def read_licence_expiry(root: Path) -> str | None:
    """Return when the licence at *root* stops being valid.

    Reads the ``exp`` claim out of the token's payload without checking the
    signature, which is the engine's job and needs Sushi ID's JWKS.

    Args:
        root: The install's directory.

    Returns:
        The expiry as an iso-8601 string in UTC, or None when the file is
        absent, is not a JWT, or names no ``exp``.
    """
    try:
        token = (root / LICENCE_FILE).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        expiry = float(json.loads(payload)["exp"])
    except (ValueError, TypeError, KeyError):
        return None
    return datetime.fromtimestamp(expiry, timezone.utc).isoformat()
