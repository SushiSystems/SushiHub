#!/usr/bin/env python3
"""Install the SushiStack `ss` CLI.

Usage:
    python cli/install.py            # install / upgrade (always editable)
    python cli/install.py --uninstall

Strategy:
  * All platforms -> pipx (isolated, puts `ss` on PATH; pipx is bootstrapped if absent).
  * Always installed --editable, against the workspace checkout at REPO_ROOT. `ss`
    is one half of a self-updating pair with `ss sync`/`ss update` (which pull this
    same checkout) -- a non-editable install would silently freeze `ss` at whatever
    revision was on disk when it was first installed, so every later fix would need
    a manual reinstall to take effect. There is no non-editable mode to opt into.

The CLI package directory is located automatically (the folder holding
pyproject.toml), so renaming the `cli/` folder later does not break this script.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "sushistack-cli"


def find_sushicore_dir() -> Path:
	"""Return the in-repo sushicore package directory.

	sushicore ships inside this repository, so there is nothing to look up and
	nothing to fetch: cloning SushiStack has already produced it. It is still a
	separate distribution (its own pyproject.toml) because pipx installs it as
	one -- it is not published to any index, so pipx's isolated venv cannot
	resolve it as a normal dependency and it is injected from this path instead.
	"""
	pkg = REPO_ROOT / "sushicore"
	if not (pkg / "pyproject.toml").is_file():
		sys.exit(
			f"[ERROR] {pkg} is missing its pyproject.toml. This is part of the "
			"SushiStack repository; re-clone or `git checkout -- sushicore`."
		)
	return pkg


def find_package_dir() -> Path:
	"""Return the directory containing the CLI's pyproject.toml."""
	# Prefer common locations, then fall back to a shallow search.
	for name in ("cli", ".tools", "tools"):
		candidate = REPO_ROOT / name / "pyproject.toml"
		if candidate.is_file():
			return candidate.parent
	for pyproject in REPO_ROOT.glob("*/pyproject.toml"):
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


def install() -> int:
	pkg_dir = find_package_dir()
	sushicore_dir = find_sushicore_dir()

	pipx = ensure_pipx().split()
	rc = run([*pipx, "install", "--force", "--editable", str(pkg_dir)])
	if rc == 0:
		# sushicore isn't a resolvable pip dependency (see pyproject.toml); inject
		# it into the venv pipx just created, always editable so future sushicore
		# edits apply without reinstalling this CLI.
		rc = run([*pipx, "inject", PACKAGE_NAME, "--editable", str(sushicore_dir)])

	if rc == 0:
		print("\n[SUCCESS] CLI installed. Try:  ss --help   (or: sushistack --help)")
		print("[NOTE] If `ss` is not found, open a new terminal "
		      "(pipx may have just added it to PATH).")
	else:
		print("\n[ERROR] Installation failed.")
	return rc


def uninstall() -> int:
	pipx = ensure_pipx().split()
	return run([*pipx, "uninstall", PACKAGE_NAME])


def main() -> None:
	parser = argparse.ArgumentParser(description="Install the SushiStack `ss` CLI.")
	parser.add_argument("--uninstall", action="store_true",
	                    help="Uninstall the CLI instead of installing.")
	args = parser.parse_args()
	sys.exit(uninstall() if args.uninstall else install())


if __name__ == "__main__":
	main()
