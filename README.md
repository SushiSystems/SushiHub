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

The repository carries two things of its own:

| Directory | What it is | Its README |
|---|---|---|
| `cli/` | The `hub` command: dependency provisioning and module lifecycle. | `cli/README.md` |
| `gui/` | The desktop application: a screen for every `hub` command, over `hub --json`. | `gui/README.md` |

The engine under every Sushi CLI is `sushicore`, which lives in its own repository and installs
from PyPI: console, config, workspace resolution and the cmake driver.

Everything else under the workspace root is a module checkout `hub add` produces, or the
`dependencies/` tree `hub install` fills. Neither is tracked here.

The manual starts at `docs/README.md`. Install steps are in `docs/getting_started/INSTALL.md`.
What is planned and not yet built is in `docs/design/REMAINING_WORK.md`.

Licensed under the terms in `LICENSE`.
