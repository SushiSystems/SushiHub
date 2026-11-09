# test_data_report.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The rows `hub doctor` prints for data packages."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from sushihub.services.data import DataFragmentError, DataPackage, DataPlacer, DataReport
from sushihub.setup.detect_step import DetectStep
from sushihub.setup.pipeline import InstallContext

from .conftest import MemorySource
from .support.listed_packages import ListedPackages, RefusedFragment

pytestmark = pytest.mark.medium

K_BODY = b"grib2 analysis " * 20


def _package(checkout, name: str, owner: str = "astro") -> DataPackage:
    """Return a package pinning K_BODY that is read at ``<name>.bin``."""
    return DataPackage(
        name=name, owner=owner, checkout=checkout, url=f"http://127.0.0.1/{name}.bin",
        sha256=hashlib.sha256(K_BODY).hexdigest(), size=len(K_BODY), licence="public",
        destination=f"{name}.bin")


def test_rows_report_a_present_a_missing_and_a_corrupt_package_with_their_owner(tmp_path, out):
    (tmp_path / "present.bin").write_bytes(K_BODY)
    (tmp_path / "corrupt.bin").write_bytes(b"not it")
    source = ListedPackages(_package(tmp_path, "present"), _package(tmp_path, "missing", "ai"),
                            _package(tmp_path, "corrupt"))
    rows = DataReport(source, DataPlacer(), out).rows()
    assert [row[:3] for row in rows] == [
        ("present", "OK", "astro"), ("missing", "MISSING", "ai"), ("corrupt", "CORRUPT", "astro")]
    assert "hub install" in rows[1][3] and "differs" in rows[2][3]


def test_rows_warn_and_list_nothing_when_a_fragment_is_wrong(tmp_path, out):
    source = RefusedFragment(DataFragmentError("fragment: [data.x] has no 'url'"))
    assert DataReport(source, DataPlacer(), out).rows() == []
    assert out.texts("warn") == ["fragment: [data.x] has no 'url'"]


def test_rows_report_a_destination_that_leaves_the_checkout_as_corrupt(tmp_path, out):
    escaping = replace(_package(tmp_path, "escape"), destination="../x.bin")
    row = DataReport(ListedPackages(escaping), DataPlacer(), out).rows()[0]
    assert row[1] == "CORRUPT" and "leaves the checkout" in row[3]


def test_detect_step_puts_each_data_row_after_the_last_row_of_its_owner(fake_cfg):
    rows = [("cmake", "OK", "shared", ""), ("acpp", "OK", "ai", ""), ("gtest", "OK", "astro", ""),
            ("opencl", "OK", "ai", "")]
    data = [("egm", "OK", "ai", ""), ("lonely", "OK", "other", "")]
    step = DetectStep(MemorySource([]), inventory=lambda ctx, deps: rows, data_rows=lambda: data)
    merged = step.inventory_rows(InstallContext(cfg=fake_cfg), [])
    assert [row[0] for row in merged] == ["cmake", "acpp", "gtest", "opencl", "egm", "lonely"]
