"""Turning a release Sushi Account resolved into an unpacked module directory.

Four steps in order: resolve, download, verify, unpack. Each is a function of
its own so a test can run it alone, and :func:`install_release` is the only one
that knows the order. The archive is unpacked into a temporary directory beside
the module's own and moved over it last, so a download that fails leaves the
install that was there untouched.

The shapes this reads are in ``contract/sushi-account.md``; the reason a
binary install exists at all is docs/agent/specs/2026-09-05-hub-design.md, §5.
"""

from __future__ import annotations

import hashlib
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

from .identity import ReleaseInfo, SushiAccount
from .presence import RELEASE_MANIFEST, Release, read_release

# How much of the body is read at a time, and so how often progress is reported.
CHUNK = 1 << 20

# The label every progress event of a download carries.
DOWNLOAD_LABEL = "download"

# How long one read of the download may stall before it is abandoned, in seconds.
TIMEOUT = 60.0

# The machine names Sushi Account knows under another spelling.
_ARCHITECTURES = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}


class ReleaseCorrupt(RuntimeError):
    """A downloaded release is not the one Sushi Account described."""


def host_platform() -> str:
    """Return the platform string a release is named by on this machine.

    Returns:
        ``windows-x64`` or ``linux-x64`` on the two platforms sushiengine ships
        for, and the system and machine joined by a hyphen anywhere else, which
        Sushi Account answers with ``no_release``.
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    return f"{system}-{_ARCHITECTURES.get(machine, machine)}"


def download(url: str, dest: Path, *,
             on_progress: Callable[[int, int], None] | None = None,
             http: Callable = urllib.request.urlopen) -> int:
    """Stream *url* into *dest* and return how many bytes arrived.

    Args:
        url: Where to read from.
        dest: The file to write; its parent directory must exist.
        on_progress: Called after every chunk with the bytes written so far and
            the total the response declares, zero when it declares none.
        http: What opens *url*; the seam a test replaces.
    """
    with http(url, timeout=TIMEOUT) as response:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        with dest.open("wb") as out:
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if on_progress is not None:
                    on_progress(done, total)
    return done


def verify(path: Path, sha256: str, size: int) -> None:
    """Check the file at *path* against the size and digest Sushi Account declared.

    Args:
        path: The downloaded archive.
        sha256: The digest the resolver named, in lower-case hexadecimal.
        size: The length in bytes the resolver named.

    Raises:
        ReleaseCorrupt: One of the two differs; the message names which.
    """
    measured = path.stat().st_size
    if measured != size:
        raise ReleaseCorrupt(
            f"{path.name}: the size is {measured} bytes, not the {size} Sushi Account declared.")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    if digest.hexdigest() != sha256:
        raise ReleaseCorrupt(
            f"{path.name}: the sha256 is {digest.hexdigest()}, not the {sha256} "
            "Sushi Account declared.")


def unpack(archive: Path, into: Path) -> None:
    """Extract *archive* into *into*, refusing anything that does not belong.

    Args:
        archive: A ``.zip`` or a ``.tar.gz``, named as the download left it.
        into: The directory to extract into, created when it is not there.

    Raises:
        ReleaseCorrupt: The suffix is neither, a member would be written outside
            *into*, or the result carries no release manifest at its top level.
    """
    into.mkdir(parents=True, exist_ok=True)
    name = archive.name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            _refuse_escapes(bundle.namelist(), into)
            bundle.extractall(into)
    elif name.endswith(".tar.gz") or name.endswith(".tgz"):
        with tarfile.open(archive, "r:gz") as bundle:
            _refuse_escapes([member.name for member in bundle.getmembers()], into)
            _extract_tar(bundle, into)
    else:
        raise ReleaseCorrupt(f"{archive.name}: not a .zip or a .tar.gz.")
    if not (into / RELEASE_MANIFEST).is_file():
        raise ReleaseCorrupt(
            f"{archive.name}: carries no {RELEASE_MANIFEST} at its top level.")


def install_release(name: str, root: Path, client: SushiAccount, console, *,
                    info: ReleaseInfo | None = None,
                    http: Callable = urllib.request.urlopen) -> Release:
    """Resolve, download, verify and unpack a release of *name* at *root*.

    Args:
        name: The module, which is also the product slug Sushi Account knows.
        root: The directory the module occupies in the workspace.
        client: A Sushi Account client with a live session.
        console: Where the download's progress events go.
        info: The release to install; the latest one, resolved through *client*,
            when None.
        http: What opens the download URL; the seam a test replaces.

    Returns:
        The release manifest the unpacked install carries.

    Raises:
        ReleaseCorrupt: The download does not match what was declared, or the
            archive is not a release.
        SushiAccountError: Sushi Account refused to resolve a release for this account.
    """
    info = info or client.resolve_release(name, host_platform())
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=root.parent))
    try:
        archive = staging / _archive_name(name, info)
        download(info.url, archive, http=http,
                 on_progress=lambda done, total: _report(console, done, total or info.size))
        verify(archive, info.sha256, info.size)
        unpacked = staging / name
        unpack(archive, unpacked)
        archive.unlink()
        _replace(root, unpacked)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    release = read_release(root)
    if release is None:
        raise ReleaseCorrupt(f"{name}: the {RELEASE_MANIFEST} at {root} will not parse.")
    return release


def _report(console, done: int, total: int) -> None:
    """Emit one download progress event, with a fraction when the total is known."""
    console.progress(DOWNLOAD_LABEL, done, total, done / total if total else None)


def _archive_name(name: str, info: ReleaseInfo) -> str:
    """Return the file name to download into, which is what decides the format.

    Args:
        name: The module the release belongs to.
        info: What the resolver answered.

    Returns:
        The last segment of the URL's path, or ``<name>-<version>.zip`` when the
        URL carries no path to take one from.
    """
    return Path(urlparse(info.url).path).name or f"{name}-{info.version}.zip"


def _refuse_escapes(names: Iterable[str], into: Path) -> None:
    """Refuse a member whose path leaves *into* once resolved.

    Args:
        names: Every member name the archive lists.
        into: The directory the members must stay inside.

    Raises:
        ReleaseCorrupt: One member resolves outside *into*.
    """
    root = into.resolve()
    for name in names:
        target = (root / name).resolve()
        if target != root and root not in target.parents:
            raise ReleaseCorrupt(f"{name}: this member would be written outside {into}.")


def _extract_tar(bundle: tarfile.TarFile, into: Path) -> None:
    """Extract *bundle* into *into*, as data alone where the runtime can."""
    if hasattr(tarfile, "data_filter"):
        bundle.extractall(into, filter="data")
    else:
        bundle.extractall(into)


def _replace(root: Path, unpacked: Path) -> None:
    """Move *unpacked* over *root*, keeping the earlier install until it lands.

    Args:
        root: Where the module lives; replaced whether or not it exists.
        unpacked: The verified install, a sibling of *root* so the move is a rename.

    Raises:
        OSError: The move failed; the earlier install is put back first.
    """
    previous = root.with_name(root.name + ".previous")
    shutil.rmtree(previous, ignore_errors=True)
    if root.exists():
        root.rename(previous)
    try:
        unpacked.rename(root)
    except OSError:
        if previous.exists():
            previous.rename(root)
        raise
    shutil.rmtree(previous, ignore_errors=True)
