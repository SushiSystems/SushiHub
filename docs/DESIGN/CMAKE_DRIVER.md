# The shared cmake driver

Status: designed, not built. Four phases, none started.

## Why

Five repositories each carry a `cli/<module>/services/project.py`: 747 lines in
SushiRuntime, 724 in SushiAI, 565 in SushiEngine, 563 in SushiBLAS, 159 in SushiDSP. The
four preceding consolidations (`config.py`, `console.py`, `services/diag.py`, `env.py`)
each found a file that was a copy of its siblings and hoisted it whole. This one is not
that. Comparing the five as ASTs, with docstrings stripped and the module and program
names normalised away, sorts their symbols into four groups:

| group | symbols |
| --- | --- |
| identical in all five | `_cmake`, `_ctest` |
| identical but for the program name in one error string | `_resolve_exe`, `_run`, `_run_drained` |
| identical in SushiAI and SushiBLAS | `_resolved_c_compiler`, `_vcpkg_prefix`, `_toolchain_args`, `_deploy_consumer_dlls`, `_configured_build_type`, `_check_runtime` |
| genuinely different | `build`, `test`, `run`, `_configure_args`, `test_package`, and SushiRuntime's sanitizer and toolchain-selection block |

So the file is two things fused together. Underneath is **a cmake driver** — spawning
processes, reading `CMakeCache.txt`, deciding whether a tree must be reconfigured,
removing it, running Doxygen. That layer is the same everywhere and is what got copied.
On top is **a build policy** — which cache variables this module passes, which targets
and test suites it has, whether it has a sanitizer lane or an execution backend. That
layer differs because the five builds differ, and it is not a defect.

The move is therefore not "hoist the identical functions". It is "name the driver as a
type and leave the policy in the module". Hoisting `build()` would drag every module's
policy into the shared package behind a `module ==` branch, which is the shape this whole
programme exists to remove.

## The defect this uncovered

`_run_drained` echoes the child's output through Rich. SushiRuntime passes `markup=False`;
SushiEngine, SushiAI and SushiBLAS do not. Rich then parses square brackets in the child's
output as style tags and drops what it cannot resolve:

```
in:   note: see [[nodiscard]] here
out:  note: see [] here
```

The single call site in all four modules is the `ctest` invocation inside `test()`, so
`se test`, `sa test` and `sb test` silently mangle failing-test output. SushiRuntime found
this and fixed it in its own copy; the fix never reached the other three. This is the
third defect of the class — after `se --help` failing outside a checkout and `[found]`
printing as nothing — and each one is a fix that landed in one copy of five.

## What sushicore gains

Three modules, none of which knows a cache variable's name.

**sushicore/proc.py** — `Runner(console, program)`

Owns spawning and executable resolution, nothing else.

- `resolve_exe(name, env)` — full path from the env's PATH, falling back to the name.
  Resolving to a full path is what keeps Windows from picking unpredictably between a
  `Path` and a `PATH` key in a plain-dict env.
- `run(cmd, cwd, env=None)` — child inherits stdout.
- `run_drained(cmd, cwd, env=None)` — child's output is piped and re-emitted line by line
  with `markup=False`. Draining ourselves is what keeps ctest's `gtest_discover_tests`
  enumeration from stalling on Windows.

`program` supplies the `sr config` / `se config` hint in the not-found message, which is
the only reason the five copies differed at all. `env=None` means "inherit", which is what
SushiDSP does today and must keep doing until it is wired to `load_build_env`.

**sushicore/cmake_cache.py**

- `cached_value(build_dir, entry)` — the value CMake baked into `CMakeCache.txt`, or None.
  Read directly rather than through `cmake -L`, so it costs nothing and works on a tree
  whose configure failed part way through.
- `home_directory(build_dir)` and `is_stale(build_dir, root)` — SushiRuntime's check for a
  tree configured against a different source path, generalised. Every module can meet a
  build tree carried over from a container mount; only one of them notices today.

**sushicore/cmake_driver.py** — `CMakeDriver(profile, console, config, runner)`

- `cmake()` / `ctest()` — the configured executable or the bare name.
- `needs_configure(build_dir, generator, expect=None, root=None)` — the generator sentinel
  (`build.ninja` or `Makefile`), the stale-source-path check, and an optional mapping of
  cache entry to expected value. That mapping is how SushiEngine's `CMAKE_BUILD_TYPE` and
  `SUSHIENGINE_EXECUTION_BACKEND` checks are expressed without the driver naming either.
  SushiRuntime keeps its own stamp file on top; it is a superset, not a variant.
- `configure(args, cwd)`, `compile(build_dir, targets, jobs)`,
  `ctest_run(build_dir, label_regex, filter, repeat)` — the invocation shapes.
- `clean_tree(build_dir)` — remove and report.
- `doxygen(doxyfile, cwd, env)` — including the "not installed" guidance, which today
  exists in four slightly different spellings.

## What stays in each module

`BuildType`, `Suite`, `_build_dir`, `_configure_args`, `build`, `test`, `run`,
`test_package`, SushiRuntime's sanitizer flags, stamp and compiler selection, SushiEngine's
`ExecutionBackend` and `CleanType`, SushiAI's demo targets.

The enums stay for a reason beyond policy: Typer builds each `--suite` and `-t` option by
reflecting on the enum class, and a Python enum with members cannot be subclassed. Only
the suite-label regex **table** is shared, keyed by string; each module still declares the
enum whose members it actually has.

## Phases

Each is one commit per repository, smallest blast radius first, so a mistake reverts alone.

- **D1 — proc.py.** All five modules. No cmake knowledge changes hands. Closes the
  `markup=False` defect in SushiEngine, SushiAI and SushiBLAS.
- **D2 — cmake_cache.py and needs_configure.** All five. Gives the four modules that lack
  it the stale-source-path check.
- **D3 — CMakeDriver.** The configure, compile, ctest, clean and doxygen invocations. The
  largest phase and the only one that touches what reaches the compiler.
- **D4 — `_resolved_c_compiler` and `_vcpkg_prefix`** to sushicore for all four cmake
  modules; `_toolchain_args` shared by SushiAI and SushiBLAS only. SushiRuntime splits its
  assembly across Windows and Linux and SushiEngine deliberately omits `CMAKE_C_COMPILER`
  (its runtime lane has no C sources), and both divergences are documented in place. Do
  not force them into one function; note it and stop.

## Verification

The A/B technique used for `env.py` — import the pre-change module beside the new one and
compare resolved values — does not transfer, because these functions spawn builds. The
equivalent here is to compare **the command lines**.

Replace `subprocess.run` and `subprocess.Popen` with a recorder that captures argv, cwd and
the env keys, and returns success. Then drive every command in every module — `build` for
each build type, `test` for each suite, `run`, `clean`, `doxygen` — once at the parent
commit and once after, and diff the recorded argv lists. If every flag reaching cmake and
ctest is identical, the build is identical, and nothing had to be compiled to know it.

Each phase also runs its repositories' CLI test suites. A real `se build` at the end is the
last check, and belongs to whoever owns a machine that builds.

## Deliberately not in scope

- Wiring SushiDSP's `_run` to `load_build_env`. Its builds run without the snapshotted
  toolchain environment today. That is a real gap and a separate change; conflating it
  with this one would make the argv diff unreadable, which is the only evidence this
  design has.
- SushiDSP's missing `clean` and `doxygen` commands.
- Merging SushiRuntime's and SushiEngine's `_configure_args`.
