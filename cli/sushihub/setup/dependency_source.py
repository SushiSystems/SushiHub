"""Dependency manifest reading; merging moved to :mod:`sushicore.provision.fragments`.

The installer must not hard-code package names. Instead it asks an
``IDependencySource`` for the packages relevant to the current platform.

SushiStack owns no single manifest. Each module declares what it needs, and the
installer aggregates those fragments into one shared dependency set:

  * ``sushihub/manifests/*.deps.toml`` — base fragments shipped inside this
    package (the module-independent build/toolchain infrastructure).
  * ``<module>/cli/sushistack.deps.toml`` — a fragment a module contributes from
    its own repo (kept under cli/, not the repo root).

Discovering those fragments is hub's own business (this module); merging what
they declare is :mod:`sushicore.provision.fragments`'s, re-exported here.
"""

from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterator

from sushicore import deps_fragment
from sushicore.provision.fragments import (  # noqa: F401
    Dependency,
    IDependencySource,
    SHARED_OWNER,
    TomlDependencySource as _CoreSource,
    _parse_manifest,
)

from ..config import workspace_root
from ..services import links
from ..services.presence import is_binary

#: Path, relative to a module's repo root, of the fragment it contributes.
MODULE_MANIFEST_REL = Path("cli") / "sushistack.deps.toml"

#: The package directory holding the dependency fragments every workspace shares.
MANIFESTS_DIR = "manifests"

#: Suffix every shipped fragment's filename carries; what precedes it names the owner.
SHIPPED_MANIFEST_SUFFIX = ".deps.toml"

#: Stem of the shipped fragment that belongs to no single component.
SHARED_MANIFEST_STEM = "base"

#: Reserved table name a fragment uses to declare module-level metadata
#: (currently ``depends_on``) rather than a dependency. Owned by
#: :mod:`sushicore.deps_fragment`, re-exported here for the callers that name it.
MODULE_META_TABLE = deps_fragment.MODULE_TABLE


def _owner_for_shipped(path: Path) -> str:
    """Name the component a shipped fragment belongs to.

    ``base.deps.toml`` is the infrastructure every module shares and is owned by
    :data:`SHARED_OWNER`; every other fragment this repository ships belongs to
    the component its filename names, so ``gui.deps.toml`` is the desktop
    application's alone. The distinction is what keeps a component's ports out
    of the shared set that decides which toolchains get provisioned.

    Args:
        path: A fragment under the package's ``manifests/`` directory.

    Returns:
        The owner label the dependencies read from *path* carry.
    """
    stem = path.name[: -len(SHIPPED_MANIFEST_SUFFIX)] if path.name.endswith(
        SHIPPED_MANIFEST_SUFFIX) else path.stem
    return SHARED_OWNER if stem == SHARED_MANIFEST_STEM else stem


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

    Each entry is ``(path, owner)``: a fragment this package ships is owned as
    :func:`_owner_for_shipped` says;
    a module's ``cli/sushistack.deps.toml`` is owned by the module's directory
    name. Shipped fragments come first (sorted, stable order), then modules in
    the workspace, then linked external checkouts.

    A binary install is skipped: the release carries the libraries it was built
    against, so a fragment left in its tree declares nothing this workspace has
    to provision.
    """
    sources: list[tuple[Path, str]] = []
    with packaged_manifests() as manifests_dir:
        sources.extend((p, _owner_for_shipped(p))
                       for p in sorted(manifests_dir.glob("*" + SHIPPED_MANIFEST_SUFFIX)))
    try:
        root = workspace_root()
    except SystemExit:
        root = None
    if root is not None:
        for module in sorted(p for p in root.iterdir() if p.is_dir()):
            if is_binary(module):
                continue
            fragment = module / MODULE_MANIFEST_REL
            if fragment.is_file():
                sources.append((fragment, module.name))
    # Modules linked to external checkouts (a developer's working repos that live
    # outside the workspace tree) contribute their fragment too.
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
