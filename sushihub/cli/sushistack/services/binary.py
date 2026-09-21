"""The licence-and-session policy above a binary release: install, add, update.

Sits above :mod:`.releases`, which does the mechanics (download, verify,
unpack) and knows nothing about Sushi Account sessions or licences. This
module decides whether a session is live, what to tell the caller when it is
not, and writes the licence file once a release lands.
"""

from __future__ import annotations

from pathlib import Path

from .. import console
from . import licence_file, releases, session
from .catalog import CATALOG
from .identity import ReleaseInfo, SushiAccount, SushiAccountError
from .presence import read_release
from .releases import ReleaseCorrupt


def install(name: str, dest: Path, client: SushiAccount,
           info: ReleaseInfo | None = None) -> bool:
    """Unpack a release of *name* at *dest* and write its licence beside it.

    Args:
        name: The module, which is also the product slug Sushi Account knows.
        dest: Where the module lives in the workspace.
        client: A Sushi Account client with a live session.
        info: The release to install; the latest one when None.

    Returns:
        Whether both landed. A refusal from Sushi Account, a download that does not
        match what was declared and a directory that will not be written are all
        reported here and answered with False.
    """
    try:
        release = releases.install_release(name, dest, client, console, info=info)
        expires_at = licence_file.write_licence(dest, client, name)
    except (SushiAccountError, ReleaseCorrupt, OSError) as error:
        console.error(f"{name}: {error}")
        return False
    console.success(f"{name}: installed binary {release.version} ({release.platform}) "
                    f"at {dest}; licence valid to {expires_at}.")
    return True


def add(name: str, dest: Path, requested: bool) -> bool:
    """Install *name* from its release, having found no other way to bring it in.

    Args:
        name: The module to install.
        dest: Where the module lives in the workspace.
        requested: Whether the binary form was asked for with ``--binary``
            rather than chosen because the source is out of reach.

    Returns:
        Whether the module is installed afterwards.
    """
    client = session.client()
    if client.access_token() is None:
        if requested:
            console.error(f"{name}: a binary install needs a Sushi Account licence. "
                          "Run `hub login` first.")
        else:
            console.error(
                f"{name}: neither way in is open. The source needs a Git identity with "
                f"access to {CATALOG[name].repo}; the binary needs a licence, which "
                "`hub login` signs you in for.")
        return False
    return install(name, dest, client)


def update(name: str, dest: Path) -> bool:
    """Reinstall *name* when Sushi Account holds a release newer than the one at *dest*.

    Args:
        name: The module to refresh.
        dest: The unpacked install.

    Returns:
        Whether the install is the latest release afterwards. One that already
        was counts as success and downloads nothing.
    """
    client = session.client()
    if client.access_token() is None:
        console.error(f"{name}: a binary install is refreshed through Sushi Account. "
                      "Run `hub login` first.")
        return False
    try:
        info = client.resolve_release(name, releases.host_platform())
    except SushiAccountError as error:
        console.error(f"{name}: {error}")
        return False
    installed = read_release(dest)
    if installed is not None and installed.version == info.version:
        console.info(f"{name}: binary {installed.version} is the latest release.")
        return True
    was = installed.version if installed else "an unreadable install"
    console.info(f"{name}: {was} -> {info.version}; downloading.")
    return install(name, dest, client, info=info)
