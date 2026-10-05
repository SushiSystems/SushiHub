# __init__.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""SushiHub developer CLI package.

``__version__`` is read from the installed distribution, so ``pyproject.toml``
is the one place the version is written.
"""

from importlib.metadata import PackageNotFoundError, version

#: The name this package is published under, and the one every consumer asks for:
#: the installed version, pipx's venv, the --describe catalogue.
DISTRIBUTION = "sushihub"

try:
    __version__ = version(DISTRIBUTION)
except PackageNotFoundError:
    __version__ = "0"
