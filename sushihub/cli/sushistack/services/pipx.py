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


def command() -> list[str] | None:
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


def distribution_name(pkg_dir: Path) -> str:
    """The distribution name pipx installs, read from the package's pyproject."""
    with (pkg_dir / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["name"])


def install(pkg_dir: Path, *, editable: bool) -> int:
    """Install *pkg_dir* with pipx, forcing a reinstall over whatever is there.

    Args:
        pkg_dir: The package to install; a directory carrying a pyproject.toml.
        editable: Install in editable mode, so a later `git pull` on the
            checkout keeps reaching the installed command.

    Returns:
        The exit code pipx reported. None here means pipx itself is missing;
        that is the caller's own check, against :func:`command`.
    """
    pipx = command()
    cmd = [*pipx, "install", "--force", *(["--editable"] if editable else []), str(pkg_dir)]
    return subprocess.run(cmd).returncode


@dataclass(frozen=True)
class Install:
    """How pipx holds one distribution: from the index, or from a checkout."""

    #: The directory pipx was pointed at, or None when it installed from the index.
    source: Path | None

    @property
    def editable(self) -> bool:
        """Whether the install tracks a checkout rather than a published version."""
        return self.source is not None


def installed(name: str) -> Install | None:
    """How pipx holds *name*, or None when pipx does not hold it at all.

    An editable install records the directory it was pointed at, so a caller can
    update it by pulling that checkout; an index install records only the name.

    Returns:
        The install, or None when pipx is missing, fails, or lists no such venv.
    """
    pipx = command()
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


def upgrade(name: str) -> int:
    """Upgrade *name* to the newest version on the index.

    Returns:
        The exit code pipx reported.
    """
    return subprocess.run([*command(), "upgrade", name]).returncode
