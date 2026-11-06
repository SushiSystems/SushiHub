# test_hub_install.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How `hub` itself is installed, read from a fake home directory."""

from __future__ import annotations

import sys
from pathlib import Path

from sushihub.services.hub_install import ALIAS_MARKER, read_hub_install

import pytest


def _write(path: Path, text: str) -> None:
    """Create *path* and its parents, holding *text*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.medium
@pytest.mark.parametrize(("frozen", "channel"), [(False, "editable"), (True, "frozen")])
def test_names_the_channel_the_executable_runs_in(tmp_path, monkeypatch, frozen, channel):
    """A frozen executable reports the frozen channel, a source install the editable one."""
    if frozen:
        monkeypatch.setattr(sys, "frozen", True, raising=False)
    else:
        monkeypatch.delattr(sys, "frozen", raising=False)

    assert read_hub_install(tmp_path)["channel"] == channel


@pytest.mark.medium
def test_reports_no_alias_when_no_rc_file_carries_the_marker(tmp_path):
    _write(tmp_path / ".bashrc", "alias ll='ls -l'\n")

    assert read_hub_install(tmp_path)["alias"] is None


@pytest.mark.medium
@pytest.mark.parametrize("relative", [
    Path(".bashrc"),
    Path(".zshrc"),
    Path("Documents") / "PowerShell" / "profile.ps1",
    Path("Documents") / "WindowsPowerShell" / "profile.ps1",
])
def test_finds_the_alias_in_a_profile_carrying_the_marker(tmp_path, relative):
    """The alias is reported under the name the installers give it, with the file that holds it."""
    _write(tmp_path / relative, f"\n{ALIAS_MARKER}\nalias sh='hub'\n")

    alias = read_hub_install(tmp_path)["alias"]

    assert alias == {"name": "sh", "defined_in": str(tmp_path / relative)}


@pytest.mark.medium
def test_the_marker_matches_what_both_installers_write():
    root = Path(__file__).resolve().parents[2]

    assert f'ALIAS_MARKER="{ALIAS_MARKER}"' in (root / "install.sh").read_text(encoding="utf-8")
    assert f'$AliasMarker = "{ALIAS_MARKER}"' in (root / "install.ps1").read_text(encoding="utf-8")
