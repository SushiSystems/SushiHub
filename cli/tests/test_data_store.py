# test_data_store.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The machine's store of data packages, fetched from a server on 127.0.0.1."""

from __future__ import annotations

import hashlib

import pytest

from sushihub import __version__
from sushihub.services.data import DataFetchError, DataStore, DataVerificationError, HttpDownloader

from .support.data_server import package_of, serve

pytestmark = pytest.mark.medium

K_BODY = b"reference data " * 100
K_PATH = "/eph/ascp01950.440"


def _store(tmp_path) -> DataStore:
    """Return a store under *tmp_path* that fetches over http."""
    return DataStore(tmp_path / "data", HttpDownloader())


def test_ensure_downloads_into_the_store_under_the_digest_and_file_name(tmp_path):
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="x")
        stored, downloaded = _store(tmp_path).ensure(package)
    assert downloaded
    assert stored == tmp_path / "data" / hashlib.sha256(K_BODY).hexdigest() / "ascp01950.440"
    assert stored.read_bytes() == K_BODY


def test_ensure_names_hub_as_the_client_in_the_request(tmp_path):
    with serve({K_PATH: K_BODY}) as served:
        _store(tmp_path).ensure(package_of(served, tmp_path, K_PATH, destination="x"))
    assert [r.user_agent for r in served.requests] == [f"sushihub/{__version__}"]


def test_ensure_makes_no_request_when_the_store_holds_the_file(tmp_path):
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="x")
        store = _store(tmp_path)
        store.ensure(package)
        served.requests.clear()
        _, downloaded = store.ensure(package)
    assert not downloaded
    assert served.requests == []


def test_ensure_replaces_a_stored_file_that_differs_from_the_pin(tmp_path):
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="x")
        store = _store(tmp_path)
        stored, _ = store.ensure(package)
        stored.write_bytes(b"damaged")
        again, downloaded = store.ensure(package)
    assert downloaded
    assert again.read_bytes() == K_BODY


def test_ensure_deletes_a_download_whose_hash_differs_and_reports_both_hashes(tmp_path):
    wrong = "0" * 64
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="x", sha256=wrong)
        with pytest.raises(DataVerificationError) as raised:
            _store(tmp_path).ensure(package)
    message = str(raised.value)
    assert f"sha256 expected {wrong}, found {hashlib.sha256(K_BODY).hexdigest()}" in message
    assert list((tmp_path / "data").rglob("*")) == [tmp_path / "data" / wrong]


def test_ensure_deletes_a_download_whose_size_differs_and_reports_both_sizes(tmp_path):
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="x", size=len(K_BODY) + 1)
        with pytest.raises(DataVerificationError) as raised:
            _store(tmp_path).ensure(package)
    assert f"size expected {len(K_BODY) + 1} bytes, found {len(K_BODY)}" in str(raised.value)
    assert [p for p in (tmp_path / "data").rglob("*") if p.is_file()] == []


def test_ensure_reports_a_refused_download_as_a_fetch_error(tmp_path):
    with serve({}) as served:
        served.files[K_PATH] = K_BODY
        package = package_of(served, tmp_path, K_PATH, destination="x")
        del served.files[K_PATH]
        with pytest.raises(DataFetchError, match="404"):
            _store(tmp_path).ensure(package)
