# data_step.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Hub's data step: downloads, verifies and places the data packages the present modules declare."""

from __future__ import annotations

from ..services.data import DataInstaller, DataPackageError, DataPlacer, DataSource
from ..services.ports import ConsolePort
from .pipeline import InstallContext, Step, StepResult


class DataStep(Step):
    """Installs every declared data package after the toolchains.

    A required package that fails fails the step; an optional one is recorded as a warning.

    Args:
        source: Lists the packages the present modules declare.
        installer: Stores and places them.
        placer: Resolves the destination a dry run reports.
        console: Where the plan of a dry run and a fragment error are printed.
    """

    name = "data"

    def __init__(self, source: DataSource, installer: DataInstaller, placer: DataPlacer,
                 console: ConsolePort) -> None:
        """Holds the source, the installer, the placer and the console."""
        self._source = source
        self._installer = installer
        self._placer = placer
        self._console = console

    def run(self, ctx: InstallContext) -> StepResult:
        """Installs the packages, or lists what would be installed under a dry run."""
        try:
            packages = self._source.packages()
            if not packages:
                return StepResult.SKIPPED
            if ctx.dry_run:
                for package in packages:
                    self._console.info(f"{package.name}: would fetch {package.url} to "
                                       f"{self._placer.destination(package)}")
                return StepResult.OK
        except DataPackageError as error:
            self._console.error(str(error))
            return StepResult.FAILED
        failed_required = False
        for result in self._installer.install(packages):
            if result.error is None:
                continue
            if result.package.required:
                failed_required = True
            else:
                ctx.warnings.append(result.error)
        return StepResult.FAILED if failed_required else StepResult.OK
