# The `ss` command

`ss` provisions the shared dependency tree and manages the module checkouts of a SushiStack
workspace. The one thing it builds is the desktop application in `sushihub/gui`, which belongs
to the workspace rather than to a module. Every module has its own CLI: `sr` (sushiruntime),
`se` (sushiengine), `sa` (sushiai), `sb` (sushiblas), `sd` (sushidsp).

## Layout

```
sushihub/cli/
  sushistack/            the Python package behind `ss`
    cli.py               the Typer application: one function per subcommand
    config.py            workspace root, config dir, the registered-modules file
    gui_config.py        the desktop application's profile, config and root
    gui_env.py           its build environment, vcvars snapshot included
    services/            module lifecycle, CLI installation, the picker, the gui build policy
    setup/               the dependency engine: manifests, package managers, toolchains, the pipeline
  manifests/             dependency fragments this repository ships (*.deps.toml)
  config.toml            defaults for the [tool], [cli] and [identity] tables
  config.local.toml      machine-local overrides written by `ss install`; git-ignored
  modules.local.toml     checkouts registered with `ss link`; git-ignored
  install.py             installs `ss` into a pipx venv and injects sushicore
  pyproject.toml
```

## Commands

`--json` and `--describe` are global: they go before the subcommand, and no row below repeats
them. See "Machine-readable output".

| Command | What it does |
|---|---|
| `ss init` | Write the `.sushistack` workspace marker and add `dependencies/` to `.gitignore`. |
| `ss install [--customize] [--dry-run] [--yes] [--refresh-toolchains]` | Download and install shared dependencies. `--customize` opens an interactive picker over the toolchains. `--yes` answers the LLVM-download prompt for unattended runs. `--refresh-toolchains` re-downloads an installed SYCL toolchain, which is otherwise reused forever; reused installs report the release they came from and say when they carry no sanitizer runtime. |
| `ss add <sushiruntime\|sushiengine\|sushiai\|sushiblas\|sushidsp\|all> [--dry-run] [--skip-install]` | Clone one or more modules into the workspace, install each one's CLI, and provision what they declare. `--skip-install` leaves the dependencies to a later `ss install`. Aliases: `sr`, `se`, `sa`, `sb`, `sd`. |
| `ss link <module> <path> [--dry-run] [--skip-install]` | Register an existing checkout outside the workspace as a module, without cloning, then provision what it declares. `--skip-install` leaves that to a later `ss install`. Same names and aliases as `ss add`. |
| `ss install-cli <module…> [--dry-run]` | Install a module's own CLI into an isolated pipx venv and inject `sushicore`. Always editable. Same names, aliases and `all` as `ss add`. |
| `ss update [module…] [--dry-run]` | Run `git pull --ff-only` on present modules, cloned or linked. A binary install is skipped; `ss add <module>` fetches its next release. No arguments means all. |
| `ss sync [--dry-run]` | Install missing dependencies, then update every module. |
| `ss status [--json]` | Which modules are present, in which form, and whether dependencies are installed. Its `--json` is the global flag under another name, kept for scripts written against the old spelling. |
| `ss doctor` | Check tools, compilers and dependencies; report what is missing. |
| `ss remove [--gpu] [--all] [--dry-run] [--yes]` | Remove installed dependencies. `--all` removes the whole `dependencies/` tree and asks first unless `--yes` is given. |
| `ss home` | Print the workspace root and the `dependencies/` path. |
| `ss gui build [--type debug\|release\|relwithdebinfo] [--clean] [-D VAR=VALUE…]` | Configure and compile the desktop application into `sushihub/gui/build/ss`, under the Visual Studio environment on Windows, against the shared vcpkg tree. |
| `ss gui test [--filter <pattern>] [--repeat <n>]` | Run the application's CTest suites. `--filter` selects by test name, `--repeat` re-runs each until it fails. |
| `ss gui run [target] [-- args…]` | Launch a program from the application's build tree; the application itself when no target is named. |
| `ss gui clean` | Remove `sushihub/gui/build/ss`. The presets' own build trees are untouched. |
| `ss login` | Sign in to Sushi ID: print a code, open the browser at the device page, wait for the grant, and store the session in this machine's credential store. |
| `ss logout` | Forget the stored Sushi ID session. Sushi ID is not told. |
| `ss whoami` | Print the signed-in account: its id, its email and how many licences it holds. |
| `ss license` | Print one row per licence on the account: product, holder (`account` or `org`), expiry. |

Tab completion: run `ss --install-completion` once.

## Machine-readable output

`ss --json <command>` writes one JSON event per line to stdout and nothing else there. Everything
a human would read instead — the setup progress bar, a config file rendered before it is written —
goes to stderr, so a caller parses stdout line by line and never has to strip a table out of it.
Every command ends with one `result` event carrying its exit status and whatever it computed:
`ss --json status` puts the module list there, `ss --json home` the workspace and dependency paths.
A question becomes a `prompt` event answered by one line on stdin.

`ss --describe` prints the command catalogue instead: every subcommand, its arguments and options
with their types, defaults and choices. It is a serialisation of the Typer application, not a
second declaration, so a new `ss` command shows up in the catalogue the moment it exists.

Both halves are JSON Schema in `../sushihub/contract/`, and `../sushihub/contract/README.md`
writes out the event shapes, the stdout rule and the prompt rule for whoever is on the other end.

## Signing in

sushiengine is sold; the other four modules are not. `ss login` is how a machine proves a licence,
and nothing else in `ss` needs it: cloning an open-source module asks only for a Git identity.

`ss login` asks Sushi ID for a device code, prints it with the page to type it into, opens that page
in the browser, and polls until you approve it there. What comes back — an access token, a refresh
token and an expiry — goes into the operating system's credential store through `keyring`, under
service `sushistack` and username `sushi-id`. A later command that needs the account refreshes the
access token when it is within 30 seconds of expiry; when the refresh is refused, the stored session
is dropped and the command says nobody is signed in.

Sushi ID lives at `https://id.sushisystems.io`, from `[identity] url` in `config.toml`.
`SUSHI_ID_URL` overrides it, which is how the tests point the four commands at a fake server on
`127.0.0.1`. The four endpoints are written out in `../sushihub/contract/sushi-id.md`; sushiweb
has not built them yet.

## How dependencies are chosen

`ss install` merges every `sushihub/cli/manifests/*.deps.toml` fragment with each present module's own
`cli/sushistack.deps.toml`, keeps the entries that name a package for the current platform, and
installs the ones that are missing. No dependency name lives in the installer code. The SYCL
toolchains and CUDA are sushiruntime's entries, not this repository's; the base fragment carries
only cmake, ninja, gtest, opencl and pkgconf.

A shipped fragment is owned by the name in its filename, with `base.deps.toml` the exception
that owns nothing and is owned by `shared`. So `gui.deps.toml`, which names the desktop
application's imgui, glfw3 and nlohmann-json, is owned by `gui` and `ss doctor` groups those
three rows under it.

The toolchain selection follows the same rule: a component is installed when a present module's
fragment declares a dependency of that name, so an empty workspace gets the base tools alone.
`ss add` and `ss link` run the provision pipeline for the module they bring in, unless you pass
`--skip-install`.

## Files it reads and writes

| File | Owner | Purpose |
|---|---|---|
| `<workspace>/.sushistack` | `ss init` | Marks the workspace root; every `ss` and module CLI walks up to it. |
| `sushihub/cli/config.local.toml` | `ss install` | Resolved toolchain paths for this machine, read by every module CLI through `sushicore`. |
| `sushihub/cli/modules.local.toml` | `ss link` | Modules that live outside the workspace tree, by name and path. |
| `<workspace>/dependencies/` | `ss install`, `ss remove` | Toolchains, vcpkg, portable cmake and ninja, with a stamp per installed toolchain. |
| OS credential store, `sushistack` / `sushi-id` | `ss login`, `ss logout` | The Sushi ID session as one JSON document: both tokens and the access token's expiry. |

## Where sushicore comes from

`ss` imports `sushicore` for its console, its config schema and its workspace helpers. The package
is not on any index; `install.py` injects the checkout under `<workspace>/sushicore` into the
pipx venv, editable. `SUSHICORE_DIR` or `ss link sushicore <path>` points it elsewhere. See
`../../sushicore/docs/README.md`.
