# Fixtures

Both files here are hand-written from the contract, not recorded from a run. `ss --json` and
`ss --describe` land in wave 1a-cli, which had not reached this tree when the parsers were
written. Replace them with real output as soon as it exists:

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
