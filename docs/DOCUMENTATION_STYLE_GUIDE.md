# Documentation style guide

Prose in this repository follows the `humanizer` skill of SushiSkills. Where a document goes,
the status line of a design document and the shape of a changelog entry follow the
`documentation` skill. Neither is restated here. `tools/documentation/check_docs_layout.py` and
`tools/documentation/check_changelog.py` check both.

## Names

| Write | For |
| --- | --- |
| SushiHub | The tool: this repository, the `sushihub` package, the `hub` command and the desktop application |
| SushiStack | The applications SushiHub installs, and the workspace that holds them |
| `hub` | The terminal command, always in a code span |
| Sushi Account | The identity service at `account.sushisystems.io`; `docs/design/HUB.md` and the archive call it Sushi ID |
| the desktop application | The program under `gui/` |
| component | `cli/`, `gui/` or `contract/` in this repository |
| module | A repository `hub` brings into a workspace; never a folder of this repository |

## Words

English, British spelling in prose: "licence" the noun, "organisation", "catalogue" for what
`hub --describe` prints. Identifiers keep the spelling the code uses: `hub license`,
`cli/sushihub/catalog.toml`, the `licenses` key Sushi Account returns.

"Licence" has two senses here. The licence of this source is PolyForm Noncommercial 1.0.0. The
licence `hub license` reports is the product licence Sushi Account issues for sushiengine. A
sentence that could mean either says which.

## Links and paths

`docs/README.md` reaches every manual and design document through a Markdown link, because
`check_docs_layout.py` follows links and not code spans. Elsewhere a cited path may be a code
span; it still resolves. A path in another repository says which repository.

## Commands

File paths, commands and identifiers are exact. A reader copies a command out of a document and
it works.
