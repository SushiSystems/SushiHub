"""Which heavy toolchains a run provisions, derived from the present modules.

The rule is in `docs/agent/specs/2026-09-05-hub-design.md` §3; the GPU
component's exception is in `docs/design/GPU_BACKEND_PROVISIONING.md` §3.
"""

from __future__ import annotations

from sushicore.provision.pipeline import ToolchainSelection  # noqa: F401

from ..config import CUSTOMIZABLE_COMPONENTS
from .dependency_source import SHARED_OWNER, IDependencySource

#: Component fields that are on by default, whatever the modules declare.
MACHINE_COMPONENTS = frozenset({"gpu"})


def components(selection: ToolchainSelection) -> list[str]:
    """List the component keys *selection* turns on, in ``CUSTOMIZABLE_COMPONENTS`` order."""
    return [key for key, _label, field in CUSTOMIZABLE_COMPONENTS
            if getattr(selection, field)]


def selection_from_source(source: IDependencySource) -> ToolchainSelection:
    """Derive the selection from the dependencies the present modules declare.

    A field in :data:`MACHINE_COMPONENTS` is always on. Any other component is on
    when some dependency carries its key as a name and an owner other than
    :data:`SHARED_OWNER`; off otherwise.
    """
    declared = {d.name for d in source.all() if d.owner != SHARED_OWNER}
    wanted = {field: field in MACHINE_COMPONENTS or key in declared
              for key, _label, field in CUSTOMIZABLE_COMPONENTS}
    return ToolchainSelection(**wanted)
