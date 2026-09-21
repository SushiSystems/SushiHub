"""How a module is present in the workspace, read from what is on disk.

Presence is never recorded, only observed. A module directory holding
``sushi-release.json`` is an unpacked binary install, one holding ``.git`` is a
checkout, and a path in ``modules.local.toml`` is a link. Every command that
used to ask whether ``.git`` is there asks this module instead, so the four
forms are decided in one place and worded the same everywhere.

The layout rule this reads by is the workspace's own: a module named
``sushiengine`` lives at ``<workspace>/sushiengine``, whether it was cloned or
unpacked. See docs/agent/specs/2026-09-05-hub-design.md, §5.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

from .catalog import CATALOG

#: File the release build writes at the root of an unpacked binary install.
#: The same name as :data:`sushicore.profile.RELEASE_MANIFEST`, which is how a
#: module's own CLI finds a binary root; cli/tests/test_presence.py pins the two
#: together so neither can drift.
RELEASE_MANIFEST = "sushi-release.json"


class Presence(str, Enum):
    """The forms a module takes in a workspace."""

    CLONED = "cloned"
    LINKED = "linked"
    BINARY = "binary"
    ABSENT = "absent"


@dataclass(frozen=True)
class Release:
    """What the release manifest says about an unpacked install."""

    product: str
    version: str
    platform: str


def read_release(root: Path) -> Release | None:
    """Read the release manifest at *root*.

    Args:
        root: Directory a release was unpacked into.

    Returns:
        The product, version and platform the manifest names, or None when the
        file is absent, is not JSON, or leaves one of the three out. The
        bundled versions and the signature are wave 5's; nothing reads them yet.
    """
    try:
        doc = json.loads((root / RELEASE_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict):
        return None
    fields = {key: doc.get(key) for key in ("product", "version", "platform")}
    if not all(isinstance(value, str) and value for value in fields.values()):
        return None
    return Release(**fields)


def is_binary(root: Path) -> bool:
    """Report whether the directory at *root* holds an unpacked binary install."""
    return (root / RELEASE_MANIFEST).is_file()


def module_dir(root: Path, name: str, linked: Mapping[str, str] | None = None) -> Path:
    """Return the directory module *name* occupies.

    Its linked path wins when there is one. Otherwise the catalog's own
    ``directory`` field decides, so a module whose directory differs from its
    name still resolves; a name the catalog does not know (a stale link this
    machine still carries, to a module dropped from the stack) falls back to
    ``root / name`` rather than raising, so a caller like `hub status` keeps
    treating it as absent instead of crashing.

    Args:
        root: Workspace root.
        name: Module name.
        linked: Module name to path, as ``hub link`` recorded it; empty when None.
    """
    target = (linked or {}).get(name)
    if target:
        return Path(target)
    if name in CATALOG:
        return root / CATALOG[name].directory
    return root / name


def presence_of(root: Path, name: str, linked: Mapping[str, str]) -> Presence:
    """Report how module *name* is present under the workspace at *root*.

    A linked module is present as the checkout it points at, and absent when
    that path holds none. A module inside the workspace is a binary install
    when its directory carries the release manifest, a clone when it carries
    ``.git``, and absent otherwise.

    Args:
        root: Workspace root.
        name: Module name, which is also its directory name under *root*.
        linked: Module name to path, as ``hub link`` recorded it.
    """
    where = module_dir(root, name, linked)
    if name in linked:
        return Presence.LINKED if (where / ".git").is_dir() else Presence.ABSENT
    if is_binary(where):
        return Presence.BINARY
    if (where / ".git").is_dir():
        return Presence.CLONED
    return Presence.ABSENT


def describe(root: Path, name: str, linked: Mapping[str, str]) -> tuple[str, str]:
    """Say where module *name* lives and what state it is in, as `hub status` shows it.

    Args:
        root: Workspace root.
        name: Module name.
        linked: Module name to path, as ``hub link`` recorded it.

    Returns:
        The location — the module's directory, or the linked path — and the
        state: ``binary 1.4.2``, ``cloned``, ``linked``, ``linked (missing)`` or
        ``absent``. A binary install whose manifest will not parse is still
        binary, and reports no version.
    """
    state = presence_of(root, name, linked)
    if name in linked:
        text = "linked" if state is Presence.LINKED else "linked (missing)"
        return str(module_dir(root, name, linked)), text
    if state is not Presence.BINARY:
        return name, state.value
    release = read_release(module_dir(root, name, linked))
    if release is None:
        return name, "binary"
    return name, f"binary {release.version}"
