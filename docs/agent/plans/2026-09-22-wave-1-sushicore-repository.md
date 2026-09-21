# Wave 1: sushicore becomes its own repository and a published package

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `sushicore` out of SushiStack into its own repository, publish it to PyPI, and
make every CLI that uses it take it as an ordinary dependency, so nothing has to inject it from
a path any more.

**Architecture:** A serial spine prepares the package, splits it out with its history, wires a
release workflow and publishes 0.1.0. Once 0.1.0 is on PyPI, two things run in parallel: this
repository drops its copy and takes the dependency, and the six consumer repositories each take
the same dependency in their own repository.

**Tech Stack:** Python 3.10+, setuptools, `git subtree split`, GitHub Actions, PyPI trusted
publishing, pipx.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §3.4 and §5 wave 1.

## Global Constraints

- The package name on PyPI is `sushicore`. Checked free on 2026-09-21; a name is reserved only
  by an upload, so task 4 is what claims it.
- The first published version is `0.1.0`, which is what `sushicore/pyproject.toml` already
  declares. No version bump happens in this wave.
- History is preserved. The new repository starts from a `git subtree split` of `sushicore/`,
  not from a fresh commit.
- Publishing runs from GitHub Actions through PyPI trusted publishing. No API token is stored
  anywhere, and nobody uploads from a laptop.
- All six consumers move in this wave: `sushiruntime`, `sushiengine`, `sushiai`, `sushiblas`,
  `sushidsp`, `sushitrack`. `sushidsp` and `sushitrack` leave the stack in wave 7, but they use
  `sushicore` today and are not left on a path injection that no longer exists.
- Tasks 2, 3 and 4 create a GitHub repository, configure a PyPI publisher and push a tag. An
  agent cannot do any of those. Each such step is marked **owner step** and carries the exact
  command or the exact page to open; an agent executing this plan stops there and reports.
- `api-stability` and `versioning-and-release` govern this wave: the path injection is a public
  installation interface and it is being removed.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`.
- Commit messages follow `commits`.

## Where this wave contradicts wave 0

`sushihub/cli/tests/test_cli_install.py`, written in wave 0, pins the `sushicore` injection:
`test_a_missing_sushicore_stops_after_the_install` and `test_the_happy_path_installs_then_injects`
both assert that `pipx inject` runs. Task 5 deletes the injection, so those two tests must be
rewritten in the same task that deletes it, and `test_sushicore_is_found_at_a_fixed_path_under_the_root`
and `test_sushicore_is_none_when_the_checkout_is_partial` must be deleted with the function they
cover. That is the wave 0 tests doing their job: they make the removal visible instead of silent.

---

### Task 1: Make sushicore publishable, in place

`sushicore/` has a `pyproject.toml`, a `LICENSE`, `docs/README.md`, `CLAUDE.md` and 94 tests, but
no front-door `README.md` and no packaging metadata beyond a name and a description. PyPI renders
the readme on the project page and the classifiers drive its search, so both are added before
anything moves.

`docs/design/REMAINING_WORK.md` carries an item, **`sushicore`'s README placement**, saying the
component's facts live in `sushicore/docs/README.md` rather than `sushicore/README.md`. This task
closes it.

**Files:**
- Create: `sushicore/README.md`
- Modify: `sushicore/pyproject.toml`
- Modify: `docs/design/REMAINING_WORK.md` (delete the README-placement item only)

**Interfaces:**
- Consumes: nothing.
- Produces: a `sushicore` distribution that builds to a wheel and an sdist on its own.

- [ ] **Step 1: Write the front-door README**

`sushicore/README.md` is the page PyPI shows. It states what the package is, who uses it, and
where the detail lives. Keep it short; `docs/README.md` beside it stays the manual and is not
duplicated here.

```markdown
# sushicore

The shared core of the Sushi developer CLIs. `hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st` all
import it for the same four things: locating a workspace, loading layered TOML configuration,
printing to a terminal or to a JSON stream, and driving cmake and ctest.

```bash
pip install sushicore
```

It is a library for those CLIs rather than a tool of its own: it installs no console script and
it knows nothing about SYCL, a renderer, or any one module's schema.

| Module | What it does |
|---|---|
| `sushicore.workspace` | Walks up for a marker, merges a `[tool]` table with its platform override |
| `sushicore.config_base` | The layered load: defaults, file, local file, environment |
| `sushicore.console`, `renderer`, `events`, `theme`, `icons` | One seam for human output and for `--json` |
| `sushicore.cmake_driver`, `cmake_cache`, `proc`, `toolchain_args` | The configure, build and test driver the CLIs share |

The manual is in `docs/README.md`. Licensed under the terms in `LICENSE`.
```

- [ ] **Step 2: Add the packaging metadata**

In `sushicore/pyproject.toml`, the `[project]` table today names only `name`, `version`,
`description`, `authors`, `requires-python` and `dependencies`. Add the four fields PyPI needs,
directly after the `description` line:

```toml
readme = "README.md"
license = { file = "LICENSE" }
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Build Tools",
]

[project.urls]
Homepage = "https://github.com/SushiSystems/SushiCore"
Source = "https://github.com/SushiSystems/SushiCore"
```

- [ ] **Step 3: Build the distribution and confirm both artifacts carry the readme**

Run:

```bash
python -m pip install --upgrade build twine
python -m build sushicore
python -m twine check sushicore/dist/*
```

Expected: `build` writes `sushicore-0.1.0-py3-none-any.whl` and `sushicore-0.1.0.tar.gz` into
`sushicore/dist/`, and `twine check` reports `PASSED` for both. A `twine check` warning about the
readme means step 1 or step 2 is wrong; fix it rather than proceeding.

- [ ] **Step 4: Confirm the tests still pass and the build tree is not committed**

Run: `python -m pytest sushicore/tests -q`
Expected: 94 passed.

Run: `git status --porcelain sushicore/`
Expected: `sushicore/dist/` and `sushicore/*.egg-info` do not appear, because `sushicore/.gitignore`
already excludes them. If either appears, add it to `sushicore/.gitignore` in this task.

- [ ] **Step 5: Close the backlog item**

Delete the **`sushicore`'s README placement** item from *Outside the programme* in
`docs/design/REMAINING_WORK.md`. Change nothing else in that file.

- [ ] **Step 6: Commit**

```bash
git add sushicore/README.md sushicore/pyproject.toml docs/design/REMAINING_WORK.md
git commit -m "build(sushicore): give it a front door and the metadata PyPI needs"
```

---

### Task 2: Split sushicore out with its history

**Owner step.** Creating a GitHub repository and pushing to it needs credentials an agent does
not have. An agent executing this plan runs step 1, then stops and reports the branch name.

**Files:**
- No file in this repository changes. The split writes a branch, not a commit on `main`.

**Interfaces:**
- Consumes: Task 1's committed state.
- Produces: `https://github.com/SushiSystems/SushiCore` at `main`, carrying `sushicore/`'s history
  with the directory as the repository root.

- [ ] **Step 1: Split the subtree into a local branch**

```bash
cd /d/Projects/sushistack
git subtree split --prefix=sushicore -b sushicore-split
git log --oneline sushicore-split | wc -l
```

Expected: a branch `sushicore-split` whose root is `pyproject.toml`, `README.md`, `sushicore/`
and `tests/` rather than `sushicore/...`. The commit count is smaller than `main`'s, because only
the commits touching `sushicore/` are carried.

Confirm the shape before pushing anything:

```bash
git ls-tree --name-only sushicore-split
```

Expected, exactly: `.gitignore`, `CLAUDE.md`, `LICENSE`, `README.md`, `docs`, `pyproject.toml`,
`sushicore`, `tests`.

- [ ] **Step 2: Create the repository** — owner step

Open https://github.com/organizations/SushiSystems/repositories/new and create `SushiCore`,
public, with no README, no `.gitignore` and no licence: the split branch brings all three.

Or, with the CLI:

```bash
gh repo create SushiSystems/SushiCore --public --description "The shared core of the Sushi developer CLIs."
```

- [ ] **Step 3: Push the split branch as main** — owner step

```bash
cd /d/Projects/sushistack
git push https://github.com/SushiSystems/SushiCore.git sushicore-split:main
```

- [ ] **Step 4: Clone it beside the others and confirm it stands alone**

```bash
cd /d/Projects
git clone https://github.com/SushiSystems/SushiCore.git sushicore
cd sushicore
python -m pip install -e ".[test]"
python -m pytest tests -q
```

Expected: 94 passed, from a checkout that has no SushiStack anywhere near it. This is the whole
point of the wave; if it does not pass here, nothing after this task is worth starting.

- [ ] **Step 5: Delete the local split branch**

```bash
cd /d/Projects/sushistack
git branch -D sushicore-split
```

The branch was a transport, not a record. The history now lives in the new repository.

---

### Task 3: Give the new repository its CI and its release workflow

Two workflows in `D:/Projects/sushicore`: one that tests every push, one that publishes when a
tag is pushed. They are separate because they answer to different events and a test failure must
never be confused with a publish failure.

**Files:**
- Create: `D:/Projects/sushicore/.github/workflows/ci.yml`
- Create: `D:/Projects/sushicore/.github/workflows/release.yml`

**Interfaces:**
- Consumes: Task 2's repository.
- Produces: a tag push on `v*` that lands a release on PyPI.

- [ ] **Step 1: Write the test workflow**

`D:/Projects/sushicore/.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.10", "3.11"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - name: Install
        run: pip install -e ".[test]"
      - name: Test
        run: python -m pytest tests -q
```

- [ ] **Step 2: Write the release workflow**

`D:/Projects/sushicore/.github/workflows/release.yml`. The `id-token: write` permission is what
trusted publishing uses in place of a token, and the environment name must match the one
configured on PyPI in step 3.

```yaml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build the distribution
        run: |
          python -m pip install --upgrade build twine
          python -m build
          python -m twine check dist/*
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 3: Register the trusted publisher on PyPI** — owner step

`sushicore` does not exist on PyPI yet, so this is a *pending* publisher, which is the form PyPI
offers for a project whose first release has not been uploaded.

Open https://pypi.org/manage/account/publishing/ and add a pending publisher with:

| Field | Value |
|---|---|
| PyPI project name | `sushicore` |
| Owner | `SushiSystems` |
| Repository name | `SushiCore` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

Then, in the new repository, open Settings, Environments, and create an environment named `pypi`.
The names must match on both sides or the publish is rejected with a mismatched-claim error.

- [ ] **Step 4: Commit and push both workflows** — owner step

```bash
cd /d/Projects/sushicore
git add .github/workflows/ci.yml .github/workflows/release.yml
git commit -m "ci: test every push and publish every tag to PyPI"
git push
```

- [ ] **Step 5: Confirm CI is green before any tag exists**

```bash
cd /d/Projects/sushicore
gh run list --limit 1
```

Expected: the `CI` run for the workflow commit concludes `success` on all four combinations. A
red CI here must be fixed before task 4; a tag pushed onto a broken tree publishes a broken
package, and a version once on PyPI cannot be replaced.

---

### Task 4: Publish 0.1.0

**Owner step**, all of it: pushing a tag is what triggers the upload.

**Files:**
- No file changes.

**Interfaces:**
- Consumes: Task 3's workflows and publisher.
- Produces: `sushicore==0.1.0` installable from PyPI. Every task after this one depends on it.

- [ ] **Step 1: Tag and push**

```bash
cd /d/Projects/sushicore
git tag -a v0.1.0 -m "sushicore 0.1.0"
git push origin v0.1.0
```

- [ ] **Step 2: Watch the release workflow**

```bash
gh run watch
```

Expected: `build` then `publish`, both green. A failure in `publish` with a claim mismatch means
step 3 of task 3 has a field wrong; fix it there and push a new tag, because a tag that failed to
publish cannot be re-pushed to the same version.

- [ ] **Step 3: Install it from the index, in an environment that has no checkout**

```bash
python -m venv /tmp/sushicore-check
/tmp/sushicore-check/bin/python -m pip install sushicore==0.1.0
/tmp/sushicore-check/bin/python -c "import sushicore.workspace as w; print(w.WORKSPACE_CLI_DIR)"
```

On Windows the interpreter is `/tmp/sushicore-check/Scripts/python.exe`.

Expected: pip resolves `sushicore` from PyPI, and the import prints `sushihub\cli`. This is the
first moment the package exists independently of any checkout.

- [ ] **Step 4: Record the release in the new repository's changelog**

`D:/Projects/sushicore/docs/reference/CHANGELOG.md` gets one line at the top of its list:

```
- 2026-09-22 — Published 0.1.0 to PyPI from its own repository (`.github/workflows/release.yml`).
```

If that file does not exist in the split, create it with the three-line header the SushiStack one
carries, then the entry.

```bash
cd /d/Projects/sushicore
git add docs/reference/CHANGELOG.md
git commit -m "docs: record the 0.1.0 release"
git push
```

---

### Task 5: SushiStack takes the published dependency and drops the injection

This task deletes the path injection in three places (`modules.py`, `install.py`, the pyproject
comment) and rewrites the wave 0 tests that pinned it.

**Files:**
- Modify: `sushihub/cli/pyproject.toml`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/install.py`
- Modify: `sushihub/cli/tests/test_cli_install.py`

**Interfaces:**
- Consumes: `sushicore==0.1.0` on PyPI, from task 4.
- Produces: a `sushistack-cli` distribution that resolves `sushicore` from an index. `sushicore_dir`
  and `SUSHICORE_NAME`'s use in `_install_module_cli` no longer exist.

- [ ] **Step 1: Declare the dependency**

In `sushihub/cli/pyproject.toml`, add `"sushicore>=0.1.0",` to the `dependencies` list, above
`"typer>=0.12",`. Then delete the six-line comment block below `[project.scripts]` that begins
`# sushicore (the shared CLI presentation layer, in this repository at ...` and explains why the
dependency is absent. It is no longer true.

- [ ] **Step 2: Delete `sushicore_dir` and the injection it served**

In `sushihub/cli/sushistack/services/modules.py`:

- Delete the whole `sushicore_dir` function.
- In `_install_module_cli`, delete everything from `cli_shared = sushicore_dir(root)` to the
  `return False` that closes the `if subprocess.run([*pipx, "inject", ...])` block, and replace it
  with `return True` directly after the `pipx install` check. The function keeps its `root`
  parameter only if another statement still uses it; if nothing does, drop the parameter and fix
  the one call site.
- `SUSHICORE_NAME` stays. `status_report.py` and `link`'s refusal both still use it, and
  `sushicore` is still a directory in this repository until task 6 removes it.

Update the function's docstring: it no longer mirrors an injection, it pipx-installs the module's
CLI and nothing else.

- [ ] **Step 3: Delete the injection from the installer**

In `sushihub/cli/install.py`:

- Delete the `find_sushicore_dir` function.
- In `install()`, delete the `sushicore_dir = find_sushicore_dir()` line and the whole
  `if rc == 0:` block that runs `pipx inject`, along with its comment. What remains is the
  `pipx install --force --editable` call, then `remove_legacy_shim`.
- Update the module docstring's `Strategy` section, which still says sushicore is injected.

- [ ] **Step 4: Rewrite the two tests that pinned the injection**

In `sushihub/cli/tests/test_cli_install.py`:

- Delete `test_sushicore_is_found_at_a_fixed_path_under_the_root` and
  `test_sushicore_is_none_when_the_checkout_is_partial`; they cover a function that no longer
  exists.
- Delete `test_a_missing_sushicore_stops_after_the_install` entirely: with no injection there is
  no second outcome to have.
- Replace `test_the_happy_path_installs_then_injects` with:

```python
def test_the_happy_path_installs_the_module_cli_alone(checkout, root, recorder, monkeypatch):
    """Installs the module's cli/ with pipx and runs no second command."""
    runs = _Runs()
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: ["pipx"])
    monkeypatch.setattr(modules, "subprocess", type("S", (), {"run": runs}))
    assert modules._install_module_cli("sushiruntime", checkout, root) is True
    assert runs.commands == [["pipx", "install", "--force", str(checkout / "cli")]]
```

- Add one test that states the new rule, which is what replaces the deleted ones:

```python
def test_a_failed_pipx_install_is_reported(checkout, root, recorder, monkeypatch):
    """Reports failure when pipx cannot install the module's CLI."""
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: ["pipx"])
    monkeypatch.setattr(modules, "subprocess", type("S", (), {"run": _Runs(code=1)}))
    assert modules._install_module_cli("sushiruntime", checkout, root) is False
    assert recorder.said("sushiruntime: CLI install failed.")
```

- The `root` fixture no longer needs to build a `sushicore` directory if nothing reads it; leave
  it only if the rewritten tests still take it.
- Rewrite the module docstring. It reads "How a module's own CLI is installed and where sushicore
  is injected from", and the second half stops being true in this task.

- [ ] **Step 5: Reinstall against the published package and confirm**

```bash
python -m pip uninstall -y sushicore
python -m pip install -e "./sushihub/cli[test]"
python -c "import sushicore, sushicore.workspace; print(sushicore.__file__)"
```

Expected: pip pulls `sushicore` from PyPI as a dependency of `sushistack-cli`, and the printed
path is inside `site-packages`, not inside this repository. A path under `D:/Projects/sushistack/sushicore`
means the editable install from an earlier day is still shadowing the published one; remove it
with `python -m pip uninstall -y sushicore` and repeat.

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 332 passed. The count drops by two from wave 0's 334: three tests are deleted and one
is added.

- [ ] **Step 6: Commit**

```bash
git add sushihub/cli/pyproject.toml sushihub/cli/sushistack/services/modules.py sushihub/cli/install.py sushihub/cli/tests/test_cli_install.py
git commit -m "build(cli)!: take sushicore from PyPI and drop the path injection"
```

The `!` is not decoration: anyone who installed `hub` from a checkout gets a different
installation path from this commit on.

---

### Task 6: Remove sushicore from this repository

Only after task 5 proves the published package works. Deleting first would leave no way back.

**Files:**
- Delete: `sushicore/` (the whole directory)
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/architecture/WORKSPACE.md`
- Modify: `docs/design/REMAINING_WORK.md`
- Modify: `docs/design/WORKSPACE_DECOUPLING.md`
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: task 5's committed state.
- Produces: a SushiStack that holds `sushihub/` and nothing else of its own.

- [ ] **Step 1: Delete the directory**

```bash
git rm -r sushicore
```

- [ ] **Step 2: Rewrite the CI workflow**

In `.github/workflows/ci.yml`:

- Delete the `sushicore` job entirely. That suite now runs in its own repository, on every push
  there.
- In the `hub` job, change the install step to `run: pip install -e "./sushihub/cli[test]"` and
  delete the two-line comment above it that explains the ordering; pip resolves `sushicore` from
  the index now, so there is no ordering to explain.
- The `consumers` job's whole premise was that `sushicore` is unpublished and unpinnable. It is
  neither from task 4 on, and its test command is broken anyway: line 145 runs
  `python -m pytest sushihub/cli/tests -q` inside a consumer checkout, which holds `cli/tests` and
  no `sushihub/` directory. Delete the job and its block comment. The contract it guarded now
  belongs in the new repository, where a change to `sushicore` can test the consumers before it
  ships; open a backlog item for it rather than porting it blind in this task.

- [ ] **Step 3: Add the backlog item the deleted job leaves behind**

Under *Outside the programme* in `docs/design/REMAINING_WORK.md`:

```markdown
- **The consumer contract has no home.** `.github/workflows/ci.yml`'s `consumers` job ran the five
  consumer CLIs' suites against the `sushicore` under test. It was deleted in wave 1 with the
  package, and its command had been broken since 2026-09-07 anyway (it ran `pytest
  sushihub/cli/tests` inside checkouts that hold `cli/tests`). The same job belongs in the
  SushiCore repository, where a change can be tested against its consumers before it is tagged.
```

- [ ] **Step 4: Update the front door and the manual**

- `README.md`: delete the `sushicore/` row from the three-row table and change the sentence above
  it from "three things of its own" to "two things of its own". The `sushicore` mention in the
  row describing what the engine is under every CLI moves to naming the PyPI package.
- `docs/README.md`: delete any line pointing at `sushicore/docs/README.md`, and add `sushicore` to
  wherever the manual names the repositories the stack spans.
- `docs/architecture/WORKSPACE.md`: it draws the workspace tree. Remove `sushicore/` from it.

Every cited path must resolve after this step. Check with:

```bash
grep -rn "sushicore/" README.md docs/ --include=*.md
```

Expected: no hit that names a path inside this repository. Hits that name the PyPI package or the
new repository are correct and stay.

- [ ] **Step 5: Close wave 1 in both places**

In `docs/design/REMAINING_WORK.md`, the decoupling table's wave 1 row gains `Landed 2026-09-22.`
In `docs/design/WORKSPACE_DECOUPLING.md`, the wave 1 row's acceptance column records the same.

Add to `docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Moved `sushicore` to its own repository and took it from PyPI (`sushihub/cli/pyproject.toml`, `.github/workflows/ci.yml`).
```

- [ ] **Step 6: Confirm the repository still works without the directory**

```bash
python -m pytest sushihub/cli/tests -q
python -c "import sushicore; print(sushicore.__file__)"
```

Expected: 332 passed, and the import resolves inside `site-packages`. Note that
`sushihub/cli/tests/conftest.py` strips the repository root from `sys.path` specifically because
`sushicore/` used to shadow the installed distribution as a namespace package; with the directory
gone that guard is harmless but no longer load-bearing. Leave it, and say so in the commit body.

- [ ] **Step 7: Commit**

```bash
git add -u
git add docs/design/REMAINING_WORK.md docs/design/WORKSPACE_DECOUPLING.md docs/reference/CHANGELOG.md
git commit -m "refactor!: move sushicore out of this repository"
```

---

### Tasks 7a to 7f: The six consumers take the dependency

Six repositories, one task each, identical in shape. They wait only on task 4, so all six run
beside tasks 5 and 6. No two of them touch the same file.

| Task | Repository | File |
|---|---|---|
| 7a | `D:/Projects/sushiruntime` | `cli/pyproject.toml` |
| 7b | `D:/Projects/sushiengine` | `cli/pyproject.toml` |
| 7c | `D:/Projects/sushiai` | `cli/pyproject.toml` |
| 7d | `D:/Projects/sushiblas` | `cli/pyproject.toml` |
| 7e | `D:/Projects/sushidsp` | `cli/pyproject.toml` |
| 7f | `D:/Projects/sushitrack` | `cli/pyproject.toml` |

**Interfaces:**
- Consumes: `sushicore==0.1.0` on PyPI, from task 4.
- Produces: a consumer CLI that pip can install from a clean environment.

Each task runs these steps in its own repository.

- [ ] **Step 1: Declare the dependency**

Add `"sushicore>=0.1.0",` to the `dependencies` list in `cli/pyproject.toml`.

- [ ] **Step 2: Delete the comment that said it could not be declared**

Every one of the six carries a block, four to six lines, beginning `# sushicore (shared CLI
presentation layer` and explaining that it is published to no index and must be installed by hand
from a sibling path. Delete the whole block. Three of them name a stale path
(`../../sushistack/sushicore`, and `sushiengine`'s names `D:/Projects/sushicore`), which is one
more reason none of them should survive.

`sushitrack` carries a second, separate remark inside its `dependencies` list explaining that Rich
is declared directly even though `sushicore.console` needs it, because sushicore is
editable-installed and unpublished. Rewrite that remark rather than deleting it: the direct Rich
dependency may still be wanted, but the reason given for it is now false.

- [ ] **Step 3: Install from a clean environment and run the CLI's tests**

```bash
python -m venv .venv-check
.venv-check/bin/python -m pip install -e "./cli"
.venv-check/bin/python -m pytest cli/tests -q
```

On Windows the interpreter is `.venv-check/Scripts/python.exe`. Delete `.venv-check` afterwards.

Expected: pip resolves `sushicore` from PyPI with no path given to it, and the CLI's own suite
passes at whatever count that repository reports today. Record the count in the commit body.

- [ ] **Step 4: Update that repository's changelog**

One line in its `docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Took `sushicore` from PyPI instead of a sibling checkout (`cli/pyproject.toml`).
```

- [ ] **Step 5: Commit**

```bash
git add cli/pyproject.toml docs/reference/CHANGELOG.md
git commit -m "build(cli): take sushicore from PyPI instead of a sibling checkout"
```

---

## Order

```
Task 1  ->  Task 2  ->  Task 3  ->  Task 4  -+->  Task 5  ->  Task 6
                                             |
                                             +->  Tasks 7a .. 7f  (six in parallel)
```

Tasks 2, 3 and 4 are the owner's. Tasks 1, 5, 6 and the six of task 7 can each be dispatched to
an agent, and the six of task 7 are dispatched together.
