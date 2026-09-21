"""The link registry: modules pointed at existing checkouts outside the workspace.

A developer's working checkouts often live outside the workspace tree (e.g.
sibling repos). ``hub link`` records a module's path here so `hub` aggregates
its ``sushistack.deps.toml`` fragment and tracks it, without cloning a second
copy. This is the one place that reads and writes
``<workspace>/sushihub/cli/modules.local.toml``.
"""

from __future__ import annotations

from pathlib import Path

from sushicore.workspace import WORKSPACE_CLI_DIR, read_toml

from ..config import MODULES_FILE, config_dir, workspace_root


def registered() -> dict[str, str]:
    """name -> absolute path for modules linked via ``hub link``.

    Reads from ``<workspace>/sushihub/cli/modules.local.toml`` ``[modules]``.
    Answers empty outside a workspace, so callers need no workspace of their own.
    """
    try:
        home = workspace_root()
    except SystemExit:
        return {}
    doc = read_toml(home / WORKSPACE_CLI_DIR / MODULES_FILE)
    mods = doc.get("modules", {})
    return {k: str(v) for k, v in mods.items() if isinstance(v, str)}


def write(name: str, path: Path) -> None:
    """Record (or update) a module -> path entry in modules.local.toml."""
    registry = dict(registered())
    registry[name] = str(path)
    target = config_dir() / MODULES_FILE
    lines = [
        "# Managed by `hub link`: modules pointed at existing checkouts outside the",
        "# workspace tree. `hub` reads these to aggregate their dependency fragments",
        "# and track them alongside cloned modules.",
        "",
        "[modules]",
    ]
    for key in sorted(registry):
        lines.append(f'{key} = "{str(registry[key]).replace(chr(92), "/")}"')
    lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")
