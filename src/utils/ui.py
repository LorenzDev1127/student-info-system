"""Terminal UI helpers: colors, tables, cards, bar charts and validated prompts.

Standard library only, so the app runs on a fresh Python install. Colors turn
off automatically when output is redirected or the NO_COLOR variable is set.
"""

from __future__ import annotations

import os
import sys
from typing import Callable, Optional, Sequence, TypeVar

T = TypeVar("T")

_STYLES = {
    "bold": "1", "dim": "2",
    "red": "31", "green": "32", "yellow": "33", "blue": "34",
    "magenta": "35", "cyan": "36",
}
_colors_on = False
_clear_on = False


def init(use_colors: bool = True, clear_screen: bool = True) -> None:
    """Prepare the terminal. Call once at startup."""
    global _colors_on, _clear_on
    if hasattr(sys.stdout, "reconfigure"):  # box-drawing characters need UTF-8
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    if os.name == "nt":
        os.system("")  # enables ANSI color codes in Windows cmd / PowerShell
    interactive = sys.stdout.isatty()
    _colors_on = use_colors and interactive and "NO_COLOR" not in os.environ
    _clear_on = clear_screen and interactive


def paint(text: object, *styles: str) -> str:
    if not _colors_on or not styles:
        return str(text)
    codes = ";".join(_STYLES[style] for style in styles)
    return f"\033[{codes}m{text}\033[0m"


def clear() -> None:
    if _clear_on:
        os.system("cls" if os.name == "nt" else "clear")


# --------------------------------------------------------------------- messages
def success(message: str) -> None:
    print(f"  {paint('✔', 'green', 'bold')} {message}")


def error(message: str) -> None:
    print(f"  {paint('✖', 'red', 'bold')} {paint(message, 'red')}")


def warning(message: str) -> None:
    print(f"  {paint('!', 'yellow', 'bold')} {paint(message, 'yellow')}")


def info(message: str) -> None:
    print(f"  {paint('•', 'cyan')} {message}")


# ---------------------------------------------------------------------- layout
def banner(title: str, subtitle: str = "") -> None:
    width = max(len(title), len(subtitle)) + 10
    edge = lambda s: paint(s, "cyan")  # noqa: E731
    print(edge("╔" + "═" * width + "╗"))
    print(edge("║") + paint(title.center(width), "bold") + edge("║"))
    if subtitle:
        print(edge("║") + paint(subtitle.center(width), "dim") + edge("║"))
    print(edge("╚" + "═" * width + "╝"))


def section(title: str, width: int = 50) -> None:
    print()
    print(paint(f"── {title} ", "cyan", "bold") + paint("─" * max(3, width - len(title) - 4), "cyan"))


def _fit(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def table(headers: Sequence[str], rows: Sequence[Sequence[object]], max_cell: int = 30) -> None:
    """Print rows as a box-drawn table."""
    cells = [[_fit(str(value), max_cell) for value in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in cells:
        widths = [max(w, len(value)) for w, value in zip(widths, row)]

    def border(left: str, mid: str, right: str) -> str:
        return paint(left + mid.join("─" * (w + 2) for w in widths) + right, "dim")

    bar = paint("│", "dim")

    def line(values: Sequence[str], *styles: str) -> str:
        return bar + bar.join(f" {paint(v.ljust(w), *styles)} " for v, w in zip(values, widths)) + bar

    print(border("┌", "┬", "┐"))
    print(line(headers, "bold", "cyan"))
    print(border("├", "┼", "┤"))
    for row in cells:
        print(line(row))
    print(border("└", "┴", "┘"))


def card(title: str, pairs: Sequence[tuple[str, object]]) -> None:
    """Print one record as a labelled card."""
    label_width = max(len(label) for label, _ in pairs)
    lines = [(label.ljust(label_width), str(value)) for label, value in pairs]
    inner = max(len(title) + 2, *(label_width + 3 + len(value) for _, value in lines))

    print(paint("┌─ ", "dim") + paint(title, "bold", "cyan") + paint(" " + "─" * (inner - len(title) - 1) + "┐", "dim"))
    for label, value in lines:
        content = f"{paint(label, 'dim')} : {value}"
        padding = inner - (label_width + 3 + len(value))
        print(paint("│ ", "dim") + content + " " * padding + paint(" │", "dim"))
    print(paint("└" + "─" * (inner + 2) + "┘", "dim"))


def bar_chart(data: dict[object, int], width: int = 24) -> None:
    """Horizontal bar chart, e.g. number of students per course."""
    if not data:
        info("Nothing to show yet.")
        return
    label_width = max(len(str(label)) for label in data)
    peak = max(data.values())
    for label, count in data.items():
        length = max(1, round(count / peak * width))
        print(f"  {str(label).ljust(label_width)}  {paint('█' * length, 'cyan')} {count}")


# --------------------------------------------------------------------- prompts
def ask(label: str, parse: Callable[[str], T] = str, default: Optional[str] = None) -> T:
    """Ask until ``parse`` accepts the answer. Blank input uses ``default``."""
    hint = paint(f" [{default}]", "dim") if default not in (None, "") else ""
    while True:
        raw = input(f"  {paint('›', 'cyan', 'bold')} {label}{hint}: ").strip()
        if raw == "" and default is not None:
            raw = default
        try:
            return parse(raw)
        except ValueError as exc:
            error(str(exc))


def confirm(question: str, default: bool = False) -> bool:
    options = "Y/n" if default else "y/N"
    answer = input(f"  {paint('?', 'yellow', 'bold')} {question} ({options}): ").strip().lower()
    return default if not answer else answer in ("y", "yes")


def pause() -> None:
    input(paint("\n  Press Enter to continue…", "dim"))
