# The workspace

A SushiStack workspace is a clone of this repository with module checkouts placed directly under
its root and one shared dependency tree beside them.

```
sushistack/
  .sushistack              workspace marker, written by `ss init`
  sushihub/cli/            the `ss` command and its dependency manifests
  sushihub/gui/            the desktop application
  sushicore/               the shared CLI engine, tracked in this repository
  dependencies/            toolchains, vcpkg, cmake and ninja; git-ignored, filled by `ss install`
  sushiruntime/            added by `ss add sushiruntime`
  sushiblas/               added by `ss add sushiblas`
  sushiai/                 added by `ss add sushiai`
  sushidsp/                added by `ss add sushidsp`
  sushiengine/             added by `ss add sushiengine`
```

## Why the layout is flat

The modules depend on one another: `sushiblas` on `sushiruntime`, `sushiai` on both. Each one's
CMake resolves a dependency by first looking for an installed package and then for a sibling
checkout next to itself (`../sushiruntime`, `../sushiblas`). Keeping every module directly under
the workspace root is what makes that fallback land. The layout is load-bearing, not cosmetic.

## How a module finds the workspace

Every module CLI walks up from the current directory to the `.sushistack` marker, through
`sushicore`'s `ModuleConfig`. From the marker it derives `dependencies/`, and from there the bundled
compiler and vcpkg root (`StackConfig`). A module checked out on its own, with no marker above it,
falls back to a dependency tree of its own; `ss link` lets a workspace adopt such a checkout without
moving it.

## What `ss` owns and what it does not

`ss` owns the marker, the dependency tree, the module checkouts and the module CLIs' installation.
It does not build. Building, testing and running belong to each module's CLI, which shares its
machinery through `sushicore` and keeps its own build policy. The line between the two is drawn in
`../agent/specs/2026-08-25-cmake-driver-design.md`.

## Three forms of presence

A module under the root is *cloned* when it holds `.git`, *binary* when it holds `sushi-release.json`,
and *linked* when `sushihub/cli/modules.local.toml` points at a checkout elsewhere. Every `ss` command asks
one place, `sushihub/cli/sushistack/services/presence.py`. A binary install contributes no dependency
fragment and is never pulled; `ss add` fetches its next release. A module CLI finds either kind of
root through `sushicore`'s `ModuleProfile.markers()`.

## What is coming

The workspace is to gain a second face: a desktop application with a screen for every `ss`
command, under `../../sushihub/gui/`. The design is `../agent/specs/2026-09-05-hub-design.md`; the
order of work is `../design/REMAINING_WORK.md`.
