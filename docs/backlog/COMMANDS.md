# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-62 | P3 | open | Give the doctor's detect step an injected inventory and console | test_doctor_table patches no repository name |  | `docs/agent/2026_11_05_TEST_REVIEW/REPORT.md` | 2026-11-07 |
| RW-63 | P3 | decision | Find an oracle for the catalog's module order other than catalog.toml | test_the_catalog_holds_the_eight_stack_modules reads its order from a source the code does not |  | `docs/agent/2026_11_05_TEST_REVIEW/REPORT.md` | 2026-11-07 |
| RW-64 | P3 | open | Give hub pin a git port so its tag lookup is reached in memory | test_pins patches no pins function |  | `docs/agent/2026_11_05_TEST_REVIEW/REPORT.md` | 2026-11-07 |
| RW-65 | P3 | open | Split a text parse from the file read in module_manifest and tool_paths | the manifest and tool-path value tests in test_module_manifest and test_tool_paths are small |  | `docs/agent/2026_11_05_TEST_REVIEW/REPORT.md` | 2026-11-07 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-9 | own | The GUI commands are listed where they do not work | run them from a clone | RW-49 |  | 2026-10-19 |
| KI-10 | own | The tool overrides are named after sushiruntime | use the names as they are | RW-50 |  | 2026-10-19 |
| KI-12 | own | A module `pyproject.toml` without a name ends `install-cli` in a `KeyError` | give the module a name | RW-52 |  | 2026-10-19 |
