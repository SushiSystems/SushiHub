# Frequently asked questions

Short answers about SushiHub and the SushiStack applications it installs: what the parts are,
how they depend on one another, how to get them onto a machine, how the source is licensed and
what is known not to work. Each answer links to the manual page that holds the detail.

## What are SushiStack and SushiHub?

SushiStack is the applications, and the workspace that holds them. SushiHub is the tool that
installs and manages them: the `hub` terminal command, a desktop application that gives each
`hub` command a screen, and the repository that carries both.

`hub` is published on PyPI as `sushihub`. It provisions the toolchains and libraries the
modules need into one `dependencies/` directory and manages the module checkouts beside it.
The [glossary](../reference/GLOSSARY.md) fixes the other words the manual uses.

## Which modules does SushiStack have, and how do they depend on each other?

The catalog names four modules. Each has its own CLI, which builds, tests and runs it.

| Module | Its CLI |
| --- | --- |
| `sushiruntime` | `sr` |
| `sushiblas` | `sb` |
| `sushiai` | `sa` |
| `sushiengine` | `se` |

`sushiblas` depends on `sushiruntime`, and `sushiai` depends on both. Each module's CMake looks
first for an installed package and then for a sibling checkout next to itself, such as
`../sushiruntime`, which is why every module sits directly under the workspace root. See
[The workspace](../architecture/WORKSPACE.md).

`sushicore` is not a module. It is the Python engine under `hub` and every module CLI, it is
never built, and it installs from PyPI. `sushidsp` and `sushitrack` left the stack on
2026-09-22: they are their own products with their own CLIs, `sd` and `st`, and
`hub add sushidsp` reports an unknown module.

## How do I install SushiHub and get all the modules?

Run the installer. It puts Python and Git in place if they are missing, installs `hub` from
PyPI with pipx, and runs `hub init` and `hub install` in the directory you choose. Setting
`SUSHISTACK_DIR` names that directory and skips the prompt.

```bash
curl -fsSL https://sushisystems.io/install.sh | bash      # Linux / WSL
```

```powershell
irm https://sushisystems.io/install.ps1 | iex             # Windows (PowerShell)
```

The installer clones no module unless you pass a list: `install.sh --add "sushiruntime sushiblas"`
or `install.ps1 -Add "sushiruntime sushiblas"`. Afterwards `hub add all` clones every module,
installs each one's CLI and provisions what they declare. [Installing](../getting_started/INSTALL.md)
gives the same steps one command at a time, starting from `pipx install sushihub`.

## Which operating systems does the installer cover?

The manual gives two installer scripts: `install.sh` for Linux and WSL, and `install.ps1` for
Windows PowerShell. It names no other operating system.

On Windows use `irm`, not `curl`. In PowerShell `curl` is an alias for `Invoke-WebRequest` and
does not pipe a script the same way. See [Installing](../getting_started/INSTALL.md).

## What is a workspace, and what does `hub` put in it?

A workspace is any directory `hub init` has marked. `hub init` writes the `.sushistack`
directory, which holds `workspace.toml`, and adds `dependencies/` to `.gitignore`. An empty
folder is enough; a workspace does not have to be a clone of the SushiHub repository.

```
<workspace>/
  .sushistack/workspace.toml   written by `hub init`
  dependencies/                filled by `hub install`
  sushiruntime/                added by `hub add sushiruntime`
  sushiblas/                   added by `hub add sushiblas`
```

Every `hub` and module CLI walks up from the current directory to `.sushistack` and derives
`dependencies/` from it. `hub home` prints the workspace root and the `dependencies/` path.
[The workspace](../architecture/WORKSPACE.md) describes the layout, and
[the `hub` README](../../cli/README.md) lists every file `hub` reads and writes.

## What does `hub install` download?

What the modules in the workspace need to build, into `<workspace>/dependencies`: toolchains,
vcpkg, and portable cmake and ninja. In an empty workspace that is the base fragment alone:
cmake, ninja, gtest, opencl and pkgconf. A toolchain arrives with the module that requires it,
so `hub add sushiruntime` is what brings a SYCL toolchain.

`sushiruntime` declares three toolchains that provide the same capability: intel/llvm,
AdaptiveCpp and oneAPI. One is enough to build. When the machine already holds one,
`hub install` downloads none; otherwise it installs intel/llvm, the first the fragment
declares. `hub install --customize` adds the others.

`hub install` also detects the machine's GPU and installs that vendor's toolkit without being
asked; on Windows the CUDA installer asks once for administrator rights. `hub install --dry-run`
is available, and `--customize` drops the GPU toolkit. See
[Installing](../getting_started/INSTALL.md).

## Do I need `hub` to build a module?

No. A module CLI provisions its own checkout with `setup` and reports on it with `doctor`,
through the same `sushicore` code `hub install` runs. A module checked out on its own, with no
`.sushistack` marker above it, falls back to a dependency tree of its own.

`hub` does that for several checkouts at once and fetches the engine's binary. It builds one
thing itself, the desktop application, through `hub gui build`. Building, testing and running a
module belong to that module's CLI, for example `cd sushiruntime && sr build`.

## How do I add a module, or use a checkout I already have?

`hub add <module>` brings a module into the workspace, installs its CLI and provisions what it
declares. It takes `sushiruntime`, `sushiengine`, `sushiai`, `sushiblas`, their aliases `sr`,
`se`, `sa`, `sb`, or `all`. `--skip-install` leaves the dependencies to a later `hub install`.

If the checkout already exists elsewhere on the machine, register it instead of cloning a
second copy:

```bash
hub link sushiruntime D:/Projects/sushiruntime
hub install-cli sushiruntime            # point `sr` at that checkout
```

`hub link` writes the name and path into `[modules]` in `.sushistack/workspace.toml`. From then
on `hub status`, `hub update`, `hub sync` and `hub install` treat the linked checkout like a
cloned one. A checkout that carries `sushi-module.toml` is recognised without a catalog entry,
so `hub link sushidsp <path>` works, but a name only a manifest knows cannot be added with
`hub add`. See [Linking checkouts](LINKING_CHECKOUTS.md) and the
[module manifest](../reference/MODULE_MANIFEST.md).

## Is sushiengine available, and how do I get it?

`sushiengine` is sold; the other three modules are not. `hub add sushiengine` first asks the
private repository whether this machine's Git identity reaches it. If it does, the module is
cloned like any other. If it does not, `hub` needs a Sushi Account session: with one it
downloads the release, and without one it names both ways in and stops. `hub add sushiengine
--binary` goes straight to the release.

`hub login` opens the session. It prints a device code, opens the Sushi Account page in the
browser, waits for you to approve it there, and stores the session in the operating system's
credential store. `hub license` then prints one row per product licence on the account.

A release brings its own `sushiruntime` and `sushiblas`, so nothing is provisioned after it and
no SYCL toolchain is downloaded; `se` arrives inside the package. `hub` writes the product
licence token beside it as `sushi-licence.jwt`, which the engine reads at start-up and verifies
offline. The detail is under "Signing in" and "Binary installs" in
[the `hub` README](../../cli/README.md).

## How is SushiHub licensed, and can I use it at work?

The source in the SushiHub repository is source-available under the PolyForm Noncommercial
License 1.0.0, free for non-commercial use. [`LICENSE`](../../LICENSE) is the binding text and
lists the permitted purposes: personal, non-commercial use, and use by the non-commercial
organisations it names.

Any commercial purpose needs a separate, paid licence from Sushi Systems. That includes use
inside a company, use in paid client work, and use in a product or service that is sold.
[`COMMERCIAL.md`](../../COMMERCIAL.md) says how to ask: write to `hello@sushisystems.io` with
what you want to build and who will use it. `sushihub` 0.1.0 on PyPI and the commits before the
one that replaced `LICENSE` were published under the Apache License 2.0 and stay available
under it.

This is the licence of the source. The licence `hub license` reports is a different thing: the
product licence Sushi Account issues for `sushiengine`.

## What does not work yet?

[Known issues](../reference/KNOWN_ISSUES.md) lists the open defects with the file each sits in.
The ones a new user meets first:

- v0.2.0 has its release commit of 2026-10-07 and no tag, so it is not published; PyPI serves
  0.1.0. The changelog lists `hub migrate` under Unreleased.
- `hub gui build`, `test`, `run` and `clean` are listed for every user and work only when the
  workspace root is a clone of the SushiHub repository. An install made with the installer
  never clones it, so there is no desktop application in that install until you run
  `git clone https://github.com/SushiSystems/SushiHub.git`.
- There is no `hub unlink`. To undo a link, remove the line from `[modules]` in
  `.sushistack/workspace.toml` and run `hub install-cli <module>` again.
- Under `hub --json`, git and pipx write plain text into the event stream.
- After a vcpkg port's feature set changes, `hub install` fails at the vcpkg step, because it
  cannot pass `--recurse`. The same page gives the command to run by hand.

## Can I contribute a change?

Not yet. [Contributing](../CONTRIBUTING.md) says contributions from outside Sushi Systems are
not accepted.

Cloning the repository is still how you work on `hub` or get the desktop application's source.
After the clone, `python cli/install.py` points the `hub` command at your checkout instead of
the published package.
