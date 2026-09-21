"""The command catalogue `hub --describe` prints.

A serialisation of the Typer application's own Click command objects, so a new
subcommand reaches the desktop application without a second declaration of it
anywhere. Nothing here names a command; the shape it produces is fixed by
``sushihub/contract/describe.schema.json`` and described in
``sushihub/contract/README.md``.
"""

from __future__ import annotations

import click
import typer
from rich.errors import MarkupError
from rich.text import Text

#: Version of the contract this catalogue and the event stream speak.
CONTRACT_VERSION = "1"

#: The forms of module presence a command can apply to.
ALL_PRESENCE = ("cloned", "linked", "binary")

#: Distribution whose version the catalogue reports.
_DISTRIBUTION = "sushihub"


def _plain(text: str) -> str:
    """Return *text* with its Rich markup tags removed."""
    try:
        return Text.from_markup(text).plain
    except MarkupError:
        return text


def _first_paragraph(help_text: str | None) -> str:
    """Return the first paragraph of *help_text* as one markup-free line."""
    lines: list[str] = []
    for line in (help_text or "").splitlines():
        if not line.strip():
            break
        lines.append(line.strip())
    return _plain(" ".join(lines))


def _type_name(param_type: click.ParamType) -> str:
    """Name *param_type* as one of the six type names the contract allows.

    Matches on the type's own ``name`` rather than its class: Typer ships its own
    Click classes from 0.21 on, so an ``isinstance`` against ``click`` fails there.
    """
    name = str(getattr(param_type, "name", "")).lower()
    if name == "choice":
        return "choice"
    if name == "path":
        return "path"
    if name == "boolean":
        return "boolean"
    if name == "integer":
        return "integer"
    if name == "float":
        return "number"
    return "string"


def _choices(param_type: click.ParamType) -> list[str] | None:
    """Return a choice type's values as strings, or None for every other type."""
    choices = getattr(param_type, "choices", None)
    if choices is None:
        return None
    return [str(choice) for choice in choices]


def _default(param: click.Parameter):
    """Return *param*'s default as JSON data, with an unset default as None."""
    value = param.default
    if value is Ellipsis:
        return None
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _param(param: click.Parameter) -> dict:
    """Describe one argument or option."""
    argument = getattr(param, "param_type_name", "") == "argument"
    return {
        "name": param.name,
        "kind": "argument" if argument else "option",
        "type": _type_name(param.type),
        "multiple": bool(param.multiple or param.nargs == -1),
        "required": bool(param.required),
        "default": _default(param),
        "choices": _choices(param.type),
        "flags": [] if argument else list(param.opts),
        "help": _plain(getattr(param, "help", "") or ""),
    }


def _describes(param: click.Parameter) -> bool:
    """Report whether *param* belongs in the catalogue rather than to Click itself."""
    return param.name not in ("help",)


def _command(name: str, command: click.Command) -> dict:
    """Describe one command and every parameter a caller can set."""
    return {
        "name": name,
        "help": _first_paragraph(command.help),
        "params": [_param(p) for p in command.params if _describes(p)],
        "applies_to": list(ALL_PRESENCE),
    }


def _flatten(group: click.Group, prefix: str = "") -> list[dict]:
    """Describe every leaf command under *group*, sorted, with its full name.

    A nested group is not a command a caller can run, so it contributes its
    children under ``"<group> <child>"`` and no entry of its own. Sorting at each
    level leaves the whole list sorted: a group's name is a prefix of its
    children's, and the space that follows it sorts before any other character.

    Args:
        group: The Click group to walk.
        prefix: What every name at this level starts with, ``""`` at the root.

    Returns:
        One entry per runnable command, in name order.
    """
    described: list[dict] = []
    for name in sorted(getattr(group, "commands", {})):
        command = group.commands[name]
        full = prefix + name
        if hasattr(command, "commands"):
            described.extend(_flatten(command, full + " "))
        else:
            described.append(_command(full, command))
    return described


def _version() -> str:
    """Return the installed distribution's version, or ``0`` when it is not installed."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(_DISTRIBUTION)
    except PackageNotFoundError:
        return "0"


def catalogue(app: typer.Typer) -> dict:
    """Serialise *app*'s commands, sorted by name, as the catalogue the contract fixes.

    A command inside a sub-group is named "<group> <command>", which is what a
    caller types and what the desktop application spawns.

    Args:
        app: The Typer application to describe.

    Returns:
        A dict matching ``sushihub/contract/describe.schema.json``.
    """
    group = typer.main.get_command(app)
    return {
        "program": app.info.name or group.name or "",
        "version": _version(),
        "contract": CONTRACT_VERSION,
        "commands": _flatten(group),
    }
