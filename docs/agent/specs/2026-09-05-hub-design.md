# The hub: `ss` in the terminal and on the desktop — Design

Date: 2026-09-05
Status: approved in conversation, awaiting the wave 1 plans

## 1. Purpose

SushiStack is open source, as are sushiruntime, sushiblas, sushiai and sushidsp. sushiengine is
sold: a licence bought through Sushi ID gives a person a compiled engine. Today the workspace
serves one kind of person, an engineer who clones everything and builds it. It must serve a second
kind, a licensed user who downloads the engine and opens a project, and it must serve both from the
same download, with no fork and no mode switch.

The `ss` command already owns the workspace: dependencies, module checkouts, module CLIs. This
design makes `ss` the whole experience. In the terminal it stays the command it is, with sign-in,
licence and binary installation added. On the desktop a Dear ImGui application gives every one of
its commands a screen and calls `ss` underneath. The two faces share one core and one contract.
The programme is called the hub; there is no program of that name.

## 2. Decisions

| Question | Decision |
|---|---|
| Who the hub serves first | The engineer who develops with the stack. The engine's end user second. |
| How a licensed user receives sushiengine | A compiled binary per platform, downloaded from Sushi ID, never source |
| How the binary carries sushiruntime and sushiblas | Inside the package, built together with the engine. The user's own checkouts of those modules are not involved |
| Where the licence is checked | At download, by Sushi ID; and at run time, by the engine, with an offline rule the engine's own design sets |
| Terminal interface | `ss` as it is. No text-mode application |
| Desktop interface | C++ and Dear ImGui, in this repository, calling `ss` as a subprocess and reading JSON |
| What the desktop application covers | Every `ss` command. Not the module CLIs; building, testing and running stay in the terminal |
| Where the code lives | `sushihub/cli/` (today's `cli/`), `sushihub/gui/`, `sushihub/contract/`; `sushicore/` unchanged in role |
| Does the Python side depend on `sushicore` | Yes, as it does today. The C++ side depends on nothing but the JSON contract |
| How a developer and a user differ | Only in state `ss` finds: Git access to the private repository, a Sushi ID session, a licence, which modules are present |
| Which toolchains `ss install` provisions | Those the present modules declare. An empty workspace installs the base fragment only |

## 3. Two people, one download

Both run the same installer and receive the same `ss` and the same desktop application. What they
see afterwards follows from what `ss` finds on their machine and in their account.

| Step | Licensed user | Engineer |
|---|---|---|
| Install | `irm install.ps1 \| iex`; the desktop application opens | same command; stays in the terminal |
| Sign in | in the application, with Sushi ID | `ss login`, or nothing: Git credentials suffice for source |
| sushiengine | an "Install" button; the binary downloads | `ss add sushiengine`; the private repository clones |
| Dependencies | none; the binary carries its own | `ss install`; the full toolchain set |
| Other modules | may clone them; they are open source and build like anyone's | `ss add all` |
| Run | choose a project; the editor opens | `se build`, `se editor` |

Four mechanisms hold this together.

**The form of a module is decided at install, not in code.** `ss add sushiengine` tries the
source path first: with the user's Git identity it asks the private repository whether it is
reachable (`git ls-remote`). If it is, it clones. If not, it asks the Sushi ID session for a live
licence; with one, it downloads the binary and records the module as `binary`. With neither it
says which of the two is missing and where each is obtained. The four open-source modules have one
path; everyone clones. The desktop application makes the same decision and labels its button
"Clone" or "Install" accordingly.

**Dependencies follow the present modules.** `ss install` merges the base fragment with each
present module's `cli/sushistack.deps.toml` (`cli/sushistack/setup/dependency_source.py`). A binary
sushiengine ships no fragment, so a licensed user never downloads a SYCL toolchain, vcpkg or LLVM.
Today this rule is broken in one place: `build_pipeline` in `cli/sushistack/setup/factory.py`
turns every toolchain on unconditionally, and both install scripts run `ss install` before any
module is added. Wave 1b repairs it (§9). If a user clones an open-source module beside a binary
engine, the toolchains that module declares will download, several gigabytes of them; that is the
right behaviour, because there is now something to build, and the desktop application says so
beside the "Clone" button.

**`se` reads the install it lives in.** A source root has `CMakeLists.txt`; a binary root has a
marker file the release carries. `ModuleProfile` (`sushicore/sushicore/profile.py`) learns the
marker, and `se` registers its command set from it: in a source install every command, in a binary
install `editor`, `player`, `package` and the diagnostics. One package, one version, one branch.
The change to `se` itself belongs to the sushiengine repository (§10).

**`ss status` and `ss doctor` tell the truth about both.** For the user, a line such as
"sushiengine: binary 1.4.2, licence valid to 2027-03-01". For the engineer, "sushiengine: cloned,
main, 3 ahead". A dependency no present module needs reports as not needed, not as missing.

## 4. Repository layout

```
sushistack/
  sushicore/              the CLI engine: ss, sr, se, sa, sb, sd all consume it
  sushihub/
    cli/                  Python: the ss command (today's cli/, moved whole)
    gui/                  C++: the Dear ImGui application; calls ss as a subprocess
    contract/             the JSON schema; cli tests and gui tests both run against it
  install.sh, install.ps1
  docs/
```

`sushicore` gains two things and nothing else: a `JsonRenderer` implementing the existing
`Renderer` protocol (`sushicore/sushicore/renderer.py` already names this as the intended
extension), and the binary-root marker in `ModuleProfile`. Neither names a module.

The dependency direction is one way. `sushihub/cli` imports `sushicore`, as it does today for
`build_console`, `ToolConfig` and the `workspace` helpers. `sushicore` knows nothing of the hub.
`sushihub/gui` imports neither; its only bond is the contract.

## 5. Presence: a third form of module

A module is present in a workspace in one of three forms, recorded in `cli/modules.local.toml`
and shown by `ss status`:

| Form | How it arrived | What `ss update` does | What its CLI offers |
|---|---|---|---|
| `cloned` | `ss add`, a checkout under the workspace root | `git pull --ff-only` | everything |
| `linked` | `ss link`, a checkout elsewhere | `git pull --ff-only` | everything |
| `binary` | `ss add`, a release downloaded and unpacked | asks Sushi ID for a newer release, downloads it | the consumer subset |

A binary install lives at the same path a clone would (`<workspace>/sushiengine`), so every
sibling-resolution rule (`docs/architecture/WORKSPACE.md`) holds unchanged. Its root carries the
marker file and a manifest the release ships: product, version, platform, the bundled
sushiruntime and sushiblas versions, and the signature `ss` verified before unpacking.

## 6. Sign-in and licence

`ss login` opens the browser on Sushi ID's device-authorization page, shows the code in the
terminal, polls until the grant completes, and stores the refresh token in the operating system's
credential store through `keyring`. `ss logout` removes it. `ss whoami` prints the account and its
live licences. The desktop application drives the same three through the contract; its sign-in
screen is the terminal flow with the code rendered as a button that opens the browser.

`ss license` prints the licences the account holds, each with product, form (account or
organization seat) and expiry. `ss add sushiengine` on the binary path asks Sushi ID for a download
URL for the account's licence and the machine's platform, downloads to a temporary path, verifies
the release signature, unpacks, and writes the licence file the engine reads at start-up. The file's
contents and the engine's offline rule are the engine's design; `ss` only writes what Sushi ID
hands it.

`ss projects` lists the projects a binary engine knows about, so the desktop application can show
them and open one with `se editor --project <name>`.

Every one of these needs a Sushi ID endpoint that does not exist yet (§10). Wave 2 builds the
`ss` side against a fake server that speaks the agreed shapes, so the two repositories can move in
parallel.

## 7. The JSON contract

Two halves, both versioned in `sushihub/contract/` as JSON Schema.

**Description.** `ss --describe` prints the command catalogue: each command's name, help text,
arguments and options with their types, defaults and choices, and which forms of presence it
applies to. Typer holds all of this already; the catalogue is a serialisation, not a second
declaration. The desktop application renders a form from a catalogue entry, so a new `ss` command
appears on the desktop without desktop code.

**Events.** Every command run with `--json` writes one event per line to stdout and nothing else
there. The event kinds are the semantic calls `Console` already exposes (`info`, `success`, `warn`,
`error`, `command`, `header`, `fail_panel`) plus three the desktop needs: `progress` (a step, its
index and count, and a fraction when known), `table` (columns and rows, for `status`, `doctor`,
`license`, `projects`) and `result` (the command's exit status and a structured payload). Prompts
become a `prompt` event and a line read from stdin; `--yes` answers them as today.

`JsonRenderer` produces the events. It is the third `Renderer`, chosen when `--json` is on the
command line, and the reason the change to `sushicore` is small: the CLI code keeps calling
`console.info(...)`; only the renderer differs.

Tests on both sides run against the schema. On the Python side each command has a recorded
event stream that is validated and diffed, in the manner of `tools/record_cli_argv.py`. On the
C++ side the bridge is fed the same recorded streams.

## 8. The desktop application

Dear ImGui on GLFW, C++17, one static binary, no runtime beyond the graphics driver. It matches
the engineer's taste and the stack's toolchain; it starts in under a second and draws at the
display's rate. It is not a web view and never will be.

Five screens are drawn by hand because they are opened every day: status, modules, dependencies,
licence, projects. Every other `ss` command is a generated form from the catalogue, so the rule
"every terminal command has a desktop equivalent" is kept by construction. As a generated form
proves worth polishing, it gains a hand-drawn screen; the form stays as the fallback.

The bridge spawns `ss <command> --json` and reads stdout line by line into a queue the UI thread
drains each frame; a long download shows its `progress` events as they arrive. A `prompt` event
opens a dialog whose answer goes to the child's stdin. Nothing in the application knows a module's
name, a file path or a toolchain; all of it arrives in events.

The application is installed by the install scripts beside `ss` (wave 7) and is what a licensed
user sees first. An engineer may never open it.

## 9. Waves

Ordered hierarchy first, then width. Each wave states what it waits on; waves that wait on the
same thing run in parallel. `docs/design/REMAINING_WORK.md` mirrors this table and is where
status is kept.

| Wave | Work | Waits on |
|---|---|---|
| 0 | Documentation skeleton; this document | nothing |
| 1a | `cli/` → `sushihub/cli/`; the contract schema; `JsonRenderer`; `ss --describe`; `--json` on every existing command | 0 |
| 1b | Dependencies follow the modules (§3); `ss doctor` reports by owner in dependency order; install scripts stop provisioning before a module exists | 0 |
| 2 | The `binary` form; the marker in `ModuleProfile`; `ss login`, `ss logout`, `ss whoami` against a fake Sushi ID | 1a |
| 3 | Sushi ID endpoints, in sushiweb | none here |
| 4 | `sushihub/gui`: skeleton, bridge, five screens, generated forms | 1a; 2 alongside |
| 5 | `ss add sushiengine` source-or-binary; download, verify, unpack; licence file; `ss projects` | 2, 3 |
| 6 | sushiengine: binary command set; `se editor --project`; runtime licence client | 5 |
| 7 | Install scripts fetch the desktop application; both journeys walked end to end | 4, 6 |

Waves 1a and 1b touch disjoint files: 1a moves `cli/` and adds to `sushicore/sushicore/renderer.py` and
`cli.py`; 1b edits `setup/factory.py`, `setup/steps.py` and the two install scripts. They land in
either order. Each wave gets its own plan under `docs/agent/plans/`.

## 10. What other repositories must build

**sushiweb.** Four endpoints, each deferred in its own documents as "device authorization grant
for desktop products" and to be designed there: the device authorization grant itself; a licence
query answering whether an account holds a live licence for a product, which `can()` already
computes internally; a signed, expiring download URL for a product release and platform; a runtime
check the engine calls with its licence file. Sushi ID's identity, licence, seat and subscription
model exists (`sushiweb/db/migrations/0011_licenses.sql` onward); nothing in this design asks it
to change.

**sushiengine.** The binary release: a package per platform carrying the engine, its bundled
sushiruntime and sushiblas, the root marker and manifest, signed. `se`'s command set from the
marker. `se editor --project <name>`. A runtime licence client with an offline rule. The build
that produces releases. All of it designed in that repository; this document only names the
marker and the manifest fields `ss` reads.

## 11. Out of scope

A text-mode interface. Wrapping the module CLIs (`sr build` and the like) in the desktop
application. Distributing the open-source modules as binaries. A version resolver that matches a
binary engine to a user's own sushiruntime build; the binary carries its own. Anything the engine
does after it has read its licence file.

## 12. Risks

**The contract drifts.** Two languages, one schema. Mitigated by keeping both test suites against
the same recorded streams and by landing every contract change in one commit that touches the
schema, the Python emitter and the C++ reader.

**A binary release lags its dependencies.** The engine bundles sushiruntime and sushiblas, so a
fix in either reaches a licensed user only with the next engine release. Accepted; the alternative
is the version resolver ruled out in §11.

**Sushi ID's endpoints arrive late.** Wave 2 builds against a fake; waves 5 to 7 wait. The fake's
shapes are written down in the contract directory so the real endpoints have a target.

**The generated forms are ugly.** They are the floor, not the ceiling. The five daily screens are
drawn by hand from the start, and any form that earns attention is promoted.
