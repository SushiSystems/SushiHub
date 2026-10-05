# Task 30: hub's raw Rich colours become theme tokens

Branch `feature/theme_tokens`, off `main` at `2f36683`. Plan: `D:/Projects/sushicore/docs/agent/plans/2026-09-21-terminal-components.md`, Wave 8.

## Files changed

- `cli/tests/test_theme_tokens.py` (new)
- `cli/sushihub/cli.py`
- `cli/sushihub/services/customize.py`
- `cli/sushihub/services/setup.py`
- `cli/sushihub/setup/steps.py`
- `cli/sushihub/setup/toolchains.py`
- `docs/reference/CHANGELOG.md`
- this report

## Commands and output

Baseline, before any change:

```
$ cd cli && PYTHONPATH=D:/Projects/sushicore python -m pytest -q
411 passed in 28.15s
```

New test on the unfixed source. One failure, for the stated reason: 36 raw tags (18 opener/closer pairs) found in string constants.

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest -q tests/test_theme_tokens.py
1 failed, 2 passed in 0.12s
  (failing test: test_source_names_no_raw_rich_colour; first offender "cli.py:109  [cyan]", 36 offenders listed)
```

Full suite after the change:

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest -q
414 passed in 7.22s
```

411 before, 414 after: the three tests in `test_theme_tokens.py`.

The task's grep after the change (only bare `[bold]` and the `[bold]` half of nested pairs remain; no colour name):

```
sushihub/cli.py:183:    its licence file, when it does not or when [bold]--binary[/bold] is given.
sushihub/cli.py:185:    provisioned once at the end unless [bold]--skip-install[/bold] is given.
sushihub/cli.py:209:    declares is provisioned afterwards unless [bold]--skip-install[/bold] is given.
sushihub/cli.py:283:    Installs what the present modules declare. Use [bold]--customize[/bold] to add
sushihub/cli.py:329:        help="[bold][error]Wipe everything[/error][/bold]: vcpkg ports, downloaded "
sushihub/cli.py:337:    """Remove provisioned dependencies. Use [bold]--all[/bold] to reclaim the lot."""
sushihub/services/customize.py:91:        console.console.print("[bold]The following dependencies will be downloaded:[/bold]")
sushihub/services/setup.py:54:                    f"[bold][warn]AdaptiveCpp needs LLVM {LLVM_WINDOWS_VERSION} "
sushihub/services/setup.py:55:                    "(a ~2-3 GB download) to build on Windows.[/warn][/bold]\n"
sushihub/setup/toolchains.py:96:        f"[bold]Your choice {hint}[/bold] (auto-"
sushihub/setup/toolchains.py:270:                "them — run [bold][cmd]hub install --refresh-toolchains[/cmd][/bold] "
sushihub/setup/toolchains.py:519:        console.info("Install it anytime with [bold][cmd]sr setup acpp[/cmd][/bold] — "
```

py_compile of every Python file written:

```
$ python -m py_compile tests/test_theme_tokens.py sushihub/cli.py sushihub/services/customize.py sushihub/services/setup.py sushihub/setup/steps.py sushihub/setup/toolchains.py; echo "exit $?"
exit 0
```

Style check on the themed Rich console (a console built from `sushicore.theme.Theme().as_rich_styles()`, forced to standard colour):

```
'\x1b[1;31mWipe\x1b[0m \x1b[36mgit pull\x1b[0m \x1b[2mm\x1b[0m old\n'
```

`[bold][error]Wipe[/error][/bold]` renders bold red, `[cmd]` cyan, `[muted]` dim. The compound `[bold error]old[/bold error]` renders with no style at all: a theme name cannot sit inside a compound tag, which is why the compound openers are nested (see below).

## Replacements

Line numbers are the post-change lines. A docstring line is the line of the tag itself.

| File | Line | Old | New |
| --- | --- | --- | --- |
| `cli/sushihub/cli.py` | 111 | `[cyan].sushistack[/cyan]`, `[cyan].gitignore[/cyan]` | `[cmd].sushistack[/cmd]`, `[cmd].gitignore[/cmd]` |
| `cli/sushihub/cli.py` | 112 | `[cyan]dependencies/[/cyan]` | `[cmd]dependencies/[/cmd]` |
| `cli/sushihub/cli.py` | 227 | `[cyan]cli/[/cyan]` | `[cmd]cli/[/cmd]` |
| `cli/sushihub/cli.py` | 228 | `[cyan]sushicore[/cyan]` | `[cmd]sushicore[/cmd]` |
| `cli/sushihub/cli.py` | 251 | `[cyan]git pull[/cyan]` | `[cmd]git pull[/cmd]` |
| `cli/sushihub/cli.py` | 329 | `[bold red]Wipe everything[/bold red]` | `[bold][error]Wipe everything[/error][/bold]` |
| `cli/sushihub/cli.py` | 368 | `[cyan]gui/build/hub[/cyan]` | `[cmd]gui/build/hub[/cmd]` |
| `cli/sushihub/cli.py` | 401 | `[cyan]--[/cyan]` | `[cmd]--[/cmd]` |
| `cli/sushihub/services/customize.py` | 93 | `[green]•[/green] [green]{key}[/green]` | `[success]•[/success] [success]{key}[/success]` |
| `cli/sushihub/services/setup.py` | 54, 55 | `[bold yellow]…[/bold yellow]` | `[bold][warn]…[/warn][/bold]` |
| `cli/sushihub/setup/steps.py` | 437 | `[green]…[/green]` | `[success]…[/success]` |
| `cli/sushihub/setup/steps.py` | 442 | `[dim]…[/dim]` | `[muted]…[/muted]` |
| `cli/sushihub/setup/steps.py` | 448 | `[yellow]…[/yellow]` | `[warn]…[/warn]` |
| `cli/sushihub/setup/steps.py` | 450 | `[green]…[/green]` | `[success]…[/success]` |
| `cli/sushihub/setup/toolchains.py` | 270 | `[bold cyan]hub install --refresh-toolchains[/bold cyan]` | `[bold][cmd]hub install --refresh-toolchains[/cmd][/bold]` |
| `cli/sushihub/setup/toolchains.py` | 519 | `[bold cyan]sr setup acpp[/bold cyan]` | `[bold][cmd]sr setup acpp[/cmd][/bold]` |

Compound openers (`[bold red]`, `[bold yellow]`, `[bold cyan]`, four sites): the plan maps single names only. I nested them as bold around the token, which keeps the old look and keeps the closing tag following its opener. This is a reading of the mapping, not a line in it; say so if you want them left.

## (a) How each string reaches the terminal

- `cli.py` help text and docstrings: printed by sushicore's help page, which `help_group(console.current)` draws through the sushicore Rich console (`_help_group` is on `app` and `gui_app`, both with `rich_markup_mode="rich"`). `hub init --help`, `hub remove --help` and `hub gui run --help` ran without an unknown-style error and drew the text.
- `customize.py:93`, `steps.py:437-450`: `console.console.print(...)`, the sushicore console's raw Rich console.
- `setup.py:54`: the message goes to `_confirm_timeout` (`setup/toolchains.py`), which prints it with `console.console.print(message)`, or in machine mode passes `Text.from_markup(message).plain` to `console.prompt`.
- `toolchains.py:270`, `519`: `console.warn` and `console.info`, so the renderer's `line`.

Nothing was printed through a plain `rich.print` or a differently built console, so nothing was left. `pipeline.py:145` already used `[header]` and `[warn]`, so the tokens were in use here before this change.

## (b) Machine output

`JsonRenderer` (`sushicore/renderer.py`) does not touch markup. `line` emits `message` as given, and `panel` and `table` emit `body` and `rows` as given. `command` emits `cmd` only. So a tag written into `console.info`/`warn` text appears verbatim in the `line` event, and the old `[bold cyan]` did too.

- `toolchains.py:270` and `519` go through `console.warn`/`console.info`: in `--json` the event text carries `[bold][cmd]hub install --refresh-toolchains[/cmd][/bold]` where it carried `[bold cyan]…[/bold cyan]`. Raw tags reached JSON before and still do; I changed nothing further, as instructed.
- `setup.py:54`: in machine mode the tags are stripped by `Text.from_markup(...).plain`, so no tag reaches the `prompt` event. Unchanged behaviour.
- `customize.py`, `steps.py:437-450`: `console.console.print` in machine mode writes to stderr through a plain, un-themed Rich console. I ran `[success]`, `[warn]` and nested `[bold][warn]` through both the Rich and the JSON `build_console(...)`: no error, the tags are consumed and the text prints. No event carries them.
- `cli.py` text: `--describe` strips markup with `Text.from_markup(text).plain` (`describe.py:28-30`); a `--describe` run printed no `[cmd]`, `[success]` or `[error]`.

## Left, and why

- Bare `[bold]` (about ten sites): stays by the mapping.
- Nothing else. No `magenta`, `white`, `blue`, `italic`, `underline`, `bright_*` or hex tag exists in `cli/sushihub/`. The four compound openers are the only case the mapping did not name.
- `\[y/n]` in `toolchains.py:94`, an escaped bracket, is not a tag and is untouched.

## Not done

- Tests, `gui/`, `contract/`, docs other than the changelog line: untouched, as scoped.
- `hub gui build`, cmake, ctest, ninja: not run.
- Terminal colour output was not looked at by eye; the style check above is a Rich render of the same strings on a themed console.
- The changelog line went under `## Unreleased`, which the release commit left open.
