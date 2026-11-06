# test_update_check.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What Sushi Account says the latest release is, and what a refusal turns into."""

from __future__ import annotations

import json
import urllib.error

import pytest

from sushihub.services.identity import SushiAccount
from sushihub.services.token_store import MemoryStore
from sushihub.services.update_check import latest_release

from .support.scripted_http import Reply, ScriptedHttp, signed_in_over

pytestmark = pytest.mark.small

RELEASE = {"version": "1.4.2", "platform": "windows-x64", "url": "https://cdn.test/e.zip",
           "sha256": "00", "size": 3, "expires_at": "2026-09-05T00:10:00Z"}


def test_names_the_latest_release():
    check = latest_release(signed_in_over(ScriptedHttp(Reply(200, RELEASE))),
                           "sushiengine", "windows-x64")

    assert (check.version, check.reason) == ("1.4.2", None)


def test_asks_for_the_latest_release_without_a_version():
    http = ScriptedHttp(Reply(200, RELEASE))

    latest_release(signed_in_over(http), "sushiengine", "windows-x64")

    assert "version" not in json.loads(http.requests[-1].data)


def test_gives_the_reason_when_nobody_issigned_in_over():
    client = SushiAccount("http://account.invalid", MemoryStore(), now=lambda: 0.0)

    check = latest_release(client, "sushiengine", "windows-x64")

    assert check.version is None
    assert "hub login" in check.reason


def test_gives_the_reason_when_the_account_holds_no_licence():
    http = ScriptedHttp(Reply(403, {"error": "no_licence"}))

    check = latest_release(signed_in_over(http), "sushiengine", "windows-x64")

    assert check.version is None
    assert "licence" in check.reason


def test_gives_the_reason_when_an_unknown_product_is_asked_for():
    http = ScriptedHttp(Reply(404, {"error": "unknown_product"}))

    check = latest_release(signed_in_over(http), "sushiunknown", "windows-x64")

    assert check.version is None
    assert "sushiunknown" in check.reason


def test_gives_the_reason_when_sushi_id_is_unreachable():
    def refuse(request, timeout):
        """Fail the way urlopen does when nothing listens."""
        raise urllib.error.URLError("connection refused")

    check = latest_release(signed_in_over(refuse), "sushiengine", "windows-x64")

    assert check.version is None
    assert "unreachable" in check.reason
