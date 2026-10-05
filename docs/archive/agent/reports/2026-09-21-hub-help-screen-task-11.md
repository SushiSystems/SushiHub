# Task 11: hub groups its commands and adds examples

Every hub command and test below ran with `PYTHONPATH=D:/Projects/sushicore`, so the sushicore 0.4.0
checkout wins over the 0.3.0 in site-packages. Nothing was installed or upgraded. Nothing was committed
or staged.

## Files changed

- `sushihub/cli/sushistack/console.py`: added `current()`, which returns `_lazy.get()`.
- `sushihub/cli/sushistack/cli.py`: `help_group(console.current)` is the `cls` of both Typer apps; five
  panel constants (`K_WORKSPACE`, `K_MODULES`, `K_DEPENDENCIES`, `K_DESKTOP_APP`, `K_ACCOUNT`); every
  top-level command carries `rich_help_panel` and `epilog`; the `gui` sub-app is added with
  `rich_help_panel=K_DESKTOP_APP`; the four `gui` commands carry `epilog`. The working copy keeps its CRLF
  line endings.
- `sushihub/cli/tests/test_help_screen.py`: new, 9 tests.

## Baseline

Command, from `D:/Projects/sushistack/sushihub/cli`, before any change:

```
PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 55%]
........................................................................ [ 73%]
........................................................................ [ 92%]
..............................                                           [100%]
390 passed in 6.85s
```

No test was failing before I started.

## Test first

The new file, run before the implementation (the assertion text is Typer's own help page, which has
no `Workspace` heading and no `Examples` section):

```
E       ValueError: 'Workspace' is not in list
E       KeyError: 'Workspace'
E       KeyError: 'Modules'
E       KeyError: 'Dependencies'
E       KeyError: 'Desktop app'
E       KeyError: 'Account'
E       AssertionError: assert ('Examples' in '   ... Usage: hub add [OPTIONS] MODULES......
FAILED tests/test_help_screen.py::test_root_help_shows_the_five_groups_in_order_of_first_appearance
FAILED tests/test_help_screen.py::test_every_command_sits_under_its_own_group[Workspace]
FAILED tests/test_help_screen.py::test_every_command_sits_under_its_own_group[Modules]
FAILED tests/test_help_screen.py::test_every_command_sits_under_its_own_group[Dependencies]
FAILED tests/test_help_screen.py::test_every_command_sits_under_its_own_group[Desktop app]
FAILED tests/test_help_screen.py::test_every_command_sits_under_its_own_group[Account]
FAILED tests/test_help_screen.py::test_no_command_is_listed_under_a_group_it_does_not_belong_to
FAILED tests/test_help_screen.py::test_a_command_help_carries_examples - Asse...
FAILED tests/test_help_screen.py::test_a_gui_command_help_carries_examples - ...
9 failed in 0.34s
```

## After

```
PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 54%]
........................................................................ [ 72%]
........................................................................ [ 90%]
.......................................                                  [100%]
399 passed in 6.54s
```

390 old tests still pass, plus the 9 new ones.

Syntax check (no C++ or GLSL here; the task replaced it with `py_compile`):

```
python -m py_compile sushistack/cli.py sushistack/console.py tests/test_help_screen.py; echo "exit $?"
exit 0
```

## `hub --describe` is unaffected

Besides the existing `test_describe.py` passing, I ran `python -m sushistack.cli --describe` against a
copy of the package with `cli.py` and `console.py` taken from `HEAD`, and against the working tree. The
`commands` arrays are equal (`a["commands"] == b["commands"]` is `True`). The only difference in the whole
document is `"version": "0"` in the copy against `"0.1.0"` in the tree, because the copy is not the
installed distribution.

`hub --help` and `hub gui build --help` also run with `SUSHISTACK_HOME` unset and the current directory
outside a workspace: both draw the grouped page and the Examples section.

## Examples checked against the real options

Each example was compared with the signatures in `cli.py` and the command table in
`sushihub/cli/README.md`. All of them name options and arguments the commands have: `--dry-run`,
`--binary`, `--check-updates`, `--customize`, `--all`, `--type release` (`BuildType` holds `debug`,
`release`, `relwithdebinfo`), `--clean`, `--filter`, `--repeat`; the aliases `sr` and `se` exist in
`catalog.toml`. None was dropped or changed from the plan.

## What the owner sees

`hub --help`, `hub add --help`, `hub gui build --help`, in-process with `CliRunner`, against a
`sushicore.Console` whose Rich console is an 80-column truecolour terminal and `dark_background=True`.
Colour codes are stripped (Click's `CliRunner` strips them from `result.output` itself; the logo appears
because the page checks the console, not the runner's stream). The script is in the scratchpad, not the
repository.

```
$ hub --help
     ▄▄▀▀▀▀▀▀▀▀▄      ▄█▀▀▀▀ ██  ██ ▄█▀▀▀▀ ██  ██ ██
   ▄▀▀▀▀▀▀▀▀▀██▀▀▄    ▀█▄▄▄  ██  ██ ▀█▄▄▄  ██▄▄██ ██
  ▄▀▀██▀▀▀▀▀██▀████       ██ ██  ██     ██ ██  ██ ██
  ███████████▀██████  ▀▀▀▀▀   ▀▀▀▀  ▀▀▀▀▀  ▀▀  ▀▀ ▀▀
  ██████████████████   ▄▄▄▄▄ ▄▄  ▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄    ▄▄  ▄▄▄▄▄
  █████▀▀██▀▀████▀▀▀  ██     ▀█▄▄█▀ ██       ██   ██     ███▄▄███ ██
   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀     ▀▀▀█▄   ██    ▀▀▀█▄   ██   ██▀▀   ██ ██ ██  ▀▀▀█▄
     ▀▀▀▀▀▀▀▀▀▀▀      ▄▄▄▄█▀   ██   ▄▄▄▄█▀   ██   ██▄▄▄▄ ██    ██ ▄▄▄▄█▀

hub
SushiStack CLI — one shared dependency tree and module manager for the stack.

Usage: hub [OPTIONS] COMMAND [ARGS]...

Workspace
  init    Turn the current directory into a SushiStack workspace.
  home    Print the resolved workspace root and dependency directory.
  status  Show which modules are cloned and whether dependencies are present.

Modules
  add          Bring one or more stack modules into the workspace, with what
               they need.
  link         Register an existing checkout (outside the workspace) as a
               module.
  install-cli  Install a module's developer CLI into an isolated pipx venv.
  update       Bring the workspace and every present module up to date.
  sync         Bring the workspace up to date: install missing deps, then update
               modules.

Dependencies
  install  Provision the shared dependencies into the workspace's dependencies/
           tree.
  doctor   Inventory tools, compilers, and dependencies; report what is missing.
  remove   Remove provisioned dependencies.

Account
  login    Sign in to Sushi Account and keep the session in the credential
           store.
  logout   Forget the stored Sushi Account session on this machine.
  whoami   Print the Sushi Account this machine is signed in as.
  license  Print the licences the signed-in Sushi Account holds.

Desktop app
  gui  Build, test and run the desktop application under sushihub/gui.

Options
  --json                One JSON event per line on stdout; nothing else there.
  --describe            Print the command catalogue as JSON and exit.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.

$ hub add --help
hub add
Bring one or more stack modules into the workspace, with what they need.

Five of the six are cloned. sushiengine is cloned when this machine's Git
identity reaches its repository, and downloaded as a compiled release, with its
licence file, when it does not or when --binary is given. Each module that
arrives by clone brings its own dependencies; they are provisioned once at the
end unless --skip-install is given.

Usage: hub add [OPTIONS] MODULES...

Arguments
  MODULES...  Modules to bring in: sushiruntime | sushiengine | sushiai |
              sushiblas | all.  [required]

Options
  --dry-run       Show, don't clone or install.
  --skip-install  Do not run the dependency install afterwards.
  --binary        Install sushiengine from its release even when its source is
                  in reach.
  --help          Show this message and exit.

Examples
  hub add sr             Bring sushiruntime in
  hub add all --dry-run  Show the plan only
  hub add se --binary    Install sushiengine from its release

$ hub gui build --help
hub gui build
Configure and compile the desktop application.

Builds into sushihub/gui/build/hub under the Visual Studio environment on
Windows, against the vcpkg tree `hub install` provisions.

Usage: hub gui build [OPTIONS]

Options
  --type [debug|release|relwithdebinfo]  The configuration to build.  [default:
                                         debug]
  --clean                                Remove the build tree before
                                         configuring.
  -D VAR=VALUE                           Extra cmake cache entry; repeatable.
  --help                                 Show this message and exit.

Examples
  hub gui build --type release
  hub gui build --clean
```

## Where `[cli]` lives

`LazyConsole(legacy_cli_dir)` layers two files from `legacy_cli_dir()`, `config.toml` then
`config.local.toml`. `legacy_cli_dir()` is `workspace_root() / "sushihub" / "cli"`. With
`SUSHISTACK_HOME=D:\Projects\sushistack`, which is set in this session, it resolves to:

```
D:\Projects\sushistack\sushihub\cli
```

- `config.toml` does not exist there.
- `config.local.toml` exists (1049 bytes, dated 2026-09-14, git-ignored by `/sushihub/cli/config.local.toml`).
  Its top-level tables are `[tool.toolchain]` and `[tool.windows]`. It has no `[cli]` table.
- `config.local.toml.bak` beside it has the same size and the same tables.

The owner adds `[cli]` with `background = "dark"` to `config.local.toml`, which is per machine and
untracked. I created and changed nothing there.

## Plan findings

1. The group order in the plan and in the brief is wrong. The plan's test expects
   Workspace, Modules, Dependencies, Desktop app, Account. Typer lists registered commands first and
   registered sub-apps after them, whatever the order of the calls, so `gui` always comes last and the
   measured order is Workspace, Modules, Dependencies, Account, Desktop app. The test expects the
   measured order. Getting the plan's order would need a custom ordering in `HelpGroup`, which is a
   sushicore change; the owner decides whether the measured order is acceptable.
2. The plan's `assert f"  {name}" in out` is too weak: it also matches a description or an option row.
   The test I wrote reads the page into heading and rows and asserts each command sits under its own
   heading, and that each heading holds exactly its commands.
3. The plan's parse would also have counted the `Options` rows (`--json`, `--describe`) under the last
   group; the helper resets on every unindented line.

## Not done

- No changes to `pyproject.toml`, `README.md`, `CHANGELOG.md`, `sushihub/contract/`, `sushihub/gui/` or
  sushicore, as instructed. `pyproject.toml` still says `sushicore>=0.3.0`, so a fresh install of the
  package would not get `sushicore.typer_help` until the orchestrator raises the bound.
- A bare `hub` (no arguments) prints the same page through `ctx.get_help()`; I did not run it separately,
  sushicore's own test covers it.
- Nothing was run on a real terminal; the screens above come from the fake 80-column terminal.
- No `clang`/`shader_compiler` check applies to this Python-only change.
