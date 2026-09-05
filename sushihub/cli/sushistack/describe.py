"""The command catalogue `ss --describe` prints.

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
_DISTRIBUTION = "sushistack-cli"


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
    """Name *param_type* as one of the six type names the contract allows."""
    if isinstance(param_type, click.Choice):
        return "choice"
    if isinstance(param_type, click.Path):
        return "path"
    if isinstance(param_type, click.types.BoolParamType):
        return "boolean"
    if isinstance(param_type, click.types.IntParamType):
        return "integer"
    if isinstance(param_type, click.types.FloatParamType):
        return "number"
    return "string"


def _choices(param_type: click.ParamType) -> list[str] | None:
    """Return a choice type's values as strings, or None for every other type."""
    if isinstance(param_type, click.Choice):
        return [str(choice) for choice in param_type.choices]
    return None


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
    argument = isinstance(param, click.Argument)
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


def _version() -> str:
    """Return the installed distribution's version, or ``0`` when it is not installed."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(_DISTRIBUTION)
    except PackageNotFoundError:
        return "0"


def catalogue(app: typer.Typer) -> dict:
    """Serialise *app*'s commands, sorted by name, as the catalogue the contract fixes.

    Args:
        app: The Typer application to describe.

    Returns:
        A dict matching ``sushihub/contract/describe.schema.json``.
    """
    group = typer.main.get_command(app)
    commands = getattr(group, "commands", {})
    return {
        "program": app.info.name or group.name or "",
        "version": _version(),
        "contract": CONTRACT_VERSION,
        "commands": [_command(name, commands[name]) for name in sorted(commands)],
    }
