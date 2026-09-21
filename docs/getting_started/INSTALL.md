# Install

## One command

On a fresh machine the installer puts Python and Git in place if they are missing, clones this
repository, installs `hub`, and provisions the shared dependency tree under `dependencies/`.
`sushicore`, the engine under `hub`, comes from PyPI as an ordinary dependency.

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
git clone https://github.com/sushisystems/sushistack.git
cd sushistack
python sushihub/cli/install.py       # install `hub` via pipx

hub init                              # write the .sushistack marker and .gitignore entries
hub install                           # download what the present modules declare
hub add all                           # clone every module with its toolchains, or name them

cd sushiruntime && sr build
```

`hub add` installs each cloned module's own CLI and then provisions the dependencies the new
modules declare. `hub install-cli <module…>` reinstalls a CLI on demand, for instance after
`hub link` pointed a module at a different checkout.

## Upgrading an install made before 2026-09-22

`sushicore` used to be injected as an editable install pointing at `sushicore/` inside this
checkout. That directory is gone, so **every** pipx environment that carried the injection now
fails at startup with `ModuleNotFoundError: No module named 'sushicore'`. That is `hub` and all
five module CLIs, not just `hub`: `sr`, `se`, `sa`, `sb` and `sd` each hold their own copy of the
dead link.

Repair `hub` first, because the second command is `hub`:

```bash
python sushihub/cli/install.py
hub install-cli sushiruntime sushiengine sushiai sushiblas sushidsp
```

Both resolve `sushicore` from PyPI this time. To check one environment rather than trust it, look
for a dead editable marker:

```bash
ls ~/pipx/venvs/sushiengine-cli/Lib/site-packages/__editable__.sushicore*
```

A hit means that environment still points at the deleted directory; no such file, and a
`sushicore/` directory beside it, means the published package is in place.

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
