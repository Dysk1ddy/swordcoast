from __future__ import annotations

import re

from .colors import ANSI_RE


ANSI_COLOR_HEX = {
    "36": "44d7e8",
    "91": "f87171",
    "92": "7ee787",
    "93": "facc15",
    "94": "60a5fa",
    "95": "d8b4fe",
    "96": "67e8f9",
    "97": "fff7ed",
}
KIVY_NON_DIALOGUE_PARAGRAPH_DELAY_SECONDS = 0.75
KIVY_COMMAND_PARAGRAPH_DELAY_SECONDS = 0.18
KIVY_COMBAT_PARAGRAPH_DELAY_SECONDS = 0.22
KIVY_DICE_INITIAL_FRAME_WEIGHT = 0.045
KIVY_DICE_SLOWDOWN_WEIGHT = 3.4


TAG_NAME_RE = re.compile(r"^/?([a-zA-Z]+)")
COLOR_TAG_RE = re.compile(r"\[color=#(?P<rgb>[0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?\]")
COMBAT_TURN_PROMPT_RE = re.compile(
    r"^(?P<prefix>.*?\bActions left:\s*)"
    r"(?P<actions>\d+)"
    r"(?P<separator>\.\s*)"
    r"Bonus action:\s*"
    r"(?P<bonus>ready|spent)"
    r"(?P<suffix>\.)$"
)
DIALOGUE_PREFIX_RE = re.compile(r'^[^:\n]{1,42}:\s+"')
RESOURCE_BAR_RE = re.compile(
    r"\b(?P<label>[A-Za-z][A-Za-z0-9 /'_-]{0,32})\s+\[[^\]\n]*\]\s*"
    r"(?P<current>\d+)\s*/\s*(?P<maximum>\d+)"
)
KIVY_VISIBLE_ENTITIES = {
    "&amp;": "&",
    "&bl;": "[",
    "&br;": "]",
}
COMBAT_SYMBOL_TRANSLATION = str.maketrans(
    {
        0x2588: "#",
        0x2593: "#",
        0x2592: "#",
        0x2591: "-",
        0x2665: "",
        0x2764: "",
        0x1F6E1: "",
        0x2620: "",
        0xFE0F: "",
    }
)


def escape_kivy_markup(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("[", "&bl;")
        .replace("]", "&br;")
    )


def ansi_to_kivy_markup(text: object) -> str:
    rendered = str(text)
    output: list[str] = []
    active_color = False
    position = 0

    for match in ANSI_RE.finditer(rendered):
        output.append(escape_kivy_markup(rendered[position : match.start()]))
        codes = [code for code in match.group()[2:-1].split(";") if code]
        if not codes:
            codes = ["0"]
        for code in codes:
            if code == "0":
                if active_color:
                    output.append("[/color]")
                    active_color = False
                continue
            color = ANSI_COLOR_HEX.get(code)
            if color is not None:
                if active_color:
                    output.append("[/color]")
                output.append(f"[color=#{color}]")
                active_color = True
        position = match.end()

    output.append(escape_kivy_markup(rendered[position:]))
    if active_color:
        output.append("[/color]")
    return "".join(output)


def format_kivy_prompt_markup(text: object) -> str:
    raw = str(text)
    match = COMBAT_TURN_PROMPT_RE.match(raw)
    if match is None:
        return ansi_to_kivy_markup(raw)

    actions = match.group("actions")
    bonus_actions = "1" if match.group("bonus") == "ready" else "0"
    counter_color = "facc15"
    return (
        ansi_to_kivy_markup(match.group("prefix")) +
        f"[b][color=#{counter_color}]{escape_kivy_markup(actions)}[/color][/b]"
        f"{ansi_to_kivy_markup(match.group('separator'))}"
        "Bonus actions: "
        f"[b][color=#{counter_color}]{bonus_actions}[/color][/b]"
        f"{ansi_to_kivy_markup(match.group('suffix'))}"
    )


def plain_combat_status_text(text: object) -> str:
    rendered = str(text)

    def replace_resource_bar(match: re.Match[str]) -> str:
        label = " ".join(match.group("label").split())
        return f"{label} {match.group('current')}/{match.group('maximum')}"

    rendered = RESOURCE_BAR_RE.sub(replace_resource_bar, rendered)
    return rendered.translate(COMBAT_SYMBOL_TRANSLATION)


def format_kivy_log_entry(text: object) -> tuple[str, bool]:
    raw = plain_combat_status_text(text)
    plain = ANSI_RE.sub("", raw).strip()
    if not plain:
        return ("", False)

    banner_match = re.fullmatch(r"=+\s*(.*?)\s*=+", plain)
    if banner_match is not None:
        title = escape_kivy_markup(banner_match.group(1).strip())
        return (
            "\n"
            f"[size=22sp][b][color=#facc15]{title}[/color][/b][/size]\n"
            "[color=#8a6b39]--------------------------------[/color]",
            False,
        )

    if plain.startswith("Commands:"):
        return (f"[size=12sp][color=#8f7d62]{ansi_to_kivy_markup(raw)}[/color][/size]", False)

    if plain.startswith("*"):
        body = escape_kivy_markup(plain[1:].strip())
        return (f"[color=#d9a441]*[/color] [i]{body}[/i]", False)

    if re.match(r"^[^:\n]{1,42}:\s+\".*\"$", plain):
        return (f"[i]{ansi_to_kivy_markup(raw)}[/i]", True)

    if re.match(r"^\s*\d+\.\s+", plain):
        return (f"[color=#d9a441]{ansi_to_kivy_markup(raw)}[/color]", False)

    if ":" in plain and len(plain) < 96:
        label, rest = raw.split(":", 1)
        return (
            f"[b][color=#facc15]{ansi_to_kivy_markup(label)}:[/color][/b]{ansi_to_kivy_markup(rest)}",
            False,
        )

    return (ansi_to_kivy_markup(raw), False)


def kivy_output_is_header(text: object) -> bool:
    plain = ANSI_RE.sub("", str(text)).strip()
    return re.fullmatch(r"=+\s*(.*?)\s*=+", plain) is not None


def should_buffer_kivy_non_dialogue_output(
    markup: str,
    *,
    animated: bool,
    source_text: object = "",
    enabled: bool = True,
    in_combat: bool = False,
) -> bool:
    return bool(
        enabled
        and not in_combat
        and markup
        and not animated
        and visible_markup_length(markup) > 0
        and not kivy_output_is_header(source_text)
    )


def _tag_name(tag: str) -> str | None:
    match = TAG_NAME_RE.match(tag.strip())
    if match is None:
        return None
    return match.group(1).lower()


def visible_markup_length(markup: str) -> int:
    visible = 0
    position = 0
    while position < len(markup):
        if markup[position] == "[":
            end = markup.find("]", position)
            if end != -1:
                position = end + 1
                continue
        if markup[position] == "&":
            end = markup.find(";", position)
            if end != -1:
                visible += 1
                position = end + 1
                continue
        visible += 1
        position += 1
    return visible


def kivy_non_dialogue_reveal_delay(
    markup: str,
    *,
    animated: bool,
    enabled: bool = True,
    fast: bool = False,
    combat: bool = False,
) -> float:
    if not enabled or animated:
        return 0.0
    paragraphs = [part for part in re.split(r"\n\s*\n+", visible_markup_text(markup).strip()) if part.strip()]
    if not paragraphs:
        return 0.0
    if fast:
        seconds_per_paragraph = KIVY_COMMAND_PARAGRAPH_DELAY_SECONDS
    elif combat:
        seconds_per_paragraph = KIVY_COMBAT_PARAGRAPH_DELAY_SECONDS
    else:
        seconds_per_paragraph = KIVY_NON_DIALOGUE_PARAGRAPH_DELAY_SECONDS
    return seconds_per_paragraph * len(paragraphs)


def kivy_resource_bar_markup(
    current: int,
    maximum: int,
    *,
    width: int = 14,
    color: str = "7ee787",
    empty_color: str = "3b3428",
) -> str:
    maximum = max(1, int(maximum))
    current = max(0, min(int(current), maximum))
    width = max(1, int(width))
    filled = max(0, min(width, int(round((current / maximum) * width))))
    empty = width - filled
    fill = "█" * filled
    remainder = "░" * empty
    return f"[color=#{color}]{fill}[/color][color=#{empty_color}]{remainder}[/color] {current}/{maximum}"


def kivy_dice_animation_allowed(
    *,
    in_combat: bool,
    style: str | None = None,
    outcome_kind: str | None = None,
) -> bool:
    if style == "initiative" or outcome_kind == "initiative":
        return True
    return not in_combat


def kivy_dice_frame_delays(frame_count: int, duration: float) -> list[float]:
    frame_count = max(1, int(frame_count))
    duration = max(0.0, float(duration))
    weights = [
        KIVY_DICE_INITIAL_FRAME_WEIGHT
        + ((index / max(1, frame_count - 1)) ** KIVY_DICE_SLOWDOWN_WEIGHT) * 3.2
        for index in range(frame_count)
    ]
    total = sum(weights) or 1.0
    return [(weight / total) * duration for weight in weights]


def kivy_dice_highlight_index(rolls: list[int], kept: int | None = None) -> int | None:
    if not rolls:
        return None
    if kept is not None:
        for index, value in enumerate(rolls):
            if value == kept:
                return index
    return max(range(len(rolls)), key=lambda index: rolls[index])


def fade_kivy_markup(markup: str, opacity: float, *, default_color: str = "ffffff") -> str:
    alpha = int(round(max(0.0, min(1.0, opacity)) * 255))
    alpha_hex = f"{alpha:02x}"
    default_rgb = re.sub(r"[^0-9a-fA-F]", "", default_color)[:6] or "ffffff"

    def replace_color(match: re.Match[str]) -> str:
        return f"[color=#{match.group('rgb')}{alpha_hex}]"

    faded = COLOR_TAG_RE.sub(replace_color, markup)
    return f"[color=#{default_rgb}{alpha_hex}]{faded}[/color]"


def visible_markup_text(markup: str) -> str:
    output: list[str] = []
    position = 0
    while position < len(markup):
        if markup[position] == "[":
            end = markup.find("]", position)
            if end != -1:
                position = end + 1
                continue
        if markup[position] == "&":
            end = markup.find(";", position)
            if end != -1:
                entity = markup[position : end + 1]
                output.append(KIVY_VISIBLE_ENTITIES.get(entity, "?"))
                position = end + 1
                continue
        output.append(markup[position])
        position += 1
    return "".join(output)


def dialogue_typing_start_index(markup: str) -> int:
    match = DIALOGUE_PREFIX_RE.match(visible_markup_text(markup))
    return 0 if match is None else match.end()


def reveal_kivy_markup(markup: str, visible_characters: int) -> str:
    remaining = max(0, int(visible_characters))
    output: list[str] = []
    open_tags: list[str] = []
    position = 0

    while position < len(markup) and remaining > 0:
        character = markup[position]
        if character == "[":
            end = markup.find("]", position)
            if end != -1:
                tag = markup[position + 1 : end]
                output.append(markup[position : end + 1])
                tag_name = _tag_name(tag)
                if tag_name is not None:
                    if tag.strip().startswith("/"):
                        for index in range(len(open_tags) - 1, -1, -1):
                            if open_tags[index] == tag_name:
                                del open_tags[index]
                                break
                    else:
                        open_tags.append(tag_name)
                position = end + 1
                continue
        if character == "&":
            end = markup.find(";", position)
            if end != -1:
                output.append(markup[position : end + 1])
                remaining -= 1
                position = end + 1
                continue
        output.append(character)
        remaining -= 1
        position += 1

    for tag_name in reversed(open_tags):
        output.append(f"[/{tag_name}]")
    return "".join(output)
