# test_releases.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Turning a resolved release into an unpacked module directory."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import tarfile

import pytest
from sushicore.console_memory import RecordingConsole

from sushihub.errors import SushiAccountError
from sushihub.services import releases
from sushihub.services.presence import RELEASE_MANIFEST, Release
from sushihub.services.releases import ReleaseCorrupt

from .support.fake_account_server import signed_in
from .support.release_files import K_MANIFEST, release_members, zip_bytes

pytestmark = pytest.mark.medium

def tar_bytes(members: dict[str, str]) -> bytes:
    """Build a gzipped tar archive in memory out of a name-to-text map."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
        for name, text in members.items():
            blob = text.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            bundle.addfile(info, io.BytesIO(blob))
    return buffer.getvalue()


class Body(io.BytesIO):
    """A response body of known length, as :func:`urllib.request.urlopen` returns one."""

    def __init__(self, payload: bytes, *, declare_length: bool = True) -> None:
        """Hold *payload*, declaring its length unless the caller says not to."""
        super().__init__(payload)
        self.headers = {"Content-Length": str(len(payload))} if declare_length else {}


@pytest.mark.parametrize("system, machine, named", [
    ("Windows", "AMD64", "windows-x64"),
    ("Linux", "x86_64", "linux-x64"),
    ("Linux", "riscv64", "linux-riscv64"),
])
def test_host_platform_names_the_system_and_the_architecture(monkeypatch, system, machine, named):
    """The two shipped platforms get their release names; any other machine passes through."""
    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(platform, "machine", lambda: machine)
    assert releases.host_platform() == named


def test_download_writes_the_file_and_reports_each_chunk(tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "CHUNK", 4)
    payload = b"0123456789"
    seen: list[tuple[int, int]] = []
    written = releases.download(
        "http://127.0.0.1/x", tmp_path / "a.zip",
        on_progress=lambda done, total: seen.append((done, total)),
        http=lambda url, timeout=None: Body(payload))
    assert written == 10
    assert (tmp_path / "a.zip").read_bytes() == payload
    assert seen == [(4, 10), (8, 10), (10, 10)]


def test_download_reports_no_total_when_the_response_declares_none(tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "CHUNK", 8)
    seen: list[tuple[int, int]] = []
    releases.download("http://127.0.0.1/x", tmp_path / "a.zip",
                      on_progress=lambda done, total: seen.append((done, total)),
                      http=lambda url, timeout=None: Body(b"12345", declare_length=False))
    assert seen == [(5, 0)]


def test_verify_accepts_the_declared_size_and_digest(tmp_path):
    blob = b"a release"
    path = tmp_path / "a.zip"
    path.write_bytes(blob)
    releases.verify(path, hashlib.sha256(blob).hexdigest(), len(blob))


def test_verify_names_the_size_when_it_differs(tmp_path):
    path = tmp_path / "a.zip"
    path.write_bytes(b"a release")
    with pytest.raises(ReleaseCorrupt, match="size"):
        releases.verify(path, hashlib.sha256(b"a release").hexdigest(), 11)


def test_verify_names_the_digest_when_it_differs(tmp_path):
    path = tmp_path / "a.zip"
    path.write_bytes(b"a release")
    with pytest.raises(ReleaseCorrupt, match="sha256"):
        releases.verify(path, "0" * 64, 9)


@pytest.mark.parametrize("name, build", [("a.zip", zip_bytes), ("a.tar.gz", tar_bytes)])
def test_unpack_extracts_an_archive(tmp_path, name, build):
    """Both archive formats unpack their members, the manifest included."""
    (tmp_path / name).write_bytes(build(release_members()))
    releases.unpack(tmp_path / name, tmp_path / "out")
    assert (tmp_path / "out" / "bin" / "se.txt").read_text(encoding="utf-8") == "the engine"
    assert json.loads((tmp_path / "out" / RELEASE_MANIFEST).read_text(
        encoding="utf-8"))["version"] == "1.4.2"


@pytest.mark.parametrize("name, build", [("a.zip", zip_bytes), ("a.tar.gz", tar_bytes)])
def test_unpack_refuses_a_member_that_escapes_the_directory(tmp_path, name, build):
    """A member that resolves outside the directory is refused and written nowhere."""
    (tmp_path / name).write_bytes(build({**release_members(), "../escaped.txt": "no"}))
    with pytest.raises(ReleaseCorrupt, match="escaped.txt"):
        releases.unpack(tmp_path / name, tmp_path / "out")
    assert not (tmp_path / "escaped.txt").exists()


def test_unpack_refuses_an_archive_without_a_manifest_at_the_top(tmp_path):
    (tmp_path / "a.zip").write_bytes(
        zip_bytes({"sushiengine/" + RELEASE_MANIFEST: "{}"}))
    with pytest.raises(ReleaseCorrupt, match=RELEASE_MANIFEST):
        releases.unpack(tmp_path / "a.zip", tmp_path / "out")


def test_unpack_refuses_a_suffix_it_does_not_know(tmp_path):
    (tmp_path / "a.7z").write_bytes(b"not an archive we open")
    with pytest.raises(ReleaseCorrupt, match="a.7z"):
        releases.unpack(tmp_path / "a.7z", tmp_path / "out")


def _install(fake_id, tmp_path, console=None) -> Release:
    """Install sushiengine from the fake server into tmp_path and return its manifest."""
    return releases.install_release("sushiengine", tmp_path / "sushiengine",
                                    signed_in(fake_id), console or RecordingConsole())


def test_install_release_returns_the_manifest_it_unpacked(fake_id, tmp_path):
    """The returned release is the one the unpacked manifest names."""
    fake_id.state.release_blob = zip_bytes(release_members())
    assert _install(fake_id, tmp_path) == Release("sushiengine", "1.4.2", "windows-x64")


def test_install_release_unpacks_the_archive_at_root(fake_id, tmp_path):
    """The archive's members land under the module's directory."""
    fake_id.state.release_blob = zip_bytes(release_members())
    _install(fake_id, tmp_path)
    assert (tmp_path / "sushiengine" / "bin" / "se.txt").is_file()


def test_install_release_leaves_nothing_beside_root(fake_id, tmp_path):
    """The staging folder is gone once the install lands."""
    fake_id.state.release_blob = zip_bytes(release_members())
    _install(fake_id, tmp_path)
    assert list(tmp_path.iterdir()) == [tmp_path / "sushiengine"]


def test_install_release_reports_the_download_as_progress(fake_id, tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "CHUNK", 64)
    blob = zip_bytes(release_members())
    fake_id.state.release_blob = blob
    console = RecordingConsole()
    _install(fake_id, tmp_path, console)
    events = [call.args for call in console.calls if call.kind == "progress"]
    assert events, "the download reported nothing"
    assert {label for label, *_ in events} == {releases.DOWNLOAD_LABEL}
    assert events[-1][1:] == (len(blob), len(blob), 1.0)


def test_install_release_asks_for_this_machines_platform(fake_id, tmp_path, monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    fake_id.state.release_blob = zip_bytes(release_members(platform="linux-x64"))
    _install(fake_id, tmp_path)
    assert fake_id.state.resolved[-1] == {"product": "sushiengine",
                                          "platform": "linux-x64"}


def test_install_release_raises_the_refusal_and_leaves_nothing_beside_root(fake_id, tmp_path):
    """A refused resolve raises SushiAccountError before any download, and writes nothing."""
    fake_id.state.rate_limited = True
    with pytest.raises(SushiAccountError):
        _install(fake_id, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_install_release_keeps_the_old_install_when_the_hash_does_not_match(
        fake_id, tmp_path):
    root = tmp_path / "sushiengine"
    root.mkdir()
    (root / RELEASE_MANIFEST).write_text(json.dumps({**K_MANIFEST, "version": "1.0.0"}),
                                         encoding="utf-8")
    fake_id.state.release_blob = zip_bytes(release_members())
    fake_id.state.release_sha256 = "0" * 64
    with pytest.raises(ReleaseCorrupt):
        releases.install_release("sushiengine", root, signed_in(fake_id),
                                 RecordingConsole())
    assert json.loads((root / RELEASE_MANIFEST).read_text(
        encoding="utf-8"))["version"] == "1.0.0"
    assert list(tmp_path.iterdir()) == [root]


def test_install_release_replaces_an_older_install(fake_id, tmp_path):
    root = tmp_path / "sushiengine"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "gone.txt").write_text("old", encoding="utf-8")
    (root / RELEASE_MANIFEST).write_text(json.dumps({**K_MANIFEST, "version": "1.0.0"}),
                                         encoding="utf-8")
    fake_id.state.release_blob = zip_bytes(release_members())
    release = releases.install_release("sushiengine", root, signed_in(fake_id),
                                       RecordingConsole())
    assert release.version == "1.4.2"
    assert not (root / "bin" / "gone.txt").exists()
    assert list(tmp_path.iterdir()) == [root]
