# backend.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Re-export of :mod:`sushicore.provision.gpu.backend`; the implementation moved
to sushicore.
"""

from __future__ import annotations

from sushicore.provision.gpu.backend import (  # noqa: F401
    GpuBackendSpec,
    NotProvided,
    PlatformLocator,
    ToolkitInstall,
    ToolkitLocator,
)
