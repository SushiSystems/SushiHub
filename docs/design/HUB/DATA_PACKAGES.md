# Data packages

**Status:** Shipped — 2026-11-10

A module's tests and tools need large reference files that do not belong in git: sushiengine's
DE440 ephemeris, the EGM2008 gravity coefficients and full-resolution GRIB2 analyses. Today each
module fetches them its own way or not at all, and the tests that need them skip. The owner ruled
on 2026-11-10 that this data comes from the hub. A data package is a file `hub install` downloads
from its official source, checks against a pinned SHA-256 and places where the module reads it.

## Decision

| Question | Decision |
| --- | --- |
| Who declares a package | The module, in the dependency fragment it already owns (`cli/sushistack.deps.toml`), one `[data.<name>]` table per file |
| Where the bytes come from | The publisher's own URL (JPL, GeographicLib, NOAA). The hub hosts nothing and mirrors nothing |
| What proves a file | Its SHA-256 and its byte count, pinned in the table. A mismatch deletes the download and fails that package |
| Where a file lands | Once per machine in the shared store `dependencies/data/<sha256>/<file name>`, then copied to the module-relative `destination` |
| Who cooks it | The module. The hub never runs a module command: a raw file the module must convert is cooked by the module's own CLI, which reads the placed file |
| Required or optional | Optional by default. A missing optional package warns, and the tests that need it skip with the command that installs it |
| How a request is made | A plain `GET` with the hub's own client name. A source that refuses automated clients is not a data package source |
| Licence | The table carries the publisher's licence or terms in one line; a table without one is refused |

## Design

### The table

```toml
[data.de440_ascii_1950]
description = "JPL DE440 ephemeris, ASCII block from 1950; sushiengine cooks it into assets/astro."
url         = "https://ssd.jpl.nasa.gov/ftp/eph/planets/ascii/de440/ascp01950.440"
sha256      = "<64 hex digits>"
bytes       = 0
licence     = "JPL ephemerides: public, no restriction stated"
destination = "assets/astro/raw/ascp01950.440"
required    = false
```

`url`, `sha256`, `bytes`, `licence` and `destination` are required. `destination` is relative to
the module's checkout, must stay inside it, and the module's `.gitignore` covers it. An archive
is placed as downloaded; unpacking, like cooking, is the module's job.

### `hub install`

After the toolchains, `hub install` walks every present module's `[data.*]` tables in fragment
order:

1. If `dependencies/data/<sha256>/<file name>` exists with the pinned size and hash, use it.
2. Otherwise download to a temporary file in the same store, streaming, with progress events in the
   `download` label `releases.py` already uses; hash while writing; check size and hash; rename
   into place. A mismatch deletes the temporary file and reports the expected and found hashes.
3. Copy the stored file to `destination` when the copy there is missing or differs in size or hash.

`hub install --no-data` skips the walk. `hub doctor` reports each package as present, missing or
corrupt, with its owner, in the same report shape as a toolchain.

### Failures and validation

A failed optional package is a warning of the install; a failed required one fails the step. One
failed package does not stop the next. `sha256` is 64 hex digits, `bytes` an integer of zero or
more, `required` a boolean, and `url` an http or https address whose file name uses only letters,
digits and `. _ + % ~ -`. `hub doctor` judges a package by the copy at its `destination` and
reports `OK`, `MISSING` or `CORRUPT`. `--dry-run` lists what would be fetched and sends nothing.
A binary install has no checkout to place into, so the step skips it.

sushicore's fragment merge reads a `data` key as a dependency of that name and ignores the tables
below it, so the hub reads `[data.*]` itself and drops that entry from the dependency list.

### What the module does

The module names the cooking command in its install documentation and in every skip message
(`se bake ephemeris`, for example). A cooked output is a build product of the module, not a
package: it is never declared, and it is rebuilt from the placed raw file.

### What it does not do

No mirror, no account, no licence check beyond the declared line, no partial-range download, no
version resolution. Changing a file means changing its URL and hash in the fragment, reviewed like
any dependency change.

## Phases

| Id | Phase | Waits on |
| --- | --- | --- |
| W8 | `[data.*]` tables read from the fragments; the store; download, verify, place; `--no-data`; `hub doctor` rows; tests against a local HTTP server | nothing |
