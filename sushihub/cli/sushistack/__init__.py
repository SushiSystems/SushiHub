"""SushiStack developer CLI package.

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
