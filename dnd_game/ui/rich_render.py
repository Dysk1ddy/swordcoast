from __future__ import annotations

from io import StringIO

from .colors import strip_ansi

try:
    from rich import box
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency fallback
    box = Columns = Group = Panel = Table = Text = None
    RICH_AVAILABLE = False


def render_rich_lines(renderable, *, width: int = 100, force_terminal: bool = False) -> list[str]:
    if not RICH_AVAILABLE:
        return []
    from rich.console import Console

    buffer = StringIO()
    console = Console(
        file=buffer,
        width=width,
        force_terminal=force_terminal,
        color_system="truecolor" if force_terminal else None,
        markup=False,
        highlight=False,
        legacy_windows=False,
    )
    console.print(renderable)
    rendered = buffer.getvalue().rstrip("\n")
    if not rendered:
        return []
    return rendered.split("\n")


def text_from_ansi(text: str):
    if not RICH_AVAILABLE:
        return strip_ansi(text)
    return Text.from_ansi(text)
