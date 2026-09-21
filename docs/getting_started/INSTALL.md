# Install

## One command

On a fresh machine the installer puts Python and Git in place if they are missing, installs `hub`
from PyPI with pipx, and runs `hub init` and `hub install` in the directory you choose. Nothing is
cloned: a workspace is any directory `hub init` has marked. `sushicore`, the engine under `hub`,
arrives as an ordinary dependency of the same install.

`SUSHISTACK_DIR` names the directory and skips the prompt.

```bash
curl -fsSL https://sushisystems.io/install.sh | bash      # Linux / WSL
```

```powershell
irm https://sushisystems.io/install.ps1 | iex             # Windows (PowerShell)
```

On Windows use `irm` (Invoke-RestMethod), not `curl`. In PowerShell `curl` is an alias for
`Invoke-WebRequest` and does not pipe a script the same way.

Both scripts accept a module list to clone at the end: `install.sh sushiruntime sushiblas`,
`install.ps1 -Add sushiruntime,sushiblas`.

## Step by step

The same result, one command at a time:

```bash
pipx install sushihub                 # or: python -m pip install --user pipx, first

mkdir ~/sushistack && cd ~/sushistack
hub init                              # write the .sushistack directory and .gitignore entries
hub install                           # download what the present modules declare
hub add all                           # clone every module with its toolchains, or name them

cd sushiruntime && sr build
```

`hub add` installs each cloned module's own CLI and then provisions the dependencies the new
modules declare. `hub install-cli <module…>` reinstalls a CLI on demand, for instance after
`hub link` pointed a module at a different checkout.

## There is no desktop application in this install

`hub gui build` and `hub gui run` build `sushihub/gui`, which lives in the SushiStack repository.
An install made the way above never clones it, so those commands have nothing to build. Clone the
repository yourself if you want the application:

```bash
git clone https://github.com/sushisystems/sushistack.git
```

Working on `hub` itself is the same clone, plus `python sushihub/cli/install.py`, which points the
`hub` command at your checkout instead of the published package.

## Upgrading an install made before 2026-09-22

`sushicore` used to be injected as an editable install pointing at `sushicore/` inside this
checkout. That directory is gone, so **every** pipx environment that carried the injection now
fails at startup with `ModuleNotFoundError: No module named 'sushicore'`. That was `hub` and every
module CLI, not just `hub`: `sr`, `se`, `sa`, `sb`, `sd` and `st` each held their own copy of the
dead link.

Repair `hub` first, because the second command is `hub`:

```bash
python sushihub/cli/install.py
hub install-cli sushiruntime sushiengine sushiai sushiblas
```

Both resolve `sushicore` from PyPI this time. `sushidsp` and `sushitrack` left the stack the same
day (see below); reinstall their own CLI directly rather than through `hub`, from each checkout:
`pipx install --force --editable sushidsp/cli` (and the same for `sushitrack/cli`).

To check one environment rather than trust it, look for a dead editable marker:

```bash
ls ~/pipx/venvs/sushiengine-cli/Lib/site-packages/__editable__.sushicore*
```

A hit means that environment still points at the deleted directory; no such file, and a
`sushicore/` directory beside it, means the published package is in place.

### sushidsp and sushitrack left the stack on 2026-09-22

They share no dependency with `sushiruntime`, `sushiblas`, `sushiai` and `sushiengine`, and are
their own products with their own CLIs, `sd` and `st`. `hub add sushidsp` reports an unknown
module: neither is in the catalog, so neither can be cloned by name.

They are not cut off, though. A checkout carrying `sushi-module.toml` is recognised without a
catalog entry, so `hub link sushidsp <path>` works, `hub status` lists it, and `hub install`
provisions what its dependency fragment declares. Each also provisions itself: `sd setup` reports
what it needs and installs it under `--install`, handing the job to `hub install` when a
workspace is there. `st setup` is designed and not yet written; until then `sushitrack` uses
`conda env create -f environment.yml` as its own README says.

Install each CLI from its checkout: `pipx install --force --editable sushidsp/cli`, and the same
for `sushitrack/cli`.

### The workspace moved its data on 2026-09-22

`.sushistack` used to be an empty marker file, with the workspace's data in the checkout at
`sushihub/cli/config.local.toml` and `sushihub/cli/modules.local.toml`. It is a directory now, and
both tables live in `.sushistack/workspace.toml`.

Nothing is asked of you: the first `hub` command run in an old workspace converts it and says so.
The two old files are left where they are, so deleting `.sushistack/` puts you back.

The tool's own defaults and its dependency manifests moved the other way, out of the checkout and
into the `hub` package. A workspace no longer has to be a clone of this repository: `hub init` in
an empty folder is enough.

## What `hub install` downloads

What the modules in the workspace declare. In an empty workspace that is the base fragment
alone: cmake, ninja, gtest, opencl and pkgconf. A toolchain arrives with the module that asks
for it, so `hub add sushiruntime` is what pulls the intel/llvm SYCL bundle, AdaptiveCpp with the
LLVM it builds against and oneAPI. The toolkit for this machine's GPU is the exception: `hub install`
detects the GPU and installs its toolkit without being asked, and on Windows the CUDA installer
asks once for administrator rights. Pass `--skip-install` to `hub add` or `hub link` to defer
that, and `hub install --customize` to add or drop a component by hand, the GPU toolkit included.

## Checking the result

```bash
hub status          # which modules are present, and whether dependencies are installed
hub doctor          # tools, compilers and dependencies, with what is missing
```

Failures that are a toolchain's or a vendor's doing rather than this workspace's are collected in
`../reference/KNOWN_ISSUES.md`.
