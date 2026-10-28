# Programmes

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-11 | P2 | blocked | Close wave 6 of the hub programme | the engine's side of a binary install is built | sushiengine RW-305 | `docs/design/HUB/README.md` | 2026-10-19 |
| RW-12 | P2 | blocked | Ship the desktop application through the installers, wave 7 | the install scripts fetch the desktop application and both journeys are walked end to end | RW-11, RW-4 |  | 2026-10-19 |
| RW-13 | P2 | blocked | Deploy the account side of the hub, wave 3 | the account project has its JWT and Supabase storage variables, and the end-to-end check passes on a released engine | sushiweb RW-34 |  | 2026-10-19 |
| RW-14 | P2 | blocked | Ship the desktop application as `sushihub-gui`, decoupling wave 8 | `pipx install "sushihub[gui]"` installs it | RW-4 | `docs/design/WORKSPACE_DECOUPLING/README.md` | 2026-10-19 |
| RW-15 | P2 | blocked | Close the standalone programme | each module's real `setup` and build has run on the standalone layout, and the hub root migration has run for real and been finalized or rolled back | sushicore RW-8, sushicore RW-9 |  | 2026-10-19 |
| RW-16 | P2 | open | Close the documentation site programme | every publisher attaches its bundle to its release, the site is deployed, the owner's two decisions and the deferred findings of the rollout report are… |  | `docs/agent/2026_10_07_DOCS_ROLLOUT/REPORT.md` | 2026-10-19 |
| RW-17 | P2 | open | Settle the command lines as one surface | every Sushi command line uses the same panel names, short options and defaults, and `sr`, `se`, `sa`, `sb`, `sd` and `st` have adopted `help_group` (command… |  |  | 2026-10-19 |
| RW-18 | P2 | open | Run the estate programmes | the licence, command line, documentation and layout, and code programmes the estate audit of 2026-10-05 opened are closed in every repository |  |  | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
