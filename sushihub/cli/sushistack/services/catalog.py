"""What the stack contains, read from the catalog that ships with this package.

The catalog is data rather than code so that adding a module is an edit to
``catalog.toml`` and nothing else, and so that a later change of source -- a
catalog fetched from a server, a module that describes itself -- replaces one
loader instead of every reader.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Iterator

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


CATALOG_FILE = "catalog.toml"


@dataclass(frozen=True)
class Module:
    """One stack module: how to fetch it, where it lands, and what it is called."""

    name: str
    repo: str
    directory: str
    alias: str
    distribution: str

    #: Where this module keeps its dependency fragment, relative to its root. All
    #: six repositories use the default; a module says otherwise in its own
    #: ``sushi-module.toml``. See docs/reference/MODULE_MANIFEST.md.
    fragment: str = "cli/sushistack.deps.toml"

    @property
    def is_binary(self) -> bool:
        """Report whether this module ships as a compiled release rather than a clone."""
        return self.distribution == "binary"


class ModuleCatalog:
    """The modules `hub` knows, indexed by name and by alias."""

    def __init__(self, entries: dict[str, Module]) -> None:
        """Store the entries in the order given and index their aliases."""
        self._entries = dict(entries)
        self._aliases = {m.alias: m.name for m in self._entries.values()}

    def names(self) -> list[str]:
        """Return every module name, in catalog order."""
        return list(self._entries)

    def aliases(self) -> dict[str, str]:
        """Return the alias-to-name map."""
        return dict(self._aliases)

    def resolve(self, name: str) -> str | None:
        """Return the module name *name* stands for, or None when it names nothing."""
        resolved = self._aliases.get(name, name)
        return resolved if resolved in self._entries else None

    def __contains__(self, name: str) -> bool:
        """Report whether *name* is a module name in this catalog."""
        return name in self._entries

    def __getitem__(self, name: str) -> Module:
        """Return the entry for *name*."""
        return self._entries[name]

    def __iter__(self) -> Iterator[str]:
        """Iterate module names in catalog order."""
        return iter(self._entries)


def load_catalog() -> ModuleCatalog:
    """Build the catalog from the ``catalog.toml`` shipped inside this package.

    @pre The file is package data; a source checkout and an installed wheel both
        resolve it through ``importlib.resources``.
    """
    raw = (files("sushistack") / CATALOG_FILE).read_text(encoding="utf-8")
    doc = tomllib.loads(raw)
    entries = {
        name: Module(name=name, repo=body["repo"], directory=body["directory"],
                     alias=body["alias"], distribution=body["distribution"])
        for name, body in doc.items()
    }
    return ModuleCatalog(entries)


CATALOG = load_catalog()
