"""hub's source names theme tokens, never a raw Rich colour, in the markup it prints."""

from __future__ import annotations

import ast
import re
from pathlib import Path

K_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "sushihub"

K_RAW_STYLE_WORDS = frozenset({
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "dim",
})

K_TAG = re.compile(r"\[/?([^\[\]]+)\]")
K_BRIGHT = re.compile(r"bright_[a-z]+")
K_HEX = re.compile(r"#[0-9a-fA-F]{6}")


def _is_raw_style_word(word: str) -> bool:
    """Return whether *word* is a Rich colour name, a bright variant, a hex code or dim."""
    return word in K_RAW_STYLE_WORDS or bool(K_BRIGHT.fullmatch(word) or K_HEX.fullmatch(word))


def _raw_tags_in(source: str) -> list[tuple[int, str]]:
    """Return the line and text of every tag in *source*'s string constants naming a raw style.

    A constant inside an f-string is a string constant too, so the walk sees the fixed parts of
    an f-string; a bare ``[bold]`` names no colour and passes.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        for tag in K_TAG.finditer(node.value):
            if any(_is_raw_style_word(word) for word in tag.group(1).split()):
                found.append((node.lineno, tag.group(0)))
    return found


def test_scanner_reads_plain_and_fstring_constants() -> None:
    source = 'a = "[green]x[/green]"\nb = f"[bold yellow]{n}[/bold yellow] [dim]y[/dim]"\n'
    tags = [tag for _line, tag in _raw_tags_in(source)]
    assert tags == [
        "[green]", "[/green]", "[bold yellow]", "[/bold yellow]", "[dim]", "[/dim]",
    ]


def test_scanner_passes_theme_tokens_and_bare_bold() -> None:
    source = 'a = "[success]x[/success] [bold]y[/bold] [muted]z[/muted]"\n'
    assert _raw_tags_in(source) == []


def test_source_names_no_raw_rich_colour() -> None:
    offenders = [
        f"{path.relative_to(K_SOURCE_ROOT)}:{line}  {tag}"
        for path in sorted(K_SOURCE_ROOT.rglob("*.py"))
        for line, tag in _raw_tags_in(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], "raw Rich colour names in string constants:\n" + "\n".join(offenders)
