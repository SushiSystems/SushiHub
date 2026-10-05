# Documentation and layout

**Status:** Open — written on 2026-10-05; the per-repository wave is running.

Programme 4 of 5 in the estate refactor. Every repository gets the documentation tree and the
checkers that SushiSkills defines, so that one command audits any of them and a reader who
knows one repository's `docs/` knows them all. The evidence is the "Documentation" and "Layout
and hygiene" sections of each repository's `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md`, and
the output of `check_docs_layout.py` measured on 2026-10-05:

| Repository | Layout findings | Chief causes |
| --- | --- | --- |
| sushiweb | 92 | Document names, 18 unreachable documents, `docs/modules/`, `docs/CLAUDE.md` |
| sushistack | 59 | Document names, 13 unreachable documents, `docs/agent/specs|plans|reports` |
| sushiruntime | 49 | Flat `docs/`, no root README, two changelogs, `docs/slop`, `docs/superpowers` |
| sushicore | 48 | No skeleton, document names, live intent filed as agent specs |
| sushiblas | 26 | Flat `docs/`, no root README |
| sushiengine | 23 | `docs/modules/`, `docs/superpowers`, `docs/api`, five design documents over 1 500 lines |
| sushitrack | 13 | Missing required documents, `docs/README.md` holds the whole manual |
| sushidsp | 11 | Unreachable documents |
| sushiai | 3 | Two document names, one work folder |

## The rules it applies

The `documentation`, `repository-layout` and `project-tools` skills of SushiSkills, as programme
1 left them. Nothing here restates them. Decisions the owner took that bear on this work:
agent work lives in `docs/agent/<YYYY_MM_DD>_<WORK_NAME>/`; there is no `docs/modules/`; a
module's facts live in its own `README.md`; work goes ahead in a repository with uncommitted
changes, whose paths are left alone.

## What each repository gets

1. **The tools.** `tools/common`, `tools/documentation`, `tools/layering`, `tools/licensing`,
   `tools/tests` and `tools/README.md` copied from SushiSkills as they are. Where the repository
   already had a checker of the same name, its `K_` settings (tier order, skipped folders) are
   carried into the new copy. A closed repository sets `K_LICENSE_LINES` to the reserved-rights
   line. Checkers and tools the repository has beyond these stay.
2. **The tree.** Every entry under `docs/` is one the skill names. Loose manual pages move into
   `getting_started/`, `architecture/`, `guides/` or `reference/`. `docs/modules/<name>` content
   moves to that module's own `README.md`. `docs/CLAUDE.md` becomes the root `CLAUDE.md`.
3. **Agent documents.** A finished spec, plan or report under `docs/agent/specs`, `plans`,
   `reports` or `docs/superpowers` moves to `docs/archive/` keeping its path below `docs/`.
   One that still states live intent becomes `docs/design/<TOPIC>.md` with a status line. Code
   and documents that cite a moved file are updated to the new path.
4. **Required documents** exist and are true: `docs/README.md` as an index that reaches every
   live document, `CONTRIBUTING.md`, `DOCUMENTATION_STYLE_GUIDE.md`, `reference/CHANGELOG.md`,
   `GLOSSARY.md`, `KNOWN_ISSUES.md`, `design/README.md`, `design/REMAINING_WORK.md`. A
   repository without a root `README.md` gets one. Backlogs outside `REMAINING_WORK.md` merge
   into it.
5. **One changelog**, in the skill's shape: `## Unreleased`, then one section per release,
   one-line entries. Older release sections move to `docs/archive/changelog/`. Entries are
   reshaped, not rewritten: an entry that does not fit in one line is split or shortened, and
   its meaning is kept.
6. **Stale pages** the audit's Documentation section names are corrected against the code, or
   listed if the fix needs a decision.

## What it does not do

- **Delete anything.** Tracked generated output, loose images, benchmark data, build probes and
  duplicate files are listed for the owner with their sizes; none is removed.
- **Edit code**, except a comment or docstring that cites a moved document.
- **CI.** Workflow files change after programme 5, when the source comment checker can pass;
  today it would fail in every C++ repository.
- **Versions, tags and releases.**
- **sushiengine's changelog**, which holds the owner's uncommitted entries and is 1 400 lines
  in another format. Its conversion is listed as remaining work.
- **sushifx**, which is an upstream fork and keeps AMD's layout.

## How it runs

One worker per repository; the repositories are the disjoint file sets. Each is reviewed by a
second agent and corrected by a third. The orchestrator then runs the header writer over the
copied tools, runs the checkers and the tool tests itself, and commits each repository locally,
by path where the owner has uncommitted work.

## Acceptance, per repository

1. `python tools/documentation/check_docs_layout.py .` prints nothing.
2. `python tools/documentation/check_changelog.py .` prints nothing (sushiengine excepted).
3. `python -m unittest discover -s tools/tests` passes.
4. `python tools/documentation/check_source_comments.py . --rule rule_license_block` prints nothing.
5. Every path cited in a moved or new document resolves, and no code cites a path that moved.
6. `git status` shows no deletion that is not one half of a move.
