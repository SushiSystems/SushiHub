# Wave 6: a module describes itself

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** A checkout carrying `sushi-module.toml` is recognised by `hub` whether or not the
catalog lists it. The catalog becomes the fallback rather than the only source.

**Architecture:** The manifest's shape is fixed first, because it is a file other repositories
will write and a format is hard to take back. Then `ModuleCatalog` gains a second source and
every reader keeps asking the same object, so nothing downstream learns a new way to look a
module up. The four modules adopt the file last, once the reader that would use it exists.

**Tech Stack:** Python 3.10+, `tomllib`, pytest.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §3.1 and §3.2.

## Global Constraints

- The suite is at 363 when this wave starts. Every task ends with
  `python -m pytest sushihub/cli/tests -q` green and states its count.
- **Check CI before calling the wave closed.** `gh run list --workflow=CI` is the last task's
  first step, not an afterthought.
- `sushi-module.toml` is a persistent format written by hand in six repositories.
  `file-formats` governs it: its shape is fixed in task 1 and grown only by adding keys.
- The catalog stays closed to strangers. A manifest does not let an arbitrary repository into
  `hub add <name>`; it lets a checkout already in the workspace describe itself. `hub add
  <git-url>` is **not** in this wave.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`;
  commit messages follow `commits`.
- Do not run the build system: `se`, `cmake`, `ninja`, `ctest` are off limits, and no build
  configuration file is edited.

## What was measured, 2026-09-22

- `ModuleCatalog` (`services/catalog.py`) holds `Module(name, repo, directory, alias,
  distribution)` and answers `names()`, `aliases()`, `resolve()`, `__contains__`,
  `__getitem__`, `__iter__`. Its readers are `cli.py` (help strings), `presence.module_dir`,
  `status_report.build_status` and `modules.add`.
- `presence.module_dir` already falls back to `root/name` for a name the catalog does not list,
  which is why a stale `sushidsp` link does not crash `hub status`. That fallback is the seam
  this wave replaces with something that can answer properly.
- The dependency fragment lives at `<module>/cli/sushistack.deps.toml` in all six repositories.
  The manifest is a **second** file with a different job: the fragment says what to install,
  the manifest says what the module *is*. Do not merge them.
- `sushidsp`'s fragment was unreadable until 2026-09-22 and nothing noticed, because the reader
  skipped what it did not understand. The manifest reader is written the other way round: an
  unknown shape is an error that names the file.

---

### Task 1: The manifest's shape

**Files:**
- Create: `docs/reference/MODULE_MANIFEST.md`
- Modify: `docs/README.md` — its reference index

**Interfaces:**
- Consumes: nothing.
- Produces: the format every later task reads and every module writes.

- [ ] **Step 1: Write the format down before any code reads it**

`sushi-module.toml` sits at a module's **repository root**, beside `CMakeLists.txt`, not under
`cli/`. The fragment is under `cli/` because `hub` owned it; the manifest is the module's own
identity and belongs where a reader looks first.

```toml
# What this module is. `hub` reads this when the checkout is in a workspace; when it is
# absent, `hub` falls back to its own catalog entry for a module it already knows.

[module]
name = "sushiruntime"        # the name on the command line and the directory under the root
alias = "sr"                 # the module's own CLI program name
distribution = "source"      # "source" to clone, "binary" for a compiled release
repo = "https://github.com/sushisystems/sushiruntime.git"
fragment = "cli/sushistack.deps.toml"   # path to the dependency fragment, relative to this file
```

Every key is required except `repo`, which a module that is never cloned by name may omit.
`name` must equal the directory the checkout sits in; a mismatch is an error, because every
module's cmake resolves a sibling by that flat layout and a manifest that disagrees would lie
about where the module is.

Record in the same page: the file is read, never written, by `hub`; a key `hub` does not know is
ignored so a newer module can add one; a *table* `hub` does not know is an error, because that is
how a whole section goes missing in silence.

- [ ] **Step 2: Index it**

`docs/README.md` lists every reference page. Add this one with a sentence saying what it is for.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/MODULE_MANIFEST.md docs/README.md
git commit -m "docs: fix the shape of a module's own manifest"
```

---

### Task 2: The reader

**Files:**
- Create: `sushihub/cli/sushistack/services/module_manifest.py`
- Create: `sushihub/cli/tests/test_module_manifest.py`

**Interfaces:**
- Consumes: task 1's format.
- Produces: `read(root: Path) -> Module | None`, returning the `Module` that
  `<root>/sushi-module.toml` describes, or None when the file is absent.

- [ ] **Step 1: Write the failing tests first**

The reader meets files written by hand in other repositories, so its tests are mostly about
what it refuses. Cover, one test each: a complete manifest reads into a `Module`; a missing file
answers None; a missing required key raises and names the key; a `name` that disagrees with the
directory raises and names both; an unknown key is ignored; an unknown *table* raises.

Reuse `services.catalog.Module` rather than declaring a second shape. If a field the manifest
needs is missing from it, say so in the report rather than widening the dataclass quietly.

- [ ] **Step 2: Write the reader**

One function, one responsibility: turn a file into a `Module` or refuse. It resolves no paths,
touches no network, and knows nothing about the catalog. Whether a manifest beats a catalog
entry is task 3's decision, made where both are in scope.

- [ ] **Step 3: Verify and commit**

```bash
python -m pytest sushihub/cli/tests/test_module_manifest.py -q
python -m pytest sushihub/cli/tests -q
git add sushihub/cli/sushistack/services/module_manifest.py sushihub/cli/tests/test_module_manifest.py
git commit -m "feat(cli): read a module's own manifest"
```

---

### Task 3: The catalog becomes the fallback

**Files:**
- Modify: `sushihub/cli/sushistack/services/catalog.py`
- Modify: `sushihub/cli/sushistack/services/presence.py`
- Modify: `sushihub/cli/tests/test_catalog.py`, `test_presence.py`
- Create: `sushihub/cli/tests/test_manifest_precedence.py`

**Interfaces:**
- Consumes: task 2's reader.
- Produces: a lookup that answers for a workspace checkout the catalog never heard of.

- [ ] **Step 1: Decide the precedence and say why**

Two questions, and the report answers both with a reason rather than a preference:

- When a checkout carries a manifest **and** the catalog lists it, which wins? A manifest is
  the module's own statement and travels with the checkout; the catalog is `hub`'s copy and can
  be older. Argue it either way, pick one, write it into `MODULE_MANIFEST.md`.
- What does `hub add <name>` do for a name only a manifest knows? It cannot: `hub add` clones
  from a repo URL it must know *before* any checkout exists. Say so plainly in the help and in
  the error, rather than letting a user guess why a linked module is known to `hub status` and
  unknown to `hub add`.

- [ ] **Step 2: Give the lookup one place, as `module_dir` already has**

`presence.module_dir` is the one directory resolver, made so on 2026-09-22. The manifest lookup
joins it rather than sitting beside it: a caller asks one function what a module is, and that
function consults the checkout first or second per step 1's decision.

Do not teach `ModuleCatalog` to read the disk. It is a catalog: data loaded once from packaged
data. A lookup that may touch a workspace is a different thing with a different lifetime, and
mixing them makes the catalog untestable without a filesystem.

- [ ] **Step 3: Test what this wave exists to make true**

`test_manifest_precedence.py` proves the acceptance criterion directly: a checkout under the
workspace root carrying a manifest, with no catalog entry, is recognised — `hub status` lists
it and its fragment reaches `hub install`. Use `sushidsp`'s real shape as the case, since that
is the checkout this is for.

- [ ] **Step 4: Look at it**

```bash
hub status
hub doctor
```

Paste both, with a manifest present in a linked checkout. `hub doctor`'s owner column is the
evidence the fragment was aggregated; it counts by owner, so a new owner appearing is the proof.

- [ ] **Step 5: Commit**

```bash
git add sushihub/cli/sushistack/services/catalog.py sushihub/cli/sushistack/services/presence.py sushihub/cli/tests/
git commit -m "feat(cli): recognise a checkout that describes itself"
```

---

### Task 4: The four modules adopt the file

**Files** (one commit per repository, in each repository):
- Create: `<repo>/sushi-module.toml` in `sushiruntime`, `sushiengine`, `sushiai`, `sushiblas`
- Modify: each repository's `docs/reference/CHANGELOG.md`

- [ ] **Step 1: Check each tree before touching it**

```bash
cd /d/Projects/<repo> && git status --porcelain && git log --oneline -1
```

These are working repositories with their own uncommitted work. Stage only the two files this
task writes; never `git add -A`. If a tree is dirty, say so and stage by path anyway.

- [ ] **Step 2: Write each manifest from the catalog entry that exists today**

`sushihub/cli/sushistack/catalog.toml` holds all four. The manifest must agree with it
key for key; a disagreement here is the first thing task 3's precedence rule would expose, and
this wave is not where it should first appear.

- [ ] **Step 3: Prove each one reads**

From the workspace:

```bash
python -c "import sys; sys.path.insert(0,'sushihub/cli'); from pathlib import Path; from sushistack.services.module_manifest import read; print(read(Path(r'D:/Projects/<repo>')))"
```

Paste all four.

- [ ] **Step 4: Commit in each repository**

```
build: describe this module in its own manifest
```

Do not push. The owner pushes each repository.

---

### Task 5: Close the wave

**Files:**
- Modify: `docs/design/WORKSPACE_DECOUPLING.md`, `docs/design/REMAINING_WORK.md`
- Modify: `docs/reference/CHANGELOG.md`

- [ ] **Step 1: Check CI**

```bash
git push
gh run list --limit 3 --workflow=CI
```

Green on all four jobs, or the wave is not closed.

- [ ] **Step 2: Record it**

Wave 6's row gains its landing date and what was verified. `REMAINING_WORK.md` gains whatever
this wave left open, including `hub add <git-url>`, which is deliberately not here.

```
- 2026-09-22 — Recognised a checkout that carries its own `sushi-module.toml` (`sushihub/cli/sushistack/services/module_manifest.py`).
```

- [ ] **Step 3: Commit**

```bash
git add docs
git commit -m "docs: record that a module can describe itself"
```

---

## Order

```
Task 1 (format)  ->  Task 2 (reader)  ->  Task 3 (precedence)  ->  Task 4 (four repos)  ->  Task 5 (docs)
```

Strictly serial. The format is fixed before anything reads it; the four repositories adopt it
only once a reader exists to prove each file.

## What this wave does not do

- `hub add <git-url>` stays unwritten. The catalog remains the only source of a repo URL for a
  module that is not yet on disk.
- `sushidsp` and `sushitrack` do not gain manifests here. That is wave 7, where their own
  install story is decided.
- The module CLIs still do not publish to PyPI; that decision stands from wave 4.
