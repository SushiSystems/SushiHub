# General

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-1 | P2 | decision | Decide whether the workspace moves out of this checkout | the owner has ruled whether the tree stays both the SushiHub source and a SushiStack workspace; the checkout is `sushistack`, the remote `SushiHub` |  |  | 2026-10-19 |
| RW-2 | P2 | decision | Decide the layout of `gui/`, `contract/` and the installers | the tree follows the `repository-layout` skill, or the skill records the exception |  |  | 2026-10-19 |
| RW-3 | P2 | decision | Decide whether SushiHub carries a `sushi-module.toml` | the owner has ruled; the desktop application's dependencies are in `cli/sushihub/manifests/gui.deps.toml` |  |  | 2026-10-19 |
| RW-4 | P2 | decision | Decide how the desktop application reaches a user | the owner has chosen how `sushihub-gui` is built and distributed |  | `docs/design/WORKSPACE_DECOUPLING/README.md` | 2026-10-19 |
| RW-5 | P2 | decision | Tag v0.2.0 | the owner has tried the hub and tagged `v0.2.0`, which publishes it to PyPI |  |  | 2026-10-19 |
| RW-6 | P2 | decision | Decide where the toolchain known issues live | the CUDA and vcpkg entries of the known issues stay here or move to sushicore, which owns the code they describe |  |  | 2026-10-19 |
| RW-7 | P2 | decision | Decide whether contributions from outside are accepted | the owner has named a contributor agreement, or ruled contributions out |  |  | 2026-10-19 |
| RW-8 | P2 | decision | Decide whether hub takes sushicore's commands | hub's `install`, `doctor` and `link` are sushicore's `setup`, `doctor`, `link` and `unlink`, or the owner keeps them apart |  |  | 2026-10-19 |
| RW-9 | P2 | decision | Decide whether the catalog opens to any Git URL | the owner has ruled whether `hub add <git-url>` reaches a repository nobody has cloned |  |  | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
