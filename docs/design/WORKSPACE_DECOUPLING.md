# Decoupling the hub from the SushiStack checkout

**Status:** Open — waves 0 to 7 built; wave 8 and `st setup` are open

## Problem

The code references in this section are those of the checkout before the waves landed; the
landing records are in [the waves report](../agent/2026_10_21_WORKSPACE_DECOUPLING_WAVES/REPORT.md).

SushiStack does two jobs from one repository. It is the install path a user runs to get an
engine and the toolchains under it, and it is the bench a developer works on with several
checkouts sharing one `dependencies/` tree. The two jobs point at different people, and where
they disagree is where the repository hurts.

A user is served well: one command fetches Python, git, the CLI, then CUDA and vcpkg into a
single tree that `hub remove --all` reclaims. A developer who only wants to change `sushiruntime`
is not: the entry step is a clone of a repository that knows about five other modules, and
`hub add all` offers all six.

Four things held the coupling in place.

- `services/modules.py:47` names six modules in code. Each entry carries the name, the clone URL
  and the directory. `_ALIASES` repeats the six.
- `sushicore/workspace.py` fixes `WORKSPACE_CLI_DIR` at `cli`, and `config.py:61`
  resolves `config.toml`, `config.local.toml`, `modules.local.toml` and `manifests/` under it.
  The workspace's data therefore lives inside the hub's source tree, so a directory that is not
  a SushiStack clone has nowhere to put it. `workspace_root` even accepts
  `cli/manifests` as a marker, which is the repository's own signature.
- `services/modules.py` injects `sushicore` into the pipx venv from the fixed path
  `<workspace>/sushicore`, so the CLI cannot be installed without the clone.
- `install.sh:130` and `install.ps1:184` clone the repository before anything else runs.

Two things were already decoupled and stay that way. No dependency name appears in installer
code: the base fragment, which lives in sushicore, holds the shared tools and each module declares
its own in a `sushistack.deps.toml` that `hub install` aggregates. And `config.py:35` resolves the
workspace by walking up for a marker rather than from the package location, which is what makes
the rest of this design cheap.

`sushidsp` and `sushitrack` name `sushiruntime` in no cmake file, and they share none of the
stack's weight: no file in either repository mentions SYCL, so the shared toolchain tree, the
reason the stack exists, buys them nothing. The dependency graph is
`sushiruntime <- sushiblas <- sushiai <- sushiengine`; the other two stand beside it rather than
in it. Both carry a `sushistack.deps.toml`, and what they declare is small: `sushitrack` asks for
GoogleTest, `sushidsp` for SDL2 and, optionally, intel/llvm's clang++ as a plain C++ compiler.
The fragment reader refuses a shape it cannot read, such as an array of `[[dependency]]` tables.

## Decision

- SushiStack is the install path plus a thin bench. The user-facing promise stays.
- The module catalog is closed to outsiders and the door is left open: a module describes
  itself, and the catalog is the fallback rather than the only source.
- `sushitrack` is in the catalog, with `st` as its alias, and still installs on its own with
  `pipx install cli/`; the catalog only makes joining a workspace optional. `sushidsp` stays
  outside. Each provisions itself from its own source of truth and attaches to a workspace when
  one is there. `sd setup` reads its dependency fragment and hands off to `hub install` inside a
  workspace; `st setup` will create its conda environment from `environment.yml`, and is deferred
  until that repository's CLI can be tested. `sushi-module.toml` is what makes a checkout
  recognisable, so the door stays open without reopening the catalog.
- `sushidsp` stays outside because its real-time path stays on the CPU: the circuit solve is
  sample-serial, so there is no parallelism along the axis a GPU wants, and a nonlinearity inside
  a feedback loop would not survive floating point that differs between machines. An offline path
  (rendering, parameter fitting, batches) is where `sushiruntime` could pay, and is a separate
  design if it is ever wanted.
- `hub` is a tool and a workspace is data. A single checkout is a workspace; so is a directory
  holding six.
- `sushicore` lives in its own repository and both it and `sushihub` publish to PyPI.
- The binary distribution of `sushiengine` does not change.
- `hub` is optional for building a module. Every module CLI provisions itself through
  `sushicore.provision` and `hub` runs the same code over a whole workspace. The engine's binary
  still arrives through `hub` and a licence. Design: the SushiCore repository's
  `docs/design/STANDALONE_PROVISIONING.md`.

## Design

### ModuleCatalog

`MODULES` becomes a `ModuleCatalog` reading a `catalog.toml` that ships inside the `sushihub`
distribution. An entry holds the name, the clone URL, the directory, the alias and a
`distribution` field whose value is `source` or `binary`.

`BINARY_MODULE = "sushiengine"` at `services/modules.py:69` disappears into that field, so the
choice at `services/modules.py:426` between a reachable source and a licensed download reads the
entry rather than a module name.

The readers are `services/modules.py`, `services/status_report.py:125` and `setup/steps.py:379`.
All three take the catalog through the one interface, which is what makes a remote catalog later
a change of source and nothing else.

### The module manifest

A module root gains `sushi-module.toml`: the name, the alias, the CLI program name and the path
to its dependency fragment. When a checkout carries one, `hub` reads it; when it does not, `hub`
falls back to the catalog entry. The modules adopt the file at their own pace, and
`hub add <git-url>` stays out until it is wanted.

### The workspace directory

The marker `.sushistack` is a directory holding one file, `workspace.toml`, with `[workspace]`,
`[modules]` and `[tool]` tables. The committed defaults belong to the tool rather than to the
workspace, so `config.toml`, the base fragment and `manifests/gui.deps.toml` live in the
`sushihub` package. `WORKSPACE_CLI_DIR` is gone from `sushicore`, and `workspace_root` does not
accept the manifests tree as a marker.

Every `hub` command upgrades an old marker file silently: it creates the directory, copies
`cli/config.local.toml` and `cli/modules.local.toml` into it, and leaves the originals in place
so the step can be undone by deleting the directory. `cli/config.local.toml` holds
machine-specific compiler, vcpkg and oneAPI paths, which is why the originals stay.

This changes a persistent layout that existing workspaces depend on. `file-formats` and
`api-stability` govern it.

### Distribution

`sushicore` has its own repository and publishes to PyPI. `sushihub` depends on it as an
ordinary requirement. `sr`, `se`, `sa` and `sb` take the same published `sushicore`.

`hub` itself publishes too, as `sushihub`. **The module CLIs do not**: every one of their
commands resolves a repository root, which each module's own `cli/pyproject.toml` states, so a
published `sr` would answer every subcommand with an error. The test a package has to pass is
whether it does anything without a checkout. `sushicore` passes it as a library, `hub` passes it
because `hub init` runs in an empty folder, and the module CLIs fail it. They stay installed
editable from a checkout by `hub add`. Reopen this only when a module CLI does useful work
without a source tree, the way `hub add sushiengine` already fetches a release.

The desktop application is distributed separately. It goes to PyPI as its own `sushihub-gui`
distribution with a wheel per platform, reached as `pipx install "sushihub[gui]"`, and it is
versioned from the same tag as `sushihub` so the two never disagree about the `--describe`
contract. `sushihub` itself stays `py3-none-any`: a platform we build no application for still
installs the CLI.

`hub gui run` launches what the build tree holds, and gains a second place to look rather than a
new job: the workspace's own build when the source is there, the installed application when it is
not. `hub gui build` and `hub gui test` stay developer commands that need the source and say so
plainly when there is none.

`install.sh` and `install.ps1` bootstrap Python, git and pipx, install `sushihub` from PyPI, then
run `hub init` in the directory the user chose. A clone of SushiStack is what a contributor does,
or a user who wants the desktop application.

### The two journeys

**A user** runs the one-line installer, which leaves `hub` on the PATH and a marked workspace in
the chosen directory. `hub add sushiengine` finds a licence on the account, downloads the signed
release, writes `sushi-release.json` and the licence file, and `hub install` provisions what the
release declares. CUDA and vcpkg land once, in one tree.

**A developer** who wants `sushiruntime` clones that repository, runs `hub init` inside it and
builds with `sr build`. The other three modules are never mentioned, because `hub status`
reports what is present rather than what the catalog knows. Working on several modules means
running `hub init` one directory up.

**The maintainer's bench** keeps its shape: a workspace at the top, checkouts linked into it
with `hub link`. `module_dest` returns the linked path, so a linked `sushiengine` keeps winning
over the binary and the source build is never displaced.

### Risks

**The PyPI names.** A name is unreserved until its first upload, so a new distribution uploads a
placeholder before anything else.

**The engine's licence path.** The source-or-binary decision at `services/modules.py:426` is
pinned by `tests/test_add_binary.py`, so a rewrite of it has something to answer to.

## Phases

Hierarchy first: `sushicore` sits under every CLI and moves first; the catalog is fixed before
anything reading it changes. Waves 6 and 7 run beside the 3-4-5 chain; their file sets are
disjoint from it.

| Id | Phase | State |
| --- | --- | --- |
| W0 | Tests for the five uncovered seams: `workspace_root` and `config_dir` resolution, the `MODULES` catalog and its aliases, `hub init`'s marker and `.gitignore` lines, `hub link`'s write to `modules.local.toml`, and the `sushicore` injection in `_install_module_cli` | built |
| W1 | `sushicore` in its own repository and on PyPI; all seven consumer CLIs depend on the published package; the path injection deleted. Waits on W0 | built |
| W2 | `ModuleCatalog` and `catalog.toml` inside the package; `BINARY_MODULE` becomes the `distribution` field; `sushidsp` and `sushitrack` leave the catalog. Waits on W1 | built |
| W3 | `.sushistack` as a directory holding `workspace.toml`; `defaults.toml` and `manifests/` inside the package; every `hub` command upgrades an old marker. Waits on W2 | built |
| W4 | `sushihub` on PyPI; the installers bootstrap Python, git and pipx and run `hub init`; `hub sync` upgrades `hub` the way it was installed. Waits on W3 | built |
| W5 | `sushicore` out of the status table, the fixtures re-recorded from a live `hub`, Linux no longer pointed at a vcpkg tree it never uses. Waits on W4 | built |
| W6 | `sushi-module.toml`, its reader, and the file in each of the four modules; `hub status` lists what the workspace knows and `hub link` accepts a checkout that names itself. Waits on W2 | built |
| W7 | `sd setup` provisions sushidsp from its own fragment and hands off to `hub install` inside a workspace; the fragment reader lives in `sushicore`. Waits on W2 | built |
| W7b | `st setup`, designed and deferred: sushitrack's CLI carries no test suite | planned |
| W8 | The desktop application distributed: a separate `sushihub-gui` distribution with platform wheels, `pipx install "sushihub[gui]"`, one tag with `sushihub`; `hub gui run` prefers the workspace's build tree and falls back to the installed one. Exit: `hub gui run` opens the application on a machine with no checkout. Waits on W5 | planned |

## Open questions

None.
