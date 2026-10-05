# __init__.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Exports SushiHub's provisioning pipeline; the entry point is :func:`factory.build_pipeline`.

The pipeline detects what is present, installs what the ``*.deps.toml`` fragments declare and
is missing, and writes the probed ``[tool]`` table. Its interfaces are named in
cli/README.md, "Notes on the source".
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
