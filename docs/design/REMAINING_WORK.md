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
| 1a-cli | `ss --json` on every command, `ss --describe`, the schemas under `sushihub/contract/`. Plan: `../agent/plans/2026-09-05-wave-1a-cli.md`. Landed 2026-09-05. | 1a-core, 1b |
| 1c | Move `cli/` to `sushihub/cli/` and repoint the installer, the workspace marker search and the docs. Landed 2026-09-05. | 1a-cli |
| 1b | Dependencies follow the modules (plan: `../agent/plans/2026-09-05-wave-1b-dependencies.md`): `build_pipeline` derives the toolchain selection from the present modules' fragments; `ss add` provisions what the new module needs; `ss doctor` reports by owner in dependency order; the install scripts stop running `ss install` before any module exists. Landed 2026-09-05. | 0 |
| 2 | Binary presence read from `sushi-release.json` in `ss status` and everywhere `ss` looks; the marker in `ModuleProfile` (landed 2026-09-05); `ss login`, `ss logout`, `ss whoami`, `ss license` against a fake Sushi ID. Plan: `../agent/plans/2026-09-05-wave-2-presence-and-identity.md`. Landed 2026-09-05. | 1a-cli |
| 3 | Sushi ID, in the sushiweb repository: device authorization grant, a licence query for a product, a signed download URL per release, a runtime licence check. Landed 2026-09-05 on sushiweb's branch `feat/device-grant-and-releases` (`docs/agent/specs/2026-09-05-device-grant-and-releases-design.md` there, three plans), awaiting merge and a database to run the migrations against. | none here |
| 4 | `sushihub/gui/` (plan: `../agent/plans/2026-09-05-wave-4-gui.md`): the Dear ImGui application, the `ss` subprocess bridge over the JSON contract, hand-drawn screens for status, modules, dependencies, licence and projects, generated forms for the rest. Landed 2026-09-05; built through `ss gui build` (plan: `../agent/plans/2026-09-05-wave-4b-gui-through-ss.md`), first build the user's. | 1a-cli; 2 in parallel |
| 5 | `ss add sushiengine` chooses source or binary from Git access and licence; downloads, verifies and unpacks the release; writes the licence file; `ss projects`. Plan: `../agent/plans/2026-09-05-wave-5-binary-engine.md`. Landed 2026-09-05 against the fake Sushi ID; the real endpoints are wave 3's. | 2, 3 |
| 6 | sushiengine, in its repository: the command set of a binary install; `se editor --project <name>`; the runtime licence client and its offline rule. Its own design document there. | 5 |
| 7 | The install scripts fetch the desktop application; a pass over developer and user experience with both journeys walked end to end. | 4, 6 |

## Outside the programme

- **The sign-in code travels as text.** `ss login` prints the user code and the verification link as
  `line` events; the desktop application scans them by shape (`sushihub/gui/src/ui/DeviceGrant.cpp`).
  A `prompt`-like structured event, or the two fields in the `result` payload, would end the scan.
- **GUI fixtures are hand-written.** `sushihub/gui/tests/fixtures/` awaits one recorded `ss --json status`
  and `ss --describe` run; the README there gives the two commands.

- **A doubled progress line.** `InstallPipeline.run` emits `console.progress` beside its Rich progress bar, so a
  human sees each step twice. One of the two should go; the JSON side needs the event.

- **A source-comment checker.** Every repository carries `tools/documentation/check_source_comments.py`
  to hold the docstring rules in `../CONTRIBUTING.md`. This one does not yet.
- **A test suite for `ss`.** `sushicore` has 44 tests and a CI job; `cli/` has none. Wave 1a adds
  the contract tests; the existing commands deserve coverage of their own before that wave moves
  them.
- **`ss unlink`.** Removing a link means editing `sushihub/cli/modules.local.toml` by hand
  (`../guides/LINKING_CHECKOUTS.md`).
- **`sushicore`'s README placement.** The component's facts live in `sushicore/docs/README.md`
  rather than `sushicore/README.md`, the shape every other component follows. Moving it touches
  the other five repositories' documentation links.
