# Shared cmake driver implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the cmake driver that five `services/project.py` copies share into `sushicore`,
leaving each module's build policy where it belongs.

**Architecture:** Three new sushicore modules — `proc.py` (spawning), `cmake_cache.py` (reading
`CMakeCache.txt`), `cmake_driver.py` (cmake and ctest invocations) — composed by each CLI's
`services/project.py`, which keeps its enums, its `_configure_args`, and its `build`/`test`/`run`.
Every change is proved by diffing the argv lists that reach cmake and ctest, captured before and
after by a recorder that stubs `subprocess`.

**Tech Stack:** Python 3.10+, pytest, Typer, Rich, CMake, CTest, Ninja.

**Spec:** `docs/agent/specs/2026-08-25-cmake-driver-design.md` in this repository.

## Global Constraints

- Five consumer repositories, all checked out as siblings under `D:/Projects/`:
  `sushiruntime` (`sr`), `sushiengine` (`se`), `sushiai` (`sa`), `sushiblas` (`sb`),
  `sushidsp` (`sd`). Each has its driver at `cli/<module>/services/project.py`.
- The shared package is `D:/Projects/sushistack/sushicore/sushicore/`.
- `sushicore` depends only on `rich` and, below Python 3.11, `tomli`. Do not add a dependency.
- Nothing in `sushicore` may name a module: no `if profile.name == "SushiRuntime"`, no cache
  variable spelled `SUSHIENGINE_EXECUTION_BACKEND`. Anything module-specific is a parameter.
- Never invoke `cmake`, `ninja` or `ctest` directly, and never run a real build as part of a
  task. The evidence is the argv diff.
- Never `git stash`. Never `git add -A`. Commit by naming exact file paths, and remember that
  `git commit -- <path>` sweeps unstaged changes under that path.
- Another agent may be working in these trees. Before each commit, confirm `git status --short`
  shows only files this plan names.
- Every consumer repo's CLI test suite must pass after every task:
  `python -m pytest cli/tests -q` from that repo's root.

---

### Task 1: Give sushicore a test suite and CI

`sushicore` today has no tests and this repository has no CI workflow. Three modules that decide
what reaches a compiler are about to move in. This task is the floor they stand on.

**Files:**
- Create: `sushicore/tests/__init__.py`
- Create: `sushicore/tests/test_profile.py`
- Create: `.github/workflows/ci.yml`
- Modify: `sushicore/pyproject.toml`

**Interfaces:**
- Consumes: `sushicore.profile.ModuleProfile` (already exists).
- Produces: a runnable `python -m pytest sushicore/tests -q` from the sushistack root, and a
  GitHub Actions job that runs it. Later tasks add files to `sushicore/tests/`.

- [ ] **Step 1: Write the first test**

Create `sushicore/tests/__init__.py` as an empty file, then `sushicore/tests/test_profile.py`:

```python
"""The profile is what keeps the shared machinery from naming a module."""

from sushicore.profile import ModuleProfile


def test_env_overrides_are_prefixed_from_the_profile():
    profile = ModuleProfile(name="SushiBLAS", program="sb", env_prefix="SB")
    overrides = profile.env_overrides()
    assert overrides["cxx"] == "SB_CXX"
    assert overrides["vcpkg_root"] == "SB_VCPKG_ROOT"


def test_extra_env_overrides_win_over_the_prefix():
    profile = ModuleProfile(
        name="SushiBLAS", program="sb", env_prefix="SB",
        siblings=("sushiruntime",),
        extra_env_overrides={"sushiruntime_dir": "SUSHIRUNTIME_DIR"})
    assert profile.env_overrides()["sushiruntime_dir"] == "SUSHIRUNTIME_DIR"


def test_sibling_skip_dirs_names_every_sibling():
    profile = ModuleProfile(name="SushiAI", program="sa", env_prefix="SA",
                            siblings=("sushiruntime", "sushiblas"))
    assert set(profile.sibling_skip_dirs()) == {"sushiruntime", "sushiblas"}
```

- [ ] **Step 2: Run it**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests -q
```

Expected: 3 passed. If any assertion fails, the profile's real behaviour differs from this
plan's reading of it — fix the test to match the code, not the code to match the test. This
task adds no behaviour.

- [ ] **Step 3: Declare the test extra**

In `sushicore/pyproject.toml`, after the `dependencies` list, add:

```toml
[project.optional-dependencies]
test = ["pytest>=7.0"]
```

And extend the packages-find exclude so the tests are not installed as a top-level package:

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["sushicore*"]
exclude = ["sushicore.tests*"]
```

- [ ] **Step 4: Add the CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  sushicore:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install sushicore
        run: pip install -e "./sushicore[test]"
      - name: Test
        run: python -m pytest sushicore/tests -q
```

- [ ] **Step 5: Verify the install path still works**

```bash
cd /d/Projects/sushistack && pip install -e "./sushicore[test]" && python -m pytest sushicore/tests -q
```

Expected: install succeeds, 3 passed.

- [ ] **Step 6: Commit**

```bash
cd /d/Projects/sushistack
git add sushicore/tests/__init__.py sushicore/tests/test_profile.py \
        sushicore/pyproject.toml .github/workflows/ci.yml
git status --short
git commit -m "test(sushicore): give the shared package a suite and a CI job

Three modules that decide what reaches a compiler are about to move in.
Until now nothing in sushicore was tested and this repository ran no CI."
```

---

### Task 2: Build the argv recorder and capture the baseline

Nothing after this task is believable without it. The recorder stubs `subprocess` and
`shutil.rmtree`, drives every CLI command in every module, and writes the argv it observed to
JSON. Run before a change and after, the two files must be byte-identical.

**Files:**
- Create: `tools/record_cli_argv.py`
- Create: `sushicore/tests/test_record_cli_argv.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `python tools/record_cli_argv.py <module> <out.json>`, writing a JSON list of
  records. Each record is `{"kind": "run"|"drained"|"rmtree", "argv": [...], "cwd": str}` with
  every absolute path left as-is. Tasks 3 to 6 each call it before and after.

- [ ] **Step 1: Write the recorder**

Create `tools/record_cli_argv.py`:

```python
"""Record the command lines a module's CLI would run, without running them.

A build's output is a function of its input, and the input is exactly the argv
list that reaches cmake and ctest. So a refactor of the code that assembles that
list is proved correct by capturing the list before and after and finding no
difference -- without compiling anything, which is the only way to check the
build code on a machine that is not going to sit through five builds.

Commands whose argv is a string rather than a list are passed through untouched:
that is the vcvars64 snapshot, which must really run or the environment every
other command is measured under would be wrong.

Usage:  python tools/record_cli_argv.py sushiblas out.json
"""

from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

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

    subprocess.run = fake_run
    subprocess.Popen = fake_popen
    shutil.rmtree = fake_rmtree


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
    if len(argv) != 3:
        print(__doc__)
        return 2
    module, out = argv[1], argv[2]

    sys.path.insert(0, str(_SIBLINGS / module / "cli"))
    _install_stubs()
    project = importlib.import_module(f"{module}.services.project")

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

    Path(out).write_text(json.dumps(_RECORDS, indent=1), encoding="utf-8")
    print(f"{len(_RECORDS)} records -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 2: Test the recorder itself**

Create `sushicore/tests/test_record_cli_argv.py`:

```python
"""The recorder is the evidence, so it gets checked before it is trusted."""

import importlib.util
import subprocess
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "record_cli_argv",
    Path(__file__).resolve().parent.parent.parent / "tools" / "record_cli_argv.py")
_REC = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_REC)


def test_a_list_command_is_recorded_and_not_run():
    _REC._RECORDS.clear()
    _REC._install_stubs()
    try:
        result = subprocess.run(["definitely-not-a-real-binary", "--flag"], cwd="/tmp")
        assert result.returncode == 0
        assert _REC._RECORDS == [
            {"kind": "run", "argv": ["definitely-not-a-real-binary", "--flag"],
             "cwd": "/tmp"}]
    finally:
        importlib.reload(subprocess)


def test_rmtree_is_recorded_and_deletes_nothing(tmp_path):
    import shutil
    victim = tmp_path / "build"
    victim.mkdir()
    _REC._RECORDS.clear()
    _REC._install_stubs()
    try:
        shutil.rmtree(victim)
        assert victim.is_dir(), "the stub must not delete anything"
        assert _REC._RECORDS[0]["kind"] == "rmtree"
    finally:
        importlib.reload(shutil)
```

- [ ] **Step 3: Run it**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests -q
```

Expected: 5 passed. If `test_a_list_command_is_recorded_and_not_run` fails on Windows because
`/tmp` is not a directory, the stub is still correct — the assertion compares the recorded
string, and nothing is spawned. Change `cwd="/tmp"` to `cwd="."` and rerun.

- [ ] **Step 4: Warm every module's build environment**

The recorder passes vcvars through, but a cold cache makes the first record slow and its
warnings noisy. Warm each cache first:

```bash
for m in sushiruntime sushiengine sushiai sushiblas; do
  (cd /d/Projects/$m && python -c "
import sys; sys.path.insert(0,'cli')
import importlib, pathlib
mod='$m'
cfgm=importlib.import_module(mod+'.config')
envm=importlib.import_module(mod+'.env')
root=cfgm.find_project_root()
envm.load_build_env(cfgm.load_config(), root/'build')
print('$m warm')")
done
```

Expected: four "warm" lines. A module that errors here has a pre-existing problem; stop and
report it rather than proceeding.

- [ ] **Step 5: Capture the baseline**

```bash
cd /d/Projects/sushistack
mkdir -p .argv-baseline
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  python tools/record_cli_argv.py $m .argv-baseline/$m.json
done
```

Expected: five "N records" lines with N > 0 for each. Record the five counts in the commit
message; a later task that changes a count without meaning to has a bug.

`.argv-baseline/` is scratch, not a deliverable. Add it to `.gitignore` in the next step.

- [ ] **Step 6: Ignore the baseline directory and commit**

```bash
cd /d/Projects/sushistack
printf '\n# Scratch output of tools/record_cli_argv.py\n.argv-baseline/\n' >> .gitignore
git add tools/record_cli_argv.py sushicore/tests/test_record_cli_argv.py .gitignore
git status --short
git commit -m "test(tools): record the argv five CLIs would send to cmake

A refactor of build code is proved by capturing the command lines before
and after and finding no difference. This is the instrument that does it,
tested itself first because everything after this leans on it."
```

---

### Task 3 (D1): Move spawning into sushicore

**Files:**
- Create: `sushicore/sushicore/proc.py`
- Create: `sushicore/tests/test_proc.py`
- Modify: `sushiruntime/cli/sushiruntime/services/project.py` (drop `_resolve_exe`, `_run`,
  `_run_drained`; add wiring)
- Modify: `sushiengine/cli/sushiengine/services/project.py` (same)
- Modify: `sushiai/cli/sushiai/services/project.py` (same)
- Modify: `sushiblas/cli/sushiblas/services/project.py` (same)
- Modify: `sushidsp/cli/sushidsp/services/project.py` (same)

**Interfaces:**
- Consumes: nothing from earlier tasks except the recorder from Task 2.
- Produces:
  - `sushicore.proc.Runner(console, program)`
  - `Runner.resolve_exe(name: str, env: Mapping[str, str] | None = None) -> str`
  - `Runner.run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int`
  - `Runner.run_drained(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int`
  Tasks 5 and 6 pass a `Runner` into `CMakeDriver`.

- [ ] **Step 1: Write the failing tests**

Create `sushicore/tests/test_proc.py`:

```python
"""Spawning, and the two things four copies of it disagreed about."""

import subprocess
from pathlib import Path

import pytest

from sushicore.proc import Runner


class _Recorder:
    """Stands in for a CLI console module, capturing what was printed."""

    def __init__(self):
        self.lines = []
        self.console = self

    def command(self, text):
        self.lines.append(("command", text))

    def error(self, text):
        self.lines.append(("error", text))

    def print(self, text, **kwargs):
        self.lines.append(("print", text, kwargs))


def test_resolve_exe_falls_back_to_the_name(tmp_path):
    runner = Runner(_Recorder(), "sb")
    assert runner.resolve_exe("definitely-not-on-path") == "definitely-not-on-path"


def test_resolve_exe_reads_path_case_insensitively(tmp_path):
    exe = tmp_path / ("tool.exe" if __import__("os").name == "nt" else "tool")
    exe.write_text("")
    exe.chmod(0o755)
    runner = Runner(_Recorder(), "sb")
    assert runner.resolve_exe("tool", {"Path": str(tmp_path)}) == str(exe)


def test_not_found_message_names_the_program():
    console = _Recorder()
    runner = Runner(console, "sb")
    rc = runner.run(["no-such-binary-anywhere"], cwd=Path("."))
    assert rc == 1
    errors = [t for kind, t, *_ in console.lines if kind == "error"]
    assert errors and "sb config" in errors[0]


def test_drained_output_is_not_parsed_as_markup(monkeypatch):
    """The defect: Rich ate '[[nodiscard]]' out of ctest output in three CLIs."""
    console = _Recorder()

    class _Proc:
        stdout = iter(["note: see [[nodiscard]] here\n"])

        def wait(self):
            return 0

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: _Proc())
    runner = Runner(console, "sb")
    assert runner.run_drained(["ctest"], cwd=Path(".")) == 0
    prints = [(t, kw) for kind, t, kw in
              (l for l in console.lines if l[0] == "print")]
    assert prints[0][0] == "note: see [[nodiscard]] here"
    assert prints[0][1]["markup"] is False
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests/test_proc.py -q
```

Expected: collection error, `ModuleNotFoundError: No module named 'sushicore.proc'`.

- [ ] **Step 3: Write the implementation**

Create `sushicore/sushicore/proc.py`:

```python
"""Spawning a child process on behalf of a CLI.

Five modules carried a copy of this. Stripped of docstrings the copies differed
in exactly two places: the program name in the not-found message, and whether
Rich was told not to parse the child's output as markup. The first is what the
profile is for. The second was a defect in three of them.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Protocol


class ConsoleLike(Protocol):
    """The slice of a CLI's console module this needs."""

    console: object

    def command(self, text: str) -> None: ...

    def error(self, text: str) -> None: ...


class Runner:
    """Runs external commands and says what it ran.

    @param console A CLI's console module.
    @param program The CLI's command name ("sr", "se", ...), used in guidance.
    """

    __slots__ = ("_console", "_program")

    def __init__(self, console: ConsoleLike, program: str) -> None:
        self._console = console
        self._program = program

    def resolve_exe(self, name: str, env: Mapping[str, str] | None = None) -> str:
        """The full path to *name* from *env*'s PATH, or *name* itself.

        Resolving to a full path is what stops subprocess.CreateProcess from
        doing its own PATH lookup against a plain-dict env. On Windows that dict
        can hold both "Path" (from os.environ) and "PATH" (from a vcvars
        overlay); subprocess sees two keys and picks between them unpredictably,
        so a tool on one of the two is intermittently not found.
        """
        if env is None:
            return shutil.which(name) or name
        env_path = next((v for k, v in env.items() if k.upper() == "PATH"), None)
        return shutil.which(name, path=env_path) or shutil.which(name) or name

    def _not_found(self, name: str) -> None:
        self._console.error(
            f"Executable not found: '{name}'.\n"
            f"  - it is not on PATH and no explicit path is configured.\n"
            f"  - set its path in config.local.toml "
            f"(e.g. cmake_exe / ctest_exe / ninja_exe), or\n"
            f"  - run `{self._program} config` to see what the CLI resolved.")

    def run(self, cmd: list[str], cwd: Path,
            env: dict[str, str] | None = None) -> int:
        """Run *cmd*, letting the child inherit this process's stdout."""
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        self._console.command(subprocess.list2cmdline(resolved))
        try:
            return subprocess.run(resolved, cwd=str(cwd), env=env).returncode
        except FileNotFoundError:
            self._not_found(cmd[0])
            return 1

    def run_drained(self, cmd: list[str], cwd: Path,
                    env: dict[str, str] | None = None) -> int:
        """Run *cmd* with its output piped here and re-emitted line by line.

        Draining the pipe ourselves is what keeps ctest's gtest_discover_tests
        step reliable on Windows: when ctest's stdout is an inherited, slowly
        drained pipe, the discovery child intermittently stalls and registers
        nothing, surfacing as "No tests were found".

        markup=False because child output carries literal "[file:line]" and
        "[[nodiscard]]" tags that Rich would otherwise parse as console markup
        and silently drop.
        """
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        self._console.command(subprocess.list2cmdline(resolved))
        try:
            proc = subprocess.Popen(
                resolved, cwd=str(cwd), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
        except FileNotFoundError:
            self._not_found(cmd[0])
            return 1
        assert proc.stdout is not None
        for line in proc.stdout:
            self._console.console.print(line.rstrip("\n"), markup=False,
                                        highlight=False, soft_wrap=True)
        return proc.wait()
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests -q
```

Expected: 9 passed.

- [ ] **Step 5: Commit sushicore before touching any consumer**

```bash
cd /d/Projects/sushistack
git add sushicore/sushicore/proc.py sushicore/tests/test_proc.py
git status --short
git commit -m "feat(sushicore): own spawning, with markup off for child output

Five copies of this differed in two places: the program name in the
not-found message, which the profile already carries, and markup=False
on the drained echo, which only SushiRuntime had. The second was eating
bracketed text out of ctest output in the other three."
```

- [ ] **Step 6: Rewire SushiBLAS first (the smallest full consumer)**

In `sushiblas/cli/sushiblas/services/project.py`:

Delete the `_resolve_exe`, `_run` and `_run_drained` function definitions (lines 82 to 133 at
the time of writing; confirm by reading before deleting). In their place put:

```python
_RUNNER = Runner(console, PROFILE.program)


def _run(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
    return _RUNNER.run(cmd, cwd, env)


def _run_drained(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
    return _RUNNER.run_drained(cmd, cwd, env)


def _resolve_exe(name: str, env: dict[str, str]) -> str:
    return _RUNNER.resolve_exe(name, env)
```

Keeping the three module-level names as thin adapters means no call site changes in this task,
so the argv diff isolates the move itself. Task 5 removes the adapters.

Add to the imports:

```python
from sushicore.proc import Runner

from ..config import Config, PROFILE, find_project_root, load_config
```

(`PROFILE` is already exported by `sushiblas/cli/sushiblas/config.py`; extend the existing
`from ..config import ...` line rather than adding a second one.)

Then check whether `shutil` is still used in the file. It is — `clean_tree` and
`_deploy_consumer_dlls` call it — so leave the import. Check `subprocess` the same way; after
this edit `subprocess.list2cmdline` no longer appears, so remove `import subprocess` if
nothing else uses it.

- [ ] **Step 7: Prove SushiBLAS is unchanged**

```bash
cd /d/Projects/sushistack
python tools/record_cli_argv.py sushiblas .argv-baseline/sushiblas.after.json
diff .argv-baseline/sushiblas.json .argv-baseline/sushiblas.after.json && echo IDENTICAL
cd /d/Projects/sushiblas && python -m pytest cli/tests -q
```

Expected: `IDENTICAL`, then the SushiBLAS suite passing (14 tests at the time of writing).

- [ ] **Step 8: Repeat Steps 6 and 7 for the other four modules**

Apply the same edit to `sushiai`, `sushiengine`, `sushiruntime` and `sushidsp`, verifying each
with its own argv diff and test suite before moving to the next. Three differences to expect:

- `sushiruntime`'s not-found message ends `re-run \`ss doctor\` to check the shared dependency
  tree.` rather than `run \`sr config\``. The shared message wins; this is the one intentional
  text change in the task. Its argv diff is still identical, because the message is printed,
  not spawned. Note the wording change in the commit message.
- `sushidsp`'s `_run` takes no `env` and its `_resolve_exe` takes no `env`. Keep both
  signatures exactly as they are and pass `env=None` through:

```python
def _run(cmd: list[str], cwd: Path) -> int:
    return _RUNNER.run(cmd, cwd)


def _resolve_exe(name: str) -> str:
    return _RUNNER.resolve_exe(name)
```

  Wiring SushiDSP to `load_build_env` is explicitly out of scope; changing it here would make
  its argv diff unreadable.
- `sushidsp` has no `PROFILE` if its `config.py` predates the profile rewrite. Confirm with
  `grep -n "^PROFILE" sushidsp/cli/sushidsp/config.py`. If it is absent, use the literal
  `"sd"` and open a follow-up note rather than rewriting its config in this task.

- [ ] **Step 9: Commit each consumer separately**

```bash
cd /d/Projects/sushiblas
git status --short
git add cli/sushiblas/services/project.py
git commit -m "refactor(cli): take spawning from sushicore

The three functions this drops were byte-identical across five CLIs but
for the program name in one message. sushicore.proc.Runner owns them now,
and with it the markup=False that only SushiRuntime's copy had -- so
bracketed text stops disappearing from ctest output here."
```

Adjust the path and the closing sentence per repository: SushiRuntime already had
`markup=False`, so its message says the fix travelled outward rather than inward.

---

### Task 4 (D2): Move cache reading and reconfigure detection into sushicore

**Files:**
- Create: `sushicore/sushicore/cmake_cache.py`
- Create: `sushicore/tests/test_cmake_cache.py`
- Modify: `sushiengine/cli/sushiengine/services/project.py` (`_cached_value`,
  `_needs_configure`)
- Modify: `sushiai/cli/sushiai/services/project.py` (`_configured_build_type`,
  `_needs_configure`)
- Modify: `sushiblas/cli/sushiblas/services/project.py` (same as SushiAI)
- Modify: `sushiruntime/cli/sushiruntime/services/project.py` (`_cache_home_dir`,
  `_stale_build_tree`, and the cache read inside `_needs_configure`)

**Interfaces:**
- Consumes: `sushicore.proc.Runner` (Task 3), unchanged.
- Produces:
  - `sushicore.cmake_cache.cached_value(build_dir: Path, entry: str) -> str | None`
  - `sushicore.cmake_cache.home_directory(build_dir: Path) -> str | None`
  - `sushicore.cmake_cache.is_stale(build_dir: Path, root: Path) -> bool`
  - `sushicore.cmake_cache.generator_sentinel(generator: str) -> str`
  Task 5's `CMakeDriver.needs_configure` calls all four.

- [ ] **Step 1: Write the failing tests**

Create `sushicore/tests/test_cmake_cache.py`:

```python
"""Reading CMakeCache.txt, which is cheaper and more robust than `cmake -L`."""

from pathlib import Path

from sushicore.cmake_cache import (cached_value, generator_sentinel,
                                   home_directory, is_stale)

_CACHE = """\
# This is the CMakeCache file.
CMAKE_BUILD_TYPE:STRING=RelWithDebInfo
CMAKE_HOME_DIRECTORY:INTERNAL=/workspace/sushiengine
SUSHIENGINE_EXECUTION_BACKEND:STRING=runtime
"""


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "CMakeCache.txt").write_text(_CACHE, encoding="utf-8")
    return tmp_path


def test_cached_value_reads_an_entry(tmp_path):
    assert cached_value(_tree(tmp_path), "CMAKE_BUILD_TYPE") == "RelWithDebInfo"


def test_cached_value_is_none_for_an_absent_entry(tmp_path):
    assert cached_value(_tree(tmp_path), "NOT_PRESENT") is None


def test_cached_value_is_none_for_an_unconfigured_tree(tmp_path):
    assert cached_value(tmp_path, "CMAKE_BUILD_TYPE") is None


def test_a_prefix_does_not_match_a_longer_entry(tmp_path):
    """CMAKE_BUILD must not match CMAKE_BUILD_TYPE."""
    assert cached_value(_tree(tmp_path), "CMAKE_BUILD") is None


def test_home_directory_is_the_configured_source_path(tmp_path):
    assert home_directory(_tree(tmp_path)) == "/workspace/sushiengine"


def test_a_tree_from_another_path_is_stale(tmp_path):
    assert is_stale(_tree(tmp_path), Path("/d/Projects/sushiengine")) is True


def test_a_tree_from_this_path_is_not_stale(tmp_path):
    assert is_stale(_tree(tmp_path), Path("/workspace/sushiengine")) is False


def test_an_unconfigured_tree_is_not_stale(tmp_path):
    assert is_stale(tmp_path, Path("/anywhere")) is False


def test_the_sentinel_follows_the_generator():
    assert generator_sentinel("Ninja") == "build.ninja"
    assert generator_sentinel("Unix Makefiles") == "Makefile"
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests/test_cmake_cache.py -q
```

Expected: `ModuleNotFoundError: No module named 'sushicore.cmake_cache'`.

- [ ] **Step 3: Write the implementation**

Create `sushicore/sushicore/cmake_cache.py`:

```python
"""What a build tree says about how it was configured.

Read out of CMakeCache.txt rather than through `cmake -L`, so it costs nothing
and works on a tree whose configure failed part way through -- which is exactly
when a caller most needs to know what is in there.
"""

from __future__ import annotations

import os
from pathlib import Path

#: The file a configured tree leaves behind, per generator family.
_SENTINELS = {"Ninja": "build.ninja"}


def generator_sentinel(generator: str) -> str:
    """The build file *generator* writes, whose absence means "not configured"."""
    return _SENTINELS.get(generator, "Makefile")


def cached_value(build_dir: Path, entry: str) -> str | None:
    """The value CMake baked into *build_dir*'s cache for *entry*, or None.

    @param build_dir The build tree to inspect.
    @param entry     The cache entry's name, without its ":TYPE" suffix.
    @return The value, or None when the tree is unconfigured or lacks the entry.
    """
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        return None
    prefix = entry + ":"
    try:
        text = cache.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1].strip()
    return None


def home_directory(build_dir: Path) -> str | None:
    """The source directory *build_dir* was configured against, or None."""
    return cached_value(build_dir, "CMAKE_HOME_DIRECTORY")


def is_stale(build_dir: Path, root: Path) -> bool:
    """True when the tree was configured for a different source directory.

    A build tree carried over from another machine or path -- a container volume
    build at /workspace, reused on the Windows host -- has absolute paths baked
    into its cache that no longer exist. CTest's `if(EXISTS ...)` guards then
    fail and it reports "No tests were found" while the sources are fine. The
    comparison is case- and separator-insensitive because Windows is.
    """
    home = home_directory(build_dir)
    if not home:
        return False
    return os.path.normcase(os.path.normpath(home)) != \
        os.path.normcase(os.path.normpath(str(root)))
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests -q
```

Expected: 18 passed. Note that `test_a_prefix_does_not_match_a_longer_entry` passes only
because of the `entry + ":"` prefix; if it fails, the implementation dropped the colon.

- [ ] **Step 5: Commit sushicore**

```bash
cd /d/Projects/sushistack
git add sushicore/sushicore/cmake_cache.py sushicore/tests/test_cmake_cache.py
git status --short
git commit -m "feat(sushicore): read what a build tree says about its own configure

Four modules read CMakeCache.txt with the same six lines. The
stale-source-path check that goes with it existed in one."
```

- [ ] **Step 6: Rewire SushiBLAS and SushiAI**

In each, delete `_configured_build_type` and replace its single use inside `_needs_configure`.
The result in both files:

```python
def _needs_configure(build_dir: Path, generator: str, build_type: str = None) -> bool:
    if not build_dir.is_dir():
        return True
    if not (build_dir / generator_sentinel(generator)).is_file():
        return True
    # Single-config generators (Ninja, Make) bake CMAKE_BUILD_TYPE into the
    # cache; `cmake --build --config X` is silently ignored for them, so a tree
    # configured for another type must be reconfigured rather than reused.
    if build_type is not None and cached_value(build_dir, "CMAKE_BUILD_TYPE") != build_type:
        return True
    return False
```

with `from sushicore.cmake_cache import cached_value, generator_sentinel` added to the imports.

Note that `_configured_build_type` returns the value only when the tree is configured, whereas
`cached_value` is the same thing without the wrapper — read the old body before deleting to
confirm there is no extra condition. If there is, keep it inline in `_needs_configure`.

- [ ] **Step 7: Rewire SushiEngine**

Delete `_cached_value` and point its call sites at `cached_value`. There are three:
`_needs_configure` (twice, for `CMAKE_BUILD_TYPE` and `SUSHIENGINE_EXECUTION_BACKEND`) and
`_compile`. Confirm with:

```bash
cd /d/Projects/sushiengine && grep -rn "_cached_value" cli/
```

Every hit must be updated, including any outside `project.py`.

- [ ] **Step 8: Rewire SushiRuntime**

Delete `_cache_home_dir` and `_stale_build_tree`, and replace their uses with
`cmake_cache.is_stale(build_dir, root)`. There are two call sites: `_needs_configure` and
`test`. Confirm with:

```bash
cd /d/Projects/sushiruntime && grep -rn "_stale_build_tree\|_cache_home_dir" cli/
```

SushiRuntime's stamp-file logic stays exactly where it is; only the cache reading moves.

- [ ] **Step 9: Prove all four are unchanged**

```bash
cd /d/Projects/sushistack
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  python tools/record_cli_argv.py $m .argv-baseline/$m.after.json
  diff .argv-baseline/$m.json .argv-baseline/$m.after.json && echo "$m IDENTICAL"
done
```

Expected: five `IDENTICAL` lines. SushiDSP is unchanged in this task and must still be
recorded — a difference there would mean a shared module changed behaviour by accident.

Then each suite:

```bash
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  (cd /d/Projects/$m && echo "== $m" && python -m pytest cli/tests -q)
done
```

- [ ] **Step 10: Commit each consumer separately**

```bash
cd /d/Projects/sushiblas
git status --short
git add cli/sushiblas/services/project.py
git commit -m "refactor(cli): read the cmake cache through sushicore"
```

Repeat per repository, adjusting the path.

---

### Task 5 (D3): Move the cmake and ctest invocations into sushicore

This is the phase that touches what reaches the compiler. Do it one repository at a time and
diff after each.

**Files:**
- Create: `sushicore/sushicore/cmake_driver.py`
- Create: `sushicore/tests/test_cmake_driver.py`
- Modify: `sushiblas/cli/sushiblas/services/project.py`
- Modify: `sushiai/cli/sushiai/services/project.py`
- Modify: `sushiengine/cli/sushiengine/services/project.py`
- Modify: `sushiruntime/cli/sushiruntime/services/project.py`
- Modify: `sushidsp/cli/sushidsp/services/project.py`

**Interfaces:**
- Consumes: `sushicore.proc.Runner` (Task 3); `sushicore.cmake_cache.cached_value`,
  `generator_sentinel`, `is_stale` (Task 4).
- Produces:
  - `CMakeDriver(console, runner)`. Every method takes the resolved `cfg` as its first
    argument, so the driver holds no configuration of its own; `cfg` supplies `expand`,
    `cmake_exe`, `ctest_exe` and `doxygen_exe`.
  - `CMakeDriver.cmake(cfg) -> str`
  - `CMakeDriver.ctest(cfg) -> str`
  - `CMakeDriver.needs_configure(build_dir: Path, generator: str, *, expect:
    Mapping[str, str] | None = None, root: Path | None = None) -> bool`
  - `CMakeDriver.configure(args: Sequence[str], cwd: Path, env=None) -> int`
  - `CMakeDriver.compile(cfg, build_dir: Path, cwd: Path, env, *, config: str | None = None,
    targets: Sequence[str] = (), jobs: int | None = None) -> int`
  - `CMakeDriver.ctest_run(cfg, build_dir: Path, env, *, label_regex: str | None = None,
    filter: str | None = None, repeat: int = 0) -> int`
  - `CMakeDriver.clean_tree(build_dir: Path) -> None`
  - `CMakeDriver.doxygen(cfg, doxyfile: Path, cwd: Path, env, *, install_hint: str) -> int`

- [ ] **Step 1: Write the failing tests**

Create `sushicore/tests/test_cmake_driver.py`:

```python
"""The driver's whole contract is the argv it produces."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.cmake_driver import CMakeDriver


class _Console:
    def __init__(self):
        self.lines = []
        self.console = self

    def command(self, text): self.lines.append(text)
    def error(self, text): self.lines.append(text)
    def info(self, text): self.lines.append(text)
    def warn(self, text): self.lines.append(text)
    def success(self, text): self.lines.append(text)
    def print(self, text, **kw): self.lines.append(text)


class _Runner:
    """Captures argv instead of spawning."""

    def __init__(self):
        self.calls = []

    def resolve_exe(self, name, env=None):
        return name

    def run(self, cmd, cwd, env=None):
        self.calls.append(("run", list(cmd), str(cwd)))
        return 0

    def run_drained(self, cmd, cwd, env=None):
        self.calls.append(("drained", list(cmd), str(cwd)))
        return 0


def _cfg(**kw):
    base = dict(cmake_exe="", ctest_exe="", doxygen_exe="", generator="Ninja")
    base.update(kw)
    base["expand"] = lambda s: s
    return SimpleNamespace(**base)


def _driver():
    runner = _Runner()
    return CMakeDriver(_Console(), runner), runner


def test_cmake_defaults_to_the_bare_name():
    driver, _ = _driver()
    assert driver.cmake(_cfg()) == "cmake"
    assert driver.cmake(_cfg(cmake_exe="C:/tools/cmake.exe")) == "C:/tools/cmake.exe"


def test_compile_builds_the_expected_argv(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release")
    assert runner.calls == [
        ("run", ["cmake", "--build", str(tmp_path), "--config", "Release"],
         str(tmp_path))]


def test_compile_appends_targets_and_jobs(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Debug",
                   targets=("editor",), jobs=8)
    assert runner.calls[0][1] == [
        "cmake", "--build", str(tmp_path), "--config", "Debug",
        "--target", "editor", "-j", "8"]


def test_ctest_run_is_drained_and_carries_the_knobs(tmp_path):
    driver, runner = _driver()
    driver.ctest_run(_cfg(), tmp_path, None, label_regex="^unit$",
                     filter="Gemm.*", repeat=3)
    kind, argv, cwd = runner.calls[0]
    assert kind == "drained"
    assert argv == ["ctest", "--test-dir", str(tmp_path), "--output-on-failure",
                    "-L", "^unit$", "-R", "Gemm.*", "--repeat", "until-fail:3"]
    assert cwd == str(tmp_path)


def test_ctest_run_omits_absent_knobs(tmp_path):
    driver, runner = _driver()
    driver.ctest_run(_cfg(), tmp_path, None)
    assert runner.calls[0][1] == ["ctest", "--test-dir", str(tmp_path),
                                  "--output-on-failure"]


def test_needs_configure_when_there_is_no_tree(tmp_path):
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path / "absent", "Ninja") is True


def test_needs_configure_when_the_sentinel_is_missing(tmp_path):
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja") is True


def test_no_reconfigure_when_expectations_hold(tmp_path):
    (tmp_path / "build.ninja").write_text("")
    (tmp_path / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja",
                                  expect={"CMAKE_BUILD_TYPE": "Release"}) is False


def test_reconfigure_when_an_expectation_is_violated(tmp_path):
    (tmp_path / "build.ninja").write_text("")
    (tmp_path / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja",
                                  expect={"CMAKE_BUILD_TYPE": "Debug"}) is True


def test_clean_tree_says_so_when_there_is_nothing_to_clean(tmp_path):
    console = _Console()
    driver = CMakeDriver(console, _Runner())
    driver.clean_tree(tmp_path / "absent")
    assert any("nothing to clean" in line for line in console.lines)
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests/test_cmake_driver.py -q
```

Expected: `ModuleNotFoundError: No module named 'sushicore.cmake_driver'`.

- [ ] **Step 3: Write the implementation**

Create `sushicore/sushicore/cmake_driver.py`:

```python
"""Invoking cmake and ctest on behalf of a module that has a build policy.

This knows the shape of a cmake command line. It does not know a single cache
variable's name: which -D flags a module passes, which targets it has and which
suites it runs are policy, and policy stays in the module. Everything
module-specific arrives as a parameter -- `expect` for the cache entries a tree
must already agree with, `targets` for what to build, `label_regex` for which
tests to select.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Mapping, Sequence

from .cmake_cache import cached_value, generator_sentinel, is_stale


class CMakeDriver:
    """The cmake and ctest half of what five project.py copies shared.

    @param console A CLI's console module.
    @param runner  A :class:`sushicore.proc.Runner`.
    """

    __slots__ = ("_console", "_runner")

    def __init__(self, console, runner) -> None:
        self._console = console
        self._runner = runner

    # -- executables ----------------------------------------------------

    def cmake(self, cfg) -> str:
        """The cmake executable: the configured path if set, else 'cmake'."""
        return cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else "cmake"

    def ctest(self, cfg) -> str:
        """The ctest executable: the configured path if set, else 'ctest'."""
        return cfg.expand(cfg.ctest_exe) if cfg.ctest_exe else "ctest"

    # -- configure ------------------------------------------------------

    def needs_configure(self, build_dir: Path, generator: str, *,
                        expect: Mapping[str, str] | None = None,
                        root: Path | None = None) -> bool:
        """Whether *build_dir* must be configured before it can be built.

        @param expect Cache entry to required value. A single-config generator
            bakes these into the tree, so a mismatch cannot be corrected by a
            flag on the build command and forces a reconfigure.
        @param root When given, also reject a tree configured against a
            different source path -- see :func:`sushicore.cmake_cache.is_stale`.
        """
        if not build_dir.is_dir():
            return True
        if not (build_dir / generator_sentinel(generator)).is_file():
            return True
        if root is not None and is_stale(build_dir, root):
            self._console.warn(
                "Build tree was configured for a different source path "
                "(e.g. a Docker volume build); reconfiguring from scratch.")
            return True
        for entry, wanted in (expect or {}).items():
            if cached_value(build_dir, entry) != wanted:
                return True
        return False

    def configure(self, args: Sequence[str], cwd: Path, env=None) -> int:
        """Run a configure whose argv the caller assembled."""
        return self._runner.run(list(args), cwd, env)

    # -- build ----------------------------------------------------------

    def compile(self, cfg, build_dir: Path, cwd: Path, env, *,
                config: str | None = None, targets: Sequence[str] = (),
                jobs: int | None = None) -> int:
        """Bring an already-configured tree up to date.

        @param config The configuration to build. When None it is read from the
            tree's own cache, because a caller that did not configure this tree
            has no business choosing one.
        """
        if config is None:
            config = cached_value(build_dir, "CMAKE_BUILD_TYPE") or "Release"
        cmd = [self.cmake(cfg), "--build", str(build_dir), "--config", config]
        for target in targets:
            cmd += ["--target", target]
        if jobs is not None:
            cmd += ["-j", str(jobs)]
        return self._runner.run(cmd, cwd, env)

    # -- test -----------------------------------------------------------

    def ctest_run(self, cfg, build_dir: Path, env, *,
                  label_regex: str | None = None, filter: str | None = None,
                  repeat: int = 0) -> int:
        """Run ctest over *build_dir*, draining its output.

        @param filter A ctest -R pattern. gtest_discover_tests registers cases
            as "Suite.Case", so this filters those names directly -- a richer
            alternative to --gtest_filter.
        @param repeat Re-run each selected test until it fails or this many runs
            pass, the native ctest way to flush out flakiness.
        """
        cmd = [self.ctest(cfg), "--test-dir", str(build_dir), "--output-on-failure"]
        if label_regex:
            cmd += ["-L", label_regex]
        if filter:
            cmd += ["-R", filter]
        if repeat > 0:
            cmd += ["--repeat", f"until-fail:{repeat}"]
            self._console.info(
                f"Repeating each test up to {repeat}x (stop on first failure).")
        return self._runner.run_drained(cmd, build_dir, env)

    # -- clean ----------------------------------------------------------

    def clean_tree(self, build_dir: Path) -> None:
        """Remove *build_dir* and say what happened either way."""
        if build_dir.is_dir():
            self._console.info(f"Removing {build_dir}...")
            shutil.rmtree(build_dir, ignore_errors=True)
            self._console.success(f"{build_dir} removed.")
        else:
            self._console.info(f"{build_dir} does not exist, nothing to clean.")

    # -- docs -----------------------------------------------------------

    def doxygen(self, cfg, doxyfile: Path, cwd: Path, env, *,
                install_hint: str) -> int:
        """Run Doxygen over *doxyfile*, or explain why it cannot.

        @param install_hint Platform installation guidance, appended to the
            not-installed message. The module supplies it because the message
            names the module's own config file.
        """
        if not doxyfile.is_file():
            self._console.error(f"Doxyfile not found at {doxyfile}.")
            return 1
        doxy = cfg.expand(cfg.doxygen_exe) if cfg.doxygen_exe else "doxygen"
        if self._runner.resolve_exe(doxy, env) == doxy and not Path(doxy).is_file():
            self._console.error(
                "Doxygen is not installed or not on PATH.\n" + install_hint)
            return 1
        return self._runner.run([doxy, str(doxyfile)], cwd, env)
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests -q
```

Expected: 29 passed.

- [ ] **Step 5: Commit sushicore**

```bash
cd /d/Projects/sushistack
git add sushicore/sushicore/cmake_driver.py sushicore/tests/test_cmake_driver.py
git status --short
git commit -m "feat(sushicore): own the cmake and ctest command shapes

Which -D flags a module passes stays with the module; how a configure, a
build and a ctest run are spelled does not. needs_configure takes the
cache entries a tree must agree with as a mapping, so the driver never
learns a variable's name."
```

- [ ] **Step 6: Rewire SushiBLAS**

Replace `_cmake`, `_ctest`, `_needs_configure`, `clean_tree` and the three inline invocations.
After the edit `sushiblas/cli/sushiblas/services/project.py` holds:

```python
_RUNNER = Runner(console, PROFILE.program)
_DRIVER = CMakeDriver(console, _RUNNER)

_DOXYGEN_HINT = (
    "  - Windows: winget install DimitriVanHeesch.Doxygen\n"
    "  - Linux:   apt-get install -y doxygen graphviz\n"
    "  - macOS:   brew install doxygen graphviz\n"
    "  - or set doxygen_exe in config.local.toml to an existing doxygen binary.")
```

with the previous adapters (`_run`, `_run_drained`, `_resolve_exe`) removed and their call
sites changed. The three inline invocations become:

```python
    rc = _DRIVER.configure(configure_args, cwd=root, env=env)
...
    rc = _DRIVER.compile(cfg, build_dir, cwd=root, env=env, config=cmake_build_type)
...
    return _DRIVER.ctest_run(
        cfg, build_dir, env,
        label_regex=None if suite is Suite.all else _SUITE_LABEL_REGEX[suite],
        filter=filter, repeat=repeat)
```

and `_configure_args` keeps assembling its own list, calling `_DRIVER.cmake(cfg)` for argv[0].

`_needs_configure` becomes a one-line call and can be deleted in favour of its call site:

```python
    fresh = _DRIVER.needs_configure(build_dir, cfg.generator,
                                    expect={"CMAKE_BUILD_TYPE": cmake_build_type})
```

`clean_tree(root)` becomes `_DRIVER.clean_tree(_build_dir(root))`. Keep the module-level
`clean_tree(root)` function if anything outside `project.py` calls it; check with:

```bash
cd /d/Projects/sushiblas && grep -rn "clean_tree" cli/
```

- [ ] **Step 7: Prove SushiBLAS is unchanged**

```bash
cd /d/Projects/sushistack
python tools/record_cli_argv.py sushiblas .argv-baseline/sushiblas.after.json
diff .argv-baseline/sushiblas.json .argv-baseline/sushiblas.after.json && echo IDENTICAL
cd /d/Projects/sushiblas && python -m pytest cli/tests -q
```

Expected: `IDENTICAL` and a passing suite. If the diff shows a changed `rmtree` record, the
`clean_tree` rewiring changed which directory is removed — stop and fix before continuing.

- [ ] **Step 8: Commit, then repeat Steps 6 and 7 per module**

```bash
cd /d/Projects/sushiblas
git status --short
git add cli/sushiblas/services/project.py
git commit -m "refactor(cli): drive cmake and ctest through sushicore"
```

Then SushiAI, then SushiEngine, then SushiRuntime, then SushiDSP, in that order — smallest
policy first. Module-specific notes:

- **SushiAI**: `test_package` assembles its own consumer configure. Point its cmake and ctest
  calls at the driver too, but leave its argument assembly alone.
- **SushiEngine**: `_compile` and `_compile_before` stay as module functions; `_compile`'s body
  becomes a single `_DRIVER.compile(...)` call with `config=build_type`. Its `_needs_configure`
  passes two expectations:
  `expect={"CMAKE_BUILD_TYPE": build_type, "SUSHIENGINE_EXECUTION_BACKEND": backend.value}`,
  each omitted when its argument is None. Build the mapping before the call rather than passing
  None values. Its `clean` and `_remove_dir` route through `_DRIVER.clean_tree`.
  `editor.py` and `player.py` import from this module — check with
  `grep -rn "from .project import\|project\._" cli/sushiengine/`.
- **SushiRuntime**: pass `root=root` to `needs_configure` so the stale check runs, and keep the
  stamp comparison as an extra condition in the module:
  `if _DRIVER.needs_configure(...) or _stamp_differs(build_dir, stamp_key): ...`. Write
  `_stamp_differs` as a small module function holding the existing stamp logic verbatim.
  Its `doxygen` uses `root / "Doxyfile"`, not `.config/doxygen/Doxyfile`.
- **SushiDSP**: has `configure`, `build`, `test`, `doxygen` and no `run` or `clean`. Its `_run`
  still passes `env=None`; pass `None` for the driver's `env` parameter throughout.

After the last module, run the full sweep:

```bash
cd /d/Projects/sushistack
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  python tools/record_cli_argv.py $m .argv-baseline/$m.after.json
  diff .argv-baseline/$m.json .argv-baseline/$m.after.json && echo "$m IDENTICAL"
done
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  (cd /d/Projects/$m && echo "== $m" && python -m pytest cli/tests -q)
done
```

Expected: five `IDENTICAL` lines and five passing suites.

---

### Task 6 (D4): Share the two pure toolchain helpers

**Files:**
- Create: `sushicore/sushicore/toolchain_args.py`
- Create: `sushicore/tests/test_toolchain_args.py`
- Modify: `sushiblas/cli/sushiblas/services/project.py`
- Modify: `sushiai/cli/sushiai/services/project.py`
- Modify: `sushiengine/cli/sushiengine/services/project.py`
- Modify: `sushiruntime/cli/sushiruntime/services/project.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `sushicore.toolchain_args.c_compiler_for(cxx: str) -> str`
  - `sushicore.toolchain_args.vcpkg_prefix(cfg, root: Path) -> str`
  Only SushiAI and SushiBLAS keep a shared `_toolchain_args`; see the note below.

- [ ] **Step 1: Write the failing tests**

Create `sushicore/tests/test_toolchain_args.py`:

```python
"""The two pieces of toolchain-flag assembly that carry no module policy."""

from pathlib import Path
from types import SimpleNamespace

from sushicore.toolchain_args import c_compiler_for, vcpkg_prefix


def test_a_clangxx_gets_its_sibling_clang(tmp_path):
    """clang++ hardcodes C++ mode, which breaks CMake's C-language probe."""
    (tmp_path / "clang").write_text("")
    cxx = tmp_path / "clang++"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "clang")


def test_a_clangxx_without_a_sibling_is_left_alone(tmp_path):
    cxx = tmp_path / "clang++"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(cxx)


def test_a_non_clangxx_compiler_is_left_alone(tmp_path):
    assert c_compiler_for("/usr/bin/g++") == "/usr/bin/g++"


def test_the_windows_exe_suffix_is_preserved(tmp_path):
    (tmp_path / "clang.exe").write_text("")
    cxx = tmp_path / "clang++.exe"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "clang.exe")


def test_vcpkg_prefix_is_empty_without_a_root():
    cfg = SimpleNamespace(vcpkg_triplet="x64-windows",
                          resolved_vcpkg=lambda root: "")
    assert vcpkg_prefix(cfg, Path(".")) == ""


def test_vcpkg_prefix_names_the_triplet():
    cfg = SimpleNamespace(vcpkg_triplet="x64-windows",
                          resolved_vcpkg=lambda root: "C:/vcpkg")
    assert vcpkg_prefix(cfg, Path(".")) == "C:/vcpkg/installed/x64-windows"
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests/test_toolchain_args.py -q
```

Expected: `ModuleNotFoundError: No module named 'sushicore.toolchain_args'`.

- [ ] **Step 3: Write the implementation**

Create `sushicore/sushicore/toolchain_args.py`:

```python
"""Two derivations every cmake configure in this stack needs.

Only two. Assembling the full -D list is not here on purpose: SushiRuntime
splits its assembly across Windows and Linux, and SushiEngine deliberately omits
CMAKE_C_COMPILER because its runtime lane has no C sources. Both divergences are
real and documented where they live. Forcing them into one function would hide a
genuine difference behind a flag.
"""

from __future__ import annotations

from pathlib import Path


def c_compiler_for(cxx: str) -> str:
    """The C compiler slot for a clang++-personality binary: its sibling clang.

    A clang++-personality binary hardcodes C++ mode regardless of file
    extension, so pointing CMAKE_C_COMPILER at the same path breaks the
    C-language probe for a project declaring LANGUAGES CXX C. The bundled
    intel-llvm toolchain ships a sibling clang next to it for that slot.

    @param cxx The resolved C++ compiler path.
    @return The sibling clang binary, or *cxx* unchanged when there is none.
    """
    path = Path(cxx)
    stem = path.stem
    if stem.lower() == "clang++":
        sibling = path.with_name(stem[:-2] + path.suffix)
        if sibling.is_file():
            return str(sibling)
    return cxx


def vcpkg_prefix(cfg, root: Path) -> str:
    """The vcpkg installed-tree prefix for this triplet, or '' when unavailable.

    Only meaningful on Windows, where the bundled vcpkg tree is what
    find_package uses to locate GoogleTest and hwloc.
    """
    vcpkg = cfg.resolved_vcpkg(root)
    return f"{vcpkg}/installed/{cfg.vcpkg_triplet}" if vcpkg else ""
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd /d/Projects/sushistack && python -m pytest sushicore/tests -q
```

Expected: 35 passed.

- [ ] **Step 5: Commit sushicore**

```bash
cd /d/Projects/sushistack
git add sushicore/sushicore/toolchain_args.py sushicore/tests/test_toolchain_args.py
git status --short
git commit -m "feat(sushicore): share the clang sibling and vcpkg prefix derivations

Not the whole -D list: SushiRuntime splits its assembly by platform and
SushiEngine omits CMAKE_C_COMPILER on purpose. Those are real differences
and stay where they are documented."
```

- [ ] **Step 6: Rewire the four consumers**

In SushiAI and SushiBLAS, delete `_resolved_c_compiler` and `_vcpkg_prefix` and import the
shared pair. Their `_toolchain_args` stays a module function in each, still identical to the
other; note in the commit message that it was left duplicated deliberately.

`_deploy_consumer_dlls` is identical in SushiAI and SushiBLAS too, and stays where it is for
the same reason `_toolchain_args` does: it is one function shared by two modules, not five,
and it names a package layout (`bin/*.dll`, `hwloc*.dll`) belonging to those two. Moving it
would put a module's install shape into the shared package to save one copy.

In SushiEngine and SushiRuntime, replace only the inline vcpkg-prefix construction if one
exists. Confirm first:

```bash
cd /d/Projects/sushiengine && grep -n "installed/" cli/sushiengine/services/project.py
cd /d/Projects/sushiruntime && grep -n "installed/" cli/sushiruntime/services/project.py
```

If neither builds a prefix string, this step is a no-op for them — record that and move on
rather than inventing a use.

- [ ] **Step 7: Prove all five are unchanged and commit**

```bash
cd /d/Projects/sushistack
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  python tools/record_cli_argv.py $m .argv-baseline/$m.after.json
  diff .argv-baseline/$m.json .argv-baseline/$m.after.json && echo "$m IDENTICAL"
done
for m in sushiruntime sushiengine sushiai sushiblas sushidsp; do
  (cd /d/Projects/$m && echo "== $m" && python -m pytest cli/tests -q)
done
```

Then commit each consumer separately, naming its exact file path.

- [ ] **Step 8: Close out the design document**

Modify `sushistack/docs/agent/specs/2026-08-25-cmake-driver-design.md`: change the status line to name the commits
that landed each phase, and record the final line counts of the five `project.py` files
alongside their starting counts (747, 565, 724, 563, 159).

```bash
cd /d/Projects/sushistack
git add docs/agent/specs/2026-08-25-cmake-driver-design.md
git commit -m "docs: record what the cmake driver programme actually landed"
```

- [ ] **Step 9: The one check that needs a machine that builds**

Hand back to the user for a real build. The argv diffs prove the command lines are unchanged;
only a real compile proves the environment they run under still works:

```
se build
se test --suite unit
```

Do not run these. Report the argv evidence and ask.
