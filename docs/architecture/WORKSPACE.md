# The workspace

A SushiStack workspace is any directory `hub init` has marked, with module checkouts placed
directly under its root and one shared dependency tree beside them. `hub` installs from PyPI and
carries its own defaults and dependency manifests inside its package, so an empty folder is a
workspace the moment `hub init` runs in it.

```
<workspace>/
  .sushistack/             the workspace's own data, written by `hub init`; git-ignored
    workspace.toml         [workspace] version, [modules] links, [tool] paths
  dependencies/            toolchains, vcpkg, cmake and ninja; git-ignored, filled by `hub install`
  sushiruntime/            added by `hub add sushiruntime`
  sushiblas/               added by `hub add sushiblas`
  sushiai/                 added by `hub add sushiai`
  sushiengine/             added by `hub add sushiengine`
```

A contributor's workspace is a clone of this repository, because the desktop application's source
is here. That root also holds the tracked folders `cli/` (the `hub` command), `gui/` (the desktop
application), `contract/` (the JSON schemas), `tools/` (the checkers) and `docs/`.

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
It builds one thing, the desktop application, through `hub gui build`. Building, testing and
running a module belong to that module's CLI, which shares its machinery through `sushicore` and
keeps its own build policy. The line between the two is drawn in
`../archive/agent/specs/2026-08-25-cmake-driver-design.md`.

## Three forms of presence

A module under the root is *cloned* when it holds `.git`, *binary* when it holds `sushi-release.json`,
and *linked* when `[modules]` in `.sushistack/workspace.toml` points at a checkout elsewhere. Every `hub` command asks
one place, `cli/sushihub/services/presence.py`. A binary install contributes no dependency
fragment and is never pulled; `hub add` fetches its next release. A module CLI finds either kind of
root through `sushicore`'s `ModuleProfile.markers()`.

## The desktop application

`hub` has a second face: a desktop application that reaches every `hub` command, described in
`../../gui/README.md`. The design is `../design/HUB.md`, and what is left of it is in
`../design/REMAINING_WORK.md`.
