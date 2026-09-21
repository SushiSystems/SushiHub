"""`hub install-cli` service: install a module's own developer CLI.

One program name per module — `sr`, `se`, `sa`, `sb`, `sd` — resolved from
the catalog in :mod:`sushistack.services.catalog`, which is the single place
that knows what the stack contains. Nothing here is per-module: the logic reads
the distribution name out of the module's own ``cli/pyproject.toml``, so a
module added to that registry works the day it is added, with no change to this
file.

The umbrella owns this so there is a single install seam for the whole stack: no
module ships its own bootstrap script. The service installs the module CLI into
an isolated pipx venv and stops there: ``sushicore`` is an ordinary PyPI
dependency each module CLI declares, so pipx resolves it like any other.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib

from .. import console
from ..config import workspace_root
from .modules import _resolve_names, module_dest


def _run(cmd: list[str]) -> int:
    console.info("$ " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def _ensure_pipx() -> list[str]:
    """Return a command prefix that runs pipx, installing it if necessary."""
    if subprocess.run([sys.executable, "-m", "pipx", "--version"],
                      capture_output=True).returncode == 0:
        return [sys.executable, "-m", "pipx"]
    console.info("pipx not found; installing it with pip ...")
    cmd = [sys.executable, "-m", "pip", "install", "pipx"]
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if not in_venv:
        # --user only makes sense (and is only valid) outside a venv/conda env,
        # where user site-packages are visible; inside one, pip rejects it.
        cmd.append("--user")
    pip_help = subprocess.run([sys.executable, "-m", "pip", "install", "--help"],
                              capture_output=True, text=True).stdout
    if "--break-system-packages" in pip_help:
        cmd.append("--break-system-packages")
    if _run(cmd) != 0:
        raise RuntimeError("Failed to install pipx.")
    _run([sys.executable, "-m", "pipx", "ensurepath"])
    return [sys.executable, "-m", "pipx"]


def _dist_name(pkg_dir: Path) -> str:
    """The distribution name pipx installs, read from the package's pyproject."""
    with (pkg_dir / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["name"])


def install_cli(names: list[str] | None, dry_run: bool = False) -> int:
    """Install the developer CLI of one or more modules. Return exit code.

    Always editable, against the checkout it was invoked from: a non-editable
    install freezes the CLI at whatever revision was on disk at install time, so
    later `git pull`s on the module silently stop reaching the installed
    `sr`/`se`/`sa`/`sb` until someone thinks to reinstall by hand.
    """
    console.header("SushiStack Install-CLI")
    resolved = _resolve_names(names)
    if resolved is None:
        return 1
    root = workspace_root()
    if dry_run:
        console.info("Dry-run: showing actions without installing.")

    if dry_run:
        failed = False
        for name in resolved:
            pkg_dir = module_dest(root, name) / "cli"
            if not (pkg_dir / "pyproject.toml").is_file():
                console.warn(f"{name}: no cli/ package at {pkg_dir}; "
                             "clone or link the module first. Skipping.")
                failed = True
                continue
            console.info(f"{name}: (dry-run) would install {_dist_name(pkg_dir)} from {pkg_dir}")
        return 1 if failed else 0

    try:
        pipx = _ensure_pipx()
    except RuntimeError as exc:
        console.error(str(exc))
        return 1

    failed = False
    for name in resolved:
        dest = module_dest(root, name)
        pkg_dir = dest / "cli"
        if not (pkg_dir / "pyproject.toml").is_file():
            console.warn(f"{name}: no cli/ package at {pkg_dir}; "
                         "clone or link the module first. Skipping.")
            failed = True
            continue
        dist = _dist_name(pkg_dir)
        console.info(f"{name}: installing {dist} from {pkg_dir}")
        rc = _run([*pipx, "install", "--force", "--editable", str(pkg_dir)])
        if rc != 0:
            console.error(f"{name}: install failed.")
            failed = True

    if failed:
        console.error("One or more module CLIs did not install. See messages above.")
        return 1
    console.success("Module CLI(s) installed. Open a new terminal if the command "
                    "is not yet on PATH.")
    return 0
