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

## Building

C++17, CMake 3.25 or newer, Ninja, and vcpkg in manifest mode. `vcpkg.json` names the four
ports: `imgui` with the GLFW and OpenGL3 bindings, `glfw3`, `nlohmann-json` and `gtest`. The
imgui port must be 1.91.1 or newer, which is where `ImGuiChildFlags_Borders` arrived.

The toplevel `CMakeLists.txt` picks the vcpkg toolchain in this order: a `CMAKE_TOOLCHAIN_FILE`
the caller passed, then `$VCPKG_ROOT`, then the workspace's own tree at `dependencies/vcpkg`.
The last one is what `ss install` provisions, so a workspace checkout configures with no
environment set up.

```
cmake --preset windows-x64
cmake --build --preset windows-x64
ctest --preset windows-x64
```

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
desktop without any code here.
