# The `hub` JSON contract

Three schemas in this directory describe everything a program needs to drive `hub` without parsing
a terminal. `events.schema.json` covers one line of output, `describe.schema.json` the command
catalogue, and `status.schema.json` the payload `hub status` ends with. All three are JSON Schema
draft 2020-12. The desktop application validates against them and so does
`../cli/tests/test_json_streams.py`, so a stream that violates one is a defect on the `hub` side,
not a case for the reader to tolerate.

The design behind them is `docs/agent/specs/2026-09-05-hub-design.md`, section 7.

A fourth file in this directory, `sushi-account.md`, is the other half of the contract: the six Sushi Account
endpoints `hub` calls. Four of them sign a machine in and read the account, for `hub login`,
`hub logout`, `hub whoami` and `hub license`. The other two serve `hub add sushiengine` and
`hub update sushiengine`: `POST /api/licenses/token` issues the licence token `hub` writes beside a
binary install, and `POST /api/releases/resolve` answers with a signed download URL, a sha256 and a
size. That page faces sushiweb rather than the desktop application, and it has no schema because
the shapes are small enough to read.

## What `hub` prints under `--json`

One JSON object per line, UTF-8, in the order the command produced them. Keys are stable.

```json
{"event": "line",     "level": "info",   "message": "..."}          level ∈ info|success|warn|error
{"event": "command",  "command": "cmake -S . -B build"}
{"event": "header",   "title": "SushiHub Install"}
{"event": "panel",    "title": "...", "body": "..."}
{"event": "table",    "title": "...", "columns": ["A","B"], "rows": [["a1","b1"]]}
{"event": "progress", "label": "install-deps", "index": 2, "count": 4, "fraction": 0.5}   fraction may be null
{"event": "result",   "ok": true, "payload": {}}
{"event": "prompt",   "id": "confirm-1", "message": "...", "default": "n"}               default may be null
```

Every command ends with exactly one `result`. Its `ok` mirrors the process exit code, and its
`payload` carries whatever the command computed: `hub status` puts the module list there, `hub home`
the workspace and dependency paths. A command with nothing to report sends an empty object.

## The status payload

`status.schema.json` fixes the payload of `hub status`, because the desktop application's Installs
and Modules screens draw from it. Every key is always present. A fact `hub` could not read is
`null`: a detached HEAD has no `branch`, a checkout without an upstream has no `ahead` or
`behind`, one that was never fetched has no `last_fetch`.

`modules` carries the stack's modules and nothing else, the ones `catalog.toml` lists. It held a
`sushicore` row until 2026-09-22; `sushicore` is a PyPI dependency of `hub` rather than a module,
and `pip show sushicore` answers the version question. A consumer that still looks for the row
finds nothing and must not read the absence as an error.

Plain `hub status` reads the disk and never the network, so `ahead` and `behind` count against
the last fetch. `hub status --check-updates` is the one online form: it fetches every checkout
first and asks Sushi Account for every binary install's latest release, sets `checked_updates` to
true, and fills `latest_version`. A check that fails, because nobody is signed in or the network
is down, leaves its field `null`, prints one `warn` line and keeps the exit code at 0.

## stdout and stderr

stdout carries event lines and nothing else. Rich renderables that the human path prints directly
(the setup progress bar, a rendered config file) go to stderr under `--json`, because the renderer
binds its raw Rich console to that stream. A consumer reads stdout line by line and treats stderr
as diagnostics for a human.

`hub --describe` is the one exception: it prints a single JSON object, the catalogue, not a stream
of event lines. It ignores `--json` because it has nothing else to be.

## Prompts

A question becomes a `prompt` event and stops there. The reader answers by writing one line to the
CLI's stdin. An empty line means the `default`; end of input means the same. The `id` is
`prompt-N`, counted from one within a run, so an answer can be matched to the question that asked
for it.

`--yes` still answers the prompts it covers before they are asked, exactly as on the human path.

## The catalogue

`hub --describe` serialises the Typer application's own command objects. Nothing declares a command
twice: the catalogue is what `hub` already knows, written down, so a new subcommand reaches the
desktop application without desktop code.

```json
{
  "program": "hub",
  "version": "1.0.0",
  "contract": "1",
  "commands": [
    {
      "name": "add",
      "help": "Clone one or more stack modules into the workspace.",
      "params": [
        {"name": "modules", "kind": "argument", "type": "string", "multiple": true, "required": true,
         "default": null, "choices": null, "flags": [], "help": "Modules to clone: ..."},
        {"name": "dry_run", "kind": "option", "type": "boolean", "multiple": false, "required": false,
         "default": false, "choices": null, "flags": ["--dry-run"], "help": "Show, don't clone or install."}
      ],
      "applies_to": ["cloned", "linked", "binary"]
    }
  ]
}
```

`type` is one of `string`, `boolean`, `integer`, `number`, `path`, `choice`; a `choice` parameter
carries its values in `choices`, and every other kind leaves that null. `version` is the installed
`sushihub` distribution's version, or `"0"` when `hub` runs from a source tree that was never
installed. The distribution was called `sushistack-cli` until 2026-09-22; a consumer still asking
for that name reads `"0"` rather than failing, so check this name before trusting a `"0"`.
`contract` is the version of this document and these schemas; it changes when a key changes
meaning.

`applies_to` names the forms of module presence a command works on. Every command in this contract
version lists all three, because none of them yet refuses one: `binary` is the form the sushiengine
binary distribution takes, and the commands that cannot serve it are narrowed when that distribution
lands.
