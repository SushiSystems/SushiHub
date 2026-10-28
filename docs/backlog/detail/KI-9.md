# KI-9 The GUI commands are listed where they do not work

The row of this entry is in `docs/backlog/COMMANDS.md`. This file holds what did not fit the row.

- Origin: own
- Where: `cli/sushihub/gui_config.py`
- Cause: `hub gui build`, `test`, `run` and `clean` assume the workspace root is a clone of this repository
- Recognise: the commands fail in any other workspace
- Workaround: run them from a clone
- Fix: RW-49
