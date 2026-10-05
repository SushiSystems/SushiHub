# Licence migration

**Status:** Shipped — ten repositories done on 2026-10-05; see `REPORT.md`.

Programme 2 of 5 in the estate refactor. It moves every Sushi Systems repository in scope from
Apache-2.0 to the licence model the owner decided on 2026-10-05, using the header template and
the rules that programme 1 fixed in SushiSkills. The evidence is each repository's
`docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md`, section "Licence".

## Owner decisions this rests on

| # | Decision |
| --- | --- |
| D1 | Shared repositories: PolyForm Noncommercial 1.0.0; companies buy a commercial licence |
| D2 | `sushiengine` and `sushiweb` are closed: all rights reserved |
| D3 | `sushihub` and `sushicore` take the non-commercial licence; the commercial agreement covers customers |
| D4 | The single licensor and copyright holder is Sushi Systems |
| D5 | `sushifx` keeps the AMD licence; only the notice of Sushi changes is corrected |
| D6 | The header is the boxed block of `source-comments` in SushiSkills |

## Scope

| Repository | Licence after | Project line |
| --- | --- | --- |
| sushistack | PolyForm Noncommercial 1.0.0 | `SushiHub - https://github.com/SushiSystems/SushiHub` |
| sushicore | PolyForm Noncommercial 1.0.0 | `SushiCore - https://github.com/SushiSystems/SushiCore` |
| sushiruntime | PolyForm Noncommercial 1.0.0 | `SushiRuntime - https://github.com/SushiSystems/SushiRuntime` |
| sushiai | PolyForm Noncommercial 1.0.0 | `SushiAI - https://github.com/SushiSystems/SushiAI` |
| sushiblas | PolyForm Noncommercial 1.0.0 | `SushiBLAS - https://github.com/SushiSystems/SushiBLAS` |
| sushidsp | PolyForm Noncommercial 1.0.0 | `SushiDSP - https://github.com/SushiSystems/SushiDSP` |
| sushitrack | PolyForm Noncommercial 1.0.0 | `SushiTrack - https://github.com/SushiSystems/SushiTrack` |
| sushiweb | All rights reserved | `SushiWeb - https://sushisystems.io` |
| sushifx | AMD's, unchanged | none; no Sushi header is written |
| sushiengine | All rights reserved | `SushiEngine - https://sushisystems.io` |

`sushiengine` was first deferred because its working tree held uncommitted work. The owner asked
for it not to wait; `REPORT.md` says how the owner's files were kept out of the commits.

## Defaults taken where the owner has not decided

Each avoids an action that cannot be taken back.

- **sushitrack benchmark data** (MOT17, MOT20, DanceTrack annotations, 234 MB tracked) stays in
  git. `NOTICE.md` names each dataset, its source and its licence. Removing it is a separate
  decision.
- **sushidsp and the Steinberg ASIO SDK:** no build setting changes. `NOTICE.md` records that a
  build with ASIO falls under Steinberg's terms and that no binary with ASIO is distributed
  until a signed agreement exists.
- **Published Apache-2.0 versions** are named, not hidden: each public repository's README and
  `NOTICE.md` say which versions stay under Apache-2.0.
- **Versions and tags:** no version number changes and no tag is created. The licence change
  is breaking, so each changelog entry names it; the owner cuts the releases.

## Design

### 1. One tool writes every header

`tools/licensing/write_license_block.py` in SushiSkills is the only place that knows how a
header is written. It takes a repository root and the project line, and for each tracked
source file it replaces the old license block or inserts the new one.

| Aspect | Rule |
| --- | --- |
| Files | Tracked files with the suffixes `check_source_comments.py` reads, plus `.cmake`, `.sh` and `CMakeLists.txt` |
| Skipped | `third_party/`, `node_modules/`, `build/`, generated files named with `--skip` |
| Old block, C family | A leading run of `/* ... */` lines, or a leading `//` run that holds "Copyright" |
| Old block, `#` family | A leading `#` run that holds "Copyright" or "Licensed"; any other leading comment is kept below the new block |
| Kept | A shebang, a source encoding line, a byte order mark, the file's newline style, everything below the block |
| Year | The year of the commit that added the file, from git |
| Variants | Non-commercial by default; `--closed` writes "All rights reserved. No licence is granted." |
| Ported files | `--upstream PATH=LINE;LINE` appends upstream notice lines to that file's block |
| `--report` | Writes nothing; prints each file whose header would change, and exits 1 if there is one |
| Idempotence | A second run changes nothing |

The lines it writes come from `check_source_comments.py`, so the checker and the writer cannot
disagree. A run with `--report` that prints nothing is the proof a repository is done; it also
serves the closed repositories, whose lines differ from the checker's defaults.

It is the one tool under `tools/` that writes files. `tools/README.md` and `project-tools` say so.

### 2. What each repository carries afterwards

| File | Non-commercial repository | Closed repository |
| --- | --- | --- |
| `LICENSE` | The PolyForm text and Required Notice, byte for byte as in SushiSkills | The proprietary notice below |
| `COMMERCIAL.md` | As in SushiSkills, with the repository's name | absent |
| `NOTICE.md` | Third-party components, ported files, redistributed binaries, data, earlier versions | The same, without earlier versions |
| Package metadata | The PolyForm identifier in each `pyproject.toml`; `license-files` where the build backend allows it, see `REPORT.md` | `"license": "UNLICENSED"` in each `package.json` |
| README, docs, site copy | "source-available, free for non-commercial use"; never "open source" | "proprietary"; never a licence name |
| Other licence copies | `docs/LICENSE` and similar duplicates removed; the README links the root file | the same |
| Changelog | One line under `## Unreleased`, scope `licence` | the same |

Closed `LICENSE` text:

```
Copyright (c) <first year>-2026 Sushi Systems. All rights reserved.

This software and its source code are proprietary to Sushi Systems. No licence, express or
implied, is granted to use, copy, modify or distribute any part of it. Access to this
repository does not grant any such right. Use is permitted only under a written agreement
signed by Sushi Systems.

Third-party components keep their own licences; see NOTICE.md.
```

### 3. Facts the audit fixed per repository

- **sushiruntime:** the LLVM exception goes with the Apache text; `docs/LICENSE` is a second,
  different licence file and is removed. `NOTICE.md` lists the staged SYCL runtime, Unified
  Runtime and hwloc binaries with their licences read from upstream; the open redistribution
  question stays open and is stated.
- **sushiblas:** `gemm.hpp` and `syrk.hpp` are ported from portBLAS (Codeplay, Apache-2.0) and
  keep that notice in their block; `NOTICE.md` becomes the single notice file and keeps a copy
  of the Apache-2.0 text for that part under `third_party/licenses/`.
- **sushitrack:** every file ported from ByteTrack-cpp (MIT), gatagat/lap (BSD-2-Clause),
  OC_SORT and YOLOX (Apache-2.0) is found by comparing against `third_party/`, and carries its
  upstream line. Files that are not ports carry the Sushi block alone.
- **sushiai:** public history under CC0, MIT and Apache-2.0 is named in `NOTICE.md`.
- **sushistack, sushicore:** PyPI releases and tags under Apache-2.0 are named.
- **sushiweb:** the site copy in three languages says "open source under Apache-2.0"; it is
  rewritten to the new model in English, Turkish and Norwegian, through `marketing-copy`. The
  `ProjectLicense` type and data follow. Fonts and the MOT17 media get `NOTICE.md` entries.
- **sushifx:** `README.md` states what Sushi changed, that the changes are MIT like the tree,
  and corrects its status paragraph. No file header changes.

## How it runs

| Wave | Work | Who |
| --- | --- | --- |
| 0 | The writer, its tests and its documentation in SushiSkills | Orchestrator, inline, test first |
| 1 | The writer run over the eight repositories; `--report` clean | Orchestrator; mechanical |
| 2 | Per repository: `LICENSE`, `COMMERCIAL.md`, `NOTICE.md`, metadata, prose, duplicates, changelog | One worker per repository; the file sets are disjoint because the repositories are |
| 3 | Per repository: review against this spec, then fixes | One reviewer per repository |
| 4 | Commit per repository, local, staged by path | Orchestrator |

Nothing is pushed and no build, test or project CLI is run. Header text sits in comments, so
no behaviour changes; the proof is the writer's `--report` and each reviewer's reading.

## Acceptance

1. `write_license_block.py <root> --report` prints nothing for each repository in scope.
2. `git grep -il apache` in each repository lists only `NOTICE.md`, licence texts of
   third-party parts, the sentence about earlier versions, changelog history and `docs/agent/`,
   `docs/archive/`.
3. No README, manual page or site string calls a Sushi product open source.
4. Every `pyproject.toml` and `package.json` in scope declares its licence.
5. Each repository's `NOTICE.md` lists every vendored, ported and redistributed part its audit
   report names.
6. In `sushiengine`, no path the owner had modified is committed by this work.

## Open risk

The legal points in programme 1's spec stand. Two are sharper here: `sushitrack` ships
annotation data under CC BY-NC-SA terms that the repository's licence cannot override, and a
`sushidsp` binary built with ASIO needs Steinberg's signed agreement before it leaves the machine.
