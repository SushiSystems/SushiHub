"""The Sushi Account client: the device grant, the account read, licences and releases.

One class over the six endpoints written down in
``sushihub/contract/sushi-account.md``. It prints nothing and asks nothing: the
commands in ``sushistack.services.session`` own the terminal, and the credential
store arrives as a :class:`~sushistack.services.token_store.TokenStore`. The
clock, the sleep and the HTTP opener are constructor arguments so a test can run
the whole grant against a fake server in a thread with no wall-clock wait.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .token_store import TokenStore, Tokens

# The client identifier every device-grant request carries.
CLIENT_ID = "sushihub"

# How close to expiry an access token is refreshed rather than used, in seconds.
REFRESH_MARGIN = 30.0

# How long a single request may take before it is abandoned, in seconds.
TIMEOUT = 30.0


@dataclass(frozen=True)
class DeviceCode:
    """One device grant in flight: what to show a person and how to poll for it."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@dataclass(frozen=True)
class Licence:
    """One licence on an account: the product, who holds it, when it lapses."""

    product: str
    holder: str                 # "account" or "org"
    expires_at: str | None      # iso-8601, or None for a licence that does not lapse


@dataclass(frozen=True)
class LicenceToken:
    """The token the engine reads at start-up, and when it stops being valid."""

    token: str
    expires_at: str             # iso-8601


@dataclass(frozen=True)
class ReleaseInfo:
    """One downloadable release: where it is, what it weighs, what it hashes to."""

    version: str
    platform: str
    url: str                    # signed, and short-lived
    sha256: str
    size: int                   # bytes
    expires_at: str             # iso-8601; when the url stops working


@dataclass(frozen=True)
class Account:
    """Who is signed in, and what they are licensed for."""

    account_id: str
    email: str
    licenses: tuple[Licence, ...]


class SushiAccountError(RuntimeError):
    """A Sushi Account call this client could not carry through."""


class LoginError(SushiAccountError):
    """The device grant ended without tokens."""


class LoginDenied(LoginError):
    """The person refused the grant."""


class LoginExpired(LoginError):
    """The grant ran out before the person completed it."""


class NoLicence(SushiAccountError):
    """The account holds no live licence for the product that was asked for."""


class NoRelease(SushiAccountError):
    """The product has no release for the platform that was asked for."""


class UnknownProduct(SushiAccountError):
    """Sushi Account knows no product under that name."""


class SushiAccount:
    """Speaks the six Sushi Account endpoints and keeps one session in a store."""

    def __init__(self, base_url: str, store: TokenStore, *,
                 http: Callable = urllib.request.urlopen,
                 sleep: Callable[[float], None] = time.sleep,
                 now: Callable[[], float] = time.time) -> None:
        """Bind the server, the credential store, and the three seams a test replaces."""
        self._base = base_url.rstrip("/")
        self._store = store
        self._http = http
        self._sleep = sleep
        self._now = now

    def start_device_login(self) -> DeviceCode:
        """Ask for a device code and return what the person needs to approve it.

        Raises:
            LoginError: The endpoint answered anything but 200.
        """
        status, body = self._post("/api/device/code", {"client_id": CLIENT_ID})
        if status != 200:
            raise LoginError(f"Sushi Account refused to start the login (HTTP {status}).")
        return DeviceCode(
            device_code=str(body["device_code"]),
            user_code=str(body["user_code"]),
            verification_uri=str(body["verification_uri"]),
            expires_in=int(body.get("expires_in", 600)),
            interval=int(body.get("interval", 5)),
        )

    def wait_for_token(self, code: DeviceCode,
                       on_poll: Callable[[int], None] | None = None) -> Tokens:
        """Poll until the person approves *code*, then store and return the tokens.

        Waits ``code.interval`` seconds between polls and doubles that wait each
        time the endpoint answers ``slow_down``. *on_poll* is called with the
        number of polls made so far, which is how `hub login` reports progress.

        Raises:
            LoginDenied: The person refused the grant.
            LoginExpired: The grant ran out, by the endpoint's word or the clock's.
            LoginError: The endpoint answered an error this client does not know.
        """
        interval = float(max(1, code.interval))
        deadline = self._now() + code.expires_in
        polls = 0
        while True:
            status, body = self._post(
                "/api/device/token",
                {"client_id": CLIENT_ID, "device_code": code.device_code})
            polls += 1
            if on_poll is not None:
                on_poll(polls)
            if status == 200:
                return self._remember(body, refresh_token=str(body["refresh_token"]))
            error = str(body.get("error", ""))
            if error == "access_denied":
                raise LoginDenied("The sign-in was refused in the browser.")
            if error == "expired_token":
                raise LoginExpired("The sign-in code expired. Run `hub login` again.")
            if error == "slow_down":
                interval *= 2
            elif error != "authorization_pending":
                raise LoginError(f"Sushi Account answered '{error or status}' while polling.")
            if self._now() >= deadline:
                raise LoginExpired("The sign-in code expired. Run `hub login` again.")
            self._sleep(interval)

    def access_token(self) -> str | None:
        """Return a live access token, refreshing it first when it is about to die.

        Returns None when the store holds no session, and clears the store when
        the refresh endpoint rejects the refresh token.
        """
        tokens = self._store.load()
        if tokens is None:
            return None
        if tokens.expires_at > self._now() + REFRESH_MARGIN:
            return tokens.access_token
        status, body = self._post("/api/token/refresh",
                                  {"refresh_token": tokens.refresh_token})
        if status != 200:
            self._store.clear()
            return None
        return self._remember(body, refresh_token=tokens.refresh_token).access_token

    def me(self) -> Account | None:
        """Return the signed-in account, or None when nobody is signed in."""
        token = self.access_token()
        if token is None:
            return None
        status, body = self._get("/api/me", token)
        if status != 200:
            return None
        return Account(
            account_id=str(body.get("account_id", "")),
            email=str(body.get("email", "")),
            licenses=tuple(
                Licence(product=str(entry.get("product", "")),
                        holder=str(entry.get("holder", "")),
                        expires_at=entry.get("expires_at"))
                for entry in body.get("licenses", [])),
        )

    def licence_token(self, product: str) -> LicenceToken:
        """Ask for the licence token *product* reads at start-up.

        Args:
            product: The product slug, which is the module name.

        Raises:
            NoLicence: The account holds no live licence for *product*.
            UnknownProduct: Sushi Account knows no such product.
            SushiAccountError: Nobody is signed in, or the endpoint refused otherwise.
        """
        status, body = self._bearer_post("/api/licenses/token", {"product": product})
        if status != 200:
            self._refuse(status, body, product)
        return LicenceToken(token=str(body["licence_token"]),
                            expires_at=str(body.get("expires_at", "")))

    def resolve_release(self, product: str, platform: str,
                        version: str | None = None) -> ReleaseInfo:
        """Ask where the *platform* release of *product* may be downloaded from.

        Args:
            product: The product slug, which is the module name.
            platform: The platform string
                :func:`~sushistack.services.releases.host_platform` derives.
            version: The release to resolve; the latest one when None.

        Raises:
            NoLicence: The account holds no live licence for *product*.
            NoRelease: The product has no release for *platform*.
            UnknownProduct: Sushi Account knows no such product.
            SushiAccountError: Nobody is signed in, or the endpoint refused otherwise.
        """
        request = {"product": product, "platform": platform}
        if version is not None:
            request["version"] = version
        status, body = self._bearer_post("/api/releases/resolve", request)
        if status != 200:
            self._refuse(status, body, f"{product} for {platform}")
        return ReleaseInfo(version=str(body["version"]),
                           platform=str(body.get("platform", platform)),
                           url=str(body["url"]),
                           sha256=str(body["sha256"]),
                           size=int(body["size"]),
                           expires_at=str(body.get("expires_at", "")))

    def logout(self) -> None:
        """Forget the stored session. Sushi Account is not told."""
        self._store.clear()

    def _bearer_post(self, path: str, body: dict) -> tuple[int, dict]:
        """POST *body* to *path* under a live access token.

        Raises:
            SushiAccountError: Nobody is signed in on this machine.
        """
        token = self.access_token()
        if token is None:
            raise SushiAccountError("Not signed in to Sushi Account. Run `hub login`.")
        return self._post(path, body, token=token)

    @staticmethod
    def _refuse(status: int, body: dict, subject: str) -> None:
        """Raise the error Sushi Account's refusal of *subject* names.

        Args:
            status: The status the endpoint answered.
            body: Its parsed body, carrying ``error`` when it named one.
            subject: What was asked for, as the message says it.

        Raises:
            NoLicence, NoRelease, UnknownProduct, SushiAccountError: Always; which one
                follows the ``error`` the body names, then the status.
        """
        error = str(body.get("error", ""))
        if error == "no_licence":
            raise NoLicence(f"This account holds no live licence for {subject}.")
        if error == "unknown_product":
            raise UnknownProduct(f"Sushi Account knows no product called {subject}.")
        if error == "no_release":
            raise NoRelease(f"Sushi Account has no release of {subject}.")
        if status == 429:
            raise SushiAccountError("Sushi Account is rate-limiting this account. Try again later.")
        raise SushiAccountError(f"Sushi Account refused to serve {subject} (HTTP {status}).")

    def _remember(self, body: dict, *, refresh_token: str) -> Tokens:
        """Store the access token in *body* against this clock, and return it."""
        tokens = Tokens(
            access_token=str(body["access_token"]),
            refresh_token=refresh_token,
            expires_at=self._now() + float(body.get("expires_in", 0)),
        )
        self._store.save(tokens)
        return tokens

    def _post(self, path: str, body: dict,
              token: str | None = None) -> tuple[int, dict]:
        """Send *body* as JSON to *path*, bearing *token* when one is given."""
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            self._base + path,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST")
        return self._send(request)

    def _get(self, path: str, token: str) -> tuple[int, dict]:
        """Read *path* with a bearer token and return the status and parsed answer."""
        request = urllib.request.Request(
            self._base + path,
            headers={"Authorization": f"Bearer {token}"},
            method="GET")
        return self._send(request)

    def _send(self, request: urllib.request.Request) -> tuple[int, dict]:
        """Perform *request*, reading an HTTP error's body as an ordinary answer.

        Raises:
            LoginError: The server could not be reached at all.
        """
        try:
            response = self._http(request, timeout=TIMEOUT)
        except urllib.error.HTTPError as error:
            return error.code, _parse(error.read())
        except urllib.error.URLError as error:
            raise LoginError(f"Sushi Account at {self._base} is unreachable: {error.reason}") from error
        with response:
            return getattr(response, "status", 200), _parse(response.read())


def _parse(payload: bytes) -> dict:
    """Parse a JSON body, reading anything unreadable as an empty object."""
    try:
        parsed = json.loads(payload or b"{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
