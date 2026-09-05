"""How a module is present on disk, read from the markers a workspace carries."""

import json

import sushicore.profile

from sushistack.services import presence
from sushistack.services.presence import Presence


def binary_install(path, version: str = "1.4.2") -> None:
    """Unpack a fake binary install at *path*: a directory and a release manifest."""
    path.mkdir(parents=True, exist_ok=True)
    (path / presence.RELEASE_MANIFEST).write_text(
        json.dumps({"product": path.name, "version": version,
                    "platform": "windows-x64",
                    "bundled": {"sushiruntime": "0.9.0"},
                    "signature": "base64"}),
        encoding="utf-8")


def checkout(path) -> None:
    """Make *path* look like a git checkout."""
    (path / ".git").mkdir(parents=True)


def test_the_manifest_name_is_the_one_sushicore_looks_for():
    assert presence.RELEASE_MANIFEST == sushicore.profile.RELEASE_MANIFEST


def test_read_release_reads_product_version_and_platform(tmp_path):
    binary_install(tmp_path / "sushiengine")
    release = presence.read_release(tmp_path / "sushiengine")
    assert release == presence.Release("sushiengine", "1.4.2", "windows-x64")


def test_read_release_is_none_without_a_manifest(tmp_path):
    assert presence.read_release(tmp_path) is None


def test_read_release_is_none_when_the_manifest_is_not_json(tmp_path):
    (tmp_path / presence.RELEASE_MANIFEST).write_text("{ not json", encoding="utf-8")
    assert presence.read_release(tmp_path) is None


def test_read_release_is_none_when_a_field_is_missing(tmp_path):
    (tmp_path / presence.RELEASE_MANIFEST).write_text(
        json.dumps({"product": "sushiengine"}), encoding="utf-8")
    assert presence.read_release(tmp_path) is None


def test_a_directory_with_the_manifest_is_binary(tmp_path):
    binary_install(tmp_path / "sushiengine")
    assert presence.presence_of(tmp_path, "sushiengine", {}) is Presence.BINARY


def test_a_directory_with_git_is_cloned(tmp_path):
    checkout(tmp_path / "sushiengine")
    assert presence.presence_of(tmp_path, "sushiengine", {}) is Presence.CLONED


def test_a_directory_that_is_not_there_is_absent(tmp_path):
    assert presence.presence_of(tmp_path, "sushiengine", {}) is Presence.ABSENT


def test_a_linked_checkout_is_linked(tmp_path):
    elsewhere = tmp_path / "work" / "sushiengine"
    checkout(elsewhere)
    linked = {"sushiengine": str(elsewhere)}
    assert presence.presence_of(tmp_path, "sushiengine", linked) is Presence.LINKED


def test_a_linked_path_without_a_checkout_is_absent(tmp_path):
    linked = {"sushiengine": str(tmp_path / "gone")}
    assert presence.presence_of(tmp_path, "sushiengine", linked) is Presence.ABSENT


def test_describe_names_the_version_of_a_binary_install(tmp_path):
    binary_install(tmp_path / "sushiengine", version="2.0.0")
    assert presence.describe(tmp_path, "sushiengine", {}) == ("sushiengine", "binary 2.0.0")


def test_describe_falls_back_to_the_bare_form_for_a_broken_manifest(tmp_path):
    (tmp_path / "sushiengine").mkdir()
    (tmp_path / "sushiengine" / presence.RELEASE_MANIFEST).write_text(
        "{ not json", encoding="utf-8")
    assert presence.describe(tmp_path, "sushiengine", {}) == ("sushiengine", "binary")


def test_describe_gives_the_directory_for_a_clone_and_an_absence(tmp_path):
    checkout(tmp_path / "sushiengine")
    assert presence.describe(tmp_path, "sushiengine", {}) == ("sushiengine", "cloned")
    assert presence.describe(tmp_path, "sushiai", {}) == ("sushiai", "absent")


def test_describe_gives_the_path_for_a_link_and_says_when_it_is_gone(tmp_path):
    elsewhere = tmp_path / "work" / "sushiengine"
    checkout(elsewhere)
    linked = {"sushiengine": str(elsewhere), "sushiai": str(tmp_path / "gone")}
    assert presence.describe(tmp_path, "sushiengine", linked) == (str(elsewhere), "linked")
    assert presence.describe(tmp_path, "sushiai", linked) == (
        str(tmp_path / "gone"), "linked (missing)")
