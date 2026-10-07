# The `hub` command

`hub` provisions the shared dependency tree and manages the module checkouts of a SushiStack
workspace. The one thing it builds is the desktop application in `gui`, which belongs
to the workspace rather than to a module. Every module has its own CLI: `sr` (sushiruntime),
`se` (sushiengine), `sa` (sushiai), `sb` (sushiblas).

## Layout

```
cli/
  sushihub/              the Python package behind `hub`
    cli.py               the Typer application, one function per subcommand, and `main()`
    config.py            workspace root, the workspace file, the packaged defaults
    console.py           the console, and the failure line `main()` prints
    describe.py          what `hub` adds to sushicore's `--describe` catalogue
    errors.py            the failures `hub` reports as one line
    gui_config.py        the desktop application's profile, config and root
    gui_env.py           its build environment, vcvars snapshot included
    services/            module lifecycle, Sushi Account, releases, the licence file, the gui build policy
    setup/               the dependency sources and the pipeline wiring over `sushicore.provision`
    defaults.toml        defaults for the [tool], [cli] and [identity] tables
    manifests/           dependency fragments this package ships (*.deps.toml)
  install.py             installs `hub` from this checkout into a pipx venv, editable
  pyproject.toml
```

## Commands

`--json`, `--describe` and `--version` are global: they go before the subcommand, and no row
below repeats them. `hub --version` prints `sushihub` and its installed version. For the other
two see "Machine-readable output".

| Command | What it does |
|---|---|
| `hub init` | Write the `.sushistack` workspace marker and add `dependencies/` to `.gitignore`. |
| `hub install [--customize] [--dry-run] [--yes] [--refresh-toolchains]` | Download and install shared dependencies. `--customize` opens an interactive picker over the toolchains and the GPU toolkit, which is on by default. `--yes` answers the LLVM-download prompt for unattended runs. `--refresh-toolchains` re-downloads an installed SYCL toolchain, which is otherwise reused forever; reused installs report the release they came from and say when they carry no sanitizer runtime. |
| `hub add <sushiruntime\|sushiengine\|sushiai\|sushiblas\|all> [--dry-run] [--skip-install] [--binary]` | Bring one or more modules into the workspace, install each one's CLI, and provision what they declare. `--skip-install` leaves the dependencies to a later `hub install`. `--binary` installs sushiengine from its release rather than its source; see "Binary installs". Aliases: `sr`, `se`, `sa`, `sb`. |
| `hub link <module> <path> [--dry-run] [--skip-install]` | Register an existing checkout outside the workspace as a module, without cloning, then provision what it declares. `--skip-install` leaves that to a later `hub install`. Same names and aliases as `hub add`. |
| `hub install-cli <module…> [--dry-run]` | Install a module's own CLI into an isolated pipx venv; `sushicore` arrives from PyPI as its dependency. Always editable. Same names, aliases and `all` as `hub add`. |
| `hub update [module…] [--dry-run]` | Upgrade `hub` itself, then run `git pull --ff-only` on present modules, cloned or linked. A binary install asks Sushi Account for the latest release and downloads it when the version differs. No arguments means all. |
| `hub sync [--dry-run]` | Update every module, then install missing dependencies. |
| `hub status [--json] [--check-updates]` | Which modules are present, in which form, on which branch and how far from upstream, and whether dependencies are installed. It reads the disk only; `--check-updates` first fetches every checkout and asks Sushi Account for each binary install's latest release. Its `--json` is the global flag under another name, kept for scripts written against the old spelling. |
| `hub doctor` | Check tools, compilers and dependencies; report what is missing. |
| `hub remove [--gpu] [--all] [--dry-run] [--yes]` | Remove installed dependencies. `--all` removes the whole `dependencies/` tree and asks first unless `--yes` is given. |
| `hub migrate [--to PATH] [--dry-run] [--rollback] [--finalize [--drop-link]] [--yes]` | Move the `dependencies/` tree to another directory and leave a link at the old path; see "Moving the dependency tree". |
| `hub home` | Print the workspace root and the `dependencies/` path. |
| `hub docs bundle --release X.Y.Z [--out DIR]` | Write the documentation bundle of the SushiHub checkout the command runs in: `docs-bundle-X.Y.Z.tar.gz` and its `.sha256`, in `build/docs/bundle` unless `--out` names another folder. `docs/publish.toml` says which pages go in. It needs a checkout of this repository, not a workspace, and fails outside one. |
| `hub gui build [--type debug\|release\|relwithdebinfo] [--clean] [-D VAR=VALUE…]` | Configure and compile the desktop application into `gui/build/hub`, under the Visual Studio environment on Windows, against the shared vcpkg tree. |
| `hub gui test [--filter <pattern>] [--repeat <n>]` | Run the application's CTest suites. `--filter` selects by test name, `--repeat` re-runs each until it fails. |
| `hub gui run [target] [-- args…]` | Launch a program from the application's build tree; the application itself when no target is named. |
| `hub gui clean` | Remove `gui/build/hub`. The presets' own build trees are untouched. |
| `hub login` | Sign in to Sushi Account: print a code, open the browser at the device page, wait for the grant, and store the session in this machine's credential store. |
| `hub logout` | Forget the stored Sushi Account session. Sushi Account is not told. |
| `hub whoami` | Print the signed-in account: its id, its email and how many licences it holds. |
| `hub license` | Print one row per licence on the account: product, holder (`account` or `org`), expiry. |

`hub --help` groups the commands under Workspace, Modules, Dependencies, Account and Desktop app,
and each command's own help ends with examples. On a colour terminal the root screen shows the
logo. On a dark terminal set `SUSHI_CLI_BACKGROUND=dark` to give it a glow; `COLORFGBG` is read
when the terminal sets it, and Windows Terminal does not. The `[cli]` table is read from
`<workspace>/sushihub/cli/config.toml` and `config.local.toml`, a directory only a workspace made
before 2026-09-22 has.

## Failures

A failure you can act on is one error line and exit code 1: a command run outside a workspace, a
configuration file that does not parse, Sushi Account out of reach or slow to answer, a machine
with no usable credential store. Under `--json` that line is a `line` event of level `error`,
followed by the `result` event with `ok` false. Anything else is a defect and keeps its traceback.
A usage error is Click's: exit code 2 and no `result` event.

Tab completion: run `hub --install-completion` once.

## Machine-readable output

`hub --json <command>` writes one JSON event per line to stdout and nothing else there. Everything
a human would read instead — the setup progress bar, a config file rendered before it is written —
goes to stderr, so a caller parses stdout line by line and never has to strip a table out of it.
Every command ends with one `result` event carrying its exit status and whatever it computed:
`hub --json status` puts the module list there, `hub --json home` the workspace and dependency paths.
The status payload's shape is fixed by `../contract/status.schema.json`.
A question becomes a `prompt` event answered by one line on stdin.

`hub --describe` prints the command catalogue instead: every subcommand, its arguments and options
with their types, defaults and choices. It is a serialisation of the Typer application, not a
second declaration, so a new `hub` command shows up in the catalogue the moment it exists.

Both halves are JSON Schema in `../contract/`, and `../contract/README.md` writes out the event
shapes, the stdout rule and the prompt rule for whoever is on the other end.

## Signing in

sushiengine is sold; the other three modules are not. `hub login` is how a machine proves a licence,
and nothing else in `hub` needs it: cloning a source-available module asks only for a Git identity.

`hub login` asks Sushi Account for a device code, prints it with the page to type it into, opens that page
in the browser, and polls until you approve it there. What comes back — an access token, a refresh
token and an expiry — goes into the operating system's credential store through `keyring`, under
service `sushihub` and username `sushi-account`. A later command that needs the account refreshes the
access token when it is within 30 seconds of expiry; when the refresh is refused, the stored session
is dropped and the command says nobody is signed in.

Sushi Account lives at `https://account.sushisystems.io`, from `[identity] url` in the packaged
`defaults.toml`; the same key in `.sushistack/workspace.toml` wins over it.
`SUSHI_ACCOUNT_URL` overrides it, which is how the tests point every Sushi Account call at a fake server on
`127.0.0.1`. The six endpoints are written out in `../contract/sushi-account.md`. sushiweb's account
application implements them; `../docs/design/REMAINING_WORK.md` records the state of its deploy.

## Moving the dependency tree

`hub migrate` moves `<workspace>/dependencies` to the directory `--to` names, `~/.sushisystems`
without it. Close the IDEs, terminals and builds that use the tree first: Windows refuses to
rename a folder while a file in it is open.

1. `hub migrate --to PATH --dry-run` prints both paths, each component with its file count and
   size, the total, the free space on the target and whether it is enough. It changes nothing.
2. `hub migrate --to PATH` prints the same plan and asks before it moves; `--yes` skips the
   question. On the same drive each component is renamed into the new directory. On another
   drive each is copied, compared with its source by file count and file size, and only then
   counted as moved; the target needs free space of 1.1 times the tree.
3. `dependencies/` becomes a link to the new directory, a junction on Windows and a symlink
   elsewhere, so every path under it still resolves. What was left of the old folder is kept
   beside it as `dependencies.pre-migrate`.
4. `hub` records the moved components in `<new directory>/registry.toml`, rewrites the `[tool]`
   paths of `.sushistack/workspace.toml` to the new directory, and sets `SUSHISYSTEMS_HOME` for
   your user when the directory is not `~/.sushisystems`; when it is, the variable is removed.
   A terminal opened before the move must be reopened to see the variable.

A run that stops part-way, because a file was open or the run was interrupted, leaves a journal
at `<new directory>/.migrate-journal.jsonl`. `hub migrate --to PATH` goes on from it.

`hub migrate --rollback` undoes the move from that journal: it removes the link, puts the old
folder back with every component in it, restores the `[tool]` paths and the earlier value of
`SUSHISYSTEMS_HOME`, and deletes the registry file the move created. After a run that stopped
before the link was made, give it the same `--to PATH`.

`hub migrate --finalize` deletes `dependencies.pre-migrate` and closes the journal, so there is
nothing left to roll back. Run it once every module builds from the new directory.
`hub migrate --finalize --drop-link` also removes the link at the old path. It is refused
unless `SUSHISYSTEMS_HOME` names the new directory, because the link is otherwise the only
thing that leads `hub` to the tree; build caches and each module's `cli/config.local.toml`
that still name the old path stop resolving once the link is gone.

| Exit code | When |
|---|---|
| 0 | The plan was shown, the tree moved, was already moved, was rolled back or finalized, or there was nothing to roll back |
| 1 | The target holds a component's name, space is short, a component could not be moved or its copy differs, the answer was no, or `--finalize` found nothing to finalize |
| 2 | `--rollback` with `--finalize`, or `--drop-link` without `--finalize` |

## Binary installs

`hub add sushiengine` decides between the two forms rather than being told. It asks the private
repository whether this machine's Git identity reaches it, with `git ls-remote --exit-code` under a
15-second timeout. If it does, the module is cloned like any other. If it does not, `hub` needs a
Sushi Account session: with one it downloads the release, without one it names both ways in and stops.
`--binary` skips the question and goes straight to the release. The other modules are
source-available and have one path; `--binary` on any of them is refused.

The download is what `sushiweb` signed a URL for. `hub` streams it, refuses to unpack it when either
the size or the sha256 differs from what Sushi Account declared, unpacks it into a directory beside
`<workspace>/sushiengine`, and renames that over the module last, so a download that fails leaves
the install that was there untouched. The release carries `sushi-release.json` at its top level:
that file is what makes the directory a binary install, and `hub status` reads the version out of it
("binary 1.4.2"). Beside it `hub` writes `sushi-licence.jwt`, the licence token Sushi Account issued,
which the engine reads at start-up and verifies offline against Sushi Account's JWKS.

A release brings its own sushiruntime and sushiblas, so it declares no dependency fragment and
nothing provisions after it: a licensed user never downloads a SYCL toolchain. It also installs no
module CLI; `se` arrives inside the package.

`hub update sushiengine` asks for the latest release, says the install is already the latest when
the versions match, and downloads the new one and writes the licence file again when they do not.
`hub add sushiengine` on a directory that is already a binary install leaves it alone.

## How dependencies are chosen

`hub install` merges sushicore's base fragment, every `*.deps.toml` fragment the `sushihub`
package ships and each present module's own `cli/sushistack.deps.toml`, keeps the entries that
name a package for the current platform, and installs the ones that are missing. No dependency
name lives in the installer code. The SYCL toolchains are sushiruntime's entries, not this
repository's; the GPU toolkit is on for every workspace and follows the detected GPU vendor
(`sushihub/setup/factory.py`, `derived_selection`); the base fragment carries only cmake, ninja,
gtest, opencl and pkgconf and ships in `sushicore.provision.manifests`.

A fragment this package ships is owned by the name in its filename. So `gui.deps.toml`, which
names the desktop application's imgui, glfw3 and nlohmann-json, is owned by `gui` and
`hub doctor` groups those three rows under it. The base fragment's entries are owned by `shared`.

The toolchain selection is sushicore's rule (`sushicore.provision.selection`): for each
capability a present module requires, nothing installs when the machine already holds a
toolchain that provides it, and otherwise the first one the fragment declares installs. An
empty workspace gets the base tools alone.
`hub add` and `hub link` run the provision pipeline for the module they bring in, unless you pass
`--skip-install`.

## Files it reads and writes

| File | Owner | Purpose |
|---|---|---|
| `<workspace>/.sushistack/` | `hub init` | Marks the workspace root; every `hub` and module CLI walks up to it. |
| `<workspace>/.sushistack/workspace.toml` | `hub init`, `hub install`, `hub link` | Everything the workspace owns: its format version, the resolved toolchain paths for this machine, and the modules linked from outside the tree. |
| `<workspace>/sushiengine/sushi-release.json` | the release | Product, version, platform and what the package bundles. Its presence is what makes the directory a binary install. |
| `<workspace>/sushiengine/sushi-licence.jwt` | `hub add`, `hub update` | The licence token the engine reads at start-up. Nothing but the token. |
| `<workspace>/dependencies/` | `hub install`, `hub remove`, `hub migrate` | Toolchains, vcpkg, portable cmake and ninja, with a stamp per installed toolchain. A link to the new directory after `hub migrate`. |
| `<workspace>/dependencies.pre-migrate/` | `hub migrate` | What was left of the old tree, kept until `hub migrate --finalize`. |
| `<new directory>/.migrate-journal.jsonl` | `hub migrate` | The steps of a move that can still be rolled back; renamed to `.migrate-journal.done.jsonl` by `--finalize`. |
| `SUSHISYSTEMS_HOME`, in the user's environment | `hub migrate` | The new directory, when it is not `~/.sushisystems`. |
| OS credential store, `sushihub` / `sushi-account` | `hub login`, `hub logout` | The Sushi Account session as one JSON document: both tokens and the access token's expiry. |

## Where sushicore comes from

`hub` imports `sushicore` for its console, its config schema, its workspace helpers, the provision
pipeline, the `--describe` catalogue, `--version` and the entry point. It is an ordinary PyPI
dependency (`sushicore>=0.8.0` in `pyproject.toml`), resolved by the same pipx install that
installs `hub`. It is not a module: `hub link sushicore <path>` is refused. To work on both, install
your sushicore checkout editable into `hub`'s venv, as `../docs/guides/LINKING_CHECKOUTS.md` says.

## Notes on the source

A comment in the source says what the code does. The reason it is built that way is here, one
heading per file, and the file cites this section.

### `install.py`

This is the contributor's install. A user installs `hub` from PyPI (`pipx install sushihub`),
which is what `install.ps1` and `install.sh` do; running this script instead points the same
command at the checkout you are editing.

Every platform goes through pipx, which isolates the install and puts `hub` on PATH; pipx is
bootstrapped when it is absent. The install is always `--editable`, against the checkout at
`REPO_ROOT`. `hub` is one half of a self-updating pair with `hub sync` and `hub update`, which
pull this same checkout. A non-editable install would freeze `hub` at whatever revision was on
disk when it was first installed, and every later fix would need a manual reinstall to take
effect. There is no non-editable mode to opt into. `sushicore` is an ordinary dependency,
resolved from PyPI by the same pipx install.

The script finds the CLI package directory itself, as the folder holding `pyproject.toml`, so
renaming the `cli/` folder does not break it.

### `sushihub/cli.py`

`hub` is the umbrella: it provisions one shared dependency tree for the whole stack and manages
the module checkouts named in `catalog.toml` that live inside the workspace. Each module keeps
its own CLI (`sr`, `se`, `sa`, `sb`) for building and testing. `hub` owns downloading,
installing and the module lifecycle, and nothing else. `cli.py` is a thin Typer layer over
`sushihub.services`, and a failure raised as a sushicore error ends in `main()`, through
`console.report_failure`.

`_MODULE_NAMES` and `_MODULE_ALIASES` hold the module names and aliases every command's help
repeats. They are built from the catalog, so a change to `catalog.toml` reaches `hub --help`
and `hub --describe` without an edit in `cli.py`.

### `sushihub/config.py`

The active platform's `[tool.<platform>]` table is merged over the common `[tool]` table, so
one file describes both Linux and Windows. SushiStack is the umbrella workspace, and `hub add`
clones the stack modules (sushiruntime, sushiengine and the rest) inside it. Everything the
installer downloads lands in `<workspace>/dependencies` and is shared by every module, so the
modules never provision their own toolchain or vcpkg tree.

`deps_dir()` answers in this order: `SUSHISTACK_DEPS_DIR`, then `SUSHISYSTEMS_HOME`, then the
directory `<workspace>/dependencies` links to after `hub migrate`, then `<workspace>/dependencies`
itself, then a user-local folder outside a workspace.

The config plumbing is domain-agnostic and shared by every Sushi CLI: the generic build-tool
schema (the cmake, ninja and vcpkg paths) and the skeleton that loads the layers and writes
`[tool]` live in sushicore. `config.py` adds only the SYCL fields.

`CHECKOUT_CLI_DIR` keeps the spelling `sushihub/cli` on purpose. It names where a workspace made
before 2026-09-22 wrote its local config, so the rename of the folder to `cli/` must not follow
it, or the upgrade reads nothing.

`TOOLCHAINS` lists the SYCL toolchains a user can select: intel-llvm is the primary one,
adaptivecpp the secondary, and oneapi is supported. `TOOLCHAIN_COMPILERS` gives each a default
compiler pair, so `sr toolchain <name>` is enough to switch. acpp compiles C++ only, so the C
slot of its pair holds a plain C compiler; the project builds CXX only, which leaves `cc`
unused but valid. `Config.toolchain` is persisted by `sr toolchain`. `llvm_root` and `acpp_exe`
are how the toolchains other than oneAPI provide a SYCL compiler on Windows; `hub install`
discovers them and writes them to `workspace.toml`.

### `sushihub/console.py`

`console.py` is a thin wrapper around `sushicore`. The theme, icon and renderer logic, with its
`[cli]` config schema, lives there and is shared with every module CLI in the stack:
sushiruntime, sushiengine, sushiai and sushiblas. sushicore's README says how to change the
colours.

The console is built on first use, not on import, so a command that needs no workspace
(`hub --help`, `hub --describe`) still runs outside one. Every name the module exposes resolves
through `sushicore.cli_console.LazyConsole`: `console` for the raw Rich console, `info`,
`success`, `warn`, `error`, `command`, `header`, `fail_panel`, `accent`, and the four
machine-readable ones, `table`, `progress`, `result` and `prompt`.

### `sushihub/gui_config.py` and `sushihub/gui_env.py`

`hub gui` builds `gui` the way a module CLI builds its own repository: through
`sushicore.cmake_driver.CMakeDriver` under a snapshotted environment, against the vcpkg tree
`hub install` provisions. That machinery asks for a profile and a config, and `gui_config.py`
is where the application answers. The application is not a module checkout. It lives inside the
workspace `hub` already owns, so its root is a fixed path under the workspace root and its
configuration is the workspace's own. There is no second config directory to find.

`GUI_PROFILE` is read by the environment snapshot's cache key and by the run target, so the two
cannot disagree about what is being built.

A parent process cannot `call vcvars64.bat` and inherit the result, so the shell runs as a child
and its environment is dumped and cached; `sushicore.build_env` holds the mechanism. That is why
`cmake --preset windows-x64` from a plain PowerShell found no compiler and `hub gui build` does.
The application consumes the shared tree and provisions nothing, so its environment is
`sushicore.build_env.StackBuildEnv` with the application's own profile and root resolver.

### `sushihub/services/cli_install.py`

Each module has one program name (`sr`, `se`, `sa`, `sb`, `sd`), resolved from the catalog in
`sushihub.services.catalog`, the single place that knows what the stack contains. Nothing in
the service is per-module: it reads the distribution name out of the module's own
`cli/pyproject.toml`, so a module added to the catalog works the day it is added, with no
change to this file.

The umbrella owns this so that the whole stack has one install seam and no module ships its own
bootstrap script. The service installs the module CLI into an isolated pipx venv and stops
there: `sushicore` is an ordinary PyPI dependency each module CLI declares, and pipx resolves it
like any other.

When the service bootstraps pipx with pip, `--user` goes on the command line only outside a
venv or conda environment. User site-packages are visible there; inside one, pip rejects the
flag.

### `sushihub/services/customize.py`

What the present modules declare installs by default. The picker is the escape hatch for a user
who wants to add or drop one of the heavy components. It opens on that derived selection and
lays the components out as a checklist, one row per component, with a pointer on the focused
row. Up and down move between rows, space toggles the focused one, enter continues, and a final
confirmation guards against an accidental enter. Capturing keys directly and rendering with
rich means the picker needs no extra dependency.

### `sushihub/services/gui.py`

The split between policy here and spawning in `CMakeDriver` is the one every module CLI in the
stack keeps, so the application is built the way sushiblas is and not by a second mechanism.

The build tree is `build/hub` under the application, beside the `build/<preset>` trees
`CMakePresets.json` writes. The two never share a directory: a preset build runs under whatever
environment the shell already had, and this one runs under the vcvars snapshot, so a cache
written by one is wrong for the other.

The configure turns vcpkg's manifest mode off. `hub install` fills a classic-mode tree under
`dependencies/vcpkg` and manifest mode ignores it, which is what the failed configure in
`../docs/archive/agent/plans/2026-09-05-wave-4b-gui-through-ss.md` showed.

### `sushihub/services/hub_install.py` and `sushihub/services/status_report.py`

`hub_install.py` reads the home directory it is given and nothing else, so the `hub` block of
the status payload is the same on every call.

With `check_updates`, `status_report.py` first fetches every checkout and asks Sushi Account
about every binary install, through `git_state` and `update_check`. It collects what failed as
warnings and does not print them.

### `sushihub/services/identity.py`, `session.py` and `token_store.py`

The client prints nothing and asks nothing: the commands in `sushihub.services.session` own the
terminal, and the credential store arrives as a `TokenStore`. The clock, the sleep and the HTTP
opener are constructor arguments, so a test can run the whole grant against a fake server in a
thread with no wall-clock wait.

One factory, `session.client`, decides which server and which credential store every Sushi
Account call in `hub` talks to, so a test replaces the pair in one place.

The client never names a credential store. In production the `TokenStore` it takes is
`KeyringStore`; in tests it is `MemoryStore`, which is gone when the process is.

### `sushihub/services/licence_file.py`

`hub` writes the token bare into the module's own directory. The engine verifies it offline
against Sushi Account's JWKS at start-up, which is why the file holds the token and nothing
around it.

### `sushihub/services/module_manifest.py`

A checkout that carries a manifest describes itself, so `hub` can recognise it without a
catalog entry. Which of the two wins when both a manifest and a catalog entry exist is decided
where both are in scope, not in this module.

### `sushihub/services/modules.py`

SushiStack is the workspace, and the stack's modules (sushiruntime, sushiengine and the rest)
are git checkouts that live inside it, cloned by `hub add`. This service owns that lifecycle:
initialising the workspace, cloning and updating modules.

`sushicore` is the shared CLI presentation layer, not a stack build module. It ships no
dependency fragment and is never built, and it stays out of `CATALOG` so that `hub add all`,
readiness and dependency aggregation all leave it out.

`_GITIGNORE_LINES` names the shared dependency tree and every module checkout because they are
build artifacts of the workspace, not part of it.

`update` brings `hub` itself up to date before any module, so a single `hub update` reaches
every fix and not only the ones in modules. Otherwise an editable `hub` goes stale until
someone remembers to pull its checkout by hand.

### `sushihub/services/presence.py`

Presence is never recorded, only observed. Every command that needs to know whether `.git` is
there asks this module, so the four forms are decided in one place and worded the same
everywhere. The layout rule it reads by is the workspace's own: a module named `sushiengine`
lives at `<workspace>/sushiengine`, whether it was cloned or unpacked.

`RELEASE_MANIFEST` has the same value as `sushicore.profile.RELEASE_MANIFEST`, which is how a
module's own CLI finds a binary root. `tests/test_presence.py` pins the two together so neither
can drift.

### `sushihub/services/releases.py`

Each of the four steps is a function of its own so a test can run it alone. The archive is
unpacked into a temporary directory beside the module's own and moved over it last, so a
download that fails leaves the install that was there untouched.

### `sushihub/services/setup.py`

Consent for the heavy LLVM download on Windows is gathered before the progress spinner starts,
so the prompt can be answered. On Linux, for a user who is not root, sudo is primed at the same
point: the password prompt appears while it is attached to the terminal. Left to `install-deps`,
the live progress spinner would swallow it and it would time out.

### `sushihub/setup/`

The pipeline is dependency-injected. Building a module is that module's own CLI's job. The
public entry point is `factory.build_pipeline`; everything else is an implementation detail
behind small interfaces: `pipeline.Step`, `package_managers.IPackageManager` and
`dependency_source.IDependencySource`.

The installer must not hard-code package names. It asks an `IDependencySource` for the packages
relevant to the current platform. SushiStack owns no single manifest: each module declares what
it needs and the installer aggregates those fragments into one shared dependency set. A module
keeps its fragment under `cli/`, not at its repository root. Finding the fragments is `hub`'s
own business, in `dependency_source.py`. A module linked to an external checkout, a developer's
working repository outside the workspace tree, contributes its fragment like one inside it.

`MODULE_META_TABLE` is the table name a fragment reserves for module-level metadata, currently
`depends_on`, as opposed to a dependency.

On Linux `VcpkgManager` is the only route for the ports that have no apt package at all:
vk-bootstrap and cgltf.

### `tests/conftest.py`

`MemorySource` exists so that no test reads a manifest, touches the network or writes into
`dependencies/`. Two things happen before `sushihub` is imported. `SUSHISTACK_HOME` is pinned to
the repository root, because `sushihub.console` resolves the workspace at import time and
pytest may run from outside one. The repository root leaves `sys.path`, because a `sushicore/`
directory there shadows the installed `sushicore` distribution as a namespace package.
