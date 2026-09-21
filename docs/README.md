# Manual

Documentation index for the SushiStack repository. Every document under `docs/` is reachable
from here. Facts about one component live in that component's own README, beside its code.

## How to contribute

- `CONTRIBUTING.md` — what must be documented, and how a change lands.
- `DOCUMENTATION_STYLE_GUIDE.md` — where a document goes, and the shape of a changelog entry.

## Getting started

- `getting_started/INSTALL.md` — from a fresh machine to a built module: the one-line installer,
  the manual steps, and what each of them does.

## Architecture

- `architecture/WORKSPACE.md` — the workspace layout, why it is flat, and how a module finds its
  siblings and the shared dependency tree.

## Modules

Each component's own facts live beside its code:

- `../sushihub/cli/README.md` — the `hub` command: every subcommand, the files it reads and writes.
- `sushicore` — the shared CLI engine: presentation layer, config plumbing, the cmake driver, and
  how a Sushi CLI consumes it. It lives at `github.com/SushiSystems/SushiCore` and installs from
  PyPI; its manual is `docs/README.md` there.
- `../sushihub/contract/README.md` — the JSON contract between `hub` and the desktop application:
  event shapes and the command catalogue.
- `../sushihub/gui/README.md` — the desktop application over `hub --json`: the four layers, the
  five hand-drawn screens, and the form generated for every other command.
- `../sushihub/contract/sushi-account.md` — the four Sushi Account endpoints `hub` signs in and reads licences
  through, and the device grant that walks between them.

## Guides

- `guides/LINKING_CHECKOUTS.md` — pointing the workspace at module checkouts that live elsewhere,
  and at your own `sushicore`.

## Reference

- `reference/CHANGELOG.md` — one line per meaningful change, newest first.
- `reference/GLOSSARY.md` — the words this repository uses in a specific sense.
- `reference/KNOWN_ISSUES.md` — failures that turn out to be a toolchain, a package manager or a
  vendor, with the symptom, the cause and the rule for each.

## Design

- `design/REMAINING_WORK.md` — the single backlog: what is planned and not yet built, in the order
  it is meant to land.
- `design/WORKSPACE_DECOUPLING.md` — `hub` as a tool and a workspace as data: the module catalog
  out of code, the workspace's own directory, `sushicore` and `sushihub` on PyPI, and `sushidsp`
  and `sushitrack` out of the stack.
- `design/GPU_BACKEND_PROVISIONING.md` — one brick per GPU vendor and one branch per operating
  system, with the adapter build wired into `hub install`.

## Agent output

Everything an agent wrote while working, kept as a record rather than as part of the manual:

- `agent/specs/2026-09-05-hub-design.md` — the hub: `hub` as the workspace's one experience in
  the terminal and on the desktop, the binary distribution of sushiengine, and the licence flow
  through Sushi Account.
- `agent/specs/2026-08-25-cmake-driver-design.md` — the shared cmake driver: what five
  `services/project.py` copies had in common, what they did not, and what moved into `sushicore`.
- `agent/plans/2026-08-25-cmake-driver.md` — the plan that landed that design, task by task.
- `agent/plans/2026-09-21-wave-0-uncovered-seams.md` — wave 0 of the decoupling: tests for the
  five seams the later waves rewrite.
- `agent/plans/2026-09-22-wave-3-workspace-directory.md` — wave 3 of the decoupling: the marker
  becomes a directory holding `workspace.toml`, and the tool's defaults move into the package.
- `agent/plans/2026-09-22-wave-2-module-catalog.md` — wave 2 of the decoupling: the catalog out
  of code into packaged data, and `sushidsp` and `sushitrack` out of the stack.
- `agent/plans/2026-09-22-wave-1-sushicore-repository.md` — wave 1 of the decoupling: `sushicore`
  out to its own repository and onto PyPI, and the six consumers onto the published package.
- `agent/reports/` — reports written while executing a plan. The five from wave 0 of the
  decoupling are dated 2026-09-22.

## Archive

- `archive/` — frozen documents, added to and never edited. Empty so far.
