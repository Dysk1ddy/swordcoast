from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid

from dnd_game.content import build_character, create_elira_dawnmantle, create_enemy, create_tolan_ironshield
from dnd_game.game import TextDnDGame
from dnd_game.gameplay.base import QuitProgram, ReturnToTitleMenu
from dnd_game.models import GameState
from dnd_game.ui.examine import ExamineEntry
from dnd_game.ui.kivy_markup import format_kivy_log_entry, visible_markup_text

try:
    from dnd_game.gui import (
        ClickableTextDnDGame,
        GameScreen,
        KIVY_SIDE_COMMAND_CLOSE_TOKEN,
        KivySideCommandClosed,
        NativeCommandWorkspace,
        NativeMapView,
    )
    from kivy.core.window import Window
except Exception as exc:  # pragma: no cover - depends on optional Kivy runtime
    ClickableTextDnDGame = None
    GameScreen = None
    KIVY_SIDE_COMMAND_CLOSE_TOKEN = ""
    KivySideCommandClosed = Exception
    NativeCommandWorkspace = None
    NativeMapView = None
    Window = None
    KIVY_IMPORT_ERROR = exc
else:
    KIVY_IMPORT_ERROR = None


class FakeKivyBridge:
    def __init__(self) -> None:
        self.screen = SimpleNamespace(kivy_dark_mode_enabled=True, kivy_fullscreen_enabled=False)
        self.outputs: list[str] = []
        self.choice_responses: list[str] = []
        self.choice_prompts: list[tuple[str, list[str]]] = []
        self.side_command_active = False
        self.native_commands: list[str] = []
        self.close_app_requested = False
        self.initiative_refresh_count = 0
        self.combat_refresh_count = 0
        self.initiative_fade_count = 0
        self.dice_frames: list[tuple[str, dict[str, object]]] = []
        self.dice_results: list[str] = []

    def post_output(self, text: object = "") -> None:
        self.outputs.append(str(text))

    def request_choice(
        self,
        prompt: str,
        options: list[str],
        *,
        option_details: dict[str, str] | None = None,
    ) -> str:
        del option_details
        self.choice_prompts.append((prompt, list(options)))
        return self.choice_responses.pop(0) if self.choice_responses else "1"

    def set_kivy_dark_mode(self, enabled: bool) -> None:
        self.screen.kivy_dark_mode_enabled = bool(enabled)

    def set_kivy_fullscreen(self, enabled: bool) -> None:
        self.screen.kivy_fullscreen_enabled = bool(enabled)

    def show_native_command(self, command: str) -> None:
        self.native_commands.append(command)

    def close_app_on_finish(self) -> None:
        self.close_app_requested = True

    def refresh_active_initiative_tray(self) -> None:
        self.initiative_refresh_count += 1

    def refresh_combat_panel(self) -> None:
        self.combat_refresh_count += 1

    def fade_out_initiative_tray(self) -> None:
        self.initiative_fade_count += 1

    def show_dice_animation_frame(self, markup: str, **kwargs: object) -> None:
        self.dice_frames.append((markup, dict(kwargs)))

    def append_dice_result(self, markup: str) -> None:
        self.dice_results.append(markup)


@unittest.skipIf(ClickableTextDnDGame is None, f"Kivy unavailable: {KIVY_IMPORT_ERROR}")
class KivySettingsTests(unittest.TestCase):
    def make_save_dir(self) -> Path:
        save_dir = Path.cwd() / "tests_output" / f"kivy_settings_{uuid.uuid4().hex}"
        save_dir.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(save_dir, ignore_errors=True))
        return save_dir

    def make_player(self):
        return build_character(
            name="Vale",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )

    def test_clickable_game_keeps_dice_ui_enabled_without_dice_setting(self) -> None:
        save_dir = self.make_save_dir()
        settings_path = save_dir / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "animations_and_delays_enabled": False,
                    "dice_animations_enabled": False,
                    "dice_animation_mode": "off",
                }
            ),
            encoding="utf-8",
        )
        bridge = FakeKivyBridge()

        game = ClickableTextDnDGame(bridge, save_dir=save_dir)

        self.assertTrue(game.animate_dice)
        self.assertTrue(callable(getattr(game.rng, "dice_roll_animator", None)))
        self.assertNotIn("dice_animations_enabled", game.current_settings_payload())
        self.assertNotIn("dice_animation_mode", game.current_settings_payload())

    def test_fullscreen_setting_loads_applies_and_persists(self) -> None:
        save_dir = self.make_save_dir()
        settings_path = save_dir / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "kivy_dark_mode_enabled": False,
                    "kivy_fullscreen_enabled": True,
                }
            ),
            encoding="utf-8",
        )
        bridge = FakeKivyBridge()

        game = ClickableTextDnDGame(bridge, save_dir=save_dir)

        self.assertTrue(game.current_settings_payload()["kivy_fullscreen_enabled"])
        self.assertTrue(bridge.screen.kivy_fullscreen_enabled)
        self.assertFalse(game.current_settings_payload()["kivy_dark_mode_enabled"])

        game.set_kivy_fullscreen_enabled(False)

        stored_settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertFalse(stored_settings["kivy_fullscreen_enabled"])
        self.assertFalse(bridge.screen.kivy_fullscreen_enabled)

    def test_story_choice_reopens_after_unexpected_side_close_token(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = [KIVY_SIDE_COMMAND_CLOSE_TOKEN, "2"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)

        choice = game.choose_with_display_mode("Choose a path.", ["First", "Second"], allow_meta=False)

        self.assertEqual(choice, 2)
        self.assertEqual([prompt for prompt, _options in bridge.choice_prompts], ["Choose a path.", "Choose a path."])

    def test_active_side_command_choice_close_still_cancels_side_command(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.side_command_active = True
        bridge.choice_responses = [KIVY_SIDE_COMMAND_CLOSE_TOKEN]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)

        with self.assertRaises(KivySideCommandClosed):
            game.choose_with_display_mode("Manage inventory.", ["View inventory"], allow_meta=False)

    def test_out_of_combat_map_journal_inventory_and_gear_use_native_command_panes(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game.state = GameState(player=player)

        self.assertTrue(game.handle_meta_command("map"))
        self.assertTrue(game.handle_meta_command("journal"))
        self.assertTrue(game.handle_meta_command("inventory"))
        self.assertTrue(game.handle_meta_command("gear"))
        self.assertTrue(game.handle_meta_command("camp"))

        self.assertEqual(bridge.native_commands, ["map", "journal", "inventory", "gear", "camp"])

    def test_kivy_camp_talk_command_runs_companion_dialogue_for_selected_companion(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        tolan = create_tolan_ironshield()
        elira = create_elira_dawnmantle()
        game.state = GameState(player=self.make_player(), companions=[tolan], camp_companions=[elira])
        talked_to: list[str] = []
        game.talk_to_companion = lambda companion=None: talked_to.append(companion.name if companion is not None else "")  # type: ignore[method-assign]

        self.assertTrue(game.handle_meta_command("camp talk 2"))

        self.assertEqual(talked_to, [elira.name])

    def test_kivy_quit_menu_can_return_to_main_menu(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = ["1"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game.state = GameState(player=self.make_player())

        with self.assertRaises(ReturnToTitleMenu):
            game.handle_meta_command("quit")

        self.assertIsNone(game.state)
        self.assertFalse(bridge.close_app_requested)
        self.assertEqual(
            bridge.choice_prompts,
            [("Quit menu.", ["Quit to Main Menu", "Quit to Desktop", "Back"])],
        )

    def test_kivy_quit_menu_can_quit_to_desktop(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = ["2"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game.state = GameState(player=self.make_player())

        with self.assertRaises(QuitProgram):
            game.handle_meta_command("quit")

        self.assertIsNotNone(game.state)
        self.assertTrue(bridge.close_app_requested)

    def test_kivy_quit_menu_back_stays_in_adventure(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = ["3"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        state = GameState(player=self.make_player())
        game.state = state

        self.assertTrue(game.handle_meta_command("quit"))

        self.assertIs(game.state, state)
        self.assertFalse(bridge.close_app_requested)
        self.assertIn("You stay with the current adventure.", bridge.outputs)

    def test_kivy_quit_menu_accepts_text_aliases(self) -> None:
        cases = (
            ("menu", ReturnToTitleMenu, False),
            ("desktop", QuitProgram, True),
        )
        for alias, expected_exception, close_requested in cases:
            with self.subTest(alias=alias):
                save_dir = self.make_save_dir()
                bridge = FakeKivyBridge()
                bridge.choice_responses = [alias]
                game = ClickableTextDnDGame(bridge, save_dir=save_dir)
                game.state = GameState(player=self.make_player())

                with self.assertRaises(expected_exception):
                    game.handle_meta_command("quit")

                self.assertEqual(bridge.close_app_requested, close_requested)

        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = ["back"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        state = GameState(player=self.make_player())
        game.state = state

        self.assertTrue(game.handle_meta_command("quit"))

        self.assertIs(game.state, state)
        self.assertFalse(bridge.close_app_requested)
        self.assertIn("You stay with the current adventure.", bridge.outputs)

    def test_kivy_quit_menu_ignores_stale_close_token_when_no_side_command_active(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = [KIVY_SIDE_COMMAND_CLOSE_TOKEN, "back"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        state = GameState(player=self.make_player())
        game.state = state

        self.assertTrue(game.handle_meta_command("quit"))

        self.assertIs(game.state, state)
        self.assertEqual(
            bridge.choice_prompts,
            [
                ("Quit menu.", ["Quit to Main Menu", "Quit to Desktop", "Back"]),
                ("Quit menu.", ["Quit to Main Menu", "Quit to Desktop", "Back"]),
            ],
        )

    def test_kivy_quit_menu_close_token_cancels_active_side_command(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.side_command_active = True
        bridge.choice_responses = [KIVY_SIDE_COMMAND_CLOSE_TOKEN]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game.state = GameState(player=self.make_player())

        with self.assertRaises(KivySideCommandClosed):
            game.handle_meta_command("quit")

    def test_kivy_title_quit_aliases_stay_on_title_or_close_desktop(self) -> None:
        for alias in ("menu", "back"):
            with self.subTest(alias=alias):
                save_dir = self.make_save_dir()
                bridge = FakeKivyBridge()
                bridge.choice_responses = [alias]
                game = ClickableTextDnDGame(bridge, save_dir=save_dir)
                game._at_title_screen = True

                self.assertTrue(game.handle_meta_command("quit"))

                self.assertFalse(bridge.close_app_requested)
                self.assertIn("You remain at the main menu.", bridge.outputs)

        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = ["desktop"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game._at_title_screen = True

        with self.assertRaises(QuitProgram):
            game.handle_meta_command("quit")

        self.assertTrue(bridge.close_app_requested)

    def make_command_screen(self, *, state=None, in_combat: bool = False):
        screen = GameScreen.__new__(GameScreen)
        game = SimpleNamespace(state=state, _in_combat=in_combat)
        screen.active_game = lambda: game
        screen.combat_active = lambda: in_combat
        screen.kivy_dark_mode_enabled = True
        return screen

    def test_command_bar_keeps_unavailable_commands_visible(self) -> None:
        screen = self.make_command_screen(state=None)

        self.assertEqual(screen._command_bar_commands_for_context(), tuple(GameScreen.COMMANDS))
        self.assertNotIn("~", GameScreen.COMMANDS)
        self.assertIn("save/load", GameScreen.COMMANDS)
        self.assertNotIn("save", GameScreen.COMMANDS)
        self.assertNotIn("load", GameScreen.COMMANDS)
        self.assertEqual(GameScreen.COMMAND_BUTTON_FONT_SIZE, "15sp")
        self.assertEqual(GameScreen.COMMAND_BAR_HEIGHT, 40)

    def test_dice_tray_waits_five_seconds_before_hiding(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen._dice_tray_hide_event = None
        screen._dice_tray_hide_ready_at = 0.0
        screen._dice_tray_fade_generation = 7
        screen._restore_persistent_dice_tray = Mock(return_value=False)
        screen._clear_dice_tray = Mock()

        first_event = SimpleNamespace(cancel=Mock())
        second_event = SimpleNamespace(cancel=Mock())
        with patch("dnd_game.gui.time.monotonic", return_value=100.0):
            with patch("dnd_game.gui.Clock.schedule_once", return_value=first_event) as schedule_once:
                screen._schedule_dice_tray_hide()

        callback, delay = schedule_once.call_args.args
        self.assertEqual(delay, 5.0)
        self.assertEqual(screen._dice_tray_hide_ready_at, 105.0)

        with patch("dnd_game.gui.time.monotonic", return_value=103.25):
            with patch("dnd_game.gui.Clock.schedule_once", return_value=second_event) as reschedule_once:
                callback(0)

        self.assertAlmostEqual(reschedule_once.call_args.args[1], 1.75)
        screen._clear_dice_tray.assert_not_called()

        rescheduled_callback = reschedule_once.call_args.args[0]
        with patch("dnd_game.gui.time.monotonic", return_value=105.01):
            rescheduled_callback(0)

        screen._clear_dice_tray.assert_called_once()
        self.assertEqual(screen._dice_tray_hide_ready_at, 0.0)

    def test_initiative_tray_waits_for_dice_result_hold(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        panel_builder = Mock(return_value=("initiative", 118))
        screen.active_game = Mock(return_value=SimpleNamespace(kivy_active_initiative_panel=panel_builder))
        screen.combat_active = Mock(return_value=True)
        screen._active_combat_actor_name = "Vale"
        screen._initiative_turn_arrow_phase = 2
        screen._dice_tray_hide_event = SimpleNamespace(cancel=Mock())
        screen._dice_tray_hide_ready_at = 105.0
        screen._dice_tray_fade_generation = 7
        screen._persistent_dice_tray_markup = "old initiative"

        with patch("dnd_game.gui.time.monotonic", return_value=101.0):
            screen.refresh_active_initiative_tray()

        panel_builder.assert_called_once_with(active_actor_name="Vale", arrow_phase=2)
        self.assertEqual(screen._dice_tray_fade_generation, 7)
        self.assertEqual(screen._persistent_dice_tray_markup, "initiative")

    def test_persistent_dice_tray_frame_does_not_replace_held_result(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen._dice_tray_hide_event = SimpleNamespace(cancel=Mock())
        screen._dice_tray_hide_ready_at = 105.0
        screen._dice_tray_fade_generation = 7
        screen._persistent_dice_tray_markup = "old initiative"

        with patch("dnd_game.gui.time.monotonic", return_value=101.0):
            screen._show_dice_tray_frame("new initiative", final=False, persist=True)

        self.assertEqual(screen._dice_tray_fade_generation, 7)
        self.assertEqual(screen._persistent_dice_tray_markup, "new initiative")

    def test_initiative_tray_waits_while_dice_roll_is_animating(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen._dice_tray_hide_event = None
        screen._dice_tray_hide_ready_at = 0.0
        screen._dice_tray_transient_hold_until = 105.0
        screen._dice_tray_fade_generation = 7
        screen._persistent_dice_tray_markup = "old initiative"

        with patch("dnd_game.gui.time.monotonic", return_value=101.0):
            screen._show_dice_tray_frame("new initiative", final=False, persist=True)

        self.assertEqual(screen._dice_tray_fade_generation, 7)
        self.assertEqual(screen._persistent_dice_tray_markup, "new initiative")

    def test_d20_roll_core_omits_die_label_text(self) -> None:
        screen = GameScreen.__new__(GameScreen)

        single = screen._kivy_dice_frame_core("d20", [14], highlight_index=0)
        advantage = screen._kivy_dice_frame_core("d20", [7, 14], kept=14, final=True, highlight_index=1)
        larger = screen._kivy_dice_frame_core("d20", [14], highlight_index=0, animate_size=True)

        self.assertNotIn("Die:", single)
        self.assertNotIn("Die A:", advantage)
        self.assertIn("14", single)
        self.assertIn("[size=34.0sp]", larger)

    def test_dice_roll_tray_has_room_for_result_suffix(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        self.assertGreaterEqual(GameScreen.DICE_ANIMATION_TRAY_HEIGHT, 118)
        self.assertGreaterEqual(screen.dice_roll_prefix_label.height, 26)
        self.assertGreaterEqual(screen.dice_roll_core_label.height, 58)
        self.assertGreaterEqual(screen.dice_roll_suffix_label.height, 42)

    def test_command_bar_explains_combat_unavailable_commands(self) -> None:
        state = SimpleNamespace(player=object())
        screen = self.make_command_screen(state=state, in_combat=True)

        self.assertEqual(screen._command_unavailable_reason("map"), "Maps are unavailable during combat.")
        self.assertEqual(
            screen._command_unavailable_reason("gear"),
            "You cannot reorganize equipment in the middle of combat.",
        )
        self.assertEqual(screen._command_unavailable_reason("camp"), "You cannot head to camp during combat.")
        self.assertEqual(screen._command_unavailable_reason("journal"), "")

    def test_unavailable_command_button_prints_reason_instead_of_submitting(self) -> None:
        screen = self.make_command_screen(state=SimpleNamespace(player=object()), in_combat=True)
        hidden: list[tuple[bool, bool]] = []
        messages: list[str] = []
        submitted: list[str] = []
        screen._set_command_bar_visible = lambda visible, *, animate: hidden.append((visible, animate))
        screen.post_command_unavailable_message = messages.append
        screen.submit_direct = submitted.append

        screen.submit_command("map")

        self.assertEqual(hidden, [(False, True)])
        self.assertEqual(messages, ["Maps are unavailable during combat."])
        self.assertEqual(submitted, [])

    def test_quit_command_bar_button_submits_even_without_active_adventure(self) -> None:
        screen = self.make_command_screen(state=None)
        hidden: list[tuple[bool, bool]] = []
        messages: list[str] = []
        submitted: list[str] = []
        screen._set_command_bar_visible = lambda visible, *, animate: hidden.append((visible, animate))
        screen.post_command_unavailable_message = messages.append
        screen.submit_direct = submitted.append

        screen.submit_command("quit")

        self.assertEqual(hidden, [(False, True)])
        self.assertEqual(messages, [])
        self.assertEqual(submitted, ["quit"])

    def test_title_quit_does_not_use_title_start_transition(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen.option_buttons = [
            SimpleNamespace(text="1. Continue"),
            SimpleNamespace(text="2. Start a new game"),
            SimpleNamespace(text="3. Save Files"),
            SimpleNamespace(text="4. Read the lore notes"),
            SimpleNamespace(text="5. Settings"),
            SimpleNamespace(text="6. Quit"),
        ]

        self.assertFalse(screen._title_menu_selection_starts_game("6"))
        self.assertFalse(screen._title_menu_selection_starts_game("quit"))

    def test_title_subprompt_clears_stale_transition_without_dropping_title_shell(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen._title_menu_active = True
        screen._title_menu_transition_active = True
        screen._main_title_menu_active = True
        screen.update_combat_layout = Mock()
        screen.title_screen_context_active = Mock(return_value=True)
        screen.side_panel_allowed = Mock(return_value=False)
        screen.combat_active = Mock(return_value=False)
        cleared: list[str] = []
        headers: list[bool] = []
        screen._set_title_card_markup = lambda markup: cleared.append(markup)
        screen._set_app_header_visible = lambda visible: headers.append(visible)
        screen.prompt_label = SimpleNamespace(text="")
        screen.status_label = SimpleNamespace(text="")
        screen.text_input = SimpleNamespace(hint_text="")
        screen._active_text_prompt_is_console = True
        screen._active_text_prompt_uses_input = True
        screen._console_drawer_visible = True
        screen._set_input_row_visible = Mock()
        screen._rebuild_options = Mock()
        screen._sync_command_bar_visibility = Mock()

        screen.show_choice_prompt("Quit menu.", ["Quit to Desktop", "Back"])

        self.assertFalse(screen._title_menu_transition_active)
        self.assertFalse(screen._main_title_menu_active)
        self.assertEqual(cleared, [])
        self.assertEqual(headers, [True])

        screen.show_choice_prompt(
            "Choose your route.",
            ["Continue"],
            option_details={"Continue": "Load latest save."},
        )

        self.assertTrue(screen._main_title_menu_active)
        self.assertEqual(cleared, [])
        self.assertEqual(headers[-1], False)

    def test_backtick_and_tilde_keys_toggle_console_drawer(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        command_bar: list[tuple[bool, bool]] = []
        input_row: list[tuple[bool, bool]] = []
        submitted: list[str] = []
        screen._console_drawer_visible = False
        screen._input_row_visible = False
        screen._active_text_prompt_is_console = False
        screen._active_text_prompt_uses_input = False
        screen._set_command_bar_visible = lambda visible, *, animate: command_bar.append((visible, animate))
        screen._set_input_row_visible = lambda visible, *, animate: input_row.append((visible, animate))
        screen.submit_direct = submitted.append

        self.assertTrue(screen._handle_window_key_down(None, 0, 0, "`", []))
        screen._console_drawer_visible = True
        self.assertTrue(screen._handle_window_key_down(None, 0, 0, "~", []))

        self.assertEqual(command_bar, [(False, True), (False, True)])
        self.assertEqual(input_row, [(False, True)])
        self.assertEqual(submitted, ["~", "back"])

    def test_backtick_is_text_when_non_console_text_prompt_is_open(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen._input_row_visible = True
        screen._active_text_prompt_is_console = False
        screen.is_fullscreen_shortcut = lambda *_args: False
        screen.is_console_menu_key = lambda *_args: True
        screen.toggle_console_drawer = Mock()

        self.assertFalse(screen._handle_window_key_down(None, 0, 0, "`", []))

        screen.toggle_console_drawer.assert_not_called()

    def test_hidden_typing_bar_still_accepts_number_shortcuts(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        submitted: list[str] = []
        screen.bridge = SimpleNamespace(waiting_for_input=True)
        screen._input_row_visible = False
        screen._save_browser_active = False
        screen._side_panel_mode = "default"
        screen.submit_direct = submitted.append
        screen.is_fullscreen_shortcut = lambda *_args: False
        screen.is_console_menu_key = lambda *_args: False
        screen.is_escape_key = lambda *_args: False

        self.assertTrue(screen._handle_window_key_down(None, 0, 0, "7", []))

        self.assertEqual(submitted, ["7"])

    def test_native_command_right_panel_uses_forty_percent_screen_width(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen.left_column = SimpleNamespace(size_hint_x=None)
        screen.combat_panel = SimpleNamespace(size_hint_x=None)
        screen._side_panel_mode = "native_command"

        screen._apply_right_panel_width()

        self.assertAlmostEqual(screen.left_column.size_hint_x, 0.6)
        self.assertAlmostEqual(screen.combat_panel.size_hint_x, 0.4)
        self.assertEqual(GameScreen.SPLIT_TEXT_WINDOW_FONT_SIZE, "17sp")

    def test_prompt_choices_and_command_bar_keep_full_width(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        self.assertIs(screen.main_body.parent, screen)
        self.assertIs(screen.log_shell.parent, screen.left_column)
        self.assertIs(screen.prompt_label.parent, screen)
        self.assertIs(screen.options_area.parent, screen)
        self.assertIs(screen.commands.parent, screen)
        self.assertIsNone(screen.input_row.parent)
        self.assertNotIn("~", screen.command_buttons_by_command)

    def test_story_choices_stack_left_with_four_visible_rows_and_scroll(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        screen.bridge.game = SimpleNamespace(state=SimpleNamespace(player=object()), _in_combat=False)

        screen.show_choice_prompt("Choose a route.", [f"Choice {index}" for index in range(1, 7)])

        self.assertEqual(screen.options_grid.cols, 1)
        self.assertEqual(screen.options_grid.rows, 6)
        self.assertEqual(screen._option_grid_shape(6), (6, 1))
        self.assertEqual(screen._option_shell_height(6), screen._option_shell_height(4))
        self.assertLess(screen.options_area.height, screen.options_grid.height)
        self.assertGreater(screen.choice_scroll_indicator.width, 0)
        self.assertIn("↓", screen.choice_scroll_indicator.text)
        screen.options_scroll.scroll_y = 0
        screen._sync_choice_scroll_indicator()
        self.assertIn("↑", screen.choice_scroll_indicator.text)
        self.assertTrue(all(button.halign == "left" for button in screen.option_buttons))
        self.assertTrue(all(button.size_hint_y is None for button in screen.option_buttons))

    def test_no_character_choices_keep_normal_grid_without_scroll(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        screen.bridge.game = SimpleNamespace(state=None, _in_combat=False)

        screen.show_choice_prompt("Choose a route.", [f"Choice {index}" for index in range(1, 7)])

        self.assertEqual((screen.options_grid.rows, screen.options_grid.cols), (2, 3))
        self.assertEqual(screen.options_grid.size_hint_y, 1)
        self.assertFalse(screen.options_scroll.do_scroll_y)
        self.assertEqual(screen.options_scroll.bar_width, 0)
        self.assertEqual(screen.choice_scroll_indicator.width, 0)
        self.assertTrue(all(button.halign == "center" for button in screen.option_buttons))

    def test_title_menu_choices_keep_normal_grid_without_scroll(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        options = ["Continue", "Start a new game", "Save Files", "Read the lore notes", "Settings", "Quit"]
        details = {option: f"{option} detail." for option in options}

        screen.show_choice_prompt("Choose your route.", options, option_details=details)

        self.assertEqual((screen.options_grid.rows, screen.options_grid.cols), (2, 3))
        self.assertEqual(screen.options_grid.size_hint_y, 1)
        self.assertFalse(screen.options_scroll.do_scroll_y)
        self.assertEqual(screen.options_scroll.bar_width, 0)
        self.assertGreaterEqual(screen._option_button_height(detailed=True), 72)
        self.assertGreaterEqual(screen.options_area.height, 168)
        self.assertTrue(all(button.halign == "center" for button in screen.option_buttons))

    def test_title_context_settings_menu_reserves_full_button_height(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        screen._title_menu_active = True
        rows = 5

        expected = 14 + rows * screen.OPTION_BUTTON_MIN_HEIGHT + (rows - 1) * screen.OPTION_BUTTON_ROW_GAP

        self.assertGreaterEqual(screen._option_shell_height(rows), expected)

    def test_combat_choices_keep_multi_column_centered_buttons(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        screen.bridge.game = SimpleNamespace(state=SimpleNamespace(player=object()), _in_combat=True)
        options = [
            "[Action] Strike",
            "[Bonus Action] Shove",
            "[Item] Potion",
            "[Social] Taunt",
            "End Turn",
            "Back",
        ]

        screen.show_choice_prompt("Choose a combat action.", options)

        self.assertEqual((screen.options_grid.rows, screen.options_grid.cols), (2, 3))
        self.assertEqual(screen._option_grid_shape(len(options)), (2, 3))
        self.assertTrue(all(button.halign == "center" for button in screen.option_buttons))

    def test_dice_roll_tray_lives_in_right_panel(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        self.assertIs(screen.dice_roll_tray.parent, screen.combat_panel)
        self.assertIsNot(screen.dice_roll_tray.parent, screen.log_shell)
        self.assertIs(screen.combat_panel.children[0], screen.dice_roll_tray)
        self.assertIs(screen.dice_roll_close_button.parent, screen.dice_roll_header)

    def test_row_style_dice_frames_route_to_right_panel(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen.update_combat_layout = Mock()
        screen.side_panel_allowed = Mock(return_value=True)
        screen._show_dice_roll_side_frame = Mock()
        screen._show_dice_tray_frame = Mock()
        screen._complete_log_append = Mock()

        screen.show_dice_animation_frame(
            "roll",
            final=True,
            use_tray=True,
            use_roll_tray=True,
            tray_parts=("", "14", "Total 14"),
        )

        screen._show_dice_roll_side_frame.assert_called_once()
        screen._show_dice_tray_frame.assert_not_called()

    def test_kivy_combat_attack_rolls_do_not_update_roll_tray(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game._in_combat = True

        game.animate_dice_roll(
            kind="roll",
            expression="1d4+2",
            sides=4,
            rolls=[3],
            modifier=2,
            style="damage",
            context_label="Short sword",
        )

        self.assertEqual(bridge.dice_frames, [])
        self.assertEqual(bridge.dice_results, [])

    def test_kivy_random_encounter_skill_checks_show_roll_tray_during_combat_unwind(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game._in_combat = True

        game.animate_dice_roll(
            kind="d20",
            expression="d20",
            sides=20,
            rolls=[16],
            kept=16,
            modifier=4,
            target_number=12,
            target_label="DC 12",
            style="skill",
            outcome_kind="check",
            context_label="Vale Perception check",
        )

        self.assertEqual(len(bridge.dice_frames), 1)
        frame_markup, frame_kwargs = bridge.dice_frames[0]
        self.assertTrue(frame_kwargs["use_tray"])
        self.assertTrue(frame_kwargs["use_roll_tray"])
        self.assertIn("Vale Perception check", visible_markup_text(frame_markup))
        self.assertIn("DC 12", visible_markup_text(frame_markup))
        self.assertEqual(len(bridge.dice_results), 1)

    def test_active_initiative_arrow_refreshes_with_zero_phase_immediately(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen._initiative_turn_arrow_phase = 3
        screen.combat_active = Mock(return_value=True)
        screen._start_initiative_turn_arrow_animation = Mock()
        screen._stop_initiative_turn_arrow_animation = Mock()
        calls: list[tuple[str, int, str]] = []
        screen.refresh_combat_panel = lambda: calls.append(
            ("combat", screen._initiative_turn_arrow_phase, screen._active_combat_actor_name)
        )
        screen.refresh_active_initiative_tray = lambda: calls.append(
            ("initiative", screen._initiative_turn_arrow_phase, screen._active_combat_actor_name)
        )

        screen.set_active_combat_actor("Vale")

        self.assertEqual(screen._initiative_turn_arrow_phase, 0)
        screen._start_initiative_turn_arrow_animation.assert_called_once()
        screen._stop_initiative_turn_arrow_animation.assert_not_called()
        self.assertIn(("initiative", 0, "Vale"), calls)

    def test_dice_roll_side_frame_waits_for_manual_close(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen.side_panel_allowed = Mock(return_value=True)
        screen._dice_roll_tray_fade_generation = 0
        screen.dice_roll_tray = Mock()
        screen._dice_tray_height_for_markup = Mock(return_value=168)
        screen._set_dice_roll_tray_visible = Mock()
        screen._set_dice_roll_tray_content_mode = Mock()
        screen.dice_roll_prefix_label = SimpleNamespace(text="", height=0)
        screen.dice_roll_core_label = SimpleNamespace(text="", height=0, font_size="")
        screen.dice_roll_suffix_label = SimpleNamespace(text="", height=0)
        screen._sync_dice_roll_label = Mock()

        screen._show_dice_roll_side_frame(
            "roll",
            final=True,
            tray_parts=("", "14", "Total 14"),
        )

        self.assertFalse(hasattr(GameScreen, "_schedule_dice_roll_tray_hide"))
        self.assertEqual(screen.dice_roll_core_label.font_size, "34sp")
        self.assertEqual(screen.dice_roll_core_label.height, 58)

    def test_initiative_table_frames_stay_on_initiative_tray(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen.update_combat_layout = Mock()
        screen.side_panel_allowed = Mock(return_value=True)
        screen._show_dice_roll_side_frame = Mock()
        screen._show_dice_tray_frame = Mock()
        screen._complete_log_append = Mock()

        screen.show_dice_animation_frame("initiative table", final=True, use_tray=True, persist=False)

        screen._show_dice_roll_side_frame.assert_not_called()
        screen._show_dice_tray_frame.assert_called_once()

        screen._show_dice_tray_frame.reset_mock()
        screen.show_dice_animation_frame("active initiative", final=False, use_tray=True, persist=True)

        screen._show_dice_roll_side_frame.assert_not_called()
        screen._show_dice_tray_frame.assert_called_once()

    def test_dead_enemies_are_removed_from_active_initiative_table(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        player = self.make_player()
        first_enemy = create_enemy("goblin_skirmisher")
        second_enemy = create_enemy("bandit")
        first_enemy.name = "Deadbat"
        second_enemy.name = "Livebat"
        first_enemy.current_hp = 0
        first_enemy.dead = True
        game._in_combat = True
        game._active_round_number = 2
        game._active_combat_enemies = [first_enemy, second_enemy]
        game._kivy_active_initiative_entries = [
            {
                "actor": player,
                "outcome": SimpleNamespace(kept=12),
                "modifier": 2,
                "total": 14,
                "dex_mod": 2,
                "side_priority": 1,
                "tie_index": 0,
            },
            {
                "actor": first_enemy,
                "outcome": SimpleNamespace(kept=18),
                "modifier": 2,
                "total": 20,
                "dex_mod": 2,
                "side_priority": 0,
                "tie_index": -1,
            },
            {
                "actor": second_enemy,
                "outcome": SimpleNamespace(kept=9),
                "modifier": 1,
                "total": 10,
                "dex_mod": 1,
                "side_priority": 0,
                "tie_index": -2,
            },
        ]

        panel = game.kivy_active_initiative_panel(active_actor_name=player.name, arrow_phase=0)

        self.assertIsNotNone(panel)
        markup, tray_height = panel
        self.assertIn(player.name, markup)
        self.assertIn(second_enemy.name, markup)
        self.assertNotIn(first_enemy.name, markup)
        self.assertLess(tray_height, game._kivy_initiative_tray_height(game._kivy_active_initiative_entries))

    def test_enemy_drop_refreshes_active_initiative_table(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        enemy = create_enemy("goblin_skirmisher")
        game._in_combat = True
        game._active_combat_enemies = [enemy]
        game.kivy_combat_is_ending = Mock(return_value=False)

        game.after_actor_damaged(enemy, previous_hp=enemy.max_hp, damage=enemy.max_hp, damage_type="slashing")

        self.assertEqual(bridge.initiative_refresh_count, 0)

        enemy.current_hp = 0
        enemy.dead = True
        game.after_actor_damaged(enemy, previous_hp=1, damage=1, damage_type="slashing")

        self.assertEqual(bridge.initiative_refresh_count, 1)

    def test_console_text_prompt_shows_input_row(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        screen.show_text_prompt("console> ")

        self.assertIs(screen.input_row.parent, screen)
        self.assertFalse(screen.text_input.disabled)
        self.assertEqual(screen.text_input.hint_text, "Type a console command, or back")
        self.assertTrue(screen._console_drawer_visible)

    def test_save_slot_text_prompt_shows_input_row(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        screen.show_text_prompt("Save slot name:")

        self.assertIs(screen.input_row.parent, screen)
        self.assertFalse(screen.text_input.disabled)
        self.assertEqual(screen.text_input.hint_text, "Type your answer here")
        self.assertFalse(screen._console_drawer_visible)

    def test_save_load_button_opens_combined_menu(self) -> None:
        save_dir = self.make_save_dir()
        bridge = FakeKivyBridge()
        bridge.choice_responses = ["3"]
        game = ClickableTextDnDGame(bridge, save_dir=save_dir)
        game.state = GameState(player=self.make_player())

        self.assertTrue(game.handle_meta_command("save/load"))

        self.assertEqual(
            bridge.choice_prompts,
            [("Save/Load.", ["Save Game", "Load Game", "Back"])],
        )

    def test_examine_docks_in_bottom_right_panel_above_choices(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        entry = ExamineEntry(title="Ledger Hook", category="Object", description="Ink has dried in the notch.")

        screen.show_examine_entry(entry)

        self.assertIs(screen.examine_shell.parent, screen.combat_panel)
        self.assertIs(screen.options_area.parent, screen)
        self.assertGreater(screen.examine_shell.height, 0)

    def test_examine_panel_uses_distinct_background_color(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        self.assertNotEqual(screen.theme["examine"], screen.theme["combat"])
        self.assertEqual(tuple(screen.examine_shell._panel_background_color), screen.theme["examine"])

    def test_left_log_colored_name_registers_examine_ref(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        screen.bridge = SimpleNamespace(game=None)
        screen._examine_ref_entries = {}
        screen._examine_ref_counter = 0
        screen._log_examine_ref_entries = {}
        screen._log_examine_ref_counter = 0
        markup, _animated = format_kivy_log_entry('\x1b[92mTessa Harrow\x1b[0m: "Hold the gate."')

        annotated = screen._annotate_log_examine_markup(markup)

        self.assertIn("[ref=log_examine_", annotated)
        entry = next(iter(screen._log_examine_ref_entries.values()))
        self.assertEqual(entry.title, "Tessa Harrow")
        self.assertEqual(entry.category, "Character")

    def test_left_log_known_location_registers_examine_ref_and_survives_panel_reset(self) -> None:
        screen = GameScreen.__new__(GameScreen)
        game = SimpleNamespace(
            state=SimpleNamespace(current_scene="glasswater_intake"),
            SCENE_LABELS={"glasswater_intake": "Glasswater Intake"},
            SCENE_OBJECTIVES={"glasswater_intake": "Stabilize the headgate."},
            hud_location_label=lambda: "Glasswater Intake",
        )
        screen.bridge = SimpleNamespace(game=game)
        screen._examine_ref_entries = {"examine_1": ExamineEntry("Grit", "Resource", "Pressure.")}
        screen._examine_ref_counter = 1
        screen._log_examine_ref_entries = {}
        screen._log_examine_ref_counter = 0
        markup, _animated = format_kivy_log_entry("The Glasswater Intake wheel shudders.")

        annotated = screen._annotate_log_examine_markup(markup)
        screen._reset_examine_refs()

        self.assertIn("[ref=log_examine_", annotated)
        self.assertEqual(screen._examine_ref_entries, {})
        entry = next(iter(screen._log_examine_ref_entries.values()))
        self.assertEqual(entry.title, "Glasswater Intake")
        self.assertEqual(entry.category, "Location")

    def test_quit_command_button_uses_danger_highlight(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)

        screen._sync_command_button_states()

        quit_button = screen.command_buttons_by_command["quit"]
        self.assertEqual(tuple(quit_button.background_color), screen.theme["choice_end_turn_bg"])
        self.assertEqual(tuple(quit_button.color), screen.theme["choice_end_turn_text"])

    def test_native_command_pane_uses_full_right_column_and_close_button(self) -> None:
        assert Window is not None
        screen = GameScreen()
        self.addCleanup(lambda: Window.unbind(on_key_down=screen._handle_window_key_down))
        self.addCleanup(screen.clear_widgets)
        screen.bridge.game = self.make_native_command_game()

        screen.show_native_command_pane("map")

        self.assertIs(screen.prompt_label.parent, screen.left_column)
        self.assertIs(screen.options_area.parent, screen.left_column)
        self.assertIs(screen.commands.parent, screen.left_column)
        self.assertEqual(screen._side_panel_mode, "native_command")
        self.assertEqual(screen._side_command_title, "Map")
        self.assertEqual(screen.command_workspace.mode, "map")
        self.assertTrue(screen.side_command_header.disabled)
        self.assertEqual(screen.side_command_header.height, 0)
        self.assertEqual(screen.side_command_title_label.text, "")
        self.assertFalse(screen.command_workspace.disabled)
        self.assertEqual(screen.command_workspace.opacity, 1)
        self.assertTrue(screen.combat_stats_scroll.disabled)
        self.assertEqual(screen.combat_stats_scroll.height, 0)
        self.assertFalse(
            screen._touch_hits_side_command_close_button(
                SimpleNamespace(pos=screen.side_command_close_button.center)
            )
        )
        command_nav = next(widget for widget in screen.command_workspace.children if getattr(widget, "cols", None) == 6)
        close_button = next(button for button in command_nav.children if getattr(button, "text", "") == "X")

        close_button.dispatch("on_release")

        self.assertEqual(screen._side_panel_mode, "default")
        self.assertIs(screen.prompt_label.parent, screen)
        self.assertIs(screen.options_area.parent, screen)
        self.assertIs(screen.commands.parent, screen)

    def make_native_command_game(self) -> TextDnDGame:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None)
        game.state = GameState(
            player=player,
            companions=[create_tolan_ironshield()],
            camp_companions=[create_elira_dawnmantle()],
            current_scene="iron_hollow_hub",
            gold=125,
            inventory={
                "potion_healing": 1,
                "travel_biscuits": 3,
                "longsword_common": 1,
                "iron_cap_common": 1,
            },
        )
        game.add_journal("The road ledger keeps Vale's promise in black ink.")
        game.add_clue("A chalk mark dries on the wagon board.")
        game.ensure_state_integrity()
        return game

    def walk_widget_tree(self, widget):
        yield widget
        for child in getattr(widget, "children", []):
            yield from self.walk_widget_tree(child)

    def test_native_command_workspace_renders_panes_refreshes_camp_and_goes_back(self) -> None:
        assert NativeCommandWorkspace is not None
        game = self.make_native_command_game()
        closed: list[bool] = []
        started_talk: list[int] = []
        screen = SimpleNamespace(
            theme=GameScreen.DARK_THEME,
            width=480,
            active_game=lambda: game,
            close_side_command_panel=lambda: closed.append(True),
            start_camp_companion_talk=lambda index: started_talk.append(index),
            _apply_font=lambda _widget, _role: None,
            side_command_title_label=SimpleNamespace(text=""),
        )
        workspace = NativeCommandWorkspace(screen)
        workspace.width = 480
        workspace.show()

        self.assertFalse(workspace._compact_layout())
        nav = workspace._command_nav("camp")
        nav_buttons = list(nav.children)
        close_button = nav_buttons[0]
        regular_button = nav_buttons[-1]
        self.assertLess(close_button.width, regular_button.width)
        self.assertEqual(regular_button.halign, "center")
        self.assertGreater(float(regular_button.font_size), float(close_button.font_size))
        workspace.render_command("journal")
        self.assertEqual(workspace.mode, "journal")
        workspace.render_command("map")
        self.assertEqual(workspace.mode, "map")
        self.assertEqual(workspace.map_view_key, "route")
        self.assertIsInstance(workspace.map_view, NativeMapView)
        self.assertFalse(workspace.map_view.disabled)
        self.assertGreater(workspace.map_view.height, 0)
        workspace.render_map(view="ledger")
        self.assertEqual(workspace.map_view_key, "ledger")
        self.assertTrue(workspace.map_view.disabled)
        workspace.render_inventory(filter_key="consumables")
        self.assertEqual(workspace.inventory_filter_key, "consumables")
        filter_grids = [
            widget
            for widget in workspace.children
            if getattr(widget, "cols", None) == 2 and getattr(widget, "rows", None) == 4
        ]
        self.assertTrue(filter_grids)
        filter_button_text = "\n".join(getattr(button, "text", "") for button in filter_grids[0].children)
        self.assertIn("[b]All Items[/b]", filter_button_text)
        self.assertIn("7 items", filter_button_text)
        self.assertIn("[b]Consumables[/b]", filter_button_text)
        self.assertIn("1 item", filter_button_text)
        workspace.render_gear(selected_slot="head")
        self.assertEqual(workspace.gear_selected_slot, "head")
        workspace.render_camp(view="recovery")
        self.assertEqual(workspace.camp_view, "recovery")
        workspace.render_camp(view="talk")
        talk_buttons = [
            widget
            for widget in self.walk_widget_tree(workspace)
            if getattr(widget, "text", "").startswith("Tolan")
        ]
        self.assertTrue(talk_buttons)
        talk_buttons[0].dispatch("on_release")
        self.assertEqual(started_talk, [0])

        workspace.refresh_active()
        self.assertEqual(workspace.mode, "camp")
        self.assertEqual(workspace.camp_view, "talk")

        workspace.go_back()
        self.assertEqual(workspace.camp_view, "overview")
        workspace.go_back()
        self.assertEqual(closed, [True])


if __name__ == "__main__":
    unittest.main()
