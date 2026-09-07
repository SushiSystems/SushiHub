"""The registry of projects, and the three commands that keep it.

A project is a directory the engine opens; the desktop application reads
``hub --json projects list`` to show them and launches ``se editor --project
<path>`` for the one a person picks. The registry is one file beside
``modules.local.toml``, so writing it never disturbs the toolchain paths
``hub install`` writes into ``config.local.toml``.

Two halves: the registry itself, which reads and writes the file and knows
nothing of a terminal, and the three commands under it, which print and return
what the ``result`` event carries. The design is
docs/agent/specs/2026-09-05-hub-design.md, §6.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sushicore.workspace import read_toml

from .. import console
from ..config import config_dir

# The file the registry lives in, beside modules.local.toml.
PROJECTS_FILE = "projects.local.toml"


@dataclass(frozen=True)
class Project:
    """One registered project: the name it is listed under and where it lives."""

    name: str
    path: str


def registry_file() -> Path:
    """Return the file the registry is kept in, whether or not it exists."""
    return config_dir() / PROJECTS_FILE


def list_projects() -> list[Project]:
    """Return every registered project, ordered by name.

    Returns:
        One :class:`Project` per entry. A registry file that is absent or holds
        no ``[projects]`` table reads as an empty list.
    """
    table = read_toml(registry_file()).get("projects", {})
    return [Project(name, str(table[name])) for name in sorted(table)
            if isinstance(table[name], str)]


def add_project(path: Path | str, name: str | None = None) -> Project:
    """Record the directory at *path* as a project and return it.

    Args:
        path: The project directory, which must exist.
        name: What to list it under; the directory's own name when None.

    Returns:
        The project as it was recorded, replacing any earlier entry of the same
        name.

    Raises:
        NotADirectoryError: *path* is not a directory.
    """
    target = Path(path).expanduser().resolve()
    if not target.is_dir():
        raise NotADirectoryError(f"{target} is not a directory.")
    project = Project(name or target.name or str(target), str(target))
    entries = {item.name: item.path for item in list_projects()}
    entries[project.name] = project.path
    _write(entries)
    return project


def remove_project(name: str) -> bool:
    """Drop *name* from the registry and report whether it was there.

    Args:
        name: The name the project is listed under. The directory is untouched.
    """
    entries = {item.name: item.path for item in list_projects()}
    if name not in entries:
        return False
    del entries[name]
    _write(entries)
    return True


def show() -> tuple[int, dict]:
    """Print one row per registered project. Return the exit code and the payload."""
    found = list_projects()
    if not found:
        console.info("No projects registered. Add one with `hub projects add <path>`.")
        return 0, {"projects": []}
    rows = [(item, Path(item.path).is_dir()) for item in found]
    console.table(
        ["Name", "Path", "Exists"],
        [[item.name, item.path, "yes" if exists else "no"] for item, exists in rows],
        title="SushiStack Projects",
    )
    return 0, {"projects": [{"name": item.name, "path": item.path, "exists": exists}
                            for item, exists in rows]}


def add(path: str, name: str | None = None) -> tuple[int, dict]:
    """Record a project. Return the exit code and the payload.

    Args:
        path: The project directory.
        name: What to list it under; the directory's own name when None.
    """
    try:
        project = add_project(path, name)
    except (NotADirectoryError, OSError) as error:
        console.error(str(error))
        return 1, {}
    console.success(f"Registered {project.name} -> {project.path}")
    return 0, {"name": project.name, "path": project.path}


def remove(name: str) -> tuple[int, dict]:
    """Drop a project from the registry. Return the exit code and the payload."""
    if not remove_project(name):
        console.error(f"No project called {name}. `hub projects list` shows the names.")
        return 1, {}
    console.success(f"Removed {name} from the registry. The directory is untouched.")
    return 0, {"name": name}


def _write(entries: dict[str, str]) -> None:
    """Write the whole registry, ordered by name, replacing whatever was there.

    Args:
        entries: Project name to directory. Both are written as quoted strings,
            so a name with a space and a Windows path both survive the trip.
    """
    lines = [
        "# Managed by `hub projects`: the project directories the desktop",
        "# application lists and opens with `se editor --project <path>`.",
        "",
        "[projects]",
    ]
    for name in sorted(entries):
        lines.append(f"{json.dumps(name)} = {json.dumps(str(entries[name]))}")
    lines.append("")
    target = registry_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
