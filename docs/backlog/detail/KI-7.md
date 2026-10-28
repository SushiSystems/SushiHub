# KI-7 The desktop application never reads the child's stderr

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `gui/src/bridge/Process.cpp`
- Cause: the bridge reads stdout alone
- Recognise: a traceback from `hub` and the readiness report never reach the window
- Workaround: run the command in a terminal
- Fix: RW-48
