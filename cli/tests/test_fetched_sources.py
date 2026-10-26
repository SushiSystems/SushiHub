# test_fetched_sources.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""How a workspace takes over the copies a module's own setup fetched."""

from __future__ import annotations

import subprocess

import pytest

from sushihub.services import fetched_sources, module_fragments

K_COMMIT = "0123456789abcdef0123456789abcdef01234567"


def _git(*args, cwd):
    """Run git quietly in *cwd*, failing the test on an error."""
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def sources(tmp_path, monkeypatch):
    """A machine sources/ folder holding sushilog at v0.1.0 and v0.10.0, each a git repository."""
    root = tmp_path / "sources"
    for version in ("v0.1.0", "v0.10.0"):
        copy = root / "sushilog" / version
        copy.mkdir(parents=True)
        _git("init", "-q", cwd=copy)
        (copy / "README.md").write_text(version, encoding="utf-8")
        _git("add", ".", cwd=copy)
        _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", version, cwd=copy)
    monkeypatch.setattr(fetched_sources.home, "sources_dir", lambda: root)
    return root


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A workspace holding one module, sushiruntime, that pins sushilog v0.1.0."""
    checkout = tmp_path / "ws" / "sushiruntime"
    fragment = checkout / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text('[module]\ndepends_on = ["sushilog"]\n\n'
                        f'[sushisystems.sushilog]\nversion = "v0.1.0"\ncommit = "{K_COMMIT}"\n',
                        encoding="utf-8")
    monkeypatch.setattr(module_fragments, "present_modules", lambda root: {"sushiruntime": checkout})
    return tmp_path / "ws"


def test_the_newest_copy_is_chosen_by_release_order(sources):
    """v0.10.0 is newer than v0.1.0, compared as numbers."""
    assert fetched_sources.newest_copy("sushilog").version == "v0.10.0"
    assert fetched_sources.newest_copy("sushiruntime") is None


def test_a_copy_no_module_pins_is_unused(sources, workspace):
    """The pinned v0.1.0 is kept; v0.10.0 is listed as unused."""
    assert [copy.version for copy in fetched_sources.unused_copies(workspace)] == ["v0.10.0"]


def test_clean_removes_only_the_unused_copy(sources, workspace):
    """`hub clean` deletes v0.10.0 and leaves the pinned copy in place."""
    assert fetched_sources.clean(workspace, dry_run=False) == 0
    assert not (sources / "sushilog" / "v0.10.0").exists()
    assert (sources / "sushilog" / "v0.1.0").exists()


def test_a_dry_run_clean_removes_nothing(sources, workspace):
    """--dry-run lists the copy and keeps it."""
    assert fetched_sources.clean(workspace, dry_run=True) == 0
    assert (sources / "sushilog" / "v0.10.0").exists()


def test_a_module_is_cloned_from_the_copy_with_the_repository_as_its_remote(sources, tmp_path):
    """The clone needs no network, and origin then names the repository, not the copy."""
    copy = fetched_sources.newest_copy("sushilog")
    dest = tmp_path / "ws" / "sushilog"
    dest.parent.mkdir(parents=True)
    repo = "https://example.invalid/sushilog.git"

    assert fetched_sources.clone_from_copy(copy, repo, dest, dest.parent)
    assert (dest / "README.md").read_text(encoding="utf-8") == "v0.10.0"
    origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=dest,
                            capture_output=True, text=True, check=True).stdout.strip()
    assert origin == repo
