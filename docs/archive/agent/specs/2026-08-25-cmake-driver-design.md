# The shared cmake driver

Status: built. Landed 2026-08-25, one phase at a time, with an argv diff and a full test
run in all five consumer repositories before each phase's commits.

| phase | sushistack | sushiruntime | sushiengine | sushiai | sushiblas | sushidsp |
| --- | --- | --- | --- | --- | --- | --- |
| sushicore test suite + CI | 27d9d37, d74fb8f | - | - | - | - | - |
| argv recorder + baselines | 24e5371, bdc64ad | - | - | - | - | - |
| D1 -- proc.py | 102dec0, 3e59f6a, 06a39e8 | 6b7c6e3 | 8e91895 | 61868af | 57f6abd | 6048b53 |
| D2 -- cmake_cache.py | 192d8e0 | b00baaf | 7bfec78c | 6a88f1a | 1000671 | not touched |
| D3 -- CMakeDriver | d5ae772, 7901c66, 547276c | 4ce969e, a3b9381 | 0ce995d3, 796afee5, c77200c5 | 90f13aa, e6c03df | 0aeb1b5, d4979fa | d6e9fd4, 2927d3e |
| D4 -- toolchain_args | 3da0660 | not applicable (see D4, below) | 35df2058 | 316eaf5 | 26fc1a8 | not touched |

The first two rows are sushistack-only: a test suite and CI workflow for a package that had
neither, and the argv recorder every later row's proof depends on. Every phase row past
that is one commit per repository, except where a review round added a follow-up commit on
top of the same day's initial one — those are listed in landing order.

Final size of the five files this programme took apart, next to where each started:

| file | before | after |
| --- | --- | --- |
| sushiruntime/cli/sushiruntime/services/project.py | 747 | 615 |
| sushiengine/cli/sushiengine/services/project.py | 565 | 460 |
| sushiai/cli/sushiai/services/project.py | 724 | 577 |
| sushiblas/cli/sushiblas/services/project.py | 563 | 422 |
| sushidsp/cli/sushidsp/services/project.py | 159 | 134 |

## Why

Five repositories each carried a `cli/<module>/services/project.py`: 747 lines in
SushiRuntime, 724 in SushiAI, 565 in SushiEngine, 563 in SushiBLAS, 159 in SushiDSP. The
four preceding consolidations (`config.py`, `console.py`, `services/diag.py`, `env.py`)
each found a file that was a copy of its siblings and hoisted it whole. This one was not
that. Comparing the five as ASTs, with docstrings stripped and the module and program
names normalised away, sorted their symbols into four groups:

| group | symbols |
| --- | --- |
| identical in all five | `_cmake`, `_ctest` |
| identical but for the program name in one error string\* | `_resolve_exe`, `_run`, `_run_drained` |
| identical in SushiAI and SushiBLAS | `_resolved_c_compiler`, `_vcpkg_prefix`, `_toolchain_args`, `_deploy_consumer_dlls`, `_configured_build_type`, `_check_runtime` |
| genuinely different | `build`, `test`, `run`, `_configure_args`, `test_package`, and SushiRuntime's sanitizer and toolchain-selection block |

\* Wrong for three of the five. See "A claim this document got wrong", below.

So the file was two things fused together. Underneath was **a cmake driver** — spawning
processes, reading `CMakeCache.txt`, deciding whether a tree must be reconfigured,
removing it, running Doxygen. That layer was the same everywhere and is what had been
copied. On top was **a build policy** — which cache variables a module passes, which
targets and test suites it has, whether it has a sanitizer lane or an execution backend.
That layer differed because the five builds differ, and it was not a defect.

The move was therefore not "hoist the identical functions". It was "name the driver as a
type and leave the policy in the module". Hoisting `build()` would have dragged every
module's policy into the shared package behind a `module ==` branch, which is the shape
this whole programme existed to remove.

## Defects the consolidation surfaced

Two kinds turned up, and they are worth keeping apart: one was a fix that had already
been made once and never spread, the other was wrong everywhere at once.

### Fixed in one copy, never reached the others: `markup=False`

`_run_drained` echoes the child's output through Rich. SushiRuntime passed `markup=False`;
SushiEngine, SushiAI and SushiBLAS did not. Rich then parsed square brackets in the
child's output as style tags and dropped what it could not resolve:

```
in:   note: see [[nodiscard]] here
out:  note: see [] here
```

The single call site in all four modules is the `ctest` invocation inside `test()`, so
`se test`, `sa test` and `sb test` silently mangled failing-test output. SushiRuntime had
found this and fixed it in its own copy; the fix never reached the other three. This was
the third defect of the class — after `se --help` failing outside a checkout and
`[found]` printing as nothing — and each one was a fix that had landed in one copy of
five. D1 unified the four into `sushicore.proc.Runner.run_drained`, which always passes
`markup=False`.

### Wrong in all five copies at once: `resolve_exe`'s PATH/Path collision

`_resolve_exe` exists to stop `subprocess.CreateProcess` from doing its own PATH lookup
against a plain-dict env, because on Windows that dict can hold both `"Path"` (from
`os.environ`) and `"PATH"` (from a vcvars overlay); handing the dict straight to
`subprocess` lets it pick between the two keys unpredictably, so a tool on one of them is
intermittently reported not found. All five copies "fixed" this by resolving to a full
path themselves — and all five did it by reading whichever of `"Path"` / `"PATH"` a
`dict` iteration happened to reach first, then searching only that value. A tool on the
other key fell through to the real process PATH and then to the bare name: the exact coin
flip the function existed to prevent, moved from `subprocess.CreateProcess` into
`next()`.

This was not found by inspection. D1's own review added a test for the two-key collision,
the test failed against the newly-landed `sushicore.proc.Runner.resolve_exe`, and the
failure traced straight back to logic every one of the five originals shared. The fix
(landed in a follow-up commit, `sushistack` `3e59f6a..06a39e8`) searches the union of
every PATH-spelled key, joined in the env's own iteration order, rather than the first one
found — a search can only turn up a tool the single-key version missed, never fewer, so
the change could only add coverage. All five argv captures were re-run after the fix and
came back byte-identical to their pre-D1 baselines, which is what you would expect: the
merged environment sushicore's own `load_build_env` builds carries PATH under a single
spelling, so the union and the single-key read agree everywhere this stack actually runs
it today. The bug was real; nothing observable had yet depended on it going the other way.

## What sushicore gains

Three modules, none of which knows a cache variable's name.

**sushicore/proc.py** — `Runner(console, program)`

Owns spawning and executable resolution, nothing else.

- `resolve_exe(name, env)` — full path from the union of every PATH-spelled key in the
  env, joined in iteration order, falling back to the process PATH and then to the bare
  name. Searching the union rather than one key is what keeps Windows from resolving a
  tool unpredictably when the env carries both a `Path` and a `PATH` key.
- `run(cmd, cwd, env=None)` — child inherits stdout.
- `run_drained(cmd, cwd, env=None)` — child's output is piped and re-emitted line by line
  with `markup=False`. Draining ourselves is what keeps ctest's `gtest_discover_tests`
  enumeration from stalling on Windows.

`program` supplies the `sr config` / `se config` hint in the not-found message, which is
the only reason the five copies' `_run` differed at all (`_run_drained` differed by more
than that in three of them — see above).

**sushicore/cmake_cache.py**

- `cached_value(build_dir, entry)` — the value CMake baked into `CMakeCache.txt`, or None.
  Read directly rather than through `cmake -L`, so it costs nothing and works on a tree
  whose configure failed part way through.
- `home_directory(build_dir)` and `is_stale(build_dir, root)` — SushiRuntime's check for a
  tree configured against a different source path, generalised into `sushicore` so any
  module can reach it through `CMakeDriver.needs_configure`'s `root` argument. Every module
  can meet a build tree carried over from a container mount, and the check is now available
  to all of them — but only SushiRuntime's `project.py` actually passes `root=`; see
  "Deliberately not in scope" for wiring the other three.

**sushicore/cmake_driver.py** — `CMakeDriver(console, runner)`

Every method takes the resolved configuration as its first argument, so the driver stores no
configuration of its own and two lanes of the same module can share one.

- `cmake(cfg)` / `ctest(cfg)` — the configured executable or the bare name.
- `needs_configure(build_dir, generator, expect=None, root=None)` — the generator sentinel
  (`build.ninja` or `Makefile`), the stale-source-path check, and an optional mapping of
  cache entry to expected value. That mapping is how SushiEngine's `CMAKE_BUILD_TYPE` and
  `SUSHIENGINE_EXECUTION_BACKEND` checks are expressed without the driver naming either.
  SushiRuntime keeps its own stamp file on top; it is a superset, not a variant.
- `configure(args, cwd)`, `compile(cfg, build_dir, cwd, env, config, targets)`,
  `ctest_run(cfg, build_dir, env, label_regex, filter, repeat)` — the invocation shapes.
  `compile`'s `config` falls back to the tree's own cached `CMAKE_BUILD_TYPE` (or
  `"Release"`) when the caller does not choose one — see "What the plan got wrong" for
  the `jobs` parameter this signature originally also carried and no longer does.
- `clean_tree(build_dir)` — remove and report.
- `doxygen(cfg, doxyfile, cwd, env, install_hint)` — including the "not installed"
  guidance, which existed in four slightly different spellings before this. It shipped in
  D3's first commit with no caller reaching it at all, because the driver ran the
  argument as an absolute path while every module ran it relative to `cwd`; see "Trimmed
  after review".

## What stays in each module

`BuildType`, `Suite`, `_build_dir`, `_configure_args`, `build`, `test`, `run`,
`test_package`, SushiRuntime's sanitizer flags, stamp and compiler selection, SushiEngine's
`ExecutionBackend` and `CleanType`, SushiAI's demo targets. SushiAI's and SushiBLAS's
`_toolchain_args` and `_deploy_consumer_dlls` also stay, still identical between the two —
see D4, below, for why duplication between two modules was kept rather than moved.

The enums stay for a reason beyond policy: Typer builds each `--suite` and `-t` option by
reflecting on the enum class, and a Python enum with members cannot be subclassed. Their
label tables stay with them, because a table enumerates the suites that module actually has
— eight in SushiRuntime, four elsewhere — and a shared one would either be a union nobody
can run or a lowest common denominator nobody wants. The driver takes the selected regex as
a parameter and never sees the table.

## Phases

Each phase landed as one commit per repository (a review round occasionally added a
follow-up commit; see the table at the top), smallest blast radius first, so a mistake
could be reverted alone.

- **D1 — proc.py.** All five modules. No cmake knowledge changed hands. Closed the
  `markup=False` defect in SushiEngine, SushiAI and SushiBLAS, and surfaced (then closed)
  the `resolve_exe` PATH/Path defect described above, which turned out to be in all five.
- **D2 — cmake_cache.py and needs_configure.** Four modules; SushiDSP was not touched, as
  planned. Gave SushiEngine, SushiAI, SushiBLAS and (on top of its own stamp file)
  SushiRuntime `cmake_cache.py` and the `root` argument on `needs_configure`, making the
  stale-source-path check reachable from all four. Only SushiRuntime's call site passes
  `root=`, though; SushiEngine, SushiAI and SushiBLAS call `needs_configure` without it, so
  `is_stale` never runs for them. See "Deliberately not in scope".
- **D3 — CMakeDriver.** All five. The configure, compile, ctest, clean and doxygen
  invocations — the largest phase, and the only one that touched what reaches the
  compiler. Two items it shipped were then trimmed on review rather than kept as
  designed; see "Trimmed after review".
- **D4 — `_resolved_c_compiler` and `_vcpkg_prefix`.** Moved to
  `sushicore.toolchain_args` as `c_compiler_for` and `vcpkg_prefix`, consumed by SushiAI,
  SushiBLAS and SushiEngine. `_toolchain_args` stayed a module function in SushiAI and
  SushiBLAS, still identical between the two: it is one function shared by two modules
  rather than five, and it encodes their shared build policy rather than a derivation
  every module needs. `_deploy_consumer_dlls` stayed for the same reason, and because it
  names a package layout (`bin/*.dll`, `hwloc*.dll`) that belongs to those two modules,
  not to a shared package. SushiEngine's own inline `{vcpkg}/installed/{triplet}` string
  (in `_configure_args`) used exactly the shared derivation and was replaced with a call
  to `vcpkg_prefix`. SushiRuntime also builds a `{vcpkg}/installed/{triplet}` string
  (`_configure_args_windows`), but its `Config` class extends
  `sushicore.config_base.ToolConfig`, not `sushicore.stack_config.StackConfig`. It is the
  bottom of the stack and the owner of the toolchain bundle the other four borrow, not
  one of the heads that resolve a bundled or overridden vcpkg root through
  `resolved_vcpkg()`, which `vcpkg_prefix()` calls. Its `vcpkg_root` is a plain, required
  config field read with `cfg.expand()` directly. Forcing it onto the shared helper would
  mean adding `resolved_vcpkg` to a `Config` class deliberately built without the
  stack-head machinery — a larger change than this phase's brief, so SushiRuntime's
  `project.py` was left untouched by D4, exactly as the design anticipated when it named
  this split as a real divergence rather than an oversight to fix.

## What the plan got wrong

A design corpus that records only what worked teaches nothing. Two things in the plan's
own text did not survive contact with the actual repositories.

**The recorder as specified did not run at all.** The plan's `record_cli_argv.py` called
each module's `build` / `test` / `run` / `clean` / `doxygen` functions without first
changing into that module's own root. Every one of those functions calls
`find_project_root()` (`sushicore.module_config.ModuleConfig.find_project_root`), which
walks up from the current working directory looking for the module's root marker and
raises `SystemExit` when it never finds one. Run from `sushistack`, every single command
died on its first line before producing any argv at all. The instrument had to `chdir()`
into the target module's root before driving it — not a refinement, a precondition for
the recorder doing anything.

**Its stub set was incomplete, and the gap caused real writes before it was caught.** The
plan stubbed `subprocess.run`, `subprocess.Popen` and `shutil.rmtree`. Two more calls on
the same paths mutate the machine and are not subprocess calls at all:
`shutil.copy2` (SushiAI's and SushiBLAS's `_deploy_consumer_dlls`, copying DLLs beside a
package-test consumer binary) and `Path.write_text` (SushiRuntime's configure stamp,
`.sushiruntime_dist`). Both ran for real during the first baseline capture, before the gap
was found:

- SushiRuntime's `build/.sushiruntime_dist` was overwritten with a genuine stamp value.
  Left alone, a plain `sr build` afterwards would have read a stamp that matched
  `build/CMakeCache.txt`'s actual `cpu` backend, skipped a reconfigure it needed, and
  silently kept a stale tree — the exact failure the stamp exists to prevent. It was
  restored by hand once found.
- SushiBLAS's `build/package/consumer/{hwloc-15.dll,sushiruntime.dll}` were re-copied for
  real via `shutil.copy2` from the install prefix and the vcpkg tree. Verified
  byte-for-byte against the source files afterward; `copy2` preserves the source's mtime
  on the destination, which is how the copies were confirmed genuine rather than
  pre-existing.

The recorder was fixed to also patch `shutil.copy2`, `Path.write_text` and
`Path.write_bytes`, recording what they were asked to do instead of doing it, before any
further capture was trusted.

## A claim this document got wrong

The "Why" table above says `_resolve_exe`, `_run` and `_run_drained` were "identical but
for the program name in one error string." That is true for `_resolve_exe` and `_run`. It
is false for `_run_drained` in SushiBLAS, SushiAI and SushiEngine: in those three,
`_run_drained` carried its own short not-found message —

```
Executable not found: '{cmd[0]}'. Run `<program> config`.
```

— distinct from `_run`'s four-line message in the same file. SushiRuntime's
`_run_drained` already used the same four-line message as its own `_run`; SushiDSP has no
`_run_drained` at all. So three of the five files held two independently-worded
not-found messages, not one message with a varying program name, and D1 silently unified
all of it into `sushicore.proc.Runner._not_found`'s four-line form. The change itself is
sound — strictly more information is printed, and it is printed rather than spawned, so
none of the five argv diffs could show it either way — but the claim that the five copies
differed only by program name was wrong for three of them, and the commit messages that
landed D1 in `sushiblas`, `sushiai` and `sushiengine` repeat the same overstatement. Those
commit messages are not being rewritten: they are published on `main` in repositories
another agent shares, and rewriting history to fix a sentence is out of proportion to the
error. This paragraph is the correction of record.

## Trimmed after review

Two things the design specified did not make it into the shipped interface, and one
ordering changed. All three are visible only from the source or from a Doxygen run with
no `doxygen` binary present — none of them can move an argv diff.

- **`CMakeDriver.doxygen` shipped once with zero callers**, because the driver ran
  `[doxy, str(doxyfile)]` with the absolute path while all five modules ran
  `[doxy, "Doxyfile"]` or `[doxy, ".config/doxygen/Doxyfile"]` — a path relative to
  `cwd=root`, resolved by the child. Rather than delete the method, it was wired: the
  driver now derives the argument as `doxyfile.relative_to(cwd).as_posix()`, which
  reproduces every module's own argument exactly. `as_posix()` is load-bearing on
  Windows, where `relative_to` yields backslashes and a raw `str()` would have changed
  the recorded argv. A Doxyfile outside `cwd` raises `ValueError` out of `relative_to`;
  no caller reaches that today, and no fallback was added for it — a `ValueError` naming
  `relative_to` is a legible failure, where silently falling back to an absolute path
  would have changed the argv for whichever module hit it first.
- **`CMakeDriver.compile`'s `jobs` parameter was removed outright**, not given a caller.
  The design's interface listed it; grepping every `_DRIVER.compile(...)` call site
  across all five repositories found ten, none passing `jobs=`. An unused parameter in a
  five-module shared API is exactly the dead weight this programme exists to remove, and
  adding a `-j` to a command line that had never carried one would have been a behaviour
  change dressed as tidiness. No consumer repository needed a commit for this at all —
  the cleanest evidence available that the parameter was dead.
- **`(root / "docs").mkdir(exist_ok=True)` now runs before the Doxyfile-exists and
  doxygen-installed checks, not after.** Every module already created that directory
  before calling into the driver; the driver's own checks now run second. The only
  visible effect is that `<repo>/docs/` gets created even when Doxygen is not installed,
  which was judged not worth restoring: doing so would mean either duplicating the
  driver's own checks in five modules or handing the driver a callback for one empty
  directory.

## Verification

The A/B technique used for `env.py` — import the pre-change module beside the new one and
compare resolved values — does not transfer, because these functions spawn builds. The
equivalent used here was to compare **the command lines**.

`subprocess.run`, `subprocess.Popen`, `shutil.rmtree`, `shutil.copy2`, `Path.write_text`
and `Path.write_bytes` were replaced with a recorder that captures argv, cwd and env keys
without doing any of it for real. Every command in every module — `build` for each build
type, `test` for each suite, `run`, `clean`, `doxygen` — was driven once at the parent
commit and once after, as a fresh subprocess per module (`python tools/record_cli_argv.py
<module> <output.json>`, run from inside that module's own root — see "What the plan got
wrong" for why that matters), and the recorded argv lists were diffed. Every flag reaching
cmake and ctest came back identical after every phase, for all five modules, on every
sweep including the final one across all five after D4.

**This proves less than "the build is unchanged."** It proves the command lines are
unchanged for the commands the recorder's matrix actually reaches. Four branches in
`sushicore/cmake_driver.py` are outside that matrix and were never exercised by an argv
diff at all:

- the `self._console.warn(...)` `CMakeDriver.needs_configure` emits when `is_stale`
  returns True for a real, mismatched build tree (`is_stale` itself has three direct
  unit tests in `sushicore/tests/test_cmake_cache.py`; the driver's own integration of
  it — passing `root=` and reaching the warning — has none, in sushicore or in any of
  the five consumers' own suites, which by design defer that decision's testing to
  sushicore's);
- `CMakeDriver.compile`'s `config is None` fallback to the tree's cached
  `CMAKE_BUILD_TYPE` (or `"Release"`) — both of `sushicore/tests/test_cmake_driver.py`'s
  `compile` tests pass an explicit `config`, so this line has no test either;
- the "Doxygen is not installed or not on PATH" message, which needs a Doxyfile that
  exists and a `doxygen_exe` that does not resolve to a real file — every doxygen test in
  `test_cmake_driver.py` either supplies a real (empty) file at that path or supplies no
  Doxyfile at all, so the actual not-installed branch is untested;
- the `ValueError` `relative_to` would raise for a Doxyfile outside `cwd` — the normal
  case (a Doxyfile under `cwd`, flat or nested) has two direct tests, but no test drives
  the exceptional one, and the driver's docstring states the precondition rather than
  guards it.

None of the five repositories' own build trees exercises these paths on this machine
either, so the honest statement is that they are unverified, not merely untested by one
particular method. A real `se build` (see below) would not close this gap by itself; it
would only prove the paths a real build happens to take, which for most machines are
none of these four.

Each phase also ran its repositories' CLI test suites, and each new sushicore module got
unit tests of its own. That was not incidental: sushicore had no tests and this repository
ran no CI before Task 1, which is not a floor three modules deciding what reaches a
compiler could stand on.

A real `se build` at the end is the last check, and belongs to whoever owns a machine that
builds. It was not run as part of this programme.

## Deliberately not in scope

- Wiring SushiDSP's `_run` to `load_build_env`. Its builds run without the snapshotted
  toolchain environment today. That is a real gap and a separate change; conflating it
  with this one would make the argv diff unreadable, which is the only evidence this
  design has.
- SushiDSP's missing `clean` and `doxygen` commands.
- Merging SushiRuntime's and SushiEngine's `_configure_args`.
- Passing `root=` from SushiEngine's, SushiAI's and SushiBLAS's `needs_configure` calls.
  `CMakeDriver.needs_configure` already accepts `root` and `cmake_cache.is_stale` already
  implements the check; only those three call sites omit the argument, so `is_stale` never
  runs for them today. Left for later because it changes what those commands do — a warning
  that can newly fire on a stale tree — and would need its own argv verification, which this
  phase's diff does not cover.
