# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-67 | P1 | open | Report every dependency pinned at more than one version with hub pins | on a fixture with SushiRuntime at two versions hub pins lists the split and exits 1 |  |  | 2026-11-16 |
| RW-68 | P1 | open | Carry a release up the depends_on graph with hub bump | on a fixture graph hub bump moves pins lowest tier first and --dry-run changes no file |  |  | 2026-11-16 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-9 | own | The GUI commands are listed where they do not work | run them from a clone | RW-49 |  | 2026-10-19 |
| KI-10 | own | The tool overrides are named after sushiruntime | use the names as they are | RW-50 |  | 2026-10-19 |
| KI-12 | own | A module `pyproject.toml` without a name ends `install-cli` in a `KeyError` | give the module a name | RW-52 |  | 2026-10-19 |
