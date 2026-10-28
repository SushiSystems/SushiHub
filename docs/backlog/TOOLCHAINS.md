# Toolchains

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-17 | toolchain | A CUDA 13 toolkit breaks a Pascal build far from the cause | set `SUSHISYSTEMS_CUDA_RELEASE` to a release whose `nvcc --list-gpu-arch` lists the card |  |  | 2026-10-19 |
| KI-18 | dependency | Changing a vcpkg port's features needs `--recurse`, which `hub install` cannot pass | run `<dependencies>/vcpkg/vcpkg install sdl2[vulkan]:x64-windows --recurse` once, then `hub install` again; `hub home` prints the folder |  |  | 2026-10-19 |
| KI-19 | toolchain | The runtime, the engine and CI build against different SYCL toolchains | prove a SYCL-level contract on the CI lane that ships it, and say which lane |  |  | 2026-10-19 |
| KI-20 | dependency | iproute2's `ss` shadows a workspace command of that name | the command is `hub`; the installer offers `sh` as an interactive alias |  |  | 2026-10-19 |
