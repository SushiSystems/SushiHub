# Command line

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-21 | P2 | blocked | Add `hub add <git-url>` | a repository nobody has cloned can be added by its URL | RW-9 |  | 2026-10-19 |
| RW-22 | P2 | open | Add `hub unlink` | a link leaves `[modules]` of `.sushistack/workspace.toml` without a hand edit |  |  | 2026-10-19 |
| RW-23 | P2 | open | Test `install-cli` through the command | a test runs `install_cli` in `cli/sushihub/services/cli_install.py` through `hub` |  |  | 2026-10-19 |
| RW-24 | P2 | blocked | Read `use_vcpkg` | the key `cli/sushihub/defaults.toml` sets per platform decides the vcpkg tree | sushicore RW-51 |  | 2026-10-19 |
| RW-25 | P2 | blocked | Read the `[cli]` theme from the workspace | `cli/sushihub/console.py` reads the theme from `workspace.toml`, not from the directory `legacy_cli_dir` returns | sushicore RW-52 |  | 2026-10-19 |
| RW-26 | P2 | open | Return each packaged manifest's text | `manifest_sources` in `cli/sushihub/setup/dependency_source.py` returns text, not a path out of an `importlib.resources.as_file` block, so a zipimported… |  |  | 2026-10-19 |
| RW-28 | P2 | open | Send the sign-in code as data | `hub login` puts the user code and the verification link in its `result` payload or a structured event, and `gui/src/ui/screens/DeviceGrant.cpp` stops… |  |  | 2026-10-19 |
| RW-43 | P2 | open | Report the install channel of a PyPI install | `hub status` says what a PyPI install is, and `contract/status.schema.json` allows it |  |  | 2026-10-19 |
| RW-44 | P2 | open | Keep git's and pipx's output out of the event stream | under `--json` no child process writes to `hub`'s stdout |  |  | 2026-10-19 |
| RW-45 | P2 | open | Keep `--customize` from opening its picker under `--json` | the picker checks the output mode as well as the terminal |  |  | 2026-10-19 |
| RW-46 | P2 | open | End `hub --json` with no subcommand in a `result` event | it prints events, not the help text |  |  | 2026-10-19 |
| RW-47 | P2 | open | Send the readiness report of `hub doctor` as events | `cli/sushihub/setup/steps.py` writes no raw Rich output |  |  | 2026-10-19 |
| RW-48 | P2 | open | Read the child's stderr in the desktop application | `gui/src/bridge/Process.cpp` shows a traceback and the readiness report in the window |  |  | 2026-10-19 |
| RW-49 | P2 | open | List the GUI commands only in a clone of this repository | `hub gui build`, `test`, `run` and `clean` are listed where they work |  |  | 2026-10-19 |
| RW-50 | P2 | open | Name the tool overrides after the hub | no override in `cli/sushihub/config.py` is named `SR_*` |  |  | 2026-10-19 |
| RW-51 | P2 | open | Find the `sh` alias under a redirected Documents folder | `hub status` reads the PowerShell profile path from the system, not four fixed paths |  |  | 2026-10-19 |
| RW-52 | P2 | open | Refuse a module `pyproject.toml` without a name cleanly | `hub install-cli` reports the missing `[project] name` instead of a `KeyError` |  |  | 2026-10-19 |
| RW-53 | P2 | open | Remove `discovery.py` | `cli/sushihub/services/discovery.py`, imported by nothing, is gone |  |  | 2026-10-19 |
| RW-54 | P2 | open | Give the command line and the desktop application a logger | both log through the `logging` skill's interface |  |  | 2026-10-19 |
| RW-57 | P2 | open | Stop the hub CLI reading SushiHub where the module-install rule forbids it | check_module_install.py reports nothing for cli/sushihub |  |  | 2026-10-28 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
