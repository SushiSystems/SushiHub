"""Turning a resolved release into an unpacked module directory."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import zipfile

import pytest

from sushihub.services import releases
from sushihub.services.presence import RELEASE_MANIFEST, Release
from sushihub.services.releases import ReleaseCorrupt

from .test_identity import fake_id  # noqa: F401  the fake Sushi Account server fixture
from .test_identity import _signed_in

MANIFEST = {"product": "sushiengine", "version": "1.4.2", "platform": "windows-x64",
            "bundled": {"sushiruntime": "0.9.0"}, "signature": "base64"}


def zip_bytes(members: dict[str, str]) -> bytes:
    """Build a zip archive in memory out of a name-to-text map."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for name, text in members.items():
            bundle.writestr(name, text)
    return buffer.getvalue()


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


def release_members(**overrides) -> dict[str, str]:
    """The members a well-formed release archive carries."""
    return {RELEASE_MANIFEST: json.dumps({**MANIFEST, **overrides}),
            "bin/se.txt": "the engine"}


class Body(io.BytesIO):
    """A response body of known length, as :func:`urllib.request.urlopen` returns one."""

    def __init__(self, payload: bytes, *, declare_length: bool = True) -> None:
        """Hold *payload*, declaring its length unless the caller says not to."""
        super().__init__(payload)
        self.headers = {"Content-Length": str(len(payload))} if declare_length else {}


class ConsoleSpy:
    """Stands in for the console and keeps every progress event it was given."""

    def __init__(self) -> None:
        """Start with no recorded events."""
        self.events: list[tuple] = []
        self.lines: list[str] = []

    def progress(self, label, index, count, fraction=None) -> None:
        """Record one progress event."""
        self.events.append((label, index, count, fraction))

    def __getattr__(self, name):
        """Record any other console call as a printed line."""
        def record(*args, **kwargs) -> None:
            self.lines.extend(str(a) for a in args)
        return record


def test_host_platform_names_windows_x64(monkeypatch):
    monkeypatch.setattr(releases.platform, "system", lambda: "Windows")
    monkeypatch.setattr(releases.platform, "machine", lambda: "AMD64")
    assert releases.host_platform() == "windows-x64"


def test_host_platform_names_linux_x64(monkeypatch):
    monkeypatch.setattr(releases.platform, "system", lambda: "Linux")
    monkeypatch.setattr(releases.platform, "machine", lambda: "x86_64")
    assert releases.host_platform() == "linux-x64"


def test_host_platform_passes_a_machine_it_does_not_rename_through(monkeypatch):
    monkeypatch.setattr(releases.platform, "system", lambda: "Linux")
    monkeypatch.setattr(releases.platform, "machine", lambda: "riscv64")
    assert releases.host_platform() == "linux-riscv64"


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


def test_unpack_extracts_a_zip(tmp_path):
    (tmp_path / "a.zip").write_bytes(zip_bytes(release_members()))
    releases.unpack(tmp_path / "a.zip", tmp_path / "out")
    assert (tmp_path / "out" / "bin" / "se.txt").read_text(encoding="utf-8") == "the engine"
    assert json.loads((tmp_path / "out" / RELEASE_MANIFEST).read_text(
        encoding="utf-8"))["version"] == "1.4.2"


def test_unpack_extracts_a_tar_gz(tmp_path):
    (tmp_path / "a.tar.gz").write_bytes(tar_bytes(release_members()))
    releases.unpack(tmp_path / "a.tar.gz", tmp_path / "out")
    assert (tmp_path / "out" / "bin" / "se.txt").read_text(encoding="utf-8") == "the engine"


def test_unpack_refuses_a_member_that_escapes_the_directory(tmp_path):
    (tmp_path / "a.zip").write_bytes(
        zip_bytes({**release_members(), "../escaped.txt": "no"}))
    with pytest.raises(ReleaseCorrupt, match="escaped.txt"):
        releases.unpack(tmp_path / "a.zip", tmp_path / "out")
    assert not (tmp_path / "escaped.txt").exists()


def test_unpack_refuses_a_tar_member_that_escapes_the_directory(tmp_path):
    (tmp_path / "a.tar.gz").write_bytes(
        tar_bytes({**release_members(), "../escaped.txt": "no"}))
    with pytest.raises(ReleaseCorrupt, match="escaped.txt"):
        releases.unpack(tmp_path / "a.tar.gz", tmp_path / "out")
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


def test_install_release_unpacks_it_and_returns_the_manifest(fake_id, tmp_path):
    fake_id.state.release_blob = zip_bytes(release_members())
    console = ConsoleSpy()
    release = releases.install_release(
        "sushiengine", tmp_path / "sushiengine", _signed_in(fake_id), console)
    assert release == Release("sushiengine", "1.4.2", "windows-x64")
    assert (tmp_path / "sushiengine" / "bin" / "se.txt").is_file()
    assert list(tmp_path.iterdir()) == [tmp_path / "sushiengine"]


def test_install_release_reports_the_download_as_progress(fake_id, tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "CHUNK", 64)
    blob = zip_bytes(release_members())
    fake_id.state.release_blob = blob
    console = ConsoleSpy()
    releases.install_release("sushiengine", tmp_path / "sushiengine",
                             _signed_in(fake_id), console)
    assert console.events, "the download reported nothing"
    assert {label for label, *_ in console.events} == {releases.DOWNLOAD_LABEL}
    assert console.events[-1][1:] == (len(blob), len(blob), 1.0)


def test_install_release_asks_for_this_machines_platform(fake_id, tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "host_platform", lambda: "linux-x64")
    fake_id.state.release_blob = zip_bytes(release_members(platform="linux-x64"))
    releases.install_release("sushiengine", tmp_path / "sushiengine",
                             _signed_in(fake_id), ConsoleSpy())
    assert fake_id.state.resolved[-1] == {"product": "sushiengine",
                                          "platform": "linux-x64"}


def test_install_release_keeps_the_old_install_when_the_hash_does_not_match(
        fake_id, tmp_path):
    root = tmp_path / "sushiengine"
    root.mkdir()
    (root / RELEASE_MANIFEST).write_text(json.dumps({**MANIFEST, "version": "1.0.0"}),
                                         encoding="utf-8")
    fake_id.state.release_blob = zip_bytes(release_members())
    fake_id.state.release_sha256 = "0" * 64
    with pytest.raises(ReleaseCorrupt):
        releases.install_release("sushiengine", root, _signed_in(fake_id), ConsoleSpy())
    assert json.loads((root / RELEASE_MANIFEST).read_text(
        encoding="utf-8"))["version"] == "1.0.0"
    assert list(tmp_path.iterdir()) == [root]


def test_install_release_replaces_an_older_install(fake_id, tmp_path):
    root = tmp_path / "sushiengine"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "gone.txt").write_text("old", encoding="utf-8")
    (root / RELEASE_MANIFEST).write_text(json.dumps({**MANIFEST, "version": "1.0.0"}),
                                         encoding="utf-8")
    fake_id.state.release_blob = zip_bytes(release_members())
    release = releases.install_release("sushiengine", root, _signed_in(fake_id),
                                       ConsoleSpy())
    assert release.version == "1.4.2"
    assert not (root / "bin" / "gone.txt").exists()
    assert list(tmp_path.iterdir()) == [root]
