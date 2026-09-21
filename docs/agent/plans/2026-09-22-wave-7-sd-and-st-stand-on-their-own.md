# Wave 7: `sd` and `st` stand on their own

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** `sd setup` and `st setup` provision their own repositories: they hand the job to
`hub install` when a SushiStack workspace is there, and otherwise read their own dependency
fragment and say — or, with `--install`, run — the one command that satisfies it.

**Architecture:** The reader that turns a fragment into "what is missing and what installs it"
moves into `sushicore`, so one schema has one reader rather than the three it would otherwise
have. `hub` delegates to the same brick, because two readers of one file is the bug this
programme has already been bitten by. The module CLIs keep only the part that acts: run the
command, or print it.

**Tech Stack:** Python 3.10+, `tomllib`, pytest, apt/dnf/pacman/zypper, vcpkg, PyPI.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §2 and §5 wave 7.

## Global Constraints

- **The owner's decisions, 2026-09-22.** The fragment reader lives in `sushicore`, because six
  repositories share the schema and one copy is the point. `sd setup` **reports by default** and
  installs only under `--install`, so a user sees what would change before it changes.
- `sushidsp` and `sushitrack` stay outside the stack. They share none of its weight: measured
  2026-09-22, no file in either repository mentions SYCL. The door stays open through wave 6's
  manifest — if `sushidsp` ever offloads to `sushiruntime`, it says so in its own manifest and
  nothing here has to be reopened.
- Three repositories are touched: `sushistack`, `sushidsp`, `sushitrack`, plus `sushicore`.
  Each has its own working tree with its own uncommitted work. **Stage by path, never
  `git add -A`.** Check `git status --porcelain` before touching any of them.
- The suite is at 363 in `sushistack` when this wave starts, 97 in `sushicore`. Every task
  states its counts.
- **Check CI before calling the wave closed.**
- Do not run the build system: `se`, `cmake`, `ninja`, `ctest` are off limits in every
  repository, and no build configuration file is edited. `sd build` and `st build` are the
  owner's to run.
- Python style follows `python-code-style`; comments follow `source-comments`; commit messages
  follow `commits`; prose goes through `humanizer`.

## What was measured, 2026-09-22

- `sushidsp` declares `sdl2` (required; `libsdl2-dev` on apt, `sdl2` on vcpkg) and `intel-llvm`
  (optional, installs nothing — it is a C++ compiler preference, and `config.py`'s
  `bundled_clang()` really looks for it).
- `sushitrack` declares `googletest` alone and vendors Eigen and nlohmann-json under
  `third_party/`.
- Neither is aggregated by `hub install` any more: both left the catalog in wave 2, so nothing
  provisions their fragments today.
- `sushidsp`'s fragment was an array of `[[dependency]]` tables, which the reader skipped in
  silence. Fixed on 2026-09-22 in both repositories, with five tests and a reader that now
  refuses a shape it cannot read.
- `sushicore.workspace.workspace_home()` already walks up for the `.sushistack` marker, and
  `sushidsp` already uses it to find the shared toolchain. Finding a workspace is solved; only
  provisioning is not.
- `hub`'s `Dependency` dataclass and `_parse_manifest` live in
  `sushihub/cli/sushistack/setup/dependency_source.py`. Its aggregation, ownership and platform
  logic stay in `hub`; only the per-file read moves.

---

### Task 1: `sushicore` gains the fragment reader

**Files** (repository `D:/Projects/sushicore`):
- Create: `sushicore/deps_fragment.py`
- Create: `tests/test_deps_fragment.py`
- Modify: `pyproject.toml` — version to `0.3.0`
- Modify: `docs/reference/CHANGELOG.md`, `README.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `Dependency`, `read(path) -> list[Dependency]`, `missing(deps, platform) ->
  list[Dependency]` and `install_command(dep, platform) -> list[str] | None`.

- [ ] **Step 1: Take the reader that exists rather than writing a second one**

`sushihub/cli/sushistack/setup/dependency_source.py` holds `Dependency` and `_parse_manifest`,
and as of 2026-09-22 five tests. Read both, and move what is generic: the dataclass, the parse,
the `[module]` metadata rule, the refusal of a shape it cannot read, and `packages_for`.

Leave behind what is `hub`'s: aggregating several fragments, the duplicate-name warning, owner
tagging, the `provides` any-of rule, `gpu_only`. Those are the installer's policy, not the
file's meaning.

`sushicore`'s own docstring says it "knows nothing about SYCL, toolchains, or any module's
schema". A fragment reader names no module and no toolchain, so it fits — but say in the report
whether anything you moved names one, and stop rather than moving it if so.

- [ ] **Step 2: Decide what "missing" means, and write it down**

A dependency is satisfied when its `check_cmd` exits 0, or — when it declares none — when its
package is present to the platform's package manager. `sushicore` must answer this **without**
running a package manager: it reports, the caller acts. Read `hub`'s
`setup/package_managers.py` for how presence is decided today and take only the decision, not
the installation.

If a dependency declares no package for the platform and no `check_cmd`, it is not missing and
not satisfied: it is *not applicable*. `sushidsp`'s `intel-llvm` is exactly that case. Give it
its own answer rather than folding it into either, and test it.

- [ ] **Step 3: Test the brick on its own**

`tests/test_deps_fragment.py` covers: the table shape reads; `[module] depends_on` is metadata;
an array of tables raises and names the file; a scalar at the top level raises; a dependency
with no package for this platform is not applicable; `install_command` names the right command
per platform and returns None when there is nothing to install.

- [ ] **Step 4: Release — owner step for the tag**

```bash
cd /d/Projects/sushicore
python -m pytest tests -q          # expect 97 plus the new ones
git add sushicore/deps_fragment.py tests/test_deps_fragment.py pyproject.toml docs/reference/CHANGELOG.md README.md
git commit -m "feat: read a dependency fragment"
```

Do not push and do not tag. The owner publishes 0.3.0.

---

### Task 2: `hub` reads through the same brick

**Files:**
- Modify: `sushihub/cli/sushistack/setup/dependency_source.py`
- Modify: `sushihub/cli/pyproject.toml` — `sushicore>=0.3.0`
- Modify: `sushihub/cli/tests/test_dependency_fragment.py`

**Interfaces:**
- Consumes: `sushicore` 0.3.0.
- Produces: one reader of the fragment schema in the whole programme.

- [ ] **Step 1: Delegate, do not duplicate**

`_parse_manifest` becomes a thin caller of `sushicore.deps_fragment.read`, adding only what
`hub` owns: the owner tag. Everything the two would otherwise both know — the shape, the
`[module]` rule, the refusal — belongs to one of them.

The point of this task is that a future fragment change is made once. If the two end up with
their own copies of any rule, the task failed even with a green suite; say so rather than
shipping it.

- [ ] **Step 2: Keep the tests that pin the behaviour, wherever it now lives**

`tests/test_dependency_fragment.py` was written on 2026-09-22 against `hub`'s reader. Some cases
now belong to `sushicore`'s suite and some stay here, testing that `hub` still refuses what it
refused. Decide per case; do not delete one because it moved.

- [ ] **Step 3: Verify and commit**

```bash
python -m pytest sushihub/cli/tests -q
hub doctor          # the reader on real fragments; paste the owner counts
git add sushihub/cli/sushistack/setup/dependency_source.py sushihub/cli/pyproject.toml sushihub/cli/tests/
git commit -m "refactor(cli): read dependency fragments through sushicore"
```

---

### Task 3: `st setup`, the simple case first

**Files** (repository `D:/Projects/sushitrack`):
- Modify: `cli/pyproject.toml` — `sushicore>=0.3.0`
- Modify: `cli/sushitrack/cli.py` and whichever module holds its commands
- Create: `cli/tests/test_setup.py`
- Modify: `README.md`, `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: task 1's brick.
- Produces: `st setup` and `st setup --install`.

- [ ] **Step 1: Read the repository before adding to it**

`sushitrack` declares GoogleTest alone, so this is the small case and it goes first: whatever
shape it takes, `sd setup` copies it. Read its existing CLI, match its command style, its
console use and its test layout. A sibling that looks different is a defect even when it works.

- [ ] **Step 2: Write the two paths**

```
st setup            reports; changes nothing
st setup --install  runs the command the report named
```

In order:

1. Ask `sushicore.workspace` for a workspace root. If there is one **and** `hub` is runnable,
   say so and hand off: `hub install`. One shared tree, nothing downloaded twice, which is the
   whole promise SushiStack exists for.
2. Otherwise read `cli/sushistack.deps.toml` through the brick, report each dependency as
   satisfied, missing or not applicable, and name the command for each missing one.
3. Under `--install`, run those commands. Nothing else in this CLI runs a package manager, so
   this is the one place that does.

Say which path was taken, every time. A tool that silently picks between two sources is one a
user cannot debug.

- [ ] **Step 3: Test both paths with no network and no package manager**

Patch the workspace lookup and the command runner with recorders, as
`sushistack`'s `tests/test_self_update.py` does for pipx and git. Assert: the workspace path
calls `hub install` and no package manager; the standalone path names the right command and
runs nothing without `--install`; `--install` runs exactly what the report named. A test that
installs a real package is not acceptable.

- [ ] **Step 4: Say it in the README**

`sushitrack`'s README is its front door and, since wave 2, its only one. It must answer: what
this is, how to get its dependencies with and without SushiStack, and how to build. Do not
mention `hub` as a requirement; it is an accelerator.

- [ ] **Step 5: Commit in `sushitrack`**

```
feat(cli): provision this repository with or without SushiStack
```

Do not push.

---

### Task 4: `sd setup`, the same shape

**Files** (repository `D:/Projects/sushidsp`):
- Modify: `cli/pyproject.toml` — `sushicore>=0.3.0`
- Modify: its CLI module
- Create: `cli/tests/test_setup.py`
- Create: `sushi-module.toml`
- Modify: `README.md`, `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: task 3's shape, wave 6's manifest format.
- Produces: `sd setup`, and a checkout `hub` can recognise when it is in a workspace.

- [ ] **Step 1: Copy the shape, not the code**

`sd setup` does what `st setup` does. Siblings that do the same kind of thing are shaped the
same: same flags, same output order, same words for the same states. If task 3's shape does not
fit `sushidsp`'s two dependencies, say what did not fit rather than diverging quietly.

- [ ] **Step 2: Give `sushidsp` a manifest**

Wave 6 taught `hub` to recognise a checkout by `sushi-module.toml`. Write `sushidsp`'s, so a
developer who keeps it inside a SushiStack workspace gets `sdl2` provisioned by `hub install`
and nothing downloaded twice. `distribution = "source"`, `alias = "sd"`, and the fragment path
`cli/sushistack.deps.toml`.

This is what makes `sushidsp` a module that describes itself without being in the catalog, which
is the arrangement the owner chose on 2026-09-22: outside the stack, able to attach.

`sushitrack` gets one too if task 3 found a reason; say which and why.

- [ ] **Step 3: Prove the attachment**

With `sushidsp` linked into this workspace:

```bash
hub doctor
```

Paste the owner counts. A `sushidsp` owner appearing, with `sdl2` under it, is the evidence that
the fragment nobody read until 2026-09-22 now reaches the installer.

- [ ] **Step 4: README and commit**

Same as task 3. Do not push.

---

### Task 5: Close the wave

**Files:**
- Modify: `docs/design/WORKSPACE_DECOUPLING.md`, `docs/design/REMAINING_WORK.md`
- Modify: `docs/reference/CHANGELOG.md`, `docs/getting_started/INSTALL.md`

- [ ] **Step 1: Record the decision that outlives the wave**

§2 says `sushidsp` and `sushitrack` "keep their own CLIs and their own install paths". Say what
that turned out to mean, and why they are outside: they share none of the stack's weight, no
file in either mentions SYCL, and the manifest keeps the door open. Record the owner's
determinism reasoning for the real-time path, so the next reader does not propose GPU offload
for a sample-serial circuit solve.

- [ ] **Step 2: Correct `INSTALL.md`**

Its section on the two modules leaving tells a reader to delete a stale `[modules]` line. Add
what to do instead: each repository installs its own CLI and provisions itself.

- [ ] **Step 3: CI, then the changelog**

```bash
git push
gh run list --limit 3 --workflow=CI
```

```
- 2026-09-22 — Provisioned sushidsp and sushitrack with or without a SushiStack workspace (`cli/sushitrack/`, `cli/sushidsp/`).
- 2026-09-22 — Moved the dependency fragment reader into `sushicore`, so one schema has one reader (`sushicore/deps_fragment.py`).
```

- [ ] **Step 4: Commit**

```bash
git add docs
git commit -m "docs: record that sd and st provision themselves"
```

---

## Order

```
Task 1 (sushicore brick)  ->  Task 2 (hub delegates)  ->  Task 3 (st)  ->  Task 4 (sd)  ->  Task 5 (docs)
```

Strictly serial. Task 1 is partly an owner step: publishing 0.3.0. Task 4 needs wave 6, because
a manifest is only useful once `hub` reads one.

## What this wave does not do

- Neither repository joins the catalog. `hub add sushidsp` still reports an unknown module.
- Neither CLI publishes to PyPI. That decision stands from wave 4: a module CLI needs a
  checkout to do anything.
- `sushidsp` gains no GPU path. The real-time circuit solve is sample-serial and must be
  bit-reproducible, so it stays on the CPU; an offline path is a separate design if it is ever
  wanted.
- Neither repository gains an installer script. `pipx install --editable <repo>/cli` is the
  documented way, as `INSTALL.md` already says.
