# Wave 4b: build the desktop application through `ss` — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** `ss gui build`, `ss gui run`, `ss gui test` and `ss gui clean` drive the application under
`sushihub/gui/` the way `sb build` drives sushiblas: through `sushicore`'s `CMakeDriver`,
`StackBuildEnv` and `ExecutableIndex`, under the vcvars snapshot on Windows, against the shared
`dependencies/vcpkg` tree. The application's dependencies arrive through `ss install`, from a
dependency fragment, like every other dependency in the stack.

**Architecture:** One profile (`GUI_PROFILE`) says what the application is; one config class
(`GuiConfig`, a `StackConfig`) resolves its tools from the shared tree; one service module
(`services/gui.py`) holds the build policy: configure arguments, build types, the test label, the
run target. The Typer group `gui` is a thin layer over it. The catalogue learns nested groups so
`ss --describe` lists `gui build` and the desktop application draws a form for it. The
application's `vcpkg.json` goes away: manifest mode fought `ss install`'s classic-mode tree and
that is what the failed configure showed.

**Tech Stack:** Python 3.10+, sushicore, Typer, pytest. The C++ side is untouched except for
`vcpkg.json` (deleted) and `README.md`.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §4, §8.

## Why the configure failed

`cmake --preset windows-x64` from a plain PowerShell found no compiler because nothing had run
`vcvars64.bat`. Every module CLI solves this once through `sushicore.build_env.StackBuildEnv`,
which runs vcvars in a child, snapshots the environment, caches it, and hands it to every cmake,
ninja and ctest it spawns. The application gets the same treatment by being driven from `ss`.

## Global Constraints

- Touch: `sushihub/cli/**`, `sushihub/gui/vcpkg.json` (delete), `sushihub/gui/README.md`,
  `sushihub/gui/CMakeLists.txt` (only the toolchain-file block, see Task 4), `docs/README.md` is
  not yours. Do not edit `docs/reference/CHANGELOG.md` or `docs/design/REMAINING_WORK.md`.
- Never run `cmake`, `ninja`, `ctest`, `ss install` or `ss gui build`. The proof is the argv:
  tests stub `CMakeDriver` and `Runner` and assert the argument lists, as
  `tools/record_cli_argv.py` and the cmake-driver programme did.
- Nothing in `sushicore` changes. If a brick there does not fit, say so in the report; do not
  fork it into `sushihub/cli`.
- Docstrings as `docs/CONTRIBUTING.md` sets. Commit per task, stage by path.

## File structure

| File | Responsibility |
|---|---|
| `sushihub/cli/manifests/gui.deps.toml` (new) | The application's ports: `imgui[glfw-binding,opengl3-binding]`, `glfw3`, `nlohmann-json`. `gtest` is already in `base.deps.toml`. |
| `sushihub/cli/sushistack/setup/dependency_source.py` | A shipped fragment's owner is its file stem, except `base` → `shared`. |
| `sushihub/cli/sushistack/setup/package_managers.py` | `VcpkgManager.is_installed` matches the port name before `[`, so a feature list installs and is then seen as installed. |
| `sushihub/cli/sushistack/gui_config.py` (new) | `GUI_PROFILE`, `GuiConfig(StackConfig)`, `gui_root()`, `load_gui_config()`. |
| `sushihub/cli/sushistack/gui_env.py` (new) | `load_gui_build_env(cfg, build_dir)` over `StackBuildEnv`. |
| `sushihub/cli/sushistack/services/gui.py` (new) | `BuildType`, `build`, `test`, `run`, `clean`; `_configure_args`. |
| `sushihub/cli/sushistack/cli.py` | Typer sub-app `gui` with the four commands, each through `_finish`. |
| `sushihub/cli/sushistack/describe.py` | Nested groups flatten to `"<group> <command>"` names. |
| `sushihub/cli/tests/test_gui_build.py`, `test_describe.py`, `test_selection.py` (add) | Argv assertions; catalogue lists `gui build`; the `gui` fragment's owner. |
| `sushihub/gui/vcpkg.json` | Deleted. |
| `sushihub/gui/CMakeLists.txt` | The toolchain-file fallback block stays for hand builds; add nothing. |
| `sushihub/gui/README.md`, `sushihub/cli/README.md` | Build through `ss gui`; the four rows in the command table. |

---

### Task 1: The fragment, its owner, and feature-list ports

**Files:** create `sushihub/cli/manifests/gui.deps.toml`; modify `setup/dependency_source.py`
(`manifest_sources`), `setup/package_managers.py` (`VcpkgManager.is_installed`); tests in
`cli/tests/test_selection.py` (owner) and a new `cli/tests/test_vcpkg_features.py`.

Fragment:
```toml
# SushiHub GUI dependency fragment: what the desktop application under sushihub/gui links.
# `ss install` provisions these into the shared dependencies/ tree; `ss gui build` configures
# against that tree. gtest is the base fragment's.

[imgui]
description   = "Dear ImGui with the GLFW and OpenGL3 backends; the desktop application's UI."
required      = true
linux_apt     = []
windows_vcpkg = ["imgui[glfw-binding,opengl3-binding]"]

[glfw3]
description   = "GLFW window and input; the desktop application's window."
required      = true
linux_apt     = ["libglfw3-dev"]
windows_vcpkg = ["glfw3"]

[nlohmann-json]
description   = "JSON for Modern C++; the desktop application's contract parser."
required      = true
linux_apt     = ["nlohmann-json3-dev"]
windows_vcpkg = ["nlohmann-json"]
```
`imgui` has no apt package; with `linux_apt = []` the existing `vcpkg_fallback_ports` rule
installs it through vcpkg on Linux too.

`manifest_sources`: owner for `manifests/<stem>.deps.toml` is `SHARED_OWNER` when `stem == "base"`,
else `stem`. Test: a source built from `[(Path("x/base.deps.toml"), ...)]` is not what to test;
test `_owner_for_shipped(path: Path) -> str`, a new pure function, on both names.

`VcpkgManager.is_installed(pkg)`: strip a trailing `[...]` before matching against `vcpkg list`.
Test with a fake `subprocess.run` returning `imgui:x64-windows  1.92.8  ...`.

Commit: `feat(cli): declare the desktop application's ports in a fragment of their own`.

### Task 2: Profile, config, environment

**Files:** create `sushistack/gui_config.py`, `sushistack/gui_env.py`; test `cli/tests/test_gui_build.py` (first tests).

```python
GUI_PROFILE = ModuleProfile(name="SushiHub GUI", program="ss gui", env_prefix="SS_GUI",
                            root_marker="CMakeLists.txt", default_target="sushihub_gui")
def gui_root(workspace: Path | None = None) -> Path      # workspace_root() / "sushihub" / "gui"; SystemExit if CMakeLists.txt missing
@dataclass
class GuiConfig(StackConfig):
    target_bin: str = "sushihub_gui"
def load_gui_config() -> GuiConfig                        # layered from config_dir()'s config.toml, config.local.toml, GUI_PROFILE.env_overrides()
def load_gui_build_env(cfg: GuiConfig, build_dir: Path) -> dict[str, str]   # StackBuildEnv(profile=GUI_PROFILE, console=console, find_root=gui_root).load
```
Read `StackConfig` (`sushicore/sushicore/stack_config.py`) and `load_tool_config` before writing.
`resolved_compiler` there prefers the bundled SYCL clang++; the application does not want it on
Windows (it is a plain C++17 program that should build with the MSVC vcvars puts on PATH), so
`GuiConfig.resolved_compiler` is overridden: explicit `cxx` if set, else `""` meaning "let CMake
find one in the snapshotted environment". Say so in its docstring.

Tests: `gui_root` finds `sushihub/gui` under a fake workspace and exits when the CMakeLists is
missing; `GuiConfig().resolved_compiler(root) == ""` with no `cxx`.

Commit: `feat(cli): describe the desktop application to the shared build machinery`.

### Task 3: The build policy

**Files:** create `sushistack/services/gui.py`; tests in `cli/tests/test_gui_build.py`.

```python
class BuildType(str, Enum): debug = "debug"; release = "release"; relwithdebinfo = "relwithdebinfo"
def build(build_type: BuildType = BuildType.debug, clean: bool = False, defines: Sequence[str] | None = None, *, driver=None, env_loader=None) -> int
def test(filter: str | None = None, repeat: int = 0, *, driver=None, env_loader=None) -> int
def run(target: str | None = None, args: Sequence[str] = (), *, runner=None, env_loader=None) -> int
def clean(*, driver=None) -> int
def _configure_args(cfg: GuiConfig, root: Path, build_dir: Path, build_type: str, defines) -> list[str]
```
Build dir: `<gui root>/build/ss` (beside the presets' `build/<preset>`, never inside it).
Generator: `cfg.generator` (Ninja). `_configure_args`: cmake, `-S root -B build_dir -G`,
`-DCMAKE_BUILD_TYPE=`, `-DCMAKE_CXX_COMPILER=` only when `resolved_compiler` is non-empty,
`-DCMAKE_MAKE_PROGRAM=` when `cfg.ninja_exe`, `-DCMAKE_TOOLCHAIN_FILE=<vcpkg>/scripts/buildsystems/vcpkg.cmake`
and `-DVCPKG_ROOT=` when `resolved_vcpkg`, `-DVCPKG_TARGET_TRIPLET=` on Windows,
`-DVCPKG_MANIFEST_MODE=OFF`, `-DSUSHIHUB_GUI_BUILD_TESTS=ON`, then the caller's `-D`s last.
`build` mirrors sushiblas's: `needs_configure` → configure → `compile`. `test` → `ctest_run`
with no label. `run` → `ExecutableIndex(skip_dirs=("_deps",)).resolve(build_dir, console, target=...)`
then `Runner.run` with the build env. `clean` → `clean_tree`.

Tests stub the driver with a recorder object exposing the same methods and assert: the configure
argv contains the toolchain file under the fake deps dir, `-DVCPKG_MANIFEST_MODE=OFF`, the build
type, and no `-DCMAKE_CXX_COMPILER` when the compiler is unresolved; `--clean` calls `clean_tree`
first; `test` passes `filter` and `repeat` through; `run` refuses with a message when `build/ss`
is absent.

Commit: `feat(cli): build, test, run and clean the desktop application through the shared driver`.

### Task 4: The `gui` group, the catalogue, and the manifest-mode file

**Files:** modify `sushistack/cli.py`, `sushistack/describe.py`; delete `sushihub/gui/vcpkg.json`;
modify `sushihub/gui/README.md`, `sushihub/cli/README.md`; tests in `cli/tests/test_describe.py`
and `cli/tests/test_json_streams.py` (`gui clean` under `--json` against the throwaway workspace
with an empty `sushihub/gui/CMakeLists.txt`).

```python
gui_app = typer.Typer(name="gui", help="Build, test and run the desktop application under sushihub/gui.")
app.add_typer(gui_app, name="gui")
@gui_app.command("build")  # --type debug|release|relwithdebinfo, --clean, -D VAR=VALUE (multiple)
@gui_app.command("test")   # --filter, --repeat
@gui_app.command("run")    # target argument optional, extra args after --
@gui_app.command("clean")
```
`describe.catalogue`: when a Click command is a `Group`, recurse and emit its children as
`"<group> <child>"`; the group itself is not listed. `applies_to` unchanged.

`sushihub/gui/README.md`: "Building" section becomes `ss install` (once; brings imgui, glfw3,
nlohmann-json) then `ss gui build`, `ss gui test`, `ss gui run`; the presets stay for an IDE, with
a note that they need vcvars in the shell and `VCPKG_MANIFEST_MODE=OFF`. `sushihub/cli/README.md`:
four rows.

Commit: `feat(cli): add ss gui build, test, run and clean, and list nested commands in the catalogue`.

## Report

Paste `python -m pytest sushihub/cli/tests -q`, `python -m pytest sushicore/tests -q`,
`python -m compileall -q sushihub/cli/sushistack`; `git log --oneline -5`; deviations; and the
line `- 2026-09-05 — Added `ss gui build|test|run|clean` over the shared cmake driver and the desktop application's dependency fragment (`sushihub/cli/sushistack/services/gui.py`, `sushihub/cli/manifests/gui.deps.toml`).`

The user then runs, from the workspace root: `ss install` (imgui, glfw3, nlohmann-json arrive),
`ss gui build`, `ss gui test`, `ss gui run`.
