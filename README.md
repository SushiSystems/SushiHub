# SushiStack

The workspace for the Sushi stack. One clone gives a machine the toolchains and libraries every
module needs, in one `dependencies/` directory, and the `ss` command that manages the module
checkouts beside it.

```bash
curl -fsSL https://sushisystems.io/install.sh | bash      # Linux / WSL
```

```powershell
irm https://sushisystems.io/install.ps1 | iex             # Windows (PowerShell)
```

The repository carries three things of its own:

| Directory | What it is | Its README |
|---|---|---|
| `sushihub/cli/` | The `ss` command: dependency provisioning and module lifecycle. | `sushihub/cli/README.md` |
| `sushihub/gui/` | The desktop application: a screen for every `ss` command, over `ss --json`. | `sushihub/gui/README.md` |
| `sushicore/` | The engine under every Sushi CLI (`ss`, `sr`, `se`, `sa`, `sb`, `sd`): console, config, workspace resolution, the cmake driver. | `sushicore/docs/README.md` |

Everything else under the workspace root is a module checkout `ss add` produces, or the
`dependencies/` tree `ss install` fills. Neither is tracked here.

The manual starts at `docs/README.md`. Install steps are in `docs/getting_started/INSTALL.md`.
What is planned and not yet built is in `docs/design/REMAINING_WORK.md`.

Licensed under the terms in `LICENSE`.
