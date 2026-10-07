# Remaining work

The single backlog of this repository. The programme tables mirror the wave tables of the design
documents so the order can be read from one place; [README.md](README.md) maps each topic to its
document.

## The hub programme

Designed in `HUB.md`; the waves below are its section 9. Each wave names what it waits on, and
waves that wait on the same thing run in parallel. Waves 6 and 7 are open.

| Wave | Work | Waits on |
|---|---|---|
| 0 | Documentation skeleton and the hub design document. Landed 2026-09-05. | nothing |
| 1a-core | `JsonRenderer` and the `table`, `progress`, `result`, `prompt` calls in `sushicore`. Plan: `../archive/agent/plans/2026-09-05-wave-1a-core.md`. Landed 2026-09-05. | 0 |
| 1a-cli | `hub --json` on every command, `hub --describe`, the schemas under `contract/`. Plan: `../archive/agent/plans/2026-09-05-wave-1a-cli.md`. Landed 2026-09-05. | 1a-core, 1b |
| 1c | Move `cli/` to `sushihub/cli/` and repoint the installer, the workspace marker search and the docs. Landed 2026-09-05; lifted back to the repository root on 2026-09-22. | 1a-cli |
| 1b | Dependencies follow the modules (plan: `../archive/agent/plans/2026-09-05-wave-1b-dependencies.md`): `build_pipeline` derives the toolchain selection from the present modules' fragments; `hub add` provisions what the new module needs; `hub doctor` reports by owner in dependency order; the install scripts stop running `hub install` before any module exists. Landed 2026-09-05. | 0 |
| 1d | The command is `hub`, not `ss`, in every repository, and the installers offer `sh` as an interactive alias. Plan: `../archive/agent/plans/2026-09-07-wave-1d-hub-command.md`. Landed 2026-09-07. | 1a-cli |
| 2 | Binary presence read from `sushi-release.json` in `hub status` and everywhere `hub` looks; the marker in `ModuleProfile` (landed 2026-09-05); `hub login`, `hub logout`, `hub whoami`, `hub license` against a fake Sushi Account. Plan: `../archive/agent/plans/2026-09-05-wave-2-presence-and-identity.md`. Landed 2026-09-05. | 1a-cli |
| 3 | Sushi Account, in the sushiweb repository: device authorization grant, a licence query for a product, a signed download URL per release, a runtime licence check. Landed 2026-09-05 on sushiweb's branch `feat/device-grant-and-releases` (`docs/agent/specs/2026-09-05-device-grant-and-releases-design.md` there, three plans), rebased onto sushiweb's `main` on 2026-09-16 with its migrations renumbered to 0034 and 0035, both applied to production with the `releases` bucket; the deploy waits on the account project's JWT and Supabase storage variables, and the end-to-end check on a released engine. | none here |
| 4 | `gui/` (plan: `../archive/agent/plans/2026-09-05-wave-4-gui.md`): the Dear ImGui application, the `hub` subprocess bridge over the JSON contract, hand-drawn screens for status, modules, dependencies, licence and projects, generated forms for the rest. Landed 2026-09-05; built through `hub gui build` (plan: `../archive/agent/plans/2026-09-05-wave-4b-gui-through-ss.md`), first build the user's. | 1a-cli; 2 in parallel |
| 4c | The desktop application's own window (plan: `../archive/agent/plans/2026-09-07-wave-4c-hub-ui.md`): a title bar, a rail of four destinations, one activity strip every run reports through, and the Installs, Modules, Settings and Commands screens. Landed 2026-09-07 and built by the user on 2026-09-15. | 4 |
| 4d | `hub status` reports a checkout's branch and distance from upstream, a binary's platform and licence expiry, and the `sh` alias; `--check-updates` is its one online form; the Installs card draws them. Plan: `../archive/agent/plans/2026-09-15-wave-4d-status-fields.md`. Landed 2026-09-15; the GUI build and `hub gui test` are the user's. | 4c |
| 5 | `hub add sushiengine` chooses source or binary from Git access and licence; downloads, verifies and unpacks the release; writes the licence file. Plan: `../archive/agent/plans/2026-09-05-wave-5-binary-engine.md`. Landed 2026-09-05 against the fake Sushi Account; the real endpoints are wave 3's. The project registry it also built was removed on 2026-09-07, because a project is the engine's concept. | 2, 3 |
| 6 | sushiengine, in its repository: the command set of a binary install; `se editor --project <name>`; the project registry and the start screen that lists it, which the hub no longer owns; the runtime licence client and its offline rule. Its own design document there. | 5 |
| 7 | The install scripts fetch the desktop application; a pass over developer and user experience with both journeys walked end to end. | 4, 6 |

## The decoupling programme

Designed in `WORKSPACE_DECOUPLING.md`; the waves below are its section 5. Waves 0 through 6 landed on 2026-09-22, and wave 7 all but its
`st setup` task; wave 8 is open.

| Wave | Work | Waits on |
|---|---|---|
| 0 | Tests for the five seams the later waves rewrite and today's suite leaves uncovered. Landed 2026-09-22. | nothing |
| 1 | `sushicore` moves to its own repository and publishes to PyPI; the path injection goes. Landed 2026-09-22. | 0 |
| 2 | `ModuleCatalog` and a packaged `catalog.toml`; `sushidsp` and `sushitrack` leave the catalog. Landed 2026-09-22. | 1 |
| 3 | `.sushistack` became a directory holding the workspace's own data in one `workspace.toml`; the defaults and the dependency manifests moved into the package. Landed 2026-09-22. | 2 |
| 4 | The installers drop the clone and take `sushihub` from PyPI. The module CLIs do not publish; they stay editable from a checkout. Landed 2026-09-22. | 3 |
| 5 | `sushicore` left the status table, the fixtures were re-recorded, Linux stopped being pointed at `~/vcpkg`. Landed 2026-09-22. | 4 |
| 6 | `sushi-module.toml` and its reader; the catalog became the fallback. Landed 2026-09-22. | 2 |
| 7 | `sd setup` provisions sushidsp with `hub` or without it, and the fragment reader moved into `sushicore` 0.3.0. Landed 2026-09-22 except `st setup`, deferred until sushitrack's CLI can be tested. | 2 |
| 8 | The desktop application ships as `sushihub-gui`, reached as `pipx install "sushihub[gui]"`. | 5 |

## The standalone programme

Designed 2026-10-04 in the SushiCore repository
(`docs/design/STANDALONE_PROVISIONING.md` there, its plan in the work folder
`docs/agent/2026_10_04_STANDALONE_PROVISIONING/`). Every module CLI gains `setup`, `doctor`, `link` and `unlink` from
`sushicore.provision` and hub stops being a precondition for building a module.

| Wave | Work | State |
|---|---|---|
| 1 | sushicore 0.7.0: the selection rule, the `depends_on` closure, the base fragment, a probe that reads legacy dependency trees. | Landed 2026-10-04, unpublished. |
| 2 | `sd` and `st` take the new `setup` options. | Landed 2026-10-04. |
| 2 | `sr`, `sb`, `sa` and `se` register the four commands. | Landed 2026-10-04. |
| 3 | Hub reads the rule and the base fragment from sushicore; a bare `hub install` installs one SYCL toolchain. | Landed 2026-10-04. |
| 4 | The owner runs the real `setup` and build of each module, then tags and publishes sushicore 0.7.0. | Open. |

`hub migrate`, the command that moves `dependencies/` to a directory the owner names, exists
since 2026-10-07 (`cli/README.md`, "Moving the dependency tree"). It needs sushicore 0.8.0,
which is unpublished. Open: the owner's real run, each module's `doctor` and build after it,
then `hub migrate --finalize` or `--rollback`.

## The documentation site programme

Designed 2026-10-07 in `../agent/2026_10_07_DOCS_SITE/SPEC.md`: a public site at
`docs.sushisystems.io` compiled from the `docs/` trees and Doxygen comments of eight
repositories. The owner approved the design on 2026-10-07.

| # | Work | State |
|---|---|---|
| 1 | The bundle contract and `docs bundle` in SushiCore, proven on sushiruntime. Plan: `docs/agent/2026_10_07_DOCS_BUNDLE/PLAN.md` in the SushiCore repository. | Built 2026-10-07 and proven by `sr docs bundle --release 1.0.0`; SushiCore's release with `docs_bundle` is open, and nothing is pushed. |
| 2 | The site, `apps/docs` in the sushiweb repository. Report: `docs/agent/2026_10_07_DOCS_APP/REPORT.md` there. | Built 2026-10-07 from sushiruntime's bundle; not deployed, and nothing is pushed. |
| 3 | `docs/publish.toml`, Doxygen XML, `docs/guides/FAQ.md` and a release step in each publishing repository. | Open; sushiruntime before 2, the rest after. |

## Outside the programmes

### Command line

- **`hub add <git-url>` is unwritten.** A module can describe itself once its checkout exists,
  but a repository nobody has cloned is still reachable only through the catalog. Wave 6 of the
  decoupling left this out on purpose; whether the catalog should ever open is a separate
  decision.
- **`hub unlink`.** Removing a link means deleting its line from `[modules]` in
  `.sushistack/workspace.toml` by hand (`../guides/LINKING_CHECKOUTS.md`).
- **`hub install-cli` has no test of its own path resolution.**
  `cli/tests/test_cli_install.py` compares the `add` and `install-cli` paths at service level
  with pipx faked; nothing runs `install_cli` in `cli/sushihub/services/cli_install.py` through
  the command.
- **`use_vcpkg` is declared and never read.** `cli/sushihub/defaults.toml` sets it per platform,
  but `sushicore.stack_config.resolved_vcpkg` returns `vcpkg_root` when one is set and the
  provisioned tree otherwise. Reading the key is a change in sushicore that reaches seven CLIs.
- **A `[cli]` theme in `workspace.toml` is not read.** `cli/sushihub/console.py` hands
  sushicore's `LazyConsole` the directory `legacy_cli_dir` returns, and `LazyConsole` appends
  `config.toml` and `config.local.toml` itself. Reaching the workspace file needs sushicore to
  take a file where it takes a directory.
- **The packaged manifests assume an unzipped install.** `dependency_source.manifest_sources`
  returns paths out of an `importlib.resources.as_file` block that the parser opens later. pip
  and pipx install unzipped, so this holds; a zipimported install would not. The fix is to
  return each fragment's text, which changes `IDependencySource`'s shape.
- **A doubled progress line.** `InstallPipeline.run` in `sushicore.provision.pipeline` emits
  `console.progress` beside its Rich progress bar, so a human sees each step twice. The JSON side needs the event; the bar is the
  one to drop.
- **The sign-in code travels as text.** `hub login` prints the user code and the verification
  link as `line` events, and the desktop application scans them by shape
  (`gui/src/ui/screens/DeviceGrant.cpp`). The two fields in the `result` payload, or a
  structured event, would end the scan.
- **Hub's `install`, `doctor` and `link` duplicate what sushicore registers for every module
  CLI** as `setup`, `doctor`, `link` and `unlink`, under other names and options. Whether hub
  takes sushicore's commands is the command line programme's decision.

### GPU

- **Every GPU vendor on a machine, where today it is one.** `detect_gpu_vendor` in
  `sushicore.provision.probe` picks a single vendor, and the registry holds one backend per
  vendor; a machine with an NVIDIA card and an AMD iGPU provisions only CUDA.
  `GPU_BACKEND_PROVISIONING.md` section 3 records the limit.
- **AMD integrated GPUs through SYCL.** Windows has no path: intel/llvm ships no HIP adapter
  there and AMD's OpenCL driver takes no SPIR-V, so `sycl-ls` does not list the 7600X's Radeon
  Graphics. Linux candidates, both unverified: Mesa rusticl, which accepts SPIR-V, and ROCm with
  `HSA_OVERRIDE_GFX_VERSION`.
- **Measure the 7600X iGPU before building for it.** One kernel on the CPU through SYCL and on
  the iGPU through Vulkan compute, timed, decides whether the two-core RDNA2 part is worth a
  backend.
- **GPU backend provisioning on real hardware.** P1 through P4 of `GPU_BACKEND_PROVISIONING.md`
  are built and `hub install` wires the adapter build into both platforms. Neither the default
  GPU component nor the CUDA 12.6.3 silent install on Windows has run on real hardware. R1 in
  SushiRuntime and E1 in SushiEngine are open.

### Sibling repositories

- **`sushiruntime`'s `env.py` repeats `sushicore.build_env`.** The measurement of 2026-09-22
  found it at 188 lines beside SushiTrack's `proc.py` and `env.py`; on 2026-10-05 it is 193
  lines, SushiTrack's `proc.py` is gone and its `env.py` is 74 lines. Plan:
  `../archive/agent/plans/2026-09-22-sushitrack-alignment.md`.
- **Wave 7's `st setup` task is unchecked.** The plan deferred a command that creates
  SushiTrack's conda environment from `environment.yml` until its CLI had tests. On 2026-10-05
  that CLI has a test suite and registers `setup` through `sushicore.provision`, and its
  `cli/sushistack.deps.toml` is still there. Whether the conda step is still wanted was not
  decided. Plan: `../archive/agent/plans/2026-09-22-wave-7-sd-and-st-stand-on-their-own.md`,
  task 3.
- **The consumer contract has no home.** The `consumers` job of `.github/workflows/ci.yml` ran
  the consumer CLIs' suites against the `sushicore` under test, and wave 1 of the decoupling
  deleted it with the package. The same guard belongs in the SushiCore repository, where a
  change can be tested against its consumers before it is tagged, with a token that reads the
  private ones.

### Documentation

- **`contract/sushi-account.md` is stale and misnamed.** It says none of the six endpoints
  exists in sushiweb, names the keyring service `sushistack` where
  `cli/sushihub/services/token_store.py` uses `sushihub`, and calls the package `sushistack`.
  Its lowercase dashed name is the only one of its kind beside the code. The documentation
  programme of 2026-10-05 could write module READMEs only, so the page is untouched but for one
  path.
- **`WORKSPACE_DECOUPLING.md` sections 1 and 3 describe the code of 2026-09-21** with line
  references that no longer resolve. Only wave 8 is open; the document can be cut to that.
- **`HUB.md` still says Sushi ID and `sushihub/cli/`** in its body, the names of 2026-09-05.
- **Paths inside the archived plans and reports** were updated only where they cite a document
  that moved on 2026-10-05; the source paths they cite are those of their own date.
- **Source comment findings.** `python tools/documentation/check_source_comments.py . --report`
  counted 67 on 2026-10-05: 25 file headers, 34 comment runs, 8 separators. The code programme
  owns them.
- **`cli/README.md` and `README.md` call the modules source-available.** The wording follows
  the licence of this repository; each module's own licence decides whether it holds there.

### Layout and continuous integration

- **CI runs no checker and never builds or tests the desktop application.**
  `.github/workflows/ci.yml` installs with pip and calls pytest directly, has no cache step, and
  tests on Python 3.10 where the checkers need 3.11; its `pytest tools/tests` step now collects
  the checker tests on the 3.10 leg too. The workflow changes after the code programme, when
  the source comment checker can pass.
- **The release workflow publishes without testing.** `.github/workflows/release.yml` builds and
  uploads on any `v*` tag, with no test job, no Windows job and no check of the tag against
  `cli/pyproject.toml`. It does not package the desktop application.
- **Root files the layout names are absent:** `.gitattributes`, `.editorconfig`,
  `.clang-format`. Without `.gitattributes` the line endings of `install.sh` follow each
  machine's git configuration.
- **`.gitignore` lacks rules** for `.pytest_cache/`, `dist/`, `.venv/`, `imgui.ini` and
  `CMakeUserPresets.json`, and carries two rules for scratch folders of past sessions.
- **`tools/record_cli_argv.py` sits directly under `tools/`**, where the entry rule is
  `tools/<area>/`.

## Open decisions

- **The folder, the remote and the product disagree.** The checkout is `sushistack`, the remote
  is `SushiHub`, and the same tree is both the SushiHub source and a SushiStack workspace
  (`dependencies/`, `.sushistack/`). Whether the workspace moves out is the owner's call.
- **`gui/`, `contract/` and the root installers depart from the standard tree.** The layout
  places an executable under `applications/`, sources under `source/` in snake_case, and has no
  `contract/` entry. Either the tree moves or the `repository-layout` skill records the
  exception.
- **Whether SushiHub carries a `sushi-module.toml`** like the modules it reads one from. The
  desktop application's dependencies are declared in `cli/sushihub/manifests/gui.deps.toml`.
- **How the desktop application reaches a user.** Wave 8 of the decoupling names a
  `sushihub-gui` distribution; no workflow builds it.
- **v0.2.0 awaits its tag.** The release commit of 2026-10-07 is on `main`; the owner tries
  the hub first, then tags `v0.2.0` and pushes the tag, which publishes it to PyPI.
- **Whether the CUDA and vcpkg entries of `../reference/KNOWN_ISSUES.md` move to SushiCore**,
  which owns the code they describe since 2026-09-23.
- **Whether contributions from outside are accepted**, and under which contributor agreement.
- **Local branches `feature/hub_help_and_doctor` and `feature/theme_tokens`** are merged into
  `main` and exist on no remote; deleting them needs the owner's word.

## Estate programmes

The estate audit of 2026-10-05 (`../agent/2026_10_05_ESTATE_AUDIT/REPORT.md`) opened five
programmes: rules unification in SushiSkills, the licence, the command line, documentation and
layout, and code. The licence migration landed here on 2026-10-05
(`../agent/2026_10_05_LICENCE_MIGRATION/SPEC.md`). Documentation and layout is
`../agent/2026_10_05_DOCS_AND_LAYOUT/SPEC.md`. The defects the audit found that stay open are in
`../reference/KNOWN_ISSUES.md`.
