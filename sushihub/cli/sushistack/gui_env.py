"""The environment the desktop application's build, test and run run under.

A parent process cannot ``call vcvars64.bat`` and inherit the result, so the
shell runs as a child and its environment is dumped and cached — see
:mod:`sushicore.build_env` for the mechanism. That is the whole reason
`cmake --preset windows-x64` from a plain PowerShell found no compiler and
`ss gui build` does.

The application consumes the shared tree rather than provisioning anything, so
its environment is exactly :class:`sushicore.build_env.StackBuildEnv` with the
application's own profile and root resolver.
"""

from __future__ import annotations

from pathlib import Path

from sushicore.build_env import StackBuildEnv

from . import console
from .gui_config import GUI_PROFILE, GuiConfig, gui_root

_ENV = StackBuildEnv(profile=GUI_PROFILE, console=console, find_root=gui_root)


def load_gui_build_env(cfg: GuiConfig, build_dir: Path) -> dict[str, str]:
    """Return the environment for the application's subprocesses.

    Args:
        cfg: The resolved configuration.
        build_dir: The build tree, where the environment snapshot is cached.
    """
    return _ENV.load(cfg, build_dir)
