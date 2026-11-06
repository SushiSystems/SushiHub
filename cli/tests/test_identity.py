# test_identity.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Sushi Account: where the base URL comes from, the token store, the client, the commands."""

from __future__ import annotations

import hashlib
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import keyring
import keyring.backend
import keyring.errors
import pytest
from sushicore.console_memory import RecordingConsole
from sushicore.errors import SushiCoreError

from sushihub.config import (
    DEFAULT_IDENTITY_URL,
    WORKSPACE_MARKER,
    identity_url,
    workspace_file,
)
from sushihub.services import session
from sushihub.services.identity import (
    Account,
    AccountUnreachable,
    Licence,
    LicenceToken,
    LoginDenied,
    LoginExpired,
    NoLicence,
    NoRelease,
    ReleaseInfo,
    SushiAccount,
    SushiAccountError,
    UnknownProduct,
)
from sushihub.services.memory.account import DEVICE_CODE, InMemoryAccount
from sushihub.services.memory.ports import memory_ports
from sushihub.services.token_store import (
    KEYRING_SERVICE,
    KEYRING_USERNAME,
    CredentialStoreError,
    KeyringStore,
    MemoryStore,
    Tokens,
)


def _workspace_with_identity(tmp_path, url: str):
    """Write a throwaway workspace whose workspace.toml pins the Sushi Account url."""
    (tmp_path / WORKSPACE_MARKER).mkdir()
    workspace_file(tmp_path).write_text(f'[identity]\nurl = "{url}"\n', encoding="utf-8")
    return tmp_path


@pytest.mark.medium
def test_identity_url_prefers_env(monkeypatch, tmp_path):
    _workspace_with_identity(tmp_path, "http://127.0.0.1:9001")
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.setenv("SUSHI_ACCOUNT_URL", "http://127.0.0.1:8123/")
    assert identity_url() == "http://127.0.0.1:8123"


@pytest.mark.medium
def test_identity_url_reads_the_config_key(monkeypatch, tmp_path):
    _workspace_with_identity(tmp_path, "http://127.0.0.1:9001/")
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.delenv("SUSHI_ACCOUNT_URL", raising=False)
    assert identity_url() == "http://127.0.0.1:9001"


@pytest.mark.parametrize("point_home", [
    lambda patch, root: patch.setenv("SUSHISTACK_HOME", str(root)),
    lambda patch, root: patch.delenv("SUSHISTACK_HOME", raising=False),
], ids=["workspace without the key", "outside any workspace"])
@pytest.mark.medium
def test_identity_url_falls_back_to_the_packaged_defaults(monkeypatch, tmp_path, point_home):
    """The packaged defaults carry the url, with or without a workspace to read."""
    point_home(monkeypatch, tmp_path)
    monkeypatch.delenv("SUSHI_ACCOUNT_URL", raising=False)
    assert identity_url() == DEFAULT_IDENTITY_URL


class DictBackend(keyring.backend.KeyringBackend):
    """An in-memory credential store, so a test never touches the OS keyring."""

    priority = 1

    def __init__(self) -> None:
        """Start with no stored passwords."""
        super().__init__()
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        """Return the stored password, or None when there is none."""
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        """Store *password* under the service and username."""
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        """Forget the password stored under the service and username."""
        if (service, username) not in self.passwords:
            raise keyring.errors.PasswordDeleteError(username)
        del self.passwords[(service, username)]


@pytest.fixture
def backend():
    """Install the in-memory backend for one test and restore the real one after."""
    previous = keyring.get_keyring()
    fake = DictBackend()
    keyring.set_keyring(fake)
    try:
        yield fake
    finally:
        keyring.set_keyring(previous)


@pytest.mark.small
def test_memory_store_round_trips_and_clears():
    store = MemoryStore()
    assert store.load() is None
    tokens = Tokens(access_token="a", refresh_token="r", expires_at=1234.5)
    store.save(tokens)
    assert store.load() == tokens
    store.clear()
    assert store.load() is None


@pytest.mark.medium
def test_keyring_store_round_trips_through_the_backend(backend):
    store = KeyringStore()
    assert store.load() is None
    store.save(Tokens(access_token="a", refresh_token="r", expires_at=99.0))
    assert backend.passwords[(KEYRING_SERVICE, KEYRING_USERNAME)]
    assert store.load() == Tokens(access_token="a", refresh_token="r", expires_at=99.0)
    store.clear()
    assert store.load() is None


@pytest.mark.medium
def test_keyring_store_reads_a_corrupt_entry_as_absent(backend):
    backend.set_password(KEYRING_SERVICE, KEYRING_USERNAME, "not json")
    assert KeyringStore().load() is None


@pytest.mark.medium
def test_keyring_store_clear_is_quiet_when_nothing_is_stored(backend):
    KeyringStore().clear()
    assert backend.passwords == {}


class BrokenBackend(keyring.backend.KeyringBackend):
    """A credential store whose every call fails, as on a machine with no backend."""

    priority = 1

    def get_password(self, service: str, username: str) -> str | None:
        """Fails the way keyring does when no backend is installed."""
        raise keyring.errors.NoKeyringError("No recommended backend was available.")

    def set_password(self, service: str, username: str, password: str) -> None:
        """Fails the way a refused write does."""
        raise keyring.errors.PasswordSetError("refused")

    def delete_password(self, service: str, username: str) -> None:
        """Fails the way a locked store does."""
        raise keyring.errors.KeyringLocked("locked")


@pytest.fixture
def broken_backend():
    """Install the failing backend for one test and restore the real one after."""
    previous = keyring.get_keyring()
    keyring.set_keyring(BrokenBackend())
    try:
        yield
    finally:
        keyring.set_keyring(previous)


@pytest.mark.medium
def test_every_keyring_failure_is_a_credential_store_error(broken_backend):
    """Reading, writing and clearing each wrap keyring's own error, cause kept."""
    store = KeyringStore()
    with pytest.raises(CredentialStoreError) as loading:
        store.load()
    assert isinstance(loading.value.__cause__, keyring.errors.NoKeyringError)
    with pytest.raises(CredentialStoreError):
        store.save(Tokens(access_token="a", refresh_token="r", expires_at=1.0))
    with pytest.raises(CredentialStoreError):
        store.clear()


@pytest.mark.small
def test_the_account_errors_share_the_base_the_entry_point_catches():
    """Every account failure derives from the error sushicore's entry point reports."""
    assert issubclass(SushiAccountError, SushiCoreError)
    assert issubclass(CredentialStoreError, SushiAccountError)
    assert issubclass(AccountUnreachable, SushiAccountError)


class Reply:
    """An open response of a given status whose body is JSON, as urlopen returns one."""

    def __init__(self, status: int, body: dict) -> None:
        """Hold the status and the JSON body to answer with."""
        self.status = status
        self._payload = json.dumps(body).encode("utf-8")

    def __enter__(self) -> "Reply":
        """Return the response itself, as urlopen's does."""
        return self

    def __exit__(self, *exc) -> None:
        """Close nothing."""

    def read(self) -> bytes:
        """Return the whole body."""
        return self._payload


class ScriptedHttp:
    """The http seam of a client: answers from a script and keeps every request it saw."""

    def __init__(self, *replies: Reply) -> None:
        """Answer the requests with *replies*, in order."""
        self._replies = list(replies)
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request, timeout):
        """Record *request* and return the next scripted reply."""
        self.requests.append(request)
        return self._replies.pop(0)


def _signed_in_over(http) -> SushiAccount:
    """Return a client with a live session whose requests go through *http*."""
    return SushiAccount("http://account.invalid",
                        MemoryStore(Tokens("access-1", "refresh-1", 1e12)),
                        http=http, now=lambda: 0.0)


@pytest.mark.small
def test_a_refused_connection_is_reported_as_unreachable():
    """A URLError becomes AccountUnreachable with the original as its cause."""
    def refuse(request, timeout):
        """Fails the way urlopen does when nothing listens."""
        raise urllib.error.URLError("connection refused")

    with pytest.raises(AccountUnreachable) as caught:
        _signed_in_over(refuse).me()
    assert "unreachable" in str(caught.value)
    assert isinstance(caught.value.__cause__, urllib.error.URLError)


@pytest.mark.small
def test_a_connect_timeout_is_reported_as_unreachable():
    """A timeout while connecting becomes AccountUnreachable."""
    def stall(request, timeout):
        """Fails the way a socket does when the server never answers."""
        raise TimeoutError("timed out")

    with pytest.raises(AccountUnreachable):
        _signed_in_over(stall).me()


@pytest.mark.small
def test_a_read_timeout_is_reported_as_unreachable():
    """A timeout while reading the answer becomes AccountUnreachable."""
    class Stalled:
        """An open response whose body never arrives."""

        status = 200

        def __enter__(self):
            """Returns the response itself, as urlopen's does."""
            return self

        def __exit__(self, *exc) -> None:
            """Closes nothing."""

        def read(self) -> bytes:
            """Fails the way a socket read does when the server goes quiet."""
            raise TimeoutError("The read operation timed out")

    with pytest.raises(AccountUnreachable) as caught:
        _signed_in_over(lambda request, timeout: Stalled()).me()
    assert isinstance(caught.value.__cause__, TimeoutError)


class FakeIdState:
    """What the fake Sushi Account remembers between two requests."""

    def __init__(self) -> None:
        """Start with a grant nobody has approved yet and one licensed release."""
        self.approved = False
        self.denied = False
        self.expired = False
        self.slow_down_once = False
        self.polls = 0
        self.refreshes = 0
        self.refresh_ok = True
        self.bearers: list[str] = []
        self.licenses = [{"product": "sushiengine", "holder": "account",
                          "expires_at": "2027-03-01"},
                         {"product": "sushiai", "holder": "org", "expires_at": None}]
        self.products = {"sushiengine"}
        self.licensed = {"sushiengine"}
        self.licence_token = "licence-jwt"
        self.release_version = "1.4.2"      # None: the product has no release
        self.release_blob = b""             # what /download/<name> serves
        self.release_sha256: str | None = None   # None: the blob's own digest
        self.release_size: int | None = None     # None: the blob's own length
        self.rate_limited = False
        self.resolved: list[dict] = []      # every /api/releases/resolve body


def _handler_for(state: FakeIdState):
    """Build a request handler answering the six endpoints out of *state*."""

    class Handler(BaseHTTPRequestHandler):
        """The six routes of contract/sushi-account.md, served from memory."""

        def log_message(self, fmt, *args):
            """Say nothing; the assertions are the test's output, not an access log."""

        def _reply(self, status: int, body: dict) -> None:
            """Write *body* as JSON under the given status."""
            blob = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)

        def _body(self) -> dict:
            """Read and parse the request body."""
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        def _bearer(self) -> bool:
            """Record the Authorization header and report whether it carries a token."""
            bearer = self.headers.get("Authorization", "")
            state.bearers.append(bearer)
            return bearer.startswith("Bearer ")

        def _licence_token(self, body: dict) -> None:
            """Answer the licence-token endpoint for the product *body* names."""
            product = body.get("product")
            if product not in state.products:
                self._reply(404, {"error": "unknown_product"})
            elif product not in state.licensed:
                self._reply(403, {"error": "no_licence"})
            else:
                self._reply(200, {"licence_token": state.licence_token,
                                  "expires_at": "2026-10-05T00:00:00Z"})

        def _resolve_release(self, body: dict) -> None:
            """Answer the release endpoint, pointing its url at this same server."""
            state.resolved.append(body)
            product = body.get("product")
            if state.rate_limited:
                self._reply(429, {"error": "rate_limited"})
            elif product not in state.products:
                self._reply(404, {"error": "unknown_product"})
            elif product not in state.licensed:
                self._reply(403, {"error": "no_licence"})
            elif state.release_version is None:
                self._reply(404, {"error": "no_release"})
            else:
                digest = hashlib.sha256(state.release_blob).hexdigest()
                self._reply(200, {
                    "version": state.release_version,
                    "platform": body.get("platform"),
                    "url": f"http://{self.headers.get('Host')}/download/{product}.zip",
                    "sha256": state.release_sha256 or digest,
                    "size": (len(state.release_blob) if state.release_size is None
                             else state.release_size),
                    "expires_at": "2026-09-05T00:10:00Z"})

        def do_POST(self):
            """Answer the device, refresh, licence-token and release endpoints."""
            body = self._body()
            if self.path in ("/api/licenses/token", "/api/releases/resolve"):
                if not self._bearer():
                    self._reply(401, {"error": "unauthorized"})
                elif self.path == "/api/licenses/token":
                    self._licence_token(body)
                else:
                    self._resolve_release(body)
            elif self.path == "/api/device/code":
                self._reply(200, {"device_code": "dev-1", "user_code": "WXYZ-1234",
                                  "verification_uri": "http://127.0.0.1/activate",
                                  "expires_in": 600, "interval": 1})
            elif self.path == "/api/device/token":
                state.polls += 1
                if state.denied:
                    self._reply(400, {"error": "access_denied"})
                elif state.expired:
                    self._reply(400, {"error": "expired_token"})
                elif state.slow_down_once and state.polls == 1:
                    self._reply(400, {"error": "slow_down"})
                elif state.approved:
                    self._reply(200, {"access_token": "access-1",
                                      "refresh_token": "refresh-1", "expires_in": 3600})
                else:
                    self._reply(400, {"error": "authorization_pending"})
            elif self.path == "/api/token/refresh":
                state.refreshes += 1
                if state.refresh_ok and body.get("refresh_token"):
                    self._reply(200, {"access_token": "access-2", "expires_in": 3600})
                else:
                    self._reply(401, {"error": "invalid_grant"})
            else:
                self._reply(404, {})

        def do_GET(self):
            """Answer the account endpoint, and serve the release the resolver named."""
            if self.path.startswith("/download/"):
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(state.release_blob)))
                self.end_headers()
                self.wfile.write(state.release_blob)
                return
            bearer = self.headers.get("Authorization", "")
            state.bearers.append(bearer)
            if self.path != "/api/me" or not bearer.startswith("Bearer "):
                self._reply(401, {})
                return
            self._reply(200, {"account_id": "acc-1", "email": "dev@sushisystems.io",
                              "licenses": state.licenses})

    return Handler


@pytest.fixture
def fake_id():
    """Serve the four endpoints from a thread on 127.0.0.1, and stop it afterwards."""
    state = FakeIdState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(state))
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01},
                              daemon=True)
    thread.start()
    try:
        yield SimpleNamespace(url=f"http://127.0.0.1:{server.server_address[1]}", state=state)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.medium
def test_start_device_login_returns_the_code_and_the_uri(fake_id):
    code = SushiAccount(fake_id.url, MemoryStore()).start_device_login()
    assert code.user_code == "WXYZ-1234"
    assert code.verification_uri == "http://127.0.0.1/activate"
    assert code.interval == 1


def _approving(fake_id, sleeps: list[float] | None = None):
    """Return a sleep that records its wait and approves the grant on the server."""
    def sleep(seconds):
        """Approve the grant, as the person does while the client waits."""
        if sleeps is not None:
            sleeps.append(seconds)
        fake_id.state.approved = True
    return sleep


@pytest.mark.medium
def test_wait_for_token_returns_the_tokens_with_an_expiry(fake_id):
    """The tokens carry what the server granted and expire expires_in seconds from now."""
    client = SushiAccount(fake_id.url, MemoryStore(), sleep=_approving(fake_id),
                          now=lambda: 100.0)
    tokens = client.wait_for_token(client.start_device_login())
    assert tokens == Tokens("access-1", "refresh-1", 100.0 + 3600)


@pytest.mark.medium
def test_wait_for_token_stores_the_tokens_it_returns(fake_id):
    """The approved grant is kept in the credential store."""
    store = MemoryStore()
    client = SushiAccount(fake_id.url, store, sleep=_approving(fake_id), now=lambda: 100.0)
    tokens = client.wait_for_token(client.start_device_login())
    assert store.load() == tokens


@pytest.mark.medium
def test_wait_for_token_waits_the_granted_interval_between_polls(fake_id):
    """One pending answer costs one sleep of the interval the server granted."""
    sleeps: list[float] = []
    client = SushiAccount(fake_id.url, MemoryStore(), sleep=_approving(fake_id, sleeps))
    client.wait_for_token(client.start_device_login())
    assert sleeps == [1]


@pytest.mark.medium
def test_slow_down_doubles_the_interval_once(fake_id):
    fake_id.state.slow_down_once = True
    sleeps: list[float] = []

    def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 2:
            fake_id.state.approved = True

    client = SushiAccount(fake_id.url, MemoryStore(), sleep=sleep)
    client.wait_for_token(client.start_device_login())
    assert sleeps == [2, 2]


@pytest.mark.medium
def test_wait_for_token_reports_each_poll(fake_id):
    polls: list[int] = []
    client = SushiAccount(fake_id.url, MemoryStore(),
                     sleep=lambda seconds: setattr(fake_id.state, "approved", True))
    client.wait_for_token(client.start_device_login(), on_poll=polls.append)
    assert polls == [1, 2]


@pytest.mark.parametrize("grant_error, ending", [("denied", LoginDenied),
                                                   ("expired", LoginExpired)])
@pytest.mark.medium
def test_a_terminal_grant_error_ends_the_login(fake_id, grant_error, ending):
    """A refused or expired grant raises its own error and stops the polling."""
    setattr(fake_id.state, grant_error, True)
    client = SushiAccount(fake_id.url, MemoryStore(), sleep=lambda seconds: None)
    with pytest.raises(ending):
        client.wait_for_token(client.start_device_login())


@pytest.mark.parametrize("now", [900.0, 969.0])
@pytest.mark.small
def test_access_token_is_returned_untouched_while_it_lives(now):
    """A token that outlives the margin is returned and no request is made."""
    http = ScriptedHttp()
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    assert SushiAccount("http://account.invalid", store, http=http,
                        now=lambda: now).access_token() == "access-1"
    assert http.requests == []


@pytest.mark.parametrize("now", [970.0, 980.0])
@pytest.mark.small
def test_access_token_refreshes_inside_the_thirty_second_margin(now):
    """From exactly 30 s before expiry the token is refreshed and the new one stored."""
    http = ScriptedHttp(Reply(200, {"access_token": "access-2", "expires_in": 3600}))
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    client = SushiAccount("http://account.invalid", store, http=http, now=lambda: now)
    assert client.access_token() == "access-2"
    assert len(http.requests) == 1
    assert store.load() == Tokens("access-2", "refresh-1", now + 3600)


@pytest.mark.small
def test_a_refused_refresh_clears_the_store():
    """A refresh token the server rejects ends the session."""
    http = ScriptedHttp(Reply(401, {"error": "invalid_grant"}))
    store = MemoryStore(Tokens("access-1", "", 1000.0))
    client = SushiAccount("http://account.invalid", store, http=http, now=lambda: 980.0)
    assert client.access_token() is None
    assert store.load() is None


@pytest.mark.small
def test_me_is_none_with_an_empty_store():
    """Nobody signed in gives no account and sends no request."""
    http = ScriptedHttp()
    assert SushiAccount("http://account.invalid", MemoryStore(), http=http).me() is None
    assert http.requests == []


@pytest.mark.medium
def test_me_reads_the_account_and_its_licences(fake_id):
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    account = SushiAccount(fake_id.url, store, now=lambda: 900.0).me()
    assert account == Account("acc-1", "dev@sushisystems.io", (
        Licence("sushiengine", "account", "2027-03-01"),
        Licence("sushiai", "org", None)))
    assert fake_id.state.bearers == ["Bearer access-1"]


@pytest.mark.small
def test_logout_forgets_the_session():
    """Logging out empties the credential store."""
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    SushiAccount("http://account.invalid", store).logout()
    assert store.load() is None


def _signed_in(fake_id) -> SushiAccount:
    """Build a client whose store already holds a live session."""
    return SushiAccount(fake_id.url, MemoryStore(Tokens("access-1", "refresh-1", 1e12)),
                   now=lambda: 0.0)


@pytest.mark.medium
def test_licence_token_is_issued_for_a_licensed_product(fake_id):
    token = _signed_in(fake_id).licence_token("sushiengine")
    assert token == LicenceToken("licence-jwt", "2026-10-05T00:00:00Z")
    assert fake_id.state.bearers[-1] == "Bearer access-1"


@pytest.mark.medium
def test_licence_token_refuses_an_unlicensed_product(fake_id):
    fake_id.state.licensed = set()
    with pytest.raises(NoLicence):
        _signed_in(fake_id).licence_token("sushiengine")


@pytest.mark.medium
def test_resolve_release_returns_the_url_the_hash_and_the_size(fake_id):
    fake_id.state.release_blob = b"a release"
    info = _signed_in(fake_id).resolve_release("sushiengine", "windows-x64")
    assert isinstance(info, ReleaseInfo)
    assert info.version == "1.4.2" and info.platform == "windows-x64"
    assert info.url.endswith("/download/sushiengine.zip")
    assert info.sha256 == hashlib.sha256(b"a release").hexdigest()
    assert info.size == len(b"a release")
    assert fake_id.state.resolved == [{"product": "sushiengine",
                                       "platform": "windows-x64"}]


@pytest.mark.medium
def test_resolve_release_carries_the_version_when_one_is_asked_for(fake_id):
    _signed_in(fake_id).resolve_release("sushiengine", "linux-x64", version="1.0.0")
    assert fake_id.state.resolved[-1]["version"] == "1.0.0"


@pytest.mark.medium
def test_resolve_release_reports_that_there_is_no_release(fake_id):
    fake_id.state.release_version = None
    with pytest.raises(NoRelease):
        _signed_in(fake_id).resolve_release("sushiengine", "windows-x64")


@pytest.mark.medium
def test_resolve_release_reports_an_unknown_product(fake_id):
    with pytest.raises(UnknownProduct):
        _signed_in(fake_id).resolve_release("sushidsp", "windows-x64")


@pytest.mark.small
def test_a_licence_token_without_a_session_is_refused_before_the_request():
    """No session raises before any request leaves."""
    http = ScriptedHttp()
    with pytest.raises(SushiAccountError):
        SushiAccount("http://account.invalid", MemoryStore(), http=http).licence_token(
            "sushiengine")
    assert http.requests == []


ACCOUNT = Account("acc-1", "dev@sushisystems.io", (
    Licence("sushiengine", "account", "2027-03-01"),
    Licence("sushiai", "org", None)))


@pytest.mark.small
def test_login_stores_the_session():
    """An approved login leaves the account signed in."""
    account = InMemoryAccount(ACCOUNT)
    session.login(open_browser=lambda uri: True, ports=memory_ports(account=account))
    assert account.signed_in is True


@pytest.mark.small
def test_login_returns_the_email_and_opens_the_verification_uri():
    """The outcome carries the email, and the browser is sent to the granted uri."""
    opened: list[str] = []
    outcome = session.login(open_browser=opened.append,
                            ports=memory_ports(account=InMemoryAccount(ACCOUNT)))
    assert outcome == session.Outcome(0, {"email": "dev@sushisystems.io"})
    assert opened == [DEVICE_CODE.verification_uri]


@pytest.mark.small
def test_login_reports_a_refused_grant():
    """A grant the person refused gives exit 1 and one error line."""
    out = RecordingConsole()
    account = InMemoryAccount(ACCOUNT, refusal=LoginDenied("refused in the browser"))
    outcome = session.login(open_browser=lambda uri: True,
                            ports=memory_ports(console=out, account=account))
    assert (outcome, out.texts("error")) == (session.Outcome(1, {}), ["refused in the browser"])


@pytest.mark.small
def test_whoami_reports_that_nobody_is_signed_in():
    """Nobody signed in gives exit 1 and a warning."""
    out = RecordingConsole()
    outcome = session.whoami(ports=memory_ports(console=out, account=InMemoryAccount(ACCOUNT)))
    assert (outcome, out.has_call("warn")) == (session.Outcome(1, {}), True)


@pytest.mark.small
def test_whoami_carries_the_account_as_its_payload():
    """The payload is the account id, the email and every licence."""
    outcome = session.whoami(
        ports=memory_ports(account=InMemoryAccount(ACCOUNT, signed_in=True)))
    assert outcome == session.Outcome(0, {
        "account_id": "acc-1", "email": "dev@sushisystems.io",
        "licenses": [{"product": "sushiengine", "holder": "account", "expires_at": "2027-03-01"},
                     {"product": "sushiai", "holder": "org", "expires_at": None}]})


@pytest.mark.small
def test_license_carries_the_licences_alone():
    """The payload holds the licences and nothing of the account."""
    code, payload = session.license(
        ports=memory_ports(account=InMemoryAccount(ACCOUNT, signed_in=True)))
    assert code == 0 and list(payload) == ["licenses"]
    assert [item["product"] for item in payload["licenses"]] == ["sushiengine", "sushiai"]


@pytest.mark.small
def test_license_says_so_when_the_account_holds_none():
    """An account without licences gives an empty list and an information line."""
    out = RecordingConsole()
    account = InMemoryAccount(Account("acc-1", "dev@sushisystems.io", ()), signed_in=True)
    outcome = session.license(ports=memory_ports(console=out, account=account))
    assert (outcome, out.texts("info")) == (session.Outcome(0, {"licenses": []}),
                                            ["No licences on this account."])


@pytest.mark.parametrize("command", [session.logout, session.whoami, session.license])
@pytest.mark.medium
def test_an_account_command_reports_a_failing_credential_store(broken_backend, command):
    """logout, whoami and license print one error line and return code 1."""
    out = RecordingConsole()
    client = SushiAccount("http://account.invalid", KeyringStore())
    outcome = command(ports=memory_ports(console=out, account=client))
    assert outcome == session.Outcome(1, {})
    assert len(out.texts("error")) == 1 and "credential store" in out.texts("error")[0]


@pytest.mark.medium
def test_login_reports_a_session_it_could_not_store(fake_id, broken_backend):
    """A grant whose tokens cannot be stored ends login in one error line and code 1."""
    out = RecordingConsole()
    client = SushiAccount(fake_id.url, KeyringStore(), sleep=_approving(fake_id))
    outcome = session.login(open_browser=lambda uri: True,
                            ports=memory_ports(console=out, account=client))
    assert outcome == session.Outcome(1, {})
    assert len(out.texts("error")) == 1 and "credential store" in out.texts("error")[0]


@pytest.mark.small
def test_whoami_reports_an_unreachable_server():
    """whoami prints one error line when Sushi Account does not answer."""
    def refuse(request, timeout):
        """Fail the way urlopen does when nothing listens."""
        raise urllib.error.URLError("connection refused")

    out = RecordingConsole()
    client = _signed_in_over(refuse)
    outcome = session.whoami(ports=memory_ports(console=out, account=client))
    assert outcome == session.Outcome(1, {})
    assert len(out.texts("error")) == 1 and "unreachable" in out.texts("error")[0]
