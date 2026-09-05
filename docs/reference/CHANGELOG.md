# Changelog

One line per meaningful change, newest first. Format: date, a past-tense verb, what changed, and
where, in backticks. No why; the reason lives in a design document the entry may link.

- 2026-09-05 — Designed the hub: binary module presence, Sushi ID sign-in, the JSON contract and the desktop application (`docs/agent/specs/2026-09-05-hub-design.md`).
- 2026-09-05 — Built the documentation skeleton: front door, manual index, style guide, changelog, glossary, backlog (`README.md`, `docs/`).
- 2026-08-28 — Added a known-issues page for the toolchains `ss` provisions (`docs/reference/KNOWN_ISSUES.md`).
- 2026-08-25 — Moved the cmake driver five `services/project.py` copies shared into `sushicore` (`sushicore/sushicore/proc.py`, `sushicore/sushicore/cmake_cache.py`, `sushicore/sushicore/cmake_driver.py`, `sushicore/sushicore/toolchain_args.py`).
- 2026-08-25 — Ran the five consumer CLIs' suites against the `sushicore` under test in CI (`.github/workflows/ci.yml`).
- 2026-08-25 — Added a test suite and a CI job for `sushicore` (`sushicore/tests`, `.github/workflows/ci.yml`).
- 2026-08-25 — Recorded the argv each CLI sends to cmake and ctest without running them (`tools/record_cli_argv.py`).
- 2026-08-25 — Registered sushidsp as a module with alias `sd` (`cli/sushistack/services/modules.py`).
- 2026-08-25 — Renamed `sushicli` to `sushicore` and resolved it from this repository (`sushicore/`).
- 2026-07-28 — Stamped installed toolchains and added `--refresh-toolchains` (`cli/sushistack/setup/toolchains.py`).
