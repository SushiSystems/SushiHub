# Cleanup report: the service layer's decomposition

Tasks 1 through 6 of `docs/agent/plans/2026-09-22-cleanup-service-decomposition.md` landed, each
in its own commit, in order. Task 0 (sushicore's writer, in `D:/Projects/sushicore`) and task 7
(closing the plan) were skipped as instructed. `python -m pytest sushihub/cli/tests -q` was green
after every task: 337, 337, 338, 338, 341, 341 — task 5 and 6 diverge from the plan's predicted
339/339; the reason is in task 5's section below.

## Task 1: links.py owns the registry

Commit `f23d4b9 refactor(cli): give the link registry one owner`.

Files: `sushihub/cli/sushistack/services/links.py` (new), `sushihub/cli/sushistack/config.py`,
`sushihub/cli/sushistack/services/modules.py`, `sushihub/cli/sushistack/services/status_report.py`,
`sushihub/cli/sushistack/setup/dependency_source.py`, `sushihub/cli/sushistack/setup/steps.py`,
`sushihub/cli/tests/test_add_binary.py`, `sushihub/cli/tests/test_add_provisions.py`,
`sushihub/cli/tests/test_link.py`.

`links.registered()` and `links.write()` moved both halves in unchanged (including the
`except SystemExit: return {}` guard). Every caller the grep found — `status_report.py`,
`setup/steps.py`, `setup/dependency_source.py`, `modules.py` — was repointed.

**Departure — file list.** The plan's task-1 file list named only `config.py` and `modules.py`
under `services/`; the grep it prescribes (`registered_modules\|_write_link`) also found
`setup/dependency_source.py` and `setup/steps.py` as callers. Both are edited and staged in this
commit, since leaving them importing a deleted name would break the tree.

**The hazard, for this task.** `test_link.py`'s `cfg_dir` fixture patched `modules.config_dir`;
the write now lives in `links`, so it patches `links.config_dir`, with the same `SUSHISTACK_HOME`
pin. Proof it still isolates:
```
$ python -m pytest sushihub/cli/tests/test_link.py -q
.........
9 passed in 0.12s
```
`modules.local.toml` before and after that run:
```
before: ['sushiai', 'sushiblas', 'sushidsp', 'sushiengine', 'sushiruntime']
after:  ['sushiai', 'sushiblas', 'sushidsp', 'sushiengine', 'sushiruntime']
```
Unchanged, as required.

## Task 2: git_ops.py owns git

Commit `0384ff3 refactor(cli): give git its own brick`.

Files: `sushihub/cli/sushistack/services/git_ops.py` (new), `sushihub/cli/sushistack/services/modules.py`,
`sushihub/cli/tests/test_add_binary.py`, `sushihub/cli/tests/test_add_provisions.py`,
`sushihub/cli/tests/test_presence.py`.

`_run_git`/`_source_reachable`/`REACHABLE_TIMEOUT` moved as `run`/`source_reachable`/
`REACHABLE_TIMEOUT`. `_self_update` stayed in `modules.py`, calling `git_ops.run`, as the plan
directs.

**The hazard, proved rather than assumed.** `test_add_binary.py`'s `workspace` fixture's
`pytest.fail` guards were retargeted at `git_ops.run`/`git_ops.source_reachable`. Before
restoring the guards, I swapped them for call-recorders and ran the file:
```
$ python -c "
import pytest, sys
sys.path.insert(0, 'sushihub/cli')
rc = pytest.main(['sushihub/cli/tests/test_add_binary.py', '-q'])
import tests.test_add_binary as t
print('HAZARD_CALLS:', t._HAZARD_CALLS)
print('rc:', rc)
"
..................
18 passed in 0.57s
HAZARD_CALLS: []
rc: 0
```
`HAZARD_CALLS == []` — none of the 18 tests reached `git_ops` for real. The recorder code was a
throwaway (not committed); the guard was restored to `pytest.fail` before the task-2 commit.

## Task 3: pipx.py, one implementation instead of two

Commit `d08be21 fix(cli): install a module's CLI the same way from both commands`.

Files: `sushihub/cli/sushistack/services/pipx.py` (new), `sushihub/cli/sushistack/services/modules.py`,
`sushihub/cli/sushistack/services/cli_install.py`, `sushihub/cli/tests/test_cli_install.py`.

**Step 1 verification, as required before touching code.** Read `cli_install.py:70`'s docstring
(now the comment above `_install_module_cli` in `modules.py`) and both call sites: `hub add`
clones a module and then installs its CLI non-editable (`modules._install_module_cli`, the old
`pipx install --force <dir>`); `hub install-cli` installs the same kind of checkout editable. A
module `hub add` clones is exactly the kind of checkout `hub update`/`hub pull` later fast-forwards,
so a frozen install goes stale the moment that happens — the docstring's argument holds for `hub
add`'s own path, not just `install-cli`'s. No reason for a deliberately frozen install turned up.
Editable wins; `hub add`'s path is the one that changed, as the plan predicted.

`pipx.command()`, `pipx.distribution_name()` and `pipx.install(pkg_dir, editable=True)` are the
new brick; both `modules._install_module_cli` and `cli_install.install_cli` route through it.
`cli_install._ensure_pipx` now checks `pipx.command()` (rather than probing
`sys.executable -m pipx` on its own), bootstraps via pip when it is None, and raises if `pipx`
still cannot be found afterwards — the brick reports (`None`), the caller decides (raise).

**Departure — the argv assertion, as the plan anticipated.** `test_the_happy_path_installs_the_module_cli_alone`
became `..._editable`; its asserted argv gained `--editable`. Added
`test_both_paths_install_a_module_cli_the_same_way`, proving `modules._install_module_cli` and
`pipx.install(..., editable=True)` now issue the identical command.

**Machine verification (task 3 step 4):**
```
$ hub install-cli sushiruntime
...
installed package sushiruntime-cli 1.0.0, installed using Python 3.13.13
  These apps are now available
    - sr.exe
    - sushiruntime.exe
[SUCCESS] Module CLI(s) installed. ...

$ python -c "
import pathlib
v = pathlib.Path.home() / 'pipx/venvs/sushiruntime-cli/Lib/site-packages'
print([p.name for p in v.glob('__editable__*')])
"
['__editable__.sushiruntime_cli-1.0.0.pth', '__editable___sushiruntime_cli_1_0_0_finder.py']
```
Editable marker present, as expected.

## Task 4: binary.py owns the licensed install policy

Commit `4343243 refactor(cli): give the licensed install its own brick`.

Files: `sushihub/cli/sushistack/services/binary.py` (new), `sushihub/cli/sushistack/services/modules.py`,
`sushihub/cli/tests/test_add_binary.py`, `sushihub/cli/tests/test_presence.py`.

`_install_binary`/`_add_binary`/`_update_binary` moved as `install`/`add`/`update`. `modules.py`
imports the module as `binary_svc` (not `binary`) because `add()`'s own `--binary` parameter is
named `binary`; importing the plain name would have shadowed it inside that function and turned
`binary.add(...)` into an `AttributeError` on a bool. Caught this before running tests by reading
the diff, not by a failure.

**Two knock-on repoints the plan's file list didn't name but the hazard covers.** `binary.py`
holds its own `from .. import console` (a fresh module-level reference, not `modules.console`),
so `test_add_binary.py`'s `recorder` fixture — which only patched `modules.console` — stopped
seeing binary-install messages. Patched `binary.console` too, in the same fixture. And
`test_presence.py`'s `test_update_refreshes_a_binary_module_through_sushi_id` patched
`modules._update_binary`, which moved; repointed to `binary.update`, and `modules.releases` in
`test_add_binary.py` (two `host_platform` patches) to `binary.releases`, since `releases` is no
longer imported into `modules.py` at all.

**Verification:**
```
$ python -m pytest sushihub/cli/tests/test_add_binary.py -q
..................
18 passed in 0.48s
$ python -m pytest sushihub/cli/tests -q
338 passed in 6.51s
```

## Task 5: one answer to where a module lives

Commit `e360206 refactor(cli): resolve a module's directory in one place, through the catalog`.

Files: `sushihub/cli/sushistack/services/presence.py`, `sushihub/cli/sushistack/services/status_report.py`,
`sushihub/cli/sushistack/services/modules.py`, `sushihub/cli/sushistack/services/cli_install.py`,
`sushihub/cli/sushistack/setup/steps.py`, `sushihub/cli/tests/test_presence.py`.

**Step 1 decision, as required.** The catalog-backed answer (`root / CATALOG[name].directory`)
is the one resolver, now `presence.module_dir(root, name, linked=None)`. A link wins first; a
name the catalog does not know (this machine's stale `sushidsp` link — dropped from the catalog
in `31ddaf0`) falls back to `root / name` rather than raising `KeyError`.

Also fixed `presence.describe`'s binary-manifest read, which still did `read_release(root /
name)` directly rather than going through the resolver — the same class of bug the plan
describes (bypasses the catalog's `directory` field), inside the one function the plan asked me
to make the single source of truth.

**Departure — three tests instead of one.** The plan's step 1 asks for a test of "exactly that
case" (the stale/unknown name). I wrote that one plus two more covering the other two paths the
resolver now unifies — the catalog-directory case and the link-priority case — since all three
were duplicated behaviours this task collapses and each deserves its own assertion. This is why
the suite reads 341 after task 5 and 341 after task 6, not the plan's predicted 339/339; every
extra test is additive coverage of the same brick, not a change in scope.

**Callers repointed beyond the plan's task-5 file list.** `cli_install.py` and `setup/steps.py`
both called the deleted `modules.module_dest`; both are now on `presence.module_dir` with a
`links.registered()` map fetched once per call, matching how `modules.py` itself calls it.

**Verification:**
```
$ python -m pytest sushihub/cli/tests -q
341 passed in 6.69s
$ hub status
...
│ sushiruntime │ D:\Projects\sushiruntime │ linked  │ main    │
│ sushiengine  │ D:\Projects\sushiengine  │ linked  │ main +1 │
│ sushiai      │ D:\Projects\sushiai      │ linked  │ main    │
│ sushiblas    │ D:\Projects\sushiblas    │ linked  │ main    │
│ sushicore    │ —                        │ missing │ —       │
```
Four linked modules at their usual locations; the stale `sushidsp` link stays absent from the
table, not raised as an error.

## Task 6: status renders where it is built

Commit `9161280 refactor(cli): render the status table where its payload is built`.

Files: `sushihub/cli/sushistack/services/status_report.py`, `sushihub/cli/sushistack/services/modules.py`,
`sushihub/cli/sushistack/cli.py`. No test named `modules.status` or `_branch_cell` (checked by
grep first); none were touched.

`_branch_cell` and `status` moved into `status_report.py` as `_branch_cell` and `render`.
`cli.py`'s `status` command now calls `status_report.render(report.payload)` directly, in place
of `modules_svc.status(report.payload)`.

**Verification:**
```
$ python -m pytest sushihub/cli/tests -q
341 passed in 6.69s
$ hub status
[same table as task 5's, unchanged]
$ hub --json status
{"event":"header","title":"SushiStack Status"}
{"event":"line","level":"info","message":"Workspace: D:\\Projects\\sushistack"}
{"event":"table","title":"SushiStack Status","columns":["Module","Location","State","Branch"],"rows":[...]}
{"event":"line","level":"info","message":"Dependencies: D:\\Projects\\sushistack\\dependencies (present). Verify with `hub doctor`."}
{"event":"result","ok":true,"payload":{...}}
```
Table and payload shape identical to before the task.

## Final measurement

```
$ wc -l sushihub/cli/sushistack/services/*.py | sort -rn
  2785 total
   356 modules.py
   352 identity.py
   245 releases.py
   240 gui.py
   161 status_report.py
   146 presence.py
   144 customize.py
   120 session.py
   117 cli_install.py
   114 setup.py
   101 token_store.py
   100 binary.py
    91 discovery.py
    90 catalog.py
    83 git_state.py
    71 licence_file.py
    61 hub_install.py
    60 pipx.py
    49 links.py
    45 git_ops.py
    38 update_check.py
     1 __init__.py
```

`modules.py` is 356 lines, holding `init`, `add`, `link`, `update`, `sync`, `_resolve_names`,
`_provision`, `_install_module_cli`, `_self_update`, `sushicore_dir` and the gitignore-lines
constant — above the plan's "roughly 250" target for task 7 to record. `sushicore_dir` was left
in place, as task 0/6's constraint says (`sushicore_dir` and the `sushicore` status row are wave
5's). `_install_module_cli` is orchestration over the new `pipx` brick, not a second
implementation of anything, so it stayed. The gap looks like the five command bodies' own
docstrings and comments (kept in full, per `source-comments`), not a leftover duplication.

```
$ git log --oneline -6
9161280 refactor(cli): render the status table where its payload is built
e360206 refactor(cli): resolve a module's directory in one place, through the catalog
4343243 refactor(cli): give the licensed install its own brick
d08be21 fix(cli): install a module's CLI the same way from both commands
0384ff3 refactor(cli): give git its own brick
f23d4b9 refactor(cli): give the link registry one owner

$ git status --porcelain
[empty]
```

## What was not done

- Task 0 (sushicore's `write_toml_document` split) — explicitly out of scope; another agent owns
  `D:/Projects/sushicore`, and it was never touched.
- Task 7 (closing the plan: the final `wc -l` measurement recorded above, plus the changelog and
  `REMAINING_WORK.md` entries, plus that commit) — explicitly left for the owner to close.
- `sushicore_dir` and the `hub status` `sushicore` row — left alone, as the plan's global
  constraints require; still wave 5's.
