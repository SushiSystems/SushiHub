# Wave 4c: the hub's own window — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** The desktop application stops being a sidebar of command outputs and becomes one window
a person manages the stack from: a title bar carrying the workspace and the account, a left rail
of four destinations, and a single activity strip along the bottom where every run reports.

**Architecture:** Three bricks are fixed before anything is drawn: a palette every widget reads
colours from, a `Screen` interface every destination implements, and a `RunLog` that owns the run
the strip draws. `Shell` then holds the chrome and the strip and knows nothing about what a screen
puts inside its region. The four screens are siblings of the same shape, each answering one
question: what is installed, what modules are present, how is the machine set up, and what else
can `hub` do.

**Tech Stack:** C++17, Dear ImGui, the existing `CommandRun` bridge over `hub --json`.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §8, and the approved mockup, whose layout
this plan follows: https://claude.ai/code/artifact/f3e762e4-f689-45e1-9b9c-fdfa681407d4

## Global Constraints

- Touch only `sushihub/gui/src/**` and `sushihub/gui/tests/**`. Not the Python side, not
  `sushicore/`, not `sushihub/contract/`.
- **No agent edits `sushihub/gui/CMakeLists.txt` or `sushihub/gui/src/CMakeLists.txt`.** A task
  that adds or deletes a source file says so in its report; the coordinator adds it to the build.
- No agent runs `cmake`, `ninja` or `ctest`. The user runs the build after each wave.
- Every file opens with `/** @file`, a one-sentence `@brief` and `@author Mustafa Garip`; every
  symbol carries a `@brief` starting with its verb. `docs/CONTRIBUTING.md` is the authority.
- Colours come from `Theme`, never from a literal `ImVec4` in a screen. Sizes come from
  `ImGui::GetFontSize()` multiples, never from a bare pixel count, so the window survives a
  different font size.
- A screen never blocks. It asks `Workspace` for its run and draws whatever has arrived.
- The projects registry is gone (2026-09-07); nothing here brings it back.

## The window, in one picture

```
┌ title bar ────────────────────────────────────────────────────────────┐
│ ● Sushi Hub 0.4.0-dev   [workspace D:\Projects\sushistack]   MG ▾      │
├──────────┬────────────────────────────────────────────────────────────┤
│ Installs │  screen region: the active Screen draws here               │
│ Modules  │                                                            │
│ Settings │                                                            │
│ Commands │                                                            │
├──────────┴────────────────────────────────────────────────────────────┤
│ ▸ hub status — done            [▓▓▓▓▓▓▓▓░░]  rc=0 · 0.4 s              │
└───────────────────────────────────────────────────────────────────────┘
```

The strip is collapsed at one line and expands to a log of the current run's events. It is the
only place a run is reported; no screen draws its own event log any more.

## Files

| Task | Creates | Modifies | Deletes |
|---|---|---|---|
| 1 | `src/ui/Screen.hpp`, `src/model/RunLog.hpp`, `src/model/RunLog.cpp` | `src/ui/Theme.hpp`, `src/ui/Theme.cpp` | — |
| 2 | `src/ui/chrome/TitleBar.hpp/.cpp`, `src/ui/chrome/NavRail.hpp/.cpp`, `src/ui/widgets/ActivityStrip.hpp/.cpp` | `src/ui/Shell.hpp`, `src/ui/Shell.cpp` | — |
| 3 | `src/ui/screens/InstallsScreen.hpp/.cpp` | — | `src/ui/screens/StatusScreen.hpp/.cpp` |
| 4 | — | `src/ui/screens/ModulesScreen.hpp/.cpp` | — |
| 5 | `src/ui/screens/SettingsScreen.hpp/.cpp` | — | `src/ui/screens/LicenceScreen.hpp/.cpp`, `src/ui/screens/DependenciesScreen.hpp/.cpp` |
| 6 | `src/ui/screens/CommandsScreen.hpp/.cpp` | — | — |
| 7 | — | `sushihub/gui/README.md`, `sushihub/gui/tests/*` | — |

Task 1 is a wave of its own. Tasks 2 to 6 are one wave and share no file. Task 7 follows them.

---

### Task 1: The palette, the screen interface, and the run log

**Files:** creates `src/ui/Screen.hpp`, `src/model/RunLog.hpp`, `src/model/RunLog.cpp`; modifies
`src/ui/Theme.hpp`, `src/ui/Theme.cpp`.

- [ ] `Theme` gains the mockup's palette as named accessors, each returning `ImVec4`:
      `ground` `#101317`, `rail` `#0B0D10`, `panel` `#171B21`, `panel_raised` `#1D222A`,
      `line` `#272D36`, `line_soft` `#1F242C`, `ink` `#DFE4EA`, `ink_dim` `#8A95A3`,
      `ink_faint` `#626D7B`, `accent` `#EF7A55`, `accent_ink` `#1A0F0A`, `accent_soft` `#3A2018`,
      `ok` `#5FAE86`, `warn` `#D3A244`, `critical` `#CF5F61`, `info` `#6F9FD0`.
      Keep the existing `level_colour` and `accent_colour` working by forwarding to these.
- [ ] `Theme::apply()` sets the ImGui style from the palette: window and child background `ground`,
      frame background `panel`, border `line`, text `ink`, a 4 px frame rounding, 0 px window
      rounding, and `ImGuiStyleVar_FramePadding` at `(0.8f, 0.5f)` of the font size.
- [ ] `Screen` is a pure interface: a virtual destructor, `virtual const char* name() const`,
      `virtual void draw() = 0`. Nothing else; a screen that needs a workspace takes it in its
      own constructor.
- [ ] `RunLog` owns which run the strip shows. Interface, exactly:
      ```cpp
      class RunLog {
      public:
          void adopt(CommandRun& run, std::string label);   ///< the strip now follows this run
          bool has_run() const;
          CommandRun& run();                                 ///< precondition: has_run()
          const std::string& label() const;                  ///< the command line, for the bar
      private:
          CommandRun* run_ = nullptr;
          std::string label_;
      };
      ```
      It holds a pointer it does not own; the run stays owned by `Workspace` or a screen.

Acceptance: the header compiles on its own (`clang -fsyntax-only` with the include path), and no
other file changed.

### Task 2: The chrome, the rail, and the strip

**Files:** creates `src/ui/chrome/TitleBar.hpp/.cpp`, `src/ui/chrome/NavRail.hpp/.cpp`,
`src/ui/widgets/ActivityStrip.hpp/.cpp`; modifies `src/ui/Shell.hpp`, `src/ui/Shell.cpp`.
**Consumes:** `Theme`, `Screen`, `RunLog` from Task 1.

- [ ] `TitleBar::draw(const std::string& workspace, const std::string& account)` draws one row at
      the top: an accent dot, the words `Sushi Hub`, the version dimmed, the workspace path in a
      bordered chip, and the account at the right. It reads nothing and starts nothing.
- [ ] `NavRail::draw(const std::vector<const char*>& names, std::size_t& active)` draws the rail
      at 11 font-sizes wide: each entry is a full-width selectable with the accent bar on its left
      edge when active, `panel` background on hover, and `ink_dim` text otherwise. It writes the
      chosen index into `active` and returns whether it changed.
- [ ] `ActivityStrip::draw(RunLog& log)` draws the bottom bar at one line: a caret, the label, a
      progress bar filled from the run's `progress` event fraction (full and `ok`-coloured once
      the `result` event arrives), and the exit status at the right. Clicking the bar toggles an
      expanded region of at most eight lines showing the run's events in arrival order, scrolled
      to the newest. The expanded state lives in the strip, not in `Shell`.
- [ ] `Shell` holds the four screens by `std::unique_ptr<Screen>`, a `RunLog`, the chrome and the
      strip. Its `draw()` is: title bar, then a row of rail plus the active screen's region, then
      the strip. It no longer knows any screen's type, no longer keeps `screen_names_` as strings
      it owns alone (the names come from `Screen::name()`), and no longer maps a screen to a
      command.
- [ ] `covered_commands()` keeps its job of hiding what a hand-drawn screen already does; its list
      becomes `doctor`, `license`, `login`, `logout`, `status`, `whoami`.

Acceptance: `Shell` compiles against the four screens' headers with every screen's `draw()` a
stub in the other tasks' files; the coordinator builds once at the end of the wave.

### Task 3: Installs

**Files:** creates `src/ui/screens/InstallsScreen.hpp/.cpp`; deletes `StatusScreen.hpp/.cpp`.
**Consumes:** `Theme`, `Screen`, `Workspace`.

- [ ] The screen reads the run of `hub status` and, when a licence row is present, `hub license`.
- [ ] It draws one card per install, in this order: sushiengine, then Sushi Hub itself. A card
      carries a title with a presence chip, a definition grid of four fields, and its actions on
      the right.
- [ ] sushiengine, cloned: branch, how far ahead or behind, where building happens (`se build`,
      in the terminal), and that no licence is needed. Actions: `Open editor`, `Pull`, `Details`.
- [ ] sushiengine, binary: version, platform, licence expiry, and whether a newer release exists.
      Actions: `Open editor`, `Update`, `Licence`.
- [ ] sushiengine, absent: one line saying which of the two paths is open, and a single action,
      `Install` or `Clone`, matching what `hub add` would choose.
- [ ] Sushi Hub's own card: the command name, the alias, the channel, and whether it is current.
- [ ] `Open editor` starts `se editor` and reads nothing back. It is the only program other than
      `hub` this application starts, and the card says so in a dimmed line.
- [ ] Every action adopts its run into the `RunLog` so the strip reports it.

Acceptance: with the recorded `status.jsonl` fixture, the screen draws two cards and no empty
region; a card whose data has not arrived draws its title and a dimmed "reading…" line.

### Task 4: Modules

**Files:** modifies `src/ui/screens/ModulesScreen.hpp/.cpp`.

- [ ] The screen becomes a list of rows, one per module, drawn in the order `hub status` returns.
- [ ] A row carries the module name, its presence chip (`cloned`, `linked`, `binary`, `absent`),
      one dimmed line of detail underneath (the path and branch, or the version and licence date,
      or that it is open source and can be cloned), and one action at the right: `Clone` for an
      absent module, `Update` for a binary one, `Details` otherwise.
- [ ] Under the list, one note in `warn` colour states what the next clone would provision, using
      the dependency count and size the run reports, and names `hub add --skip-install` as the way
      to defer it. When nothing would be provisioned, the note is not drawn at all.
- [ ] A chip is a rounded rectangle with a 6 px square in the presence colour: `ok` for cloned,
      `info` for linked, `accent` for binary, `ink_faint` for absent.

Acceptance: six rows from the fixture, each with exactly one action, and the note absent when the
fixture reports nothing to provision.

### Task 5: Settings

**Files:** creates `src/ui/screens/SettingsScreen.hpp/.cpp`; deletes `LicenceScreen.hpp/.cpp` and
`DependenciesScreen.hpp/.cpp`.
**Consumes:** the sign-in flow that today lives in `LicenceScreen`, including `DeviceGrant`.

- [ ] Four setting rows, each a three-column grid of title with one dimmed sentence, current
      value, and one control:
      Sushi ID (the account, `Sign in` or `Sign out`), workspace (the path, `Change`),
      the `sh` alias (where it is defined, a toggle), dependencies (how many are ready and how
      many missing, `Provision`).
- [ ] Below them, the doctor table: an index, the dependency and its owner, the note, and the
      state in colour, `ok` for ready, `critical` for missing, `ink_faint` for not needed. The
      order is the order `hub doctor` reports, which is already the dependency order.
- [ ] Sign-in keeps today's behaviour from `LicenceScreen`: the user code at two and a half times
      the text size, and the verification link opened through `Browser`.
- [ ] The alias toggle is drawn but does nothing yet; a dimmed line says the installer writes it.

Acceptance: the four rows and the doctor table draw from the `doctor` fixture, and the sign-in
still reaches `DeviceGrant`.

### Task 6: Commands

**Files:** creates `src/ui/screens/CommandsScreen.hpp/.cpp`.
**Consumes:** `CatalogueSource`, `GeneratedForm`, `FormOpener`.

- [ ] Every `hub` command must be reachable from the window; this screen is where the ones without
      a hand-drawn home live.
- [ ] A search field at the top filters by name and by help text. Under it, the catalogue's
      commands as rows: name in monospace, help dimmed beside it, and `Open` at the right.
- [ ] Opening a command draws its `GeneratedForm` in the right half of the region, the list
      staying on the left. The form keeps what was typed while the user is elsewhere, as it does
      today.
- [ ] Commands in `covered_commands()` are listed but marked, with a dimmed line naming the screen
      that already does it; their `Open` still works.
- [ ] A form's run adopts into the `RunLog`; the form no longer draws its own event log.

Acceptance: with the recorded `describe.json`, every catalogued command appears, the filter
narrows the list, and opening two commands in turn keeps both forms' fields.

### Task 7: Tests and the README

**Files:** modifies `sushihub/gui/tests/*`, `sushihub/gui/README.md`.

- [ ] The existing tests follow the moved code: whatever asserted on `StatusScreen`,
      `LicenceScreen` or `DependenciesScreen` now asserts on the screen that took the job.
- [ ] `RunLog` gets its own test: adopting a run, reading its label, and that `has_run()` is false
      before the first adoption.
- [ ] The README's screen list becomes the four destinations, the strip is described once, and the
      sentence about `Workspace` mapping a screen to arguments goes, since it no longer does.

Acceptance: the test sources compile and the README cites no file that is gone.

## Report

Per task: the files created, modified and deleted, whether the build list needs a line added or
removed, and the syntax check. The coordinator updates `src/CMakeLists.txt`, writes the changelog
line and asks the user for the build:

`hub gui build` then `hub gui run`.

`- 2026-09-07 — Rebuilt the desktop application around a title bar, a four-entry rail and one activity strip (`sushihub/gui/src/ui/Shell.cpp`, `sushihub/gui/src/ui/chrome/`, `sushihub/gui/src/ui/screens/`).`
