# test_git_ops.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the git adapter answers about a tag, against a real repository on disk."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushihub.services.git_ops import ProcessGit

pytestmark = pytest.mark.medium


def _git(cwd: Path, *args: str) -> str:
    """Run git in *cwd* with a fixed identity and return its output."""
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
         *args],
        cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def library(tmp_path) -> Path:
    """A repository with one commit, a lightweight tag v1 and an annotated tag v2 on it."""
    path = tmp_path / "library"
    path.mkdir()
    _git(path, "init", "-q")
    (path / "README.md").write_text("x", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "first")
    _git(path, "tag", "v1")
    _git(path, "tag", "-a", "v2", "-m", "second")
    return path


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_tag_commit_names_the_commit_of_a_lightweight_and_of_an_annotated_tag(library, version):
    """An annotated tag answers with the commit it peels to, not with the tag object."""
    assert ProcessGit().tag_commit(str(library), version) == _git(library, "rev-parse", "HEAD")


def test_tag_commit_is_none_for_a_tag_the_repository_lacks(library):
    """A tag nobody made is not found."""
    assert ProcessGit().tag_commit(str(library), "v9") is None


def test_tag_commit_is_none_for_a_repository_that_does_not_exist(tmp_path):
    """A repository git cannot read is not found, not an error."""
    assert ProcessGit().tag_commit(str(tmp_path / "gone"), "v1") is None
