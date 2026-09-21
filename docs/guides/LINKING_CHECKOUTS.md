# Linking checkouts that live elsewhere

A workspace does not have to hold its modules. If a module's checkout already exists somewhere
else on the machine, register it instead of cloning a second copy:

```bash
hub link sushiruntime D:/Projects/sushiruntime
hub install-cli sushiruntime            # point `sr` at that checkout
```

`hub link` writes the name and path into `[modules]` in `.sushistack/workspace.toml`, which is
git-ignored. From then on
`hub status`, `hub update`, `hub sync` and the dependency aggregation treat the linked checkout like a
cloned one: its `cli/sushistack.deps.toml` contributes to what `hub install` provisions, and
`hub update` pulls it.

## Your own sushicore

`sushicore` is not a module and `hub link sushicore` is refused. Since 2026-09-22 it lives at
`github.com/SushiSystems/SushiCore` and every CLI takes it from PyPI. To edit it and have the
change reach the CLIs, install your checkout over the published one:

```bash
git clone https://github.com/SushiSystems/SushiCore.git
pip install -e ./SushiCore
```

An editable install shadows the release for as long as it is there, so edits apply to `hub`, `sr`,
`se` and the rest without reinstalling. `pip install --force-reinstall sushicore` puts the
published version back.

## Undoing a link

There is no `hub unlink` yet. Remove the line from `[modules]` in `.sushistack/workspace.toml` and run
`hub install-cli <module>` again so the CLI points back at the workspace copy.
