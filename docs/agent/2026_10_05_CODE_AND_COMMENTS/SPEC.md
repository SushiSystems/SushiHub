# Code and comments

**Status:** Shipped — comments and defects landed on 2026-10-05; three C++ fixes await the owner's build. See `REPORT.md`.

Programme 5 of 5 in the estate refactor. It closes the defects the estate audit found that
can be fixed without redrawing a module boundary, and brings source comments under the
`source-comments` skill. The evidence is the "Code shape" section of each repository's
`docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md` and the source comment checker, which printed
about 17 000 findings on 2026-10-05, 12 174 of them in sushiengine.

## Owner decisions, 2026-10-05

| # | Decision |
| --- | --- |
| D1 | Comment findings in the large repositories are closed module by module; reasoning moves to a document, it is not deleted. sushiengine goes last |
| D2 | C++ defects are fixed with a test written first and a syntax check; the owner builds and runs the tests |
| D3 | sushicore verifies what it downloads against a SHA-256 pinned in the dependency manifest |

## Comments

A finding is closed in one of these ways and no other.

| Finding | How it closes |
| --- | --- |
| No file block | The file gets `@file`, one `@brief` sentence read from the file, `@author`; Python gets a module docstring |
| Two or more `//` or `#` lines in a row | One line stating the invariant stays. Reasoning moves, in full sentences, to the README of the module or folder the file is in, and the line cites it |
| A block over eight lines | `@brief` and the tags that state a rule stay; the rest moves the same way |
| A separator line | Removed. A file it split into separate responsibilities is reported, not split |
| `TODO`, history | To `docs/design/REMAINING_WORK.md`, or dropped when git already says it |

Only comments, docstrings and the receiving documents change. The orchestrator proves it per
repository: for Python, the syntax tree of each changed file equals the committed one apart
from docstrings; for C-family and TypeScript files, the text with comments stripped equals
the committed text with comments stripped.

Each work unit is a folder with a few hundred findings, so two workers never hold one file.
A unit writes moved reasoning only to READMEs inside its own folder. The orchestrator writes
the changelog line.

## Defects

| Repository | Defect | Proof |
| --- | --- | --- |
| sushicore | Dropped failures in provisioning | Tests, run |
| sushicore | Downloads opened and run without an integrity check (D3) | Tests, run |
| sushiweb | Mail with verification and reset links written to the production log | Tests, run |
| sushiblas | `truncated_normal` ignores its bounds; `SB_ASSERT` loses its message; the async logger can hang on shutdown; `IO` reads unchecked | Tests written, not run |
| sushitrack | Exception text passed as a printf format; a log call per element in the cost-matrix loops; the C ABI reports failure as zero tracks | Tests written, not run |
| sushiai | An unlisted operation falls through to a default kernel in lowering | Tests written, not run |

A C++ fix is committed with "not built" in its message. The report names, per fix, the test
that proves it and what the test must show when the owner runs it.

## Not in this programme

- Restructuring: `API::Graph`, `RuntimeContext`, the editor entry function, `RuntimeSimulation`,
  the dtype switch written nine times, error models that mix exceptions and status values.
  Each needs a module boundary or a public interface decided by the owner.
- A logger for sushidsp and sushiweb, which is a new module in each.
- Versions, tags, releases.

## CI

When a repository's comment checker prints nothing, its workflow gains the four checkers and
the tool tests as a job. The workflow file is the orchestrator's edit.

## Acceptance

1. `python tools/documentation/check_source_comments.py .` prints nothing in each repository
   whose units are done.
2. The comment-only proof above holds for every changed source file outside a defect fix.
3. Each defect has a test that failed before its fix, seen failing for Python and TypeScript,
   reasoned for C++.
4. The Python and TypeScript suites pass.
