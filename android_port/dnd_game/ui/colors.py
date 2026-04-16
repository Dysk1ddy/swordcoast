from __future__ import annotations

import re


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
RESET = "\x1b[0m"

COLOR_CODES = {
    "white": "97",
    "green": "92",
    "blue": "94",
    "purple": "95",
    "yellow": "93",
    "light_red": "91",
    "aqua": "36",
    "light_aqua": "96",
    "light_green": "92",
    "light_yellow": "93",
}

RARITY_COLORS = {
    "common": "white",
    "uncommon": "green",
    "rare": "blue",
    "epic": "purple",
    "legendary": "yellow",
}


def colorize(text: object, color: str) -> str:
    rendered = str(text)
    code = COLOR_CODES.get(color)
    if not rendered or code is None:
        return rendered
    return f"\x1b[{code}m{rendered}{RESET}"


def rarity_color(rarity: str) -> str:
    return RARITY_COLORS.get(rarity, "white")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)
