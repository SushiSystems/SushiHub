# Plan: two equal ways into every module

**Status:** Open — plan written 2026-10-28, nothing started

Carries out [SPEC.md](SPEC.md). Findings and solutions are in the spec under each module's
heading; this file holds the order, the files per task and how each task is accepted.

## Execution

Inline, in one session, tasks in the order below (the owner's choice, 2026-10-28). A task is one
module and one commit in that module's repository, with its pages in the same commit, staged by
path. The shared checkout rules of `git-workflow` hold: no `git add -A`, and each repository's
index is read before a commit. Prose goes through `humanizer`.

A task has one acceptance criterion and one verification. The criterion is the same for every
module task: the three checks of `module-install`, "Checking a module", each read `done` after
the task, and the pages carry both headings.

## Hierarchy

1. The standard, `module-install` in SushiSkills. **Done 2026-10-28** (skill, index rows,
   changelog, `check_all` clean). The checker is task C1.
2. The gate, G0: `sushicore` is installable from a clean machine at the pinned version.
3. The modules, lowest tier first, because a bare-clone lane fetches its siblings.
4. The bare-clone lanes, after G0, because a lane needs the package.

## Gate

| Id | What | Who | Done when |
| --- | --- | --- | --- |
| G0 | Publish `sushicore` 0.9.7, or pin every module to a published version | Owner (Open question 1) | `pip index versions sushicore` lists the pinned version |

Pages and static fixes proceed without G0. Nothing that runs a clean install does.

## Tasks

| Id | Repository | Needs | Files (spec heading) | Verification |
| --- | --- | --- | --- | --- |
| C1 | sushiskills | skill | `tools/documentation/check_module_install.py`, its test, `tools/README.md`, `skills/project-tools/SKILL.md` | `python tools/check_all.py .` |
| S0 | sushistack | none | `cli/sushihub/catalog.toml` and the tests and pages of the sushidsp entry, already edited and uncommitted | `pytest` in `cli/`: 377 passed on 2026-10-28 |
| M1 | sushilog | C1 | sushilog | its `tools/check_all.py` and `pytest` |
| M2 | sushiprofiler | C1 | sushiprofiler | the same |
| M3 | sushiruntime | M1, M2 | sushiruntime, including `cmake/SushiRuntimeVcpkg.cmake` | the same, then a configure through `sr build` run by the owner |
| M4 | sushiblas | M3 | sushiblas | the same, then `sb build` by the owner |
| M5 | sushiai | M3, M4 | sushiai, including the dataset paths and `cmake/Vcpkg.cmake` | the same, then `sa build` by the owner |
| M6 | sushiengine | M3, M4 | sushiengine, including `doctor.py`, `validation.py`, `test_doctor.py`, two CMake files | the same, then `se build` by the owner |
| M7 | sushitrack | M1, M2 | sushitrack, including a new `sushi-module.toml`, the conda file, the Dockerfile, the fragment | the same, then `st build` by the owner |
| M8 | sushidsp | M1, M2 | sushidsp, including `CMakePresets.json`, the manifest comment, RW-2 | the same, then `sd build` by the owner |
| L1 to L8 | each module | G0, its M task | the module's `ci.yml`: one job `bare-clone` | the job is green on both operating systems |
| X1 | sushistack | M1 to M8 | `docs/guides/FAQ.md`, `docs/getting_started/INSTALL.md`, `docs/reference/CHANGELOG.md` | `check_docs_truth.py`, `pytest` |

M3 to M6 edit a CMake file. Each such edit first shows, from the CLI's own code, that the CLI
hands `VCPKG_ROOT` and `<NAME>_DIR` already; a fallback it makes unreachable is deleted
(decision 2). If the CLI does not hand one, the task adds it to the CLI first and reports it.

## Order inside a module task

1. Run the three checks and write the verdicts on the module's side.
2. Fix code and CMake: machine paths, hint strings, the manifest, the broken pins.
3. Rewrite the install pages under the two headings, and correct each stale version by naming
   its file.
4. Search the module for the old text: `git grep -n <old> -- '*.md'`.
5. Add the changelog line and the test the fix needs. A hint string change carries a test that
   no service prints `hub install`.
6. Run the verification, paste its output, commit by path.

## Acceptance of the programme

- Every module reads `done` on the three checks, and `C1` reports no finding in any of them.
- Every module has a `bare-clone` job that passed once on each operating system it supports.
- `module-install` and this spec agree; a rule found wrong here is fixed in the skill first.

## Not in this plan

- The `sushicore` release (G0) and anything that pushes to a remote.
- SushiHub changes. None of the findings needs one.

## Risks

- A module whose bare-clone lane fails for a reason outside the audit (a missing port, a
  sibling that is not tagged) gets its own entry in `KNOWN_ISSUES.md` and does not hold the
  others.
- A CMake edit cannot be verified without the owner's build; the task stays open until the
  owner reports it.
