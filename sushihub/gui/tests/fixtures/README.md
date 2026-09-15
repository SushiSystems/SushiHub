# Fixtures

Two kinds of file live here, and a test reads the kind that matches what it checks.

**Recorded** files are what `hub` printed on a real workspace, last on 2026-09-15. They prove the
parsers accept the stream `hub` actually writes today. Re-record them whenever the contract or the
command set changes:

```
hub --json status > events/status.jsonl
hub --json doctor > events/doctor.jsonl
hub --describe    > describe.json
```

A recorded stream the parsers refuse is a finding about the parsers, not a reason to edit the
recording.

**Hand-written** files cover what no single real run produces, so the parsers are checked against
every shape the contract allows. `events/all_kinds.jsonl` carries one line of every one of the
eight event kinds, a `progress` event with a numeric `fraction` and one with `null`, and a
`prompt` with a default. `all_types.json` carries one parameter of every one of the six types, an
argument with `multiple`, a `choice` with its values, and a command with no parameters. Edit these
by hand when the contract gains a shape.

Sources: `../../../contract/events.schema.json`, `../../../contract/describe.schema.json`,
`../../../contract/status.schema.json` and `../../../contract/README.md`.
