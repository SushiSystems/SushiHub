"""Sushi ID: where the base URL comes from, the token store, the client, the commands."""

from __future__ import annotations

import keyring
import keyring.backend
import keyring.errors
import pytest

from sushistack.config import DEFAULT_IDENTITY_URL, identity_url
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
    (tmp_path / "cli").mkdir()
    (tmp_path / "cli" / "config.toml").write_text(
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
