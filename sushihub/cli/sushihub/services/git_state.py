"""Where a checkout stands against its upstream, read from git.

Reading never touches the network: ``ahead`` and ``behind`` count against the
upstream as the last fetch left it, and ``last_fetch`` says when that was.
:func:`fetch` is the one call here that goes online, and only
``hub status --check-updates`` makes it. See sushihub/contract/README.md,
"The status payload".
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class GitState:
    """A checkout's branch, its distance from upstream, and when it was last fetched."""

    branch: str | None
    ahead: int | None
    behind: int | None
    last_fetch: str | None

    def as_payload(self) -> dict:
        """Return the state as the ``source`` object of the status payload."""
        return {"branch": self.branch, "ahead": self.ahead, "behind": self.behind,
                "last_fetch": self.last_fetch}


def _git(path: Path, *args: str) -> str | None:
    """Run git in *path* and return its trimmed stdout, or None when it fails."""
    try:
        done = subprocess.run(["git", *args], cwd=path, capture_output=True, text=True,
                              timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _last_fetch(path: Path) -> str | None:
    """Return the modification time of ``.git/FETCH_HEAD`` in UTC, or None when absent."""
    try:
        stamp = (path / ".git" / "FETCH_HEAD").stat().st_mtime
    except OSError:
        return None
    moment = datetime.fromtimestamp(stamp, tz=timezone.utc).replace(microsecond=0)
    return moment.isoformat().replace("+00:00", "Z")


def read_git_state(path: Path) -> GitState | None:
    """Read the checkout rooted at *path*.

    Args:
        path: A directory that holds its own ``.git``; a subdirectory of another
            checkout is not one.

    Returns:
        The branch (None on a detached HEAD), the commits ahead of and behind the
        upstream (both None without one) and the last fetch, or None when *path*
        is not a checkout.
    """
    if not (path / ".git").exists():
        return None
    branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:
        return None
    if branch == "HEAD":
        return GitState(None, None, None, _last_fetch(path))

    ahead = behind = None
    counts = _git(path, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    if counts is not None:
        left, right = counts.split()
        ahead, behind = int(left), int(right)
    return GitState(branch, ahead, behind, _last_fetch(path))


def fetch(path: Path) -> bool:
    """Fetch the checkout at *path* from its remotes without merging. Report success."""
    return _git(path, "fetch", "--quiet") is not None
