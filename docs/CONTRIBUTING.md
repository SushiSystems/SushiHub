# Contributing

## Language

Every artifact in this repository is written in English: code, comments, commit messages,
documentation.

## How work lands here

Work that touches more than one file starts as a design in `docs/agent/specs/` and a plan in
`docs/agent/plans/`, dated, each plan stating its goal, the files each task touches and the
check that closes it. A plan may not silently contradict the design it implements; changing the
design is a decision made in the design document, not a side effect of a plan.

Everything an agent writes while working lives under `docs/agent/`. It is a record of what
happened. The hand-maintained manual is the rest of `docs/`, indexed from `docs/README.md`.

## Two components, two owners

`sushihub/cli/` is the `hub` command, `sushihub/gui/` the desktop application over it. `sushicore/` is the engine under `hub` and the five module CLIs in the
other repositories. A change to `sushicore` is a change to six programs at once, and this
repository's CI runs each of the five consumers' own test suites against the `sushicore` under
test. Nothing in `sushicore` may name a module or a cache variable; anything module-specific is a
parameter. The reasoning is in `docs/agent/specs/2026-08-25-cmake-driver-design.md`.

## Documentation lands with the code

A manual page that stops being true is a defect in the change that made it false. The
documentation update is part of the same commit as the code: the component's `README.md`, the
manual page, a design document's status line, the changelog entry. Before a change is finished,
check whether any page under `docs/` or any `README.md` now says something false about it.

A changelog entry (`docs/reference/CHANGELOG.md`) is one line: the date, a past-tense verb, what
changed, and where, in backticks. It never says why; the reason lives in a design document the
entry may link. The exact shape is in `docs/DOCUMENTATION_STYLE_GUIDE.md`.

## Source comments

A comment says what a thing does, in docstring form, and nothing else. Every module opens with a
docstring stating its purpose; every function carries a Google-style docstring whose first line
starts with its verb. History, reasons and TODO do not go in source; a reason is a design document
the docstring cites by path.

## Verification before claiming something works

`sushicore`'s suite runs with `python -m pytest sushicore/tests -q` from the repository root. The
`hub` command's suite runs with `python -m pytest sushihub/cli/tests -q`; the two suites cannot share
one run, because both packages are named `tests`. Never invoke
`cmake`, `ninja` or `ctest` directly, and never run a real build to prove a CLI change; the argv
recorder in `tools/record_cli_argv.py` exists so the build code can be checked without compiling.
Say plainly what was verified and what was not.
