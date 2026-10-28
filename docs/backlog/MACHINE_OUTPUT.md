# Machine output

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-3 | own | Under `--json`, git and pipx write into the event stream | skip lines that do not parse as JSON | RW-44 |  | 2026-10-19 |
| KI-4 | own | `hub install --customize` opens its picker under `--json` | leave `--customize` out under `--json` | RW-45 |  | 2026-10-19 |
| KI-5 | own | `hub --json` with no subcommand prints help text | name a subcommand | RW-46 |  | 2026-10-19 |
| KI-7 | own | The desktop application never reads the child's stderr | run the command in a terminal | RW-48 |  | 2026-10-19 |
