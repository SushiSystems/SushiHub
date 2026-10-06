# steps.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Hub's pipeline steps: sushicore's shared steps and hub's readiness report."""

from __future__ import annotations

from sushicore.provision.steps import (  # noqa: F401
    ConfigureStep,
    DetectStep,
    InstallDepsStep,
    UninstallStep,
)

from .. import console
from .dependency_source import SHARED_OWNER, Dependency, IDependencySource
from .ordering import owner_order
from .pipeline import InstallContext


def _effective_required(source: IDependencySource, module: str,
                        all_deps: list[Dependency]) -> list[Dependency]:
    """Return the required dependencies *module* needs to build.

    These are the shared required dependencies, the module's own, and those of
    every module it builds on through *source*'s ``depends_on``, transitively.
    """
    want: dict[str, Dependency] = {}
    seen: set[str] = set()

    def visit(m: str) -> None:
        """Collect *m*'s required dependencies and recurse into what it builds on."""
        if m in seen:
            return
        seen.add(m)
        for dep in all_deps:
            if dep.required and dep.owner == m:
                want[dep.name] = dep
        for upstream in source.depends_on(m):
            visit(upstream)

    visit(module)
    for dep in all_deps:
        if dep.required and dep.owner == SHARED_OWNER:
            want[dep.name] = dep
    return list(want.values())


def _missing_requirements(ctx: InstallContext, required: list[Dependency]) -> list[str]:
    """Return the unmet requirement labels among *required*, honouring any-of groups.

    Dependencies sharing a ``provides`` tag form one group, met when any member
    is present and reported as "a or b" when none is. A group no member of which
    was probed on this platform counts as met.
    """
    groups: dict[str, list[Dependency]] = {}
    for dep in required:
        groups.setdefault(dep.provides or dep.name, []).append(dep)

    missing: list[str] = []
    for members in groups.values():
        checked = [m for m in members if m.name in ctx.detected]
        if not checked:
            continue
        if any(ctx.detected.get(m.name) for m in members):
            continue
        missing.append(" or ".join(m.name for m in members))
    return missing


def report_readiness(source: IDependencySource, ctx: InstallContext,
                     all_deps: list[Dependency]) -> None:
    """Print, per catalogue module in build order, how it is present and whether it can build.

    Args:
        source: The dependency source whose ``all()`` produced *all_deps*.
    """
    from ..config import find_workspace_root
    from ..services import links
    from ..services.catalog import CATALOG
    from ..services.presence import Presence, describe, module_dir, presence_of

    root = find_workspace_root()
    if root is None:
        return

    linked = links.registered()
    console.info("Module readiness:")
    for name in owner_order(source, CATALOG):
        dest = module_dir(root, name, linked)
        state = presence_of(root, name, linked)
        if state is Presence.BINARY:
            _, text = describe(root, name, linked)
            console.console.print(
                f"  [success]{name}: {text}, nothing to build[/success]")
            continue
        if state is Presence.ABSENT:
            verb = "linked but missing at" if name in linked else "not cloned yet"
            hint = f" ({dest})" if name in linked else f" (hub add {name})"
            console.console.print(f"  [muted]{name}: {verb}{hint}[/muted]")
            continue
        missing = _missing_requirements(ctx, _effective_required(source, name, all_deps))
        if missing:
            console.console.print(
                f"  [warn]{name}: needs {', '.join(missing)}[/warn]")
        else:
            console.console.print(f"  [success]{name}: ready to build[/success]")

