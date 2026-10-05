# CI red diagnosis, 2026-09-22

Status: diagnosis only, no fix applied.

## Verified: the run everyone sees red on is blocked before it starts

`gh api repos/:owner/:repo/actions/runs/35276022837/jobs` lists all 13 jobs completed in 3-4
seconds with an empty `steps` array. `gh api repos/:owner/:repo/check-runs/<job id>/annotations`
on three of them (`hub (ubuntu-latest, 3.10)` id `105386741019`, `sushicore (windows-latest,
3.10)` id `105386741172`, `Consumer CLI contract (sushiengine)` id `105386741209`) returns the
same message on each:

```
The job was not started because recent account payments have failed or your spending limit
needs to be increased. Please check the 'Billing & plans' section in your settings
```

The same check on run `35086543836` (2026-09-16, job `104762583676`) returns the identical
message. `gh run list --limit 10` shows every run from 2026-09-15 22:49 onward completing in
2-3 seconds across all 13 jobs — the signature of a run that never got a runner. This is the
proximate cause of the CI you are looking at today: GitHub is refusing to start any job on this
repository over an account billing or spending-limit problem, which sits outside the workflow
file and outside any of the three repositories' code. Nothing in `.github/workflows/ci.yml`
causes it and nothing in it can fix it — it is settled in the organization's GitHub billing
settings, not in this repository.

## Verified: the last run that actually executed (2026-09-14) was not clean either

Two runs on 2026-09-14 ran real jobs for real seconds: `34849695918` (13:30, 34-53s per job) and
`34902765292` (22:10, 9-45s per job). Both predate the billing lockout — `35032828222`
(2026-09-15 22:49) is the first run showing the 2-3-second pattern. So the billing block started
between 2026-09-14 22:10 and 2026-09-15 22:49, and it is masking three separate, still-present
bugs that were already failing jobs before it hit. I confirmed each from
`gh run view 34902765292 --log-failed --job <id>` and each check run's annotations.

### `sushicore`: a Linux-only test bug, not a code bug — two of four jobs actually passed

In run `34902765292`, `sushicore (windows-latest, 3.10)` and `sushicore (windows-latest, 3.11)`
both show `conclusion: success`. Only the two `ubuntu-latest` jobs failed, with:

```
FAILED sushicore/tests/test_discovery.py::test_resolve_finds_an_explicit_target
FAILED sushicore/tests/test_discovery.py::test_resolve_falls_back_to_the_default_when_no_target_is_given
FAILED sushicore/tests/test_discovery.py::test_resolve_with_sort_returns_select_choice_even_though_target_also_matches
3 failed, 84 passed in 0.24s
```

The cause: `sushicore/tests/test_discovery.py:20-24`, the `_exe()` helper, creates a file with
`path.write_text("")` and no execute bit, on the stated assumption that `_is_executable`
"recognizes [it], regardless of platform." `sushicore/sushicore/discovery.py:60-63` actually
branches on platform: on Windows it accepts any file with a `.exe` suffix, but on Linux
(`sushicore/sushicore/discovery.py:63`) it requires `os.access(path, os.X_OK)`. A file written
by `write_text` carries no execute permission, so `_is_executable` returns `False` on Linux and
`resolve()` returns `None` where the test expects a path. This is why the user's local run (a
Windows machine) shows 94 passed: the bug only reaches Linux CI. The fix belongs in
`sushicore/tests/test_discovery.py:20-24` — set the execute bit (e.g. `path.chmod(0o755)`) after
writing the file, or in `sushicore/sushicore/discovery.py:47-63` if the intended contract is
suffix-based matching on every platform. That is a design choice, not mine to make here.

### `hub`: `click` imported but never declared, invisible locally because it is already installed

`hub (windows-latest, 3.10)` (and, by the same install log pattern, every `hub` job) fails
collection with:

```
sushihub\cli\sushistack\describe.py:12: in <module>
    import click
E   ModuleNotFoundError: No module named 'click'
```

`sushihub/cli/sushistack/describe.py:12` imports `click` directly, but
`sushihub/cli/pyproject.toml`'s `dependencies` list (lines 10-15: `typer`, `rich`, `keyring`,
`tomli`) never names it. The pip install log for the same job shows `typer-0.27.2` installed
without pulling in `click` as a transitive dependency — so nothing in a fresh CI virtualenv
provides it. Locally, `python -m pip show click` resolves to `C:\ProgramData\Miniconda\Lib\
site-packages`, installed independently of this project (required by `typer-slim` and
`anaconda-cli-base` in that environment), which is why `pytest sushihub/cli/tests` passes on the
user's machine and nowhere else. The fix belongs in `sushihub/cli/pyproject.toml`'s
`dependencies` list — add `click` as a direct dependency, since `describe.py` imports it
directly and cannot rely on a version of `typer` that happens to carry it.

### `Consumer CLI contract`: the five consumer repositories are private, and `GITHUB_TOKEN` cannot see them

`Consumer CLI contract (sushiai)` fails at the checkout step for the consumer, before any pytest
step runs:

```
repository 'https://github.com/SushiSystems/SushiAI/' not found
The process '/usr/bin/git' failed with exit code 128
```

`.github/workflows/ci.yml:116-118` documents the assumption behind this checkout: "Public under
SushiSystems, so the default GITHUB_TOKEN reads it." `gh repo list SushiSystems` shows otherwise
— `SushiRuntime`, `SushiEngine`, `SushiAI`, `SushiBLAS`, and `SushiDSP` are all listed `private`.
The default `GITHUB_TOKEN` GitHub Actions issues is scoped to the triggering repository only; it
cannot read a sibling private repository, which is exactly the "not found" GitHub returns for a
private repo an unauthorized token cannot even confirm exists. The fix is a token or workflow
change, not a one-line diff I can point at with confidence — a PAT or GitHub App with read
access to the five consumer repos, stored as a secret and passed to `actions/checkout@v4`'s
`token:` input at `.github/workflows/ci.yml:123-127`, or making the five repositories public if
that matches intent. Which one is a call for the repository owner, not this report.

This checkout failure is what actually stops these jobs; it happens before the
`working-directory`/`sushihub/cli/tests` mismatch the user already found at
`.github/workflows/ci.yml:145` (the consumer repos have `cli/tests`, not `sushihub/`) ever gets
a chance to run. Once the checkout is fixed, line 145 will still need to change to
`cli/tests` — both bugs are real and stacked, checkout first.

## Not determined

- The exact GitHub account/organization spending-limit state — I have no billing access from
  this tool. `gh api repos/:owner/:repo/actions/runs/<id>` and the check-run annotations are as
  far as `gh` reaches; resolving it needs a human in the organization's Settings > Billing &
  plans.
- Whether `sushicore`'s Linux failure, `hub`'s missing `click`, and the consumers' private-repo
  checkout were already broken before 2026-09-14, or introduced by a commit that day. I only
  confirmed they were live in the last two runs that executed jobs; I did not bisect further
  back, since the task's scope was the current red state, not its full history.
- Whether the five consumer repositories were made private on purpose or the CI workflow's
  claim that they are public is simply stale.

## Summary by job group

| Group | Immediate blocker on the run you're looking at | Underlying bug, confirmed on the last run that actually executed | File / line to change |
| --- | --- | --- | --- |
| `sushicore` (4 jobs) | Billing lockout, all four | Linux-only: test helper writes a non-executable file | `sushicore/tests/test_discovery.py:20-24` (or `sushicore/sushicore/discovery.py:47-63` if the contract itself should change) |
| `hub` (4 jobs) | Billing lockout, all four | `click` imported directly, never declared as a dependency | `sushihub/cli/pyproject.toml` dependencies list (lines 10-15) |
| `Consumer CLI contract` (5 jobs) | Billing lockout, all five | Consumer repos are private; default `GITHUB_TOKEN` can't check them out | `.github/workflows/ci.yml:123-127` (token), plus the already-known path bug at line 145 |
