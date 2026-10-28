# KI-4 `hub install --customize` opens its picker under `--json`

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `cli/sushihub/services/customize.py`
- Cause: it decides on `sys.stdin.isatty()` alone
- Recognise: a picker on a terminal during a JSON run
- Workaround: leave `--customize` out under `--json`
- Fix: RW-45
