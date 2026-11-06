# cli_install.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
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
from .ports import ConsolePort, PipxClient, Ports
from .presence import module_dir


def _run(cmd: list[str]) -> int:
    console.info("$ " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def _ensure_pipx(pipx: PipxClient, out: ConsolePort) -> None:
    """Install pipx with pip when *pipx* is not available.

    Raises:
        RuntimeError: pip itself failed to install pipx.
    """
    if pipx.available():
        return
    out.info("pipx not found; installing it with pip ...")
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
    if not pipx.available():
        raise RuntimeError("pipx was installed but could not be found afterwards.")


def install_cli(names: list[str] | None, dry_run: bool = False,
                ports: Ports | None = None) -> int:
    """Install the developer CLI of one or more modules. Return exit code.

    Always editable, against the checkout it was invoked from: a non-editable
    install freezes the CLI at whatever revision was on disk at install time, so
    later `git pull`s on the module silently stop reaching the installed
    `sr`/`se`/`sa`/`sb` until someone thinks to reinstall by hand.
    """
    ports = ports or Ports.machine(console)
    out = ports.console
    out.header("SushiHub Install-CLI")
    resolved = _resolve_names(names)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        out.info("Dry-run: showing actions without installing.")

    linked = links.registered()
    if dry_run:
        failed = False
        for name in resolved:
            pkg_dir = module_dir(root, name, linked) / "cli"
            if not (pkg_dir / "pyproject.toml").is_file():
                out.warn(f"{name}: no cli/ package at {pkg_dir}; "
                             "clone or link the module first. Skipping.")
                failed = True
                continue
            out.info(
                f"{name}: (dry-run) would install {pipx_svc.distribution_name(pkg_dir)} "
                f"from {pkg_dir}")
        return 1 if failed else 0

    try:
        _ensure_pipx(ports.pipx, out)
    except RuntimeError as exc:
        out.error(str(exc))
        return 1

    failed = False
    for name in resolved:
        dest = module_dir(root, name, linked)
        pkg_dir = dest / "cli"
        if not (pkg_dir / "pyproject.toml").is_file():
            out.warn(f"{name}: no cli/ package at {pkg_dir}; "
                         "clone or link the module first. Skipping.")
            failed = True
            continue
        dist = pipx_svc.distribution_name(pkg_dir)
        out.info(f"{name}: installing {dist} from {pkg_dir}")
        if ports.pipx.install(pkg_dir, editable=True) != 0:
            out.error(f"{name}: install failed.")
            failed = True

    if failed:
        out.error("One or more module CLIs did not install. See messages above.")
        return 1
    out.success("Module CLI(s) installed. Open a new terminal if the command "
                    "is not yet on PATH.")
    return 0
