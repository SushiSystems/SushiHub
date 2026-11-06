# account.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds a Sushi Account client that answers from fixed tables and opens no connection."""

from __future__ import annotations

from typing import Callable

from ...errors import SushiAccountError
from ..identity import Account, DeviceCode, LicenceToken, NoLicence, NoRelease, ReleaseInfo

#: The device code every login of this client hands out.
DEVICE_CODE = DeviceCode(device_code="device-1", user_code="ABCD-EFGH",
                         verification_uri="https://account.test/device",
                         expires_in=600, interval=5)


class InMemoryAccount:
    """Keeps one account, its licences and the releases it may download.

    A login is approved at the first poll and signs *account* in. Every call that needs a
    session raises :class:`~sushihub.errors.SushiAccountError` while nobody is signed in, with
    the message the real client gives.

    Args:
        account: The account a login signs in.
        signed_in: Whether the account starts signed in.
        licences: The licence token of each product the account holds.
        releases: The release of each product and platform pair.
        refusal: What a login raises instead of signing in, or None to approve it.
    """

    def __init__(self, account: Account, *, signed_in: bool = False,
                 licences: dict[str, LicenceToken] | None = None,
                 releases: dict[tuple[str, str], ReleaseInfo] | None = None,
                 refusal: SushiAccountError | None = None) -> None:
        """Keeps the tables; no call is recorded yet."""
        self._account = account
        self._signed_in = signed_in
        self._licences = dict(licences or {})
        self._releases = dict(releases or {})
        self._refusal = refusal

    @property
    def signed_in(self) -> bool:
        """Returns whether a session is stored."""
        return self._signed_in

    def start_device_login(self) -> DeviceCode:
        """Returns :data:`DEVICE_CODE`."""
        return DEVICE_CODE

    def wait_for_token(self, code: DeviceCode, on_poll: Callable[[int], None] | None = None) -> None:
        """Polls once, then signs the account in or raises the refusal it was given."""
        if on_poll is not None:
            on_poll(1)
        if self._refusal is not None:
            raise self._refusal
        self._signed_in = True

    def access_token(self) -> str | None:
        """Returns a token while signed in, None otherwise."""
        return "access-token" if self._signed_in else None

    def me(self) -> Account | None:
        """Returns the account while signed in, None otherwise."""
        return self._account if self._signed_in else None

    def licence_token(self, product: str) -> LicenceToken:
        """Returns the licence token of *product*.

        Raises:
            NoLicence: The account holds no licence for *product*.
            SushiAccountError: Nobody is signed in.
        """
        self._require_session()
        if product not in self._licences:
            raise NoLicence(f"This account holds no live licence for {product}.")
        return self._licences[product]

    def resolve_release(self, product: str, platform: str, version: str | None = None) -> ReleaseInfo:
        """Returns the release of *product* for *platform*; *version* is not consulted.

        Raises:
            NoRelease: No release was given for that pair.
            SushiAccountError: Nobody is signed in.
        """
        self._require_session()
        release = self._releases.get((product, platform))
        if release is None:
            raise NoRelease(f"Sushi Account has no release of {product} for {platform}.")
        return release

    def logout(self) -> None:
        """Forgets the session."""
        self._signed_in = False

    def _require_session(self) -> None:
        """Raises the real client's error while nobody is signed in."""
        if not self._signed_in:
            raise SushiAccountError("Not signed in to Sushi Account. Run `hub login`.")
