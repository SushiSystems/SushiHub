# bump.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Moves one Sushi library to a tag in every module that takes it, lowest tier first.

Each module is checked after its move; nothing is committed. The rule is decision D5 of
docs/agent/2026_11_16_DEPENDENCY_SYNC/PLAN.md in SushiSkills.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sushicore.deps_fragment import read_present

from ..setup.ordering import owner_order
from . import core_pin
from .catalog import library_repo
from .module_fragments import fragment_of, present_modules
from .pins import rewrite_pin
from .ports import GitClient

#: The line of a `tools/settings.py` that names sushicore as the tooling package.
K_TOOLING_SUSHICORE = re.compile(r'^K_TOOLING_PACKAGE\s*=\s*["\']sushicore["\']', re.MULTILINE)

#: Where a module keeps the checks run before work is reported finished.
K_CHECK_ALL = Path("tools") / "check_all.py"

#: Seconds one sync or check may run before it counts as failed.
K_RUN_TIMEOUT = 600


class BumpError(Exception):
    """Raised when a bump cannot be planned."""


class CommandRunner(Protocol):
    """Runs one command line in a directory."""

    def run(self, args: list[str], cwd: Path) -> tuple[int, str]:
        """Returns the exit code and the combined output of *args* run in *cwd*."""
        ...


@dataclass(frozen=True, slots=True)
class BumpResult:
    """Holds what a bump did, or would do, to one module."""

    module: str
    old_pin: str
    new_pin: str
    synced: bool
    check_passed: bool | None
    detail: str


@dataclass(frozen=True, slots=True)
class _Target:
    """Holds one module a bump moves: its checkout, the file holding its pin and the old pin."""

    module: str
    checkout: Path
    pin_file: Path | None
    old_pin: str


class ProcessRunner:
    """Runs commands as child processes; the machine adapter of :class:`CommandRunner`."""

    def run(self, args: list[str], cwd: Path) -> tuple[int, str]:
        """Returns the exit code and the combined output of *args* run in *cwd*."""
        try:
            done = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                                  timeout=K_RUN_TIMEOUT)
        except (OSError, subprocess.SubprocessError) as error:
            return 1, str(error)
        return done.returncode, done.stdout + done.stderr


def bump(root: Path, library: str, tag: str, dry_run: bool, git: GitClient,
         runner: CommandRunner) -> list[BumpResult]:
    """Move *library* to *tag* in every module of the workspace at *root* that takes it.

    Modules move lowest tier first; each is checked with its `tools/check_all.py` after.
    A dry run changes no file and runs nothing.

    Raises:
        BumpError: When the tag has no commit, or the modules depend on one another in a cycle.
    """
    if library == core_pin.K_LIBRARY:
        version = _core_version(tag)
        targets = _core_targets(root, version)
        new_pin = f"sushicore=={version}"
        commit = ""
    else:
        repo = library_repo(library)
        commit = git.tag_commit(repo, tag) or ""
        if not commit:
            raise BumpError(f"{library}: no tag {tag} found in {repo}.")
        targets = _library_targets(root, library)
        new_pin = f"{tag} ({commit[:12]})"
    results: list[BumpResult] = []
    for target in _ordered(root, targets):
        if dry_run:
            results.append(BumpResult(target.module, target.old_pin, new_pin, False, None,
                                      "planned"))
            continue
        _move(target, library, tag, commit)
        results.append(_sync_and_check(target, library, tag, new_pin, runner))
    return results


def _core_version(tag: str) -> str:
    """Return the release number of a sushicore *tag*, without its `v`."""
    parsed = core_pin.K_VERSION.fullmatch(tag)
    if parsed is None:
        raise BumpError(f"sushicore: '{tag}' is not a release number such as 0.9.8 or v0.9.8.")
    return parsed.group(1)


def _library_targets(root: Path, library: str) -> list[_Target]:
    """Return every present module whose fragment pins *library*."""
    targets: list[_Target] = []
    for name, checkout in present_modules(root).items():
        fragment = fragment_of(name, checkout)
        parsed = read_present(fragment)
        if parsed is None:
            continue
        for pin in parsed.pins:
            if pin.name == library:
                targets.append(_Target(name, checkout, fragment, pin.version))
    return targets


def _core_targets(root: Path, version: str) -> list[_Target]:
    """Return every checkout whose CLI requires sushicore or whose tools come from it."""
    checkouts = {"sushihub": root, **present_modules(root)}
    targets: list[_Target] = []
    for name, checkout in checkouts.items():
        pyproject = checkout / core_pin.K_PYPROJECT
        text = pyproject.read_text(encoding="utf-8") if pyproject.is_file() else ""
        found = core_pin.K_REQUIREMENT.search(text)
        if found is not None:
            targets.append(_Target(name, checkout, pyproject, found.group(0).strip('"')))
        elif _takes_core_tools(checkout):
            targets.append(_Target(name, checkout, None, "tools only"))
    return targets


def _takes_core_tools(checkout: Path) -> bool:
    """Return whether *checkout*'s `tools/settings.py` names sushicore as its tooling package."""
    settings = checkout / "tools" / "settings.py"
    return settings.is_file() and \
        K_TOOLING_SUSHICORE.search(settings.read_text(encoding="utf-8")) is not None


class _FragmentGraph:
    """Reads each workspace module's `depends_on` for :func:`owner_order`."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._edges: dict[str, list[str]] = {}

    def all(self) -> list[object]:
        """Read every present module's `depends_on`; returns no dependency."""
        for name, checkout in present_modules(self._root).items():
            parsed = read_present(fragment_of(name, checkout))
            self._edges[name] = parsed.depends_on if parsed is not None else []
        return []

    def depends_on(self, module: str) -> list[str]:
        """Return the modules *module* builds on."""
        return self._edges.get(module, [])


def _ordered(root: Path, targets: list[_Target]) -> list[_Target]:
    """Return *targets* lowest tier first, over the workspace modules' `depends_on`."""
    by_name = {target.module: target for target in targets}
    try:
        order = owner_order(_FragmentGraph(root), by_name)
    except ValueError as error:
        raise BumpError(str(error)) from error
    return [by_name[name] for name in order]


def _move(target: _Target, library: str, tag: str, commit: str) -> None:
    """Write the new pin into *target*'s pin file, when it has one."""
    if target.pin_file is None:
        return
    text = target.pin_file.read_bytes().decode("utf-8")
    if library == core_pin.K_LIBRARY:
        text = core_pin.rewrite_requirement(text, _core_version(tag))
    else:
        text = rewrite_pin(text, library, tag, commit)
    target.pin_file.write_bytes(text.encode("utf-8"))


def _sync_and_check(target: _Target, library: str, tag: str, new_pin: str,
                    runner: CommandRunner) -> BumpResult:
    """Sync sushicore's shared tools when bumping it, then run the module's checks."""
    synced = False
    if library == core_pin.K_LIBRARY:
        code, output = runner.run([sys.executable, "-m", "sushicore.shared_tools", "sync",
                                   str(target.checkout), "--tag", tag], target.checkout)
        if code != 0:
            return BumpResult(target.module, target.old_pin, new_pin, False, False,
                              "sync: " + _first_line(output))
        synced = True
    if not (target.checkout / K_CHECK_ALL).is_file():
        return BumpResult(target.module, target.old_pin, new_pin, synced, None, "no check_all")
    code, output = runner.run([sys.executable, str(K_CHECK_ALL), "."], target.checkout)
    detail = "" if code == 0 else _first_line(output)
    return BumpResult(target.module, target.old_pin, new_pin, synced, code == 0, detail)


def _first_line(output: str) -> str:
    """Return the first failing line of *output*, or its first line when none says so."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    failing = [line for line in lines if re.search(r"fail|error", line, re.IGNORECASE)]
    return (failing or lines or ["no output"])[0]
