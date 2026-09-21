# Changelog

One line per meaningful change, newest first. Format: date, a past-tense verb, what changed, and
where, in backticks. No why; the reason lives in a design document the entry may link.

Releases are sectioned newest first. Sections older than the current release move to
`../archive/changelog/`, one file per version.

## Unreleased

## v0.2.0 — 2026-09-22

- 2026-09-22 — Grouped the `hub doctor` table by owner and listed what is missing after it (`cli/sushihub/setup/steps.py`).
- 2026-09-22 — Drew `hub --help` from sushicore's help page: command groups, examples and the logo (`cli/sushihub/cli.py`, `cli/sushihub/console.py`).
- 2026-09-22 — Split the two names in prose: `SushiHub` is the tool, `SushiStack` is the applications it installs (`README.md`, `docs/`).
- 2026-09-22 — Pointed the application's vcpkg fallback at the workspace root it now sits one level below (`gui/CMakeLists.txt`).
- 2026-09-22 — Lifted the CLI, the application and the contract to the repository root, the shape every sibling module already had (`cli/`, `gui/`, `contract/`).
- 2026-09-22 — Renamed the CLI's Python package from `sushistack` to `sushihub`, so the tool's name is the tool's (`cli/sushihub/`).
- 2026-09-22 — Provisioned sushidsp with or without a SushiStack workspace, and described it in its own manifest (`sushidsp`).
- 2026-09-22 — Read dependency fragments through `sushicore`, so one schema has one reader (`cli/sushihub/setup/dependency_source.py`).
- 2026-09-22 — Recognised a checkout that carries its own `sushi-module.toml` (`cli/sushihub/services/module_manifest.py`).
- 2026-09-22 — Listed in `hub status` what the workspace knows rather than what the catalog ships (`cli/sushihub/services/presence.py`).
- 2026-09-22 — Accepted a self-describing checkout in `hub link` (`cli/sushihub/services/modules.py`).
- 2026-09-22 — Merged two modules' declarations of one dependency instead of taking the first, which cost `sushiengine` the Vulkan feature of its SDL2 (`cli/sushihub/setup/dependency_source.py`).
- 2026-09-22 — Refused a dependency fragment shape the reader cannot read, which used to be skipped in silence (`cli/sushihub/setup/dependency_source.py`).
- 2026-09-22 — Stopped reporting `sushicore` as a module in `hub status` (`cli/sushihub/services/status_report.py`).
- 2026-09-22 — Stopped pointing Linux builds at `~/vcpkg`, which Linux never uses (`cli/sushihub/defaults.toml`).
- 2026-09-22 — Re-recorded the desktop application's fixtures from a live `hub` (`gui/tests/fixtures/`).
- 2026-09-22 — Said "Sushi Account" once rather than twice in two help strings (`cli/cli.py`).
- 2026-09-22 — Installed `hub` from PyPI rather than cloning the workspace (`install.ps1`, `install.sh`).
- 2026-09-22 — Upgraded `hub` the way it was installed, by pipx or by pulling its checkout (`cli/sushihub/services/modules.py`).
- 2026-09-22 — Gave the distribution name one owner (`cli/sushihub/__init__.py`).
