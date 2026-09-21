"""Running pipx: finding it, naming a package's distribution, and installing it.

`hub add` and `hub install-cli` both install a module's own `cli/` package with
pipx; this is the one place either of them does it, so they can no longer
install it two different ways.
"""

from __future__ import annotations

import shutil
import subprocess
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
