# package_managers.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Re-export of :mod:`sushicore.provision.packages`; the implementation moved to sushicore."""

from __future__ import annotations

from sushicore.provision.packages import (  # noqa: F401
    WINGET_ID_TO_CMD,
    AptManager,
    DirectDownloadWindowsManager,
    DnfManager,
    IPackageManager,
    LinuxPackageManager,
    PacmanManager,
    VcpkgManager,
    WingetManager,
    YumManager,
    ZypperManager,
    download,
    ensure_intel_oneapi_repo,
    gh_tagged_asset,
    install_gpu_stack,
    refresh_windows_path,
    tools_dir,
)

