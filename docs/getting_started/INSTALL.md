# Install

## One command

On a fresh machine the installer puts Python and Git in place if they are missing, clones this
repository, installs `ss` together with the `sushicore` it carries, and provisions the shared
dependency tree under `dependencies/`.

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
python cli/install.py                # install `ss` via pipx, inject sushicore

ss init                              # write the .sushistack marker and .gitignore entries
ss install                           # download toolchains and libraries
ss add all                           # clone every module, or name them: sushiruntime sushiai …

cd sushiruntime && sr build
```

`ss add` installs each cloned module's own CLI. `ss install-cli <module…>` reinstalls one on
demand, for instance after `ss link` pointed a module at a different checkout.

## What `ss install` downloads today

Everything: the intel/llvm SYCL bundle, AdaptiveCpp with the LLVM it builds against, oneAPI and
CUDA, whether or not a module that needs them is present. `ss install --customize` narrows the
selection interactively. Making the selection follow the present modules is on the backlog; see
`../design/REMAINING_WORK.md`.

## Checking the result

```bash
ss status          # which modules are present, and whether dependencies are installed
ss doctor          # tools, compilers and dependencies, with what is missing
```

Failures that are a toolchain's or a vendor's doing rather than this workspace's are collected in
`../reference/KNOWN_ISSUES.md`.
