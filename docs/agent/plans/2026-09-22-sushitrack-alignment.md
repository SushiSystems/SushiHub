# SushiTrack leans on `sushicore` like its siblings

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** `sushitrack`'s CLI stops carrying its own copy of what `sushicore` already provides.
`proc.py` and `env.py` go first, because their whole job is `sushicore`'s, and a test suite
arrives ahead of them so the migration is protected rather than hoped for.

**Architecture:** Tests before the move, not after: `proc` is the spine every command runs
through, and `sushitrack`'s CLI has no test at all today. The tests pin what the code does now,
the code is then rewired to `sushicore`, and the same tests say whether anything changed. Only
after that is the smaller surface of `diag` and `discovery` worth re-measuring.

**Tech Stack:** Python 3.10+, pytest, `sushicore` 0.3.0.

**Spec:** none. This is a debt paid down rather than a feature; the measurement that justifies
it is below.

## Global Constraints

- The repository is `D:/Projects/sushitrack`, which has its own working tree and its own
  uncommitted work. **Stage by path, never `git add -A`.** Check `git status --porcelain` first.
- Do not run the build system: `cmake`, `ninja` and `ctest` are off limits, and no build
  configuration file is edited. `st build` is the owner's to run.
- **Behaviour does not change in this plan.** Every task is a move. A difference a user could
  see is a finding to report, not a thing to ship quietly.
- `sushitrack`'s CLI is argparse-based through its own `app.py`. **Whether it becomes Typer is
  not decided here** and is not in this plan.
- Python style follows `python-code-style`; comments follow `source-comments`; commit messages
  follow `commits`; prose goes through `humanizer`.

## What was measured, 2026-09-22

`sushitrack`'s CLI is 2338 lines and imports four `sushicore` modules. Its siblings import nine
to eleven:

| CLI | `sushicore` modules imported |
| --- | --- |
| sushiai, sushiblas | 11 |
| sushiruntime | 10 |
| sushidsp | 9 |
| **sushitrack** | **4** — `cli_console`, `module_config`, `profile`, `workspace` |

What it carries instead:

| File | Lines | `sushicore` equivalent | How much moves |
| --- | --- | --- | --- |
| `proc.py` | 132 | `proc.Runner` | All of it |
| `env.py` | 133 | `build_env` | The pure helpers; the vcvars search stays (see below) |
| `services/discovery.py` | 89 | `discovery.ExecutableIndex` | The walk; the library-artifact helpers stay |
| `services/diag.py` | 269 | `diag.Diagnostics` | `config` and `env` only |
| `app.py` | 211 | — | Nothing; a separate decision |
| `config.py` | 273 | already uses `ModuleConfig` | To be re-measured |

`status` and `doctor` in `services/diag.py` stay: they check test binaries, data sets and Python
modules, which is knowledge `sushicore` has no business holding.

The model to copy is `sushidsp`, whose `env.py` is 81 lines because it imports five functions
from `sushicore.build_env` and writes only what is its own, and whose services hold
`_RUNNER = Runner(console, PROFILE.program)` at module level.

`config.py` already builds `PROFILE = ModuleProfile(name="SushiTrack", program="st",
env_prefix="ST", ...)`, so the identity `Runner` and `Diagnostics` need is there.

## Two corrections, measured 2026-09-22 after the plan was written

**Task 2 is blocked, and waiting is the owner's decision.** `sushicore.proc.Runner` catches no
`KeyboardInterrupt`, so migrating `proc.py` onto it as-is would turn Ctrl+C into a traceback.
The owner chose to move `sushitrack`'s handling into `sushicore` rather than keep a wrapper, and
another session is mid-wave in that repository with `0.4.0` already claimed, uncommitted and not
close. Both `pyproject.toml` and `docs/reference/CHANGELOG.md` there carry that session's
changes, so even a `proc.py`-only commit could not carry its own changelog line. Task 2 waits
for their release.

**`env.py` moves less than this plan claimed.** `sushicore.build_env.snapshot_windows(cfg,
console)` reads `cfg.vs_vcvars` and answers None when it is not set: it *uses* a configured
vcvars and cannot *find* one. Nothing in `sushicore` searches for one — no vswhere, no disk
scan. `sushitrack`'s `_from_vswhere` and `_from_disk_scan` are capability `sushicore` does not
have, and `sushitrack`'s `Config` is its own flat dataclass rather than a `ToolConfig`, so it
carries neither `vs_vcvars` nor `expand`.

What still moves: `merge_env`, `prepend_path`, `parse_windows_set`, `read_cache` and
`write_cache`. What stays: the vcvars search, and `_snapshot_windows` thinned down to "find one
locally, then parse through `sushicore`". Finding a vcvars is worth its own look in `sushicore`
later, since five CLIs would want it; that is recorded rather than built here.

## Why the tests come first

`proc.run` is called by every service in the repository. There is no test in
`cli/sushitrack_cli/` — no `tests/` directory, no pytest configuration, no `test` extra — so a
regression in it would reach a user before it reached anyone else. Three bugs of the
"this reached the real machine" class were caught by tests elsewhere in this programme on
2026-09-22 alone.

The suite this plan adds is deliberately narrow: the two modules being moved, and nothing else.
It is not an answer to "what should sushitrack's CLI test?", which is a larger question. It is
the harness the move needs.

---

### Task 1: A test harness, and what `proc` and `env` do today

**Files:**
- Modify: `cli/pyproject.toml` — a `test` extra
- Create: `cli/tests/__init__.py`, `cli/tests/conftest.py`
- Create: `cli/tests/test_proc.py`, `cli/tests/test_env.py`
- Modify: `docs/CONTRIBUTING.md` — how to run them

**Interfaces:**
- Consumes: nothing.
- Produces: `python -m pytest cli/tests -q` green, pinning today's behaviour.

- [ ] **Step 1: Copy the harness a sibling already has**

`D:/Projects/sushidsp/cli/tests/conftest.py` and `D:/Projects/sushidsp/cli/pyproject.toml` show
the shape: a `test = ["pytest>=7.0"]` extra and a conftest that keeps a test off the real
machine. Read both. Match them rather than inventing a second convention.

- [ ] **Step 2: Pin `proc`, without running anything real**

`cli/sushitrack_cli/proc.py` holds `which`, `_resolve`, `format_command`, `run`, `run_drained`,
`capture` and `tool_version`. Cover what a caller depends on, one test each:

- `which` prefers an explicit env's PATH over the process's own;
- `format_command` quotes what a shell would need quoted;
- `run` returns the child's exit code;
- `run` answers 127 with a message rather than a traceback when the executable is missing —
  the file's own docstring calls this the most common failure, so it is the behaviour most
  worth pinning;
- `capture` returns the triple and does not echo unless asked;
- `tool_version` reads a version and survives a tool that is not there.

Use `sys.executable` as the program to run. A test that needs cmake, ninja or docker is not
acceptable here.

- [ ] **Step 3: Pin `env`, the same way**

`cli/sushitrack_cli/env.py` holds `find_vcvars`, `_snapshot_windows`, `_merge`, `load_build_env`
and the `.sushitrack_env.json` cache. The pure parts are testable directly: `_merge`'s overlay
rule, and the cache's write-then-read round trip including what happens when the key changes.

`_snapshot_windows` runs `vcvars64.bat`. Do not run it. Patch the capture it goes through and
assert what it does with the output it is handed. Say in the report which functions are covered
and which are not, and why.

- [ ] **Step 4: Verify and commit**

```bash
cd /d/Projects/sushitrack
python -m pytest cli/tests -q
git add cli/pyproject.toml cli/tests docs/CONTRIBUTING.md
git commit -m "test(cli): pin what proc and env do, before they move to sushicore"
```

Do not push.

---

### Task 2: `proc` becomes `sushicore.proc.Runner`

**Files:**
- Modify: `cli/sushitrack_cli/proc.py`
- Modify: every caller the grep in step 1 finds
- Modify: `cli/tests/test_proc.py` — where a test names a moved function
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: task 1's tests.
- Produces: one process runner in the stack, not two.

- [ ] **Step 1: Read both, then list every caller**

```bash
grep -rn "proc\." cli/sushitrack_cli --include=*.py | grep -v __pycache__
```

`sushicore.proc.Runner` takes a console and a program name and offers `resolve_exe`, `run` and
`run_drained`. `sushitrack`'s module offers the same as free functions plus `capture`,
`format_command` and `tool_version`. Say in the report what `sushicore` does **not** cover, and
keep exactly that in `proc.py`; do not push a sushitrack-specific helper into a shared library
to make the file disappear.

- [ ] **Step 2: Wire the Runner the way a sibling does**

`D:/Projects/sushidsp/cli/sushidsp/services/project.py:90` is the pattern:
`_RUNNER = Runner(console, PROFILE.program)` at module level. `sushitrack`'s `PROFILE` is in
`cli/sushitrack_cli/config.py`.

`proc.py` keeps its name and its module-level functions, now delegating, so no caller changes
shape. A module that every service imports is not the place to change a calling convention and
a dependency at once.

- [ ] **Step 3: Check the two behaviours that differ if they differ**

The missing-executable path and the command echo are the two places the two implementations
could disagree. Run task 1's tests: they were written against the old behaviour, so a failure
here is the answer to "did anything change?". Paste the result either way.

If `sushicore`'s message differs from `sushitrack`'s, that is a user-visible difference. Report
it and stop rather than choosing one.

- [ ] **Step 4: Verify and commit**

```bash
python -m pytest cli/tests -q
python -m compileall -q <every changed file>
st doctor          # a real command through the new runner; paste it
git commit -m "refactor(cli): run processes through sushicore"
```

---

### Task 3: `env` becomes `sushicore.build_env`

**Files:**
- Modify: `cli/sushitrack_cli/env.py`
- Modify: `cli/tests/test_env.py`
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: task 2's green suite.
- Produces: an `env.py` that holds only what is SushiTrack's.

- [ ] **Step 1: Read the model before the source**

`D:/Projects/sushidsp/cli/sushidsp/env.py` is 81 lines and imports `merge_env`, `prepend_path`,
`read_cache`, `snapshot_windows` and `write_cache`. `sushitrack`'s is 133 and does all five
itself. Read both side by side and list, in the report, which of the five are line-for-line the
same job.

- [ ] **Step 2: Mind the cache**

`sushitrack` caches at `.sushitrack_env.json`. `sushicore.build_env.read_cache`/`write_cache`
take the file and a key. Keep the same filename and make the key mean the same thing it means
now, or a developer's first build after this lands silently re-runs vcvars — harmless, but it
is a behaviour change and it must be a deliberate one. Say in the report what the key was and
what it became.

- [ ] **Step 3: Verify and commit**

```bash
python -m pytest cli/tests -q
st env             # paste it; this is what the module exists for
git commit -m "refactor(cli): assemble the build environment through sushicore"
```

---

### Task 4: Re-measure, then close

**Files:**
- Modify: `docs/reference/CHANGELOG.md`, `docs/README.md` if it describes the CLI's layout
- Modify: `D:/Projects/sushistack/docs/design/REMAINING_WORK.md`

- [ ] **Step 1: Measure what is left**

```bash
wc -l cli/sushitrack_cli/*.py cli/sushitrack_cli/services/*.py | sort -rn
python -c "..."   # the sushicore-module count from 'What was measured' above
```

State the new line count and the new module count. `discovery` and `diag` were measured at a
partial overlap before this plan; with `proc` and `env` gone, re-measure rather than trusting
the earlier figure.

- [ ] **Step 2: Say what is left and what it is worth**

Record in `REMAINING_WORK.md`, in SushiStack, since that is where this programme's backlog
lives: what `discovery` and `diag` could still take from `sushicore`, and that the argparse
command layer is undecided. A number with a date is worth more than an intention.

The deferred `st setup` becomes cheap once `cli/tests/` exists; say so there too.

- [ ] **Step 3: Commit in both repositories**

---

## Order

```
Task 1 (tests)  ->  Task 2 (proc)  ->  Task 3 (env)  ->  Task 4 (measure and close)
```

Strictly serial. Task 1 exists to make tasks 2 and 3 checkable, so it cannot move.

## What this plan does not do

- The argparse command layer stays. Whether `st` becomes Typer like its five siblings is a
  user-visible decision and is not taken here.
- `status` and `doctor` stay where they are. They know about data sets and test binaries, which
  is not `sushicore`'s business.
- `st setup` is still deferred. This plan makes it cheaper by leaving a test harness behind, but
  does not write it.
- `sushiruntime` carries the same debt in `env.py`, at 188 lines with no `build_env` import.
  Nothing here touches it; it is worth its own look.
