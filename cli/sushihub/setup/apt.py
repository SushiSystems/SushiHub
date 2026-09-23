"""Re-export of :mod:`sushicore.provision.system`; the implementation moved to sushicore."""

from __future__ import annotations

from sushicore.provision.system import (  # noqa: F401
    USER_AGENT,
    ensure_intel_oneapi_repo,
    is_root,
    os_release,
    sudo_bash,
)
