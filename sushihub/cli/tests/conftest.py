"""Shared fakes for the `ss` test suite.

``MemorySource`` stands in for the TOML dependency source so no test reads a
manifest, touches the network, or writes into ``dependencies/``. ``fake_cfg``
gives the steps a Linux :class:`Config` whose every tool path is empty.

Two things happen before ``sushistack`` is imported. ``SUSHISTACK_HOME`` is
pinned to the repository root, because ``sushistack.console`` resolves the
workspace at import time and pytest may run from outside one. The repository
root leaves ``sys.path``, because its ``sushicore/`` directory shadows the
installed ``sushicore`` distribution as a namespace package.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("SUSHISTACK_HOME", str(_REPO_ROOT))
sys.path[:] = [p for p in sys.path if p and Path(p).resolve() != _REPO_ROOT]
sys.modules.pop("sushicore", None)

from sushistack.config import Config  # noqa: E402
from sushistack.setup.dependency_source import (  # noqa: E402
    SHARED_OWNER,
    Dependency,
    IDependencySource,
)


class MemorySource(IDependencySource):
    """Serves a fixed dependency list and a fixed module dependency map."""

    def __init__(self, deps: list[Dependency],
                 depends_on: dict[str, list[str]] | None = None) -> None:
        """Store the dependencies and the module-to-modules map to serve."""
        self._deps = list(deps)
        self._depends_on = dict(depends_on or {})

    def all(self) -> list[Dependency]:
        """Return the dependency list exactly as it was given."""
        return list(self._deps)

    def depends_on(self, module: str) -> list[str]:
        """Return the modules *module* directly builds on."""
        return list(self._depends_on.get(module, []))


def dep(name: str, owner: str = SHARED_OWNER, *, provides: str = "",
        required: bool = True, linux_apt=(), windows_vcpkg=(),
        check_cmd=()) -> Dependency:
    """Build one :class:`Dependency` with the fields a test cares about."""
    return Dependency(
        name=name,
        description=f"{name} (test)",
        required=required,
        gpu_only=False,
        linux_apt=list(linux_apt),
        windows_vcpkg=list(windows_vcpkg),
        check_cmd=list(check_cmd),
        owner=owner,
        provides=provides,
    )


@pytest.fixture
def fake_cfg() -> Config:
    """Return a Linux configuration that pins no tool path."""
    return Config(platform="linux")
