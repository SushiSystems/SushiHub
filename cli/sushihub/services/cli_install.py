# cli_install.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Installs a module's own developer CLI into an isolated pipx venv, for `hub install-cli`.

The program name comes from the catalog in :mod:`sushihub.services.catalog` and the
distribution name from the module's ``cli/pyproject.toml``. Why the umbrella owns this is in
cli/README.md, "Notes on the source".
"""

from __future__ import annotations

import subprocess
import sys

from .. import console
from ..config import workspace_root
from . import links
from . import pipx as pipx_svc
from .modules import _resolve_names
from .presence import module_dir


def _run(cmd: list[str]) -> int:
    console.info("$ " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def _ensure_pipx() -> None:
    """Install pipx with pip when :func:`~.pipx.command` cannot find it.

    Raises:
        RuntimeError: pip itself failed to install pipx.
    """
    if pipx_svc.command() is not None:
        return
    console.info("pipx not found; installing it with pip ...")
    cmd = [sys.executable, "-m", "pip", "install", "pipx"]
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if not in_venv:
        # pip accepts --user only outside a venv or conda env.
        cmd.append("--user")
    pip_help = subprocess.run([sys.executable, "-m", "pip", "install", "--help"],
                              capture_output=True, text=True).stdout
    if "--break-system-packages" in pip_help:
        cmd.append("--break-system-packages")
    if _run(cmd) != 0:
        raise RuntimeError("Failed to install pipx.")
    _run([sys.executable, "-m", "pipx", "ensurepath"])
    if pipx_svc.command() is None:
        raise RuntimeError("pipx was installed but could not be found afterwards.")


def install_cli(names: list[str] | None, dry_run: bool = False) -> int:
    """Install the developer CLI of one or more modules. Return exit code.

    Always editable, against the checkout it was invoked from: a non-editable
    install freezes the CLI at whatever revision was on disk at install time, so
    later `git pull`s on the module silently stop reaching the installed
    `sr`/`se`/`sa`/`sb` until someone thinks to reinstall by hand.
    """
    console.header("SushiHub Install-CLI")
    resolved = _resolve_names(names)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        console.info("Dry-run: showing actions without installing.")

    linked = links.registered()
    if dry_run:
        failed = False
        for name in resolved:
            pkg_dir = module_dir(root, name, linked) / "cli"
            if not (pkg_dir / "pyproject.toml").is_file():
                console.warn(f"{name}: no cli/ package at {pkg_dir}; "
                             "clone or link the module first. Skipping.")
                failed = True
                continue
            console.info(
                f"{name}: (dry-run) would install {pipx_svc.distribution_name(pkg_dir)} "
                f"from {pkg_dir}")
        return 1 if failed else 0

    try:
        _ensure_pipx()
    except RuntimeError as exc:
        console.error(str(exc))
        return 1

    failed = False
    for name in resolved:
        dest = module_dir(root, name, linked)
        pkg_dir = dest / "cli"
        if not (pkg_dir / "pyproject.toml").is_file():
            console.warn(f"{name}: no cli/ package at {pkg_dir}; "
                         "clone or link the module first. Skipping.")
            failed = True
            continue
        dist = pipx_svc.distribution_name(pkg_dir)
        console.info(f"{name}: installing {dist} from {pkg_dir}")
        if pipx_svc.install(pkg_dir, editable=True) != 0:
            console.error(f"{name}: install failed.")
            failed = True

    if failed:
        console.error("One or more module CLIs did not install. See messages above.")
        return 1
    console.success("Module CLI(s) installed. Open a new terminal if the command "
                    "is not yet on PATH.")
    return 0
