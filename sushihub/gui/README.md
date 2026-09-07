# `sushihub/gui` — the desktop application

A Dear ImGui window over `hub`. It spawns `hub --json <command>`, reads one JSON event per line
from the child's stdout, and draws what arrives. Nothing here knows a module name, a toolchain
or a path; all of that comes in events or in the catalogue `hub --describe` prints.

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
`hub --describe` once, and `open_in_browser`, which hands a link to `ShellExecuteW` on Windows and
to `xdg-open` elsewhere. `Theme` is the only place a colour, a rounding or a spacing is chosen.

## What the screens draw

The sidebar lists the five hand-drawn screens, then every catalogue command none of them covers.
`Shell` reads the catalogue at start-up and builds a form the first time a command is selected,
so a form keeps what was typed into it while the user is elsewhere.

`Status` draws the tables of `hub --json status` and the dependency directory its result payload
names. `Modules` draws the rows of the same run and ends each one with an Add and an Update
button that open that module's form with the module already entered. `Dependencies` draws the
table of `hub --json doctor`, dims the rows reading NOT NEEDED and offers Install on the rows
reading MISSING. `Licence` draws `whoami` and `license`, and its Sign in button starts `login`,
shows the user code at two and a half times the text size, and opens the verification link.
`Projects` draws the rows of `hub --json projects list`, the one run whose arguments `Workspace`
maps from the screen name instead of copying it. Each row ends with Open and Remove, a row whose
directory is gone is dimmed, and the form under the table registers a directory under a name of
its own when one is typed. Open spawns `se editor --project <path>` and reads nothing back from
it; `se` is the only program other than `hub` this application starts.

Four widgets do the drawing everywhere: `EventLog` renders a run's events in arrival order,
`TableView` one table event, `ProgressBar` the latest progress event, and `PromptDialog` the
question a run stopped on.

## The generated form

`GeneratedForm` turns one catalogue `Command` into widgets: a checkbox for a boolean, a combo for
a choice, a text field for the rest, filtered to decimal or scientific characters where the type
asks for it. ImGui has no file dialog, so a path is typed and the Browse button puts the caret
back in the field. A parameter that takes more than one value is typed as a space-separated list.
Run assembles `hub --json <command>`, then the options as `--flag value` with a true boolean as
the bare flag, then the positional arguments in the order the catalogue declares them.

## What the UI reads into `hub` output

Two rules here are guesses at shape rather than schema, and both are worth knowing about when the
CLI's wording changes.

The event schema carries no field for a device code, so `read_device_grant` takes one out of the
`login` run's messages: a word of six to twenty-four characters built from capitals, digits and
hyphens, holding at least one capital and one digit, is the code, and the first word beginning
`http://` or `https://` is the verification link. A `result` payload carrying `user_code` or
`verification_uri` outranks both.

`hub status`'s result payload reports its dependency directory either as a path or as an object
with `path` and `present`; the status screen draws whichever arrives.

## Building

`hub` builds it. C++17, CMake 3.25 or newer, Ninja.

```
hub install     # once: imgui, glfw3 and nlohmann-json arrive
hub gui build   # --type debug|release|relwithdebinfo, --clean, -D VAR=VALUE
hub gui test    # --filter <pattern>, --repeat <n>
hub gui run     # an optional target, then anything after -- goes to the program
hub gui clean
```

The ports are declared in `sushihub/cli/manifests/gui.deps.toml`: `imgui` with the GLFW and
OpenGL3 bindings, `glfw3`, and `nlohmann-json`. `gtest` comes from the base fragment, because
every module in the stack tests with it. `hub install` puts them in the workspace's shared
`dependencies/vcpkg` tree, in classic mode. The imgui port must be 1.91.1 or newer, which is
where `ImGuiChildFlags_Borders` arrived.

`hub gui build` configures into `build/hub` with the vcpkg toolchain file, the triplet and
`VCPKG_MANIFEST_MODE=OFF`, and on Windows it spawns cmake under a snapshot of the environment
`vcvars64.bat` produces. A `cmake` run from a plain PowerShell has neither, which is why one
reports that it found no compiler.

The presets remain for an IDE, and configure into `build/<preset>`:

```
cmake --preset windows-x64
cmake --build --preset windows-x64
ctest --preset windows-x64
```

They need what `hub gui build` arranges for itself: a shell that has already run `vcvars64.bat`,
and `VCPKG_MANIFEST_MODE=OFF` set in the environment or passed as a cache variable. The toplevel
`CMakeLists.txt` picks the vcpkg toolchain in this order: a `CMAKE_TOOLCHAIN_FILE` the caller
passed, then `$VCPKG_ROOT`, then the workspace's own tree at `dependencies/vcpkg`.

`linux-x64` is the same three commands on Linux. Both presets are Ninja Multi-Config with Debug
and Release; the build and test presets default to Debug, and `windows-x64-release` builds the
other configuration.

## Tests

GoogleTest, one suite per layer, discovered by `gtest_discover_tests`. `bridge_test` spawns a
Python one-liner and reads its output back. `event_test` and `catalogue_test` parse the fixtures
in `tests/fixtures/`, which are hand-written until `hub --json` and `hub --describe` land; the
README there says how to record the real thing. `model_test` feeds a scripted queue to a
`CommandRun` and checks the fold. The `ui/` layer has no unit tests; it is checked by running the
application.

## Talking to `hub`

`hub` writes one JSON object per line to stdout under `--json` and nothing else there; stderr is
diagnostics for a human. Every run ends with exactly one `result` event carrying the exit status
and a payload. A `prompt` event stops the run until the reader writes one line to the child's
stdin, which is what `CommandRun::answer_prompt` does.

Five screens are drawn by hand: status, modules, dependencies, licence, projects. Every other
`hub` command gets a form generated from its catalogue entry, so a new subcommand reaches the
desktop without any code here. `hub` itself is looked up on the search path; `Workspace` holds the
name every run is spawned from and is the one place to change it.
