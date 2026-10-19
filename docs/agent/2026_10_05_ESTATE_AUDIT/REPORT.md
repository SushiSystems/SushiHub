# Estate audit: sushistack

**Status:** Shipped — 2026-10-05. Read-only audit; nothing in the repository was changed.

One auditing agent per dimension read the tree and a second agent checked each finding against
the files. A finding marked *confirmed* was re-read by the reviewer; *unclear* means the reviewer
could not settle it; *found by review* means the first pass missed it and nobody re-checked it.
Refuted findings are listed and not counted. No build, test or project CLI was run.

| Dimension | High | Medium | Low | Refuted |
| --- | --- | --- | --- | --- |
| Licence | 4 | 8 | 4 | 0 |
| Command line | 4 | 13 | 4 | 0 |
| Documentation | 6 | 10 | 2 | 0 |
| Layout and hygiene | 6 | 8 | 5 | 0 |
| Code shape | 4 | 20 | 0 | 0 |

## Licence

### Facts

- Repository: D:/Projects/sushistack, origin https://github.com/SushiSystems/SushiHub.git, 229 tracked files (82 .py, 61 .md, 31 .cpp, 29 .hpp, 6 .json, 4 .toml, 3 CMakeLists.txt, 3 .jsonl, 2 .yml, 1 .sh, 1 .ps1).
- D:/Projects/sushistack/LICENSE is the only licence document in the tree: unmodified Apache License 2.0 text, 201 lines, added in commit 2ae1178 (2026-06-30, 'Initial commit') and never changed since. No NOTICE, COPYING, docs/LICENSE, cli/LICENSE, gui/LICENSE or THIRD_PARTY file is tracked.
- LICENSE line 189 still holds the template appendix 'Copyright [yyyy] [name of copyright owner]'; no year or holder was ever filled in.
- Licence header blocks in source: zero variants. `git grep -i -E 'copyright|SPDX' -- . ':!LICENSE'` matches only three lines of agent prose under docs/agent/. No tracked file contains 'Licensed under the Apache License'.
- Files carrying no licence header, by language: Python 82 of 82 (e.g. cli/sushihub/cli.py, cli/sushihub/config.py, tools/record_cli_argv.py); C++ .cpp 31 of 31 (e.g. gui/src/main.cpp, gui/src/bridge/Process.cpp, gui/tests/bridge_test.cpp); C++ .hpp 29 of 29 (e.g. gui/src/ui/Shell.hpp, gui/src/contract/Event.hpp, gui/tests/FixtureFile.hpp); shell 1 of 1 (install.sh); PowerShell 1 of 1 (install.ps1); CMake 3 of 3 (gui/CMakeLists.txt, gui/src/CMakeLists.txt, gui/tests/CMakeLists.txt); TOML 4 of 4; YAML 2 of 2.
- C++ files open directly with the Doxygen file block (`/** @file main.cpp ... @author Mustafa Garip */` in gui/src/main.cpp:1-4); Python files open directly with the module docstring (cli/sushihub/services/licence_file.py:1).
- Machine-readable declarations: cli/pyproject.toml has no `license` key, no `license-files` and no `classifiers`; it declares name sushihub, version 0.2.0, authors = Mustafa Garip <mustafagarip@sushisystems.io>. No package.json, Doxyfile, Dockerfile, conda file, setup.py/setup.cfg or sushi-module.toml is tracked. gui/CMakeLists.txt:16 declares `project(sushihub_gui VERSION 0.1.0 LANGUAGES CXX)` with no licence field.
- The only machine-readable licence statement for this repository is GitHub's detection: `gh repo view SushiSystems/SushiHub` returns licenseInfo key apache-2.0, visibility PUBLIC, forkCount 0.
- Prose licence statements: README.md:38 'Licensed under the terms in `LICENSE`.' and cli/README.md:79-80 'sushiengine is sold; the other four modules are not ... cloning an open-source module asks only for a Git identity.' No other README or docs page names the repository's licence; docs/CONTRIBUTING.md has no contribution-licence or CLA wording.
- Every other 'licence/license' hit in the tree (cli/sushihub/services/licence_file.py, `hub license` at cli/sushihub/cli.py:458, contract/sushi-account.md, cli/README.md:49-50,108-116,147) refers to the product licence token Sushi Account issues for sushiengine (sushi-licence.jwt), not to the source licence.
- Copyright holder names and years in the tree: none. The only personal attribution is `@author Mustafa Garip` in C++ file blocks and the pyproject authors entry.
- git shortlog -sne HEAD: 250 Mustafa Garip <mustafa.garip3434@hotmail.com>; 2 Mustafa Garip <51916290+sushimg@users.noreply.github.com> (committer GitHub <noreply@github.com>, i.e. web edits). One human author under two addresses. First commit 2026-06-30, last 2026-10-04.
- Commit trailers: 222 'Co-Authored-By: Claude ...' lines across 252 commits (Opus 5 100, Fable 5.1 65, Sonnet 5 22, Opus 4.8 21, Opus 5.5 6, Sonnet 4.6 5, Fable 5 2, Haiku 4.5 1). No Signed-off-by lines.
- Third-party code vendored in the tracked tree: none. No third_party/ directory, no FetchContent, no git submodule, no vcpkg.json. D:/Projects/sushistack/dependencies/ exists on disk but is untracked (the tree `hub install` fills).
- C++ link dependencies of gui/ (gui/src/CMakeLists.txt:1-5, gui/tests/CMakeLists.txt:1, cli/sushihub/manifests/gui.deps.toml), licences read from dependencies/vcpkg/installed/x64-windows/share/<pkg>/copyright: Dear ImGui MIT (Omar Cornut), nlohmann-json MIT (Niels Lohmann), GLFW zlib/libpng (Geelnard, Lowy), GoogleTest BSD-3-Clause (Google, tests only). Plus system OpenGL, Threads, shell32.
- Python dependencies (cli/pyproject.toml:12-25): click>=8.0, sushicore>=0.7.0, typer>=0.12, rich>=13.0, keyring>=24, tomli>=2.0 (py<3.11); test extra pytest>=7.0, jsonschema>=4.0; build backend setuptools>=61. From memory, not read from their sources: click BSD-3-Clause, typer/rich/keyring/tomli/pytest/jsonschema/setuptools MIT. sushicore is Sushi Systems' own package in a sibling repository.
- No third-party notice is kept anywhere in the repository: the licences of the linked libraries exist only in the untracked vcpkg install tree.
- Toolchains `hub install` provisions onto the user's machine (Intel LLVM/oneAPI, CUDA, ROCm, Level Zero; cli/sushihub/defaults.toml:24-40, cli/sushihub/setup/gpu_backends/*.py) are re-exports of sushicore.provision code; this repository downloads nothing proprietary into its own tree and redistributes none of it.
- Tags: v0.1.0 (2026-09-21, annotated) and v0.2.0 (2026-09-22, annotated) exist locally; both carry the Apache-2.0 LICENSE. `git ls-remote --tags origin` lists only v0.1.0, so v0.2.0 is not on the remote.
- PyPI (https://pypi.org/pypi/sushihub/json, queried 2026-10-05): one release, 0.1.0, uploaded 2026-09-21 as sushihub-0.1.0-py3-none-any.whl and sushihub-0.1.0.tar.gz; license = None, license_expression = None, classifiers = []. 0.2.0 is not on PyPI.
- `gh release list -R SushiSystems/SushiHub` returned no rows: no GitHub release object exists. .github/workflows/release.yml publishes to PyPI on any pushed `v*` tag.
- docs/reference/CHANGELOG.md:16 has a 'v0.2.0 — 2026-09-22' section and line 35 records 'Installed `hub` from PyPI rather than cloning the workspace'; README.md:6 says '`hub` comes from PyPI as `sushihub`'. No changelog entry mentions the licence.

### Corrections from review

- Fact 'sushicore>=0.7.0 is published separately on PyPI' (F9 evidence): PyPI holds sushicore 0.1.0, 0.2.0, 0.3.0 and 0.4.0 only; latest is 0.4.0. 0.7.0 exists only in the sibling checkout D:/Projects/sushicore/pyproject.toml:7. HEAD's cli/pyproject.toml:17 pin cannot be resolved from PyPI today.
- Tracked-file breakdown sums to 223, not 229: the list omits 2 .gitkeep, 2 .gitignore, cli/sushihub/py.typed and LICENSE. The total of 229 is right.
- 'No other README or docs page names the repository's licence': docs/agent/specs/2026-09-05-hub-design.md:8 states 'SushiStack is open source, as are sushiruntime, sushiblas, sushiai and sushidsp', and lines 47, 56, 65, 225 repeat it. The brief asked for every prose statement in docs.
- 'The only machine-readable licence statement for this repository is GitHub's detection' holds for this repository, but the audit lists sushicore's licence as not checked while the PyPI JSON is one request away: sushicore 0.4.0 declares license_expression = Apache-2.0 with classifiers; sushihub 0.1.0 depends on sushicore>=0.2.0 (PKG-INFO), v0.2.0 tag on >=0.4.0.
- F5 implies pushing v0.2.0 would extend the Apache-2.0 grant by one version. The v0.2.0 commit is already an ancestor of origin/main (remote head 18de796; local HEAD 51f6bde is 3 commits ahead), so that source is public already; the tag push adds only the PyPI artefact.
- F1's '144 code files' under 'the house file-opening rule': the source-comments skill covers C++, GLSL, TypeScript and Python, which is 142 tracked files here; install.sh and install.ps1 are outside the rule as written.

### Findings

#### L1. [high] No source file carries a licence header; the house file-opening rule is unmet in all 144 code files

Evidence: 0 of 82 .py, 0 of 31 .cpp, 0 of 29 .hpp, 0 of install.sh / install.ps1 carry a licence block. Examples: D:/Projects/sushistack/gui/src/main.cpp:1 opens with `/** @file main.cpp`; D:/Projects/sushistack/cli/sushihub/cli.py:1 and D:/Projects/sushistack/cli/sushihub/services/licence_file.py:1 open with the module docstring. The source-comments skill requires 'the license block, a blank line, then the @file block'.

Recommendation: The relicence here is an insertion, not a replacement: add the new licence block to all 144 files in one mechanical pass once the licence text and the holder line are fixed. Decide first whether CMake, TOML, YAML and JSON-schema files get one too, since the skill names only C++, GLSL, TypeScript and Python.

Review: confirmed. Recomputed: 0 of 82 .py, 31 .cpp, 29 .hpp carry copyright/Licensed/SPDX in their first 12 lines; gui/src/main.cpp:1 opens with `/** @file`, cli/sushihub/cli.py:1 with the docstring. 144 = 82+31+29+2, but the skill names only C++, GLSL, TypeScript and Python, so 142 files are under the rule and install.sh/install.ps1 belong with the CMake/TOML decision the recommendation defers.

#### L2. [high] Copyright holder and year are stated nowhere

Evidence: D:/Projects/sushistack/LICENSE:189 is the unfilled template 'Copyright [yyyy] [name of copyright owner]'. `git grep -i -E 'copyright|SPDX' -- . ':!LICENSE'` finds no copyright line in any source, README or manifest. The skill template expects 'Copyright (c) <year>-present <Owner> & <Organisation>'.

Recommendation: Owner decides the holder string (person, Sushi Systems, or both) and the start year (first commit is 2026-06-30) before any header is written, and uses the same string in LICENSE, headers and pyproject across every repository.

Review: confirmed. LICENSE:189 is the unfilled template; `git grep -i -E 'copyright|SPDX' -- . ':!LICENSE'` returns only the three docs/agent lines the audit lists.

#### L3. [high] sushihub 0.1.0 is already public and cannot be retracted: PyPI wheel and sdist, the v0.1.0 tag and the public Apache-2.0 repository history

Evidence: PyPI JSON for sushihub lists sushihub-0.1.0-py3-none-any.whl and sushihub-0.1.0.tar.gz uploaded 2026-09-21. `git ls-remote --tags origin` shows refs/tags/v0.1.0. `gh repo view` reports visibility PUBLIC with licenseInfo apache-2.0; D:/Projects/sushistack/LICENSE has been Apache-2.0 since commit 2ae1178 (2026-06-30). README.md:6 and install.sh:136 direct users to that PyPI package.

Recommendation: Treat every commit up to the relicensing commit as permanently Apache-2.0 for whoever already has it. State the cut in the changelog and the README ('from version X the licence is ...'). Yanking 0.1.0 on PyPI hides it from resolvers but does not revoke the grant.

Review: confirmed. PyPI JSON shows sushihub 0.1.0 wheel and sdist uploaded 2026-09-21, not yanked; ls-remote (full listing) shows v0.1.0; gh reports PUBLIC, apache-2.0; install.sh:136 and README.md:6 cite PyPI. Understated: origin/main is at 18de796, so all history up to three commits before HEAD is public Apache-2.0, including the v0.2.0 commit.

#### L4. [high] A non-commercial licence on hub would bar the engine's paying organisations from the tool that installs what they bought

Evidence: D:/Projects/sushistack/cli/README.md:79 'sushiengine is sold'; D:/Projects/sushistack/cli/sushihub/catalog.toml:19-23 marks sushiengine `distribution = "binary"`; D:/Projects/sushistack/contract/sushi-account.md:21 and :53 give a licence holder of `org` 'when it comes from an organization seat'; cli/README.md:50 prints holder `account` or `org`. hub login, hub add sushiengine and hub update sushiengine are the only delivery path for the sold binary, and README.md:10-14 installs hub for every user.

Recommendation: Owner decision before the licence text is chosen: either hub and sushicore stay permissive (they are installers, not the product), or the new licence carries an explicit grant for using hub to install and run Sushi products under a valid Sushi Account licence. The audit treats hub as one more repository to relicense and never raises this.

Review: found by review.

#### L5. [medium] The published 0.1.0 distribution carries no licence at all, so its terms rest only on the repository

Evidence: PyPI metadata for 0.1.0: license None, license_expression None, classifiers []. D:/Projects/sushistack/cli/pyproject.toml has no `license`, `license-files` or `classifiers` key, and LICENSE sits at the repository root, outside the `cli/` project that `python -m build cli` packages (.github/workflows/release.yml:19), so setuptools cannot pick it up. cli/sushihub.egg-info/ holds no licence file.

Recommendation: With the new licence, add `license` (a `LicenseRef-...` SPDX expression for a custom text) and `license-files` to cli/pyproject.toml and make the licence text reachable from cli/ so the wheel and sdist ship it. That is a build-configuration edit and an owner decision.

Review: confirmed. cli/pyproject.toml has no license, license-files or classifiers; no cli/LICENSE*; egg-info has no licence file. I listed the 0.1.0 sdist from PyPI (103 entries): no LICENSE or NOTICE inside, PKG-INFO has no License field. This closes the audit's first not_checked item.

#### L6. [medium] v0.2.0 is tagged locally and sectioned in the changelog but is not published; pushing the tag publishes it to PyPI under whatever licence the tree holds then

Evidence: `git for-each-ref refs/tags` lists v0.2.0 (3ea5ac9, 2026-09-22); `git ls-remote --tags origin` does not; PyPI has only 0.1.0. docs/reference/CHANGELOG.md:16 reads '## v0.2.0 — 2026-09-22'. .github/workflows/release.yml:4-5 triggers on `tags: ["v*"]` and uploads through pypa/gh-action-pypi-publish.

Recommendation: Do not push v0.2.0 until the licence decision lands. The tag points at a tree with the Apache-2.0 LICENSE, so pushing it as is extends the irrevocable Apache-2.0 release by one version. Owner decides whether 0.2.0 goes out as Apache-2.0 or is re-cut after the relicence.

Review: confirmed. for-each-ref shows v0.2.0 (3ea5ac9); full `git ls-remote --tags origin` shows only v0.1.0 and its peeled ref; release.yml:4-5 triggers on v*. One correction to the framing: the v0.2.0 commit is already an ancestor of origin/main, so its source is public under Apache-2.0 now; only the PyPI upload is pending.

#### L7. [medium] Prose calls the modules 'open-source', which a non-commercial licence would make false

Evidence: D:/Projects/sushistack/cli/README.md:79-80: 'sushiengine is sold; the other four modules are not ... cloning an open-source module asks only for a Git identity.' A licence that forbids commercial use is source-available, not open source by the OSI definition. The same sentence counts four unsold modules while cli/sushihub/catalog.toml lists three source modules (sushiruntime, sushiai, sushiblas).

Recommendation: Reword to 'source-available' (or name the licence) in the same change that swaps LICENSE, and correct the module count against catalog.toml.

Review: confirmed. cli/README.md:79-80 read as quoted; catalog.toml has three source modules and one binary. The fourth is sushidsp (docs/agent/specs/2026-09-05-hub-design.md:8, CHANGELOG.md:24), which self-describes through sushi-module.toml and is not in the catalog, so the count is a catalog mismatch, not an arithmetic error. The finding misses the same wording in shipped code (see missed).

#### L8. [medium] README names no licence, and the word 'licence' in this repository already means the engine's product token

Evidence: D:/Projects/sushistack/README.md:38 says only 'Licensed under the terms in `LICENSE`.' The term is otherwise used for the Sushi Account token: `hub license` (cli/sushihub/cli.py:458, cli/README.md:50), sushi-licence.jwt (cli/sushihub/services/licence_file.py:21), contract/sushi-account.md:50-68.

Recommendation: After the change, README states the licence by name and in one sentence what it allows and forbids, and distinguishes the source licence from the sushiengine product licence that `hub license` reports.

Review: confirmed. README.md:38 as quoted; cli/sushihub/cli.py:458 is the `license` command name, licence_file.py:21 the sushi-licence.jwt comment, contract/sushi-account.md:50 the Licences section. Medium is generous; this is low on its own.

#### L9. [medium] No third-party notice exists for the libraries the desktop application links

Evidence: gui/src/CMakeLists.txt:1-5 and gui/tests/CMakeLists.txt:1 link Dear ImGui (MIT), GLFW (zlib/libpng), nlohmann-json (MIT) and GoogleTest (BSD-3-Clause). No NOTICE or THIRD_PARTY file is tracked; the licence texts exist only under the untracked D:/Projects/sushistack/dependencies/vcpkg/installed/x64-windows/share/*/copyright. gui/README.md and cli/sushihub/manifests/gui.deps.toml name the libraries without their licences.

Recommendation: MIT and BSD require their notice to travel with binary copies. Before a sushihub_gui binary is distributed, add a third-party notices document listing each library, version and licence text, and ship it beside the executable. None of these four licences conflicts with a non-commercial outbound licence.

Review: confirmed. gui/src/CMakeLists.txt:1-5 and gui/tests/CMakeLists.txt:1 find imgui, glfw3, OpenGL, Threads, nlohmann_json, GTest; the four copyright files under dependencies/vcpkg/installed/x64-windows/share read MIT, zlib, MIT, BSD-3 as stated; no NOTICE or THIRD_PARTY tracked. The obligation is conditional on a binary being shipped, which the audit says; none is today.

#### L10. [medium] sushicore is already irrevocably Apache-2.0 on PyPI with an explicit declaration, and hub's pin points at a version that is not published

Evidence: https://pypi.org/pypi/sushicore/json: releases 0.1.0-0.4.0, latest 0.4.0, license_expression 'Apache-2.0'. D:/Projects/sushicore/pyproject.toml:7,10,11 is version 0.7.0 with license = "Apache-2.0" and license-files. D:/Projects/sushistack/cli/pyproject.toml:17 requires sushicore>=0.7.0; the v0.2.0 tag requires >=0.4.0; published sushihub 0.1.0 requires >=0.2.0.

Recommendation: Record in the cross-repository plan that four sushicore versions stay Apache-2.0 for good and that every published sushihub resolves to them. Decide the order: sushicore's licence cut and 0.7.0 release come before any sushihub release from HEAD, since HEAD cannot install from PyPI until then.

Review: found by review.

#### L11. [medium] The desktop application prints 'Open source' in its UI

Evidence: D:/Projects/sushistack/gui/src/ui/screens/ModulesScreen.cpp:78 returns "Open source; can be cloned." for every absent module. F6 found the README wording only; `git grep -i 'open.source' -- cli gui contract` shows this second hit in shipped code.

Recommendation: Change the string in the same commit as the README wording in F6, and check gui/tests for an assertion on it. Keep the wording in one place if both the CLI and the GUI need it.

Review: found by review.

#### L12. [medium] The audit names no enforcement brick for the header pass

Evidence: `git ls-files tools` returns only tools/record_cli_argv.py and tools/tests/test_record_cli_argv.py; tools/documentation/check_source_comments.py, which the source-comments skill and CLAUDE.md name as the checker every repository carries, is absent. F1 recommends 'one mechanical pass' over 144 files with nothing to keep the result true afterwards.

Recommendation: Add the checker (with the licence-block rule reading one template from sushiskills) before the insertion pass, so the pass is verified by a tool and new files cannot land without the block. That is the brick-shaped form of F1.

Review: found by review.

#### L13. [low] No GPL, LGPL or proprietary-SDK code is in this repository; the only term-bearing inbound dependency is the sibling sushicore

Evidence: No third_party/, submodule or FetchContent. Python dependencies in cli/pyproject.toml:12-25 are permissive (click BSD-3-Clause; typer, rich, keyring, tomli MIT, stated from memory). cli/sushihub/setup/gpu_backends/cuda.py:7 and its siblings only re-export sushicore.provision code that installs CUDA, oneAPI and ROCm on the user's machine; nothing of those SDKs is redistributed here. `sushicore>=0.7.0` is published separately on PyPI.

Recommendation: No conflict to resolve here. sushicore must move to the same licence in step, or sushihub under a non-commercial licence will depend on an Apache-2.0 package whose published versions stay Apache-2.0.

Review: unclear. No GPL/LGPL/vendored code: confirmed (no third_party, submodule, FetchContent). But the evidence line '`sushicore>=0.7.0` is published separately on PyPI' is false: PyPI sushicore latest is 0.4.0 (releases 0.1.0-0.4.0), and it declares license_expression Apache-2.0. The conclusion 'no conflict here' holds; the sushicore part is wrong and understated.

#### L14. [low] Single human author, but two author addresses and 222 AI co-author trailers; a third address in package metadata

Evidence: git shortlog -sne: 250 commits as mustafa.garip3434@hotmail.com, 2 as 51916290+sushimg@users.noreply.github.com. cli/pyproject.toml:10 gives mustafagarip@sushisystems.io. 222 'Co-Authored-By: Claude ...' trailers across 252 commits. No other human contributor, no Signed-off-by, forkCount 0.

Recommendation: No outside contributor's consent is needed to relicence. Two points for the owner, possibly with counsel: whether the copyright sits with the person or with Sushi Systems as a company, and that AI-assisted authorship may limit what copyright protects in some jurisdictions, which a restrictive licence relies on more than a permissive one does.

Review: confirmed. shortlog: 250 + 2, both Mustafa Garip; 252 commits; 222 Co-Authored-By lines, 0 Signed-off-by; pyproject.toml:10 holds the sushisystems.io address. Model breakdown matches (Opus 5.5 is 3 + 3 '(1M context)').

#### L15. [low] Contribution terms are undefined

Evidence: D:/Projects/sushistack/docs/CONTRIBUTING.md contains no licence, CLA or DCO wording (no match for licen[cs]e, copyright or sign-off). Under Apache-2.0 section 5 inbound contributions default to Apache-2.0; a custom non-commercial licence has no such default.

Recommendation: Add an inbound-licence rule to docs/CONTRIBUTING.md with the relicence (a CLA or copyright assignment), so that a future outside contribution does not block the owner from selling or relicensing the code.

Review: confirmed. grep of docs/CONTRIBUTING.md for licen[cs]e, copyright, sign-off, CLA, DCO matches only the unrelated word 'claiming' at line 52.

#### L16. [low] The house rules that govern this repository contradict the target licence

Evidence: The `dependencies` skill (C:/Users/sushi/.claude/skills/dependencies) lists 'Non-commercial, source-available, field-of-use limits: Rejected' for inbound code, and the `source-comments` skill's file-opening template reads '... Apache-2.0 notice ...'. Both live in the sushiskills repository, outside this one.

Recommendation: Update the header template in sushiskills before the header pass runs here, so every repository inserts the same block. The inbound table may stay as is (it concerns dependencies), but then sibling Sushi repositories under the new licence need an explicit exception.

Review: confirmed. Loaded both skills: dependencies lists 'Non-commercial, source-available, field-of-use limits | Rejected'; source-comments template reads '/* ... Apache-2.0 notice ... */' and 'Copyright (c) <year>-present <Owner> & <Organisation>'. Low severity undersells it: the header pass in F1 cannot start until this template changes, so it is a blocker for every repository.

### Not checked

- The contents of the published PyPI artefacts (sushihub-0.1.0 wheel and sdist) were not downloaded; that they contain no LICENSE file is inferred from the pyproject layout and the empty PyPI licence fields.
- Licences of the Python dependencies (click, typer, rich, keyring, tomli, pytest, jsonschema, setuptools) and of their transitive dependencies were stated from memory, not read from installed distributions.
- sushicore's own licence and PyPI metadata (sibling repository, out of scope for this dimension run).
- Whether sushisystems.io serves install.sh / install.ps1 copies with any licence statement, and any licence wording on the website.
- Whether a sushihub_gui binary has been distributed anywhere outside GitHub releases and PyPI (none found there).
- The 57 files under docs/ were searched by pattern for licence wording, not read in full; docs/agent/ plans and reports were not reviewed beyond the grep hits.
- Untracked local files (cli/config.local.toml, cli/modules.local.toml, cli/build/, gui/build/, dependencies/ beyond the four vcpkg copyright files) were not examined.
- The v0.2.0 tag's absence on the remote was read from a truncated ls-remote listing (first 10 lines, which showed only v0.1.0 and its peeled ref) and from PyPI; not confirmed with a full listing.
- Legal questions: whether the copyright belongs to the individual or to a registered company, and the effect of AI co-authorship on copyrightability, were flagged but not assessed.

## Command line

### Facts

- Entry points: console scripts `hub` and `sushihub`, both `sushihub.cli:app` (D:/Projects/sushistack/cli/pyproject.toml:27-29); `python -m sushihub` via cli/sushihub/__main__.py. Distribution `sushihub` 0.2.0, requires-python >=3.10.
- Framework: Typer (>=0.12) with `rich_markup_mode="rich"`; click is imported directly only by describe.py. The whole command surface is one file, cli/sushihub/cli.py (469 lines); there is no `commands/` package.
- Requires `sushicore>=0.7.0` (cli/pyproject.toml:17). D:/Projects/sushicore/pyproject.toml is at 0.7.0, which REMAINING_WORK.md:57-61 records as unpublished.
- Root options: `--json` (eager, one JSON event per line on stdout) and `--describe` (eager, prints the command catalogue as JSON, exit 0). Typer's default `--install-completion`/`--show-completion` are left on. There is no `--version` flag.
- Workspace panel: `init` (no options); `home` (no options); `status [--json] [--check-updates]`.
- Modules panel: `add MODULES... [--dry-run] [--skip-install] [--binary]`; `link MODULE PATH [--dry-run] [--skip-install]`; `install-cli MODULES... [--dry-run]`; `update [MODULES...] [--dry-run]`; `sync [--dry-run]`.
- Dependencies panel: `install [--customize] [--dry-run] [--yes/-y] [--refresh-toolchains]`; `doctor` (no options); `remove [--all] [--gpu] [--dry-run] [--yes/-y]`.
- Desktop app panel: sub-app `gui` with `build [--type debug|release|relwithdebinfo] [--clean] [-D VAR=VALUE ...]`, `test [--filter PATTERN] [--repeat N]`, `run [TARGET] [-- args]`, `clean`.
- Account panel: `login`, `logout`, `whoami`, `license`, none with options.
- Help panels are five module constants (K_WORKSPACE, K_MODULES, K_DEPENDENCIES, K_DESKTOP_APP, K_ACCOUNT) passed as `rich_help_panel`; cli/tests/test_help_screen.py pins the grouping. Every command carries an `epilog` of examples. Help is drawn by `sushicore.typer_help.help_group`.
- Taken from sushicore: the help group, `LazyConsole` (console.py), `provision.bind_console` and `provision.home.bind_root`, config plumbing (`config_base`, `workspace`), the provision pipeline, steps, package managers, selection, probe and fragments, `CMakeDriver`, `ExecutableIndex`, `Runner`, `StackBuildEnv`, `ModuleProfile`, `StackConfig`.
- Implemented locally: the command bodies for `install`, `doctor`, `remove` and `link` (hub does not call `sushicore.provision.commands.register_provision_commands`, which all six sibling CLIs do), module lifecycle, pipx handling, the Sushi Account client, release download, `--describe` (describe.py), the `--customize` picker, the status payload.
- cli/sushihub/setup/ holds mostly re-export shims of sushicore.provision (apt.py, ordering.py, package_managers.py, pipeline.py, probe.py, toolchains.py, gpu_backends/*); only dependency_source.py, factory.py and steps.py carry hub logic.
- Output: Rich through sushicore's Console in human mode; under `--json` the same calls become `line`, `command`, `header`, `panel`, `table`, `progress`, `result`, `prompt` events (contract/README.md:24-33). Every command body ends through `_finish`, which emits one `result` event and raises `typer.Exit`.
- `--describe` serialises the Typer app's Click objects (describe.py): program, version, contract "1", leaf commands with params; nested commands are named `gui build`. `applies_to` is the same three presences on every command.
- Exit codes: 0 success; 1 for every service failure, a cancelled `--customize`, a declined `remove --all`, and `whoami`/`license` when not signed in; 2 for a malformed `-D` (services/gui.py:138) and Typer usage errors; `gui build/test/run` return the child's code.
- Errors: services print one `console.error` line and return non-zero. `workspace_root()` and `gui_root()` raise `SystemExit(<message>)` instead (config.py:78, gui_config.py:57). There is no top-level catch of a module base error; Typer's default exception handling applies.
- Colour: resolved in sushicore from `[cli] color = auto|always|never`, `SUSHI_CLI_COLOR`, and `NO_COLOR` (always wins). There is no `--no-color` flag. Hub's console reads its `[cli]` table from `<workspace>/sushihub/cli/config.toml` and `config.local.toml` (console.py:22, config.py:52).
- Help wording: imperative first sentence per command ("Show which modules...", "Bring one or more..."); short option help often uses the clipped form "Show, don't change."; Rich markup tags `[cmd]`, `[bold]`, `[error]` inside docstrings. Spelling mixes `license` (command, payload key) with `licence` (prose, file name).
- Environment variables hub reads: SUSHISTACK_HOME, SUSHISTACK_DEPS_DIR, SUSHI_ACCOUNT_URL, SUSHI_CLI_*, NO_COLOR, HUB_GUI_* (gui profile), and seventeen SR_* tool overrides (config.py:235-253).
- Sibling surface for comparison (read from their cli.py only): sr/se/sa/sb/sd/st all register `setup`, `doctor`, `link`, `unlink` from sushicore; all use `no_args_is_help=True`; build commands take `--type/-t` and `--filter/-f`; only `se` has `--version`; none has `--json` or `--describe`.
- catalog.toml lists four modules: sushiruntime (sr), sushiengine (se, binary), sushiai (sa), sushiblas (sb). sushidsp and sushitrack are outside the catalog and reachable only through `hub link` with a `sushi-module.toml`.
- No file named CLI_GUIDE exists in this repository; the CLI documentation is cli/README.md, docs/getting_started/INSTALL.md, docs/guides/LINKING_CHECKOUTS.md, docs/architecture/WORKSPACE.md and contract/README.md.

### Corrections from review

- F16 says 'All 21 commands'. cli.py registers 19 leaf commands: init, home, status, add, link, install-cli, update, install, sync, doctor, remove (11), gui build/test/run/clean (4), login, logout, whoami, license (4). The audit's own facts list also adds up to 19.
- F3 cites cli/README.md:6, :34, :79, :100 for 'the other four modules'. Only :79 and :100 carry that phrase; :6 and :34 list the four aliases correctly.
- Facts: 'build commands take --type/-t and --filter/-f' for all six siblings. sushidsp/cli/sushidsp/cli.py has --type/-t (lines 48, 68, 90, 160) but no --filter at all; F9's 'BuildType.release default' holds for sr, se, sa, sb only, since sushidsp and sushitrack default --type to None.
- Recomputed and correct: cli.py is 469 lines; discovery.py is 91 lines; _ENV_OVERRIDES holds 17 SR_* entries; catalog.toml lists 4 modules with 1 binary; sushicore/pyproject.toml is 0.7.0 and all seven CLIs require sushicore>=0.7.0; only se has --version; no CLI_GUIDE file is tracked.

### Findings

#### C1. [high] Account commands reach the user as a traceback when Sushi Account is unreachable or no keyring backend exists

Evidence: cli/sushihub/services/session.py:79 (`whoami`), :95 (`license`) and :64 (`login`, after the grant) call `client().me()` with no try. `me()` -> `access_token()`/`_get()` -> `_send()` raises `LoginError` on `URLError` (services/identity.py:340-341); a read timeout raises `TimeoutError`, which `_send` does not catch at all. cli/sushihub/services/binary.py:60 and :85 call `client.access_token()` outside their try blocks, so `hub add sushiengine` and `hub update sushiengine` have the same hole. cli/sushihub/services/token_store.py:68 and :72 call `keyring.get_password`/`set_password` unguarded; only `PasswordDeleteError` is caught (:80), so `keyring.errors.NoKeyringError` on a headless Linux box crashes `login`, `logout`, `whoami`, `license` and `status --check-updates` with a binary install. cli.py has no catch around any of these.

Recommendation: Give the identity layer one base error that also wraps keyring and timeout failures (`raise ... from error` at the boundary), and catch that base once in session.py and binary.py, printing one line and returning 1, as python-code-style's Errors section requires.

Review: confirmed. Read services/session.py:64,79,95, binary.py:60,85, token_store.py:68-81, identity.py:178-212,330-343. me()/access_token() run outside any try; _send catches only HTTPError/URLError and response.read() sits outside the try; KeyringStore guards only PasswordDeleteError. status --check-updates shares the keyring hole through resolve_release -> access_token (update_check.py:36 catches SushiAccountError only).

#### C2. [high] `install`, `doctor`, `link` are local reimplementations of commands sushicore registers for every sibling, under a different name and shape

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py:249-340 registers `setup [--dry-run] [--yes] [--toolchain X]... [--no-gpu]`, `doctor [--for GROUP]`, `link [--workspace PATH]`, `unlink [--workspace PATH]`; sr, se, sa, sb, sd, st all call `register_provision_commands`. Hub instead defines `install [--customize] [--dry-run] [--yes/-y] [--refresh-toolchains]` (cli.py:265-301), `doctor` with no `--for` (cli.py:316-323), `link MODULE PATH` (cli.py:195-215) and no `unlink`. The same act is `hub install` in hub and `<cli> setup` in the six siblings; toolchain choice is a TUI (`--customize`) in hub and `--toolchain`/`--no-gpu` flags in siblings; `-y` exists only in hub. `hub install` also skips sushicore's `ProvisionLock` (commands.py:220) that sibling `setup` takes.

Recommendation: Owner decision on the public surface: either hub adopts the shared verbs (`setup`, `doctor --for`, `unlink`, `--toolchain`, `--no-gpu`) or sushicore exposes one command set both hub and the modules register. Whichever is chosen, `-y` and the provision lock should be the same everywhere.

Review: confirmed. sushicore/provision/commands.py:247-340 registers setup/doctor/link/unlink with the cited options; all six sibling cli.py files call register_provision_commands; hub cli.py:195-215,265-301,316-323 define their own. grep finds no ProvisionLock anywhere under cli/sushihub. `--yes` in sushicore (commands.py:265-266) has no -y.

#### C3. [high] cli/README.md describes a sushicore delivery and a package layout that no longer exist

Evidence: cli/README.md:151-156 ("The package is not on any index; `install.py` injects the checkout under `<workspace>/sushicore`... `SUSHICORE_DIR` or `hub link sushicore <path>` points it elsewhere") contradicts cli/install.py:19 (PyPI dependency), services/modules.py:213-217 (`hub link sushicore` is refused) and docs/guides/LINKING_CHECKOUTS.md:19. README.md:12 names the package `sushistack/` (it is `sushihub/`); :21 says install.py "injects sushicore"; :36 says `install-cli` injects sushicore (services/cli_install.py:11-13 says it does not); :85 and :149 give the keyring service as `sushistack` (token_store.py:22 is `sushihub`); :6, :34, :79, :100 count "the other four modules" where catalog.toml has three besides sushiengine. docs/reference/GLOSSARY.md:10-11 says sushicore "ships inside this repository" and :18 names the `sushistack` package.

Recommendation: Rewrite the Layout, Commands, Signing in and "Where sushicore comes from" sections of cli/README.md and the two glossary entries against the current code.

Review: confirmed. cli/README.md:12,21,36,85,149,151-156 and GLOSSARY.md:10-11,19 read as cited and contradict install.py:19, modules.py:213-217, token_store.py:22. Line cites partly off: 'the other four modules' is at :79 and :100 only; :6 and :34 list four aliases and carry no count.

#### C4. [high] Hub has no entry-point function, so no failure path can honour the `--json` result contract

Evidence: cli/pyproject.toml:28-29 maps `hub` and `sushihub` straight to `sushihub.cli:app`, and cli/sushihub/__main__.py:3-6 calls `app()`. Every path that leaves without `_finish` therefore ends with no `result` event: the SystemExit in F5, the tracebacks in F1 and F14, and every Click usage error (exit 2, e.g. `hub --json home --json`, or an unknown option sent by the desktop application). contract/README.md:35 says every command ends with exactly one `result`. sushitrack already has the shape: D:/Projects/sushitrack/cli/sushitrack_cli/cli.py:372-395 `entry()`, wired at sushitrack/cli/pyproject.toml:31-32. The audit treats F1, F5 and F14 as three separate catches.

Recommendation: One brick, in sushicore: an `entry(app, console)` function that runs the Typer app, catches the module base error, usage errors and SystemExit-with-message, prints one line through the console, emits the `result` event in machine mode and returns the code. All seven CLIs point their console scripts at it. Public interface, so an owner decision.

Review: found by review.

#### C5. [medium] Help text shown by `hub --help` and exported through `--describe` is stale

Evidence: cli.py:185 (`hub add` help): "Five of the six are cloned" while catalog.toml has four modules, three cloned; services/modules.py:119 says "Four of the five". cli.py:231-232 (`hub install-cli` help): "injects the shared sushicore presentation layer that ships in this repository", false since sushicore moved to PyPI. cli.py:117: "Run this once after cloning sushihub", while INSTALL.md:6-7 says nothing is cloned. cli.py:312 (`sync`): "install missing deps, then update modules" while services/modules.py:390-393 updates first and provisions second; cli/README.md:38 repeats the wrong order. services/modules.py:193-194 hard-codes "(`sr`, `se`, `sa`, `sb`)" in the success line instead of reading the catalog.

Recommendation: Correct the four docstrings and build the alias list from `CATALOG.aliases()`, the way `_MODULE_NAMES` already is.

Review: confirmed. cli.py:117,185,231-232,312; modules.py:119,193-194,375-393 and catalog.toml (four tables, one binary) read as cited. The unused cli.py:164 _MODULE_ALIASES is the constant the recommendation needs.

#### C6. [medium] Under `--json`, a command run outside a workspace ends with no `result` event

Evidence: cli/sushihub/config.py:78-82 raises `SystemExit("Not inside a SushiStack workspace...")`; cli/sushihub/gui_config.py:57-60 does the same for a missing `gui/`. Callers that do not catch it: cli.py:130 (`home`), services/status_report.py:100, services/modules.py:132 and :273, services/cli_install.py:72, config.py:321 (`load_config`, used by install/doctor/remove), services/gui.py:129/187/215/239. Click does not intercept `SystemExit`, so Python prints the bare string to stderr and exits 1, bypassing `_finish`. contract/README.md:35 states "Every command ends with exactly one `result`". In human mode the message also skips the themed `console.error` rendering.

Recommendation: Raise a hub base error from `workspace_root`/`gui_root` and catch it once at the entry point, routing through `console.error` and `_finish(1)`.

Review: confirmed. config.py:78-82 and gui_config.py:57-60 raise SystemExit(str); cli.py:130, status_report.py:100, modules.py:132/273, cli_install.py:72, gui.py:129/187/215/239 do not catch it; contract/README.md:35 promises one result. The recommendation is incomplete as a brick: sushicore's LazyConsole.sources() (cli_console.py:58-61), cli.py:83-86 and config.py:208-210 all catch SystemExit as the 'no workspace' signal, and pyproject.toml:28-29 points the scripts at the Typer `app`, so there is no entry point to catch in yet.

#### C7. [medium] The `[cli]` theme override is read from a directory that only pre-2026-09-22 clones have, and the docs name a different one

Evidence: cli/sushihub/console.py:22 feeds `legacy_cli_dir` to `LazyConsole`; config.py:52 sets it to `<workspace>/sushihub/cli`, the path before commit ebc4c82 lifted `cli/` to the root. sushicore/cli_console.py:62 then reads `config.toml` and `config.local.toml` there. A workspace made by `hub init` has no such directory, and `[cli]` in `.sushistack/workspace.toml` is not read (acknowledged in docs/design/REMAINING_WORK.md:89). cli/README.md:54-55 tells the user to add `[cli] background = "dark"` to "`config.local.toml` in the `hub` checkout", and INSTALL.md:105-106 says the old data lived at `cli/config.local.toml`; neither matches `sushihub/cli/`. The packaged defaults.toml `[cli]` table (lines 45-52) is never passed to the console either.

Recommendation: Pass the packaged defaults and `workspace.toml` as the console's config sources (needs the sushicore change REMAINING_WORK names), and until then make README and INSTALL state the path the code reads, or point users at `SUSHI_CLI_*`.

Review: confirmed. console.py:22, config.py:52,90-99, sushicore/cli_console.py:56-62, REMAINING_WORK.md:89-92, cli/README.md:54-55, INSTALL.md:105-106, defaults.toml:45-52 all as cited.

#### C8. [medium] `hub gui` is listed for every user but works only when the workspace root is a clone of this repository

Evidence: cli/sushihub/gui_config.py:38 and :55 fix the application at `<workspace>/gui`; a `hub init` workspace has none, so all four `gui` commands exit through the `SystemExit` at :57-60, whose advice "Update the workspace checkout (`hub update`)" cannot help. cli.py:349-355 registers the group unconditionally and `--describe` exports it to the desktop application. INSTALL.md:45-53 and REMAINING_WORK.md:85 acknowledge the gap.

Recommendation: Hide or omit the `gui` group when no `gui/CMakeLists.txt` is in reach (sushicore already does this for binary installs in `register_provision_commands`), and replace the hint with the clone instruction INSTALL.md gives.

Review: confirmed. gui_config.py:38,55-60, cli.py:349-355, INSTALL.md:45-53, REMAINING_WORK.md:85-88 as cited. The '`hub update`' hint is wrong for a hub-init workspace.

#### C9. [medium] No `--version` flag, and the root has two differently shaped `--json` flags

Evidence: cli.py:50-59 defines only `--json` and `--describe` at the root; the version is reachable only inside the `--describe` JSON (describe.py:142-149). sushiengine has `--version` (sushiengine/cli/sushiengine/cli.py:114); the other siblings have none either, so the stack has no shared version flag. `status` re-declares `--json` locally (cli.py:143-144) with different help text; cli/README.md:39 calls it "kept for scripts written against the old spelling", and it is the only command with it, so `hub home --json` is a usage error while `hub status --json` works.

Recommendation: Add one `--version` callback in sushicore for all seven CLIs. Either retire `status --json` with a deprecation note or mark it `hidden=True` so help and `--describe` show one spelling.

Review: confirmed. cli.py:50-59 has no --version; cli.py:143-144 re-declares --json on status; sushiengine cli.py:114 is the only sibling --version (grep over six cli.py). sushihub/__init__.py already computes __version__, so the flag needs no new data.

#### C10. [medium] Option naming for the same concept differs between hub's `gui` commands and the sibling build commands

Evidence: cli.py:364-365: `--type` has no `-t` and defaults to `debug`; siblings declare `"--type", "-t"` with `BuildType.release` default (e.g. sushiblas/cli/sushiblas/cli.py:50, sushiruntime/cli/sushiruntime/cli.py:90). cli.py:385-386: `--filter` has no `-f`; siblings declare `"--filter", "-f"` (sushiblas cli.py:84). cli.py:368-369: `-D` has no long form. cli.py:279 and :339 give `--yes` a `-y` short form that sushicore's `setup --yes` lacks (provision/commands.py:266-267). The gui group is built without `no_args_is_help=True` (cli.py:349-354) where every sibling sub-app has it, so bare `hub gui` is expected to end in a usage error instead of the help page (not executed).

Recommendation: Fix the option spellings in one place in sushicore (a shared option factory for `--type/-t`, `--filter/-f`, `--clean`, `--dry-run`, `--yes/-y`) and have hub's gui commands use it.

Review: confirmed. cli.py:364-369,385-386,279,339,349-354 against sushiblas cli.py:50,84 and sushiruntime cli.py:90,126. Caveats: sushidsp and sushitrack default --type to None, not release, and sushidsp has no --filter, so the siblings are not uniform either. Bare `hub gui` behaviour not executed by me either.

#### C11. [medium] Dead code in the CLI package, including a step that cannot import

Evidence: cli/sushihub/setup/steps.py:119-120 imports `..services.project`, which does not exist (cli/sushihub/services/ has no project.py); `VerifyStep` is wired into `build_pipeline` for `only="all"` and `"verify"` (setup/factory.py:101-111), and `services/setup.py:15` defaults `step="all"`, so any caller that omits the step gets an ImportError. cli.py only passes `provision` and `detect`. cli/sushihub/services/discovery.py (91 lines) has no importer; services/gui.py:26 uses `sushicore.discovery.ExecutableIndex` instead. cli.py:164 `_MODULE_ALIASES` is never read. config.py:87 `find_project_root`, :222-228 `TOOLCHAIN_COMPILERS`, :285-314 `resolved_compilers`/`resolved_windows_compiler`, :330-340 `set_toolchain` and :283 `target_bin = "sr_functional_tests"` have no caller in cli/sushihub or cli/tests. setup/apt.py and setup/probe.py have no importer.

Recommendation: Delete discovery.py, `VerifyStep` with the `all`/`verify` branches, the unused config members and the unimported shims, after owner approval since they were not created in this task.

Review: confirmed. steps.py:119-120 imports services.project, absent from git ls-files; factory.py:102-110 wires VerifyStep; services/setup.py:15 defaults to 'all'; grep finds no importer for services/discovery.py, setup/apt.py, setup/probe.py, and no reader for find_project_root, TOOLCHAIN_COMPILERS, resolved_compilers, resolved_windows_compiler, set_toolchain, target_bin, _MODULE_ALIASES. The ImportError only fires on a non-dry run, and no current caller omits the step.

#### C12. [medium] `hub status` reports channel `editable` for a PyPI install

Evidence: cli/sushihub/services/hub_install.py:60: `"frozen" if getattr(sys, "frozen", False) else "editable"`. install.sh:160 and install.ps1 install `sushihub` from PyPI, non-editable; services/pipx.py:78-99 already tells the two apart for `hub update`. contract/status.schema.json:23 allows only `editable` and `frozen`, so the published install has no truthful value.

Recommendation: Add an index channel to the schema (a contract version change) and derive the value from `pipx.installed(DISTRIBUTION)`.

Review: confirmed. hub_install.py:60, contract/status.schema.json:23 (enum editable|frozen), install.sh:160 (`$PIPX install sushihub`), pipx.py:78-99 as cited.

#### C13. [medium] Hub's tool overrides and comments still carry sushiruntime's names

Evidence: cli/sushihub/config.py:235-253 maps seventeen hub settings to `SR_*` variables (`SR_CMAKE`, `SR_VCPKG_ROOT`, ...), while the gui profile uses `HUB_GUI_*` (gui_config.py:32) and the workspace uses `SUSHISTACK_*`. cli/sushihub/defaults.toml:5 documents the layer as "`SUSHI_*` env vars -> CLI flags"; neither a `SUSHI_*` tool override nor a flag layer exists. defaults.toml:39-43 and config.py:221, :266 refer to `sr setup`, `sr toolchain` and `AppData/Local/SushiRuntime/toolchains`. cli/sushihub/setup/__init__.py:1 is titled "SushiRuntime one-shot installer pipeline" and cites a `dependencies.toml` manifest.

Recommendation: Decide the override prefix for hub (owner decision, it is public surface), then correct defaults.toml's header and the copied comments.

Review: confirmed. config.py:235-253 holds 17 SR_* entries (counted); defaults.toml:5,39-43; config.py:221,266; setup/__init__.py:1-6 as cited.

#### C14. [medium] F5's fix as written breaks three callers that use SystemExit as the 'no workspace' signal

Evidence: D:/Projects/sushicore/sushicore/cli_console.py:58-61 (`except SystemExit: return []`, documented at :33-37 as the protocol every CLI's config_dir follows), cli/sushihub/cli.py:83-86 (`_upgrade_if_old`) and cli/sushihub/config.py:208-210 (`deps_dir` fallback) all catch SystemExit from `workspace_root()`. Replacing it with a hub base error, as F5 recommends, turns `hub --help`, `hub init` and `hub --describe` outside a workspace into tracebacks unless those three are changed in the same step, one of them in sushicore.

Recommendation: Define the 'not inside a workspace' error once in sushicore (the sibling CLIs raise the same SystemExit from find_project_root), have LazyConsole catch that type, then move hub and the six modules together. Sequence it after the sushicore release, not as a hub-only patch.

Review: found by review.

#### C15. [medium] `hub install --customize` and bare `hub --json` break the stdout rule in machine mode

Evidence: cli/sushihub/services/customize.py:120-141 decides on `sys.stdin.isatty()` only and never consults `console.is_machine()`; with `--json` on a terminal it opens a `rich.live.Live(screen=True)` picker and reads raw keys (:29-54), and :89-93 prints through `console.console.print`. cli/sushihub/cli.py:71-73 answers `hub --json` with no subcommand by `typer.echo(ctx.get_help())` on stdout and no `result` event. contract/README.md:57-59 says stdout carries event lines and nothing else. `--describe` exports `--customize` to the desktop application as an ordinary boolean (describe.py:106-113).

Recommendation: In machine mode `--customize` should refuse with one error line and exit 2 (or take the selection as flags, which F2's `--toolchain`/`--no-gpu` decision would give it); bare `hub --json` should emit a `result` event rather than the help page.

Review: found by review.

#### C16. [medium] A checkout of main cannot install `hub` or any module CLI until sushicore 0.7.0 is published

Evidence: cli/pyproject.toml:17 and all six sibling cli/pyproject.toml files require `sushicore>=0.7.0`; docs/design/REMAINING_WORK.md:57 and :61 record 0.7.0 as 'unpublished' with wave 4 open. cli/install.py:19 and services/cli_install.py:11-13 resolve sushicore from PyPI, so `python cli/install.py` and `hub install-cli <module>` fail at dependency resolution unless a local `pip install -e` of sushicore is already in place. The audit lists this as a fact, not a finding. Not checked against PyPI (no network use).

Recommendation: Treat the sushicore 0.7.0 publish as the first step of the CLI programme, or state the editable-sushicore prerequisite in docs/getting_started/INSTALL.md:55-56 until it is done.

Review: found by review.

#### C17. [medium] Audit's recommendations for F8 and F9 put new public surface in sushicore without marking it an owner decision

Evidence: F8 ('Add one --version callback in sushicore for all seven CLIs') and F9 ('a shared option factory for --type/-t, --filter/-f, --clean, --dry-run, --yes/-y') both change sushicore's public interface and every CLI's command line; F2 and F12 flag the same kind of choice as an owner decision, these two do not. F9's factory also conflicts with what it would unify: sushicore's own `setup --yes` has no -y (provision/commands.py:265-266), sr/se/sa/sb default --type to release while sd/st default to None and hub gui to debug, and sushidsp has no --filter.

Recommendation: Fold F8 and F9 into the F2 surface decision: one list of shared options with spelling and default per option, approved by the owner, then implemented once in sushicore. The default for `--type` is a real choice and must be asked, not picked.

Review: found by review.

#### C18. [low] Hard-coded paths and platform assumptions in install detection and fallbacks

Evidence: cli/sushihub/services/hub_install.py:25-30 looks for the alias only in `~/.bashrc`, `~/.zshrc`, `~/Documents/PowerShell/profile.ps1` and `~/Documents/WindowsPowerShell/profile.ps1`; install.ps1:95 writes to `$PROFILE.CurrentUserAllHosts`, which sits under a redirected (OneDrive) Documents folder on many Windows machines, so `status` then reports `alias: null`. config.py:211-213 falls back to `%LOCALAPPDATA%/SushiStack` or `~/.local/SushiStack` rather than an XDG or sushicore-provided home (sushicore's sibling `setup` uses `~/.sushisystems`, INSTALL.md:95). services/customize.py:49-51 reads two more bytes after ESC on Unix, so a bare ESC blocks until two further keys are pressed. defaults.toml:24 fixes `oneapi_root = "/opt/intel/oneapi"`.

Recommendation: Resolve the PowerShell profile path the way the installer does (or record the alias location in workspace.toml at install time); take the no-workspace dependency home from `sushicore.provision.home`.

Review: confirmed. hub_install.py:25-30, install.ps1:95, config.py:211-213, customize.py:49-51, defaults.toml:24 as cited. The OneDrive redirection is an inference, not observed.

#### C19. [low] `hub install-cli` can crash on a malformed module pyproject, and subprocess failures are unguarded

Evidence: cli/sushihub/services/pipx.py:44-45 indexes `["project"]["name"]` and lets `KeyError`/`tomllib.TOMLDecodeError` escape; services/cli_install.py:87 and :106 call it without a try. pipx.py:60-62 does `[*pipx, ...]` with `pipx = command()`, a `TypeError` when pipx is missing; the two current callers check first, the function itself does not. services/identity.py:133-135 indexes `body["device_code"]` on a 200 answer and raises `KeyError` on a malformed body.

Recommendation: Raise a named error from `distribution_name` and `install`, and validate the device-code body into `LoginError`.

Review: confirmed. pipx.py:44-45,60-62,108; cli_install.py:87,106; identity.py:133-135 as cited. pipx.upgrade (:108) has the same `[*command(), ...]` hole and was not named.

#### C20. [low] Docs cite code locations that are now re-export shims, and the backlog carries duplicate and stale items

Evidence: docs/reference/KNOWN_ISSUES.md:19-24 places `LinuxCudaLocator.provision` and `_cuda_repo_tag` in `cli/sushihub/setup/gpu_backends/cuda.py`, :39-40 places `VcpkgManager.install` in `cli/sushihub/setup/package_managers.py`, :60-61 places `install_intel_llvm` in `cli/sushihub/setup/toolchains.py`; all three files are 7 to 29 line re-exports of sushicore. docs/design/REMAINING_WORK.md:140 says removing a link means editing `cli/modules.local.toml` (it is `.sushistack/workspace.toml`, LINKING_CHECKOUTS.md:34), and sushicore already ships `remove_module`. REMAINING_WORK.md:100 and :135 list "`hub install-cli` has no test" twice; :97 lists "`hub status` reports sushicore as a module" although contract/README.md:46-49 says the row was removed. docs/README.md:33 says "the four Sushi Account endpoints" where contract/sushi-account.md:1 says six. docs/architecture/WORKSPACE.md:53-57 describes the desktop application as coming. cli/README.md:37 omits that `hub update` also upgrades `hub` itself (services/modules.py:281).

Recommendation: Point the KNOWN_ISSUES citations at the sushicore modules, prune the three backlog items, and correct the endpoint count and the WORKSPACE closing section.

Review: confirmed. KNOWN_ISSUES.md:19-24,39-40,60-61 point at 7 to 29 line shims; REMAINING_WORK.md:97,100,135,140; docs/README.md:33 'four' vs contract/sushi-account.md:1 'six'; WORKSPACE.md 'What is coming' all read as cited. Not listed: defaults.toml:55-56 also says 'four requests', and cli/README.md:89 names `config.toml` where the file is defaults.toml.

#### C21. [low] CLI package departs from the python-code-style layout and error rules the stack sets

Evidence: All 21 commands are parsed in one module, cli/sushihub/cli.py, where the skill prescribes `commands/` beside `services/`. Services write to the terminal directly (`console.*` in services/modules.py, session.py, setup.py), which the skill forbids for a service. cli/install.py:36-134 is tab-indented and its functions lack annotations' docstrings in places (`run`, `install`, `uninstall`); install.py:39 lists `"cli"` twice. cli.py:163-164 places module-name constants between a section banner's two lines (158-165). cli.py:18 uses `typing.List`/`Optional` rather than built-in generics.

Recommendation: Treat as its own refactor task after the surface decision in F2: split cli.py into `commands/`, return results from services and print in the command layer.

Review: confirmed. Defects are real (single cli.py, console.* in services, cli/install.py has 73 tab-indented lines and 'cli' twice at :39, cli.py:18 typing.List/Optional), but the count is wrong: cli.py defines 19 leaf commands, not 21. The clause 'lack annotations' docstrings in places' is garbled.

### Not checked

- Nothing was executed: no `hub` invocation, no test run. Every behaviour claim (tracebacks, missing result event, bare `hub gui`) comes from reading the source, not from observed output.
- cli/tests/*.py were only grepped for usages; test quality and coverage were not reviewed.
- gui/src (C++) was not read; only gui/README.md was scanned for CLI references. Whether the desktop application tolerates the gaps in F5 and F11 is unverified.
- contract/describe.schema.json, contract/events.schema.json and contract/sushi-account.md were not compared field by field with the code; only status.schema.json's `channel` enum and the sushi-account.md headings were read.
- install.sh and install.ps1 were grepped for alias, pipx and hub lines only, not reviewed in full.
- docs/design/WORKSPACE_DECOUPLING.md, GPU_BACKEND_PROVISIONING.md, docs/reference/MODULE_MANIFEST.md, docs/CONTRIBUTING.md, DOCUMENTATION_STYLE_GUIDE.md and everything under docs/agent/ and docs/archive/ were not checked against the code.
- docs/reference/CHANGELOG.md was read only to line 14.
- cli/sushihub/manifests/gui.deps.toml, setup/gpu_backends/*.py beyond backend.py and __init__.py, and tools/record_cli_argv.py were not read.
- sushicore internals were read only where hub touches them (typer_help.py, cli_console.py, provision/commands.py, part of config.py); the renderer, JSON event code and help page model were not.
- Sibling CLIs were surveyed by grep of their cli.py for command names and option spellings only; their help wording, exit codes and error handling were not compared.
- The untracked cli/build/, cli/sushihub.egg-info/, cli/config.local.toml(.bak) and cli/modules.local.toml on disk were skipped as instructed.
- Whether sushicore 0.7.0 is on PyPI was not checked (no network use); the 'unpublished' statement is taken from REMAINING_WORK.md.

## Documentation

### Facts

- Present: README.md, docs/README.md, docs/CONTRIBUTING.md, docs/DOCUMENTATION_STYLE_GUIDE.md, docs/getting_started/ (INSTALL.md), docs/architecture/ (WORKSPACE.md), docs/guides/ (LINKING_CHECKOUTS.md), docs/reference/ with CHANGELOG.md, GLOSSARY.md, KNOWN_ISSUES.md and MODULE_MANIFEST.md.
- Present: docs/design/ with REMAINING_WORK.md, WORKSPACE_DECOUPLING.md and GPU_BACKEND_PROVISIONING.md; docs/agent/specs (2 files), plans (22), reports (16 plus .gitkeep); docs/archive/ with changelog/v0.1.0.md and a leftover .gitkeep.
- Missing: docs/modules/ (the global CLAUDE.md tree lists it; docs/README.md has a 'Modules' heading that points at component READMEs instead) and docs/design/README.md (the topic-to-document map the documentation skill requires).
- Module READMEs present: cli/README.md, gui/README.md, contract/README.md, gui/tests/fixtures/README.md. Missing: tools/README.md (tools/ holds record_cli_argv.py and its tests).
- docs/ holds no superpowers/, slop/ or other stray folder, and no duplicated CHANGELOG or LICENSE; LICENSE exists once at the repository root. .superpowers/ and .argv-baseline/ sit at the root but are git-ignored scratch.
- The one document under docs/ with no place in the architecture is docs/CLAUDE.md (agent instructions, 49 lines). It is not a manual page; its content belongs in a root CLAUDE.md, with the documentation rules it repeats left to docs/CONTRIBUTING.md.
- docs/agent/ uses the specs|plans|reports layout of the global CLAUDE.md with lowercase dashed names (2026-09-22-wave-2.md). The documentation skill prescribes one folder per piece of work (YYYY_MM_DD_WORK_NAME with SPEC.md, PLAN.md, REPORT.md) and UPPER_SNAKE_CASE names. The two yardsticks disagree and the owner has to pick one.
- contract/sushi-account.md is the only manual-like document outside docs/ with a lowercase dashed name; the rest use UPPER_SNAKE_CASE.
- There is one backlog, docs/design/REMAINING_WORK.md. No TODO list was found in the other manual pages. Both design documents carry a status line, but as a multi-line paragraph (11 lines in GPU_BACKEND_PROVISIONING.md, 10 in WORKSPACE_DECOUPLING.md).
- docs/reference/CHANGELOG.md has '## Unreleased' (4 entries) and '## v0.2.0 — 2026-09-22' (20 entries); v0.1.0 is archived. No entry in the live file exceeds 240 characters; the longest is 221. Tags v0.1.0 and v0.2.0 exist and cli/pyproject.toml says 0.2.0.
- The markdown files use no `[text](path)` links at all; every reference is a backticked path. Reachability and path checks were therefore done on code spans. All four sibling-repository citations I could test (sushiengine, sushicore, sushiweb) resolve on this machine.
- The hub command set in cli/sushihub/cli.py is init, home, status, add, link, install-cli, update, install, sync, doctor, remove, gui build/test/run/clean, login, logout, whoami, license. The command table in cli/README.md matches it.
- Prose register is sound across the manual: no filler connectives, no closing summaries, few evaluative words. The em dashes are the glossary's and index's term separators and the changelog's date separator. Nothing needs a humanizer rewrite; the defects are staleness, not style.

### Corrections from review

- F6 evidence says gui/ has 60 tracked files; `git ls-files gui | wc -l` gives 72.
- F14 cites a ' -- ' dash at gui/README.md:71; that line has none. The only ' -- ' in the file is line 91, inside a code block, describing the `--` argument separator of `hub gui run`.
- F14 treats cli/README.md:5-6 (four module CLIs: sr, se, sa, sb) as an omission; cli/sushihub/catalog.toml lists exactly those four, so the line is correct.
- F4 says README.md was last touched 'Oct 4 13:15'; git log gives 8313fe1 at 2026-10-04 13:16:06 +0300 (trivial, conclusion unchanged).
- Fact 'All four sibling-repository citations I could test' is followed by five OK lines in the audit's own verification output; five resolve.
- Recomputed and correct: 22 plans / 16 reports / 2 specs; 4 Unreleased and 20 v0.2.0 changelog entries; longest live changelog line 221 characters and v0.1.0.md:60 at 246; hub command set (11 top-level, 4 gui, 4 account) matches cli/sushihub/cli.py; tags v0.1.0 and v0.2.0; cli/pyproject.toml version 0.2.0.

### Findings

#### D1. [high] cli/README.md still describes the pre-2026-09-22 package and sushicore injection

Evidence: D:/Projects/sushistack/cli/README.md:12 names the package directory `sushistack/` (the tree has cli/sushihub/). Line 21: 'install.py ... injects sushicore'. Lines 151-156 ('Where sushicore comes from'): 'The package is not on any index; install.py injects the checkout under <workspace>/sushicore ... SUSHICORE_DIR or hub link sushicore <path> points it elsewhere. See ../../sushicore/docs/README.md'. Against the tree: cli/pyproject.toml:17 requires `sushicore>=0.7.0`, cli/install.py:19 says sushicore is 'resolved from PyPI', no SUSHICORE_DIR exists under cli/sushihub, and docs/guides/LINKING_CHECKOUTS.md:19 says `hub link sushicore` is refused. Line 36 also says install-cli 'inject[s] sushicore'.

Recommendation: Rewrite the Layout block and the 'Where sushicore comes from' section to the PyPI dependency, drop the injection wording from the install-cli row, and remove the SUSHICORE_DIR and `hub link sushicore` claims.

Review: confirmed. cli/README.md:12 says `sushistack/`, :21 and :36 say inject, :151-156 describe the checkout injection and SUSHICORE_DIR; cli/pyproject.toml:17 has sushicore>=0.7.0, cli/install.py:19 says PyPI, no SUSHICORE_DIR under cli/sushihub, LINKING_CHECKOUTS.md:19 refuses `hub link sushicore`.

#### D2. [high] Sushi Account pages say the endpoints do not exist and name the wrong keyring service

Evidence: D:/Projects/sushistack/contract/sushi-account.md:4-5 'None of the six exists in sushiweb yet'; cli/README.md:91-92 'sushiweb has not built them yet'. docs/design/REMAINING_WORK.md:22 records wave 3 as landed 2026-09-05 with migrations applied to production. cli/README.md:85 and :149 and contract/sushi-account.md:42 give the keyring service as `sushistack`; cli/sushihub/services/token_store.py:22 has KEYRING_SERVICE = "sushihub". contract/sushi-account.md:28 says the URL comes from 'the `sushistack` package's defaults.toml' (the package is sushihub); cli/README.md:89 says `config.toml` (the file is cli/sushihub/defaults.toml). docs/README.md:33 says 'the four Sushi Account endpoints' while contract/README.md:12 and sushi-account.md:1 say six, and identity.py calls six.

Recommendation: State the real status of the sushiweb endpoints, correct the keyring service to `sushihub`, the package name and the defaults file, and make the index say six endpoints.

Review: confirmed. contract/sushi-account.md:4-5,:28,:42 and cli/README.md:85,:89,:91-92,:149 read as cited; token_store.py:22 is KEYRING_SERVICE = "sushihub"; docs/README.md:33 says four, identity.py calls six. All six routes exist under D:/Projects/sushiweb/apps/account/app/api (device/code, device/token, token/refresh, me, licenses/token, releases/resolve) on sushiweb main, which the auditor did not check.

#### D3. [high] The backlog carries items that are done, duplicated or point at dead paths

Evidence: D:/Projects/sushistack/docs/design/REMAINING_WORK.md: lines 97-99 '`hub status` reports sushicore as a module ... the row lies' contradicts CHANGELOG.md:31 'Stopped reporting `sushicore` as a module' and contract/README.md:46-48. Lines 119-120 'GUI fixtures are hand-written ... awaits one recorded run' contradicts CHANGELOG.md:33 and gui/tests/fixtures/README.md:5 (recorded 2026-09-22). Lines 100-101 and 135-139 are the same item ('hub install-cli has no test') twice. Lines 140-141 tell the reader to edit `cli/modules.local.toml`; the guide (docs/guides/LINKING_CHECKOUTS.md:34) says `.sushistack/workspace.toml`. Line 117 cites `gui/src/ui/DeviceGrant.cpp`; the file is gui/src/ui/screens/DeviceGrant.cpp. Line 18 reads 'Move `cli/` to `cli/`'. Lines 87 and 98 say 'Wave 5 owns/decides' for work the table at line 46 gives to wave 8. Line 125 names `tools/documentation/check_source_comments.py`, which does not exist (the item itself says so, so this one is a true open item).

Recommendation: Delete the two landed items and the duplicate, fix the three paths and the wave number, and restore the original source path in the wave 1c row.

Review: confirmed. REMAINING_WORK.md lines 18, 87, 97-99, 100-101, 117, 119-120, 135-139, 140-141 read as cited; DeviceGrant.cpp is under gui/src/ui/screens/. One addition: cli/tests/test_cli_install.py:79-90 compares the add and install-cli paths at service level, so the duplicated 'no test' item needs rewording to 'no test of the command's own path resolution', not only de-duplication.

#### D4. [high] Front door and install page say sr, sb, sa and se lack setup and doctor; the backlog says they landed

Evidence: D:/Projects/sushistack/README.md:30 '`sd` and `st` have the two commands today; docs/design/REMAINING_WORK.md tracks the rest.' docs/getting_started/INSTALL.md:134 '`sd` and `st` have that command today; `sr`, `sb`, `sa` and `se` are next'. docs/design/REMAINING_WORK.md:59 '`sr`, `sb`, `sa` and `se` register the four commands. Landed 2026-10-04.' and commit 51f6bde 'mark the module wave of the standalone programme as landed'. README.md was last touched on Oct 4 13:15 and was not updated with that commit.

Recommendation: Update both sentences to the landed state (all six module CLIs carry setup, doctor, link and unlink; wave 4 is the open step).

Review: confirmed. README.md:30 and INSTALL.md:134-135 against REMAINING_WORK.md:59. Verified in the siblings: sushiruntime, sushiblas, sushiai, sushiengine, sushidsp and sushitrack cli.py each call register_provision_commands from sushicore.provision.commands.

#### D5. [high] INSTALL.md gives commands that do not work as written

Evidence: D:/Projects/sushistack/docs/getting_started/INSTALL.md:23 'install.sh sushiruntime sushiblas'; install.sh:44-49 accepts only `--add`, `--dry-run`, `--no-alias` and prints '[WARN] unknown argument' for a bare module name, so nothing is added. INSTALL.md:52 'git clone https://github.com/sushisystems/sushistack.git'; the remote is https://github.com/SushiSystems/SushiHub.git (git remote -v). The style guide at docs/DOCUMENTATION_STYLE_GUIDE.md:47-48 requires that a copied command works.

Recommendation: Write the shell form as `install.sh --add "sushiruntime sushiblas"` and correct the clone URL to the SushiHub repository.

Review: confirmed. install.sh:44-49 warns on a bare module name; INSTALL.md:23 gives that form. INSTALL.md:52 clones sushisystems/sushistack.git while origin is SushiSystems/SushiHub.git. The URL half stays unproven without a network check (GitHub redirects renamed repositories), the install.sh half is certain. install.ps1 -Add a,b works because the [string] parameter joins the array with a space.

#### D6. [high] KNOWN_ISSUES.md and the GPU design status cite code that moved to sushicore

Evidence: Commits ba0af29, 1cd0e08 and 18de796 (2026-09-23) turned cli/sushihub/setup/ into re-exports: gpu_backends/cuda.py is 7 lines (`from sushicore.provision.gpu.cuda import CUDA`), package_managers.py 29, toolchains.py 11. D:/Projects/sushistack/docs/reference/KNOWN_ISSUES.md:19-24 still cites `LinuxCudaLocator.provision`, `_cuda_repo_tag` and `_CUDA126_MAX_UBUNTU_TAG` 'in cli/sushihub/setup/gpu_backends/cuda.py'; grep finds none of the three under cli/sushihub (they are in D:/Projects/sushicore/sushicore/provision/gpu/cuda.py). KNOWN_ISSUES.md:39-40 and :60-61 place `VcpkgManager.install` and `install_intel_llvm` in files that only re-export them. docs/design/GPU_BACKEND_PROVISIONING.md:3-9 says the bricks 'exist under cli/sushihub/setup/gpu_backends/'. cli/README.md:18 describes setup/ as 'the dependency engine'. The auditor listed both pages under not_checked, so the gap is declared, but it is the largest code-versus-page contradiction in the repository.

Recommendation: Repoint every symbol citation to sushicore.provision (or to the SushiCore repository's own pages), rewrite the GPU design status to say the implementation lives in sushicore and hub re-exports it, and change the cli/README.md layout line for setup/ accordingly. Ask the owner whether the CUDA and vcpkg known-issue entries should move to SushiCore's KNOWN_ISSUES, since the code they describe is no longer owned here.

Review: found by review.

#### D7. [medium] Glossary and architecture page describe a past state

Evidence: D:/Projects/sushistack/docs/reference/GLOSSARY.md:10-11 '`sushicore` ... ships inside this repository' (it left on 2026-09-22, docs/CONTRIBUTING.md:28). GLOSSARY.md:18-19 'This repository ships the base fragment inside the `sushistack` package's `manifests/`' (cli/sushihub/manifests/ holds only gui.deps.toml; the base fragment is in sushicore per cli/README.md:126-127). GLOSSARY.md:36-37 'a schema under `contract/` will bind both sides' (three schemas exist). docs/architecture/WORKSPACE.md:53-57 'What is coming: The workspace is to gain a second face: a desktop application' (gui/ is built, 60 tracked files). WORKSPACE.md:39-41 'It does not build' while cli/README.md:4 says hub builds the desktop application.

Recommendation: Correct the three glossary entries, and replace the 'What is coming' section of WORKSPACE.md with a present-tense line pointing at gui/README.md.

Review: confirmed. GLOSSARY.md:10-11, :18-19, :36-37 and WORKSPACE.md:39-41, :53-57 read as cited; cli/sushihub/manifests holds only gui.deps.toml; contract/ holds three schemas. The gui file count in the evidence is wrong (72, not 60) but does not change the conclusion.

#### D8. [medium] Cited paths that do not resolve

Evidence: D:/Projects/sushistack/gui/README.md:8 `../../docs/agent/specs/2026-09-05-hub-design.md` climbs above the repository; from gui/ the path is `../docs/...`. cli/README.md:156 `../../sushicore/docs/README.md` assumes a sibling checkout at a fixed place. docs/reference/CHANGELOG.md:34 cites `cli/cli.py`, which never existed at the repository root layout (the file is cli/sushihub/cli.py). docs/design/REMAINING_WORK.md:117 `gui/src/ui/DeviceGrant.cpp` (see F3). gui/README.md:40 `model/InstallFacts` and docs/README.md:68 `services/project.py` are symbol-style citations and resolve by intent.

Recommendation: Fix the gui/README.md and CHANGELOG paths, and cite the SushiCore manual by repository name as docs/README.md:27-28 already does.

Review: confirmed. gui/README.md:8 `../../docs/...` climbs out of the repository; CHANGELOG.md:34 cites cli/cli.py; cli/README.md:156 points outside the repository. The audit misses the larger set of dead symbol citations in KNOWN_ISSUES.md and GPU_BACKEND_PROVISIONING.md (see missed).

#### D9. [medium] Not every document is reachable from docs/README.md

Evidence: D:/Projects/sushistack/docs/README.md:3 claims 'Every document under `docs/` is reachable from here.' The 'Agent output' section (lines 64-81) names 6 of 22 plans; 16 are unnamed, among them docs/agent/plans/2026-09-22-rename-to-sushihub.md (cited by the design status line) and 2026-09-22-wave-4-hub-on-pypi.md through wave-7. No docs/agent/plans/ folder entry exists to cover them, unlike `agent/reports/` at line 80. docs/CLAUDE.md is not named at all. Lines 80-81 describe the reports folder as holding 'the five from wave 0'; it holds 16.

Recommendation: List plans and specs by folder the way reports are, or name every file; correct the reports description; decide docs/CLAUDE.md's home (F11).

Review: confirmed. Recounted from git ls-files: 22 plans, 6 named in docs/README.md:69-79, 16 unnamed; 16 reports plus .gitkeep; docs/CLAUDE.md unnamed; line 80-81 says 'the five from wave 0'.

#### D10. [medium] Changelog entries state reasons and lack the scope prefix

Evidence: D:/Projects/sushistack/docs/reference/CHANGELOG.md: only lines 11-12 carry a scope ('docs:', 'setup:'); lines 13-14 and all 20 entries under v0.2.0 have none, against the entry shape in the documentation skill. Entries that say why: line 23 '... so the tool's name is the tool's', line 25 '... so one schema has one reader', line 29 '... which cost `sushiengine` the Vulkan feature of its SDL2', line 30 '... which used to be skipped in silence', line 32 '... which Linux never uses', line 12 '... so a bare hub install installs one SYCL toolchain'. Line 24 gives `sushidsp` as the place, which is a repository, not a file or symbol. docs/archive/changelog/v0.1.0.md:60 is 246 characters, over the 240 limit (archive is frozen, so this one is recorded, not edited).

Recommendation: Add the scope to the unreleased entries, strip the reason clauses from the live file, and add the scope rule to docs/DOCUMENTATION_STYLE_GUIDE.md:27-38, which omits it.

Review: confirmed. Reason clauses at CHANGELOG.md:12, 23, 25, 29, 30, 32 and the repository-as-place at :24 are real under both yardsticks; awk gives the longest live line as 221 (line 12) and v0.1.0.md:60 as 246. The scope-prefix half holds only against the documentation skill: the global CLAUDE.md example entry has no scope, so that part is an owner choice like the ones the audit raises in F12, and should have been framed so.

#### D11. [medium] Status lines are paragraphs, and the approved spec still says it awaits plans

Evidence: D:/Projects/sushistack/docs/design/GPU_BACKEND_PROVISIONING.md:3-13 and docs/design/WORKSPACE_DECOUPLING.md:3-12 put ten-line narratives in the status slot; the skill's form is one line such as '**Status:** Open — phase 2 of 4', and docs/DOCUMENTATION_STYLE_GUIDE.md:23-24 says 'Status: <one clause>'. docs/agent/specs/2026-09-05-hub-design.md:4 reads 'Status: approved in conversation, awaiting the wave 1 plans' although REMAINING_WORK.md:15-26 records waves 0 through 5 as landed. docs/design/REMAINING_WORK.md:3 uses 'Status:' without the bold form the two design documents use.

Recommendation: Cut each status to one line with the open phase, move the narrative into the body, and bring the hub spec's status up to date.

Review: confirmed. GPU_BACKEND_PROVISIONING.md:3-13 (11 lines) and WORKSPACE_DECOUPLING.md:3-12 (10 lines) against DOCUMENTATION_STYLE_GUIDE.md:23-24; hub-design.md:4 still says 'awaiting the wave 1 plans'.

#### D12. [medium] Documents and work in the wrong place

Evidence: D:/Projects/sushistack/docs/CLAUDE.md has no slot in the architecture and is not loaded from the repository root as agent instructions. docs/design/WORKSPACE_DECOUPLING.md is 217 lines of which sections 1 and 3 describe the code before 2026-09-22 with dead line references (lines 28, 30, 35, 37, 96-101: `services/modules.py:47`, `sushicore/workspace.py`, `install.sh:130`); waves 0-7 are landed and only wave 8 is open. Section 3.3 (line 114) names `modules.toml` and `config.local.toml` inside .sushistack, while line 194 and the tree have one workspace.toml. The hub programme's design of record is docs/agent/specs/2026-09-05-hub-design.md, cited as the design by REMAINING_WORK.md:6, WORKSPACE.md:56, gui/README.md:8 and contract/README.md:10: live intent with open waves 6 and 7 sits in docs/agent/ instead of docs/design/. docs/archive/.gitkeep and docs/agent/reports/.gitkeep remain in folders that now hold files.

Recommendation: Ask the owner about moving docs/CLAUDE.md to the root; promote the hub design to docs/design/HUB.md or cite it from a short design page; trim the decoupling document to what is still open and correct section 3.3; drop the two .gitkeep files.

Review: confirmed. docs/CLAUDE.md exists with no root CLAUDE.md; WORKSPACE_DECOUPLING.md:28-31 cites `services/modules.py:47` and `sushicore/workspace.py`, :114 names modules.toml and config.local.toml; both .gitkeep files are tracked beside real files. Promoting the hub spec to docs/design/ is a data-ownership move the owner decides; the recommendation offers two options without saying so.

#### D13. [medium] Skeleton gaps against the architecture

Evidence: No D:/Projects/sushistack/docs/modules/ folder, no docs/design/README.md topic map, no tools/README.md. docs/CONTRIBUTING.md:10-11 tells contributors to write to `docs/agent/specs/` and `docs/agent/plans/` by date, which is the global CLAUDE.md layout and not the per-work-folder layout of the documentation skill. docs/DOCUMENTATION_STYLE_GUIDE.md:9-10 orders the placement questions archive-then-design, as the global CLAUDE.md does; the skill orders them design-then-archive and adds a 90-day rule.

Recommendation: Add docs/design/README.md and tools/README.md; settle with the owner whether docs/modules/ is a folder or the index heading it is today, and which agent-folder layout and placement order is the rule, then make CONTRIBUTING and the style guide say it.

Review: confirmed. No docs/modules/, docs/design/README.md or tools/README.md in the tree; CONTRIBUTING.md:10-11 and DOCUMENTATION_STYLE_GUIDE.md:9-10 read as cited. The skill's own tree has no docs/modules/, so only the global CLAUDE.md asks for it; the audit says this correctly.

#### D14. [medium] The index and the architecture page disagree with gui/README.md and INSTALL.md

Evidence: D:/Projects/sushistack/docs/README.md:31-32 says 'the five hand-drawn screens'; gui/README.md:21-22 and :140 say four (installs, modules, settings, commands), and gui/src/ui/screens holds four *Screen.cpp files. docs/architecture/WORKSPACE.md:4-5 says a workspace 'is usually a clone of this repository'; INSTALL.md:6-7 says 'Nothing is cloned' and CONTRIBUTING.md:22 says cloning is what a contributor does. The tree at WORKSPACE.md:10-20 omits contract/ and tools/.

Recommendation: Say four screens in the index; rewrite the WORKSPACE.md opening so the PyPI install is the usual case and the clone is the contributor's, and add contract/ and tools/ to its tree.

Review: found by review.

#### D15. [medium] cli/README.md counts five modules where the catalog has four

Evidence: D:/Projects/sushistack/cli/README.md:79 'sushiengine is sold; the other four modules are not' and :100 'The other four modules are open source'. cli/sushihub/catalog.toml lists sushiruntime, sushiengine, sushiai and sushiblas, so the others are three; sushidsp and sushitrack left on 2026-09-22. The 'open source' wording also depends on the licence decision the owner is about to make (LICENSE is Apache 2.0 today).

Recommendation: Say 'the other three' in both lines, and revisit 'open source' in cli/README.md and README.md:38 together with the licence change.

Review: found by review.

#### D16. [medium] The breaking setup change has an entry that does not name what breaks

Evidence: Commit 8313fe1 is `refactor(setup)!`. D:/Projects/sushistack/docs/reference/CHANGELOG.md:12 records it as 'Took the toolchain selection rule and the base fragment from sushicore, so a bare hub install installs one SYCL toolchain'. The documentation skill's rule is that a breaking entry names what breaks; INSTALL.md:124-125 states it ('Before 2026-10-04 it installed all three'). The audit's F9 flags the reason clause on this line but not the missing break.

Recommendation: Reword the entry to name the break, for example 'setup: Stopped installing all three SYCL toolchains on a bare `hub install`; one is installed', with the two files as the place.

Review: found by review.

#### D17. [low] Root README is accurate in outline but thin and partly stale

Evidence: D:/Projects/sushistack/README.md is 38 lines. Its table (lines 19-22) lists cli/ and gui/ and omits contract/ and tools/, both tracked top-level directories. Line 38 'Licensed under the terms in `LICENSE`' names no licence. Line 30 is stale (F4). It gives no way to verify an install (hub status, hub doctor) and no contributor entry beyond the manual pointer.

Recommendation: Add contract/ and tools/ to the table, name the licence once the owner's licence decision lands, and fix line 30.

Review: confirmed. README.md is 38 lines, table at 19-22 lists cli/ and gui/ only, line 38 names no licence (LICENSE is Apache 2.0). 'Thin' is partly taste; the omitted directories and line 30 are facts.

#### D18. [low] Small inconsistencies in component READMEs

Evidence: D:/Projects/sushistack/gui/README.md:37 writes 'Sushi Hub' where every other page writes SushiHub. gui/README.md:71 '-- ' and docs/design/WORKSPACE_DECOUPLING.md (5 occurrences, e.g. line 47) use ' -- ' as a dash. cli/README.md:54-55 tells the reader to put `[cli] background` in `config.local.toml` 'in the hub checkout', a location INSTALL.md:105-107 describes as the old one; REMAINING_WORK.md:89-92 confirms the new file is not read yet, so the instruction works only for a clone. cli/README.md:5-6 lists four module CLIs and omits `sd` and `st`, which INSTALL.md:88-96 says hub still links and provisions.

Recommendation: Normalise the product name and the dash, and say in cli/README.md that the theme override is a known gap for a PyPI install.

Review: unclear. 'Sushi Hub' at gui/README.md:37 and five ' -- ' in WORKSPACE_DECOUPLING.md (47, 71, 75, 148, 149) are real. Two parts fail: gui/README.md:71 holds no ' -- ' (the only one is the CLI argument separator at :91, which is correct), and cli/README.md:5-6 listing four module CLIs matches catalog.toml, since sd and st left the stack on 2026-09-22.

### Not checked

- The 22 plans, 16 reports and 2 specs under docs/agent/ were not read in full; only their names, line counts, the first lines of the two specs and their coverage in the index were checked. Paths cited inside them were not resolved.
- docs/archive/changelog/v0.1.0.md was checked for line length only (one line over 240), not for entry shape or cited paths.
- docs/reference/KNOWN_ISSUES.md lines 1-80 were read only in part (first 24 lines and the last rule); its claims about cuda.py symbols such as `_cuda_repo_tag` and `_CUDA126_MAX_UBUNTU_TAG` were not compared with the code.
- docs/design/GPU_BACKEND_PROVISIONING.md's claims about function names in cli/sushihub/setup/gpu_backends/ and about SushiRuntime and SushiEngine CMake files were not verified against those sources.
- Claims about other repositories (sd/st/sr/sb/sa/se carrying setup and doctor, `~/.sushisystems` as the standalone install target in INSTALL.md:95, sushicore 0.7.0 contents, the sushiweb deployment state) were not verified in those repositories; F2 and F4 rest on this repository's own backlog and changelog.
- Option-level accuracy of the command table in cli/README.md (every flag of every command) was checked only for `hub status`; command names were checked for all.
- The JSON examples in contract/README.md were not validated against the three schema files.
- Source comments and docstrings (the Doxygen and Google-style rules) are outside this dimension and were not examined.
- Whether https://github.com/sushisystems/sushistack.git redirects to the SushiHub repository was not tested; no network call was made.
- LICENSE content and licence headers were not reviewed; only the file's presence and uniqueness.

## Layout and hygiene

### Facts

- Local folder is D:/Projects/sushistack; origin is https://github.com/SushiSystems/SushiHub.git; README title is 'SushiHub'; PyPI distribution and Python package are `sushihub`; console scripts are `hub` and `sushihub`.
- Tracked top level (229 files): .github/ (2 workflows), .gitignore, LICENSE (Apache License 2.0 text), README.md, install.sh, install.ps1, cli/ (86 files: the `sushihub` package, tests, pyproject.toml, install.py), gui/ (72 files: ImGui desktop application, CMake, src/, tests/), contract/ (5 files: three JSON schemas, README.md, sushi-account.md), docs/ (57 files), tools/ (2 files).
- Ignored and present at the root: dependencies/ (build, toolchains, tools, ur, vcpkg: the provisioned workspace tree), .sushistack/workspace.toml (machine-local tool paths), .argv-baseline/ (10 JSON files dated 2026-08-25), .superpowers/sdd/ (holds only a .gitignore).
- Ignored and present under cli/: build/ (bdist.win-amd64, lib), sushihub.egg-info/, .pytest_cache/, config.local.toml, config.local.toml.bak, modules.local.toml, __pycache__ folders. Under gui/: build/ (hub, ss, windows-x64). Under tools/: __pycache__ folders.
- Absent from the root: AGENTS.md, CLAUDE.md, .gitattributes, .editorconfig, .clang-format, cmake/, tests/, sushi-module.toml. A CLAUDE.md exists at docs/CLAUDE.md instead.
- Versions: cli/pyproject.toml:7 `version = "0.2.0"`; gui/CMakeLists.txt:16 `project(sushihub_gui VERSION 0.1.0 ...)`; cli/sushihub/__init__.py reads __version__ from the installed distribution (fallback "0"); changelog newest release heading is `## v0.2.0 — 2026-09-22`. No package.json and no sushi-module.toml. CLI, tag and changelog agree at 0.2.0; the GUI says 0.1.0.
- Git tags: v0.1.0 (annotated, 2026-09-21) and v0.2.0 (annotated, 2026-09-22). pyproject version at tag v0.2.0 equals the current one. 8 commits on main since v0.2.0.
- docs/reference/CHANGELOG.md has 4 entries under `## Unreleased`; v0.1.0 is archived at docs/archive/changelog/v0.1.0.md. No changelog line exceeds 240 characters.
- CI: .github/workflows/ci.yml (push to main and pull_request; ubuntu-latest and windows-latest by Python 3.10 and 3.11; `pip install -e ./cli[test]`, `pytest cli/tests`, `pytest tools/tests`). .github/workflows/release.yml (tag `v*`; `python -m build cli`, `twine check`, publish to PyPI through trusted publishing on ubuntu only).
- tools/ holds one script, tools/record_cli_argv.py (records CLI argv as evidence for a CLI change), and its test tools/tests/test_record_cli_argv.py. None of the four standard checkers exists.
- .gitignore (root) ignores: /dependencies/, /sushiruntime/, /sushiengine/, /sushiai/, /sushiblas/, /.sushistack/, /cli/config.local.toml, /cli/modules.local.toml, __pycache__/, *.egg-info/, *.pyc, /cli/build/, cli/config.local.toml.bak, .superpowers/, .argv-baseline/. gui/.gitignore holds `build/`.
- git status: working tree clean, no untracked non-ignored files. main is 3 commits ahead of origin/main (51f6bde, 8313fe1, 4adc055). Local branches feature/hub_help_and_doctor and feature/theme_tokens are both fully merged into main; neither exists on origin.
- No loose images, imgui.ini, cmake_test_discovery JSON, compiler probe headers or .rsp files were found in the tracked or untracked tree outside dependencies/ and the build folders. No tracked binary; the largest tracked file is docs/agent/plans/2026-08-25-cmake-driver.md at 60,522 bytes.
- Sibling comparison: sushicore depends at `sushicore>=0.7.0` (cli/pyproject.toml:17) and sushicore's pyproject declares 0.7.0, while sushicore's local tags stop at v0.4.0. sushitrack and sushidsp carry tools/documentation and tools/layering; sushidsp and sushiengine carry sushi-module.toml, AGENTS.md or CLAUDE.md at the root.

### Corrections from review

- F12 and the facts list say .gitignore omits 'other catalogued modules such as sushidsp or sushitrack'. cli/sushihub/catalog.toml has four tables only (sushiruntime, sushiengine, sushiai, sushiblas), the same four .gitignore:3-6 ignores. The not_checked list admits the comparison was not made, yet the finding asserts it.
- Facts say 'CLI, tag and changelog agree at 0.2.0' and list tags v0.1.0 and v0.2.0 without saying they are local. `git ls-remote --tags origin` returns v0.1.0 only, and `pip index versions sushihub` returns 0.1.0 only. v0.2.0 exists on this machine and nowhere else.
- Sibling fact 'sushicore's local tags stop at v0.4.0' is right but incomplete: PyPI's newest sushicore is 0.4.0, sushicore origin/main declares 0.6.0, local declares 0.7.0 and is 18 commits ahead of origin. sushihub's floor was >=0.4.0 at v0.2.0, is >=0.5.0 at origin/main and >=0.7.0 at HEAD.
- F4 line ranges: release.yml build job is lines 8-25 and publish is 27-40, not 9-24 and 26-40. The conclusion does not change.
- F9 counts cli/install.py as a third installer entry point. Its docstring (cli/install.py:2-6) says it is the contributor's editable install; the root scripts are the user install from PyPI. Two roles, three files.
- F8 recommends copying .gitattributes-adjacent files from sushiengine 'which has both' .editorconfig and .clang-format: correct for those two, but sushiengine has no .gitattributes and no AGENTS.md; sushidsp and sushitrack are the siblings with .gitattributes and AGENTS.md.

### Findings

#### L1. [high] Folder name, remote name and product name disagree

Evidence: Working copy is D:/Projects/sushistack; `git remote -v` gives https://github.com/SushiSystems/SushiHub.git; README.md:1 is `# SushiHub` and README.md:3-5 says 'SushiStack is the applications; SushiHub is what installs them'. The plan docs/agent/plans/2026-09-22-rename-to-sushihub.md renamed the package, but the local folder kept the old name, and the machine workspace file .sushistack/workspace.toml points every tool path at D:/Projects/sushistack/dependencies/..., so this checkout is at once the SushiHub source repository and a SushiStack workspace root.

Recommendation: Decide with the owner whether the checkout moves to D:/Projects/sushihub and the workspace (dependencies/, .sushistack/) moves to its own directory outside the source repository. Until then the two roles share one tree and the name of the folder names the wrong one.

Review: confirmed. git remote -v gives SushiSystems/SushiHub.git, README.md:1 is '# SushiHub', folder is sushistack; .sushistack/workspace.toml points cmake, llvm and vcpkg at D:/Projects/sushistack/dependencies. README.md:32-33 and .gitignore:1 ('Managed by hub init', written by cli/sushihub/services/modules.py:34) show the dual role was designed, so the fix is an owner decision as the audit says.

#### L2. [high] The four standard checkers are missing from tools/

Evidence: tools/ contains only tools/record_cli_argv.py and tools/tests/test_record_cli_argv.py. Absent: tools/documentation/check_source_comments.py, tools/documentation/check_docs_layout.py, tools/documentation/check_changelog.py, tools/layering/check_layering.py. Siblings sushitrack and sushidsp carry tools/documentation/ and tools/layering/ (plus tools/common/ and tools/README.md).

Recommendation: Add the four checkers under the standard names and paths, shaped as the siblings', and a tools/README.md. Move record_cli_argv.py into an area folder (for example tools/cli/) so tools/ follows the `tools/<area>/` entry rule.

Review: confirmed. tools/ holds record_cli_argv.py and tests/ only; no tools/README.md. sushitrack and sushidsp both carry check_source_comments.py, check_docs_layout.py, check_changelog.py and layering/check_layering.py. Recommendation is brick-shaped (same names, same paths).

#### L3. [high] CI runs no checker, never builds or tests the GUI, and calls pytest directly

Evidence: .github/workflows/ci.yml:22-28 runs `pip install -e "./cli[test]"`, `python -m pytest cli/tests -q` and `python -m pytest tools/tests -q`. No step touches gui/ (72 tracked files, 5 test sources under gui/tests/), no checker runs, and the yardstick forbids pytest invoked directly in the workflow. The file is named ci.yml where the yardstick names it push.yml.

Recommendation: Have CI call the project CLI for tests and the four checkers, add a GUI configure/build/test job for both platforms (or record in docs/reference/KNOWN_ISSUES.md why it cannot run headless), and rename the workflow to push.yml.

Review: confirmed. ci.yml:22,24,28 call pip and pytest directly; no gui step; gui/tests has 5 *_test.cpp files; file is ci.yml, not push.yml. The audit omits two more rule breaks in the same file: no dependency cache (shape rule 3) and no printed CLI command (rule 4).

#### L4. [high] The release workflow publishes to PyPI without running tests or checking the tag against the version

Evidence: .github/workflows/release.yml:9-24 builds with `python -m build cli` and `twine check`, then release.yml:26-40 publishes. It has no test job, no checker job, no Windows job and no step comparing the pushed tag with cli/pyproject.toml:7. A `v*` tag on a commit whose pyproject still says another version uploads that other version.

Recommendation: Make the release workflow run everything the push workflow runs on both platforms first, and fail when the tag does not equal `v` plus the pyproject version.

Review: confirmed. release.yml build job is lines 8-25 and publish 27-40 (audit cites 9-24 and 26-40, off by one or two). No test, checker, Windows or tag-versus-pyproject step.

#### L5. [high] v0.2.0 was tagged locally but never pushed or published

Evidence: `git ls-remote --tags origin` lists refs/tags/v0.1.0 only; `python -m pip index versions sushihub` gives 'Available versions: 0.1.0'. The local annotated tag v0.2.0 (2026-09-22) and docs/reference/CHANGELOG.md:16 '## v0.2.0 — 2026-09-22' describe a release no user can install. README.md:6 and install.sh/install.ps1 send users to PyPI, where they get 0.1.0.

Recommendation: Tell the owner v0.2.0 is unshipped and ask whether to push the tag as it stands (its floor is sushicore>=0.4.0, which is on PyPI) or to skip it and ship v0.3.0 after sushicore is released. Either way the changelog heading must match a tag that exists on origin.

Review: found by review.

#### L6. [high] The pushed main already requires a sushicore that PyPI does not have

Evidence: `git show origin/main:cli/pyproject.toml` line 17 is `sushicore>=0.5.0`; PyPI's newest sushicore is 0.4.0 and sushicore's remote tags stop at v0.4.0. .github/workflows/ci.yml:22 runs `pip install -e "./cli[test]"`, which cannot resolve that floor, so CI on origin/main cannot be green. The continuous-integration skill says a red main is fixed before other work lands and no release is proposed while CI is red. The audit's F7 treats this as a medium, future risk at HEAD only.

Recommendation: Raise F7 to high and order the work: release sushicore (0.5.0 through 0.7.0 are untagged; its origin/main says 0.6.0, local 0.7.0, 18 commits unpushed) before pushing the three sushihub commits, then confirm CI is green before proposing v0.3.0. The audit's F6 advice to push the three commits would deepen the break if followed first.

Review: found by review.

#### L7. [medium] Two version numbers in one repository, and the GUI one is stale

Evidence: cli/pyproject.toml:7 `version = "0.2.0"`; gui/CMakeLists.txt:16 `project(sushihub_gui VERSION 0.1.0 LANGUAGES CXX)`. Tag v0.2.0 and the changelog heading `## v0.2.0 — 2026-09-22` follow the CLI. The GUI changed in v0.2.0 (changelog: 'Pointed the application's vcpkg fallback ...' in gui/CMakeLists.txt) without its version moving.

Recommendation: Name one source of truth (pyproject, since the tag follows it) and generate or check the CMake project version against it; a checker rule can enforce the equality.

Review: confirmed. cli/pyproject.toml:7 is 0.2.0, gui/CMakeLists.txt:16 is 0.1.0. The GUI number is read nowhere: grep for PROJECT_VERSION and sushihub_gui_VERSION under gui/ finds only the project() line, so it is dead as well as stale.

#### L8. [medium] A breaking change sits unreleased and three commits are unpushed

Evidence: Commit 8313fe1 `refactor(setup)!: take the selection rule and the base fragment from sushicore` is under `## Unreleased` in docs/reference/CHANGELOG.md:12; `git status -sb` reports `main...origin/main [ahead 3]`. Before v1.0.0 a breaking change demands a MINOR bump, so the next release is v0.3.0 with 4 entries since v0.2.0, and the rule 'propose a release when an Unreleased entry is breaking' is met. The entry itself does not say what breaks.

Recommendation: Push the three commits after owner approval, state the break in the changelog entry, and propose v0.3.0.

Review: confirmed. 8313fe1 carries '!', CHANGELOG.md:12 sits under Unreleased with 4 entries, status is 'ahead 3'. v0.3.0 is the right next version. The audit understates it: the v0.2.0 tag itself is also unpushed (see missed).

#### L9. [medium] Dependency floor points at a sushicore version that has no tag locally

Evidence: cli/pyproject.toml:17 `"sushicore>=0.7.0"`; D:/Projects/sushicore/pyproject.toml:7 `version = "0.7.0"`; `git -C D:/Projects/sushicore tag -l` lists only v0.1.0 to v0.4.0. If 0.7.0 is not on PyPI, `pip install -e ./cli[test]` in ci.yml:23 and every `pipx install sushihub` fail to resolve.

Recommendation: Confirm which sushicore versions are published and tagged; release and tag sushicore 0.7.0 before sushihub ships anything that requires it. This belongs to the cross-repository release order.

Review: confirmed. Understated; it should be high. pip index shows sushicore on PyPI stops at 0.4.0, remote tags stop at v0.4.0, sushicore origin/main is 0.6.0 and local is 0.7.0 (ahead 18). The floor at origin/main is already >=0.5.0, so the pushed main cannot install today; HEAD's >=0.7.0 widens it.

#### L10. [medium] Root lacks the agent and formatting files the layout requires; CLAUDE.md is under docs/

Evidence: Missing at the root: AGENTS.md, CLAUDE.md, .gitattributes, .editorconfig, .clang-format. docs/CLAUDE.md exists (it opens '# CLAUDE.md / ## Getting oriented'), where Claude Code does not load it automatically for work at the repository root. The repository holds C++ (gui/src), shell and PowerShell installers, so missing .gitattributes leaves install.sh line endings to each machine's git config.

Recommendation: Move docs/CLAUDE.md to the root (and add AGENTS.md naming the skills), add .gitattributes with `*.sh text eol=lf` and `*.ps1 text eol=crlf`, and add .editorconfig and .clang-format copied from the sibling that owns them (sushiengine has both).

Review: confirmed. AGENTS.md, CLAUDE.md, .gitattributes, .editorconfig, .clang-format absent at the root; docs/CLAUDE.md exists. sushiengine has .clang-format and .editorconfig but no .gitattributes; that one would come from sushidsp, sushitrack or sushiskills.

#### L11. [medium] Top-level folders depart from the standard tree

Evidence: gui/ holds an executable, which the layout places under applications/; its sources are in gui/src/ rather than source/, and its files are PascalCase (gui/src/bridge/LineQueue.cpp, gui/src/ui/screens/CommandsScreen.hpp) where the rule is snake_case with one symbol per file. contract/ is a top-level folder outside the allowed table. install.sh, install.ps1 at the root and cli/install.py are three installer entry points outside cli/ commands and tools/. Changelog line 'Lifted the CLI, the application and the contract to the repository root, the shape every sibling module already had' shows the current shape was chosen on purpose.

Recommendation: Owner decision: either move gui/ to applications/hub/ with source/ and snake_case names and give contract/ a home (docs/reference/ for the prose, a module or cli/ package data for the schemas), or record the exception in the repository-layout skill so all siblings agree. The root installers are served from sushisystems.io; state in docs where the served copy comes from.

Review: confirmed. gui/src/bridge/LineQueue.cpp and gui/src/ui/screens/CommandsScreen.hpp exist in PascalCase; contract/ holds 3 schemas and 2 markdown files; install.sh, install.ps1 and cli/install.py exist. cli/install.py:2-6 says it is the contributor's editable install, a different job from the root scripts, so 'three installer entry points' counts two roles as one.

#### L12. [medium] No sushi-module.toml although the repository reads and requires one from siblings

Evidence: No sushi-module.toml at the root; cli/sushihub/services/module_manifest.py and docs/reference/MODULE_MANIFEST.md define the manifest, and sushidsp and sushiengine carry one at their roots. The GUI's own dependencies are described in a different place, cli/sushihub/manifests/gui.deps.toml.

Recommendation: Decide whether the hub describes itself with the same manifest its modules use; if so add it at the root and derive gui.deps.toml from it.

Review: unclear. Facts hold: no root sushi-module.toml, cli/sushihub/manifests/gui.deps.toml exists. The repository-layout root table does not list sushi-module.toml, and sushicore, the nearest Python-tool sibling, has none; the hub is not a module in its own catalog. An owner question, not a defect under the skills.

#### L13. [medium] No workflow builds or packages the desktop application for release

Evidence: .github/workflows/release.yml:17-21 builds only `python -m build cli`. gui/ (72 tracked files, gui/CMakeLists.txt, gui/CMakePresets.json) has no packaging job, and the continuous-integration table requires 'everything above, then the packaging build' on a tag. F3 covers the missing CI build; nothing in the audit covers the release side.

Recommendation: Ask the owner how the application reaches users (cli/sushihub/services/gui.py and gui_env.py suggest a local build through `hub`). If it ships as a binary, add its packaging to release.yml; if it is always built on the user's machine, say so in gui/README.md and docs/reference/KNOWN_ISSUES.md.

Review: found by review.

#### L14. [medium] CI workflow breaks two more shape rules the audit did not list

Evidence: .github/workflows/ci.yml has no cache step keyed on cli/pyproject.toml (continuous-integration shape rule 3) and no job prints the CLI command it ran as its first line (rule 4). F3 names the direct pytest call and the file name only.

Recommendation: Fold both into the F3 rewrite: one push.yml whose jobs call the project CLI, echo that command first, and cache pip on the hash of cli/pyproject.toml.

Review: found by review.

#### L15. [low] Leftover scratch from earlier agents and tools in the working tree

Evidence: .argv-baseline/ holds 10 files from 2026-08-25 (sushiai.json, sushiai.after.json, ... sushiruntime.after.json) from the cmake-driver work that has since moved to sushicore; .superpowers/sdd/ holds only a .gitignore; cli/config.local.toml.bak (2026-09-14) is a hand backup; cli/build/ (bdist.win-amd64, lib) and cli/sushihub.egg-info/ are setuptools output; gui/build/ has three build trees (hub, ss, windows-x64), of which `ss` predates the rename to hub. All are ignored, none is tracked.

Recommendation: With owner approval delete .argv-baseline/, .superpowers/, cli/config.local.toml.bak, cli/build/ and the stale gui/build/ss tree. Remove the one-off `cli/config.local.toml.bak` line from .gitignore once the file is gone.

Review: confirmed. .argv-baseline has 10 JSON files dated Aug 25; .superpowers/sdd holds a 2-byte .gitignore; cli/config.local.toml.bak dated Sep 14; gui/build has hub (Sep 22), ss and windows-x64 (Sep 5). All ignored.

#### L16. [low] .gitignore mixes workspace rules into the source repository and misses common output

Evidence: .gitignore:1-6 ('Managed by `hub init`') ignores /dependencies/ and four module names (/sushiruntime/, /sushiengine/, /sushiai/, /sushiblas/) but not the other catalogued modules such as sushidsp or sushitrack, so a `hub add` of those inside this checkout would show as untracked. No rule for .pytest_cache/ (it is hidden only by the cache's own inner .gitignore), dist/ (release.yml writes cli/dist/), .venv/, venv/, imgui.ini, CMakeUserPresets.json or cmake_test_discovery_*.json. Scratch rules `.superpowers/` and `.argv-baseline/` are per-session leftovers. gui/.gitignore duplicates what one root rule could say.

Recommendation: After F1 is decided, drop the workspace block if the workspace leaves the repository, or generate the module list from the catalog. Add .pytest_cache/, dist/, .venv/, venv/, imgui.ini, CMakeUserPresets.json and /gui/build/ to the root file and delete gui/.gitignore.

Review: confirmed. Missing rules for dist/, .pytest_cache/, venvs and imgui.ini are real. One sub-claim is wrong: cli/sushihub/catalog.toml holds exactly four modules (sushiruntime, sushiengine, sushiai, sushiblas) and .gitignore:3-6 lists exactly those four; sushidsp and sushitrack are not catalogued.

#### L17. [low] CI tests Python 3.10 while the tools contract fixes Python 3.11

Evidence: .github/workflows/ci.yml:14 `python: ["3.10", "3.11"]` and cli/pyproject.toml:11 `requires-python = ">=3.10"`; the project-tools contract says checkers are Python 3.11, and `pytest tools/tests` runs on the 3.10 leg too (ci.yml:28).

Recommendation: Keep 3.10 for the package if that is the supported floor, but run tools/ and the checkers on the 3.11 leg only, or raise the floor to 3.11 across the Sushi Python packages so the rule is one.

Review: unclear. ci.yml:14 and pyproject.toml:11 are as cited. The 3.11 rule in project-tools covers the four checkers; record_cli_argv.py is not one of them, so the rule only bites once F2 lands. A note for the F2 work, not a defect today.

#### L18. [low] Merged local feature branches remain

Evidence: `git branch --merged main` lists feature/hub_help_and_doctor and feature/theme_tokens; neither exists on origin.

Recommendation: Delete both local branches after owner approval.

Review: confirmed. git branch -a --merged main lists feature/hub_help_and_doctor and feature/theme_tokens; neither is under remotes/origin.

#### L19. [low] Two newest changelog entries carry a scope prefix the others do not

Evidence: docs/reference/CHANGELOG.md:11 `- 2026-10-04 — docs: Marked ...` and :12 `- 2026-10-04 — setup: Took ...`; every other entry starts with the past-tense verb directly after the date, as the format requires. Line 12 also carries a reason clause ('so a bare hub install installs one SYCL toolchain').

Recommendation: Drop the `docs:` and `setup:` prefixes and the reason clause; a check_changelog.py rule (F2) would catch this.

Review: confirmed. CHANGELOG.md:11 'docs:' and :12 'setup:' prefixes and the 'so a bare hub install...' clause are there. Reason clauses also sit in the v0.2.0 section (lines 22, 23, 25, 29, 32), which the audit does not mention.

### Not checked

- Size of dependencies/, gui/build/ and cli/build/: the sizing command timed out after 120 s and was not repeated; no byte counts are reported.
- Contents of dependencies/ (toolchains, vcpkg, ur, build) were skipped as provisioned output.
- Whether sushihub 0.2.0 and sushicore 0.7.0 are actually published on PyPI; no network lookup was made.
- The GitHub side: whether CI is currently green, whether the `pypi` environment exists, branch protection, and remote tags (only local tags were read).
- The full module list in cli/sushihub/catalog.toml was not compared line by line against the .gitignore module block.
- Whether install.sh and install.ps1 at the root are byte-identical to what sushisystems.io serves (sushiweb was not opened).
- Git history for files that were once tracked and are large (no pack or history size audit).
- Documentation tree completeness (docs/modules/ is absent; status lines, links, archive candidates) belongs to the documentation dimension and was only listed, not audited.
- Source comment headers, licence headers and code-level SOLID shape in cli/ and gui/ belong to other dimensions and were not read.
- sushiai, sushiblas, sushiruntime, sushifx and sushiconverter were not opened for the sibling layout comparison; only sushicore, sushitrack, sushidsp and sushiengine root listings were read.

## Code shape

### Facts

- 229 tracked files: 82 .py, 31 .cpp, 29 .hpp, 61 .md, 6 .json, 4 .toml. 16 114 lines of Python and C++ in total. No TypeScript, no GLSL.
- Two products in one repository: the Python CLI `hub` (D:/Projects/sushistack/cli, package `sushihub` 0.2.0) and the C++17 ImGui desktop application (D:/Projects/sushistack/gui). `contract/` holds the three JSON schemas both sides read.
- cli/sushihub top level: 8 .py files, 1 189 lines (cli.py, config.py, console.py, describe.py, gui_config.py, gui_env.py, __init__.py, __main__.py).
- cli/sushihub/services: 23 files, 2 978 lines. cli/sushihub/setup: 20 files, 617 lines, of which 15 are re-export shims over sushicore.provision (5 to 29 lines each).
- cli/tests: 28 files, 3 602 lines, flat. tools: record_cli_argv.py (201 lines) plus tools/tests/test_record_cli_argv.py (96 lines).
- gui/src: bridge 4 files / 752 lines; contract 4 / 847; model 9 / 697; ui 36 / 4 031 (screens, widgets, forms, chrome); main.cpp 99. gui/tests: 5 suites plus FixtureFile.hpp, 868 lines, 37 TEST cases.
- Python dependency direction: cli.py -> services -> (config, console, setup) -> sushicore. Two cycles break it: config <-> console, and services <-> setup (see F3, F4). Third-party: typer, click, rich, keyring, sushicore.
- C++ dependency direction, as gui/src/CMakeLists.txt links it: bridge and contract are leaves; model -> bridge + contract; ui -> model; main -> ui. No include goes against that order; no cycle found.
- Twenty largest source files: gui/src/bridge/Process.cpp 560; cli/tests/test_identity.py 519; cli/sushihub/cli.py 469; gui/src/ui/screens/SettingsScreen.cpp 429; cli/sushihub/services/modules.py 393; services/identity.py 352; cli/sushihub/config.py 340; gui/src/ui/forms/GeneratedForm.cpp 338; gui/src/contract/Event.cpp 333; gui/src/ui/screens/InstallsScreen.cpp 324; gui/src/contract/Catalogue.cpp 276; services/releases.py 245; tests/test_add_binary.py 244; gui/src/ui/screens/ModulesScreen.cpp 243; tests/test_releases.py 240; services/gui.py 240; tests/test_gui_build.py 214; tests/test_presence.py 211; gui/src/ui/Theme.cpp 208; gui/src/ui/screens/CommandsScreen.cpp 204.
- Test layout: cli/tests is one flat pytest folder (no unit/integration/regression split, no mirror of the source path). gui/tests is one flat GoogleTest folder with files named `<subject>_test.cpp`, registered through gtest_discover_tests. No tests/regression, tests/golden or tests/benchmark anywhere.
- No tests at all: the whole gui/src/ui library (36 files, 4 031 lines), gui/src/model/Workspace, gui/src/main.cpp, cli/sushihub/services/setup.py, services/cli_install.py `install_cli`, services/discovery.py, cli/sushihub/gui_env.py, cli/install.py, install.sh, install.ps1.
- CI (.github/workflows/ci.yml) runs `pytest cli/tests` and `pytest tools/tests` only; the file has no gui, cmake or ctest step, so the 37 C++ tests never run in CI.
- Source comments: all 60 C++ files carry `@file`, `@brief` and `@author` (530 `@brief` in total) and no stacked `//` lines, TODO or separators. No source file in the repository carries a licence block (0 of 142 match `copyright`).
- Python comment census (AST over the 54 non-test files): 22 functions or classes without a docstring, 30 signatures without a return annotation, 24 module docstrings longer than six lines, 3 files without `from __future__ import annotations`. In tests: 193 without docstring, 317 without return annotation.
- Logging: neither product has a logger. No `logging.getLogger` or `K_LOGGER` in Python; no log category or log macro in C++. The CLI writes through sushicore's console; the GUI has one `fprintf(stderr)` in main.cpp:29.
- Tooling absent from the tree: no `.clang-format`, no `.clang-tidy`, no ruff/black/mypy configuration in cli/pyproject.toml, no tools/documentation/check_source_comments.py or any other checker.
- Untracked leftovers on disk, not part of the review: cli/build/lib/sushihub (a stale copy of the package from before the move to sushicore) and cli/tests/__pycache__ entries for five deleted test files.
- Verdicts. cli/sushihub top level (cli.py, config.py, console.py, describe.py, gui_*): needs targeted fixes.
- Verdict cli/sushihub/services: needs restructuring (terminal output, exit codes and policy are mixed in every service; no module error base).
- Verdict cli/sushihub/setup: needs restructuring (15 shims with no remaining job, a broken VerifyStep, a cycle with services).
- Verdict cli/tests and tools: needs targeted fixes (layout and naming, missing files listed above).
- Verdict gui/src/bridge: needs targeted fixes. gui/src/contract: needs targeted fixes. gui/src/model: sound, apart from the json type it passes on. gui/src/ui: needs targeted fixes and has no tests. gui as a whole: one repository-wide style pass (file names, constant names, enum shape, class layout) is open.

### Corrections from review

- Python census base: the audit says 54 non-test .py files. The tree has 53 (82 tracked, 28 under cli/tests, 1 under tools/tests). The census numbers themselves (22, 30, 24, 3, 193, 317) recompute exactly.
- F2: 'ten service/setup files import the console' is eleven; cli/sushihub/services/modules.py:14 is missing from the list.
- F3: gui_config.py raises SystemExit at one site (line 57), not two.
- F5 and the facts line: 16 of 20 files under cli/sushihub/setup are shims, not 15, because gpu_backends has ten files, not nine. Of those, only apt.py, probe.py and the gpu_backends files have no importer; pipeline, ordering, package_managers and toolchains are still imported by hub code and tests.
- F4: the services imports in setup/dependency_source.py are on lines 37-38, not 38-39.
- F7: cli/sushihub/catalog.toml lists four modules (sushiruntime, sushiengine, sushiai, sushiblas), so both 'Four of the five' and 'Five of the six' are false.
- F16: 'all 60 files' are PascalCase is 59; gui/src/main.cpp is lower-case. The title counts five rules and the evidence lists nine.
- F18: the undocumented symbols in tools/record_cli_argv.py span lines 59-104 (12 of the 22), not 59-74.
- F19: SUSHICORE_NAME is live code (services/modules.py:213), not dead.
- Recomputed and correct: 229 tracked files and the per-extension split; 16 114 lines; per-module file and line counts; the twenty largest files; 60 of 60 C++ files with @file and 530 @brief; 0 of 142 sources matching 'copyright'; 37 TEST cases (4, 8, 8, 7, 10); no nodiscard; ci.yml has no gui step.

### Findings

#### C1. [high] VerifyStep imports a module that does not exist; the `verify` and `all` pipeline steps cannot run

Evidence: D:/Projects/sushistack/cli/sushihub/setup/steps.py:119-120 does `from ..services import project as project_svc` and `from ..services.project import BuildType, Suite`. cli/sushihub/services/ holds no project.py (listing: binary, catalog, cli_install, customize, discovery, git_ops, git_state, gui, hub_install, identity, licence_file, links, module_manifest, modules, pipx, presence, releases, session, setup, status_report, token_store, update_check). setup/factory.py:102 still wires `"verify": VerifyStep()`, factory.py:105-111 builds it into `only == "all"`, and services/setup.py:15 declares `step: str = "all"` as the default. cli.py only ever passes "provision" (line 300) and "detect" (line 323), so the break is latent. No test names VerifyStep.

Recommendation: Delete VerifyStep, the "verify" and "all" entries in factory.py (lines 39, 102, 105-111) and the "all" default in services/setup.py:15, or ask the owner whether hub should verify at all. Deleting code is the owner's call; raise it before the module wave.

Review: confirmed. cli/sushihub/setup/steps.py:119-120 imports services.project; cli/sushihub/services has no project.py; factory.py:39 and :102-111 still wire verify and all; services/setup.py:15 defaults to "all"; cli.py:300 and :323 pass only provision and detect. No test names VerifyStep.

#### C2. [high] Services write to the terminal and return bare exit codes; no module error hierarchy exists

Evidence: python-code-style: 'A service never imports the command framework or writes to the terminal' and 'Each module defines its own exception classes, all derived from one module base error'. Ten service/setup files import the console: services/binary.py:13, cli_install.py:21, customize.py, discovery.py:15, git_ops.py:14, gui.py:29, session.py:15, setup.py:10, status_report.py:18, setup/steps.py:12. Every public service function returns `int` (modules.py:83 init, :115 add, :198 link, :262 update, :375 sync; services/setup.py:15, :81; gui.py:111-231) and reports failure by `console.error(...)` + `return 1`. services/customize.py and discovery.py import rich directly. Only identity.py (LoginError, SushiAccountError) and releases.py (ReleaseCorrupt) raise typed errors; there is no shared base.

Recommendation: Give the package one base error (e.g. HubError) and let services raise it; let cli.py catch it, print one line and set the exit code. Services return data (as status_report.build_status already does) and a thin presenter renders it. This is a public-surface change, so fix the shape with the owner first; status_report.py (build vs render) is the sibling to copy.

Review: confirmed. Console imports and int returns are there. The count is eleven files, not ten: services/modules.py:14 also imports console. identity.py does have its own base (SushiAccountError, :81) with six subclasses; the rest raise ValueError, RuntimeError or SystemExit. The fix (one base error, services return data) is brick-shaped.

#### C3. [high] `SystemExit` is the control-flow signal for 'not inside a workspace', caught in six places

Evidence: cli/sushihub/config.py:78 raises `SystemExit("Not inside a SushiStack workspace ...")` from workspace_root(). Callers catch it to mean 'no workspace': cli.py:85, config.py:181-182 (`except SystemExit: pass`), config.py:210, services/links.py:21, setup/dependency_source.py:103, setup/steps.py:82. gui_config.py also raises SystemExit (2 sites).

Recommendation: Raise a named error (WorkspaceNotFoundError under the base from F2), or add a `find_workspace_root() -> Path | None` beside the raising form, and replace the six `except SystemExit` sites. The entry point turns the error into exit code and message.

Review: confirmed. config.py:78 raises; cli.py:85, config.py:181 and :210, services/links.py:21, setup/dependency_source.py:103, setup/steps.py:82 catch. gui_config.py has one raise (line 57), not two; line 52 is a docstring.

#### C4. [high] Child processes write plain text into the --json event stream

Evidence: D:/Projects/sushistack/cli/sushihub/services/git_ops.py:24, services/pipx.py:62 and :108, and services/cli_install.py:31 call subprocess.run without capturing output, so git and pipx inherit hub's stdout. No service consults console.is_machine() (cli/sushihub/console.py:37 has no caller in services), and sushicore's renderer does not redirect file descriptors. The GUI starts exactly these paths with --json: gui/src/ui/screens/InstallsScreen.cpp:255, 269 and 286 run `hub --json add` and `hub --json update`. cli.py:10 and contract/README.md promise JSON events only on stdout. cli/tests/test_json_streams.py covers read-only, gui clean and account commands, not add, update or install-cli. F9 points at the stderr-bound console.console lines and misses this.

Recommendation: One brick runs every child for hub: it captures the child's output and emits it as line events in machine mode, and streams it otherwise. git_ops, pipx and cli_install call that brick. Add add, update and install-cli to the stream test with a recorded child. The module wave should confirm on a real run which git and pipx lines reach stdout.

Review: found by review.

#### C5. [medium] Two import cycles in the CLI package, both hidden by function-level imports

Evidence: (a) config <-> console: cli/sushihub/console.py:20 `from .config import legacy_cli_dir`; cli/sushihub/config.py:142 `from . import console` inside upgrade_workspace(). (b) services <-> setup: services/modules.py:16 `from ..setup.dependency_source import MODULE_MANIFEST_REL`, services/setup.py:11 `from ..setup import build_pipeline`; setup/dependency_source.py:38-39 `from ..services import links` and `from ..services.presence import is_binary`; setup/steps.py:75-78 imports services.links, services.catalog and services.presence inside report_readiness(). modules.py:110 and :384 import services.setup lazily for the same reason.

Recommendation: Declare the order config -> console is wrong for upgrade_workspace: return the upgrade result and let cli.py print it. Move the workspace readers (links, presence, catalog, module_manifest) below setup, or move report_readiness and manifest_sources up into services, so imports point one way and the lazy imports go.

Review: confirmed. console.py:20 imports config, config.py:142 imports console inside upgrade_workspace. services/modules.py:16 and services/setup.py:11 import setup; setup/dependency_source.py imports services at lines 37-38 (the audit says 38-39); steps.py:76-78 does it lazily.

#### C6. [medium] cli/sushihub/setup is mostly re-export shims with no caller left

Evidence: 15 of 20 files only re-export sushicore.provision: setup/apt.py, pipeline.py, probe.py, ordering.py, package_managers.py, toolchains.py, and nine under setup/gpu_backends/. No hub code or tracked test imports setup.apt, setup.probe or anything under setup/gpu_backends (grep over cli/ and tools/ finds only the stale cli/build copy). gpu_backends/windows_installer.py is 6 lines and exports nothing; its own docstring says 'No hub code imports a name from here directly'. gpu_backends/__init__.py:1 still says 'one brick per vendor, one branch per platform'. setup/probe.py:22 write_platform_paths and :16 render_local_config have no caller. toolchains.py re-exports the private names `_confirm_timeout` and `_find_windows_llvm`, which services/setup.py:45-47 then imports. dependency_source.py:33 re-exports sushicore's private `_parse_manifest` and cli/tests/test_dependency_fragment.py:14 tests it through hub.

Recommendation: Import sushicore.provision directly where it is used (factory.py, steps.py, services/setup.py, the tests) and delete the shims; ask sushicore for public names in place of `_confirm_timeout`, `_find_windows_llvm` and `_parse_manifest`. test_dependency_fragment belongs in sushicore. Deletion needs the owner's approval; the api-stability skill decides whether `sushihub.setup.*` is a public surface.

Review: confirmed. Shims and private re-exports are as cited, but the title overstates: pipeline, ordering, package_managers and toolchains are imported by factory.py:18-29, steps.py:14-15, services/setup.py:45 and :67 and three tests. Only apt, probe and the gpu_backends files have no importer. gpu_backends holds ten files, so 16 of 20 are shims. probe.py is not a pure re-export; it wraps write_platform_paths.

#### C7. [medium] config.py carries sushiruntime's build configuration and four unused symbols

Evidence: cli/sushihub/config.py is 340 lines doing five jobs: workspace location (63-128), legacy upgrade (131-160), identity URL (163-188), dependency directory (191-213), SYCL toolchain config (216-340). Dead in the tracked tree: `find_project_root` alias (line 87, no caller), `set_toolchain` (330, only the stale cli/build copy calls it), `Config.resolved_compilers` (285), `Config.resolved_windows_compiler` (300), `Config.llvm_bin` (295, only used by the previous), `TOOLCHAIN_COMPILERS` (222, only used by resolved_compilers), `target_bin = "sr_functional_tests"` (283). resolved_windows_compiler (308-314) is an if-chain over toolchain names and TOOLCHAIN_COMPILERS a second table over the same kinds, beside `selection.toolchain_keys()` at line 218: three places a new toolchain must touch.

Recommendation: Split into workspace.py, identity_url (beside session.py), deps_dir, and a provisioning config. Remove the dead compiler helpers after the owner confirms hub no longer builds a module. Whatever per-toolchain data stays belongs in one table owned by sushicore's selection.

Review: confirmed. Grep over sushistack and D:/Projects/sushicore finds no caller of find_project_root, set_toolchain, resolved_compilers, resolved_windows_compiler, llvm_bin or TOOLCHAIN_COMPILERS outside config.py. The split into four files is brick-shaped; the 'provisioning config' part needs the owner because Config subclasses sushicore's ToolConfig.

#### C8. [medium] services/modules.py: `add` and `link` are long multi-responsibility functions that duplicate cli_install

Evidence: cli/sushihub/services/modules.py:115-195 `add` (81 lines) resolves names, branches over presence state, picks clone versus binary, clones, installs the module CLI, provisions and prints. :198-259 `link` validates, reads a manifest, writes the link and provisions. `_install_module_cli` (41-63) repeats what services/cli_install.py:98-110 does (pyproject check, pipx.install editable, error line) with different wording and a different missing-pipx policy (warn and skip versus install pipx). cli_install.py:25 imports the private `_resolve_names` from modules. The docstring at modules.py:119 says 'Four of the five modules are cloned' while cli.py:185 says 'Five of the six'. modules.py:22-27 describes sushicore as living 'inside this repository (see `sushicore/`)', which the tree contradicts, and modules.py:214 says it is installed from PyPI.

Recommendation: Split modules.py into workspace init, add, link, update and self-update bricks; make name resolution a public function of catalog.py; let one function install a module CLI and have both `hub add` and `hub install-cli` call it.

Review: confirmed. modules.py:41-63 and cli_install.py:98-110 repeat the install; cli_install.py:25 imports _resolve_names. cli/sushihub/catalog.toml lists four modules, so 'Four of the five' (modules.py:119) and 'Five of the six' (cli.py:185, user-facing help) are both wrong, not only inconsistent.

#### C9. [medium] cli.py holds logic, separators and a second `--json` flag

Evidence: cli/sushihub/cli.py:104-106, 158-165, 262-264, 346-348 are separator comment lines (forbidden in source); the block at 158-165 has module constants sitting inside an unclosed banner. Lines 290-299 build the dependency source, the config and the derived selection inside the `install` command body rather than in a service. `home` (127-133) formats output itself and re-imports names already imported at line 26 (line 129). `status` declares its own `--json` option (143-144, 150-151) beside the root `--json` (53-55). Function-level imports at 238, 292-295, 431, 442, 453, 464. No command function has a return annotation (30 unannotated signatures in the package, 16 of them here).

Recommendation: Move the customize selection into services, drop the per-command `--json` or document it as an alias in one place, split the file by command group (workspace, modules, dependencies, gui, account) so the banners go, and annotate `-> None`.

Review: confirmed. Separators at cli.py:104-106 and 158-165 with constants inside the banner, selection logic at 290-299, the second --json at 143-151, function-level imports at 129, 238, 292-295, 431-464 all present.

#### C10. [medium] Output that bypasses the JSON event contract

Evidence: cli/sushihub/setup/steps.py:92, 98, 102, 105 write the readiness report through `console.console.print(...)`, the raw Rich console, instead of info/warn/success. services/customize.py:89-94 and services/discovery.py:74 do the same. cli.py:72 uses `typer.echo(ctx.get_help())`. contract/README.md is cited by cli.py:10 as requiring that stdout carry JSON events only under `--json`.

Recommendation: Route every line through the level functions of the console module, or give report_readiness a table event. The module wave should confirm against sushicore's LazyConsole what `console.console` resolves to in machine mode; that was not opened here.

Review: confirmed. Sites exist. The open question resolves from sushicore/renderer.py:263-267: under --json, console.console is a Rich console bound to stderr, so stdout stays clean and the lines leave the event stream instead. The title should say 'output that never reaches the event stream'. See the first missed item for the larger leak.

#### C11. [medium] Failures that are swallowed with neither a status nor a record

Evidence: cli/sushihub/config.py:181-182 `except SystemExit: pass`. services/token_store.py:59 `_decode` returns None for a corrupt stored session, so a damaged keyring entry reads as 'not signed in'; :80-81 `except keyring.errors.PasswordDeleteError: pass`; KeyringStore.load/save (68, 72) let every other keyring exception leave the module as a third-party type. services/identity.py:350 `_parse` turns an unreadable server body into `{}`. services/presence.py:63 returns None for an unreadable release manifest; services/licence_file.py:61 and :69, services/releases.py:241, services/git_state.py:38 and :47, services/git_ops.py:44 all map an OSError to a falsy value. cli/install.py:87 `except OSError: continue`. gui: Process::start returns nullptr on four distinct failures per platform (gui/src/bridge/Process.cpp:152, 166, 172, 198 and 337, 344, 350, 380) and CommandRun.cpp reports all of them as 'could not start <program>'.

Recommendation: For each site decide: raise the module's error, or return a result that names the reason. Wrap keyring at the store boundary and re-raise as the module's own error with `from error`. Process::start should return a status enum (or an expected-like pair) so the UI can say which step failed.

Review: confirmed. token_store.py:59 and :80-81, identity.py:347-351, cli/install.py:87 and the eight nullptr returns in Process.cpp read as cited. KeyringStore.clear ignoring PasswordDeleteError is its documented contract, not a swallowed failure; presence.py, licence_file.py, releases.py:241 and git_state.py sites were not opened.

#### C12. [medium] Neither product has a logger; the logging rules have nothing to attach to

Evidence: No `logging.getLogger`/`K_LOGGER` in cli/sushihub or tools. No log category header, logger or log macro in gui/src; gui/src/main.cpp:29 writes GLFW errors with `std::fprintf(stderr, ...)` and main.cpp:38-41, 51-55 exit with code 1 and no message. ParseError lines are kept in RunState.errors (gui/src/model/CommandRun.cpp:63-66) and shown or dropped by the widgets, never recorded.

Recommendation: Owner decision: whether the GUI gets a small logger module with one category per library (bridge, contract, model, ui), and whether the CLI adds `K_LOGGER = logging.getLogger("sushihub.<module>")` beside its console output. Until then the fallbacks in F10 leave no trace.

Review: confirmed. No logger in either product; gui/src/main.cpp:29 is the only fprintf in gui/src. The finding is an owner decision, correctly framed; stdout belongs to the CLI under the logging skill, so the CLI half is weaker than the GUI half.

#### C13. [medium] Event kinds are dispatched by if-chains in four files; a ninth kind edits all of them

Evidence: gui/src/contract/Event.cpp:277-329 chain over the `event` string, with command, header and panel parsed inline (281-311) while line, table, progress, result and prompt have their own parse_* functions. gui/src/model/CommandRun.cpp:103-119, gui/src/ui/widgets/EventLog.cpp:61-88 and gui/src/ui/screens/DeviceGrant.cpp:104-108 are `std::get_if` chains over the same variant. gui/src/contract/Catalogue.cpp:197-217 is a chain over the six parameter type names; gui/src/ui/forms/GeneratedForm.cpp:90-94, 157, 171-184, 285, 325 branch on ParameterType again; gui/src/ui/Theme.cpp:181-189 branches on level strings that Event.cpp:152 also lists.

Recommendation: Parse through a name-to-parser table in Event.cpp with one function per kind, and consume the variant with `std::visit` over an overload set so a missing kind fails to compile. Make the line level an enum parsed once in contract, and use a name table for ParameterType.

Review: confirmed. Event.cpp:277-329, CommandRun.cpp:103-119, EventLog.cpp:61-88, DeviceGrant.cpp:104-108, Catalogue.cpp:197-217 and Theme.cpp:181-189 are if-chains over the same kinds. Table plus std::visit is the fix the cpp-code-style skill names.

#### C14. [medium] nlohmann::json leaks through contract and model headers into the UI

Evidence: gui/src/contract/Event.hpp:8 and :91 (`ResultEvent::payload` is `nlohmann::json`), gui/src/contract/Catalogue.hpp:10 and :55 (`Parameter::default_value`), gui/src/model/InstallFacts.hpp:8, gui/src/ui/screens/InstallsScreen.hpp:12 and :51-60, gui/src/ui/screens/ModulesScreen.hpp:12 and :39-48. gui/src/CMakeLists.txt links nlohmann_json PUBLIC from sushihub_gui_contract. The screens read the status payload key by key although contract/status.schema.json fixes its shape and model/InstallFacts exists to do that reading. gui/src/ui/Theme.hpp:8 exposes ImVec4 the same way, inside the one library that is ImGui by definition.

Recommendation: Add a typed StatusPayload (workspace, hub, modules, dependencies) parsed in contract or model, hand screens that type, and keep nlohmann PRIVATE to contract. The dependencies skill names a third-party type in a public header as the trigger.

Review: confirmed. nlohmann/json.hpp is included by Event.hpp:8, Catalogue.hpp:10, InstallFacts.hpp:8, InstallsScreen.hpp:12 and ModulesScreen.hpp:12, linked PUBLIC at gui/src/CMakeLists.txt:20. The ImVec4 remark is not a defect, as the audit itself says. A typed StatusPayload is a brick; making the link PRIVATE is a build-file edit for the owner.

#### C15. [medium] Sibling screens are shaped differently and repeat the same argv handling

Evidence: gui/src/ui/screens/ModulesScreen.hpp:22 is `final`, SettingsScreen.hpp:23 and InstallsScreen.hpp:24 are not. SettingsScreen.hpp:32-34 leaves `name()` and `draw()` without `@brief`; the other two document them. The log member is `log_` in SettingsScreen.hpp:72 and `run_log_` in InstallsScreen.hpp:81. ModulesScreen starts work through FormOpener, the other two start CommandRun themselves. Stripping `--json` to build a label is written twice: gui/src/ui/forms/GeneratedForm.cpp:68-84 `spoken_line` and gui/src/ui/screens/InstallsScreen.cpp:209-223. `{hub, "--json", ...}` is assembled by hand at InstallsScreen.cpp:103, 255, 269-270, 286-287, GeneratedForm.cpp:268 and model/Workspace.cpp:47. The command name "status" is a constant in three files (InstallsScreen.cpp:24, ModulesScreen.cpp:21, SettingsScreen.cpp:37).

Recommendation: One brick in model builds a hub command line and its spoken label; every screen asks it. Make all Screen implementations `final`, name the shared members alike, and document overrides the same way in all three.

Review: confirmed. Only ModulesScreen is final; SettingsScreen.hpp:32-34 lacks @brief; log_ versus run_log_; "--json" assembled at the six cited sites; "status" constant in three files. model/Workspace.cpp:47 already builds {hub, --json, screen}, so the fix is to widen that function, not add a second brick beside it.

#### C16. [medium] Shell hard-codes which commands screens cover and where the commands screen sits

Evidence: gui/src/ui/Shell.cpp:36 `COMMANDS_INDEX = 3` must match the emplace order at :71-74. Shell.cpp:48-53 `covered_commands()` lists "doctor", "license", "login", "logout", "status", "whoami" by hand, while the screens that cover them keep their own constants (SettingsScreen.cpp:28-43, InstallsScreen.cpp:24, ModulesScreen.cpp:21-27). Shell.cpp:97 passes `std::string()` as the title bar's third argument every frame. gui/src/ui/screens/SettingsScreen.hpp:80-81 `alias_enabled_` is documented as 'which nothing yet reads back'.

Recommendation: Let Screen expose the commands it covers and have Shell collect them; route open_form through the stored pointer and derive the index from it. Remove the alias toggle or wire it, and record the open item in docs/design/REMAINING_WORK.md.

Review: confirmed. Shell.cpp:36 COMMANDS_INDEX = 3 against the emplace order at 71-74, the hand list at 48-53, the empty string at 97, SettingsScreen.hpp:80-81 alias_enabled_ all present.

#### C17. [medium] The C++ tree does not follow cpp-code-style in five repository-wide ways

Evidence: File names are PascalCase (gui/src/ui/Shell.hpp, gui/src/bridge/Process.cpp, all 60 files) against `snake_case`. Constants lack the `K_` prefix (gui/src/main.cpp:21 WINDOW_TITLE, :24 GLSL_VERSION; Shell.cpp:27 FRAME_FLAGS, :33, :36). Enums are unsized with lower-case enumerators and no per-enumerator comment (gui/src/contract/Catalogue.hpp:23-31). Access specifiers and namespace bodies are not indented (gui/src/ui/Screen.hpp:14-17, Shell.hpp:32-34). Project includes use quotes (Shell.cpp:6-11). `[[nodiscard]]` appears nowhere in gui/src although parse_event (Event.hpp:123), parse_catalogue (Catalogue.hpp:101), CommandRun::start (CommandRun.hpp:39) and Process::start (Process.hpp:32) all return results. parse_parameter_type (Catalogue.hpp:109) returns bool with an out-parameter. Process.hpp:84-87 marks state `mutable` so that `remember_exit` can be const. The layout is gui/src and gui/tests, not modules/<tier>/<module>/{include,source,tests}; tests are named `bridge_test.cpp`, not `test_bridge.cpp`. No .clang-format is tracked.

Recommendation: Add the .clang-format first, then run one mechanical pass per rule (rename, K_ prefix, enum shape, nodiscard) as separate commits. The layout move is a module-boundary decision for the owner.

Review: confirmed. Constants without K_, unsized lower-case enums (Catalogue.hpp:23, TableView.hpp:24), unindented access specifiers, zero nodiscard, mutable members at Process.hpp:84-87 all present. 'All 60 files' is loose: main.cpp is lower-case. The title says five ways and the evidence lists nine; the layout claim rests on repository-layout, which the brief did not name.

#### C18. [medium] gui/src/bridge/Process.cpp carries two platform implementations in one 560-line file

Evidence: gui/src/bridge/Process.cpp:35-304 is the Windows implementation and :305 onward the POSIX one, split by `#ifdef _WIN32` (lines 11, 35, 305). gui/src/ui/Browser.cpp:8-14 and :26-70 repeat the pattern. main.cpp:46 has an `__APPLE__` branch although no macOS target is declared.

Recommendation: Split into process_windows.cpp and process_posix.cpp selected by CMake, keeping the shared line-splitting (emit_complete_lines, flush_pending) in one file; the same for Browser. The platform-portability skill is the yardstick for the module wave.

Review: confirmed. Process.cpp #ifdef at 11, 35, #else at 305, #endif at 498; Browser.cpp 8-19 and 26-106; main.cpp:46 __APPLE__. Per-platform files are the brick-shaped fix, but selecting them means editing CMake, which is the owner's.

#### C19. [medium] Python source-comment rules are broken across the CLI

Evidence: Stacked `#` lines (two or more in a row): cli/sushihub/config.py 14 pairs (27-29, 49-51, 216-217, 220-224, 265-266, 275-278), services/modules.py 9 (22-26, 30-32, 277-280), cli.py 8, setup/factory.py 4 (113-116), setup/dependency_source.py 3, services/setup.py 3 (41-42, 63-65), services/presence.py 3. History in source: config.py:49-61, :78 of cli.py ('pre-2026-09-22'), config.py:134 ('used to be a file'), services/presence.py:6, services/pipx.py:4, setup/gpu_backends/windows_installer.py:3, services/discovery.py:3 ('Replaces the find-based search in the old run.sh'), plus the 'implementation moved to sushicore' line in each of the 15 shims. 24 module docstrings exceed six lines (tools/record_cli_argv.py 36, cli/install.py 21, services/gui.py 16, setup/dependency_source.py 16). 22 functions or classes have no docstring (cli/install.py:48, 106, 123, 128; services/customize.py:57, 72, 82, 87; services/cli_install.py:29; services/discovery.py:26; tools/record_cli_argv.py:59-74). Doxygen tags inside Python docstrings: config.py:106, 121, 140; modules.py:124-126, 208. cli/install.py is indented with tabs and starts with a shebang before its docstring. No file has `@author` or a licence block.

Recommendation: Move the reasons into docs/design (WORKSPACE_DECOUPLING.md is already cited at config.py:96) and cut each comment to one invariant line. Write tools/documentation/check_source_comments.py, which CLAUDE.md requires and the tree lacks, so the pass can be verified.

Review: confirmed. AST recount gives the same numbers: 22 undocumented, 24 module docstrings over six lines, stacked pairs config.py 14, modules.py 9, cli.py 8, factory.py 4. tools/record_cli_argv.py holds 12 undocumented symbols on lines 59-104, not 59-74. The phrase 'config.py:49-61, :78 of cli.py' is garbled.

#### C20. [medium] Dead code beyond the shims

Evidence: cli/sushihub/services/discovery.py (91 lines) is imported by nothing; services/gui.py:26 uses sushicore.discovery.ExecutableIndex instead. Config helpers listed in F6. setup/factory.py:39 STEP_NAMES names steps no command reaches. setup/dependency_source.py:52 MODULE_META_TABLE and :124 manifest_paths have no caller in the tracked tree. services/modules.py:27 SUSHICORE_NAME is used only for one refusal message and one test (cli/tests/test_catalog.py:48). gui/src/ui/screens/SettingsScreen.hpp:81 alias_enabled_.

Recommendation: Delete after owner approval; each is a separate small commit with its changelog line.

Review: confirmed. services/discovery.py has no importer; STEP_NAMES, MODULE_META_TABLE and manifest_paths have no caller. SUSHICORE_NAME is not dead: modules.py:213 uses it on a live refusal path of `hub link`. Drop that item from the list.

#### C21. [medium] Python class and file shape

Evidence: cli/sushihub/services/token_store.py holds a Protocol and two implementations in one file (TokenStore :35, KeyringStore :63, MemoryStore :84), against 'implementations are separate classes in separate files'; MemoryStore is a test double shipped in the package. services/identity.py (352 lines) holds five dataclasses, two exceptions and the client. Module-level singletons: services/gui.py:52-56 `_RUNNER`, `_DRIVER`, `_EXECUTABLES`; cli/sushihub/console.py:22 `_lazy`, rebound through `global` at :32. `@dataclass` without frozen/slots: config.py:256 Config, status_report.py:28 StatusReport. No class is marked `@typing.final`. Constants lack the `K_` prefix everywhere except cli.py:34-38 (config.py:52-61 CHECKOUT_CLI_DIR, DEFAULTS_FILE; identity.py:23-29; presence.py:29). gui.py:34-39 BuildType members are lower-case. cli/pyproject.toml declares `requires-python = ">=3.10"` against the 3.11 floor, which is why catalog.py:17, module_manifest.py:19 and pipx.py:18 each carry a tomli fallback. Layout is cli/sushihub, not cli/source/sushihub; `sushihub/__init__.py` re-exports nothing.

Recommendation: One file per primary class in services (token_store split three ways, identity's records apart from the client), dependencies passed through constructors rather than module globals, and a decision from the owner on the Python floor and the package layout before any rename.

Review: confirmed. token_store.py holds the protocol and both stores; MemoryStore has no importer in the package. gui.py:52-56 globals, lower-case BuildType members, requires-python >=3.10 with three tomli fallbacks all present. gui_config.py:64 is a third unfrozen dataclass the audit does not list.

#### C22. [medium] Tests: missing files, flat layout, private-name testing, a wall-clock wait

Evidence: No test file for cli/sushihub/services/setup.py (run, uninstall), services/cli_install.py install_cli (cli/tests/test_cli_install.py:7 tests modules and pipx, not that function), services/discovery.py, cli/sushihub/gui_env.py, cli/install.py. No GUI test touches gui/src/ui or model/Workspace. Tests reach private names: cli/tests/test_dependency_fragment.py:14 `_parse_manifest`, cli/tests/test_selection.py:80 `_owner_for_shipped`. cli/tests/test_cli_install.py:9 imports a helper from another test (`from .test_presence import Recorder`) instead of a tests/common module. gui/tests/bridge_test.cpp:44 polls with `sleep_for(1ms)`, so it depends on wall-clock time and on spawning a real child. Test files do not mirror source paths (test_add_binary, test_add_provisions, test_json_streams, test_doctor_table). 193 test functions lack a docstring.

Recommendation: Add the missing test files with the module wave, move shared doubles to cli/tests/common, sort tests into unit and integration, and add the GUI suites to CI through the project CLI once the owner allows a CI build step.

Review: confirmed. No test file for services/setup.py, discovery.py, gui_env.py or install.py; test_cli_install.py:9 imports Recorder from test_presence; bridge_test.cpp:44 sleeps. cli/tests/test_catalog.py:60-72 also tests the private _resolve_names, which the audit does not list.

#### C23. [medium] The GUI never reads the child's stderr

Evidence: D:/Projects/sushistack/gui/src/bridge/Process.cpp:183 hands the child the GUI's own stderr handle, and the POSIX branch at :355-356 redirects only stdin and stdout. Under --json, sushicore/renderer.py:263-267 sends console.console output to stderr, so the module readiness report (cli/sushihub/setup/steps.py:92-105) of `hub --json doctor`, which SettingsScreen.cpp:40 runs, never reaches the window. A Python traceback from hub is lost the same way; the screen shows only an exit code.

Recommendation: Decide with the owner: either Process gives stderr its own pipe and the model keeps it as error lines, or report_readiness emits a table event so nothing a screen needs travels on stderr. The second fix also closes F9.

Review: found by review.

#### C24. [medium] The audit's verdict for gui/src/bridge rests on about a tenth of its largest file

Evidence: D:/Projects/sushistack/gui/src/bridge/Process.cpp is the largest source file (560 lines) and the audit's not_checked list says only its header, failure returns and platform split were read. I read lines 36-150 and 176-186 and found the quoting and handle ownership sound, but waiter-thread join order, write_line partial writes and the POSIX spawn path at 305-498 remain unread by both passes.

Recommendation: The module wave reads Process.cpp in full before any split per F17, and bridge_test.cpp gains a case for a child that fails to start and one that exits with stdin still open.

Review: found by review.

### Not checked

- Line-by-line reading of gui/src/bridge/Process.cpp (560 lines): only the header, the failure returns and the platform split were read; handle lifetime, thread join order and partial-write loops were not.
- gui/src/ui/screens/SettingsScreen.cpp, InstallsScreen.cpp, ModulesScreen.cpp, CommandsScreen.cpp, DeviceGrant.cpp bodies: read by header and by grep, not in full.
- gui/src/ui/forms/GeneratedForm.cpp beyond lines 60-100, gui/src/ui/Theme.cpp, CatalogueSource.cpp, Browser.cpp, every file under ui/widgets and ui/chrome, gui/src/model/InstallFacts.cpp, RunLog, RunState, Workspace, bridge/LineQueue.
- gui/src/contract/Catalogue.cpp and Event.cpp lines 1-199 (the read_* helpers).
- cli/sushihub/describe.py, gui_config.py, gui_env.py, services/releases.py, services/identity.py lines 60-300, services/licence_file.py, pipx.py, catalog.py, module_manifest.py, update_check.py, hub_install.py, git_state.py, customize.py and discovery.py bodies.
- cli/install.py beyond lines 75-95, install.sh, install.ps1.
- The content of any test: cli/tests and gui/tests were inventoried by name, includes and grep, not read for assertion quality, seeds or tolerances.
- tools/record_cli_argv.py and tools/tests beyond the AST census.
- Whether `console.console.print` breaks `--json` output (F9): depends on sushicore's LazyConsole, which lives in another repository and was not opened.
- Whether any `sushihub.setup.*` shim is imported by another repository (sushiruntime, sushiengine, sushiai, sushiblas); only this repository was searched.
- Formatting conformance (column limit 100, trailing commas, quote style) was not measured; no formatter configuration exists to measure against.
- Per-symbol Doxygen audit of the C++ (verb-first briefs, eight-line limit, @param only for rules): only the presence of @file/@brief/@author and the absence of forbidden markers were counted.
- contract/*.schema.json, catalog.toml, defaults.toml, manifests/gui.deps.toml, CMakePresets.json and the two workflow files beyond the first 30 lines of ci.yml (file-format and CI dimensions).
- Licence headers and LICENSE content (licence dimension); documentation tree (documentation dimension); CLI experience (CLI dimension).
- Untracked directories cli/build, gui/build, dependencies/, .superpowers/, .argv-baseline/ and all __pycache__ were skipped as instructed.

## The estate

The same audit ran over eleven repositories on the same day. Each repository holds its own
report at `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md`. Counts include findings added by review.

| Repository | High | Medium | Low |
| --- | --- | --- | --- |
| sushistack | 24 | 59 | 15 |
| sushicore | 22 | 52 | 25 |
| sushiruntime | 25 | 67 | 26 |
| sushiengine | 16 | 65 | 29 |
| sushiai | 14 | 62 | 29 |
| sushiblas | 17 | 63 | 24 |
| sushidsp | 15 | 66 | 27 |
| sushitrack | 24 | 72 | 20 |
| sushiskills | 8 | 27 | 12 |
| sushiweb | 15 | 42 | 19 |
| sushifx | 7 | 12 | 7 |

## Licence research for Sushi Systems

**Not legal advice.** Top pick: **PolyForm Noncommercial 1.0.0** plus a separate signed commercial licence. No candidate implements "individuals yes, companies no" literally: every one tests the purpose of use, not who the user is.

Clauses were fetched on 2026-10-05 through a fetch tool that summarises. The four PolyForm texts and FSL came back whole; BUSL, Prosperity, Commons Clause, CC, Apache and the OSD came back as quoted fragments.

### 1. Operative clauses

**PolyForm Noncommercial 1.0.0** (https://polyformproject.org/licenses/noncommercial/1.0.0)
- "Any noncommercial purpose is a permitted purpose." The word "noncommercial" is not defined.
- Personal uses: "Personal use for research, experiment, and testing for the benefit of public knowledge, personal study, private entertainment, hobby projects, amateur pursuits, or religious observance, without any anticipated commercial application, is use for a permitted purpose."
- Organisations: "Use by any charitable organization, educational institution, public research organization, public safety or health organization, environmental protection organization, or government institution is use for a permitted purpose regardless of the source of funding or obligations resulting from the funding."
- Distribution: "The licensor grants you an additional copyright license to distribute copies of the software."
- Changes: "...to make changes and new works based on the software for any permitted purpose."
- Patents: "The licensor grants you a patent license for the software that covers patent claims the licensor can license, or becomes able to license, that you would infringe by using the software."
- Notices: recipients must get the terms or their URL, plus "any plain-text lines beginning with `Required Notice:`".
- Cure period: 32 days after written notice. No sublicensing.
- "Your company is any legal entity, sole proprietorship, or other kind of organization that you work for".

**PolyForm Strict 1.0.0** (https://polyformproject.org/licenses/strict/1.0.0)
- Same permitted purposes, but the grant is "...for any permitted purpose, other than distributing the software or making changes or new works based on the software."

**PolyForm Small Business 1.0.0** (https://polyformproject.org/licenses/small-business/1.0.0)
- Permits company use "if your company has fewer than 100 total individuals working as employees and independent contractors, and less than 1,000,000 USD (2019) total revenue in the prior tax year."

**PolyForm Shield 1.0.0** (https://polyformproject.org/licenses/shield/1.0.0)
- "Any purpose is a permitted purpose, except for providing any product that competes with the software or any product the licensor or any of its affiliates provides using the software."

**Prosperity Public License 3.0.0** (https://prosperitylicense.com/versions/3.0.0)
- "Limit your use of this software for commercial purposes to a thirty-day trial period."
- "If you use this software for work, your company gets one trial period for all personnel, not one trial per person."
- Personal-use and organisation wording matches PolyForm Noncommercial.
- Contributions back under Apache-2.0, MIT, BSD-2-Clause or Blue Oak "doesn't count as use for a commercial purpose".
- "The contributor can't revoke this license."
- Copyright grant: "to do everything with this software that would otherwise infringe their copyright in it". Patent grant: yes.

**CC BY-NC-SA 4.0** (https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- "NonCommercial means not primarily intended for or directed towards commercial advantage or monetary compensation."
- "Patent and trademark rights are not licensed under this Public License."
- Adaptations must carry the same licence.
- CC's own FAQ (https://creativecommons.org/faq/): "We recommend against using Creative Commons licenses for software."
- Its reasons: "CC licenses do not contain specific terms about the distribution of source code", patents are not addressed, and "our licenses are currently not compatible with the major software licenses".

**Business Source License 1.1** (https://spdx.org/licenses/BUSL-1.1.html, https://mariadb.com/bsl11/)
- "The Licensor hereby grants you the right to copy, modify, create derivative works, redistribute, and make non-production use of the Licensed Work."
- "Effective on the Change Date, or the fourth anniversary of the first publicly available distribution of a specific version of the Licensed Work under this License, whichever comes first, the Licensor hereby grants you rights under the terms of the Change License."
- The change licence must be GPL-2.0-or-later compatible.

**Functional Source License 1.1** (https://fsl.software, text from the getsentry/fsl.software repository)
- "A Permitted Purpose is any purpose other than a Competing Use."
- Permitted purposes "specifically include using the Software: 1. for your internal use and access".
- "We hereby irrevocably grant you an additional license to use the Software under the Apache License, Version 2.0 that is effective on the second anniversary".

**Commons Clause 1.0** (https://commonsclause.com/)
- "...the License does not grant to you, the right to Sell the Software."
- "Sell" means providing "for a fee or other consideration (including without limitation fees for hosting or consulting/ support services related to the Software), a product or service whose value derives, entirely or substantially, from the functionality of the Software."
- Its FAQ: "you may embed and redistribute Commons Clause software in a larger product, and you may distribute and even 'sell' ... your product."

### 2. Comparison

| Licence | Individual, personal/hobby/study/research | Company internal use | University, charity, government | Sell it or a product on it | Modify / redistribute | Patent grant | SPDX id (list 3.29.0) |
|---|---|---|---|---|---|---|---|
| PolyForm Noncommercial | Yes | No, if the purpose is commercial | Yes, by name, whatever the funding | No | Both, for permitted purposes, with notices | Yes | `PolyForm-Noncommercial-1.0.0` |
| PolyForm Strict | Use only | No | Use only | No | Neither | Yes | None (SPDX page returns 404) |
| PolyForm Small Business | Not addressed; the grant is for company benefit | Yes, under 100 people and USD 1M | Not addressed | Yes, if small | Both | Yes | `PolyForm-Small-Business-1.0.0` |
| PolyForm Shield | Yes | Yes | Yes | Yes, unless it competes | Both | Yes | None (404) |
| Prosperity 3.0.0 | Yes | 30-day trial, once per company | Yes, by name | Only inside the 30 days | Both, with notices | Yes | None (404) |
| CC BY-NC-SA 4.0 | Yes | Unclear ("primarily intended") | Yes if non-commercial | No | Both, share-alike | No, excluded | `CC-BY-NC-SA-4.0` |
| BUSL 1.1 | Yes | Non-production only | Non-production only | No, until the change date | Both | Not seen in the fetched text | `BUSL-1.1` |
| FSL 1.1 | Yes | Yes, including production | Yes | Yes, unless it competes | Both | Yes, narrow | `FSL-1.1-ALv2`, `FSL-1.1-MIT` |
| Apache-2.0 + Commons Clause | Yes | Yes | Yes | Only the software itself is barred | Both | Yes (Apache §3) | None for the clause |
| Custom | As drafted | As drafted | As drafted | As drafted | As drafted | As drafted | `LicenseRef-…` only |

Why the contrasts fail the owner's intent:
- **Small Business, Shield, FSL, Commons Clause** let companies use the software in commerce.
- **BUSL and FSL** turn into GPL-compatible or Apache/MIT code after four or two years, which contradicts "never".
- **Strict** stops individuals from forking or patching, which contradicts "benefit without limit".
- **CC BY-NC-SA** has no patent licence and its steward advises against it for software.

**Tooling**
- **PyPI metadata:** core metadata 2.4 takes any valid SPDX expression in `License-Expression`, including `LicenseRef-…` (https://packaging.python.org/en/latest/specifications/core-metadata/). PolyForm Noncommercial works as-is; Prosperity needs a `LicenseRef-`.
- **PyPI terms:** they do not require open source (https://policies.python.org/pypi.org/Terms-of-Use/). The uploader does grant "the PSF and all other users of the web site an irrevocable, worldwide, royalty-free, nonexclusive license to reproduce, distribute, transmit, display, perform, and publish the Content". That grant has no purpose limit and conflicts directly with Strict.
- **GitHub:** detection uses Licensee, which "relies on the crowdsourced license content and metadata from choosealicense.com". None of the candidates is in GitHub's keyword table, so the repository will not show a recognised licence badge.
- **OSI:** none of the candidates is on https://opensource.org/licenses.

**Known users**
- BUSL: MariaDB and HashiCorp (change licence MPL 2.0 after four years, https://www.hashicorp.com/en/bsl).
- FSL: Sentry, Codecov and GitButler.
- Commons Clause: listed on faircode.io.
- PolyForm Noncommercial: the search turned up only small GitHub projects.
- Prosperity and CC BY-NC-SA for software: I found no verified adopter.

### 3. Honest wording

The Open Source Definition (https://opensource.org/osd) rules all of these out:
- Criterion 1: "The license shall not restrict any party from selling or giving away the software".
- Criterion 6: "it may not restrict the program from being used in a business".

The owner's request says "open source licence"; what they describe cannot be called that.

- **Use:** "source-available", "free for non-commercial use", "commercial use requires a licence from Sushi Systems".
- **Avoid "open source".**
- **Avoid "fair-code":** faircode.io lists six licences and PolyForm is not one of them.
- **Avoid "Fair Source":** that label requires delayed open-source publication.

### 4. Leaving Apache-2.0

- **What stays Apache forever:** Apache §2 grants "a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license". Every version already published stays Apache-2.0, including PyPI sdists and wheels and existing clones. Anyone may fork the last Apache commit and sell it. Only new versions can carry the new licence.
- **The LLVM-exception repository:** the exception lets users ship compiled-in portions "without complying with the conditions of Sections 4(a), 4(b) and 4(d)". Later versions lose that.
- **Past outside contributions:** Apache §5 puts them under Apache-2.0, which permits sublicensing and "additional or different license terms" for derivative works. They can stay in a relicensed work if their notices are kept.
- **Future outside contributions:** under a non-commercial outbound licence, the owner would receive only non-commercial rights and could not sell them. A CLA is needed, either a broad licence grant with the right to relicense or an assignment.
- **DCO is not enough:** it certifies origin, grants nothing, and its text refers to "the open source license indicated in the file" (https://developercertificate.org/).
- **Verified here:** `D:\Projects\sushistack` has 252 commits, all by one author under two addresses (`git shortlog -sne --all`). The other repositories were not checked.

### 5. Dual-licence setup

1. One party holds all copyright, through sole authorship plus a CLA.
2. The public `LICENSE` carries the non-commercial text and a `Required Notice:` line.
3. A `COMMERCIAL.md` says how to buy.
4. The commercial licence is a signed agreement per customer. It should cover scope, seats or products, redistribution of binaries, term, warranty, governing law and venue.
5. Binaries ship under that agreement or an EULA.
6. A trademark policy covers the names, because none of these licences grants trademark rights.

### 6. File headers

REUSE 3.3 requires a copyright notice and an `SPDX-License-Identifier` in each header, and licence texts in `LICENSES/` named by identifier (https://reuse.software/spec-3.3/).

C++ and GLSL, placed before the `/** @file` block:

```
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 Sushi Systems
```

- Python uses the same two lines with `#`.
- `pyproject.toml` takes `license = "PolyForm-Noncommercial-1.0.0"` and `license-files = ["LICENSE"]`.
- `LICENSE` takes the unmodified text plus `Required Notice: Copyright Sushi Systems (<url>)`.
- To advertise the dual offer in the expression, use `PolyForm-Noncommercial-1.0.0 OR LicenseRef-Sushi-Commercial` with a matching file in `LICENSES/`.
- Today `D:\Projects\sushistack\cli\pyproject.toml` has no licence field, and I found no SPDX line in the repository's own files.

### 7. Third-party components

The owner's licence covers only the owner's code.
- **MIT, BSD, Apache-2.0:** these keep their own terms. Their notices go in a third-party notices file, and anyone may still use those parts commercially.
- **LGPL:** it needs dynamic linking or relinkable objects, and the outer licence must permit modification for the user's own use. PolyForm Noncommercial does; Strict does not. This is from memory; I did not fetch the LGPL text.
- **GPL:** it cannot be combined with a non-commercial outbound licence. `LICENSE-gpl3.txt` exists under `dependencies\vcpkg\buildtrees\sdl2\...\src\hidapi\`; hidapi also ships BSD and original-licence files, so pick one of those explicitly.
- **Proprietary SDKs:** they stay under their own EULA and may forbid redistribution alongside public source. Check each one.

### 8. Points for a lawyer, especially under Turkish law

Only the first item was confirmed by a search result. The rest are from memory, because the fetch of the statute PDF returned no article text.
- **Written form:** FSEK (Law 5846) art. 52 requires contracts over economic rights to be in writing with each right listed. Does a public licence posted online satisfy it, and does the commercial licence need a wet or qualified e-signature?
- **Who the licensor is:** the natural person or the company, and how economic rights reach the company (art. 18, 48, 56).
- **"Noncommercial" is undefined** in PolyForm, and the licence has no governing-law or venue clause.
- **The "Fair Use" section** has no Turkish equivalent.
- **The liability disclaimer** may not hold against the Code of Obligations or consumer law.
- **The PyPI upload grant:** does it weaken the non-commercial restriction for redistribution?
- **Modifying PolyForm:** may its text be altered or supplemented?
- **Trademark registration** for the Sushi Systems names.
- **Tax treatment** of licence fees.

### 9. Ranked recommendation

1. **PolyForm Noncommercial 1.0.0** with a separate commercial licence. It has an SPDX identifier, a patent grant, a patent-defence clause, lawyer-drafted text and a cure period. It blocks commercial use with no time limit.
2. **Prosperity 3.0.0.** Same purpose test, plus a built-in 30-day commercial trial, a contributions-back carve-out and express irrevocability. It has no SPDX identifier.
3. **A custom licence**, only if the owner wants a rule the two above cannot express, such as "natural persons only" or "no government use". It costs a lawyer, a `LicenseRef-` and distrust from tooling.

**Gap against "individuals yes, companies no"**

| Case | PolyForm Noncommercial | Prosperity 3.0.0 |
|---|---|---|
| Freelancer on paid work | Not permitted; an individual is blocked | 30-day trial, then not permitted |
| Sole trader | Not permitted; "sole proprietorship" counts as a company | One 30-day trial for the business |
| Student | Permitted (personal study, educational institution) | Permitted |
| University lab | Permitted even when a company funds the work ("regardless of the source of funding") | Same |
| Non-profit | Permitted if it is a "charitable organization"; a trade association or foundation running a business is unclear | Same |
| Company evaluating | Not permitted; needs a separate evaluation grant | Permitted for 30 days, once per company |

Three gaps remain in both:
- A natural person earning money is stopped. That matches "nobody earns money" but not "individuals without limit".
- Government bodies and company-funded university labs use it free, which the owner did not mention.
- A company using it for a non-commercial purpose is arguably allowed, because the test is purpose, not legal form.

Prosperity adds a fourth gap: 30 days of free commercial use.

### not_checked

- Full verbatim text of BUSL 1.1, Prosperity 3.0.0, CC BY-NC-SA 4.0 and the Commons Clause FAQ; only fragments came back.
- The BUSL patent position.
- Whether Prosperity's "contributor and source code lines" need a specific header form.
- Whether a PolyForm trial licence exists, and PolyForm's policy on modified texts (its about page returned 404).
- The CC FAQ entry on the NonCommercial clause, which was truncated.
- FSEK articles 18, 38, 48, 51 and 56, the Code of Obligations and consumer law.
- Acceptance by vcpkg, conda-forge, Homebrew, Debian and Fedora.
- GitHub's exact display for an unrecognised licence.
- The Trove classifier to use.
- Adopters of Prosperity and of CC BY-NC-SA for software.
- LGPL and GPL texts.
- Every Sushi repository other than `D:\Projects\sushistack`: contributor history, headers, which one carries the LLVM exception.
- The actual licence of each dependency under `D:\Projects\sushistack\dependencies`, and any proprietary SDK EULA.

### verification_output

- Nothing was written, edited, moved or deleted in any repository, so item 5 has nothing to syntax-check.
- No build, test or project CLI was run. No state-changing git command was run; the only git commands were `git shortlog -sne --all` and `git ls-files`, which returned:

```
   250	Mustafa Garip <mustafa.garip3434@hotmail.com>
     2	Mustafa Garip <51916290+sushimg@users.noreply.github.com>
LICENSE
```

- The scratchpad was not used (0 bytes).
- One file exists that I did not choose to create: the fetch tool saved the 444 KB statute PDF to `C:\Users\sushi\.claude\projects\D--Projects-sushistack\22bbebbf-733a-4f1a-8c0e-c4cf81eb78ae\tool-results\webfetch-1791148603919-11hp6h.pdf`. I left it in place.
- The humanizer skill was loaded before writing this report.
