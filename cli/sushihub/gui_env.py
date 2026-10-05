# gui_env.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builds the environment the desktop application's build, test and run run under.

It is :class:`sushicore.build_env.StackBuildEnv` with the application's own profile and root
resolver. Why a vcvars snapshot is needed is in cli/README.md, "Notes on the source".
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
