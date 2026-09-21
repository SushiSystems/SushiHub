# Wave 3: the workspace keeps its own data

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the `.sushistack` marker from a file into a directory that holds everything the
workspace owns, in one `workspace.toml`, and move the tool's own defaults into the `sushihub`
package, so a directory that is not a SushiStack checkout can be a workspace.

**Architecture:** `sushicore` 0.2.0 goes first, because it holds both the constant that names
SushiStack's directory layout and the TOML writer that would destroy the new file. Then the
marker becomes a directory, then the two data tables move into it one at a time, then the
defaults leave the checkout for the package. Every task ends green.

**Tech Stack:** Python 3.10+, `tomllib`, `importlib.resources`, setuptools package data, pytest,
PyPI trusted publishing.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §3.3 and §5 wave 3.

## Global Constraints

- The owner's four decisions, taken 2026-09-22:
  1. One file. `.sushistack/workspace.toml` holds everything, with `[modules]` and `[tool]`
     tables. No `config.local.toml`, no `modules.local.toml`.
  2. An old workspace upgrades **silently**, under whichever command meets it, with no prompt
     and no separate migration step.
  3. `sushicore` 0.2.0 is task 1, before anything depends on it.
  4. One plan, serial tasks.
- `workspace.toml` is a persistent format written by a released tool and read by the desktop
  application's data. `file-formats` governs it. Its shape is fixed in task 2 and grown only by
  adding tables, never by renaming or moving one.
- `api-stability` and `versioning-and-release` govern task 1: a public name leaves a published
  package.
- Every task ends with `python -m pytest sushihub/cli/tests -q` green and states its count. The
  suite is at 337 when this wave starts.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`;
  commit messages follow `commits`.
- Do not touch `sushicore_dir` or `_sushicore_row`: the `hub status` `sushicore` row is deferred
  to wave 5 by the owner's decision.

## The hazard that shapes this wave

`sushicore.config_base.write_tool_section` rewrites its target file from scratch. It reads the
document, keeps `[tool]` and its `[tool.<platform>]` sub-tables, and writes those alone. Every
other top-level table in that file is lost.

Today that is harmless: `config.local.toml` holds only `[tool]`, and `[modules]` lives in a
separate `modules.local.toml`. The two files are split for exactly this reason — the comment at
`sushihub/cli/sushistack/config.py:69` says so.

The owner chose one file. That removes the split, so the writer must stop destroying what it
does not know about. Task 1 fixes the writer before task 3 puts `[modules]` in its way. Getting
the order wrong loses a developer's link registry the first time `hub install` picks a toolchain.

---

### Task 1: sushicore 0.2.0

**Files** (repository `D:/Projects/sushicore`):
- Modify: `sushicore/workspace.py`
- Modify: `sushicore/config_base.py`
- Modify: `pyproject.toml`
- Modify: `tests/test_module_config.py` — only if it names `WORKSPACE_CLI_DIR`; check first
- Create: `tests/test_config_writer.py`
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `sushicore` 0.2.0 on PyPI. `WORKSPACE_CLI_DIR` no longer exists.
  `write_tool_section(target, updates, header_lines)` keeps its signature and its behaviour for
  `[tool]`, and additionally preserves every other top-level table in the file verbatim.

- [ ] **Step 1: Delete the constant that does not belong**

`sushicore/workspace.py` declares:

```python
#: Where the workspace keeps the `hub` package and the config `hub install` writes, relative to the root.
WORKSPACE_CLI_DIR = Path("sushihub") / "cli"
```

That is SushiStack's directory layout inside a package whose own docstring says it "knows
nothing about SYCL, toolchains, or any module's schema". Delete the constant and its comment.

Before deleting, confirm nothing else in this repository uses it:

```bash
cd /d/Projects/sushicore
grep -rn "WORKSPACE_CLI_DIR" . --include=*.py
```

Measured on 2026-09-22 across all seven Sushi repositories: the only users are in SushiStack,
which task 2 rewrites. If this grep finds a use inside `sushicore` itself, stop and report
rather than inventing a replacement.

- [ ] **Step 2: Make the writer preserve what it did not write**

In `sushicore/config_base.py`, `write_tool_section` rewrites the file and keeps only `[tool]`.
Give it a third thing to do: carry every other top-level table through unchanged.

Read the whole function first. It currently builds `lines` from `header_lines`, then `[tool]`
scalars, then the `[tool.<platform>]` sub-tables. Add, after those, a pass that re-emits every
top-level key of the parsed document other than `tool`, and update the docstring to say so.

The emitter must handle what the callers actually store: a table of string values, which is what
`[modules]` is. Keep it to that and raise on anything else rather than silently dropping it:

```python
def _emit_table(name: str, table: dict) -> list[str]:
    """Render one top-level table of string values as TOML lines.

    @pre Every value is a string; a nested table or a non-string raises, because
        silently dropping it is how a caller loses data it thought was saved.
    """
    lines = ["", f"[{name}]"]
    for key in sorted(table):
        value = table[key]
        if not isinstance(value, str):
            raise TypeError(
                f"[{name}] {key}: only string values are preserved, got {type(value).__name__}")
        lines.append(f'{key} = "{value}"')
    return lines
```

- [ ] **Step 3: Test the preservation, which is the whole point**

`tests/test_config_writer.py`:

```python
"""The config writer keeps the tables it was not asked to write."""

from __future__ import annotations

from sushicore.config_base import write_tool_section
from sushicore.workspace import read_toml


def test_a_sibling_table_survives_a_tool_write(tmp_path):
    """Writing [tool] leaves an unrelated [modules] table intact."""
    target = tmp_path / "workspace.toml"
    target.write_text('[modules]\nsushiai = "D:/Projects/sushiai"\n\n[tool]\ngenerator = "Ninja"\n',
                      encoding="utf-8")
    write_tool_section(target, {"toolchain": "intel-llvm"}, ["# header"])
    doc = read_toml(target)
    assert doc["modules"] == {"sushiai": "D:/Projects/sushiai"}
    assert doc["tool"]["toolchain"] == "intel-llvm"
    assert doc["tool"]["generator"] == "Ninja"


def test_the_platform_sub_table_still_survives(tmp_path):
    """The existing guarantee holds: [tool.<platform>] is preserved verbatim."""
    target = tmp_path / "workspace.toml"
    target.write_text('[tool]\n[tool.windows]\ngenerator = "Ninja"\n', encoding="utf-8")
    write_tool_section(target, {"toolchain": "acpp"}, ["# header"])
    doc = read_toml(target)
    assert doc["tool"]["windows"]["generator"] == "Ninja"
    assert doc["tool"]["toolchain"] == "acpp"


def test_a_non_string_in_a_sibling_table_is_refused(tmp_path):
    """A value the emitter cannot render raises rather than disappearing."""
    import pytest
    target = tmp_path / "workspace.toml"
    target.write_text('[counts]\nmodules = 4\n\n[tool]\n', encoding="utf-8")
    with pytest.raises(TypeError):
        write_tool_section(target, {"toolchain": "acpp"}, ["# header"])
```

- [ ] **Step 4: Bump, release and verify**

Set `version = "0.2.0"` in `pyproject.toml`. Add to `docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Removed `WORKSPACE_CLI_DIR`, which named another repository's layout (`sushicore/workspace.py`).
- 2026-09-22 — Kept sibling tables when writing `[tool]`, so one file can hold more than one section (`sushicore/config_base.py`).
```

Run the suite, then tag. **Owner step**, because pushing a tag publishes:

```bash
cd /d/Projects/sushicore
python -m pytest tests -q          # expect 89 plus the three new tests
git add -A && git commit -m "feat!: drop WORKSPACE_CLI_DIR and preserve sibling tables"
git push
git tag -a v0.2.0 -m "sushicore 0.2.0"
git push origin v0.2.0
gh run watch
```

Then confirm it is installable, from a directory that is not the checkout:

```bash
python -m pip install --upgrade sushicore==0.2.0
python -c "import sushicore.workspace as w; print(hasattr(w, 'WORKSPACE_CLI_DIR'))"
```

Expected: `False`.

- [ ] **Step 5: Pin it in SushiStack**

In `D:/Projects/sushistack/sushihub/cli/pyproject.toml`, raise the dependency to
`"sushicore>=0.2.0"`. SushiStack will not import until task 2 removes its `WORKSPACE_CLI_DIR`
import, so commit this together with task 2 rather than on its own.

---

### Task 2: The marker becomes a directory

**Files:**
- Modify: `sushihub/cli/sushistack/config.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/pyproject.toml`
- Modify: `sushihub/cli/tests/test_workspace_resolution.py`
- Modify: `sushihub/cli/tests/test_init.py`
- Create: `sushihub/cli/tests/test_workspace_upgrade.py`

**Interfaces:**
- Consumes: `sushicore` 0.2.0.
- Produces: `sushistack.config` exporting `WORKSPACE_MARKER = ".sushistack"` (now a directory),
  `WORKSPACE_FILE = "workspace.toml"`, `workspace_file(root: Path | None = None) -> Path` and
  `upgrade_workspace(root: Path) -> bool`, which returns whether it converted anything.

- [ ] **Step 1: Define the file's shape**

`.sushistack/workspace.toml`, written by `hub init`:

```toml
# The SushiStack workspace's own data. `hub` locates this directory by walking up from the
# working directory, and everything it records about this machine lives in this one file.
#
# [workspace] version  the format's version, so a later `hub` can migrate this file.
# [modules]            name = path, written by `hub link`.
# [tool]               tool paths and the selected toolchain, written by `hub install`.

[workspace]
version = "1"
```

`version` is a string, not an integer, so it can become `"1.1"` without changing its type.

- [ ] **Step 2: Resolve the directory, and keep resolving the old file**

In `config.py`, `workspace_root` today walks up for `has_marker(WORKSPACE_MARKER, str(WORKSPACE_CLI_DIR / "manifests"))`.
It must now find either the new directory or the old file, because task 2 alone does not migrate
anyone — the silent upgrade in step 3 does, and it can only run after the root is found.

```python
def workspace_root(start: Path | None = None) -> Path:
    """Locate the SushiStack workspace root.

    The CLI is installed outside the workspace, so the invocation directory is what
    says where the workspace is. Resolution order: ``SUSHISTACK_HOME``, then a walk
    up from the current directory for the ``.sushistack`` marker. The marker is a
    directory since 2026-09-22 and was a file before it; both are accepted, and
    :func:`upgrade_workspace` converts the second into the first.
    """
    home = resolve_env_path("SUSHISTACK_HOME")
    if home:
        return home
    root = walk_up(start or Path.cwd(), has_marker(WORKSPACE_MARKER))
    if root is None:
        raise SystemExit(
            "Not inside a SushiStack workspace: no .sushistack marker found in the "
            "current directory or any parent. Run `hub init` first, or set "
            "SUSHISTACK_HOME to the workspace root.")
    return root
```

`has_marker` already answers for a file or a directory; it calls `.exists()`. The
`sushihub/cli/manifests` fallback goes: it was the repository's own signature, and a workspace is
no longer a repository.

- [ ] **Step 3: Upgrade silently, wherever the workspace is first resolved**

```python
def upgrade_workspace(root: Path) -> bool:
    """Convert a pre-2026-09-22 workspace in place. Return whether anything changed.

    The marker used to be a file and the data used to sit in the checkout, at
    ``sushihub/cli/``. This replaces the file with a directory and moves what it
    finds into ``workspace.toml``: ``modules.local.toml``'s ``[modules]`` and
    ``config.local.toml``'s ``[tool]``. The originals are left where they are, so
    the step is undone by deleting the directory.

    @pre *root* is a workspace root, old or new.
    """
```

Its body, in order:

1. Return `False` when `root / WORKSPACE_MARKER` is already a directory.
2. Read `[modules]` from `root / "sushihub" / "cli" / "modules.local.toml"` and `[tool]` from
   `root / "sushihub" / "cli" / "config.local.toml"`, each through `read_toml`, each `{}` when
   absent.
3. Delete the marker file, create the marker directory, and write `workspace.toml` carrying
   `[workspace] version = "1"` plus whichever of the two tables is non-empty.
4. Leave both source files on disk. Say what happened through `console.info`, once.

Do not call it from `workspace_root` itself. That function runs inside `except SystemExit`
guards in `deps_dir` and `identity_url`, so a write there would fire in code paths that only
meant to read a default.

Call it from `_root`, the `@app.callback(invoke_without_command=True)` at
`sushihub/cli/sushistack/cli.py:37`. Typer runs that callback before every subcommand, which is
what "under whichever command meets it" means. Three guards, all of them required:

- Skip when `--describe` is set. That path prints a catalogue and exits; it must not write.
- Skip when no subcommand was invoked (`ctx.invoked_subcommand is None`), which is `hub` alone
  and `hub --help`.
- Resolve the root inside a `try: ... except SystemExit: return`. Outside a workspace there is
  nothing to upgrade, and `hub init` must still be able to run there.

Say in the report what `hub init` does when it meets an old marker: it is the one command that
both upgrades and then writes, so make sure it does not end up writing the file twice or
reporting the upgrade twice.

- [ ] **Step 4: Point the readers at the new file**

`config_dir` disappears. In its place:

```python
def workspace_file(root: Path | None = None) -> Path:
    """The one file the workspace owns: ``<root>/.sushistack/workspace.toml``."""
    root = root or workspace_root()
    return root / WORKSPACE_MARKER / WORKSPACE_FILE
```

`registered_modules` reads `[modules]` from `workspace_file()`. `load_config`'s `sources` list
becomes the packaged defaults (task 5) plus `workspace_file()`; until task 5 lands, keep reading
`root / "sushihub" / "cli" / "config.toml"` as the defaults so this task changes one thing.
`identity_url` reads `[identity]` from `workspace_file()` then the same defaults.
`set_toolchain` writes `workspace_file()`.

`services/modules.py`: `init()` creates the directory and the file rather than writing a marker
file, and `_write_link` writes `[modules]` into `workspace_file()` through
`write_tool_section`'s sibling-preserving behaviour — or, if `[modules]` is what is being
written rather than `[tool]`, through a small local writer that does the same for one table.
Decide which and say why; do not write a second whole-file rewriter that can lose `[tool]`.

- [ ] **Step 5: Follow the tests**

`tests/test_workspace_resolution.py` asserts `config_dir(...) == root / WORKSPACE_CLI_DIR` and
that a `sushihub/cli/manifests` tree marks a workspace. Both facts are gone. Replace them with
the new ones: `workspace_file` resolves to `<root>/.sushistack/workspace.toml`, and a directory
marker resolves while a bare `sushihub/cli/manifests` tree does not.

`tests/test_init.py` asserts the marker is a file with a particular comment. It is a directory
now, holding a file with a `[workspace] version`.

`tests/test_workspace_upgrade.py` is new and is the task's real evidence:

```python
"""An old workspace becomes a new one under whichever command meets it first."""

from __future__ import annotations

from sushistack.config import WORKSPACE_MARKER, upgrade_workspace, workspace_file
from sushicore.workspace import read_toml


def _old_workspace(root):
    """Build a pre-2026-09-22 workspace: a marker file and the two data files."""
    (root / WORKSPACE_MARKER).write_text("# old marker\n", encoding="utf-8")
    cli = root / "sushihub" / "cli"
    cli.mkdir(parents=True)
    (cli / "modules.local.toml").write_text(
        '[modules]\nsushiai = "D:/Projects/sushiai"\n', encoding="utf-8")
    (cli / "config.local.toml").write_text(
        '[tool]\ntoolchain = "intel-llvm"\n', encoding="utf-8")
    return root


def test_the_marker_file_becomes_a_directory(tmp_path):
    """Upgrading replaces the file with a directory holding workspace.toml."""
    _old_workspace(tmp_path)
    assert upgrade_workspace(tmp_path) is True
    assert (tmp_path / WORKSPACE_MARKER).is_dir()
    assert workspace_file(tmp_path).is_file()


def test_both_tables_move_across(tmp_path):
    """The link registry and the tool section survive the move."""
    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    doc = read_toml(workspace_file(tmp_path))
    assert doc["modules"] == {"sushiai": "D:/Projects/sushiai"}
    assert doc["tool"]["toolchain"] == "intel-llvm"
    assert doc["workspace"]["version"] == "1"


def test_the_originals_are_left_alone(tmp_path):
    """Nothing is deleted, so the step is undone by removing the directory."""
    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    assert (tmp_path / "sushihub" / "cli" / "modules.local.toml").is_file()
    assert (tmp_path / "sushihub" / "cli" / "config.local.toml").is_file()


def test_upgrading_twice_changes_nothing(tmp_path):
    """A workspace already in the new shape is left exactly as it is."""
    _old_workspace(tmp_path)
    upgrade_workspace(tmp_path)
    before = workspace_file(tmp_path).read_text(encoding="utf-8")
    assert upgrade_workspace(tmp_path) is False
    assert workspace_file(tmp_path).read_text(encoding="utf-8") == before


def test_a_workspace_with_no_old_data_still_upgrades(tmp_path):
    """A marker file with nothing beside it becomes a directory with a version alone."""
    (tmp_path / WORKSPACE_MARKER).write_text("# old marker\n", encoding="utf-8")
    assert upgrade_workspace(tmp_path) is True
    doc = read_toml(workspace_file(tmp_path))
    assert doc["workspace"]["version"] == "1"
    assert "modules" not in doc
```

- [ ] **Step 6: Verify on this machine, which is an old workspace**

This checkout is a real pre-upgrade workspace: it has a `.sushistack` marker file and a
`sushihub/cli/modules.local.toml` linking five modules, two of which the catalog no longer
knows. Before running anything, copy both aside so the run can be repeated:

```bash
cp .sushistack /tmp/marker.bak
cp sushihub/cli/modules.local.toml /tmp/modules.bak
```

Then run `hub status` and paste the whole output. Expected: one line saying the workspace was
upgraded, a `.sushistack/` directory, and the same four module rows as before, with the linked
paths intact. Paste `cat .sushistack/workspace.toml` too.

`sushidsp` and `sushitrack` carry across into `[modules]` even though the catalog dropped them.
That is correct: the upgrade moves data, it does not judge it, and `hub status` ignores what the
catalog does not list. Say so in the report rather than "fixing" it.

Then prove the other half of the design's acceptance, a workspace that was never a checkout:

```bash
mkdir /tmp/fresh && cd /tmp/fresh
hub init
cat .sushistack/workspace.toml
hub install --dry-run
```

Expected: `hub init` writes the directory in a folder that has no `sushihub/` anywhere, and
`hub install --dry-run` runs there. Paste all three outputs. Delete `/tmp/fresh` afterwards.

- [ ] **Step 7: Commit**

Stage the SushiStack changes together with task 1's dependency bump.

```bash
git add sushihub/cli/pyproject.toml sushihub/cli/sushistack/config.py sushihub/cli/sushistack/services/modules.py sushihub/cli/tests/
git commit -m "feat(cli)!: keep the workspace's data in a .sushistack directory"
```

---

### Task 3: The defaults move into the package

**Files:**
- Move: `sushihub/cli/config.toml` to `sushihub/cli/sushistack/defaults.toml`
- Move: `sushihub/cli/manifests/*.deps.toml` to `sushihub/cli/sushistack/manifests/`
- Modify: `sushihub/cli/pyproject.toml`
- Modify: `sushihub/cli/sushistack/config.py`
- Modify: `sushihub/cli/sushistack/setup/dependency_source.py`
- Modify: `sushihub/cli/tests/test_identity.py`, `test_gui_build.py`, `test_json_streams.py` —
  each builds a fake `sushihub/cli/` tree; check each with
  `grep -rn "WORKSPACE_CLI_DIR\|config.toml\|manifests" sushihub/cli/tests`

**Interfaces:**
- Consumes: task 2's `workspace_file`.
- Produces: `load_config` and `manifest_sources` read the package, not the checkout.

- [ ] **Step 1: Move the files and ship them**

The committed defaults belong to the tool. `config.toml` becomes `sushistack/defaults.toml`,
beside `catalog.toml`, and the two manifest fragments become `sushistack/manifests/base.deps.toml`
and `sushistack/manifests/gui.deps.toml`.

In `pyproject.toml`, extend the package data:

```toml
sushistack = ["py.typed", "catalog.toml", "defaults.toml", "manifests/*.deps.toml"]
```

Build a wheel and confirm all four are inside before going further — this is how the catalog was
checked in wave 2 and it is the only way to know:

```bash
python -m build --wheel sushihub/cli
python -c "import zipfile,glob;z=zipfile.ZipFile(sorted(glob.glob('sushihub/cli/dist/*.whl'))[-1]);print([n for n in z.namelist() if n.endswith(('.toml','py.typed'))])"
```

- [ ] **Step 2: Read them through importlib.resources**

`load_config`'s sources become the packaged `defaults.toml` followed by `workspace_file()`.
`load_tool_config` takes paths, and `importlib.resources.files(...)` gives a traversable that is
a real path for a wheel installed unzipped, which is what pip produces. Use
`importlib.resources.as_file` rather than assuming, and say in the report which form you used.

`dependency_source.manifest_sources` reads `config_dir() / "manifests"` at line 147. That becomes
the packaged directory. The rest of the function — the workspace walk and the linked checkouts —
is unchanged and must stay unchanged: it is what makes a module's own fragment count.

- [ ] **Step 3: Delete the checkout copies and the last of the old layout**

`git rm sushihub/cli/config.toml` and `git rm -r sushihub/cli/manifests`. Check that nothing
still names them:

```bash
grep -rn "cli/config.toml\|cli/manifests\|config.local.toml\|modules.local.toml" sushihub docs README.md --include=*.py --include=*.md --include=*.toml | grep -v docs/agent
```

Resolve every hit. `.gitignore`'s `/sushihub/cli/config.local.toml` and
`/sushihub/cli/modules.local.toml` lines, and the same two in `_GITIGNORE_LINES` in
`services/modules.py`, name files a new workspace never creates; replace both with
`/.sushistack/`.

- [ ] **Step 4: Verify**

Run: `python -m pytest sushihub/cli/tests -q`

Run `hub doctor` and paste the output: it reads every manifest, so it proves the packaged
fragments are found.

Run `hub install --dry-run` and paste it: it aggregates the fragments and resolves the toolchain
from the defaults, which is the other half.

- [ ] **Step 5: Commit**

```bash
git add -u sushihub/cli
git add sushihub/cli/sushistack/defaults.toml sushihub/cli/sushistack/manifests .gitignore
git commit -m "refactor(cli)!: ship the defaults and the manifests inside the package"
```

---

### Task 4: Close the wave

**Files:**
- Modify: `README.md`, `docs/architecture/WORKSPACE.md`, `docs/getting_started/INSTALL.md`,
  `docs/guides/LINKING_CHECKOUTS.md`, `docs/CONTRIBUTING.md`
- Modify: `docs/design/REMAINING_WORK.md`, `docs/design/WORKSPACE_DECOUPLING.md`
- Modify: `docs/reference/CHANGELOG.md`

- [ ] **Step 1: Correct every page that draws the old layout**

`docs/architecture/WORKSPACE.md` draws the tree with `.sushistack` as a marker file and
`sushihub/cli/` holding the manifests. `docs/guides/LINKING_CHECKOUTS.md` tells a reader to edit
`sushihub/cli/modules.local.toml` by hand, twice, including under "Undoing a link".
`docs/CONTRIBUTING.md` and `README.md` describe what the repository carries.

Find them all and fix each:

```bash
grep -rn "modules.local.toml\|config.local.toml\|sushihub/cli/manifests\|\.sushistack" README.md docs --include=*.md | grep -v docs/agent
```

- [ ] **Step 2: Say what an upgrade does**

Add to `docs/getting_started/INSTALL.md`, beside the existing upgrade section:

```markdown
### The workspace moved its data on 2026-09-22

`.sushistack` used to be an empty marker file, with the workspace's data in the checkout at
`sushihub/cli/config.local.toml` and `sushihub/cli/modules.local.toml`. It is a directory now,
and both tables live in `.sushistack/workspace.toml`.

Nothing is asked of you: the first `hub` command run in an old workspace converts it and says so.
The two old files are left where they are, so deleting `.sushistack/` puts you back.
```

- [ ] **Step 3: Close the wave**

`docs/design/REMAINING_WORK.md` and `docs/design/WORKSPACE_DECOUPLING.md`: the wave 3 rows gain
their landing date and the acceptance column records what was verified.

`docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Moved the workspace's own data into `.sushistack/workspace.toml` (`sushihub/cli/sushistack/config.py`).
- 2026-09-22 — Shipped the tool's defaults and dependency manifests inside the package (`sushihub/cli/sushistack/defaults.toml`, `sushihub/cli/sushistack/manifests/`).
```

- [ ] **Step 4: Commit**

```bash
git add README.md docs
git commit -m "docs: record that the workspace keeps its own data"
```

---

## Order

```
Task 1 (sushicore 0.2.0)  ->  Task 2 (marker + data)  ->  Task 3 (defaults)  ->  Task 4 (docs)
```

Strictly serial. Task 1 is partly an owner step: the tag push publishes.

## What this wave does not do

- `hub status`'s `sushicore` row still reports `missing`. Wave 5 decides it.
- The old `sushihub/cli/config.local.toml` and `modules.local.toml` are left on disk forever
  rather than deleted. A later wave may remove them once no one is upgrading from that shape;
  until then they are the undo.
- The desktop application's fixtures are not re-recorded. Wave 5 owns that, and `hub status`'s
  payload does not change in this wave.
