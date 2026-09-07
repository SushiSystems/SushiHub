# Wave 1d: the command is `hub` — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** The hub's command is `hub`, in every repository that mentions it. `ss` disappears as a
command name; the install scripts offer `sh` as a shell alias for the people who want to type two
letters.

**Architecture:** One rename, four seams. The console script and everything that spells the
executable move first; the install scripts and CI follow; the desktop application spells the
subprocess it launches; the manuals catch up. Sibling repositories mention the command only in
prose and in a config line each, so each is a task of its own with no ordering between them.

**Tech Stack:** Python 3.10+, PowerShell, POSIX sh, C++17, Markdown.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §2, §8.

## Global Constraints

- **Rename only the command.** `ss` changes where it names the CLI: a console script, an
  executable spelling (`ss`, `ss.exe`), an argv element, a PATH shim, prose such as "run
  `ss status`".
- **Leave everything else.** `sushistack` stays: the repository, the workspace root, the Python
  package `sushihub/cli/sushistack/`, the `.sushistack` marker, every `sushistack.deps.toml`.
  A C++ variable named `ss` (a `std::stringstream`) is not the command. `third_party/**` is not
  ours. `docs/archive/**` is frozen and is never edited.
- **History is not rewritten.** Landed plans under `docs/agent/plans/` and the lines already in
  `docs/reference/CHANGELOG.md` record what was true when they were written; leave them. Live
  documents change: the manual, every README, the hub design spec, `docs/design/`.
- **No compatibility alias for `ss`.** Linux ships `ss` with iproute2; shadowing it is the reason
  for the rename. The console scripts are `hub` and `sushihub`.
- No agent runs `se`, `cmake`, `ninja` or `ctest`, and none edits a build configuration file
  except where this plan names it.
- Sibling repositories have dirty worktrees. Stage by path, never `git add -A`.

## Files

| Task | Repository | Files |
|---|---|---|
| 1 | sushistack | `sushihub/cli/pyproject.toml`, `sushihub/cli/install.py`, `sushihub/cli/sushistack/**.py`, `sushihub/cli/tests/**.py`, `sushihub/cli/config.toml`, `sushihub/cli/manifests/*.deps.toml` |
| 2 | sushistack | `install.ps1`, `install.sh`, `.github/workflows/ci.yml`, `.gitignore` |
| 3 | sushistack | `sushihub/gui/src/**`, `sushihub/gui/tests/**`, `sushihub/gui/README.md` |
| 4 | sushistack | `sushicore/sushicore/**.py`, `sushicore/docs/README.md`, `sushicore/pyproject.toml` |
| 5 | sushistack | `README.md`, `docs/README.md`, `docs/CONTRIBUTING.md`, `docs/getting_started/`, `docs/architecture/`, `docs/guides/`, `docs/reference/GLOSSARY.md`, `docs/reference/KNOWN_ISSUES.md`, `docs/design/`, `docs/agent/specs/2026-09-05-hub-design.md`, `sushihub/cli/README.md`, `sushihub/contract/**` |
| 6 | sushiengine | `README.md`, `docs/**` outside `docs/archive/`, `cli/config.toml`, `.github/workflows/ci.yml`, `cmake/Runtime.cmake`, `tools/**` |
| 7 | sushiruntime, sushiblas | `README.md`, `docs/**` outside archives, `cli/**` config and prose |
| 8 | sushiai, sushidsp | the same shape |
| 9 | sushiweb | `docs/**` outside archives, and the worktree `D:\Projects\sushiweb-hub` on `feat/device-grant-and-releases` |

Tasks 1 to 5 share a repository but no file. Tasks 6 to 9 are independent repositories.

---

### Task 1: The console script and every spelling in the Python package

- [ ] `[project.scripts]` becomes `hub = "sushistack.cli:app"` and `sushihub = "sushistack.cli:app"`.
      The `ss` and `sushistack` entries go.
- [ ] `install.py` writes the shim under the new name and removes a shim it finds under the old one.
- [ ] Every string, docstring, help text and error message that spells the command changes:
      `services/gui.py` (the executable the desktop application is told to call),
      `services/modules.py`, `services/setup.py`, `services/customize.py`, `services/presence.py`,
      `services/projects.py`, `services/identity.py`, `services/session.py`,
      `services/licence_file.py`, `services/token_store.py`, `setup/**`, `cli.py`, `describe.py`,
      `gui_config.py`, `gui_env.py`, `console.py`.
- [ ] Tests follow the strings they assert.
- [ ] Verify: `python -m pytest sushihub/cli/tests -q`, `python -m compileall -q sushihub/cli/sushistack`.

Commit: `refactor(cli): name the hub's command hub`.

### Task 2: The install scripts, the alias, and CI

- [ ] Both scripts install the `hub` shim and delete an `ss` shim left by an earlier install.
- [ ] Each offers the alias once, and skips it whenever stdin is not a terminal or the caller
      passes `--no-alias` / `-NoAlias`: `alias sh='hub'` appended to `~/.bashrc` or `~/.zshrc`,
      `function sh { hub @args }` appended to `$PROFILE`. A marker comment `# sushi hub alias`
      guards the block, so a second run rewrites nothing.
- [ ] The scripts say, in one line, that the alias changes typing only and leaves `/bin/sh` alone.
- [ ] `.github/workflows/ci.yml` calls `hub`.
- [ ] `.gitignore` paths that mention the command follow.
- [ ] Verify: `bash -n install.sh`, and for PowerShell a parse check that runs nothing:
      `pwsh -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseFile('install.ps1',[ref]$null,[ref]$null) | Out-Null"`.

Commit: `refactor(install): install hub and offer sh as a typing alias`.

### Task 3: The desktop application

- [ ] Wherever the C++ decides which executable to launch, or shows the command to the reader, the
      name is `hub` / `hub.exe`.
- [ ] Recorded fixtures under `sushihub/gui/tests/fixtures/` that carry the command name are
      re-recorded by editing the fixture text, not by running anything.
- [ ] A `std::stringstream ss` stays as it is.
- [ ] Verify: `clang -fsyntax-only` through `compile_commands.json` for each file touched, or, when
      no compilation database exists, say so and paste `git diff --stat`.

Commit: `refactor(gui): launch hub`.

### Task 4: sushicore

- [ ] Module docstrings and comments that list the CLIs say `hub` where they said `ss`.
- [ ] `WORKSPACE_CLI_DIR` and every path stay untouched; they name directories, not the command.
- [ ] Verify: `python -m pytest sushicore/tests -q`.

Commit: `docs(sushicore): the hub's command is hub`.

### Task 5: The manual and the contract

- [ ] Every live document in the list above spells the command `hub`.
- [ ] `docs/reference/GLOSSARY.md` gains one entry: the command, what it is, and that `sh` is an
      optional alias the installer offers.
- [ ] `docs/reference/KNOWN_ISSUES.md` records why `ss` was abandoned: iproute2 ships `/usr/bin/ss`.
- [ ] Do not edit `docs/reference/CHANGELOG.md` or `docs/design/REMAINING_WORK.md`; report the lines.
- [ ] Verify: every link and path cited in the files touched resolves; paste the check.

Commit: `docs: rename the hub's command to hub`.

### Tasks 6 to 9: The sibling repositories

For each repository:

- [ ] Prose that tells the reader to run the hub says `hub`.
- [ ] `cli/sushistack.deps.toml` keeps its name; only a command spelling inside it changes.
- [ ] `docs/archive/**` and `third_party/**` are not touched.
- [ ] One line is added to that repository's `docs/reference/CHANGELOG.md`:
      ``- 2026-09-07 — Renamed the hub's command from `ss` to `hub` in the manual (`docs/`).``
- [ ] Verify: `git status --porcelain` before and after, and `git diff --stat`.

Commit in each: `docs: the hub's command is hub`.

## Report

Per task: the verification output, the files touched, and anything found that the rules above did
not decide.

The coordinator writes, in sushistack:
``- 2026-09-07 — Renamed the hub's command from `ss` to `hub` and offered `sh` as an installer alias (`sushihub/cli/pyproject.toml`, `install.sh`, `install.ps1`).``
