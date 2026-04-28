from __future__ import annotations

import os
import json
import math
from pathlib import Path
from queue import Queue
import re
import sys
from threading import Event, Thread
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_FILELOG", "1")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from .game import TextDnDGame
from .gameplay.constants import MENU_PAGE_SIZE
from .gameplay.magic_points import current_magic_points, maximum_magic_points
from .ui.colors import strip_ansi
from .ui.kivy_markup import (
    ansi_to_kivy_markup,
    dialogue_typing_start_index,
    escape_kivy_markup,
    fade_kivy_markup,
    format_kivy_log_entry,
    kivy_non_dialogue_reveal_delay,
    plain_combat_status_text,
    reveal_kivy_markup,
    should_buffer_kivy_non_dialogue_output,
    visible_markup_length,
    visible_markup_text,
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
        Clock.schedule_once(lambda _dt: self.screen.finish_session())

    def post_output(self, text: object = "") -> None:
        markup, animated = format_kivy_log_entry(text)
        if should_buffer_kivy_non_dialogue_output(
            markup,
            animated=animated,
            source_text=text,
            enabled=self.screen.typing_animation_enabled,
        ):
            self._pending_non_dialogue_markups.append(markup)
            self._pending_non_dialogue_fast_reveal = (
                self._pending_non_dialogue_fast_reveal or self._fast_reveal_until_next_prompt
            )
            return
        self.flush_pending_non_dialogue_output()
        self.post_preformatted_output(markup, animated=animated, fast_reveal=self._fast_reveal_until_next_prompt)

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

    def request_choice(self, prompt: str, options: list[str]) -> str:
        self.flush_pending_non_dialogue_output()
        self._fast_reveal_until_next_prompt = False
        self.waiting_for_input = True
        Clock.schedule_once(lambda _dt: self.screen.show_choice_prompt(prompt, options))
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
        Clock.schedule_once(lambda _dt: self.screen.clear_prompt())
        self._responses.put(value)

    def show_combat_actor(self, actor) -> None:
        name = "" if actor is None else str(getattr(actor, "name", ""))
        Clock.schedule_once(lambda _dt: self.screen.set_active_combat_actor(name))

    def set_kivy_dark_mode(self, enabled: bool) -> None:
        Clock.schedule_once(lambda _dt: self.screen.set_kivy_dark_mode_enabled(enabled))


class ClickableTextDnDGame(TextDnDGame):
    KIVY_DARK_MODE_SETTING_KEY = "kivy_dark_mode_enabled"

    def __init__(self, bridge: ClickableGameBridge, *, save_dir: Path):
        self.bridge = bridge
        super().__init__(
            input_fn=lambda _prompt="": "",
            output_fn=self.bridge.post_output,
            save_dir=save_dir,
            animate_dice=False,
            pace_output=False,
            type_dialogue=False,
            staggered_reveals=False,
        )
        self._kivy_dark_mode_preference = bool(
            getattr(self, "_loaded_kivy_dark_mode_preference", self.bridge.screen.kivy_dark_mode_enabled)
        )
        self.bridge.set_kivy_dark_mode(self._kivy_dark_mode_preference)

    def load_persisted_settings(self) -> dict[str, object]:
        settings = super().load_persisted_settings()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return settings
        if isinstance(data, dict) and self.KIVY_DARK_MODE_SETTING_KEY in data:
            self._loaded_kivy_dark_mode_preference = bool(data[self.KIVY_DARK_MODE_SETTING_KEY])
        return settings

    def current_settings_payload(self) -> dict[str, object]:
        payload = super().current_settings_payload()
        payload[self.KIVY_DARK_MODE_SETTING_KEY] = bool(
            getattr(self, "_kivy_dark_mode_preference", self.bridge.screen.kivy_dark_mode_enabled)
        )
        return payload

    def music_output_allows_playback(self) -> bool:
        return True

    def say(self, text: str, *, typed: bool = False) -> None:
        if not text:
            self.output_fn("")
            return
        for paragraph in str(text).split("\n"):
            self.output_fn(paragraph)

    def banner(self, title: str) -> None:
        self.output_fn("")
        self.output_fn(f"=== {title} ===")

    def choose_title_menu(
        self,
        title: str,
        subtitle: str,
        intro_text: str,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> int:
        self.banner(title)
        self.say(subtitle)
        self.say("Frontier roads. Hard bargains. Consequences that travel.")
        self.say(intro_text)
        if option_details:
            self.output_fn("")
            for option in options:
                detail = option_details.get(option)
                if detail:
                    self.output_fn(f"{option}: {detail}")
        return self.choose_with_display_mode(
            "What would you like to do?",
            options,
            allow_meta=True,
            show_hud=False,
        )

    def ask_text(self, prompt: str) -> str:
        while True:
            value = self.bridge.request_text(f"{prompt}:").strip()
            if self.handle_meta_command(value):
                continue
            if value:
                return value
            self.say("Please enter a value.")

    def read_input(self, prompt: str) -> str:
        return self.bridge.request_text(prompt)

    def set_kivy_dark_mode_enabled(self, enabled: bool) -> None:
        self._kivy_dark_mode_preference = bool(enabled)
        self.bridge.set_kivy_dark_mode(self._kivy_dark_mode_preference)
        self.persist_settings()
        self.say(f"Kivy dark mode {'enabled' if self._kivy_dark_mode_preference else 'disabled'}.")

    def toggle_kivy_dark_mode(self) -> None:
        self.set_kivy_dark_mode_enabled(not getattr(self, "_kivy_dark_mode_preference", True))

    def open_settings_menu(self) -> None:
        while True:
            music_available = bool(getattr(self, "_music_assets_ready", False))
            options = [
                f"Toggle sound effects ({self.settings_toggle_label(getattr(self, 'sound_effects_enabled', False))})",
                (
                    f"Toggle music ({self.settings_toggle_label(getattr(self, 'music_enabled', False), unavailable=not music_available)})"
                ),
                f"Dice animation style ({self.dice_animation_mode_label()})",
                f"Difficulty ({self.difficulty_mode_label()})",
                f"Toggle typed dialogue and narration ({self.settings_toggle_label(getattr(self, '_typed_dialogue_preference', self.type_dialogue))})",
                f"Toggle pacing pauses ({self.settings_toggle_label(getattr(self, '_pacing_pauses_preference', self.pace_output))})",
                f"Toggle staggered option reveals ({self.settings_toggle_label(getattr(self, '_staggered_reveals_preference', getattr(self, 'staggered_reveals_enabled', False)))})",
                f"Toggle Kivy dark mode ({self.settings_toggle_label(getattr(self, '_kivy_dark_mode_preference', True))})",
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
                self.open_dice_animation_settings()
                continue
            if choice == 4:
                self.open_difficulty_settings()
                continue
            if choice == 5:
                self.toggle_typed_dialogue()
                continue
            if choice == 6:
                self.toggle_pacing_pauses()
                continue
            if choice == 7:
                self.toggle_staggered_reveals()
                continue
            if choice == 8:
                self.toggle_kivy_dark_mode()
                continue
            return

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
            indexed, _sections = self.group_combat_options(options)
            ordered_indexes = sorted(indexed)
            display_options = [self.format_option_text(indexed[index]) for index in ordered_indexes]
            raw = self.bridge.request_choice(prompt, display_options).strip()
            if self.handle_meta_command(raw):
                continue
            if raw.isdigit():
                selected = int(raw)
                if 1 <= selected <= len(ordered_indexes):
                    return indexed[ordered_indexes[selected - 1]]
            self.say("Please choose one of the listed combat options.")

    def choose_with_display_mode(
        self,
        prompt: str,
        options: list[str],
        *,
        allow_meta: bool = True,
        staggered: bool = False,
        show_hud: bool = True,
        sticky_trailing_options: int = 0,
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
            raw = self.bridge.request_choice(prompt, display_options).strip()
            if self.handle_meta_command(raw):
                continue
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= len(options):
                    return value
            self.say("Please choose one of the listed options.")


class GameScreen(BoxLayout):
    MAX_LOG_ENTRIES = 900
    TYPEWRITER_INTERVAL_SECONDS = 0.035
    TYPEWRITER_CHARS_PER_TICK = 1
    TYPEWRITER_FULLSTOP_PAUSE_SECONDS = 0.5
    TYPEWRITER_WAIT_PADDING_SECONDS = 2.0
    NON_DIALOGUE_FADE_INTERVAL_SECONDS = 0.05
    COMBAT_RESOURCE_ANIMATION_INTERVAL_SECONDS = 0.08
    COMBAT_RESOURCE_ANIMATION_MAX_STEPS = 12
    SINGLE_TEXT_WINDOW_FONT_SIZE = "20sp"
    SPLIT_TEXT_WINDOW_FONT_SIZE = "15sp"
    OPTION_BUTTON_MIN_HEIGHT = 30
    OPTION_BUTTON_ROW_GAP = 4
    COMMANDS = [
        "help",
        "load",
        "map",
        "journal",
        "party",
        "inventory",
        "gear",
        "camp",
        "save",
        "settings",
        "quit",
    ]
    COMMAND_LABELS = {
        "help": "Help",
        "load": "Load",
        "map": "Map",
        "journal": "Journal",
        "party": "Party",
        "inventory": "Inv",
        "gear": "Gear",
        "camp": "Camp",
        "save": "Save",
        "settings": "Settings",
        "quit": "Quit",
    }
    KIVY_DARK_MODE_SETTING_KEY = ClickableTextDnDGame.KIVY_DARK_MODE_SETTING_KEY
    DARK_THEME = {
        "window": (0.055, 0.050, 0.045, 1),
        "header": (0.13, 0.10, 0.07, 1),
        "panel": (0.08, 0.07, 0.055, 1),
        "options": (0.11, 0.13, 0.10, 1),
        "combat": (0.075, 0.075, 0.085, 1),
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
        "choice_bg": (0.20, 0.42, 0.34, 1),
        "choice_text": (1, 0.98, 0.94, 1),
    }
    LIGHT_THEME = {
        "window": (0.93, 0.89, 0.80, 1),
        "header": (0.74, 0.57, 0.31, 1),
        "panel": (0.97, 0.93, 0.82, 1),
        "options": (0.89, 0.82, 0.66, 1),
        "combat": (0.91, 0.86, 0.75, 1),
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
        "choice_bg": (0.36, 0.58, 0.47, 1),
        "choice_text": (0.06, 0.08, 0.06, 1),
    }

    def __init__(self, *, load_save: str | None = None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(6), **kwargs)
        self._log_lines: list[str] = []
        self._typing_queue: list[tuple[str, Event | None]] = []
        self._typing_current_markup: str | None = None
        self._typing_current_event: Event | None = None
        self._typing_current_index: int | None = None
        self._typing_current_visible_text = ""
        self._typing_visible_characters = 0
        self._typing_total_characters = 0
        self._combat_resource_display_values: dict[tuple[int, str], int] = {}
        self._combat_resource_targets: dict[tuple[int, str], int] = {}
        self._combat_resource_animation_event = None
        self._active_combat_actor_name = ""
        self._combat_mode_enabled = False
        self.kivy_dark_mode_enabled = self.load_kivy_dark_mode_setting()
        self.command_buttons: list[Button] = []
        self.option_buttons: list[Button] = []
        self.typing_animation_enabled = True
        self.bridge = ClickableGameBridge(self, load_save=load_save)
        self._build_ui()
        Window.bind(on_key_down=self._handle_window_key_down)

    def load_kivy_dark_mode_setting(self) -> bool:
        settings_path = Path.cwd() / "saves" / "settings.json"
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return True
        if not isinstance(data, dict):
            return True
        return bool(data.get(self.KIVY_DARK_MODE_SETTING_KEY, True))

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
        self.log_label = WrappedLabel(
            text="[color=#8f7d62]Launching...[/color]",
            markup=True,
            color=(0.92, 0.86, 0.74, 1),
            font_size=self.SINGLE_TEXT_WINDOW_FONT_SIZE,
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._apply_font(self.log_label, "story")
        self.log_scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        self.log_viewport = BoxLayout(orientation="vertical", size_hint_y=None)
        self.log_spacer = Widget()
        self.log_viewport.add_widget(self.log_label)
        self.log_viewport.add_widget(self.log_spacer)
        self.log_scroll.bind(size=self._sync_log_viewport_height)
        self.log_label.bind(height=self._sync_log_viewport_height)
        self.log_scroll.add_widget(self.log_viewport)
        self.log_shell.add_widget(self.log_scroll)
        self.left_column.add_widget(self.log_shell)

        self.prompt_label = WrappedLabel(
            text="",
            markup=True,
            color=(0.94, 0.78, 0.36, 1),
            font_size="15sp",
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
        )
        self._apply_font(self.prompt_label, "ui")

        self.options_shell = PanelBox(
            orientation="vertical",
            size_hint_y=None,
            height=dp(142),
            padding=[dp(6), dp(6), dp(6), dp(6)],
            background_color=(0.11, 0.13, 0.10, 1),
            radius=6,
        )
        self.options_grid = GridLayout(cols=1, spacing=dp(self.OPTION_BUTTON_ROW_GAP), size_hint=(1, 1))
        self.options_shell.add_widget(self.options_grid)

        self.combat_panel = PanelBox(
            orientation="vertical",
            size_hint_x=0.5,
            padding=[dp(8), dp(8), dp(8), dp(8)],
            background_color=(0.075, 0.075, 0.085, 1),
            radius=6,
        )
        self.combat_stats_label = WrappedLabel(
            text="",
            markup=True,
            color=(0.92, 0.86, 0.74, 1),
            font_size="15sp",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._apply_font(self.combat_stats_label, "mono")
        self.combat_stats_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self.combat_stats_scroll.add_widget(self.combat_stats_label)
        self.combat_panel.add_widget(self.combat_stats_scroll)
        self.add_widget(self.main_body)
        self.add_widget(self.prompt_label)
        self.add_widget(self.options_shell)

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
        )
        self._apply_font(self.send_button, "ui")
        self.send_button.bind(on_release=lambda *_args: self.submit_text())
        self.input_row.add_widget(self.send_button)
        self.add_widget(self.input_row)

        self.commands = GridLayout(
            rows=1,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(34),
        )
        for command in self.COMMANDS:
            button = Button(
                text=self.COMMAND_LABELS.get(command, command.title()),
                background_normal="",
                background_color=(0.48, 0.36, 0.18, 1),
                color=(1, 0.94, 0.78, 1),
                font_size="12sp",
            )
            self._apply_font(button, "ui")
            button.bind(on_release=lambda _btn, value=command: self.submit_direct(value))
            self.command_buttons.append(button)
            self.commands.add_widget(button)
        self.add_widget(self.commands)
        self._apply_text_window_mode(combat_active=False)
        self.apply_theme()

    def _sync_status_label(self, instance: Label, _value) -> None:
        instance.text_size = (instance.width, None)

    def set_kivy_dark_mode_enabled(self, enabled: bool) -> None:
        self.kivy_dark_mode_enabled = bool(enabled)
        self.apply_theme()

    def apply_theme(self) -> None:
        theme = self.theme
        try:
            Window.clearcolor = theme["window"]
        except Exception:
            pass
        for panel, key in (
            (self.header, "header"),
            (self.log_shell, "panel"),
            (self.options_shell, "options"),
            (self.combat_panel, "combat"),
        ):
            panel.set_background_color(theme[key])
        self.title_label.color = theme["title"]
        self.status_label.color = theme["status"]
        self.log_label.color = theme["text"]
        self.prompt_label.color = theme["prompt"]
        self.combat_stats_label.color = theme["text"]
        self.text_input.background_color = theme["input_bg"]
        self.text_input.foreground_color = theme["input_text"]
        self.text_input.cursor_color = theme["cursor"]
        self.send_button.background_color = theme["send_bg"]
        self.send_button.color = theme["send_text"]
        for button in self.command_buttons:
            button.background_color = theme["command_bg"]
            button.color = theme["command_text"]
        for button in self.option_buttons:
            button.background_color = theme["choice_bg"]
            button.color = theme["choice_text"]

    def _sync_log_viewport_height(self, *_args) -> None:
        self.log_viewport.height = max(self.log_scroll.height, self.log_label.height)

    def active_game(self) -> "ClickableTextDnDGame | None":
        return self.bridge.game

    def set_active_combat_actor(self, name: str) -> None:
        self._active_combat_actor_name = name
        self.refresh_combat_panel()

    def combat_active(self) -> bool:
        game = self.active_game()
        return bool(game is not None and getattr(game, "_in_combat", False))

    def update_combat_layout(self) -> None:
        active = self.combat_active()
        if active == self._combat_mode_enabled:
            self._apply_text_window_mode(combat_active=active)
            if active:
                self.refresh_combat_panel()
            return
        self._combat_mode_enabled = active
        self._apply_text_window_mode(combat_active=active)
        if active:
            self.left_column.size_hint_x = 0.5
            if self.combat_panel.parent is None:
                self.main_body.add_widget(self.combat_panel)
            self.status_label.text = "Combat: story on the left, stats on the right, choices below."
            self.refresh_combat_panel()
            return
        if self.combat_panel.parent is self.main_body:
            self.main_body.remove_widget(self.combat_panel)
        self.left_column.size_hint_x = 1
        self._active_combat_actor_name = ""
        self._clear_combat_resource_animation()
        self.combat_stats_label.text = ""

    def _apply_text_window_mode(self, *, combat_active: bool) -> None:
        self.log_label.font_size = (
            self.SPLIT_TEXT_WINDOW_FONT_SIZE if combat_active else self.SINGLE_TEXT_WINDOW_FONT_SIZE
        )
        self.log_label.halign = "left"
        self.log_label._sync_text_size()
        self.log_label._sync_height()
        self._sync_log_viewport_height()

    def refresh_combat_panel(self) -> None:
        if not self.combat_active():
            self._clear_combat_resource_animation()
            return
        self._sync_combat_resource_targets()
        self._render_combat_panel()

    def _render_combat_panel(self, *, scroll_to_top: bool = True) -> None:
        self.combat_stats_label.text = self.build_combat_stats_markup()
        if not scroll_to_top:
            return
        Clock.schedule_once(lambda _dt: setattr(self.combat_stats_scroll, "scroll_y", 1), 0)

    def _clear_combat_resource_animation(self) -> None:
        event = self._combat_resource_animation_event
        if event is not None:
            event.cancel()
        self._combat_resource_animation_event = None
        self._combat_resource_display_values.clear()
        self._combat_resource_targets.clear()

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
            if getattr(combatant, "dead", False):
                continue
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
            self._combat_resource_display_values.setdefault(key, current)
            self._combat_resource_targets[key] = current

        for key in list(self._combat_resource_display_values):
            if key not in active_keys:
                del self._combat_resource_display_values[key]
        for key in list(self._combat_resource_targets):
            if key not in active_keys:
                del self._combat_resource_targets[key]

        if any(
            self._combat_resource_display_values.get(key, target) != target
            for key, target in self._combat_resource_targets.items()
        ):
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

    def _advance_combat_resource_animation(self, _dt) -> bool:
        if not self.combat_active():
            self._clear_combat_resource_animation()
            return False
        changed = False
        remaining = False
        for key, target in list(self._combat_resource_targets.items()):
            current = self._combat_resource_display_values.get(key, target)
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
        maximum = max(1, int(maximum))
        current = max(0, min(int(current), maximum))
        filled = max(0, min(width, int(round((current / maximum) * width))))
        empty = width - filled
        resolved_color = color or self.health_color(current, maximum)
        return f"|[color=#{resolved_color}]{'#' * filled}[/color][color=#3b3428]{'-' * empty}[/color]| {current}/{maximum}"

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

    def combatant_resource_text(self, combatant) -> str:
        resources = getattr(combatant, "resources", {}) or {}
        maximums = getattr(combatant, "max_resources", {}) or {}
        parts: list[str] = []
        for key in sorted(set(resources) | set(maximums)):
            current = int(resources.get(key, 0) or 0)
            maximum = int(maximums.get(key, 0) or 0)
            if current <= 0 and maximum <= 0:
                continue
            label = key.replace("_", " ").title()
            parts.append(f"{label} {current}/{maximum}" if maximum else f"{label} {current}")
        return " | ".join(parts)

    def combatant_markup(self, game: "ClickableTextDnDGame", combatant, *, enemy: bool) -> str:
        raw_name = str(getattr(combatant, "name", "Unknown"))
        public_name = game.public_character_name(raw_name) if hasattr(game, "public_character_name") else raw_name
        name_color = "f87171" if enemy else "67e8f9"
        if raw_name == self._active_combat_actor_name:
            name_color = "facc15"
        current_hp = int(getattr(combatant, "current_hp", 0) or 0)
        hp = self.stat_bar_markup(
            self._displayed_combat_resource_value(combatant, "hp", current_hp),
            getattr(combatant, "max_hp", 1),
        )
        ac = getattr(combatant, "armor_class", "?")
        temp = f" temp {combatant.temp_hp}" if getattr(combatant, "temp_hp", 0) else ""
        defense_summary = ""
        combat_defense_summary = getattr(game, "combat_defense_summary", None)
        if callable(combat_defense_summary):
            defense_summary = f" | {strip_ansi(combat_defense_summary(combatant))}"
        status = " DEAD" if getattr(combatant, "dead", False) else " DOWN" if getattr(combatant, "current_hp", 0) <= 0 else ""
        lines = [
            f"[b][color=#{name_color}]{escape_kivy_markup(public_name)}[/color][/b]"
            f" [size=14sp][color=#b8a98d]Lv {getattr(combatant, 'level', '?')} AC {ac}{defense_summary}{temp}{status}[/color][/size]",
            f"[size=14sp]HP: {hp}[/size]",
        ]
        max_mp = maximum_magic_points(combatant)
        if max_mp > 0:
            current_mp = current_magic_points(combatant)
            displayed_mp = self._displayed_combat_resource_value(combatant, "mp", current_mp)
            lines.append(f"[size=14sp]MP: {self.stat_bar_markup(displayed_mp, max_mp, color='60a5fa')}[/size]")
        resources = self.combatant_resource_text(combatant)
        if resources:
            lines.append(f"[size=14sp][color=#d6c59a]{escape_kivy_markup(resources)}[/color][/size]")
        conditions = self.combatant_conditions_text(game, combatant)
        if conditions:
            lines.append(f"[size=14sp][color=#d8b4fe]{escape_kivy_markup(conditions)}[/color][/size]")
        return "\n".join(lines)

    def build_combat_group_markup(self, title: str, combatants: list, *, enemy: bool) -> str:
        game = self.active_game()
        if game is None:
            return ""
        living = [combatant for combatant in combatants if not getattr(combatant, "dead", False)]
        title_color = "f87171" if enemy else "67e8f9"
        lines = [f"[b][color=#{title_color}]{title}[/color][/b]"]
        if not living:
            lines.append("[color=#8f7d62]None standing.[/color]")
        else:
            for combatant in living:
                lines.append(self.combatant_markup(game, combatant, enemy=enemy))
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
        return "\n\n".join(
            [
                header,
                self.build_combat_group_markup("Party", heroes, enemy=False),
                self.build_combat_group_markup("Enemies", enemies, enemy=True),
            ]
        )

    def append_output(self, text: object, *, done_event: Event | None = None) -> None:
        self.update_combat_layout()
        markup, animated = format_kivy_log_entry(text)
        self.append_log(markup, done_event=done_event, animated=animated)

    def append_log(
        self,
        text: str,
        *,
        done_event: Event | None = None,
        animated: bool = True,
        fast_reveal: bool = False,
    ) -> None:
        if not text or not self.typing_animation_enabled or not animated or visible_markup_length(text) <= 8:
            delay = kivy_non_dialogue_reveal_delay(
                text,
                animated=animated,
                enabled=bool(text and self.typing_animation_enabled),
                fast=fast_reveal,
            )
            if delay > 0:
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

        def advance_fade(dt) -> bool:
            nonlocal elapsed
            if entry_index >= len(self._log_lines):
                self._complete_log_append(done_event)
                return False
            elapsed += dt
            progress = 1.0 if duration <= 0 else min(1.0, elapsed / duration)
            self._log_lines[entry_index] = text if progress >= 1.0 else fade_kivy_markup(text, progress)
            self._render_log()
            if progress >= 1.0:
                self._complete_log_append(done_event)
                return False
            return True

        Clock.schedule_interval(advance_fade, self.NON_DIALOGUE_FADE_INTERVAL_SECONDS)

    def _complete_log_append(self, done_event: Event | None, *, delay: float = 0.0) -> None:
        if done_event is None:
            return
        if delay <= 0:
            done_event.set()
            return
        Clock.schedule_once(lambda _dt: done_event.set(), delay)

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

    def _handle_window_key_down(self, _window, key, _scancode, _codepoint, _modifiers) -> bool:
        if key in (13, 271):
            return self.skip_current_typing_animation()
        return False

    def _scroll_log_to_bottom(self) -> None:
        self.log_scroll.scroll_y = 1 if self.log_viewport.height <= self.log_scroll.height + dp(1) else 0

    def show_choice_prompt(self, prompt: str, options: list[str]) -> None:
        self.update_combat_layout()
        self.prompt_label.text = ansi_to_kivy_markup(prompt)
        if self.combat_active():
            self.status_label.text = "Combat: story on the left, stats on the right, choices below."
        else:
            self.status_label.text = "Click a choice button or type a number / command."
        self._rebuild_options(options)
        self.text_input.hint_text = "Type a number or a command like help"
        Clock.schedule_once(lambda _dt: self._focus_text_input(), 0)

    def show_text_prompt(self, prompt: str) -> None:
        self.update_combat_layout()
        self.prompt_label.text = ansi_to_kivy_markup(prompt)
        self.status_label.text = "Type a response below. Commands like save and journal still work."
        self._rebuild_options([])
        self.text_input.hint_text = "Type your answer here"
        Clock.schedule_once(lambda _dt: self._focus_text_input(), 0)

    def clear_prompt(self) -> None:
        self.prompt_label.text = ""
        self._rebuild_options([])
        self.text_input.text = ""
        self.text_input.hint_text = "Waiting for the story..."
        self.refresh_combat_panel()

    def finish_session(self) -> None:
        self.status_label.text = "Session finished. Close the window or restart the game to play again."
        self.prompt_label.text = ""
        self._rebuild_options([])
        self.text_input.disabled = True

    def _focus_text_input(self) -> None:
        self.text_input.focus = True

    def _option_grid_shape(self, option_count: int) -> tuple[int, int]:
        if option_count <= 0:
            return (0, 1)
        if option_count <= 4:
            columns = 1
        elif option_count <= 12:
            columns = 2
        elif option_count <= 24:
            columns = 3
        else:
            columns = 4
        rows = max(1, math.ceil(option_count / columns))
        return (rows, columns)

    def _option_shell_height(self, rows: int) -> float:
        if rows <= 0:
            return dp(36)
        row_height = self.OPTION_BUTTON_MIN_HEIGHT
        vertical_padding = 12
        gaps = max(0, rows - 1) * self.OPTION_BUTTON_ROW_GAP
        return dp(min(178, vertical_padding + rows * row_height + gaps))

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

    def _sync_choice_button_text_size(self, button: Button, *_args) -> None:
        button.text_size = (max(0, button.width - dp(12)), max(0, button.height - dp(4)))

    def _rebuild_options(self, options: list[str]) -> None:
        self.options_grid.clear_widgets()
        self.option_buttons = []
        rows, columns = self._option_grid_shape(len(options))
        self.options_grid.rows = rows or 1
        self.options_grid.cols = columns
        self.options_shell.height = self._option_shell_height(rows)
        font_size = "15sp" if columns >= 3 else "16sp"
        for index, option in enumerate(options, start=1):
            button = Button(
                text=self._compact_option_markup(index, option, columns),
                markup=True,
                background_normal="",
                background_color=(0.20, 0.42, 0.34, 1),
                color=(1, 0.98, 0.94, 1),
                font_size=font_size,
                halign="left",
                valign="middle",
            )
            self._apply_font(button, "ui")
            button.bind(size=lambda instance, _value: self._sync_choice_button_text_size(instance))
            self._sync_choice_button_text_size(button)
            button.bind(on_release=lambda _btn, value=str(index): self.submit_direct(value))
            self.option_buttons.append(button)
            self.options_grid.add_widget(button)
        self.apply_theme()

    def submit_direct(self, value: str) -> None:
        self.text_input.text = ""
        self.bridge.submit(value)

    def submit_text(self) -> None:
        if self.skip_current_typing_animation():
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
