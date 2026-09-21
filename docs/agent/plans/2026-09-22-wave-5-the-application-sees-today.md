# Wave 5: the application sees today's workspace

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `hub status`'s payload true — `sushicore` is not a module and stops being drawn as
one — re-record the desktop application's fixtures from a real run, and close the one Linux
default that points every build at a directory nobody has.

**Architecture:** The payload is the interface between `hub` and the application, so it is fixed
first, then the fixtures are re-recorded from it, then the application is measured against what
arrives. The Linux default is unrelated to all three and lands first because it is one line and
it removes a workaround a test is carrying.

**Tech Stack:** Python, pytest, JSON Lines, C++17, Dear ImGui, CMake, CTest, GoogleTest.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §5 wave 5.

## Global Constraints

- **No agent compiles anything.** `se`, `cmake`, `ninja` and `ctest` are off limits, and so is
  editing any build configuration file. The application's own tests therefore prove nothing an
  agent can paste; every task that needs the application built states so and leaves that
  verification to CI or to the owner. A task whose only evidence would be a build is not a task
  for an agent.
- The suite is at 359 when this wave starts. Every task ends with
  `python -m pytest sushihub/cli/tests -q` green and states its count.
- **Check CI before calling a wave closed.** Wave 3 landed a failure that only Linux showed and
  it survived two pushes, because the suite was run on Windows alone. `gh run list --workflow=CI`
  is part of the last task, not an afterthought.
- The status payload is a published contract, described in `sushihub/contract/README.md` and
  consumed by a C++ program. `api-stability` governs task 2: removing a row changes what a
  consumer reads.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`;
  C++ follows `cpp-code-style`; commit messages follow `commits`.

## The owner's decisions, 2026-09-22

- **`sushicore` leaves `hub status` entirely.** It is a PyPI dependency, not a module, and
  `pip show sushicore` answers the version question. No row, no replacement field.
- **`[tool.linux] vcpkg_root` is deleted.** Linux takes its libraries from apt — every manifest
  entry says so — and vcpkg is not used there.
- Two decisions belong to a later wave and are recorded in §3.4 of the design rather than here:
  the application ships as a separate `sushihub-gui` distribution behind a `sushihub[gui]` extra,
  versioned from the same tag as `sushihub`. **That is wave 8 and this plan does not start it.**

## What was measured, 2026-09-22

Do not re-derive these; they are why the tasks are shaped as they are.

- `sushihub/gui/tests/fixtures/events/status.jsonl` is stale in two ways at once: it lists
  `sushidsp`, which wave 2 removed from the catalog, and it shows `sushicore` as `in-repo`, which
  wave 1 made impossible. A live `hub --json status` today shows four modules and `sushicore` as
  `missing`.
- **The application already reads every field the payload carries.** `InstallFacts.cpp` reads
  `binary`, `latest_version`, `version` and `hub.source`; `InstallsScreen.cpp` draws Version and
  Platform. The design's line about wave 5 "drawing the new fields" predates that work. Task 4
  is therefore a measurement that may end in no code change, and saying so is an acceptable
  outcome.
- The payload's shape: `workspace`, `checked_updates`, `hub`, `modules`, `dependencies`. A module
  row carries `name`, `location`, `state`, `presence`, `version`, `source`, `binary`,
  `latest_version`.
- The built application is `sushihub_gui.exe` at 2.4 MB with `glfw3.dll` at 484 KB beside it. The
  262 MB under `sushihub/gui/build` is the build tree, not the product. This matters to wave 8,
  not to this wave.

---

### Task 1: Linux stops being pointed at a vcpkg tree it does not use

**Files:**
- Modify: `sushihub/cli/sushistack/defaults.toml`
- Modify: `sushihub/cli/tests/test_gui_build.py`
- Modify: `docs/design/REMAINING_WORK.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `resolved_vcpkg` answers `""` on Linux unless a workspace pins a root.

- [ ] **Step 1: See the defect before removing it**

```bash
grep -n "use_vcpkg\|vcpkg_root" sushihub/cli/sushistack/defaults.toml
grep -rn "use_vcpkg" /d/Projects/sushicore/sushicore/
```

`[tool.linux]` sets `use_vcpkg = false` and `vcpkg_root = "~/vcpkg"`.
`sushicore.stack_config.resolved_vcpkg` never reads `use_vcpkg`: it returns `vcpkg_root` when one
is set, else the provisioned tree. So on Linux every build is handed
`-DCMAKE_TOOLCHAIN_FILE=~/vcpkg/scripts/buildsystems/vcpkg.cmake`, a path most machines do not
have, while `dependencies/vcpkg` is ignored.

- [ ] **Step 2: Delete the line**

Remove `vcpkg_root = "~/vcpkg"` from `[tool.linux]`. Leave `use_vcpkg` where it is: the owner's
decision was to delete the dead path, not to change `sushicore`. Keep the backlog entry that
records `use_vcpkg` being declared and read by nothing, and add one sentence saying the Linux
default that made it harmful is gone, so the remaining item is tidiness rather than a defect.

- [ ] **Step 3: Drop the workaround the test is carrying**

`tests/test_gui_build.py`'s `provisioned` fixture writes a `workspace.toml` clearing
`vcpkg_root`, added on 2026-09-22 so the test asked the same question on both platforms. With the
Linux default gone the platforms agree by themselves. Remove the write and the paragraph of the
docstring that explains it; keep the fixture's first line.

Do not remove it and leave the docstring, and do not leave it in place "to be safe": a fixture
that neutralises a default nobody sets any more is a lie about what the test needs.

- [ ] **Step 4: Prove it on the Linux layer, which is the only place it showed**

An agent on Windows cannot see this by running the suite. Load both layers directly and print
what each platform resolves:

```bash
python - <<'EOF'
import sys, pathlib, tempfile
sys.path.insert(0, 'sushihub/cli')
from sushicore.config_base import load_tool_config
from sushistack.gui_config import GuiConfig, GUI_PROFILE
from sushistack.config import packaged_defaults

target = pathlib.Path(tempfile.mkdtemp()) / "workspace.toml"
target.write_text("", encoding="utf-8")
with packaged_defaults() as d:
    for plat in ("linux", "windows"):
        cfg = load_tool_config(GuiConfig, [d, target], plat, GUI_PROFILE.env_overrides())
        print(plat, repr(cfg.vcpkg_root))
EOF
```

Expected after the change: `linux ''` and `windows ''`. Paste it.

- [ ] **Step 5: Test and commit**

```bash
python -m pytest sushihub/cli/tests -q
git add sushihub/cli/sushistack/defaults.toml sushihub/cli/tests/test_gui_build.py docs/design/REMAINING_WORK.md
git commit -m "fix(cli): stop pointing Linux builds at a vcpkg tree it never uses"
```

---

### Task 2: `sushicore` leaves the status table

**Files:**
- Modify: `sushihub/cli/sushistack/services/status_report.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/contract/README.md`
- Modify: `sushihub/cli/tests/test_status_payload.py`, and any other test the grep below finds

**Interfaces:**
- Consumes: task 1's green suite.
- Produces: a `modules` list holding modules alone. `sushicore_dir` and `_sushicore_row` are gone.

- [ ] **Step 1: Find everything that knows about the row**

```bash
grep -rn "sushicore_dir\|_sushicore_row\|SUSHICORE_NAME" sushihub --include=*.py --include=*.md \
  | grep -v "build/lib\|__pycache__"
```

Measured 2026-09-22, so that the task removes the row and not more than the row:

| Name | Where | Fate |
| --- | --- | --- |
| `_sushicore_row` | `status_report.py:86`, called at 123 | deleted |
| `sushicore_dir` | `modules.py:41`; its only product caller is that row | deleted, with `tests/test_cli_install.py:46-60` |
| `SUSHICORE_NAME` | `modules.py:27`, also used at 225 by `hub link sushicore`'s refusal | **stays** |

`SUSHICORE_NAME` is the trap. Deleting it breaks the message that tells a user `sushicore` is not
a module, which is the one place the name still belongs. `tests/test_catalog.py:48` asserts it is
absent from the catalog and stays as it is.

- [ ] **Step 2: Remove the row and the function behind it**

Delete `_sushicore_row`, its call and `modules.sushicore_dir`, and narrow `status_report.py:24`'s
import to what is left. `build_status`'s `rows` then holds exactly the catalog's modules.

The `hub` entry in the payload stays as it is. It describes `hub` itself, not a module, and it
already lives outside the `modules` list.

- [ ] **Step 3: Say it in the contract, which a C++ program reads**

`sushihub/contract/README.md` never names `sushicore` — checked 2026-09-22, the grep is empty —
so there is nothing to correct and something to add. Where it describes the `modules` list, say
that the list carries the catalog's modules and nothing else, and that `sushicore` had a row
until 2026-09-22. A consumer still looking for that row finds nothing and must not read the
absence as an error.

- [ ] **Step 4: Follow the tests, and write the one that pins the absence**

Every test asserting a `sushicore` row changes. Add one that states the new rule directly:

```python
def test_sushicore_is_not_a_module_row(...):
    """sushicore is a PyPI dependency; the module list carries modules alone."""
    payload = build_status(...)
    assert [row["name"] for row in payload["modules"]] == [...]
    assert all(row["name"] != "sushicore" for row in payload["modules"])
```

- [ ] **Step 5: Look at it**

```bash
hub status
hub --json status
```

Paste both. Four module rows, no `sushicore`, and the JSON `modules` list matching the table.

- [ ] **Step 6: Commit**

```bash
git add sushihub/cli/sushistack/services/status_report.py sushihub/cli/sushistack/services/modules.py sushihub/contract/README.md sushihub/cli/tests/
git commit -m "fix(cli)!: stop reporting sushicore as a module"
```

---

### Task 3: The fixtures are re-recorded from a real run

**Files:**
- Modify: `sushihub/gui/tests/fixtures/events/status.jsonl`
- Modify: `sushihub/gui/tests/fixtures/events/all_kinds.jsonl`, `doctor.jsonl` — only where they
  carry the same staleness; check each
- Modify: `sushihub/gui/tests/fixtures/describe.json`, `all_types.json` — same check
- Modify: `sushihub/gui/tests/fixtures/README.md`

**Interfaces:**
- Consumes: task 2's payload.
- Produces: fixtures that match what `hub` prints today.

- [ ] **Step 1: Record, do not hand-edit**

`sushihub/gui/tests/fixtures/README.md` splits the files into **recorded** and the other kind, and
prints the three commands that make the recorded ones. It says they were last recorded on
2026-09-15. Read it first and run exactly what it gives:

```bash
cd sushihub/gui/tests/fixtures
hub --json status > events/status.jsonl
hub --json doctor > events/doctor.jsonl
hub --describe    > describe.json
```

Whatever the README calls the other kind is made the way the README says, not by recording. A
hand-written fixture that claims to be a recording is worse than a stale one. Update the README's
"last on 2026-09-15" to today in the same commit.

- [ ] **Step 2: Scrub what is this machine's and not the contract's**

A recording from this machine carries `D:\Projects\...` paths, a `last_fetch` timestamp and a
branch state (`main +6`). Read the README: if the fixtures are meant to be machine-neutral,
replace those the way it says. If they are meant to be a verbatim capture, leave them and say so.
Decide from the README, not from taste, and state which you found.

- [ ] **Step 3: Diff the old against the new and account for every change**

```bash
git diff sushihub/gui/tests/fixtures/
```

Expected differences and nothing else: `sushidsp` gone (wave 2), `sushicore` gone (task 2),
paths and timestamps if step 2 kept them. A difference you cannot name is a signal that something
else changed in the payload without anyone noticing; report it instead of committing it.

- [ ] **Step 4: Commit**

The application's tests read these fixtures and are the real check, and no agent may run them.
Say plainly in the report that the fixtures were not validated by a build, and leave that to
task 4.

```bash
git add sushihub/gui/tests/fixtures
git commit -m "test(gui): re-record the fixtures from today's hub"
```

---

### Task 4: Measure what the application does with the new payload — owner step

**Files:** decided by the measurement; possibly none.

This task is the owner's because its only evidence is a build.

- [ ] **Step 1: Build and run the application's tests**

```bash
hub gui build
hub gui test
```

The parsers are `sushihub/gui/src/contract/` and `sushihub/gui/src/model/InstallFacts.cpp`; the
screen is `src/ui/screens/InstallsScreen.cpp`. A failure here is a place the C++ assumed a row
that task 2 removed.

- [ ] **Step 2: Look at the Installs screen**

```bash
hub gui run
```

Four modules, no `sushicore`, and the fields already drawn (Version, Platform, the update line)
still populated from the real payload.

- [ ] **Step 3: Decide whether anything is owed**

The measurement of 2026-09-22 says the application already reads every field the payload carries,
so the expected outcome is no code change. If the screen is missing something, that is a finding
for its own task rather than a patch smuggled into this one.

---

### Task 5: Close the wave

**Files:**
- Modify: `docs/design/WORKSPACE_DECOUPLING.md`, `docs/design/REMAINING_WORK.md`
- Modify: `docs/reference/CHANGELOG.md`
- Modify: `sushihub/gui/README.md` — only if it describes the status table's rows

- [ ] **Step 1: Record the wave and the decision that outlived it**

Wave 5's row gains its landing date and what was verified. §3.4 gains the application's
distribution decision — a separate `sushihub-gui` distribution behind a `sushihub[gui]` extra,
platform wheels, versioned from the same tag — as **wave 8**, with the measurement that makes it
cheap: the product is about 3 MB per platform, not the 262 MB build tree. Add the wave 8 row to
both wave tables.

- [ ] **Step 2: Changelog**

```
- 2026-09-22 — Stopped reporting `sushicore` as a module in `hub status` (`sushihub/cli/sushistack/services/status_report.py`).
- 2026-09-22 — Stopped pointing Linux builds at `~/vcpkg`, which Linux never uses (`sushihub/cli/sushistack/defaults.toml`).
- 2026-09-22 — Re-recorded the desktop application's fixtures from a live `hub` (`sushihub/gui/tests/fixtures/`).
```

- [ ] **Step 3: Check CI, then say the wave is closed**

```bash
git push
gh run list --limit 3 --workflow=CI
```

Green on all four jobs, or the wave is not closed. This step exists because wave 3 was called
closed while CI was red.

- [ ] **Step 4: Commit**

```bash
git add docs sushihub/gui/README.md
git commit -m "docs: record that the application sees today's workspace"
```

---

## Order

```
Task 1 (linux vcpkg)  ->  Task 2 (the row)  ->  Task 3 (fixtures)  ->  Task 4 (owner builds)  ->  Task 5 (docs)
```

Strictly serial. Task 1 is independent of the rest and goes first only because it is one line and
frees a test from a workaround. Task 4 is the owner's.

## What this wave does not do

- The application is not distributed. That is wave 8, decided on 2026-09-22 and recorded in the
  design; an install from PyPI still has no desktop application until then.
- `use_vcpkg` stays declared and unread. Task 1 removes the default that made it harmful; making
  the key mean something is a `sushicore` change affecting seven CLIs.
- The `[cli]` theme still cannot be set in `workspace.toml`. `LazyConsole` takes a directory and
  appends the old file names; changing that is a `sushicore` change too.
- The packaged manifests still assume an unzipped install.
