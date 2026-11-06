# test_migrate_command.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What `hub migrate` moves, records and undoes, in a throwaway workspace.

Every test runs under the ``workspace`` fixture, which points the workspace, the default
root and the user's environment at ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sushicore.config_base import write_toml_document
from sushicore.provision import home, user_environment
from sushicore.provision.links import is_dir_link, link_target
from sushicore.provision.migrate import JOURNAL, MigrationJournal
from sushicore.provision.registry import Registry
from sushicore.provision.user_environment import ProfileEnvironment
from sushicore.workspace import WORKSPACE_HEADER, read_toml

from sushihub.cli import app
from sushihub.config import WORKSPACE_MARKER, deps_dir, workspace_file
from sushihub.services import migrate as migrate_svc

from .test_presence import Recorder

pytestmark = pytest.mark.medium

_FILES = {
    "toolchains/llvm-sycl/bin/clang++.exe": b"clang",
    "tools/cmake/bin/cmake.exe": b"cmake-binary",
    "vcpkg/installed/x.lib": b"library",
}


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch) -> Path:
    """Build a workspace with a dependency tree, and keep every write inside ``tmp_path``."""
    root = tmp_path / "ws"
    (root / WORKSPACE_MARKER).mkdir(parents=True)
    for name, data in _FILES.items():
        (root / "dependencies" / name).parent.mkdir(parents=True, exist_ok=True)
        (root / "dependencies" / name).write_bytes(data)
    write_toml_document(workspace_file(root), {
        "workspace": {"version": "1"},
        "tool": {"vcpkg_root": f"{root.as_posix()}/dependencies/vcpkg"},
    }, WORKSPACE_HEADER)
    monkeypatch.setenv("SUSHISTACK_HOME", str(root))
    monkeypatch.delenv("SUSHISTACK_DEPS_DIR", raising=False)
    monkeypatch.delenv(home.ENV_HOME, raising=False)
    monkeypatch.setattr(home, "default_root", lambda: tmp_path / "default")
    store = ProfileEnvironment(tmp_path / "profile")
    monkeypatch.setattr(user_environment, "default_environment", lambda: store)
    return root


@pytest.fixture
def recorder(monkeypatch) -> Recorder:
    """Capture every line `hub migrate` prints."""
    spy = Recorder()
    monkeypatch.setattr(migrate_svc, "console", spy)
    return spy


def _snapshot(root: Path) -> dict[str, bytes]:
    """Return the bytes of every file under *root* by relative path."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _stored_home() -> str | None:
    """Return the ``SUSHISYSTEMS_HOME`` the fake user environment holds."""
    return user_environment.read_user_variable(home.ENV_HOME)


def _unsaid(recorder: Recorder, texts: list[str]) -> list[str]:
    """Return the *texts* no printed line contains."""
    return [text for text in texts if not recorder.said(text)]


def test_dry_run_prints_every_component_and_the_space(workspace, recorder, tmp_path):
    """--dry-run names both roots, each component and the space."""
    assert migrate_svc.run(dry_run=True) == 0
    assert _unsaid(recorder, [
        "toolchains: 1 file, 5 B", "tools: 1 file, 12 B", "vcpkg: 1 file, 7 B",
        f"from: {workspace.as_posix()}/dependencies",
        f"to:   {tmp_path.as_posix()}/default",
        "total: 24 B", "enough space: yes", "Dry-run: nothing was changed."]) == []


def test_dry_run_changes_nothing(workspace, recorder, tmp_path):
    """--dry-run touches no file and makes no link or target."""
    before = _snapshot(workspace)
    migrate_svc.run(dry_run=True)
    assert _snapshot(workspace) == before
    assert not (tmp_path / "default").exists()
    assert not is_dir_link(workspace / "dependencies")


def test_run_with_yes_links_the_old_path(workspace, recorder, tmp_path):
    """A confirmed run leaves a link at the old path that still reads the files."""
    target = tmp_path / "default"
    assert migrate_svc.run(assume_yes=True) == 0
    assert link_target(workspace / "dependencies").resolve() == target.resolve()
    assert (workspace / "dependencies/tools/cmake/bin/cmake.exe").read_bytes() == b"cmake-binary"


def test_run_with_yes_writes_the_registry(workspace, recorder, tmp_path):
    """A confirmed run records every component in the registry of the new root."""
    migrate_svc.run(assume_yes=True)
    registry = Registry(tmp_path / "default" / "registry.toml")
    registry.load()
    assert {(c.name, c.consumers) for c in registry.components()} == {
        ("llvm-sycl", ("hub",)), ("cmake", ("hub",)), ("vcpkg", ("hub",))}


def test_run_asks_before_moving_and_stops_on_no(workspace, recorder, monkeypatch):
    """Without --yes the move waits for an answer, and "n" changes nothing."""
    recorder.prompt = lambda *_args: "n"
    assert migrate_svc.run() == 1
    assert recorder.said("Aborted.")
    assert not is_dir_link(workspace / "dependencies")


def test_run_to_the_default_root_leaves_the_variable_unset(workspace, recorder):
    """Moving to the default root sets no SUSHISYSTEMS_HOME and says so."""
    assert migrate_svc.run(assume_yes=True) == 0
    assert _stored_home() is None
    assert recorder.said("is the default root")


def test_run_to_another_path_sets_the_variable(workspace, recorder, tmp_path):
    """Moving elsewhere stores SUSHISYSTEMS_HOME."""
    target = tmp_path / "elsewhere"
    assert migrate_svc.run(target, assume_yes=True) == 0
    assert _stored_home() == target.as_posix()


def test_run_to_another_path_prints_the_facts_of_the_move(workspace, recorder, tmp_path):
    """Moving elsewhere prints the four facts of the move."""
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    assert _unsaid(recorder, [
        f"The dependency tree is now at {target.as_posix()}.",
        f"{workspace.as_posix()}/dependencies is a link to it",
        f"SUSHISYSTEMS_HOME was set to {target.as_posix()}",
        "Terminals opened before now must be reopened to see it."]) == []


def test_run_rewrites_the_tool_paths_of_the_workspace_file(workspace, recorder, tmp_path):
    """The [tool] value that named the old tree names the new root afterwards."""
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    tool = read_toml(workspace_file(workspace))["tool"]
    assert tool["vcpkg_root"] == f"{target.as_posix()}/vcpkg"


def _journal_after_a_run(tmp_path) -> dict[str, dict]:
    """Migrate with the variable already set, and return the journal entries by step."""
    user_environment.write_user_variable(home.ENV_HOME, "/somewhere/else")
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    return {e["step"]: e for e in MigrationJournal(target).entries()}


def test_run_journals_the_earlier_variable(workspace, recorder, tmp_path):
    """The journal holds the value SUSHISYSTEMS_HOME had before the move."""
    assert _journal_after_a_run(tmp_path)["environment"] == {
        "step": "environment", "name": "SUSHISYSTEMS_HOME", "previous": "/somewhere/else"}


def test_run_journals_the_workspace_rewrite(workspace, recorder, tmp_path):
    """The journal holds a workspace step."""
    assert "workspace" in _journal_after_a_run(tmp_path)


def test_run_journals_the_registry_it_created(workspace, recorder, tmp_path):
    """The journal records that the registry did not exist before the move."""
    assert _journal_after_a_run(tmp_path)["registry"]["created"] is True


def test_a_second_run_reports_the_finished_move(workspace, recorder, tmp_path):
    """Running again after success exits zero and moves nothing."""
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    journal = (target / JOURNAL).read_text(encoding="utf-8")
    assert migrate_svc.run(assume_yes=True) == 0
    assert recorder.said("already migrated")
    assert (target / JOURNAL).read_text(encoding="utf-8") == journal


def test_run_refuses_a_target_that_holds_a_component(workspace, recorder, tmp_path):
    """A target that already holds a component's name stops the run before the prompt."""
    (tmp_path / "default" / "vcpkg").mkdir(parents=True)
    assert migrate_svc.run(assume_yes=True) == 1
    assert recorder.said("already exists")
    assert not is_dir_link(workspace / "dependencies")


def _rollback_after_a_run(tmp_path) -> Path:
    """Migrate with the variable already set, roll back, and return the target."""
    user_environment.write_user_variable(home.ENV_HOME, "/somewhere/else")
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    assert migrate_svc.rollback() == 0
    return target


def test_rollback_restores_the_tree_and_the_file(workspace, recorder, tmp_path):
    """--rollback puts back the folder and the tool paths of the workspace file."""
    before = _snapshot(workspace)
    _rollback_after_a_run(tmp_path)
    assert not is_dir_link(workspace / "dependencies")
    assert _snapshot(workspace) == before


def test_rollback_restores_the_earlier_variable(workspace, recorder, tmp_path):
    """--rollback puts back the value SUSHISYSTEMS_HOME had before the move."""
    _rollback_after_a_run(tmp_path)
    assert _stored_home() == "/somewhere/else"


def test_rollback_removes_the_registry_and_the_journal(workspace, recorder, tmp_path):
    """--rollback leaves neither the registry nor the journal in the target."""
    target = _rollback_after_a_run(tmp_path)
    assert not (target / "registry.toml").exists()
    assert not (target / JOURNAL).exists()


def test_rollback_removes_a_variable_that_was_not_set_before(workspace, recorder, tmp_path):
    """--rollback unsets SUSHISYSTEMS_HOME when the migration was the one that set it."""
    migrate_svc.run(tmp_path / "elsewhere", assume_yes=True)
    assert migrate_svc.rollback() == 0
    assert _stored_home() is None


def test_rollback_with_nothing_to_undo_exits_zero(workspace, recorder):
    """--rollback before any migration reports that and changes nothing."""
    before = _snapshot(workspace)
    assert migrate_svc.rollback() == 0
    assert recorder.said("nothing to roll back")
    assert _snapshot(workspace) == before


def _finalized(tmp_path) -> Path:
    """Migrate, finalize, and return the target."""
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    assert migrate_svc.finalize() == 0
    return target


def test_finalize_deletes_the_old_copy(workspace, recorder, tmp_path):
    """--finalize removes dependencies.pre-migrate."""
    _finalized(tmp_path)
    assert not (workspace / "dependencies.pre-migrate").exists()


def test_finalize_keeps_the_link_and_the_new_tree(workspace, recorder, tmp_path):
    """--finalize leaves the link and the files in the new tree."""
    target = _finalized(tmp_path)
    assert is_dir_link(workspace / "dependencies")
    assert (target / "vcpkg/installed/x.lib").is_file()


def test_rollback_after_finalize_keeps_the_link(workspace, recorder, tmp_path):
    """--rollback after --finalize exits zero and the link stays."""
    _finalized(tmp_path)
    assert migrate_svc.rollback() == 0
    assert is_dir_link(workspace / "dependencies")


def test_finalize_before_a_migration_refuses(workspace, recorder):
    """--finalize on a workspace that was never migrated exits one and deletes nothing."""
    before = _snapshot(workspace)
    assert migrate_svc.finalize() == 1
    assert recorder.said("is not a link")
    assert _snapshot(workspace) == before


def test_finalize_with_drop_link_removes_the_link(workspace, recorder, tmp_path):
    """--finalize --drop-link removes the link once SUSHISYSTEMS_HOME names the tree."""
    target = tmp_path / "elsewhere"
    migrate_svc.run(target, assume_yes=True)
    assert migrate_svc.finalize(drop_link=True) == 0
    assert not (workspace / "dependencies").exists()
    assert not is_dir_link(workspace / "dependencies")
    assert (target / "vcpkg/installed/x.lib").is_file()


def test_drop_link_is_refused_when_nothing_else_names_the_tree(workspace, recorder):
    """--drop-link keeps the link when SUSHISYSTEMS_HOME does not name the new root."""
    migrate_svc.run(assume_yes=True)
    assert migrate_svc.finalize(drop_link=True) == 1
    assert recorder.said("The link was kept.")
    assert is_dir_link(workspace / "dependencies")
    assert (workspace / "dependencies.pre-migrate").is_dir()


def test_deps_dir_follows_the_link_after_a_migration(workspace, recorder, tmp_path):
    """After the move the dependency directory is the new root, and the old one after rollback."""
    migrate_svc.run(assume_yes=True)
    assert deps_dir().resolve() == (tmp_path / "default").resolve()
    migrate_svc.rollback()
    assert deps_dir() == workspace / "dependencies"


def test_deps_dir_prefers_sushisystems_home_to_the_workspace(workspace, monkeypatch, tmp_path):
    """SUSHISYSTEMS_HOME answers before the workspace tree and its link."""
    monkeypatch.setenv(home.ENV_HOME, str(tmp_path / "from-env"))
    assert deps_dir() == (tmp_path / "from-env").resolve()


def test_the_command_runs_a_dry_run_through_typer(workspace, tmp_path):
    """`hub migrate --dry-run --to PATH` exits zero and leaves the tree where it was."""
    result = CliRunner().invoke(app, ["migrate", "--dry-run", "--to", str(tmp_path / "t")])
    assert result.exit_code == 0, result.output
    assert "enough space: yes" in result.output
    assert not is_dir_link(workspace / "dependencies")
    assert not (tmp_path / "t").exists()


def test_the_command_refuses_rollback_with_finalize(workspace):
    """--rollback and --finalize together are a usage error and nothing runs."""
    result = CliRunner().invoke(app, ["migrate", "--rollback", "--finalize"])
    assert result.exit_code == 2
    assert not is_dir_link(workspace / "dependencies")


def test_the_command_refuses_drop_link_without_finalize(workspace):
    """--drop-link alone is a usage error and nothing runs."""
    result = CliRunner().invoke(app, ["migrate", "--drop-link", "--yes"])
    assert result.exit_code == 2
    assert not is_dir_link(workspace / "dependencies")


def test_the_command_migrates_and_rolls_back_through_typer(workspace, tmp_path):
    """`hub migrate --to PATH --yes` then `--rollback` leaves the workspace as it began."""
    before = _snapshot(workspace)
    target = tmp_path / "t"
    moved = CliRunner().invoke(app, ["migrate", "--to", str(target), "--yes"])
    assert moved.exit_code == 0, moved.output
    assert is_dir_link(workspace / "dependencies")
    undone = CliRunner().invoke(app, ["migrate", "--rollback"])
    assert undone.exit_code == 0, undone.output
    assert _snapshot(workspace) == before
