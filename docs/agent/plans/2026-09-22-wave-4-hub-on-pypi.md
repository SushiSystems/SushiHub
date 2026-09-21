# Wave 4: `hub` comes from PyPI and the installer stops cloning

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `hub` to PyPI as `sushihub`, and turn the two installer scripts into a
bootstrap that never clones: Python, git and pipx, then `pipx install sushihub`, then `hub init`
in the directory the user chose.

**Architecture:** The distribution is renamed before anything uploads, because PyPI locks a name
on its first upload and the rename touches five files. Then the release workflow lands and the
owner tags. Only then do the installers switch, because the only honest way to verify them is to
install from the live index. `hub sync` stops assuming the workspace is a git checkout last,
since it is the one command whose meaning the wave changes.

**Tech Stack:** setuptools, `python -m build`, PyPI trusted publishing (OIDC), GitHub Actions,
pipx, PowerShell, POSIX sh, pytest.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §3.4 and §5 wave 4.

## Global Constraints

- **Scope, decided by the owner on 2026-09-22: `hub` alone publishes.** The module CLIs (`sr`,
  `se`, `sa`, `sb`) stay where they are, installed editable from a checkout by `hub add`. The
  reason is written in each module's own `cli/pyproject.toml`: "The CLI always runs from inside a
  checkout (every command resolves the repo root via `find_project_root`)". All nine of `sr`'s
  commands — `build`, `test`, `run`, `package`, `clean`, `doxygen`, `docker`, `config`, `env` —
  need a source tree, so a PyPI install of one would answer every subcommand with an error.
  `sushicore` earned PyPI because it is a library under seven CLIs; `hub` earns it because
  `hub init` runs in an empty folder. The module CLIs fit neither test.
- **The distribution is named `sushihub`**, the owner's decision of 2026-09-22 and what
  `WORKSPACE_DECOUPLING.md` §3.4 already says. Measured 2026-09-22: `pypi.org/simple/` answers
  404 for `sushihub`, `sushistack-cli` and `sushistack`, so the name is free and unreserved
  until the first upload.
- **The installers must not clone at all**, the owner's decision of 2026-09-22. A workspace is
  a directory `hub init` marked; a clone of this repository is one way to get one, not a
  precondition. The consequence is stated rather than hidden: a user installed this way has no
  `sushihub/gui/` and therefore no `hub gui` commands. Wave 5 owns the desktop application's
  distribution.
- Every task ends with `python -m pytest sushihub/cli/tests -q` green and states its count. The
  suite is at 353 when this wave starts.
- `versioning-and-release` and `api-stability` govern tasks 1 and 2: a public name leaves a
  published package, and the rename is breaking for anyone who installed from the checkout.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`;
  commit messages follow `commits`; the installers' prose follows `humanizer`.
- Do not run the build system. `python -m build` is a wheel build, not a CMake build, and is
  allowed; `se`, `cmake`, `ninja` and `ctest` are not.

## What is already broken

Wave 3 moved `sushihub/cli/manifests/` into the package. Both installers detect "am I standing
in a SushiStack checkout?" by testing for that directory:

- `install.ps1:177` — `Test-Path (Join-Path $ScriptDir "sushihub\cli\manifests")`
- `install.sh:110` — `[ -d "$SCRIPT_DIR/sushihub/cli/manifests" ]`

Neither test can pass any more, so both scripts now always take the clone branch, even when run
from inside a checkout. Task 3 deletes the test rather than repairing it; nothing downstream of
it survives the wave. This is not a regression to fix first — it is the code this wave removes.

## The rename's blast radius

`sushistack-cli` appears in five places, measured 2026-09-22:

| File | Line | What it is |
| --- | --- | --- |
| `sushihub/cli/pyproject.toml` | 6 | `name = "sushistack-cli"` |
| `sushihub/cli/install.py` | 29 | `PACKAGE_NAME`, used to uninstall before reinstalling |
| `sushihub/cli/sushistack/describe.py` | 24 | `_DISTRIBUTION`, the version in `hub --describe` |
| `sushihub/cli/sushistack/__init__.py` | 10 | `version("sushistack-cli")` for `__version__` |
| `sushihub/contract/README.md` | 100 | the contract's description of the version field |

The import package stays `sushistack`. Only the distribution is renamed; nothing a module CLI
imports changes.

---

### Task 1: The distribution becomes `sushihub`

**Files:**
- Modify: `sushihub/cli/pyproject.toml`
- Modify: `sushihub/cli/install.py`
- Modify: `sushihub/cli/sushistack/describe.py`
- Modify: `sushihub/cli/sushistack/__init__.py`
- Modify: `sushihub/contract/README.md`
- Modify: `sushihub/cli/tests/test_describe.py` — only if it pins the distribution name; check first

**Interfaces:**
- Consumes: nothing.
- Produces: a wheel whose distribution is `sushihub` and whose import package is still
  `sushistack`, providing the `hub` and `sushihub` console scripts.

- [ ] **Step 1: Find every occurrence before changing one**

```bash
grep -rn "sushistack-cli" --include=*.py --include=*.toml --include=*.md --include=*.yml . \
  | grep -v "\.git/\|build/lib\|egg-info\|docs/agent"
```

Expect the five rows in the table above. If the grep finds a sixth, stop and report it rather
than renaming it blind — `describe.py`'s value feeds the desktop application's contract.

- [ ] **Step 2: Rename, and say in the contract what changed**

Set `name = "sushihub"` in `pyproject.toml`, `PACKAGE_NAME = "sushihub"` in `install.py`,
`_DISTRIBUTION = "sushihub"` in `describe.py`, and `version("sushihub")` in `__init__.py`.

`sushihub/contract/README.md:100` describes the field to the desktop application. Correct the
name there and add one sentence saying the distribution was renamed on 2026-09-22, because a GUI
build pinned to the old name reads `"0"` rather than failing, which is the quiet kind of wrong.

- [ ] **Step 3: Handle the install that is already on this machine**

`install.py` uninstalls `PACKAGE_NAME` before reinstalling. With the new value it will not find
the old install, so a stale `sushistack-cli` would sit in pipx beside the new one, both owning a
`hub` shim. `install.py` already carries `remove_legacy_shim` for exactly this class of problem
(the `ss.exe` left by an earlier rename); read it, and extend the same idea: uninstall
`sushistack-cli` if pipx lists it, then install `sushihub`.

Say in the report what `pipx list` showed before and after.

- [ ] **Step 4: Prove the wheel is right before trusting it**

```bash
python -m build --wheel --outdir <scratch>/dist sushihub/cli
python -c "import zipfile,glob;z=zipfile.ZipFile(sorted(glob.glob('<scratch>/dist/*.whl'))[-1]);print([n for n in z.namelist() if 'dist-info' in n or n.endswith('.toml')])"
```

Expected: a `sushihub-0.1.0.dist-info/` directory, and the four packaged data files wave 3 put
inside (`catalog.toml`, `defaults.toml`, `manifests/base.deps.toml`, `manifests/gui.deps.toml`).

Then reinstall and check the version resolves through the new name:

```bash
python sushihub/cli/install.py
hub --version
python -c "import sushistack; print(sushistack.__version__)"
```

`__version__` printing `0` means `version("sushihub")` did not find the distribution; that is a
failure, not a warning.

- [ ] **Step 5: Test and commit**

```bash
python -m pytest sushihub/cli/tests -q
git add sushihub/cli/pyproject.toml sushihub/cli/install.py sushihub/cli/sushistack/describe.py sushihub/cli/sushistack/__init__.py sushihub/contract/README.md
git commit -m "build(cli)!: rename the distribution to sushihub"
```

---

### Task 2: `sushihub` publishes to PyPI

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: task 1's renamed distribution.
- Produces: `sushihub` 0.1.0 on PyPI, installable with `pipx install sushihub`.

- [ ] **Step 1: Copy the workflow that already works**

`D:/Projects/sushicore/.github/workflows/release.yml` published `sushicore` 0.1.0 and 0.2.0
without incident. Read it and write SushiStack's from it. Two differences, both because `hub`'s
package is not at the repository root:

- the build step runs `python -m build sushihub/cli` and `python -m twine check sushihub/cli/dist/*`;
- the artifact path is `sushihub/cli/dist/`.

Keep the rest as sushicore has it: a `build` job and a `publish` job, `needs: build`,
`environment: pypi`, `permissions: id-token: write`, `pypa/gh-action-pypi-publish@release/v1`,
and no API token anywhere. The environment name must match the one registered with the PyPI
trusted publisher or the upload is rejected for a mismatched claim; sushicore's file says so in
a comment and this one should too.

- [ ] **Step 2: Rehearse the release from a clean clone**

A tag push is irreversible: PyPI does not allow re-uploading a version. Before it, build from a
fresh clone so nothing uncommitted is what makes it work.

```bash
git clone <this repo> <scratch>/release-rehearsal
cd <scratch>/release-rehearsal
python -m build sushihub/cli
python -m twine check sushihub/cli/dist/*
```

Paste both outputs. `twine check` must say `PASSED` for the wheel and the sdist.

- [ ] **Step 3: Register the trusted publisher — owner step**

The owner adds a pending publisher at `pypi.org/manage/account/publishing/`: project `sushihub`,
owner `SushiSystems`, repository `sushistack`, workflow `release.yml`, environment `pypi`. A
pending publisher is what allows the first upload of a name that does not exist yet.

- [ ] **Step 4: Tag — owner step**

```bash
git push
git tag -a v0.1.0 -m "sushihub 0.1.0"
git push origin v0.1.0
gh run watch
```

Then confirm from outside the checkout, because a local install would mask a broken upload:

```bash
python -c "import urllib.request,json;d=json.load(urllib.request.urlopen('https://pypi.org/pypi/sushihub/json'));print(d['info']['version'])"
```

PyPI's JSON endpoint is cached; if it answers stale, re-request with a `Cache-Control: no-cache`
header rather than concluding the upload failed. That happened with `sushicore` 0.2.0.

- [ ] **Step 5: Record it**

`docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Renamed the distribution to `sushihub` (`sushihub/cli/pyproject.toml`).
- 2026-09-22 — Published `hub` to PyPI from a tag (`.github/workflows/release.yml`).
```

Commit the workflow and the changelog together.

---

### Task 3: The installers stop cloning

**Files:**
- Modify: `install.ps1`
- Modify: `install.sh`
- Modify: `sushihub/cli/install.py`
- Modify: `README.md`, `docs/getting_started/INSTALL.md`

**Interfaces:**
- Consumes: `sushihub` on PyPI.
- Produces: two scripts that bootstrap Python, git and pipx, install `sushihub` from the index,
  and run `hub init` in the chosen directory.

- [ ] **Step 1: Decide what git is still for, and say so**

Python and pipx are needed to install `hub`. Git is no longer needed to *get* the workspace, but
`hub add` clones module checkouts with it, so it stays bootstrapped. Write that reason into the
script header rather than leaving a reader to wonder why a non-cloning installer installs git.

- [ ] **Step 2: Replace the locate-or-clone block**

In `install.ps1` the block runs from the comment "Locate or clone the workspace" to
`Info "Workspace: $WorkspaceDir"`, and the `$RepoUrl` variable above it becomes dead. In
`install.sh` the same block sits at lines 107–136, ending at `cd "$WORKSPACE_DIR"`. Both must
become: ask for a directory
(`Prompt-WorkspaceDir` already does this, with its 30-second timeout and its `SUSHISTACK_DIR`
override — keep it), create it if absent, and `Set-Location` / `cd` into it.

`SUSHISTACK_REPO_URL` goes with the clone. Check that nothing else reads it:

```bash
grep -rn "SUSHISTACK_REPO_URL" . --include=*.ps1 --include=*.sh --include=*.py --include=*.md | grep -v docs/agent
```

- [ ] **Step 3: Install from the index, not from the checkout**

`python sushihub/cli/install.py` becomes `python -m pipx install sushihub` — but pipx has to
exist first, and today `install.py` is what bootstraps it. Read `install.py`'s `ensure_pipx`
(line 49) and decide: either both scripts grow the same six lines, or `install.py` gains a mode
that bootstraps pipx and installs from the index. Pick one and say why; duplicating a bootstrap
in three places is the failure mode to avoid.

`install.py` itself stays, and its docstring must say what it is *for* after this wave: the
developer's editable install from a checkout, not the user's install path. Its header currently
describes itself as the install; that becomes false here.

Keep `remove_legacy_shim` and task 1's `sushistack-cli` uninstall. A user upgrading from a
pre-wave-4 install has a `hub` shim pointing into a checkout, and pipx will refuse or shadow.

- [ ] **Step 4: Verify on a clean path, which is the wave's acceptance**

Run the script in a directory that is not a checkout and has no `sushihub/` anywhere, with
`SUSHISTACK_DIR` pointing at a scratch directory so no prompt blocks. Paste the whole output.

Expected: pipx installs `sushihub` from PyPI, `hub init` writes `.sushistack/workspace.toml`,
`hub install` provisions the base tools. Then, in that directory:

```bash
hub status
hub add sushiruntime
```

`hub add` must still clone and install `sr` editable, because that is the scope decision.

Do not run the full `hub install` if it would download several GB on this machine; `--dry-run`
is acceptable evidence for the provisioning step as long as the report says which was run.

- [ ] **Step 5: Rewrite the two pages that tell a user what to do**

`README.md`'s install snippet and `docs/getting_started/INSTALL.md`'s "One command" and "Step by
step" sections describe a clone. Both become the pipx path. `INSTALL.md` also gains one honest
paragraph: an install made this way has no desktop application, and the way to get one today is
to clone the repository.

- [ ] **Step 6: Commit**

```bash
git add install.ps1 install.sh sushihub/cli/install.py README.md docs/getting_started/INSTALL.md
git commit -m "feat(install)!: install hub from PyPI instead of cloning the workspace"
```

---

### Task 4: `hub sync` stops assuming a git checkout

**Files:**
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/sushistack/services/pipx.py`
- Create or modify: `sushihub/cli/tests/test_self_update.py`

**Interfaces:**
- Consumes: `sushihub` on PyPI, and `services/pipx.py` from the cleanup of 2026-09-22.
- Produces: `_self_update` upgrades `hub` the way it was installed.

- [ ] **Step 1: Read what it does today**

`services/modules.py:318`, `_self_update`, returns immediately unless `root / ".git"` is a
directory, then runs `git pull --ff-only` in the workspace root. After this wave most workspaces
are not git checkouts at all, so `hub sync` silently stops updating `hub` — silently, because
the early return says nothing.

- [ ] **Step 2: Upgrade the way `hub` was installed**

Two cases, and the function must tell them apart rather than guessing:

- `hub` came from pipx and the index: `pipx upgrade sushihub`.
- `hub` is an editable install against a checkout (the developer's path, what `install.py`
  writes): a `git pull` in *that checkout*, which is not necessarily the workspace root any more.

`services/pipx.py` already owns `command()`, `distribution_name(pkg_dir)` and
`install(pkg_dir, *, editable)`. Add the upgrade there, beside its siblings, not in
`modules.py`; the brick that knows pipx is the one that should run pipx.

How to tell the two apart is yours to decide and to justify in the report. `pipx list --json`
names the installed package and whether it is editable; an `__editable__*.pth` marker in the
venv is the other signal, and the cleanup's task 3 already used it as evidence. Do not invent a
third mechanism.

- [ ] **Step 3: Test both branches with no network and no pipx**

Patch `pipx.command` and the upgrade entry point with recorders, as
`tests/test_add_binary.py` does for `git_ops`. Assert the pipx branch calls the upgrade and not
git, the editable branch calls git and not the upgrade, and that neither runs under `--dry-run`.
A test that reaches PyPI or GitHub is not acceptable here.

- [ ] **Step 4: Verify and commit**

```bash
python -m pytest sushihub/cli/tests -q
git add sushihub/cli/sushistack/services/modules.py sushihub/cli/sushistack/services/pipx.py sushihub/cli/tests/test_self_update.py
git commit -m "fix(cli): upgrade hub the way it was installed"
```

---

### Task 5: Close the wave

**Files:**
- Modify: `docs/design/WORKSPACE_DECOUPLING.md`, `docs/design/REMAINING_WORK.md`
- Modify: `docs/reference/CHANGELOG.md`
- Modify: `docs/CONTRIBUTING.md`

- [ ] **Step 1: Record the scope decision where it will be found**

`WORKSPACE_DECOUPLING.md` §3.4 says `sr`, `se`, `sa` and `sb` "take the same published
package", which is true of `sushicore` and is easy to misread as "they publish too". Add the
owner's decision and its reason — the checkout dependency — so the next reader does not reopen
it. Wave 4's row gains its landing date and what was verified.

- [ ] **Step 2: Say what a contributor does now**

`docs/CONTRIBUTING.md` describes the repository as the thing you clone to work on the stack.
That is still true for a contributor and false for a user; make the distinction explicit, and
name `sushihub/cli/install.py` as the contributor's install path.

- [ ] **Step 3: Backlog what this wave leaves open**

`REMAINING_WORK.md`, under *Outside the programme*: an installed-from-PyPI workspace has no
desktop application and no `hub gui`. Wave 5 owns it; record it so it is not discovered by a
user first.

- [ ] **Step 4: Commit**

```bash
git add docs
git commit -m "docs: record that hub ships from PyPI"
```

---

## Order

```
Task 1 (rename)  ->  Task 2 (publish)  ->  Task 3 (installers)  ->  Task 4 (self-update)  ->  Task 5 (docs)
```

Strictly serial. Task 2 is partly an owner step twice over: registering the pending publisher and
pushing the tag. Task 3 cannot be verified before task 2 has published.

## What this wave does not do

- The module CLIs do not publish. The owner decided this on 2026-09-22; the reason is in the
  Global Constraints and belongs in the design document, not in a future plan's preamble.
- The desktop application is not distributed. Wave 5 owns it.
- `hub status`'s `sushicore` row still reports `missing`. Wave 5 decides it.
- The old `sushihub/cli/config.local.toml` and `modules.local.toml` stay on disk as wave 3's
  undo.
