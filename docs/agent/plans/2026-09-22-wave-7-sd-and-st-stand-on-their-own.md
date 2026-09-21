# Wave 7: `sd` and `st` stand on their own

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** `sd setup` and `st setup` get their own repositories ready to build, each from its own
source of truth: `sd` from its dependency fragment, handing off to `hub install` inside a
workspace; `st` from `environment.yml` through conda. Both report by default and act under
`--install`.

**Architecture:** The two commands share a shape, not a mechanism. `sd`'s fragment reader moves
into `sushicore`, so one schema has one reader — two readers of one file is the bug this
programme was bitten by today — and `hub` delegates to the same brick. `st` needs none of that:
conda already gives it cmake, ninja, gtest and PyTorch, so its whole job is to run the right
environment tool. No abstraction is built over the two.

**Tech Stack:** Python 3.10+, `tomllib`, pytest, apt/dnf/pacman/zypper, vcpkg, conda/mamba, PyPI.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §2 and §5 wave 7.

## Global Constraints

- **The owner's decisions, 2026-09-22.** The fragment reader lives in `sushicore`, so one schema
  has one reader. Both commands **report by default** and install only under `--install`, so a
  user sees what would change before it changes. `st setup` uses `mamba` or `micromamba` when
  PATH carries one and `conda` otherwise, and creates rather than updates. `sushitrack`'s
  `cli/sushistack.deps.toml` is deleted; `environment.yml` is its single source.
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
- **Corrected 2026-09-22, before task 1.** `sushitrack` does not provision the way this plan
  first assumed. Its dependencies come from conda: `environment.yml` pins Python 3.11, PyTorch
  with `pytorch-cuda=12.1`, torchvision, torchaudio and thirty pip packages, and it carries
  `cmake=4.3.3`, `ninja` and `gtest=1.17.0` too. Everything `hub install` would provide, conda
  already provides. Its `cli/sushistack.deps.toml` declares `googletest` alone, which
  `environment.yml` also has, so **the owner decided on 2026-09-22 that the file is deleted** and
  `environment.yml` becomes the single source.

  `st setup` therefore has nothing to do with the fragment reader. Task 3 is rewritten below.
  The consequence for task 1 is noted rather than acted on: the reader now has two consumers,
  `hub` and `sd`, rather than the six the owner's decision assumed. One owner for one schema is
  still the answer — two readers of one file is the bug this programme hit today — but the case
  is thinner than it was, and a later reader of this plan should know that.

- `sushitrack`'s CLI is not shaped like the others: it has its own `app.py` command framework
  rather than Typer, and already carries `status`, `doctor`, `config`, `paths` and `env`.
  `setup` joins those and takes their shape, not `hub`'s.
- Nothing in `sushitrack`'s CLI knows about conda today. `services/evaluate.py` prints
  `conda env create -f environment.yml` in an error message, and `docs/README.md` line 316 tells
  a reader to run it by hand. That hand-off is what `st setup` replaces.
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

### Task 3: `st setup`, the conda environment

**Files** (repository `D:/Projects/sushitrack`):
- Modify: `cli/sushitrack_cli/cli.py` and a new service module beside its siblings
- Create: `cli/tests/` coverage for the new command, in whatever shape that repository tests in
- Delete: `cli/sushistack.deps.toml`
- Modify: `README.md`, `docs/README.md`, `docs/reference/CHANGELOG.md` (check the real path first)

**Interfaces:**
- Consumes: nothing from `sushicore`'s new brick. This task is independent of tasks 1 and 2.
- Produces: `st setup` and `st setup --install`.

- [ ] **Step 1: Read the repository's own shape before adding to it**

`st` has its own command framework in `cli/sushitrack_cli/app.py`, its own `console` and `proc`
modules, and a services layer. `setup` is a sibling of `doctor` and `status`: same registration,
same console calls, same return-code convention. A command that looks like `hub`'s in this
repository is a defect even when it works.

- [ ] **Step 2: Name the tool, and say which one was chosen**

The owner's decision of 2026-09-22: use `mamba` or `micromamba` when PATH carries one, else
`conda`. The same `environment.yml` drives all three, and mamba's solver is the one that makes
an environment this size bearable. When none is found, name the command and stop rather than
guessing at a Python that might do.

Say which tool was picked, every time. A tool that silently chooses between two package managers
is one a user cannot debug.

- [ ] **Step 3: The two paths**

```
st setup            reports; changes nothing
st setup --install  creates the environment
```

An environment named `sushitrack` that already exists is reported, not overwritten:
`conda env create` fails on an existing name, and the update command is named for the user
rather than run. The owner chose create over update on 2026-09-22; do not quietly add the
second behaviour.

- [ ] **Step 4: Delete the fragment**

`git rm cli/sushistack.deps.toml`. `environment.yml` is the single source of truth, which
`docs/README.md` already says. Check nothing else in the repository names the file:

```bash
grep -rn "sushistack.deps.toml" . --include=*.py --include=*.md --include=*.toml | grep -v build/
```

A SushiStack workspace holding this checkout then aggregates nothing from it, which is correct:
conda gives it everything `hub install` would.

- [ ] **Step 5: Test without conda**

Patch the tool lookup and the command runner with recorders. Assert: mamba is preferred over
conda when both are present; conda is used when mamba is not; nothing runs without `--install`;
`--install` runs exactly the command that was reported; an absent tool is reported rather than
guessed at. A test that creates a real environment is not acceptable.

- [ ] **Step 6: Say it where a reader already looks**

`docs/README.md` line 316 tells a reader to run `conda env create -f environment.yml` by hand.
It becomes `st setup --install`, with the hand-written command kept as what the command runs.

- [ ] **Step 7: Commit in `sushitrack`**

```
feat(cli): create this repository's conda environment from st
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

- [ ] **Step 1: Take the command's shape, not its mechanism**

`sd setup` and `st setup` answer the same question — "what do I need before I can build?" — from
different places: `sd` from its dependency fragment through `sushicore`'s reader, `st` from
`environment.yml` through conda. What the two share is the *command*: the same flags, the same
output order, the same words for the same states, report by default and act under `--install`.
What they do not share is the provisioner, and no abstraction is built over two mechanisms with
two users.

`sushidsp`'s CLI is Typer-shaped like `hub`'s, so `sd setup` follows its own repository's
conventions rather than `st`'s framework.

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
