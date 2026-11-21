# tools

The five checkers every Sushi Systems repository carries, copied whole from SushiSkills, where a
rule is fixed first and copied out. `record_cli_argv.py` is this repository's own.

| Path | Checks | Takes |
| --- | --- | --- |
| `common/checker.py` | Nothing itself; runs a checker's rule table and prints findings | |
| `documentation/check_source_comments.py` | C++, GLSL, TypeScript and Python: license block, file header, block ceiling, `//` and `#` runs, separators, history words, `@date` | Files or folders |
| `documentation/check_docs_layout.py` | `docs/` entries, required documents, document names, work folders, status lines in the four forms, design ceiling, links under `docs/`, reachability from `docs/README.md`, READMEs under `modules/<tier>/`, archive candidates by the date in the status line, roadmap, journal, handover, milestone, priority and to-do files | Repository root |
| `documentation/check_changelog.py` | Headings and entry shape, releases kept live, length, one sentence, nesting, cited places | Repository root |
| `documentation/check_design_format.py` | Design documents: the five sections in order, a status line of at most 160 characters, the phase table and its states, no commit hash, no line that dates built or merged work | Repository root |
| `layering/check_layering.py` | Declared tiers and domains, upward includes from a module or its tests, cross-domain and unlisted same-tier includes, reaches into another module's `source/`, dependencies the build file lists, internal headers in installed ones | Repository root |
| `licensing/write_license_block.py` | Nothing; writes the license block of `source-comments` into every tracked source file, or lists the files that lack it with `--report` | Repository root, `--project` |
| `record_cli_argv.py` | Nothing; records the argv a Sushi CLI would hand to cmake and ctest, so a CLI change is proven without a build | A CLI command line |
| `tests/` | Unit tests for the checker rules; run `python -m unittest discover -s tools/tests` | |
| `check_all.py` | Nothing itself; runs the eleven checkers, then the repository's own `<area>/check_<what>.py` files and the tests, and prints only what failed | Repository root |
| `checking/checker.py` | Nothing itself; runs a checker's rule table and prints findings | |
| `checking/ignored_paths.py` | Nothing itself; names the files and folders git ignores, which no checker reads | |
| `checking/check_shared_tools.py` | The shared tools lock: present unless the repository is SushiCore, readable, and every locked file present and hashing to its lock | Repository root |
| `documentation/check_backlog.py` | `REMAINING_WORK.md` and `KNOWN_ISSUES.md`: shape, IDs and the counter, paths, references here and in siblings checked out beside the repository, entry size, a backlog entry for every open design document; `--report` lists the siblings read and the entries naming one | Repository root |
| `documentation/design_status.py` | Nothing itself; finds the design documents and work folders and reads their status lines | |
| `documentation/check_docs_truth.py` | The manual against the source: named symbols, cited paths, example sources, history words, page length, duplicated passages, em dashes, the allow-list | Repository root, `--source` |
| `testing/check_test_mirror.py` | `tests/` mirrors the source: one `test_<name>` file per header or source file (`<name>.test.ts` in TypeScript), no test without a unit, no folder without a counterpart, no test that includes a header under `source/`; in a Unity repository, `Assets/<Product>/Tests/` with `<Name>Tests.cs` | Repository root |
| `testing/check_test_sizes.py` | Every test names its size in its source: a `Small_`, `Medium_` or `Large_` C++ suite, a size mark on a pytest file, class or function, a `small:` TypeScript `describe` | Repository root |
| `testing/check_probes.py` | Folders named as probes or benchmarks outside `applications/probes/` and `applications/benchmarks/`, such a program using a test framework or added to the test runner, one named after another of its kind, one its README does not list | Repository root |
| `logs/check_logging.py` | Console writes outside the paths `settings.py` allows, empty `catch` and `except: pass`, C++ log calls without their module's category, a logging module without `<module>_log_category.hpp`, Python root-logger, named-logger and f-string records | Repository root |
| `routing/summarize_dispatches.py` | Nothing; sums the dispatch lines of every `REPORT.md` per model and effort, for `model-routing` | Repository root |

`check_docs_layout.py` reads inline Markdown links, with or without a title, wrapped over a
line or in angle brackets. It does not read reference-style links or a link around an image.

`write_license_block.py` is the one tool here that writes files. It takes its licence lines
from `check_source_comments.py`, covers `.in` templates and `.inc` fragments by the file they become, `--closed` for a closed repository, `--skip GLOB` for generated
files and `--upstream PATH=LINE;LINE` for a ported file; a later run without it keeps those lines. A `--report` run that prints nothing
proves a repository's headers are in place.

Every checker takes `--report` and `--rule NAME`, exits 1 on findings, 0 when clean or
reporting, 2 on a bad path. Python 3.11, standard library only.

## Per-repository settings

`K_` constants at the top of each checker. `check_layering.py` does nothing until
`K_TIER_ORDER` lists the repository's tiers, lowest first. `K_COPYRIGHT_LINE` and
`K_LICENSE_LINES` in `check_source_comments.py` hold the repository's licence lines; a closed
repository sets `K_LICENSE_LINES` to `("All rights reserved. No licence is granted.",)`.

This repository changes one setting: `K_SKIPPED_FOLDERS` in `check_source_comments.py` also
names `dependencies`, the provisioned tree `hub install` fills beside the source.

## record_cli_argv.py

A build's output is a function of its input, and the input is the argv list that reaches cmake
and ctest. So a refactor of the code that assembles that list is proved correct by capturing
the list before and after and finding no difference. Nothing is compiled, which is the only way
to check the build code on a machine that is not going to sit through five builds.

A command whose argv is a string, not a list, is passed through untouched. That is the vcvars64
snapshot, which must really run or the environment every other command is measured under would
be wrong. SushiRuntime's Linux equivalent, `_snapshot_linux` sourcing oneAPI's `setvars.sh`,
does not get this treatment: it calls `subprocess.run(["bash", "-c", script])`, a list, so the
recorder stubs it like any other command. A Linux capture is therefore taken under an unsourced
environment, and its argv is not evidence of what `setvars.sh` would have changed.

`subprocess.run`, `subprocess.Popen` and `shutil.rmtree` are not the only ways a command touches
disk. The package-consumer path of SushiBLAS and SushiAI deploys DLLs with `shutil.copy2`, and
SushiRuntime's `build()` writes a configure-stamp file with `Path.write_text`. Neither goes
through cmake or ctest, so neither is a command whose argv belongs in the record, but both are
real writes into a sibling checkout, and a recording pass that consumes and never modifies must
not make them. They are stubbed the same way: recorded, not performed. Each has a test in
`tests/test_record_cli_argv.py` that stands in for it. `Path.write_text` is captured unpatched
at import, as `_REAL_WRITE_TEXT`, and that is what writes the script's own JSON output after the
recording is done.

Every command a module's CLI exposes resolves its project root by walking up from the current
directory (`sushicore.module_config.find_project_root`). That is how a real `sb build` finds its
checkout when a developer runs it from inside the repository. Recording from this checkout's
own cwd would make every call fail at that first step, "not inside a project", before it
reached the cmake and ctest argv the tool exists to capture. So the process cwd is switched to
the target module's root for the duration of the matrix, which is what running the command by
hand would require, and restored afterwards.
