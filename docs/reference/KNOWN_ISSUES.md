# Known issues

Next id: KI-21

## Release

### KI-1 v0.2.0 has its release commit and no tag
- Origin: own
- Where: `cli/pyproject.toml`, `docs/reference/CHANGELOG.md`
- Cause: the owner tries the hub before tagging
- Recognise: the package declares 0.2.0; PyPI serves 0.1.0
- Workaround: install from a checkout
- Fix: RW-5

## Machine output

### KI-3 Under `--json`, git and pipx write into the event stream
- Origin: own
- Where: `cli/sushihub/services/git_ops.py`, `cli/sushihub/services/pipx.py`,
  `cli/sushihub/services/cli_install.py`
- Cause: the children inherit `hub`'s stdout
- Recognise: lines that are not JSON among the events
- Workaround: skip lines that do not parse as JSON
- Fix: RW-44

### KI-4 `hub install --customize` opens its picker under `--json`
- Origin: own
- Where: `cli/sushihub/services/customize.py`
- Cause: it decides on `sys.stdin.isatty()` alone
- Recognise: a picker on a terminal during a JSON run
- Workaround: leave `--customize` out under `--json`
- Fix: RW-45

### KI-5 `hub --json` with no subcommand prints help text
- Origin: own
- Where: `cli/sushihub/cli.py`
- Cause: the help path ignores the output mode
- Recognise: plain help on stdout and no `result` event
- Workaround: name a subcommand
- Fix: RW-46

### KI-7 The desktop application never reads the child's stderr
- Origin: own
- Where: `gui/src/bridge/Process.cpp`
- Cause: the bridge reads stdout alone
- Recognise: a traceback from `hub` and the readiness report never reach the window
- Workaround: run the command in a terminal
- Fix: RW-48

## Commands

### KI-9 The GUI commands are listed where they do not work
- Origin: own
- Where: `cli/sushihub/gui_config.py`
- Cause: `hub gui build`, `test`, `run` and `clean` assume the workspace root is a clone of this
  repository
- Recognise: the commands fail in any other workspace
- Workaround: run them from a clone
- Fix: RW-49

### KI-10 The tool overrides are named after sushiruntime
- Origin: own
- Where: `cli/sushihub/config.py`
- Cause: 22 mentions of `SR_*` in one file
- Recognise: a hub setting spelled with the runtime's prefix
- Workaround: use the names as they are
- Fix: RW-50

### KI-12 A module `pyproject.toml` without a name ends `install-cli` in a `KeyError`
- Origin: own
- Where: `cli/sushihub/services/pipx.py`
- Cause: `[project] name` is read without a check
- Recognise: a traceback ending in `KeyError: 'name'`
- Workaround: give the module a name
- Fix: RW-52

## Source and documentation

### KI-15 The account contract page is out of date and misnamed
- Origin: own
- Where: `contract/sushi-account.md`, `cli/sushihub/services/token_store.py`
- Cause: it says the six endpoints do not exist in sushiweb and names the keyring service
  `sushistack`; the code uses `sushihub`
- Recognise: the page and `token_store.py` disagree
- Workaround: trust the code
- Fix: RW-33

## Toolchains

### KI-17 A CUDA 13 toolkit breaks a Pascal build far from the cause
- Origin: toolchain
- Cause: CUDA 13 removed `sm_6x`; sushicore picks 12.x for a Pascal machine, but
  `SUSHISYSTEMS_CUDA_RELEASE`, a `CUDA_PATH` to another toolkit or an `SR_CUDA_ARCH` naming an
  absent card bypasses the choice
- Recognise: `nvcc --version`, `hub doctor` and the configure pass; ptxas fails on `sm_61`
- Workaround: set `SUSHISYSTEMS_CUDA_RELEASE` to a release whose `nvcc --list-gpu-arch` lists the
  card

### KI-18 Changing a vcpkg port's features needs `--recurse`, which `hub install` cannot pass
- Origin: dependency
- Cause: vcpkg rebuilds a port with new features only with `--recurse`, and sushicore's
  `VcpkgManager.install` runs a plain install with no way to add it
- Recognise: after a manifest changes, say, `sdl2` to `sdl2[vulkan]`, the vcpkg step refuses and
  asks for `--recurse`
- Workaround: run `<dependencies>/vcpkg/vcpkg install sdl2[vulkan]:x64-windows --recurse` once,
  then `hub install` again; `hub home` prints the folder

### KI-19 The runtime, the engine and CI build against different SYCL toolchains
- Origin: toolchain
- Cause: `hub install` takes the newest intel/llvm nightly and reuses it, the engine's CI pins a
  nightly by date, and the runtime's CI uses Intel's packaged `icpx`
- Recognise: SYCL behaviour that holds locally fails in CI, or the other way round
- Workaround: prove a SYCL-level contract on the CI lane that ships it, and say which lane

### KI-20 iproute2's `ss` shadows a workspace command of that name
- Origin: dependency
- Cause: every Linux distribution ships `/usr/bin/ss`
- Recognise: an old script or page that calls the workspace command `ss`
- Workaround: the command is `hub`; the installer offers `sh` as an interactive alias
