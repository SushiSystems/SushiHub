# tools

This repository's side of the shared checkers, which run from the sushicore package with
`python -m sushicore.tools check .`:

| Path | Holds |
| --- | --- |
| `settings.py` | The settings the checkers read for this repository |
| `known_findings.toml` | The findings the checkers accept for now, each with its backlog ID |
| `hooks/pre-commit`, `hooks/commit-msg` | The git hooks; `python -m sushicore.tools install-hooks .` points git at them |

The repository's own tools:

| Path | Does |
| --- | --- |
| `common/checker.py` | Nothing itself; runs a checker's rule table and prints findings | |
| `record_cli_argv.py` | Nothing; records the argv a Sushi CLI would hand to cmake and ctest, so a CLI change is proven without a build | A CLI command line |
