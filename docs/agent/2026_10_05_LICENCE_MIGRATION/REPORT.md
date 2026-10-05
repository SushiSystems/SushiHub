# Licence migration report

**Status:** Ten repositories done and committed locally on 2026-10-05. Nothing is pushed.

## What was done

| Wave | Work | Result |
| --- | --- | --- |
| 0 | `tools/licensing/write_license_block.py` in SushiSkills, 21 tests | Commits `17bc9ad`, `08a46fe` there |
| 1 | The writer run over eight repositories | 2 525 source files carry the new block |
| 2 | One worker per repository: `LICENSE`, `COMMERCIAL.md`, `NOTICE.md`, prose, changelog | 8 workers |
| 3 | One reviewer per repository, then one fixing agent where needed | 2 Critical and 19 Important findings; see below |
| 4 | Package metadata, three leftover fixes, one commit per repository | Orchestrator |

| Repository | Files with the block | Licence after |
| --- | --- | --- |
| sushistack | 146 | PolyForm Noncommercial 1.0.0 |
| sushicore | 164 | PolyForm Noncommercial 1.0.0 |
| sushiruntime | 244 | PolyForm Noncommercial 1.0.0 |
| sushiai | 180 | PolyForm Noncommercial 1.0.0 |
| sushiblas | 335 | PolyForm Noncommercial 1.0.0; two files keep the portBLAS notice |
| sushidsp | 502 | PolyForm Noncommercial 1.0.0 |
| sushitrack | 136 | PolyForm Noncommercial 1.0.0; sixteen files keep upstream notices |
| sushiweb | 818 | All rights reserved |
| sushiengine | 2 791 | All rights reserved |
| sushifx | none | AMD's MIT, unchanged; the README states what the fork changes |

## Proof

Run on 2026-10-05 after the last edit, for each repository with its project line:

```
$ python D:/Projects/sushiskills/tools/licensing/write_license_block.py <root> --project "<line>" --report
0 files pending
```

All eight print `0 files pending`; `sushiweb` takes `--closed` and three `--skip` globs for
generated files. `cmp` finds `LICENSE` in the seven non-commercial repositories identical to
the one in SushiSkills. After the rewrite, a scan of every removed line found none outside an
old license block, and all 389 rewritten Python files parse. Eight `pyproject.toml` files and
fourteen `package.json` files were read back and declare the licence.

No build, test or project CLI was run. The source changes are comment lines, one string in
`gui/src/ui/screens/ModulesScreen.cpp` and one argument in `bindings/python/setup.py` of
sushitrack; none of it was compiled.

## Review findings and what became of them

Closed by the fixing agents or the orchestrator:

- sushiblas, Critical: the Apache-2.0 text kept for the Codeplay part named Sushi as licensor;
  the verbatim portBLAS notice had been reduced to a table cell. Both restored.
- sushicore, Critical: "commits after `9c0fce1` are under the new licence" was false for the
  18 unpushed commits; the wording now states what each tree carries.
- sushistack: the desktop application printed "Open source"; `cli/README.md` counted the wrong
  number of unsold modules; `NOTICE.md` misdated three unpushed commits.
- sushitrack: `setup.py` still declared Apache-2.0; two inference scripts carried a second
  holder's "All rights reserved".
- sushidsp: a legal claim about ASIO builds beyond the spec, the Steinberg trademark wording,
  two READMEs that named Apache-2.0.
- sushiai: the roadmap's standing Apache-2.0 decision is marked superseded.
- sushiruntime: `NOTICE.md` called the Intel OpenCL runtime optional although the Dockerfile
  installs it.
- The writer stripped upstream lines on a rerun without `--upstream`; it now keeps them.

Not closed:

- The seven `cli/pyproject.toml` files use `license = { text = ... }` and carry no
  `license-files`. The spec's form needs `setuptools>=77` and a licence file inside `cli/`;
  raising a build requirement is the owner's decision. Until then the built `sushihub` and
  module CLI distributions ship no licence text.
- `install.ps1` and other `.ps1`, `.css`, `.mjs` and `.js` files carry no block; the writer
  does not cover those suffixes.
- 51 Minor findings were not acted on.

## Rulings

- The spec was written and executed on the owner's "continue", without a separate review of the
  spec. Cost if wrong: eight local commits to revert, one per repository.
- Package manifests were edited by the orchestrator; workers were barred from build
  configuration by the dispatch block.
- The audit reports under `docs/agent/2026_10_05_ESTATE_AUDIT/` were left untracked in every
  repository but SushiSkills. Two repositories are public and their reports name unfixed defects.
- `docs/LICENSE` in sushiruntime and sushiblas and `NOTICE` in sushidsp were deleted by workers
  on the dispatch's instruction. All three were tracked; git restores them.
- Workers added `third_party/licenses/` with third-party licence texts in sushistack, sushiblas,
  sushidsp and sushitrack so that `NOTICE.md` can point at them.
- The worker for sushiai found the repository private, against the audit, and wrote
  `NOTICE.md` accordingly.

## For the owner

Decisions that block a push or a release:

1. **Unpushed Apache-era commits in public repositories.** sushistack has 3 and sushicore 18
   local commits whose trees carry the Apache-2.0 `LICENSE`. Pushing them publishes that work
   under Apache-2.0. The alternative is to rebuild them as was done in SushiSkills.
2. **sushistack tag `v0.2.0`** exists locally on an Apache-era commit; pushing it publishes
   0.2.0 to PyPI under Apache-2.0.
3. **First version under the new licence** in each repository; no version or tag was changed.
4. **`setuptools>=77` and a licence file inside `cli/`**, so that distributions ship the text.
5. **Customers and `hub`.** `COMMERCIAL.md` is the generic text; the commercial agreement must
   grant engine customers the use of SushiHub and SushiCore.

Legal and factual points only the owner or a lawyer can settle:

6. sushiruntime: PolyForm terms now reach binaries that instantiate the header templates; the
   LLVM exception that exempted them is gone. Redistribution of the SYCL, Unified Runtime and
   hwloc binaries is still unlicensed.
7. sushitrack: the licences of the MOT17 and MOT20 annotations and the origin of the detection
   files are unverified; DanceTrack is for non-commercial research; whether `tracker.cpp`,
   `tracklet.cpp`, `kalman_filter.cpp` and `distance_strategies.cpp` count as ports; Eigen is
   MPL-2.0, which the dependency table does not list.
8. sushiblas: whether `philox.hpp` was written from the paper or adapted from Random123; the
   portBLAS version the tiling came from.
9. sushidsp: the Steinberg agreement; the admission rule for bundled impulse responses and
   HRTF data; the licences of the schematic sources.
10. sushiweb: the licence of the Clash fonts and of the MOT17-derived video and image; LGPL
    binaries that arrive with `next`; whether SushiEngine's site label becomes "proprietary".
11. sushiai: an earlier home-written "BUSL-1.1" licence period that the audit had not named.
12. Many third-party licences in the `NOTICE.md` files are marked "unverified" because no
    licence text was in the tree to read.

## sushiengine and sushifx, done after the first eight

The owner asked for sushiengine not to wait for a clean tree. Its headers were written into
every tracked source file, and only the files whose sole change was the block were committed
(`e1ab59e5`, 2 742 files): each was checked by applying the writer to its committed version and
comparing with the working copy. The licence files followed in `c7bf9c50`. Files with the
owner's own uncommitted changes carry the new block and were left for the owner to commit; so
was `docs/reference/CHANGELOG.md`, which holds the owner's entries beside the line for this
change.

The engine run found three gaps in the writer, fixed in SushiSkills (`12a2f7b`, `512f1ee`): a
tracked file deleted from the working tree stopped it; configure templates and `.inc`
fragments were not covered; an old box with indented rows was left under the new block.
The add-on scaffold under `cli/sushiengine/templates/` is skipped on purpose with `--skip`: it
becomes the user's own source. Shaders carry the block before `#version`; no shader was
compiled to prove that, and GLSL allows comments there.

sushifx: `README.md` now states what builds, that the prebuilt Vulkan DLL is AMD's and still
carries the defect, that the import leaves out 49 ignored binaries, and whose licence covers
what (`6c99724`).

## What was not done

- In sushiengine, about 38 paths with the owner's uncommitted work are not committed.
- No repository's `tools/` was replaced with the new checkers; that is programme 4.
- No build or test proved the changes.
- Nothing was pushed.
