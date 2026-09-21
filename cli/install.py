#!/usr/bin/env python3
"""Install the `hub` CLI from this checkout, for working on it.

This is the contributor's install. A user installs `hub` from PyPI
(`pipx install sushihub`), which is what install.ps1 and install.sh do; running
this script instead points the same command at the checkout you are editing.

Usage:
    python cli/install.py            # install / upgrade (always editable)
    python cli/install.py --uninstall

Strategy:
  * All platforms -> pipx (isolated, puts `hub` on PATH; pipx is bootstrapped if absent).
  * Always installed --editable, against the workspace checkout at REPO_ROOT. `hub`
    is one half of a self-updating pair with `hub sync`/`hub update` (which pull this
    same checkout) -- a non-editable install would silently freeze `hub` at whatever
    revision was on disk when it was first installed, so every later fix would need
    a manual reinstall to take effect. There is no non-editable mode to opt into.
  * `sushicore` is an ordinary dependency, resolved from PyPI by the same pipx install.

The CLI package directory is located automatically (the folder holding
pyproject.toml), so renaming the `cli/` folder later does not break this script.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "sushihub"


def find_package_dir() -> Path:
	"""Return the directory containing the CLI's pyproject.toml."""
	# Prefer common locations, then fall back to a shallow search.
	for name in ("cli", "cli", ".tools", "tools"):
		candidate = REPO_ROOT / name / "pyproject.toml"
		if candidate.is_file():
			return candidate.parent
	for pyproject in REPO_ROOT.glob("*/*/pyproject.toml"):
		return pyproject.parent
	sys.exit("[ERROR] Could not find the CLI package (no pyproject.toml under the repo root).")


def run(cmd: list[str]) -> int:
	print(f"[INFO] $ {' '.join(cmd)}")
	return subprocess.run(cmd).returncode


def ensure_pipx() -> str:
	"""Return a command prefix that runs pipx, installing it if necessary."""
	if subprocess.run([sys.executable, "-m", "pipx", "--version"],
	                   capture_output=True).returncode == 0:
		return f"{sys.executable} -m pipx"
	print("[INFO] pipx not found; installing it with pip...")
	
	cmd = [sys.executable, "-m", "pip", "install", "--user", "pipx"]
	pip_help = subprocess.run([sys.executable, "-m", "pip", "install", "--help"], 
	                          capture_output=True, text=True).stdout
	if "--break-system-packages" in pip_help:
		cmd.append("--break-system-packages")
		
	if run(cmd) != 0:
		sys.exit("[ERROR] Failed to install pipx.")
	run([sys.executable, "-m", "pipx", "ensurepath"])
	return f"{sys.executable} -m pipx"


def remove_legacy_shim(pipx: list[str]) -> None:
	"""Delete the `ss` shim an install made before the command was renamed.

	pipx removes only the shims of the console scripts it currently knows, so
	the `ss` entry point dropped from pyproject.toml survives on PATH until it
	is deleted by name.
	"""
	probe = subprocess.run([*pipx, "environment", "--value", "PIPX_BIN_DIR"],
	                       capture_output=True, text=True)
	if probe.returncode != 0:
		return
	bin_dir = Path(probe.stdout.strip())
	for shim in (bin_dir / "ss", bin_dir / "ss.exe"):
		try:
			shim.unlink()
		except OSError:
			continue
		print(f"[INFO] Removed the old shim {shim}")


def remove_legacy_package(pipx: list[str]) -> None:
	"""Uninstall the distribution under the name it carried before 2026-09-22.

	pipx keys a venv by distribution name, so the rename to `sushihub` leaves an
	earlier `sushihub-cli` venv in place, owning a `hub` shim of its own. Which
	one PATH resolves is then an accident.
	"""
	probe = subprocess.run([*pipx, "list", "--short"], capture_output=True, text=True)
	if probe.returncode != 0 or "sushihub-cli" not in probe.stdout:
		return
	print("[INFO] Removing the sushihub-cli install this package was renamed from.")
	run([*pipx, "uninstall", "sushihub-cli"])


def install() -> int:
	pkg_dir = find_package_dir()

	pipx = ensure_pipx().split()
	remove_legacy_package(pipx)
	rc = run([*pipx, "install", "--force", "--editable", str(pkg_dir)])

	if rc == 0:
		remove_legacy_shim(pipx)
		print("\n[SUCCESS] CLI installed. Try:  hub --help   (or: sushihub --help)")
		print("[NOTE] If `hub` is not found, open a new terminal "
		      "(pipx may have just added it to PATH).")
	else:
		print("\n[ERROR] Installation failed.")
	return rc


def uninstall() -> int:
	pipx = ensure_pipx().split()
	return run([*pipx, "uninstall", PACKAGE_NAME])


def main() -> None:
	parser = argparse.ArgumentParser(description="Install the SushiHub `hub` CLI.")
	parser.add_argument("--uninstall", action="store_true",
	                    help="Uninstall the CLI instead of installing.")
	args = parser.parse_args()
	sys.exit(uninstall() if args.uninstall else install())


if __name__ == "__main__":
	main()
