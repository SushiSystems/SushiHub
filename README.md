# SushiHub

The tool that acquires and manages a SushiStack workspace. One command gives a machine the
toolchains and libraries every module needs, in one `dependencies/` directory, and the `hub`
command that manages the module checkouts beside it. SushiStack is the applications; SushiHub
is what installs them. `hub` comes from PyPI as `sushihub`; this repository carries its source and
the desktop application.

```bash
curl -fsSL https://sushisystems.io/install.sh | bash      # Linux / WSL
```

```powershell
irm https://sushisystems.io/install.ps1 | iex             # Windows (PowerShell)
```

The repository carries four things of its own:

| Directory | What it is | Its README |
|---|---|---|
| `cli/` | The `hub` command: dependency provisioning and module lifecycle. | `cli/README.md` |
| `gui/` | The desktop application: a screen for every `hub` command, over `hub --json`. | `gui/README.md` |
| `contract/` | The JSON schemas `hub` and the desktop application both validate against. | `contract/README.md` |
| `tools/` | The checkers and the argv recorder; they build nothing. | `tools/README.md` |

The engine under every Sushi CLI is `sushicore`, which lives in its own repository and installs
from PyPI: console, config, workspace resolution, the cmake driver and dependency provisioning.

`hub` is not required to build a module. A module CLI provisions its own checkout with
`setup` and reports on it with `doctor`, through the same `sushicore` code `hub install` runs.
`hub` is what does that for several checkouts at once, and what fetches the engine's binary.
Every module CLI has registered the two commands since 2026-10-04.

Everything else under the workspace root is a module checkout `hub add` produces, or the
`dependencies/` tree `hub install` fills. Neither is tracked here.

After an install, `hub status` lists the modules present and `hub doctor` reports what is
missing.

The manual starts at [`docs/README.md`](docs/README.md). Install steps are in
`docs/getting_started/INSTALL.md`. What is planned and not yet built is in
`docs/design/REMAINING_WORK.md`.

## Licence

SushiHub is source-available, free for non-commercial use under the PolyForm Noncommercial
License 1.0.0; commercial use needs a licence from Sushi Systems, see `COMMERCIAL.md`. `LICENSE`
is the binding text and `NOTICE.md` lists the third-party parts.

sushihub 0.1.0 on PyPI and the commits before the one that replaced `LICENSE` were published
under the Apache License 2.0 and stay available under it.

This is the licence of the source in this repository. The licence `hub license` reports is a
different thing: the product licence Sushi Account issues for sushiengine.
