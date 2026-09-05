# Linking checkouts that live elsewhere

A workspace does not have to hold its modules. If a module's checkout already exists somewhere
else on the machine, register it instead of cloning a second copy:

```bash
ss link sushiruntime D:/Projects/sushiruntime
ss install-cli sushiruntime            # point `sr` at that checkout
```

`ss link` writes the name and path to `sushihub/cli/modules.local.toml`, which is git-ignored. From then on
`ss status`, `ss update`, `ss sync` and the dependency aggregation treat the linked checkout like a
cloned one: its `cli/sushistack.deps.toml` contributes to what `ss install` provisions, and
`ss update` pulls it.

## Your own sushicore

`sushicore` is not a module; it ships inside this repository and needs no clone. To make every CLI
use a checkout of it that you are editing:

```bash
ss link sushicore /path/to/sushicore
```

Resolution order, first match wins: the `SUSHICORE_DIR` environment variable, a linked path, the
`sushicore/` under the workspace, a sibling checkout next to the workspace. Because the CLIs
receive it as an editable install, edits apply to `ss`, `sr`, `se` and the rest without
reinstalling.

## Undoing a link

There is no `ss unlink` yet. Remove the line from `sushihub/cli/modules.local.toml` and run
`ss install-cli <module>` again so the CLI points back at the workspace copy.
