"""The link registry: modules pointed at existing checkouts outside the workspace.

A developer's working checkouts often live outside the workspace tree (e.g.
sibling repos). ``hub link`` records a module's path here so `hub` aggregates
its ``sushistack.deps.toml`` fragment and tracks it, without cloning a second
copy. This is the one place that reads and writes ``[modules]`` in
``<workspace>/.sushistack/workspace.toml``.
"""

from __future__ import annotations

from pathlib import Path

from sushicore.config_base import write_toml_document
from sushicore.workspace import read_toml

from ..config import WORKSPACE_HEADER, workspace_file, workspace_root


def registered() -> dict[str, str]:
    """name -> absolute path for modules linked via ``hub link``.

    Reads ``[modules]`` from ``<workspace>/.sushistack/workspace.toml``. Answers
    empty outside a workspace, so callers need no workspace of their own.
    """
    try:
        home = workspace_root()
    except SystemExit:
        return {}
    mods = read_toml(workspace_file(home)).get("modules", {})
    return {k: str(v) for k, v in mods.items() if isinstance(v, str)}


def write(name: str, path: Path) -> None:
    """Record (or update) a module -> path entry in ``[modules]``.

    Re-renders the whole document through :func:`write_toml_document`, the one
    renderer ``[tool]``'s writer also goes through, so the tool paths sharing the
    file survive the write.
    """
    target = workspace_file()
    document = dict(read_toml(target))
    registry = dict(document.get("modules", {}))
    registry[name] = str(path)
    document["modules"] = registry
    document.setdefault("workspace", {"version": "1"})
    target.parent.mkdir(parents=True, exist_ok=True)
    write_toml_document(target, document, WORKSPACE_HEADER)
