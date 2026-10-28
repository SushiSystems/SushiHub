# Layout continuous integration

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-37 | P2 | open | Run the checkers and the desktop application in CI | `.github/workflows/ci.yml` runs the checkers, builds and tests `gui/`, caches its installs and tests on 3.11 |  |  | 2026-10-19 |
| RW-38 | P2 | open | Gate the release on the tests | `.github/workflows/release.yml` publishes only after the tests and a Windows job pass, checks the tag against `cli/pyproject.toml` and packages the desktop… |  |  | 2026-10-19 |
| RW-39 | P2 | open | Add the root files the layout names | `.gitattributes`, `.editorconfig` and `.clang-format` exist; `install.sh` keeps its line endings on every machine |  |  | 2026-10-19 |
| RW-40 | P2 | open | Finish the ignore rules | `.gitignore` names `.pytest_cache/`, `dist/`, `.venv/`, `imgui.ini` and `CMakeUserPresets.json`, and drops the two rules for old scratch folders |  |  | 2026-10-19 |
| RW-41 | P2 | open | Move `record_cli_argv.py` into an area | `tools/record_cli_argv.py` sits under `tools/<area>/` |  |  | 2026-10-19 |
| RW-42 | P2 | open | Take the whole shared tool set | `tools/` holds SushiSkills' checkers and `tools/check_all.py` passes |  |  | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
