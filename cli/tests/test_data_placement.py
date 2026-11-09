# test_data_placement.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Placing a stored data package where its module reads it."""

from __future__ import annotations

import hashlib

import pytest

from sushihub.services.data import DataDestinationError, DataPackage, DataPlacer, FileState

pytestmark = pytest.mark.medium

K_BODY = b"coefficients " * 50


def _package(checkout, destination: str) -> DataPackage:
    """Return a package pinning K_BODY that is read at *destination*."""
    return DataPackage(
        name="egm", owner="astro", checkout=checkout, url="http://127.0.0.1/egm.gz",
        sha256=hashlib.sha256(K_BODY).hexdigest(), size=len(K_BODY), licence="MIT",
        destination=destination)


def _stored(tmp_path):
    """Write K_BODY as the store's copy and return its path."""
    stored = tmp_path / "store" / "egm.gz"
    stored.parent.mkdir()
    stored.write_bytes(K_BODY)
    return stored


@pytest.mark.parametrize("destination", ["../outside.gz", "assets/../../outside.gz", ".", ""])
def test_destination_refuses_a_path_that_leaves_the_checkout(tmp_path, destination):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with pytest.raises(DataDestinationError, match="leaves the checkout"):
        DataPlacer().destination(_package(checkout, destination))


def test_destination_refuses_an_absolute_path(tmp_path):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with pytest.raises(DataDestinationError):
        DataPlacer().destination(_package(checkout, str(tmp_path / "elsewhere.gz")))


def test_place_copies_the_stored_file_to_the_destination_creating_its_folders(tmp_path):
    checkout = tmp_path / "module"
    checkout.mkdir()
    package = _package(checkout, "assets/raw/egm.gz")
    assert DataPlacer().place(package, _stored(tmp_path))
    assert (checkout / "assets/raw/egm.gz").read_bytes() == K_BODY
    assert [p.name for p in (checkout / "assets/raw").iterdir()] == ["egm.gz"]


def test_place_copies_nothing_when_an_intact_copy_is_there(tmp_path):
    checkout = tmp_path / "module"
    checkout.mkdir()
    package = _package(checkout, "egm.gz")
    placer = DataPlacer()
    stored = _stored(tmp_path)
    placer.place(package, stored)
    assert not placer.place(package, stored)


def test_place_replaces_a_copy_that_differs_in_content(tmp_path):
    checkout = tmp_path / "module"
    checkout.mkdir()
    (checkout / "egm.gz").write_bytes(b"x" * len(K_BODY))
    assert DataPlacer().place(_package(checkout, "egm.gz"), _stored(tmp_path))
    assert (checkout / "egm.gz").read_bytes() == K_BODY


def test_state_is_missing_when_nothing_is_at_the_destination(tmp_path):
    assert DataPlacer().state(_package(tmp_path, "egm.gz")) is FileState.MISSING


@pytest.mark.parametrize("content, state", [
    (K_BODY, FileState.INTACT),
    (b"short", FileState.CORRUPT),
    (b"x" * len(K_BODY), FileState.CORRUPT),
])
def test_state_judges_the_destination_by_size_and_digest(tmp_path, content, state):
    (tmp_path / "egm.gz").write_bytes(content)
    assert DataPlacer().state(_package(tmp_path, "egm.gz")) is state
