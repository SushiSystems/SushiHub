# pin_report.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Collects the version each module of the workspace pins of each Sushi library.

A `[sushisystems.<name>]` table of a module's fragment is one pin; the `sushicore` requirement
of a `cli/pyproject.toml`, read through :mod:`sushihub.services.core_pin`, is the other. The
report holds data only: printing and the latest tag belong to the command.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..errors import HubError
from .core_pin import K_LIBRARY, K_PYPROJECT, K_REQUIREMENT
from .module_fragments import present_modules, workspace_pins


@dataclass(frozen=True, slots=True)
class ModulePin:
    """One module's pin of one library.

    Attributes:
        dependency: The library name, such as `sushiruntime` or `sushicore`.
        module: The module that pins it; `sushihub` for the hub's own `sushicore` requirement.
        version: The pinned release tag, or for `sushicore` the version its requirement names.
    """

    dependency: str
    module: str
    version: str


@dataclass(frozen=True, slots=True)
class Split:
    """One library pinned at more than one version.

    Attributes:
        dependency: The library name.
        modules_by_version: Each pinned version and the modules that pin it, in version order.
    """

    dependency: str
    modules_by_version: dict[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class PinReport:
    """Every pin of the workspace and every library pinned at more than one version."""

    pins: tuple[ModulePin, ...]
    splits: tuple[Split, ...]

    def dependencies(self) -> tuple[str, ...]:
        """Returns each pinned library name once, sorted."""
        return tuple(sorted({pin.dependency for pin in self.pins}))


def collect(root: Path) -> PinReport:
    """Reads every pin of the workspace at *root* and finds the libraries split across versions.

    Raises:
        HubError: When a fragment cannot be read.
    """
    try:
        pins = [ModulePin(pin.name, module, pin.version) for module, _, pin in workspace_pins(root)]
    except ValueError as error:
        raise HubError(str(error)) from error
    pins.extend(_core_pins(root))
    pins.sort(key=lambda pin: (pin.dependency, pin.module))
    return PinReport(tuple(pins), _splits(pins))


def _core_pins(root: Path) -> list[ModulePin]:
    """Returns the `sushicore` requirement of the hub and of each module CLI that states one."""
    found: list[ModulePin] = []
    for module, checkout in {"sushihub": root, **present_modules(root)}.items():
        pyproject = checkout / K_PYPROJECT
        if not pyproject.is_file():
            continue
        requirement = K_REQUIREMENT.search(pyproject.read_text(encoding="utf-8"))
        if requirement is not None:
            found.append(ModulePin(K_LIBRARY, module, requirement.group(1)))
    return found


def _splits(pins: list[ModulePin]) -> tuple[Split, ...]:
    """Returns one split per library whose pins name more than one version."""
    by_library: dict[str, dict[str, list[str]]] = {}
    for pin in pins:
        by_library.setdefault(pin.dependency, {}).setdefault(pin.version, []).append(pin.module)
    return tuple(
        Split(library, {version: tuple(modules) for version, modules in sorted(versions.items())})
        for library, versions in sorted(by_library.items()) if len(versions) > 1)
