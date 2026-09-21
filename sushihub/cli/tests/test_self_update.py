"""`hub sync` updates `hub` itself the way `hub` was installed.

An install from the index is upgraded with pipx; an editable install tracks a
checkout and is pulled. Neither branch may reach the network or the machine's
real pipx, so both are answered with recorders.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sushistack.services import git_ops, modules, pipx


class Recorder:
    """Collect what the service printed, so a test can assert on one line."""

    def __init__(self):
        self.lines: list[str] = []

    def _say(self, text, *a, **k):
        self.lines.append(str(text))

    info = success = warn = error = header = _say

    def said(self, fragment: str) -> bool:
        """Whether any line printed so far contains *fragment*."""
        return any(fragment in line for line in self.lines)


@pytest.fixture
def calls(monkeypatch):
    """Answer pipx and git with recorders and hand both lists back."""
    pulled: list[Path] = []
    upgraded: list[str] = []
    monkeypatch.setattr(git_ops, "run", lambda args, cwd: pulled.append(cwd) or 0)
    monkeypatch.setattr(pipx, "upgrade", lambda name: upgraded.append(name) or 0)
    monkeypatch.setattr(modules, "console", Recorder())
    return pulled, upgraded


def _checkout(root: Path) -> Path:
    """Make *root* look like a git checkout holding the CLI package."""
    (root / ".git").mkdir(parents=True)
    package = root / "sushihub" / "cli"
    package.mkdir(parents=True)
    return package


def test_an_index_install_is_upgraded_with_pipx(tmp_path, monkeypatch, calls):
    """pipx holds `hub` by name, so pipx upgrades it and git is never run."""
    pulled, upgraded = calls
    monkeypatch.setattr(pipx, "installed", lambda name: pipx.Install(None))
    modules._self_update(tmp_path, dry_run=False)
    assert upgraded == ["sushihub"]
    assert pulled == []


def test_an_editable_install_pulls_its_own_checkout(tmp_path, monkeypatch, calls):
    """The checkout pipx recorded is pulled, not the workspace it was asked about."""
    pulled, upgraded = calls
    package = _checkout(tmp_path / "elsewhere")
    monkeypatch.setattr(pipx, "installed", lambda name: pipx.Install(package))
    modules._self_update(tmp_path / "workspace", dry_run=False)
    assert pulled == [tmp_path / "elsewhere"]
    assert upgraded == []


def test_neither_branch_runs_under_dry_run(tmp_path, monkeypatch, calls):
    """A dry run says what it would do and touches nothing."""
    pulled, upgraded = calls
    monkeypatch.setattr(pipx, "installed", lambda name: pipx.Install(None))
    modules._self_update(tmp_path, dry_run=True)
    package = _checkout(tmp_path / "elsewhere")
    monkeypatch.setattr(pipx, "installed", lambda name: pipx.Install(package))
    modules._self_update(tmp_path, dry_run=True)
    assert pulled == []
    assert upgraded == []


def test_a_workspace_that_is_no_checkout_is_left_alone(tmp_path, monkeypatch, calls):
    """pipx knows no `hub` and the workspace is no git tree, so nothing happens."""
    pulled, upgraded = calls
    monkeypatch.setattr(pipx, "installed", lambda name: None)
    modules._self_update(tmp_path, dry_run=False)
    assert pulled == []
    assert upgraded == []


def test_an_editable_install_outside_a_checkout_warns(tmp_path, monkeypatch, calls):
    """A recorded source with no .git above it is reported, not pulled blindly."""
    pulled, upgraded = calls
    recorder = Recorder()
    monkeypatch.setattr(modules, "console", recorder)
    loose = tmp_path / "loose" / "cli"
    loose.mkdir(parents=True)
    monkeypatch.setattr(pipx, "installed", lambda name: pipx.Install(loose))
    modules._self_update(tmp_path, dry_run=False)
    assert pulled == []
    assert upgraded == []
    assert recorder.said("not a git checkout")


def test_a_failed_upgrade_warns_rather_than_raising(tmp_path, monkeypatch):
    """pipx returning non-zero must not stop the rest of `hub sync`."""
    recorder = Recorder()
    monkeypatch.setattr(modules, "console", recorder)
    monkeypatch.setattr(pipx, "installed", lambda name: pipx.Install(None))
    monkeypatch.setattr(pipx, "upgrade", lambda name: 1)
    modules._self_update(tmp_path, dry_run=False)
    assert recorder.said("self-update failed")
