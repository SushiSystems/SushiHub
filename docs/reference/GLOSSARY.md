# Glossary

Words this repository uses in a specific sense.

**Workspace** — a clone of this repository with the `.sushistack` marker at its root, module
checkouts directly under it and one `dependencies/` tree beside them. `docs/architecture/WORKSPACE.md`.

**Module** — one of the stack's buildable repositories: sushiruntime, sushiblas, sushiai, sushidsp,
sushiengine, sushitrack. Each has a CLI (`sr`, `sb`, `sa`, `sd`, `se`, `st`) and a dependency fragment
`cli/sushistack.deps.toml`. `sushicore` is not a module: it is never built and ships inside this
repository.

**Presence** — the form in which a module exists in a workspace, read from disk: *cloned* (a checkout
under the workspace root), *linked* (a checkout elsewhere, registered in `sushihub/cli/modules.local.toml`),
*binary* (a downloaded release whose root holds `sushi-release.json`), or *absent*.
`sushihub/cli/sushistack/services/presence.py` answers it; `hub status` shows it.

**Dependency fragment** — a `*.deps.toml` file naming packages per platform. This repository ships
the base fragment under `sushihub/cli/manifests/`; each module ships its own. `hub install` merges them.

**Toolchain** — a compiler bundle `hub install` downloads into `dependencies/` rather than
installing through a package manager: intel/llvm, AdaptiveCpp, oneAPI. Each carries a stamp naming
the release it came from.

**Sushi Account** — the identity service at `account.sushisystems.io`, built in the sushiweb repository. It
issues the access tokens and holds the licences the hub design relies on.

**Hub** — the name for `hub` as the workspace's one experience: the terminal command and the
desktop application that gives every one of its commands a screen. Not a separate program.

**`hub`** — the terminal command: dependency provisioning and module lifecycle, installed by
`install.sh` or `install.ps1`. The installer offers `sh` as an optional interactive alias, for
typing two letters instead of four; it changes typing only; `/bin/sh` is untouched.

**JSON contract** — the shape of what `hub` prints under `--json`, one event per line, and of what
`hub --describe` says about its own commands. The desktop application consumes it; a schema under
`sushihub/contract/` will bind both sides.
