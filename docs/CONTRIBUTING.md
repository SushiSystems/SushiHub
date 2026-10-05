# Contributing

## Language

Every artifact in this repository is written in English: code, comments, commit messages,
documentation.

## How work lands here

Work that touches more than one file opens one folder, `docs/agent/<YYYY_MM_DD>_<WORK_NAME>/`,
holding at most `SPEC.md`, `PLAN.md` and `REPORT.md`. A plan states its goal, the files each task
touches and the check that closes it. A plan may not contradict the design it implements;
changing the design is a decision made in the design document under `docs/design/`.

Live intent is in `docs/design/`, one document per topic, mapped in `docs/design/README.md`.
`docs/design/REMAINING_WORK.md` is the only backlog. Finished work folders move to
`docs/archive/`, which is added to and never edited. The `documentation` skill of SushiSkills
holds the full rules.

## Two components

`cli/` is the `hub` command, `gui/` the desktop application over it, and `contract/` the schemas
both validate against.

Cloning this repository is what a contributor does. A user installs `hub` from PyPI
(`pipx install sushihub`) and `hub init` marks whatever directory they chose. To work on `hub`,
clone this repository and run `python cli/install.py`, which points the same `hub` command at
your checkout. The desktop application has no other source, so anyone who wants it clones too.

The engine under both, `sushicore`, left this repository on 2026-09-22 and is installed from
PyPI like any other dependency. Its source, its tests and its own CI are at
`github.com/SushiSystems/SushiCore`. A change there reaches seven programs at once, so nothing in
it may name a module or a cache variable; anything module-specific is a parameter. The reasoning
is in `docs/archive/agent/specs/2026-08-25-cmake-driver-design.md`.

## Documentation lands with the code

A manual page that stops being true is a defect in the change that made it false. The
documentation update is part of the same commit as the code: the component's `README.md`, the
manual page, a design document's status line, the changelog entry. Before a change is finished,
check whether any page under `docs/` or any `README.md` now says something false about it.

A changelog entry in `docs/reference/CHANGELOG.md` is one line under `## Unreleased`:

```
- 2026-10-04 — setup: Reduced a bare `hub install` from three SYCL toolchains to one (`cli/sushihub/setup/factory.py`).
```

The scope is the commit scope. The entry never says why.

## Licence

The source is under the PolyForm Noncommercial License 1.0.0; `LICENSE` at the repository root is
the binding text. Contributions from outside Sushi Systems are not accepted yet.

## Source comments

Every source file opens with the license block of the `source-comments` skill, which
`tools/licensing/write_license_block.py` writes. A comment says what a thing does and nothing
else. Python carries a module docstring and Google-style function docstrings whose first line
starts with its verb; C++ carries Doxygen blocks. History, reasons and TODO do not go in source;
a reason is a design document the comment cites by path.

## Before claiming something works

```
python -m pytest cli/tests -q
python -m unittest discover -s tools/tests
python tools/documentation/check_docs_layout.py .
python tools/documentation/check_changelog.py .
python tools/documentation/check_source_comments.py .
```

`sushicore`'s own suite runs in its repository. Never invoke `cmake`, `ninja` or `ctest`
directly, and never run a real build to prove a CLI change; `tools/record_cli_argv.py` records
what a CLI would send to cmake without compiling. A claim that a check passed carries the
command and its output. Say what was verified and what was not.
