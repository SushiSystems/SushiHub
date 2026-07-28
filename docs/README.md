# SushiStack

A shared workspace for the Sushi stack. Installs the toolchains and libraries all modules need into one `dependencies/` directory and manages the module checkouts.

Each module has its own CLI (`sr`, `se`) for building and testing. `ss` only handles dependencies and module lifecycle.

## Layout

```
sushistack/
  cli/                     ← the `ss` CLI
    manifests/             ← dependency fragments (*.deps.toml)
  dependencies/            ← toolchains, vcpkg, cmake/ninja (git-ignored)
  sushicli/                ← shared CLI presentation layer (fetched automatically)
  sushiruntime/            ← added by `ss add sushiruntime`
  sushiengine/             ← added by `ss add sushiengine`
  .sushistack              ← workspace marker
```

Modules resolve their compiler and vcpkg from `../dependencies`.

## Install

One command on a fresh machine installs Python and Git if they are missing,
clones the workspace, installs the `ss` CLI, fetches the shared `sushicli`
presentation layer, and downloads the toolchains and libraries into
`dependencies/`:

```bash
curl -fsSL https://sushisystems.io/install.sh | bash      # Linux / WSL
```

```powershell
irm https://sushisystems.io/install.ps1 | iex             # Windows (PowerShell)
```

On Windows use `irm` (Invoke-RestMethod), not `curl` — in PowerShell `curl` is
an alias for `Invoke-WebRequest` and does not pipe a script the same way.

### Manual, step by step

```bash
git clone https://github.com/sushisystems/sushistack.git
cd sushistack
python cli/install.py                # install the `ss` CLI via pipx

ss init                              # write the .sushistack marker and .gitignore entries
ss install                           # download toolchains and libraries
ss add sushiruntime sushiengine      # clone modules into the workspace (aliases: sr se)
ss install-cli sushiruntime          # install that module's own CLI (`sr`)

cd sushiruntime && sr build
```

## `ss` commands

| Command | What it does |
|---|---|
| `ss init` | Write the `.sushistack` workspace marker and add `dependencies/` to `.gitignore`. |
| `ss install [--customize] [--dry-run] [--yes] [--refresh-toolchains]` | Download and install shared dependencies. `--customize` opens an interactive picker to select which toolchains to install. `--yes` assumes yes on the LLVM-download prompt, for unattended runs. `--refresh-toolchains` re-downloads the SYCL toolchain even when one is already installed — an install is otherwise reused forever, and a bundle that predates a capability the build needs (compiler-rt's sanitizer runtimes, say) would keep failing at an unrelated-looking link error. Reused installs report the release they came from and say so when they carry no sanitizer runtime. |
| `ss add <sushiruntime\|sushiengine\|sushiai\|sushiblas\|all> [--dry-run]` | Clone one or more modules into the workspace. Aliases: `sr`, `se`, `sa`, `sb`. |
| `ss link <module> <path> [--dry-run]` | Register an existing checkout outside the workspace as a module (no clone). Also accepts `sushicli` to point at your own checkout. Accepts the same aliases as `ss add`. |
| `ss install-cli <module…> [--dry-run]` | Install a module's own developer CLI (`sr`, `se`) into an isolated pipx venv and inject `sushicli`. Always editable. |
| `ss update [module…] [--dry-run]` | Run `git pull --ff-only` on present modules (cloned or linked). Omit arguments to update all. |
| `ss sync [--dry-run]` | Install missing dependencies, then update all modules. |
| `ss status [--json]` | Show which modules are present and whether dependencies are installed. `--json` prints machine-readable output for scripting. |
| `ss doctor` | Check tools, compilers, and dependencies; report what is missing. |
| `ss remove [--gpu] [--all] [--dry-run] [--yes]` | Remove installed dependencies. `--all` removes the entire `dependencies/` tree and asks for confirmation unless `--yes` is given. |
| `ss home` | Print the workspace root and the `dependencies/` path. |

Shell completion: run `ss --install-completion` once to enable tab-completion for your shell.
