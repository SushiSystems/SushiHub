"""Which heavy toolchains a run provisions, derived from the present modules.

The workspace ships no toolchain list of its own: a customizable component is
wanted when a module's fragment declares a dependency of that name. The shared
base fragments cannot select one, since they belong to no module. The rule is
in `docs/agent/specs/2026-09-05-hub-design.md` §3.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from ..config import CUSTOMIZABLE_COMPONENTS
from .dependency_source import SHARED_OWNER, IDependencySource


@dataclass(frozen=True)
class ToolchainSelection:
    """The four customizable components of one install run, on or off."""

    install_intel_llvm: bool
    install_acpp: bool
    oneapi: bool
    gpu: bool

    def as_dict(self) -> dict[str, bool]:
        """Return the selection as ``InstallContext`` field name -> value."""
        return {f.name: bool(getattr(self, f.name)) for f in fields(self)}

    def components(self) -> list[str]:
        """List the selected component keys in ``CUSTOMIZABLE_COMPONENTS`` order."""
        return [key for key, _label, field in CUSTOMIZABLE_COMPONENTS
                if getattr(self, field)]

    def merged(self, overrides: dict[str, bool]) -> "ToolchainSelection":
        """Return a copy with the known field names in *overrides* applied."""
        values = self.as_dict()
        values.update({k: bool(v) for k, v in overrides.items() if k in values})
        return ToolchainSelection(**values)


def selection_from_source(source: IDependencySource) -> ToolchainSelection:
    """Derive the selection from the dependencies the present modules declare.

    A component is on when some dependency carries its key as a name and an
    owner other than :data:`SHARED_OWNER`; off otherwise.
    """
    declared = {d.name for d in source.all() if d.owner != SHARED_OWNER}
    wanted = {field: key in declared for key, _label, field in CUSTOMIZABLE_COMPONENTS}
    return ToolchainSelection(**wanted)
