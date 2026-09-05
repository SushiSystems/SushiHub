# Wave 2: binary presence and Sushi ID sign-in — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** A module can be present as a downloaded binary and every `ss` command and every module
CLI knows it; `ss login`, `ss logout`, `ss whoami` and `ss license` work against a Sushi ID whose
four endpoints are written down here and faked in tests.

**Architecture:** Presence is read from disk, never recorded: a directory under the workspace root
holding `sushi-release.json` is a binary install; one holding `.git` is a clone; a path in
`modules.local.toml` is a link. `sushicore.ModuleProfile` learns the release manifest's name so a
module CLI finds its root through either marker and can ask which one it found. In `ss`, one module
`services/presence.py` answers "how is this module present" and everything that used to test
`.git` asks it instead. Identity is a client class over four HTTP endpoints, a token store behind a
protocol (`keyring` in production, memory in tests), and four thin commands.

**Tech Stack:** Python 3.10+, `keyring` (new runtime dependency of `sushistack-cli`), `urllib`
(no `requests`), `http.server` in tests.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §3, §5, §6.

## Global Constraints

- Waits on wave 1a-cli.
- Two file sets, two tasks groups that can run in parallel: **2a** touches `sushicore/**` only;
  **2b** and **2c** touch `cli/**` and `sushihub/contract/**` only. 2b waits on nothing in 2a at
  run time (`ss` reads the manifest file name from its own constant, tested equal to sushicore's).
- No network in tests. No `ss install`, no downloads.
- Docstrings as `docs/CONTRIBUTING.md` sets. Commit per task, stage by path.
- Do not edit `docs/reference/CHANGELOG.md` or `docs/design/REMAINING_WORK.md`.

## The release manifest

`<module root>/sushi-release.json`, written by the release build in the module's repository and
read by `ss` and by the module's own CLI:

```json
{"product": "sushiengine", "version": "1.4.2", "platform": "windows-x64",
 "bundled": {"sushiruntime": "0.9.0", "sushiblas": "0.4.1"},
 "signature": "base64…"}
```

`ss` reads `product`, `version`, `platform`. The module CLI reads nothing but the file's presence.
Verification of `signature` is wave 5's.

## Sushi ID endpoints (the target for sushiweb)

Written to `sushihub/contract/sushi-id.md` in Task 2c-1, verbatim:

| Method and path | Request | Response |
|---|---|---|
| `POST /api/device/code` | `{"client_id": "ss"}` | `{"device_code", "user_code", "verification_uri", "expires_in", "interval"}` |
| `POST /api/device/token` | `{"client_id": "ss", "device_code"}` | `200 {"access_token", "refresh_token", "expires_in"}` or `400 {"error": "authorization_pending" | "slow_down" | "expired_token" | "access_denied"}` |
| `POST /api/token/refresh` | `{"refresh_token"}` | `200 {"access_token", "expires_in"}` or `401` |
| `GET /api/me` (Bearer) | | `{"account_id", "email", "licenses": [{"product", "holder": "account" | "org", "expires_at": iso-8601 or null}]}` |

Base URL from `cli/config.toml` `[identity] url = "https://id.sushisystems.io"`, overridden by
`SUSHI_ID_URL`.

---

## 2a — sushicore

### Task 2a-1: `ModuleProfile` knows the release manifest

**Files:** modify `sushicore/sushicore/profile.py`, `sushicore/sushicore/module_config.py`;
test `sushicore/tests/test_profile.py`, `sushicore/tests/test_module_config.py` (new).

**Interfaces:**
```python
RELEASE_MANIFEST = "sushi-release.json"          # sushicore.profile, module constant
class ModuleProfile:
    release_manifest: str = RELEASE_MANIFEST     # new field
    def markers(self) -> tuple[str, ...]         # (root_marker, release_manifest)
    def presence(self, root: Path) -> str        # "binary" if root/release_manifest is a file, else "source"
class ModuleConfig:
    def find_project_root(self, start=None) -> Path   # walks up to ANY marker in profile.markers()
    def presence(self, root: Path | None = None) -> str
```
`not_a_project_message` names both markers.

Tests: a tmp tree with only `sushi-release.json` is found and reports `binary`; one with only
`CMakeLists.txt` reports `source`; one with neither raises `SystemExit` whose message names both.

Commit: `feat(sushicore): let a module CLI find a binary install and say which kind it found`.

---

## 2b — presence in `ss`

### Task 2b-1: `services/presence.py`

**Files:** create `cli/sushistack/services/presence.py`; test `cli/tests/test_presence.py`.

**Interfaces:**
```python
class Presence(str, Enum): CLONED="cloned"; LINKED="linked"; BINARY="binary"; ABSENT="absent"
RELEASE_MANIFEST = "sushi-release.json"
@dataclass(frozen=True)
class Release: product: str; version: str; platform: str
def read_release(root: Path) -> Release | None        # None when the file is missing or malformed
def presence_of(root: Path, name: str, linked: Mapping[str, str]) -> Presence
    # linked path with .git -> LINKED; linked path without -> ABSENT (the caller says "linked (missing)")
    # <root>/<dir>/sushi-release.json -> BINARY; <root>/<dir>/.git -> CLONED; else ABSENT
def describe(root: Path, name: str, linked) -> tuple[str, str]   # (location, state) as status shows them
    # BINARY -> ("sushiengine", "binary 1.4.2"); CLONED -> (dir, "cloned"); LINKED -> (path, "linked"); ABSENT -> (dir, "absent")
```
A test in `cli/tests/test_presence.py` asserts `RELEASE_MANIFEST == sushicore.profile.RELEASE_MANIFEST`
so the two constants cannot drift (import sushicore in the test only).

Commit: `feat(cli): answer how a module is present from what is on disk`.

### Task 2b-2: Every `.git` test asks `presence_of`

**Files:** modify `cli/sushistack/services/modules.py` (`_status_rows`, `add`, `update`),
`cli/sushistack/setup/steps.py` (`_report_readiness`), `cli/sushistack/setup/dependency_source.py`
(`manifest_sources`: a binary module contributes no fragment even if one lies in its tree);
test additions in `cli/tests/test_presence.py` and `cli/tests/test_add_provisions.py`.

Behaviour: `ss update` skips a binary module with `info("sushiengine: binary 1.4.2; updates come
through `ss add sushiengine`.")`. `ss add` on a module already present as binary says so and does
not clone. Readiness prints `sushiengine: binary 1.4.2, nothing to build` for a binary module.
`status`'s payload rows gain `"presence"` (the enum value) and `"version"` (or null).

Commit: `feat(cli): treat a binary install as present everywhere ss looks`.

---

## 2c — identity

### Task 2c-1: The contract page and the config key

**Files:** create `sushihub/contract/sushi-id.md` (the table above plus the device-grant walk:
code, browser, poll at `interval`, store); modify `cli/config.toml` (`[identity] url`),
`cli/sushistack/config.py` (`identity_url() -> str`: env `SUSHI_ID_URL`, else the config key,
else the default), `sushihub/contract/README.md` (link the page), `docs/README.md` (link it).
Test: `cli/tests/test_identity.py::test_identity_url_prefers_env`.

Commit: `feat(contract): write down the four Sushi ID endpoints ss needs`.

### Task 2c-2: Token store

**Files:** create `cli/sushistack/services/token_store.py`; test in `cli/tests/test_identity.py`.
Modify `cli/pyproject.toml`: add `"keyring>=24"` to `dependencies`.

**Interfaces:**
```python
class TokenStore(Protocol):
    def load(self) -> Tokens | None
    def save(self, tokens: Tokens) -> None
    def clear(self) -> None
@dataclass(frozen=True) class Tokens: access_token: str; refresh_token: str; expires_at: float  # epoch seconds
class KeyringStore(TokenStore)   # service "sushistack", username "sushi-id"; value is JSON of Tokens
class MemoryStore(TokenStore)
```
`KeyringStore` is tested with `keyring.set_keyring(keyring.backends.null.Keyring())`? No: with a
tiny in-memory `keyring.backend.KeyringBackend` subclass set for the test, so the JSON round trip
through keyring's API is exercised without touching the OS store.

Commit: `feat(cli): store Sushi ID tokens behind one protocol, keyring in production`.

### Task 2c-3: The client

**Files:** create `cli/sushistack/services/identity.py`; test `cli/tests/test_identity.py`
with a fake server (`http.server.ThreadingHTTPServer` on `127.0.0.1:0`, one handler class
implementing the four routes with an in-memory state: pending until the test "approves").

**Interfaces:**
```python
class SushiId:
    def __init__(self, base_url: str, store: TokenStore, *, http=urllib.request.urlopen, sleep=time.sleep, now=time.time)
    def start_device_login(self) -> DeviceCode          # POST /api/device/code
    def wait_for_token(self, code: DeviceCode) -> Tokens # polls /api/device/token honouring interval and slow_down; raises LoginDenied / LoginExpired
    def access_token(self) -> str | None                 # from store; refreshes when expires_at <= now + 30
    def me(self) -> Account | None                       # GET /api/me; None when not signed in
    def logout(self) -> None
@dataclass(frozen=True) class DeviceCode: device_code: str; user_code: str; verification_uri: str; expires_in: int; interval: int
@dataclass(frozen=True) class Licence: product: str; holder: str; expires_at: str | None
@dataclass(frozen=True) class Account: account_id: str; email: str; licenses: tuple[Licence, ...]
```
Tests: pending → approved → tokens saved; `slow_down` doubles the interval once; `access_denied`
raises; a refresh happens when the access token is within 30 s of expiry; `me()` returns None
with an empty store.

Commit: `feat(cli): speak the device grant to Sushi ID and keep the session fresh`.

### Task 2c-4: The four commands

**Files:** modify `cli/sushistack/cli.py` (four commands), create
`cli/sushistack/services/session.py` (`login(open_browser=webbrowser.open) -> int`,
`logout() -> int`, `whoami() -> int`, `license() -> int`, each building `SushiId(identity_url(),
KeyringStore())` through one `_client()` factory that tests monkeypatch); tests in
`cli/tests/test_json_streams.py` (the four under `--json` against the fake server, with
`MemoryStore`) and `cli/tests/test_identity.py`.

Behaviour: `login` prints the code and URI through `console.info`, opens the browser, emits
`progress` events while polling (label `login`, index = polls so far, count 0 → the schema allows
`count` ≥ 0; if not, use `fraction: null` and `count: 1`), ends with `result` payload
`{"email": ...}`. `whoami` prints a table `Field | Value` and the account as payload. `license`
prints a table `Product | Holder | Expires` and the list as payload; empty prints `info("No
licences on this account.")`. `logout` clears the store. All four end with `_finish`.

`cli/README.md`: four rows in the command table, and a "Signing in" section.

Commit: `feat(cli): add ss login, logout, whoami and license`.

## Report

Paste `python -m pytest cli/tests -q`, `python -m pytest sushicore/tests -q`,
`python -m compileall -q cli/sushistack sushicore/sushicore`, `git log --oneline -8`, and:

- CHANGELOG: `- 2026-09-05 — Added binary presence, read from `sushi-release.json`, to `ss` and to `ModuleProfile` (`cli/sushistack/services/presence.py`, `sushicore/sushicore/profile.py`).`
- CHANGELOG: `- 2026-09-05 — Added `ss login`, `ss logout`, `ss whoami` and `ss license` over the device grant (`cli/sushistack/services/identity.py`, `cli/sushistack/services/session.py`, `sushihub/contract/sushi-id.md`).`
- REMAINING_WORK: wave 2 landed.
