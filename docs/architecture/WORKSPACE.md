# The workspace

A SushiStack workspace is any directory `hub init` has marked, with module checkouts placed
directly under its root and one shared dependency tree beside them. It is usually a clone of this
repository, because that is where the desktop application's source lives, but nothing requires it:
`hub` carries its own defaults and dependency manifests inside its package, so an empty folder is
a workspace the moment `hub init` runs in it.

```
sushistack/
  .sushistack/             the workspace's own data, written by `hub init`; git-ignored
    workspace.toml         [workspace] version, [modules] links, [tool] paths
  cli/            the `hub` command's source
  gui/            the desktop application
  dependencies/            toolchains, vcpkg, cmake and ninja; git-ignored, filled by `hub install`
  sushiruntime/            added by `hub add sushiruntime`
  sushiblas/               added by `hub add sushiblas`
  sushiai/                 added by `hub add sushiai`
  sushiengine/             added by `hub add sushiengine`
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
falls back to a dependency tree of its own; `hub link` lets a workspace adopt such a checkout without
moving it.

## What `hub` owns and what it does not

`hub` owns the marker directory and what it holds, the dependency tree, the module checkouts and
the module CLIs' installation.
It does not build. Building, testing and running belong to each module's CLI, which shares its
machinery through `sushicore` and keeps its own build policy. The line between the two is drawn in
`../agent/specs/2026-08-25-cmake-driver-design.md`.

## Three forms of presence

A module under the root is *cloned* when it holds `.git`, *binary* when it holds `sushi-release.json`,
and *linked* when `[modules]` in `.sushistack/workspace.toml` points at a checkout elsewhere. Every `hub` command asks
one place, `cli/sushihub/services/presence.py`. A binary install contributes no dependency
fragment and is never pulled; `hub add` fetches its next release. A module CLI finds either kind of
root through `sushicore`'s `ModuleProfile.markers()`.

## What is coming

The workspace is to gain a second face: a desktop application with a screen for every `hub`
command, under `../../gui/`. The design is `../agent/specs/2026-09-05-hub-design.md`; the
order of work is `../design/REMAINING_WORK.md`.
