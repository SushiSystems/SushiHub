# test_data_fragment_reader.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reading the [data.<name>] tables of a dependency fragment."""

from __future__ import annotations

import pytest

from sushihub.services.data import DataFragmentError, read_data_packages
from sushihub.setup.dependency_source import TomlDependencySource

pytestmark = pytest.mark.medium

K_DIGEST = "ab" * 32

K_TABLE = f"""
[data.de440]
description = "JPL DE440 ephemeris"
url         = "https://ssd.jpl.nasa.gov/ftp/eph/planets/ascii/de440/ascp01950.440"
sha256      = "{K_DIGEST.upper()}"
bytes       = 1234
licence     = "JPL ephemerides: public"
destination = "assets/astro/raw/ascp01950.440"
required    = true

[data.egm]
url         = "http://127.0.0.1/egm2008.gz"
sha256      = "{K_DIGEST}"
bytes       = 0
licence     = "GeographicLib: MIT"
destination = "assets/egm2008.gz"
"""


def _write(tmp_path, text: str):
    """Write *text* as a module fragment and return its path."""
    fragment = tmp_path / "sushistack.deps.toml"
    fragment.write_text(text, encoding="utf-8")
    return fragment


def test_read_data_packages_returns_each_table_in_file_order(tmp_path):
    packages = read_data_packages(_write(tmp_path, K_TABLE), "astro", tmp_path)
    assert [p.name for p in packages] == ["de440", "egm"]
    first = packages[0]
    assert (first.owner, first.checkout, first.size, first.required) == ("astro", tmp_path, 1234, True)
    assert first.sha256 == K_DIGEST
    assert first.file_name == "ascp01950.440"
    assert first.destination == "assets/astro/raw/ascp01950.440"


def test_read_data_packages_makes_a_package_optional_unless_it_says_required(tmp_path):
    packages = read_data_packages(_write(tmp_path, K_TABLE), "astro", tmp_path)
    assert packages[1].required is False


def test_read_data_packages_returns_none_for_a_fragment_without_data(tmp_path):
    assert read_data_packages(_write(tmp_path, '[module]\ncli = "x"\n'), "astro", tmp_path) == []


@pytest.mark.parametrize("key", ["url", "sha256", "bytes", "licence", "destination"])
def test_read_data_packages_refuses_a_table_missing_a_required_key(tmp_path, key):
    lines = [line for line in K_TABLE.split("[data.egm]")[1].splitlines()
             if not line.startswith(key + " ")]
    text = "[data.egm]\n" + "\n".join(lines)
    with pytest.raises(DataFragmentError, match=f"data.egm.*no '{key}'"):
        read_data_packages(_write(tmp_path, text), "astro", tmp_path)


@pytest.mark.parametrize("old, new, complaint", [
    (K_DIGEST, "xyz", "sha256"),
    ("bytes       = 0", 'bytes       = "big"', "bytes"),
    ("http://127.0.0.1/egm2008.gz", "ftp://127.0.0.1/egm2008.gz", "url"),
    ("http://127.0.0.1/egm2008.gz", "http://127.0.0.1/", "url"),
    ("http://127.0.0.1/egm2008.gz", "http://127.0.0.1/a/..", "url"),
    ('licence     = "GeographicLib: MIT"', 'licence     = ""', "licence"),
])
def test_read_data_packages_refuses_a_wrong_value_naming_the_key(tmp_path, old, new, complaint):
    text = "[data.egm]" + K_TABLE.split("[data.egm]")[1].replace(old, new)
    with pytest.raises(DataFragmentError, match=complaint):
        read_data_packages(_write(tmp_path, text), "astro", tmp_path)


def test_read_data_packages_refuses_a_data_key_that_is_not_a_table(tmp_path):
    with pytest.raises(DataFragmentError, match="'data' is a str"):
        read_data_packages(_write(tmp_path, 'data = "x"\n'), "astro", tmp_path)


def test_dependency_source_does_not_list_the_data_table_as_a_dependency(tmp_path):
    fragment = _write(tmp_path, K_TABLE + '\n[cmake]\ndescription = "cmake"\nlinux_apt = ["cmake"]\n')
    names = [dep.name for dep in TomlDependencySource([(fragment, "astro")]).all()]
    assert names == ["cmake"]
