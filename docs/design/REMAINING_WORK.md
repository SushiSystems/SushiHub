# Remaining work

Status: living backlog, updated as items land or new ones are found.

The single backlog for planned-but-not-built work. The hub programme is designed in
`../agent/specs/2026-09-05-hub-design.md`; the waves below are its §9, kept here so the order can
be read from one place. Items outside the programme follow.

## The hub programme

Each wave names what it waits on. Waves that wait on the same thing run in parallel.

| Wave | Work | Waits on |
|---|---|---|
| 0 | Documentation skeleton and the hub design document. Landed 2026-09-05. | nothing |
| 1a-core | `JsonRenderer` and the `table`, `progress`, `result`, `prompt` calls in `sushicore`. Plan: `../agent/plans/2026-09-05-wave-1a-core.md`. Landed 2026-09-05. | 0 |
| 1a-cli | `hub --json` on every command, `hub --describe`, the schemas under `sushihub/contract/`. Plan: `../agent/plans/2026-09-05-wave-1a-cli.md`. Landed 2026-09-05. | 1a-core, 1b |
| 1c | Move `cli/` to `sushihub/cli/` and repoint the installer, the workspace marker search and the docs. Landed 2026-09-05. | 1a-cli |
| 1b | Dependencies follow the modules (plan: `../agent/plans/2026-09-05-wave-1b-dependencies.md`): `build_pipeline` derives the toolchain selection from the present modules' fragments; `hub add` provisions what the new module needs; `hub doctor` reports by owner in dependency order; the install scripts stop running `hub install` before any module exists. Landed 2026-09-05. | 0 |
| 1d | The command is `hub`, not `ss`, in every repository, and the installers offer `sh` as an interactive alias. Plan: `../agent/plans/2026-09-07-wave-1d-hub-command.md`. Landed 2026-09-07. | 1a-cli |
| 2 | Binary presence read from `sushi-release.json` in `hub status` and everywhere `hub` looks; the marker in `ModuleProfile` (landed 2026-09-05); `hub login`, `hub logout`, `hub whoami`, `hub license` against a fake Sushi Account. Plan: `../agent/plans/2026-09-05-wave-2-presence-and-identity.md`. Landed 2026-09-05. | 1a-cli |
| 3 | Sushi Account, in the sushiweb repository: device authorization grant, a licence query for a product, a signed download URL per release, a runtime licence check. Landed 2026-09-05 on sushiweb's branch `feat/device-grant-and-releases` (`docs/agent/specs/2026-09-05-device-grant-and-releases-design.md` there, three plans), rebased onto sushiweb's `main` on 2026-09-16 with its migrations renumbered to 0034 and 0035, both applied to production with the `releases` bucket; the deploy waits on the account project's JWT and Supabase storage variables, and the end-to-end check on a released engine. | none here |
| 4 | `sushihub/gui/` (plan: `../agent/plans/2026-09-05-wave-4-gui.md`): the Dear ImGui application, the `hub` subprocess bridge over the JSON contract, hand-drawn screens for status, modules, dependencies, licence and projects, generated forms for the rest. Landed 2026-09-05; built through `hub gui build` (plan: `../agent/plans/2026-09-05-wave-4b-gui-through-ss.md`), first build the user's. | 1a-cli; 2 in parallel |
| 4c | The desktop application's own window (plan: `../agent/plans/2026-09-07-wave-4c-hub-ui.md`): a title bar, a rail of four destinations, one activity strip every run reports through, and the Installs, Modules, Settings and Commands screens. Landed 2026-09-07 and built by the user on 2026-09-15. | 4 |
| 4d | `hub status` reports a checkout's branch and distance from upstream, a binary's platform and licence expiry, and the `sh` alias; `--check-updates` is its one online form; the Installs card draws them. Plan: `../agent/plans/2026-09-15-wave-4d-status-fields.md`. Landed 2026-09-15; the GUI build and `hub gui test` are the user's. | 4c |
| 5 | `hub add sushiengine` chooses source or binary from Git access and licence; downloads, verifies and unpacks the release; writes the licence file. Plan: `../agent/plans/2026-09-05-wave-5-binary-engine.md`. Landed 2026-09-05 against the fake Sushi Account; the real endpoints are wave 3's. The project registry it also built was removed on 2026-09-07, because a project is the engine's concept. | 2, 3 |
| 6 | sushiengine, in its repository: the command set of a binary install; `se editor --project <name>`; the project registry and the start screen that lists it, which the hub no longer owns; the runtime licence client and its offline rule. Its own design document there. | 5 |
| 7 | The install scripts fetch the desktop application; a pass over developer and user experience with both journeys walked end to end. | 4, 6 |

## The decoupling programme

Designed in `WORKSPACE_DECOUPLING.md`; the waves below are its §5, kept here so the order can be
read from one place. Waves 0 through 5 landed on 2026-09-22; waves 6, 7 and 8 are open.

| Wave | Work | Waits on |
|---|---|---|
| 0 | Tests for the five seams the later waves rewrite and today's suite leaves uncovered. Landed 2026-09-22. | nothing |
| 1 | `sushicore` moves to its own repository and publishes to PyPI; the path injection goes. Landed 2026-09-22. | 0 |
| 2 | `ModuleCatalog` and a packaged `catalog.toml`; `sushidsp` and `sushitrack` leave the catalog. Landed 2026-09-22. | 1 |
| 3 | `.sushistack` became a directory holding the workspace's own data in one `workspace.toml`; the defaults and the dependency manifests moved into the package. Landed 2026-09-22. | 2 |
| 4 | The installers drop the clone and take `sushihub` from PyPI. The module CLIs do not publish; they stay editable from a checkout. Landed 2026-09-22. | 3 |
| 5 | `sushicore` left the status table, the fixtures were re-recorded, Linux stopped being pointed at `~/vcpkg`. Landed 2026-09-22. | 4 |
| 6 | `sushi-module.toml` and its reader; the catalog becomes the fallback. Plan: `../agent/plans/2026-09-22-wave-6-a-module-describes-itself.md`. | 2 |
| 7 | `sd setup` and `st setup` provision their repositories, with `hub` or without it; the fragment reader moves into `sushicore`. Plan: `../agent/plans/2026-09-22-wave-7-sd-and-st-stand-on-their-own.md`. | 2 |
| 8 | The desktop application ships as `sushihub-gui`, reached as `pipx install "sushihub[gui]"`. | 5 |

## Outside the programme

- **`use_vcpkg` is declared and never read.** `defaults.toml` sets `use_vcpkg = false` for Linux,
  but `sushicore.stack_config.resolved_vcpkg` never consults it: it returns `vcpkg_root` when one
  is set, else the provisioned tree. The Linux default that made this harmful, `~/vcpkg`, was
  deleted on 2026-09-22, so what is left is tidiness: a key that means nothing until
  `resolved_vcpkg` reads it, in a change that reaches seven CLIs.
- **An install from PyPI has no desktop application.** `hub gui build` and `hub gui run` build
  `sushihub/gui`, which only a clone of this repository carries, and the installers no longer
  clone. A user who wants the application clones by hand today. Wave 5 owns how it is
  distributed.
- **A `[cli]` theme in `workspace.toml` is not read.** `console.py` hands sushicore's
  `LazyConsole` a directory, and `LazyConsole` appends `config.toml` and `config.local.toml`
  itself. The override still works from its old location; reaching the new file needs sushicore
  to take a file rather than a directory.
- **The packaged manifests assume an unzipped install.** `dependency_source.manifest_sources`
  returns paths out of an `importlib.resources.as_file` block that the parser opens later. pip
  and pipx install unzipped, so this holds; a zipimported install would not. The fix is to
  return each fragment's text, which changes `IDependencySource`'s shape.
- **`hub status` reports sushicore as a module.** `sushicore` is a PyPI dependency, not a linked
  module, yet it still takes a row in the status table and shows as missing. Wave 5 decides what a
  non-module row should say; until then the row lies.
- **`hub install-cli` has no test.** The command installs a module's CLI through
  `services/pipx.py`, which is tested, but nothing covers the command's own path resolution.
- **Every GPU vendor on a machine, not one.** `probe.detect_gpu_vendor` still picks a single
  vendor, and the registry holds one backend per vendor; a machine with an NVIDIA card and an AMD
  iGPU provisions only CUDA. `GPU_BACKEND_PROVISIONING.md` §3 records the limit.
- **AMD integrated GPUs through SYCL.** Windows has no path: intel/llvm ships no HIP adapter there
  and AMD's OpenCL driver takes no SPIR-V, so `sycl-ls` does not list the 7600X's Radeon Graphics.
  Linux candidates, both unverified: Mesa rusticl, which accepts SPIR-V, and ROCm with
  `HSA_OVERRIDE_GFX_VERSION`.
- **Measure the 7600X iGPU before building for it.** One kernel on the CPU through SYCL and on the
  iGPU through Vulkan compute, timed, decides whether the two-core RDNA2 part is worth a backend.
- **GPU backend provisioning.** One brick per vendor and one branch per operating system, CUDA on
  Windows first, ROCm and Level Zero declared empty. Design: `GPU_BACKEND_PROVISIONING.md`; P1
  through P4 are built and `hub install` wires the adapter build into both platforms. The GPU
  component is on by default and Windows installs CUDA 12.6.3 through NVIDIA's silent installer,
  but neither has run on real hardware yet. R1 in SushiRuntime and E1 in SushiEngine are open.
- **The sign-in code travels as text.** `hub login` prints the user code and the verification link as
  `line` events; the desktop application scans them by shape (`sushihub/gui/src/ui/DeviceGrant.cpp`).
  A `prompt`-like structured event, or the two fields in the `result` payload, would end the scan.
- **GUI fixtures are hand-written.** `sushihub/gui/tests/fixtures/` awaits one recorded `hub --json status`
  and `hub --describe` run; the README there gives the two commands.

- **A doubled progress line.** `InstallPipeline.run` emits `console.progress` beside its Rich progress bar, so a
  human sees each step twice. One of the two should go; the JSON side needs the event.

- **A source-comment checker.** Every repository carries `tools/documentation/check_source_comments.py`
  to hold the docstring rules in `../CONTRIBUTING.md`. This one does not yet.
- **The consumer contract has no home.** `.github/workflows/ci.yml`'s `consumers` job ran the five
  consumer CLIs' suites against the `sushicore` under test. Wave 1 deleted it with the package. It
  had been broken since 2026-09-07 in one way and since it was written in another: it ran `pytest
  sushihub/cli/tests` inside checkouts that hold `cli/tests`, and it checked the consumers out
  assuming they are public, which all five are not. The same guard belongs in the SushiCore
  repository, where a change can be tested against its consumers before it is tagged, with a token
  that reads the private ones.

- **`hub install-cli` has no test.** Wave 1 removed its `sushicore` lookup and pipx injection
  (`sushihub/cli/sushistack/services/cli_install.py`) with nothing covering the command. The
  removal was found by reading, not by a failing test: `hub install-cli` would have hard-failed
  on every module once `sushicore/` was deleted. The service needs fakes for pipx and
  `module_dest` the way `tests/test_cli_install.py` fakes them for `_install_module_cli`.
- **`hub unlink`.** Removing a link means editing `sushihub/cli/modules.local.toml` by hand
  (`../guides/LINKING_CHECKOUTS.md`).
