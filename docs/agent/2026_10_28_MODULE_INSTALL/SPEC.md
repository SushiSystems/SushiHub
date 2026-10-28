# Two equal ways into every module

**Status:** Open — all eight modules changed 2026-10-28 and read clean on the checker; the `sushicore` release (Open question 1) and the bare-clone lanes remain

## Problem

SushiHub installs the stack, but a module is meant to stand on its own. The owner wants two ways
into every module, equal in rank, and neither built on the other.

- **Standalone.** A person clones one module (and the siblings it needs) and builds, tests and
  runs it from its own CLI and pages, with no SushiHub.
- **With SushiHub.** `hub add` and `hub install` bring every module, and `hub link` adopts a
  checkout that exists.

The standard is the skill `module-install` in SushiSkills. This spec records what the eight
modules do against it on 2026-10-28, what each needs, and the decisions taken.

## What was measured

One read-only audit per module, on the three questions of `module-install`, "Checking a module".
Eight modules: sushilog, sushiprofiler, sushiruntime, sushiblas, sushiai, sushiengine,
sushitrack, sushidsp. No build and no `hub` command was run, so a claim about a run is marked
unverified.

| Module | Standalone | With SushiHub | Pages | Size |
| --- | --- | --- | --- | --- |
| sushilog | partial | done | partial | S |
| sushiprofiler | partial | partial | partial | S |
| sushiruntime | partial | done | partial | S |
| sushiblas | partial | done | partial | S |
| sushiai | partial | done | partial | S |
| sushiengine | partial | done | partial | S |
| sushidsp | partial | partial | partial | S |
| sushitrack | partial | partial | partial | M |

No module is `done` standalone. The code is close in all eight: no CMake file, CLI or CI
workflow needs `hub`. What is missing is one published package, a few stray paths and strings,
and pages that teach one way.

## The blocker: sushicore

Every module's CLI is built on `sushicore` and pins it:

| Module | Pin in `cli/pyproject.toml` |
| --- | --- |
| sushilog, sushiruntime, sushiai, sushiprofiler, sushidsp | `==0.9.7` or `>=0.9.7` |
| sushiblas, sushiengine, sushitrack | `>=0.9.7` |

PyPI carries 0.9.5 as its newest release (checked 2026-10-28; the releases are 0.1.0 to 0.9.2
and 0.9.5). `pip install -e cli` on a clean machine therefore fails at the pin, in every module.
CI passes only where a runner installs `sushicore` another way. Pages in sushitrack, sushidsp
and sushiblas still say `sushicore` is not on PyPI, or stops at 0.4.0, which contradicts the pin.

The fix is a release, not a code change: publish `sushicore` 0.9.7, or move the pins to a
published version. Until then no page can be tested end to end.

## Findings and solutions

Each solution carries the id the plan uses. `module-install` names the rule behind it.

### Common to all eight

| Finding | Solution | Rule |
| --- | --- | --- |
| Install pages teach one way, almost always `hub install-cli` first | `Standalone` and `With SushiHub` headings in the README and `docs/getting_started/INSTALL.md`, with prerequisites and the clones | boundary 5 |
| `hub link` is documented in one place or none | Name `hub link <module> <path>` next to `<alias> link`, and say a standalone checkout links with no change | boundary 5 |
| `sushicore` and library versions are copied into prose and drifted (0.9.0, 0.9.2, `v0.3.0` against `v0.3.2`) | Name the file that holds the version; NOTICE.md stays the one prose copy | default 3 |
| No job proves the bare clone | A `bare-clone` CI job: checkout, install the CLI, `<alias> setup`, build, test; no `hub`, no `SUSHISTACK_HOME` | default 4 |
| Nothing checks the standard | A checker `check_module_install.py` for boundaries 1 and 2 and the presence of the elements | none yet |

### sushilog (S)

- README and `docs/guides/CLI_GUIDE.md` give only `pip install -e ./cli`: add prerequisites
  (Python, compiler, CMake, network for googletest) and the `sushicore` source, then the hub way.
- `cli/README.md:6` says `sushicore` 0.9.2 and `NOTICE.md:14` says 0.9.0, against the 0.9.7 pin.
- googletest is fetched from GitHub; it does not look in the shared store. Left as is: a test
  framework fetch is allowed, and the store does not offer it (unverified).

### sushiprofiler (S)

- Pages describe standalone only: add the `With SushiHub` block and `hub link`.
- `NOTICE.md:17` and `cli/README.md:6` say 0.9.2, against the 0.9.7 pin.
- `cli/README.md` gets one paragraph on the workspace config layer and `SUSHISTACK_HOME`.
- Ignore `D:/Projects/sushiprofiler_live`: it is not a module. Its status is open (Open questions).

### sushiruntime (S)

- README, `docs/guides/CLI_GUIDE.md`, `INTRODUCTION.md` and `CONTRIBUTING.md` lead with the hub
  bootstrap and name no `sushicore` prerequisite. `CONTRIBUTING.md:24-28` says "with only this
  checkout" and then runs `hub install-cli`.
- `cli/README.md:5` says `sushicore` ships in the SushiStack repository. It is its own
  repository and a PyPI package.
- `cli/config.toml:40-44` comments imply hub is needed.
- `cmake/SushiRuntimeVcpkg.cmake:16-27` reads `SUSHISTACK_HOME`; move it to the CLI (decision 2).

### sushiblas (S)

- README, `cli/README.md`, `CONTRIBUTING.md` and `BUILDING.md` give `hub install-cli` as the
  only install; `BUILDING.md:27` is the one place `hub link` appears.
- `.github/workflows/ci.yml:101` reads the pin as `['sushi']['sushilog']['version']`, while the
  fragment's tables are `[sushisystems.<name>]`. Five places. A CI step may fail; check it.
- Name the store in one table: `~/.sushisystems`, `SUSHISYSTEMS_HOME`, `SUSHISTACK_HOME`.

### sushiai (S)

- `README.md:30`, `TUTORIAL.md:36-51`, `CONTRIBUTING.md:35-39` and `CLI_GUIDE.md:36` start at
  `hub install-cli sushiai`. Add the standalone clone order: sushiai, sushiruntime and sushiblas
  side by side.
- `CLI_GUIDE.md:183` and `:487` promise a "Building with CMake directly" section the README
  does not have. A direct configure needs a built SushiRuntime package, so write the section
  (naming `SushiRuntime_DIR` and the other package variables) or remove the promise.
- 12 JSON files and 3 example READMEs under `applications/examples/` hold
  `D:/Projects/.sushisystems/datasets/coco128`. Resolve the dataset root from the CLI's home
  or an environment variable, and check how `train.json` is read first.
- `cmake/Vcpkg.cmake:25-33` reads `SUSHISTACK_HOME`; move it to the CLI (decision 2).

### sushiengine (S)

- `README.md:7-8`, `BUILDING.md:7-22` and `CONTRIBUTING.md:31-32` give hub commands only.
  `BUILDING.md:8-9` and `:44-45` call the workspace a requirement, against
  `COMMAND_LINE_INTERFACE.md:506`, where `se setup` installs into `~/.sushisystems`.
- `cli/sushiengine/services/doctor.py:26` and `validation.py:22` tell the person to run
  `hub add` or `hub install`. Replace them with `se setup` and `se doctor`, and update
  `cli/tests/test_doctor.py` (decision 1).
- `cmake/BLAS.cmake:40-63` and `cmake/Vcpkg.cmake:21-23` read `SUSHISTACK_HOME`; move it to the
  CLI (decision 2).

### sushidsp (S)

- `CMakePresets.json:17,28` set the compiler to
  `D:/Projects/sushistack/dependencies/toolchains/llvm-sycl/bin/clang++.exe`. Every machine
  without that path fails the presets. Unset it; the CLI resolves the compiler.
- `sushi-module.toml:1-2` says SushiDSP is not in the hub catalog; it is, since 2026-10-28.
  `docs/backlog/README.md` RW-2 says the same and can close. `docs/design/SUSHIDSP/README.md`
  lines 72 and 76-81 name a registry file that moved and claim zero dependencies on the stack.
- The README gives `git clone` and `pip install -e ./cli`; it lacks `hub add`, `hub install`
  and `hub link`. `README.md:38`, `cli/README.md:10-15` and `FAQ.md:37` say `sushicore` is not
  on PyPI and install from a checkout.
- The manifest's repository URL is `SushiSystems/SushiDSP.git`; the catalog's is
  `sushisystems/sushidsp.git`. Nothing in the repository depends on the casing.

### sushitrack (M)

- The root has no `sushi-module.toml`, so SushiHub knows it only from the catalog. Add one:
  name `sushitrack`, alias `st`, distribution `source`, repository URL.
- `.config/conda/environment.yml:65` pins `sushicore==0.4.0` and the Dockerfile does the same,
  against the CLI's `>=0.9.7`. The hand-made path is broken (KI-4, RW-16).
- GoogleTest has no `check_cmd` in the fragment (KI-8, RW-18), so a missing one fails late at
  `find_package(GTest)`.
- `README.md` Build lists SushiLog and not SushiProfiler; `INSTALL.md` says SushiProfiler
  `v0.3.0` against the fragment's `v0.3.2`; `NOTICE.md:31` has old `sushicore` pins.
- `ci.yml` never clones sushilog or sushiprofiler and never runs `st setup`, yet the build
  needs both packages. Whether it passes by `st build` fetching them is unverified.
- Eigen, TrackEval and YOLOX are submodules; the standalone block names `git submodule update
  --init`.

## Decisions

1. **A remedy names the module's own command.** The sushiengine audit proposed naming both
   `se setup` and `hub install`. The module's command works on both ways in and `hub install`
   on one, so messages name the module command only. sushiruntime already tests that no
   service prints "hub install"; the other modules copy that test.
2. **The CLI resolves the workspace, CMake does not.** `SUSHISTACK_HOME` fallbacks in four
   CMake files go, after each is shown to be unreachable once the CLI hands `VCPKG_ROOT` and
   `<NAME>_DIR`. A fallback with no reader is deleted outright.
3. **A checker enforces the standard.** `check_module_install.py` in SushiSkills `tools/`,
   copied to the modules like the other shared tools, fails on a machine path in a committed
   file and on `hub` in code, and reports a missing element.
4. **`dependencies` and `module-install` do not repeat each other.** The search order for a
   Sushi library stays in `dependencies`; `module-install` cites it.

## What the work found beyond the audit

- `sushiengine` native lane: its `BLAS.cmake` searched `SUSHISTACK_HOME` for the SushiBLAS checkout
  and the CLI handed none. The CLI now hands `SUSHIBLAS_DIR` (`sushiblas_dir`, then the sibling, then
  the fetched copy), and the CMake candidates went (decision 2).
- `sushiblas` and `sushiengine` kept their install text in `BUILDING.md`; the checker asked for
  `INSTALL.md`, so the text moved there and `BUILDING.md` links to it.
- `sushiai` examples: the `data` block is passed through as written and is not resolved against the
  file, so a relative `data.root` is relative to the working directory. The examples read
  `datasets/coco128` under the repository root, git-ignored.
- `sushiruntime` `sr toolchain` wrote a header naming `hub install` into `config.local.toml`.
- `sushitrack`: closing the conda pin closed KI-4 and RW-16; `sushidsp`: stating the catalog entry
  closed KI-36 and RW-2.

## Out of scope

- The module code beyond the files named above, and SushiHub's own commands.
- `sushicore` itself, except that it must publish (Open questions).
- Binary distribution of sushiengine. The catalog says `binary`; both ways in still apply to
  the source checkout.

## Open questions

1. **Publish `sushicore` 0.9.7, or pin the modules to 0.9.5?** Owner's decision, and a release
   is outside any module. Pages and the bare-clone lane wait on it.
2. **`D:/Projects/sushiprofiler_live`:** an old copy, or a separate product? Not audited as a
   module.
