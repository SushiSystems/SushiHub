"""Sushi ID: where the base URL comes from, the token store, the client, the commands."""

from __future__ import annotations

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import keyring
import keyring.backend
import keyring.errors
import pytest

from sushicore.workspace import WORKSPACE_CLI_DIR
from sushistack.config import DEFAULT_IDENTITY_URL, identity_url
from sushistack.services import session
from sushistack.services.identity import (
    Account,
    Licence,
    LicenceToken,
    LoginDenied,
    LoginExpired,
    NoLicence,
    NoRelease,
    ReleaseInfo,
    SushiId,
    SushiIdError,
    UnknownProduct,
)
from sushistack.services.token_store import (
    KEYRING_SERVICE,
    KEYRING_USERNAME,
    KeyringStore,
    MemoryStore,
    Tokens,
)


def _workspace_with_identity(tmp_path, url: str):
    """Write a throwaway workspace whose config.toml pins the Sushi ID url."""
    (tmp_path / ".sushistack").write_text("marker\n", encoding="utf-8")
    (tmp_path / WORKSPACE_CLI_DIR).mkdir(parents=True)
    (tmp_path / WORKSPACE_CLI_DIR / "config.toml").write_text(
        f'[identity]\nurl = "{url}"\n', encoding="utf-8")
    return tmp_path


def test_identity_url_prefers_env(monkeypatch, tmp_path):
    _workspace_with_identity(tmp_path, "http://127.0.0.1:9001")
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.setenv("SUSHI_ID_URL", "http://127.0.0.1:8123/")
    assert identity_url() == "http://127.0.0.1:8123"


def test_identity_url_reads_the_config_key(monkeypatch, tmp_path):
    _workspace_with_identity(tmp_path, "http://127.0.0.1:9001/")
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.delenv("SUSHI_ID_URL", raising=False)
    assert identity_url() == "http://127.0.0.1:9001"


def test_identity_url_defaults_when_no_workspace_and_no_key(monkeypatch, tmp_path):
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    monkeypatch.delenv("SUSHI_ID_URL", raising=False)
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


def test_memory_store_round_trips_and_clears():
    store = MemoryStore()
    assert store.load() is None
    tokens = Tokens(access_token="a", refresh_token="r", expires_at=1234.5)
    store.save(tokens)
    assert store.load() == tokens
    store.clear()
    assert store.load() is None


def test_keyring_store_round_trips_through_the_backend(backend):
    store = KeyringStore()
    assert store.load() is None
    store.save(Tokens(access_token="a", refresh_token="r", expires_at=99.0))
    assert backend.passwords[(KEYRING_SERVICE, KEYRING_USERNAME)]
    assert store.load() == Tokens(access_token="a", refresh_token="r", expires_at=99.0)
    store.clear()
    assert store.load() is None


def test_keyring_store_reads_a_corrupt_entry_as_absent(backend):
    backend.set_password(KEYRING_SERVICE, KEYRING_USERNAME, "not json")
    assert KeyringStore().load() is None


def test_keyring_store_clear_is_quiet_when_nothing_is_stored(backend):
    KeyringStore().clear()
    assert backend.passwords == {}


class FakeIdState:
    """What the fake Sushi ID remembers between two requests."""

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
        """The six routes of sushihub/contract/sushi-id.md, served from memory."""

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


def test_start_device_login_returns_the_code_and_the_uri(fake_id):
    code = SushiId(fake_id.url, MemoryStore()).start_device_login()
    assert code.user_code == "WXYZ-1234"
    assert code.verification_uri == "http://127.0.0.1/activate"
    assert code.interval == 1


def test_wait_for_token_polls_until_the_grant_is_approved(fake_id):
    store = MemoryStore()
    sleeps: list[float] = []

    def sleep(seconds):
        sleeps.append(seconds)
        fake_id.state.approved = True

    client = SushiId(fake_id.url, store, sleep=sleep, now=lambda: 100.0)
    tokens = client.wait_for_token(client.start_device_login())
    assert tokens.access_token == "access-1" and tokens.refresh_token == "refresh-1"
    assert tokens.expires_at == 100.0 + 3600
    assert store.load() == tokens
    assert sleeps == [1]


def test_slow_down_doubles_the_interval_once(fake_id):
    fake_id.state.slow_down_once = True
    sleeps: list[float] = []

    def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 2:
            fake_id.state.approved = True

    client = SushiId(fake_id.url, MemoryStore(), sleep=sleep)
    client.wait_for_token(client.start_device_login())
    assert sleeps == [2, 2]


def test_wait_for_token_reports_each_poll(fake_id):
    polls: list[int] = []
    client = SushiId(fake_id.url, MemoryStore(),
                     sleep=lambda seconds: setattr(fake_id.state, "approved", True))
    client.wait_for_token(client.start_device_login(), on_poll=polls.append)
    assert polls == [1, 2]


def test_access_denied_ends_the_login(fake_id):
    fake_id.state.denied = True
    client = SushiId(fake_id.url, MemoryStore(), sleep=lambda seconds: None)
    with pytest.raises(LoginDenied):
        client.wait_for_token(client.start_device_login())


def test_expired_token_ends_the_login(fake_id):
    fake_id.state.expired = True
    client = SushiId(fake_id.url, MemoryStore(), sleep=lambda seconds: None)
    with pytest.raises(LoginExpired):
        client.wait_for_token(client.start_device_login())


def test_access_token_is_returned_untouched_while_it_lives(fake_id):
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    client = SushiId(fake_id.url, store, now=lambda: 900.0)
    assert client.access_token() == "access-1"
    assert fake_id.state.refreshes == 0


def test_access_token_refreshes_inside_the_thirty_second_margin(fake_id):
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    client = SushiId(fake_id.url, store, now=lambda: 980.0)
    assert client.access_token() == "access-2"
    assert fake_id.state.refreshes == 1
    assert store.load() == Tokens("access-2", "refresh-1", 980.0 + 3600)


def test_a_refused_refresh_clears_the_store(fake_id):
    fake_id.state.refresh_ok = False
    store = MemoryStore(Tokens("access-1", "", 1000.0))
    client = SushiId(fake_id.url, store, now=lambda: 980.0)
    assert client.access_token() is None
    assert store.load() is None


def test_me_is_none_with_an_empty_store(fake_id):
    assert SushiId(fake_id.url, MemoryStore()).me() is None
    assert fake_id.state.bearers == []


def test_me_reads_the_account_and_its_licences(fake_id):
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    account = SushiId(fake_id.url, store, now=lambda: 900.0).me()
    assert account == Account("acc-1", "dev@sushisystems.io", (
        Licence("sushiengine", "account", "2027-03-01"),
        Licence("sushiai", "org", None)))
    assert fake_id.state.bearers == ["Bearer access-1"]


def test_logout_forgets_the_session(fake_id):
    store = MemoryStore(Tokens("access-1", "refresh-1", 1000.0))
    SushiId(fake_id.url, store).logout()
    assert store.load() is None


def _signed_in(fake_id) -> SushiId:
    """Build a client whose store already holds a live session."""
    return SushiId(fake_id.url, MemoryStore(Tokens("access-1", "refresh-1", 1e12)),
                   now=lambda: 0.0)


def test_licence_token_is_issued_for_a_licensed_product(fake_id):
    token = _signed_in(fake_id).licence_token("sushiengine")
    assert token == LicenceToken("licence-jwt", "2026-10-05T00:00:00Z")
    assert fake_id.state.bearers[-1] == "Bearer access-1"


def test_licence_token_refuses_an_unlicensed_product(fake_id):
    fake_id.state.licensed = set()
    with pytest.raises(NoLicence):
        _signed_in(fake_id).licence_token("sushiengine")


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


def test_resolve_release_carries_the_version_when_one_is_asked_for(fake_id):
    _signed_in(fake_id).resolve_release("sushiengine", "linux-x64", version="1.0.0")
    assert fake_id.state.resolved[-1]["version"] == "1.0.0"


def test_resolve_release_reports_that_there_is_no_release(fake_id):
    fake_id.state.release_version = None
    with pytest.raises(NoRelease):
        _signed_in(fake_id).resolve_release("sushiengine", "windows-x64")


def test_resolve_release_reports_an_unknown_product(fake_id):
    with pytest.raises(UnknownProduct):
        _signed_in(fake_id).resolve_release("sushidsp", "windows-x64")


def test_a_licence_token_without_a_session_is_refused_before_the_request(fake_id):
    with pytest.raises(SushiIdError):
        SushiId(fake_id.url, MemoryStore()).licence_token("sushiengine")
    assert fake_id.state.bearers == []


def _bind(monkeypatch, fake_id, store, **kwargs):
    """Point the four commands at *fake_id* with *store* as their credential store."""
    client = SushiId(fake_id.url, store, **kwargs)
    monkeypatch.setattr(session, "_client", lambda: client)
    return client


def test_login_stores_the_session_and_returns_the_email(fake_id, monkeypatch):
    store = MemoryStore()
    _bind(monkeypatch, fake_id, store,
          sleep=lambda seconds: setattr(fake_id.state, "approved", True))
    opened: list[str] = []
    outcome = session.login(open_browser=opened.append)
    assert outcome == session.Outcome(0, {"email": "dev@sushisystems.io"})
    assert opened == ["http://127.0.0.1/activate"]
    assert store.load().access_token == "access-1"


def test_login_reports_a_refused_grant(fake_id, monkeypatch):
    fake_id.state.denied = True
    _bind(monkeypatch, fake_id, MemoryStore(), sleep=lambda seconds: None)
    assert session.login(open_browser=lambda uri: True) == session.Outcome(1, {})


def test_logout_command_clears_the_store(fake_id, monkeypatch):
    store = MemoryStore(Tokens("access-1", "refresh-1", 1e12))
    _bind(monkeypatch, fake_id, store)
    assert session.logout() == session.Outcome(0, {})
    assert store.load() is None


def test_whoami_reports_that_nobody_is_signed_in(fake_id, monkeypatch):
    _bind(monkeypatch, fake_id, MemoryStore())
    assert session.whoami() == session.Outcome(1, {})


def test_whoami_carries_the_account_as_its_payload(fake_id, monkeypatch):
    _bind(monkeypatch, fake_id, MemoryStore(Tokens("access-1", "refresh-1", 1e12)))
    code, payload = session.whoami()
    assert code == 0
    assert payload["account_id"] == "acc-1" and payload["email"] == "dev@sushisystems.io"
    assert payload["licenses"][0] == {"product": "sushiengine", "holder": "account",
                                      "expires_at": "2027-03-01"}


def test_license_carries_the_licences_alone(fake_id, monkeypatch):
    _bind(monkeypatch, fake_id, MemoryStore(Tokens("access-1", "refresh-1", 1e12)))
    code, payload = session.license()
    assert code == 0 and list(payload) == ["licenses"]
    assert [item["product"] for item in payload["licenses"]] == ["sushiengine", "sushiai"]


def test_license_says_so_when_the_account_holds_none(fake_id, monkeypatch):
    fake_id.state.licenses = []
    _bind(monkeypatch, fake_id, MemoryStore(Tokens("access-1", "refresh-1", 1e12)))
    assert session.license() == session.Outcome(0, {"licenses": []})
