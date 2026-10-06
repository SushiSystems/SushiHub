# record_cli_argv.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Records the command lines a module's CLI would run, without running them.

What is stubbed, what really runs and why the cwd changes are in tools/README.md,
"record_cli_argv.py".

Usage:  python tools/record_cli_argv.py sushiblas out.json
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

#: The unpatched Path.write_text, captured before _install_stubs() replaces it.
_REAL_WRITE_TEXT = Path.write_text

#: Module -> the repository root holding its CLI. Siblings of this checkout.
_SIBLINGS = Path(__file__).resolve().parent.parent.parent

_RECORDS: list[dict] = []


class _FakeCompleted:
    def __init__(self) -> None:
        self.returncode = 0
        self.stdout = ""
        self.stderr = ""


class _FakePopen:
    def __init__(self) -> None:
        self.stdout: list[str] = []

    def wait(self) -> int:
        return 0


def _install_stubs() -> None:
    real_run = subprocess.run
    real_popen = subprocess.Popen
    real_rmtree = shutil.rmtree

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, str):
            return real_run(cmd, *args, **kwargs)      # vcvars64: must really run
        _RECORDS.append({"kind": "run", "argv": list(cmd),
                         "cwd": str(kwargs.get("cwd", ""))})
        return _FakeCompleted()

    def fake_popen(cmd, *args, **kwargs):
        if isinstance(cmd, str):
            return real_popen(cmd, *args, **kwargs)
        _RECORDS.append({"kind": "drained", "argv": list(cmd),
                         "cwd": str(kwargs.get("cwd", ""))})
        return _FakePopen()

    def fake_rmtree(path, *args, **kwargs):
        _RECORDS.append({"kind": "rmtree", "argv": [str(path)], "cwd": ""})

    def fake_copy2(src, dst, *args, **kwargs):
        _RECORDS.append({"kind": "copy", "argv": [str(src), str(dst)], "cwd": ""})
        return str(dst)

    def fake_write_text(self, *args, **kwargs):
        _RECORDS.append({"kind": "write", "argv": [str(self)], "cwd": ""})
        return 0

    def fake_write_bytes(self, *args, **kwargs):
        _RECORDS.append({"kind": "write", "argv": [str(self)], "cwd": ""})
        return 0

    subprocess.run = fake_run
    subprocess.Popen = fake_popen
    shutil.rmtree = fake_rmtree
    shutil.copy2 = fake_copy2
    Path.write_text = fake_write_text
    Path.write_bytes = fake_write_bytes


def _matrix(project, module: str) -> list[tuple[str, dict]]:
    """Every command worth recording, as (function name, kwargs).

    Built by reflection so a module that lacks a command simply contributes
    fewer records rather than raising -- and so a command *appearing* or
    *disappearing* shows up in the diff as a changed record count.
    """
    calls: list[tuple[str, dict]] = []
    build_types = list(getattr(project, "BuildType", []))
    suites = list(getattr(project, "Suite", []))

    if hasattr(project, "build"):
        for bt in build_types:
            calls.append(("build", {"build_type": bt}))
        calls.append(("build", {"build_type": build_types[0], "clean": True}))
    if hasattr(project, "test"):
        for suite in suites:
            calls.append(("test", {"suite": suite}))
        if suites:
            calls.append(("test", {"suite": suites[0], "filter": "Foo.*", "repeat": 3}))
    if hasattr(project, "run"):
        calls.append(("run", {}))
    if hasattr(project, "clean"):
        calls.append(("clean", {}))
    if hasattr(project, "doxygen"):
        calls.append(("doxygen", {}))
    return calls


def main(argv: list[str]) -> int:
    """Capture one module's argv. Contract: one capture per process, not one per call.

    ``importlib.import_module`` caches the target's ``<module>.services.project``
    (and everything it imports) in ``sys.modules`` for the life of the process.
    A second in-process call -- for a different module, or the same one again --
    would silently reuse that cached import rather than re-reading whatever is on
    disk now. For this tool that is the one wrong answer that must never happen:
    a stale cached module compared against fresh disk state reports "no diff"
    when the two were never actually compared. So this is invoked once per
    process (`python tools/record_cli_argv.py <module> <out.json>`, one process
    per module) and never looped in-process.
    """
    if len(argv) != 3:
        print(__doc__)
        return 2
    module, out = argv[1], argv[2]
    # Resolved against the *invocation* cwd, before that cwd is changed below.
    out_path = Path(out).resolve()

    module_root = _SIBLINGS / module
    if not module_root.is_dir():
        print(f"No sibling checkout at {module_root}")
        return 2

    _RECORDS.clear()
    sys.path.insert(0, str(module_root / "cli"))
    _install_stubs()
    project = importlib.import_module(f"{module}.services.project")

    original_cwd = Path.cwd()
    os.chdir(module_root)
    try:
        for name, kwargs in _matrix(project, module):
            _RECORDS.append({"kind": "call", "argv": [name, json.dumps(
                {k: getattr(v, "value", v) for k, v in kwargs.items()}, sort_keys=True)],
                "cwd": ""})
            try:
                getattr(project, name)(**kwargs)
            except SystemExit as exc:
                _RECORDS.append({"kind": "exit", "argv": [str(exc.code)], "cwd": ""})
            except Exception as exc:                       # noqa: BLE001 - recorded, not raised
                _RECORDS.append({"kind": "raise", "argv": [type(exc).__name__, str(exc)],
                                 "cwd": ""})
    finally:
        os.chdir(original_cwd)

    # Path.write_text is still stubbed here; the real one, captured at import, writes the output.
    _REAL_WRITE_TEXT(out_path, json.dumps(_RECORDS, indent=1), encoding="utf-8")
    print(f"{len(_RECORDS)} records -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
