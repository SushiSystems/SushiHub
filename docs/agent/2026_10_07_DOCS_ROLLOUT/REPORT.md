# Documentation rollout: report

**Status:** Built 2026-10-07, committed locally on `main` in nine repositories. Nothing is pushed,
no workflow has run, the site is not deployed.

The design is `SPEC.md` beside this file.

## What exists

| Repository | Publish list | Command | Bundle built here | Release workflow |
|---|---|---|---|---|
| sushistack | all four sections, no API | `hub docs bundle` | 0.2.0, 8 pages | two jobs appended |
| sushicore | all four sections, no API | `python -m sushicore.docs_bundle` | 0.8.0, 11 pages | two jobs appended |
| sushiruntime | all four sections, API | `sr docs bundle` | 0.3.0, 9 pages | new |
| sushiblas | guides, architecture, reference, API | `sb docs bundle` | 0.1.0, 6 pages | new |
| sushiai | all four sections, API | `sa docs bundle` | 0.1.0, 8 pages | new |
| sushidsp | all four sections, API | `sd docs bundle` | 0.1.0, 18 pages | new |
| sushitrack | all four sections, no API | `st docs bundle` | 1.0.0, 21 pages | new |
| sushiengine | getting started, guides, architecture; no API | `se docs bundle` | 0.1.0, 22 pages | new |

Seven repositories carry `docs/guides/FAQ.md`. The engine's waits for a binary install page
(decision R4).

`apps/docs` in the sushiweb repository pins the eight bundles as files and builds 466 pages, 464
of them indexed for search; its smoke test passes. The same repository holds
`tools/sync_manifest.mjs` and `.github/workflows/docs-manifest.yml`, which follow the publishers'
releases and open one pull request against the manifest.

## Evidence

- Every bundle above was built by the command in its row on 2026-10-07, at the repository's
  `HEAD`, and the archive's `commit` equals that `HEAD`. The engine's was built with
  `python -m sushicore.docs_bundle`; no `se` command was run.
- CLI suites after the change: sushiruntime 135, sushiblas 79, sushiai 81 (the 14 end-to-end
  tests that start built programs were deselected), sushidsp 90, sushitrack 116, sushistack 356,
  sushiengine 412 in the eleven files that start no program. SushiCore: 1057.
- The site: 22 test files, 176 tests; `tsc` clean; build and `e2e/smoke.mjs` pass.
- Each workflow file parses as YAML, its embedded Python compiles, and its version pattern finds
  the version in the repository's real file.

## Not verified

- No workflow has run. There is no runner on this machine.
- No release carries a bundle, so the sync script has only been run against repositories without
  one: it printed "has no release" eight times, six of them because no token was set.
- The release job installs SushiCore from PyPI, and no published SushiCore carries
  `docs_bundle`. Until one does, the job fails at its bundle step.
- The sync script and its tests were written together, not test first.

## Review

One reviewer read the commits of the six CLI registrations, the workflows and the sync script.
It reported one critical and twelve important findings.

Fixed, each with a test where code changed:

| Finding | Fix |
|---|---|
| `release.yml` passed no secrets to the called `ci.yml`, so the sibling checkouts of sushiblas, sushiai and sushiengine would fail on a tag | `secrets: inherit` in all eight |
| A bundle attached again has the same bytes and a new asset address; the manifest kept the dead one | The update compares the address too (`manifest_update.mjs`) |
| `node ... \| tee` hid the script's exit code | `set -o pipefail` |
| One new pull request a day while the first stays open | One branch, `docs-manifest/sync`; an open pull request is updated |
| `gh pr create` needs a repository setting that is off by default | Listed in the site's README |
| sushiblas wrote Doxygen XML into `docs/api-site/xml`, which was not ignored | `.gitignore` |
| Four CLIs had no test that `docs bundle` reaches the producer | Two tests each, the same in all four |
| sushiruntime and sushiai had no changelog lines | Committed |
| The page order claimed to walk as the layout checker does and stopped at documents outside the four sections | It now reads on through every document outside `agent/` and `archive/` |
| sushiruntime's summary was not a sentence of its README | The README's first sentence |
| sushiai and sushidsp published their Doxygen main page | Excluded |

Not fixed; these are the owner's to decide:

1. **The release job exists in eight copies.** A reusable workflow in the public SushiCore
   repository would hold it once. It is a boundary between repositories, and it can only be
   called once SushiCore is pushed.
2. **sushitrack publishes `reference/BENCHMARKS.md`.** It compares against ByteTrack and OC-SORT,
   and says that the date, the commit and the machine of the runs were not recorded.

Minor findings, deferred:

- sushitrack's `ci.yml` has no branch filter on `push`, so a tag runs CI twice.
- In sushistack and sushicore, `publish` does not wait for `ci`; a tag whose CI fails still goes
  to PyPI. A pre-release tag fails the bundle job with "declares None".
- sushidsp's docs build does not create its output folder; whether the runner's Doxygen does is
  not known.
- `gh release create` publishes before the upload; a repository with immutable releases refuses
  the upload.
- A publisher removed from `publishers.json` keeps its manifest entry, with no line printed. A
  version that goes backwards is ignored without a line.
- `workflow_dispatch` from another branch opens a pull request with that branch's commits.
- sushiweb's `ci.yml` runs the Python checkers only, so the site's tests run in no workflow.
- `hub docs bundle` runs in any checkout that has a publish list, not only SushiHub's; its
  docstring and message say otherwise. Its `result` payload is empty.
- sushitrack's bundle test commits without `commit.gpgsign=false`.
- Differences between the registrations that the repositories do not force: `K_API_XML` is a
  `Path` in sushiblas and a string elsewhere; `program=` is spelt three ways; `_docs_alias`
  repeats the bare callback's body; the test files have three names.
- The producer and the checker disagree on a link spelt in another case, on three link forms and
  on fences longer than three backticks.
- sushidsp publishes nine `reference/spice/**/README.md` pages of working notes. Four FAQ pages
  print the address of the excluded security policy. All seven publish `KNOWN_ISSUES.md`.
- The summaries of sushiai and sushitrack are fragments of their README's first sentence.
- The header comment of the new `release.yml` files says the workflow has not run; it goes stale
  on the first tag.
- `sync_manifest.mjs` sends the token to any address it is given; the site's reader checks the
  host first.

## What the FAQ work found in the manuals

The FAQ writers answered only what each manual says. What they could not answer is a list of
gaps:

- Where to report a problem: no page in sushistack, sushicore or sushitrack says.
- Which operating systems are supported: no repository lists them.
- What each module is for: sushistack's manual names the parts and does not describe them.
- sushiengine's manual describes a source build only.

## Left in the working trees

- sushiengine's changelog has no line for this work. The file holds the owner's uncommitted
  changes and uses another format (`## [Unreleased]`).
- sushiai's `docs/guides/CLI_GUIDE.md` describes `sa docs` in a file that held another writer's
  uncommitted changes; it is not committed.
- sushiengine's `docs/guides/COMMAND_LINE_INTERFACE.md` was over the 900-line ceiling at 994
  lines and is now 1004.
- In `sb --help`, the Documentation panel now lists after Diagnostics, because Typer lists a
  group after the plain commands.

## Order for the owner

1. Release SushiCore, so that a published version carries `docs_bundle`.
2. Raise the `sushicore>=` floor in each CLI to that version.
3. Push the eight publishing repositories; tag one to see the release job run.
4. In sushiweb: create the secret `SUSHI_DOCS_TOKEN`, turn on "Allow GitHub Actions to create
   and approve pull requests", create the Vercel project and `docs.sushisystems.io`.
