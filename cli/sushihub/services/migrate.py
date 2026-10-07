# migrate.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""`hub migrate` service: moves the workspace's dependency tree to another directory.

Resolves the two roots, shows the plan, runs sushicore's migration and then settles what
names the tree: the registry, the workspace file's tool paths and ``SUSHISYSTEMS_HOME``.
"""

from __future__ import annotations

from pathlib import Path

from sushicore.provision import home, user_environment
from sushicore.provision import migrate as engine
from sushicore.provision.links import link_target
from sushicore.provision.lock import LockTimeout
from sushicore.provision.registry import Registry

from .. import console
from ..config import workspace_file, workspace_root
from .tool_paths import rewrite_tool_paths

K_CONSUMER = "hub"
K_TREE = "dependencies"
K_REGISTRY_FILE = "registry.toml"
K_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")

#: The journal steps this service records beside sushicore's own.
K_STEP_REGISTRY = "registry"
K_STEP_WORKSPACE = "workspace"
K_STEP_ENVIRONMENT = "environment"


def old_root() -> Path:
    """Return the tree a workspace has always held: ``<workspace>/dependencies``."""
    return workspace_root() / K_TREE


def new_root(target: Path | None) -> Path:
    """Return where the tree goes, or went.

    *target* answers first, then the directory the old path already links to, then
    sushicore's default root.
    """
    if target is not None:
        return Path(target).expanduser().resolve()
    return link_target(old_root()) or home.default_root()


def render_plan(plan: engine.MigrationPlan) -> list[str]:
    """Return the lines that describe *plan*: the roots, each component, the totals."""
    lines = [
        f"from: {plan.old_root.as_posix()}",
        f"to:   {plan.new_root.as_posix()}",
    ]
    lines.extend(
        f"{move.name}: {move.files} file{'' if move.files == 1 else 's'}, {_size(move.bytes)}"
        for move in plan.moves)
    way = "rename on one volume" if plan.same_volume else "copy across volumes, then verify"
    lines.append(f"total: {_size(plan.total_bytes)}, {way}")
    lines.append(f"free space on the target: {_size(plan.free_bytes)}")
    lines.append(f"enough space: {'yes' if plan.enough_space else 'no'}")
    return lines


def run(target: Path | None = None, dry_run: bool = False, assume_yes: bool = False) -> int:
    """Move the dependency tree to *target* and return a process exit code."""
    console.header("SushiHub Migrate")
    try:
        plan = engine.plan(old_root(), new_root(target))
    except engine.MigrationError as error:
        console.error(str(error))
        return 1
    for line in render_plan(plan):
        console.info(line)
    if dry_run:
        console.info("Dry-run: nothing was changed.")
        return 0
    if not plan.already_migrated and not plan.enough_space:
        console.error("Not enough free space on the target. Nothing was changed.")
        return 1
    if not plan.already_migrated and not _confirmed(assume_yes):
        console.info("Aborted.")
        return 1
    try:
        engine.migrate(plan, console.info)
    except (engine.MigrationError, LockTimeout) as error:
        console.error(str(error))
        console.info("Run `hub migrate` again to go on, or `hub migrate --rollback` to undo.")
        return 1
    _settle(plan.old_root, plan.new_root)
    return 0


def rollback(target: Path | None = None) -> int:
    """Undo a migration that was not finalized and return a process exit code."""
    console.header("SushiHub Migrate: rollback")
    old, new = old_root(), new_root(target)
    try:
        for entry in reversed(engine.MigrationJournal(new).entries()):
            _unsettle(entry, old, new)
        engine.rollback(old, new, console.info)
    except (engine.MigrationError, LockTimeout) as error:
        console.error(str(error))
        return 1
    return 0


def finalize(target: Path | None = None, drop_link: bool = False) -> int:
    """Delete the copy a migration set aside, and the link too when *drop_link* is set."""
    console.header("SushiHub Migrate: finalize")
    old, new = old_root(), new_root(target)
    if drop_link and not _is_named_by_environment(new):
        console.error(
            f"{home.ENV_HOME} does not name {new.as_posix()}, so without the link at "
            f"{old.as_posix()} hub would not find the tree. The link was kept.")
        return 1
    try:
        engine.finalize(old, new, console.info, drop_link=drop_link)
    except (engine.MigrationError, LockTimeout) as error:
        console.error(str(error))
        return 1
    console.success("Finalized. `hub migrate --rollback` can no longer undo the move.")
    return 0


def _confirmed(assume_yes: bool) -> bool:
    """Report whether the user agreed to the move, asking unless *assume_yes* is set."""
    if assume_yes:
        return True
    return console.prompt("Move the tree now? (y/N)", "n").strip().lower() in ("y", "yes")


def _settle(old: Path, new: Path) -> None:
    """Record the tree in the registry, the workspace file and the user's environment.

    Each step is journaled before it is taken, so a rollback undoes it, and a step
    already journaled is not taken again. A finalized migration has no journal and
    is left as it is.
    """
    journal = engine.MigrationJournal(new)
    if not journal.exists():
        console.info("Nothing left to do.")
        return
    taken = {entry["step"] for entry in journal.entries()}
    if K_STEP_REGISTRY not in taken:
        registry_file = new / K_REGISTRY_FILE
        journal.append(K_STEP_REGISTRY, created=not registry_file.is_file())
        registry = Registry(registry_file)
        registry.load()
        registry.seed_from_tree(new, consumer=K_CONSUMER)
        registry.save()
    if K_STEP_WORKSPACE not in taken:
        journal.append(K_STEP_WORKSPACE)
        rewrite_tool_paths(workspace_file(), old, new)
    if K_STEP_ENVIRONMENT not in taken:
        previous = user_environment.read_user_variable(home.ENV_HOME)
        journal.append(K_STEP_ENVIRONMENT, name=home.ENV_HOME, previous=previous)
        _name_in_environment(new)
    _report_settled(old, new)


def _unsettle(entry: dict, old: Path, new: Path) -> None:
    """Reverse one step :func:`_settle` journaled; any other step is sushicore's."""
    step = entry["step"]
    if step == K_STEP_ENVIRONMENT:
        if entry.get("previous") is None:
            user_environment.remove_user_variable(entry["name"])
        else:
            user_environment.write_user_variable(entry["name"], entry["previous"])
        console.info(f"Restored {entry['name']}.")
    elif step == K_STEP_WORKSPACE:
        rewrite_tool_paths(workspace_file(), new, old)
        console.info(f"Restored the tool paths in {workspace_file().as_posix()}.")
    elif step == K_STEP_REGISTRY and entry.get("created"):
        (new / K_REGISTRY_FILE).unlink(missing_ok=True)


def _name_in_environment(new: Path) -> None:
    """Set ``SUSHISYSTEMS_HOME`` to *new*, or unset it when *new* is the default root."""
    if new.resolve() == home.default_root().resolve():
        user_environment.remove_user_variable(home.ENV_HOME)
    else:
        user_environment.write_user_variable(home.ENV_HOME, new.as_posix())


def _is_named_by_environment(new: Path) -> bool:
    """Report whether the user's ``SUSHISYSTEMS_HOME`` names *new*."""
    value = user_environment.read_user_variable(home.ENV_HOME)
    return bool(value) and Path(value).expanduser().resolve() == new.resolve()


def _report_settled(old: Path, new: Path) -> None:
    """Say where the tree is, what the old path became and what the environment holds."""
    console.success(f"The dependency tree is now at {new.as_posix()}.")
    console.info(f"{old.as_posix()} is a link to it, so every path under it still resolves.")
    if _is_named_by_environment(new):
        console.info(f"{home.ENV_HOME} was set to {new.as_posix()} for your user.")
        console.info("Terminals opened before now must be reopened to see it.")
    else:
        console.info(f"{home.ENV_HOME} is not set: {new.as_posix()} is the default root.")
    console.info("Keep the old copy until every module builds, then run "
                 "`hub migrate --finalize`. `hub migrate --rollback` undoes the move.")


def _size(count: int) -> str:
    """Return *count* bytes in the largest unit that keeps the number at one or above."""
    value = float(count)
    for unit in K_SIZE_UNITS[:-1]:
        if value < 1024:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} {K_SIZE_UNITS[-1]}"
