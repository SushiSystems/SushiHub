# Fixtures

The files here are what `hub` printed on a real workspace, last on 2026-09-22. They prove the
parsers accept the stream `hub` actually writes today. Re-record them whenever the contract or the
command set changes:

```
hub --json status > events/status.jsonl
hub --json doctor > events/doctor.jsonl
hub --describe    > describe.json
```

A recorded stream the parsers refuse is a finding about the parsers, not a reason to edit the
recording.

Sources: `../../../contract/events.schema.json`, `../../../contract/describe.schema.json`,
`../../../contract/status.schema.json` and `../../../contract/README.md`.
