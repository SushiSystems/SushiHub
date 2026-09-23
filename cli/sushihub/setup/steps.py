"""Hub's pipeline steps: sushicore's shared steps, hub's verify step and readiness report."""

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
from .pipeline import InstallContext, Step, StepResult


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
    from ..config import workspace_root
    from ..services import links
    from ..services.catalog import CATALOG
    from ..services.presence import Presence, describe, module_dir, presence_of

    try:
        root = workspace_root()
    except SystemExit:
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


class VerifyStep(Step):
    """Build and smoke-test through the existing project service."""

    name = "verify"

    def run(self, ctx: InstallContext) -> StepResult:
        """Build a release and run the functional suite, failing on either error."""
        if ctx.dry_run:
            console.info("(dry-run) skipping build/verify.")
            return StepResult.SKIPPED

        from ..services import project as project_svc
        from ..services.project import BuildType, Suite

        no_cuda = not ctx.gpu and ctx.cfg.platform != "windows"
        rc = project_svc.build(BuildType.release, distributed=False,
                               no_cuda=no_cuda, clean=False)
        if rc != 0:
            console.error("Build failed during verification.")
            return StepResult.FAILED

        rc = project_svc.test(Suite.functional, distributed=False,
                              filter=None, asan=False, repeat=0)
        if rc != 0:
            console.warn("Functional smoke test reported failures.")
            return StepResult.FAILED

        console.success("Build + smoke test passed. Project is ready.")
        return StepResult.OK
