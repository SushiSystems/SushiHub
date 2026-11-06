# test_status_payload.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The payload `hub status` ends with, checked against its schema and its readers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

from sushihub.services import status_report
from sushihub.services.hub_install import ALIAS_MARKER
from sushihub.services.identity import SushiAccount
from sushihub.services.catalog import CATALOG
from sushihub.services.token_store import MemoryStore

from .support.fake_account_server import signed_in
from .support.release_files import binary_install
from .support.workspace_files import workspace_at

pytestmark = pytest.mark.medium

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


def _offline_rows(tmp_path) -> dict[str, dict]:
    """Return the offline status rows of the workspace under *tmp_path*, keyed by module name."""
    payload = status_report.build_status(home=tmp_path, client_factory=_never_called).payload
    return {row["name"]: row for row in payload["modules"]}


def _checked_row(report, name: str) -> dict:
    """Return the row of module *name* from a status *report*."""
    return {row["name"]: row for row in report.payload["modules"]}[name]


def test_the_offline_payload_matches_the_schema(tmp_path, monkeypatch):
    root = workspace_at(tmp_path / "ws", monkeypatch)
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
    root = workspace_at(tmp_path / "ws", monkeypatch)
    _real_checkout(root / "sushiruntime")

    assert list(_offline_rows(tmp_path)) == list(CATALOG.names())


def test_a_checkout_row_carries_its_branch(tmp_path, monkeypatch):
    root = workspace_at(tmp_path / "ws", monkeypatch)
    _real_checkout(root / "sushiruntime")

    source = _offline_rows(tmp_path)["sushiruntime"]["source"]

    assert source["branch"] == "main"
    assert source["ahead"] is None


def test_a_checkout_row_carries_no_binary(tmp_path, monkeypatch):
    root = workspace_at(tmp_path / "ws", monkeypatch)
    _real_checkout(root / "sushiruntime")

    assert _offline_rows(tmp_path)["sushiruntime"]["binary"] is None


def test_a_module_that_is_absent_carries_no_source(tmp_path, monkeypatch):
    root = workspace_at(tmp_path / "ws", monkeypatch)
    _real_checkout(root / "sushiruntime")

    assert _offline_rows(tmp_path)["sushiai"]["source"] is None


def test_a_binary_row_carries_its_platform_and_licence_expiry(tmp_path, monkeypatch):
    root = workspace_at(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine")

    row = _offline_rows(tmp_path)["sushiengine"]

    assert row["binary"] == {"platform": "windows-x64", "licence_expires_at": None}
    assert row["source"] is None
    assert row["latest_version"] is None


def test_the_hub_block_reports_the_alias_under_the_given_home(tmp_path, monkeypatch):
    workspace_at(tmp_path / "ws", monkeypatch)
    (tmp_path / ".bashrc").write_text(f"{ALIAS_MARKER}\nalias sh='hub'\n", encoding="utf-8")

    hub = status_report.build_status(home=tmp_path, client_factory=_never_called).payload["hub"]

    assert hub["alias"]["name"] == "sh"
    assert hub["latest_version"] is None


def test_checking_updates_fills_the_latest_release(tmp_path, monkeypatch, fake_id):
    root = workspace_at(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine", version="1.4.0")

    report = status_report.build_status(True, home=tmp_path,
                                        client_factory=lambda: signed_in(fake_id))

    jsonschema.validate(report.payload, _SCHEMA)
    assert report.payload["checked_updates"] is True
    assert _checked_row(report, "sushiengine")["latest_version"] == "1.4.2"
    assert report.warnings == []


def _refused_report(tmp_path, monkeypatch, fake_id):
    """Check updates for one binary install with a client that holds no session."""
    root = workspace_at(tmp_path / "ws", monkeypatch)
    binary_install(root / "sushiengine")
    return status_report.build_status(
        True, home=tmp_path, client_factory=lambda: SushiAccount(fake_id.url, MemoryStore()))


def test_a_refused_check_leaves_the_latest_release_null(tmp_path, monkeypatch, fake_id):
    report = _refused_report(tmp_path, monkeypatch, fake_id)

    assert _checked_row(report, "sushiengine")["latest_version"] is None


def test_a_refused_check_leaves_one_warning_naming_the_module(tmp_path, monkeypatch, fake_id):
    report = _refused_report(tmp_path, monkeypatch, fake_id)

    assert len(report.warnings) == 1
    assert report.warnings[0].startswith("sushiengine: ")
