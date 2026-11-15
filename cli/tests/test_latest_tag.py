# test_latest_tag.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which tag of a `git ls-remote --tags` listing counts as the latest release."""

from __future__ import annotations

import pytest

from sushihub.services.git_ops import highest_release_tag

pytestmark = pytest.mark.small

K_HASH = "0123456789abcdef0123456789abcdef01234567"


def _listing(*refs: str) -> str:
    """Return `git ls-remote --tags` output naming each of *refs*."""
    return "".join(f"{K_HASH}\trefs/tags/{ref}\n" for ref in refs)


def test_the_highest_version_wins_over_the_lexical_order():
    """v0.10.0 is newer than v0.9.9."""
    assert highest_release_tag(_listing("v0.9.9", "v0.10.0", "v0.2.0")) == "v0.10.0"


def test_peeled_and_pre_release_refs_are_ignored():
    """An annotated tag's ^{} line and a release candidate never count."""
    listing = _listing("v0.5.1", "v0.5.1^{}", "v0.6.0-rc1", "v1.0.0-beta.2", "nightly")
    assert highest_release_tag(listing) == "v0.5.1"


def test_a_listing_without_a_release_has_no_latest_tag():
    """Empty output and pre-releases only answer None."""
    assert highest_release_tag("") is None
    assert highest_release_tag(_listing("v1.0.0-rc1")) is None
