# SushiHub manual

Facts about one component live in that component's README, beside its code. This tree holds the
rest: how to install, how the workspace is laid out, what is designed and what is left.

## Components

| README | Holds |
| --- | --- |
| [`cli/`](../cli/README.md) | The `hub` command: every subcommand, the files it reads and writes, how dependencies are chosen |
| [`gui/`](../gui/README.md) | The desktop application over `hub --json`: its four layers, its four hand-drawn screens and the form generated for every other command |
| [`contract/`](../contract/README.md) | The JSON contract between `hub` and the desktop application: event shapes, the status payload and the command catalogue |
| [`contract/sushi-account.md`](../contract/sushi-account.md) | The six Sushi Account endpoints `hub` calls and the device grant that walks between them |
| [`gui/tests/fixtures/`](../gui/tests/fixtures/README.md) | Which fixtures are recorded from a live `hub` and which are written by hand |
| [`tools/`](../tools/README.md) | The checkers, the license block writer and the argv recorder |

`sushicore`, the engine under `hub` and every module CLI, lives at
`github.com/SushiSystems/SushiCore` and installs from PyPI. Its manual is `docs/README.md` there.

## Manual

| Document | Holds |
| --- | --- |
| [Installing](getting_started/INSTALL.md) | From a fresh machine to a built module: the one-line installer, the same steps by hand, and what `hub install` downloads |
| [The workspace](architecture/WORKSPACE.md) | The workspace layout, why it is flat, and how a module finds its siblings and the shared dependency tree |
| [Linking checkouts](guides/LINKING_CHECKOUTS.md) | Pointing a workspace at module checkouts that live elsewhere, and at your own `sushicore` |
| [Module manifest](reference/MODULE_MANIFEST.md) | `sushi-module.toml`, the file a module writes to say what it is, and what `hub` does when it is absent |
| [Changelog](reference/CHANGELOG.md) | What changed, by release |
| [Glossary](reference/GLOSSARY.md) | The words this repository uses in a specific sense |
| [Known issues](reference/KNOWN_ISSUES.md) | Open defects with where each sits, and failures that are a toolchain's or a vendor's doing |
| [Contributing](CONTRIBUTING.md) | How a change lands and what it must carry |
| [Documentation style guide](DOCUMENTATION_STYLE_GUIDE.md) | The names and spellings this repository's prose keeps |

## Design

| Document | Holds |
| --- | --- |
| [Design map](design/README.md) | Which design document covers which topic, with its status |
| [Remaining work](design/REMAINING_WORK.md) | The single backlog |
| [The hub](design/HUB.md) | `hub` in the terminal and on the desktop, the binary distribution of sushiengine and the licence flow through Sushi Account |
| [Workspace decoupling](design/WORKSPACE_DECOUPLING.md) | `hub` as a tool and a workspace as data: the catalog out of code, the workspace's own directory, `sushicore` and `sushihub` on PyPI |
| [GPU backend provisioning](design/GPU_BACKEND_PROVISIONING.md) | One brick per GPU vendor and one branch per operating system, with the adapter build wired into `hub install` |

Agent work folders are under `agent/`. Finished material is under `archive/` and is not edited:
`archive/changelog/` holds the release sections older than the live changelog keeps, and
`archive/agent/` holds the specs, plans and reports written before 2026-10-05.
