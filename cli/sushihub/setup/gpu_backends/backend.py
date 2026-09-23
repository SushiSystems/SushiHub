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
