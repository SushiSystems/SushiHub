"""The payload `hub status` ends with, checked against its schema and its readers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

from sushistack.services import status_report
from sushistack.services.hub_install import ALIAS_MARKER
from sushistack.services.identity import SushiAccount
from sushistack.services.token_store import MemoryStore

from .test_identity import fake_id  # noqa: F401  the fake Sushi Account server fixture
from .test_identity import _signed_in
from .test_presence import binary_install, workspace

_SCHEMA = json.loads((Path(__file__).resolve().parents[2] / "contract" / "status.schema.json")
                     .read_text(encoding="utf-8"))


def _git(cwd: Path, *args: str) -> None:
    """Run git in *cwd* with a fixed identity."""
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
                    "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True)


def _real_checkout(path: Path) -> None:
    """Make *path* a git repository with one commit on main."""
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    (path / "README.md").write_text("x", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "first")


def _never_called() -> SushiAccount:
    """Fail the test: the offline form must not build a Sushi Account client."""
    pytest.fail("the offline status built a Sushi Account client")


def test_the_offline_payload_matches_the_schema(tmp_path, monkeypatch):
    root = workspace(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine")
    _real_checkout(root / "sushiruntime")

    report = status_report.build_status(home=tmp_path, client_factory=_never_called)

    jsonschema.validate(report.payload, _SCHEMA)
    assert report.payload["checked_updates"] is False
    assert report.warnings == []


def test_the_module_list_carries_the_catalog_and_nothing_else(tmp_path, monkeypatch):
    """sushicore is a PyPI dependency of `hub`, so it is not one of the rows.

    It had a row until 2026-09-22, reporting `missing` on every machine that took
    sushicore from the index, which is every machine.
    """
    from sushistack.services.catalog import CATALOG

    root = workspace(tmp_path / "ws", monkeypatch)
    _real_checkout(root / "sushiruntime")

    names = [r["name"] for r in status_report.build_status(
        home=tmp_path, client_factory=_never_called).payload["modules"]]

    assert names == list(CATALOG.names())
    assert "sushicore" not in names


def test_a_checkout_row_carries_its_branch_and_no_binary(tmp_path, monkeypatch):
    root = workspace(tmp_path / "ws", monkeypatch)
    _real_checkout(root / "sushiruntime")

    rows = {r["name"]: r for r in status_report.build_status(
        home=tmp_path, client_factory=_never_called).payload["modules"]}

    assert rows["sushiruntime"]["source"]["branch"] == "main"
    assert rows["sushiruntime"]["source"]["ahead"] is None
    assert rows["sushiruntime"]["binary"] is None
    assert rows["sushiai"]["source"] is None


def test_a_binary_row_carries_its_platform_and_licence_expiry(tmp_path, monkeypatch):
    root = workspace(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine")

    row = next(r for r in status_report.build_status(
        home=tmp_path, client_factory=_never_called).payload["modules"]
        if r["name"] == "sushiengine")

    assert row["binary"] == {"platform": "windows-x64", "licence_expires_at": None}
    assert row["source"] is None
    assert row["latest_version"] is None


def test_the_hub_block_reports_the_alias_under_the_given_home(tmp_path, monkeypatch):
    workspace(tmp_path / "ws", monkeypatch)
    (tmp_path / ".bashrc").write_text(f"{ALIAS_MARKER}\nalias sh='hub'\n", encoding="utf-8")

    hub = status_report.build_status(home=tmp_path, client_factory=_never_called).payload["hub"]

    assert hub["alias"]["name"] == "sh"
    assert hub["latest_version"] is None


def test_checking_updates_fills_the_latest_release(tmp_path, monkeypatch, fake_id):
    root = workspace(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine", version="1.4.0")

    report = status_report.build_status(True, home=tmp_path,
                                        client_factory=lambda: _signed_in(fake_id))

    jsonschema.validate(report.payload, _SCHEMA)
    row = next(r for r in report.payload["modules"] if r["name"] == "sushiengine")
    assert report.payload["checked_updates"] is True
    assert row["latest_version"] == "1.4.2"
    assert report.warnings == []


def test_a_refused_check_leaves_null_and_one_warning(tmp_path, monkeypatch, fake_id):
    root = workspace(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine")

    report = status_report.build_status(
        True, home=tmp_path, client_factory=lambda: SushiAccount(fake_id.url, MemoryStore()))

    row = next(r for r in report.payload["modules"] if r["name"] == "sushiengine")
    assert row["latest_version"] is None
    assert len(report.warnings) == 1
    assert report.warnings[0].startswith("sushiengine: ")
