# Renaming the repository to SushiHub

**Status:** done 2026-09-22. All four tasks landed; CI is green on `main` and the remote is
`SushiSystems/SushiHub`. The checkout on disk keeps its old name on purpose: every sibling
module's `config.local.toml` stores absolute paths into `D:/Projects/sushistack/dependencies`,
and ten of them were checked to still resolve after the move. Publishing `sushihub` 0.2.0 to
PyPI is the one step left, and it is a release, not part of this plan.

**Goal:** the tool is called `sushihub` at every layer that names the tool, and
`sushistack` survives only where it names the stack of applications.

**Why:** the owner fixed the distinction on 2026-09-22. `sushistack` is the
applications; `sushihub` is the application that acquires and manages them. This
repository holds no module, only the tool, so it carries the wrong name. In prose
the tool is written `SushiHub`.

## The rule, applied

Every layer was decided by the rule rather than by taste. Two of them keep the old
name, and that is the point of writing the rule down first.

| Layer | Names | Becomes |
| --- | --- | --- |
| Repository | the tool | `SushiSystems/SushiHub` |
| `sushihub/` top folder | nothing — a folder inside itself | dissolves into the root |
| Python import package | the tool | `sushihub` |
| PyPI distribution | the tool | `sushihub`, already |
| Commands | the tool | `hub`, `sushihub`, already |
| `.sushistack/workspace.toml` | a stack on disk | unchanged |
| `SUSHISTACK_HOME` | a stack on disk | unchanged |
| `sushistack.deps.toml` | a format the stack shares | unchanged |
| `catalog.toml`, design prose | the applications | unchanged |

`sushistack.deps.toml` is the one worth restating: `sushidsp` carries that file and
`sushidsp` is not the hub. Renaming it would have been the natural mistake.

## Target layout

Siblings that do the same kind of thing are shaped the same. `sushitrack` and
`sushidsp` keep their CLI at `cli/`, so this repository does too.

```
cli/            was sushihub/cli/
  sushihub/     was sushihub/cli/sushistack/
  tests/
  pyproject.toml
gui/            was sushihub/gui/
contract/       was sushihub/contract/
docs/  tools/  .github/  install.sh  install.ps1  README.md  LICENSE
```

## What the measurement found

Taken 2026-09-22, before any change.

| Where | Mentions | Kind |
| --- | --- | --- |
| `dependencies/` | ~4900 | absolute paths inside provisioned trees; regenerated, never edited |
| `sushihub/gui` | 170 | absolute paths inside generated build trees; no symbol in any source file |
| `sushihub/cli` | 214 | 132 import lines in 37 files, ~70 path citations, 6 dead strings, the rest keeps its name |
| `docs/` | ~45 | mostly the umbrella, which stays |

Tracked files under `sushihub/`: 173. `dependencies/` is not tracked.

The dead strings are `sushistack-cli` and `sushistack-installer`, names of things
that no longer exist. They are deleted rather than renamed.

## Order

Strictly sequential: each task's acceptance depends on the one before it, so there
are no independent waves here. Inline execution.

### Task 0: clear the tree

The shared working tree holds another session's uncommitted work on `hub doctor`
and `hub help`, including two of the files this rename moves. `git mv` over a
modified file destroys that work and it cannot be recovered.

**Acceptance:** `git status --porcelain` lists nothing but this task's own files.

### Task 1: rename the Python package

`git mv sushihub/cli/sushistack sushihub/cli/sushihub`, then rewrite the 132 import
lines, the path citations in docstrings and comments, and `pyproject.toml`'s entry
points, `packages.find` and `package-data`. Delete the dead strings. Leave every
name in the table above that the rule keeps.

`git mv` first and in its own operation, so git records renames and the file
history survives.

**Acceptance:** the CLI's suite passes and `hub --describe` answers, both from a
checkout and from a wheel built out of it.

### Task 2: dissolve the top folder

`git mv sushihub/cli cli`, then `gui`, then `contract`. Update `.github/workflows/ci.yml`
(two lines), `.github/workflows/release.yml` (four lines), the install scripts and
the paths cited in the manual.

**Acceptance:** CI is green on a pushed branch. Not "tests pass locally" — the
workflows are what this task changes.

### Task 3: prose and brand

`SushiHub` where the tool is meant, `SushiStack` where the applications are meant,
across `README.md`, `docs/` and the module READMEs. The changelog gains its line and
`docs/design/WORKSPACE_DECOUPLING.md` its status update.

**Acceptance:** every link and cited path in the manual resolves.

### Task 4: rename the remote

Rename the repository on GitHub and update `origin`. GitHub redirects the old URL,
and nothing in this repository or in `catalog.toml` clones it by name, so the blast
radius is a stale URL in someone's shell history.

**Acceptance:** `git push` reaches `SushiSystems/SushiHub` without a redirect notice.

## Release

The entry point moves from `sushistack.cli:app` to `sushihub.cli:app` and the import
package changes underneath a distribution that keeps its name. A workspace installed
from PyPI cannot upgrade across that; `install.ps1` and `install.sh` already uninstall
an existing venv before installing, which is what makes the upgrade path work.

This is a breaking release, and below 1.0 that is a minor bump: `sushihub` 0.2.0. Calling it
1.0.0 would declare the public interface settled, which is the owner's call and not a
consequence of breaking something.

## Open

Whether the checkout at `D:/Projects/sushistack` is also renamed on disk. It is not
required by anything above, and it is not free: every provisioned tree under
`dependencies/` and every CMake cache under `gui/build/` stores absolute paths, so
renaming the directory forces a re-provision and a fresh configure. The owner decides.
