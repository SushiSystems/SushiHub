"""Re-export of :mod:`sushicore.provision.probe`; the implementation moved to sushicore."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision.probe import (  # noqa: F401
    binary_works,
    classify_display_adapters,
    detect_gpu_vendor,
    find_configured_toolchain,
    find_sycl_compiler,
    resolve_local_config,
    toolchain_status,
)
from sushicore.provision.sinks import render_local_config  # noqa: F401
from sushicore.provision.sinks import write_platform_paths as _write

from ..config import WORKSPACE_HEADER


def write_platform_paths(target: Path, platform: str, values: dict[str, str]) -> Path:
    """Merge *values* into *target*'s ``[tool.<platform>]`` table under hub's workspace header."""
    return _write(target, platform, values, WORKSPACE_HEADER)
