"""How a module is present on disk, and what every `ss` command does about it."""

import json

import sushicore.profile

from sushistack.services import modules, presence
from sushistack.services.presence import Presence
from sushistack.setup import dependency_source, steps
from sushistack.setup.pipeline import InstallContext
from sushistack.setup.steps import DetectStep

from .conftest import MemorySource, dep


class Recorder:
    """Stands in for the console and keeps every line a step printed."""

    def __init__(self) -> None:
        """Start with no lines, and answer ``console.console`` with itself."""
        self.lines: list[str] = []
        self.console = self

    def __getattr__(self, name: str):
        """Return a call that records its first argument as a printed line."""
        def record(*args, **kwargs) -> None:
            self.lines.extend(str(a) for a in args)
        return record

    def said(self, text: str) -> bool:
        """Report whether any recorded line contains *text*."""
        return any(text in line for line in self.lines)


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


def workspace(tmp_path, monkeypatch):
    """Point every `ss` lookup at *tmp_path* and return it as the workspace root."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    return tmp_path


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


def test_status_rows_carry_the_presence_and_the_version(tmp_path, monkeypatch):
    root = workspace(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    checkout(root / "sushiruntime")
    rows = {row["name"]: row for row in modules.status_payload()["modules"]}
    assert rows["sushiengine"]["presence"] == "binary"
    assert rows["sushiengine"]["version"] == "1.4.2"
    assert rows["sushiengine"]["state"] == "binary 1.4.2"
    assert rows["sushiruntime"]["presence"] == "cloned"
    assert rows["sushiruntime"]["version"] is None
    assert rows["sushiai"]["presence"] == "absent"


def test_update_leaves_a_binary_module_to_ss_add(tmp_path, monkeypatch):
    root = workspace(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    pulled = []
    monkeypatch.setattr(modules, "_run_git", lambda args, cwd: pulled.append(cwd) or 0)
    recorder = Recorder()
    monkeypatch.setattr(modules, "console", recorder)
    assert modules.update(["sushiengine"]) == 0
    assert pulled == []
    assert recorder.said("sushiengine: binary 1.4.2; updates come through `ss add sushiengine`.")
    assert not recorder.said("No modules present yet")


def test_readiness_says_a_binary_module_has_nothing_to_build(tmp_path, monkeypatch, fake_cfg):
    root = workspace(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    source = MemorySource([dep("cmake"), dep("vulkan", "sushiengine")])
    step = DetectStep(source, managers=[],
                      toolchain_status=lambda cfg, gpu: [], gpu_vendor=lambda: "none")
    recorder = Recorder()
    monkeypatch.setattr(steps, "console", recorder)
    step._report_readiness(InstallContext(cfg=fake_cfg), source.all())
    assert recorder.said("sushiengine: binary 1.4.2, nothing to build")


def test_a_binary_module_contributes_no_dependency_fragment(tmp_path, monkeypatch):
    root = workspace(tmp_path, monkeypatch)
    binary_install(root / "sushiengine")
    checkout(root / "sushiruntime")
    for module in ("sushiengine", "sushiruntime"):
        fragment = root / module / dependency_source.MODULE_MANIFEST_REL
        fragment.parent.mkdir(parents=True, exist_ok=True)
        fragment.write_text("[vulkan]\ndescription = \"test\"\n", encoding="utf-8")
    owners = [owner for _, owner in dependency_source.manifest_sources()]
    assert "sushiruntime" in owners
    assert "sushiengine" not in owners
