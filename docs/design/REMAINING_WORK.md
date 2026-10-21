# Remaining work

Next id: RW-57

## Decisions waiting for the owner

### RW-1 Decide whether the workspace moves out of this checkout
- State: decision
- Done when: the owner has ruled whether the tree stays both the SushiHub source and a SushiStack
  workspace; the checkout is `sushistack`, the remote `SushiHub`

### RW-2 Decide the layout of `gui/`, `contract/` and the installers
- State: decision
- Done when: the tree follows the `repository-layout` skill, or the skill records the exception

### RW-3 Decide whether SushiHub carries a `sushi-module.toml`
- State: decision
- Done when: the owner has ruled; the desktop application's dependencies are in
  `cli/sushihub/manifests/gui.deps.toml`

### RW-4 Decide how the desktop application reaches a user
- State: decision
- Done when: the owner has chosen how `sushihub-gui` is built and distributed
- Source: `docs/design/WORKSPACE_DECOUPLING/README.md`

### RW-5 Tag v0.2.0
- State: decision
- Done when: the owner has tried the hub and tagged `v0.2.0`, which publishes it to PyPI

### RW-6 Decide where the toolchain known issues live
- State: decision
- Done when: the CUDA and vcpkg entries of the known issues stay here or move to sushicore, which
  owns the code they describe

### RW-7 Decide whether contributions from outside are accepted
- State: decision
- Done when: the owner has named a contributor agreement, or ruled contributions out

### RW-8 Decide whether hub takes sushicore's commands
- State: decision
- Done when: hub's `install`, `doctor` and `link` are sushicore's `setup`, `doctor`, `link` and
  `unlink`, or the owner keeps them apart

### RW-9 Decide whether the catalog opens to any Git URL
- State: decision
- Done when: the owner has ruled whether `hub add <git-url>` reaches a repository nobody has
  cloned

## Programmes

### RW-11 Close wave 6 of the hub programme
- State: blocked
- Blocked by: sushiengine RW-305
- Done when: the engine's side of a binary install is built
- Source: `docs/design/HUB/README.md`

### RW-12 Ship the desktop application through the installers, wave 7
- State: blocked
- Blocked by: RW-11, RW-4
- Done when: the install scripts fetch the desktop application and both journeys are walked end
  to end

### RW-13 Deploy the account side of the hub, wave 3
- State: blocked
- Blocked by: sushiweb RW-34
- Done when: the account project has its JWT and Supabase storage variables, and the end-to-end
  check passes on a released engine

### RW-14 Ship the desktop application as `sushihub-gui`, decoupling wave 8
- State: blocked
- Blocked by: RW-4
- Done when: `pipx install "sushihub[gui]"` installs it
- Source: `docs/design/WORKSPACE_DECOUPLING/README.md`

### RW-15 Close the standalone programme
- State: blocked
- Blocked by: sushicore RW-8, sushicore RW-9
- Done when: each module's real `setup` and build has run on the standalone layout, and the hub
  root migration has run for real and been finalized or rolled back

### RW-16 Close the documentation site programme
- State: open
- Done when: every publisher attaches its bundle to its release, the site is deployed, the
  owner's two decisions and the deferred findings of the rollout report are settled, the engine
  has its FAQ, and the repositories are pushed in the report's order
- Source: `docs/agent/2026_10_07_DOCS_ROLLOUT/REPORT.md`

The site's deploy is `sushiweb RW-1`; each command line registers the `docs` group.

### RW-17 Settle the command lines as one surface
- State: open
- Done when: every Sushi command line uses the same panel names, short options and defaults, and
  `sr`, `se`, `sa`, `sb`, `sd` and `st` have adopted `help_group` (command line C5, C6)

### RW-18 Run the estate programmes
- State: open
- Done when: the licence, command line, documentation and layout, and code programmes the estate
  audit of 2026-10-05 opened are closed in every repository

Rules unification, the first programme, is SushiSkills' and has shipped.

## Command line

### RW-21 Add `hub add <git-url>`
- State: blocked
- Blocked by: RW-9
- Done when: a repository nobody has cloned can be added by its URL

### RW-22 Add `hub unlink`
- State: open
- Done when: a link leaves `[modules]` of `.sushistack/workspace.toml` without a hand edit

### RW-23 Test `install-cli` through the command
- State: open
- Done when: a test runs `install_cli` in `cli/sushihub/services/cli_install.py` through `hub`

### RW-24 Read `use_vcpkg`
- State: blocked
- Blocked by: sushicore RW-51
- Done when: the key `cli/sushihub/defaults.toml` sets per platform decides the vcpkg tree

### RW-25 Read the `[cli]` theme from the workspace
- State: blocked
- Blocked by: sushicore RW-52
- Done when: `cli/sushihub/console.py` reads the theme from `workspace.toml`, not from the
  directory `legacy_cli_dir` returns
- Where: `cli/sushihub/console.py`, `cli/sushihub/config.py`

The `[cli]` theme is read from a directory few workspaces have. A theme set in the workspace has no
effect. Cause: `legacy_cli_dir` points at `<workspace>/sushihub/cli/`, which only a workspace made
before 2026-09-22 has.

### RW-26 Return each packaged manifest's text
- State: open
- Done when: `manifest_sources` in `cli/sushihub/setup/dependency_source.py` returns text, not a
  path out of an `importlib.resources.as_file` block, so a zipimported install works

The change reaches sushicore's `IDependencySource`.

### RW-28 Send the sign-in code as data
- State: open
- Done when: `hub login` puts the user code and the verification link in its `result` payload or
  a structured event, and `gui/src/ui/screens/DeviceGrant.cpp` stops scanning text

### RW-43 Report the install channel of a PyPI install
- State: open
- Done when: `hub status` says what a PyPI install is, and `contract/status.schema.json` allows it
- Where: `cli/sushihub/services/hub_install.py`, `contract/status.schema.json`

`hub status` reports the channel `editable` for a PyPI install. An install from PyPI reads as
editable. Cause: the schema allows only `editable` and `frozen`.

### RW-44 Keep git's and pipx's output out of the event stream
- State: open
- Done when: under `--json` no child process writes to `hub`'s stdout

### RW-45 Keep `--customize` from opening its picker under `--json`
- State: open
- Done when: the picker checks the output mode as well as the terminal

### RW-46 End `hub --json` with no subcommand in a `result` event
- State: open
- Done when: it prints events, not the help text

### RW-47 Send the readiness report of `hub doctor` as events
- State: open
- Done when: `cli/sushihub/setup/steps.py` writes no raw Rich output
- Where: `cli/sushihub/setup/steps.py`

The readiness report of `hub doctor` bypasses the event stream. Drawn text in a JSON run. Cause: it
is written through the raw Rich console.

### RW-48 Read the child's stderr in the desktop application
- State: open
- Done when: `gui/src/bridge/Process.cpp` shows a traceback and the readiness report in the window

### RW-49 List the GUI commands only in a clone of this repository
- State: open
- Done when: `hub gui build`, `test`, `run` and `clean` are listed where they work

### RW-50 Name the tool overrides after the hub
- State: open
- Done when: no override in `cli/sushihub/config.py` is named `SR_*`

### RW-51 Find the `sh` alias under a redirected Documents folder
- State: open
- Done when: `hub status` reads the PowerShell profile path from the system, not four fixed paths
- Where: `cli/sushihub/services/hub_install.py`

`hub status` misses the `sh` alias under a redirected Documents folder. `sh` works and the status
reports no alias. Cause: it looks in four fixed profile paths.

### RW-52 Refuse a module `pyproject.toml` without a name cleanly
- State: open
- Done when: `hub install-cli` reports the missing `[project] name` instead of a `KeyError`

### RW-53 Remove `discovery.py`
- State: open
- Done when: `cli/sushihub/services/discovery.py`, imported by nothing, is gone
- Where: `cli/sushihub/services/discovery.py`

`discovery.py` is imported by nothing. No import names it. Cause: its callers left.

### RW-54 Give the command line and the desktop application a logger
- State: open
- Done when: both log through the `logging` skill's interface
- Where: `cli/sushihub`, `gui/src`

Neither the command line nor the desktop application has a logger. A failure leaves no record.
Cause: none was written.

## GPU

### RW-30 Find a SYCL path to AMD integrated GPUs
- State: open
- Done when: Mesa rusticl or ROCm with `HSA_OVERRIDE_GFX_VERSION` is tried on Linux, or ruled out;
  Windows has no path today
- Source: `docs/design/GPU_BACKEND_PROVISIONING/README.md`

### RW-31 Measure the 7600X's integrated GPU
- State: unmeasured
- Done when: one kernel timed on the CPU through SYCL and on the iGPU through Vulkan compute shows
  whether the part is worth a backend

### RW-32 Prove GPU backend provisioning on real hardware
- State: blocked
- Blocked by: sushicore RW-12, sushicore RW-14, sushiruntime RW-63, sushiengine RW-306
- Done when: a CUDA 13 build, a ROCm install and build on an AMD card, R1's acceptance in the
  runtime and E1's in the engine have each passed
- Source: `docs/design/GPU_BACKEND_PROVISIONING/README.md`


## Documentation

### RW-33 Correct `contract/sushi-account.md`
- State: open
- Done when: the page says which endpoints sushiweb has, names the keyring service `sushihub`
  and the package `sushihub`, and carries an `UPPER_SNAKE_CASE` name

### RW-34 Cut the decoupling design to wave 8
- State: open
- Done when: sections 1 and 3, which describe the code of 2026-09-21, are gone
- Source: `docs/design/WORKSPACE_DECOUPLING/README.md`

### RW-35 Close the source comment findings
- State: open
- Done when: `tools/documentation/check_source_comments.py` reports none here; 67 on 2026-10-05

### RW-36 State each module's licence in the READMEs
- State: open
- Done when: `cli/README.md` and `README.md` call a module source-available only where its own
  licence says so

## Layout and continuous integration

### RW-37 Run the checkers and the desktop application in CI
- State: open
- Done when: `.github/workflows/ci.yml` runs the checkers, builds and tests `gui/`, caches its
  installs and tests on 3.11

### RW-38 Gate the release on the tests
- State: open
- Done when: `.github/workflows/release.yml` publishes only after the tests and a Windows job
  pass, checks the tag against `cli/pyproject.toml` and packages the desktop application

### RW-39 Add the root files the layout names
- State: open
- Done when: `.gitattributes`, `.editorconfig` and `.clang-format` exist; `install.sh` keeps its
  line endings on every machine

### RW-40 Finish the ignore rules
- State: open
- Done when: `.gitignore` names `.pytest_cache/`, `dist/`, `.venv/`, `imgui.ini` and
  `CMakeUserPresets.json`, and drops the two rules for old scratch folders

### RW-41 Move `record_cli_argv.py` into an area
- State: open
- Done when: `tools/record_cli_argv.py` sits under `tools/<area>/`

### RW-42 Take the whole shared tool set
- State: open
- Done when: `tools/` holds SushiSkills' checkers and `tools/check_all.py` passes

The backlog migration took the checking frame, `check_docs_layout.py` and `check_backlog.py`;
the older checkers still run on `tools/common/`.

## Documentation architecture

### RW-55 Write the About line of each design topic by hand
- State: open
- Done when: each topic has an `**About:**` line of one sentence written for a cold reader

The topic model generated the lines from the first sentence of each document or from its title.

### RW-56 Turn the whole shared gate green
- State: open
- Done when: `python tools/check_all.py .` reports nothing on a clean checkout

sushistack never ran the whole shared gate before the topic model copied the shared tools in. `check_source_comments.py` reports 169 646 findings, most of them under `dependencies/vcpkg`, which it should not read; `check_docs_truth.py` reports 37 and `check_test_sizes.py` 356.
