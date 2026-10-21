# sushitrack returns to the module catalog

**Status:** Shipped — 2026-10-21. The owner reversed the 2026-09-22 decision that took
`sushitrack` out of the catalog.

`sushitrack` is a catalog module again, with `st` as its alias, so `hub add sushitrack` clones it
and `hub install-cli sushitrack` installs `st`. Joining is optional: `pipx install cli/` from the
checkout still gives a standalone `st`, and `hub link` attaches an existing checkout later.
`sushidsp` stays outside the catalog.

## What changed

- `cli/sushihub/catalog.toml` gained the `sushitrack` entry; `.gitignore` gained `/sushitrack/`.
- `test_catalog.py` and `test_link.py` name six modules and the `st` alias. The test that kept
  both products out now keeps only `sushidsp` out.
- The manual pages that list the modules, the changelog and the decision in
  `docs/design/WORKSPACE_DECOUPLING.md` say the same.

## Checks

The suite ran 324 passed. Four test files do not collect here (`test_describe`,
`test_docs_command`, `test_json_streams`, `test_status_payload`) because `jsonschema` is not
installed in the environment that ran them; they were not run. `hub add st --dry-run`,
`hub link` and `hub install-cli sushitrack` were run against a real checkout, and `st` installed.

## Seen and not changed

`test_link_refuses_a_checkout_that_describes_a_different_module` never stubbed `links.write`. When
it failed during this work it wrote two test paths into the real `.sushistack/workspace.toml`;
both entries were restored with `hub link` and the test now stubs the write.

## Fixed afterwards

`modules.link` checked that a manifest matched the name only for a module outside the catalog, so
linking a checkout that describes another module under a catalog name was accepted and recorded.
It now reads the manifest for every name and refuses a mismatch, with four tests
(`test_manifest_precedence.py`) and a line in `MODULE_MANIFEST.md`. The suite ran 328 passed; the
same four files as before do not collect without `jsonschema`.
