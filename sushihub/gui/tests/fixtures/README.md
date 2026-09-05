# Fixtures

Both files here are recorded from a real run on 2026-09-05 with the two commands below; re-record them
whenever the contract or the command set changes.

```
ss --json status > events/status.jsonl
ss --describe    > describe.json
```

The tests read whatever is in these files, so a recorded stream that differs from the hand-written
one is a finding about the parsers, not a reason to edit the recording.

`events/status.jsonl` carries one line of every one of the eight event kinds, a `progress` event
with a numeric `fraction` and one with `null`, and a `prompt` with a default. `describe.json`
carries one parameter of every one of the six types, an argument with `multiple`, and a `choice`
with its values.

Sources: `../../../contract/events.schema.json`, `../../../contract/describe.schema.json` and
`../../../contract/README.md`.
