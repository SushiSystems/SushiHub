# Documentation and layout report

**Status:** Nine repositories done and committed locally on 2026-10-05. Nothing is pushed.

## What was done

| Repository | Commit | Layout findings before | After | Tool tests |
| --- | --- | --- | --- | --- |
| sushistack | `bd9cbf8` | 59 | 0 | 50 pass |
| sushicore | `ba8c4b5` | 48 | 3 | 50 pass |
| sushiruntime | `ff0250e` | 49 | 4 | 50 pass |
| sushiai | `601cb16` | 3 | 0 | 50 pass |
| sushiblas | `4297610` | 26 | 3 | 50 pass |
| sushidsp | `c320ec8` | 11 | 0 | 50 pass |
| sushitrack | `f8b8c07` | 13 | 0 | 50 pass |
| sushiweb | `91d7b6c6` | 92 | 0 | 50 pass |
| sushiengine | `64f26063` | 23 | 86 | 50 pass |

The counts are lines printed by `python tools/documentation/check_docs_layout.py .`, run by the
orchestrator after the last edit. `check_changelog.py` prints nothing in the eight
repositories whose changelog was converted. One worker restructured each repository, a second
agent reviewed it and a third corrected what the review graded Critical or Important; no
review found a Critical defect.

What remains in the four repositories that are not at zero:

- **sushicore, 3:** the owner's untracked plan under `docs/agent/plans/`, which was not moved.
- **sushiruntime 4, sushiblas 3:** `docs/api/mainpage.md`, the Doxygen main page, and
  `docs/api-site/`, its generated output. Moving them means changing the Doxyfile's main page
  and output directory and removing generated output; listed below.
- **sushiengine, 86:** 78 are links inside `docs/design/REMAINING_WORK.md` and four inside the
  changelog, both of which hold the owner's uncommitted work and were not edited; the rest are
  `docs/api`, `docs/api-site` and the audit folder. The count rose because the checker now
  follows links that the earlier one did not read.

## What the orchestrator did after the wave

- `docs/CLAUDE.md` became `AGENTS.md` at the root in sushistack, sushicore and sushiruntime,
  with a `CLAUDE.md` that imports it. Three workers had declined to move an instruction file.
  The content moved unchanged; sushicore's still tells the reader to build with `se`.
- `sushiruntime/Doxyfile` named three manual pages by their old paths; its `INPUT` was corrected.
- Quoted links in two audit reports tripped the link rule and were put in code spans.
- The header writer skipped files that were staged and not yet committed, so the copied tools
  kept the SushiSkills project line. Fixed in SushiSkills (`d3214c7`) with a test; each
  repository's tools now carry its own line.
- In sushiengine the index was cleared once: an over-broad `git add tools` had staged four of
  the owner's files. Nothing of the owner's was committed. The commit holds 739 paths chosen
  by rule: not on the owner's list, and for source files, changed in comments only.

## Proof

- The layout and changelog checkers, the licence rule and the tool tests were run in every
  repository by the orchestrator; the table holds the results.
- The CLI suites were rerun after the docstring edits: sushistack 316, sushicore 880 with the
  tool tests, sushiruntime 132, sushidsp 87, sushitrack 113 pass; sushiengine 936 pass and the
  same 12 fail as before.
- A script read the diff of every code file the wave touched in six repositories. Outside
  comments and cited document paths it found two lines, both inside one rewrapped docstring.
- No build ran. sushiengine's C++ and GLSL files changed in comments only and were not compiled.

## For the owner

Delete candidates. Nothing was deleted; sizes are the workers' measurements.

| Repository | Path | Size | What it is |
| --- | --- | --- | --- |
| sushiengine | `move_trace.json` | 6.9 GB | Untracked trace in the root |
| sushiengine | `.scratch/`, `.superpowers/` | 375 MB, 32 MB | Agent leftovers |
| sushiengine | 64 loose images in the root | 87 MB | Untracked |
| sushitrack | `tests/regression/evaluator/data/` | 234 MB | Tracked benchmark annotations, 22 blobs stored twice |
| sushidsp | `.superpowers/` | 16 MB | Agent leftovers |
| sushidsp | `docs/reference/spice/*/*_tran.csv` | 3.1 MB | Tracked simulator output inside the manual; a move, not a deletion |
| sushistack | `gui/build/ss/`, `gui/build/windows-x64/` | 87 MB, 84 MB | Build trees from before the rename to hub |
| sushiruntime | `venv/` | 29 MB | Old virtual environment; its Python link also crashes the comment checker when run on `.` |
| sushiruntime | four `CXX-DetectStdlib-*.h` in the root | 0 bytes | Compiler probes |
| sushiruntime, sushiblas, sushiengine | `docs/api-site/` | 1 to 4 MB | Generated Doxygen output |
| sushicore, sushiai | `.superpowers/` | about 2 MB each | Agent leftovers |
| sushiweb | `apps/account/e2e/_flows-account.png` | 235 KB | Tracked end-to-end screenshot |
| sushiblas | `include/SushiBLAS/core/export.hpp`, `kernels/math.hpp` | under 1 KB | Tracked headers nothing uses |

Decisions:

1. `docs/api/mainpage.md` and `docs/api-site/` in three repositories: move the main page into
   `docs/reference/` and point `OUTPUT_DIRECTORY` at `build/docs/api-site`, as sushiai and
   sushidsp already do.
2. sushiengine's changelog: 1 400 lines in Keep a Changelog form. Converting it waits until
   the owner's entries in it are committed.
3. sushiengine: five plans that still state open work were moved to the archive by the worker
   and noticed by the reviewer; they belong in `docs/design/`.
4. sushiweb: five error strings in code and 26 applied migrations cite guides by their old
   names. The strings are code; an applied migration is not edited.
5. sushitrack: two CLI strings cite sections of the old one-file manual.
6. sushidsp: two source comments and an issue template cite `modules/<name>` paths from before
   the regrouping.
7. Each repository's `REMAINING_WORK.md` and `KNOWN_ISSUES.md` now hold what the audit found and
   this work left; the agents listed between eight and eleven owner decisions per repository there.

## What was not done

- CI workflow files, as the spec says. sushistack's `ci.yml` runs `pytest tools/tests` on
  Python 3.10 too, and the copied tool tests target 3.11.
- The other rules of the source comment checker. `check_source_comments.py` without
  `--rule` reports findings in every C++ repository; that is programme 5.
- The audit folders under `docs/agent/2026_10_05_ESTATE_AUDIT/` stay untracked outside
  SushiSkills.
- Citations of moved documents from one repository into another were not searched for.
