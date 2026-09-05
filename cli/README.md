# The `ss` command

`ss` provisions the shared dependency tree and manages the module checkouts of a SushiStack
workspace. It builds nothing. Each module has its own CLI for that: `sr` (sushiruntime), `se`
(sushiengine), `sa` (sushiai), `sb` (sushiblas), `sd` (sushidsp).

## Layout

```
cli/
  sushistack/            the Python package behind `ss`
    cli.py               the Typer application: one function per subcommand
    config.py            workspace root, config dir, the registered-modules file
    services/            module lifecycle, CLI installation, the interactive picker
    setup/               the dependency engine: manifests, package managers, toolchains, the pipeline
  manifests/             dependency fragments this repository ships (*.deps.toml)
  config.toml            defaults for the [tool] and [cli] tables
  config.local.toml      machine-local overrides written by `ss install`; git-ignored
  modules.local.toml     checkouts registered with `ss link`; git-ignored
  install.py             installs `ss` into a pipx venv and injects sushicore
  pyproject.toml
```

## Commands

| Command | What it does |
|---|---|
| `ss init` | Write the `.sushistack` workspace marker and add `dependencies/` to `.gitignore`. |
| `ss install [--customize] [--dry-run] [--yes] [--refresh-toolchains]` | Download and install shared dependencies. `--customize` opens an interactive picker over the toolchains. `--yes` answers the LLVM-download prompt for unattended runs. `--refresh-toolchains` re-downloads an installed SYCL toolchain, which is otherwise reused forever; reused installs report the release they came from and say when they carry no sanitizer runtime. |
| `ss add <sushiruntime\|sushiengine\|sushiai\|sushiblas\|sushidsp\|all> [--dry-run] [--skip-install]` | Clone one or more modules into the workspace, install each one's CLI, and provision what they declare. `--skip-install` leaves the dependencies to a later `ss install`. Aliases: `sr`, `se`, `sa`, `sb`, `sd`. |
| `ss link <module> <path> [--dry-run] [--skip-install]` | Register an existing checkout outside the workspace as a module, without cloning, then provision what it declares. `--skip-install` leaves that to a later `ss install`. Same names and aliases as `ss add`. |
| `ss install-cli <module…> [--dry-run]` | Install a module's own CLI into an isolated pipx venv and inject `sushicore`. Always editable. Same names, aliases and `all` as `ss add`. |
| `ss update [module…] [--dry-run]` | Run `git pull --ff-only` on present modules, cloned or linked. No arguments means all. |
| `ss sync [--dry-run]` | Install missing dependencies, then update every module. |
| `ss status [--json]` | Which modules are present, in which form, and whether dependencies are installed. `--json` prints the same for scripts. |
| `ss doctor` | Check tools, compilers and dependencies; report what is missing. |
| `ss remove [--gpu] [--all] [--dry-run] [--yes]` | Remove installed dependencies. `--all` removes the whole `dependencies/` tree and asks first unless `--yes` is given. |
| `ss home` | Print the workspace root and the `dependencies/` path. |

Tab completion: run `ss --install-completion` once.

## How dependencies are chosen

`ss install` merges every `cli/manifests/*.deps.toml` fragment with each present module's own
`cli/sushistack.deps.toml`, keeps the entries that name a package for the current platform, and
installs the ones that are missing. No dependency name lives in the installer code. The SYCL
toolchains and CUDA are sushiruntime's entries, not this repository's; the base fragment carries
only cmake, ninja, gtest, opencl and pkgconf.

The toolchain selection follows the same rule: a component is installed when a present module's
fragment declares a dependency of that name, so an empty workspace gets the base tools alone.
`ss add` and `ss link` run the provision pipeline for the module they bring in, unless you pass
`--skip-install`.

## Files it reads and writes

| File | Owner | Purpose |
|---|---|---|
| `<workspace>/.sushistack` | `ss init` | Marks the workspace root; every `ss` and module CLI walks up to it. |
| `cli/config.local.toml` | `ss install` | Resolved toolchain paths for this machine, read by every module CLI through `sushicore`. |
| `cli/modules.local.toml` | `ss link` | Modules that live outside the workspace tree, by name and path. |
| `<workspace>/dependencies/` | `ss install`, `ss remove` | Toolchains, vcpkg, portable cmake and ninja, with a stamp per installed toolchain. |

## Where sushicore comes from

`ss` imports `sushicore` for its console, its config schema and its workspace helpers. The package
is not on any index; `install.py` injects the checkout under `<workspace>/sushicore` into the
pipx venv, editable. `SUSHICORE_DIR` or `ss link sushicore <path>` points it elsewhere. See
`../sushicore/docs/README.md`.
