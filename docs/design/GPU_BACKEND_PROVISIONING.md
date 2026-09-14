# GPU backend provisioning: one brick per vendor, one branch per operating system

**Status:** P1 through P4 built. `backend.py`, `registry.py`, `compiler_identity.py`,
`adapter_builder.py` and `provisioning.py` exist under
`sushihub/cli/sushistack/setup/gpu_backends/`, alongside the vendor specs `cuda.py`, `rocm.py`
and `level_zero.py`, each importing shared apt helpers from `sushihub/cli/sushistack/setup/apt.py`.
`setup/steps.py` calls `provision_gpu_adapters` after the SYCL toolchains on both Windows and
Linux. `hub install` has not yet been run against this wiring on real hardware. R1 onward (§7)
are open. The need comes from
SushiEngine's `docs/design/SYCL_VULKAN_INTEROP.md` §10 and the spike in its
`docs/agent/reports/2026_09_14_CUDA_ADAPTER_SPIKE.md`.

## 1. The problem

A SYCL build reaches a GPU when three things are true on the machine: the vendor's toolkit is
installed, the SYCL runtime has the vendor's Unified Runtime adapter, and the compiler is told
where the toolkit lives. Today each of the three is answered in a different place, for one vendor
and one operating system at a time:

- `install_intel_llvm` downloads a bundle whose Windows build ships no CUDA adapter.
- `ensure_cuda_toolkit`, `ensure_rocm` and `ensure_intel_gpu_runtime` are apt code, dispatched by an
  `if vendor ==` chain in `install_gpu_stack`, and `_run_windows` never calls it.
- SushiRuntime's `cmake/gpu/DetectGpu.cmake` looks for `nvcc` and `hipcc` on Linux prefixes only.

Adding a vendor or an operating system touches all three places and every chain in them.

## 2. The contract

A GPU backend answers three questions, and nothing outside the backend asks them another way.

| Question | Answer |
| --- | --- |
| Where is the toolkit? | `locate(platform)` returns an install root or nothing. |
| Which adapter makes the SYCL runtime reach it? | The Unified Runtime CMake option, the extra configure definitions naming the toolkit root, and the binaries the build produces. |
| What does the compiler need? | The flags that point it at the toolkit, emitted by the backend's own CMake strategy file. |

A backend that has no answer for a platform says so; it does not pretend. Every loop over
backends treats "not provided on this platform" as an ordinary outcome, not an error.

## 3. SushiStack

A package `sushihub/cli/sushistack/setup/gpu_backends/`, one responsibility per file.

| File | Holds |
| --- | --- |
| `backend.py` | `ToolkitInstall` (root, version), the `ToolkitLocator` protocol with `locate(cfg) -> ToolkitInstall \| None` and `provision(cfg, dry_run) -> bool`, and the frozen `GpuBackendSpec`: vendor name, the vendor key `probe.py` reports, locator, adapter option, adapter configure definitions from a toolkit root, adapter binaries. |
| `cuda.py` | The CUDA spec. A Windows locator reading `CUDA_PATH`, the same variable SushiRuntime's CMake locator reads, reporting and never installing; the Linux locator, which is today's apt code moved here unchanged. |
| `rocm.py` | The ROCm spec, adapter option `UR_BUILD_ADAPTER_HIP`. The Linux locator is today's `ensure_rocm`; the Windows locator reports "not provided". |
| `level_zero.py` | The Level Zero spec, adapter option `UR_BUILD_ADAPTER_L0`. The Linux locator is today's `ensure_intel_gpu_runtime`; the Windows locator reports "not provided". |
| `registry.py` | `BACKENDS`, the ordered tuple of specs, and `backend_for_vendor(vendor)`. |
| `adapter_builder.py` | Builds one spec's adapter for one compiler commit: sparse fetch of `unified-runtime/` at that commit into a short build directory under `dependencies/build/`, configure with only that adapter on, build its target, copy the binaries into the toolchain's `bin/`, and record the commit in the toolchain stamp through `toolchains.py`, which owns the stamp format. Skips when the stamp already names that commit for that vendor. Vendor-agnostic: it reads the spec and nothing else. |
| `compiler_identity.py` | Reads the intel/llvm commit from `clang++ --version` of an installed toolchain. |
| `provisioning.py` | `provision_gpu_adapters`: reads the installed toolchain's commit once, then asks every registered spec's locator for its toolkit and hands a found one to `adapter_builder.build`. Reports every outcome through console and never raises. |

`install_gpu_stack` becomes a registry lookup and a `provision` call. The Windows and Linux install
steps both run one loop after the toolchains: for every backend whose locator finds a toolkit,
build its adapter for the installed compiler. The adapter build needs the MSVC environment on
Windows, which it takes from the same `vcvars64.bat` environment snapshot the desktop
application's build uses, once per install run.

The registry holds one backend per probed vendor, so two backends for one vendor, such as Level
Zero and OpenCL for Intel, need the lookup to return a tuple first.

Adding a backend is a new spec file and one line in `registry.py`. A test registers a fake spec and
proves the loop and the builder handle it without any other edit.

## 4. SushiRuntime

Each vendor gains a locator file beside its strategy file, `cmake/gpu/locate/<Vendor>Toolkit.cmake`,
holding one function of the same name shape: `sushiruntime_gpu_locate_cuda_toolkit`,
`sushiruntime_gpu_locate_rocm_toolkit`, `sushiruntime_gpu_locate_intel_toolkit`. It returns the
toolkit root, or nothing, and a description of what it searched, with its operating system
branches inside the file. `DetectGpu.cmake` publishes the root as `SR_<VENDOR>_TOOLKIT_ROOT`. The
CUDA function reads `CUDA_PATH` on Windows and keeps today's prefixes on Linux.

`DetectGpu.cmake` calls the locate function of every vendor in `SR_GPU_VENDORS` in one loop and
stops naming `nvcc` or `hipcc`. A vendor strategy file also publishes the compiler flags that need
the root, such as intel/llvm's `--cuda-path`, into `gpu/GpuBackend.cmake`'s accumulators.

`cli/sushiruntime/config.py`'s bundle search looks for `llvm-sycl` before `llvm-sycl-nightly`, so the
runtime and the engine build with one compiler.

## 5. SushiEngine

`cmake/Install.cmake` stages a `umf` role beside `sycl`, `adapter`, `loader` and `hwloc`, because the
CUDA adapter imports `UMF.dll`. The adapter itself already matches the `adapter` role. The CUDA
adapter imports only `nvcuda.dll` and `nvml.dll` from CUDA, both shipped with the driver, so no
CUDA toolkit binary is staged.

## 6. Failure

- A locator that finds no toolkit makes its backend absent. The install continues and reports it.
- An adapter build that fails warns and leaves the toolchain as it was. The CPU path still works.
- A toolchain whose commit cannot be read skips every adapter build with one warning.
- CMake detection stays authoritative: a toolkit the installer found but CMake cannot locate
  resolves to `cpu`, and the configure message names the variable it looked for.

## 7. Phases

| Phase | Content | Exit |
| --- | --- | --- |
| P1 | `backend.py`, `registry.py`, `compiler_identity.py`, and the fake-spec tests | the registry and identity tests pass |
| P2 | `cuda.py`, `rocm.py`, `level_zero.py`, with today's Linux code moved in unchanged | the existing Linux behaviour is identical; Windows CUDA locator tests pass |
| P3 | `adapter_builder.py` and its tests with a fake runner | the builder test passes for the CUDA spec and the fake spec |
| P4 | Install step wiring on Windows and Linux; docs | landed; `hub install` on the RTX 3080 Ti puts `ur_adapter_cuda.dll` and `umf.dll` in `llvm-sycl/bin`, not yet run |
| R1 | SushiRuntime locate functions, `DetectGpu.cmake` loop, `--cuda-path`, bundle order, docs | `sr build` reports `SR_GPU_BACKEND_RESOLVED=cuda`; `Unit_NvidiaTopologyTest` runs and passes |
| E1 | SushiEngine `umf` staging role | `se build` stages `umf.dll`; the interop device-tier test runs |
| X | ROCm or Level Zero filled on real hardware | its locator bodies and one test; no other file changes |
