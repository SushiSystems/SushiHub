# KI-3 Under `--json`, git and pipx write into the event stream

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `cli/sushihub/services/git_ops.py`, `cli/sushihub/services/pipx.py`, `cli/sushihub/services/cli_install.py`
- Cause: the children inherit `hub`'s stdout
- Recognise: lines that are not JSON among the events
- Workaround: skip lines that do not parse as JSON
- Fix: RW-44
