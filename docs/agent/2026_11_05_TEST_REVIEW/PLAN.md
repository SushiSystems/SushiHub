# Test review: plan

**Status:** Open — T1 done; T2 and M2 wait for a lead that may build C++; M1 is next

Applies the verdicts of `REPORT.md`, in hierarchy order: the shared helpers, adapters and seams the
rewrites need come first, then the defects the review found, then each module's tests. A module job
applies every record of its module: rewrite, resize, split, merge and delete as the record says, and
writes each add. Nothing in a module job changes production code except a seam a job above built.

## Jobs

| Job | Files | Waits on | Status |
| --- | --- | --- | --- |
| T1 | Ports and in-memory adapters for git, the session client, pipx, the release host and the console |  | done |
| T2 | Size prefixes on every gui suite |  | todo: needs a C++ build to prove, skipped by the 2026-11-07 lead |
| M1 | the tests of `cli` (34 files): 125 rewrite, 33 resize, 21 split, 31 merge, 7 delete | T1, T2 | todo |
| M2 | the tests of `gui` (5 files): 7 rewrite, 15 resize, 12 split, 1 merge, 2 delete | T1, T2 | todo: needs a C++ build, skipped by the 2026-11-07 lead |

## Acceptance

- **T1.** Each command reaches these through a port, and each adapter keeps its port's promise with no subprocess or network. Build: the CLI's test command.
- **T2.** Every gui test carries a size and the size checker passes. Build: the repository's test checkers.
- **M jobs.** Every record of the module is applied: no test the report deletes remains, every kept and
  new test passes at the size its label states, and the module's tests pass through the project's own
  test command. Build: that command over the module.

The owner chooses inline or parallel mode.
