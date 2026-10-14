# Known issues

Two kinds of entry. The table lists defects in this repository that are recorded and not yet
fixed, each with where it sits; the estate audit of 2026-10-05 found them and each was checked
against the tree that day, except the two about PyPI and the remote, which rest on the audit's
own lookup. The sections after it record failures that are a toolchain's, a
package manager's or a vendor's doing, each with the symptom, the cause and the rule, so the
next person recognises one where they would otherwise diagnose it again. Each module keeps its
own page for failures inside its build.

## Open defects

| Issue | Where |
| --- | --- |
| A checkout of `main` cannot install `hub` from PyPI: it requires `sushicore>=0.7.0`, and 0.7.0 is unpublished | `cli/pyproject.toml` |
| v0.2.0 has its release commit of 2026-10-07 and no tag yet, so it is not published; PyPI serves 0.1.0 | git, `docs/reference/CHANGELOG.md` |
| `hub status` reports the channel `editable` for an install from PyPI; the schema allows only `editable` and `frozen` | `cli/sushihub/services/hub_install.py`, `contract/status.schema.json` |
| git and pipx inherit `hub`'s stdout, so under `--json` their plain text lands in the event stream | `cli/sushihub/services/git_ops.py`, `cli/sushihub/services/pipx.py`, `cli/sushihub/services/cli_install.py` |
| `hub install --customize` decides on `sys.stdin.isatty()` alone and opens its picker under `--json` on a terminal | `cli/sushihub/services/customize.py` |
| `hub --json` with no subcommand prints the help text to stdout and no `result` event | `cli/sushihub/cli.py` |
| The module readiness report of `hub doctor` is written through the raw Rich console, outside the event stream | `cli/sushihub/setup/steps.py` |
| The desktop application never reads the child's stderr, so a traceback from `hub` and the readiness report never reach the window | `gui/src/bridge/Process.cpp` |
| The `[cli]` theme is read from `<workspace>/sushihub/cli/`, a directory only a workspace made before 2026-09-22 has | `cli/sushihub/console.py`, `legacy_cli_dir` in `cli/sushihub/config.py` |
| `hub gui build`, `test`, `run` and `clean` are listed for every user and work only when the workspace root is a clone of this repository | `cli/sushihub/gui_config.py` |
| The tool overrides are named `SR_*` after sushiruntime, 22 mentions in one file | `cli/sushihub/config.py` |
| `hub status` looks for the `sh` alias in four fixed profile paths and reports none when the PowerShell profile is under a redirected Documents folder | `cli/sushihub/services/hub_install.py` |
| A module `pyproject.toml` without `[project] name` ends `hub install-cli` in a `KeyError` | `cli/sushihub/services/pipx.py` |
| `discovery.py` is imported by nothing | `cli/sushihub/services/discovery.py` |
| Neither the CLI nor the desktop application has a logger | `cli/sushihub/`, `gui/src/` |
| `contract/sushi-account.md` says the six endpoints do not exist in sushiweb and names the keyring service `sushistack`; the code uses `sushihub` | `contract/sushi-account.md`, `cli/sushihub/services/token_store.py` |
| The archived v0.1.0 changelog cites `docs/agent/specs/2026-09-05-hub-design.md`, which is now `docs/design/HUB.md`, and has one entry of 246 characters | `docs/archive/changelog/v0.1.0.md` |
| `check_docs_layout.py` reports `docs/CLAUDE.md`, which waits for the owner to move it to the root, and one line of the audit report that reads as a link | `docs/CLAUDE.md`, `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md` |

The audit's code-shape findings that are work and not a failure a user meets are in
`docs/design/REMAINING_WORK.md` and in the audit report itself.

## A toolkit release chosen elsewhere breaks Pascal builds far from the cause

**Symptom.** A CUDA 13 toolkit on a Pascal machine: `nvcc --version` succeeds, `hub doctor`
reports the toolkit present, and the CMake configure passes. The build then fails in the ptxas
link step with an unknown-architecture error for `sm_61`.

**Cause.** CUDA 13 removed `sm_6x`. SushiCore chooses the release from the machine's cards, so
it gives a Pascal machine a 12.x toolkit on its own (sushicore's
`docs/design/CUDA_TOOLKIT_SELECTION.md`). The failure comes back when the choice is bypassed:
`SUSHISYSTEMS_CUDA_RELEASE` set to 13.x, a `CUDA_PATH` pointed at another toolkit, or an
`SR_CUDA_ARCH` that names a card the machine does not have.

**Rule.** For a build that must target a card absent from the machine, set
`SUSHISYSTEMS_CUDA_RELEASE` to a release whose `nvcc --list-gpu-arch` lists it. A passing
`nvcc --version` proves nothing here.

## Changing a vcpkg port's feature set needs `--recurse`, which `hub install` cannot pass

**Symptom.** A manifest changes a port's features, for example `sdl2` to `sdl2[vulkan]` in
`sushiengine/cli/sushistack.deps.toml`. `hub install` then fails at the vcpkg step: vcpkg refuses
to rebuild the already-installed port with different features and asks for `--recurse`.

**Cause.** vcpkg treats a feature change on an installed port as a removal plus a reinstall of
everything depending on it, and only does that when told to with `--recurse`. `VcpkgManager.install`
in sushicore's `sushicore/provision/packages/vcpkg.py` runs a plain `vcpkg install <port>:<triplet>` with
no way to add that flag, and no `hub install` option exposes it.

**Rule.** After a feature-set change, run the install once by hand with the workspace's vcpkg
(`hub home` prints the `dependencies/` path; the root is `vcpkg_root` in `.sushistack/workspace.toml` when
set):

```
<dependencies>/vcpkg/vcpkg install sdl2[vulkan]:x64-windows --recurse
```

Then rerun `hub install`; vcpkg's list output now carries the featured port, so the check passes.
Do not remove the plain port to work around it; `--recurse` is the supported path.

## The runtime, engine and CI lanes build against different SYCL toolchains

**Symptom.** A SYCL-level behaviour that holds on a developer's machine fails in CI, or the other
way round, with no change in the code under test.

**Cause.** Three different SYCL toolchains are in use. `hub install` downloads the newest
intel/llvm nightly bundle at the time it runs (`install_intel_llvm` in sushicore's
`sushicore/provision/toolchains/intel_llvm.py`), and the install is then reused forever unless
`--refresh-toolchains` is given, so two developer machines can differ from one another. The
engine's CI job pins a specific nightly by date (`INTEL_LLVM_DATE` in
`sushiengine/.github/workflows/ci.yml`). The runtime's CI job builds inside
`intel/oneapi-basekit:latest` with Intel's packaged `icpx`, a separate libsycl build again.
Runtime and header behaviour differs between these builds in ways the SYCL specification leaves
open, such as whether a particular call allocates.

**Rule.** A contract stated at the SYCL level (allocation freedom, ordering, what a runtime call
may do) is not proven by a local run. It needs CI proof on the lane that ships it, and a claim
that holds on one lane must say which one.

## The command was `ss`, and is now `hub`

**Symptom.** Documentation and scripts predating this entry call the workspace command `ss`.

**Cause.** `ss` is not free to claim: iproute2 ships `/usr/bin/ss` on every Linux distribution, so
the workspace command shadowed a system tool of the same name on every machine that had one.

**Rule.** The command is `hub`. The installer offers `sh` as an optional interactive alias for
typing, which changes typing only and leaves `/bin/sh` untouched.
