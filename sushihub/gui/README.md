# `sushihub/gui` — the desktop application

A Dear ImGui window over `ss`. It spawns `ss --json <command>`, reads one JSON event per line
from the child's stdout, and draws what arrives. Nothing here knows a module name, a toolchain
or a path; all of that comes in events or in the catalogue `ss --describe` prints.

The contract both sides validate against is `../contract/`. The design behind it is
`../../docs/agent/specs/2026-09-05-hub-design.md`, sections 7 and 8.

## Layers

Four directories under `src/`, each depending only on the one below it, each a separate library
so the build enforces the order.

`bridge/` spawns a process and turns its stdout into a queue of lines. It has never heard of
JSON. `contract/` parses one line into an `Event` and the catalogue into `Command` records; it
has never heard of processes or pixels. `model/` runs a command through the bridge and folds the
events into a `RunState` the UI reads each frame; it has never heard of ImGui. `ui/` draws.
`main.cpp` wires them together.

`ui/` holds `Shell`, the four widgets under `widgets/`, the five screens under `screens/`, the
form under `forms/`, and two bricks the screens lean on: `CatalogueSource`, which reads
`ss --describe` once, and `open_in_browser`, which hands a link to `ShellExecuteW` on Windows and
to `xdg-open` elsewhere. `Theme` is the only place a colour, a rounding or a spacing is chosen.

## What the screens draw

The sidebar lists the five hand-drawn screens, then every catalogue command none of them covers.
`Shell` reads the catalogue at start-up and builds a form the first time a command is selected,
so a form keeps what was typed into it while the user is elsewhere.

`Status` draws the tables of `ss --json status` and the dependency directory its result payload
names. `Modules` draws the rows of the same run and ends each one with an Add and an Update
button that open that module's form with the module already entered. `Dependencies` draws the
table of `ss --json doctor`, dims the rows reading NOT NEEDED and offers Install on the rows
reading MISSING. `Licence` draws `whoami` and `license`, and its Sign in button starts `login`,
shows the user code at two and a half times the text size, and opens the verification link.
`Projects` says that projects arrive with wave 5, because `ss projects` does not exist yet.

Four widgets do the drawing everywhere: `EventLog` renders a run's events in arrival order,
`TableView` one table event, `ProgressBar` the latest progress event, and `PromptDialog` the
question a run stopped on.

## The generated form

`GeneratedForm` turns one catalogue `Command` into widgets: a checkbox for a boolean, a combo for
a choice, a text field for the rest, filtered to decimal or scientific characters where the type
asks for it. ImGui has no file dialog, so a path is typed and the Browse button puts the caret
back in the field. A parameter that takes more than one value is typed as a space-separated list.
Run assembles `ss --json <command>`, then the options as `--flag value` with a true boolean as
the bare flag, then the positional arguments in the order the catalogue declares them.

## What the UI reads into `ss` output

Two rules here are guesses at shape rather than schema, and both are worth knowing about when the
CLI's wording changes.

The event schema carries no field for a device code, so `read_device_grant` takes one out of the
`login` run's messages: a word of six to twenty-four characters built from capitals, digits and
hyphens, holding at least one capital and one digit, is the code, and the first word beginning
`http://` or `https://` is the verification link. A `result` payload carrying `user_code` or
`verification_uri` outranks both.

`ss status`'s result payload reports its dependency directory either as a path or as an object
with `path` and `present`; the status screen draws whichever arrives.

## Building

`ss` builds it. C++17, CMake 3.25 or newer, Ninja.

```
ss install     # once: imgui, glfw3 and nlohmann-json arrive
ss gui build   # --type debug|release|relwithdebinfo, --clean, -D VAR=VALUE
ss gui test    # --filter <pattern>, --repeat <n>
ss gui run     # an optional target, then anything after -- goes to the program
ss gui clean
```

The ports are declared in `sushihub/cli/manifests/gui.deps.toml`: `imgui` with the GLFW and
OpenGL3 bindings, `glfw3`, and `nlohmann-json`. `gtest` comes from the base fragment, because
every module in the stack tests with it. `ss install` puts them in the workspace's shared
`dependencies/vcpkg` tree, in classic mode. The imgui port must be 1.91.1 or newer, which is
where `ImGuiChildFlags_Borders` arrived.

`ss gui build` configures into `build/ss` with the vcpkg toolchain file, the triplet and
`VCPKG_MANIFEST_MODE=OFF`, and on Windows it spawns cmake under a snapshot of the environment
`vcvars64.bat` produces. A `cmake` run from a plain PowerShell has neither, which is why one
reports that it found no compiler.

The presets remain for an IDE, and configure into `build/<preset>`:

```
cmake --preset windows-x64
cmake --build --preset windows-x64
ctest --preset windows-x64
```

They need what `ss gui build` arranges for itself: a shell that has already run `vcvars64.bat`,
and `VCPKG_MANIFEST_MODE=OFF` set in the environment or passed as a cache variable. The toplevel
`CMakeLists.txt` picks the vcpkg toolchain in this order: a `CMAKE_TOOLCHAIN_FILE` the caller
passed, then `$VCPKG_ROOT`, then the workspace's own tree at `dependencies/vcpkg`.

`linux-x64` is the same three commands on Linux. Both presets are Ninja Multi-Config with Debug
and Release; the build and test presets default to Debug, and `windows-x64-release` builds the
other configuration.

## Tests

GoogleTest, one suite per layer, discovered by `gtest_discover_tests`. `bridge_test` spawns a
Python one-liner and reads its output back. `event_test` and `catalogue_test` parse the fixtures
in `tests/fixtures/`, which are hand-written until `ss --json` and `ss --describe` land; the
README there says how to record the real thing. `model_test` feeds a scripted queue to a
`CommandRun` and checks the fold. The `ui/` layer has no unit tests; it is checked by running the
application.

## Talking to `ss`

`ss` writes one JSON object per line to stdout under `--json` and nothing else there; stderr is
diagnostics for a human. Every run ends with exactly one `result` event carrying the exit status
and a payload. A `prompt` event stops the run until the reader writes one line to the child's
stdin, which is what `CommandRun::answer_prompt` does.

Five screens are drawn by hand: status, modules, dependencies, licence, projects. Every other
`ss` command gets a form generated from its catalogue entry, so a new subcommand reaches the
desktop without any code here. `ss` itself is looked up on the search path; `Workspace` holds the
name every run is spawned from and is the one place to change it.
