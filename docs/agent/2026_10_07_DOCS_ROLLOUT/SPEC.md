# Documentation rollout

**Status:** Open — designed 2026-10-07; the FAQ pages of seven repositories are written.

Sub-project 3 of the documentation site programme, whose design is
`docs/agent/2026_10_07_DOCS_SITE/SPEC.md`. Sub-project 1 built the bundle producer in SushiCore
and proved it on SushiRuntime; sub-project 2 built the site in the sushiweb repository. This one
makes the other repositories publish and gives the site a way to follow their releases.

## 1. Owner decisions, 2026-10-07

| # | Decision |
| --- | --- |
| R1 | The order is the FAQ pages, then the release workflows, then sushiengine |
| R2 | The site pulls. One workflow in sushiweb looks at each repository's latest release and opens a pull request that changes `content.manifest.json`. This replaces the sentence of the programme design that had each repository open that pull request |
| R3 | A repository's `release.yml` calls its `ci.yml` as a reusable workflow, and packages only when that is green |
| R4 | sushiengine's FAQ page waits. The manual describes only the checkout-and-build path, and an outside reader gets a binary; the page is written after the manual has an install page for the binary |

## 2. What was found

- On GitHub only SushiHub and SushiCore are public. SushiRuntime, SushiEngine, SushiAI,
  SushiBLAS, SushiDSP and SushiTrack are private, and so is sushiweb.
- A private repository's `publish.toml` therefore carries no `source_url`: a link out of its
  bundle becomes text, since a link to a private file would answer 404. It gains the key when
  the repository opens.
- The site fetches a private repository's bundle with `SUSHI_DOCS_TOKEN`, from the release
  asset's API address, `https://api.github.com/repos/<owner>/<repo>/releases/assets/<id>`. The
  download address of a private asset does not take a bearer token.
- Of the eight repositories only SushiHub and SushiCore have a `release.yml`. SushiRuntime has
  one release, `v0.3.0`; the others have none.
- A bundle's release is the repository's version in its source of truth: `project(VERSION)` for
  the C++ repositories, `version` in `pyproject.toml` for SushiHub and SushiCore. The first
  sample bundle was named after SushiRuntime's CLI package by mistake and was rebuilt as 0.3.0.

## 3. Per repository

| Repository | CLI | API reference | `source_url` |
| --- | --- | --- | --- |
| sushistack (SushiHub) | `hub docs bundle` | none | set |
| sushicore | `python -m sushicore.docs_bundle` | none | set |
| sushiruntime | `sr docs`, `sr docs bundle` | Doxygen | absent |
| sushiblas | `sb docs`, `sb docs bundle` | Doxygen | absent |
| sushiai | `sa docs`, `sa docs bundle` | Doxygen | absent |
| sushidsp | `sd docs`, `sd docs bundle` | Doxygen | absent |
| sushitrack | `st docs bundle` | none | absent |
| sushiengine | `se docs`, `se docs bundle` | none published | absent |

Each gets `docs/publish.toml`, `publish.toml` in `K_DOCS_ENTRIES` of its layout checker, the
`docs` group registered from `sushicore.docs_bundle`, and, where it has a Doxyfile and publishes
its API, `GENERATE_XML = YES`. The excluded pages are the ones that are not manual content: the
Doxygen main page, the code of conduct and the security policy.

## 4. The release workflow

`release.yml`, on a pushed tag `v*`:

1. `ci`: the repository's `ci.yml`, called through `workflow_call`.
2. `bundle`, after `ci`: check that the tag is `v` plus the version in the source of truth;
   install the CLI and Doxygen; run `<cli> docs bundle --release <version>`; create the release
   if the tag has none, and attach `docs-bundle-<version>.tar.gz` and its `.sha256`.

The job needs a published SushiCore that carries `docs_bundle`, which does not exist yet. Until
the owner releases it the workflow fails at the install step, by design: a CLI that imports the
module cannot be installed without it.

## 5. The manifest workflow

In sushiweb, `.github/workflows/docs-manifest.yml`, run by hand and on a schedule:

1. For each entry of `content.manifest.json` whose `source` is a release asset, and for each
   repository listed in `apps/docs/publishers.json`, read the latest release.
2. When it carries a bundle of a newer version, write the entry: version, the asset's API
   address, and the SHA-256 read from the attached `.sha256` file.
3. Open one pull request with the change. A person merges it; Vercel deploys.

The step is a Node script with its own tests, `apps/docs/tools/sync_manifest.mjs`. It reads with
`SUSHI_DOCS_TOKEN`, a token that can read the publishing repositories, and opens the pull
request with the workflow's own token.

## 6. Not verified, and cannot be here

No workflow in this sub-project has run. GitHub Actions cannot be run on this machine, so each
file is checked for syntax and read against the forge's documentation, and its first real run
is the owner's first tag.

## 7. Acceptance

Each of the seven open repositories builds its bundle locally with its own command, and the
site compiles from those seven bundles as files. The workflows exist and are syntactically
valid. sushiengine follows in its own step.
