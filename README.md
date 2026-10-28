# SushiHub

The `hub` command and its desktop application: one install gives a machine every toolchain and
library the SushiStack modules need, in one `dependencies/` directory, and manages the module
checkouts beside it.

```bash
curl -fsSL https://sushisystems.io/install.sh | bash      # Linux / WSL
irm https://sushisystems.io/install.ps1 | iex             # Windows (PowerShell)
hub add sushiengine                                       # check out a module
hub status                                                # what is present
hub doctor                                                # what is missing
```

`hub` is not required to build one module: each module CLI runs the same provisioning through
its own `setup` and `doctor`.

| Path | Holds |
| --- | --- |
| `cli/` | The `hub` command, published on PyPI as `sushihub` |
| `gui/` | The desktop application, a screen for every `hub` command over `hub --json` |
| `contract/` | The JSON schemas both validate against |
| `tools/` | The checkers and the argv recorder |

## Build

```bash
pip install -e "cli[test]"
python -m pytest cli
```

## Status

The CLI installs dependencies and manages checkouts; planned work is in
[`docs/backlog/README.md`](docs/backlog/README.md).

## Documentation

The manual starts at [`docs/README.md`](docs/README.md); install steps are in
[`docs/getting_started/INSTALL.md`](docs/getting_started/INSTALL.md), and how a change lands in
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

## Licence

Source-available, free for non-commercial use under the PolyForm Noncommercial License 1.0.0;
see `LICENSE`. Commercial use needs a licence from Sushi Systems; see `COMMERCIAL.md`.
Third-party parts are listed in `NOTICE.md`. sushihub 0.1.0 and the commits before the one that
replaced `LICENSE` stay available under the Apache License 2.0. The product licence `hub license`
reports is a separate thing, issued by Sushi Account for sushiengine.
