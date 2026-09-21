# `sushi-module.toml`

The file a module writes to say what it is. `hub` reads it from a checkout inside the workspace;
when it is absent, `hub` falls back to its own catalog entry for a module it already knows. A
checkout that carries one is recognised whether or not the catalog lists it.

It sits at the **repository root**, beside `CMakeLists.txt`. The dependency fragment lives under
`cli/` because `hub` owns that format; the manifest is the module's own identity and belongs
where a reader looks first.

## The file

```toml
# What this module is. `hub` reads this when the checkout is in a workspace; when it is
# absent, `hub` falls back to its own catalog entry for a module it already knows.

[module]
name = "sushiruntime"                   # the name on the command line and the directory under the root
alias = "sr"                            # the module's own CLI program name
distribution = "source"                 # "source" to clone, "binary" for a compiled release
repo = "https://github.com/sushisystems/sushiruntime.git"
fragment = "cli/sushistack.deps.toml"   # the dependency fragment, relative to this file
```

## The keys

| Key | Required | What it is |
| --- | --- | --- |
| `name` | yes | The name on the command line, and the directory the checkout sits in |
| `alias` | yes | The module's own CLI program name, accepted wherever a name is |
| `distribution` | yes | `source` to clone, `binary` for a module sold as a compiled release |
| `fragment` | yes | Path to the dependency fragment, relative to this file |
| `repo` | no | The git clone URL. A module that is never cloned by name may omit it |

`name` must equal the directory the checkout sits in. Every module's cmake resolves a sibling by
the flat `<workspace>/<module>` layout, so a manifest that disagrees would lie about where the
module is; a reader raises rather than believing it.

## What a reader does with a shape it does not know

A **key** it does not know is ignored, so a newer module can add one without breaking an older
`hub`.

A **table** it does not know is an error that names the file. This is not symmetry for its own
sake. Until 2026-09-22 the dependency fragment's reader skipped every top-level key it could not
read, and `sushidsp`'s whole fragment — a required `sdl2` among it — went unprovisioned without
a word. A section a reader silently drops is a section nobody knows is missing.

`hub` reads this file and never writes it. A module owns its own manifest.

## What the manifest does not do

It does not open the catalog. `hub add <name>` clones from a repo URL it must know *before* any
checkout exists, so a name only a manifest knows cannot be added by name — the manifest
describes a checkout that is already on disk. A module can therefore be known to `hub status`
and unknown to `hub add`, and both commands say so plainly.

## Where it is used

- The catalog it falls back to: `sushihub/cli/sushistack/catalog.toml`.
- The other file a module owns: its dependency fragment at `cli/sushistack.deps.toml`, which
  says what to install rather than what the module is.
- The design behind both: `../design/WORKSPACE_DECOUPLING.md` §3.1 and §3.2.
