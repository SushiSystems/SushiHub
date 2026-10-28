# KI-5 `hub --json` with no subcommand prints help text

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `cli/sushihub/cli.py`
- Cause: the help path ignores the output mode
- Recognise: plain help on stdout and no `result` event
- Workaround: name a subcommand
- Fix: RW-46
