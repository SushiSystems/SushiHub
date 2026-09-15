"""How `hub` itself is installed, read from a fake home directory."""

from __future__ import annotations

from pathlib import Path

from sushistack.services.hub_install import ALIAS_MARKER, read_hub_install


def _write(path: Path, text: str) -> None:
    """Create *path* and its parents, holding *text*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_names_the_command_and_the_editable_channel(tmp_path):
    block = read_hub_install(tmp_path)

    assert block["command"] == "hub"
    assert block["channel"] == "editable"


def test_reports_no_alias_when_no_rc_file_carries_the_marker(tmp_path):
    _write(tmp_path / ".bashrc", "alias ll='ls -l'\n")

    assert read_hub_install(tmp_path)["alias"] is None


def test_finds_the_alias_in_bashrc(tmp_path):
    _write(tmp_path / ".bashrc", f"\n{ALIAS_MARKER}\nalias sh='hub'\n")

    alias = read_hub_install(tmp_path)["alias"]

    assert alias == {"name": "sh", "defined_in": str(tmp_path / ".bashrc")}


def test_finds_the_alias_in_the_powershell_profile(tmp_path):
    profile = tmp_path / "Documents" / "PowerShell" / "profile.ps1"
    _write(profile, f"\n{ALIAS_MARKER}\nfunction sh {{ hub @args }}\n")

    assert read_hub_install(tmp_path)["alias"]["defined_in"] == str(profile)


def test_finds_the_alias_in_the_windows_powershell_profile(tmp_path):
    profile = tmp_path / "Documents" / "WindowsPowerShell" / "profile.ps1"
    _write(profile, f"{ALIAS_MARKER}\nfunction sh {{ hub @args }}\n")

    assert read_hub_install(tmp_path)["alias"]["defined_in"] == str(profile)


def test_the_marker_matches_what_both_installers_write():
    root = Path(__file__).resolve().parents[3]

    assert f'ALIAS_MARKER="{ALIAS_MARKER}"' in (root / "install.sh").read_text(encoding="utf-8")
    assert f'$AliasMarker = "{ALIAS_MARKER}"' in (root / "install.ps1").read_text(encoding="utf-8")
