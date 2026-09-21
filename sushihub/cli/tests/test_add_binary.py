"""Choosing between the source and the binary, and what the binary path writes."""

from __future__ import annotations

import base64
import json

import pytest

from sushistack.services import binary, git_ops, licence_file, links, modules, pipx, session
from sushistack.services.identity import SushiAccount
from sushistack.services.licence_file import LICENCE_FILE
from sushistack.services.presence import RELEASE_MANIFEST
from sushistack.services.token_store import MemoryStore, Tokens

from .test_identity import fake_id  # noqa: F401  the fake Sushi Account server fixture
from .test_presence import Recorder
from .test_releases import release_members, zip_bytes


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Point `hub add` at a throwaway root where nothing is cloned or linked."""
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(links, "registered", lambda: {})
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    monkeypatch.setattr(git_ops, "run",
                        lambda args, cwd: pytest.fail(f"git ran: {args}"))
    monkeypatch.setattr(git_ops, "source_reachable",
                        lambda repo: pytest.fail(f"the remote was asked about: {repo}"))
    monkeypatch.setattr(pipx, "installed", lambda name: None)
    return tmp_path


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line `hub add` and `hub update` print.

    The binary install policy prints through its own `console` reference
    (:mod:`sushistack.services.binary`), so both it and `modules` are patched
    to the same spy; otherwise a message ``binary`` prints would go unseen.
    """
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    monkeypatch.setattr(binary, "console", spy)
    return spy


def sign_in(fake_id, monkeypatch, tokens=Tokens("access-1", "refresh-1", 1e12)):
    """Point every Sushi Account call in `hub` at the fake server with *tokens* stored."""
    client = SushiAccount(fake_id.url, MemoryStore(tokens), now=lambda: 0.0)
    monkeypatch.setattr(session, "client", lambda: client)
    return client


def reachable(monkeypatch, answer: bool) -> None:
    """Say whether this machine's Git identity reaches a module's repository."""
    monkeypatch.setattr(git_ops, "source_reachable", lambda repo: answer)


def serve_release(fake_id, version: str = "1.4.2") -> None:
    """Have the fake server offer *version* of sushiengine as a zip."""
    fake_id.state.release_version = version
    fake_id.state.release_blob = zip_bytes(release_members(version=version))


def installed_version(root) -> str:
    """Read the version the install at *root* reports."""
    return json.loads((root / RELEASE_MANIFEST).read_text(encoding="utf-8"))["version"]


def jwt(expiry: int) -> str:
    """Build a token whose payload names *expiry* as its ``exp`` claim."""
    def segment(payload: dict) -> str:
        blob = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8"))
        return blob.decode("ascii").rstrip("=")
    return f"{segment({'alg': 'EdDSA'})}.{segment({'exp': expiry})}.signature"


def test_add_clones_sushiengine_when_its_repository_answers(
        workspace, recorder, monkeypatch):
    reachable(monkeypatch, True)
    cloned = []
    monkeypatch.setattr(git_ops, "run",
                        lambda args, cwd: cloned.append(args[0]) or 0)
    rc = modules.add(["sushiengine"], provision=lambda dry_run: 0)
    assert rc == 0 and cloned == ["clone"]


def test_add_installs_the_binary_when_the_repository_is_out_of_reach(
        workspace, recorder, monkeypatch, fake_id):
    reachable(monkeypatch, False)
    sign_in(fake_id, monkeypatch)
    serve_release(fake_id)
    provisioned = []
    rc = modules.add(["sushiengine"], provision=lambda dry_run: provisioned.append(dry_run))
    assert rc == 0
    assert installed_version(workspace / "sushiengine") == "1.4.2"
    assert (workspace / "sushiengine" / LICENCE_FILE).read_text(
        encoding="utf-8") == "licence-jwt"
    assert provisioned == [], "a release brings its own dependencies"
    assert recorder.said("installed binary 1.4.2")


def test_add_binary_installs_it_even_when_the_source_is_in_reach(
        workspace, recorder, monkeypatch, fake_id):
    reachable(monkeypatch, True)
    sign_in(fake_id, monkeypatch)
    serve_release(fake_id)
    assert modules.add(["sushiengine"], binary=True, provision=lambda dry_run: 0) == 0
    assert installed_version(workspace / "sushiengine") == "1.4.2"


def test_add_names_both_ways_in_when_neither_is_open(
        workspace, recorder, monkeypatch, fake_id):
    reachable(monkeypatch, False)
    sign_in(fake_id, monkeypatch, tokens=None)
    assert modules.add(["sushiengine"], provision=lambda dry_run: 0) == 1
    assert recorder.said("a Git identity with access")
    assert recorder.said("`hub login`")
    assert not (workspace / "sushiengine").exists()


def test_add_binary_without_a_session_asks_for_the_login_alone(
        workspace, recorder, monkeypatch, fake_id):
    sign_in(fake_id, monkeypatch, tokens=None)
    assert modules.add(["sushiengine"], binary=True, provision=lambda dry_run: 0) == 1
    assert recorder.said("Run `hub login` first.")
    assert not recorder.said("a Git identity with access")


def test_add_binary_refuses_a_module_that_is_not_sold(workspace, recorder, monkeypatch):
    assert modules.add(["sushiruntime"], binary=True, provision=lambda dry_run: 0) == 1
    assert recorder.said("only sushiengine is sold as a binary")
    assert not (workspace / "sushiruntime").exists()


def test_add_reports_a_licence_the_account_does_not_hold(
        workspace, recorder, monkeypatch, fake_id):
    reachable(monkeypatch, False)
    sign_in(fake_id, monkeypatch)
    fake_id.state.licensed = set()
    assert modules.add(["sushiengine"], provision=lambda dry_run: 0) == 1
    assert recorder.said("no live licence")
    assert not (workspace / "sushiengine").exists()


def test_add_refuses_a_download_whose_hash_does_not_match(
        workspace, recorder, monkeypatch, fake_id):
    reachable(monkeypatch, False)
    sign_in(fake_id, monkeypatch)
    serve_release(fake_id)
    fake_id.state.release_sha256 = "0" * 64
    assert modules.add(["sushiengine"], provision=lambda dry_run: 0) == 1
    assert recorder.said("sha256")
    assert not (workspace / "sushiengine").exists()


def test_add_dry_run_says_it_would_install_the_release(
        workspace, recorder, monkeypatch, fake_id):
    reachable(monkeypatch, False)
    sign_in(fake_id, monkeypatch)
    assert modules.add(["sushiengine"], dry_run=True, provision=lambda dry_run: 0) == 0
    assert recorder.said("would install its release")
    assert not (workspace / "sushiengine").exists()


def test_add_leaves_an_installed_binary_alone(workspace, recorder, monkeypatch, fake_id):
    root = workspace / "sushiengine"
    root.mkdir()
    (root / RELEASE_MANIFEST).write_text(
        json.dumps(dict(product="sushiengine", version="1.0.0", platform="windows-x64")),
        encoding="utf-8")
    assert modules.add(["sushiengine"], provision=lambda dry_run: 0) == 0
    assert installed_version(root) == "1.0.0"


def test_update_says_a_binary_install_is_already_the_latest(
        workspace, recorder, monkeypatch, fake_id):
    root = workspace / "sushiengine"
    root.mkdir()
    (root / RELEASE_MANIFEST).write_text(
        json.dumps(dict(product="sushiengine", version="1.4.2", platform="windows-x64")),
        encoding="utf-8")
    sign_in(fake_id, monkeypatch)
    serve_release(fake_id)
    monkeypatch.setattr(binary.releases, "host_platform", lambda: "windows-x64")
    assert modules.update(["sushiengine"]) == 0
    assert recorder.said("binary 1.4.2 is the latest release.")
    assert not (root / LICENCE_FILE).exists()


def test_update_downloads_a_newer_release_and_writes_the_licence_again(
        workspace, recorder, monkeypatch, fake_id):
    root = workspace / "sushiengine"
    root.mkdir()
    (root / RELEASE_MANIFEST).write_text(
        json.dumps(dict(product="sushiengine", version="1.4.2", platform="windows-x64")),
        encoding="utf-8")
    sign_in(fake_id, monkeypatch)
    serve_release(fake_id, version="1.5.0")
    monkeypatch.setattr(binary.releases, "host_platform", lambda: "windows-x64")
    assert modules.update(["sushiengine"]) == 0
    assert installed_version(root) == "1.5.0"
    assert (root / LICENCE_FILE).read_text(encoding="utf-8") == "licence-jwt"


def test_update_asks_for_a_login_before_refreshing_a_binary_install(
        workspace, recorder, monkeypatch, fake_id):
    root = workspace / "sushiengine"
    root.mkdir()
    (root / RELEASE_MANIFEST).write_text(
        json.dumps(dict(product="sushiengine", version="1.4.2", platform="windows-x64")),
        encoding="utf-8")
    sign_in(fake_id, monkeypatch, tokens=None)
    assert modules.update(["sushiengine"]) == 1
    assert recorder.said("Run `hub login` first.")


def test_write_licence_returns_the_expiry_and_writes_the_bare_token(
        tmp_path, monkeypatch, fake_id):
    client = sign_in(fake_id, monkeypatch)
    expires_at = licence_file.write_licence(tmp_path, client, "sushiengine")
    assert expires_at == "2026-10-05T00:00:00Z"
    assert (tmp_path / LICENCE_FILE).read_text(encoding="utf-8") == "licence-jwt"


def test_read_licence_expiry_reads_the_exp_claim(tmp_path):
    (tmp_path / LICENCE_FILE).write_text(jwt(1790000000), encoding="utf-8")
    assert licence_file.read_licence_expiry(tmp_path) == "2026-09-21T14:13:20+00:00"


def test_read_licence_expiry_is_none_without_a_file(tmp_path):
    assert licence_file.read_licence_expiry(tmp_path) is None


def test_read_licence_expiry_is_none_when_the_token_is_not_a_jwt(tmp_path):
    (tmp_path / LICENCE_FILE).write_text("not a token", encoding="utf-8")
    assert licence_file.read_licence_expiry(tmp_path) is None


def test_read_licence_expiry_is_none_when_the_payload_names_no_expiry(tmp_path):
    (tmp_path / LICENCE_FILE).write_text("header.eyJzdWIiOiAiYSJ9.sig", encoding="utf-8")
    assert licence_file.read_licence_expiry(tmp_path) is None
