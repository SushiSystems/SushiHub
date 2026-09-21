"""What a checkout's branch and upstream say, read from real repositories on disk."""

from __future__ import annotations

import subprocess
from pathlib import Path

from sushihub.services.git_state import fetch, read_git_state


def _git(cwd: Path, *args: str) -> str:
    """Run git in *cwd* with a fixed identity and return its stdout."""
    env_args = ["-c", "user.name=test", "-c", "user.email=test@example.com",
                "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
    done = subprocess.run(["git", *env_args, *args], cwd=cwd, check=True,
                          capture_output=True, text=True)
    return done.stdout.strip()


def _commit(cwd: Path, name: str) -> None:
    """Write file *name* in *cwd* and commit it."""
    (cwd / name).write_text(name, encoding="utf-8")
    _git(cwd, "add", name)
    _git(cwd, "commit", "-q", "-m", name)


def _origin_and_clone(tmp_path: Path) -> tuple[Path, Path]:
    """Create an origin with one commit and a clone tracking its main branch."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q")
    _commit(origin, "first")
    _git(tmp_path, "clone", "-q", str(origin), "clone")
    return origin, tmp_path / "clone"


def test_reads_nothing_from_a_directory_that_is_not_a_checkout(tmp_path):
    assert read_git_state(tmp_path) is None


def test_reads_nothing_from_a_subdirectory_of_someone_elses_checkout(tmp_path):
    _git(tmp_path, "init", "-q")
    inner = tmp_path / "inner"
    inner.mkdir()

    assert read_git_state(inner) is None


def test_reports_no_upstream_as_null_counts(tmp_path):
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "first")

    state = read_git_state(tmp_path)

    assert state is not None
    assert state.branch == "main"
    assert state.ahead is None
    assert state.behind is None


def test_counts_local_commits_as_ahead(tmp_path):
    _, clone = _origin_and_clone(tmp_path)
    _commit(clone, "second")
    _commit(clone, "third")

    state = read_git_state(clone)

    assert (state.ahead, state.behind) == (2, 0)


def test_counts_behind_only_after_a_fetch(tmp_path):
    origin, clone = _origin_and_clone(tmp_path)
    _commit(origin, "upstream")

    assert read_git_state(clone).behind == 0
    assert fetch(clone) is True
    assert read_git_state(clone).behind == 1


def test_reports_a_detached_head_as_no_branch(tmp_path):
    _, clone = _origin_and_clone(tmp_path)
    _git(clone, "checkout", "-q", "--detach")

    state = read_git_state(clone)

    assert state.branch is None
    assert state.ahead is None


def test_reports_no_last_fetch_for_a_checkout_never_fetched(tmp_path):
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "first")

    assert read_git_state(tmp_path).last_fetch is None


def test_reports_the_last_fetch_in_utc_once_one_happened(tmp_path):
    _, clone = _origin_and_clone(tmp_path)
    fetch(clone)

    stamp = read_git_state(clone).last_fetch
    assert stamp is not None and stamp.endswith("Z")


def test_reports_a_failed_fetch(tmp_path):
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "first")
    _git(tmp_path, "remote", "add", "origin", str(tmp_path / "missing"))

    assert fetch(tmp_path) is False
