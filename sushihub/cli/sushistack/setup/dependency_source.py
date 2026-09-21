"""Dependency manifest reading.

The installer must not hard-code package names. Instead it asks an
``IDependencySource`` for the packages relevant to the current platform.

SushiStack owns no single manifest. Each module declares what it needs, and the
installer aggregates those fragments into one shared dependency set:

  * ``sushistack/manifests/*.deps.toml`` — base fragments shipped inside this
    package (the module-independent build/toolchain infrastructure).
  * ``<module>/cli/sushistack.deps.toml`` — a fragment a module contributes from
    its own repo (kept under cli/, not the repo root).

When two fragments declare the same dependency name the first one wins and a
warning is emitted, so the union stays predictable. Tests can inject an
in-memory source.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, replace
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterator

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib

from .. import console
from ..config import workspace_root
from ..services import links
from ..services.presence import is_binary

#: Path, relative to a module's repo root, of the fragment it contributes.
MODULE_MANIFEST_REL = Path("cli") / "sushistack.deps.toml"

#: Owner label for the base fragments this package ships — the build/toolchain
#: infrastructure every module shares, owned by no single module.
SHARED_OWNER = "shared"

#: The package directory holding the dependency fragments every workspace shares.
MANIFESTS_DIR = "manifests"

#: Suffix every shipped fragment's filename carries; what precedes it names the owner.
SHIPPED_MANIFEST_SUFFIX = ".deps.toml"

#: Stem of the shipped fragment that belongs to no single component.
SHARED_MANIFEST_STEM = "base"

#: Reserved table name a fragment uses to declare module-level metadata
#: (currently ``depends_on``) rather than a dependency.
MODULE_META_TABLE = "module"


@dataclass(frozen=True)
class Dependency:
    """One entry from the manifest, normalized."""

    name: str
    description: str
    required: bool
    gpu_only: bool
    linux_apt: list[str]
    windows_vcpkg: list[str]
    check_cmd: list[str]
    owner: str = SHARED_OWNER  # which module contributed this dependency
    provides: str = ""  # capability tag; deps sharing one are any-of alternatives

    def packages_for(self, platform: str) -> list[str]:
        """Package names for the given platform ('windows' | other = linux)."""
        return self.windows_vcpkg if platform == "windows" else self.linux_apt

    def vcpkg_fallback_ports(self, platform: str) -> list[str]:
        """Vcpkg ports to install on Linux when this dep has no apt package.

        vcpkg port names are the same cross-platform, so ``windows_vcpkg`` also
        names the Linux ports for a library that ships no apt package at all
        (``linux_apt = []`` in the manifest, e.g. vk-bootstrap, cgltf) — without
        this, such a dependency is silently unprovisionable on Linux. Empty
        on Windows (windows_vcpkg is already the primary path there) and empty
        whenever an apt package exists (apt is the native, preferred route).
        """
        if platform == "windows" or self.linux_apt:
            return []
        return self.windows_vcpkg


def _merge_ports(first: list[str], second: list[str]) -> list[str]:
    """Union two package lists, keeping one entry per port with all its features.

    A vcpkg port carries its feature set in brackets, so ``sdl2`` and
    ``sdl2[vulkan]`` name one port at two strengths. Taking either alone would
    drop a feature a module needs; the union keeps both.

    Returns:
        The ports in the order first met, each carrying every feature either
        list asked for.
    """
    features: dict[str, list[str]] = {}
    for port in [*first, *second]:
        name, _, rest = port.partition("[")
        wanted = [f.strip() for f in rest.rstrip("]").split(",") if f.strip()]
        for feature in wanted:
            if feature not in features.setdefault(name, []):
                features[name].append(feature)
        features.setdefault(name, [])
    return [name + (f"[{','.join(f)}]" if f else "") for name, f in features.items()]


def _merge(existing: Dependency, incoming: Dependency) -> tuple[Dependency, str]:
    """Combine two declarations of one dependency without losing either.

    Modules declare what they need, not what the workspace installs, so two
    modules naming the same dependency differently are both right. The merge
    takes the stronger of every field: required if either requires it, every
    package either asks for, and GPU-only only when both say so. Ownership goes
    to the first module that required it, because that is the module whose
    absence would make the dependency unnecessary.

    Returns:
        The merged dependency, and a warning to print when a field could not be
        merged and one had to be chosen; empty when nothing was lost.
    """
    lost = []
    for field in ("check_cmd", "provides"):
        one, two = getattr(existing, field), getattr(incoming, field)
        if one and two and one != two:
            lost.append(field)
    owner = existing.owner
    if incoming.required and not existing.required:
        owner = incoming.owner
    merged = replace(
        existing,
        owner=owner,
        description=existing.description or incoming.description,
        required=existing.required or incoming.required,
        gpu_only=existing.gpu_only and incoming.gpu_only,
        linux_apt=_merge_ports(existing.linux_apt, incoming.linux_apt),
        windows_vcpkg=_merge_ports(existing.windows_vcpkg, incoming.windows_vcpkg),
        check_cmd=existing.check_cmd or incoming.check_cmd,
        provides=existing.provides or incoming.provides,
    )
    if not lost:
        return merged, ""
    return merged, (
        f"{existing.owner} and {incoming.owner} declare '{existing.name}' with different "
        f"{' and '.join(lost)}; {existing.owner}'s is the one used.")


class IDependencySource(ABC):
    """Source of the dependency list. Abstraction the steps depend on."""

    @abstractmethod
    def all(self) -> list[Dependency]:
        """Every declared dependency, regardless of platform."""
        raise NotImplementedError

    def depends_on(self, module: str) -> list[str]:
        """Modules the given module directly builds on. Empty unless overridden."""
        return []

    def selected(self, platform: str, gpu: bool) -> list[Dependency]:
        """Dependencies relevant to this platform/GPU choice with packages.

        Filters out gpu-only entries when ``gpu`` is False and entries that
        declare no package for this platform — including no apt package *and*
        no vcpkg fallback (see :meth:`Dependency.vcpkg_fallback_ports`).
        """
        out: list[Dependency] = []
        for dep in self.all():
            if dep.gpu_only and not gpu:
                continue
            if dep.packages_for(platform) or dep.vcpkg_fallback_ports(platform):
                out.append(dep)
        return out


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
    with as_file(files("sushistack") / MANIFESTS_DIR) as path:
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


def _parse_manifest(path: Path, owner: str) -> tuple[list[Dependency], list[str]]:
    """Return this fragment's dependencies and its ``[module] depends_on`` list.

    The reserved ``[module]`` table carries module metadata (currently the
    ``depends_on`` list) rather than a dependency, so it is pulled out here and
    never becomes a :class:`Dependency`.

    Raises:
        ValueError: A top-level key holds something other than a table. Skipping
            it is how sushidsp's whole fragment went unread; a fragment shape
            this function does not understand is a defect to report, not to
            ignore.
    """
    with path.open("rb") as fh:
        doc = tomllib.load(fh)
    depends_on: list[str] = []
    deps: list[Dependency] = []
    for name, table in doc.items():
        if not isinstance(table, dict):
            raise ValueError(
                f"{path}: '{name}' is a {type(table).__name__}, and a fragment declares one "
                f"table per dependency. An array of [[{name}]] tables reads as a list here and "
                f"was skipped in silence until 2026-09-22, which lost every dependency the file "
                f"declared.")
        if name == MODULE_META_TABLE:
            depends_on = [str(m) for m in table.get("depends_on", [])]
            continue
        deps.append(
            Dependency(
                name=name,
                description=str(table.get("description", "")),
                required=bool(table.get("required", True)),
                gpu_only=bool(table.get("gpu_only", False)),
                linux_apt=list(table.get("linux_apt", [])),
                windows_vcpkg=list(table.get("windows_vcpkg", [])),
                check_cmd=list(table.get("check_cmd", [])),
                owner=owner,
                provides=str(table.get("provides", "")),
            )
        )
    return deps, depends_on


class TomlDependencySource(IDependencySource):
    """Aggregates dependency fragments from across the workspace.

    ``sources`` can be injected (tests) as ``(path, owner)`` pairs; otherwise the
    union of every fragment from :func:`manifest_sources` is read, with first-wins
    de-duplication by name. Alongside the merged dependencies it records, per
    owning module, which modules that module ``depends_on`` — so callers can
    reason about a module's *effective* dependency set (its own plus those it
    builds on).
    """

    def __init__(self, sources: list[tuple[Path, str]] | None = None) -> None:
        self._sources = sources if sources is not None else manifest_sources()
        self._depends_on: dict[str, list[str]] = {}
        self._merged: list[Dependency] | None = None

    def all(self) -> list[Dependency]:
        """Return every declared dependency, merged first-wins by name.

        Read once and kept: several steps of one run ask for the set, the files
        do not change under them, and a duplicate would otherwise be reported
        again for each asking.
        """
        if self._merged is not None:
            return list(self._merged)
        if not self._sources:
            raise FileNotFoundError(
                "No dependency manifests found. Expected at least "
                "manifests/*.deps.toml inside the installed sushistack package."
            )
        merged: dict[str, Dependency] = {}
        for path, owner in self._sources:
            if not path.is_file():
                continue
            deps, depends_on = _parse_manifest(path, owner)
            if depends_on:
                self._depends_on.setdefault(owner, []).extend(depends_on)
            for dep in deps:
                if dep.name in merged:
                    merged[dep.name], warning = _merge(merged[dep.name], dep)
                    if warning:
                        console.warn(warning)
                    continue
                merged[dep.name] = dep
        self._merged = list(merged.values())
        return list(self._merged)

    def depends_on(self, module: str) -> list[str]:
        """Modules the given module directly builds on (``[module] depends_on``).

        Populated as a side effect of :meth:`all`; call ``all()`` first (the
        readiness reporter does).
        """
        return self._depends_on.get(module, [])
