# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-70 | P1 | open | Let hub bump skip modules, reach tools-only repositories and print the pin it writes | hub bump --skip X leaves X untouched, lists sushiskills and sushiweb as tools-only, and prints the range it writes |  |  | 2026-11-16 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-9 | own | The GUI commands are listed where they do not work | run them from a clone | RW-49 |  | 2026-10-19 |
| KI-10 | own | The tool overrides are named after sushiruntime | use the names as they are | RW-50 |  | 2026-10-19 |
| KI-12 | own | A module `pyproject.toml` without a name ends `install-cli` in a `KeyError` | give the module a name | RW-52 |  | 2026-10-19 |
