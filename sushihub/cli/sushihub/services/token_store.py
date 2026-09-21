"""Where the Sushi Account session lives between two `hub` runs.

The client in ``sushihub.services.identity`` never names a credential store: it
takes a :class:`TokenStore`. In production that is :class:`KeyringStore`, which
puts one JSON document in the operating system's credential store; in tests it is
:class:`MemoryStore`, which holds it in the process and is gone when the process
is. The document's fields are the ones
``sushihub/contract/sushi-account.md`` says the token endpoint returns.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Protocol

import keyring
import keyring.errors

# The credential store's coordinates. One entry holds the whole session, so a
# sign-out is one deletion.
KEYRING_SERVICE = "sushihub"
KEYRING_USERNAME = "sushi-account"


@dataclass(frozen=True)
class Tokens:
    """One signed-in session: the two tokens and when the access token dies."""

    access_token: str
    refresh_token: str
    expires_at: float          # epoch seconds, as time.time() reports them


class TokenStore(Protocol):
    """Reads, writes and forgets the one session `hub` holds."""

    def load(self) -> Tokens | None:
        """Return the stored session, or None when nobody is signed in."""

    def save(self, tokens: Tokens) -> None:
        """Store *tokens* as the session, replacing any earlier one."""

    def clear(self) -> None:
        """Forget the stored session. Storing nothing is not an error."""


def _decode(blob: str | None) -> Tokens | None:
    """Parse a stored JSON document, treating anything unreadable as absent."""
    if not blob:
        return None
    try:
        data = json.loads(blob)
        return Tokens(
            access_token=str(data["access_token"]),
            refresh_token=str(data["refresh_token"]),
            expires_at=float(data["expires_at"]),
        )
    except (ValueError, TypeError, KeyError):
        return None


class KeyringStore:
    """Keeps the session in the operating system's credential store."""

    def load(self) -> Tokens | None:
        """Return the session keyring holds, or None when it holds none."""
        return _decode(keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME))

    def save(self, tokens: Tokens) -> None:
        """Write *tokens* as one JSON document under the service and username."""
        keyring.set_password(
            KEYRING_SERVICE, KEYRING_USERNAME,
            json.dumps(asdict(tokens), ensure_ascii=False))

    def clear(self) -> None:
        """Delete the entry, ignoring a keyring that has none to delete."""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except keyring.errors.PasswordDeleteError:
            pass


class MemoryStore:
    """Keeps the session in this process, for tests and for `--dry-run` paths."""

    def __init__(self, tokens: Tokens | None = None) -> None:
        """Start holding *tokens*, or nothing when none is given."""
        self._tokens = tokens

    def load(self) -> Tokens | None:
        """Return the held session, or None when there is none."""
        return self._tokens

    def save(self, tokens: Tokens) -> None:
        """Hold *tokens* as the session."""
        self._tokens = tokens

    def clear(self) -> None:
        """Drop the held session."""
        self._tokens = None
