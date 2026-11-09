# test_data_installer.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installing data packages: download, verify, place."""

from __future__ import annotations

import pytest

from sushihub.services.data import DataInstaller, DataPlacer, DataStore, HttpDownloader

from .support.data_server import package_of, serve

pytestmark = pytest.mark.medium

K_BODY = b"ephemeris block " * 64
K_PATH = "/eph/ascp01950.440"


def _installer(tmp_path, out) -> DataInstaller:
    """Return an installer whose store is under *tmp_path* and whose output goes to *out*."""
    return DataInstaller(DataStore(tmp_path / "data", HttpDownloader()), DataPlacer(), out)


def test_install_downloads_then_places_the_file_at_the_destination(tmp_path, out):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, checkout, K_PATH, destination="assets/raw/ascp01950.440")
        results = _installer(tmp_path, out).install([package])
    assert [r.error for r in results] == [None]
    assert (checkout / "assets/raw/ascp01950.440").read_bytes() == K_BODY
    assert [r.path for r in served.requests] == [K_PATH]
    assert out.texts("progress") == ["download"]


def test_install_takes_a_stored_file_without_a_request(tmp_path, out):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    with serve({K_PATH: K_BODY}) as served:
        installer = _installer(tmp_path, out)
        installer.install([package_of(served, first, K_PATH, destination="a.440")])
        served.requests.clear()
        results = installer.install([package_of(served, second, K_PATH, destination="b.440")])
    assert [r.error for r in results] == [None]
    assert served.requests == []
    assert (second / "b.440").read_bytes() == K_BODY


def test_install_refuses_an_escaping_destination_before_any_request(tmp_path, out):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, checkout, K_PATH, destination="../escaped.440")
        results = _installer(tmp_path, out).install([package])
    assert "leaves the checkout" in (results[0].error or "")
    assert served.requests == []
    assert not (tmp_path / "escaped.440").exists()


def test_install_fails_the_package_on_a_hash_mismatch_and_places_nothing(tmp_path, out):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, checkout, K_PATH, destination="a.440", sha256="1" * 64)
        results = _installer(tmp_path, out).install([package])
    assert "sha256 expected " + "1" * 64 in (results[0].error or "")
    assert not (checkout / "a.440").exists()
    assert out.texts("error") == [results[0].error]


def test_install_goes_on_to_the_next_package_after_a_failure(tmp_path, out):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with serve({K_PATH: K_BODY}) as served:
        bad = package_of(served, checkout, K_PATH, destination="a.440", size=1)
        good = package_of(served, checkout, K_PATH, destination="b.440", name="second")
        results = _installer(tmp_path, out).install([bad, good])
    assert [r.error is None for r in results] == [False, True]
    assert (checkout / "b.440").read_bytes() == K_BODY
