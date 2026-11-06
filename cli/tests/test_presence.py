# test_presence.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How a module is present on disk, and what every `hub` command does about it."""

import json
from pathlib import Path

import pytest
import sushicore.profile
from sushicore.console_memory import RecordingConsole

from sushihub.services import modules, presence, status_report
from sushihub.services.identity import Account, ReleaseInfo
from sushihub.services.memory.account import InMemoryAccount
from sushihub.services.memory.git import InMemoryGit
from sushihub.services.memory.ports import memory_ports
from sushihub.services.presence import Presence
from sushihub.setup import dependency_source, steps
from sushihub.setup.pipeline import InstallContext

from .conftest import MemorySource, dep
from .support.console_text import printed
from .support.release_files import binary_install
from .support.workspace_files import workspace_at


def checkout(path) -> None:
    """Make *path* look like a git checkout."""
    (path / ".git").mkdir(parents=True)


@pytest.mark.medium
def test_a_manifest_under_the_name_sushicore_writes_is_read(tmp_path):
    """read_release finds the manifest under the file name sushicore's profile names."""
    (tmp_path / sushicore.profile.RELEASE_MANIFEST).write_text(
        json.dumps({"product": "sushiengine", "version": "1.4.2", "platform": "windows-x64"}),
        encoding="utf-8")
    assert presence.read_release(tmp_path) == presence.Release(
        "sushiengine", "1.4.2", "windows-x64")


@pytest.mark.small
def test_parse_release_reads_product_version_and_platform():
    """The three fields of a manifest's text become a Release."""
    text = json.dumps({"product": "sushiengine", "version": "1.4.2", "platform": "windows-x64"})
    assert presence.parse_release(text) == presence.Release("sushiengine", "1.4.2", "windows-x64")


@pytest.mark.medium
@pytest.mark.parametrize("manifest", [
    None,
    "{ not json",
    json.dumps({"product": "sushiengine"}),
], ids=["no manifest", "not json", "a field missing"])
def test_read_release_is_none_for_an_invalid_release(tmp_path, manifest):
    if manifest is not None:
        (tmp_path / presence.RELEASE_MANIFEST).write_text(manifest, encoding="utf-8")
    assert presence.read_release(tmp_path) is None


@pytest.mark.small
def test_module_dir_follows_the_catalog_directory():
    """A cataloged name resolves through CATALOG[name].directory, not the bare name."""
    assert presence.module_dir(Path("/work"), "sushiengine") == Path("/work") / "sushiengine"


@pytest.mark.small
def test_module_dir_prefers_a_link_over_the_catalog():
    """A linked path wins even for a name the catalog knows."""
    linked = {"sushiengine": "/elsewhere"}
    assert presence.module_dir(Path("/work"), "sushiengine", linked) == Path("/elsewhere")


@pytest.mark.small
def test_module_dir_falls_back_to_the_bare_name_for_a_name_the_catalog_lacks():
    """A name the catalog no longer lists resolves under the root without raising."""
    assert presence.module_dir(Path("/work"), "sushidsp") == Path("/work") / "sushidsp"


@pytest.mark.medium
def test_a_directory_with_the_manifest_is_binary(tmp_path):
    binary_install(tmp_path / "sushiengine")
    assert presence.presence_of(tmp_path, "sushiengine", {}) is Presence.BINARY


@pytest.mark.medium
def test_a_directory_with_git_is_cloned(tmp_path):
    checkout(tmp_path / "sushiengine")
    assert presence.presence_of(tmp_path, "sushiengine", {}) is Presence.CLONED


@pytest.mark.medium
def test_a_directory_that_is_not_there_is_absent(tmp_path):
    assert presence.presence_of(tmp_path, "sushiengine", {}) is Presence.ABSENT


@pytest.mark.medium
def test_a_linked_checkout_is_linked(tmp_path):
    elsewhere = tmp_path / "work" / "sushiengine"
    checkout(elsewhere)
    linked = {"sushiengine": str(elsewhere)}
    assert presence.presence_of(tmp_path, "sushiengine", linked) is Presence.LINKED


@pytest.mark.medium
def test_a_linked_path_without_a_checkout_is_absent(tmp_path):
    linked = {"sushiengine": str(tmp_path / "gone")}
    assert presence.presence_of(tmp_path, "sushiengine", linked) is Presence.ABSENT


@pytest.mark.medium
def test_describe_names_the_version_of_a_binary_install(tmp_path):
    binary_install(tmp_path / "sushiengine", version="2.0.0")
    assert presence.describe(tmp_path, "sushiengine", {}) == ("sushiengine", "binary 2.0.0")


@pytest.mark.medium
def test_describe_falls_back_to_the_bare_form_for_a_broken_manifest(tmp_path):
    (tmp_path / "sushiengine").mkdir()
    (tmp_path / "sushiengine" / presence.RELEASE_MANIFEST).write_text(
        "{ not json", encoding="utf-8")
    assert presence.describe(tmp_path, "sushiengine", {}) == ("sushiengine", "binary")


@pytest.mark.medium
def test_describe_gives_the_directory_for_a_clone(tmp_path):
    checkout(tmp_path / "sushiengine")
    assert presence.describe(tmp_path, "sushiengine", {}) == ("sushiengine", "cloned")


@pytest.mark.medium
def test_describe_gives_the_name_for_an_absence(tmp_path):
    assert presence.describe(tmp_path, "sushiai", {}) == ("sushiai", "absent")


@pytest.mark.medium
def test_describe_gives_the_path_for_a_link(tmp_path):
    elsewhere = tmp_path / "work" / "sushiengine"
    checkout(elsewhere)
    linked = {"sushiengine": str(elsewhere)}
    assert presence.describe(tmp_path, "sushiengine", linked) == (str(elsewhere), "linked")


@pytest.mark.medium
def test_describe_says_when_a_link_is_gone(tmp_path):
    linked = {"sushiai": str(tmp_path / "gone")}
    assert presence.describe(tmp_path, "sushiai", linked) == (
        str(tmp_path / "gone"), "linked (missing)")


def _row(payload: dict, name: str) -> dict:
    """The module row of *name* in a status payload."""
    return next(row for row in payload["modules"] if row["name"] == name)


@pytest.mark.medium
@pytest.mark.parametrize("name, expected", [
    ("sushiengine", {"presence": "binary", "version": "1.4.2", "state": "binary 1.4.2"}),
    ("sushiruntime", {"presence": "cloned", "version": None}),
    ("sushiai", {"presence": "absent"}),
])
def test_status_rows_carry_the_presence_and_the_version(tmp_path, monkeypatch, name, expected):
    root = workspace_at(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    checkout(root / "sushiruntime")
    row = _row(status_report.build_status(home=tmp_path).payload, name)
    assert {key: row[key] for key in expected} == expected


@pytest.mark.medium
def test_update_refreshes_a_binary_module_through_sushi_id(tmp_path, monkeypatch):
    root = workspace_at(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    release = ReleaseInfo("1.4.2", "linux-x64", "https://cdn.test/e.zip", "00", 3, "")
    account = InMemoryAccount(Account("acc-1", "ada@example.com", ()), signed_in=True,
                              releases={("sushiengine", "linux-x64"): release})
    git, out = InMemoryGit(), RecordingConsole()
    ports = memory_ports(console=out, git=git, account=account)
    assert modules.update(["sushiengine"], ports=ports) == 0
    assert git.calls == []
    assert "sushiengine: binary 1.4.2 is the latest release." in out.texts("info")


@pytest.mark.medium
def test_readiness_says_a_binary_module_has_nothing_to_build(tmp_path, monkeypatch, fake_cfg, out):
    root = workspace_at(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    source = MemorySource([dep("cmake"), dep("vulkan", "sushiengine")])
    steps.report_readiness(source, InstallContext(cfg=fake_cfg), source.all(), out)
    assert printed(out, "sushiengine: binary 1.4.2, nothing to build")


def _write_fragment(root, module: str) -> None:
    """Write a dependency fragment into *module*'s folder under *root*."""
    fragment = root / module / dependency_source.MODULE_MANIFEST_REL
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text("[vulkan]\ndescription = \"test\"\n", encoding="utf-8")


@pytest.mark.medium
def test_a_binary_module_contributes_no_dependency_fragment(tmp_path, monkeypatch):
    root = workspace_at(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    checkout(root / "sushiruntime")
    _write_fragment(root, "sushiengine")
    _write_fragment(root, "sushiruntime")
    owners = {owner for _, owner in dependency_source.manifest_sources()}
    assert owners & {"sushiruntime", "sushiengine"} == {"sushiruntime"}
