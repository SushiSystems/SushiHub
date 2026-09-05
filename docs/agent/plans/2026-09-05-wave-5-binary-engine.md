# Wave 5: the binary engine, its licence file, and projects — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** `ss add sushiengine` chooses source or binary from what the machine and the account
allow; the binary path resolves a release through Sushi ID, downloads it with progress, verifies
the hash and size, unpacks it into the module's directory and writes the engine's licence token
beside it; `ss update` refreshes a binary install; `ss projects` keeps the registry the desktop
application opens projects from.

**Architecture:** Three new service bricks, each one responsibility: `services/releases.py`
(resolve, download, verify, unpack), `services/licence_file.py` (fetch and write the licence
token), `services/projects.py` (the registry). `SushiId` gains the two calls the endpoints need.
`modules.add` gains one decision, `_source_reachable`, and delegates the binary path whole.
The fake Sushi ID in the tests grows the two endpoints so every path runs end to end without a
network.

**Tech Stack:** Python 3.10+, `urllib`, `zipfile`, `tarfile`, `hashlib`, pytest.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §3, §5, §6; the endpoint shapes in
`D:\Projects\sushiweb-hub\docs\agent\specs\2026-09-05-device-grant-and-releases-design.md` §5, §6.

## Global Constraints

- Touch only `sushihub/cli/**`, `sushihub/contract/sushi-id.md`, `sushihub/contract/README.md`.
  Not `sushicore/`, not `sushihub/gui/`. Do not edit `docs/reference/CHANGELOG.md` or
  `docs/design/REMAINING_WORK.md`; report the lines.
- No network beyond `127.0.0.1` in tests; no `git clone` of a real repository (stub `_run_git`
  and `_source_reachable`); no `ss install`.
- Docstrings as `docs/CONTRIBUTING.md` sets. Commit per task, stage by path.

## The two endpoints, verbatim into `sushihub/contract/sushi-id.md`

| Method and path | Request | Response |
|---|---|---|
| `POST /api/licenses/token` (Bearer) | `{"product"}` | `200 {"licence_token", "expires_at"}`; `403 {"error": "no_licence"}`; `404 {"error": "unknown_product"}` |
| `POST /api/releases/resolve` (Bearer) | `{"product", "platform", "version"?}` | `200 {"version", "platform", "url", "sha256", "size", "expires_at"}`; `403 no_licence`; `404 unknown_product` or `no_release`; `429` |

Platform strings: `windows-x64`, `linux-x64`, derived from `platform.system()` and
`platform.machine()` in one function, `services/releases.py::host_platform()`.

## Files

| File | Responsibility |
|---|---|
| `services/identity.py` | `SushiId.licence_token(product) -> LicenceToken`; `SushiId.resolve_release(product, platform, version=None) -> ReleaseInfo`; `NoLicence`, `NoRelease`, `UnknownProduct` errors. |
| `services/releases.py` (new) | `host_platform()`, `download(url, dest, *, on_progress, http)`, `verify(path, sha256, size)`, `unpack(archive, into)`, `install_release(name, root, client, console, *, http)`: the whole binary path, returning the `Release` read back from `sushi-release.json`. |
| `services/licence_file.py` (new) | `LICENCE_FILE = "sushi-licence.jwt"`; `write_licence(root, client, product)`; `read_licence_expiry(root)`. |
| `services/projects.py` (new) | `PROJECTS_FILE = "projects.local.toml"`; `Project(name, path)`; `list_projects()`, `add_project(path, name=None)`, `remove_project(name)`; the file lives beside `modules.local.toml`. |
| `services/modules.py` | `_source_reachable(repo) -> bool` (`git ls-remote --exit-code -h <repo> HEAD`, 15 s timeout); `add(..., binary=False)`: per module, source when reachable and not `binary`, else the binary path when the module is `sushiengine`, else the two-hint error; `update`: a binary module resolves the latest release and reinstalls when the version differs. |
| `cli.py` | `ss add --binary`; `ss projects list|add <path> [--name]|remove <name>`. |
| `tests/test_identity.py` | The fake server gains the two routes; `resolve_release`'s `url` points at the fake server's own `/download/<name>` serving a zip built in the test. |
| `tests/test_releases.py`, `tests/test_projects.py`, `tests/test_add_binary.py` (new) | Download with progress; hash mismatch refused; unpack zip and tar.gz; `install_release` end to end against the fake; the registry; `add` choosing source, binary, or refusing. |
| `cli/README.md` | `--binary`, `ss projects`, the licence file. |

---

### Task 1: The contract page and the client calls

Modify `sushihub/contract/sushi-id.md` (the table above and one paragraph on the licence file: what
`ss` writes, where, and that the engine verifies it against the JWKS), `services/identity.py`,
`tests/test_identity.py` (fake routes plus five tests: token issued; `no_licence`; release resolved;
`no_release`; `unknown_product`).

```python
@dataclass(frozen=True) class LicenceToken: token: str; expires_at: str
@dataclass(frozen=True) class ReleaseInfo: version: str; platform: str; url: str; sha256: str; size: int; expires_at: str
class NoLicence(Exception); class NoRelease(Exception); class UnknownProduct(Exception)
```
Commit: `feat(cli): ask Sushi ID for a licence token and a release`.

### Task 2: Download, verify, unpack

`services/releases.py` and `tests/test_releases.py`. `download` streams in 1 MiB chunks and calls
`on_progress(done_bytes, total_bytes)`; `verify` raises `ReleaseCorrupt` naming which of the two
mismatched; `unpack` handles `.zip` and `.tar.gz`, refuses a member whose path escapes `into`
(zip slip), and requires `sushi-release.json` at the top level of the result.
`install_release` orders them, emits `console.progress("download", ...)` events with a fraction,
unpacks into a temporary sibling directory and renames it over `root` last so a failed download
never leaves a half-installed module.

Commit: `feat(cli): download, verify and unpack a release without leaving a half-installed module`.

### Task 3: The licence file and the decision in `add` and `update`

`services/licence_file.py`, `modules.py`, `cli.py` (`--binary`), `tests/test_add_binary.py`.
`add` for `sushiengine`: `binary` flag or `_source_reachable` false → needs `client.access_token()`;
none → error listing both hints (`ss login`, or a Git identity with access) and return 1; else
`install_release` then `write_licence`. A binary install runs no `_install_module_cli` (wave 6's).
`update`: binary module → `resolve_release` latest; equal version → info; newer → `install_release`
and `write_licence` again. The provision step is not run for a binary module.

Commit: `feat(cli): install sushiengine as a binary with its licence when the source is out of reach`.

### Task 4: Projects

`services/projects.py`, `cli.py`, `tests/test_projects.py`. `list` prints a table
`Name | Path | Exists`; `add` refuses a path that is not a directory and derives the name from the
directory unless `--name`; `remove` by name. `status_payload` unchanged; the desktop application
runs `ss --json projects list` and opens `se editor --project <path>`.

Commit: `feat(cli): keep the project registry the desktop application opens from`.

### Task 5: Documentation

`cli/README.md`: `ss add [--binary]`, `ss projects` rows, a "Binary installs" section (the marker,
the licence file, how `update` behaves). `sushihub/contract/README.md` links the two new rows.

Commit: `docs(cli): describe binary installs, the licence file and projects`.

## Report

`python -m pytest sushihub/cli/tests -q`, `python -m compileall -q sushihub/cli/sushistack`,
`git log --oneline -6`, deviations, and:
`- 2026-09-05 — Added the binary path of `ss add sushiengine`, the licence file, and `ss projects` (`sushihub/cli/sushistack/services/releases.py`, `licence_file.py`, `projects.py`).`
