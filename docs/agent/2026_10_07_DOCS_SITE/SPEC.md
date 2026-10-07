# Documentation site

**Status:** Open — sub-projects 1 and 2 of 3 built on 2026-10-07; the site is not deployed and sub-project 3 has not started.

A public site at `docs.sushisystems.io` that shows how the SushiStack applications are built:
guides, architecture pages, C++ API reference and a FAQ. Nothing is written for the site. Every
page is compiled from the `docs/` tree and the Doxygen comments of the repositories, and the
site looks like the marketing site of sushiweb because it draws from the same `@sushi/brand`
package.

This document is the programme design. Each sub-project in section 2 gets its own `SPEC.md` and
`PLAN.md` in the repository that owns it.

## 1. Owner decisions, 2026-10-07

| # | Decision |
| --- | --- |
| D1 | Seven repositories publish in full: sushistack, sushicore, sushiruntime, sushiblas, sushiai, sushidsp, sushitrack. sushiengine publishes its architecture pages and guides and no API reference. sushiweb, sushiskills and sushifx do not publish |
| D2 | The site is a fourth application of the sushiweb monorepo, `apps/docs`, deployed as its own Vercel project |
| D3 | Each repository produces a documentation bundle in its own CI and attaches it to a release. The site downloads the bundles a manifest pins |
| D4 | Each repository carries its own FAQ at `docs/guides/FAQ.md`. Questions about the stack as a whole live in sushistack's |
| D5 | Content stays in English. The interface (menus, search, buttons) is in `en`, `tr` and `no` through `@sushi/i18n-core` |
| D6 | One domain, `docs.sushisystems.io`. `api.sushisystems.io` stays free for an HTTP API |
| D7 | The site is built with Astro and searched with Pagefind |
| D8 | The bundle producer lives in sushicore and every CLI exposes it as `docs bundle` |
| D9 | `docs` becomes a command group on every CLI. Bare `sr docs` still builds the Doxygen HTML; `sr docs bundle --release X.Y.Z` builds the bundle. `hub` and `st`, which have no `docs` today, get the group with `bundle` alone. sushicore has no CLI and runs `python -m sushicore.docs_bundle --release X.Y.Z` |
| D10 | A published page may link to a file the bundle does not carry. A repository that sets `source_url` gets that link turned into a link to the file on GitHub at the bundle's commit; a repository without it, sushiengine, gets the link's text and no link. The producer stops only when the target does not exist |

## 2. Sub-projects

| # | Sub-project | Owner repository | Delivers |
| --- | --- | --- | --- |
| 1 | Bundle contract and producer | sushicore | The `bundle.json` schema, `docs bundle` on every CLI, one bundle built from sushiruntime |
| 2 | Site | sushiweb, `apps/docs` | A static site compiled from pinned bundles, live on `docs.sushisystems.io` |
| 3 | Rollout | the eight publishing repositories | `docs/publish.toml`, Doxygen XML, `FAQ.md`, a release step that attaches the bundle and proposes the manifest change |

Order: 1, then the sushiruntime part of 3, then 2, then the rest of 3. The site work starts
with a real bundle in hand. sushiruntime goes first because it has a Doxyfile and a small
manual, eight published pages, which exercises every part of the contract without the size of
sushiengine.

## 3. Data flow

```
repository at tag vX.Y.Z
    CI runs `<cli> docs bundle`
        -> docs-bundle-X.Y.Z.tar.gz and docs-bundle-X.Y.Z.tar.gz.sha256 on the GitHub release

sushiweb/apps/docs/content.manifest.toml      repository -> version, sha256
    Vercel build: fetch -> verify -> read -> Astro pages -> Pagefind index -> static HTML
```

The site shows the version the manifest pins, so one commit of sushiweb always builds the same
site. A repository's release step opens a pull request in sushiweb that changes its own entry
in the manifest; merging it redeploys. The first version has no version selector.

## 4. The bundle contract

The contract is the only thing the two sides share. The site reads `bundle.json` and nothing
else about a repository; a repository that changes its `docs/` layout or its API generator
keeps the site working as long as the bundle keeps the schema.

### 4.1 Archive layout

```
bundle.json
pages/<section>/<FILE>.md        the published manual pages
pages/<section>/<asset>          images a published page links to
api/xml/                         Doxygen XML; absent when the repository publishes no API
```

### 4.2 `bundle.json`

```json
{
  "schema": 1,
  "repository": "sushiruntime",
  "title": "SushiRuntime",
  "summary": "One sentence from publish.toml.",
  "version": "0.5.0",
  "commit": "0123abcd...",
  "source_url": "https://github.com/SushiSystems/SushiRuntime",
  "pages": [
    {
      "path": "pages/guides/BUILDING.md",
      "section": "guides",
      "title": "Building",
      "order": 3,
      "source": "docs/guides/BUILDING.md"
    }
  ],
  "assets": ["pages/guides/images/graph.png"],
  "faq": "pages/guides/FAQ.md",
  "api": { "format": "doxygen-xml", "root": "api/xml" }
}
```

| Field | Rule |
| --- | --- |
| `schema` | An integer. The site refuses a number it does not know |
| `repository` | The `name` of `docs/publish.toml`: lower-case letters and digits, the first segment of the repository's routes |
| `source_url` | The repository's address, or `null`. With an address, the site turns a link that leaves the bundle into `<source_url>/blob/<commit>/<path>`; with `null`, into plain text |
| `assets` | Every file under `pages/` that is not a page |
| `section` | One of `getting_started`, `guides`, `architecture`, `reference` |
| `title` | The page's first level-one heading |
| `order` | The position of the page's link in the repository's `docs/README.md` |
| `source` | The path in the repository, so a page can link to its source |
| `faq` | The FAQ page's path, or `null` |
| `api` | The object above, or `null` |

Links between published pages stay relative inside the bundle. The site turns them into
routes. A link whose target is not in `pages` or `assets` leaves the bundle; the site resolves it against
the page's `source` and treats it as `source_url` says.

The written form of the contract is `docs/reference/DOCS_BUNDLE.md` in the SushiCore
repository. A golden `bundle.json` in SushiCore's tests pins it; the site writes its validator
from that page.

### 4.3 `docs/publish.toml`

The repository decides what leaves it.

```toml
name = "sushiruntime"
title = "SushiRuntime"
summary = "The task runtime every SushiStack application schedules its work on."
sections = ["getting_started", "guides", "architecture", "reference"]
exclude = ["reference/KNOWN_ISSUES.md"]
api = true
source_url = "https://github.com/SushiSystems/SushiRuntime"
```

sushiengine's file lists `getting_started`, `guides` and `architecture`, sets `api = false` and
has no `source_url`. `sections` takes those four names and no other, so `docs/agent/`,
`docs/archive/` and `docs/design/` cannot be published. An `exclude` entry that names no file
stops the producer, because a misspelt exclusion would publish the page it meant to hide.

`docs/publish.toml` is a new entry of the `docs/` tree. The `documentation` skill in SushiSkills
names it, and `K_DOCS_ENTRIES` in each repository's `tools/documentation/check_docs_layout.py`
takes it, in the same change that adds the file.

### 4.4 The producer

`docs bundle` does four things: reads `docs/publish.toml`, collects the listed pages and the
assets they link to, runs Doxygen with XML output when `api = true`, and writes `bundle.json`,
the archive and its SHA-256.

It stops with the file and line when a published page links to a file that does not exist,
to an absolute path, out of the repository or with a backslash, when a page has no level-one
heading or is not UTF-8, and when a page in a published section is missing from
`docs/README.md`. It copies only the Doxygen XML files `index.xml` names, so a file left in the
output directory by an earlier run does not reach the bundle.

The producer is the sub-package `sushicore.docs_bundle`. A CLI calls
`register_docs_commands` once, which replaces its own `docs` declaration (D9). `--describe`
lists a group that runs bare as a command of its own beside its children, so `docs` stays in
every catalogue. The design is `docs/agent/2026_10_07_DOCS_BUNDLE/SPEC.md` in the SushiCore
repository.

## 5. The site

`sushiweb/apps/docs`. Each unit does one thing and hands the next a typed value.

| Unit | Does | Takes -> gives |
| --- | --- | --- |
| `content.manifest.toml` | Pins repository, version and SHA-256 | edited by pull request |
| `content/fetch` | Downloads a release asset, verifies its SHA-256, caches it | manifest entry -> local archive |
| `content/bundle` | Unpacks an archive and validates `bundle.json` | archive -> `Bundle` |
| `content/pages` | Loads the pages into an Astro collection and rewrites relative links into routes | `Bundle` -> page entries |
| `content/api` | Turns Doxygen XML into a typed model of namespaces, classes, functions and enums | `Bundle` -> symbol entries |
| `content/faq` | Splits an FAQ page into question and answer entries at its level-two headings | page -> FAQ entries |
| `nav` | Builds the sidebar tree from `order` and `section` | `Bundle` -> navigation tree |
| `layouts`, `components` | Page templates for a manual page, a symbol page and the FAQ | entry -> HTML |

The API reference is rendered by the site's own templates from the XML. Doxygen's HTML is not
embedded, because it cannot take the brand's look.

### 5.1 Routes

```
/                                 the stack map: eight parts, what each does, how they connect
/<repository>/                    the repository's landing page
/<repository>/guides/...          getting_started and guides
/<repository>/architecture/...
/<repository>/reference/...
/<repository>/api/...             symbol pages; absent where the bundle has no API
/faq                              every repository's FAQ under its own heading
```

### 5.2 Look and weight

Colour, type and spacing come from `@sushi/brand`'s `tokens.css`, and the header and footer
follow `apps/web`. Three islands run in the browser: the theme toggle, the language switch and
the search box. Every other page ships as HTML and CSS. Code blocks are highlighted at build
time.

### 5.3 Failure

The build stops, and publishes nothing, when a bundle cannot be downloaded, a SHA-256 does not
match, a schema number is unknown, an internal link does not resolve, or two pages claim one
route. The message names the repository, the file and the line.

### 5.4 Tests

Each `content/*` unit is tested in Vitest against small fixture bundles. A Playwright smoke run
over the built site opens every repository's landing page, runs one search, and switches theme
and language. An architecture test, shaped like the one in `packages/brand`, fails when a unit
imports another unit's internals.

## 6. Rollout per repository

| Change | Note |
| --- | --- |
| `docs/publish.toml` | Section 4.3 |
| `GENERATE_XML = YES` in the Doxyfile | sushiruntime, sushiblas, sushiai and sushidsp have a Doxyfile of their own |
| `docs/guides/FAQ.md` | Level-two heading per question. The owner supplies or approves the questions; none is invented |
| Release step | Builds the bundle, attaches it to the release, opens the manifest pull request in sushiweb |

Only sushistack has a release workflow today (`.github/workflows/release.yml`); the other
repositories have `ci.yml` alone. The rollout therefore gives each of them a release workflow,
which the `versioning-and-release` and `continuous-integration` skills govern.

## 7. Out of the first version

- A version selector; each repository shows one version.
- An API reference for the Python packages. sushistack, sushicore and sushitrack have no
  Doxyfile, so they publish manual pages and a FAQ and no symbol pages.
- Automatic links from a symbol name in a guide to its API page.
- Translated content.
- Comments or a feedback form.

## 8. Not verified

- Whether the publishing repositories are public on GitHub. The check on 2026-10-07 timed out.
  If a repository is private, `content/fetch` needs a read token in the Vercel project's
  environment, and the name of that variable is sub-project 2's decision.
- Which credential lets a repository's release step open a pull request in sushiweb, whose
  remote is `sushimg/SushiWeb` and not under the `SushiSystems` organisation.
- That Doxygen is available on the CI runners the release steps will use.

## 9. Acceptance

| Sub-project | Done when |
| --- | --- |
| 1 | `sr docs bundle --release X.Y.Z` in sushiruntime writes an archive whose `bundle.json` carries the fields of section 4.2, and a published page that links to a missing file makes it exit non-zero |
| 2 | `docs.sushisystems.io` serves sushiruntime's guides, API reference and FAQ from a pinned bundle, the Playwright smoke run passes, and a corrupted SHA-256 in the manifest fails the build |
| 3 | All eight repositories appear on the site from bundles their own release steps attached |
