# dependency_source.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Finds the dependency fragments of a workspace and reads them for the current platform.

The sources are sushicore's base fragment, ``sushihub/manifests/*.deps.toml`` and each
module's ``cli/sushistack.deps.toml``. Merging is :mod:`sushicore.provision.fragments`'s,
re-exported here. See cli/README.md, "Notes on the source".
"""

from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterator

from sushicore import deps_fragment
from sushicore.provision import manifests
from sushicore.provision.fragments import (  # noqa: F401
    Dependency,
    IDependencySource,
    SHARED_OWNER,
    TomlDependencySource as _CoreSource,
    _parse_manifest,
)

from ..config import find_workspace_root
from ..services import links
from ..services.presence import is_binary

#: Path, relative to a module's repo root, of the fragment it contributes.
MODULE_MANIFEST_REL = Path("cli") / "sushistack.deps.toml"

#: The package directory holding the dependency fragments every workspace shares.
MANIFESTS_DIR = "manifests"

#: Suffix every shipped fragment's filename carries; what precedes it names the owner.
SHIPPED_MANIFEST_SUFFIX = ".deps.toml"

#: The reserved fragment table for module metadata; owned by :mod:`sushicore.deps_fragment`.
MODULE_META_TABLE = deps_fragment.MODULE_TABLE


def _owner_for_shipped(path: Path) -> str:
    """Name the component a fragment this package ships belongs to.

    Every fragment hub ships belongs to the component its filename names, so
    ``gui.deps.toml`` is the desktop application's alone. That keeps a
    component's ports out of the shared set every module reads.

    Args:
        path: A fragment under the package's ``manifests/`` directory.

    Returns:
        The owner label the dependencies read from *path* carry.
    """
    if path.name.endswith(SHIPPED_MANIFEST_SUFFIX):
        return path.name[: -len(SHIPPED_MANIFEST_SUFFIX)]
    return path.stem


@contextmanager
def packaged_manifests() -> Iterator[Path]:
    """Yield a real filesystem path to the ``manifests/`` directory this package ships.

    @pre The path is valid only inside the ``with`` block, because
        ``importlib.resources`` may have extracted it.
    """
    with as_file(files("sushihub") / MANIFESTS_DIR) as path:
        yield path


def manifest_sources() -> list[tuple[Path, str]]:
    """Every dependency fragment plus the module that owns it.

    Each entry is ``(path, owner)``. sushicore's base fragment comes first, owned
    by :data:`SHARED_OWNER`; a fragment this package ships is owned as
    :func:`_owner_for_shipped` says; a module's ``cli/sushistack.deps.toml`` is
    owned by the module's directory name. Shipped fragments are sorted, then
    come the modules in the workspace, then linked external checkouts.

    A binary install is skipped: the release carries the libraries it was built
    against, so a fragment left in its tree declares nothing this workspace has
    to provision.
    """
    sources: list[tuple[Path, str]] = [(manifests.base_fragment(), manifests.BASE_OWNER)]
    with packaged_manifests() as manifests_dir:
        sources.extend((p, _owner_for_shipped(p))
                       for p in sorted(manifests_dir.glob("*" + SHIPPED_MANIFEST_SUFFIX)))
    root = find_workspace_root()
    if root is not None:
        for module in sorted(p for p in root.iterdir() if p.is_dir()):
            if is_binary(module):
                continue
            fragment = module / MODULE_MANIFEST_REL
            if fragment.is_file():
                sources.append((fragment, module.name))
    # A module linked from outside the workspace tree contributes its fragment too.
    seen = {p for p, _ in sources}
    for name, module_path in links.registered().items():
        fragment = Path(module_path) / MODULE_MANIFEST_REL
        if fragment.is_file() and fragment not in seen:
            sources.append((fragment, name))
            seen.add(fragment)
    return sources


def manifest_paths() -> list[Path]:
    """Every dependency-fragment file the installer should aggregate."""
    return [p for p, _ in manifest_sources()]


class TomlDependencySource(_CoreSource):
    """Hub's source: the core source fed the workspace-wide manifest list."""

    def __init__(self, sources: list[tuple[Path, str]] | None = None) -> None:
        """Default to every manifest the workspace carries."""
        super().__init__(manifest_sources() if sources is None else sources)
