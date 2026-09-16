"""Whether a newer release of a binary install exists, asked of Sushi Account.

This is the online half of ``hub status --check-updates``. A refusal is not an
error here: the status payload leaves the field null and the caller prints the
reason once. See sushihub/contract/README.md, "The status payload".
"""

from __future__ import annotations

from dataclasses import dataclass

from .identity import SushiAccount, SushiAccountError


@dataclass(frozen=True)
class UpdateCheck:
    """The latest version Sushi Account names, or the reason it named none."""

    version: str | None
    reason: str | None


def latest_release(client: SushiAccount, product: str, platform: str) -> UpdateCheck:
    """Ask Sushi Account for the latest *platform* release of *product*.

    Args:
        client: The Sushi Account client, signed in or not.
        product: The product slug, which is the module name.
        platform: The platform string the install was unpacked for.

    Returns:
        The version with no reason, or no version and the message Sushi Account's
        refusal or the failed connection produced.
    """
    try:
        return UpdateCheck(client.resolve_release(product, platform).version, None)
    except SushiAccountError as error:
        return UpdateCheck(None, str(error))
