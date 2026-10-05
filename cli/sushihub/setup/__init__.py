# __init__.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""SushiHub's provisioning pipeline.

A dependency-injected pipeline that detects what is present, installs what the
``*.deps.toml`` fragments declare and is missing, and writes the probed ``[tool]``
table. Building a module is its own CLI's job.

The public entry point is :func:`factory.build_pipeline`; everything else is an
implementation detail behind small interfaces (:class:`pipeline.Step`,
:class:`package_managers.IPackageManager`,
:class:`dependency_source.IDependencySource`).
"""

from __future__ import annotations

from .factory import build_pipeline, build_uninstall_pipeline
from .pipeline import InstallContext, InstallPipeline, Step, StepResult

__all__ = [
    "build_pipeline",
    "build_uninstall_pipeline",
    "InstallContext",
    "InstallPipeline",
    "Step",
    "StepResult",
]
