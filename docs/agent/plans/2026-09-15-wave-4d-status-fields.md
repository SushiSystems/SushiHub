# Wave 4d: what `hub status` knows about an install — Plan

**Goal:** `hub status` reports what the Installs card draws: a checkout's branch and how far it
is from its upstream, a binary's platform and licence expiry, and how `hub` itself is installed.
`hub status --check-updates` goes online and adds whether something newer exists.

**Architecture:** Each fact comes from one reader brick that looks at disk and nothing else:
git state, the release manifest, the licence file, the shell alias. `status_payload` composes
them. The online step is a separate brick the flag switches on, so plain `hub status` stays
offline and fast. The desktop application reads the new fields and runs the online check once in
the background after the offline status has drawn.

**Tech Stack:** Python 3.10+, Typer, git, C++17 and Dear ImGui.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §5, §8; wave 4c's Installs card
(`docs/agent/plans/2026-09-07-wave-4c-hub-ui.md`, Task 3).

## Decisions taken with the user (2026-09-15)

- Plain `hub status` never touches the network. `--check-updates` does: `git fetch` for every
  checkout and for the workspace, `/api/releases/resolve` for every binary install.
- `ahead` and `behind` count against the last fetch. `last_fetch` sits beside them so a reader
  can say how old the numbers are.

## Global Constraints

- The payload only grows. No existing key is renamed, removed or retyped.
- A fact that cannot be read is `null`, never a guessed value and never an omitted key.
- No reader writes anything. Only `--check-updates` fetches, and it fetches without merging.
- No agent runs `se`, `cmake`, `ninja` or `ctest`, or edits a build configuration file.

## The payload

```json
{
  "workspace": "D:\\Projects\\sushistack",
  "checked_updates": false,
  "hub": {
    "command": "hub",
    "alias": {"name": "sh", "defined_in": "C:\\Users\\sushi\\Documents\\PowerShell\\profile.ps1"},
    "channel": "editable",
    "source": {"branch": "main", "ahead": 0, "behind": 0, "last_fetch": "2026-09-14T08:12:00Z"},
    "latest_version": null
  },
  "modules": [
    {"name": "sushiengine", "location": "sushiengine", "state": "cloned", "presence": "cloned",
     "version": null,
     "source": {"branch": "main", "ahead": 2, "behind": 0, "last_fetch": "2026-09-14T08:12:00Z"},
     "binary": null,
     "latest_version": null}
  ],
  "dependencies": {"path": "…", "present": true}
}
```

- `source` is set for `cloned` and `linked` and null otherwise. `branch` is null on a detached
  HEAD. `ahead` and `behind` are null when there is no upstream. `last_fetch` is the mtime of
  `.git/FETCH_HEAD`, null when the checkout has never been fetched.
- `binary` is `{"platform", "licence_expires_at"}` for `binary` and null otherwise.
- `alias` is null when no rc file carries the `# sushi hub alias` marker.
- `channel` is `editable`; it is a field so wave 7's frozen build can report `frozen`.
- `latest_version` is null unless `checked_updates` is true. For a binary it is what Sushi ID
  resolves; for a checkout the fetch updates `behind` instead and `latest_version` stays null.
- An online failure (not signed in, no network) leaves the field null and adds one `line` event
  at `warn` level. The exit code stays 0.

## Files

| Task | Creates | Modifies | Waits on |
|---|---|---|---|
| 1 | `sushihub/contract/status.schema.json` | `sushihub/contract/README.md` | — |
| 2 | `sushihub/cli/sushistack/services/git_state.py`, `tests/test_git_state.py` | — | 1 |
| 3 | `sushihub/cli/sushistack/services/hub_install.py`, `tests/test_hub_install.py` | — | 1 |
| 4 | `sushihub/cli/sushistack/services/update_check.py`, `tests/test_update_check.py` | — | 1 |
| 5 | `tests/test_status_payload.py` | `services/modules.py`, `cli.py`, `sushihub/cli/README.md` | 2, 3, 4 |
| 6 | `sushihub/gui/tests/fixtures/events/doctor.jsonl` | `ui/screens/InstallsScreen.hpp/.cpp`, `tests/fixtures/events/status.jsonl`, `tests/event_test.cpp` | 1 |

Tests paths under 2–5 are relative to `sushihub/cli/`.

---

### Task 1: The contract

- [ ] `status.schema.json` describes the payload above: every key required, every nullable key
      typed `[..., "null"]`.
- [ ] The contract README names the file, says `hub status --check-updates` is the one online
      form, and says what a null means.

Acceptance: the example payload above validates against the schema (`python -c` with
`jsonschema`, pasted).

### Task 2: Git state

- [ ] `read_git_state(path) -> GitState | None` returns branch, ahead, behind, last_fetch; None
      when `path` is not a checkout. It runs `git rev-parse --abbrev-ref HEAD` and
      `git rev-list --left-right --count @{u}...HEAD`, never `fetch`.
- [ ] `fetch(path) -> bool` runs `git fetch --quiet` and reports success. It is the only
      function in the file that touches the network.
- [ ] Tests build real repositories in `tmp_path`: no upstream, ahead by two, behind by one,
      detached HEAD, never fetched.

Acceptance: `python -m pytest sushihub/cli/tests/test_git_state.py -q`.

### Task 3: How `hub` is installed

- [ ] `read_hub_install(home: Path) -> dict` returns the `hub` block without `source` and
      `latest_version`: the command, the alias found by scanning `.bashrc`, `.zshrc` and the
      PowerShell profile paths under `home` for the marker, and the channel.
- [ ] `home` is a parameter so tests never read the real home directory.

Acceptance: `python -m pytest sushihub/cli/tests/test_hub_install.py -q`.

### Task 4: The update check

- [ ] `latest_release(client, product, platform) -> str | None` asks `/api/releases/resolve`
      without a version and returns what it names, None on any refusal or network error, and
      reports the reason to its caller.
- [ ] Tests run against the fake Sushi ID from `tests/test_identity.py`.

Acceptance: `python -m pytest sushihub/cli/tests/test_update_check.py -q`.

### Task 5: Composing the payload

- [ ] `status_payload(check_updates: bool = False)` adds `checked_updates`, `hub`, and per row
      `source`, `binary`, `latest_version`, from Tasks 2–4 and the existing `read_release` and
      `read_licence_expiry`.
- [ ] With `check_updates`, it fetches first, then reads, so `behind` is fresh.
- [ ] `hub status --check-updates` exists; the table output gains a Branch column and prints
      the online warnings.
- [ ] The CLI README documents the flag.

Acceptance: `python -m pytest sushihub/cli/tests -q`, all green, pasted.

### Task 6: The Installs card reads it

- [ ] The card draws `source`, `binary`, `alias` and `latest_version` where it drew dashes.
      A null `last_fetch` draws "never fetched"; otherwise "fetched N days ago".
- [ ] The screen starts `hub --json status --check-updates` once, after the offline run has
      finished, adopts it into `RunLog`, and switches to its payload when it arrives.
- [ ] `status.jsonl` carries the new keys; `doctor.jsonl` is recorded by hand from the table
      shape `hub doctor --json` prints today.
- [ ] `event_test.cpp` parses both fixtures.

Acceptance: the syntax check through `clang-tidy --checks='clang-diagnostic-*'` is clean, then
the user runs `hub gui build`, `hub gui test`, `hub gui run`.

## How it runs

Task 1 alone. Tasks 2, 3, 4 and 6 share no file and wait only on Task 1. Task 5 waits on 2, 3
and 4. After the last task: `hub gui build`, `hub gui test`, `hub gui run`.

The coordinator writes:
``- 2026-09-15 — Added branch, licence expiry, alias and an online update check to `hub status` (`sushihub/cli/sushistack/services/modules.py`, `sushihub/contract/status.schema.json`).``
and closes the wave 4c follow-ups in `docs/design/REMAINING_WORK.md`.
