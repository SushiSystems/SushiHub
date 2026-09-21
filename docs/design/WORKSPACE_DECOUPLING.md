# Decoupling the hub from the SushiStack checkout

**Status:** designed 2026-09-21, nothing built. Wave 0 is the first task; the waves are
mirrored into `REMAINING_WORK.md` so the order can be read from one place. The catalog work in
wave 2 removes `sushidsp` and `sushitrack` from the stack, which is a breaking change to
`hub add`, `hub link` and `hub install-cli`.

## 1. The problem

SushiStack does two jobs from one repository. It is the install path a user runs to get an
engine and the toolchains under it, and it is the bench a developer works on with several
checkouts sharing one `dependencies/` tree. The two jobs point at different people, and where
they disagree is where the repository hurts.

A user is served well today: one command fetches Python, git, the CLI, then CUDA and vcpkg into
a single tree that `hub remove --all` reclaims. A developer who only wants to change
`sushiruntime` is not: the entry step is a clone of a repository that knows about five other
modules, and `hub add all` offers all six.

Four things hold the coupling in place.

- `services/modules.py:47` names six modules in code. Each entry carries the name, the clone URL
  and the directory. `_ALIASES` repeats the six.
- `sushicore/workspace.py` fixes `WORKSPACE_CLI_DIR` at `sushihub/cli`, and `config.py:61`
  resolves `config.toml`, `config.local.toml`, `modules.local.toml` and `manifests/` under it.
  The workspace's data therefore lives inside the hub's source tree, so a directory that is not
  a SushiStack clone has nowhere to put it. `workspace_root` even accepts
  `sushihub/cli/manifests` as a marker, which is the repository's own signature.
- `services/modules.py` injects `sushicore` into the pipx venv from the fixed path
  `<workspace>/sushicore`, so the CLI cannot be installed without the clone.
- `install.sh:130` and `install.ps1:184` clone the repository before anything else runs.

Two things are already decoupled and stay that way. No dependency name appears in installer
code: `manifests/base.deps.toml` holds the shared tools and each module declares its own in a
`sushistack.deps.toml` that `hub install` aggregates. And `config.py:35` resolves the workspace
by walking up for a marker rather than from the package location, which is what makes the rest
of this design cheap.

`sushidsp` and `sushitrack` carry no `sushistack.deps.toml` and name `sushiruntime` in no cmake
file. The dependency graph is `sushiruntime <- sushiblas <- sushiai <- sushiengine`; the other
two stand beside it rather than in it.

## 2. What is decided

- SushiStack is the install path plus a thin bench. The user-facing promise stays.
- The module catalog is closed to outsiders today and the door is left open: a module describes
  itself, and the catalog is the fallback rather than the only source.
- `sushidsp` and `sushitrack` leave the catalog. They keep their own CLIs and their own install
  paths.
- `hub` is a tool and a workspace is data. A single checkout is a workspace; so is a directory
  holding six.
- `sushicore` moves to its own repository and both it and `sushihub` publish to PyPI.
- The binary distribution of `sushiengine` does not change.

## 3. The bricks

### 3.1 ModuleCatalog

`MODULES` becomes a `ModuleCatalog` reading a `catalog.toml` that ships inside the `sushihub`
distribution. An entry holds the name, the clone URL, the directory, the alias and a
`distribution` field whose value is `source` or `binary`. Four entries remain.

`BINARY_MODULE = "sushiengine"` at `services/modules.py:69` disappears into that field, so the
choice at `services/modules.py:426` between a reachable source and a licensed download reads the
entry rather than a module name.

Today's readers are `services/modules.py`, `services/status_report.py:125` and
`setup/steps.py:379`. All three take the catalog through the one interface, which is what makes
a remote catalog later a change of source and nothing else.

### 3.2 The module manifest

A module root gains `sushi-module.toml`: the name, the alias, the CLI program name and the path
to its dependency fragment. When a checkout carries one, `hub` reads it; when it does not, `hub`
falls back to the catalog entry. The four modules adopt the file at their own pace, and
`hub add <git-url>` becomes a path that skips the catalog whenever it is wanted.

### 3.3 The workspace directory

The marker `.sushistack` becomes a directory and holds what belongs to the workspace:
`workspace.toml`, `modules.toml` and `config.local.toml`. The committed defaults belong to the
tool rather than to the workspace, so `config.toml`, `manifests/base.deps.toml` and
`manifests/gui.deps.toml` move into the `sushihub` package. `WORKSPACE_CLI_DIR` leaves
`sushicore`, and `workspace_root` stops accepting the manifests tree as a marker.

`hub init` upgrades a marker file it finds: it creates the directory, copies
`sushihub/cli/config.local.toml` and `sushihub/cli/modules.local.toml` into it, and leaves the
originals in place so the step can be undone by deleting the directory.

This changes a persistent layout that existing workspaces depend on. `file-formats` and
`api-stability` govern it.

### 3.4 Distribution

`sushicore` moves to its own repository and publishes to PyPI. `sushihub` depends on it as an
ordinary requirement, and `sushicore_dir` and its path injection are deleted. `sr`, `se`, `sa`
and `sb` take the same published package.

`install.sh` and `install.ps1` stop cloning. They bootstrap Python, git and pipx, install
`sushihub` from PyPI, then run `hub init` in the directory the user chose. A clone of SushiStack
becomes the default starting point rather than a precondition.

## 4. The two journeys

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

## 5. Waves

Hierarchy first: `sushicore` sits under every CLI and moves first; the catalog is fixed before
anything reading it changes.

Measured on 2026-09-21: `sushihub/cli/tests` holds 24 files and 297 passing tests, and
`.github/workflows/ci.yml:43` runs them. The source-or-binary decision is the best covered part
of the code, with 18 tests in `tests/test_add_binary.py`.

Five seams this design rewrites carry no test at all. No test file names `config_dir`,
`MODULES`, `_GITIGNORE_LINES`, `sushicore_dir` or `_install_module_cli`, and `hub init` and
`hub link` are exercised only incidentally through `tests/test_json_streams.py`. Wave 0 covers
those five and nothing else.

| Wave | Work | Waits on | Acceptance |
|---|---|---|---|
| 0 | Tests for the five uncovered seams: `workspace_root` and `config_dir` resolution, the `MODULES` catalog and its aliases, `hub init`'s marker and `.gitignore` lines, `hub link`'s write to `modules.local.toml`, and the `sushicore` injection in `_install_module_cli`. | nothing | The five state today's behaviour and the suite still passes as a whole |
| 1 | `sushicore` moves to its own repository and publishes to PyPI. `hub`, `sr`, `se`, `sa` and `sb` depend on the published package; the path injection is deleted. | 0 | On a clean machine `pipx install sushihub` gives a working `hub --version` |
| 2 | `ModuleCatalog` and `catalog.toml` inside the package, four entries. `BINARY_MODULE` becomes the `distribution` field. `sushidsp` and `sushitrack` leave the catalog. | 1 | `hub add all` names four modules; `hub add sushidsp` reports an unknown module |
| 3 | `.sushistack` becomes a directory holding `workspace.toml`, `modules.toml` and `config.local.toml`. `config.toml` and `manifests/` move into the package. `hub init` upgrades an old marker. | 2 | `hub init` then `hub install` works in an empty directory, and an upgraded existing workspace prints the same `hub status` table as before |
| 4 | The installers drop the clone: pipx from PyPI, then `hub init`. `sushihub` publishes to PyPI. | 3 | One line on a clean Windows machine, then `hub add sushiengine` downloads the release |
| 5 | The desktop application draws the new fields, and `tests/fixtures/` is re-recorded from a real `hub --json status` and `hub --describe`. | 4 | `hub gui build` and `hub gui test` pass and the Installs screen draws the new workspace |
| 6 | A reader for `sushi-module.toml` and the file in each of the four modules. The catalog becomes the fallback. | 2 | A checkout carrying a manifest is recognised with no catalog entry |
| 7 | `sushidsp` and `sushitrack` gain their own install paths and leave SushiStack's documentation. | 2 | Both repositories stand on their own READMEs, `sd build` and `st build` work |

Waves 6 and 7 run beside the 3-4-5 chain; their file sets are disjoint from it.

## 6. Risks

**Migration.** `sushihub/cli/config.local.toml` holds machine-specific compiler, vcpkg and
oneAPI paths. Wave 3 moves it, so the upgrade leaves the original in place and the new directory
is removable.

**The PyPI names.** Checked on 2026-09-21: `pypi.org/simple/` answers 404 for `sushicore`,
`sushihub`, `sushistack`, `sushiruntime`, `sushiengine`, `sushiai`, `sushiblas`, `sushidsp` and
`sushitrack`, so all nine are free. They are unreserved until the first upload, so wave 1
uploads a placeholder `sushicore` before anything else in that wave.

**The engine's licence path.** Wave 2 rewrites the source-or-binary decision at
`services/modules.py:426`. `tests/test_add_binary.py` already pins it with 18 tests covering the
clone, the out-of-reach fallback, the forced binary, the missing licence, the hash mismatch and
the update path, so the rewrite has something to answer to and wave 0 adds nothing here.
