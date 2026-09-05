"""The four Sushi ID commands: what `ss login`, `logout`, `whoami` and `license` do.

Each function drives :class:`~sushistack.services.identity.SushiId` and writes to
the console, and returns the exit code and the payload the ``result`` event
carries. One factory, :func:`client`, decides which server and which credential
store every Sushi ID call in `ss` talks to, so a test replaces the pair in one
place. The endpoints are in ``sushihub/contract/sushi-id.md``.
"""

from __future__ import annotations

import webbrowser
from typing import Callable, NamedTuple

from .. import console
from ..config import identity_url
from .identity import Account, LoginError, SushiId
from .token_store import KeyringStore

# The label every progress event of the login carries.
LOGIN_LABEL = "login"


class Outcome(NamedTuple):
    """What a command returns to the CLI: its exit code and its result payload."""

    code: int
    payload: dict


def client() -> SushiId:
    """Build the client every Sushi ID call uses: the configured server, the keyring."""
    return SushiId(identity_url(), KeyringStore())


def login(open_browser: Callable[[str], bool] | None = None) -> Outcome:
    """Run the device grant to its end and store the session.

    Prints the user code and the verification URI, opens that URI in the
    browser, then reports one progress event per poll until Sushi ID answers.

    Args:
        open_browser: What opens the verification URI; :func:`webbrowser.open`
            when None.
    """
    id_client = client()
    try:
        code = id_client.start_device_login()
    except LoginError as error:
        console.error(str(error))
        return Outcome(1, {})

    console.info(f"Your Sushi ID code is {code.user_code}.")
    console.info(f"Open {code.verification_uri} and enter it.")
    (open_browser or webbrowser.open)(code.verification_uri)

    try:
        id_client.wait_for_token(
            code, on_poll=lambda polls: console.progress(LOGIN_LABEL, polls, 0, None))
    except LoginError as error:
        console.error(str(error))
        return Outcome(1, {})

    account = id_client.me()
    email = account.email if account else ""
    console.success(f"Signed in to Sushi ID as {email}." if email else "Signed in to Sushi ID.")
    return Outcome(0, {"email": email})


def logout() -> Outcome:
    """Forget the stored session, whether or not there was one."""
    client().logout()
    console.success("Signed out of Sushi ID.")
    return Outcome(0, {})


def whoami() -> Outcome:
    """Print the signed-in account as a two-column table."""
    account = client().me()
    if account is None:
        console.warn("Not signed in. Run `ss login`.")
        return Outcome(1, {})
    console.table(
        ["Field", "Value"],
        [["Account", account.account_id],
         ["Email", account.email],
         ["Licences", str(len(account.licenses))]],
        title="Sushi ID",
    )
    return Outcome(0, _payload(account))


def license() -> Outcome:
    """Print the licences the signed-in account holds, one row each."""
    account = client().me()
    if account is None:
        console.warn("Not signed in. Run `ss login`.")
        return Outcome(1, {})
    if not account.licenses:
        console.info("No licences on this account.")
        return Outcome(0, {"licenses": []})
    console.table(
        ["Product", "Holder", "Expires"],
        [[item.product, item.holder, item.expires_at or "never"]
         for item in account.licenses],
        title="Sushi ID Licences",
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
