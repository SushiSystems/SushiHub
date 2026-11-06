# test_pins.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How `hub pin` moves one library's pin in every module that pins it."""

from __future__ import annotations

import pytest

from sushihub.services import pins

K_OLD = "0123456789abcdef0123456789abcdef01234567"
K_NEW = "89abcdef0123456789abcdef0123456789abcdef"


def _fragment(path, version, commit, extra=""):
    """Write a fragment that pins sushilog at *version* and *commit*."""
    path.parent.mkdir(parents=True)
    path.write_text(f'# kept comment\n[module]\ndepends_on = ["sushilog"{extra}]\n\n'
                    f'[sushisystems.sushilog]\nversion = "{version}"\ncommit = "{commit}"\n\n'
                    '[hwloc]\ndescription = "x"\n', encoding="utf-8")
    return path


@pytest.fixture
def two_modules(tmp_path, monkeypatch):
    """A real workspace: two cloned modules pinning sushilog v0.1.0, and a third that pins nothing."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    checkouts = {name: tmp_path / name for name in ("sushiruntime", "sushidsp", "sushiai")}
    for checkout in checkouts.values():
        (checkout / ".git").mkdir(parents=True)
    _fragment(checkouts["sushiruntime"] / "cli" / "sushistack.deps.toml", "v0.1.0", K_OLD)
    _fragment(checkouts["sushidsp"] / "cli" / "sushistack.deps.toml", "v0.1.0", K_OLD)
    return checkouts


@pytest.mark.small
def test_rewrite_changes_only_the_two_keys_of_the_table():
    """Comments and other tables stay as written."""
    text = ('# kept comment\n[sushisystems.sushilog]\nversion = "v0.1.0"\ncommit = "' + K_OLD + '"\n\n'
            '[sushisystems.sushiruntime]\nversion = "v0.1.0"\ncommit = "' + K_OLD + '"\n')
    rewritten = pins.rewrite_pin(text, "sushilog", "v0.2.0", K_NEW)
    assert rewritten == text.replace('version = "v0.1.0"\ncommit = "' + K_OLD, 'version = "v0.2.0"\ncommit = "' + K_NEW, 1)


@pytest.mark.small
def test_rewrite_renames_every_deprecated_table():
    """A fragment on [sushi.<name>] comes back on [sushisystems.<name>], every table of it."""
    text = ('[sushi.sushilog]\nversion = "v0.1.0"\ncommit = "' + K_OLD + '"\n\n'
            '[sushi.sushiruntime]\nversion = "v0.1.0"\ncommit = "' + K_OLD + '"\n')
    rewritten = pins.rewrite_pin(text, "sushilog", "v0.2.0", K_NEW)
    assert rewritten == ('[sushisystems.sushilog]\nversion = "v0.2.0"\ncommit = "' + K_NEW + '"\n\n'
                         '[sushisystems.sushiruntime]\nversion = "v0.1.0"\ncommit = "' + K_OLD + '"\n')


@pytest.mark.small
def test_a_fragment_without_the_table_is_refused():
    """Rewriting a pin the fragment does not hold is an error, not a silent no-op."""
    with pytest.raises(ValueError):
        pins.rewrite_pin('[module]\ndepends_on = []\n', "sushilog", "v0.2.0", K_NEW)


@pytest.mark.medium
def test_move_pin_rewrites_every_module_that_pins_the_library(two_modules, tmp_path):
    """Both pinning modules move at once; the third is untouched."""
    moved = pins.move_pin(tmp_path, "sushilog", "v0.2.0", K_NEW, dry_run=False)
    assert sorted(moved) == [("sushidsp", "v0.1.0"), ("sushiruntime", "v0.1.0")]
    for name in ("sushiruntime", "sushidsp"):
        text = (two_modules[name] / "cli" / "sushistack.deps.toml").read_text(encoding="utf-8")
        assert 'version = "v0.2.0"' in text and K_NEW in text and "# kept comment" in text


@pytest.mark.medium
def test_move_pin_neither_rewrites_nor_lists_a_fragment_already_at_the_target(two_modules, tmp_path):
    """A fragment on the target version and commit is skipped, and only the other one moves."""
    fragment = two_modules["sushidsp"] / "cli" / "sushistack.deps.toml"
    fragment.write_text(fragment.read_text(encoding="utf-8").replace("v0.1.0", "v0.2.0").replace(K_OLD, K_NEW),
                        encoding="utf-8")
    before = fragment.read_bytes()

    moved = pins.move_pin(tmp_path, "sushilog", "v0.2.0", K_NEW, dry_run=False)

    assert moved == [("sushiruntime", "v0.1.0")]
    assert fragment.read_bytes() == before


@pytest.mark.medium
def test_a_dry_run_lists_every_move(two_modules, tmp_path):
    """--dry-run still reports both modules that would move."""
    assert len(pins.move_pin(tmp_path, "sushilog", "v0.2.0", K_NEW, dry_run=True)) == 2


@pytest.mark.medium
def test_a_dry_run_writes_nothing(two_modules, tmp_path):
    """--dry-run leaves every fragment as it was."""
    pins.move_pin(tmp_path, "sushilog", "v0.2.0", K_NEW, dry_run=True)
    text = (two_modules["sushiruntime"] / "cli" / "sushistack.deps.toml").read_text(encoding="utf-8")
    assert 'version = "v0.1.0"' in text


@pytest.mark.medium
def test_pin_refuses_a_short_commit(two_modules):
    """A commit that is not 40 hex characters stops the command before any rewrite."""
    assert pins.pin("sushilog", "v0.2.0", "abc123", dry_run=False) == 1


@pytest.mark.medium
def test_pin_reads_the_commit_from_the_tag_when_none_is_given(two_modules, monkeypatch):
    """Without --commit, the tag's commit comes from the repository."""
    monkeypatch.setattr(pins, "tag_commit", lambda repo, version: K_NEW)
    assert pins.pin("sushilog", "v0.2.0", None, dry_run=False) == 0
    text = (two_modules["sushidsp"] / "cli" / "sushistack.deps.toml").read_text(encoding="utf-8")
    assert K_NEW in text


@pytest.mark.medium
def test_pin_fails_when_the_tag_is_not_found(two_modules, monkeypatch):
    """An unknown tag names the repository and the --commit way out."""
    monkeypatch.setattr(pins, "tag_commit", lambda repo, version: None)
    assert pins.pin("sushilog", "v9.9.9", None, dry_run=False) == 1
