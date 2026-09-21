# Task 20: `hub doctor` groups its table and lists what is missing

Plan: `D:/Projects/sushicore/docs/agent/plans/2026-09-21-terminal-components.md`, Wave 7, Task 20.
Every command ran from `D:/Projects/sushistack/sushihub/cli` with `PYTHONPATH=D:/Projects/sushicore`.
Nothing was installed, staged or committed.

## Files changed

- `sushihub/cli/sushistack/setup/steps.py`
- `sushihub/cli/tests/test_doctor_table.py` (new)
- this report

## What changed in `steps.py`

- `run` keeps the rows in a variable, hands `console.table` the same columns and the same
  `[list(row) for row in rows]` as before, and adds `group_by="Owner"`.
- `DetectStep.summarize_inventory(rows)` sits directly under `inventory_rows`. It is a static method that takes
  the rows and returns `(counts, missing_rows)`. Counts are ordered OK, MISSING, NOT NEEDED, then any other
  status by first appearance; a status no row carries has no entry.
- `run` calls `_report_inventory(rows)` after the platform note and before the module readiness. That private
  method does the printing, so the pure function prints nothing. It prints the summary line, and only when a row
  is MISSING it prints `console.warn("Needs attention")`, one `console.info` per missing row and
  ``Run `hub install` to provision what is missing.``
- Status texts: `_status(...)` returns only `OK` or `MISSING`, and the toolchain and dependency rows add
  `NOT NEEDED`. The summary labels are `OK`, `missing`, `not needed`; any other status is printed under its own
  text (tested with a made-up `STALE`).
- The attention lines go through `_literal`, which escapes Rich markup on a terminal and leaves the text alone
  in `--json` (see "Found wrong" item 2).

## Baseline and result

Baseline before any edit:

```
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 54%]
........................................................................ [ 72%]
........................................................................ [ 90%]
.......................................                                  [100%]
399 passed in 6.82s
```

The new test file before the implementation (9 failed, 3 passed). The failures were the missing
`summarize_inventory`, the missing summary line and the missing attention list; the 3 that passed already held
with the old code (the JSON event is ungrouped, and the success result):

```
FAILED tests/test_doctor_table.py::test_summarize_counts_each_status_under_its_own_text
FAILED tests/test_doctor_table.py::test_summarize_leaves_out_a_status_no_row_carries
FAILED tests/test_doctor_table.py::test_summarize_counts_an_unforeseen_status_under_its_own_text
FAILED tests/test_doctor_table.py::test_summarize_returns_the_missing_rows_in_table_order
FAILED tests/test_doctor_table.py::test_doctor_prints_groups_then_summary_then_attention_list
FAILED tests/test_doctor_table.py::test_doctor_prints_no_attention_list_when_nothing_is_missing
FAILED tests/test_doctor_table.py::test_doctor_keeps_brackets_in_a_missing_detail_on_a_terminal
FAILED tests/test_doctor_table.py::test_doctor_json_carries_the_summary_and_attention_as_line_events
FAILED tests/test_doctor_table.py::test_doctor_json_message_holds_a_bracketed_detail_unescaped
9 failed, 3 passed in 0.16s
```

After the implementation (the same command `python -m pytest tests -q`, run twice, the second time after a
line-length fix in the test file):

```
...................................................                      [100%]
411 passed in 7.03s
```

399 existing + 12 new, none lost.

## The `--json` table event

`test_doctor_json_table_event_is_the_ungrouped_one` runs `run` under the JSON renderer, then makes the pre-change
call by hand (`console.table(columns, [list(row) for row in rows], title="Environment inventory")`) and asserts
the two table events are equal, carry the four columns and the given rows, and have no `group_by` key. It passes.

The event stream around it gains line events (the summary, `Needs attention`, one line per missing row, the
`hub install` hint); the JSON test proves they arrive as `line` events with levels `info` and `warn`.

## Does anything pin the `hub --json doctor` sequence?

No. `sushihub/cli/tests/` has no test that runs `doctor`. `sushihub/gui/tests/event_test.cpp` (line 83) only
checks that every line of `events/doctor.jsonl` parses; `doctor.jsonl` is a recorded sample, not a golden
sequence. The new line events parse like the existing ones. I did not touch the fixture. It is now older than
what `hub --json doctor` prints; re-recording it is the owner's call (the fixtures README says how).

## What the owner will see

Fake 100-column console with colour on (84 colour codes in the raw output, stripped below). Rows: one OK, one
MISSING, one NOT NEEDED, two owners. Produced by a scratch script outside the repository:

```
Environment inventory

  Component    Status      Detail                                                                  
───────────────────────────────────────────────────────────────────────────────────────────────────
shared
  cmake        OK          /usr/bin/cmake                                                          

sushiruntime
  adaptivecpp  MISSING     AdaptiveCpp (acpp)                                                      
  cuda         NOT NEEDED  no present module declares it                                           
[INFO] Vendored dependencies go in one folder: /deps
[INFO] Remove the whole install by deleting that folder (`hub remove --all` does it for you).
[INFO] System prerequisites kept outside that folder: the host compiler (gcc) plus the -dev 
packages (hwloc, gtest, opencl), git, and the toolkit for the detected GPU.
[INFO] 1 OK | 1 missing | 1 not needed
[WARN] Needs attention
[INFO] adaptivecpp  AdaptiveCpp (acpp)
[INFO] Run `hub install` to provision what is missing.
```

The `[INFO]`/`[WARN]` prefixes are this console's icon set; the owner's theme may draw others.

## Syntax check

```
python -m py_compile sushistack/setup/steps.py tests/test_doctor_table.py; echo "exit $?"
exit 0
```

## The `hub install` hint

`sushihub/cli/README.md` line 115 says `hub install` "merges every `*.deps.toml` fragment ... and installs the
ones that are missing", and line 33 lists it as the command that installs dependencies. The hint matches.

## Found wrong or worth a decision

1. **The plan miscounts the notes.** It says "the existing two `console.info` lines about vendored
   dependencies". `run` prints three: two always, and one system-prerequisites line that differs by platform.
   I placed the summary after all three, just before "Module readiness:". That leaves three lines between the
   table and its summary; moving `_report_inventory(rows)` above them is a one-line change if the owner prefers
   the summary directly under the table.
2. **Rich markup swallows bracketed details.** `console.info` and `Table` cells are read as Rich markup.
   Real manifest details contain brackets (`imgui[glfw-binding,opengl3-binding]`, `hdf5[core,zlib]`).
   Checked with Rich directly: `console.print("... (imgui[glfw-binding,opengl3-binding])")` prints
   `... (imgui)`. For the attention list I escape the text on a terminal and pass it raw in `--json` (`_literal`,
   tested both ways). This is a workaround for a missing literal-print path on sushicore's `Console.info`. The
   table cell has the same loss (`Text.from_markup` in `sushicore/ui/table.py`, unchanged since Task 19). I read
   that from the code and did not run the table on a bracketed cell. Suggest a follow-up in sushicore: a
   literal option for `info` and for table cells.
3. `run` delegates the printing to a private method `_report_inventory`, beside the existing
   `_report_readiness`, instead of inlining it. The summary function itself prints nothing.

## What I did not do

- Did not run `hub doctor` or `hub --json doctor` against the real workspace (the tests replace
  `inventory_rows`, the readiness report and `deps_dir`).
- Did not touch `sushihub/gui/`, its fixtures, `sushihub/contract/`, `pyproject.toml`, the README, the
  changelog or sushicore. The hub README and changelog probably need a line for this change; that was outside my
  file list.
- Did not run `check_source_comments.py` (there is no `tools/documentation/` in this repository).
- Did not stage or commit.
