# Backlog migration: inventory

**Status:** Shipped — 2026-10-19. The owner approved the inventory as proposed.

The migration of this repository to the backlog format of SushiSkills'
`skills/documentation/BACKLOG_FORMAT.md`, step 2 of section 8 of SushiSkills'
`docs/agent/2026_10_19_BACKLOG_FORMAT/SPEC.md`. This repository coordinates the others, so the
programmes that span repositories live here (decision D2 of that spec).

## Shared tools

As in sushiweb, this repository carries the older shared tools on `tools/common/`; the migration
took only the `tools/checking/` frame, `check_backlog.py`, `design_status.py` and the current
`check_docs_layout.py`, with their tests. Taking the whole set is `RW-42`.

## Fact check

| Entry | Verdict |
| --- | --- |
| A checkout cannot install `hub`: `sushicore` 0.7.0 is unpublished | Closed: PyPI serves 0.7.0 to 0.9.2, and the package requires 0.9.1 |
| `hub migrate` needs `sushicore` 0.8.0, unpublished | Closed: published; the owner's real run is `sushicore RW-9` |
| Standalone wave 4: tag and publish `sushicore` 0.7.0 | Closed; the owner's runs are `sushicore RW-8` |
| Documentation site item 1: SushiCore's release with `docs_bundle` | Closed: released in 0.8.1 |
| `check_docs_layout.py` reports `docs/CLAUDE.md` | Closed: the file is gone |
| `HUB.md` still says Sushi ID and `sushihub/cli/` | Not a defect: the design states that its body keeps the names of its date |
| Local branches `feature/hub_help_and_doctor` and `feature/theme_tokens` | Closed: both are gone. `pre-clean-main` exists and is the owner's |
| Paths inside the archived plans and reports | The archive is frozen; deleted |
| Every landed wave of the four programme tables | Finished work; deleted. The design documents and the changelog keep them |

Every other entry was read against the code and stands.

## Entries moved between repositories

| Entry | From | To |
| --- | --- | --- |
| The estate programmes | sushiskills `RW-15` | `RW-18` here |
| The backlog migration of every repository | sushiskills `RW-14` | `RW-19` here |
| Settle panel names, short options and defaults across the command lines | sushiblas `RW-81` | `RW-17` here; `RW-81` there goes when SushiBLAS's current work is done |
| The six command lines adopt `help_group`; each registers `docs` | sushicore's backlog before its migration | `RW-17` and `RW-16` here |
| The consumer contract has no home | here | `sushicore RW-50` |
| `use_vcpkg` is never read | here | `sushicore RW-51`; `RW-24` here waits on it |
| A `[cli]` theme in `workspace.toml` is not read | here | `sushicore RW-52`; `RW-25` here waits on it |
| A doubled progress line | here | `sushicore RW-53` |
| Every GPU vendor on a machine | here | `sushicore RW-54` |
| `sushiruntime`'s `env.py` repeats `sushicore.build_env` | here | `sushiruntime RW-64` |
| R1 of the GPU backend provisioning plan | here | `sushiruntime RW-63`; `RW-32` here waits on it |
| The site's bundles become addresses | sushiweb `RW-15` | now blocked by `RW-16` here |

The engine's side of the hub (wave 6, `RW-11`) and E1 of the GPU plan get their entries when
sushiengine migrates.

## Shape

The backlog holds `RW-1` to `RW-54` less `RW-20`, `RW-27` and `RW-29`, ten of them decisions;
the known issues hold `KI-1` to `KI-20`. The open defects table became `KI-1` to `KI-16`, and the
four toolchain stories `KI-17` to `KI-20`.

## Status lines

Four work folder files took the four forms; all four shipped.

## Outcome

The owner approved the inventory on 2026-10-19. `check_docs_layout.py`, `check_backlog.py`,
`check_changelog.py` and the tool tests pass.
