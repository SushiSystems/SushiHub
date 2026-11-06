# detect_step.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Hub's detect step: sushicore's, with the machine inventory it probes made replaceable."""

from __future__ import annotations

from typing import Callable

from sushicore.provision import probe
from sushicore.provision.steps import DetectStep as CoreDetectStep

from .dependency_source import Dependency, IDependencySource
from .package_managers import IPackageManager
from .pipeline import InstallContext

#: One inventory row: component, status, owner, detail.
InventoryRow = tuple[str, str, str, str]

#: What probes the machine and returns the rows of the inventory table.
Inventory = Callable[[InstallContext, list[Dependency]], list[InventoryRow]]


class DetectStep(CoreDetectStep):
    """Inventories the machine and fills ``ctx.detected``.

    Args:
        source: The dependency source whose fragments the inventory covers.
        managers: The package managers that know whether a dependency is installed.
        after_inventory: Called once the inventory table has been printed.
        inventory: Returns the rows in place of probing the machine; sushicore's probe when None.
        toolchain_status: Reads the SYCL toolchains off the machine.
        gpu_vendor: Reads the discrete-GPU vendor off the machine.
    """

    def __init__(self, source: IDependencySource,
                 managers: list[IPackageManager] | None = None,
                 after_inventory: Callable[[InstallContext, list[Dependency]], None] | None = None,
                 *, inventory: Inventory | None = None,
                 toolchain_status=probe.toolchain_status,
                 gpu_vendor=probe.detect_gpu_vendor) -> None:
        """Wire the sources, the managers, the machine probes and the inventory to use."""
        super().__init__(source, managers, after_inventory,
                         toolchain_status=toolchain_status, gpu_vendor=gpu_vendor)
        self._inventory = inventory

    def inventory_rows(self, ctx: InstallContext,
                       all_deps: list[Dependency]) -> list[InventoryRow]:
        """Return the injected inventory's rows, or probe the machine when none was given."""
        if self._inventory is not None:
            return self._inventory(ctx, all_deps)
        return super().inventory_rows(ctx, all_deps)
