# Documentation style guide

## Placement

Five questions, in order; stop at the first yes:

1. Is it a fact about one component? → that component's `README.md`, beside its code.
2. Was it written by an agent while working? → `docs/agent/` (`specs/`, `plans/`, `reports/`).
3. Is it work with nothing open, a closed chapter? → `docs/archive/`.
4. Is it intent with an open phase, a decision still being worked through? → `docs/design/`.
5. Otherwise → the manual: `docs/getting_started/`, `docs/architecture/`,
   `docs/guides/`, `docs/reference/`, every page reachable from `docs/README.md`.

## Prose

Plain declarative sentences, in English. Put a measurement where an evaluative word wants to go.
Make the component that acts the subject of the sentence. Say a thing once and stop; no closing
summary. Explain a decision's reason when it is not obvious, in the design document, not in the
source.

## Design documents

Every document in `docs/design/` carries a status line as its first line after the heading:
`Status: <one clause>`. `docs/design/REMAINING_WORK.md` is the single backlog; planned-but-not-built
work is recorded there and nowhere else, so what is left can be read from one place.

## Changelog entries

`docs/reference/CHANGELOG.md`, one line per entry, newest first:

```
- 2026-08-28 — Fixed the star field's exposure (`star.vert`, `StarPass`).
```

A date, a past-tense verb, what changed, and where, in backticks. Never more than 240 characters,
never a second sentence, never a nested bullet, never a why. An entry that reads as a paragraph is
a violation, whatever it explains. Not every commit earns an entry; a changelog records a new
capability, a structural shift, or a fixed defect a reader would care about.

## Links and paths

Every link and every cited file path resolves. Check paths after a rename or a move, not only
after adding content.

## Code and identifiers

File paths, commands, identifiers and code blocks are exact and verbatim. A reader copies a
command out of a document and it works.
