# test_core_pin.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""How `hub pin sushicore` sets one exact requirement in every module CLI of the workspace."""

from __future__ import annotations

import pytest

from sushihub.services import core_pin, module_fragments, pins

K_TEXT = ('[project]\nname = "x"\ndependencies = [\n    "typer>=0.12",\n    "sushicore{operator}",\n]\n')


def _project(path, requirement, crlf=False):
    """Write a CLI `pyproject.toml` that requires sushicore as *requirement*."""
    path.parent.mkdir(parents=True)
    text = K_TEXT.format(operator=requirement)
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    return path


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Two modules and the hub itself, each requiring sushicore in another form."""
    checkouts = {"sushilog": tmp_path / "sushilog", "sushiai": tmp_path / "sushiai"}
    _project(checkouts["sushilog"] / "cli" / "pyproject.toml", "==0.9.7")
    _project(checkouts["sushiai"] / "cli" / "pyproject.toml", ">=0.9.5", crlf=True)
    _project(tmp_path / "cli" / "pyproject.toml", ">=0.9.5")
    monkeypatch.setattr(module_fragments, "present_modules", lambda root: checkouts)
    monkeypatch.setattr(core_pin, "present_modules", lambda root: checkouts)
    monkeypatch.setattr(core_pin, "workspace_root", lambda: tmp_path)
    return checkouts


def test_rewrite_sets_the_exact_form_whatever_the_operator_was():
    """`>=`, `==` and `~=` all become `==<version>`; the other requirements stay."""
    for operator in (">=0.9.5", "==0.9.7", "~=0.9"):
        text = K_TEXT.format(operator=operator)
        assert core_pin.rewrite_requirement(text, "0.9.8") == K_TEXT.format(operator="==0.9.8")


def test_rewrite_refuses_a_file_without_the_requirement():
    """A pyproject that does not require sushicore is an error, not a silent no-op."""
    with pytest.raises(ValueError):
        core_pin.rewrite_requirement('[project]\ndependencies = ["typer"]\n', "0.9.8")


def test_pin_rewrites_every_module_and_the_hub_itself(workspace, tmp_path):
    """Both modules and the hub move to the one exact form, and CRLF stays CRLF."""
    assert pins.pin("sushicore", "v0.9.8", None, dry_run=False) == 0
    for pyproject in (workspace["sushilog"] / "cli" / "pyproject.toml",
                      workspace["sushiai"] / "cli" / "pyproject.toml",
                      tmp_path / "cli" / "pyproject.toml"):
        assert b'"sushicore==0.9.8"' in pyproject.read_bytes()
    assert b"\r\n" in (workspace["sushiai"] / "cli" / "pyproject.toml").read_bytes()
    assert b"\r\n" not in (workspace["sushilog"] / "cli" / "pyproject.toml").read_bytes()


def test_a_dry_run_writes_nothing(workspace, tmp_path):
    """--dry-run reports the moves and leaves every file as it was."""
    assert len(core_pin.move_core_pin(tmp_path, "0.9.8", dry_run=True)) == 3
    assert b'"sushicore==0.9.7"' in (workspace["sushilog"] / "cli" / "pyproject.toml").read_bytes()


def test_a_project_already_on_the_version_is_not_reported(workspace, tmp_path):
    """Only the projects that change are listed, and the second run changes none."""
    core_pin.move_core_pin(tmp_path, "0.9.8", dry_run=False)
    assert core_pin.move_core_pin(tmp_path, "0.9.8", dry_run=False) == []


@pytest.mark.parametrize("version", ["latest", "0.9", "v1.2.3.4", "0.9.8rc1"])
def test_a_version_that_is_not_a_release_number_is_refused(version, workspace):
    """The version is three numbers, with or without the leading v."""
    assert pins.pin("sushicore", version, None, dry_run=False) == 1
