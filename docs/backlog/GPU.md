# Gpu

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-30 | P2 | open | Find a SYCL path to AMD integrated GPUs | Mesa rusticl or ROCm with `HSA_OVERRIDE_GFX_VERSION` is tried on Linux, or ruled out; Windows has no path today |  | `docs/design/GPU_BACKEND_PROVISIONING/README.md` | 2026-10-19 |
| RW-31 | P2 | unmeasured | Measure the 7600X's integrated GPU | one kernel timed on the CPU through SYCL and on the iGPU through Vulkan compute shows whether the part is worth a backend |  |  | 2026-10-19 |
| RW-32 | P2 | blocked | Prove GPU backend provisioning on real hardware | a CUDA 13 build, a ROCm install and build on an AMD card, R1's acceptance in the runtime and E1's in the engine have each passed | sushicore RW-12, sushicore RW-14, sushiruntime RW-63, sushiengine RW-306 | `docs/design/GPU_BACKEND_PROVISIONING/README.md` | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
