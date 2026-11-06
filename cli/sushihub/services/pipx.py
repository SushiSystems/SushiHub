# pipx.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Running pipx: finding it, naming a package's distribution, and installing it.

`hub add` and `hub install-cli` both install a module's own `cli/` package with
pipx; this is the one place either of them does it, so they can no longer
install it two different ways.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib


def distribution_name(pkg_dir: Path) -> str:
    """The distribution name pipx installs, read from the package's pyproject."""
    with (pkg_dir / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["name"])


@dataclass(frozen=True)
class Install:
    """How pipx holds one distribution: from the index, or from a checkout."""

    #: The directory pipx was pointed at, or None when it installed from the index.
    source: Path | None

    @property
    def editable(self) -> bool:
        """Whether the install tracks a checkout rather than a published version."""
        return self.source is not None


class ProcessPipx:
    """Runs pipx as a child process; the machine adapter of :class:`~.ports.PipxClient`."""

    def available(self) -> bool:
        """Returns whether pipx can be found on this machine."""
        return _command() is not None

    def install(self, pkg_dir: Path, *, editable: bool) -> int:
        """Installs *pkg_dir* with pipx over whatever is there and returns pipx's exit code.

        Args:
            pkg_dir: The package to install; a directory carrying a pyproject.toml.
            editable: Install in editable mode, so a later `git pull` on the checkout keeps
                reaching the installed command.
        """
        cmd = [*_command(), "install", "--force", *(["--editable"] if editable else []),
               str(pkg_dir)]
        return subprocess.run(cmd).returncode

    def installed(self, name: str) -> Install | None:
        """Returns how pipx holds *name*, or None when pipx is missing, fails or lists no such venv.

        An editable install records the directory it was pointed at, so a caller can update it by
        pulling that checkout; an index install records only the name.
        """
        pipx = _command()
        if pipx is None:
            return None
        probe = subprocess.run([*pipx, "list", "--json"], capture_output=True, text=True)
        if probe.returncode != 0:
            return None
        try:
            venv = json.loads(probe.stdout)["venvs"][name]["metadata"]["main_package"]
        except (ValueError, KeyError):
            return None
        if "--editable" not in venv.get("pip_args", []):
            return Install(None)
        return Install(Path(venv["package_or_url"]))

    def upgrade(self, name: str) -> int:
        """Upgrades *name* to the newest version on the index and returns pipx's exit code."""
        return subprocess.run([*_command(), "upgrade", name]).returncode


def _command() -> list[str] | None:
    """Return a command that runs pipx, or None if pipx can't be found.

    `hub` itself was installed by pipx, so pipx is normally on PATH; fall back to
    `python -m pipx` under whichever interpreter has it. We never use
    sys.executable here — that is `hub`'s own isolated pipx venv, which has no
    pipx module.
    """
    exe = shutil.which("pipx")
    if exe:
        return [exe]
    for py in ("python3", "python"):
        found = shutil.which(py)
        if found and subprocess.run(
            [found, "-m", "pipx", "--version"], capture_output=True
        ).returncode == 0:
            return [found, "-m", "pipx"]
    return None
