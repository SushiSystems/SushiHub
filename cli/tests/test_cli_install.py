# test_cli_install.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How a module's own CLI is installed."""

from __future__ import annotations

import pytest

from sushihub.services import cli_install, modules
from sushihub.services.memory.pipx import InMemoryPipx
from sushihub.services.memory.ports import memory_ports

from .test_add_binary import out, said, workspace  # noqa: F401  shared fixtures

pytestmark = pytest.mark.medium


@pytest.fixture
def checkout(workspace):
    """A cloned module whose checkout carries a cli/ package pipx could install."""
    cli = workspace / "sushiruntime" / "cli"
    cli.mkdir(parents=True)
    (cli / "pyproject.toml").write_text('[project]\nname = "sushiruntime"\n', encoding="utf-8")
    (workspace / "sushiruntime" / ".git").mkdir()
    return workspace / "sushiruntime"


def add_runtime(out, installer: InMemoryPipx) -> None:
    """Run `hub add sushiruntime` against the cloned checkout with *installer* as pipx."""
    modules.add(["sushiruntime"], provision=lambda dry_run: 0,
                ports=memory_ports(console=out, pipx=installer))


def test_a_module_without_a_cli_package_is_skipped(workspace, out):
    """Skips pipx and says so when the checkout carries no cli/pyproject.toml."""
    (workspace / "sushiruntime" / ".git").mkdir(parents=True)
    installer = InMemoryPipx()
    add_runtime(out, installer)
    assert installer.installs == []
    assert said(out, "sushiruntime: no cli/ package to install; skipping CLI install.")


def test_a_missing_pipx_is_a_warning(checkout, out):
    """Warns and names the command to run later when pipx is missing."""
    add_runtime(out, InMemoryPipx(available=False))
    assert out.texts("warn") == [
        "sushiruntime: pipx not found; skipping CLI install. Install "
        f"it later with `pipx install {checkout.resolve() / 'cli'}`."]


def test_the_happy_path_installs_the_module_cli_editable(checkout, out):
    """Installs the module's cli/ with pipx, editable, and nothing else."""
    installer = InMemoryPipx()
    add_runtime(out, installer)
    assert installer.installs == [(checkout.resolve() / "cli", True)]


def test_a_failed_pipx_install_is_reported(checkout, out):
    """Says the CLI install failed when pipx exits non-zero."""
    add_runtime(out, InMemoryPipx(exit_code=1))
    assert out.texts("error") == ["sushiruntime: CLI install failed."]


def test_both_paths_install_a_module_cli_the_same_way(checkout, out):
    """`hub add` and `hub install-cli` leave the same install behind."""
    from_add, from_install_cli = InMemoryPipx(), InMemoryPipx()
    add_runtime(out, from_add)
    cli_install.install_cli(["sushiruntime"], ports=memory_ports(pipx=from_install_cli))
    assert from_install_cli.installs == from_add.installs
