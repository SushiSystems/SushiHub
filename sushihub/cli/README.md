# The `hub` command

`hub` provisions the shared dependency tree and manages the module checkouts of a SushiStack
workspace. The one thing it builds is the desktop application in `sushihub/gui`, which belongs
to the workspace rather than to a module. Every module has its own CLI: `sr` (sushiruntime),
`se` (sushiengine), `sa` (sushiai), `sb` (sushiblas), `sd` (sushidsp).

## Layout

```
sushihub/cli/
  sushistack/            the Python package behind `hub`
    cli.py               the Typer application: one function per subcommand
    config.py            workspace root, config dir, the registered-modules file
    gui_config.py        the desktop application's profile, config and root
    gui_env.py           its build environment, vcvars snapshot included
    services/            module lifecycle, Sushi ID, releases, the licence file, projects, the gui build policy
    setup/               the dependency engine: manifests, package managers, toolchains, the pipeline
  manifests/             dependency fragments this repository ships (*.deps.toml)
  config.toml            defaults for the [tool], [cli] and [identity] tables
  config.local.toml      machine-local overrides written by `hub install`; git-ignored
  modules.local.toml     checkouts registered with `hub link`; git-ignored
  projects.local.toml    projects registered with `hub projects`; git-ignored
  install.py             installs `hub` into a pipx venv and injects sushicore
  pyproject.toml
```

## Commands

`--json` and `--describe` are global: they go before the subcommand, and no row below repeats
them. See "Machine-readable output".

| Command | What it does |
|---|---|
| `hub init` | Write the `.sushistack` workspace marker and add `dependencies/` to `.gitignore`. |
| `hub install [--customize] [--dry-run] [--yes] [--refresh-toolchains]` | Download and install shared dependencies. `--customize` opens an interactive picker over the toolchains. `--yes` answers the LLVM-download prompt for unattended runs. `--refresh-toolchains` re-downloads an installed SYCL toolchain, which is otherwise reused forever; reused installs report the release they came from and say when they carry no sanitizer runtime. |
| `hub add <sushiruntime\|sushiengine\|sushiai\|sushiblas\|sushidsp\|all> [--dry-run] [--skip-install] [--binary]` | Bring one or more modules into the workspace, install each one's CLI, and provision what they declare. `--skip-install` leaves the dependencies to a later `hub install`. `--binary` installs sushiengine from its release rather than its source; see "Binary installs". Aliases: `sr`, `se`, `sa`, `sb`, `sd`. |
| `hub link <module> <path> [--dry-run] [--skip-install]` | Register an existing checkout outside the workspace as a module, without cloning, then provision what it declares. `--skip-install` leaves that to a later `hub install`. Same names and aliases as `hub add`. |
| `hub install-cli <module…> [--dry-run]` | Install a module's own CLI into an isolated pipx venv and inject `sushicore`. Always editable. Same names, aliases and `all` as `hub add`. |
| `hub update [module…] [--dry-run]` | Run `git pull --ff-only` on present modules, cloned or linked. A binary install asks Sushi ID for the latest release and downloads it when the version differs. No arguments means all. |
| `hub sync [--dry-run]` | Install missing dependencies, then update every module. |
| `hub status [--json]` | Which modules are present, in which form, and whether dependencies are installed. Its `--json` is the global flag under another name, kept for scripts written against the old spelling. |
| `hub doctor` | Check tools, compilers and dependencies; report what is missing. |
| `hub remove [--gpu] [--all] [--dry-run] [--yes]` | Remove installed dependencies. `--all` removes the whole `dependencies/` tree and asks first unless `--yes` is given. |
| `hub home` | Print the workspace root and the `dependencies/` path. |
| `hub gui build [--type debug\|release\|relwithdebinfo] [--clean] [-D VAR=VALUE…]` | Configure and compile the desktop application into `sushihub/gui/build/hub`, under the Visual Studio environment on Windows, against the shared vcpkg tree. |
| `hub gui test [--filter <pattern>] [--repeat <n>]` | Run the application's CTest suites. `--filter` selects by test name, `--repeat` re-runs each until it fails. |
| `hub gui run [target] [-- args…]` | Launch a program from the application's build tree; the application itself when no target is named. |
| `hub gui clean` | Remove `sushihub/gui/build/hub`. The presets' own build trees are untouched. |
| `hub login` | Sign in to Sushi ID: print a code, open the browser at the device page, wait for the grant, and store the session in this machine's credential store. |
| `hub logout` | Forget the stored Sushi ID session. Sushi ID is not told. |
| `hub whoami` | Print the signed-in account: its id, its email and how many licences it holds. |
| `hub license` | Print one row per licence on the account: product, holder (`account` or `org`), expiry. |
| `hub projects list` | Print the registered projects: name, path, and whether the directory is still there. |
| `hub projects add <path> [--name <name>]` | Register a project directory. The name is the directory's own unless `--name` says otherwise. |
| `hub projects remove <name>` | Drop a project from the registry. Its directory is untouched. |

Tab completion: run `hub --install-completion` once.

## Machine-readable output

`hub --json <command>` writes one JSON event per line to stdout and nothing else there. Everything
a human would read instead — the setup progress bar, a config file rendered before it is written —
goes to stderr, so a caller parses stdout line by line and never has to strip a table out of it.
Every command ends with one `result` event carrying its exit status and whatever it computed:
`hub --json status` puts the module list there, `hub --json home` the workspace and dependency paths.
A question becomes a `prompt` event answered by one line on stdin.

`hub --describe` prints the command catalogue instead: every subcommand, its arguments and options
with their types, defaults and choices. It is a serialisation of the Typer application, not a
second declaration, so a new `hub` command shows up in the catalogue the moment it exists.

Both halves are JSON Schema in `../contract/`, and `../contract/README.md` writes out the event
shapes, the stdout rule and the prompt rule for whoever is on the other end.

## Signing in

sushiengine is sold; the other four modules are not. `hub login` is how a machine proves a licence,
and nothing else in `hub` needs it: cloning an open-source module asks only for a Git identity.

`hub login` asks Sushi ID for a device code, prints it with the page to type it into, opens that page
in the browser, and polls until you approve it there. What comes back — an access token, a refresh
token and an expiry — goes into the operating system's credential store through `keyring`, under
service `sushistack` and username `sushi-id`. A later command that needs the account refreshes the
access token when it is within 30 seconds of expiry; when the refresh is refused, the stored session
is dropped and the command says nobody is signed in.

Sushi ID lives at `https://id.sushisystems.io`, from `[identity] url` in `config.toml`.
`SUSHI_ID_URL` overrides it, which is how the tests point every Sushi ID call at a fake server on
`127.0.0.1`. The six endpoints are written out in `../contract/sushi-id.md`; sushiweb has not built
them yet.

## Binary installs

`hub add sushiengine` decides between the two forms rather than being told. It asks the private
repository whether this machine's Git identity reaches it, with `git ls-remote --exit-code` under a
15-second timeout. If it does, the module is cloned like any other. If it does not, `hub` needs a
Sushi ID session: with one it downloads the release, without one it names both ways in and stops.
`--binary` skips the question and goes straight to the release. The other four modules are open
source and have one path; `--binary` on any of them is refused.

The download is what `sushiweb` signed a URL for. `hub` streams it, refuses to unpack it when either
the size or the sha256 differs from what Sushi ID declared, unpacks it into a directory beside
`<workspace>/sushiengine`, and renames that over the module last, so a download that fails leaves
the install that was there untouched. The release carries `sushi-release.json` at its top level:
that file is what makes the directory a binary install, and `hub status` reads the version out of it
("binary 1.4.2"). Beside it `hub` writes `sushi-licence.jwt`, the licence token Sushi ID issued,
which the engine reads at start-up and verifies offline against Sushi ID's JWKS.

A release brings its own sushiruntime and sushiblas, so it declares no dependency fragment and
nothing provisions after it: a licensed user never downloads a SYCL toolchain. It also installs no
module CLI; `se` arrives inside the package.

`hub update sushiengine` asks for the latest release, says the install is already the latest when
the versions match, and downloads the new one and writes the licence file again when they do not.
`hub add sushiengine` on a directory that is already a binary install leaves it alone.

## How dependencies are chosen

`hub install` merges every `sushihub/cli/manifests/*.deps.toml` fragment with each present module's own
`cli/sushistack.deps.toml`, keeps the entries that name a package for the current platform, and
installs the ones that are missing. No dependency name lives in the installer code. The SYCL
toolchains and CUDA are sushiruntime's entries, not this repository's; the base fragment carries
only cmake, ninja, gtest, opencl and pkgconf.

A shipped fragment is owned by the name in its filename, with `base.deps.toml` the exception
that owns nothing and is owned by `shared`. So `gui.deps.toml`, which names the desktop
application's imgui, glfw3 and nlohmann-json, is owned by `gui` and `hub doctor` groups those
three rows under it.

The toolchain selection follows the same rule: a component is installed when a present module's
fragment declares a dependency of that name, so an empty workspace gets the base tools alone.
`hub add` and `hub link` run the provision pipeline for the module they bring in, unless you pass
`--skip-install`.

## Files it reads and writes

| File | Owner | Purpose |
|---|---|---|
| `<workspace>/.sushistack` | `hub init` | Marks the workspace root; every `hub` and module CLI walks up to it. |
| `sushihub/cli/config.local.toml` | `hub install` | Resolved toolchain paths for this machine, read by every module CLI through `sushicore`. |
| `sushihub/cli/modules.local.toml` | `hub link` | Modules that live outside the workspace tree, by name and path. |
| `sushihub/cli/projects.local.toml` | `hub projects` | The projects the desktop application lists and opens, by name and path. |
| `<workspace>/sushiengine/sushi-release.json` | the release | Product, version, platform and what the package bundles. Its presence is what makes the directory a binary install. |
| `<workspace>/sushiengine/sushi-licence.jwt` | `hub add`, `hub update` | The licence token the engine reads at start-up. Nothing but the token. |
| `<workspace>/dependencies/` | `hub install`, `hub remove` | Toolchains, vcpkg, portable cmake and ninja, with a stamp per installed toolchain. |
| OS credential store, `sushistack` / `sushi-id` | `hub login`, `hub logout` | The Sushi ID session as one JSON document: both tokens and the access token's expiry. |

## Where sushicore comes from

`hub` imports `sushicore` for its console, its config schema and its workspace helpers. The package
is not on any index; `install.py` injects the checkout under `<workspace>/sushicore` into the
pipx venv, editable. `SUSHICORE_DIR` or `hub link sushicore <path>` points it elsewhere. See
`../../sushicore/docs/README.md`.
