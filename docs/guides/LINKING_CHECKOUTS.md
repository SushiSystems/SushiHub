# Linking checkouts that live elsewhere

A workspace does not have to hold its modules. If a module's checkout already exists somewhere
else on the machine, register it instead of cloning a second copy:

```bash
hub link sushiruntime D:/Projects/sushiruntime
hub install-cli sushiruntime            # point `sr` at that checkout
```

`hub link` writes the name and path to `sushihub/cli/modules.local.toml`, which is git-ignored. From then on
`hub status`, `hub update`, `hub sync` and the dependency aggregation treat the linked checkout like a
cloned one: its `cli/sushistack.deps.toml` contributes to what `hub install` provisions, and
`hub update` pulls it.

## Your own sushicore

`sushicore` is not a module; it ships inside this repository and needs no clone. To make every CLI
use a checkout of it that you are editing:

```bash
hub link sushicore /path/to/sushicore
```

Resolution order, first match wins: the `SUSHICORE_DIR` environment variable, a linked path, the
`sushicore/` under the workspace, a sibling checkout next to the workspace. Because the CLIs
receive it as an editable install, edits apply to `hub`, `sr`, `se` and the rest without
reinstalling.

## Undoing a link

There is no `hub unlink` yet. Remove the line from `sushihub/cli/modules.local.toml` and run
`hub install-cli <module>` again so the CLI points back at the workspace copy.
