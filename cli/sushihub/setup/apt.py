# apt.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Re-export of :mod:`sushicore.provision.system`; the implementation moved to sushicore."""

from __future__ import annotations

from sushicore.provision.system import (  # noqa: F401
    USER_AGENT,
    ensure_intel_oneapi_repo,
    is_root,
    os_release,
    sudo_bash,
)
