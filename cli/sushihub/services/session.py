# session.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs the four Sushi Account commands: `hub login`, `logout`, `whoami` and `license`.

Each function drives :class:`~sushihub.services.identity.SushiAccount`, writes to the console
and returns the exit code and the payload the ``result`` event carries. :func:`client` decides
which server and which credential store every Sushi Account call in `hub` talks to. The
endpoints are in ``contract/sushi-account.md``.
"""

from __future__ import annotations

import functools
import webbrowser
from typing import Callable, NamedTuple

from .. import console
from ..config import identity_url
from ..errors import SushiAccountError
from .identity import Account, SushiAccount
from .ports import Ports
from .token_store import KeyringStore

# The label every progress event of the login carries.
LOGIN_LABEL = "login"


class Outcome(NamedTuple):
    """What a command returns to the CLI: its exit code and its result payload."""

    code: int
    payload: dict


def _reported(command: Callable[..., Outcome]) -> Callable[..., Outcome]:
    """Returns *command* wrapped to end a Sushi Account failure in one error line and code 1."""
    @functools.wraps(command)
    def wrapper(*args, ports: Ports | None = None, **kwargs) -> Outcome:
        """Runs the command against *ports*, this machine's when None, and reports its failure."""
        ports = ports or Ports.machine(console)
        try:
            return command(*args, ports=ports, **kwargs)
        except SushiAccountError as error:
            ports.console.error(str(error))
            return Outcome(1, {})

    return wrapper


def client() -> SushiAccount:
    """Build the client every Sushi Account call uses: the configured server, the keyring."""
    return SushiAccount(identity_url(), KeyringStore())


@_reported
def login(open_browser: Callable[[str], bool] | None = None, *, ports: Ports) -> Outcome:
    """Run the device grant to its end and store the session.

    Prints the user code and the verification URI, opens that URI in the
    browser, then reports one progress event per poll until Sushi Account answers.

    Args:
        open_browser: What opens the verification URI; :func:`webbrowser.open`
            when None.
        ports: What the login reaches the outside through; this machine's when the caller
            gives none.
    """
    out = ports.console
    id_client = ports.account()
    code = id_client.start_device_login()

    out.info(f"Your Sushi Account code is {code.user_code}.")
    out.info(f"Open {code.verification_uri} and enter it.")
    (open_browser or webbrowser.open)(code.verification_uri)

    id_client.wait_for_token(
        code, on_poll=lambda polls: out.progress(LOGIN_LABEL, polls, 0, None))

    account = id_client.me()
    email = account.email if account else ""
    out.success(f"Signed in to Sushi Account as {email}." if email else "Signed in to Sushi Account.")
    return Outcome(0, {"email": email})


@_reported
def logout(*, ports: Ports) -> Outcome:
    """Forget the stored session, whether or not there was one."""
    out = ports.console
    ports.account().logout()
    out.success("Signed out of Sushi Account.")
    return Outcome(0, {})


@_reported
def whoami(*, ports: Ports) -> Outcome:
    """Print the signed-in account as a two-column table."""
    out = ports.console
    account = ports.account().me()
    if account is None:
        out.warn("Not signed in. Run `hub login`.")
        return Outcome(1, {})
    out.table(
        ["Field", "Value"],
        [["Account", account.account_id],
         ["Email", account.email],
         ["Licences", str(len(account.licenses))]],
        title="Sushi Account",
    )
    return Outcome(0, _payload(account))


@_reported
def license(*, ports: Ports) -> Outcome:
    """Print the licences the signed-in account holds, one row each."""
    out = ports.console
    account = ports.account().me()
    if account is None:
        out.warn("Not signed in. Run `hub login`.")
        return Outcome(1, {})
    if not account.licenses:
        out.info("No licences on this account.")
        return Outcome(0, {"licenses": []})
    out.table(
        ["Product", "Holder", "Expires"],
        [[item.product, item.holder, item.expires_at or "never"]
         for item in account.licenses],
        title="Sushi Account Licences",
    )
    return Outcome(0, {"licenses": _payload(account)["licenses"]})


def _payload(account: Account) -> dict:
    """Render *account* as the JSON structure the result event carries."""
    return {
        "account_id": account.account_id,
        "email": account.email,
        "licenses": [
            {"product": item.product, "holder": item.holder, "expires_at": item.expires_at}
            for item in account.licenses
        ],
    }
