"""SushiStack developer CLI package.

``__version__`` is read from the installed distribution, so ``pyproject.toml``
is the one place the version is written.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sushistack-cli")
except PackageNotFoundError:
    __version__ = "0"
