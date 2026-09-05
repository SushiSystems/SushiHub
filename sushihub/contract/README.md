# The `ss` JSON contract

Two schemas in this directory describe everything a program needs to drive `ss` without parsing
a terminal. `events.schema.json` covers one line of output; `describe.schema.json` covers the
command catalogue. Both are JSON Schema draft 2020-12. The desktop application validates against
them and so does `../cli/tests/test_json_streams.py`, so a stream that violates either is a defect
on the `ss` side, not a case for the reader to tolerate.

The design behind them is `docs/agent/specs/2026-09-05-hub-design.md`, section 7.

A third page in this directory, `sushi-id.md`, is the other half of the contract: the six Sushi ID
endpoints `ss` calls. Four of them sign a machine in and read the account, for `ss login`,
`ss logout`, `ss whoami` and `ss license`. The other two serve `ss add sushiengine` and
`ss update sushiengine`: `POST /api/licenses/token` issues the licence token `ss` writes beside a
binary install, and `POST /api/releases/resolve` answers with a signed download URL, a sha256 and a
size. That page faces sushiweb rather than the desktop application, and it has no schema because
the shapes are small enough to read.

## What `ss` prints under `--json`

One JSON object per line, UTF-8, in the order the command produced them. Keys are stable.

```json
{"event": "line",     "level": "info",   "message": "..."}          level ∈ info|success|warn|error
{"event": "command",  "command": "cmake -S . -B build"}
{"event": "header",   "title": "SushiStack Install"}
{"event": "panel",    "title": "...", "body": "..."}
{"event": "table",    "title": "...", "columns": ["A","B"], "rows": [["a1","b1"]]}
{"event": "progress", "label": "install-deps", "index": 2, "count": 4, "fraction": 0.5}   fraction may be null
{"event": "result",   "ok": true, "payload": {}}
{"event": "prompt",   "id": "confirm-1", "message": "...", "default": "n"}               default may be null
```

Every command ends with exactly one `result`. Its `ok` mirrors the process exit code, and its
`payload` carries whatever the command computed: `ss status` puts the module list there, `ss home`
the workspace and dependency paths. A command with nothing to report sends an empty object.

## stdout and stderr

stdout carries event lines and nothing else. Rich renderables that the human path prints directly
(the setup progress bar, a rendered config file) go to stderr under `--json`, because the renderer
binds its raw Rich console to that stream. A consumer reads stdout line by line and treats stderr
as diagnostics for a human.

`ss --describe` is the one exception: it prints a single JSON object, the catalogue, not a stream
of event lines. It ignores `--json` because it has nothing else to be.

## Prompts

A question becomes a `prompt` event and stops there. The reader answers by writing one line to the
CLI's stdin. An empty line means the `default`; end of input means the same. The `id` is
`prompt-N`, counted from one within a run, so an answer can be matched to the question that asked
for it.

`--yes` still answers the prompts it covers before they are asked, exactly as on the human path.

## The catalogue

`ss --describe` serialises the Typer application's own command objects. Nothing declares a command
twice: the catalogue is what `ss` already knows, written down, so a new subcommand reaches the
desktop application without desktop code.

```json
{
  "program": "ss",
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
`sushistack-cli` distribution's version, or `"0"` when `ss` runs from a source tree that was never
installed. `contract` is the version of this document and these schemas; it changes when a key
changes meaning.

`applies_to` names the forms of module presence a command works on. Every command in this contract
version lists all three, because none of them yet refuses one: `binary` is the form the sushiengine
binary distribution takes, and the commands that cannot serve it are narrowed when that distribution
lands.
