# test_tool_paths.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Which values of a workspace file move when the dependency root moves."""

from __future__ import annotations

from sushicore.config_base import write_toml_document
from sushicore.workspace import WORKSPACE_HEADER, read_toml

from sushihub.services.tool_paths import rewrite_tool_paths


def _write(path, tool: dict, modules: dict | None = None) -> None:
    """Write a workspace file holding *tool* and, when given, a ``[modules]`` table."""
    tables = {"workspace": {"version": "1"}, "tool": tool}
    if modules:
        tables["modules"] = modules
    write_toml_document(path, tables, WORKSPACE_HEADER)


def test_values_under_the_old_root_move_to_the_new_root(tmp_path):
    """A path under the old root, in [tool] or a platform table, names the new root."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "ws" / "dependencies", tmp_path / "deps"
    _write(target, {
        "toolchain": "intel-llvm",
        "vcpkg_root": f"{old.as_posix()}/vcpkg",
        "windows": {"llvm_root": f"{old.as_posix()}/toolchains/llvm-sycl"},
    })
    assert rewrite_tool_paths(target, old, new) == 2
    tool = read_toml(target)["tool"]
    assert tool["vcpkg_root"] == f"{new.as_posix()}/vcpkg"
    assert tool["windows"]["llvm_root"] == f"{new.as_posix()}/toolchains/llvm-sycl"
    assert tool["toolchain"] == "intel-llvm"


def test_a_value_equal_to_the_old_root_moves(tmp_path):
    """A value that is the old root itself becomes the new root."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    _write(target, {"deps_root": old.as_posix()})
    assert rewrite_tool_paths(target, old, new) == 1
    assert read_toml(target)["tool"]["deps_root"] == new.as_posix()


def test_a_sibling_folder_with_a_longer_name_is_left_alone(tmp_path):
    """A path that only shares the old root's leading characters does not move."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    value = f"{old.as_posix()}.pre-migrate/vcpkg"
    _write(target, {"vcpkg_root": value, "cmake_exe": "C:/Program Files/CMake/bin/cmake.exe"})
    before = target.read_text(encoding="utf-8")
    assert rewrite_tool_paths(target, old, new) == 0
    assert target.read_text(encoding="utf-8") == before


def test_other_tables_are_written_back_unchanged(tmp_path):
    """The [modules] table survives a rewrite, even when it names the old root."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    _write(target, {"vcpkg_root": f"{old.as_posix()}/vcpkg"},
           modules={"sushiai": f"{old.as_posix()}/checkout"})
    rewrite_tool_paths(target, old, new)
    document = read_toml(target)
    assert document["modules"] == {"sushiai": f"{old.as_posix()}/checkout"}
    assert document["workspace"] == {"version": "1"}


def test_a_rewrite_back_restores_the_file(tmp_path):
    """Swapping the roots puts every value back."""
    target = tmp_path / "workspace.toml"
    old, new = tmp_path / "dependencies", tmp_path / "deps"
    _write(target, {"vcpkg_root": f"{old.as_posix()}/vcpkg"})
    before = target.read_text(encoding="utf-8")
    rewrite_tool_paths(target, old, new)
    assert rewrite_tool_paths(target, new, old) == 1
    assert target.read_text(encoding="utf-8") == before


def test_a_missing_file_is_not_created(tmp_path):
    """A workspace with no file has nothing to rewrite and gets no file."""
    target = tmp_path / "workspace.toml"
    assert rewrite_tool_paths(target, tmp_path / "a", tmp_path / "b") == 0
    assert not target.exists()
