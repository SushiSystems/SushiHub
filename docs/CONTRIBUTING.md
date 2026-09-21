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

`sushihub/cli/` is the `hub` command, `sushihub/gui/` the desktop application over it.

The engine under both, `sushicore`, left this repository on 2026-09-22 and is installed from
PyPI like any other dependency. Its source, its tests and its own CI are at
`github.com/SushiSystems/SushiCore`. A change there still reaches seven programs at once, so
nothing in it may name a module or a cache variable; anything module-specific is a parameter.
The reasoning is in `docs/agent/specs/2026-08-25-cmake-driver-design.md`.

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

The `hub` command's suite runs with `python -m pytest sushihub/cli/tests -q` and the argv
recorder's with `python -m pytest tools/tests -q`. `sushicore`'s own suite runs in its
repository. Never invoke
`cmake`, `ninja` or `ctest` directly, and never run a real build to prove a CLI change; the argv
recorder in `tools/record_cli_argv.py` exists so the build code can be checked without compiling.
Say plainly what was verified and what was not.
