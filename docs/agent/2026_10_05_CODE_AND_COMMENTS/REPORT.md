# Code and comments report

**Status:** Done in nine repositories and committed locally on 2026-10-05, with three C++ fixes that were never built. Nothing is pushed.

## Source comments

Findings printed by `python tools/documentation/check_source_comments.py .`, measured by the
orchestrator before the work and after the last commit.

| Repository | Before | After | Commit |
| --- | --- | --- | --- |
| sushistack | 67 | 0 | `d148931` |
| sushicore | 60 | 0 | `a66f9c0` |
| sushitrack | 13 | 0 | `755fd3d` |
| sushidsp | 1 106 | 0 | `ecf48ca` |
| sushiweb | 801 | 0 | `3310f3d2` |
| sushiai | 714 | 0 | `288bfc7` |
| sushiblas | 1 051 | 0 | `aaf4c15` |
| sushiruntime | 1 299 | 8 | `7b584c9` |
| sushiengine | 12 174 | 253 | `027a0783` |

The eight in sushiruntime sit on four empty compiler probe files in the root that git does
not track. The 253 in sushiengine sit in files that hold the owner's uncommitted work; no agent
edited them.

### How it was done

Each repository was cut into folders of a few hundred findings. One agent worked a folder, a
second reviewed it, a third corrected what the review graded Critical or Important and
continued any unfinished part. Large flat folders in sushiengine (`tests/unit`, the shaders)
were worked in successive rounds by one unit, so that one document received their reasoning.
Reasoning moved to a README or topic document inside the folder; the source keeps one line
that states the invariant and names the document.

### Proof that only comments changed

The orchestrator compared every changed source file with its committed text.

| Repository | Files compared | Differ outside comments |
| --- | --- | --- |
| sushistack, sushitrack | 41 Python files | 0, by syntax tree without docstrings |
| sushiruntime | 205 | 0 |
| sushidsp | 345 | 0 |
| sushiblas | 313 | 0 |
| sushiweb | 515 | 5 flagged, 0 real |
| sushiai | 60 | 5 flagged, 0 real |
| sushiengine | 2 033 | 21 flagged: 19 are the owner's files and were not committed, 2 are not real |

The comparison strips comments and whitespace from C-family and TypeScript text. It reads a
quote inside a regular expression literal as the start of a string, which is what flagged the
twelve files that are not real; each was then read line by line and differs in comment lines
only. sushicore is not in the table: a defect fix shared its working tree, so its commit holds
code changes by design.

### What the reviews found

The recurring finding was reasoning shortened in place instead of moved: a comment run cut to
one line whose "why" reached no document. Reviews graded it Critical in eleven sushiengine
units, one sushiblas unit and one sushiruntime unit, and each correcting agent restored the
passages the review named. Nobody compared every shortened comment with its document. As a
whole-repository check, about 500 000 words left sushiengine's source comments and about
720 000 were written into 241 documents.

Known losses and limits:

- sushiblas: 130 `@param` lines that restated the signature were dropped and exist only in git
  history; eight that stated a rule were restored.
- sushiengine `engine/domain/animation` and its siblings: 128 `@param` lines were removed, at
  least 23 of which stated a unit, a sentinel or a precondition. The correcting agent's report
  should be read before relying on those headers.
- sushiruntime `include/`: about 45 in-body lines rely on the file block's citation only.
- The new documents are comments regrouped under headings more than they are written prose;
  several reviews said so. They pass the layout checker.
- In sushiengine's shader unit, rounds two to seven did nothing: after round one, `git status`
  could no longer tell the owner's files from the unit's own edits, so the rule that protects
  the owner's work stopped every later round. The owner's files were protected; the rounds
  were wasted.

## Defects

| Repository | Commit | Defect | Proof |
| --- | --- | --- | --- |
| sushicore | `a66f9c0` | Provisioning failures were caught and dropped | 906 tests pass |
| sushicore | `e25b1b0` | Downloads were opened and run unverified | 961 tests pass |
| sushiweb | `298f387d` | Mail with verification and reset links reached the production log | 11 tests in the package, 2 365 in the workspace pass |
| sushiblas | `a687331` | `truncated_normal` ignored its bounds; `SB_ASSERT` lost its message; the logger could hang on shutdown; `IO` read unchecked | **Not built** |
| sushitrack | `073b081` | Exception text used as a printf format; exceptions crossing the C boundary; a log call per element in a hot loop | **Not built** |
| sushiai | `c05a838` | An unlisted operation fell through to a default kernel | **Not built, no test** |

### What the owner has to build and see

- **sushiblas.** `tests/functional/regression/test_io.cpp` and `test_logger.cpp` are new and
  registered in `tests/CMakeLists.txt`. `Unit_DistributionsTest.TruncatedNormal*` must pass;
  on the previous code `TruncatedNormalStaysInsideItsBounds` fails. The `SB_ASSERT` death test
  runs only in a Debug build. `BinRoundTripsDeviceAllocatedStorage` skips on a CPU device.
- **sushitrack.** `CAPIBoundaryExceptionTest.*` and `GatingLogVolumeTest.*` must pass and fail
  on the previous sources. `KalmanFilterRegistryTest.UnregisteredTypeLogsTheTypeAndReturnsNull`
  passes either way; it pins a message.
- **sushiai.** No test exists. The helpers are private; a test needs a seam the owner picks.
- **sushiblas does not pass a syntax check against the sibling sushiruntime checkout**, before
  or after these changes: `USMAllocator`, `IAllocatorStrategy` and `Memory::Strategies` are not
  found. This also blocks sushiai's syntax check. It was not caused by this work and was not fixed.

### What stays open in the fixed areas

- sushicore: entries without a `sha256` install as before and are reported; the owner pins
  the digests. The CUDA keyring package on Linux, the apt keys piped into gpg and the git
  clones are not verified. Two public functions that return `None` report failure only through
  the log.
- sushiweb: a production deployment without `RESEND_API_KEY`, and the admin console always,
  deliver no mail. The log now says so in one line.
- sushitrack: `update` and `get_tracklets` report failure as zero tracks; a log callback that
  throws still crosses the boundary.
- sushiblas: `truncated_normal` costs 24 `erfc` calls per FLOAT32 element and 53 per FLOAT64.

## CI

Eight repositories got a `checkers` job that runs the four checkers and the tool tests on
Linux and Windows (`build(ci)` commits). Every step passes on the committed tree, run locally.
sushiruntime and sushiblas leave the layout checker out, because `docs/api` is still outside
the tree. sushiengine's workflow was not changed. No workflow has run on GitHub.

## Process failures in this programme

- Two agents wrote a scratch script of the same name; one ran the other's once. It applied
  that agent's own planned edits in sushicore and nothing else. Scratch files have carried the
  agent's label since.
- Two tasks ran in sushicore in one wave and their changes could not be separated by file.
- A first fix for the sushiweb mail leak made the development sender throw in production,
  which would have stopped the admin console at start-up. The review caught it and the
  orchestrator replaced it.
- sushiweb had no ignore rule for Python bytecode, and eight `.pyc` files were committed with
  the tools. They were removed from the index and the rule was added (`54dab9ef`).

## Not done

- Restructuring named in the spec's "Not in this programme".
- A logger for sushidsp and sushiweb.
- The 253 findings in the owner's uncommitted sushiengine files.
- `docs/api` in three repositories, and the layout step in two CI jobs.
- No build, no C++ test run, no shader compiled.
