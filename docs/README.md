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

- `../cli/README.md` — the `ss` command: every subcommand, the files it reads and writes.
- `../sushicore/docs/README.md` — the shared CLI engine: presentation layer, config plumbing, the
  cmake driver, and how a Sushi CLI consumes it.
- `../sushihub/contract/README.md` — the JSON contract between `ss` and the desktop application:
  event shapes and the command catalogue.
- `../sushihub/contract/sushi-id.md` — the four Sushi ID endpoints `ss` signs in and reads licences
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

## Agent output

Everything an agent wrote while working, kept as a record rather than as part of the manual:

- `agent/specs/2026-09-05-hub-design.md` — the hub: `ss` as the workspace's one experience in
  the terminal and on the desktop, the binary distribution of sushiengine, and the licence flow
  through Sushi ID.
- `agent/specs/2026-08-25-cmake-driver-design.md` — the shared cmake driver: what five
  `services/project.py` copies had in common, what they did not, and what moved into `sushicore`.
- `agent/plans/2026-08-25-cmake-driver.md` — the plan that landed that design, task by task.
- `agent/reports/` — reports written while executing a plan. Empty so far.

## Archive

- `archive/` — frozen documents, added to and never edited. Empty so far.
