from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import textwrap

from ..models import GameState
from ..ui.colors import ANSI_RE, colorize, rarity_color, rich_style_name, strip_ansi
from ..ui.rich_render import Columns, Group, Panel, RICH_AVAILABLE, Table, Text, box, render_rich_lines, text_from_ansi
from .constants import MENU_PAGE_SIZE


class GameIOMixin:
    def style_text(self, text: object, color: str) -> str:
        return colorize(text, color)

    def style_damage(self, amount: int) -> str:
        return self.style_text(amount, "light_red")

    def style_healing(self, amount: int) -> str:
        return self.style_text(amount, "light_green")

    def style_skill_label(self, skill: str) -> str:
        return self.style_text(skill, "light_yellow")

    def style_rarity_text(self, text: str, rarity: str) -> str:
        return self.style_text(text, rarity_color(rarity))

    def style_name(self, subject) -> str:
        if not hasattr(subject, "name"):
            return str(subject)
        name = subject.name
        if self.state is not None and subject is self.state.player:
            return self.style_text(name, "aqua")
        tags = set(getattr(subject, "tags", []))
        if "enemy" in tags:
            return self.style_text(name, "light_red")
        if getattr(subject, "companion_id", "") or "companion" in tags:
            return self.style_text(name, "light_aqua")
        return name

    def format_option_text(self, option: str) -> str:
        match = re.match(r"^(\[[^\]]+\])(\s*)(.*)$", option)
        if match is None:
            return option
        tag, spacing, rest = match.groups()
        return f"{self.style_text(tag, 'light_yellow')}{spacing}{rest}"

    def rich_enabled(self) -> bool:
        return RICH_AVAILABLE and all(component is not None for component in (Group, Panel, Text, box))

    def should_use_rich_ui(self) -> bool:
        return self.rich_enabled() and bool(getattr(self, "_interactive_output", False))

    def rich_console_width(self) -> int:
        fallback = 108 if getattr(self, "_interactive_output", False) else 100
        try:
            return max(88, min(shutil.get_terminal_size((fallback, 30)).columns, 132))
        except OSError:
            return fallback

    def emit_rich(self, renderable, *, width: int | None = None) -> bool:
        if not self.rich_enabled():
            return False
        rendered_lines = render_rich_lines(
            renderable,
            width=width or self.rich_console_width(),
            force_terminal=getattr(self, "_interactive_output", False),
        )
        if not rendered_lines:
            return False
        for line in rendered_lines:
            self.output_fn(line)
        return True

    def rich_text(self, text: object, color: str | None = None, *, bold: bool = False, dim: bool = False):
        content = strip_ansi(str(text))
        if not self.rich_enabled():
            return content
        style_bits: list[str] = []
        if color is not None:
            style_bits.append(rich_style_name(color))
        if bold:
            style_bits.append("bold")
        if dim:
            style_bits.append("dim")
        style = " ".join(style_bits) or None
        return Text(content, style=style)

    def rich_from_ansi(self, text: str):
        if not self.rich_enabled():
            return strip_ansi(text)
        return text_from_ansi(text)

    def rich_title_screen_enabled(self) -> bool:
        return self.rich_enabled() and Columns is not None and Table is not None

    def title_screen_save_summary(self) -> tuple[str, str]:
        saves = self.loadable_save_paths()
        if not saves:
            return ("No save files yet", "Forge a new hero to create your first journal entry.")
        save_label = "save" if len(saves) == 1 else "saves"
        return (f"{len(saves)} {save_label} available", f"Latest: {self.save_display_label(saves[0])}")

    def title_screen_audio_summary(self) -> str:
        sound_label = "On" if getattr(self, "sound_effects_enabled", False) else "Off"
        music_ready = bool(getattr(self, "_music_assets_ready", False))
        if not music_ready:
            music_label = "Unavailable"
        else:
            music_label = "On" if getattr(self, "music_enabled", False) else "Off"
        return f"SFX {sound_label} | Music {music_label}"

    def title_screen_presentation_summary(self) -> str:
        presentation = "On" if getattr(self, "_animations_and_delays_preference", False) else "Off"
        dice_mode_label = (
            self.dice_animation_mode_label()
            if callable(getattr(self, "dice_animation_mode_label", None))
            else ("On" if getattr(self, "_dice_animations_preference", False) else "Off")
        )
        typed = "On" if getattr(self, "_typed_dialogue_preference", getattr(self, "type_dialogue", False)) else "Off"
        return f"Animations {presentation} | Dice {dice_mode_label} | Typed text {typed}"

    def render_title_screen(
        self,
        title: str,
        subtitle: str,
        intro_text: str,
        options: list[str],
        option_details: dict[str, str] | None = None,
    ) -> None:
        option_details = option_details or {}
        self.output_fn("")
        save_summary, save_detail = self.title_screen_save_summary()
        campaign_summary = "Acts I and II are playable now, with later acts scaffolded for expansion."

        if self.rich_title_screen_enabled():
            header = Text(justify="center")
            header.append(f"{title}\n", style="bold bright_yellow")
            header.append(f"{subtitle}\n", style="bold bright_cyan")
            header.append("Frontier roads. Hard bargains. Consequences that travel.\n", style="white")
            header.append(intro_text, style="dim")

            status_table = Table.grid(expand=True, padding=(0, 1))
            status_table.add_column(style="bold bright_yellow", ratio=1)
            status_table.add_column(ratio=3)
            status_table.add_row("Campaign", campaign_summary)
            status_table.add_row("Saves", save_summary)
            status_table.add_row("", save_detail)
            status_table.add_row("Audio", self.title_screen_audio_summary())
            status_table.add_row("Presentation", self.title_screen_presentation_summary())

            options_table = Table.grid(expand=True, padding=(0, 1))
            options_table.add_column(style="bold bright_yellow", width=3)
            options_table.add_column(style="bold")
            options_table.add_column(style="dim", ratio=1)
            for index, option in enumerate(options, start=1):
                options_table.add_row(f"{index}.", strip_ansi(option), option_details.get(option, ""))

            rendered = self.emit_rich(
                Group(
                    Panel(
                        header,
                        border_style=rich_style_name("light_yellow"),
                        box=box.DOUBLE,
                        padding=(1, 2),
                        title=self.rich_text("Sword Coast Chronicle", "light_yellow", bold=True),
                    ),
                    Columns(
                        [
                            Panel(
                                status_table,
                                title=self.rich_text("Campaign Ledger", "light_aqua", bold=True),
                                border_style=rich_style_name("light_aqua"),
                                box=box.ROUNDED,
                                padding=(0, 1),
                            ),
                            Panel(
                                options_table,
                                title=self.rich_text("What Would You Like To Do?", "light_green", bold=True),
                                border_style=rich_style_name("light_green"),
                                box=box.ROUNDED,
                                padding=(0, 1),
                            ),
                        ],
                        expand=True,
                        equal=False,
                    ),
                ),
                width=max(108, self.rich_console_width()),
            )
            if rendered:
                return

        self.output_fn(f"=== {title} ===")
        self.output_fn(subtitle)
        self.say("Frontier roads. Hard bargains. Consequences that travel.")
        self.say(intro_text)
        self.say(f"Campaign: {campaign_summary}")
        self.say(f"Saves: {save_summary}")
        self.say(save_detail)
        self.say(f"Audio: {self.title_screen_audio_summary()}")
        self.say(f"Presentation: {self.title_screen_presentation_summary()}")
        self.output_fn("")
        self.say("What would you like to do?")
        self.render_choice_options(options, staggered=False)

    def choose_title_menu(
        self,
        title: str,
        subtitle: str,
        intro_text: str,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> int:
        while True:
            self.render_title_screen(title, subtitle, intro_text, options, option_details)
            raw = self.read_input("> ").strip()
            lowered = raw.lower()
            if lowered == "quit":
                if self.confirm("Quit the program and close the main menu?"):
                    from .base import QuitProgram

                    raise QuitProgram()
                self.say("You remain at the main menu.")
                continue
            if lowered in {"load", "saves", "save files"}:
                if self.open_save_files_menu():
                    from .base import ResumeLoadedGame

                    raise ResumeLoadedGame()
                continue
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= len(options):
                    return value
            self.say("Please enter a listed number.")

    def choose(
        self,
        prompt: str,
        options: list[str],
        *,
        allow_meta: bool = True,
        show_hud: bool = True,
        sticky_trailing_options: int = 0,
    ) -> int:
        return self.choose_with_display_mode(
            prompt,
            options,
            allow_meta=allow_meta,
            staggered=False,
            show_hud=show_hud,
            sticky_trailing_options=sticky_trailing_options,
        )

    def scenario_choice(
        self,
        prompt: str,
        options: list[str],
        *,
        allow_meta: bool = True,
        show_hud: bool = True,
        sticky_trailing_options: int = 0,
    ) -> int:
        return self.choose_with_display_mode(
            prompt,
            options,
            allow_meta=allow_meta,
            staggered=True,
            show_hud=show_hud,
            sticky_trailing_options=sticky_trailing_options,
        )

    def render_choice_options(self, options: list[str], *, staggered: bool) -> None:
        pause = getattr(self, "pause_for_option_reveal", None)
        for index, option in enumerate(options, start=1):
            self.output_fn(f"  {index}. {self.format_option_text(option)}")
            if staggered and index < len(options) and callable(pause):
                pause()

    def compact_hud_scene_key(self) -> tuple[int, str] | None:
        if self.state is None or getattr(self, "_in_combat", False):
            return None
        return (id(self.state), str(self.state.current_scene))

    def should_render_compact_hud(self) -> bool:
        return self.compact_hud_scene_key() is not None

    def hud_act_label(self) -> str:
        assert self.state is not None
        act_labels = getattr(self, "ACT_LABELS", {})
        return f"Act {act_labels.get(self.state.current_act, self.state.current_act)}"

    def hud_location_label(self) -> str:
        assert self.state is not None
        scene_labels = getattr(self, "SCENE_LABELS", {})
        current_scene = str(self.state.current_scene)
        return scene_labels.get(current_scene, current_scene.replace("_", " ").title())

    def hud_objective_label(self) -> str:
        assert self.state is not None
        refresh_quest_statuses = getattr(self, "refresh_quest_statuses", None)
        if callable(refresh_quest_statuses):
            refresh_quest_statuses(announce=False)
        ready_quests = getattr(self, "quest_entries_by_status", lambda status: [])("ready_to_turn_in")
        if ready_quests:
            return f"Turn in {ready_quests[0][0].title}"
        active_quests = getattr(self, "quest_entries_by_status", lambda status: [])("active")
        quest_focused_scenes = set(getattr(self, "HUD_QUEST_FOCUSED_SCENES", set()))
        if self.state.current_scene in quest_focused_scenes and active_quests:
            return active_quests[0][0].title
        scene_objectives = getattr(self, "SCENE_OBJECTIVES", {})
        current_scene = str(self.state.current_scene)
        if current_scene in scene_objectives:
            return str(scene_objectives[current_scene])
        if active_quests:
            return active_quests[0][0].title
        return "Press on."

    def hud_short_name(self, member) -> str:
        return str(getattr(member, "name", "")).split()[0] or str(getattr(member, "name", "Party"))

    def hud_member_health_text(self, member) -> str:
        if getattr(member, "dead", False):
            return self.style_text("DEAD", "light_red")
        if getattr(member, "current_hp", 0) <= 0:
            return self.style_text("DOWN", "light_red")
        health = f"{member.current_hp}/{member.max_hp}"
        styled = self.style_text(health, self.health_bar_color(member.current_hp, member.max_hp))
        if getattr(member, "temp_hp", 0):
            styled += self.style_text(f"+{member.temp_hp}t", "light_aqua")
        return styled

    def hud_party_summary(self) -> str:
        assert self.state is not None
        return " | ".join(
            f"{self.hud_short_name(member)} {self.hud_member_health_text(member)}"
            for member in self.state.party_members()
        )

    def render_compact_hud(self) -> None:
        scene_key = self.compact_hud_scene_key()
        if scene_key is None:
            return
        objective = textwrap.shorten(self.hud_objective_label(), width=40, placeholder="...")
        header_line = (
            f"{self.style_text(f'[{self.hud_act_label()}]', 'light_yellow')} "
            f"{self.style_text(self.hud_location_label(), 'light_aqua')} | "
            f"{self.style_text('Objective:', 'light_yellow')} {objective}"
        )
        resources_line = (
            f"{self.style_text('Resources:', 'light_yellow')} {self.state.gold} gp | "
            f"Short rests: {self.state.short_rests_remaining} | "
            f"Carry: {self.current_inventory_weight():.1f}/{self.carrying_capacity()} lb"
        )
        party_line = f"{self.style_text('Party:', 'light_yellow')} {self.hud_party_summary()}"
        if not self.emit_rich(
            Panel(
                Group(
                    self.rich_from_ansi(header_line),
                    self.rich_from_ansi(resources_line),
                    self.rich_from_ansi(party_line),
                ),
                title=self.rich_text("Travel Ledger", "light_yellow", bold=True),
                border_style=rich_style_name("light_yellow"),
                box=box.ROUNDED,
                padding=(0, 1),
            )
        ):
            self.output_fn(header_line)
            self.output_fn(resources_line)
            self.output_fn(party_line)
        self.output_fn("")
        self._compact_hud_last_scene_key = scene_key

    def maybe_render_compact_hud(self, *, show_hud: bool) -> None:
        if not show_hud:
            return
        scene_key = self.compact_hud_scene_key()
        if scene_key is None:
            return
        if getattr(self, "_compact_hud_last_scene_key", None) == scene_key:
            return
        self.render_compact_hud()

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
                self.output_fn("")
                self.maybe_render_compact_hud(show_hud=show_hud)
                self.say(f"{prompt} (page {page + 1})")
                self.render_choice_options(labels, staggered=staggered)
                raw = self.read_input("> ").strip()
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
                self.say("Please enter a listed number.")
        while True:
            self.output_fn("")
            self.maybe_render_compact_hud(show_hud=show_hud)
            self.say(prompt)
            self.render_choice_options(options, staggered=staggered)
            raw = self.read_input("> ").strip()
            if self.handle_meta_command(raw):
                continue
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= len(options):
                    return value
            self.say("Please enter a listed number.")

    def confirm(self, prompt: str) -> bool:
        return self.choose(prompt, ["Yes", "No"], allow_meta=False, show_hud=False) == 1

    def ask_text(self, prompt: str) -> str:
        while True:
            self.output_fn("")
            value = self.read_input(f"{prompt}: ").strip()
            if self.handle_meta_command(value):
                continue
            if value:
                return value
            self.say("Please enter a value.")

    def banner(self, title: str) -> None:
        self.output_fn("")
        self.output_fn(f"=== {title} ===")
        self.maybe_render_compact_hud(show_hud=True)

    def say(self, text: str, *, typed: bool = False) -> None:
        if not text:
            self.output_fn("")
            return
        narrator = getattr(self, "typewrite_narration", None)
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                self.output_fn("")
                continue
            if ANSI_RE.search(paragraph):
                self.output_fn(paragraph)
                continue
            wrapped = textwrap.fill(paragraph, width=88)
            if typed and callable(narrator) and getattr(self, "type_dialogue", False):
                narrator(wrapped)
            else:
                self.output_fn(wrapped)

    def inline_save(self) -> None:
        if self.state is None:
            self.say("There is no active game to save.")
            return
        slot_name = self.ask_text("Save slot name")
        path = self.save_game(slot_name=slot_name)
        self.say(f"Saved to {path.name}.")

    def save_game(self, *, slot_name: str) -> Path:
        assert self.state is not None
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", slot_name).strip("_") or "save"
        path = self.save_dir / f"{safe_name}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(self.state.to_dict(), handle, indent=2)
        return path

    def is_autosave_path(self, path: Path) -> bool:
        return path.stem.startswith(getattr(self, "AUTOSAVE_PREFIX", "autosave__"))

    def autosave_paths(self) -> list[Path]:
        settings_path = getattr(self, "settings_path", None)
        candidates = [
            path
            for path in self.save_dir.glob(f"{getattr(self, 'AUTOSAVE_PREFIX', 'autosave__')}*.json")
            if path != settings_path
        ]
        return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)

    def autosave_slot_name(self, label: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_label = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_") or "autosave"
        return f"{getattr(self, 'AUTOSAVE_PREFIX', 'autosave__')}{stamp}_{safe_label}"

    def prune_old_autosaves(self) -> None:
        limit = int(getattr(self, "AUTOSAVE_LIMIT", 15))
        for stale_path in self.autosave_paths()[limit:]:
            try:
                stale_path.unlink(missing_ok=True)
            except OSError:
                continue

    def create_autosave(self, *, label: str) -> Path | None:
        if self.state is None or not getattr(self, "autosaves_enabled", True):
            return None
        path = self.save_game(slot_name=self.autosave_slot_name(label))
        self.prune_old_autosaves()
        return path

    def loadable_save_paths(self) -> list[Path]:
        settings_path = getattr(self, "settings_path", None)
        saves = sorted(
            (path for path in self.save_dir.glob("*.json") if path != settings_path),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        manual_saves = [path for path in saves if not self.is_autosave_path(path)]
        autosaves = [path for path in saves if self.is_autosave_path(path)]
        return [*manual_saves, *autosaves]

    def save_display_label(self, path: Path) -> str:
        if not self.is_autosave_path(path):
            return path.stem
        prefix = getattr(self, "AUTOSAVE_PREFIX", "autosave__")
        stem = path.stem[len(prefix):]
        match = re.match(r"^(?P<date>\d{8})_(?P<time>\d{6})_(?P<micro>\d{6})_(?P<label>.+)$", stem)
        if match is None:
            return f"[Autosave] {stem.replace('_', ' ')}"
        date_code = match.group("date")
        time_code = match.group("time")
        label = match.group("label").replace("_", " ").strip() or "autosave"
        timestamp = (
            f"{date_code[:4]}-{date_code[4:6]}-{date_code[6:8]} "
            f"{time_code[:2]}:{time_code[2:4]}:{time_code[4:6]}"
        )
        return f"[Autosave] {label.title()} | {timestamp}"

    def load_save_path(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.state = GameState.from_dict(data)
        self.ensure_state_integrity()
        self._compact_hud_last_scene_key = None
        refresh_scene_music = getattr(self, "refresh_scene_music", None)
        if callable(refresh_scene_music):
            refresh_scene_music()
        self.say(f"Loaded {self.save_display_label(path)}.")

    def delete_save_path(self, path: Path) -> bool:
        label = self.save_display_label(path)
        if not self.confirm(f"Delete {label}? This cannot be undone."):
            self.say("The save file remains.")
            return False
        try:
            path.unlink()
        except OSError:
            self.say(f"Could not delete {label}.")
            return False
        self.say(f"Deleted {label}.")
        return True

    def open_save_files_menu(self) -> bool:
        while True:
            saves = self.loadable_save_paths()
            if not saves:
                self.say("No save files were found yet.")
                return False
            choice = self.choose(
                "Save Files",
                [self.save_display_label(path) for path in saves] + ["Back"],
                allow_meta=False,
                sticky_trailing_options=1,
            )
            if choice == len(saves) + 1:
                return False
            selected = saves[choice - 1]
            label = self.save_display_label(selected)
            action = self.choose(
                f"{label}",
                [
                    "Load this save",
                    "Delete this save",
                    "Back",
                ],
                allow_meta=False,
            )
            if action == 1:
                self.load_save_path(selected)
                return True
            if action == 2:
                self.delete_save_path(selected)

    def load_from_menu(self) -> bool:
        return self.open_save_files_menu()
