# Known issues

Some failures are not bugs in this workspace. They are a toolchain, a package manager or a
vendor doing something a reasonable reader would not expect. This page records those, each with
the symptom, the cause and the rule, so the next person recognises one instead of diagnosing it
again. Add an entry whenever a failure turns out not to be the code's fault. Each module keeps its
own page for failures inside its build; this one covers what `ss` provisions.

## Raising the CUDA pin above 12.6 breaks Pascal builds far from the cause

**Symptom.** After the CUDA toolkit is bumped past 12.6, `nvcc --version` succeeds, `ss doctor`
reports the toolkit present, and the CMake configure passes. The build then fails in the ptxas
link step with an unknown-architecture error for `sm_61`.

**Cause.** Pascal (`sm_6x`) is hardware this project is actively developed on, not legacy
support. NVIDIA drops older architectures from ptxas across major releases, and CUDA 13 removed
`sm_6x` outright. SushiRuntime's `SR_CUDA_ARCH` has no default; `cmake/gpu/Cuda.cmake` resolves
it from `nvidia-smi`, so on a Pascal box it resolves to `61` on its own, and only a 12.x toolkit
can compile that. `ensure_cuda_toolkit` in `cli/sushistack/setup/package_managers.py` therefore
installs the pinned `cuda-toolkit-12-6` package, never the unversioned `cuda-toolkit`
meta-package. The same reason drives `_cuda_repo_tag`: NVIDIA's apt repos for Ubuntu releases
newer than 24.04 carry only CUDA 13.x, so an exact distro tag there 404s on the 12.6 package and
the install fails silently. The tag is clamped to `_CUDA126_MAX_UBUNTU_TAG` (`ubuntu2404`), whose
debs run on newer Ubuntu. Multi-arch binaries are a real case too: `SR_CUDA_ARCH` accepts a list
such as `61;86`, so a machine that has moved to Ampere can still ship a Pascal build.

**Rule.** Do not raise or unpin `cuda-toolkit-12-6`, and do not lift the `ubuntu2404` clamp,
without a Pascal build proving the replacement works. A passing `nvcc --version` proves nothing
here.

## Changing a vcpkg port's feature set needs `--recurse`, which `ss install` cannot pass

**Symptom.** A manifest changes a port's features, for example `sdl2` to `sdl2[vulkan]` in
`sushiengine/cli/sushistack.deps.toml`. `ss install` then fails at the vcpkg step: vcpkg refuses
to rebuild the already-installed port with different features and asks for `--recurse`.

**Cause.** vcpkg treats a feature change on an installed port as a removal plus a reinstall of
everything depending on it, and only does that when told to with `--recurse`. `VcpkgManager.install`
in `cli/sushistack/setup/package_managers.py` runs a plain `vcpkg install <port>:<triplet>` with
no way to add that flag, and no `ss install` option exposes it.

**Rule.** After a feature-set change, run the install once by hand with the workspace's vcpkg
(`ss home` prints the `dependencies/` path; the root is `vcpkg_root` in `cli/config.toml` when
set):

```
<dependencies>/vcpkg/vcpkg install sdl2[vulkan]:x64-windows --recurse
```

Then rerun `ss install`; vcpkg's list output now carries the featured port, so the check passes.
Do not remove the plain port to work around it; `--recurse` is the supported path.

## The runtime, engine and CI lanes build against different SYCL toolchains

**Symptom.** A SYCL-level behaviour that holds on a developer's machine fails in CI, or the other
way round, with no change in the code under test.

**Cause.** Three different SYCL toolchains are in use. `ss install` downloads the newest
intel/llvm nightly bundle at the time it runs (`install_intel_llvm` in
`cli/sushistack/setup/toolchains.py`), and the install is then reused forever unless
`--refresh-toolchains` is given, so two developer machines can differ from one another. The
engine's CI job pins a specific nightly by date (`INTEL_LLVM_DATE` in
`sushiengine/.github/workflows/ci.yml`). The runtime's CI job builds inside
`intel/oneapi-basekit:latest` with Intel's packaged `icpx`, a separate libsycl build again.
Runtime and header behaviour differs between these builds in ways the SYCL specification leaves
open, such as whether a particular call allocates.

**Rule.** A contract stated at the SYCL level (allocation freedom, ordering, what a runtime call
may do) is not proven by a local run. It needs CI proof on the lane that ships it, and a claim
that holds on one lane must say which one.
