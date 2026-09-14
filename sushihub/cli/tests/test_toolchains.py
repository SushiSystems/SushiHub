"""The toolchain stamp keeps every field across writers and survives a crash mid-write."""

from __future__ import annotations

import json
import os
from pathlib import Path

from sushistack.setup.toolchains import (
    TOOLCHAIN_STAMP,
    _write_toolchain_stamp,
    read_toolchain_stamp,
    record_toolchain_adapter,
    toolchain_adapter_commit,
)


def test_write_toolchain_stamp_keeps_an_existing_adapters_key(tmp_path):
    record_toolchain_adapter(tmp_path, "fake", "commit1")

    _write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2")

    stamp = read_toolchain_stamp(tmp_path)
    assert stamp["tag"] == "nightly-2"
    assert stamp["adapters"]["fake"] == "commit1"


def test_record_toolchain_adapter_keeps_the_existing_source_and_tag(tmp_path):
    _write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    record_toolchain_adapter(tmp_path, "fake", "commit1")

    stamp = read_toolchain_stamp(tmp_path)
    assert stamp["source"] == "intel/llvm"
    assert stamp["tag"] == "nightly-1"
    assert stamp["adapters"]["fake"] == "commit1"


def test_toolchain_adapter_commit_reads_back_a_recorded_commit(tmp_path):
    record_toolchain_adapter(tmp_path, "fake", "commit1")

    assert toolchain_adapter_commit(tmp_path, "fake") == "commit1"
    assert toolchain_adapter_commit(tmp_path, "other") is None


def test_read_toolchain_stamp_returns_empty_on_invalid_json(tmp_path):
    (tmp_path / TOOLCHAIN_STAMP).write_text("{not json")

    assert read_toolchain_stamp(tmp_path) == {}


def test_read_toolchain_stamp_returns_empty_on_invalid_utf8(tmp_path):
    (tmp_path / TOOLCHAIN_STAMP).write_bytes(b"\xff\xfe\x00")

    assert read_toolchain_stamp(tmp_path) == {}


def test_read_toolchain_stamp_returns_empty_on_a_non_object_top_level(tmp_path):
    (tmp_path / TOOLCHAIN_STAMP).write_text(json.dumps(["not", "an", "object"]))

    assert read_toolchain_stamp(tmp_path) == {}


def test_toolchain_adapter_commit_treats_a_non_dict_adapters_as_absent(tmp_path):
    (tmp_path / TOOLCHAIN_STAMP).write_text(json.dumps({"adapters": "not-a-dict"}))

    assert toolchain_adapter_commit(tmp_path, "fake") is None


def test_record_toolchain_adapter_replaces_a_non_dict_adapters(tmp_path):
    (tmp_path / TOOLCHAIN_STAMP).write_text(json.dumps({"adapters": "not-a-dict"}))

    record_toolchain_adapter(tmp_path, "fake", "commit1")

    stamp = read_toolchain_stamp(tmp_path)
    assert stamp["adapters"] == {"fake": "commit1"}


def test_write_toolchain_stamp_is_atomic_via_a_temp_file_and_replace(tmp_path, monkeypatch):
    calls: list[tuple[str, str]] = []
    real_replace = os.replace

    def spy(src, dst):
        calls.append((Path(src).name, Path(dst).name))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)

    _write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    assert calls == [(TOOLCHAIN_STAMP + ".tmp", TOOLCHAIN_STAMP)]
    assert not (tmp_path / (TOOLCHAIN_STAMP + ".tmp")).exists()
    stamp = json.loads((tmp_path / TOOLCHAIN_STAMP).read_text())
    assert stamp["tag"] == "nightly-1"


def test_a_failing_replace_removes_the_temp_file(tmp_path, monkeypatch):
    def failing_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", failing_replace)

    _write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    assert not (tmp_path / (TOOLCHAIN_STAMP + ".tmp")).exists()
    assert not (tmp_path / TOOLCHAIN_STAMP).exists()
