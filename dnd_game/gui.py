from __future__ import annotations

import os
import json
import math
from pathlib import Path
from queue import Queue
import random
import re
import sys
from threading import Event, Thread
import time
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_FILELOG", "1")

from kivy.config import Config

Config.set("kivy", "exit_on_escape", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from .game import TextDnDGame
from .gameplay.base import QuitProgram, ReturnToTitleMenu
from .gameplay.constants import MENU_PAGE_SIZE
from .data.story.companions import COMPANION_PROFILES
from .drafts.map_system import ACT1_HYBRID_MAP, ACT2_ENEMY_DRIVEN_MAP
from .drafts.map_system.runtime import (
    available_travel_edges,
    current_room_exits,
    requirement_met,
    room_exit_directions,
    room_travel_path,
)
from .gameplay.magic_points import current_magic_points, maximum_magic_points
from .ui.colors import strip_ansi
from .ui.kivy_markup import (
    ansi_to_kivy_markup,
    dialogue_typing_start_index,
    escape_kivy_markup,
    fade_kivy_markup,
    format_kivy_prompt_markup,
    format_kivy_log_entry,
    kivy_dice_animation_allowed,
    kivy_dice_frame_delays,
    kivy_dice_highlight_index,
    kivy_non_dialogue_reveal_delay,
    kivy_resource_bar_markup,
    plain_combat_status_text,
    reveal_kivy_markup,
    should_buffer_kivy_non_dialogue_output,
    visible_markup_length,
    visible_markup_text,
)
from .ui.examine import (
    ExamineEntry,
    character_examine_entry,
    current_location_examine_entry,
    examine_entry_for_text,
    feature_examine_entry,
    resource_examine_entry,
    status_examine_entry,
)
from .ui.command_snapshots import (
    build_camp_snapshot,
    build_gear_snapshot,
    build_inventory_snapshot,
    build_journal_snapshot,
)
from .ui.command_actions import (
    drop_inventory_item,
    equip_item_for_member,
    magic_mirror_unavailable_reason,
    revive_dead_ally,
    take_long_rest,
    take_short_rest,
    unequip_member_slot,
    usable_inventory_targets,
    use_inventory_item_on_target,
)


FONT_ASSET_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT_ROLE_CANDIDATES: dict[str, tuple[str, ...]] = {
    "story": (
        "Alegreya-Regular.ttf",
        "Alegreya-VariableFont_wght.ttf",
        "Alegreya.ttf",
        "SourceSerif4-Regular.ttf",
        "SourceSerif4-VariableFont_opsz,wght.ttf",
        "SourceSerif4_18pt-Regular.ttf",
        "SourceSerifPro-Regular.ttf",
        "georgia.ttf",
        "cambria.ttc",
    ),
    "ui": (
        "Lato-Regular.ttf",
        "Lato.ttf",
        "OpenSans-Regular.ttf",
        "OpenSans-VariableFont_wdth,wght.ttf",
        "Montserrat-Regular.ttf",
        "Montserrat-VariableFont_wght.ttf",
        "segoeui.ttf",
        "arial.ttf",
    ),
    "mono": (
        "JetBrainsMono-Regular.ttf",
        "JetBrainsMono-VariableFont_wght.ttf",
        "Inconsolata-Regular.ttf",
        "Inconsolata-VariableFont_wdth,wght.ttf",
        "CascadiaMono.ttf",
        "CascadiaCode.ttf",
        "consola.ttf",
        "cour.ttf",
    ),
}
FONT_ROLE_KEYWORDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "story": (
        ("alegreya", "regular"),
        ("alegreya", "variablefont"),
        ("sourceserif4", "regular"),
        ("sourceserif4", "variablefont"),
        ("sourceserifpro", "regular"),
        ("georgia",),
        ("cambria",),
    ),
    "ui": (
        ("lato", "regular"),
        ("opensans", "regular"),
        ("opensans", "variablefont"),
        ("montserrat", "regular"),
        ("montserrat", "variablefont"),
        ("segoeui",),
        ("arial",),
    ),
    "mono": (
        ("jetbrainsmono", "regular"),
        ("jetbrainsmono", "variablefont"),
        ("inconsolata", "regular"),
        ("inconsolata", "variablefont"),
        ("cascadiamono",),
        ("cascadiacode",),
        ("consola",),
        ("cour",),
    ),
}
FONT_PATH_CACHE: dict[str, str | None] = {}
FONT_FILE_CACHE: list[Path] | None = None
KIVY_DICE_COLOR_HEX = {
    "cyan": "67e8f9",
    "light_aqua": "67e8f9",
    "light_green": "86efac",
    "light_red": "f87171",
    "light_yellow": "d6c59a",
    "yellow": "facc15",
}
KIVY_SIDE_COMMAND_CLOSE_TOKEN = "__aethrune_kivy_close_side_command__"
KIVY_EXAMINE_HOLD_SECONDS = 0.35
KIVY_COLOR_SPAN_RE = re.compile(
    r"\[color=#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\](?P<body>.*?)\[/color\]",
    re.DOTALL,
)
KIVY_TITLE_PHRASE_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z']+|[A-Z]{2,}|I{1,3}|IV|V)"
    r"(?:\s+(?:and|of|the|And|Of|The|[A-Z][A-Za-z']+|[A-Z]{2,}|I{1,3}|IV|V)){0,5}\b"
)
KIVY_SKILL_TAG_RE = re.compile(r"\[[A-Z][A-Z /,_-]{2,}\]")


class KivySideCommandClosed(Exception):
    """Raised inside the Kivy worker thread when the command panel is closed."""


def normalize_font_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def kivy_font_directories() -> list[Path]:
    directories = [FONT_ASSET_DIR]
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        directories.append(Path(local_appdata) / "Microsoft" / "Windows" / "Fonts")
    windir = os.environ.get("WINDIR")
    if windir:
        directories.append(Path(windir) / "Fonts")
    return directories


def available_kivy_font_files() -> list[Path]:
    global FONT_FILE_CACHE
    if FONT_FILE_CACHE is not None:
        return FONT_FILE_CACHE
    files: list[Path] = []
    seen: set[Path] = set()
    for directory in kivy_font_directories():
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.suffix.lower() not in {".ttf", ".otf", ".ttc"} or not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)
    FONT_FILE_CACHE = files
    return files


def resolve_kivy_font(role: str) -> str | None:
    if role in FONT_PATH_CACHE:
        return FONT_PATH_CACHE[role]
    candidates = FONT_ROLE_CANDIDATES.get(role, ())
    for directory in kivy_font_directories():
        for filename in candidates:
            path = directory / filename
            if path.is_file():
                FONT_PATH_CACHE[role] = str(path)
                return FONT_PATH_CACHE[role]

    available = available_kivy_font_files()
    normalized = [(normalize_font_filename(path.name), path) for path in available]
    for keywords in FONT_ROLE_KEYWORDS.get(role, ()):
        for normalized_name, path in normalized:
            if all(keyword in normalized_name for keyword in keywords):
                FONT_PATH_CACHE[role] = str(path)
                return FONT_PATH_CACHE[role]
    FONT_PATH_CACHE[role] = None
    return None


class WrappedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(width=self._sync_text_size, texture_size=self._sync_height)
        self._sync_text_size()
        self._sync_height()

    def _sync_text_size(self, *_args) -> None:
        self.text_size = (max(0, self.width - dp(12)), None)

    def _sync_height(self, *_args) -> None:
        self.height = max(dp(32), self.texture_size[1] + dp(12))


class ExaminableWrappedLabel(WrappedLabel):
    def __init__(self, *, hold_seconds: float = KIVY_EXAMINE_HOLD_SECONDS, **kwargs):
        self._examine_hold_seconds = float(hold_seconds)
        self._examine_ref_touch_uid = None
        self._examine_ref_name: str | None = None
        self._examine_ref_event = None
        super().__init__(**kwargs)

    def _touch_uid(self, touch) -> object:
        return getattr(touch, "uid", id(touch))

    def _touch_is_right_click(self, touch) -> bool:
        return str(getattr(touch, "button", "")).lower() == "right"

    def _ref_at_touch(self, touch) -> str | None:
        if not self.collide_point(*touch.pos):
            return None
        self.texture_update()
        if not self.refs:
            return None
        tx, ty = touch.pos
        tx -= self.center_x - self.texture_size[0] / 2.0
        ty -= self.center_y - self.texture_size[1] / 2.0
        ty = self.texture_size[1] - ty
        for ref_name, zones in self.refs.items():
            for zone in zones:
                x1, y1, x2, y2 = zone
                if x1 <= tx <= x2 and y1 <= ty <= y2:
                    return str(ref_name)
        return None

    def _cancel_examine_ref_hold(self) -> None:
        if self._examine_ref_event is not None:
            self._examine_ref_event.cancel()
        self._examine_ref_event = None
        self._examine_ref_touch_uid = None
        self._examine_ref_name = None

    def _trigger_examine_ref_hold(self, _dt) -> None:
        ref_name = self._examine_ref_name
        self._examine_ref_event = None
        if ref_name:
            self.dispatch("on_ref_press", ref_name)

    def on_touch_down(self, touch) -> bool:
        ref_name = self._ref_at_touch(touch)
        if ref_name is None:
            return super().on_touch_down(touch)
        if self._touch_is_right_click(touch):
            self.dispatch("on_ref_press", ref_name)
            return True
        self._cancel_examine_ref_hold()
        self._examine_ref_touch_uid = self._touch_uid(touch)
        self._examine_ref_name = ref_name
        self._examine_ref_event = Clock.schedule_once(
            self._trigger_examine_ref_hold,
            self._examine_hold_seconds,
        )
        return True

    def on_touch_move(self, touch) -> bool:
        if self._touch_uid(touch) == self._examine_ref_touch_uid and self._ref_at_touch(touch) != self._examine_ref_name:
            self._cancel_examine_ref_hold()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch) -> bool:
        if self._touch_uid(touch) == self._examine_ref_touch_uid:
            self._cancel_examine_ref_hold()
            return True
        return super().on_touch_up(touch)


class WrappedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(width=self._sync_text_size, texture_size=self._sync_height)
        self._sync_text_size()
        self._sync_height()

    def _sync_text_size(self, *_args) -> None:
        self.text_size = (max(0, self.width - dp(24)), None)

    def _sync_height(self, *_args) -> None:
        self.height = max(dp(38), self.texture_size[1] + dp(14))


class ExaminableButton(Button):
    def __init__(
        self,
        *,
        examine_callback=None,
        hold_seconds: float = KIVY_EXAMINE_HOLD_SECONDS,
        **kwargs,
    ):
        self.examine_callback = examine_callback
        self._examine_hold_seconds = float(hold_seconds)
        self._examine_touch_uid = None
        self._examine_hold_event = None
        self._examine_hold_triggered = False
        super().__init__(**kwargs)

    def _touch_uid(self, touch) -> object:
        return getattr(touch, "uid", id(touch))

    def _touch_is_right_click(self, touch) -> bool:
        return str(getattr(touch, "button", "")).lower() == "right"

    def _cancel_examine_hold(self) -> None:
        if self._examine_hold_event is not None:
            self._examine_hold_event.cancel()
        self._examine_hold_event = None

    def _open_examine(self) -> None:
        callback = self.examine_callback
        if callable(callback):
            callback()

    def _trigger_examine_hold(self, _dt) -> None:
        self._examine_hold_event = None
        self._examine_hold_triggered = True
        self.state = "normal"
        self._open_examine()

    def on_touch_down(self, touch) -> bool:
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._touch_is_right_click(touch):
            self._open_examine()
            return True
        self._cancel_examine_hold()
        self._examine_touch_uid = self._touch_uid(touch)
        self._examine_hold_triggered = False
        self._examine_hold_event = Clock.schedule_once(
            self._trigger_examine_hold,
            self._examine_hold_seconds,
        )
        return super().on_touch_down(touch)

    def on_touch_move(self, touch) -> bool:
        if self._touch_uid(touch) == self._examine_touch_uid and not self.collide_point(*touch.pos):
            self._cancel_examine_hold()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch) -> bool:
        if self._touch_uid(touch) == self._examine_touch_uid:
            self._cancel_examine_hold()
            triggered = self._examine_hold_triggered
            self._examine_touch_uid = None
            self._examine_hold_triggered = False
            if triggered:
                if getattr(touch, "grab_current", None) is self:
                    touch.ungrab(self)
                self.state = "normal"
                return True
        return super().on_touch_up(touch)


class PanelBox(BoxLayout):
    def __init__(self, *, background_color=(0.10, 0.08, 0.06, 1), radius: int = 8, **kwargs):
        self._panel_background_color = background_color
        self._panel_radius = radius
        super().__init__(**kwargs)
        with self.canvas.before:
            self._canvas_color = Color(*self._panel_background_color)
            self._canvas_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._sync_canvas_rect, size=self._sync_canvas_rect)

    def _sync_canvas_rect(self, *_args) -> None:
        self._canvas_rect.pos = self.pos
        self._canvas_rect.size = self.size

    def set_background_color(self, color: tuple[float, float, float, float]) -> None:
        self._panel_background_color = color
        self._canvas_color.rgba = color


class MapTokenLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.markup = True
        self.halign = "center"
        self.valign = "middle"
        self.padding = [dp(2), 0]
        self._fill_rgba = (0.10, 0.10, 0.10, 1)
        self._border_rgba = (0.40, 0.40, 0.40, 1)
        with self.canvas.before:
            self._fill_color = Color(*self._fill_rgba)
            self._fill_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
            self._border_color = Color(*self._border_rgba)
            self._border_line = Line(rectangle=(self.x, self.y, self.width, self.height), width=dp(1))
        self.bind(pos=self._sync_canvas, size=self._sync_canvas)
        self._sync_canvas()

    def _sync_canvas(self, *_args) -> None:
        self._fill_rect.pos = self.pos
        self._fill_rect.size = self.size
        self._border_line.rectangle = (self.x, self.y, self.width, self.height)
        self.text_size = (max(1, self.width - dp(4)), self.height)

    def set_style(
        self,
        *,
        fill: tuple[float, float, float, float],
        border: tuple[float, float, float, float],
        text: tuple[float, float, float, float],
    ) -> None:
        self._fill_rgba = fill
        self._border_rgba = border
        self._fill_color.rgba = fill
        self._border_color.rgba = border
        self.color = text


class NativeMapCanvas(Widget):
    ROLE_SYMBOLS = {
        "entrance": "D",
        "combat": "E",
        "event": "*",
        "treasure": "T",
        "boss": "B",
        "exit": "X",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode = ""
        self._payload: dict[str, object] = {}
        self._dark_mode = True
        self._redraw_event = None
        self.bind(pos=self._schedule_redraw, size=self._schedule_redraw)

    def set_dark_mode(self, enabled: bool) -> None:
        self._dark_mode = bool(enabled)
        self._schedule_redraw()

    def clear_map(self) -> None:
        self._mode = ""
        self._payload = {}
        self._schedule_redraw()

    def show_overworld(self, blueprint, state) -> None:
        self._mode = "overworld"
        self._payload = {"blueprint": blueprint, "state": state}
        self._schedule_redraw()

    def show_dungeon(self, dungeon, state) -> None:
        self._mode = "dungeon"
        self._payload = {"dungeon": dungeon, "state": state}
        self._schedule_redraw()

    def _schedule_redraw(self, *_args) -> None:
        if self._redraw_event is not None:
            return
        self._redraw_event = Clock.schedule_once(self._redraw, 0)

    def _palette(self) -> dict[str, tuple[float, float, float, float]]:
        if self._dark_mode:
            return {
                "background": (0.045, 0.050, 0.052, 1),
                "grid": (0.22, 0.26, 0.25, 0.55),
                "route": (0.40, 0.56, 0.58, 0.80),
                "route_available": (0.90, 0.73, 0.30, 1),
                "route_hidden": (0.24, 0.24, 0.24, 0.48),
                "current_fill": (0.15, 0.42, 0.48, 1),
                "current_border": (0.98, 0.82, 0.28, 1),
                "known_fill": (0.075, 0.080, 0.085, 1),
                "known_border": (0.98, 0.78, 0.26, 1),
                "unknown_fill": (0.075, 0.080, 0.085, 1),
                "unknown_border": (0.38, 0.39, 0.38, 1),
                "locked_fill": (0.050, 0.052, 0.055, 1),
                "locked_border": (0.20, 0.21, 0.21, 1),
                "text": (0.98, 0.94, 0.82, 1),
                "muted_text": (0.64, 0.59, 0.50, 1),
                "dim_text": (0.38, 0.38, 0.36, 1),
            }
        return {
            "background": (0.92, 0.88, 0.78, 1),
            "grid": (0.44, 0.36, 0.24, 0.45),
            "route": (0.30, 0.42, 0.40, 0.90),
            "route_available": (0.72, 0.48, 0.10, 1),
            "route_hidden": (0.54, 0.49, 0.40, 0.45),
            "current_fill": (0.20, 0.58, 0.62, 1),
            "current_border": (0.72, 0.48, 0.10, 1),
            "known_fill": (0.76, 0.72, 0.64, 1),
            "known_border": (0.72, 0.48, 0.10, 1),
            "unknown_fill": (0.76, 0.72, 0.64, 1),
            "unknown_border": (0.48, 0.45, 0.39, 1),
            "locked_fill": (0.64, 0.61, 0.55, 1),
            "locked_border": (0.36, 0.34, 0.31, 1),
            "text": (0.10, 0.08, 0.05, 1),
            "muted_text": (0.34, 0.29, 0.22, 1),
            "dim_text": (0.46, 0.43, 0.38, 1),
        }

    def _redraw(self, _dt) -> None:
        self._redraw_event = None
        self.canvas.before.clear()
        self.clear_widgets()
        palette = self._palette()
        with self.canvas.before:
            Color(*palette["background"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        if self.width <= dp(12) or self.height <= dp(12):
            return
        if self._mode == "overworld":
            self._draw_overworld(palette)
        elif self._mode == "dungeon":
            self._draw_dungeon(palette)

    def _node_is_known(self, node, state) -> bool:
        return node.node_id == state.current_node_id or node.node_id in state.visited_nodes

    def _node_status(self, node, state, *, reachable_node_ids: set[str] | None = None) -> str:
        # Node colors encode gameplay state only:
        # current = teal/gold; known reachable = dark/gold;
        # unknown = dark/muted gray; known locked = dim gray.
        if node.node_id == state.current_node_id:
            return "current"
        if not self._node_is_known(node, state):
            return "unknown"
        if reachable_node_ids is not None and node.node_id in reachable_node_ids:
            return "known_reachable"
        if requirement_met(state, node.requirement):
            return "known"
        return "locked"

    def _node_style(
        self,
        status: str,
        palette: dict[str, tuple[float, float, float, float]],
    ) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float], tuple[float, float, float, float]]:
        if status == "current":
            return palette["current_fill"], palette["current_border"], palette["text"]
        if status == "known_reachable":
            return palette["known_fill"], palette["known_border"], palette["text"]
        if status == "unknown":
            return palette["unknown_fill"], palette["unknown_border"], palette["muted_text"]
        if status == "locked":
            return palette["locked_fill"], palette["locked_border"], palette["dim_text"]
        return palette["known_fill"], palette["unknown_border"], palette["text"]

    def _draw_overworld(self, palette: dict[str, tuple[float, float, float, float]]) -> None:
        blueprint = self._payload.get("blueprint")
        state = self._payload.get("state")
        if blueprint is None or state is None or not getattr(blueprint, "overworld_positions", None):
            return

        positions = dict(blueprint.overworld_positions)
        min_x = min(x for x, _ in positions.values())
        max_x = max(x for x, _ in positions.values())
        min_y = min(y for _, y in positions.values())
        max_y = max(y for _, y in positions.values())
        margin = dp(12)
        columns = max(1, max_x - min_x + 1)
        rows = max(1, max_y - min_y + 1)
        slot_w = max(dp(28), (self.width - 2 * margin) / columns)
        slot_h = max(dp(22), (self.height - 2 * margin) / rows)
        node_w = min(dp(112), max(dp(48), slot_w * 0.84))
        node_h = min(dp(31), max(dp(18), slot_h * 0.72))
        font_size = min(sp(10), max(sp(6), node_h * 0.44))

        centers: dict[str, tuple[float, float]] = {}
        for node_id, (grid_x, grid_y) in positions.items():
            centers[node_id] = (
                self.x + margin + (grid_x - min_x + 0.5) * slot_w,
                self.top - margin - (grid_y - min_y + 0.5) * slot_h,
            )

        try:
            available_edges = list(available_travel_edges(blueprint, state))
        except Exception:
            available_edges = []
        available_edge_ids = {edge.edge_id for edge in available_edges}
        reachable_node_ids = {edge.to_node_id for edge in available_edges}

        with self.canvas.before:
            for edge in blueprint.edges:
                if edge.from_node_id not in centers or edge.to_node_id not in centers:
                    continue
                source = blueprint.nodes[edge.from_node_id]
                target = blueprint.nodes[edge.to_node_id]
                source_status = self._node_status(source, state, reachable_node_ids=reachable_node_ids)
                target_status = self._node_status(target, state, reachable_node_ids=reachable_node_ids)
                if edge.edge_id in available_edge_ids and self._node_is_known(target, state):
                    Color(*palette["route_available"])
                    width = dp(2.2)
                elif source_status != "locked" and target_status in {"current", "known", "known_reachable"}:
                    Color(*palette["route"])
                    width = dp(1.4)
                else:
                    Color(*palette["route_hidden"])
                    width = dp(1)
                sx, sy = centers[edge.from_node_id]
                tx, ty = centers[edge.to_node_id]
                Line(points=[sx, sy, tx, ty], width=width)

        for node_id, (center_x, center_y) in centers.items():
            node = blueprint.nodes[node_id]
            status = self._node_status(node, state, reachable_node_ids=reachable_node_ids)
            label_text = node.short_label if self._node_is_known(node, state) else "???"
            fill, border, text = self._node_style(status, palette)
            token = MapTokenLabel(
                text=escape_kivy_markup(label_text),
                font_size=font_size,
                bold=status == "current",
                size=(node_w, node_h),
                pos=(center_x - node_w / 2, center_y - node_h / 2),
            )
            token.set_style(fill=fill, border=border, text=text)
            self.add_widget(token)

    def _room_anchor(self, room) -> tuple[int, int]:
        return (room.x * 2, room.y * 2)

    def _room_visible(self, dungeon, state, room_id: str) -> bool:
        room = dungeon.rooms[room_id]
        return room_id == (state.current_room_id or dungeon.entrance_room_id) or room_id in state.cleared_rooms or requirement_met(state, room.requirement)

    def _room_status(self, dungeon, state, room_id: str) -> str:
        if room_id == (state.current_room_id or dungeon.entrance_room_id):
            return "current"
        if room_id in state.cleared_rooms:
            return "cleared"
        if requirement_met(state, dungeon.rooms[room_id].requirement):
            return "available"
        return "locked"

    def _draw_dungeon(self, palette: dict[str, tuple[float, float, float, float]]) -> None:
        dungeon = self._payload.get("dungeon")
        state = self._payload.get("state")
        if dungeon is None or state is None or not getattr(dungeon, "rooms", None):
            return

        margin = dp(14)
        fine_w = max(1, dungeon.width * 2 - 1)
        fine_h = max(1, dungeon.height * 2 - 1)
        cell_w = max(dp(20), (self.width - 2 * margin) / fine_w)
        cell_h = max(dp(20), (self.height - 2 * margin) / fine_h)
        tile = min(dp(44), max(dp(24), min(cell_w, cell_h) * 0.78))
        font_size = min(sp(17), max(sp(10), tile * 0.42))

        def center_for(anchor: tuple[int, int]) -> tuple[float, float]:
            anchor_x, anchor_y = anchor
            return (
                self.x + margin + (anchor_x + 0.5) * cell_w,
                self.top - margin - (anchor_y + 0.5) * cell_h,
            )

        with self.canvas.before:
            Color(*palette["grid"])
            for index in range(fine_w):
                x = self.x + margin + (index + 0.5) * cell_w
                Line(points=[x, self.y + margin, x, self.top - margin], width=dp(0.5))
            for index in range(fine_h):
                y = self.top - margin - (index + 0.5) * cell_h
                Line(points=[self.x + margin, y, self.right - margin, y], width=dp(0.5))

            drawn_edges: set[tuple[str, str]] = set()
            for room in dungeon.rooms.values():
                if not self._room_visible(dungeon, state, room.room_id):
                    continue
                for target_id in room.exits:
                    if target_id not in dungeon.rooms or not self._room_visible(dungeon, state, target_id):
                        continue
                    edge_key = tuple(sorted((room.room_id, target_id)))
                    if edge_key in drawn_edges:
                        continue
                    drawn_edges.add(edge_key)
                    target = dungeon.rooms[target_id]
                    route = [self._room_anchor(room), *room_travel_path(dungeon, room, target)]
                    if len(route) < 2:
                        route = [self._room_anchor(room), self._room_anchor(target)]
                    points: list[float] = []
                    for anchor in route:
                        cx, cy = center_for(anchor)
                        points.extend([cx, cy])
                    room_status = self._room_status(dungeon, state, room.room_id)
                    target_status = self._room_status(dungeon, state, target_id)
                    if "current" in {room_status, target_status} and "available" in {room_status, target_status}:
                        Color(*palette["route_available"])
                        width = dp(2.2)
                    elif room_status == "locked" or target_status == "locked":
                        Color(*palette["route_hidden"])
                        width = dp(1)
                    else:
                        Color(*palette["route"])
                        width = dp(1.4)
                    Line(points=points, width=width)

        for room_id, room in dungeon.rooms.items():
            status = self._room_status(dungeon, state, room_id)
            if status == "current":
                fill, border, text = self._node_style("current", palette)
                symbol = "P"
            elif status == "cleared":
                fill, border, text = self._node_style("known", palette)
                symbol = "."
            elif status == "locked":
                fill, border, text = self._node_style("locked", palette)
                symbol = "?"
            else:
                symbol = self.ROLE_SYMBOLS.get(room.role, "?")
                fill, border, text = self._node_style("known_reachable", palette)
            cx, cy = center_for(self._room_anchor(room))
            token = MapTokenLabel(
                text=escape_kivy_markup(symbol),
                font_size=font_size,
                bold=True,
                size=(tile, tile),
                pos=(cx - tile / 2, cy - tile / 2),
            )
            token.set_style(fill=fill, border=border, text=text)
            self.add_widget(token)


class NativeMapView(BoxLayout):
    MAP_HEIGHT_MIN = 260
    MAP_HEIGHT_MAX = 560

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            spacing=dp(5),
            **kwargs,
        )
        self._dark_mode = True
        self.header = Label(
            text="",
            markup=True,
            color=(0.96, 0.78, 0.28, 1),
            font_size="15sp",
            bold=True,
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
        )
        self.header.bind(size=self._sync_header)
        self.canvas_widget = NativeMapCanvas()
        self.info = WrappedLabel(
            text="",
            markup=True,
            color=(0.82, 0.76, 0.65, 1),
            font_size="12sp",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self.add_widget(self.header)
        self.add_widget(self.canvas_widget)
        self.add_widget(self.info)

    def _sync_header(self, instance: Label, _value) -> None:
        instance.text_size = (instance.width, None)

    def set_dark_mode(self, enabled: bool) -> None:
        self._dark_mode = bool(enabled)
        self.header.color = (0.96, 0.78, 0.28, 1) if self._dark_mode else (0.18, 0.12, 0.06, 1)
        self.info.color = (0.82, 0.76, 0.65, 1) if self._dark_mode else (0.28, 0.22, 0.14, 1)
        self.canvas_widget.set_dark_mode(enabled)

    def hide_map(self) -> None:
        self.canvas_widget.clear_map()
        self.header.text = ""
        self.info.text = ""
        self.height = 0
        self.opacity = 0
        self.disabled = True

    def _show(self, desired_height: float) -> None:
        self.height = max(dp(self.MAP_HEIGHT_MIN), min(dp(self.MAP_HEIGHT_MAX), desired_height))
        self.opacity = 1
        self.disabled = False

    def show_overworld(self, *, title: str, blueprint, state) -> None:
        positions = getattr(blueprint, "overworld_positions", {})
        rows = 6
        if positions:
            rows = max(y for _, y in positions.values()) - min(y for _, y in positions.values()) + 1
        self._show(dp(140) + rows * dp(52))
        self.header.text = f"[b]{escape_kivy_markup(title)}[/b]"
        self.info.text = self._overworld_info_markup(blueprint, state)
        self.info._sync_text_size()
        self.info._sync_height()
        self.canvas_widget.show_overworld(blueprint, state)

    def show_dungeon(self, *, title: str, dungeon, state) -> None:
        rows = max(1, dungeon.height * 2 - 1)
        self._show(dp(125) + rows * dp(44))
        self.header.text = f"[b]{escape_kivy_markup(title)}[/b]"
        self.info.text = self._dungeon_info_markup(dungeon, state)
        self.info._sync_text_size()
        self.info._sync_height()
        self.canvas_widget.show_dungeon(dungeon, state)

    def _overworld_info_markup(self, blueprint, state) -> str:
        current = blueprint.nodes.get(state.current_node_id)
        known_count = sum(
            1
            for node in blueprint.nodes.values()
            if node.node_id == state.current_node_id or node.node_id in state.visited_nodes
        )
        travel_labels: list[str] = []
        for edge in available_travel_edges(blueprint, state):
            target = blueprint.nodes[edge.to_node_id]
            label = target.title if target.node_id in state.visited_nodes else edge.label
            travel_labels.append(label)
        travel = "; ".join(travel_labels[:3]) if travel_labels else "No open route from here"
        if len(travel_labels) > 3:
            travel += f"; +{len(travel_labels) - 3} more"
        lines = [
            f"[b]Here[/b]: {escape_kivy_markup(current.title if current is not None else 'Unknown')}",
            f"[b]Known[/b]: {known_count}/{len(blueprint.nodes)}",
            f"[b]Open routes[/b]: {escape_kivy_markup(travel)}",
        ]
        pressure = self._act2_pressure_markup(state)
        if pressure:
            lines.append(pressure)
        return "\n".join(lines)

    def _dungeon_info_markup(self, dungeon, state) -> str:
        room = dungeon.rooms[state.current_room_id or dungeon.entrance_room_id]
        exits = current_room_exits(dungeon, state)
        directions = room_exit_directions(room, exits, dungeon=dungeon) if exits else {}
        exit_text = ", ".join(
            f"{directions[exit_room.room_id]} {exit_room.title}" for exit_room in exits[:4]
        )
        if not exit_text:
            exit_text = "No visible exit"
        elif len(exits) > 4:
            exit_text += f", +{len(exits) - 4} more"
        lines = [
            f"[b]Room[/b]: {escape_kivy_markup(room.title)}",
            f"[b]Role[/b]: {escape_kivy_markup(room.role.upper())}",
            f"[b]Exits[/b]: {escape_kivy_markup(exit_text)}",
            "[b]Legend[/b]: P you, . cleared, E fight, * event, T treasure, B boss, ? locked",
        ]
        pressure = self._act2_pressure_markup(state)
        if pressure:
            lines.insert(3, pressure)
        return "\n".join(lines)

    def _act2_pressure_markup(self, state) -> str:
        values = getattr(state, "flag_values", {})
        if not values or not any(key in values for key in ("act2_town_stability", "act2_route_control", "act2_whisper_pressure")):
            return ""
        parts: list[str] = []
        for key, label in (
            ("act2_town_stability", "Town"),
            ("act2_route_control", "Routes"),
            ("act2_whisper_pressure", "Whispers"),
        ):
            value = values.get(key, 0)
            if isinstance(value, bool) or not isinstance(value, int | float):
                value = 0
            parts.append(f"{label} {max(0, min(5, int(value)))}/5")
        return f"[b]Pressure[/b]: {escape_kivy_markup(' | '.join(parts))}"


class NativeCommandWorkspace(BoxLayout):
    RARITY_HEX = {
        "common": "f0e7d1",
        "uncommon": "86efac",
        "rare": "70a8ff",
        "epic": "d58cff",
        "legendary": "facc15",
    }

    def __init__(self, screen: "GameScreen", **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(6),
            size_hint=(1, 1),
            opacity=0,
            disabled=True,
            **kwargs,
        )
        self.screen = screen
        self.mode = ""
        self.inventory_filter_key = "all"
        self.inventory_selected_item_id: str | None = None
        self.inventory_use_item_id: str | None = None
        self.gear_selected_member_index = 0
        self.gear_selected_slot: str | None = None
        self.camp_view = "overview"
        self.journal_section_index = 0
        self.map_view_key = "route"
        self.map_view = NativeMapView()
        self.feedback_message = ""
        self.confirm_action: dict[str, object] | None = None

    def _theme(self) -> dict[str, tuple[float, float, float, float]]:
        return self.screen.theme

    def _activate_mode(self, mode: str) -> None:
        if self.mode != mode:
            self.feedback_message = ""
        self.mode = mode

    def _compact_layout(self) -> bool:
        width = self.width
        if width <= dp(80):
            width = getattr(self.screen, "width", width)
        return width < dp(240)

    def _split_body(
        self,
        *,
        first_weight: float = 0.5,
        second_weight: float = 0.5,
    ) -> tuple[BoxLayout, tuple[float, float], tuple[float, float]]:
        if self._compact_layout():
            return (
                BoxLayout(orientation="vertical", spacing=dp(6)),
                (1, first_weight),
                (1, second_weight),
            )
        return (
            BoxLayout(orientation="horizontal", spacing=dp(6)),
            (first_weight, 1),
            (second_weight, 1),
        )

    def _rarity_hex(self, rarity: str) -> str:
        return self.RARITY_HEX.get(str(rarity), self.RARITY_HEX["common"])

    def _sync_label(self, label: Label, *_args) -> None:
        label.text_size = (max(1, label.width - dp(8)), None)
        label.height = max(dp(24), label.texture_size[1] + dp(8))

    def _sync_button(self, button: Button, *_args) -> None:
        button.text_size = (
            max(1, button.width - dp(16)),
            max(1, button.height - dp(8)),
        )

    def _label(
        self,
        text: str,
        *,
        font_size: str = "14sp",
        bold: bool = False,
        color: tuple[float, float, float, float] | None = None,
        height: float | None = None,
    ) -> WrappedLabel:
        label = WrappedLabel(
            text=text,
            markup=True,
            color=color or self._theme()["text"],
            font_size=font_size,
            bold=bold,
            halign="left",
            valign="top",
            size_hint_y=None,
            height=height if height is not None else dp(28),
        )
        self.screen._apply_font(label, "ui")
        label.bind(width=self._sync_label, texture_size=self._sync_label)
        self._sync_label(label)
        return label

    def _button_font_size(self, text: str, font_size: str) -> str:
        if str(text).strip().upper() == "X":
            return font_size
        match = re.fullmatch(r"(\d+(?:\.\d+)?)sp", str(font_size).strip())
        if match is None:
            return font_size
        return f"{max(14.0, float(match.group(1))):g}sp"

    def _button(
        self,
        text: str,
        callback,
        *,
        role: str = "choice",
        height: float = 44,
        font_size: str = "13sp",
        selected: bool = False,
        disabled: bool = False,
    ) -> Button:
        theme = self._theme()
        if selected:
            background = theme["choice_group_bg"]
            color = theme["choice_group_text"]
        elif role == "back":
            background = theme["choice_back_bg"]
            color = theme["choice_back_text"]
        elif role == "danger":
            background = theme["choice_end_turn_bg"]
            color = theme["choice_end_turn_text"]
        else:
            background = theme["choice_bg"]
            color = theme["choice_text"]
        button = Button(
            text=text,
            markup=True,
            background_normal="",
            background_color=background,
            color=color,
            font_size=self._button_font_size(text, font_size),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(height),
            disabled=disabled,
            opacity=0.58 if disabled else 1,
        )
        self.screen._apply_font(button, "ui")
        button.bind(size=self._sync_button)
        self._sync_button(button)
        if callback is not None and not disabled:
            button.bind(on_release=lambda *_args: callback())
        return button

    def _scrolling_grid(self) -> tuple[ScrollView, GridLayout]:
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)
        return scroll, grid

    def _scroll_label(self, label: WrappedLabel) -> ScrollView:
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(label)
        Clock.schedule_once(lambda _dt: setattr(scroll, "scroll_y", 1), 0)
        return scroll

    def _panel(self, *, orientation: str = "vertical", size_hint=(1, 1), padding: int = 6) -> PanelBox:
        return PanelBox(
            orientation=orientation,
            size_hint=size_hint,
            padding=[dp(padding), dp(padding), dp(padding), dp(padding)],
            spacing=dp(5),
            background_color=self._theme()["panel"],
            radius=5,
        )

    def _command_nav(self, active: str) -> BoxLayout:
        nav = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=None, height=dp(42))
        for mode, label in (
            ("map", "Map"),
            ("journal", "Journal"),
            ("inventory", "Items"),
            ("gear", "Gear"),
            ("camp", "Camp"),
        ):
            callback = {
                "map": self.render_map,
                "journal": self.render_journal,
                "inventory": self.render_inventory,
                "gear": self.render_gear,
                "camp": self.render_camp,
            }[mode]
            nav.add_widget(
                self._button(
                    label,
                    callback,
                    height=38,
                    font_size="13sp",
                    selected=mode == active,
                )
            )
        close_button = self._button(
            "X",
            self.screen.close_side_command_panel,
            role="back",
            height=30,
            font_size="11sp",
        )
        close_button.size_hint_x = None
        close_button.width = dp(30)
        nav.add_widget(close_button)
        return nav

    def show(self) -> None:
        self.opacity = 1
        self.disabled = False

    def hide(self) -> None:
        self.opacity = 0
        self.disabled = True
        self.clear_widgets()
        self.mode = ""
        self.confirm_action = None
        self.inventory_use_item_id = None
        self.map_view.hide_map()

    def refresh_active(self) -> None:
        if self.mode == "journal":
            self.render_journal()
        elif self.mode == "inventory":
            self.render_inventory(
                filter_key=self.inventory_filter_key,
                selected_item_id=self.inventory_selected_item_id,
            )
        elif self.mode == "gear":
            self.render_gear(
                selected_member_index=self.gear_selected_member_index,
                selected_slot=self.gear_selected_slot,
            )
        elif self.mode == "camp":
            self.render_camp(view=self.camp_view)
        elif self.mode == "map":
            self.render_map(view=self.map_view_key)

    def render_command(self, command: str) -> None:
        normalized = " ".join(str(command).strip().lower().split())
        self.confirm_action = None
        self.inventory_use_item_id = None
        if normalized in {"map", "maps", "map menu"}:
            self.render_map()
        elif normalized == "journal":
            self.render_journal()
        elif normalized in {"inventory", "backpack", "bag"}:
            self.render_inventory()
        elif normalized in {"gear", "equipment"}:
            self.render_gear()
        elif normalized == "camp":
            self.render_camp()

    def go_back(self) -> None:
        self.confirm_action = None
        self.inventory_use_item_id = None
        if self.mode == "camp" and self.camp_view != "overview":
            self.render_camp(view="overview")
            return
        self.screen.close_side_command_panel()

    def set_feedback(self, message: str) -> None:
        self.feedback_message = str(message or "")

    def _feedback_label(self) -> WrappedLabel | None:
        if not self.feedback_message:
            return None
        return self._label(
            f"[color=#d6c59a]{escape_kivy_markup(self.feedback_message)}[/color]",
            font_size="12sp",
        )

    def _confirmation_panel(self, prompt: str, confirm_callback, cancel_callback) -> PanelBox:
        panel = self._panel(padding=6)
        panel.size_hint_y = None
        panel.height = dp(108)
        panel.add_widget(self._label(f"[b][color=#facc15]{escape_kivy_markup(prompt)}[/color][/b]", font_size="13sp"))
        row = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(42))
        row.add_widget(self._button("Confirm", confirm_callback, height=38, font_size="12sp", selected=True))
        row.add_widget(self._button("Cancel", cancel_callback, role="back", height=38, font_size="12sp"))
        panel.add_widget(row)
        return panel

    def _section_title(self, title: str, subtitle: str = "") -> WrappedLabel:
        subtitle_markup = f"\n[size=12sp][color=#b9ad91]{escape_kivy_markup(subtitle)}[/color][/size]" if subtitle else ""
        return self._label(
            f"[size=17sp][b][color=#facc15]{escape_kivy_markup(title)}[/color][/b][/size]{subtitle_markup}",
            font_size="15sp",
            bold=True,
        )

    def _stat_line(self, label: str, value: str) -> str:
        return f"[b][color=#d6c59a]{escape_kivy_markup(label)}[/color][/b] {escape_kivy_markup(value)}"

    def _member_health_text(self, member) -> str:
        current_hp = max(0, int(getattr(member, "current_hp", 0)))
        max_hp = max(0, int(getattr(member, "max_hp", 0)))
        temp_hp = max(0, int(getattr(member, "temp_hp", 0)))
        suffix = ""
        if getattr(member, "dead", False):
            suffix = " (dead)"
        elif current_hp == 0:
            suffix = " (down)"
        temp = f", temp {temp_hp}" if temp_hp else ""
        return f"HP {current_hp}/{max_hp}{temp}{suffix}"

    def _active_map_context(self, game) -> dict[str, object] | None:
        if game is None or getattr(game, "state", None) is None:
            return None
        if getattr(game, "act2_hybrid_map_available", lambda: False)():
            state = game.act2_map_state()
            return {
                "act": "Act II",
                "route_title": "Act II Route Map",
                "site_empty": "There is no Act II site map to show from this location.",
                "blueprint": ACT2_ENEMY_DRIVEN_MAP,
                "state": state,
                "dungeon": game.current_act2_dungeon(),
            }
        if getattr(game, "act1_hybrid_map_available", lambda: False)():
            state = game.act1_map_state()
            return {
                "act": "Act I",
                "route_title": "Act I Overworld",
                "site_empty": "There is no dungeon map to show from this location.",
                "blueprint": ACT1_HYBRID_MAP,
                "state": state,
                "dungeon": game.current_act1_dungeon(),
            }
        return None

    def _map_subtitle(self, context: dict[str, object]) -> str:
        blueprint = context["blueprint"]
        state = context["state"]
        current = getattr(blueprint, "nodes", {}).get(getattr(state, "current_node_id", ""))
        if current is None:
            return str(context["act"])
        return f"{context['act']} | {current.title}"

    def _map_ledger_markup(self, context: dict[str, object]) -> str:
        blueprint = context["blueprint"]
        state = context["state"]
        current = blueprint.nodes.get(state.current_node_id)
        known_count = sum(
            1
            for node in blueprint.nodes.values()
            if node.node_id == state.current_node_id or node.node_id in state.visited_nodes
        )
        travel_labels: list[str] = []
        for edge in available_travel_edges(blueprint, state):
            target = blueprint.nodes[edge.to_node_id]
            label = target.title if target.node_id in state.visited_nodes else edge.label
            travel_labels.append(label)
        travel = "\n".join(f"  - {escape_kivy_markup(label)}" for label in travel_labels[:6])
        if not travel:
            travel = "  - No open route from here"
        elif len(travel_labels) > 6:
            travel += f"\n  - +{len(travel_labels) - 6} more"

        lines = [
            "[size=16sp][b][color=#facc15]Travel Ledger[/color][/b][/size]",
            self._stat_line("Current", current.title if current is not None else "Unknown"),
            self._stat_line("Known", f"{known_count}/{len(blueprint.nodes)}"),
            "[b][color=#d6c59a]Open Routes[/color][/b]",
            travel,
        ]
        pressure = self.map_view._act2_pressure_markup(state)
        if pressure:
            lines.append(pressure)

        dungeon = context["dungeon"]
        if dungeon is not None:
            room = dungeon.rooms[state.current_room_id or dungeon.entrance_room_id]
            exits = current_room_exits(dungeon, state)
            exit_text = ", ".join(exit_room.title for exit_room in exits[:4])
            if not exit_text:
                exit_text = "No visible exit"
            elif len(exits) > 4:
                exit_text += f", +{len(exits) - 4} more"
            lines.extend(
                [
                    "",
                    "[size=15sp][b][color=#facc15]Current Site[/color][/b][/size]",
                    self._stat_line("Site", dungeon.title),
                    self._stat_line("Room", room.title),
                    self._stat_line("Exits", exit_text),
                ]
            )
        return "\n".join(lines)

    def _map_tabs(self, context: dict[str, object], active: str) -> GridLayout:
        dungeon = context["dungeon"]
        tabs = GridLayout(cols=3, spacing=dp(5), size_hint_y=None, height=dp(42))
        options = (
            ("ledger", "Ledger", True),
            ("route", "Route", True),
            ("site", "Site", dungeon is not None),
        )
        for key, label, enabled in options:
            tabs.add_widget(
                self._button(
                    label,
                    lambda view_key=key: self.render_map(view=view_key),
                    height=38,
                    font_size="12sp",
                    selected=key == active,
                    disabled=not enabled,
                )
            )
        return tabs

    def render_map(self, *, view: str | None = None) -> None:
        self._activate_mode("map")
        if view is not None:
            self.map_view_key = str(view or "route")
        self.clear_widgets()
        self.map_view.hide_map()
        if self.map_view.parent is not None:
            self.map_view.parent.remove_widget(self.map_view)
        game = self.screen.active_game()
        context = self._active_map_context(game)
        self.add_widget(self._command_nav("map"))
        if context is None:
            self.add_widget(self._section_title("Map", "No active route map"))
            self.add_widget(self._label("[color=#8f7d62]There is no active hybrid map at this point in the adventure.[/color]"))
            return

        dungeon = context["dungeon"]
        if self.map_view_key == "site" and dungeon is None:
            self.map_view_key = "route"
        if self.map_view_key not in {"ledger", "route", "site"}:
            self.map_view_key = "route"

        self.add_widget(self._section_title("Map", self._map_subtitle(context)))
        self.add_widget(self._map_tabs(context, self.map_view_key))
        if self.map_view_key == "ledger":
            label = self._label(self._map_ledger_markup(context), font_size="13sp")
            self.add_widget(self._scroll_label(label))
            return

        panel = self._panel(padding=4)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self.map_view)
        panel.add_widget(scroll)
        self.add_widget(panel)
        self.map_view.set_dark_mode(getattr(self.screen, "kivy_dark_mode_enabled", True))
        if self.map_view_key == "site" and dungeon is not None:
            self.map_view.show_dungeon(title=dungeon.title, dungeon=dungeon, state=context["state"])
        else:
            self.map_view.show_overworld(
                title=str(context["route_title"]),
                blueprint=context["blueprint"],
                state=context["state"],
            )

    def render_journal(self, *, section_index: int | None = None) -> None:
        self._activate_mode("journal")
        if section_index is not None:
            self.journal_section_index = int(section_index)
        self.clear_widgets()
        game = self.screen.active_game()
        if game is None or getattr(game, "state", None) is None:
            self.add_widget(self._label("[color=#8f7d62]There is no active journal yet.[/color]"))
            return
        snapshot = build_journal_snapshot(game)
        self.add_widget(self._command_nav("journal"))
        tabs = GridLayout(cols=4, rows=2, spacing=dp(5), size_hint_y=None, height=dp(76))
        sections = (
            ("Snapshot", self._journal_snapshot_markup(snapshot)),
            ("Quests", self._journal_quests_markup(snapshot)),
            ("Clues", self._numbered_markup("Unresolved Clues", snapshot.unresolved_clues, empty="No unresolved clues tracked yet.")),
            ("Choices", self._numbered_markup("Major Choices", snapshot.major_choices, empty="No major choices logged yet.")),
            ("Pressure", self._numbered_markup("Faction Pressure", snapshot.faction_pressure, empty="No faction pressure tracked yet.")),
            ("Companions", self._numbered_markup("Companion Disposition", snapshot.companion_disposition, empty="No companion trust changes tracked yet.")),
            ("Updates", self._journal_updates_markup(snapshot)),
        )
        self.journal_section_index = max(0, min(self.journal_section_index, len(sections) - 1))
        content_label = self._label("", font_size="13sp")

        def set_section(index: int) -> None:
            title, markup = sections[index]
            content_label.text = markup
            if getattr(self.screen, "_side_panel_mode", "") != "native_command":
                self.screen.side_command_title_label.text = escape_kivy_markup(f"Journal - {title}")
            self._sync_label(content_label)

        for index, (label, _markup) in enumerate(sections):
            tabs.add_widget(
                self._button(
                    escape_kivy_markup(label),
                    lambda value=index: self.render_journal(section_index=value),
                    height=34,
                    font_size="12sp",
                    selected=index == self.journal_section_index,
                )
            )
        self.add_widget(tabs)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(content_label)
        self.add_widget(scroll)
        if snapshot.empty_message:
            content_label.text = f"[color=#8f7d62]{escape_kivy_markup(snapshot.empty_message)}[/color]"
        else:
            set_section(self.journal_section_index)
        Clock.schedule_once(lambda _dt: setattr(scroll, "scroll_y", 1), 0)

    def _journal_snapshot_markup(self, snapshot) -> str:
        lines = [
            "[size=17sp][b][color=#facc15]Campaign Snapshot[/color][/b][/size]",
            "",
            self._stat_line("Location", snapshot.location),
            self._stat_line("Objective", snapshot.objective),
            self._stat_line("Quest load", snapshot.quest_load),
            self._stat_line("Leads", snapshot.lead_count),
        ]
        for line in snapshot.extra_snapshot_lines:
            lines.append(self._stat_line("Act II", str(line)))
        consequences = "\n".join(f"{index}. {escape_kivy_markup(line)}" for index, line in enumerate(snapshot.consequences, start=1))
        if consequences:
            lines.extend(["", "[b][color=#d6c59a]Current Consequences[/color][/b]", consequences])
        return "\n".join(lines)

    def _journal_quests_markup(self, snapshot) -> str:
        lines = ["[size=17sp][b][color=#facc15]Quests[/color][/b][/size]"]
        groups = (
            ("Ready To Turn In", snapshot.ready_quests),
            ("Active", snapshot.active_quests),
            ("Completed", snapshot.completed_quests),
        )
        wrote_any = False
        for title, quests in groups:
            lines.extend(["", f"[b][color=#d6c59a]{escape_kivy_markup(title)}[/color][/b]"])
            if not quests:
                lines.append("[color=#8f7d62]Nothing logged.[/color]")
                continue
            wrote_any = True
            for quest in quests:
                lines.append(f"[b]{escape_kivy_markup(quest.title)}[/b] [color=#8f7d62]{escape_kivy_markup(quest.giver)}[/color]")
                if quest.summary and title == "Active":
                    lines.append(escape_kivy_markup(quest.summary))
                lines.append(self._stat_line("Objective", quest.objective))
                if title == "Ready To Turn In":
                    lines.append(self._stat_line("Turn in", quest.turn_in))
                lines.append(self._stat_line("Rewards", quest.rewards))
                if quest.latest_note:
                    lines.append(self._stat_line("Latest", quest.latest_note))
                lines.append("")
        if not wrote_any:
            lines.append("[color=#8f7d62]No quest entries are tracked yet.[/color]")
        return "\n".join(lines).strip()

    def _numbered_markup(self, title: str, lines: tuple[str, ...], *, empty: str) -> str:
        output = [f"[size=17sp][b][color=#facc15]{escape_kivy_markup(title)}[/color][/b][/size]", ""]
        if not lines:
            output.append(f"[color=#8f7d62]{escape_kivy_markup(empty)}[/color]")
            return "\n".join(output)
        output.extend(f"{index}. {escape_kivy_markup(line)}" for index, line in enumerate(lines, start=1))
        return "\n".join(output)

    def _inventory_filter_button_text(self, filter_snapshot) -> str:
        count = max(0, int(getattr(filter_snapshot, "count", 0)))
        noun = "item" if count == 1 else "items"
        return (
            f"[b]{escape_kivy_markup(filter_snapshot.label)}[/b]\n"
            f"[size=10sp]{count} {noun}[/size]"
        )

    def _journal_updates_markup(self, snapshot) -> str:
        lines = ["[size=17sp][b][color=#facc15]Recent Updates[/color][/b][/size]", ""]
        if not snapshot.recent_updates:
            lines.append("[color=#8f7d62]No recent updates logged.[/color]")
        else:
            lines.extend(f"{index}. {escape_kivy_markup(line)}" for index, line in enumerate(snapshot.recent_updates, start=1))
        if snapshot.older_note_count:
            lines.extend(["", f"[color=#d6c59a]Older notes archived in this run: {snapshot.older_note_count}[/color]"])
        return "\n".join(lines)

    def render_inventory(self, *, filter_key: str = "all", selected_item_id: str | None = None) -> None:
        self._activate_mode("inventory")
        if selected_item_id != self.inventory_selected_item_id:
            self.inventory_use_item_id = None
            self.confirm_action = None
        self.inventory_filter_key = filter_key
        self.inventory_selected_item_id = selected_item_id
        self.clear_widgets()
        game = self.screen.active_game()
        if game is None or getattr(game, "state", None) is None:
            self.add_widget(self._label("[color=#8f7d62]There is no shared inventory yet.[/color]"))
            return
        snapshot = build_inventory_snapshot(game, filter_key=filter_key, selected_item_id=selected_item_id)
        self.inventory_filter_key = snapshot.filter_key
        self.inventory_selected_item_id = snapshot.selected_item_id
        self.add_widget(self._command_nav("inventory"))
        self.add_widget(
            self._section_title(
                "Shared Inventory",
                f"{snapshot.gold_label} | Supplies {snapshot.supply_points} | {snapshot.total_available} free / {snapshot.total_quantity} carried",
            )
        )
        feedback = self._feedback_label()
        if feedback is not None:
            self.add_widget(feedback)

        filter_grid = GridLayout(cols=2, rows=4, spacing=dp(5), size_hint_y=None, height=dp(172))
        for filter_snapshot in snapshot.filters:
            filter_grid.add_widget(
                self._button(
                    self._inventory_filter_button_text(filter_snapshot),
                    lambda key=filter_snapshot.key: self.render_inventory(filter_key=key),
                    height=38,
                    font_size="11sp",
                    selected=filter_snapshot.key == snapshot.filter_key,
                )
            )
        self.add_widget(filter_grid)

        body, list_hint, detail_hint = self._split_body(first_weight=0.46, second_weight=0.54)
        list_panel = self._panel(size_hint=list_hint, padding=4)
        detail_panel = self._panel(size_hint=detail_hint, padding=6)
        scroll, grid = self._scrolling_grid()
        if not snapshot.items:
            grid.add_widget(self._label(f"[color=#8f7d62]{escape_kivy_markup(snapshot.empty_message)}[/color]"))
        for item in snapshot.items:
            rarity = self._rarity_hex(item.rarity)
            free_text = f"{item.available} free" if item.equipped else f"x{item.quantity}"
            if item.equipped:
                free_text += f" | {item.equipped} equipped"
            row = (
                f"[b][color=#{rarity}]{escape_kivy_markup(item.name)}[/color][/b]\n"
                f"[size=11sp]{escape_kivy_markup(item.kind_label)} | {escape_kivy_markup(item.rarity_title)} | {escape_kivy_markup(free_text)}[/size]"
            )
            grid.add_widget(
                self._button(
                    row,
                    lambda value=item.item_id: self.render_inventory(filter_key=snapshot.filter_key, selected_item_id=value),
                    height=58,
                    font_size="12sp",
                    selected=item.item_id == snapshot.selected_item_id,
                )
            )
        list_panel.add_widget(scroll)
        detail_panel.add_widget(self._scroll_label(self._inventory_detail_label(snapshot.selected_item)))
        controls = self._inventory_controls(snapshot.selected_item)
        if controls is not None:
            detail_panel.add_widget(controls)
        body.add_widget(list_panel)
        body.add_widget(detail_panel)
        self.add_widget(body)
        Clock.schedule_once(lambda _dt: setattr(scroll, "scroll_y", 1), 0)

    def _inventory_detail_label(self, item) -> WrappedLabel:
        if item is None:
            return self._label("[color=#8f7d62]Select an item to inspect it.[/color]")
        rarity = self._rarity_hex(item.rarity)
        action_bits = []
        if item.usable:
            action_bits.append("Usable")
        if item.equippable:
            action_bits.append(f"Equips: {item.slot_label or 'Gear'}")
        action_text = " | ".join(action_bits) if action_bits else "No direct action"
        lines = [
            f"[size=17sp][b][color=#{rarity}]{escape_kivy_markup(item.name)}[/color][/b][/size]",
            f"[color=#b9ad91]{escape_kivy_markup(item.rarity_title)} {escape_kivy_markup(item.kind_label)}[/color]",
            "",
            self._stat_line("Quantity", f"{item.quantity} carried | {item.available} free | {item.equipped} equipped"),
            self._stat_line("Value", item.value_label),
            self._stat_line("Supply", item.supply_label),
            self._stat_line("Action flags", action_text),
            "",
            escape_kivy_markup(item.description),
        ]
        if item.rules:
            lines.extend(["", "[b][color=#d6c59a]Rules[/color][/b]", escape_kivy_markup(item.rules)])
        if item.source:
            lines.extend(["", "[b][color=#d6c59a]Source[/color][/b]", escape_kivy_markup(item.source)])
        return self._label("\n".join(lines), font_size="13sp")

    def _inventory_controls(self, item):
        if item is None:
            return None
        game = self.screen.active_game()
        if game is None:
            return None
        if self.confirm_action and self.confirm_action.get("mode") == "inventory":
            action = str(self.confirm_action.get("action", ""))
            if action == "drop":
                return self._confirmation_panel(
                    f"Drop {item.name}?",
                    lambda: self._confirm_drop_item(str(self.confirm_action.get("item_id", item.item_id))),
                    lambda: self._cancel_inventory_action(),
                )
            if action == "use":
                target_index = int(self.confirm_action.get("target_index", 0) or 0)
                target = game.state.party_members()[target_index] if game.state is not None and 0 <= target_index < len(game.state.party_members()) else None
                target_name = getattr(target, "name", "this ally")
                return self._confirmation_panel(
                    f"Use {item.name} on {target_name}?",
                    lambda: self._confirm_use_item(str(self.confirm_action.get("item_id", item.item_id)), target_index),
                    lambda: self._cancel_inventory_action(),
                )
        if self.inventory_use_item_id == item.item_id:
            panel = self._panel(padding=6)
            panel.size_hint_y = None
            targets = usable_inventory_targets(game, item.item_id)
            rows = max(1, min(4, len(targets) + 1))
            panel.height = dp(38 + rows * 42)
            panel.add_widget(self._label("[b][color=#facc15]Choose Target[/color][/b]", font_size="12sp"))
            target_scroll, grid = self._scrolling_grid()
            target_scroll.size_hint_y = None
            target_scroll.height = dp(rows * 42)
            if not targets:
                grid.add_widget(self._label("[color=#8f7d62]No valid target right now.[/color]", font_size="12sp"))
            for target_index, target in targets:
                label = f"{escape_kivy_markup(target.name)}\n[size=11sp]{escape_kivy_markup(self._member_health_text(target))}[/size]"
                grid.add_widget(
                    self._button(
                        label,
                        lambda idx=target_index: self._ask_use_item(item.item_id, idx),
                        height=38,
                        font_size="12sp",
                    )
                )
            grid.add_widget(self._button("Back", self._cancel_inventory_action, role="back", height=38, font_size="12sp"))
            panel.add_widget(target_scroll)
            return panel
        action_count = 1 if self._compact_layout() else 3
        row_height = 126 if self._compact_layout() else 44
        row = GridLayout(cols=action_count, spacing=dp(5), size_hint_y=None, height=dp(row_height))
        use_label = "Use"
        if not item.usable:
            use_label = "Use\n[size=11sp]No direct use[/size]"
        elif item.available <= 0:
            use_label = "Use\n[size=11sp]None free[/size]"
        drop_label = "Drop 1" if item.available > 0 else "Drop 1\n[size=11sp]None free[/size]"
        row.add_widget(
            self._button(
                use_label,
                lambda: self._start_use_item(item.item_id),
                height=40,
                font_size="12sp",
                disabled=not item.usable or item.available <= 0,
            )
        )
        row.add_widget(
            self._button(
                drop_label,
                lambda: self._ask_drop_item(item.item_id),
                height=40,
                font_size="12sp",
                disabled=item.available <= 0,
            )
        )
        row.add_widget(self._button("Back", self.go_back, role="back", height=40, font_size="12sp"))
        return row

    def _cancel_inventory_action(self) -> None:
        self.confirm_action = None
        self.inventory_use_item_id = None
        self.render_inventory(filter_key=self.inventory_filter_key, selected_item_id=self.inventory_selected_item_id)

    def _start_use_item(self, item_id: str) -> None:
        self.confirm_action = None
        self.inventory_use_item_id = item_id
        self.render_inventory(filter_key=self.inventory_filter_key, selected_item_id=item_id)

    def _ask_use_item(self, item_id: str, target_index: int) -> None:
        self.confirm_action = {"mode": "inventory", "action": "use", "item_id": item_id, "target_index": target_index}
        self.render_inventory(filter_key=self.inventory_filter_key, selected_item_id=item_id)

    def _confirm_use_item(self, item_id: str, target_index: int) -> None:
        self.confirm_action = None
        self.inventory_use_item_id = None
        result = use_inventory_item_on_target(self.screen.active_game(), item_id, target_index)
        self.set_feedback(result.message)
        self.render_inventory(filter_key=self.inventory_filter_key, selected_item_id=item_id)

    def _ask_drop_item(self, item_id: str) -> None:
        self.confirm_action = {"mode": "inventory", "action": "drop", "item_id": item_id}
        self.render_inventory(filter_key=self.inventory_filter_key, selected_item_id=item_id)

    def _confirm_drop_item(self, item_id: str) -> None:
        self.confirm_action = None
        result = drop_inventory_item(self.screen.active_game(), item_id, 1)
        self.set_feedback(result.message)
        self.render_inventory(filter_key=self.inventory_filter_key, selected_item_id=item_id)

    def render_gear(self, *, selected_member_index: int = 0, selected_slot: str | None = None) -> None:
        self._activate_mode("gear")
        if selected_member_index != self.gear_selected_member_index or selected_slot != self.gear_selected_slot:
            self.confirm_action = None
        self.gear_selected_member_index = selected_member_index
        self.gear_selected_slot = selected_slot
        self.clear_widgets()
        game = self.screen.active_game()
        if game is None or getattr(game, "state", None) is None:
            self.add_widget(self._label("[color=#8f7d62]There is no active party gear to manage yet.[/color]"))
            return
        snapshot = build_gear_snapshot(
            game,
            selected_member_index=selected_member_index,
            selected_slot=selected_slot,
        )
        self.gear_selected_member_index = snapshot.selected_member_index
        self.gear_selected_slot = snapshot.selected_slot
        self.add_widget(self._command_nav("gear"))
        subtitle = "Equipment changes are locked during combat." if snapshot.combat_locked else "Active loadouts and shared inventory candidates."
        self.add_widget(self._section_title("Gear", subtitle))
        feedback = self._feedback_label()
        if feedback is not None:
            self.add_widget(feedback)
        member_columns = max(1, min(3, len(snapshot.members) or 1))
        member_rows = max(1, math.ceil(max(1, len(snapshot.members)) / member_columns))
        member_grid = GridLayout(
            cols=member_columns,
            rows=member_rows,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(member_rows * 42 + max(0, member_rows - 1) * 5),
        )
        for member in snapshot.members:
            member_grid.add_widget(
                self._button(
                    escape_kivy_markup(member.name),
                    lambda index=member.index: self.render_gear(selected_member_index=index),
                    height=42,
                    font_size="12sp",
                    selected=member.index == snapshot.selected_member_index,
                )
            )
        self.add_widget(member_grid)
        if not snapshot.members:
            self.add_widget(self._label("[color=#8f7d62]No party members are available.[/color]"))
            return
        member = snapshot.members[snapshot.selected_member_index]
        body, slot_hint, detail_hint = self._split_body(first_weight=0.42, second_weight=0.58)
        slot_panel = self._panel(size_hint=slot_hint, padding=4)
        detail_panel = self._panel(size_hint=detail_hint, padding=6)
        scroll, grid = self._scrolling_grid()
        selected_slot_snapshot = None
        for slot in member.slots:
            if slot.slot == snapshot.selected_slot:
                selected_slot_snapshot = slot
            current = slot.current_name
            row = (
                f"[b][color=#facc15]{escape_kivy_markup(slot.label)}[/color][/b]\n"
                f"[size=11sp]{escape_kivy_markup(current)} | {len(slot.candidates)} candidate(s)[/size]"
            )
            grid.add_widget(
                self._button(
                    row,
                    lambda value=slot.slot: self.render_gear(
                        selected_member_index=snapshot.selected_member_index,
                        selected_slot=value,
                    ),
                    height=55,
                    font_size="12sp",
                    selected=slot.slot == snapshot.selected_slot,
                )
            )
        if selected_slot_snapshot is None and member.slots:
            selected_slot_snapshot = member.slots[0]
        slot_panel.add_widget(scroll)
        detail_panel.add_widget(self._scroll_label(self._gear_detail_label(member, selected_slot_snapshot, snapshot.combat_locked)))
        controls = self._gear_controls(member, selected_slot_snapshot, snapshot.combat_locked)
        if controls is not None:
            detail_panel.add_widget(controls)
        body.add_widget(slot_panel)
        body.add_widget(detail_panel)
        self.add_widget(body)
        Clock.schedule_once(lambda _dt: setattr(scroll, "scroll_y", 1), 0)

    def _gear_detail_label(self, member, slot, combat_locked: bool) -> WrappedLabel:
        if slot is None:
            return self._label("[color=#8f7d62]Select a slot to inspect it.[/color]")
        lines = [
            f"[size=17sp][b][color=#facc15]{escape_kivy_markup(member.name)} - {escape_kivy_markup(slot.label)}[/color][/b][/size]",
            f"[color=#b9ad91]{escape_kivy_markup(member.public_identity)}[/color]",
            "",
            self._stat_line("Health", member.health),
            self._stat_line("Combat", member.combat),
            self._stat_line("Conditions", member.conditions),
            self._stat_line("Resources", member.resources),
            "",
            self._stat_line("Current", slot.current_name),
        ]
        if slot.current_rules:
            lines.extend(["", "[b][color=#d6c59a]Current Rules[/color][/b]", escape_kivy_markup(slot.current_rules)])
        if slot.unequip_comparison:
            lines.extend(["", "[b][color=#d6c59a]Unequip Preview[/color][/b]", escape_kivy_markup(slot.unequip_comparison)])
        lines.extend(["", "[b][color=#d6c59a]Compatible Inventory[/color][/b]"])
        if not slot.candidates:
            lines.append("[color=#8f7d62]No unequipped inventory item fits this slot.[/color]")
        for candidate in slot.candidates:
            rarity = self._rarity_hex(candidate.rarity)
            lines.append(f"[color=#{rarity}][b]{escape_kivy_markup(candidate.name)}[/b][/color] x{candidate.available}")
            lines.append(escape_kivy_markup(candidate.comparison))
            if candidate.rules:
                lines.append(f"[size=12sp][color=#b9ad91]{escape_kivy_markup(candidate.rules)}[/color][/size]")
            lines.append("")
        if combat_locked:
            lines.append("[color=#f87171]Equipment changes are locked during combat.[/color]")
        return self._label("\n".join(lines).strip(), font_size="13sp")

    def _gear_controls(self, member, slot, combat_locked: bool):
        if slot is None:
            return None
        if self.confirm_action and self.confirm_action.get("mode") == "gear":
            action = str(self.confirm_action.get("action", ""))
            if action == "unequip":
                return self._confirmation_panel(
                    f"Clear {slot.label} for {member.name}?",
                    lambda: self._confirm_unequip_slot(member.index, slot.slot),
                    lambda: self._cancel_gear_action(),
                )
            if action == "equip":
                item_name = str(self.confirm_action.get("item_name", "this item"))
                return self._confirmation_panel(
                    f"Equip {item_name} in {slot.label}?",
                    lambda: self._confirm_equip_item(member.index, slot.slot, str(self.confirm_action.get("item_id", ""))),
                    lambda: self._cancel_gear_action(),
                )
        panel = self._panel(padding=6)
        button_count = 1 + len(slot.candidates) + (1 if slot.current_item_id else 0)
        rows = max(1, min(4, button_count))
        panel.size_hint_y = None
        panel.height = dp(42 + rows * 42)
        panel.add_widget(self._label("[b][color=#facc15]Gear Actions[/color][/b]", font_size="12sp"))
        scroll, grid = self._scrolling_grid()
        scroll.size_hint_y = None
        scroll.height = dp(rows * 42)
        if slot.current_item_id is not None:
            grid.add_widget(
                self._button(
                    f"Unequip {escape_kivy_markup(slot.current_name)}",
                    lambda: self._ask_unequip_slot(member.index, slot.slot),
                    height=38,
                    font_size="12sp",
                    disabled=combat_locked,
                )
            )
        for candidate in slot.candidates:
            label = (
                f"Equip {escape_kivy_markup(candidate.name)}\n"
                f"[size=11sp]{escape_kivy_markup(candidate.comparison)}[/size]"
            )
            grid.add_widget(
                self._button(
                    label,
                    lambda item_id=candidate.item_id, item_name=candidate.name: self._ask_equip_item(
                        member.index,
                        slot.slot,
                        item_id,
                        item_name,
                    ),
                    height=48,
                    font_size="11sp",
                    disabled=combat_locked,
                )
            )
        grid.add_widget(self._button("Back", self.go_back, role="back", height=38, font_size="12sp"))
        panel.add_widget(scroll)
        return panel

    def _cancel_gear_action(self) -> None:
        self.confirm_action = None
        self.render_gear(selected_member_index=self.gear_selected_member_index, selected_slot=self.gear_selected_slot)

    def _ask_unequip_slot(self, member_index: int, slot: str) -> None:
        self.confirm_action = {"mode": "gear", "action": "unequip", "member_index": member_index, "slot": slot}
        self.render_gear(selected_member_index=member_index, selected_slot=slot)

    def _confirm_unequip_slot(self, member_index: int, slot: str) -> None:
        self.confirm_action = None
        result = unequip_member_slot(self.screen.active_game(), member_index, slot)
        self.set_feedback(result.message)
        self.render_gear(selected_member_index=member_index, selected_slot=slot)

    def _ask_equip_item(self, member_index: int, slot: str, item_id: str, item_name: str) -> None:
        self.confirm_action = {
            "mode": "gear",
            "action": "equip",
            "member_index": member_index,
            "slot": slot,
            "item_id": item_id,
            "item_name": item_name,
        }
        self.render_gear(selected_member_index=member_index, selected_slot=slot)

    def _confirm_equip_item(self, member_index: int, slot: str, item_id: str) -> None:
        self.confirm_action = None
        result = equip_item_for_member(self.screen.active_game(), member_index, slot, item_id)
        self.set_feedback(result.message)
        self.render_gear(selected_member_index=member_index, selected_slot=slot)

    def render_camp(self, *, view: str = "overview") -> None:
        self._activate_mode("camp")
        self.camp_view = view
        self.inventory_use_item_id = None
        self.clear_widgets()
        game = self.screen.active_game()
        if game is None or getattr(game, "state", None) is None:
            self.add_widget(self._label("[color=#8f7d62]There is no active adventure yet, so camp is not available.[/color]"))
            return
        snapshot = build_camp_snapshot(game)
        self.add_widget(self._command_nav("camp"))
        self.add_widget(self._section_title("Camp", f"{snapshot.gold_label} | Supplies {snapshot.supply_points} | Short rests {snapshot.short_rests_remaining}"))
        feedback = self._feedback_label()
        if feedback is not None:
            self.add_widget(feedback)
        if self.confirm_action and self.confirm_action.get("mode") == "camp":
            confirmation = self._camp_confirmation()
            if confirmation is not None:
                self.add_widget(confirmation)
        if view == "party":
            self._render_camp_party(snapshot)
        elif view == "supplies":
            self._render_camp_supplies(snapshot)
        elif view == "recovery":
            self._render_camp_recovery(snapshot)
        elif view == "talk":
            self._render_camp_talk(snapshot)
        elif view == "banter":
            self._render_camp_banter(snapshot)
        else:
            self._render_camp_overview(snapshot)

    def _camp_confirmation(self):
        action = str(self.confirm_action.get("action", ""))
        if action == "short_rest":
            return self._confirmation_panel("Take a short rest?", self._confirm_short_rest, self._cancel_camp_action)
        if action == "long_rest":
            game = self.screen.active_game()
            cost = game.long_rest_supply_cost() if game is not None else 0
            return self._confirmation_panel(f"Take a long rest for {cost} supply points?", self._confirm_long_rest, self._cancel_camp_action)
        if action == "revive":
            return self._confirmation_panel(
                f"Use Revivify on {self.confirm_action.get('target_name', 'this ally')}?",
                lambda: self._confirm_revive(int(self.confirm_action.get("target_index", 0) or 0)),
                self._cancel_camp_action,
            )
        return None

    def _render_camp_overview(self, snapshot) -> None:
        body, status_hint, action_hint = self._split_body(first_weight=0.66, second_weight=0.34)
        status_panel = self._panel(size_hint=status_hint, padding=6)
        lines = [
            "[size=18sp][b][color=#facc15]Camp Ledger[/color][/b][/size]",
            "",
            self._stat_line("Gold", snapshot.gold_label),
            self._stat_line("Supplies", str(snapshot.supply_points)),
            self._stat_line("Short rests", str(snapshot.short_rests_remaining)),
            self._stat_line("Active party", str(snapshot.active_party_count)),
            self._stat_line("Camp roster", str(snapshot.camp_roster_count)),
        ]
        if snapshot.digest_lines:
            lines.extend(["", "[b][color=#d6c59a]Act II Digest[/color][/b]"])
            lines.extend(escape_kivy_markup(line) for line in snapshot.digest_lines)
        if snapshot.active_party:
            lines.extend(["", "[b][color=#d6c59a]Around The Fire[/color][/b]"])
            lines.extend(escape_kivy_markup(line) for line in snapshot.active_party)
        if snapshot.camp_roster:
            lines.extend(["", "[b][color=#d6c59a]Resting At Camp[/color][/b]"])
            lines.extend(escape_kivy_markup(line) for line in snapshot.camp_roster)
        else:
            lines.extend(["", "[b][color=#d6c59a]Resting At Camp[/color][/b]", "[color=#8f7d62]No companions are resting at camp right now.[/color]"])
        status_panel.add_widget(self._scroll_label(self._label("\n".join(lines), font_size="14sp")))

        action_panel = self._panel(size_hint=action_hint, padding=6)
        scroll, grid = self._scrolling_grid()
        action_map = {
            "recovery": lambda: self.render_camp(view="recovery"),
            "talk": lambda: self.render_camp(view="talk"),
            "mirror": self._show_magic_mirror_reason,
            "banter": lambda: self.render_camp(view="banter"),
        }
        for action in snapshot.actions:
            text = escape_kivy_markup(action.label)
            if action.reason:
                text += f"\n[size=11sp]{escape_kivy_markup(action.reason)}[/size]"
            grid.add_widget(
                self._button(
                    text,
                    action_map.get(action.key, lambda: None),
                    height=54,
                    font_size="14sp",
                    disabled=not action.enabled and action.key != "mirror",
                )
            )
        action_panel.add_widget(scroll)
        body.add_widget(status_panel)
        body.add_widget(action_panel)
        self.add_widget(body)

    def _render_camp_party(self, snapshot) -> None:
        body, active_hint, camp_hint = self._split_body(first_weight=0.5, second_weight=0.5)
        active_panel = self._panel(size_hint=active_hint, padding=6)
        camp_panel = self._panel(size_hint=camp_hint, padding=6)
        active_lines = ["[size=16sp][b][color=#facc15]Around The Fire[/color][/b][/size]", ""]
        active_lines.extend(escape_kivy_markup(line) for line in snapshot.active_party)
        camp_lines = ["[size=16sp][b][color=#facc15]Camp Roster[/color][/b][/size]", ""]
        if snapshot.camp_roster:
            camp_lines.extend(escape_kivy_markup(line) for line in snapshot.camp_roster)
        else:
            camp_lines.append("[color=#8f7d62]No companions are resting at camp right now.[/color]")
        active_panel.add_widget(self._scroll_label(self._label("\n".join(active_lines), font_size="13sp")))
        camp_panel.add_widget(self._scroll_label(self._label("\n".join(camp_lines), font_size="13sp")))
        body.add_widget(active_panel)
        body.add_widget(camp_panel)
        self.add_widget(body)
        self.add_widget(self._button("Back To Camp", lambda: self.render_camp(view="overview"), role="back", height=40, font_size="12sp"))

    def _render_camp_supplies(self, snapshot) -> None:
        del snapshot
        panel = self._panel(padding=8)
        panel.add_widget(self._label("[size=16sp][b][color=#facc15]Supplies And Equipment[/color][/b][/size]", font_size="14sp"))
        grid = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, height=dp(150))
        grid.add_widget(self._button("Open Inventory", lambda: self.render_inventory(), height=44, font_size="13sp"))
        grid.add_widget(self._button("Open Gear", lambda: self.render_gear(), height=44, font_size="13sp"))
        grid.add_widget(self._button("Back To Camp", lambda: self.render_camp(view="overview"), role="back", height=44, font_size="13sp"))
        panel.add_widget(grid)
        self.add_widget(panel)

    def _render_camp_recovery(self, snapshot) -> None:
        game = self.screen.active_game()
        panel = self._panel(padding=8)
        lines = [
            "[size=16sp][b][color=#facc15]Rest And Recovery[/color][/b][/size]",
            "",
            self._stat_line("Short rests", str(snapshot.short_rests_remaining)),
            self._stat_line("Supplies", str(snapshot.supply_points)),
        ]
        if game is not None:
            lines.append(self._stat_line("Long rest cost", str(game.long_rest_supply_cost())))
        panel.add_widget(self._label("\n".join(lines), font_size="13sp"))
        scroll, grid = self._scrolling_grid()
        scroll.size_hint_y = None
        scroll.height = dp(230)
        grid.add_widget(
            self._button(
                "Take Short Rest",
                self._ask_short_rest,
                height=44,
                font_size="13sp",
                disabled=snapshot.short_rests_remaining <= 0,
            )
        )
        grid.add_widget(
            self._button(
                "Take Long Rest",
                self._ask_long_rest,
                height=44,
                font_size="13sp",
                disabled=game is None or snapshot.supply_points < game.long_rest_supply_cost(),
            )
        )
        if game is not None:
            dead_allies = game.dead_allies_in_company()
            if dead_allies:
                for index, ally in enumerate(dead_allies):
                    grid.add_widget(
                        self._button(
                            f"Use Revivify: {escape_kivy_markup(ally.name)}",
                            lambda idx=index, name=ally.name: self._ask_revive(idx, name),
                            height=44,
                            font_size="13sp",
                            disabled=game.inventory_dict().get("scroll_revivify", 0) <= 0,
                        )
                    )
        grid.add_widget(self._button("Back To Camp", lambda: self.render_camp(view="overview"), role="back", height=44, font_size="13sp"))
        panel.add_widget(scroll)
        self.add_widget(panel)

    def _render_camp_talk(self, snapshot) -> None:
        del snapshot
        game = self.screen.active_game()
        panel = self._panel(padding=8)
        panel.add_widget(self._label("[size=16sp][b][color=#facc15]Talk To A Companion[/color][/b][/size]", font_size="14sp"))
        scroll, grid = self._scrolling_grid()
        if game is None or game.state is None or not game.state.all_companions():
            grid.add_widget(self._label("[color=#8f7d62]No companions are with your wider company yet.[/color]"))
        elif self.confirm_action and self.confirm_action.get("mode") == "camp_talk":
            companion_index = int(self.confirm_action.get("companion_index", 0) or 0)
            companions = game.state.all_companions()
            companion = companions[companion_index] if 0 <= companion_index < len(companions) else companions[0]
            lines = [
                f"[size=16sp][b][color=#facc15]{escape_kivy_markup(companion.name)}[/color][/b][/size]",
                "",
                escape_kivy_markup(game.companion_status_line(companion)),
                self._stat_line("Relationship", f"{game.relationship_label_for(companion)} ({companion.disposition})"),
            ]
            profile = COMPANION_PROFILES.get(companion.companion_id, {})
            if profile.get("summary"):
                lines.extend(["", escape_kivy_markup(str(profile["summary"]))])
            grid.add_widget(self._label("\n".join(lines), font_size="13sp"))
            grid.add_widget(self._button("Back To Companions", lambda: self._clear_camp_talk_selection(), role="back", height=40, font_size="12sp"))
        else:
            for index, companion in enumerate(game.state.all_companions()):
                grid.add_widget(
                    self._button(
                        f"{escape_kivy_markup(companion.name)}\n[size=11sp]{escape_kivy_markup(game.relationship_label_for(companion))} ({companion.disposition})[/size]",
                        lambda idx=index: self.screen.start_camp_companion_talk(idx),
                        height=48,
                        font_size="12sp",
                    )
                )
            grid.add_widget(self._button("Back To Camp", lambda: self.render_camp(view="overview"), role="back", height=40, font_size="12sp"))
        panel.add_widget(scroll)
        self.add_widget(panel)

    def _render_camp_banter(self, snapshot) -> None:
        del snapshot
        game = self.screen.active_game()
        panel = self._panel(padding=8)
        lines = ["[size=16sp][b][color=#facc15]Campfire Conversations[/color][/b][/size]", ""]
        if game is None:
            lines.append("[color=#8f7d62]No campfire is available right now.[/color]")
        else:
            banters = game.available_camp_banters()
            if not banters:
                lines.append("The campfire is companionable tonight, but no new conversation rises above the crackle.")
            else:
                for index, banter in enumerate(banters, start=1):
                    lines.append(f"{index}. {escape_kivy_markup(game.camp_banter_option_label(banter))}")
        panel.add_widget(self._scroll_label(self._label("\n".join(lines), font_size="13sp")))
        self.add_widget(panel)
        self.add_widget(self._button("Back To Camp", lambda: self.render_camp(view="overview"), role="back", height=40, font_size="12sp"))

    def _show_companion_talk(self, companion_index: int) -> None:
        self.confirm_action = {"mode": "camp_talk", "companion_index": companion_index}
        self.render_camp(view="talk")

    def _clear_camp_talk_selection(self) -> None:
        self.confirm_action = None
        self.render_camp(view="talk")

    def _cancel_camp_action(self) -> None:
        self.confirm_action = None
        self.render_camp(view=self.camp_view)

    def _ask_short_rest(self) -> None:
        self.confirm_action = {"mode": "camp", "action": "short_rest"}
        self.render_camp(view="recovery")

    def _confirm_short_rest(self) -> None:
        self.confirm_action = None
        result = take_short_rest(self.screen.active_game())
        self.set_feedback(result.message)
        self.render_camp(view="recovery")

    def _ask_long_rest(self) -> None:
        self.confirm_action = {"mode": "camp", "action": "long_rest"}
        self.render_camp(view="recovery")

    def _confirm_long_rest(self) -> None:
        self.confirm_action = None
        result = take_long_rest(self.screen.active_game())
        self.set_feedback(result.message)
        self.render_camp(view="recovery")

    def _ask_revive(self, target_index: int, target_name: str) -> None:
        self.confirm_action = {"mode": "camp", "action": "revive", "target_index": target_index, "target_name": target_name}
        self.render_camp(view="recovery")

    def _confirm_revive(self, target_index: int) -> None:
        self.confirm_action = None
        result = revive_dead_ally(self.screen.active_game(), target_index)
        self.set_feedback(result.message)
        self.render_camp(view="recovery")

    def _show_magic_mirror_reason(self) -> None:
        self.set_feedback(magic_mirror_unavailable_reason(self.screen.active_game()))
        self.render_camp(view="overview")


class ClickableGameBridge:
    FAST_REVEAL_COMMANDS = {
        "camp",
        "character",
        "characters",
        "gear",
        "help",
        "helpconsole",
        "inventory",
        "inv",
        "journal",
        "level",
        "load",
        "map",
        "maps",
        "party",
        "save",
        "saves",
        "settings",
        "sheet",
        "sheets",
    }

    def __init__(self, screen: "GameScreen", *, load_save: str | None = None):
        self.screen = screen
        self.load_save = load_save
        self.game: ClickableTextDnDGame | None = None
        self._responses: Queue[str] = Queue()
        self._worker: Thread | None = None
        self.waiting_for_input = False
        self._pending_non_dialogue_markups: list[str] = []
        self._pending_non_dialogue_fast_reveal = False
        self._fast_reveal_until_next_prompt = False
        self._side_command_depth = 0
        self._close_app_on_finish = False

    def start(self) -> None:
        if self._worker is not None:
            return
        self._worker = Thread(target=self._run_game, daemon=True)
        self._worker.start()

    def _run_game(self) -> None:
        game = ClickableTextDnDGame(self, save_dir=Path.cwd() / "saves")
        self.game = game
        try:
            if self.load_save:
                save_path = resolve_save_path(game, self.load_save)
                if save_path is None:
                    self.post_output(f"Save not found: {self.load_save}")
                    return
                game.load_save_path(save_path)
                game.play_current_state()
                return
            game.run()
        except Exception:
            self.post_output("")
            self.post_output("The clickable game window hit an unexpected error.")
            for line in traceback.format_exc().splitlines():
                self.post_output(line)
        finally:
            self.finish()
            self.game = None

    def finish(self) -> None:
        self.flush_pending_non_dialogue_output()
        close_app = self._close_app_on_finish
        self._close_app_on_finish = False
        Clock.schedule_once(lambda _dt: self.screen.finish_session(close_app=close_app))

    def close_app_on_finish(self) -> None:
        self._close_app_on_finish = True

    def post_output(self, text: object = "") -> None:
        markup, animated = format_kivy_log_entry(text)
        in_combat = self.screen.combat_active()
        if self.side_command_active:
            self.post_side_output(markup)
            return
        if should_buffer_kivy_non_dialogue_output(
            markup,
            animated=animated,
            source_text=text,
            enabled=self.screen.typing_animation_enabled,
            in_combat=in_combat,
        ):
            self._pending_non_dialogue_markups.append(markup)
            self._pending_non_dialogue_fast_reveal = (
                self._pending_non_dialogue_fast_reveal or self._fast_reveal_until_next_prompt
            )
            return
        self.flush_pending_non_dialogue_output()
        if in_combat:
            animated = False
        elif markup:
            Clock.schedule_once(lambda _dt: self.screen.restore_default_side_panel())
        self.post_preformatted_output(markup, animated=animated, fast_reveal=self._fast_reveal_until_next_prompt)

    @property
    def side_command_active(self) -> bool:
        return self._side_command_depth > 0

    def begin_side_command(self, title: str) -> None:
        self._side_command_depth += 1
        if self._side_command_depth > 1:
            return
        done = Event()
        Clock.schedule_once(lambda _dt: self.screen.begin_side_command(title, done_event=done))
        done.wait(timeout=1.0)

    def end_side_command(self) -> None:
        if self._side_command_depth > 0:
            self._side_command_depth -= 1

    def post_side_output(self, markup: str) -> None:
        done = Event()
        Clock.schedule_once(lambda _dt: self.screen.append_side_output(markup, done_event=done))
        done.wait(timeout=1.0)

    def show_dice_animation_frame(
        self,
        markup: str,
        *,
        final: bool = False,
        use_tray: bool = False,
        use_roll_tray: bool = False,
        tray_height: float | None = None,
        tray_parts: tuple[str, str, str] | None = None,
        pulse_scale: float = 1.0,
        core_slot_width: float | None = None,
        persist: bool = False,
    ) -> None:
        done = Event()
        Clock.schedule_once(
            lambda _dt: self.screen.show_dice_animation_frame(
                markup,
                final=final,
                use_tray=use_tray,
                use_roll_tray=use_roll_tray,
                tray_height=tray_height,
                tray_parts=tray_parts,
                pulse_scale=pulse_scale,
                core_slot_width=core_slot_width,
                persist=persist,
                done_event=done,
            )
        )
        done.wait(timeout=1.0)

    def append_dice_result(self, markup: str) -> None:
        done = Event()
        Clock.schedule_once(lambda _dt: self.screen.append_dice_result(markup, done_event=done))
        done.wait(timeout=1.0)

    def post_preformatted_output(self, markup: str, *, animated: bool, fast_reveal: bool = False) -> None:
        done = Event()
        Clock.schedule_once(
            lambda _dt: self.screen.append_log(
                markup,
                done_event=done,
                animated=animated,
                fast_reveal=fast_reveal,
            )
        )
        done.wait(timeout=self.screen.typing_wait_timeout_markup(markup, animated=animated, fast_reveal=fast_reveal))

    def flush_pending_non_dialogue_output(self) -> None:
        if not self._pending_non_dialogue_markups:
            return
        markup = "\n".join(self._pending_non_dialogue_markups)
        fast_reveal = self._pending_non_dialogue_fast_reveal
        self._pending_non_dialogue_markups = []
        self._pending_non_dialogue_fast_reveal = False
        self.post_preformatted_output(markup, animated=False, fast_reveal=fast_reveal)

    def show_title_menu(
        self,
        *,
        title: str,
        subtitle: str,
        intro_text: str,
        campaign_summary: str,
        save_summary: str,
        save_detail: str,
        audio_summary: str,
        presentation_summary: str,
    ) -> None:
        done = Event()
        Clock.schedule_once(
            lambda _dt: self.screen.show_title_menu(
                title=title,
                subtitle=subtitle,
                intro_text=intro_text,
                campaign_summary=campaign_summary,
                save_summary=save_summary,
                save_detail=save_detail,
                audio_summary=audio_summary,
                presentation_summary=presentation_summary,
                done_event=done,
            )
        )
        done.wait(timeout=1.0)

    def request_choice(
        self,
        prompt: str,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> str:
        self.flush_pending_non_dialogue_output()
        self._fast_reveal_until_next_prompt = False
        self.waiting_for_input = True
        Clock.schedule_once(
            lambda _dt: self.screen.show_choice_prompt(prompt, options, option_details=option_details)
        )
        return self._responses.get()

    def request_save_browser_choice(self, title: str, entries: list[dict[str, str]]) -> str:
        self.flush_pending_non_dialogue_output()
        self._fast_reveal_until_next_prompt = False
        self.waiting_for_input = True
        Clock.schedule_once(lambda _dt: self.screen.show_save_browser(title, entries))
        return self._responses.get()

    def request_save_action_choice(self, entry: dict[str, str]) -> str:
        self.flush_pending_non_dialogue_output()
        self._fast_reveal_until_next_prompt = False
        self.waiting_for_input = True
        Clock.schedule_once(lambda _dt: self.screen.show_save_action_browser(entry))
        return self._responses.get()

    def request_text(self, prompt: str) -> str:
        self.flush_pending_non_dialogue_output()
        self._fast_reveal_until_next_prompt = False
        self.waiting_for_input = True
        Clock.schedule_once(lambda _dt: self.screen.show_text_prompt(prompt))
        return self._responses.get()

    def value_requests_fast_reveal(self, value: str) -> bool:
        normalized = " ".join(str(value).strip().lower().split())
        return normalized in self.FAST_REVEAL_COMMANDS or normalized.startswith("load ")

    def submit(self, value: str) -> None:
        if not self.waiting_for_input:
            return
        self.waiting_for_input = False
        self._fast_reveal_until_next_prompt = self.value_requests_fast_reveal(value)
        if self.screen.title_menu_active():
            delay = self.screen.begin_title_menu_transition(value)
            if delay > 0:
                Clock.schedule_once(lambda _dt: self._complete_submit(value), delay)
                return
        self._complete_submit(value)

    def _complete_submit(self, value: str) -> None:
        Clock.schedule_once(lambda _dt: self.screen.clear_prompt())
        Clock.schedule_once(lambda _dt: self.screen.mark_input_separator_pending())
        self._responses.put(value)

    def close_side_command(self) -> None:
        self._fast_reveal_until_next_prompt = False
        if not self.side_command_active:
            return
        if not self.waiting_for_input:
            return
        self.waiting_for_input = False
        Clock.schedule_once(lambda _dt: self.screen.clear_prompt())
        Clock.schedule_once(lambda _dt: self.screen.mark_input_separator_pending())
        self._responses.put(KIVY_SIDE_COMMAND_CLOSE_TOKEN)

    def show_combat_actor(self, actor) -> None:
        name = "" if actor is None else str(getattr(actor, "name", ""))
        done = Event()

        def update_actor(_dt) -> None:
            self.screen.set_active_combat_actor(name)
            done.set()

        Clock.schedule_once(update_actor, -1)
        done.wait(timeout=1.0)

    def refresh_combat_panel(self) -> None:
        Clock.schedule_once(lambda _dt: self.screen.refresh_combat_panel())

    def refresh_active_initiative_tray(self) -> None:
        Clock.schedule_once(lambda _dt: self.screen.refresh_active_initiative_tray())

    def fade_out_initiative_tray(self) -> None:
        Clock.schedule_once(lambda _dt: self.screen.fade_out_initiative_tray())

    def wait_for_combat_transition(self, *, ending: bool = False) -> None:
        done = Event()
        Clock.schedule_once(lambda _dt: self.screen.prepare_combat_transition(done_event=done, ending=ending))
        done.wait(timeout=2.0)

    def wait_for_animation(self, duration: float) -> bool:
        return self.screen.wait_for_animation_skip(duration)

    def set_kivy_dark_mode(self, enabled: bool) -> None:
        Clock.schedule_once(lambda _dt: self.screen.set_kivy_dark_mode_enabled(enabled))

    def set_kivy_fullscreen(self, enabled: bool) -> None:
        Clock.schedule_once(lambda _dt: self.screen.set_kivy_fullscreen_enabled(enabled))

    def show_overworld_map(self, blueprint, state, title: str) -> None:
        done = Event()
        Clock.schedule_once(
            lambda _dt: self.screen.show_native_overworld_map(
                blueprint,
                state,
                title=title,
                done_event=done,
            )
        )
        done.wait(timeout=1.0)

    def show_dungeon_map(self, dungeon, state, title: str) -> None:
        done = Event()
        Clock.schedule_once(
            lambda _dt: self.screen.show_native_dungeon_map(
                dungeon,
                state,
                title=title,
                done_event=done,
            )
        )
        done.wait(timeout=1.0)

    def show_native_command(self, command: str) -> None:
        done = Event()
        Clock.schedule_once(lambda _dt: self.screen.show_native_command_pane(command, done_event=done))
        done.wait(timeout=1.0)


class ClickableTextDnDGame(TextDnDGame):
    KIVY_DARK_MODE_SETTING_KEY = "kivy_dark_mode_enabled"
    KIVY_FULLSCREEN_SETTING_KEY = "kivy_fullscreen_enabled"
    DEFAULT_KIVY_DARK_MODE_ENABLED = True
    DEFAULT_KIVY_FULLSCREEN_ENABLED = True

    def __init__(self, bridge: ClickableGameBridge, *, save_dir: Path):
        self.bridge = bridge
        super().__init__(
            input_fn=lambda _prompt="": "",
            output_fn=self.bridge.post_output,
            save_dir=save_dir,
            animate_dice=True,
            pace_output=None,
            type_dialogue=None,
            staggered_reveals=None,
        )
        self._kivy_dark_mode_preference = bool(
            getattr(self, "_loaded_kivy_dark_mode_preference", self.bridge.screen.kivy_dark_mode_enabled)
        )
        self._kivy_fullscreen_preference = bool(
            getattr(self, "_loaded_kivy_fullscreen_preference", self.bridge.screen.kivy_fullscreen_enabled)
        )
        self._kivy_active_initiative_entries: list[dict[str, object]] = []
        self._kivy_character_creation_title_shell = False
        self.bridge.set_kivy_dark_mode(self._kivy_dark_mode_preference)
        self.bridge.set_kivy_fullscreen(self._kivy_fullscreen_preference)

    def kivy_title_shell_active(self) -> bool:
        if getattr(self, "_at_title_screen", False):
            return True
        if not getattr(self, "_kivy_character_creation_title_shell", False):
            return False
        state = getattr(self, "state", None)
        if state is None:
            return True
        flags = getattr(state, "flags", {})
        tutorial_choice_pending = bool(
            flags.get("opening_tutorial_pending")
            and not flags.get("opening_tutorial_started")
            and not flags.get("opening_tutorial_seen")
        )
        if getattr(state, "current_scene", "") == "opening_tutorial":
            return tutorial_choice_pending
        if tutorial_choice_pending:
            return True
        self._kivy_character_creation_title_shell = False
        return False

    def start_new_game(self) -> None:
        self._kivy_character_creation_title_shell = True
        super().start_new_game()
        if self.state is None:
            self._kivy_character_creation_title_shell = False

    def load_persisted_settings(self) -> dict[str, object]:
        settings = super().load_persisted_settings()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return settings
        if isinstance(data, dict) and self.KIVY_DARK_MODE_SETTING_KEY in data:
            self._loaded_kivy_dark_mode_preference = bool(data[self.KIVY_DARK_MODE_SETTING_KEY])
        if isinstance(data, dict) and self.KIVY_FULLSCREEN_SETTING_KEY in data:
            self._loaded_kivy_fullscreen_preference = bool(data[self.KIVY_FULLSCREEN_SETTING_KEY])
        return settings

    @classmethod
    def default_settings_payload(cls) -> dict[str, object]:
        payload = super().default_settings_payload()
        payload[cls.KIVY_DARK_MODE_SETTING_KEY] = cls.DEFAULT_KIVY_DARK_MODE_ENABLED
        payload[cls.KIVY_FULLSCREEN_SETTING_KEY] = cls.DEFAULT_KIVY_FULLSCREEN_ENABLED
        return payload

    def current_settings_payload(self) -> dict[str, object]:
        payload = super().current_settings_payload()
        payload[self.KIVY_DARK_MODE_SETTING_KEY] = bool(
            getattr(self, "_kivy_dark_mode_preference", self.bridge.screen.kivy_dark_mode_enabled)
        )
        payload[self.KIVY_FULLSCREEN_SETTING_KEY] = bool(
            getattr(self, "_kivy_fullscreen_preference", self.bridge.screen.kivy_fullscreen_enabled)
        )
        return payload

    def music_output_allows_playback(self) -> bool:
        return True

    def kivy_should_animate_dice_roll(self, *, style: str | None = None, outcome_kind: str | None = None) -> bool:
        return kivy_dice_animation_allowed(
            in_combat=bool(getattr(self, "_in_combat", False)),
            style=style,
            outcome_kind=outcome_kind,
        )

    def animate_dice_roll(self, **payload) -> None:
        kind = str(payload.get("kind", "roll"))
        rolls = list(payload.get("rolls") or [])
        if not rolls:
            return
        expression = str(payload.get("expression", "roll"))
        sides = int(payload.get("sides", 20) or 20)
        value_width = max(2, len(str(max(1, sides))))
        modifier = int(payload.get("modifier", 0) or 0)
        display_modifier = payload.get("display_modifier")
        effective_modifier = modifier if display_modifier is None else int(display_modifier)
        critical = bool(payload.get("critical", False))
        advantage_state = int(payload.get("advantage_state", 0) or 0)
        rerolls = list(payload.get("rerolls") or [])
        kept = payload.get("kept")
        kept = int(kept) if kept is not None else None
        target_number = payload.get("target_number")
        target_number = int(target_number) if target_number is not None else None
        target_label = payload.get("target_label")
        context_label = payload.get("context_label")
        style = payload.get("style")
        outcome_kind = payload.get("outcome_kind")
        animate_allowed = self.kivy_should_animate_dice_roll(style=style, outcome_kind=outcome_kind)
        if not animate_allowed:
            return
        if not self.animate_dice:
            self.render_dice_result_panel(
                kind=kind,
                expression=expression,
                rolls=rolls,
                modifier=effective_modifier,
                kept=kept,
                rerolls=rerolls,
                target_number=target_number,
                target_label=target_label,
                context_label=context_label,
                style=style,
                outcome_kind=outcome_kind,
                critical=critical,
                advantage_state=advantage_state,
            )
            return

        self.begin_animation_skip_scope()
        try:
            mode = self.current_dice_animation_mode()
            show_total_frame = (
                mode == "full"
                or kind == "d20"
                or effective_modifier != 0
                or len(rolls) > 1
                or style in {"damage", "healing"}
            )
            emphasis = 0.0
            if critical:
                emphasis += 0.18
            if style in {"attack", "damage", "save", "skill"}:
                emphasis += 0.12
            if target_number is not None or advantage_state:
                emphasis += 0.08
            duration = min(
                self._dice_animation_max_seconds,
                max(
                    self._dice_animation_min_seconds,
                    self._dice_animation_min_seconds
                    + 0.18 * max(0, len(rolls) - 1)
                    + (0.14 if advantage_state else 0.0)
                    + emphasis,
                ),
            )
            play_dice_roll_sound = getattr(self, "play_dice_roll_sound", None)
            if callable(play_dice_roll_sound):
                play_dice_roll_sound(duration, cooldown=0.05)
            frames = min(
                max(self._dice_animation_max_frames + 12, 1),
                max(
                    self._dice_animation_min_frames + 8,
                    int(max(1.0, duration) * max(1.0, self._dice_animation_frame_rate + 9)),
                ),
            )
            preview_rng = random.Random(time.perf_counter_ns() ^ id(rolls) ^ (sides << 8))
            label = self.dice_animation_label(
                kind,
                expression,
                style=style,
                critical=critical,
                advantage_state=advantage_state,
            )
            skipped = False
            delays = kivy_dice_frame_delays(frames, duration)
            for index, delay in enumerate(delays):
                progress = (index + 1) / max(1, frames)
                shown = self.kivy_dice_preview_rolls(
                    rolls,
                    sides=sides,
                    preview_rng=preview_rng,
                    progress=progress,
                )
                self.render_dice_animation_frame(
                    label,
                    shown,
                    kind=kind,
                    final=False,
                    kept=kept,
                    style=style,
                    outcome_kind=outcome_kind,
                    target_number=target_number,
                    target_label=target_label,
                    context_label=context_label,
                    highlight_index=self._kivy_dice_live_highlight_index(
                        kind,
                        shown,
                        advantage_state=advantage_state,
                    ),
                    pop_scale=self._kivy_dice_live_pop_scale(index, frames),
                    value_width=value_width,
                )
                if self.sleep_for_dice_animation(delay):
                    skipped = True
                    break

            final_label = self.dice_animation_final_label(
                kind,
                expression,
                style=style,
                critical=critical,
                advantage_state=advantage_state,
            )
            if not skipped:
                final_highlight_index = kivy_dice_highlight_index(rolls, kept)
                winner_color = self._kivy_dice_winner_color(
                    kind=kind,
                    rolls=rolls,
                    modifier=modifier,
                    kept=kept,
                    target_number=target_number,
                    style=style,
                    outcome_kind=outcome_kind,
                    critical=critical,
                    fallback=self._kivy_dice_accent(kind, style, outcome_kind),
                )
                for pop_scale, pause in (
                    (1.68, 0.045),
                    (0.78, 0.035),
                    (1.42, 0.04),
                    (0.92, 0.035),
                    (1.18, 0.035),
                ):
                    self.render_dice_animation_frame(
                        final_label,
                        rolls,
                        kind=kind,
                        final=True,
                        modifier=modifier,
                        kept=kept,
                        rerolls=rerolls,
                        style=style,
                        outcome_kind=outcome_kind,
                        target_number=target_number,
                        target_label=target_label,
                        show_total=not show_total_frame,
                        context_label=context_label,
                        highlight_index=final_highlight_index,
                        highlight_color=winner_color,
                        pop_scale=pop_scale,
                        value_width=value_width,
                        clear_animation=False,
                    )
                    skipped = self.sleep_for_dice_animation(pause)
                    if skipped:
                        break
            self.render_dice_animation_frame(
                final_label,
                rolls,
                kind=kind,
                final=True,
                modifier=modifier,
                kept=kept,
                rerolls=rerolls,
                style=style,
                outcome_kind=outcome_kind,
                target_number=target_number,
                target_label=target_label,
                show_total=not show_total_frame,
                context_label=context_label,
                highlight_index=kivy_dice_highlight_index(rolls, kept),
                highlight_color=self._kivy_dice_winner_color(
                    kind=kind,
                    rolls=rolls,
                    modifier=modifier,
                    kept=kept,
                    target_number=target_number,
                    style=style,
                    outcome_kind=outcome_kind,
                    critical=critical,
                    fallback=self._kivy_dice_accent(kind, style, outcome_kind),
                ),
                pop_scale=1.0,
                value_width=value_width,
                clear_animation=not show_total_frame,
            )
            if show_total_frame:
                total_skipped = bool(skipped)
                if not total_skipped and self._dice_total_reveal_pause_seconds > 0:
                    total_skipped = self.sleep_for_animation(
                        self._dice_total_reveal_pause_seconds,
                        require_animation=True,
                    )
                if not total_skipped:
                    self.render_dice_animation_frame(
                        final_label,
                        rolls,
                        kind=kind,
                        final=True,
                        modifier=effective_modifier,
                        kept=kept,
                        rerolls=rerolls,
                        style=style,
                        outcome_kind=outcome_kind,
                        target_number=target_number,
                        target_label=target_label,
                        show_total=False,
                        total_reveal_stage=1,
                        context_label=context_label,
                        highlight_index=kivy_dice_highlight_index(rolls, kept),
                        highlight_color=self._kivy_dice_winner_color(
                            kind=kind,
                            rolls=rolls,
                            modifier=effective_modifier,
                            kept=kept,
                            target_number=target_number,
                            style=style,
                            outcome_kind=outcome_kind,
                            critical=critical,
                            fallback=self._kivy_dice_accent(kind, style, outcome_kind),
                        ),
                        pop_scale=1.0,
                        value_width=value_width,
                        clear_animation=False,
                    )
                    total_skipped = self.sleep_for_dice_animation(0.12)
                if total_skipped:
                    total_pop_frames = ((1.0, 0.0),)
                else:
                    total_pop_frames = (
                        (1.26, 0.045),
                        (0.92, 0.035),
                        (1.10, 0.035),
                        (1.0, 0.0),
                    )
                total_reveal_cleared = False
                for total_pop_scale, pause in total_pop_frames:
                    self.render_dice_animation_frame(
                        final_label,
                        rolls,
                        kind=kind,
                        final=True,
                        modifier=effective_modifier,
                        kept=kept,
                        rerolls=rerolls,
                        style=style,
                        outcome_kind=outcome_kind,
                        target_number=target_number,
                        target_label=target_label,
                        show_total=False,
                        total_reveal_stage=2,
                        total_pop_scale=total_pop_scale,
                        context_label=context_label,
                        highlight_index=kivy_dice_highlight_index(rolls, kept),
                        highlight_color=self._kivy_dice_winner_color(
                            kind=kind,
                            rolls=rolls,
                            modifier=effective_modifier,
                            kept=kept,
                            target_number=target_number,
                            style=style,
                            outcome_kind=outcome_kind,
                            critical=critical,
                            fallback=self._kivy_dice_accent(kind, style, outcome_kind),
                        ),
                        pop_scale=1.0,
                        value_width=value_width,
                        clear_animation=pause <= 0,
                    )
                    total_reveal_cleared = pause <= 0
                    if pause > 0 and self.sleep_for_dice_animation(pause):
                        break
                if not total_reveal_cleared:
                    self.render_dice_animation_frame(
                        final_label,
                        rolls,
                        kind=kind,
                        final=True,
                        modifier=effective_modifier,
                        kept=kept,
                        rerolls=rerolls,
                        style=style,
                        outcome_kind=outcome_kind,
                        target_number=target_number,
                        target_label=target_label,
                        show_total=False,
                        total_reveal_stage=2,
                        total_pop_scale=1.0,
                        context_label=context_label,
                        highlight_index=kivy_dice_highlight_index(rolls, kept),
                        highlight_color=self._kivy_dice_winner_color(
                            kind=kind,
                            rolls=rolls,
                            modifier=effective_modifier,
                            kept=kept,
                            target_number=target_number,
                            style=style,
                            outcome_kind=outcome_kind,
                            critical=critical,
                            fallback=self._kivy_dice_accent(kind, style, outcome_kind),
                        ),
                        pop_scale=1.0,
                        value_width=value_width,
                        clear_animation=True,
                    )
            if self._dice_animation_final_pause_seconds > 0:
                self.sleep_for_animation(self._dice_animation_final_pause_seconds, require_animation=True)
        finally:
            self.end_animation_skip_scope()

    def can_render_initiative_panel_animation(self) -> bool:
        return True

    def _kivy_dice_color(self, color_name: str | None, *, fallback: str = "d6c59a") -> str:
        return KIVY_DICE_COLOR_HEX.get(str(color_name or ""), fallback)

    def _kivy_dice_accent(self, kind: str, style: str | None, outcome_kind: str | None = None) -> str:
        if style == "initiative" or outcome_kind == "initiative":
            return "facc15"
        if style in {"attack", "damage"} or outcome_kind == "attack":
            return "f87171"
        if style == "healing":
            return "86efac"
        if style == "skill":
            return "67e8f9"
        if style == "save" or outcome_kind == "save":
            return "d6c59a"
        return "d6c59a" if kind == "roll" else "facc15"

    def _kivy_dice_winner_color(
        self,
        *,
        kind: str,
        rolls: list[int],
        modifier: int,
        kept: int | None,
        target_number: int | None,
        style: str | None,
        outcome_kind: str | None,
        critical: bool,
        fallback: str,
    ) -> str:
        if not rolls:
            return fallback
        _label, outcome_color, _note = self.dice_outcome_details(
            kind=kind,
            rolls=rolls,
            modifier=modifier,
            kept=kept,
            target_number=target_number,
            style=style,
            outcome_kind=outcome_kind,
            critical=critical,
        )
        return self._kivy_dice_color(outcome_color, fallback=fallback)

    def _kivy_dice_live_highlight_index(
        self,
        kind: str,
        rolls: list[int],
        *,
        advantage_state: int = 0,
    ) -> int | None:
        if not rolls:
            return None
        if kind == "d20" and len(rolls) > 1 and advantage_state < 0:
            return min(range(len(rolls)), key=lambda index: rolls[index])
        return max(range(len(rolls)), key=lambda index: rolls[index])

    def _kivy_dice_live_pop_scale(self, frame_index: int, frame_count: int) -> float:
        progress = frame_index / max(1, frame_count - 1)
        beat = (1.00, 1.22, 0.90, 1.14, 0.96, 1.08)[frame_index % 6]
        return 1.0 + (beat - 1.0) * (0.55 + 0.45 * progress)

    def kivy_dice_preview_rolls(
        self,
        final_rolls: list[int],
        *,
        sides: int,
        preview_rng: random.Random,
        progress: float,
    ) -> list[int]:
        lock_progress = max(0.0, (progress - 0.78) / 0.22)
        lock_chance = lock_progress**1.7
        shown: list[int] = []
        for final_value in final_rolls:
            if preview_rng.random() < lock_chance:
                shown.append(final_value)
            else:
                shown.append(preview_rng.randint(1, sides))
        return shown

    def _kivy_mono_span(self, markup: str) -> str:
        font_name = resolve_kivy_font("mono")
        if not font_name:
            return markup
        safe_font_name = font_name.replace("\\", "/")
        return f"[font={safe_font_name}]{markup}[/font]"

    def _kivy_dice_value_markup(
        self,
        value: int,
        *,
        highlighted: bool,
        accent: str,
        highlight_color: str | None = None,
        pop_scale: float = 1.0,
        muted: bool = False,
        width: int = 2,
        animate_size: bool = False,
    ) -> str:
        escaped = escape_kivy_markup(str(value).rjust(max(1, int(width))))
        if animate_size:
            value_size = max(28.0, min(38.0, 34.0 * max(0.82, pop_scale)))
            escaped = f"[size={value_size:.1f}sp]{escaped}[/size]"
        if muted:
            return f"[color=#8f7d62]{escaped}[/color]"
        if not highlighted:
            return escaped
        color = highlight_color or accent
        return f"[b][color=#{color}]{escaped}[/color][/b]"

    def _kivy_dice_frame_core(
        self,
        kind: str,
        rolls: list[int],
        *,
        kept: int | None = None,
        final: bool = False,
        highlight_index: int | None = None,
        highlight_color: str | None = None,
        pop_scale: float = 1.0,
        accent: str = "facc15",
        value_width: int = 2,
        animate_size: bool = False,
    ) -> str:
        value_width = max(1, int(value_width))
        if kind == "d20":
            if len(rolls) == 1:
                value = self._kivy_dice_value_markup(
                    rolls[0],
                    highlighted=highlight_index == 0,
                    accent=accent,
                    highlight_color=highlight_color,
                    pop_scale=pop_scale,
                    width=value_width,
                    animate_size=animate_size,
                )
                return value
            lanes: list[str] = []
            kept_index = self.dice_kept_index(rolls, kept) if final else None
            for index, value in enumerate(rolls):
                highlighted = highlight_index == index
                rendered = self._kivy_dice_value_markup(
                    value,
                    highlighted=highlighted,
                    accent=accent,
                    highlight_color=highlight_color,
                    pop_scale=pop_scale if highlighted else 1.0,
                    muted=final and highlight_index is not None and highlight_index != index,
                    width=value_width,
                    animate_size=animate_size,
                )
                lane = rendered
                if kept_index == index:
                    lane += f" [b][color=#{highlight_color or accent}][kept][/color][/b]"
                lanes.append(lane)
            return " | ".join(lanes)
        parts = [
            self._kivy_dice_value_markup(
                value,
                highlighted=highlight_index == index,
                accent=accent,
                highlight_color=highlight_color,
                pop_scale=pop_scale if highlight_index == index else 1.0,
                width=value_width,
                animate_size=animate_size,
            )
            for index, value in enumerate(rolls)
        ]
        return " + ".join(parts)

    def _kivy_dice_base_value(self, kind: str, rolls: list[int], kept: int | None) -> int:
        if kind == "d20":
            return kept if kept is not None else (rolls[-1] if rolls else 0)
        return sum(rolls)

    def _kivy_dice_bonus_markup(self, modifier: int) -> str:
        if modifier > 0:
            return f"[color=#8f7d62]Bonus[/color] [color=#d6c59a]+{modifier}[/color]"
        if modifier < 0:
            return f"[color=#8f7d62]Bonus[/color] [color=#d6c59a]{modifier}[/color]"
        return ""

    def _kivy_dice_total_markup(
        self,
        total: int,
        *,
        color: str,
        pop_scale: float,
    ) -> str:
        escaped = escape_kivy_markup(str(total))
        value_size = max(28.0, min(38.0, 34.0 * max(0.82, pop_scale)))
        escaped = f"[size={value_size:.1f}sp]{escaped}[/size]"
        return f"[b][color=#{color}]{escaped}[/color][/b]"

    def _kivy_dice_core_slot_width(self, kind: str, roll_count: int, value_width: int) -> float:
        value = "9" * max(1, int(value_width))
        roll_count = max(1, int(roll_count))
        if kind == "d20":
            if roll_count == 1:
                visible = value
            else:
                lanes = [f"{value} [kept]" for _index in range(roll_count)]
                visible = " | ".join(lanes)
        else:
            visible = " + ".join(value for _index in range(roll_count))
        return min(430.0, max(78.0, len(visible) * 8.5 + 24.0))

    def render_dice_animation_frame(
        self,
        label: str,
        rolls: list[int],
        *,
        kind: str = "roll",
        final: bool,
        modifier: int = 0,
        kept: int | None = None,
        rerolls: list[tuple[int, int]] | None = None,
        style: str | None = None,
        outcome_kind: str | None = None,
        target_number: int | None = None,
        target_label: str | None = None,
        show_total: bool = True,
        context_label: str | None = None,
        highlight_index: int | None = None,
        highlight_color: str | None = None,
        pop_scale: float = 1.0,
        total_reveal_stage: int = 0,
        total_pop_scale: float = 1.0,
        value_width: int = 2,
        clear_animation: bool | None = None,
    ) -> None:
        rerolls = rerolls or []
        accent = self._kivy_dice_accent(kind, style, outcome_kind)
        core = self._kivy_dice_frame_core(
            kind,
            rolls,
            kept=kept,
            final=final,
            highlight_index=highlight_index,
            highlight_color=highlight_color,
            pop_scale=pop_scale,
            accent=accent,
            value_width=value_width,
            animate_size=True,
        )
        prefix = escape_kivy_markup(strip_ansi(str(context_label or "")))
        suffix_parts: list[str] = []
        if target_number is not None and total_reveal_stage < 2:
            suffix_parts.append(f"vs {escape_kivy_markup(str(target_label or target_number))}")
        if final and (show_total or total_reveal_stage > 0):
            bonus_markup = self._kivy_dice_bonus_markup(modifier)
            if bonus_markup and (show_total or total_reveal_stage > 0):
                suffix_parts.append(bonus_markup)
            if show_total or total_reveal_stage >= 2:
                total = self._kivy_dice_base_value(kind, rolls, kept) + modifier
                total_color = highlight_color or accent
                total_markup = (
                    self._kivy_dice_total_markup(total, color=total_color, pop_scale=total_pop_scale)
                    if total_reveal_stage >= 2
                    else f"[b][color=#{total_color}]{escape_kivy_markup(str(total))}[/color][/b]"
                )
                if bonus_markup:
                    suffix_parts.append(f"[color=#8f7d62]=[/color] {total_markup}")
                else:
                    suffix_parts.append(f"[color=#8f7d62]Total[/color] {total_markup}")
                if target_number is not None and total_reveal_stage >= 2:
                    suffix_parts.append(f"[color=#8f7d62]vs[/color] {escape_kivy_markup(str(target_label or target_number))}")
        if final and rerolls:
            suffix_parts.append(f"reroll {escape_kivy_markup(', '.join(f'{old}->{new}' for old, new in rerolls))}")
        suffix = "  ".join(suffix_parts)
        text = f"{prefix}: {core}" if prefix else core
        if suffix:
            text += f" | {suffix}"
        markup = self._kivy_mono_span(f"[b][color=#{accent}]{text}[/color][/b]")
        prefix_markup = self._kivy_mono_span(f"[b][color=#{accent}]{prefix}: [/color][/b]") if prefix else ""
        core_markup = self._kivy_mono_span(f"[b][color=#{accent}]{core}[/color][/b]")
        suffix_markup = self._kivy_mono_span(f"[b][color=#{accent}]{suffix}[/color][/b]") if suffix else ""
        self.bridge.show_dice_animation_frame(
            markup,
            final=final if clear_animation is None else clear_animation,
            use_tray=True,
            use_roll_tray=True,
            tray_parts=(prefix_markup, core_markup, suffix_markup),
            pulse_scale=pop_scale,
            core_slot_width=self._kivy_dice_core_slot_width(kind, len(rolls), value_width),
        )

    def render_dice_result_panel(
        self,
        *,
        kind: str,
        expression: str,
        rolls: list[int],
        modifier: int,
        kept: int | None = None,
        rerolls: list[tuple[int, int]] | None = None,
        target_number: int | None = None,
        target_label: str | None = None,
        context_label: str | None = None,
        style: str | None = None,
        outcome_kind: str | None = None,
        critical: bool = False,
        advantage_state: int = 0,
    ) -> None:
        rerolls = rerolls or []
        total = (kept if kept is not None else sum(rolls)) + modifier
        panel_title, _accent_name = self.dice_animation_theme(kind, style)
        heading = context_label or panel_title
        outcome_label, outcome_color, outcome_note = self.dice_outcome_details(
            kind=kind,
            rolls=rolls,
            modifier=modifier,
            kept=kept,
            target_number=target_number,
            style=style,
            outcome_kind=outcome_kind,
            critical=critical,
        )
        accent = self._kivy_dice_accent(kind, style, outcome_kind)
        outcome_hex = self._kivy_dice_color(outcome_color, fallback=accent)
        dice_markup = self._kivy_dice_frame_core(
            kind,
            rolls,
            kept=kept,
            final=True,
            highlight_index=kivy_dice_highlight_index(rolls, kept),
            highlight_color=outcome_hex,
            pop_scale=1.0,
            accent=accent,
        )
        self.render_dice_animation_frame(
            self.dice_animation_final_label(
                kind,
                expression,
                style=style,
                critical=critical,
                advantage_state=advantage_state,
            ),
            rolls,
            kind=kind,
            final=True,
            modifier=modifier,
            kept=kept,
            rerolls=rerolls,
            style=style,
            outcome_kind=outcome_kind,
            target_number=target_number,
            target_label=target_label,
            show_total=True,
            context_label=context_label,
            highlight_index=kivy_dice_highlight_index(rolls, kept),
            highlight_color=outcome_hex,
            pop_scale=1.0,
            value_width=max(2, max(len(str(value)) for value in rolls)),
            clear_animation=True,
        )
        lines = [
            f"[b][color=#{accent}]{escape_kivy_markup(strip_ansi(heading))}[/color][/b]",
            (
                f"[color=#8f7d62]Roll[/color]: "
                f"{escape_kivy_markup(self.dice_animation_final_label(kind, expression, style=style, critical=critical, advantage_state=advantage_state))}"
            ),
            dice_markup,
            f"[color=#8f7d62]Total[/color]: [b][color=#{outcome_hex}]{total}[/color][/b]",
        ]
        if target_number is not None:
            lines.append(f"[color=#8f7d62]Target[/color]: {escape_kivy_markup(str(target_label or target_number))}")
        lines.append(f"[color=#8f7d62]Outcome[/color]: [b][color=#{outcome_hex}]{escape_kivy_markup(outcome_label)}[/color][/b]")
        if outcome_note is not None:
            lines.append(f"[color=#8f7d62]Note[/color]: {escape_kivy_markup(outcome_note)}")
        if rerolls:
            reroll_text = ", ".join(f"{old}->{new}" for old, new in rerolls)
            lines.append(f"[color=#8f7d62]Reroll[/color]: {escape_kivy_markup(reroll_text)}")
        self.bridge.append_dice_result("\n".join(lines))

    def _kivy_table_cell(self, text: object, width: int, *, align: str = "left") -> str:
        value = strip_ansi(str(text))
        if len(value) > width:
            value = value[: max(1, width - 1)] + "~"
        if align == "right":
            return value.rjust(width)
        if align == "center":
            return value.center(width)
        return value.ljust(width)

    def _kivy_markup_table_cell(
        self,
        text: object,
        width: int,
        *,
        align: str = "left",
        color: str | None = None,
        bold: bool = False,
        size_sp: int | None = None,
    ) -> str:
        cell = escape_kivy_markup(self._kivy_table_cell(text, width, align=align))
        if color:
            cell = f"[color=#{color}]{cell}[/color]"
        if bold:
            cell = f"[b]{cell}[/b]"
        if size_sp is not None:
            cell = f"[size={size_sp}sp]{cell}[/size]"
        return cell

    def _kivy_initiative_actor_color(self, actor) -> str:
        enemies = list(getattr(self, "_active_combat_enemies", []) or [])
        if actor in enemies or "enemy" in set(getattr(actor, "tags", []) or []):
            return "f87171"
        return "67e8f9"

    def _kivy_initiative_leader_index(self, entries: list[dict[str, object]], shown_rolls: list[int]) -> int | None:
        if not entries or not shown_rolls:
            return None
        return max(
            range(min(len(entries), len(shown_rolls))),
            key=lambda index: (
                int(shown_rolls[index]) + int(entries[index]["modifier"]),
                int(entries[index].get("dex_mod", 0)),
                int(entries[index].get("side_priority", 0)),
                int(entries[index].get("tie_index", 0)),
            ),
        )

    def _kivy_initiative_status_details(self, entry: dict[str, object], *, final: bool, leader: bool) -> tuple[str, str, bool]:
        if not final:
            return ("Rolling", "d6c59a" if leader else "8f7d62", leader)
        note = self.initiative_entry_note(entry)
        if note == "Natural 20":
            return ("Natural 20", "facc15", True)
        if note == "Natural 1":
            return ("Natural 1", "f87171", True)
        if leader:
            return ("First move", "86efac", True)
        return ("Ready", "8f7d62", False)

    def _kivy_initiative_status_markup(self, entry: dict[str, object], *, final: bool, leader: bool) -> str:
        text, color, bold = self._kivy_initiative_status_details(entry, final=final, leader=leader)
        markup = f"[color=#{color}]{escape_kivy_markup(text)}[/color]"
        return f"[b]{markup}[/b]" if bold else markup

    def _kivy_initiative_tray_height(self, entries: list[dict[str, object]]) -> int:
        return min(320, max(150, 104 + 24 * max(1, len(entries))))

    def _kivy_initiative_actor_is_defeated_enemy(self, actor) -> bool:
        is_enemy = actor in list(getattr(self, "_active_combat_enemies", []) or []) or "enemy" in set(
            getattr(actor, "tags", []) or []
        )
        return bool(is_enemy and (getattr(actor, "dead", False) or int(getattr(actor, "current_hp", 0) or 0) <= 0))

    def _kivy_visible_initiative_entries(self, entries: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            entry
            for entry in entries
            if not self._kivy_initiative_actor_is_defeated_enemy(entry.get("actor"))
        ]

    def _kivy_initiative_turn_arrow(self, *, active: bool, arrow_phase: int = 0) -> str:
        if not active:
            return ""
        arrows = (">", ">>", ">>>", ">>")
        return arrows[arrow_phase % len(arrows)]

    def _kivy_initiative_panel_markup(
        self,
        entries: list[dict[str, object]],
        *,
        shown_rolls: list[int] | None = None,
        final: bool,
        frame_index: int = 0,
        frame_count: int = 1,
        pop_scale: float | None = None,
        active_actor_name: str = "",
        arrow_phase: int = 0,
    ) -> str:
        del frame_index, frame_count, pop_scale
        display_rolls = shown_rolls or [getattr(entry["outcome"], "kept", 0) for entry in entries]
        leader_index = self._kivy_initiative_leader_index(entries, display_rolls)
        title = "Initiative Order" if final else "Rolling Initiative"
        round_number = int(getattr(self, "_active_round_number", 0) or 0)
        round_prefix = f"Round {round_number} | " if round_number > 0 else ""
        subtitle = f"{round_prefix}{'Highest total acts first' if final else 'Dice settling into turn order'}"
        active_actor_name = str(active_actor_name).strip()
        lines = [
            f"[size=18sp][b][color=#facc15]{title}[/color][/b][/size]",
            f"[size=12sp][color=#8f7d62]{subtitle}[/color][/size]",
            (
                f"[color=#8f7d62]"
                f"{self._kivy_table_cell('Turn', 4)} | "
                f"{self._kivy_table_cell('#', 2, align='right')} | "
                f"{self._kivy_table_cell('Combatant', 19)} | "
                f"{self._kivy_table_cell('Roll', 4, align='right')} | "
                f"{self._kivy_table_cell('Mod', 4, align='right')} | "
                f"{self._kivy_table_cell('Total', 5, align='right')} | "
                f"{self._kivy_table_cell('Status', 11)}"
                f"[/color]"
            ),
            f"[color=#4b3f30]{'----+-' + '-' * 2 + '-+-' + '-' * 19 + '-+-' + '-' * 4 + '-+-' + '-' * 4 + '-+-' + '-' * 5 + '-+-' + '-' * 11}[/color]",
        ]
        for index, (entry, shown) in enumerate(zip(entries, display_rolls), start=1):
            actor = entry["actor"]
            modifier = int(entry["modifier"])
            total = int(entry["total"]) if final else int(shown) + modifier
            is_leader = leader_index == index - 1
            is_active = final and active_actor_name and str(getattr(actor, "name", "")) == active_actor_name
            actor_name = strip_ansi(self.initiative_actor_summary_name(actor))
            actor_color = self._kivy_initiative_actor_color(actor)
            rank_color = "facc15" if is_leader else "8f7d62"
            winner_color = "facc15" if is_leader else "d6c59a"
            arrow_text = self._kivy_initiative_turn_arrow(active=is_active, arrow_phase=arrow_phase)
            arrow_cell = self._kivy_markup_table_cell(
                arrow_text,
                4,
                color="facc15" if is_active else "8f7d62",
                bold=is_active,
            )
            roll_cell = self._kivy_markup_table_cell(
                int(shown),
                4,
                align="right",
                color=winner_color if is_leader else "b8a98d",
                bold=is_leader,
            )
            total_cell = self._kivy_markup_table_cell(
                total,
                5,
                align="right",
                color=winner_color if is_leader else "b8a98d",
                bold=is_leader,
            )
            status_text, status_color, status_bold = self._kivy_initiative_status_details(
                entry,
                final=final,
                leader=is_leader,
            )
            if is_active:
                status_text, status_color, status_bold = ("Acting", "facc15", True)
            lines.append(
                f"{arrow_cell}"
                f" [color=#8f7d62]|[/color] "
                f"{self._kivy_markup_table_cell(index, 2, align='right', color=rank_color, bold=is_leader)}"
                f" [color=#8f7d62]|[/color] "
                f"{self._kivy_markup_table_cell(actor_name, 19, color=actor_color, bold=is_leader or is_active)}"
                f" [color=#8f7d62]|[/color] "
                f"{roll_cell}"
                f" [color=#8f7d62]|[/color] "
                f"{self._kivy_markup_table_cell(f'{modifier:+d}', 4, align='right', color='d6c59a')}"
                f" [color=#8f7d62]|[/color] "
                f"{total_cell}"
                f" [color=#8f7d62]|[/color] "
                f"{self._kivy_markup_table_cell(status_text, 11, color=status_color, bold=status_bold)}"
            )
        return self._kivy_mono_span("\n".join(lines))

    def kivy_active_initiative_panel(self, *, active_actor_name: str, arrow_phase: int = 0) -> tuple[str, int] | None:
        entries = self._kivy_visible_initiative_entries(list(getattr(self, "_kivy_active_initiative_entries", []) or []))
        if not entries:
            return None
        markup = self._kivy_initiative_panel_markup(
            entries,
            final=True,
            active_actor_name=active_actor_name,
            arrow_phase=arrow_phase,
        )
        return markup, self._kivy_initiative_tray_height(entries)

    def show_combat_actor(self, actor) -> None:
        self.bridge.show_combat_actor(actor)

    def build_initiative_panel_lines(
        self,
        entries: list[dict[str, object]],
        *,
        shown_rolls: list[int] | None = None,
        final: bool,
    ) -> list[str]:
        return [
            self._kivy_initiative_panel_markup(
                entries,
                shown_rolls=shown_rolls,
                final=final,
            )
        ]

    def draw_initiative_panel_lines(self, lines: list[str], *, previous_line_count: int = 0) -> None:
        del previous_line_count
        markup = "\n".join(lines)
        final = "Initiative Order" in visible_markup_text(markup)
        line_count = visible_markup_text(markup).count("\n") + 1
        tray_height = min(320, max(150, 28 + 24 * line_count))
        self.bridge.show_dice_animation_frame(
            markup,
            final=final,
            use_tray=True,
            tray_height=tray_height,
            persist=final,
        )

    def render_kivy_initiative_panel(
        self,
        entries: list[dict[str, object]],
        *,
        shown_rolls: list[int],
        final: bool,
        frame_index: int = 0,
        frame_count: int = 1,
        pop_scale: float | None = None,
        clear_animation: bool | None = None,
    ) -> None:
        if final:
            self._kivy_active_initiative_entries = list(entries)
            entries = self._kivy_visible_initiative_entries(list(entries))
        markup = self._kivy_initiative_panel_markup(
            entries,
            shown_rolls=shown_rolls,
            final=final,
            frame_index=frame_index,
            frame_count=frame_count,
            pop_scale=pop_scale,
        )
        self.bridge.show_dice_animation_frame(
            markup,
            final=final if clear_animation is None else clear_animation,
            use_tray=True,
            tray_height=self._kivy_initiative_tray_height(entries),
            persist=final and (clear_animation is None or bool(clear_animation)),
        )

    def animate_initiative_rolls(self, entries: list[dict[str, object]]) -> None:
        if not entries:
            return
        if not self.animate_dice:
            self.render_kivy_initiative_panel(
                entries,
                shown_rolls=[getattr(entry["outcome"], "kept", 0) for entry in entries],
                final=True,
                clear_animation=True,
            )
            return
        self.begin_animation_skip_scope()
        try:
            duration = min(
                self._dice_animation_max_seconds + 0.35,
                max(
                    self._dice_animation_min_seconds + 0.12,
                    self._dice_animation_min_seconds + 0.08 * max(0, len(entries) - 1) + 0.24,
                ),
            )
            play_dice_roll_sound = getattr(self, "play_dice_roll_sound", None)
            if callable(play_dice_roll_sound):
                play_dice_roll_sound(duration, cooldown=0.08)
            frames = min(
                max(self._dice_animation_max_frames + 12, 1),
                max(
                    self._dice_animation_min_frames + 8,
                    int(max(1.0, duration) * max(1.0, self._dice_animation_frame_rate + 8)),
                ),
            )
            preview_rng = random.Random(time.perf_counter_ns() ^ len(entries) ^ (id(entries) << 1))
            final_rolls = [getattr(entry["outcome"], "kept", 0) for entry in entries]
            skipped = False
            for index, delay in enumerate(kivy_dice_frame_delays(frames, duration)):
                shown = self.initiative_preview_rolls(
                    final_rolls,
                    preview_rng=preview_rng,
                    progress=(index + 1) / max(1, frames),
                )
                self.render_kivy_initiative_panel(
                    entries,
                    shown_rolls=shown,
                    final=False,
                    frame_index=index,
                    frame_count=frames,
                    clear_animation=False,
                )
                if self.sleep_for_dice_animation(delay):
                    skipped = True
                    break
            if not skipped:
                for pop_scale, pause in (
                    (1.52, 0.045),
                    (0.84, 0.035),
                    (1.28, 0.04),
                    (0.96, 0.035),
                    (1.10, 0.035),
                ):
                    self.render_kivy_initiative_panel(
                        entries,
                        shown_rolls=final_rolls,
                        final=True,
                        pop_scale=pop_scale,
                        clear_animation=False,
                    )
                    skipped = self.sleep_for_dice_animation(pause)
                    if skipped:
                        break
            self.render_kivy_initiative_panel(
                entries,
                shown_rolls=final_rolls,
                final=True,
                pop_scale=1.0,
                clear_animation=True,
            )
            if self._dice_total_reveal_pause_seconds > 0:
                self.sleep_for_animation(self._dice_total_reveal_pause_seconds, require_animation=True)
            if self._dice_animation_final_pause_seconds > 0:
                self.sleep_for_animation(self._dice_animation_final_pause_seconds, require_animation=True)
        finally:
            self.end_animation_skip_scope()

    def sleep_for_animation(self, duration: float, *, require_animation: bool = False) -> bool:
        if require_animation and not self.animate_dice:
            return False
        return self.bridge.wait_for_animation(duration)

    def kivy_combat_is_ending(self) -> bool:
        enemies = list(getattr(self, "_active_combat_enemies", []) or [])
        return bool(enemies) and not any(enemy.is_conscious() for enemy in enemies)

    def pause_for_combat_transition(self) -> None:
        if getattr(self, "_in_combat", False):
            ending = self.kivy_combat_is_ending()
            self.bridge.wait_for_combat_transition(ending=ending)
            return
        super().pause_for_combat_transition()

    def after_actor_damaged(self, target, *, previous_hp: int, damage: int, damage_type: str = "") -> None:
        super().after_actor_damaged(target, previous_hp=previous_hp, damage=damage, damage_type=damage_type)
        if getattr(self, "_in_combat", False):
            if self.kivy_combat_is_ending():
                self.bridge.fade_out_initiative_tray()
            elif self._kivy_initiative_actor_is_defeated_enemy(target):
                self.bridge.refresh_active_initiative_tray()
            self.bridge.refresh_combat_panel()

    def kivy_side_panel_available(self) -> bool:
        return self.state is not None and not getattr(self, "_at_title_screen", False)

    def kivy_side_command_title(self, raw: str) -> str:
        normalized = " ".join(str(raw).strip().lower().split())
        titles = {
            "~": "Console",
            "console": "Console",
            "console menu": "Console",
            "console commands": "Console",
            "help": "Commands",
            "helpconsole": "Console Commands",
            "console help": "Console Commands",
            "load": "Load Game",
            "save/load": "Save/Load",
            "save load": "Save/Load",
            "saveload": "Save/Load",
            "saves": "Save Files",
            "save files": "Save Files",
            "settings": "Settings",
            "save": "Save",
            "party": "Party",
            "journal": "Journal",
            "inventory": "Inventory",
            "backpack": "Inventory",
            "bag": "Inventory",
            "equipment": "Gear",
            "gear": "Gear",
            "sheet": "Character Sheets",
            "sheets": "Character Sheets",
            "character": "Character Sheets",
            "characters": "Character Sheets",
            "camp": "Camp",
            "map": "Map",
            "maps": "Map",
            "map menu": "Map",
            "quit": "Quit",
        }
        return titles.get(normalized, normalized.title() or "Command")

    def kivy_should_route_command_to_side(self, raw: str) -> bool:
        if not self.kivy_side_panel_available():
            return False
        normalized = " ".join(str(raw).strip().lower().split())
        return normalized in {
            "~",
            "console",
            "console menu",
            "console commands",
            "help",
            "helpconsole",
            "console help",
            "load",
            "save/load",
            "save load",
            "saveload",
            "saves",
            "save files",
            "settings",
            "save",
            "party",
            "journal",
            "inventory",
            "backpack",
            "bag",
            "equipment",
            "gear",
            "sheet",
            "sheets",
            "character",
            "characters",
            "camp",
            "map",
            "maps",
            "map menu",
            "quit",
        }

    def kivy_should_show_native_command(self, raw: str) -> bool:
        if not self.kivy_side_panel_available() or getattr(self, "_in_combat", False):
            return False
        normalized = " ".join(str(raw).strip().lower().split())
        return normalized in {
            "camp",
            "map",
            "maps",
            "map menu",
            "journal",
            "inventory",
            "backpack",
            "bag",
            "equipment",
            "gear",
        }

    def open_kivy_quit_menu(self) -> bool:
        active_adventure = bool(
            getattr(self, "state", None) is not None
            and not getattr(self, "_at_title_screen", False)
        )
        options = ["Quit to Main Menu", "Quit to Desktop", "Back"] if active_adventure else ["Quit to Desktop", "Back"]
        display_options = [self.format_option_text(option) for option in options]
        while True:
            raw = self.bridge.request_choice("Quit menu.", display_options).strip()
            if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                self.handle_kivy_close_token()
                continue
            normalized = " ".join(raw.strip().lower().split())
            selected = ""
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= len(options):
                    selected = options[value - 1]
            else:
                aliases = {
                    "quit to desktop": "Quit to Desktop",
                    "desktop": "Quit to Desktop",
                    "exit": "Quit to Desktop",
                    "close": "Quit to Desktop",
                    "back": "Back",
                    "cancel": "Back",
                    "stay": "Back",
                }
                menu_aliases = {
                    "quit to main menu",
                    "main menu",
                    "menu",
                    "quit to title",
                    "title",
                    "title screen",
                }
                aliases.update(
                    {alias: "Quit to Main Menu" if active_adventure else "Back" for alias in menu_aliases}
                )
                selected = aliases.get(normalized, "")
                if selected not in options:
                    selected = ""

            if selected == "Quit to Main Menu":
                self.state = None
                self._compact_hud_last_scene_key = None
                raise ReturnToTitleMenu()
            if selected == "Quit to Desktop":
                self.bridge.close_app_on_finish()
                raise QuitProgram()
            if selected == "Back":
                if active_adventure:
                    self.say("You stay with the current adventure.")
                else:
                    self.say("You remain at the main menu.")
                return True
            self.say("Please choose one of the listed quit options.")

    def open_kivy_save_load_menu(self) -> bool:
        active_adventure = bool(
            getattr(self, "state", None) is not None
            and not getattr(self, "_at_title_screen", False)
        )
        options = ["Save Game", "Load Game", "Back"] if active_adventure else ["Load Game", "Back"]
        display_options = [self.format_option_text(option) for option in options]
        while True:
            raw = self.bridge.request_choice("Save/Load.", display_options).strip()
            if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                self.handle_kivy_close_token()
                continue
            normalized = " ".join(raw.strip().lower().split())
            selected = ""
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= len(options):
                    selected = options[value - 1]
            else:
                aliases = {
                    "save": "Save Game",
                    "save game": "Save Game",
                    "load": "Load Game",
                    "load game": "Load Game",
                    "saves": "Load Game",
                    "save files": "Load Game",
                    "back": "Back",
                    "cancel": "Back",
                }
                selected = aliases.get(normalized, "")
                if selected not in options:
                    selected = ""

            if selected == "Save Game":
                self.inline_save()
                return True
            if selected == "Load Game":
                return self.open_save_files_menu()
            if selected == "Back":
                return True
            self.say("Please choose one of the listed save/load options.")

    def handle_meta_command(self, raw: str) -> bool:
        normalized = " ".join(str(raw).strip().lower().split())
        camp_talk_match = re.fullmatch(r"(?:camp talk|talk companion|talk to companion)(?: (?P<index>\d+))?", normalized)
        if camp_talk_match:
            if self.state is None:
                self.say("There is no active adventure yet, so camp is not available.")
                return True
            if getattr(self, "_in_combat", False):
                self.say("You cannot head to camp during combat.")
                return True
            companion = None
            index_text = camp_talk_match.group("index")
            if index_text is not None:
                roster = self.state.all_companions()
                companion_index = int(index_text) - 1
                if not 0 <= companion_index < len(roster):
                    self.say("Choose a valid companion to talk to at camp.")
                    return True
                companion = roster[companion_index]
            self.talk_to_companion(companion)
            return True
        if normalized in {"save/load", "save load", "saveload"}:
            return self.open_kivy_save_load_menu()
        if normalized == "quit":
            return self.open_kivy_quit_menu()
        if self.kivy_should_show_native_command(raw):
            self.bridge.show_native_command(normalized)
            return True
        if not self.kivy_should_route_command_to_side(raw):
            try:
                return super().handle_meta_command(raw)
            except QuitProgram:
                normalized = " ".join(str(raw).strip().lower().split())
                if normalized == "quit" and getattr(self, "_at_title_screen", False):
                    self.bridge.close_app_on_finish()
                raise
        self.bridge.begin_side_command(self.kivy_side_command_title(raw))
        try:
            return super().handle_meta_command(raw)
        except QuitProgram:
            normalized = " ".join(str(raw).strip().lower().split())
            if normalized == "quit" and getattr(self, "_at_title_screen", False):
                self.bridge.close_app_on_finish()
            raise
        except KivySideCommandClosed:
            return True
        finally:
            self.bridge.end_side_command()

    def kivy_close_token_cancels_active_side_command(self) -> bool:
        return bool(getattr(self.bridge, "side_command_active", False))

    def handle_kivy_close_token(self) -> None:
        if self.kivy_close_token_cancels_active_side_command():
            raise KivySideCommandClosed

    def say(self, text: str, *, typed: bool = False) -> None:
        if not text:
            self.output_fn("")
            return
        for paragraph in str(text).split("\n"):
            self.output_fn(paragraph)

    def banner(self, title: str) -> None:
        self.output_fn("")
        self.output_fn(f"=== {title} ===")

    def render_act1_overworld_map(self, *, force: bool = False) -> None:
        if self.kivy_side_panel_available():
            self.bridge.show_overworld_map(ACT1_HYBRID_MAP, self.act1_map_state(), "Act I Overworld")
            return
        super().render_act1_overworld_map(force=force)

    def render_act1_dungeon_map(self, dungeon, *, force: bool = False) -> None:
        if self.kivy_side_panel_available():
            self.bridge.show_dungeon_map(dungeon, self.act1_map_state(), dungeon.title)
            return
        super().render_act1_dungeon_map(dungeon, force=force)

    def render_act2_overworld_map(self, *, force: bool = False) -> None:
        if self.kivy_side_panel_available():
            self.bridge.show_overworld_map(ACT2_ENEMY_DRIVEN_MAP, self.act2_map_state(), "Act II Route Map")
            return
        super().render_act2_overworld_map(force=force)

    def render_act2_dungeon_map(self, dungeon, *, force: bool = False) -> None:
        if self.kivy_side_panel_available():
            self.bridge.show_dungeon_map(dungeon, self.act2_map_state(), dungeon.title)
            return
        super().render_act2_dungeon_map(dungeon, force=force)

    def choose_title_menu(
        self,
        title: str,
        subtitle: str,
        intro_text: str,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> int:
        save_summary, save_detail = self.title_screen_save_summary()
        self.bridge.show_title_menu(
            title=title,
            subtitle=subtitle,
            intro_text=intro_text,
            campaign_summary=self.title_screen_campaign_summary(),
            save_summary=save_summary,
            save_detail=save_detail,
            audio_summary=self.title_screen_audio_summary(),
            presentation_summary=self.title_screen_presentation_summary(),
        )
        choice = self.choose_with_display_mode(
            "Choose your route.",
            options,
            allow_meta=True,
            show_hud=False,
            option_details=option_details,
        )
        if 1 <= choice <= len(options) and strip_ansi(options[choice - 1]).strip().lower() == "quit":
            self.bridge.close_app_on_finish()
        return choice

    def kivy_save_browser_entry(self, path: Path) -> dict[str, str]:
        preview = self.save_preview_payload(path)
        return {
            "title": self.save_preview_short_label(path),
            "meta": f"Saved {preview['saved_at_label']} | Lv {preview['party_level']}",
            "detail_title": self.save_preview_short_label(path),
            "detail": self.save_preview_detail(path),
        }

    def open_save_files_menu(self) -> bool:
        while True:
            saves = self.loadable_save_paths()
            if not saves:
                self.say("No save files were found yet.")
                return False
            entries = [self.kivy_save_browser_entry(path) for path in saves]
            raw = self.bridge.request_save_browser_choice("Save Files", entries).strip()
            if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN or raw.lower() in {"back", "b"}:
                return False
            if raw.isdigit():
                selected_index = int(raw) - 1
                if 0 <= selected_index < len(saves):
                    selected = saves[selected_index]
                    action = self.bridge.request_save_action_choice(entries[selected_index]).strip().lower()
                    if action == KIVY_SIDE_COMMAND_CLOSE_TOKEN or action in {"back", "b"}:
                        continue
                    if action in {"load", "1"}:
                        self.load_save_path(selected)
                        return True
                    if action in {"delete", "2"}:
                        self.delete_save_path(selected)
                        continue
            self.say("Please choose one of the listed save files.")

    def ask_text(self, prompt: str) -> str:
        while True:
            value = self.bridge.request_text(f"{prompt}:").strip()
            if value == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                self.handle_kivy_close_token()
                continue
            if self.handle_meta_command(value):
                continue
            if value:
                return value
            self.say("Please enter a value.")

    def read_input(self, prompt: str) -> str:
        value = self.bridge.request_text(prompt)
        if value == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
            self.handle_kivy_close_token()
            return ""
        return value

    def set_kivy_dark_mode_enabled(self, enabled: bool) -> None:
        self._kivy_dark_mode_preference = bool(enabled)
        self.bridge.set_kivy_dark_mode(self._kivy_dark_mode_preference)
        self.persist_settings()
        self.say(f"Kivy dark mode {'enabled' if self._kivy_dark_mode_preference else 'disabled'}.")

    def toggle_kivy_dark_mode(self) -> None:
        self.set_kivy_dark_mode_enabled(
            not getattr(self, "_kivy_dark_mode_preference", self.DEFAULT_KIVY_DARK_MODE_ENABLED)
        )

    def set_kivy_fullscreen_enabled(self, enabled: bool) -> None:
        self._kivy_fullscreen_preference = bool(enabled)
        self.bridge.set_kivy_fullscreen(self._kivy_fullscreen_preference)
        self.persist_settings()
        self.say(f"Kivy fullscreen {'enabled' if self._kivy_fullscreen_preference else 'disabled'}.")

    def toggle_kivy_fullscreen(self) -> None:
        self.set_kivy_fullscreen_enabled(
            not getattr(self, "_kivy_fullscreen_preference", self.DEFAULT_KIVY_FULLSCREEN_ENABLED)
        )

    def open_settings_menu(self) -> None:
        while True:
            music_available = bool(getattr(self, "_music_assets_ready", False))
            options = [
                f"Toggle sound effects ({self.settings_toggle_label(getattr(self, 'sound_effects_enabled', False))})",
                (
                    f"Toggle music ({self.settings_toggle_label(getattr(self, 'music_enabled', False), unavailable=not music_available)})"
                ),
                f"Difficulty ({self.difficulty_mode_label()})",
                f"Toggle typed dialogue and narration ({self.settings_toggle_label(getattr(self, '_typed_dialogue_preference', self.type_dialogue))})",
                f"Toggle pacing pauses ({self.settings_toggle_label(getattr(self, '_pacing_pauses_preference', self.pace_output))})",
                f"Toggle staggered option reveals ({self.settings_toggle_label(getattr(self, '_staggered_reveals_preference', getattr(self, 'staggered_reveals_enabled', False)))})",
                f"Toggle Karmic Dice ({self.settings_toggle_label(self.current_karmic_dice_enabled())})",
                f"Toggle Kivy dark mode ({self.settings_toggle_label(getattr(self, '_kivy_dark_mode_preference', self.DEFAULT_KIVY_DARK_MODE_ENABLED))})",
                f"Toggle fullscreen ({self.settings_toggle_label(getattr(self, '_kivy_fullscreen_preference', self.DEFAULT_KIVY_FULLSCREEN_ENABLED))})",
                "Back",
            ]
            choice = self.choose("Settings", options, allow_meta=False)
            if choice == 1:
                toggle_sound_effects = getattr(self, "toggle_sound_effects", None)
                if callable(toggle_sound_effects):
                    toggle_sound_effects()
                else:
                    self.say("Sound effects are not supported in this build.")
                continue
            if choice == 2:
                toggle_music = getattr(self, "toggle_music", None)
                if callable(toggle_music):
                    toggle_music()
                else:
                    self.say("Music playback is not supported in this build.")
                continue
            if choice == 3:
                self.open_difficulty_settings()
                continue
            if choice == 4:
                self.toggle_typed_dialogue()
                continue
            if choice == 5:
                self.toggle_pacing_pauses()
                continue
            if choice == 6:
                self.toggle_staggered_reveals()
                continue
            if choice == 7:
                self.toggle_karmic_dice()
                continue
            if choice == 8:
                self.toggle_kivy_dark_mode()
                continue
            if choice == 9:
                self.toggle_kivy_fullscreen()
                continue
            return

    def browse_lore_section(self, title: str, entries: dict[str, dict[str, str]]) -> None:
        names = list(entries)
        visible_slots = max(1, MENU_PAGE_SIZE - 3)
        page = 0
        while True:
            start = page * visible_slots
            visible_names = names[start : start + visible_slots]
            labels = ["Return to lore categories", *[self.lore_menu_label(name, entries[name]) for name in visible_names]]
            nav_map: dict[int, str] = {}
            if page > 0:
                labels.append("Previous page")
                nav_map[len(labels)] = "prev"
            if start + visible_slots < len(names):
                labels.append("Next page")
                nav_map[len(labels)] = "next"
            choice = self.choose(
                f"Browse {title}. (page {page + 1})",
                labels,
                allow_meta=False,
                show_hud=False,
            )
            if choice == 1:
                return
            if choice in nav_map:
                page = page - 1 if nav_map[choice] == "prev" else page + 1
                continue
            entry_index = choice - 2
            if 0 <= entry_index < len(visible_names):
                selected = visible_names[entry_index]
                return_to_categories = self.show_lore_entry(title, selected, entries[selected])
                if return_to_categories:
                    return
                continue
            self.say("Please choose one of the listed lore options.")

    def kivy_combat_group_label(self, section: str, grouped_options: list[tuple[int, str]]) -> str:
        if section == "End Turn" and len(grouped_options) == 1:
            return "End Turn"
        option_count = len(grouped_options)
        noun = "option" if option_count == 1 else "options"
        return f"[{section}] {option_count} {noun}"

    def kivy_combatant_target_option(self, combatant) -> str:
        name = strip_ansi(self.style_name(combatant))
        current_hp = max(0, int(getattr(combatant, "current_hp", 0)))
        max_hp = max(1, int(getattr(combatant, "max_hp", current_hp or 1)))
        return f"{name}: HP {current_hp}/{max_hp}"

    def combatant_menu_options(self, combatants: list) -> list[str]:
        return [self.kivy_combatant_target_option(combatant) for combatant in combatants]

    def choose_kivy_combat_group_action(
        self,
        prompt: str,
        section: str,
        grouped_options: list[tuple[int, str]],
    ) -> str | None:
        action_options = [self.format_option_text(option) for _display_index, option in grouped_options]
        action_options.append("Back")
        while True:
            raw = self.bridge.request_choice(f"{section} - {prompt}", action_options).strip()
            if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                self.handle_kivy_close_token()
                continue
            if self.handle_meta_command(raw):
                continue
            normalized = raw.strip().lower()
            if normalized in {"back", "b"}:
                return None
            if raw.isdigit():
                selected = int(raw)
                if selected == len(action_options):
                    return None
                if 1 <= selected <= len(grouped_options):
                    return grouped_options[selected - 1][1]
            self.say("Please choose one of the listed combat options.")

    def choose_grouped_combat_option(
        self,
        prompt: str,
        options: list[str],
        *,
        actor=None,
        heroes=None,
        enemies=None,
    ) -> str:
        self.bridge.show_combat_actor(actor)
        while True:
            indexed, sections = self.group_combat_options(options)
            if len(sections) <= 1:
                ordered_indexes = sorted(indexed)
                display_options = [self.format_option_text(indexed[index]) for index in ordered_indexes]
                raw = self.bridge.request_choice(prompt, display_options).strip()
                if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                    self.handle_kivy_close_token()
                    continue
                if self.handle_meta_command(raw):
                    continue
                if raw.isdigit():
                    selected = int(raw)
                    if 1 <= selected <= len(ordered_indexes):
                        return indexed[ordered_indexes[selected - 1]]
                self.say("Please choose one of the listed combat options.")
                continue

            group_lookup = {index: section for index, section in enumerate(sections, start=1)}
            group_options = [
                self.kivy_combat_group_label(section, grouped_options)
                for section, grouped_options in sections
            ]
            raw = self.bridge.request_choice(prompt, group_options).strip()
            if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                self.handle_kivy_close_token()
                continue
            if self.handle_meta_command(raw):
                continue
            if raw.isdigit():
                selected = int(raw)
                if selected in group_lookup:
                    section, grouped_options = group_lookup[selected]
                    if section == "End Turn" and len(grouped_options) == 1:
                        return grouped_options[0][1]
                    selected_option = self.choose_kivy_combat_group_action(prompt, section, grouped_options)
                    if selected_option is not None:
                        return selected_option
                    continue
            self.say("Please choose one of the listed combat groups.")

    def choose_with_display_mode(
        self,
        prompt: str,
        options: list[str],
        *,
        allow_meta: bool = True,
        staggered: bool = False,
        show_hud: bool = True,
        sticky_trailing_options: int = 0,
        option_details: dict[str, str] | None = None,
    ) -> int:
        del allow_meta, staggered, show_hud
        if not options:
            raise ValueError("Choice lists must contain at least one option.")

        sticky_count = max(0, min(sticky_trailing_options, len(options) - 1))
        sticky_options = options[-sticky_count:] if sticky_count else []
        paged_options = options[:-sticky_count] if sticky_count else options
        page_size = max(1, MENU_PAGE_SIZE - sticky_count)

        if len(paged_options) > page_size:
            page = 0
            while True:
                start = page * page_size
                visible = paged_options[start : start + page_size]
                labels = [*visible, *sticky_options]
                nav_map: dict[int, str] = {}
                sticky_map = {
                    len(visible) + offset + 1: len(paged_options) + offset + 1
                    for offset in range(len(sticky_options))
                }
                if page > 0:
                    labels.append("Previous page")
                    nav_map[len(labels)] = "prev"
                if start + page_size < len(paged_options):
                    labels.append("Next page")
                    nav_map[len(labels)] = "next"

                paged_prompt = f"{prompt} (page {page + 1})" if prompt else f"Page {page + 1}"
                display_labels = [self.format_option_text(label) for label in labels]
                raw = self.bridge.request_choice(paged_prompt, display_labels).strip()
                if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                    self.handle_kivy_close_token()
                    continue
                if self.handle_meta_command(raw):
                    continue
                if raw.isdigit():
                    value = int(raw)
                    if value in nav_map:
                        page = page - 1 if nav_map[value] == "prev" else page + 1
                        continue
                    if value in sticky_map:
                        return sticky_map[value]
                    if 1 <= value <= len(visible):
                        return start + value
                self.say("Please choose one of the listed options.")

        while True:
            display_options = [self.format_option_text(option) for option in options]
            display_details = None
            if option_details:
                display_details = {
                    display_option: option_details[option]
                    for option, display_option in zip(options, display_options)
                    if option in option_details
                }
            raw = self.bridge.request_choice(prompt, display_options, option_details=display_details).strip()
            if raw == KIVY_SIDE_COMMAND_CLOSE_TOKEN:
                self.handle_kivy_close_token()
                continue
            if self.handle_meta_command(raw):
                continue
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= len(options):
                    return value
            self.say("Please choose one of the listed options.")


class GameScreen(BoxLayout):
    F11_KEY_CODE = 292
    F11_FALLBACK_KEY_CODE = 65480
    F11_SCANCODES = {68, 87}
    MAX_LOG_ENTRIES = 900
    TYPEWRITER_INTERVAL_SECONDS = 0.035
    TYPEWRITER_CHARS_PER_TICK = 1
    TYPEWRITER_FULLSTOP_PAUSE_SECONDS = 0.5
    TYPEWRITER_WAIT_PADDING_SECONDS = 2.0
    NON_DIALOGUE_FADE_INTERVAL_SECONDS = 0.05
    COMBAT_RESOURCE_ANIMATION_INTERVAL_SECONDS = 0.08
    COMBAT_RESOURCE_ANIMATION_MAX_STEPS = 12
    COMBAT_HP_IMPACT_RED_SECONDS = 0.18
    COMBAT_HP_IMPACT_RECOVER_SECONDS = 0.16
    COMBAT_HP_IMPACT_SHAKE_OFFSETS = (1, 0, 2, 0, 1, 0)
    COMBAT_DAMAGE_NUMBER_HOLD_SECONDS = 0.18
    COMBAT_DAMAGE_NUMBER_FADE_SECONDS = 0.72
    COMBAT_ENTRY_TRANSITION_SECONDS = 0.35
    COMBAT_EXIT_TRANSITION_SECONDS = 1.05
    DEFEATED_ENEMY_HOLD_SECONDS = 0.25
    DEFEATED_ENEMY_FADE_SECONDS = 0.65
    DEFEATED_ENEMY_FADE_INTERVAL_SECONDS = 0.05
    INITIATIVE_TURN_ARROW_INTERVAL_SECONDS = 0.28
    SINGLE_TEXT_WINDOW_FONT_SIZE = "20sp"
    SPLIT_TEXT_WINDOW_FONT_SIZE = "17sp"
    OPTION_BUTTON_MIN_HEIGHT = 48
    OPTION_BUTTON_ROW_GAP = 6
    OPTION_BUTTON_VISIBLE_ROWS = 4
    CHOICE_SCROLL_INDICATOR_WIDTH = 28
    CHOICE_SCROLL_INDICATOR_PULSE_SECONDS = 0.48
    BUTTON_FONT_MIN_SP = 7
    BUTTON_FONT_MAX_SP = 24
    BUTTON_TEXT_HORIZONTAL_PADDING = 16
    BUTTON_TEXT_VERTICAL_PADDING = 8
    DICE_ANIMATION_TRAY_HEIGHT = 118
    DICE_ANIMATION_TRAY_MAX_HEIGHT = 340
    DICE_ANIMATION_TRAY_HIDE_SECONDS = 5.0
    DICE_ANIMATION_TRAY_FADE_SECONDS = 0.22
    SEND_BUTTON_FONT_SIZE = "14sp"
    COMMAND_BUTTON_FONT_SIZE = "15sp"
    COMMAND_BAR_HEIGHT = 40
    COMMAND_BAR_ANIMATION_SECONDS = 0.18
    RIGHT_PANEL_WIDTH_FRACTION = 0.40
    NATIVE_COMMAND_PANEL_WIDTH_FRACTION = 0.40
    LOG_EXAMINE_STOP_LABELS = frozenset(
        {
            "audio",
            "bonus",
            "campaign",
            "commands",
            "current consequences",
            "current site",
            "latest",
            "location",
            "note",
            "objective",
            "outcome",
            "presentation",
            "recent updates",
            "reroll",
            "roll",
            "saves",
            "source",
            "target",
            "total",
            "value",
        }
    )
    TITLE_MENU_TRANSITION_SECONDS = 0.38
    COMMANDS = [
        "save/load",
        "map",
        "journal",
        "inventory",
        "gear",
        "camp",
        "settings",
        "quit",
    ]
    COMMAND_LABELS = {
        "save/load": "Save/Load",
        "map": "Map",
        "journal": "Journal",
        "inventory": "Inventory",
        "gear": "Gear",
        "camp": "Camp",
        "settings": "Settings",
        "quit": "Quit",
    }
    KIVY_DARK_MODE_SETTING_KEY = ClickableTextDnDGame.KIVY_DARK_MODE_SETTING_KEY
    KIVY_FULLSCREEN_SETTING_KEY = ClickableTextDnDGame.KIVY_FULLSCREEN_SETTING_KEY
    DEFAULT_KIVY_DARK_MODE_ENABLED = ClickableTextDnDGame.DEFAULT_KIVY_DARK_MODE_ENABLED
    DEFAULT_KIVY_FULLSCREEN_ENABLED = ClickableTextDnDGame.DEFAULT_KIVY_FULLSCREEN_ENABLED
    DARK_THEME = {
        "window": (0.055, 0.050, 0.045, 1),
        "header": (0.13, 0.10, 0.07, 1),
        "panel": (0.08, 0.07, 0.055, 1),
        "options": (0.11, 0.13, 0.10, 1),
        "combat": (0.075, 0.075, 0.085, 1),
        "examine": (0.035, 0.105, 0.100, 1),
        "title_panel": (0.035, 0.070, 0.073, 1),
        "title_info_panel": (0.025, 0.052, 0.055, 0.96),
        "title_info_header": (0.44, 0.84, 0.81, 1),
        "title_info_label": (0.85, 0.67, 0.34, 1),
        "title_info_value": (0.94, 0.90, 0.82, 1),
        "title_options": (0.045, 0.120, 0.125, 1),
        "title": (0.96, 0.78, 0.28, 1),
        "status": (0.78, 0.70, 0.58, 1),
        "text": (0.92, 0.86, 0.74, 1),
        "prompt": (0.94, 0.78, 0.36, 1),
        "input_bg": (0.96, 0.91, 0.78, 1),
        "input_text": (0.12, 0.09, 0.06, 1),
        "cursor": (0.82, 0.56, 0.18, 1),
        "send_bg": (0.36, 0.22, 0.08, 1),
        "send_text": (1, 0.98, 0.94, 1),
        "command_bg": (0.48, 0.36, 0.18, 1),
        "command_text": (1, 0.94, 0.78, 1),
        "command_disabled_bg": (0.20, 0.20, 0.18, 1),
        "command_disabled_text": (0.58, 0.55, 0.49, 1),
        "choice_bg": (0.20, 0.42, 0.34, 1),
        "choice_text": (1, 0.98, 0.94, 1),
        "choice_group_bg": (0.38, 0.28, 0.12, 1),
        "choice_group_text": (1, 0.96, 0.82, 1),
        "choice_end_turn_bg": (0.46, 0.16, 0.14, 1),
        "choice_end_turn_text": (1, 0.94, 0.90, 1),
        "choice_back_bg": (0.20, 0.28, 0.42, 1),
        "choice_back_text": (0.92, 0.96, 1, 1),
        "title_choice_primary_bg": (0.66, 0.40, 0.13, 1),
        "title_choice_primary_text": (1.0, 0.96, 0.84, 1),
        "title_choice_bg": (0.08, 0.32, 0.34, 1),
        "title_choice_text": (0.95, 0.93, 0.84, 1),
        "title_choice_utility_bg": (0.18, 0.24, 0.22, 1),
        "title_choice_back_bg": (0.16, 0.24, 0.40, 1),
        "title_choice_back_text": (0.92, 0.96, 1.0, 1),
        "title_choice_quit_bg": (0.26, 0.16, 0.14, 1),
        "title_choice_disabled_bg": (0.18, 0.18, 0.17, 1),
        "title_choice_disabled_text": (0.54, 0.52, 0.48, 1),
        "dice_tray": (0.105, 0.085, 0.055, 1),
        "dice_tray_text": (0.96, 0.86, 0.62, 1),
    }
    LIGHT_THEME = {
        "window": (0.93, 0.89, 0.80, 1),
        "header": (0.74, 0.57, 0.31, 1),
        "panel": (0.97, 0.93, 0.82, 1),
        "options": (0.89, 0.82, 0.66, 1),
        "combat": (0.91, 0.86, 0.75, 1),
        "examine": (0.78, 0.89, 0.84, 1),
        "title_panel": (0.84, 0.91, 0.88, 1),
        "title_info_panel": (0.78, 0.87, 0.84, 1),
        "title_info_header": (0.05, 0.36, 0.36, 1),
        "title_info_label": (0.45, 0.27, 0.08, 1),
        "title_info_value": (0.16, 0.11, 0.07, 1),
        "title_options": (0.78, 0.88, 0.84, 1),
        "title": (0.18, 0.12, 0.06, 1),
        "status": (0.30, 0.23, 0.14, 1),
        "text": (0.16, 0.11, 0.07, 1),
        "prompt": (0.34, 0.22, 0.08, 1),
        "input_bg": (0.99, 0.96, 0.88, 1),
        "input_text": (0.12, 0.08, 0.04, 1),
        "cursor": (0.40, 0.25, 0.10, 1),
        "send_bg": (0.58, 0.39, 0.16, 1),
        "send_text": (1, 0.98, 0.92, 1),
        "command_bg": (0.74, 0.58, 0.37, 1),
        "command_text": (0.16, 0.11, 0.07, 1),
        "command_disabled_bg": (0.62, 0.60, 0.54, 1),
        "command_disabled_text": (0.38, 0.36, 0.32, 1),
        "choice_bg": (0.36, 0.58, 0.47, 1),
        "choice_text": (0.06, 0.08, 0.06, 1),
        "choice_group_bg": (0.70, 0.53, 0.25, 1),
        "choice_group_text": (0.12, 0.08, 0.03, 1),
        "choice_end_turn_bg": (0.75, 0.30, 0.24, 1),
        "choice_end_turn_text": (0.12, 0.04, 0.03, 1),
        "choice_back_bg": (0.45, 0.57, 0.74, 1),
        "choice_back_text": (0.04, 0.07, 0.12, 1),
        "title_choice_primary_bg": (0.58, 0.32, 0.12, 1),
        "title_choice_primary_text": (1.0, 0.96, 0.86, 1),
        "title_choice_bg": (0.20, 0.52, 0.54, 1),
        "title_choice_text": (0.03, 0.10, 0.10, 1),
        "title_choice_utility_bg": (0.55, 0.68, 0.58, 1),
        "title_choice_back_bg": (0.45, 0.57, 0.74, 1),
        "title_choice_back_text": (0.04, 0.07, 0.12, 1),
        "title_choice_quit_bg": (0.72, 0.48, 0.42, 1),
        "title_choice_disabled_bg": (0.64, 0.62, 0.56, 1),
        "title_choice_disabled_text": (0.36, 0.34, 0.30, 1),
        "dice_tray": (0.82, 0.73, 0.55, 1),
        "dice_tray_text": (0.18, 0.12, 0.06, 1),
    }
    TITLE_MENU_LABELS = {
        "continue": "Continue",
        "start a new game": "New Game",
        "save files": "Save Files",
        "read the lore notes": "Lore Notes",
        "settings": "Settings",
        "quit": "Quit",
    }
    TITLE_MENU_CAPTIONS = {
        "continue": "Load latest save",
        "start a new game": "Build a character",
        "save files": "Browse saves and journals",
        "read the lore notes": "World notes and mechanics",
        "settings": "Audio, animations, pacing",
        "quit": "Close the window",
    }

    def __init__(self, *, load_save: str | None = None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(6), **kwargs)
        self._log_lines: list[str] = []
        self._input_separator_pending = False
        self._typing_queue: list[tuple[str, Event | None]] = []
        self._typing_current_markup: str | None = None
        self._typing_current_event: Event | None = None
        self._typing_current_index: int | None = None
        self._typing_current_visible_text = ""
        self._typing_visible_characters = 0
        self._typing_total_characters = 0
        self._dice_animation_line_index: int | None = None
        self._dice_tray_active = False
        self._dice_tray_hide_event = None
        self._dice_tray_hide_ready_at = 0.0
        self._dice_tray_transient_hold_until = 0.0
        self._dice_tray_fade_generation = 0
        self._dice_roll_tray_active = False
        self._dice_roll_tray_fade_generation = 0
        self._persistent_dice_tray_markup = ""
        self._persistent_dice_tray_height: float | None = None
        self._persistent_dice_tray_parts: tuple[str, str, str] | None = None
        self._persistent_dice_tray_pulse_scale = 1.0
        self._persistent_dice_tray_core_slot_width: float | None = None
        self._fade_animation_event = None
        self._fade_animation_index: int | None = None
        self._fade_animation_markup = ""
        self._fade_animation_done_event: Event | None = None
        self._delayed_done_events: list[tuple[Event, object]] = []
        self._animation_sleep_event = Event()
        self._animation_sleep_active = False
        self._combat_resource_display_values: dict[tuple[int, str], int] = {}
        self._combat_resource_targets: dict[tuple[int, str], int] = {}
        self._combat_resource_animation_event = None
        self._combat_hp_impact_elapsed: dict[tuple[int, str], float] = {}
        self._combat_damage_popups: dict[tuple[int, str], tuple[int, float]] = {}
        self._defeated_enemy_fade_elapsed: dict[int, float] = {}
        self._hidden_defeated_enemy_ids: set[int] = set()
        self._defeated_enemy_fade_event = None
        self._active_combat_actor_name = ""
        self._initiative_turn_arrow_phase = 0
        self._initiative_turn_arrow_event = None
        self._combat_mode_enabled = False
        self._side_panel_visible = False
        self._side_panel_mode = "default"
        self._side_command_title = ""
        self._side_command_lines: list[str] = []
        self._examine_panel_visible = False
        self._examine_ref_entries: dict[str, ExamineEntry] = {}
        self._examine_ref_counter = 0
        self._log_examine_ref_entries: dict[str, ExamineEntry] = {}
        self._log_examine_ref_counter = 0
        self._save_browser_active = False
        self._save_browser_root: PanelBox | None = None
        self._save_browser_detail_panel: PanelBox | None = None
        self._save_browser_detail_label: WrappedLabel | None = None
        self._save_browser_detail_scroll: ScrollView | None = None
        self._standard_widgets: list[Widget] = []
        self._current_option_rows = 0
        self._current_options_detailed = False
        self._title_menu_active = False
        self._title_menu_transition_active = False
        self._main_title_menu_active = False
        self._command_bar_visible = False
        self._input_row_visible = False
        self._console_drawer_visible = False
        self._active_text_prompt_is_console = False
        self._active_text_prompt_uses_input = False
        self.kivy_dark_mode_enabled = self.load_kivy_dark_mode_setting()
        self.kivy_fullscreen_enabled = self.load_kivy_fullscreen_setting()
        self.command_buttons: list[Button] = []
        self.command_buttons_by_command: dict[str, Button] = {}
        self._visible_command_bar_commands: tuple[str, ...] = ()
        self.option_buttons: list[Button] = []
        self._button_font_bindings: dict[Button, list[tuple[str, int]]] = {}
        self._button_font_sync_event = None
        self._button_font_syncing = False
        self._choice_scroll_indicator_active = False
        self.typing_animation_enabled = True
        self.bridge = ClickableGameBridge(self, load_save=load_save)
        self._build_ui()
        self.apply_kivy_fullscreen()
        Window.bind(on_key_down=self._handle_window_key_down)

    def load_kivy_dark_mode_setting(self) -> bool:
        settings_path = Path.cwd() / "saves" / "settings.json"
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.DEFAULT_KIVY_DARK_MODE_ENABLED
        if not isinstance(data, dict):
            return self.DEFAULT_KIVY_DARK_MODE_ENABLED
        return bool(data.get(self.KIVY_DARK_MODE_SETTING_KEY, self.DEFAULT_KIVY_DARK_MODE_ENABLED))

    def load_kivy_fullscreen_setting(self) -> bool:
        settings_path = Path.cwd() / "saves" / "settings.json"
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.DEFAULT_KIVY_FULLSCREEN_ENABLED
        if not isinstance(data, dict):
            return self.DEFAULT_KIVY_FULLSCREEN_ENABLED
        return bool(data.get(self.KIVY_FULLSCREEN_SETTING_KEY, self.DEFAULT_KIVY_FULLSCREEN_ENABLED))

    @property
    def theme(self) -> dict[str, tuple[float, float, float, float]]:
        return self.DARK_THEME if self.kivy_dark_mode_enabled else self.LIGHT_THEME

    def _apply_font(self, widget, role: str) -> None:
        font_name = resolve_kivy_font(role)
        if font_name is None:
            return
        widget.font_name = font_name
        sync_text_size = getattr(widget, "_sync_text_size", None)
        if callable(sync_text_size):
            sync_text_size()
        sync_height = getattr(widget, "_sync_height", None)
        if callable(sync_height):
            sync_height()

    def _build_ui(self) -> None:
        self.header = PanelBox(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(10), dp(4), dp(10), dp(4)],
            spacing=dp(10),
            background_color=(0.13, 0.10, 0.07, 1),
            radius=6,
        )
        self.title_label = Label(
            text="Aethrune",
            color=(0.96, 0.78, 0.28, 1),
            font_size="22sp",
            bold=True,
            size_hint_x=None,
            width=dp(150),
        )
        self._apply_font(self.title_label, "story")
        self.header.add_widget(self.title_label)
        self.status_label = Label(
            text="Click a choice, or type a response below.",
            color=(0.78, 0.70, 0.58, 1),
            font_size="14sp",
            halign="left",
            valign="middle",
        )
        self._apply_font(self.status_label, "ui")
        self.status_label.bind(size=self._sync_status_label)
        self.header.add_widget(self.status_label)

        self.main_body = BoxLayout(orientation="horizontal", spacing=dp(8))
        self.left_column = BoxLayout(orientation="vertical", spacing=dp(6))
        self.main_body.add_widget(self.left_column)

        self.log_shell = PanelBox(
            orientation="vertical",
            padding=[dp(10), dp(8), dp(10), dp(8)],
            spacing=dp(4),
            background_color=(0.08, 0.07, 0.055, 1),
            radius=6,
        )
        self.log_label = ExaminableWrappedLabel(
            text="[color=#8f7d62]Launching...[/color]",
            markup=True,
            color=(0.92, 0.86, 0.74, 1),
            font_size=self.SINGLE_TEXT_WINDOW_FONT_SIZE,
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._apply_font(self.log_label, "story")
        self.log_label.bind(on_ref_press=lambda _label, ref_name: self.show_examine_ref(str(ref_name)))
        self.title_card_label = Label(
            text="",
            markup=True,
            color=(0.92, 0.86, 0.74, 1),
            font_size=self.SINGLE_TEXT_WINDOW_FONT_SIZE,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
        )
        self._apply_font(self.title_card_label, "story")
        self.title_card_label.bind(width=self._sync_title_card_label, texture_size=self._sync_title_card_label)
        self.title_info_panel = PanelBox(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            padding=[dp(18), dp(14), dp(18), dp(14)],
            spacing=dp(10),
            background_color=self.theme["title_info_panel"],
            radius=5,
            opacity=0,
            disabled=True,
        )
        self.title_info_header = Label(
            text="Route Desk",
            color=self.theme["title_info_header"],
            font_size="24sp",
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(38),
        )
        self._apply_font(self.title_info_header, "ui")
        self.title_info_header.bind(size=self._sync_title_info_header, texture_size=self._sync_title_info_header)
        self.title_info_rows = GridLayout(
            cols=2,
            spacing=[dp(12), dp(8)],
            size_hint_y=None,
            height=0,
        )
        self.title_info_rows.bind(
            minimum_height=self.title_info_rows.setter("height"),
            height=self._sync_title_info_panel_height,
        )
        self.title_info_panel.add_widget(self.title_info_header)
        self.title_info_panel.add_widget(self.title_info_rows)
        self._title_info_label_widgets: list[Label] = []
        self._title_info_value_widgets: list[Label] = []
        self.log_scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        self.log_viewport = BoxLayout(orientation="vertical", size_hint_y=None)
        self.log_spacer = Widget()
        self.log_viewport.add_widget(self.log_label)
        self.log_viewport.add_widget(self.log_spacer)
        self.log_scroll.bind(size=self._sync_log_viewport_height)
        self.log_label.bind(height=self._sync_log_viewport_height)
        self.log_scroll.add_widget(self.log_viewport)
        self.log_shell.add_widget(self.title_card_label)
        self.log_shell.add_widget(self.title_info_panel)
        self.log_shell.add_widget(self.log_scroll)
        self.dice_animation_tray = PanelBox(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            padding=[dp(10), dp(6), dp(10), dp(8)],
            background_color=(0.105, 0.085, 0.055, 1),
            radius=5,
            opacity=0,
            disabled=True,
        )
        self.dice_animation_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.86, 0.62, 1),
            font_size="15sp",
            halign="left",
            valign="middle",
            size_hint=(1, 1),
        )
        self._apply_font(self.dice_animation_label, "mono")
        self.dice_animation_label.bind(size=self._sync_dice_animation_label)
        self.dice_animation_tray.add_widget(self.dice_animation_label)
        self.dice_roll_tray = PanelBox(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            padding=[dp(10), dp(6), dp(10), dp(8)],
            spacing=dp(3),
            background_color=(0.105, 0.085, 0.055, 1),
            radius=5,
            opacity=0,
            disabled=True,
        )
        self.dice_roll_header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26),
        )
        self.dice_roll_header.add_widget(Widget())
        self.dice_roll_close_button = Button(
            text="X",
            size_hint_x=None,
            width=dp(28),
            background_normal="",
            background_color=(0.48, 0.36, 0.18, 1),
            color=(1, 0.94, 0.78, 1),
            font_size="12sp",
            bold=True,
        )
        self._apply_font(self.dice_roll_close_button, "ui")
        self.dice_roll_close_button.bind(on_release=lambda *_args: self._clear_dice_roll_tray())
        self.dice_roll_header.add_widget(self.dice_roll_close_button)
        self.dice_roll_panel_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.86, 0.62, 1),
            font_size="16sp",
            halign="left",
            valign="middle",
            size_hint=(1, 1),
        )
        self._apply_font(self.dice_roll_panel_label, "mono")
        self.dice_roll_panel_label.bind(size=self._sync_dice_animation_label)
        self.dice_roll_row = BoxLayout(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
        )
        self.dice_roll_prefix_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.86, 0.62, 1),
            font_size="15sp",
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(26),
        )
        self.dice_roll_core_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.86, 0.62, 1),
            font_size="34sp",
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(58),
        )
        self.dice_roll_suffix_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.86, 0.62, 1),
            font_size="15sp",
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(42),
        )
        for label in (self.dice_roll_prefix_label, self.dice_roll_core_label, self.dice_roll_suffix_label):
            self._apply_font(label, "mono")
            label.bind(size=self._sync_dice_roll_label)
            self.dice_roll_row.add_widget(label)
        self.dice_roll_tray.add_widget(self.dice_roll_header)
        self.dice_roll_tray.add_widget(self.dice_roll_panel_label)
        self.dice_roll_tray.add_widget(self.dice_roll_row)
        self.log_shell.add_widget(self.dice_animation_tray)
        self.left_column.add_widget(self.log_shell)

        self.prompt_label = WrappedLabel(
            text="",
            markup=True,
            color=(0.94, 0.78, 0.36, 1),
            font_size="19sp",
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(42),
        )
        self._apply_font(self.prompt_label, "ui")

        self.options_area = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(142),
            spacing=dp(8),
        )

        self.options_shell = PanelBox(
            orientation="vertical",
            size_hint=(1, 1),
            padding=[dp(6), dp(6), dp(6), dp(6)],
            background_color=(0.11, 0.13, 0.10, 1),
            radius=6,
        )
        self.options_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self.options_scroll.bind(scroll_y=lambda *_args: self._sync_choice_scroll_indicator())
        self.options_grid = GridLayout(
            cols=1,
            spacing=dp(self.OPTION_BUTTON_ROW_GAP),
            size_hint=(1, None),
        )
        self.options_grid.bind(
            minimum_height=self.options_grid.setter("height"),
            height=lambda *_args: self._sync_choice_scroll_indicator(),
        )
        self.options_scroll.add_widget(self.options_grid)
        self.options_shell.add_widget(self.options_scroll)
        self.options_area.add_widget(self.options_shell)
        self.choice_scroll_indicator = Label(
            text="",
            markup=True,
            color=(0.96, 0.78, 0.28, 1),
            font_size="24sp",
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(None, 1),
            width=0,
            opacity=0,
            disabled=True,
        )
        self._apply_font(self.choice_scroll_indicator, "ui")
        self.choice_scroll_indicator.bind(size=self._sync_choice_scroll_indicator_label)
        self.options_area.add_widget(self.choice_scroll_indicator)

        self.examine_shell = PanelBox(
            orientation="vertical",
            size_hint=(1, None),
            height=0,
            padding=[dp(8), dp(6), dp(8), dp(8)],
            spacing=dp(5),
            background_color=self.theme["examine"],
            radius=6,
            opacity=0,
            disabled=True,
        )
        self.examine_header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
            spacing=dp(6),
        )
        self.examine_title_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.78, 0.28, 1),
            font_size="16sp",
            bold=True,
            halign="left",
            valign="middle",
        )
        self._apply_font(self.examine_title_label, "ui")
        self.examine_title_label.bind(size=self._sync_examine_title_label)
        self.examine_close_button = Button(
            text="X",
            size_hint_x=None,
            width=dp(26),
            background_normal="",
            background_color=(0.48, 0.36, 0.18, 1),
            color=(1, 0.94, 0.78, 1),
            font_size="11sp",
            bold=True,
        )
        self._apply_font(self.examine_close_button, "ui")
        self.examine_close_button.bind(on_release=lambda *_args: self.close_examine_panel())
        self.examine_header.add_widget(self.examine_title_label)
        self.examine_header.add_widget(self.examine_close_button)
        self.examine_label = WrappedLabel(
            text="",
            markup=True,
            color=(0.92, 0.86, 0.74, 1),
            font_size="13sp",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._apply_font(self.examine_label, "ui")
        self.examine_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self.examine_scroll.add_widget(self.examine_label)
        self.examine_shell.add_widget(self.examine_header)
        self.examine_shell.add_widget(self.examine_scroll)

        self.combat_panel = PanelBox(
            orientation="vertical",
            size_hint_x=0.4,
            padding=[dp(8), dp(8), dp(8), dp(8)],
            background_color=(0.075, 0.075, 0.085, 1),
            radius=6,
        )
        self.combat_stats_label = ExaminableWrappedLabel(
            text="",
            markup=True,
            color=(0.92, 0.86, 0.74, 1),
            font_size="15sp",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._apply_font(self.combat_stats_label, "mono")
        self.combat_stats_label.bind(on_ref_press=lambda _label, ref_name: self.show_examine_ref(str(ref_name)))
        self.side_command_header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            spacing=dp(6),
        )
        self.side_command_title_label = Label(
            text="",
            markup=True,
            color=(0.96, 0.78, 0.28, 1),
            font_size="18sp",
            bold=True,
            halign="left",
            valign="middle",
        )
        self._apply_font(self.side_command_title_label, "ui")
        self.side_command_title_label.bind(size=self._sync_side_command_title_label)
        self.side_command_close_button = Button(
            text="X",
            size_hint_x=None,
            width=dp(28),
            background_normal="",
            background_color=(0.48, 0.36, 0.18, 1),
            color=(1, 0.94, 0.78, 1),
            font_size="12sp",
            bold=True,
        )
        self._apply_font(self.side_command_close_button, "ui")
        self.side_command_close_button.bind(on_release=lambda *_args: self.close_side_command_panel())
        self.side_command_header.add_widget(self.side_command_title_label)
        self.side_command_header.add_widget(self.side_command_close_button)
        self.native_map_view = NativeMapView()
        self.native_map_view.set_dark_mode(self.kivy_dark_mode_enabled)
        self.command_workspace = NativeCommandWorkspace(self)
        self.combat_stats_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self.combat_stats_scroll.add_widget(self.combat_stats_label)
        self.combat_panel.add_widget(self.side_command_header)
        self.combat_panel.add_widget(self.native_map_view)
        self.combat_panel.add_widget(self.command_workspace)
        self.combat_panel.add_widget(self.combat_stats_scroll)
        self.combat_panel.add_widget(self.dice_roll_tray)
        self.add_widget(self.main_body)

        self.input_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.text_input = TextInput(
            multiline=False,
            hint_text="Type your answer here",
            background_color=(0.96, 0.91, 0.78, 1),
            foreground_color=(0.12, 0.09, 0.06, 1),
            cursor_color=(0.82, 0.56, 0.18, 1),
            padding=[dp(10), dp(9), dp(10), dp(9)],
        )
        self._apply_font(self.text_input, "mono")
        self.text_input.bind(on_text_validate=lambda *_args: self.submit_text())
        self.input_row.add_widget(self.text_input)
        self.send_button = Button(
            text="Send",
            size_hint_x=None,
            width=dp(78),
            background_normal="",
            background_color=(0.36, 0.22, 0.08, 1),
            color=(1, 0.98, 0.94, 1),
            font_size=self.SEND_BUTTON_FONT_SIZE,
            halign="center",
            valign="middle",
        )
        self._apply_font(self.send_button, "ui")
        self._bind_fixed_button_alignment(self.send_button)
        self.send_button.bind(on_release=lambda *_args: self.submit_text())
        self.input_row.add_widget(self.send_button)

        self.commands = GridLayout(
            rows=1,
            spacing=dp(5),
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
        )
        for command in self.COMMANDS:
            button = Button(
                text=self.COMMAND_LABELS.get(command, command.title()),
                background_normal="",
                background_color=(0.48, 0.36, 0.18, 1),
                color=(1, 0.94, 0.78, 1),
                font_size=self.COMMAND_BUTTON_FONT_SIZE,
                halign="center",
                valign="middle",
            )
            self._apply_font(button, "ui")
            self._bind_fixed_button_alignment(button)
            button.bind(on_release=lambda _btn, value=command: self.submit_command(value))
            button._kivy_command_name = command
            self.command_buttons.append(button)
            self.command_buttons_by_command[command] = button
            self.commands.add_widget(button)
        self.add_widget(self.prompt_label)
        self.add_widget(self.options_area)
        self.add_widget(self.commands)
        self._standard_widgets = [
            self.main_body,
            self.prompt_label,
            self.options_area,
            self.commands,
        ]
        self._apply_text_window_mode(side_visible=False)
        self.apply_theme()
        self._sync_command_bar_visibility()
        self._schedule_button_font_sync()

    def _sync_status_label(self, instance: Label, _value) -> None:
        instance.text_size = (instance.width, None)

    def _sync_title_card_label(self, *_args) -> None:
        if not hasattr(self, "title_card_label"):
            return
        self.title_card_label.text_size = (max(1, self.title_card_label.width - dp(12)), None)
        if not self.title_card_label.text or self.title_card_label.opacity <= 0:
            self.title_card_label.height = 0
            return
        self.title_card_label.height = self.title_card_label.texture_size[1] + dp(18)

    def _sync_title_info_header(self, instance: Label, _value=None) -> None:
        instance.text_size = (max(1, instance.width), None)

    def _sync_title_info_row_label(self, instance: Label, _value=None) -> None:
        wrap_width = instance.width
        if getattr(instance, "_title_info_value", False) and wrap_width < dp(160):
            wrap_width = dp(420)
        instance.text_size = (max(1, wrap_width), None)
        instance.texture_update()
        instance.height = max(dp(24), instance.texture_size[1] + dp(4))

    def _sync_title_info_rows(self, *_args) -> None:
        for widget in [*self._title_info_label_widgets, *self._title_info_value_widgets]:
            self._sync_title_info_row_label(widget)
        self._sync_title_info_panel_height()

    def _sync_title_info_panel_height(self, *_args) -> None:
        if not hasattr(self, "title_info_panel"):
            return
        if self.title_info_panel.opacity <= 0:
            self.title_info_panel.height = 0
            return
        left, top, right, bottom = self.title_info_panel.padding
        del left, right
        self.title_info_panel.height = (
            top
            + self.title_info_header.height
            + self.title_info_panel.spacing
            + self.title_info_rows.height
            + bottom
        )
        self._sync_log_viewport_height()

    def _title_menu_latest_save_value(self, save_summary: str, save_detail: str) -> str:
        if save_summary.strip().lower().startswith("no save"):
            return "None yet"
        detail_lines = [line.strip() for line in save_detail.splitlines() if line.strip()]
        latest_save = " ".join(detail_lines[:2]) if detail_lines else save_detail.strip()
        return re.sub(r"^Latest:\s*", "", latest_save).strip() or "Unknown"

    def _title_menu_info_rows(
        self,
        *,
        campaign_summary: str,
        save_summary: str,
        save_detail: str,
        audio_summary: str,
        presentation_summary: str,
    ) -> list[tuple[str, str]]:
        return [
            ("Campaign:", campaign_summary),
            ("Saves:", save_summary),
            ("Latest Save:", self._title_menu_latest_save_value(save_summary, save_detail)),
            ("Audio:", audio_summary),
            ("Table Settings:", presentation_summary),
        ]

    def _set_title_info_panel(self, rows: list[tuple[str, str]] | None) -> None:
        if not hasattr(self, "title_info_panel"):
            return
        self.title_info_rows.clear_widgets()
        self._title_info_label_widgets = []
        self._title_info_value_widgets = []
        if not rows:
            self.title_info_panel.opacity = 0
            self.title_info_panel.disabled = True
            self.title_info_panel.height = 0
            self._sync_log_viewport_height()
            return

        theme = self.theme
        label_width = dp(136)
        for label, value in rows:
            label_widget = Label(
                text=label,
                color=theme["title_info_label"],
                font_size="15sp",
                bold=True,
                halign="right",
                valign="top",
                size_hint=(None, None),
                width=label_width,
            )
            value_widget = Label(
                text=value,
                color=theme["title_info_value"],
                font_size="15sp",
                halign="left",
                valign="top",
                size_hint=(1, None),
                width=dp(420),
            )
            value_widget._title_info_value = True
            for widget in (label_widget, value_widget):
                self._apply_font(widget, "ui")
                widget.bind(width=self._sync_title_info_row_label, texture_size=self._sync_title_info_row_label)
                self._sync_title_info_row_label(widget)
            self.title_info_rows.add_widget(label_widget)
            self.title_info_rows.add_widget(value_widget)
            self._title_info_label_widgets.append(label_widget)
            self._title_info_value_widgets.append(value_widget)

        self.title_info_panel.opacity = 1
        self.title_info_panel.disabled = False
        self._sync_title_info_panel_height()
        Clock.schedule_once(lambda _dt: self._sync_title_info_rows(), 0)

    def _set_title_card_markup(self, markup: str) -> None:
        if not hasattr(self, "title_card_label"):
            return
        self.title_card_label.text = markup
        self.title_card_label.opacity = 1 if markup else 0
        self.title_card_label.disabled = not bool(markup)
        if not markup:
            self._set_title_info_panel(None)
        self._sync_title_card_label()
        self._sync_log_viewport_height()

    def _clear_title_menu_shell(self) -> None:
        self._title_menu_active = False
        self._title_menu_transition_active = False
        self._main_title_menu_active = False
        self._set_title_card_markup("")
        self._log_lines = []
        self._render_log()

    def _sync_side_command_title_label(self, instance: Label, _value) -> None:
        instance.text_size = (instance.width, None)

    def _sync_examine_title_label(self, instance: Label, _value) -> None:
        instance.text_size = (instance.width, None)

    def _sync_dice_animation_label(self, instance: Label, _value=None) -> None:
        instance.text_size = (
            max(1, instance.width - dp(8)),
            max(1, instance.height - dp(4)),
        )

    def _sync_dice_roll_label(self, instance: Label, _value=None) -> None:
        instance.text_size = (
            max(1, instance.width - dp(6)),
            max(1, instance.height - dp(2)),
        )

    def _sync_choice_scroll_indicator_label(self, instance: Label, _value=None) -> None:
        instance.text_size = (
            max(1, instance.width),
            max(1, instance.height),
        )

    def _fit_label_to_texture_width(self, instance: Label, maximum_width: float) -> None:
        instance.texture_update()
        instance.width = min(maximum_width, max(dp(1), instance.texture_size[0] + dp(6)))

    def _set_side_command_header_visible(self, visible: bool) -> None:
        self.side_command_header.height = dp(34) if visible else 0
        self.side_command_header.opacity = 1 if visible else 0
        self.side_command_header.disabled = not visible

    def _set_prompt_controls_docked_to_left(self, docked: bool) -> None:
        controls = (self.prompt_label, self.options_area, self.commands)
        if docked:
            for widget in controls:
                if widget.parent is self:
                    self.remove_widget(widget)
                elif widget.parent is not None and widget.parent is not self.left_column:
                    widget.parent.remove_widget(widget)
            for widget in controls:
                if widget.parent is not self.left_column:
                    self.left_column.add_widget(widget)
            return

        for widget in controls:
            if widget.parent is self.left_column:
                self.left_column.remove_widget(widget)
            elif widget.parent is not None and widget.parent is not self:
                widget.parent.remove_widget(widget)
        for widget in controls:
            if widget.parent is not self:
                self.add_widget(widget)

    def _set_app_header_visible(self, visible: bool) -> None:
        self.header.height = dp(44) if visible else 0
        self.header.opacity = 1 if visible else 0
        self.header.disabled = not visible

    def _set_input_row_visible(self, visible: bool, *, animate: bool = False) -> None:
        self._input_row_visible = bool(visible)
        Animation.cancel_all(self.input_row, "height", "opacity")
        if visible:
            if self.input_row.parent is None and self.commands.parent is self:
                self.remove_widget(self.commands)
                if self.input_row.height <= 0:
                    self.input_row.height = 0
                    self.input_row.opacity = 0
                self.add_widget(self.input_row)
                self.add_widget(self.commands)
            elif self.input_row.parent is None:
                if self.input_row.height <= 0:
                    self.input_row.height = 0
                    self.input_row.opacity = 0
                self.add_widget(self.input_row)
            self.input_row.disabled = False
            self.text_input.disabled = False
            self.send_button.disabled = False
            target_height = dp(42)
            if not animate:
                self.input_row.height = target_height
                self.input_row.opacity = 1
                return
            Animation(
                height=target_height,
                opacity=1,
                duration=self.COMMAND_BAR_ANIMATION_SECONDS,
                t="out_quad",
            ).start(self.input_row)
            return

        if self.input_row.parent is self:
            if animate:
                self.input_row.disabled = True
                animation = Animation(
                    height=0,
                    opacity=0,
                    duration=self.COMMAND_BAR_ANIMATION_SECONDS,
                    t="in_quad",
                )
                animation.bind(on_complete=lambda *_args: self._finish_input_row_hide())
                animation.start(self.input_row)
                return
            self.remove_widget(self.input_row)
        self.input_row.height = 0
        self.input_row.opacity = 0
        self.input_row.disabled = True

    def _finish_input_row_hide(self) -> None:
        if self._input_row_visible:
            return
        if self.input_row.parent is self:
            self.remove_widget(self.input_row)
        self.input_row.height = 0
        self.input_row.opacity = 0
        self.input_row.disabled = True

    def _prompt_is_console_drawer(self, prompt: str) -> bool:
        return plain_combat_status_text(visible_markup_text(str(prompt))).strip().lower().startswith("console>")

    def toggle_console_drawer(self) -> None:
        self._set_command_bar_visible(False, animate=True)
        if self._console_drawer_visible:
            self._console_drawer_visible = False
            self._active_text_prompt_is_console = False
            self._active_text_prompt_uses_input = False
            self._set_input_row_visible(False, animate=True)
            self.submit_direct("back")
            return
        self.submit_direct("~")

    def _enter_save_browser(self, root: PanelBox) -> None:
        self._save_browser_active = True
        self._save_browser_root = root
        self._set_input_row_visible(False)
        self.clear_widgets()
        self.add_widget(root)

    def hide_save_browser(self) -> None:
        if not self._save_browser_active:
            return
        self._save_browser_active = False
        self._save_browser_root = None
        self._save_browser_detail_panel = None
        self._save_browser_detail_label = None
        self._save_browser_detail_scroll = None
        self.clear_widgets()
        for widget in self._standard_widgets:
            if widget.parent is not self:
                self.add_widget(widget)
        self._set_input_row_visible(
            self.bridge.waiting_for_input and self._active_text_prompt_uses_input,
            animate=False,
        )
        self.apply_theme()

    def _sync_save_browser_button_text_size(self, button: Button, *_args) -> None:
        button.text_size = (
            max(1, button.width - dp(28)),
            max(1, button.height - dp(12)),
        )

    def _save_browser_bar_markup(self, index: int | None, title: str, meta: str = "") -> str:
        prefix = f"[b][color=#facc15]{index:02d}[/color][/b] " if index is not None else ""
        meta_markup = f"\n[size=15sp][color=#b9ad91]{escape_kivy_markup(meta)}[/color][/size]" if meta else ""
        return f"{prefix}[b]{escape_kivy_markup(title)}[/b]{meta_markup}"

    def _build_save_browser_button(
        self,
        *,
        title: str,
        meta: str = "",
        value: str,
        index: int | None = None,
        examine_entry: dict[str, str] | None = None,
        role: str = "choice",
        height: float | None = None,
    ) -> ExaminableButton:
        theme = self.theme
        if role == "back":
            background = theme["choice_back_bg"]
            text_color = theme["choice_back_text"]
        elif role == "delete":
            background = theme["choice_end_turn_bg"]
            text_color = theme["choice_end_turn_text"]
        else:
            background = theme["choice_bg"]
            text_color = theme["choice_text"]
        button = ExaminableButton(
            text=self._save_browser_bar_markup(index, title, meta),
            markup=True,
            examine_callback=(
                (lambda data=examine_entry: self.show_save_browser_detail(data))
                if examine_entry is not None
                else None
            ),
            background_normal="",
            background_color=background,
            color=text_color,
            font_size="17sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=height if height is not None else dp(78),
        )
        button._kivy_fixed_font_size = True
        self._apply_font(button, "ui")
        button.bind(size=lambda instance, _value: self._sync_save_browser_button_text_size(instance))
        self._sync_save_browser_button_text_size(button)
        button.bind(on_release=lambda _btn, response=value: self.submit_direct(response))
        return button

    def _save_browser_detail_markup(self, entry: dict[str, str]) -> str:
        title = str(entry.get("detail_title") or entry.get("title") or "Save File")
        detail = str(entry.get("detail") or "").strip()
        lines = [
            f"[size=21sp][b][color=#facc15]{escape_kivy_markup(title)}[/color][/b][/size]",
        ]
        if detail:
            lines.append("")
            lines.extend(f"[size=16sp]{escape_kivy_markup(line)}[/size]" for line in detail.splitlines())
        return "\n".join(lines)

    def show_save_browser_detail(self, entry: dict[str, str] | None) -> None:
        if not entry or self._save_browser_detail_panel is None or self._save_browser_detail_label is None:
            return
        self._save_browser_detail_panel.height = min(dp(300), max(dp(190), self.height * 0.38))
        self._save_browser_detail_panel.opacity = 1
        self._save_browser_detail_panel.disabled = False
        self._save_browser_detail_label.text = self._save_browser_detail_markup(entry)
        self._save_browser_detail_label._sync_text_size()
        self._save_browser_detail_label._sync_height()
        if self._save_browser_detail_scroll is not None:
            Clock.schedule_once(lambda _dt: setattr(self._save_browser_detail_scroll, "scroll_y", 1), 0)

    def close_save_browser_detail(self) -> None:
        if self._save_browser_detail_panel is None or self._save_browser_detail_label is None:
            return
        self._save_browser_detail_panel.height = 0
        self._save_browser_detail_panel.opacity = 0
        self._save_browser_detail_panel.disabled = True
        self._save_browser_detail_label.text = ""

    def _build_save_browser_root(self, title: str) -> tuple[PanelBox, GridLayout]:
        theme = self.theme
        root = PanelBox(
            orientation="vertical",
            padding=[dp(10), dp(8), dp(10), dp(10)],
            spacing=dp(7),
            background_color=theme["panel"],
            radius=0,
        )
        header = Label(
            text=f"[b]{escape_kivy_markup(title)}[/b]",
            markup=True,
            color=theme["title"],
            font_size="24sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(38),
        )
        self._apply_font(header, "ui")
        header.bind(size=lambda instance, _value: setattr(instance, "text_size", (instance.width, instance.height)))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(7))
        grid = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)
        root.add_widget(scroll)

        detail_panel = PanelBox(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            padding=[dp(8), dp(6), dp(8), dp(8)],
            spacing=dp(5),
            background_color=theme["combat"],
            radius=6,
        )
        detail_header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
            spacing=dp(6),
        )
        detail_title = Label(
            text="Details",
            color=theme["title"],
            font_size="17sp",
            bold=True,
            halign="left",
            valign="middle",
        )
        self._apply_font(detail_title, "ui")
        detail_close = Button(
            text="X",
            size_hint_x=None,
            width=dp(32),
            background_normal="",
            background_color=theme["command_bg"],
            color=theme["command_text"],
            font_size="14sp",
            bold=True,
        )
        self._apply_font(detail_close, "ui")
        detail_close.bind(on_release=lambda *_args: self.close_save_browser_detail())
        detail_header.add_widget(detail_title)
        detail_header.add_widget(detail_close)
        detail_label = WrappedLabel(
            text="",
            markup=True,
            color=theme["text"],
            font_size="16sp",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._apply_font(detail_label, "ui")
        detail_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        detail_scroll.add_widget(detail_label)
        detail_panel.add_widget(detail_header)
        detail_panel.add_widget(detail_scroll)
        root.add_widget(detail_panel)
        self._save_browser_detail_panel = detail_panel
        self._save_browser_detail_label = detail_label
        self._save_browser_detail_scroll = detail_scroll
        return root, grid

    def show_save_browser(self, title: str, entries: list[dict[str, str]]) -> None:
        self.skip_current_animation()
        self.close_examine_panel()
        self._clear_title_menu_shell()
        root, grid = self._build_save_browser_root(title)
        for index, entry in enumerate(entries, start=1):
            grid.add_widget(
                self._build_save_browser_button(
                    title=str(entry.get("title") or f"Save {index}"),
                    meta=str(entry.get("meta") or ""),
                    value=str(index),
                    index=index,
                    examine_entry=entry,
                )
            )
        root.add_widget(
            self._build_save_browser_button(
                title="Back",
                value="back",
                role="back",
                height=dp(52),
            )
        )
        self._enter_save_browser(root)

    def show_save_action_browser(self, entry: dict[str, str]) -> None:
        self.skip_current_animation()
        self._clear_title_menu_shell()
        root, grid = self._build_save_browser_root(str(entry.get("title") or "Save File"))
        grid.add_widget(
            self._build_save_browser_button(
                title="Load This Save",
                value="load",
                role="choice",
            )
        )
        grid.add_widget(
            self._build_save_browser_button(
                title="Delete This Save",
                value="delete",
                role="delete",
            )
        )
        root.add_widget(
            self._build_save_browser_button(
                title="Back",
                value="back",
                role="back",
                height=dp(52),
            )
        )
        self._enter_save_browser(root)

    def _active_scaled_buttons(self) -> list[Button]:
        return [
            button
            for button in self.option_buttons
            if button.parent is not None
            and button.width > 0
            and button.height > 0
            and not getattr(button, "_kivy_fixed_font_size", False)
        ]

    def _button_inner_size(self, button: Button) -> tuple[float, float]:
        width = max(1.0, float(button.width) - dp(self.BUTTON_TEXT_HORIZONTAL_PADDING))
        height = max(1.0, float(button.height) - dp(self.BUTTON_TEXT_VERTICAL_PADDING))
        return (width, height)

    def _sync_button_text_size(self, button: Button) -> None:
        width, height = self._button_inner_size(button)
        button.text_size = (width, height)

    def _bind_fixed_button_alignment(self, button: Button, *, halign: str = "center") -> None:
        button.halign = halign
        button.valign = "middle"
        self._sync_button_text_size(button)
        button.bind(size=lambda instance, _value: self._sync_button_text_size(instance))

    def _bind_button_font_scaling(self, button: Button) -> None:
        if button in self._button_font_bindings:
            return
        bindings: list[tuple[str, int]] = []
        for property_name in ("size", "text"):
            uid = button.fbind(property_name, self._schedule_button_font_sync)
            if uid:
                bindings.append((property_name, uid))
        self._button_font_bindings[button] = bindings
        self._sync_button_text_size(button)
        self._schedule_button_font_sync()

    def _unbind_button_font_scaling(self, buttons: list[Button]) -> None:
        for button in buttons:
            for property_name, uid in self._button_font_bindings.pop(button, []):
                button.unbind_uid(property_name, uid)

    def _schedule_button_font_sync(self, *_args) -> None:
        if self._button_font_syncing or self._button_font_sync_event is not None:
            return
        self._button_font_sync_event = Clock.schedule_once(self._sync_button_font_sizes, 0)

    def _sync_command_bar_visibility(self) -> None:
        self._set_command_bar_visible(self._command_bar_visible, animate=False)

    def _character_exists_for_commands(self) -> bool:
        game = self.active_game()
        state = getattr(game, "state", None) if game is not None else None
        return bool(state is not None and getattr(state, "player", None) is not None)

    def _command_bar_commands_for_context(self) -> tuple[str, ...]:
        return tuple(self.COMMANDS)

    def _command_unavailable_reason(self, command: str) -> str:
        normalized = " ".join(str(command).strip().lower().split())
        game = self.active_game()
        state = getattr(game, "state", None) if game is not None else None
        in_combat = self.combat_active()
        is_camp_talk = bool(
            re.fullmatch(r"(?:camp talk|talk companion|talk to companion)(?: \d+)?", normalized)
        )
        if normalized in {"save/load", "save load", "saveload", "load", "settings", "quit"}:
            return ""
        if is_camp_talk:
            if state is None:
                return "There is no active adventure yet, so camp is not available."
            if in_combat:
                return "You cannot head to camp during combat."
            return ""
        if state is None:
            no_state_reasons = {
                "map": "There is no active map yet.",
                "journal": "There is no active journal yet.",
                "inventory": "There is no shared inventory yet.",
                "gear": "There is no active party gear to manage yet.",
                "camp": "There is no active adventure yet, so camp is not available.",
                "save": "There is no active game to save.",
            }
            return no_state_reasons.get(normalized, "Start or load an adventure before using that command.")
        if normalized == "map" and in_combat:
            return "Maps are unavailable during combat."
        if normalized == "gear" and in_combat:
            return "You cannot reorganize equipment in the middle of combat."
        if normalized == "camp":
            if in_combat:
                return "You cannot head to camp during combat."
            if state is None:
                return "There is no active adventure yet, so camp is not available."
            return ""
        return ""

    def _apply_command_button_theme(self, button: Button) -> None:
        theme = self.theme
        unavailable = bool(getattr(button, "_kivy_command_unavailable_reason", ""))
        command_name = str(getattr(button, "_kivy_command_name", "")).lower()
        if unavailable:
            button.background_color = theme["command_disabled_bg"]
            button.color = theme["command_disabled_text"]
        elif command_name == "quit":
            button.background_color = theme["choice_end_turn_bg"]
            button.color = theme["choice_end_turn_text"]
        else:
            button.background_color = theme["command_bg"]
            button.color = theme["command_text"]
        button.opacity = 0.72 if unavailable else 1.0
        button.disabled = False

    def _sync_command_button_states(self) -> None:
        for command, button in self.command_buttons_by_command.items():
            button._kivy_command_unavailable_reason = self._command_unavailable_reason(command)
            self._apply_command_button_theme(button)

    def _sync_command_bar_buttons(self) -> None:
        commands = self._command_bar_commands_for_context()
        if commands != self._visible_command_bar_commands:
            self.commands.clear_widgets()
            for command in commands:
                button = self.command_buttons_by_command.get(command)
                if button is not None:
                    self.commands.add_widget(button)
            self._visible_command_bar_commands = commands
        self._sync_command_button_states()

    def _set_command_bar_visible(self, visible: bool, *, animate: bool) -> None:
        self._command_bar_visible = visible
        if not hasattr(self, "commands"):
            return

        self._sync_command_bar_buttons()
        target_height = dp(self.COMMAND_BAR_HEIGHT) if visible else 0
        target_opacity = 1 if visible else 0
        Animation.cancel_all(self.commands, "height", "opacity")
        if visible:
            self.commands.disabled = False

        if not animate:
            self.commands.height = target_height
            self.commands.opacity = target_opacity
            self.commands.disabled = not visible
            return

        transition = "out_quad" if visible else "in_quad"
        animation = Animation(
            height=target_height,
            opacity=target_opacity,
            duration=self.COMMAND_BAR_ANIMATION_SECONDS,
            t=transition,
        )
        animation.bind(on_complete=lambda *_args, expected=visible: self._finish_command_bar_animation(expected))
        animation.start(self.commands)

    def _finish_command_bar_animation(self, expected_visible: bool) -> None:
        if self._command_bar_visible != expected_visible:
            return
        self.commands.height = dp(self.COMMAND_BAR_HEIGHT) if expected_visible else 0
        self.commands.opacity = 1 if expected_visible else 0
        self.commands.disabled = not expected_visible

    def toggle_command_bar(self) -> None:
        self._set_command_bar_visible(not self._command_bar_visible, animate=True)

    def _button_font_fits(self, button: Button, font_size: float) -> bool:
        available_width, available_height = self._button_inner_size(button)
        original_font_size = button.font_size
        original_text_size = button.text_size
        button.font_size = font_size
        button.text_size = (available_width, None)
        button.texture_update()
        texture_width, texture_height = button.texture_size
        button.font_size = original_font_size
        button.text_size = original_text_size
        button.texture_update()
        return texture_width <= available_width + 1 and texture_height <= available_height + 1

    def _sync_button_font_sizes(self, _dt=None) -> None:
        self._button_font_sync_event = None
        buttons = self._active_scaled_buttons()
        if not buttons:
            return

        self._button_font_syncing = True
        try:
            low = sp(self.BUTTON_FONT_MIN_SP)
            high = sp(self.BUTTON_FONT_MAX_SP)
            for _step in range(8):
                midpoint = (low + high) / 2
                if all(self._button_font_fits(button, midpoint) for button in buttons):
                    low = midpoint
                else:
                    high = midpoint
            chosen_size = low
            for button in buttons:
                button.font_size = chosen_size
                self._sync_button_text_size(button)
                button.texture_update()
        finally:
            self._button_font_syncing = False

    def set_kivy_dark_mode_enabled(self, enabled: bool) -> None:
        self.kivy_dark_mode_enabled = bool(enabled)
        self.apply_theme()

    def set_kivy_fullscreen_enabled(self, enabled: bool) -> None:
        self.kivy_fullscreen_enabled = bool(enabled)
        self.apply_kivy_fullscreen()

    def _set_active_game_fullscreen_preference(self, enabled: bool) -> bool:
        game = self.active_game()
        if game is None:
            return False
        game._kivy_fullscreen_preference = bool(enabled)
        game.persist_settings()
        return True

    def persist_kivy_fullscreen_setting(self) -> None:
        if self._set_active_game_fullscreen_preference(self.kivy_fullscreen_enabled):
            return
        settings_path = Path.cwd() / "saves" / "settings.json"
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        data[self.KIVY_FULLSCREEN_SETTING_KEY] = self.kivy_fullscreen_enabled
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def toggle_kivy_fullscreen_from_shortcut(self) -> None:
        self.set_kivy_fullscreen_enabled(not self.kivy_fullscreen_enabled)
        self.persist_kivy_fullscreen_setting()

    def is_fullscreen_shortcut(self, key, scancode, codepoint) -> bool:
        if key in {self.F11_KEY_CODE, self.F11_FALLBACK_KEY_CODE}:
            return True
        if scancode in self.F11_SCANCODES:
            return True
        return str(codepoint).strip().lower() == "f11"

    def is_escape_key(self, key, scancode, codepoint) -> bool:
        if key == 27 or scancode == 1:
            return True
        normalized = str(codepoint).strip().lower()
        return normalized in {"\x1b", "esc", "escape"}

    def is_console_menu_key(self, key, scancode, codepoint) -> bool:
        del key, scancode
        return str(codepoint).strip() in {"`", "~"}

    def apply_kivy_fullscreen(self) -> None:
        try:
            Window.fullscreen = "auto" if self.kivy_fullscreen_enabled else False
        except Exception:
            pass

    def apply_theme(self) -> None:
        theme = self.theme
        try:
            Window.clearcolor = theme["window"]
        except Exception:
            pass
        for panel, key in (
            (self.header, "header"),
            (self.log_shell, "title_panel" if self._title_menu_active else "panel"),
            (self.dice_animation_tray, "dice_tray"),
            (self.dice_roll_tray, "dice_tray"),
            (self.options_shell, "title_options" if self._title_menu_active else "options"),
            (self.combat_panel, "combat"),
            (self.examine_shell, "examine"),
        ):
            panel.set_background_color(theme[key])
        self.title_label.color = theme["title"]
        self.status_label.color = theme["status"]
        self.log_label.color = theme["text"]
        if hasattr(self, "title_info_panel"):
            self.title_info_panel.set_background_color(theme["title_info_panel"])
            self.title_info_header.color = theme["title_info_header"]
            for label in self._title_info_label_widgets:
                label.color = theme["title_info_label"]
            for label in self._title_info_value_widgets:
                label.color = theme["title_info_value"]
        self.dice_animation_label.color = theme["dice_tray_text"]
        for label in (
            self.dice_roll_panel_label,
            self.dice_roll_prefix_label,
            self.dice_roll_core_label,
            self.dice_roll_suffix_label,
        ):
            label.color = theme["dice_tray_text"]
        self.prompt_label.color = theme["prompt"]
        if hasattr(self, "choice_scroll_indicator"):
            self.choice_scroll_indicator.color = theme["prompt"]
        self.combat_stats_label.color = theme["text"]
        self.side_command_title_label.color = theme["title"]
        self.side_command_close_button.background_color = theme["command_bg"]
        self.side_command_close_button.color = theme["command_text"]
        self.dice_roll_close_button.background_color = theme["command_bg"]
        self.dice_roll_close_button.color = theme["command_text"]
        self.examine_title_label.color = theme["title"]
        self.examine_label.color = theme["text"]
        self.examine_close_button.background_color = theme["command_bg"]
        self.examine_close_button.color = theme["command_text"]
        self.native_map_view.set_dark_mode(self.kivy_dark_mode_enabled)
        self.text_input.background_color = theme["input_bg"]
        self.text_input.foreground_color = theme["input_text"]
        self.text_input.cursor_color = theme["cursor"]
        self.send_button.background_color = theme["send_bg"]
        self.send_button.color = theme["send_text"]
        for button in self.command_buttons:
            self._apply_command_button_theme(button)
        for button in self.option_buttons:
            role = getattr(button, "_kivy_choice_role", "choice")
            if role == "title_primary":
                button.background_color = theme["title_choice_primary_bg"]
                button.color = theme["title_choice_primary_text"]
            elif role == "title_utility":
                button.background_color = theme["title_choice_utility_bg"]
                button.color = theme["title_choice_text"]
            elif role == "title_disabled":
                button.background_color = theme["title_choice_disabled_bg"]
                button.color = theme["title_choice_disabled_text"]
            elif role == "title_back":
                button.background_color = theme["title_choice_back_bg"]
                button.color = theme["title_choice_back_text"]
            elif role == "title_quit":
                button.background_color = theme["title_choice_quit_bg"]
                button.color = theme["title_choice_primary_text"]
            elif role == "title_choice":
                button.background_color = theme["title_choice_bg"]
                button.color = theme["title_choice_text"]
            elif role == "end_turn":
                button.background_color = theme["choice_end_turn_bg"]
                button.color = theme["choice_end_turn_text"]
            elif role == "back":
                button.background_color = theme["choice_back_bg"]
                button.color = theme["choice_back_text"]
            elif role == "combat_group":
                button.background_color = theme["choice_group_bg"]
                button.color = theme["choice_group_text"]
            else:
                button.background_color = theme["choice_bg"]
                button.color = theme["choice_text"]

    def _sync_log_viewport_height(self, *_args) -> None:
        self.log_viewport.height = max(self.log_scroll.height, self.log_label.height)

    def active_game(self) -> "ClickableTextDnDGame | None":
        return self.bridge.game

    def show_native_overworld_map(self, blueprint, state, *, title: str, done_event: Event | None = None) -> None:
        if not self.side_panel_allowed() or self.combat_active():
            self._complete_log_append(done_event)
            return
        self._set_prompt_controls_docked_to_left(False)
        self.update_combat_layout()
        self._side_panel_mode = "command"
        self._side_command_title = title
        self._hide_command_workspace()
        self._set_side_command_header_visible(True)
        self.side_command_title_label.text = escape_kivy_markup(title)
        self.native_map_view.show_overworld(title=title, blueprint=blueprint, state=state)
        self._complete_log_append(done_event)

    def show_native_dungeon_map(self, dungeon, state, *, title: str, done_event: Event | None = None) -> None:
        if not self.side_panel_allowed() or self.combat_active():
            self._complete_log_append(done_event)
            return
        self._set_prompt_controls_docked_to_left(False)
        self.update_combat_layout()
        self._side_panel_mode = "command"
        self._side_command_title = title
        self._hide_command_workspace()
        self._set_side_command_header_visible(True)
        self.side_command_title_label.text = escape_kivy_markup(title)
        self.native_map_view.show_dungeon(title=title, dungeon=dungeon, state=state)
        self._complete_log_append(done_event)

    def _show_command_workspace(self) -> None:
        self.combat_stats_scroll.size_hint_y = None
        self.combat_stats_scroll.height = 0
        self.combat_stats_scroll.opacity = 0
        self.combat_stats_scroll.disabled = True
        self.command_workspace.size_hint_y = 1
        self.command_workspace.height = 0
        self.command_workspace.show()

    def _hide_command_workspace(self) -> None:
        if not hasattr(self, "command_workspace"):
            return
        self.command_workspace.hide()
        self.command_workspace.size_hint_y = None
        self.command_workspace.height = 0
        self.combat_stats_scroll.size_hint_y = 1
        self.combat_stats_scroll.opacity = 1
        self.combat_stats_scroll.disabled = False

    def show_native_command_pane(self, command: str, *, done_event: Event | None = None) -> None:
        if not self.side_panel_allowed() or self.combat_active():
            self._complete_log_append(done_event)
            return
        normalized = " ".join(str(command).strip().lower().split())
        title = {
            "journal": "Journal",
            "map": "Map",
            "maps": "Map",
            "map menu": "Map",
            "inventory": "Inventory",
            "backpack": "Inventory",
            "bag": "Inventory",
            "camp": "Camp",
            "equipment": "Gear",
            "gear": "Gear",
        }.get(normalized, normalized.title() or "Command")
        self._side_panel_mode = "native_command"
        self._side_command_title = title
        self._set_prompt_controls_docked_to_left(True)
        self.update_combat_layout()
        self.native_map_view.hide_map()
        self._set_side_command_header_visible(False)
        self.side_command_title_label.text = ""
        self._clear_combat_resource_animation()
        self._show_command_workspace()
        self.command_workspace.render_command(normalized)
        self._complete_log_append(done_event)

    def set_active_combat_actor(self, name: str) -> None:
        self._active_combat_actor_name = str(name or "")
        self._initiative_turn_arrow_phase = 0
        if self._active_combat_actor_name and self.combat_active():
            self._start_initiative_turn_arrow_animation()
        else:
            self._stop_initiative_turn_arrow_animation()
        self.refresh_combat_panel()
        self.refresh_active_initiative_tray()

    def combat_active(self) -> bool:
        game = self.active_game()
        return bool(game is not None and getattr(game, "_in_combat", False))

    def side_panel_allowed(self) -> bool:
        game = self.active_game()
        return bool(
            game is not None
            and getattr(game, "state", None) is not None
            and not getattr(game, "_at_title_screen", False)
        )

    def _right_panel_width_fraction(self) -> float:
        if self._side_panel_mode == "native_command":
            return self.NATIVE_COMMAND_PANEL_WIDTH_FRACTION
        return self.RIGHT_PANEL_WIDTH_FRACTION

    def _apply_right_panel_width(self, fraction: float | None = None) -> None:
        fraction = self._right_panel_width_fraction() if fraction is None else fraction
        fraction = max(0.1, min(0.9, float(fraction)))
        self.left_column.size_hint_x = 1.0 - fraction
        self.combat_panel.size_hint_x = fraction

    def update_combat_layout(self) -> None:
        side_visible = self.side_panel_allowed()
        combat_active = self.combat_active()
        was_combat_active = self._combat_mode_enabled
        if self._side_panel_mode != "native_command":
            self._set_prompt_controls_docked_to_left(False)
        if side_visible == self._side_panel_visible and combat_active == self._combat_mode_enabled:
            self._apply_text_window_mode(side_visible=side_visible)
            if side_visible:
                self._apply_right_panel_width()
            if side_visible:
                self.refresh_combat_panel()
            return

        self._side_panel_visible = side_visible
        self._combat_mode_enabled = combat_active
        if was_combat_active and not combat_active:
            self._clear_dice_tray()
        self._apply_text_window_mode(side_visible=side_visible)
        if side_visible:
            self._apply_right_panel_width()
            if self.combat_panel.parent is None:
                self.main_body.add_widget(self.combat_panel)
            self.status_label.text = (
                "Combat: story on the left, stats on the right, choices below."
                if combat_active
                else "Story on the left. Party, maps, and command screens on the right."
            )
            self.refresh_combat_panel()
            return

        if self.combat_panel.parent is self.main_body:
            self.main_body.remove_widget(self.combat_panel)
        self._set_prompt_controls_docked_to_left(False)
        self.left_column.size_hint_x = 1
        self._active_combat_actor_name = ""
        self._stop_initiative_turn_arrow_animation()
        self._clear_combat_resource_animation()
        self._clear_defeated_enemy_fades()
        self.native_map_view.hide_map()
        self._hide_command_workspace()
        self.combat_stats_label.text = ""
        self._clear_dice_tray()
        self._side_panel_mode = "default"
        self._side_command_lines = []
        self._side_command_title = ""
        self._set_side_command_header_visible(False)

    def _apply_text_window_mode(self, *, side_visible: bool) -> None:
        self.log_label.font_size = (
            self.SPLIT_TEXT_WINDOW_FONT_SIZE if side_visible else self.SINGLE_TEXT_WINDOW_FONT_SIZE
        )
        self.log_label.halign = "left"
        self.log_label._sync_text_size()
        self.log_label._sync_height()
        if not self._dice_tray_active:
            self._set_dice_tray_reserved(False)
        self._sync_log_viewport_height()

    def refresh_combat_panel(self) -> None:
        if not self.side_panel_allowed():
            self._clear_combat_resource_animation()
            self._clear_defeated_enemy_fades()
            self.native_map_view.hide_map()
            self._set_side_command_header_visible(False)
            return
        if not self.combat_active():
            self._clear_combat_resource_animation()
            self._clear_defeated_enemy_fades()
            if self._side_panel_mode == "command":
                self._render_side_command()
            elif self._side_panel_mode == "native_command":
                self._apply_right_panel_width()
                self._show_command_workspace()
                self.command_workspace.refresh_active()
            else:
                self._render_party_stats_panel()
            return
        self._sync_combat_resource_targets()
        self._render_combat_panel()

    def restore_default_side_panel(self) -> None:
        if not self.side_panel_allowed() or self.combat_active():
            return
        if self._side_panel_mode != "default":
            self._side_panel_mode = "default"
            self._side_command_title = ""
            self._side_command_lines = []
        self._set_prompt_controls_docked_to_left(False)
        self.native_map_view.hide_map()
        self._hide_command_workspace()
        self._set_side_command_header_visible(False)
        self.refresh_combat_panel()

    def close_side_command_panel(self) -> None:
        self.skip_current_animation()
        self.bridge.close_side_command()
        self._side_panel_mode = "default"
        self._side_command_title = ""
        self._side_command_lines = []
        self._set_prompt_controls_docked_to_left(False)
        self.native_map_view.hide_map()
        self._hide_command_workspace()
        self._set_side_command_header_visible(False)
        if not self.side_panel_allowed():
            return
        if self.combat_active():
            self._render_combat_panel()
        else:
            self._render_party_stats_panel()

    def start_camp_companion_talk(self, companion_index: int) -> None:
        self.close_side_command_panel()
        self.submit_command(f"camp talk {int(companion_index) + 1}")

    def _examine_entry_markup(self, entry: ExamineEntry) -> str:
        lines = [
            f"[size=18sp][b][color=#facc15]{escape_kivy_markup(entry.title)}[/color][/b][/size]",
            f"[size=12sp][color=#8f7d62]{escape_kivy_markup(entry.category)}[/color][/size]",
            "",
            escape_kivy_markup(entry.description),
        ]
        detail_lines = [detail for detail in entry.details if detail]
        if detail_lines:
            lines.append("")
            lines.extend(f"[color=#d6c59a]{escape_kivy_markup(detail)}[/color]" for detail in detail_lines)
        return "\n".join(lines)

    def show_examine_entry(self, entry: ExamineEntry) -> None:
        self._examine_panel_visible = True
        self.examine_title_label.text = escape_kivy_markup(entry.title)
        self.examine_label.text = self._examine_entry_markup(entry)
        self.examine_label._sync_text_size()
        self.examine_label._sync_height()
        self._sync_options_area_layout()
        Clock.schedule_once(lambda _dt: setattr(self.examine_scroll, "scroll_y", 1), 0)

    def close_examine_panel(self) -> None:
        self._examine_panel_visible = False
        self.examine_title_label.text = ""
        self.examine_label.text = ""
        self._sync_options_area_layout()

    def show_option_examine(self, option: str, index: int) -> None:
        del index
        self.show_examine_entry(examine_entry_for_text(option, game=self.active_game()))

    def show_examine_ref(self, ref_name: str) -> None:
        entry = self._examine_ref_entries.get(ref_name)
        if entry is None:
            entry = getattr(self, "_log_examine_ref_entries", {}).get(ref_name)
        if entry is not None:
            self.show_examine_entry(entry)

    def _active_game_for_examine_markup(self):
        bridge = getattr(self, "bridge", None)
        return getattr(bridge, "game", None)

    def _reset_examine_refs(self) -> None:
        self._examine_ref_entries = {}
        self._examine_ref_counter = 0

    def _register_examine_ref(self, entry: ExamineEntry) -> str:
        self._examine_ref_counter += 1
        ref_name = f"examine_{self._examine_ref_counter}"
        self._examine_ref_entries[ref_name] = entry
        return ref_name

    def _register_log_examine_ref(self, entry: ExamineEntry) -> str:
        if not hasattr(self, "_log_examine_ref_entries"):
            self._log_examine_ref_entries = {}
            self._log_examine_ref_counter = 0
        self._log_examine_ref_counter += 1
        ref_name = f"log_examine_{self._log_examine_ref_counter}"
        self._log_examine_ref_entries[ref_name] = entry
        return ref_name

    def _clean_log_examine_label(self, label: str) -> str:
        cleaned = " ".join(str(label).replace("\n", " ").split()).strip()
        if re.fullmatch(r"\[[^\]]+\]", cleaned):
            return cleaned
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned).strip()
        return cleaned.strip(" \t\r\n\"'.,:;!?()[]{}")

    def _log_examine_label_allowed(self, label: str) -> bool:
        normalized = " ".join(label.lower().split())
        if not normalized or normalized in self.LOG_EXAMINE_STOP_LABELS:
            return False
        if "\n" in label or len(label) > 64:
            return False
        if "|" in label or re.fullmatch(r"[\d\s/+.,:%-]+", label):
            return False
        if not any(character.isalnum() for character in label):
            return False
        if not re.fullmatch(r"\[[^\]]+\]", label) and len(label.split()) > 6:
            return False
        return True

    def _log_examine_entry_for_label(self, label: str, *, allow_generic: bool) -> ExamineEntry | None:
        cleaned = self._clean_log_examine_label(label)
        if not self._log_examine_label_allowed(cleaned):
            return None
        entry = examine_entry_for_text(cleaned, game=self._active_game_for_examine_markup())
        if not allow_generic and entry.category == "Examine":
            return None
        return entry

    def _visible_index_at_markup_position(self, markup: str, target: int) -> int:
        visible_index = 0
        position = 0
        limit = max(0, min(int(target), len(markup)))
        while position < limit:
            if markup[position] == "[":
                end = markup.find("]", position)
                if end != -1 and end < limit:
                    position = end + 1
                    continue
            if markup[position] == "&":
                end = markup.find(";", position)
                if end != -1 and end < limit:
                    visible_index += 1
                    position = end + 1
                    continue
            visible_index += 1
            position += 1
        return visible_index

    def _markup_visible_character_bounds(self, markup: str) -> list[tuple[int, int, bool]]:
        bounds: list[tuple[int, int, bool]] = []
        position = 0
        ref_depth = 0
        while position < len(markup):
            if markup[position] == "[":
                end = markup.find("]", position)
                if end != -1:
                    tag = markup[position + 1 : end].strip().lower()
                    if tag.startswith("ref="):
                        ref_depth += 1
                    elif tag == "/ref" and ref_depth > 0:
                        ref_depth -= 1
                    position = end + 1
                    continue
            if markup[position] == "&":
                end = markup.find(";", position)
                if end != -1:
                    bounds.append((position, end + 1, ref_depth > 0))
                    position = end + 1
                    continue
            bounds.append((position, position + 1, ref_depth > 0))
            position += 1
        return bounds

    def _log_examine_known_terms(self, visible: str) -> list[str]:
        game = self._active_game_for_examine_markup()
        terms: set[str] = set()
        if game is None:
            return []
        intros = getattr(game, "NAMED_CHARACTER_INTROS", {})
        if isinstance(intros, dict):
            terms.update(str(name) for name in intros)
        scene_labels = getattr(game, "SCENE_LABELS", {})
        if isinstance(scene_labels, dict):
            terms.update(str(label) for label in scene_labels.values())
            terms.update(str(scene_key).replace("_", " ").title() for scene_key in scene_labels)
        hud_location = getattr(game, "hud_location_label", None)
        if callable(hud_location):
            try:
                terms.add(str(hud_location()))
            except Exception:
                pass
        state = getattr(game, "state", None)
        party_members = getattr(state, "party_members", None)
        members = []
        if callable(party_members):
            try:
                members.extend(party_members())
            except Exception:
                pass
        for attr_name in ("companions", "camp_companions"):
            members.extend(getattr(state, attr_name, []) or [])
        public_character_name = getattr(game, "public_character_name", None)
        for member in members:
            name = str(getattr(member, "name", "")).strip()
            if not name:
                continue
            terms.add(name)
            if callable(public_character_name):
                terms.add(str(public_character_name(name)))
        return sorted(
            {
                term.strip()
                for term in terms
                if term and len(term.strip()) > 1 and term.strip().lower() in visible.lower()
            },
            key=len,
            reverse=True,
        )

    def _add_log_examine_range(
        self,
        ranges: list[tuple[int, int, ExamineEntry]],
        start: int,
        end: int,
        entry: ExamineEntry | None,
    ) -> None:
        if entry is None or start < 0 or end <= start:
            return
        for used_start, used_end, _entry in ranges:
            if start < used_end and end > used_start:
                return
        ranges.append((start, end, entry))

    def _annotate_log_examine_markup(self, markup: str) -> str:
        if not markup or "[ref=" in markup:
            return markup
        visible = visible_markup_text(markup)
        if not visible.strip():
            return markup

        ranges: list[tuple[int, int, ExamineEntry]] = []
        for match in KIVY_COLOR_SPAN_RE.finditer(markup):
            label = visible_markup_text(match.group("body"))
            entry = self._log_examine_entry_for_label(label, allow_generic=True)
            start = self._visible_index_at_markup_position(markup, match.start("body"))
            end = self._visible_index_at_markup_position(markup, match.end("body"))
            self._add_log_examine_range(ranges, start, end, entry)

        for term in self._log_examine_known_terms(visible):
            entry = self._log_examine_entry_for_label(term, allow_generic=False)
            if entry is None:
                continue
            pattern = re.compile(rf"(?<![A-Za-z0-9']){re.escape(term)}(?![A-Za-z0-9'])", re.IGNORECASE)
            for match in pattern.finditer(visible):
                self._add_log_examine_range(ranges, match.start(), match.end(), entry)

        for pattern in (KIVY_SKILL_TAG_RE, KIVY_TITLE_PHRASE_RE):
            for match in pattern.finditer(visible):
                label = match.group(0)
                entry = self._log_examine_entry_for_label(label, allow_generic=False)
                self._add_log_examine_range(ranges, match.start(), match.end(), entry)

        if not ranges:
            return markup
        bounds = self._markup_visible_character_bounds(markup)
        insertions: list[tuple[int, int, str]] = []
        occupied: list[tuple[int, int]] = []
        for start, end, entry in sorted(ranges, key=lambda item: (item[0], -(item[1] - item[0]))):
            if start >= len(bounds) or end > len(bounds) or any(bounds[index][2] for index in range(start, end)):
                continue
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            ref_name = self._register_log_examine_ref(entry)
            insertions.append((bounds[end - 1][1], 0, "[/ref]"))
            insertions.append((bounds[start][0], 1, f"[ref={ref_name}]"))
            occupied.append((start, end))
        for position, _order, text in sorted(insertions, key=lambda item: (item[0], item[1]), reverse=True):
            markup = f"{markup[:position]}{text}{markup[position:]}"
        return markup

    def _examine_ref_markup(
        self,
        label: str,
        entry: ExamineEntry,
        *,
        color: str,
        bold: bool = False,
    ) -> str:
        ref_name = self._register_examine_ref(entry)
        body = f"[ref={ref_name}][color=#{color}]{escape_kivy_markup(label)}[/color][/ref]"
        return f"[b]{body}[/b]" if bold else body

    def begin_side_command(self, title: str, *, done_event: Event | None = None) -> None:
        if not self.side_panel_allowed():
            self._complete_log_append(done_event)
            return
        self._set_prompt_controls_docked_to_left(False)
        self.update_combat_layout()
        self._side_panel_mode = "command"
        self._side_command_title = title
        self._side_command_lines = []
        self._clear_combat_resource_animation()
        self.native_map_view.hide_map()
        self._hide_command_workspace()
        self._set_side_command_header_visible(True)
        self.side_command_title_label.text = escape_kivy_markup(title)
        self._render_side_command()
        self._complete_log_append(done_event)

    def append_side_output(self, markup: str, *, done_event: Event | None = None) -> None:
        if not self.side_panel_allowed():
            self._complete_log_append(done_event)
            return
        self._set_prompt_controls_docked_to_left(False)
        self.update_combat_layout()
        if self._side_panel_mode != "command":
            self._side_panel_mode = "command"
            self._side_command_title = "Command"
            self._side_command_lines = []
        if markup:
            self.native_map_view.hide_map()
            self._hide_command_workspace()
            self._side_command_lines.append(markup)
            if len(self._side_command_lines) > self.MAX_LOG_ENTRIES:
                self._side_command_lines = self._side_command_lines[-self.MAX_LOG_ENTRIES :]
        self._render_side_command()
        self._complete_log_append(done_event)

    def prepare_combat_transition(self, *, done_event: Event | None = None, ending: bool = False) -> None:
        self.update_combat_layout()
        if self.combat_active():
            self._side_panel_mode = "default"
            self._sync_combat_resource_targets()
            if ending:
                self._snap_combat_resource_display_to_targets()
                self._fade_out_dice_tray()
            else:
                self._render_combat_panel()
        delay = self.COMBAT_EXIT_TRANSITION_SECONDS if ending else self.COMBAT_ENTRY_TRANSITION_SECONDS
        self._complete_log_append(done_event, delay=delay)

    def _render_combat_panel(self, *, scroll_to_top: bool = True) -> None:
        self._side_panel_mode = "default"
        self.native_map_view.hide_map()
        self._hide_command_workspace()
        self._set_side_command_header_visible(False)
        self._sync_defeated_enemy_fades()
        self._reset_examine_refs()
        self.combat_stats_label.text = self.build_combat_stats_markup()
        if not scroll_to_top:
            return
        Clock.schedule_once(lambda _dt: setattr(self.combat_stats_scroll, "scroll_y", 1), 0)

    def _render_side_command(self) -> None:
        self._reset_examine_refs()
        self._hide_command_workspace()
        title = escape_kivy_markup(self._side_command_title or "Command")
        self._set_side_command_header_visible(True)
        self.side_command_title_label.text = title
        body = "\n".join(line for line in self._side_command_lines if line).strip()
        if body:
            self.combat_stats_label.text = body
        else:
            self.combat_stats_label.text = "[color=#8f7d62]Waiting for command output.[/color]"
        Clock.schedule_once(lambda _dt: setattr(self.combat_stats_scroll, "scroll_y", 1), 0)

    def _render_party_stats_panel(self) -> None:
        self._reset_examine_refs()
        self.native_map_view.hide_map()
        self._hide_command_workspace()
        self._set_side_command_header_visible(False)
        self.combat_stats_label.text = self.build_party_stats_markup()
        Clock.schedule_once(lambda _dt: setattr(self.combat_stats_scroll, "scroll_y", 1), 0)

    def _clear_combat_resource_animation(self) -> None:
        event = self._combat_resource_animation_event
        if event is not None:
            event.cancel()
        self._combat_resource_animation_event = None
        self._combat_resource_display_values.clear()
        self._combat_resource_targets.clear()
        self._combat_hp_impact_elapsed.clear()
        self._combat_damage_popups.clear()

    def _clear_defeated_enemy_fades(self) -> None:
        event = self._defeated_enemy_fade_event
        if event is not None:
            event.cancel()
        self._defeated_enemy_fade_event = None
        self._defeated_enemy_fade_elapsed.clear()
        self._hidden_defeated_enemy_ids.clear()

    def _start_initiative_turn_arrow_animation(self) -> None:
        if self._initiative_turn_arrow_event is not None:
            return
        self._initiative_turn_arrow_event = Clock.schedule_interval(
            self._advance_initiative_turn_arrow,
            self.INITIATIVE_TURN_ARROW_INTERVAL_SECONDS,
        )

    def _stop_initiative_turn_arrow_animation(self) -> None:
        event = self._initiative_turn_arrow_event
        if event is not None:
            event.cancel()
        self._initiative_turn_arrow_event = None
        self._initiative_turn_arrow_phase = 0

    def _advance_initiative_turn_arrow(self, _dt) -> bool:
        if not self.combat_active() or not self._active_combat_actor_name:
            self._initiative_turn_arrow_event = None
            return False
        self._initiative_turn_arrow_phase += 1
        self.refresh_active_initiative_tray()
        return True

    def refresh_active_initiative_tray(self) -> None:
        if not self.combat_active() or not self._active_combat_actor_name:
            return
        game = self.active_game()
        panel_builder = getattr(game, "kivy_active_initiative_panel", None)
        if not callable(panel_builder):
            return
        panel = panel_builder(
            active_actor_name=self._active_combat_actor_name,
            arrow_phase=self._initiative_turn_arrow_phase,
        )
        if panel is None:
            return
        markup, tray_height = panel
        self._show_dice_tray_frame(
            markup,
            final=False,
            tray_height=tray_height,
            persist=True,
        )

    def _enemy_defeated(self, enemy) -> bool:
        return bool(getattr(enemy, "dead", False) or int(getattr(enemy, "current_hp", 0) or 0) <= 0)

    def _enemy_fade_key(self, enemy) -> int:
        return id(enemy)

    def _enemy_fade_opacity(self, enemy) -> float:
        key = self._enemy_fade_key(enemy)
        if key in self._hidden_defeated_enemy_ids:
            return 0.0
        elapsed = self._defeated_enemy_fade_elapsed.get(key)
        if elapsed is None or elapsed <= 0:
            return 1.0
        return max(0.0, 1.0 - (elapsed / max(0.01, self.DEFEATED_ENEMY_FADE_SECONDS)))

    def _start_defeated_enemy_fade_animation(self) -> None:
        if self._defeated_enemy_fade_event is not None or not self._defeated_enemy_fade_elapsed:
            return
        self._defeated_enemy_fade_event = Clock.schedule_interval(
            self._advance_defeated_enemy_fade,
            self.DEFEATED_ENEMY_FADE_INTERVAL_SECONDS,
        )

    def _sync_defeated_enemy_fades(self) -> None:
        if not self.combat_active():
            self._clear_defeated_enemy_fades()
            return
        game = self.active_game()
        enemies = list(getattr(game, "_active_combat_enemies", []) or []) if game is not None else []
        active_ids = {self._enemy_fade_key(enemy) for enemy in enemies}
        for key in list(self._defeated_enemy_fade_elapsed):
            if key not in active_ids:
                del self._defeated_enemy_fade_elapsed[key]
        self._hidden_defeated_enemy_ids.intersection_update(active_ids)

        for enemy in enemies:
            key = self._enemy_fade_key(enemy)
            if not self._enemy_defeated(enemy):
                self._defeated_enemy_fade_elapsed.pop(key, None)
                self._hidden_defeated_enemy_ids.discard(key)
                continue
            if key in self._hidden_defeated_enemy_ids or key in self._defeated_enemy_fade_elapsed:
                continue
            current_hp = int(getattr(enemy, "current_hp", 0) or 0)
            displayed_hp = self._displayed_combat_resource_value(enemy, "hp", current_hp)
            if displayed_hp <= 0:
                self._defeated_enemy_fade_elapsed[key] = -self.DEFEATED_ENEMY_HOLD_SECONDS
        self._start_defeated_enemy_fade_animation()

    def _advance_defeated_enemy_fade(self, dt) -> bool:
        if not self.combat_active():
            self._clear_defeated_enemy_fades()
            return False
        remaining = False
        for key in list(self._defeated_enemy_fade_elapsed):
            elapsed = self._defeated_enemy_fade_elapsed[key] + dt
            if elapsed >= self.DEFEATED_ENEMY_FADE_SECONDS:
                del self._defeated_enemy_fade_elapsed[key]
                self._hidden_defeated_enemy_ids.add(key)
            else:
                self._defeated_enemy_fade_elapsed[key] = elapsed
                remaining = True
        self._render_combat_panel(scroll_to_top=False)
        remaining = remaining or bool(self._defeated_enemy_fade_elapsed)
        if not remaining:
            self._defeated_enemy_fade_event = None
        return remaining

    def _skip_defeated_enemy_fade_animation(self) -> bool:
        if not self._defeated_enemy_fade_elapsed:
            return False
        event = self._defeated_enemy_fade_event
        if event is not None:
            event.cancel()
        self._hidden_defeated_enemy_ids.update(self._defeated_enemy_fade_elapsed)
        self._defeated_enemy_fade_elapsed.clear()
        self._defeated_enemy_fade_event = None
        if self.combat_active():
            self._render_combat_panel(scroll_to_top=False)
        return True

    def _combat_resource_key(self, combatant, resource_name: str) -> tuple[int, str]:
        return (id(combatant), resource_name)

    def _combat_resource_entries(self) -> list[tuple[object, str, int, int]]:
        game = self.active_game()
        if game is None:
            return []
        combatants = list(getattr(game, "_active_combat_heroes", []) or [])
        combatants.extend(list(getattr(game, "_active_combat_enemies", []) or []))
        entries: list[tuple[object, str, int, int]] = []
        for combatant in combatants:
            max_hp = max(1, int(getattr(combatant, "max_hp", 1) or 1))
            current_hp = max(0, min(int(getattr(combatant, "current_hp", 0) or 0), max_hp))
            entries.append((combatant, "hp", current_hp, max_hp))
            max_mp = max(0, int(maximum_magic_points(combatant) or 0))
            if max_mp > 0:
                current_mp = max(0, min(int(current_magic_points(combatant) or 0), max_mp))
                entries.append((combatant, "mp", current_mp, max_mp))
        return entries

    def _sync_combat_resource_targets(self) -> None:
        active_keys: set[tuple[int, str]] = set()
        for combatant, resource_name, current, _maximum in self._combat_resource_entries():
            key = self._combat_resource_key(combatant, resource_name)
            active_keys.add(key)
            displayed = self._combat_resource_display_values.setdefault(key, current)
            previous_target = self._combat_resource_targets.get(key, displayed)
            self._combat_resource_targets[key] = current
            if resource_name == "hp":
                damage_amount = max(
                    1,
                    (previous_target - current) if current < previous_target else (displayed - current),
                )
                if current < displayed and key not in self._combat_hp_impact_elapsed:
                    self._combat_hp_impact_elapsed[key] = 0.0
                    self._combat_damage_popups[key] = (damage_amount, 0.0)
                elif current < previous_target:
                    self._combat_damage_popups[key] = (damage_amount, 0.0)
                elif current >= displayed:
                    self._combat_hp_impact_elapsed.pop(key, None)
                    if current > displayed:
                        self._combat_damage_popups.pop(key, None)

        for key in list(self._combat_resource_display_values):
            if key not in active_keys:
                del self._combat_resource_display_values[key]
        for key in list(self._combat_resource_targets):
            if key not in active_keys:
                del self._combat_resource_targets[key]
        for key in list(self._combat_hp_impact_elapsed):
            if key not in active_keys:
                del self._combat_hp_impact_elapsed[key]
        for key in list(self._combat_damage_popups):
            if key not in active_keys:
                del self._combat_damage_popups[key]

        if any(
            self._combat_resource_display_values.get(key, target) != target
            for key, target in self._combat_resource_targets.items()
        ) or bool(self._combat_hp_impact_elapsed) or bool(self._combat_damage_popups):
            self._start_combat_resource_animation()
        elif self._combat_resource_animation_event is not None:
            self._combat_resource_animation_event.cancel()
            self._combat_resource_animation_event = None

    def _start_combat_resource_animation(self) -> None:
        if self._combat_resource_animation_event is not None:
            return
        self._combat_resource_animation_event = Clock.schedule_interval(
            self._advance_combat_resource_animation,
            self.COMBAT_RESOURCE_ANIMATION_INTERVAL_SECONDS,
        )

    def _snap_combat_resource_display_to_targets(self) -> None:
        event = self._combat_resource_animation_event
        if event is not None:
            event.cancel()
        self._combat_resource_animation_event = None
        for key, target in self._combat_resource_targets.items():
            self._combat_resource_display_values[key] = target
        self._combat_hp_impact_elapsed.clear()
        self._combat_damage_popups.clear()
        self._render_combat_panel(scroll_to_top=False)

    def _combat_hp_impact_duration(self) -> float:
        return self.COMBAT_HP_IMPACT_RED_SECONDS + self.COMBAT_HP_IMPACT_RECOVER_SECONDS

    def _combat_damage_number_duration(self) -> float:
        return self.COMBAT_DAMAGE_NUMBER_HOLD_SECONDS + self.COMBAT_DAMAGE_NUMBER_FADE_SECONDS

    def _advance_combat_resource_animation(self, dt) -> bool:
        if not self.combat_active():
            self._clear_combat_resource_animation()
            return False
        changed = False
        remaining = False
        popup_dt = max(0.0, float(dt))
        for key, (amount, elapsed) in list(self._combat_damage_popups.items()):
            next_elapsed = elapsed + popup_dt
            if next_elapsed >= self._combat_damage_number_duration():
                del self._combat_damage_popups[key]
            else:
                self._combat_damage_popups[key] = (amount, next_elapsed)
                remaining = True
            changed = True
        for key, target in list(self._combat_resource_targets.items()):
            current = self._combat_resource_display_values.get(key, target)
            impact_elapsed = self._combat_hp_impact_elapsed.get(key)
            if impact_elapsed is not None:
                if current > target:
                    next_elapsed = impact_elapsed + max(0.0, float(dt))
                    if next_elapsed < self._combat_hp_impact_duration():
                        self._combat_hp_impact_elapsed[key] = next_elapsed
                    else:
                        del self._combat_hp_impact_elapsed[key]
                    changed = True
                    remaining = True
                    continue
                del self._combat_hp_impact_elapsed[key]
            if current == target:
                continue
            delta = target - current
            step = max(1, math.ceil(abs(delta) / self.COMBAT_RESOURCE_ANIMATION_MAX_STEPS))
            next_value = target if abs(delta) <= step else current + (step if delta > 0 else -step)
            self._combat_resource_display_values[key] = next_value
            changed = True
            if next_value != target:
                remaining = True
        if changed:
            self._render_combat_panel(scroll_to_top=False)
        if not remaining:
            self._combat_resource_animation_event = None
        return remaining

    def _displayed_combat_resource_value(self, combatant, resource_name: str, current: int) -> int:
        return self._combat_resource_display_values.get(self._combat_resource_key(combatant, resource_name), current)

    def combat_damage_popup_markup(self, combatant) -> str:
        popup = self._combat_damage_popups.get(self._combat_resource_key(combatant, "hp"))
        if popup is None:
            return ""
        amount, elapsed = popup
        fade_elapsed = max(0.0, elapsed - self.COMBAT_DAMAGE_NUMBER_HOLD_SECONDS)
        fade_duration = max(0.01, self.COMBAT_DAMAGE_NUMBER_FADE_SECONDS)
        opacity = 1.0 - min(1.0, fade_elapsed / fade_duration)
        alpha_hex = f"{int(round(max(0.0, min(1.0, opacity)) * 255)):02x}"
        return f"  [size=16sp][b][color=#ef4444{alpha_hex}]-{amount}[/color][/b][/size]"

    def health_color(self, current_hp: int, max_hp: int) -> str:
        if max_hp <= 0 or current_hp <= 0:
            return "f87171"
        ratio = current_hp / max_hp
        if ratio > 0.5:
            return "7ee787"
        if ratio > 0.25:
            return "facc15"
        return "f87171"

    def stat_bar_markup(self, current: int, maximum: int, *, width: int = 14, color: str | None = None) -> str:
        resolved_color = color or self.health_color(current, maximum)
        return kivy_resource_bar_markup(current, maximum, width=width, color=resolved_color)

    def health_bar_markup(self, combatant, current: int, maximum: int, *, width: int = 14) -> str:
        key = self._combat_resource_key(combatant, "hp")
        color = self.health_color(current, maximum)
        shake_offset = 0
        elapsed = self._combat_hp_impact_elapsed.get(key)
        if elapsed is not None:
            if elapsed < self.COMBAT_HP_IMPACT_RED_SECONDS:
                color = "f87171"
            offsets = self.COMBAT_HP_IMPACT_SHAKE_OFFSETS
            if offsets:
                frame = int(elapsed / max(0.01, self.COMBAT_RESOURCE_ANIMATION_INTERVAL_SECONDS))
                shake_offset = int(offsets[frame % len(offsets)])
        return (" " * max(0, shake_offset)) + self.stat_bar_markup(current, maximum, width=width, color=color)

    def combatant_conditions_text(self, game: "ClickableTextDnDGame", combatant) -> str:
        conditions: list[str] = []
        status_name = getattr(game, "status_name", None)
        total_charges = getattr(game, "total_arcanist_pattern_charges", None)
        for name, value in getattr(combatant, "conditions", {}).items():
            if value == 0:
                continue
            if name == "pattern_charge" and callable(total_charges):
                charges = total_charges(combatant)
                if charges:
                    conditions.append(f"Pattern Charge {charges}")
                continue
            conditions.append(str(status_name(name) if callable(status_name) else name.replace("_", " ").title()))
        return ", ".join(conditions)

    def combatant_conditions_markup(self, game: "ClickableTextDnDGame", combatant) -> str:
        conditions: list[str] = []
        status_name = getattr(game, "status_name", None)
        total_charges = getattr(game, "total_arcanist_pattern_charges", None)
        for name, value in getattr(combatant, "conditions", {}).items():
            if value == 0:
                continue
            if name == "pattern_charge" and callable(total_charges):
                charges = total_charges(combatant)
                if not charges:
                    continue
                label = f"Pattern Charge {charges}"
            else:
                label = str(status_name(name) if callable(status_name) else name.replace("_", " ").title())
            entry = status_examine_entry(name) or feature_examine_entry(name)
            if entry is None:
                conditions.append(escape_kivy_markup(label))
            else:
                conditions.append(self._examine_ref_markup(label, entry, color="d8b4fe"))
        return ", ".join(conditions)

    def combatant_resource_text(self, combatant) -> str:
        resources = getattr(combatant, "resources", {}) or {}
        maximums = getattr(combatant, "max_resources", {}) or {}
        parts: list[str] = []
        for key in sorted(set(resources) | set(maximums)):
            if key == "mp":
                continue
            current = int(resources.get(key, 0) or 0)
            maximum = int(maximums.get(key, 0) or 0)
            if current <= 0 and maximum <= 0:
                continue
            label = key.replace("_", " ").title()
            parts.append(f"{label} {current}/{maximum}" if maximum else f"{label} {current}")
        return " | ".join(parts)

    def combatant_resource_markup(self, combatant) -> str:
        resources = getattr(combatant, "resources", {}) or {}
        maximums = getattr(combatant, "max_resources", {}) or {}
        parts: list[str] = []
        for key in sorted(set(resources) | set(maximums)):
            if key == "mp":
                continue
            current = int(resources.get(key, 0) or 0)
            maximum = int(maximums.get(key, 0) or 0)
            if current <= 0 and maximum <= 0:
                continue
            label = key.replace("_", " ").title()
            value = f"{current}/{maximum}" if maximum else f"{current}"
            entry = resource_examine_entry(key)
            if entry is None:
                parts.append(f"{escape_kivy_markup(label)} {escape_kivy_markup(value)}")
            else:
                parts.append(f"{self._examine_ref_markup(entry.title, entry, color='d6c59a')} {escape_kivy_markup(value)}")
        return " | ".join(parts)

    def combatant_feature_markup(self, combatant, *, limit: int = 5) -> str:
        features = [str(feature) for feature in getattr(combatant, "features", []) if str(feature).strip()]
        if not features:
            return ""
        parts: list[str] = []
        for feature_id in features[:limit]:
            entry = feature_examine_entry(feature_id)
            if entry is None:
                parts.append(escape_kivy_markup(feature_id.replace("_", " ").title()))
            else:
                parts.append(self._examine_ref_markup(entry.title, entry, color="d8b4fe"))
        if len(features) > limit:
            parts.append(escape_kivy_markup(f"+{len(features) - limit} more"))
        return ", ".join(parts)

    def combatant_markup(self, game: "ClickableTextDnDGame", combatant, *, enemy: bool) -> str:
        raw_name = str(getattr(combatant, "name", "Unknown"))
        public_name = game.public_character_name(raw_name) if hasattr(game, "public_character_name") else raw_name
        name_color = "f87171" if enemy else "67e8f9"
        current_hp = int(getattr(combatant, "current_hp", 0) or 0)
        if getattr(combatant, "dead", False) or current_hp <= 0:
            name_color = "8f7d62"
        if raw_name == self._active_combat_actor_name:
            name_color = "facc15"
        name_markup = self._examine_ref_markup(
            public_name,
            character_examine_entry(combatant, game=game),
            color=name_color,
            bold=True,
        )
        hp = self.health_bar_markup(
            combatant,
            self._displayed_combat_resource_value(combatant, "hp", current_hp),
            getattr(combatant, "max_hp", 1),
        )
        damage_popup = self.combat_damage_popup_markup(combatant)
        ac = getattr(combatant, "armor_class", "?")
        temp = f" temp {combatant.temp_hp}" if getattr(combatant, "temp_hp", 0) else ""
        defense_summary = ""
        combat_defense_summary = getattr(game, "combat_defense_summary", None)
        if callable(combat_defense_summary):
            defense_summary = f" | {strip_ansi(combat_defense_summary(combatant))}"
        status = " DEAD" if getattr(combatant, "dead", False) else " DOWN" if getattr(combatant, "current_hp", 0) <= 0 else ""
        lines = [
            f"{name_markup}"
            f" [size=14sp][color=#b8a98d]Lv {getattr(combatant, 'level', '?')} AC {ac}{defense_summary}{temp}{status}[/color][/size]",
            f"[size=14sp]HP: {hp}{damage_popup}[/size]",
        ]
        max_mp = maximum_magic_points(combatant)
        if max_mp > 0:
            current_mp = current_magic_points(combatant)
            displayed_mp = self._displayed_combat_resource_value(combatant, "mp", current_mp)
            mp_entry = resource_examine_entry("mp")
            mp_label = self._examine_ref_markup("MP", mp_entry, color="60a5fa") if mp_entry is not None else "MP"
            lines.append(f"[size=14sp]{mp_label}: {self.stat_bar_markup(displayed_mp, max_mp, color='60a5fa')}[/size]")
        resources = self.combatant_resource_markup(combatant)
        if resources:
            lines.append(f"[size=14sp][color=#d6c59a]{resources}[/color][/size]")
        conditions = self.combatant_conditions_markup(game, combatant)
        if conditions:
            lines.append(f"[size=14sp][color=#d8b4fe]{conditions}[/color][/size]")
        features = self.combatant_feature_markup(combatant)
        if features:
            lines.append(f"[size=13sp][color=#8f7d62]Traits[/color]: {features}[/size]")
        markup = "\n".join(lines)
        if enemy:
            opacity = self._enemy_fade_opacity(combatant)
            if opacity < 1.0:
                return fade_kivy_markup(markup, opacity, default_color="8f7d62")
        return markup

    def build_combat_group_markup(self, title: str, combatants: list, *, enemy: bool) -> str:
        game = self.active_game()
        if game is None:
            return ""
        title_color = "f87171" if enemy else "67e8f9"
        lines = [f"[b][color=#{title_color}]{title}[/color][/b]"]
        visible_combatants = [
            combatant
            for combatant in combatants
            if not enemy or self._enemy_fade_key(combatant) not in self._hidden_defeated_enemy_ids
        ]
        if not visible_combatants:
            lines.append("[color=#8f7d62]None standing.[/color]")
        else:
            for combatant in visible_combatants:
                lines.append(self.combatant_markup(game, combatant, enemy=enemy))
        return "\n\n".join(lines)

    def build_party_stats_markup(self) -> str:
        game = self.active_game()
        if game is None or getattr(game, "state", None) is None:
            return "[color=#8f7d62]No active party.[/color]"
        state = game.state
        scene_labels = getattr(game, "SCENE_LABELS", {})
        current_scene = str(getattr(state, "current_scene", ""))
        location = scene_labels.get(current_scene, current_scene.replace("_", " ").title() or "Adventure")
        location_entry = current_location_examine_entry(game)
        location_markup = (
            self._examine_ref_markup(location, location_entry, color="67e8f9")
            if location_entry is not None
            else escape_kivy_markup(location)
        )
        act_labels = getattr(game, "ACT_LABELS", {})
        act_text = f"Act {act_labels.get(getattr(state, 'current_act', '?'), getattr(state, 'current_act', '?'))}"
        supply_getter = getattr(game, "current_supply_points", None)
        supplies = supply_getter() if callable(supply_getter) else "?"
        header = (
            f"[size=20sp][b][color=#facc15]Party[/color][/b][/size]\n"
            f"[size=14sp][color=#8f7d62]{escape_kivy_markup(act_text)} | {location_markup}[/color][/size]\n"
            f"[size=14sp][color=#d6c59a]Gold {getattr(state, 'gold', 0)} | Short rests {getattr(state, 'short_rests_remaining', 0)} | Supplies {supplies}[/color][/size]"
        )
        objective_getter = getattr(game, "hud_objective_label", None)
        objective = objective_getter() if callable(objective_getter) else ""
        lines = [header]
        if objective:
            lines.append(f"[size=14sp][color=#b8a98d]Objective: {escape_kivy_markup(objective)}[/color][/size]")
        party_members = list(state.party_members())
        if party_members:
            lines.append(self.build_combat_group_markup("Active Party", party_members, enemy=False))
        else:
            lines.append("[color=#8f7d62]No one is in the active party.[/color]")
        return "\n\n".join(lines)

    def build_combat_stats_markup(self) -> str:
        game = self.active_game()
        if game is None:
            return ""
        encounter = getattr(game, "_active_encounter", None)
        encounter_title = str(getattr(encounter, "title", "Combat"))
        round_number = getattr(game, "_active_round_number", None)
        actor_line = f" | Acting: {self._active_combat_actor_name}" if self._active_combat_actor_name else ""
        header = (
            f"[size=20sp][b][color=#facc15]{escape_kivy_markup(encounter_title)}[/color][/b][/size]\n"
            f"[size=14sp][color=#8f7d62]Round {round_number or '?'}{escape_kivy_markup(actor_line)}[/color][/size]"
        )
        heroes = list(getattr(game, "_active_combat_heroes", []) or [])
        enemies = list(getattr(game, "_active_combat_enemies", []) or [])
        sections = [
            header,
            self.build_combat_group_markup("Party", heroes, enemy=False),
            self.build_combat_group_markup("Enemies", enemies, enemy=True),
        ]
        return "\n\n".join(sections)

    def append_output(self, text: object, *, done_event: Event | None = None) -> None:
        self.update_combat_layout()
        markup, animated = format_kivy_log_entry(text)
        self.append_log(markup, done_event=done_event, animated=animated)

    def show_dice_animation_frame(
        self,
        markup: str,
        *,
        final: bool = False,
        use_tray: bool = False,
        use_roll_tray: bool = False,
        tray_height: float | None = None,
        tray_parts: tuple[str, str, str] | None = None,
        pulse_scale: float = 1.0,
        core_slot_width: float | None = None,
        persist: bool = False,
        done_event: Event | None = None,
    ) -> None:
        self.update_combat_layout()
        if use_tray and use_roll_tray and self.side_panel_allowed():
            self._show_dice_roll_side_frame(
                markup,
                final=final,
                tray_height=tray_height,
                tray_parts=tray_parts,
                pulse_scale=pulse_scale,
                core_slot_width=core_slot_width,
            )
            self._complete_log_append(done_event)
            return
        if use_tray:
            self._show_dice_tray_frame(
                markup,
                final=final,
                tray_height=tray_height,
                tray_parts=tray_parts,
                pulse_scale=pulse_scale,
                core_slot_width=core_slot_width,
                persist=persist,
            )
            self._complete_log_append(done_event)
            return
        if self._dice_animation_line_index is None or self._dice_animation_line_index >= len(self._log_lines):
            self._dice_animation_line_index = len(self._log_lines)
            self._append_log_entry(markup)
        else:
            self._log_lines[self._dice_animation_line_index] = markup
            self._render_log()
        if final:
            self._dice_animation_line_index = None
        self._complete_log_append(done_event)

    def _dice_tray_height_for_markup(self, markup: str, tray_height: float | None = None) -> float:
        if tray_height is not None:
            return min(float(self.DICE_ANIMATION_TRAY_MAX_HEIGHT), max(float(self.DICE_ANIMATION_TRAY_HEIGHT), float(tray_height)))
        line_count = visible_markup_text(markup).count("\n") + 1
        if line_count <= 2:
            return float(self.DICE_ANIMATION_TRAY_HEIGHT)
        return min(float(self.DICE_ANIMATION_TRAY_MAX_HEIGHT), max(150.0, 28.0 + 24.0 * line_count))

    def _cancel_dice_tray_hide(self) -> None:
        if self._dice_tray_hide_event is not None:
            self._dice_tray_hide_event.cancel()
            self._dice_tray_hide_event = None
        self._dice_tray_hide_ready_at = 0.0

    def _dice_tray_hold_seconds(self) -> float:
        return max(5.0, float(self.DICE_ANIMATION_TRAY_HIDE_SECONDS))

    def _mark_dice_tray_transient_hold(self) -> None:
        hold_until = time.monotonic() + self._dice_tray_hold_seconds()
        self._dice_tray_transient_hold_until = max(
            float(getattr(self, "_dice_tray_transient_hold_until", 0.0)),
            hold_until,
        )

    def _dice_tray_result_hold_active(self) -> bool:
        hold_until = max(
            float(getattr(self, "_dice_tray_hide_ready_at", 0.0)),
            float(getattr(self, "_dice_tray_transient_hold_until", 0.0)),
        )
        return bool(
            hold_until > 0
            and time.monotonic() < hold_until
        )

    def _schedule_dice_tray_hide(self) -> None:
        self._cancel_dice_tray_hide()
        visible_seconds = self._dice_tray_hold_seconds()
        hide_generation = self._dice_tray_fade_generation
        self._dice_tray_hide_ready_at = time.monotonic() + visible_seconds
        self._dice_tray_transient_hold_until = max(
            float(getattr(self, "_dice_tray_transient_hold_until", 0.0)),
            self._dice_tray_hide_ready_at,
        )

        def hide_tray(_dt) -> None:
            if hide_generation != self._dice_tray_fade_generation:
                return
            remaining = self._dice_tray_hide_ready_at - time.monotonic()
            if remaining > 0.01:
                self._dice_tray_hide_event = Clock.schedule_once(hide_tray, remaining)
                return
            self._dice_tray_hide_event = None
            self._dice_tray_hide_ready_at = 0.0
            self._dice_tray_transient_hold_until = 0.0
            if self._restore_persistent_dice_tray():
                return
            self._clear_dice_tray()

        self._dice_tray_hide_event = Clock.schedule_once(hide_tray, visible_seconds)

    def _remember_persistent_dice_tray(
        self,
        markup: str,
        *,
        tray_height: float | None,
        tray_parts: tuple[str, str, str] | None,
        pulse_scale: float,
        core_slot_width: float | None,
    ) -> None:
        self._persistent_dice_tray_markup = markup
        self._persistent_dice_tray_height = tray_height
        self._persistent_dice_tray_parts = tray_parts
        self._persistent_dice_tray_pulse_scale = pulse_scale
        self._persistent_dice_tray_core_slot_width = core_slot_width

    def _clear_persistent_dice_tray(self) -> None:
        self._persistent_dice_tray_markup = ""
        self._persistent_dice_tray_height = None
        self._persistent_dice_tray_parts = None
        self._persistent_dice_tray_pulse_scale = 1.0
        self._persistent_dice_tray_core_slot_width = None

    def _restore_persistent_dice_tray(self) -> bool:
        if not self._persistent_dice_tray_markup or not self.combat_active():
            return False
        self._show_dice_tray_frame(
            self._persistent_dice_tray_markup,
            final=False,
            tray_height=self._persistent_dice_tray_height,
            tray_parts=self._persistent_dice_tray_parts,
            pulse_scale=self._persistent_dice_tray_pulse_scale,
            core_slot_width=self._persistent_dice_tray_core_slot_width,
            persist=True,
        )
        return True

    def _set_dice_tray_reserved(self, reserved: bool, *, tray_height: float | None = None) -> None:
        height = float(self.DICE_ANIMATION_TRAY_HEIGHT if tray_height is None else tray_height)
        self.dice_animation_tray.height = dp(height) if reserved else 0
        self._sync_log_viewport_height()

    def _set_dice_tray_visible(self, visible: bool, *, tray_height: float | None = None) -> None:
        self._dice_tray_active = visible
        self._set_dice_tray_reserved(visible, tray_height=tray_height)
        self.dice_animation_tray.opacity = 1 if visible else 0
        self.dice_animation_tray.disabled = not visible

    def _set_dice_roll_tray_visible(self, visible: bool, *, tray_height: float | None = None) -> None:
        self._dice_roll_tray_active = visible
        height = max(168.0, float(self.DICE_ANIMATION_TRAY_HEIGHT if tray_height is None else tray_height))
        self.dice_roll_tray.height = dp(height) if visible else 0
        self.dice_roll_tray.opacity = 1 if visible else 0
        self.dice_roll_tray.disabled = not visible

    def _clear_dice_roll_tray(self) -> None:
        self._dice_roll_tray_fade_generation += 1
        Animation.cancel_all(self.dice_roll_tray, "opacity")
        self.dice_roll_panel_label.text = ""
        self.dice_roll_prefix_label.text = ""
        self.dice_roll_core_label.text = ""
        self.dice_roll_suffix_label.text = ""
        self._set_dice_roll_tray_content_mode("row")
        self.dice_roll_prefix_label.height = dp(26)
        self.dice_roll_core_label.height = dp(58)
        self.dice_roll_suffix_label.height = dp(42)
        self._set_dice_roll_tray_visible(False)

    def _set_dice_roll_tray_content_mode(self, mode: str) -> None:
        label_visible = mode == "label"
        self.dice_roll_panel_label.opacity = 1 if label_visible else 0
        self.dice_roll_panel_label.disabled = not label_visible
        self.dice_roll_panel_label.size_hint_y = 1 if label_visible else None
        self.dice_roll_panel_label.height = max(dp(1), self.dice_roll_tray.height) if label_visible else 0
        self.dice_roll_row.opacity = 0 if label_visible else 1
        self.dice_roll_row.disabled = label_visible
        self.dice_roll_row.size_hint_y = None if label_visible else 1
        self.dice_roll_row.height = 0 if label_visible else max(dp(1), self.dice_roll_tray.height)

    def _show_dice_roll_side_frame(
        self,
        markup: str,
        *,
        final: bool,
        tray_height: float | None = None,
        tray_parts: tuple[str, str, str] | None = None,
        pulse_scale: float = 1.0,
        core_slot_width: float | None = None,
    ) -> None:
        del pulse_scale, core_slot_width
        if not self.side_panel_allowed():
            return
        self._dice_roll_tray_fade_generation += 1
        Animation.cancel_all(self.dice_roll_tray, "opacity")
        resolved_height = self._dice_tray_height_for_markup(markup, tray_height)
        self._set_dice_roll_tray_visible(True, tray_height=resolved_height)
        if tray_parts is None:
            self._set_dice_roll_tray_content_mode("label")
            self.dice_roll_panel_label.text = markup
            self._sync_dice_animation_label(self.dice_roll_panel_label)
        else:
            self._set_dice_roll_tray_content_mode("row")
            prefix, core, suffix = tray_parts
            self.dice_roll_prefix_label.text = prefix
            self.dice_roll_prefix_label.height = dp(26) if prefix else 0
            self.dice_roll_core_label.text = core
            self.dice_roll_core_label.height = dp(58)
            self.dice_roll_suffix_label.text = suffix
            self.dice_roll_suffix_label.height = dp(42) if suffix else dp(22)
            self.dice_roll_core_label.font_size = "34sp"
            for label in (self.dice_roll_prefix_label, self.dice_roll_core_label, self.dice_roll_suffix_label):
                self._sync_dice_roll_label(label)
        del final

    def fade_out_initiative_tray(self) -> None:
        self._fade_out_dice_tray()

    def _fade_out_dice_tray(self) -> None:
        if not self._dice_tray_active:
            self._clear_persistent_dice_tray()
            self._dice_tray_transient_hold_until = 0.0
            self._stop_initiative_turn_arrow_animation()
            return
        self._dice_tray_fade_generation += 1
        fade_generation = self._dice_tray_fade_generation
        self._cancel_dice_tray_hide()
        self._dice_tray_transient_hold_until = 0.0
        self._clear_persistent_dice_tray()
        self._stop_initiative_turn_arrow_animation()
        self.dice_animation_tray.disabled = True
        Animation.cancel_all(self.dice_animation_tray, "opacity")

        def finish_clear(_animation, _widget) -> None:
            if fade_generation != self._dice_tray_fade_generation:
                return
            self._clear_dice_tray(clear_persistent=False)

        animation = Animation(opacity=0, duration=self.DICE_ANIMATION_TRAY_FADE_SECONDS)
        animation.bind(on_complete=finish_clear)
        animation.start(self.dice_animation_tray)

    def _set_dice_tray_content_mode(self, mode: str) -> None:
        del mode
        self.dice_animation_label.opacity = 1
        self.dice_animation_label.disabled = False
        self.dice_animation_label.size_hint_y = 1
        self.dice_animation_label.height = max(dp(1), self.dice_animation_tray.height)

    def _show_dice_tray_row(
        self,
        tray_parts: tuple[str, str, str],
        *,
        pulse_scale: float,
        core_slot_width: float | None,
    ) -> None:
        del pulse_scale, core_slot_width
        prefix, core, suffix = tray_parts
        self._set_dice_tray_content_mode("row")
        self.dice_roll_prefix_label.text = prefix
        self.dice_roll_core_label.text = core
        self.dice_roll_suffix_label.text = suffix
        self.dice_roll_core_label.font_size = "20sp"
        for label in (self.dice_roll_prefix_label, self.dice_roll_core_label, self.dice_roll_suffix_label):
            self._sync_dice_roll_label(label)

    def _show_dice_tray_frame(
        self,
        markup: str,
        *,
        final: bool,
        tray_height: float | None = None,
        tray_parts: tuple[str, str, str] | None = None,
        pulse_scale: float = 1.0,
        core_slot_width: float | None = None,
        persist: bool = False,
    ) -> None:
        if persist and self._dice_tray_result_hold_active():
            resolved_height = self._dice_tray_height_for_markup(markup, tray_height)
            self._remember_persistent_dice_tray(
                markup,
                tray_height=resolved_height,
                tray_parts=tray_parts,
                pulse_scale=pulse_scale,
                core_slot_width=core_slot_width,
            )
            return
        if not persist:
            self._mark_dice_tray_transient_hold()
        self._dice_tray_fade_generation += 1
        Animation.cancel_all(self.dice_animation_tray, "opacity")
        self._cancel_dice_tray_hide()
        resolved_height = self._dice_tray_height_for_markup(markup, tray_height)
        if persist:
            self._remember_persistent_dice_tray(
                markup,
                tray_height=resolved_height,
                tray_parts=tray_parts,
                pulse_scale=pulse_scale,
                core_slot_width=core_slot_width,
            )
        if not self._dice_tray_active:
            self._set_dice_tray_visible(True, tray_height=resolved_height)
        else:
            self._set_dice_tray_reserved(True, tray_height=resolved_height)
        self._set_dice_tray_content_mode("label")
        self.dice_animation_label.text = markup
        self._sync_dice_animation_label(self.dice_animation_label)
        if final and not persist:
            self._schedule_dice_tray_hide()

    def _clear_dice_tray(self, *, clear_persistent: bool = True) -> None:
        self._dice_tray_fade_generation += 1
        Animation.cancel_all(self.dice_animation_tray, "opacity")
        self._cancel_dice_tray_hide()
        self._dice_tray_transient_hold_until = 0.0
        if clear_persistent:
            self._clear_persistent_dice_tray()
            self._stop_initiative_turn_arrow_animation()
        self.dice_animation_label.text = ""
        self._set_dice_tray_content_mode("label")
        self._set_dice_tray_visible(False)

    def append_dice_result(self, markup: str, *, done_event: Event | None = None) -> None:
        self._dice_animation_line_index = None
        self.update_combat_layout()
        if markup:
            self._append_log_entry(markup)
        self._complete_log_append(done_event)

    def append_log(
        self,
        text: str,
        *,
        done_event: Event | None = None,
        animated: bool = True,
        fast_reveal: bool = False,
    ) -> None:
        text = self._annotate_log_examine_markup(text)
        if not text or not self.typing_animation_enabled or not animated or visible_markup_length(text) <= 8:
            combat_delay = self.combat_active()
            delay = kivy_non_dialogue_reveal_delay(
                text,
                animated=animated,
                enabled=bool(text and self.typing_animation_enabled),
                fast=fast_reveal,
                combat=combat_delay,
            )
            if delay > 0:
                if combat_delay:
                    self._append_log_entry(text)
                    self._complete_log_append(done_event, delay=delay)
                else:
                    self._append_fading_log_entry(text, done_event=done_event, duration=delay)
            else:
                self._append_log_entry(text)
                self._complete_log_append(done_event)
            return
        self._typing_queue.append((text, done_event))
        self._start_typing_next()

    def _append_fading_log_entry(self, text: str, *, done_event: Event | None, duration: float) -> None:
        entry_index = len(self._log_lines)
        self._append_log_entry(fade_kivy_markup(text, 0.0))
        elapsed = 0.0
        self._fade_animation_index = entry_index
        self._fade_animation_markup = text
        self._fade_animation_done_event = done_event

        def advance_fade(dt) -> bool:
            nonlocal elapsed
            if entry_index >= len(self._log_lines):
                self._finish_fade_animation()
                return False
            elapsed += dt
            progress = 1.0 if duration <= 0 else min(1.0, elapsed / duration)
            self._log_lines[entry_index] = text if progress >= 1.0 else fade_kivy_markup(text, progress)
            self._render_log()
            if progress >= 1.0:
                self._finish_fade_animation()
                return False
            return True

        self._fade_animation_event = Clock.schedule_interval(advance_fade, self.NON_DIALOGUE_FADE_INTERVAL_SECONDS)

    def _finish_fade_animation(self) -> bool:
        entry_index = self._fade_animation_index
        if entry_index is None:
            return False
        event = self._fade_animation_event
        if event is not None:
            event.cancel()
        if 0 <= entry_index < len(self._log_lines):
            self._log_lines[entry_index] = self._fade_animation_markup
            self._render_log()
        done_event = self._fade_animation_done_event
        self._fade_animation_event = None
        self._fade_animation_index = None
        self._fade_animation_markup = ""
        self._fade_animation_done_event = None
        if done_event is not None:
            done_event.set()
        return True

    def _complete_log_append(self, done_event: Event | None, *, delay: float = 0.0) -> None:
        if done_event is None:
            return
        if delay <= 0:
            done_event.set()
            return

        def complete_after_delay(_dt) -> None:
            self._delayed_done_events = [
                (event, scheduled_event)
                for event, scheduled_event in self._delayed_done_events
                if event is not done_event
            ]
            done_event.set()

        scheduled = Clock.schedule_once(complete_after_delay, delay)
        self._delayed_done_events.append((done_event, scheduled))

    def _complete_delayed_log_appends(self) -> bool:
        if not self._delayed_done_events:
            return False
        delayed = self._delayed_done_events
        self._delayed_done_events = []
        for done_event, scheduled_event in delayed:
            scheduled_event.cancel()
            done_event.set()
        return True

    def mark_input_separator_pending(self) -> None:
        self._input_separator_pending = True

    def typing_wait_timeout(self, text: object) -> float:
        markup, animated = format_kivy_log_entry(text)
        return self.typing_wait_timeout_markup(markup, animated=animated)

    def typing_wait_timeout_markup(self, markup: str, *, animated: bool, fast_reveal: bool = False) -> float:
        visible_length = visible_markup_length(markup)
        if not markup or not self.typing_animation_enabled or not animated or visible_length <= 8:
            reveal_delay = kivy_non_dialogue_reveal_delay(
                markup,
                animated=animated,
                enabled=bool(markup and self.typing_animation_enabled),
                fast=fast_reveal,
                combat=self.combat_active(),
            )
            return max(8, reveal_delay + 1.0)
        typing_start = dialogue_typing_start_index(markup)
        seconds_per_character = self.TYPEWRITER_INTERVAL_SECONDS / max(1, self.TYPEWRITER_CHARS_PER_TICK)
        typed_text = visible_markup_text(markup)[typing_start:]
        pause_count = typed_text.count(".")
        estimated_seconds = (
            max(0, visible_length - typing_start) * seconds_per_character
            + pause_count * self.TYPEWRITER_FULLSTOP_PAUSE_SECONDS
            + self.TYPEWRITER_WAIT_PADDING_SECONDS
        )
        return max(8, estimated_seconds)

    def _append_log_entry(self, text: str) -> None:
        if text and self._input_separator_pending:
            if self._log_lines and self._log_lines[-1] != "":
                self._log_lines.append("")
            self._input_separator_pending = False
        self._log_lines.append(text)
        if len(self._log_lines) > self.MAX_LOG_ENTRIES:
            self._log_lines = self._log_lines[-self.MAX_LOG_ENTRIES :]
        self._render_log()

    def _render_log(self) -> None:
        self.log_label.text = "\n".join(self._log_lines).strip("\n")
        self._sync_log_viewport_height()
        Clock.schedule_once(lambda _dt: self._scroll_log_to_bottom(), 0)

    def _start_typing_next(self) -> None:
        if self._typing_current_markup is not None or not self._typing_queue:
            return
        markup, done_event = self._typing_queue.pop(0)
        self._typing_current_markup = markup
        self._typing_current_event = done_event
        self._typing_current_index = len(self._log_lines)
        self._typing_current_visible_text = visible_markup_text(markup)
        self._typing_total_characters = max(1, visible_markup_length(markup))
        self._typing_visible_characters = min(
            self._typing_total_characters,
            dialogue_typing_start_index(markup),
        )
        self._append_log_entry(reveal_kivy_markup(markup, self._typing_visible_characters))
        Clock.schedule_interval(self._advance_typing, self.TYPEWRITER_INTERVAL_SECONDS)

    def _advance_typing(self, _dt) -> bool:
        if self._typing_current_markup is None or self._typing_current_index is None:
            return False
        self._typing_visible_characters = min(
            self._typing_total_characters,
            self._typing_visible_characters + self.TYPEWRITER_CHARS_PER_TICK,
        )
        self._log_lines[self._typing_current_index] = reveal_kivy_markup(
            self._typing_current_markup,
            self._typing_visible_characters,
        )
        self._render_log()
        if self._typing_should_pause_on_fullstop():
            Clock.schedule_once(lambda _dt: self._resume_typing_after_pause(), self.TYPEWRITER_FULLSTOP_PAUSE_SECONDS)
            return False
        if self._typing_visible_characters < self._typing_total_characters:
            return True

        self._finish_typing_current()
        return False

    def _typing_should_pause_on_fullstop(self) -> bool:
        index = self._typing_visible_characters - 1
        return (
            0 <= index < len(self._typing_current_visible_text)
            and self._typing_current_visible_text[index] == "."
        )

    def _resume_typing_after_pause(self) -> None:
        if self._typing_current_markup is None or self._typing_current_index is None:
            return
        if self._typing_visible_characters >= self._typing_total_characters:
            self._finish_typing_current()
            return
        Clock.schedule_interval(self._advance_typing, self.TYPEWRITER_INTERVAL_SECONDS)

    def _finish_typing_current(self) -> None:
        if self._typing_current_markup is None or self._typing_current_index is None:
            return
        done_event = self._typing_current_event
        self._log_lines[self._typing_current_index] = self._typing_current_markup
        self._typing_current_markup = None
        self._typing_current_event = None
        self._typing_current_index = None
        self._typing_current_visible_text = ""
        self._render_log()
        if done_event is not None:
            done_event.set()
        Clock.schedule_once(lambda _dt: self._start_typing_next(), 0)

    def skip_current_typing_animation(self) -> bool:
        if self._typing_current_markup is None or self._typing_current_index is None:
            return False
        self._finish_typing_current()
        return True

    def _skip_combat_resource_animation(self) -> bool:
        if self._combat_resource_animation_event is None:
            return False
        self._snap_combat_resource_display_to_targets()
        return True

    def wait_for_animation_skip(self, duration: float) -> bool:
        duration = max(0.0, float(duration))
        if duration <= 0:
            return False
        self._animation_sleep_event.clear()
        self._animation_sleep_active = True
        try:
            return self._animation_sleep_event.wait(duration)
        finally:
            self._animation_sleep_active = False
            self._animation_sleep_event.clear()

    def skip_current_animation(self) -> bool:
        skipped = False
        skipped = self.skip_current_typing_animation() or skipped
        skipped = self._finish_fade_animation() or skipped
        skipped = self._complete_delayed_log_appends() or skipped
        skipped = self._skip_combat_resource_animation() or skipped
        skipped = self._skip_defeated_enemy_fade_animation() or skipped
        if self._animation_sleep_active:
            self._animation_sleep_event.set()
            skipped = True
        return skipped

    def _escape_should_quit_title_screen(self) -> bool:
        return bool(self._main_title_menu_active and self.bridge.waiting_for_input)

    def _handle_window_key_down(self, _window, key, scancode, codepoint, modifiers) -> bool:
        if self.is_fullscreen_shortcut(key, scancode, codepoint):
            self.toggle_kivy_fullscreen_from_shortcut()
            return True
        if self.is_console_menu_key(key, scancode, codepoint):
            if self._input_row_visible and not self._active_text_prompt_is_console:
                return False
            self.toggle_console_drawer()
            return True
        if self._save_browser_active:
            normalized = str(codepoint).strip().lower()
            if self.is_escape_key(key, scancode, codepoint):
                self.submit_direct("back")
                return True
            if normalized.isdigit():
                self.submit_direct(normalized)
                return True
            if normalized in {"b", "back"}:
                self.submit_direct("back")
                return True
        if self.bridge.waiting_for_input and not self._input_row_visible:
            normalized = str(codepoint).strip().lower()
            if normalized.isdigit():
                self.submit_direct(normalized)
                return True
        if self._side_panel_mode == "native_command":
            if self.is_escape_key(key, scancode, codepoint):
                self.close_side_command_panel()
                return True
            normalized = str(codepoint).strip().lower()
            modifier_set = {str(modifier).lower() for modifier in (modifiers or [])}
            if "ctrl" in modifier_set or "control" in modifier_set:
                shortcut_map = {
                    "j": "journal",
                    "i": "inventory",
                    "g": "gear",
                    "c": "camp",
                }
                command = shortcut_map.get(normalized)
                if command:
                    self.show_native_command_pane(command)
                    return True
            if normalized in {"b"}:
                self.command_workspace.go_back()
                return True
        if self.is_escape_key(key, scancode, codepoint):
            if self._escape_should_quit_title_screen():
                self.submit_direct("quit")
                return True
            self.toggle_command_bar()
            return True
        if key in (13, 271):
            return self.skip_current_animation()
        return False

    def _touch_hits_side_command_close_button(self, touch) -> bool:
        button = getattr(self, "side_command_close_button", None)
        if (
            button is None
            or self._side_panel_mode not in {"command", "native_command"}
            or self.side_command_header.disabled
            or self.side_command_header.opacity <= 0
        ):
            return False
        return bool(button.collide_point(*touch.pos))

    def _touch_hits_examine_close_button(self, touch) -> bool:
        button = getattr(self, "examine_close_button", None)
        if button is None or not self._examine_panel_visible or self.examine_shell.disabled:
            return False
        return bool(button.collide_point(*touch.pos))

    def on_touch_down(self, touch) -> bool:
        if self._touch_hits_side_command_close_button(touch):
            self.close_side_command_panel()
            return True
        if self._touch_hits_examine_close_button(touch):
            return super().on_touch_down(touch)
        if self.skip_current_animation():
            return True
        return super().on_touch_down(touch)

    def _scroll_log_to_bottom(self) -> None:
        self.log_scroll.scroll_y = 1 if self.log_viewport.height <= self.log_scroll.height + dp(1) else 0

    def _title_menu_header_markup(self, *, title: str, subtitle: str, intro_text: str) -> str:
        return "\n".join(
            [
                f"[size=38sp][b][color=#d8aa57]{escape_kivy_markup(title.upper())}[/color][/b][/size]",
                f"[size=16sp][color=#70d6cf]{escape_kivy_markup(subtitle)}[/color][/size]",
                "",
                "[size=15sp][color=#f0e7d1]A wet ledger lies open on the Greywake counter.[/color][/size]",
                f"[size=14sp][color=#9fb8aa]{escape_kivy_markup(intro_text)}[/color][/size]",
            ]
        )

    def show_title_menu(
        self,
        *,
        title: str,
        subtitle: str,
        intro_text: str,
        campaign_summary: str,
        save_summary: str,
        save_detail: str,
        audio_summary: str,
        presentation_summary: str,
        done_event: Event | None = None,
    ) -> None:
        self.hide_save_browser()
        self.update_combat_layout()
        self.close_examine_panel()
        self._clear_dice_tray()
        self._set_app_header_visible(False)
        self._title_menu_active = True
        self._title_menu_transition_active = False
        self._main_title_menu_active = True
        self._set_command_bar_visible(False, animate=False)
        self.title_label.text = title
        self.status_label.text = "Route desk open. Pick a tag, browse saves, or tune the table."
        self.prompt_label.text = ""
        self._active_text_prompt_is_console = False
        self._active_text_prompt_uses_input = False
        self._console_drawer_visible = False
        self._set_input_row_visible(False, animate=False)
        self.text_input.disabled = False
        self.text_input.text = ""
        self.text_input.hint_text = "Type a number, load, settings, or quit"
        self.apply_theme()
        self._sync_command_bar_visibility()
        self._set_title_card_markup(
            self._title_menu_header_markup(
                title=title,
                subtitle=subtitle,
                intro_text=intro_text,
            )
        )
        self._set_title_info_panel(
            self._title_menu_info_rows(
                campaign_summary=campaign_summary,
                save_summary=save_summary,
                save_detail=save_detail,
                audio_summary=audio_summary,
                presentation_summary=presentation_summary,
            )
        )
        self._log_lines = []
        self._render_log()
        Clock.schedule_once(lambda _dt: setattr(self.log_scroll, "scroll_y", 1), 0)
        self._complete_log_append(done_event)

    def title_screen_context_active(self) -> bool:
        game = self.active_game()
        title_shell_active = False
        if game is not None:
            kivy_title_shell_active = getattr(game, "kivy_title_shell_active", None)
            title_shell_active = (
                bool(kivy_title_shell_active())
                if callable(kivy_title_shell_active)
                else bool(getattr(game, "_at_title_screen", False))
            )
        return bool(
            game is not None
            and title_shell_active
            and not self.side_panel_allowed()
            and not self.combat_active()
        )

    def title_menu_active(self) -> bool:
        return (
            not self._save_browser_active
            and (self._title_menu_active or self.title_screen_context_active())
            and not self._title_menu_transition_active
        )

    def _selected_title_menu_label(self, value: str) -> str:
        raw = str(value).strip()
        if raw.isdigit():
            selected_index = int(raw) - 1
            if 0 <= selected_index < len(self.option_buttons):
                button_text = plain_combat_status_text(visible_markup_text(self.option_buttons[selected_index].text))
                label_lines = [line.strip() for line in button_text.splitlines() if line.strip()]
                if label_lines:
                    return re.sub(r"^\d+\s+", "", label_lines[0]).title()
        return raw.title() if raw else "Route"

    def _title_menu_selection_starts_game(self, value: str) -> bool:
        label = " ".join(self._selected_title_menu_label(value).lower().split())
        return label in {"continue", "load this save"}

    def begin_title_menu_transition(self, value: str) -> float:
        if not self._title_menu_active:
            return 0.0
        if not self._title_menu_selection_starts_game(value):
            return 0.0
        self._title_menu_transition_active = True
        selected_label = self._selected_title_menu_label(value)
        self.status_label.text = f"{selected_label} selected. Opening the table..."
        self.prompt_label.text = "[color=#d8aa57]Opening the route desk...[/color]"
        self.text_input.disabled = True
        self.send_button.disabled = True
        for index, button in enumerate(self.option_buttons, start=1):
            selected = str(value).strip() == str(index)
            button.disabled = True
            button.opacity = 1.0 if selected else 0.48
        return self.TITLE_MENU_TRANSITION_SECONDS

    def show_choice_prompt(
        self,
        prompt: str,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> None:
        self.update_combat_layout()
        self._title_menu_transition_active = False
        title_context = self.title_screen_context_active()
        self._title_menu_active = bool(
            (option_details or title_context)
            and not self.side_panel_allowed()
            and not self.combat_active()
        )
        main_title_prompt = (
            self._title_menu_active
            and bool(option_details)
            and plain_combat_status_text(visible_markup_text(prompt)).strip().lower() == "choose your route."
        )
        self._main_title_menu_active = bool(main_title_prompt)
        if not self._title_menu_active or (not title_context and not self._main_title_menu_active):
            self._set_title_card_markup("")
        self._set_app_header_visible(not self._main_title_menu_active)
        self.prompt_label.text = format_kivy_prompt_markup(prompt)
        self._active_text_prompt_is_console = False
        self._active_text_prompt_uses_input = False
        self._console_drawer_visible = False
        self._set_input_row_visible(False, animate=True)
        if self._title_menu_active:
            self.status_label.text = "Route desk open. Pick a tag, browse saves, or tune the table."
        elif self.combat_active():
            self.status_label.text = "Combat: story on the left, stats on the right, choices below."
        elif self.side_panel_allowed():
            self.status_label.text = "Story on the left. Party, maps, and command screens on the right."
        else:
            self.status_label.text = "Click a choice button or type a number / command."
        self._rebuild_options(options, option_details=option_details)
        self.text_input.hint_text = (
            "Type a number, back, load, settings, or quit"
            if self._title_menu_active
            else "Type a number or a command like help"
        )
        self._sync_command_bar_visibility()

    def show_text_prompt(self, prompt: str) -> None:
        self.update_combat_layout()
        self._title_menu_active = self.title_screen_context_active()
        if not self._title_menu_active:
            self._title_menu_transition_active = False
        self._main_title_menu_active = False
        self._set_title_card_markup("")
        self._set_app_header_visible(True)
        self.apply_theme()
        self.prompt_label.text = format_kivy_prompt_markup(prompt)
        console_prompt = self._prompt_is_console_drawer(prompt)
        self._active_text_prompt_uses_input = True
        self._active_text_prompt_is_console = console_prompt
        self._console_drawer_visible = console_prompt
        self._set_input_row_visible(True, animate=True)
        if self._title_menu_active:
            self.status_label.text = "Route desk open. Type a response or command."
        elif self.side_panel_allowed():
            self.status_label.text = "Type below. Command screens use the right panel."
        else:
            self.status_label.text = "Type a response below. Commands like save and journal still work."
        self._rebuild_options([])
        self.text_input.hint_text = "Type a console command, or back" if console_prompt else "Type your answer here"
        self._sync_command_bar_visibility()
        Clock.schedule_once(lambda _dt: self._focus_text_input(), 0)

    def clear_prompt(self) -> None:
        self.hide_save_browser()
        keep_title_mode = (
            self.title_screen_context_active()
            and self._title_menu_active
            and not self._title_menu_transition_active
        )
        if self._title_menu_active and not keep_title_mode:
            self._title_menu_active = False
            self._title_menu_transition_active = False
            self._main_title_menu_active = False
            self._set_title_card_markup("")
            self._set_app_header_visible(True)
            self.apply_theme()
        elif keep_title_mode:
            self._title_menu_active = True
            self.apply_theme()
        self.prompt_label.text = ""
        self._rebuild_options([])
        self.text_input.text = ""
        self.text_input.hint_text = "Waiting for the story..."
        self.text_input.disabled = False
        self.send_button.disabled = False
        self._active_text_prompt_is_console = False
        self._active_text_prompt_uses_input = False
        self._console_drawer_visible = False
        self._set_input_row_visible(False, animate=True)
        self._sync_command_bar_visibility()
        self.refresh_combat_panel()

    def finish_session(self, *, close_app: bool = False) -> None:
        self._title_menu_active = False
        self._title_menu_transition_active = False
        self._main_title_menu_active = False
        self._set_title_card_markup("")
        self._set_app_header_visible(True)
        self.apply_theme()
        self.status_label.text = "Session finished. Close the window or restart the game to play again."
        self.prompt_label.text = ""
        self._rebuild_options([])
        self._active_text_prompt_is_console = False
        self._active_text_prompt_uses_input = False
        self._console_drawer_visible = False
        self._set_input_row_visible(False, animate=True)
        self.text_input.disabled = True
        self._sync_command_bar_visibility()
        if close_app:
            Clock.schedule_once(lambda _dt: self.stop_running_app(), 0.05)

    def stop_running_app(self) -> None:
        app = App.get_running_app()
        if app is not None:
            app.stop()

    def _focus_text_input(self) -> None:
        self.text_input.focus = True

    def _option_grid_shape(self, option_count: int, *, detailed: bool = False) -> tuple[int, int]:
        if option_count <= 0:
            return (0, 1)
        if self._stack_story_choices_vertically():
            return (option_count, 1)
        if detailed and self._title_menu_active:
            if option_count <= 5:
                return (1, option_count)
            columns = 4 if option_count >= 8 else 3
            return (max(1, math.ceil(option_count / columns)), columns)
        if self._title_menu_active:
            columns = 1 if option_count <= 2 else 2
            return (max(1, math.ceil(option_count / columns)), columns)
        if detailed:
            return (option_count, 1)
        if option_count == 1:
            columns = 1
        elif option_count <= 4:
            columns = 2
        elif option_count <= 9:
            columns = 3
        else:
            columns = 4
        rows = max(1, math.ceil(option_count / columns))
        return (rows, columns)

    def _stack_story_choices_vertically(self) -> bool:
        if getattr(self, "_title_menu_active", False):
            return False
        try:
            if self.combat_active():
                return False
            game = self.active_game()
        except AttributeError:
            return False
        state = getattr(game, "state", None) if game is not None else None
        return bool(state is not None and getattr(state, "player", None) is not None)

    def _option_button_height(self, *, detailed: bool = False) -> int:
        if detailed and self._title_menu_active:
            return 72
        return 66 if detailed else self.OPTION_BUTTON_MIN_HEIGHT

    def _option_shell_height(self, rows: int, *, detailed: bool = False) -> float:
        if rows <= 0:
            return dp(44)
        if self._stack_story_choices_vertically():
            visible_rows = max(1, min(rows, self.OPTION_BUTTON_VISIBLE_ROWS))
            row_height = self._option_button_height(detailed=detailed)
            vertical_padding = 14
            gaps = max(0, visible_rows - 1) * self.OPTION_BUTTON_ROW_GAP
            return dp(vertical_padding + visible_rows * row_height + gaps)
        if detailed and self._title_menu_active:
            row_height = self._option_button_height(detailed=detailed)
            vertical_padding = 18
            gaps = max(0, rows - 1) * self.OPTION_BUTTON_ROW_GAP
            return dp(min(204, vertical_padding + rows * row_height + gaps))
        row_height = self._option_button_height(detailed=detailed)
        vertical_padding = 14
        gaps = max(0, rows - 1) * self.OPTION_BUTTON_ROW_GAP
        max_height = 340 if self._title_menu_active else (380 if detailed else 260)
        return dp(min(max_height, vertical_padding + rows * row_height + gaps))

    def _sync_options_area_layout(self, rows: int | None = None) -> None:
        if rows is None:
            rows = self._current_option_rows
        option_height = self._option_shell_height(rows, detailed=self._current_options_detailed)
        self.options_area.height = max(option_height, dp(44))
        self.options_shell.size_hint_x = 1
        self._sync_examine_panel_layout()
        self._sync_choice_scroll_indicator()

    def _choice_scroll_indicator_needed(self) -> bool:
        if not hasattr(self, "options_scroll") or not hasattr(self, "options_grid"):
            return False
        if not bool(getattr(self.options_scroll, "do_scroll_y", False)):
            return False
        return bool(self.options_grid.height > self.options_scroll.height + dp(2))

    def _set_choice_scroll_indicator_visible(self, visible: bool) -> None:
        if not hasattr(self, "choice_scroll_indicator"):
            return
        if not visible:
            Animation.cancel_all(self.choice_scroll_indicator, "opacity")
            self._choice_scroll_indicator_active = False
            self.choice_scroll_indicator.text = ""
            self.choice_scroll_indicator.width = 0
            self.choice_scroll_indicator.opacity = 0
            self.choice_scroll_indicator.disabled = True
            return
        self.choice_scroll_indicator.width = dp(self.CHOICE_SCROLL_INDICATOR_WIDTH)
        self.choice_scroll_indicator.disabled = False
        if self._choice_scroll_indicator_active:
            return
        self._choice_scroll_indicator_active = True
        self.choice_scroll_indicator.opacity = 1
        pulse = (
            Animation(opacity=0.38, duration=self.CHOICE_SCROLL_INDICATOR_PULSE_SECONDS)
            + Animation(opacity=1.0, duration=self.CHOICE_SCROLL_INDICATOR_PULSE_SECONDS)
        )
        pulse.repeat = True
        pulse.start(self.choice_scroll_indicator)

    def _sync_choice_scroll_indicator(self, *_args) -> None:
        if not self._choice_scroll_indicator_needed():
            self._set_choice_scroll_indicator_visible(False)
            return
        scroll_y = float(getattr(self.options_scroll, "scroll_y", 1.0) or 0.0)
        arrow = "↑" if scroll_y <= 0.02 else "↓"
        self.choice_scroll_indicator.text = f"[b]{arrow}[/b]"
        self._set_choice_scroll_indicator_visible(True)

    def _sync_examine_panel_layout(self) -> None:
        if self._examine_panel_visible:
            for parent in (self.left_column, self.options_area):
                if self.examine_shell.parent is parent:
                    parent.remove_widget(self.examine_shell)
            if self.examine_shell.parent is not self.combat_panel:
                if self.examine_shell.parent is not None:
                    self.examine_shell.parent.remove_widget(self.examine_shell)
                self.combat_panel.add_widget(self.examine_shell)
            self.examine_shell.size_hint_y = None
            self.examine_shell.height = dp(190)
            self.examine_shell.opacity = 1
            self.examine_shell.disabled = False
            self.examine_label._sync_text_size()
            self.examine_label._sync_height()
        else:
            for parent in (self.options_area, self.left_column, self.combat_panel):
                if self.examine_shell.parent is parent:
                    parent.remove_widget(self.examine_shell)
            self.examine_shell.opacity = 0
            self.examine_shell.disabled = True
            self.examine_shell.height = 0

    def _compact_option_markup(self, index: int, option: str, columns: int) -> str:
        plain = plain_combat_status_text(" ".join(strip_ansi(option).split()))
        number = f"[b][color=#facc15]{index}.[/color][/b] "
        tag_match = re.match(r"^(\[[^\]]+\])\s*(.*)$", plain)
        if tag_match is None:
            return f"{number}{escape_kivy_markup(plain)}"
        tag, rest = tag_match.groups()
        return (
            f"{number}[b][color=#facc15]{escape_kivy_markup(tag)}[/color][/b]"
            f" {escape_kivy_markup(rest)}"
        )

    def _detailed_option_markup(self, index: int, option: str, detail: str) -> str:
        title = plain_combat_status_text(" ".join(strip_ansi(option).split()))
        cleaned_detail = plain_combat_status_text(" ".join(strip_ansi(detail).split()))
        return (
            f"[b][color=#facc15]{index}.[/color][/b] [b]{escape_kivy_markup(title)}[/b]\n"
            f"[size=12sp][color=#b9ad91]{escape_kivy_markup(cleaned_detail)}[/color][/size]"
        )

    def _title_menu_option_label(self, option: str) -> str:
        plain = plain_combat_status_text(" ".join(strip_ansi(option).split())).strip()
        return self.TITLE_MENU_LABELS.get(plain.lower(), plain)

    def _title_menu_option_disabled(self, option: str, detail: str = "") -> bool:
        label = " ".join(self._title_menu_option_label(option).lower().split())
        if label != "continue":
            return False
        return "no save files" in " ".join(str(detail or "").lower().split())

    def _title_menu_option_caption(self, option: str, detail: str) -> str:
        plain = plain_combat_status_text(" ".join(strip_ansi(option).split())).strip().lower()
        if self._title_menu_option_disabled(option, detail):
            return "No save files"
        caption = self.TITLE_MENU_CAPTIONS.get(plain)
        if caption:
            return caption
        return plain_combat_status_text(" ".join(strip_ansi(detail).split())).strip()

    def _title_menu_option_markup(self, index: int, option: str, detail: str) -> str:
        label = self._title_menu_option_label(option)
        caption = self._title_menu_option_caption(option, detail)
        caption_markup = (
            f"\n[size=12sp]{escape_kivy_markup(caption)}[/size]"
            if caption
            else ""
        )
        return (
            f"[b][color=#d8aa57]{index:02d}[/color][/b] "
            f"[b]{escape_kivy_markup(label.upper())}[/b]"
            f"{caption_markup}"
        )

    def _title_menu_button_role(self, option: str, detail: str = "") -> str:
        label = " ".join(self._title_menu_option_label(option).lower().split())
        if self._title_menu_option_disabled(option, detail):
            return "title_disabled"
        back_labels = {
            "back",
            "return to lore categories",
            "back to this section",
            "previous page",
            "return to title screen",
            "return to title",
        }
        if label in back_labels or label.startswith("back to "):
            return "title_back"
        if label in {"continue", "new game"}:
            return "title_primary"
        if label in {"settings", "lore notes", "save files"}:
            return "title_utility" if label in {"settings", "lore notes"} else "title_choice"
        if label == "quit":
            return "title_quit"
        return "title_choice"

    def _choice_button_role(self, option: str) -> str:
        plain = plain_combat_status_text(" ".join(strip_ansi(option).split())).strip().lower()
        tag_match = re.match(r"^\[([^\]]+)\]", plain)
        if tag_match and tag_match.group(1) in {
            "action",
            "bonus action",
            "item",
            "social",
            "escape",
        }:
            return "combat_group"
        plain = re.sub(r"^\[[^\]]+\]\s*", "", plain).strip()
        if plain == "end turn":
            return "end_turn"
        if plain == "back":
            return "back"
        return "choice"

    def _sync_choice_button_text_size(self, button: Button, *_args) -> None:
        self._sync_button_text_size(button)

    def _rebuild_options(
        self,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> None:
        self._unbind_button_font_scaling(self.option_buttons)
        self.options_grid.clear_widgets()
        self.option_buttons = []
        detailed_options = bool(option_details)
        self._current_options_detailed = detailed_options
        rows, columns = self._option_grid_shape(len(options), detailed=detailed_options)
        stack_choices = self._stack_story_choices_vertically()
        button_halign = "left" if stack_choices else "center"
        button_height = dp(self._option_button_height(detailed=detailed_options))
        if hasattr(self, "options_scroll"):
            self.options_scroll.do_scroll_y = bool(stack_choices)
            self.options_scroll.bar_width = dp(5) if stack_choices else 0
        self.options_grid.size_hint_y = None if stack_choices else 1
        self._current_option_rows = rows
        self.options_grid.rows = rows or 1
        self.options_grid.cols = columns
        self._sync_options_area_layout(rows)
        for index, option in enumerate(options, start=1):
            detail = option_details.get(option, "") if option_details else ""
            if self._title_menu_active and detailed_options:
                button_text = self._title_menu_option_markup(index, option, detail)
            else:
                button_text = (
                    self._detailed_option_markup(index, option, detail)
                    if detail
                    else self._compact_option_markup(index, option, columns)
                )
            examine_text = f"{option}\n\n{detail}" if detail else option
            button = ExaminableButton(
                text=button_text,
                markup=True,
                examine_callback=lambda value=examine_text, option_index=index: self.show_option_examine(
                    value,
                    option_index,
                ),
                background_normal="",
                background_color=(0.20, 0.42, 0.34, 1),
                color=(1, 0.98, 0.94, 1),
                halign=button_halign,
                valign="middle",
                size_hint_y=None,
                height=button_height,
            )
            if self._title_menu_active and detailed_options:
                button._kivy_choice_role = self._title_menu_button_role(option, detail)
                button._kivy_fixed_font_size = True
                button.font_size = "15sp"
                self._apply_font(button, "mono")
                self._bind_fixed_button_alignment(button, halign=button_halign)
                if self._title_menu_option_disabled(option, detail):
                    button.disabled = True
                    button.opacity = 0.72
            else:
                button._kivy_choice_role = (
                    self._title_menu_button_role(option, detail)
                    if self._title_menu_active
                    else self._choice_button_role(option)
                )
                self._apply_font(button, "ui")
                self._sync_choice_button_text_size(button)
                self._bind_button_font_scaling(button)
            self._sync_choice_button_text_size(button)
            button.bind(on_release=lambda _btn, value=str(index): self.submit_direct(value))
            self.option_buttons.append(button)
            self.options_grid.add_widget(button)
        if hasattr(self, "options_scroll"):
            Clock.schedule_once(lambda _dt: setattr(self.options_scroll, "scroll_y", 1), 0)
        self.apply_theme()
        self._schedule_button_font_sync()

    def submit_direct(self, value: str) -> None:
        self.text_input.text = ""
        self.bridge.submit(value)

    def post_command_unavailable_message(self, reason: str) -> None:
        markup, _animated = format_kivy_log_entry(reason)
        self.mark_input_separator_pending()
        self.append_log(markup, animated=False, fast_reveal=True)

    def submit_command(self, value: str) -> None:
        reason = self._command_unavailable_reason(value)
        self._set_command_bar_visible(False, animate=True)
        if reason:
            self.post_command_unavailable_message(reason)
            return
        self.submit_direct(value)

    def submit_text(self) -> None:
        if self.skip_current_animation():
            return
        value = self.text_input.text.strip()
        if not value:
            return
        self.text_input.text = ""
        self.bridge.submit(value)


class ClickableDnDApp(App):
    def __init__(self, *, load_save: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.load_save = load_save

    def build(self) -> GameScreen:
        self.title = "Aethrune"
        try:
            Window.clearcolor = (0.93, 0.89, 0.80, 1)
            Window.size = (920, 860)
        except Exception:
            pass
        return GameScreen(load_save=self.load_save)

    def on_start(self) -> None:
        self.root.bridge.start()


def resolve_save_path(game: TextDnDGame, token: str) -> Path | None:
    raw_path = Path(token)
    candidates: list[Path] = []
    if raw_path.suffix.lower() == ".json":
        candidates.append(raw_path)
        candidates.append(game.save_dir / raw_path.name)
    else:
        candidates.append(game.save_path_for_slot_name(token))
        candidates.append(game.save_dir / f"{token}.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    normalized = token.strip().lower()
    for path in game.loadable_save_paths():
        if path.stem.lower() == normalized:
            return path
        if path.name.lower() == normalized:
            return path
        if game.save_display_label(path).lower() == normalized:
            return path
    return None


def run_gui(*, load_save: str | None = None) -> int:
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]]
    try:
        ClickableDnDApp(load_save=load_save).run()
    finally:
        sys.argv = original_argv
    return 0
