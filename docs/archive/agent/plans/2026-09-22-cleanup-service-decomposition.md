# Cleanup: one responsibility per brick in the service layer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `services/modules.py` into bricks with one responsibility each, and remove the
three places where the same job has two or three implementations.

**Architecture:** `modules.py` keeps the command bodies — `init`, `add`, `link`, `update`,
`sync` — and the mechanics under them move out: the link registry, git, pipx, the binary install
policy. Two duplications collapse into one implementation each, and `hub status`'s rendering
joins the report that builds it.

**Tech Stack:** Python 3.10+, pytest.

**Spec:** none. This is a structural debt this programme created and measured on 2026-09-22; the
measurements are in §"What was measured" below. It is not part of
`docs/design/WORKSPACE_DECOUPLING.md`, and wave 3 waits until it lands.

## Global Constraints

- The owner's decisions, taken 2026-09-22: four new bricks (`pipx.py`, `git_ops.py`,
  `binary.py`, `links.py`); `links.py` owns both the read and the write of the link registry;
  `hub status`'s rendering moves into `status_report.py`.
- Behaviour does not change anywhere in this plan, except where a duplication is collapsed and
  the two implementations disagreed. Every such disagreement is named in its task and resolved
  deliberately, never by picking whichever was shorter.
- Every task ends with `python -m pytest sushihub/cli/tests -q` green. The suite is at 337 when
  this plan starts.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`;
  commit messages follow `commits`.
- Do not touch `sushicore_dir` or `_sushicore_row`: the `hub status` `sushicore` row is deferred
  to wave 5 by the owner's decision.

## What was measured

On 2026-09-22, against `sushihub/cli/sushistack/services/`:

- `modules.py` is 557 lines and 20 top-level functions, spanning path resolution, the link
  registry, git, binary install, pipx, name resolution, six command bodies and status rendering.
- **Installing a module's CLI has two implementations that disagree.**
  `modules.py:207 _pipx_cmd` with `modules.py:226 _install_module_cli` runs
  `pipx install --force`; `cli_install.py:37 _ensure_pipx` with `cli_install.py:110` runs
  `pipx install --force --editable`. So `hub add sushiruntime` and
  `hub install-cli sushiruntime` leave different installs on the same machine.
- **Resolving a module's directory has three implementations.** `modules.py:56 module_dest`
  answers `root / CATALOG[name].directory`; `presence.py:75 _module_dir` answers `root / name`;
  `status_report.py:36 _module_dir` picks between a link target and `module_dest`. The first two
  agree today only because every catalog entry's `directory` equals its `name`. `catalog.toml`
  carries a `directory` field precisely so that they may differ, and on the day one does,
  `presence` looks in the wrong place and `hub status` reports a present module as absent.

## The hazard that will bite this plan

Five test modules monkeypatch functions **by their name in `modules`**:
`test_add_binary.py`, `test_add_provisions.py`, `test_cli_install.py`, `test_link.py`,
`test_presence.py`.

`test_add_binary.py`'s `workspace` fixture is the sharpest case. It patches
`modules._run_git` and `modules._source_reachable` to `pytest.fail(...)`, so that a test which
reaches the network or the disk fails loudly. The moment `add` calls `git_ops.run_git` instead
of `modules._run_git`, that patch stops intercepting anything — and the guard does not fail, it
silently stops guarding. The test still passes, and it now runs real git.

So every task that moves a function must repoint the patches in the same commit, and must prove
the guard still guards. The proof is in each task's verification step and is not optional.

---

### Task 0: Reshape the sushicore writer before 0.2.0 ships

`sushicore` 0.2.0 is committed at `15e65d8` in `D:/Projects/sushicore` and has **not** been
pushed, tagged or published. Its `write_tool_section` now writes `[tool]` and also carries every
other top-level table through. The name says one thing and the function does two.

Because nothing has shipped yet, the right shape costs nothing now and a whole release later.

**Files** (repository `D:/Projects/sushicore`):
- Modify: `sushicore/config_base.py`
- Modify: `tests/test_config_writer.py`
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Produces: `write_toml_document(target, tables, header_lines) -> Path`, which writes a whole
  document from `{table_name: {key: value}}`, normalising backslashes and refusing a value it
  cannot render. `write_tool_section(target, updates, header_lines) -> Path` keeps its signature
  and becomes a thin caller: it reads the document, merges *updates* into `tool`, and hands the
  whole thing to `write_toml_document`.

- [ ] **Step 1: Extract the document writer**

Read `write_tool_section` as it stands at `15e65d8`. It does four things in sequence: read the
document, merge `updates` into `tool`, render `[tool]` scalars and `[tool.<platform>]` tables,
render every sibling table through `_emit_table`.

Split at the seam: rendering a whole document is the brick, merging one table is the caller.
`write_toml_document` takes the tables to write and renders all of them, keeping the existing
ordering — `[tool]` first with its platform sub-tables, then the rest sorted — so no existing
file changes shape. `_emit_table` becomes its private helper.

- [ ] **Step 2: Keep the existing tests and add one for the new entry point**

`tests/test_config_writer.py`'s three tests exercise `write_tool_section` and must keep passing
unchanged: that is the evidence the split changed nothing. Add:

```python
def test_the_document_writer_renders_every_table_it_is_given(tmp_path):
    """write_toml_document writes each table, tool first, the rest sorted."""
    target = tmp_path / "workspace.toml"
    write_toml_document(
        target,
        {"modules": {"sushiai": "D:\\Projects\\sushiai"}, "tool": {"toolchain": "acpp"},
         "workspace": {"version": "1"}},
        ["# header"])
    body = target.read_text(encoding="utf-8")
    assert body.index("[tool]") < body.index("[modules]") < body.index("[workspace]")
    assert 'sushiai = "D:/Projects/sushiai"' in body
```

- [ ] **Step 3: Verify and commit**

Run: `python -m pytest tests -q` — expect 96 plus the new test.
Run: `python -m build -q && python -m twine check dist/*`, then delete `dist/` and `build/`.

```bash
cd /d/Projects/sushicore
git add -A
git commit -m "refactor: make the document writer the brick and the tool writer its caller"
```

Do not push or tag. The owner publishes 0.2.0 once this plan's sushicore work is done.

---

### Task 1: links.py owns the registry

**Files:**
- Create: `sushihub/cli/sushistack/services/links.py`
- Modify: `sushihub/cli/sushistack/config.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/tests/test_link.py`
- Check and repoint: every other test naming `registered_modules` or `_write_link`

**Interfaces:**
- Produces: `sushistack.services.links` exporting `registered() -> dict[str, str]` and
  `write(name: str, path: Path) -> None`. `config.registered_modules` is deleted, not
  re-exported: a name with two homes is what this plan is removing.

- [ ] **Step 1: Move both halves into one brick**

`config.py:73 registered_modules` reads `[modules]`; `modules.py:80 _write_link` writes it.
Move both into `links.py` as `registered` and `write`. Keep the reading behaviour exactly,
including the `except SystemExit: return {}` guard that lets it answer outside a workspace.

- [ ] **Step 2: Repoint every caller**

```bash
grep -rn "registered_modules\|_write_link" sushihub/cli --include=*.py
```

Every hit becomes `links.registered()` or `links.write(...)`. `status_report.py`, `steps.py`,
`presence.py` and `modules.py` are the expected callers; confirm against the grep rather than
this list.

- [ ] **Step 3: Repoint the tests, and prove the fixture still isolates**

`test_link.py`'s `cfg_dir` fixture patches `modules.config_dir`. After the move the writer lives
in `links`, so the patch target changes. **This fixture is the one that stopped a test from
reading the developer's real `modules.local.toml`** — CI caught that on 2026-09-22 and the fix
was to pin `SUSHISTACK_HOME` inside it. Keep both the env pin and the patch, retargeted.

Prove the isolation survived rather than assuming it:

```bash
python -m pytest sushihub/cli/tests/test_link.py -q
python -c "
import tomllib, pathlib
p = pathlib.Path('sushihub/cli/modules.local.toml')
print('developer registry still on disk, untouched:', sorted(tomllib.loads(p.read_text())['modules']))
"
```

The second command must print the same five names before and after the test run.

- [ ] **Step 4: Verify and commit**

Run: `python -m pytest sushihub/cli/tests -q` — expect 337.

```bash
git add sushihub/cli/sushistack/services/links.py sushihub/cli/sushistack/config.py sushihub/cli/sushistack/services/ sushihub/cli/tests/
git commit -m "refactor(cli): give the link registry one owner"
```

---

### Task 2: git_ops.py owns git

**Files:**
- Create: `sushihub/cli/sushistack/services/git_ops.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/tests/test_add_binary.py`, `test_add_provisions.py`, and any other test
  the grep below names

**Interfaces:**
- Produces: `sushistack.services.git_ops` exporting `run(args: list[str], cwd: Path) -> int`,
  `source_reachable(repo: str) -> bool` and `REACHABLE_TIMEOUT`.

- [ ] **Step 1: Move the three git functions**

`modules.py:98 _run_git`, `modules.py:107 _source_reachable` and the `REACHABLE_TIMEOUT`
constant at `modules.py:41` move to `git_ops.py` as `run`, `source_reachable` and
`REACHABLE_TIMEOUT`.

`modules.py:519 _self_update` stays in `modules.py`: it is the `hub sync` policy of pulling the
workspace's own checkout, not a git primitive. It calls `git_ops.run`.

- [ ] **Step 2: Repoint the fail-guards, which is the dangerous part**

```bash
grep -rn "_run_git\|_source_reachable" sushihub/cli/tests
```

`test_add_binary.py`'s `workspace` fixture patches both to `pytest.fail`. Retarget both to
`git_ops`. Then prove the guard still intercepts, because a patch pointed at the wrong module
does not fail — it silently stops guarding.

Do not prove it by letting real git run: `source_reachable` calls `git ls-remote`, which reaches
the network. Prove it by counting calls instead. Replace the fixture's `pytest.fail` with a
recorder for the length of one check, run the file, and assert the recorder saw nothing:

```python
calls = []
monkeypatch.setattr(git_ops, "run", lambda args, cwd: calls.append(args) or 0)
monkeypatch.setattr(git_ops, "source_reachable", lambda repo: calls.append(repo) or False)
```

Then, in a throwaway check you do not commit, assert `calls == []` after the binary tests run.
If the list is non-empty, the tests were reaching git through a path the old guard never covered:
report that rather than adjusting the assertion. Restore `pytest.fail` before committing, because
a guard that fails loudly is the point.

- [ ] **Step 3: Verify and commit**

Run: `python -m pytest sushihub/cli/tests -q` — expect 337.

```bash
git add sushihub/cli/sushistack/services/git_ops.py sushihub/cli/sushistack/services/modules.py sushihub/cli/tests/
git commit -m "refactor(cli): give git its own brick"
```

---

### Task 3: pipx.py, one implementation instead of two

This task changes behaviour, on purpose, and is the reason this plan exists.

**Files:**
- Create: `sushihub/cli/sushistack/services/pipx.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/sushistack/services/cli_install.py`
- Modify: `sushihub/cli/tests/test_cli_install.py`

**Interfaces:**
- Produces: `sushistack.services.pipx` exporting
  `command() -> list[str] | None`, `distribution_name(pkg_dir: Path) -> str` and
  `install(pkg_dir: Path, *, editable: bool) -> int`.

- [ ] **Step 1: Decide the disagreement before writing any code**

`modules._install_module_cli` installs **not** editable; `cli_install.install_cli` installs
**editable**. One of them is wrong and the plan does not get to dodge which.

`cli_install.py`'s own docstring argues for editable, at `cli_install.py:70`: a non-editable
install freezes the CLI at the revision on disk, so later `git pull`s on the module stop reaching
the installed `sr`/`se`, until someone reinstalls by hand. `hub add` clones a module and installs
its CLI; that checkout is exactly the kind that gets pulled.

So editable wins, and `hub add`'s path is the one that changes. Read both call sites and confirm
that argument holds before acting on it; if you find a reason `hub add` deliberately wanted a
frozen install, stop and report rather than changing behaviour on my say-so.

- [ ] **Step 2: Write the brick and route both callers through it**

`pipx.command()` is `modules._pipx_cmd`'s body: `shutil.which("pipx")`, then `python3 -m pipx`,
then `python -m pipx`. `cli_install._ensure_pipx` raises where `_pipx_cmd` returns `None`; keep
returning `None` and let `cli_install` raise at its own call site, so the brick reports and the
caller decides.

`pipx.distribution_name` is `cli_install._dist_name`.

`pipx.install(pkg_dir, editable=True)` runs `pipx install --force [--editable] <pkg_dir>` and
returns the exit code.

- [ ] **Step 3: Follow the tests**

`test_cli_install.py` covers `_install_module_cli`: a module with no `cli/` package, a missing
pipx, and the happy path asserting the exact argv
`["pipx", "install", "--force", str(checkout / "cli")]`. That argv gains `--editable`, which is
the behaviour change; update the assertion and say so in the report.

Add one test that the two entry points now agree, because that is the defect being fixed:

```python
def test_both_paths_install_a_module_cli_the_same_way(checkout, recorder, monkeypatch):
    """hub add and hub install-cli leave the same install behind."""
    runs = _Runs()
    monkeypatch.setattr(pipx, "command", lambda: ["pipx"])
    monkeypatch.setattr(pipx, "subprocess", type("S", (), {"run": runs}))
    modules._install_module_cli("sushiruntime", checkout)
    from_add = list(runs.commands)
    runs.commands.clear()
    pipx.install(checkout / "cli", editable=True)
    assert runs.commands == from_add
```

Adjust it to whatever the real module and fixture names are; the assertion is the point, not the
spelling.

- [ ] **Step 4: Verify on this machine**

Run: `python -m pytest sushihub/cli/tests -q` — expect 338.

Then prove the behaviour change end to end, because five module CLIs on this machine were
reinstalled on 2026-09-22 and are the evidence:

```bash
hub install-cli sushiruntime
python -c "
import pathlib
v = pathlib.Path.home() / 'pipx/venvs/sushiruntime-cli/Lib/site-packages'
print([p.name for p in v.glob('__editable__*')])
"
```

Expected: an editable marker for `sushiruntime_cli`. Paste it.

- [ ] **Step 5: Commit**

```bash
git add sushihub/cli/sushistack/services/pipx.py sushihub/cli/sushistack/services/modules.py sushihub/cli/sushistack/services/cli_install.py sushihub/cli/tests/test_cli_install.py
git commit -m "fix(cli): install a module's CLI the same way from both commands"
```

---

### Task 4: binary.py owns the licensed install policy

**Files:**
- Create: `sushihub/cli/sushistack/services/binary.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/tests/test_add_binary.py`

**Interfaces:**
- Produces: `sushistack.services.binary` exporting
  `install(name, dest, client, info=None) -> bool`, `add(name, dest, requested) -> bool` and
  `update(name, dest) -> bool`.

- [ ] **Step 1: Move the trio**

`modules.py:125 _install_binary`, `:151 _add_binary` and `:177 _update_binary` move as `install`,
`add` and `update`. They are the licence-and-session policy above `releases.py`'s mechanics
(download, verify, unpack), which stays where it is and is not touched.

- [ ] **Step 2: Repoint the 18 tests that pin this path**

`test_add_binary.py` is the most valuable file in the suite: 18 tests covering the clone, the
out-of-reach fallback, the forced binary, the missing licence, the hash mismatch and the update
path. Do not weaken any of them. Its `workspace` and `recorder` fixtures patch `modules.*`;
retarget only what moved, and run the file on its own before running the suite.

- [ ] **Step 3: Verify and commit**

Run: `python -m pytest sushihub/cli/tests/test_add_binary.py -q` — expect 18.
Run: `python -m pytest sushihub/cli/tests -q` — expect 338.

```bash
git add sushihub/cli/sushistack/services/binary.py sushihub/cli/sushistack/services/modules.py sushihub/cli/tests/test_add_binary.py
git commit -m "refactor(cli): give the licensed install its own brick"
```

---

### Task 5: one answer to where a module lives

**Files:**
- Modify: `sushihub/cli/sushistack/services/presence.py`
- Modify: `sushihub/cli/sushistack/services/status_report.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/tests/test_presence.py`

**Interfaces:**
- Produces: `presence.module_dir(root: Path, name: str, linked: Mapping[str, str] | None = None) -> Path`
  as the one resolver. `modules.module_dest` and `status_report._module_dir` are deleted.

- [ ] **Step 1: Pick the correct behaviour, which is not the majority one**

Two of the three implementations answer `root / name`; one answers
`root / CATALOG[name].directory`. The catalog is right: `directory` exists as a field so a module
may one day land somewhere other than its own name, and a resolver that ignores it is a latent
bug rather than a simplification.

The one resolver reads the catalog. Where `linked` is given it wins, as all three already agree.
A name the catalog does not know — a stale link to `sushidsp`, which this machine has — must not
raise: return the linked path when there is one, and otherwise `root / name`, so `hub status`
keeps ignoring it rather than crashing. Write a test for exactly that case.

- [ ] **Step 2: Delete the other two and repoint**

```bash
grep -rn "module_dest\|_module_dir" sushihub/cli --include=*.py
```

- [ ] **Step 3: Verify and commit**

Run: `python -m pytest sushihub/cli/tests -q` — expect 339.

Run `hub status` and paste it: the four modules must show the same locations as before, and the
stale `sushidsp` link must still be absent from the table rather than raising.

```bash
git add sushihub/cli/sushistack/services/ sushihub/cli/tests/test_presence.py
git commit -m "refactor(cli): resolve a module's directory in one place, through the catalog"
```

---

### Task 6: status renders where it is built

**Files:**
- Modify: `sushihub/cli/sushistack/services/status_report.py`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/sushistack/cli.py`
- Modify: whichever test names `modules.status`; check with a grep

**Interfaces:**
- Produces: `status_report.render(payload: dict) -> int`. `modules.status` and
  `modules._branch_cell` are deleted.

- [ ] **Step 1: Move the renderer**

`modules.py:490 _branch_cell` and `modules.py:499 status` move into `status_report.py` as
`_branch_cell` and `render`. `cli.py`'s `status` command calls `status_report.render` after
`build_status`.

- [ ] **Step 2: Verify and commit**

Run: `python -m pytest sushihub/cli/tests -q` — expect 339.
Run: `hub status` and `hub status --json`, and paste both. The table and the JSON must be
identical to what they were before this task.

```bash
git add sushihub/cli/sushistack/services/status_report.py sushihub/cli/sushistack/services/modules.py sushihub/cli/sushistack/cli.py sushihub/cli/tests/
git commit -m "refactor(cli): render the status table where its payload is built"
```

---

### Task 7: Close the cleanup

- [ ] **Step 1: Measure what changed**

```bash
wc -l sushihub/cli/sushistack/services/*.py | sort -rn
```

Record `modules.py`'s new length. The target is roughly 250 lines holding `init`, `add`, `link`,
`update`, `sync`, `_resolve_names`, `_provision` and `_self_update`. If it is much larger, say
what stayed and why rather than forcing a number.

- [ ] **Step 2: Record it**

`docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Split the module service into bricks: links, git, pipx and the licensed install (`sushihub/cli/sushistack/services/`).
- 2026-09-22 — Installed a module's CLI the same way from `hub add` and `hub install-cli` (`sushihub/cli/sushistack/services/pipx.py`).
- 2026-09-22 — Resolved a module's directory in one place, through the catalog (`sushihub/cli/sushistack/services/presence.py`).
```

`docs/design/REMAINING_WORK.md`: add one line under *Outside the programme* recording that the
`hub status` `sushicore` row is still a non-module reported as a module, deferred to wave 5.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/CHANGELOG.md docs/design/REMAINING_WORK.md
git commit -m "docs: record the service decomposition"
```

---

## Order

```
Task 0 (sushicore, unshipped)  ->  1 links  ->  2 git  ->  3 pipx  ->  4 binary  ->  5 dir  ->  6 status  ->  7 docs
```

Serial: tasks 1 through 6 all edit `modules.py`. Task 0 is in another repository and could run
beside them, but it gates the owner's 0.2.0 release, so it goes first.

## What this plan does not do

- It does not touch `sushicore_dir` or the `hub status` `sushicore` row. Wave 5 owns that.
- It does not change `releases.py`, `identity.py` or `gui.py`.
- It does not add a test for `hub install-cli` itself, which still has none
  (`docs/design/REMAINING_WORK.md` records it). Task 3 covers the shared brick, not the command.
