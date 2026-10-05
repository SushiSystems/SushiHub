# Design map

One topic, one document. Look a topic up here before writing; extend the document it names.

| Topic | Document | Status |
| --- | --- | --- |
| `hub` in the terminal and on the desktop, the JSON contract, binary installs of sushiengine, sign-in and licences through Sushi Account | [HUB.md](HUB.md) | Open: waves 6 and 7 |
| The module catalog, the workspace directory, `sushicore` and `sushihub` on PyPI, the module manifest, distribution of the desktop application | [WORKSPACE_DECOUPLING.md](WORKSPACE_DECOUPLING.md) | Open: wave 8 |
| GPU toolkits and Unified Runtime adapters per vendor and operating system | [GPU_BACKEND_PROVISIONING.md](GPU_BACKEND_PROVISIONING.md) | Open: phases R1, E1 and X |

Standalone provisioning, where every module CLI gains `setup`, `doctor`, `link` and `unlink`, is
designed in the SushiCore repository. Its waves are mirrored in
[REMAINING_WORK.md](REMAINING_WORK.md), which is the single backlog.
