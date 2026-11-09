# workspace_source.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The workspace adapter of :class:`~.ports.DataSource`: the fragments of the present modules."""

from __future__ import annotations

from pathlib import Path
from typing import final

from ...config import find_workspace_root
from ..module_fragments import fragment_of, present_modules
from .fragment_reader import read_data_packages
from .package import DataPackage


@final
class WorkspaceDataSource:
    """Reads ``[data.*]`` from each cloned or linked module of a workspace.

    A binary install is left out: it carries no checkout to place a file in.

    Args:
        root: The workspace root; the one the environment or the working folder names when None.
    """

    def __init__(self, root: Path | None = None) -> None:
        """Holds the workspace root, resolved when :meth:`packages` runs."""
        self._root = root

    def packages(self) -> list[DataPackage]:
        """Returns every package the present modules declare, module by module in file order.

        Raises:
            DataFragmentError: A fragment declares a table wrongly.
        """
        root = self._root if self._root is not None else find_workspace_root()
        if root is None:
            return []
        found: list[DataPackage] = []
        for name, checkout in present_modules(root).items():
            fragment = fragment_of(name, checkout)
            if fragment.is_file():
                found.extend(read_data_packages(fragment, name, checkout))
        return found
