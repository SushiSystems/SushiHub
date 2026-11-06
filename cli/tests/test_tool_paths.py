# test_tool_paths.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which values of a workspace file move when the dependency root moves."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sushicore.config_base import write_toml_document
from sushicore.workspace import WORKSPACE_HEADER, read_toml

from sushihub.services.tool_paths import moved_document, rewrite_tool_paths

K_OLD = Path("/ws/dependencies")
K_NEW = Path("/deps")


def _write(path, tool: dict, modules: dict | None = None) -> None:
    """Write a workspace file holding *tool* and, when given, a ``[modules]`` table."""
    tables = {"workspace": {"version": "1"}, "tool": tool}
    if modules:
        tables["modules"] = modules
    write_toml_document(path, tables, WORKSPACE_HEADER)


def _filled(table: dict, old: str, new: str) -> dict:
    """Return *table* with ``{old}`` and ``{new}`` replaced by the two roots, nested tables too."""
    return {key: _filled(value, old, new) if isinstance(value, dict)
            else value.replace("{old}", old).replace("{new}", new)
            for key, value in table.items()}


@pytest.mark.small
@pytest.mark.parametrize(("tool", "moved", "count"), [
    ({"toolchain": "intel-llvm", "vcpkg_root": "{old}/vcpkg",
      "windows": {"llvm_root": "{old}/toolchains/llvm-sycl"}},
     {"toolchain": "intel-llvm", "vcpkg_root": "{new}/vcpkg",
      "windows": {"llvm_root": "{new}/toolchains/llvm-sycl"}}, 2),
    ({"deps_root": "{old}"}, {"deps_root": "{new}"}, 1),
], ids=["under-the-old-root", "equal-to-the-old-root"])
def test_values_at_or_under_the_old_root_move_to_the_new_root(tool, moved, count):
    """A path under the old root, or the old root itself, in [tool] or a platform table, names the new root."""
    document = {"workspace": {"version": "1"},
                "tool": _filled(tool, K_OLD.as_posix(), K_NEW.as_posix())}
    result, changed = moved_document(document, K_OLD, K_NEW)
    assert (result["tool"], changed) == (_filled(moved, K_OLD.as_posix(), K_NEW.as_posix()), count)


@pytest.mark.small
def test_a_sibling_folder_with_a_longer_name_is_left_alone():
    """A path that only shares the old root's leading characters does not move."""
    tool = {"vcpkg_root": f"{K_OLD.as_posix()}.pre-migrate/vcpkg",
            "cmake_exe": "C:/Program Files/CMake/bin/cmake.exe"}
    assert moved_document({"tool": tool}, K_OLD, K_NEW) == ({"tool": tool}, 0)


@pytest.mark.small
def test_other_tables_are_returned_unchanged():
    """The [modules] table is kept as it was, even when it names the old root."""
    modules = {"sushiai": f"{K_OLD.as_posix()}/checkout"}
    document = {"workspace": {"version": "1"}, "modules": modules,
                "tool": {"vcpkg_root": f"{K_OLD.as_posix()}/vcpkg"}}
    result, _ = moved_document(document, K_OLD, K_NEW)
    assert (result["modules"], result["workspace"]) == (modules, {"version": "1"})


@pytest.mark.medium
def test_the_file_is_not_written_when_no_value_moves(tmp_path):
    """A file with nothing under the old root is left byte for byte as it was."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    _write(target, {"vcpkg_root": f"{old.as_posix()}.pre-migrate/vcpkg"})
    before = target.read_text(encoding="utf-8")
    assert rewrite_tool_paths(target, old, new) == 0
    assert target.read_text(encoding="utf-8") == before


@pytest.mark.medium
def test_other_tables_are_written_back_unchanged(tmp_path):
    """The [modules] table survives a rewrite of the file, even when it names the old root."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    _write(target, {"vcpkg_root": f"{old.as_posix()}/vcpkg"},
           modules={"sushiai": f"{old.as_posix()}/checkout"})
    rewrite_tool_paths(target, old, new)
    document = read_toml(target)
    assert document["modules"] == {"sushiai": f"{old.as_posix()}/checkout"}
    assert document["workspace"] == {"version": "1"}


@pytest.mark.medium
def test_a_rewrite_back_restores_the_file(tmp_path):
    """Swapping the roots puts every value back."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    _write(target, {"vcpkg_root": f"{old.as_posix()}/vcpkg"})
    before = target.read_text(encoding="utf-8")
    rewrite_tool_paths(target, old, new)
    assert rewrite_tool_paths(target, new, old) == 1
    assert target.read_text(encoding="utf-8") == before


@pytest.mark.medium
def test_a_missing_file_is_not_created(tmp_path):
    """A workspace with no file has nothing to rewrite and gets no file."""
    target = tmp_path / "workspace.toml"
    assert rewrite_tool_paths(target, tmp_path / "a", tmp_path / "b") == 0
    assert not target.exists()


@pytest.mark.medium
@pytest.mark.skipif(sys.platform != "win32", reason="only Windows compares paths without case")
def test_a_drive_letter_in_another_case_still_moves(tmp_path):
    """The roots are compared the way the file system compares names."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    swapped = old.as_posix()[:1].swapcase() + old.as_posix()[1:]
    _write(target, {"vcpkg_root": f"{swapped}/vcpkg"})
    assert rewrite_tool_paths(target, old, new) == 1
