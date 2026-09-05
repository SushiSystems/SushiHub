"""Sushi ID: where the base URL comes from, the token store, the client, the commands."""

from __future__ import annotations

from sushistack.config import DEFAULT_IDENTITY_URL, identity_url


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
