# Changelog

## Unreleased

- 2026-10-06 — licence: Restored the three-section license box and named both holders in the copyright line of every source file (`tools/licensing/write_license_block.py`, `tools/documentation/check_source_comments.py`).
- 2026-10-05 — cli: Reset the console to the terminal renderer after each test, so a `--json` test no longer breaks the next file under click 8.5 (`cli/tests/conftest.py`).
- 2026-10-05 — docs: Moved the reasoning held in module docstrings and comment paragraphs to the component READMEs (`cli/README.md`, `tools/README.md`, `cli/sushihub/`, `tools/record_cli_argv.py`).
- 2026-10-05 — docs: Moved the agent specs, plans and reports to the archive, promoted the hub design to `docs/design/HUB.md`, and added the SushiSkills checkers (`docs/`, `tools/`).
- 2026-10-05 — cli: Added the version flag to the root command (`hub --version`, `cli.py`).
- 2026-10-05 — cli: Added a `main()` entry point that ends a sushicore failure in one error line, a failed result event under JSON output, and exit code 1 (`cli.py`, `console.py`, `__main__.py`).
- 2026-10-05 — cli: Replaced the `SystemExit` raised outside a workspace with `WorkspaceNotFoundError` (`errors.py`, `config.py`).
- 2026-10-05 — cli: Replaced the `SystemExit` raised for missing desktop sources with `GuiSourcesMissingError` (`errors.py`, `gui_config.py`).
- 2026-10-05 — account: Raised `AccountUnreachable` for connection failures and timeouts, reported as one line (`identity.py`, `session.py`, `binary.py`).
- 2026-10-05 — account: Raised `CredentialStoreError` for keyring failures, reported as one line (`token_store.py`, `session.py`).
- 2026-10-05 — describe: Took the `--describe` catalogue from `sushicore.describe` and removed the local serialiser (`describe.py`).
- 2026-10-05 — setup: Removed the `verify` and `all` pipeline steps (`factory.py`, `services/setup.py`).
- 2026-10-05 — setup: Removed `VerifyStep` (`steps.py`).
- 2026-10-05 — cli: Corrected the help of hub init, add, install-cli and sync (`cli.py`, `modules.py`, `cli/README.md`).
- 2026-10-05 — cli: Corrected the desktop-sources hint (`gui_config.py`).
- 2026-10-05 — licence: Replaced Apache-2.0 with PolyForm Noncommercial 1.0.0, which ends commercial use without a licence (`LICENSE`, `COMMERCIAL.md`, `NOTICE.md`, `README.md`).
- 2026-10-04 — docs: Marked the module wave of the standalone programme as landed (`docs/design/REMAINING_WORK.md`).
- 2026-10-04 — setup: Took the toolchain selection rule and the base fragment from sushicore (`cli/sushihub/setup/factory.py`, `cli/sushihub/setup/dependency_source.py`).
- 2026-10-04 — setup: Reduced a bare `hub install` from three SYCL toolchains to one (`cli/sushihub/setup/factory.py`).
- 2026-09-23 — setup: Ran `hub install` and `hub remove` through sushicore.provision's pipeline and steps (`cli/sushihub/setup/`, `cli/pyproject.toml`).
- 2026-09-22 — cli: Replaced raw Rich colour names with sushicore theme tokens in printed markup (`cli/sushihub/`).

## v0.2.0 — 2026-09-22

- 2026-09-22 — cli: Grouped the `hub doctor` table by owner and listed what is missing after it (`cli/sushihub/setup/steps.py`).
- 2026-09-22 — cli: Drew `hub --help` from sushicore's help page: command groups, examples and the logo (`cli/sushihub/cli.py`, `cli/sushihub/console.py`).
- 2026-09-22 — docs: Split the two names in prose: `SushiHub` is the tool, `SushiStack` is the applications it installs (`README.md`, `docs/`).
- 2026-09-22 — gui: Pointed the application's vcpkg fallback at the workspace root it now sits one level below (`gui/CMakeLists.txt`).
- 2026-09-22 — repo: Lifted the CLI, the application and the contract to the repository root (`cli/`, `gui/`, `contract/`).
- 2026-09-22 — cli: Renamed the CLI's Python package from `sushistack` to `sushihub` (`cli/sushihub/`).
- 2026-09-22 — cli: Provisioned sushidsp with or without a SushiStack workspace, and described it in its own manifest (`sushi-module.toml` in sushidsp).
- 2026-09-22 — cli: Read dependency fragments through `sushicore` (`cli/sushihub/setup/dependency_source.py`).
- 2026-09-22 — cli: Recognised a checkout that carries its own `sushi-module.toml` (`cli/sushihub/services/module_manifest.py`).
- 2026-09-22 — cli: Listed in `hub status` what the workspace knows rather than what the catalog ships (`cli/sushihub/services/presence.py`).
- 2026-09-22 — cli: Accepted a self-describing checkout in `hub link` (`cli/sushihub/services/modules.py`).
- 2026-09-22 — cli: Merged two modules' declarations of one dependency instead of taking the first (`cli/sushihub/setup/dependency_source.py`).
- 2026-09-22 — cli: Refused a dependency fragment shape the reader cannot read (`cli/sushihub/setup/dependency_source.py`).
- 2026-09-22 — cli: Stopped reporting `sushicore` as a module in `hub status` (`cli/sushihub/services/status_report.py`).
- 2026-09-22 — cli: Stopped pointing Linux builds at `~/vcpkg` (`cli/sushihub/defaults.toml`).
- 2026-09-22 — gui: Rerecorded the desktop application's fixtures from a live `hub` (`gui/tests/fixtures/`).
- 2026-09-22 — cli: Said "Sushi Account" once rather than twice in two help strings (`cli/sushihub/cli.py`).
- 2026-09-22 — install: Installed `hub` from PyPI rather than cloning the workspace (`install.ps1`, `install.sh`).
- 2026-09-22 — cli: Upgraded `hub` the way it was installed, by pipx or by pulling its checkout (`cli/sushihub/services/modules.py`).
- 2026-09-22 — cli: Gave the distribution name one owner (`cli/sushihub/__init__.py`).
