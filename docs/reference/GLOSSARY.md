# Glossary

Words this repository's documents use in a specific sense.

| Word | Meaning |
| --- | --- |
| SushiHub | The tool: the `hub` command, the desktop application and this repository |
| SushiStack | The applications SushiHub installs, and the workspace that holds them |
| `hub` | The terminal command for dependency provisioning and module lifecycle, installed from PyPI as `sushihub`. The installer offers `sh` as an optional interactive alias, which leaves `/bin/sh` untouched |
| Hub | `hub` as the workspace's one experience: the terminal command and the desktop application that gives each of its commands a screen. One program with two faces, designed in `docs/design/HUB.md` |
| Desktop application | The Dear ImGui program under `gui/`, which spawns `hub --json` and draws the events it reads |
| Component | One of the three folders of this repository that carry code or schemas: `cli/`, `gui/`, `contract/` |
| Workspace | A directory with the `.sushistack` marker directory at its root, module checkouts directly under it and one `dependencies/` tree beside them. See `docs/architecture/WORKSPACE.md` |
| Marker | The `.sushistack` directory `hub init` writes. It holds `workspace.toml`, and every `hub` and module CLI walks up to it |
| Module | A buildable repository `hub` brings into a workspace. The catalog names four: sushiruntime, sushiblas, sushiai, sushiengine. `sushicore` is not a module: it is never built and installs from PyPI |
| Module CLI | A module's own command: `sr`, `sb`, `sa`, `se`. It builds, tests and runs the module, and provisions it through `setup` and `doctor` |
| Catalog | `cli/sushihub/catalog.toml`, the modules `hub add` can clone by name. A checkout's own module manifest wins over its catalog entry |
| Module manifest | `sushi-module.toml` at a module's root, the file a module writes to say what it is. See `docs/reference/MODULE_MANIFEST.md` |
| Presence | The form in which a module exists in a workspace, read from disk: cloned (a checkout under the root), linked (a checkout elsewhere, registered in `[modules]` of `.sushistack/workspace.toml`), binary, or absent. `cli/sushihub/services/presence.py` answers it and `hub status` shows it |
| Binary install | A module directory that holds a downloaded release, recognised by `sushi-release.json` at its root. Only sushiengine has one |
| Dependency fragment | A `*.deps.toml` file naming packages per platform. Each module ships `cli/sushistack.deps.toml`; this package ships `cli/sushihub/manifests/gui.deps.toml` for the desktop application |
| Base fragment | The fragment every workspace gets: cmake, ninja, gtest, opencl and pkgconf. It ships in `sushicore.provision.manifests` |
| Toolchain | A compiler bundle `hub install` downloads into `dependencies/` where a package manager is not used: intel/llvm, AdaptiveCpp, oneAPI. Each carries a stamp naming the release it came from |
| Selection rule | sushicore's rule for which toolchain installs: none when the machine already holds one that provides the capability a module requires, otherwise the first the fragment declares |
| Sushi Account | The identity service at `account.sushisystems.io`, built in the sushiweb repository. It issues the access tokens, the licence tokens and the signed release URLs `hub` asks for |
| Licence | Two things. The licence of this source is PolyForm Noncommercial 1.0.0, in `LICENSE`. The licence `hub license` lists is the product licence Sushi Account issues for sushiengine |
| JSON contract | The shape of what `hub` prints under `--json`, one event per line, and of what `hub --describe` prints. Three schemas under `contract/` fix it for both sides |
| Catalogue | What `hub --describe` prints: every subcommand with its arguments and options. The desktop application generates a form from it |
| Wave | One step of a programme in `docs/design/REMAINING_WORK.md`, naming what it waits on |
| Work folder | `docs/agent/<YYYY_MM_DD>_<WORK_NAME>/`, holding the `SPEC.md`, `PLAN.md` and `REPORT.md` of one piece of agent work |
