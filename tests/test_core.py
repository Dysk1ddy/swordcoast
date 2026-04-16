from __future__ import annotations

import io
import json
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from collections import Counter
from unittest.mock import patch

import dnd_game.gameplay.base as gameplay_base
from dnd_game.content import (
    BACKGROUNDS,
    CLASSES,
    PRESET_CHARACTERS,
    RACES,
    build_character,
    create_bryn_underbough,
    create_elira_dawnmantle,
    create_enemy,
    create_kaelis_starling,
    create_nim_ardentglass,
    create_rhogar_valeguard,
    create_irielle_ashwake,
    create_tolan_ironshield,
    point_buy_total,
)
from dnd_game.dice import roll, roll_d20
from dnd_game.game import Encounter, TextDnDGame
from dnd_game.gameplay.combat_flow import TurnState
from dnd_game.gameplay.sound_effects import SFX_ASSET_DIR, SOUND_EFFECT_FILES
from dnd_game.gameplay.spell_slots import spell_slot_counts
from dnd_game.data.story.lore import APPENDIX_LORE
from dnd_game.data.quests import QuestLogEntry
from dnd_game.items import ITEMS, format_inventory_line
from dnd_game.models import GameState
from dnd_game.gameplay.status_effects import STATUS_DEFINITIONS
from dnd_game.ui.colors import colorize, strip_ansi
from dnd_game.ui.rich_render import RICH_AVAILABLE


class CoreTests(unittest.TestCase):
    class _SceneExit(RuntimeError):
        pass

    def plain_output(self, lines: list[str]) -> str:
        return strip_ansi("\n".join(lines))

    def test_point_buy_total(self) -> None:
        scores = {"STR": 15, "DEX": 14, "CON": 13, "INT": 10, "WIS": 10, "CHA": 8}
        self.assertEqual(point_buy_total(scores), 25)

    def test_roll_functions_use_rng_animation_hook(self) -> None:
        rng = random.Random(9001)
        calls: list[str] = []
        rng.dice_roll_animator = lambda **payload: calls.append(payload["kind"])
        roll("1d6", rng)
        roll_d20(rng)
        self.assertEqual(calls, ["roll", "d20"])

    def test_roll_animation_payload_can_include_display_bonus(self) -> None:
        rng = random.Random(90011)
        payloads: list[dict[str, object]] = []
        rng.dice_roll_display_bonus = 3
        rng.dice_roll_animator = lambda **payload: payloads.append(payload)
        roll("1d8", rng)
        self.assertEqual(payloads[-1]["modifier"], 0)
        self.assertEqual(payloads[-1]["display_modifier"], 3)

    def test_game_disables_dice_animation_for_custom_io_by_default(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9002))
        self.assertFalse(game.animate_dice)
        self.assertFalse(hasattr(game.rng, "dice_roll_animator"))

    def test_game_can_enable_dice_animation_explicitly(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9003), animate_dice=True)
        self.assertTrue(game.animate_dice)
        self.assertTrue(callable(getattr(game.rng, "dice_roll_animator", None)))

    def test_game_disables_output_pacing_and_dialogue_typing_for_custom_io_by_default(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90031))
        self.assertFalse(game.pace_output)
        self.assertFalse(game.type_dialogue)

    def test_game_disables_sound_effects_for_custom_io_by_default(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900311))
        self.assertFalse(game.sound_effects_enabled)

    def test_game_disables_music_for_custom_io_by_default(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900312))
        self.assertFalse(game.music_enabled)

    def test_sound_effect_library_contains_expected_files(self) -> None:
        self.assertEqual(len(SOUND_EFFECT_FILES), 11)
        self.assertEqual(set(SOUND_EFFECT_FILES), {
            "fight_victory",
            "dice_roll",
            "game_over",
            "skill_success",
            "skill_fail",
            "buy_item",
            "sell_item",
            "player_attack",
            "enemy_attack",
            "player_heal",
            "enemy_heal",
        })

    def test_generated_sound_effect_manifest_matches_asset_files(self) -> None:
        manifest = json.loads((SFX_ASSET_DIR / "manifest.json").read_text(encoding="utf-8"))
        generated = {entry["filename"] for entry in manifest["effects"]}
        expected = set(SOUND_EFFECT_FILES.values())
        self.assertEqual(generated, expected)
        self.assertEqual({path.name for path in SFX_ASSET_DIR.glob("*.wav")}, expected)
        self.assertTrue(all(0.5 <= entry["duration_seconds"] <= 2.0 for entry in manifest["effects"]))

    def test_attack_and_heal_sound_routing_matches_actor_side(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900312))
        played: list[str] = []
        game.play_sound_effect = lambda effect_name, cooldown=0.0: played.append(effect_name)
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        enemy = create_enemy("bandit")
        game.play_attack_sound_for(player)
        game.play_attack_sound_for(enemy)
        game.play_heal_sound_for(player)
        game.play_heal_sound_for(enemy)
        self.assertEqual(played, ["player_attack", "enemy_attack", "player_heal", "enemy_heal"])

    def test_d20_animation_payload_includes_target_number_for_checks(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        payloads: list[dict[str, object]] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9004))
        game.rng.dice_roll_animator = lambda **payload: payloads.append(payload)
        game.skill_check(player, "Athletics", 14, context="to scale the wall")
        self.assertEqual(payloads[-1]["kind"], "d20")
        self.assertEqual(payloads[-1]["target_number"], 14)
        self.assertEqual(payloads[-1]["target_label"], "DC 14")
        self.assertEqual(payloads[-1]["modifier"], player.skill_bonus("Athletics"))

    def test_initiative_rolls_are_batched_into_shared_animation(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        enemy = create_enemy("goblin_skirmisher")
        payloads: list[dict[str, object]] = []
        batched_entries: list[dict[str, object]] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90041))
        game.rng.dice_roll_animator = lambda **payload: payloads.append(payload)
        game.animate_initiative_rolls = lambda entries: batched_entries.extend(entries)
        initiative = game.roll_initiative([player], [enemy])
        self.assertEqual([actor.name for actor in initiative], [player.name, enemy.name])
        self.assertEqual(payloads, [])
        self.assertEqual([entry["actor"].name for entry in batched_entries], [player.name, enemy.name])
        self.assertTrue(all(entry["outcome"].kept + entry["modifier"] == entry["total"] for entry in batched_entries))

    def test_game_uses_updated_dice_animation_timing_window(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9005), animate_dice=True)
        self.assertEqual(game._dice_animation_min_seconds, 0.85)
        self.assertEqual(game._dice_animation_max_seconds, 1.75)

    def test_dialogue_typewriter_uses_fixed_character_rate(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9006))
        delays: list[float] = []
        game.typewrite_text = lambda text, *, delay: delays.append(delay)
        with patch("dnd_game.gameplay.base.sys.stdout", io.StringIO()):
            game.typewrite_dialogue_line("Mira Thann", "Hold the line.")
            game.typewrite_dialogue_line("Mira Thann", "Hold the line. Fall back to the cart.")
        self.assertEqual(delays, [0.03, 0.03])

    def test_typewriter_pauses_after_each_sentence_for_dialogue_and_narration(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=print, rng=random.Random(90063), type_dialogue=True)
        game.output_fn = lambda _: None
        buffer = io.StringIO()
        sleeps: list[float] = []
        game.sleep_for_animation = lambda duration, require_animation=False: sleeps.append(duration) or False
        with patch("dnd_game.gameplay.base.sys.stdout", buffer):
            game.typewrite_dialogue_line("Mira Thann", "Hold the line. Fall back!")
            game.typewrite_narration("A shape moves in the fog. Steel flashes!")
        pause_calls = [duration for duration in sleeps if duration == 0.75]
        self.assertEqual(len(pause_calls), 4)

    def test_health_bar_summary_uses_blocks_and_numbers(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90064))
        summary = strip_ansi(game.format_health_bar(9, 12))
        self.assertEqual(summary, "HP [█████████   ]  9/12")

    def test_health_bar_thresholds_match_requested_breakpoints(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900641))
        self.assertEqual(game.health_bar_color(11, 20), "light_green")
        self.assertEqual(game.health_bar_color(10, 20), "yellow")
        self.assertEqual(game.health_bar_color(5, 20), "light_red")

    def test_typewriter_skip_fast_forwards_remaining_text(self) -> None:
        game = TextDnDGame(input_fn=input, output_fn=print, rng=random.Random(900642), type_dialogue=True)
        game.output_fn = lambda _: None
        buffer = io.StringIO()
        skip_calls = iter([False, True])
        game.animation_skip_requested = lambda **kwargs: next(skip_calls, True)
        game.sleep_for_animation = lambda duration, require_animation=False: False
        with patch("dnd_game.gameplay.base.sys.stdout", buffer):
            game.typewrite_text("Hold fast.", delay=0.1)
        self.assertEqual(buffer.getvalue(), "Hold fast.")

    def test_animation_skip_scope_consumes_only_one_enter_press(self) -> None:
        game = TextDnDGame(input_fn=input, output_fn=print, rng=random.Random(900643), animate_dice=True)
        queued_keys = ["\r", "\r"]
        fake_console = SimpleNamespace(
            kbhit=lambda: bool(queued_keys),
            getwch=lambda: queued_keys.pop(0),
        )
        fake_stdin = SimpleNamespace(isatty=lambda: True)
        with patch.object(gameplay_base, "msvcrt", fake_console), patch.object(gameplay_base.sys, "stdin", fake_stdin):
            game.begin_animation_skip_scope()
            try:
                self.assertTrue(game.animation_skip_requested())
                self.assertFalse(game.animation_skip_requested())
                self.assertEqual(queued_keys, [])
                queued_keys.append("\r")
            finally:
                game.end_animation_skip_scope()
            game.begin_animation_skip_scope()
            try:
                self.assertTrue(game.animation_skip_requested())
            finally:
                game.end_animation_skip_scope()

    def test_typed_scenario_text_uses_narration_typewriter_path(self) -> None:
        log: list[str] = []
        typed: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=print, rng=random.Random(90062), type_dialogue=True)
        game.output_fn = log.append
        game.typewrite_narration = lambda text: typed.append(text)
        game.say("A new danger waits on the road.", typed=True)
        self.assertEqual(typed, ["A new danger waits on the road."])
        self.assertEqual(log, [])

    def test_only_npc_dialogue_uses_typewriter_path(self) -> None:
        log: list[str] = []
        typed: list[tuple[str, str]] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=print, rng=random.Random(90061), type_dialogue=True)
        game.output_fn = log.append
        game.typewrite_dialogue_line = lambda speaker_name, text: typed.append((speaker_name, text))
        game.speaker("Mira Thann", "Move quickly.")
        game.player_speaker("I am moving.")
        self.assertEqual(len(typed), 1)
        self.assertEqual(typed[0][1], "Move quickly.")
        rendered = self.plain_output(log)
        self.assertIn('You: "I am moving."', rendered)

    def test_player_choice_output_calls_choice_pause_hook(self) -> None:
        pauses: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9007))
        game.pause_for_choice_resolution = lambda: pauses.append("pause")
        game.player_choice_output(game.action_option("Take the ridge and move."))
        self.assertEqual(pauses, ["pause"])

    def test_scenario_choice_reveals_options_one_by_one(self) -> None:
        pauses: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90073))
        game.pause_for_option_reveal = lambda: pauses.append("pause")
        choice = game.scenario_choice("Choose a path.", ["First", "Second", "Third"], allow_meta=False)
        self.assertEqual(choice, 1)
        self.assertEqual(pauses, ["pause", "pause"])

    def test_dice_animation_skip_fast_forwards_but_keeps_final_pause(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90071), animate_dice=True)
        rendered: list[bool] = []
        waits: list[tuple[float, bool]] = []
        game.render_dice_animation_frame = lambda *args, **kwargs: rendered.append(kwargs["final"])
        game.sleep_for_dice_animation = lambda duration: True
        game.sleep_for_animation = lambda duration, require_animation=False: waits.append((duration, require_animation)) or False
        sounds: list[str] = []
        game.play_sound_effect = lambda effect_name, cooldown=0.0: sounds.append(effect_name)
        game.animate_dice_roll(kind="d20", expression="d20", sides=20, rolls=[14], kept=14)
        self.assertEqual(rendered, [False, True])
        self.assertEqual(sounds, ["dice_roll"])
        self.assertEqual(waits, [(0.28, True), (0.42, True)])

    def test_skill_check_plays_success_and_failure_sounds(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900711))
        sounds: list[str] = []
        game.play_sound_effect = lambda effect_name, cooldown=0.0: sounds.append(effect_name)
        game.roll_with_advantage = lambda actor, advantage_state: SimpleNamespace(kept=18)
        self.assertTrue(game.skill_check(player, "Athletics", 12, context="to clear the ledge"))
        game.roll_with_advantage = lambda actor, advantage_state: SimpleNamespace(kept=2)
        self.assertFalse(game.skill_check(player, "Athletics", 20, context="to clear the ledge"))
        self.assertEqual(sounds, ["skill_success", "skill_fail"])

    def test_d20_animation_shows_raw_roll_then_final_total_after_pause(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90072), animate_dice=True)
        rendered: list[tuple[str, bool, int, int | None]] = []
        totals: list[tuple[int, int, int | None, str | None]] = []
        game.render_dice_animation_frame = (
            lambda label, rolls, **kwargs: rendered.append((label, kwargs["final"], rolls[-1], kwargs.get("target_number")))
        )
        game.render_dice_animation_total_frame = (
            lambda **kwargs: totals.append(
                (kwargs["kept"], kwargs["modifier"], kwargs.get("target_number"), kwargs.get("target_label"))
            )
        )
        game.sleep_for_dice_animation = lambda duration: True
        waits: list[tuple[float, bool]] = []
        game.sleep_for_animation = lambda duration, require_animation=False: waits.append((duration, require_animation)) or False
        game.animate_dice_roll(
            kind="d20",
            expression="d20",
            sides=20,
            rolls=[9],
            kept=9,
            modifier=5,
            target_number=14,
            target_label="DC 14",
        )
        self.assertEqual(len(rendered), 2)
        self.assertEqual(rendered[0][0], "Rolling d20")
        self.assertFalse(rendered[0][1])
        self.assertEqual(rendered[0][3], 14)
        self.assertEqual(rendered[1], ("Rolled d20", True, 9, 14))
        self.assertEqual(totals, [(9, 5, 14, "DC 14")])
        self.assertEqual(waits, [(0.28, True), (0.42, True)])

    def test_damage_roll_animation_shows_final_total_after_pause(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90074), animate_dice=True)
        rendered: list[tuple[str, bool, list[int]]] = []
        totals: list[tuple[list[int], int]] = []
        game.render_dice_animation_frame = lambda label, rolls, **kwargs: rendered.append((label, kwargs["final"], list(rolls)))
        game.render_roll_animation_total_frame = lambda **kwargs: totals.append((list(kwargs["rolls"]), kwargs["modifier"]))
        game.sleep_for_dice_animation = lambda duration: True
        waits: list[tuple[float, bool]] = []
        game.sleep_for_animation = lambda duration, require_animation=False: waits.append((duration, require_animation)) or False
        game.animate_dice_roll(kind="roll", expression="1d8", sides=8, rolls=[7], modifier=0, display_modifier=3)
        self.assertEqual(len(rendered), 2)
        self.assertEqual(rendered[0][0], "Rolling 1d8")
        self.assertFalse(rendered[0][1])
        self.assertEqual(rendered[1], ("Rolled 1d8", True, [7]))
        self.assertEqual(totals, [([7], 3)])
        self.assertEqual(waits, [(0.28, True), (0.42, True)])

    def test_run_encounter_calls_combat_transition_pause_hook(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        enemy = create_enemy("goblin_skirmisher")
        enemy.current_hp = 0
        enemy.dead = True
        pauses: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(9008))
        game.state = GameState(player=player, current_scene="road_ambush")
        game.pause_for_combat_transition = lambda: pauses.append("pause")
        outcome = game.run_encounter(Encounter(title="Spent Ambush", description="The danger is already over.", enemies=[enemy]))
        self.assertEqual(outcome, "victory")
        self.assertEqual(pauses, ["pause", "pause"])

    def test_apply_damage_triggers_health_bar_animation_on_hp_loss(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90085))
        seen: list[tuple[int, int]] = []
        game.animate_health_bar_loss = lambda target, previous_hp, new_hp: seen.append((previous_hp, new_hp))
        actual = game.apply_damage(player, 3)
        self.assertEqual(actual, 3)
        self.assertEqual(seen, [(player.max_hp, player.max_hp - 3)])

    def test_health_bar_animation_skip_jumps_to_final_value(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=input, output_fn=print, rng=random.Random(90086))
        game.pace_output = True
        buffer = io.StringIO()
        calls = iter([False, True])
        game.sleep_for_animation = lambda duration, require_animation=False: next(calls, True)
        with patch("dnd_game.gameplay.base.sys.stdout", buffer):
            game.animate_health_bar_loss(player, player.max_hp, player.max_hp - 4)
        rendered = strip_ansi(buffer.getvalue())
        self.assertIn(f"{player.max_hp - 4}/{player.max_hp}", rendered)

    def test_collect_loot_reveals_each_drop_with_pause_hook(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90082))
        game.state = GameState(player=player, current_scene="road_ambush", inventory={})
        pauses: list[str] = []
        game.pause_for_loot_reveal = lambda: pauses.append("pause")
        with patch("dnd_game.gameplay.inventory_core.roll_loot_for_enemy", return_value={"bread_round": 1, "potion_healing": 1}):
            game.collect_loot([create_enemy("bandit")], source="Roadside Ambush")
        self.assertEqual(pauses, ["pause", "pause"])

    def test_speaker_introduces_new_named_npc_once(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(90083))
        game.state = GameState(player=player, current_scene="neverwinter_briefing")
        game.speaker("Mira Thann", "The road south is failing.")
        game.speaker("Mira Thann", "We need it secured.")
        rendered = self.plain_output(log)
        self.assertEqual(rendered.count("Mira Thann is a sharp-eyed Neverwinter officer"), 1)

    def test_run_encounter_introduces_unique_enemy_before_fight(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        enemy = create_enemy("rukhar")
        enemy.current_hp = 0
        enemy.dead = True
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(90084))
        game.state = GameState(player=player, current_scene="ashfall_watch")
        outcome = game.run_encounter(Encounter(title="Rukhar Test", description="The sergeant waits in smoke.", enemies=[enemy]))
        self.assertEqual(outcome, "victory")
        rendered = self.plain_output(log)
        self.assertIn("Rukhar Cinderfang is a broad hobgoblin sergeant", rendered)

    def test_phandalin_arrival_action_choice_renders_as_action_not_speech(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["3", "10", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(90081))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            clues=["one", "two"],
            flags={"miners_exchange_lead": True},
        )
        game.skill_check = lambda actor, skill, dc, context: False
        game.scene_phandalin_hub()
        rendered = self.plain_output(log)
        self.assertIn("*Show me the tracks, barricades, and weak points first.", rendered)
        self.assertNotIn('Velkor: "Show me the tracks, barricades, and weak points first."', rendered)

    def test_map_state_initializes_for_phandalin_hub(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90082))
        game.state = GameState(player=player, current_scene="phandalin_hub", flags={"phandalin_arrived": True})
        game.ensure_state_integrity()
        self.assertEqual(game.state.flags["map_state"]["current_node_id"], "phandalin_hub")
        self.assertIsNone(game.state.flags["map_state"]["current_dungeon_id"])
        self.assertIn("phandalin_hub", game.state.flags["map_state"]["visited_nodes"])

    def test_old_owl_well_branching_tracks_cleared_rooms(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1", "2", "1", "1", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(90083))
        game.state = GameState(
            player=player,
            current_scene="old_owl_well",
            flags={"miners_exchange_lead": True},
        )
        game.run_encounter = lambda encounter: "victory"
        game.scene_old_owl_well()
        self.assertEqual(game.state.current_scene, "phandalin_hub")
        self.assertEqual(game.state.flags["map_state"]["current_node_id"], "phandalin_hub")
        self.assertCountEqual(
            game.state.flags["map_state"]["cleared_rooms"],
            ["well_ring", "supply_trench", "gravecaller_lip"],
        )

    def test_old_owl_well_vaelith_miniboss_uses_buffed_encounter_setup(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companions = [create_tolan_ironshield(), create_elira_dawnmantle(), create_kaelis_starling()]
        answers = iter(["1", "2", "1", "1", "1"])
        encounters: list[Encounter] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(900831))
        game.state = GameState(
            player=player,
            companions=companions,
            current_scene="old_owl_well",
            flags={"miners_exchange_lead": True},
        )

        def capture_encounter(encounter):
            encounters.append(encounter)
            return "victory"

        game.run_encounter = capture_encounter  # type: ignore[method-assign]
        game.scene_old_owl_well()
        boss_encounter = next(encounter for encounter in encounters if encounter.title == "Miniboss: Vaelith Marr")
        self.assertEqual(len(boss_encounter.enemies), 3)
        self.assertEqual(boss_encounter.enemies[0].name, "Vaelith Marr")
        self.assertEqual(boss_encounter.enemies[0].archetype, "vaelith_marr")
        self.assertGreater(boss_encounter.enemies[0].max_hp, 26)
        self.assertTrue(any(enemy.name == "Carrion Lash Crawler" for enemy in boss_encounter.enemies[1:]))

    def test_phandalin_hub_marks_wyvern_tor_as_recommended_level_three_when_underleveled(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        captured: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900832))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            flags={"phandalin_arrived": True, "edermath_orchard_lead": True, "miners_exchange_lead": True},
        )
        game.run_phandalin_council_event = lambda: None  # type: ignore[method-assign]
        game.run_after_watch_gathering = lambda: None  # type: ignore[method-assign]

        def capture_choice(prompt: str, options: list[str], **kwargs) -> int:
            if prompt == "Where do you go next?":
                captured.extend(options)
                raise self._SceneExit()
            return 1

        game.scenario_choice = capture_choice  # type: ignore[method-assign]
        with self.assertRaises(self._SceneExit):
            game.scene_phandalin_hub()
        self.assertIn("*Hunt the raiders at Wyvern Tor (recommended level 3)", captured)

    def test_confirm_wyvern_tor_departure_can_cancel_underleveled_trip(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900833))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.scenario_choice = lambda prompt, options, **kwargs: 2  # type: ignore[method-assign]
        self.assertFalse(game.confirm_wyvern_tor_departure())

    def test_tresendar_encounters_scale_up_for_full_party(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companions = [create_tolan_ironshield(), create_elira_dawnmantle(), create_kaelis_starling()]
        encounters: list[Encounter] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900834))
        game.state = GameState(
            player=player,
            companions=companions,
            current_scene="tresendar_manor",
            flags={"tresendar_revealed": True},
        )
        game.ensure_state_integrity()
        dungeon = game.current_act1_dungeon()
        assert dungeon is not None
        game.run_encounter = lambda encounter: encounters.append(encounter) or "victory"  # type: ignore[method-assign]
        game._tresendar_cellar_intake(dungeon, dungeon.rooms["cellar_intake"])
        game._tresendar_nothic_lair(dungeon, dungeon.rooms["nothic_lair"])
        self.assertEqual(len(encounters[0].enemies), 4)
        self.assertEqual(len(encounters[1].enemies), 3)
        self.assertGreater(encounters[1].enemies[0].max_hp, 29)

    def test_emberhall_and_forge_encounters_reinforce_for_full_party(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        act1_companions = [create_tolan_ironshield(), create_elira_dawnmantle(), create_kaelis_starling()]
        act2_companions = [create_rhogar_valeguard(), create_elira_dawnmantle(), create_nim_ardentglass()]
        encounters: list[Encounter] = []

        act1_game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900835))
        act1_game.state = GameState(player=player, companions=act1_companions, current_scene="emberhall_cellars")
        act1_game.ensure_state_integrity()
        dungeon = act1_game.current_act1_dungeon()
        assert dungeon is not None
        act1_game.run_encounter = lambda encounter: encounters.append(encounter) or "victory"  # type: ignore[method-assign]
        act1_game._emberhall_antechamber(dungeon, dungeon.rooms["antechamber"])
        act1_game._emberhall_black_reserve(dungeon, dungeon.rooms["black_reserve"])
        act1_game._emberhall_varyn_sanctum(dungeon, dungeon.rooms["varyn_sanctum"])
        self.assertEqual(len(encounters[0].enemies), 4)
        self.assertEqual(len(encounters[1].enemies), 4)
        self.assertEqual(len(encounters[2].enemies), 5)
        self.assertGreater(encounters[2].enemies[0].max_hp, 38)

        act2_game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(900836))
        act2_game.state = GameState(
            player=build_character(
                name="Vale",
                race="Human",
                class_name="Fighter",
                background="Soldier",
                base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
                class_skill_choices=["Athletics", "Survival"],
            ),
            companions=act2_companions,
            camp_companions=[create_tolan_ironshield(), create_bryn_underbough(), create_irielle_ashwake()],
            current_scene="forge_of_spells",
            current_act=2,
            flags={"black_lake_barracks_raided": True},
        )
        act2_game.run_encounter = lambda encounter: encounters.append(encounter) or "victory"  # type: ignore[method-assign]
        act2_game.scene_black_lake_causeway()
        act2_game.scene_forge_of_spells()
        self.assertEqual(encounters[3].title, "Black Lake Causeway")
        self.assertEqual(len(encounters[3].enemies), 4)
        self.assertEqual(encounters[4].title, "Boss: Sister Caldra Voss")
        self.assertEqual(len(encounters[4].enemies), 4)
        self.assertGreater(encounters[4].enemies[0].max_hp, 42)

    def test_act1_room_navigation_options_show_direction_tags(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90084))
        game.state = GameState(
            player=player,
            current_scene="old_owl_well",
            flags={"miners_exchange_lead": True},
        )
        game.ensure_state_integrity()
        dungeon = game.current_act1_dungeon()
        assert dungeon is not None
        game.complete_map_room(dungeon, "well_ring")
        option_labels = [label for _, _, label in game.act1_room_navigation_options(dungeon)]
        self.assertIn("[MOVE RIGHT] *Advance to Salt Cart Hollow", option_labels)
        self.assertIn("[MOVE DOWN] *Advance to Supply Trench", option_labels)
        self.assertIn("*Withdraw to Phandalin", option_labels)

    def test_dungeon_map_renders_once_per_room_until_room_changes(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(90085))
        game.state = GameState(
            player=player,
            current_scene="old_owl_well",
            flags={"miners_exchange_lead": True},
        )
        game.ensure_state_integrity()
        dungeon = game.current_act1_dungeon()
        assert dungeon is not None
        game.render_act1_dungeon_map(dungeon)
        first_render_count = len(log)
        game.render_act1_dungeon_map(dungeon)
        self.assertEqual(len(log), first_render_count)
        game.complete_map_room(dungeon, "well_ring")
        game.render_act1_dungeon_map(dungeon)
        self.assertGreater(len(log), first_render_count)
        rerender_count = len(log)
        game.render_act1_dungeon_map(dungeon)
        self.assertEqual(len(log), rerender_count)
        game.set_current_map_room("salt_cart")
        self.assertGreater(len(log), rerender_count)

    def test_travel_to_act1_node_prints_the_updated_overworld_map(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(900851))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            flags={"phandalin_arrived": True, "miners_exchange_lead": True},
        )
        game.ensure_state_integrity()
        game.travel_to_act1_node("old_owl_well")
        rendered = self.plain_output(log)
        self.assertIn("Overworld Route Map", rendered)
        self.assertIn("OLD OWL", rendered)
        self.assertNotIn("Wyvern Tor", rendered)

    def test_set_current_map_room_prints_the_updated_dungeon_map(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(900852))
        game.state = GameState(
            player=player,
            current_scene="old_owl_well",
            flags={"miners_exchange_lead": True, "old_owl_ring_cleared": True},
        )
        game.ensure_state_integrity()
        game.set_current_map_room("salt_cart", announce=True)
        rendered = self.plain_output(log)
        self.assertIn("You move toward salt cart.", rendered)
        self.assertIn("Current room: Salt Cart Hollow", rendered)

    def test_map_menu_offers_overworld_and_dungeon_views(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        captured: dict[str, list[str]] = {}
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90086))
        game.state = GameState(
            player=player,
            current_scene="old_owl_well",
            flags={"miners_exchange_lead": True},
        )
        game.ensure_state_integrity()

        def fake_choose(prompt: str, options: list[str], **kwargs) -> int:
            captured["options"] = options
            return 3

        game.choose = fake_choose  # type: ignore[method-assign]
        game.open_map_menu()
        self.assertEqual(captured["options"], ["Overworld", "Old Owl Well Dig Ring", "Back"])

    def test_help_menu_lists_map_command(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(90087))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        if RICH_AVAILABLE:
            game._interactive_output = True
        game.show_global_commands()
        rendered = self.plain_output(log)
        self.assertIn("Global Commands", rendered)
        self.assertIn("map", rendered)

    def test_build_character_applies_racial_bonus(self) -> None:
        character = build_character(
            name="Nim",
            race="Halfling",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        self.assertEqual(character.ability_scores["DEX"], 17)
        self.assertIn("lucky", character.features)
        self.assertEqual(character.armor_class, 14)

    def test_save_round_trip(self) -> None:
        player = build_character(
            name="Iri",
            race="Human",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        state = GameState(
            player=player,
            current_scene="phandalin_hub",
            clues=["one"],
            journal=["entry"],
            xp=125,
            gold=37,
            inventory={"potion_healing": 2, "bread_round": 3},
            short_rests_remaining=1,
        )
        save_dir = Path.cwd() / "tests_output"
        save_dir.mkdir(exist_ok=True)
        game = TextDnDGame(
            input_fn=lambda _: "2",
            output_fn=lambda _: None,
            save_dir=save_dir,
            rng=random.Random(3),
        )
        game.state = state
        path = game.save_game(slot_name="roundtrip")
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
        restored = GameState.from_dict(loaded)
        self.assertEqual(restored.player.name, "Iri")
        self.assertEqual(restored.current_scene, "phandalin_hub")
        self.assertEqual(restored.clues, ["one"])
        self.assertEqual(restored.xp, 125)
        self.assertEqual(restored.gold, 37)
        self.assertEqual(restored.inventory["potion_healing"], 2)
        self.assertEqual(restored.short_rests_remaining, 1)
        Path(path).unlink(missing_ok=True)

    def test_information_dialogue_can_grant_quest_and_show_in_journal(self) -> None:
        player = build_character(
            name="Iri",
            race="Human",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        answers = iter(["1", "3"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(301))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.visit_steward()
        self.assertIn("secure_miners_road", game.state.quests)
        game.show_journal()
        rendered = self.plain_output(log)
        self.assertIn("Quest Added: Stop the Watchtower Raids", rendered)
        self.assertIn("Active Quests:", rendered)
        self.assertIn("Stop the Watchtower Raids", rendered)

    def test_journal_groups_snapshot_clues_and_recent_updates(self) -> None:
        player = build_character(
            name="Iri",
            race="Human",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(3011))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            clues=["A hidden tunnel runs under the shrine."],
            journal=[
                "Clue: A hidden tunnel runs under the shrine.",
                "Spoke with Sister Garaele about the old shrine.",
                "Recovered a scorched map scrap from the roadside.",
            ],
        )
        game.show_journal()
        rendered = self.plain_output(log)
        self.assertIn("Campaign Snapshot:", rendered)
        self.assertIn("Clue Board:", rendered)
        self.assertIn("Recent Updates:", rendered)
        self.assertIn("Spoke with Sister Garaele", rendered)
        self.assertIn("Recovered a scorched map scrap", rendered)
        self.assertNotIn("Clue: A hidden tunnel runs under the shrine.", rendered)

    def test_ashfall_watch_returns_to_phandalin_and_marks_quests_ready(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["3", "3", "1", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(302))
        game.state = GameState(player=player, current_scene="ashfall_watch", clues=["one", "two"])
        game.grant_quest("secure_miners_road")
        game.run_encounter = lambda encounter: "victory"
        game.scene_ashfall_watch()
        self.assertEqual(game.state.current_scene, "phandalin_hub")
        self.assertTrue(game.state.flags["ashfall_watch_cleared"])
        self.assertEqual(game.state.quests["secure_miners_road"].status, "ready_to_turn_in")

    def test_post_combat_random_encounter_pool_has_fifteen_plus_entries(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(810))
        self.assertGreaterEqual(len(game.post_combat_random_encounter_ids()), 15)

    def test_run_encounter_triggers_post_combat_random_event_after_victory(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(811))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        enemy = create_enemy("bandit")
        enemy.current_hp = 0
        enemy.dead = True
        seen: list[str] = []
        game.maybe_run_post_combat_random_encounter = lambda encounter: seen.append(encounter.title)
        outcome = game.run_encounter(Encounter(title="Spent Ambushers", description="The danger is already over.", enemies=[enemy]))
        self.assertEqual(outcome, "victory")
        self.assertEqual(seen, ["Spent Ambushers"])

    def test_victory_autosaves_are_created_and_pruned_to_limit(self) -> None:
        save_dir = Path.cwd() / "tests_output" / "autosave_rotation"
        save_dir.mkdir(parents=True, exist_ok=True)
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=lambda _: None,
            save_dir=save_dir,
            rng=random.Random(3031),
        )
        game.autosaves_enabled = True
        game.state = GameState(player=player, current_scene="road_ambush")

        try:
            for index in range(17):
                enemy = create_enemy("goblin_skirmisher")
                enemy.dead = True
                enemy.current_hp = 0
                outcome = game.run_encounter(
                    Encounter(
                        title=f"Spent Ambush {index}",
                        description="The danger is already over.",
                        enemies=[enemy],
                    )
                )
                self.assertEqual(outcome, "victory")

            autosaves = sorted(save_dir.glob("autosave__*.json"))
            self.assertEqual(len(autosaves), 15)
            self.assertTrue(all(path.name.startswith("autosave__") for path in autosaves))
        finally:
            for path in save_dir.glob("*.json"):
                path.unlink(missing_ok=True)
            save_dir.rmdir()

    def test_post_combat_random_event_skips_when_roll_misses(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(812))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        calls: list[str] = []
        game.run_named_post_combat_random_encounter = lambda encounter_id: calls.append(encounter_id)
        game.rng = SimpleNamespace(random=lambda: 0.99, choice=lambda options: options[0])
        game.maybe_run_post_combat_random_encounter(Encounter(title="Skipped", description="", enemies=[]))
        self.assertEqual(calls, [])

    def test_post_combat_random_event_skips_for_chained_encounter(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(813))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        calls: list[str] = []
        game.run_named_post_combat_random_encounter = lambda encounter_id: calls.append(encounter_id)
        game.rng = SimpleNamespace(random=lambda: 0.0, choice=lambda options: options[0])
        game.maybe_run_post_combat_random_encounter(
            Encounter(title="Chained", description="", enemies=[], allow_post_combat_random_encounter=False)
        )
        self.assertEqual(calls, [])

    def test_locked_chest_random_encounter_can_award_loot_without_combat(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Sleight of Hand", "Stealth"],
        )
        answers = iter(["2"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(814))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={}, gold=0)
        game.skill_check = lambda actor, skill, dc, context: True
        game.run_named_post_combat_random_encounter("locked_chest_under_ferns")
        self.assertGreater(game.state.gold, 0)
        self.assertEqual(game.state.inventory["potion_healing"], 1)

    def test_random_encounter_rewards_reveal_results_line_by_line(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(812))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={})
        pauses: list[str] = []
        game.pause_for_loot_reveal = lambda: pauses.append("pause")
        game.grant_random_encounter_rewards(reason="the fern-hidden chest", gold=9, items={"potion_healing": 1, "bread_round": 1})
        self.assertEqual(pauses, ["pause", "pause", "pause"])

    def test_random_event_spawned_fight_disables_follow_up_random_encounters(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(815))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        captured: list[Encounter] = []

        def fake_run_encounter(encounter: Encounter) -> str:
            captured.append(encounter)
            return "victory"

        game.run_encounter = fake_run_encounter
        game.run_named_post_combat_random_encounter("abandoned_cottage")
        self.assertEqual(len(captured), 1)
        self.assertFalse(captured[0].allow_post_combat_random_encounter)

    def test_seen_random_encounters_are_weighted_far_lower_than_unseen_ones(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(817))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            flags={"random_encounters_seen": ["locked_chest_under_ferns"]},
        )
        pool = game.weighted_post_combat_random_encounter_pool()
        seen_count = sum(1 for entry in pool if entry[0] == "locked_chest_under_ferns")
        unseen_count = sum(1 for entry in pool if entry[0] == "abandoned_cottage")
        self.assertEqual(seen_count, 1)
        self.assertEqual(unseen_count, 10)

    def test_random_encounter_intro_uses_typed_narration(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        typed: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=print, rng=random.Random(818), type_dialogue=True)
        game.output_fn = lambda _: None
        game.typewrite_narration = lambda text: typed.append(text)
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.random_encounter_intro("A hidden danger waits in the reeds.")
        self.assertEqual(typed, ["A hidden danger waits in the reeds."])

    def test_ashfall_watch_marks_first_encounter_as_chained_for_random_events(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["3", "2", "1", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(816))
        game.state = GameState(player=player, current_scene="ashfall_watch", clues=["one", "two"])
        captured: list[Encounter] = []

        def fake_run_encounter(encounter: Encounter) -> str:
            captured.append(encounter)
            return "victory"

        game.run_encounter = fake_run_encounter
        game.scene_ashfall_watch()
        self.assertEqual(len(captured), 3)
        self.assertFalse(captured[0].allow_post_combat_random_encounter)
        self.assertFalse(captured[1].allow_post_combat_random_encounter)
        self.assertFalse(captured[2].allow_post_combat_random_encounter)

    def test_turning_in_quest_grants_rewards(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(303))
        game.state = GameState(player=player, current_scene="phandalin_hub", flags={"ashfall_watch_cleared": True})
        game.grant_quest("restore_barthen_supplies")
        game.refresh_quest_statuses(announce=False)
        game.visit_barthen_provisions()
        self.assertEqual(game.state.quests["restore_barthen_supplies"].status, "completed")
        self.assertEqual(game.state.gold, 12)
        self.assertEqual(game.state.xp, 30)
        self.assertEqual(game.state.inventory["bread_round"], 2)
        self.assertEqual(game.state.inventory["camp_stew_jar"], 1)

    def test_enemy_template_smoke(self) -> None:
        enemy = create_enemy("rukhar")
        self.assertEqual(enemy.name, "Rukhar Cinderfang")
        self.assertGreater(enemy.max_hp, 20)

    def test_new_race_and_class_options_available(self) -> None:
        self.assertIn("Dragonborn", RACES)
        self.assertIn("Gnome", RACES)
        self.assertIn("Tiefling", RACES)
        self.assertIn("Goliath", RACES)
        self.assertIn("Orc", RACES)
        self.assertIn("Half-Orc", RACES)
        self.assertIn("Barbarian", CLASSES)
        self.assertIn("Bard", CLASSES)
        self.assertIn("Monk", CLASSES)
        self.assertIn("Paladin", CLASSES)
        self.assertIn("Druid", CLASSES)
        self.assertIn("Sorcerer", CLASSES)
        self.assertIn("Warlock", CLASSES)
        self.assertIn("Outlander", BACKGROUNDS)
        self.assertIn("Guild Artisan", BACKGROUNDS)

    def test_item_rarity_distribution_favors_lower_tiers(self) -> None:
        counts = Counter(item.rarity for item in ITEMS.values())
        self.assertGreater(counts["common"], counts["uncommon"])
        self.assertGreater(counts["uncommon"], counts["rare"])
        self.assertGreater(counts["rare"], counts["epic"])
        self.assertGreater(counts["epic"], counts["legendary"])
        self.assertLessEqual(counts["legendary"], 5)

    def test_inventory_line_shows_weapon_damage_and_enchantment_rules(self) -> None:
        line = strip_ansi(format_inventory_line("rapier_rare", 1))
        self.assertIn("1d8 piercing", line)
        self.assertIn("enchantment Vicious", line)
        self.assertIn("+2d6 on crit", line)

    def test_sync_equipment_applies_magic_item_traits(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(500))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        player.equipment_slots = {slot: None for slot in ["head", "ring_1", "ring_2", "neck", "chest", "gloves", "boots", "main_hand", "off_hand", "cape"]}
        player.equipment_slots["main_hand"] = "longsword_uncommon"
        player.equipment_slots["boots"] = "silent_step_boots_uncommon"
        player.equipment_slots["chest"] = "breastplate_epic"
        game.sync_equipment(player)
        self.assertEqual(player.gear_bonuses["initiative"], 1)
        self.assertEqual(player.gear_bonuses["stealth_advantage"], 1)
        self.assertEqual(player.gear_bonuses["resist_lightning"], 1)

    def test_consumable_can_grant_temporary_resistance(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(501))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={"fireward_elixir": 1})
        used = game.use_item_from_inventory()
        self.assertTrue(used)
        self.assertIn("resist_fire", player.conditions)
        self.assertEqual(game.apply_damage(player, 10, damage_type="fire"), 5)

    def test_character_creation_and_briefing_flow(self) -> None:
        answers = iter(
            [
                "2",  # custom character
                "Aric",  # name
                "1", "1",  # race select + confirm
                "1", "1",  # class select + confirm
                "1", "1",  # background select + confirm
                "1",  # standard array
                "1", "1", "1", "1", "1", "1",  # assign array
                "1", "1",  # fighter skills
                "1",  # confirm character
                "1",  # soldier prologue choice
                "6",  # take the writ
                "1",  # recruit Kaelis on departure
            ]
        )
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(7))
        game.start_new_game()
        self.assertIsNotNone(game.state)
        self.assertEqual(game.state.current_scene, "background_prologue")
        game.run_encounter = lambda encounter: "victory"
        game.scene_background_prologue()
        self.assertEqual(game.state.current_scene, "neverwinter_briefing")
        game.scene_neverwinter_briefing()
        self.assertEqual(game.state.current_scene, "road_ambush")
        self.assertTrue(any(companion.name in {"Kaelis Starling", "Rhogar Valeguard"} for companion in game.state.companions))

    def test_can_recruit_companion_before_first_fight(self) -> None:
        answers = iter(
            [
                "2",
                "Aric",
                "1", "1",
                "1", "1",
                "1", "1",
                "1",
                "1", "1", "1", "1", "1", "1",
                "1", "1",
                "1",
                "1",  # soldier prologue choice
                "6",  # take the writ
                "1",  # recruit Kaelis on departure
            ]
        )
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(8))
        game.start_new_game()
        game.run_encounter = lambda encounter: "victory"
        game.scene_background_prologue()
        game.scene_neverwinter_briefing()
        self.assertEqual(game.state.current_scene, "road_ambush")
        self.assertTrue(any(companion.name == "Kaelis Starling" for companion in game.state.companions))

    def test_road_ambush_flow_recruits_tolan(self) -> None:
        player = build_character(
            name="Vale",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(4))
        game.state = GameState(player=player, current_scene="road_ambush", clues=[], journal=[])
        game.run_encounter = lambda encounter: "victory"
        game.scene_road_ambush()
        self.assertEqual(game.state.current_scene, "phandalin_hub")
        self.assertTrue(any(companion.name == "Tolan Ironshield" for companion in game.state.companions))
        rendered = self.plain_output(log)
        self.assertIn("Tolan Ironshield: \"Good. Give me a minute to cinch the shield", rendered)

    def test_point_buy_character_creation_flow(self) -> None:
        answers = iter(
            [
                "2",
                "Mira",
                "1", "1",
                "1", "1",
                "1", "1",
                "2",
                "15",
                "14",
                "13",
                "10",
                "10",
                "8",
                "1",
                "1",       # skill 1
                "1",       # skill 2
                "1",       # confirm character
            ]
        )
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(9))
        game.start_new_game()
        self.assertIsNotNone(game.state)
        self.assertEqual(game.state.player.ability_scores["STR"], 16)
        self.assertEqual(game.state.player.ability_scores["CHA"], 9)

    def test_preset_character_creation_flow(self) -> None:
        answers = iter(
            [
                "1",  # preset character
                "3",  # Fighter preset
                "1",  # lock preset
                "1",  # begin adventure
            ]
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(44))
        game.start_new_game()
        self.assertIsNotNone(game.state)
        self.assertEqual(game.state.player.class_name, "Fighter")
        self.assertEqual(game.state.player.name, PRESET_CHARACTERS["Fighter"]["name"])
        rendered = self.plain_output(log)
        self.assertIn("3. Fighter", rendered)
        self.assertNotIn(f"3. Fighter: {PRESET_CHARACTERS['Fighter']['description']}", rendered)
        self.assertIn(PRESET_CHARACTERS["Fighter"]["name"], rendered)
        self.assertIn("Preset abilities:", rendered)
        self.assertIn("Starting point:", rendered)

    def test_background_prologues_converge_to_neverwinter_briefing(self) -> None:
        for background in BACKGROUNDS:
            with self.subTest(background=background):
                player = build_character(
                    name="Vale",
                    race="Human",
                    class_name="Fighter",
                    background=background,
                    base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
                    class_skill_choices=["Athletics", "Survival"],
                )
                game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(445))
                game.state = GameState(player=player, current_scene="background_prologue")
                game.skill_check = lambda actor, skill, dc, context: True
                game.run_encounter = lambda encounter: "victory"
                game.scene_background_prologue()
                self.assertEqual(game.state.current_scene, "neverwinter_briefing")
                self.assertEqual(game.state.flags["background_prologue_completed"], background)

    def test_background_prologue_shows_starting_rundown(self) -> None:
        player = build_character(
            name="Ash",
            race="Human",
            class_name="Cleric",
            background="Acolyte",
            base_ability_scores={"STR": 10, "DEX": 12, "CON": 13, "INT": 10, "WIS": 15, "CHA": 14},
            class_skill_choices=["Medicine", "Persuasion"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(446))
        game.state = GameState(player=player, current_scene="background_prologue")
        game.skill_check = lambda actor, skill, dc, context: True
        game.run_encounter = lambda encounter: "victory"
        game.scene_background_prologue()
        rendered = self.plain_output(log)
        self.assertIn("Acolyte Prologue: Hall of Justice Hospice", rendered)
        self.assertIn("Starting point:", rendered)
        self.assertIn("poisoned teamster", rendered)

    def test_lore_codex_can_browse_world_entry(self) -> None:
        answers = iter(["1", "4", "2", "10", "2"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(440))
        game.show_lore_notes()
        rendered = self.plain_output(log)
        self.assertIn("=== Lore Codex ===", rendered)
        self.assertIn("=== World & Locations: Neverwinter ===", rendered)
        self.assertIn("Jewel of the North", rendered)

    def test_lore_codex_skills_section_has_visible_exit(self) -> None:
        answers = iter(["6", "1", "10", "2"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(442))
        game.show_lore_notes()
        rendered = self.plain_output(log)
        self.assertIn("Browse Skills. (page 1)", rendered)
        self.assertIn("1. Return to lore categories", rendered)

    def test_lore_codex_class_entry_includes_gameplay_manual(self) -> None:
        answers = iter(["2", "2", "2", "10", "2"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(443))
        game.show_lore_notes()
        rendered = self.plain_output(log).replace("\n", " ")
        self.assertIn("Main stats: Strength, Constitution", rendered)
        self.assertIn("Hit die: d12", rendered)
        self.assertIn("Starting abilities:", rendered)
        self.assertIn("Level 2:", rendered)

    def test_lore_codex_includes_appendix_reference_entries(self) -> None:
        answers = iter(["8", "2", "2", "10", "2"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(445))
        game.show_lore_notes()
        rendered = self.plain_output(log)
        self.assertIn("=== Appendices: Appendix A: Conditions ===", rendered)
        self.assertIn("Contents:", rendered)
        self.assertIn("- Unconscious", rendered)
        self.assertGreaterEqual(len(APPENDIX_LORE), 30)
        self.assertIn("Appendix B: Forgotten Realms Deities", APPENDIX_LORE)
        self.assertIn("Appendix D: Demiplanes", APPENDIX_LORE)

    def test_lore_codex_includes_item_manual_entries(self) -> None:
        game = TextDnDGame(input_fn=lambda _: "10", output_fn=lambda _: None, rng=random.Random(444))
        entries = game.item_manual_entries()
        self.assertIn("Weapons", entries)
        self.assertIn("Consumables and Potions", entries)
        self.assertIn("Scrolls", entries)
        self.assertIn("one-use", entries["Consumables and Potions"]["text"])

    def test_class_choice_displays_expanded_lore(self) -> None:
        answers = iter(["2", "1"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(441))
        selected = game.choose_named_option("Choose a class", CLASSES)
        self.assertEqual(selected, "Bard")
        rendered = self.plain_output(log).replace("\n", " ")
        self.assertIn("song of creation", rendered)
        self.assertIn("read a room", rendered)

    def test_class_identity_option_appears_in_briefing(self) -> None:
        player = build_character(
            name="Mira",
            race="Human",
            class_name="Bard",
            background="Charlatan",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 10, "WIS": 12, "CHA": 15},
            class_skill_choices=["Insight", "Performance", "Persuasion"],
        )
        log: list[str] = []
        answers = iter(["1", "3", "4", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(3010))
        game.state = GameState(player=player, current_scene="neverwinter_briefing")
        game.scene_neverwinter_briefing()
        rendered = self.plain_output(log)
        self.assertIn("better story and a sharper tongue", rendered)
        self.assertIn("Reward gained for Bard identity choice: 10 XP, 6 gp.", rendered)

    def test_race_identity_option_appears_on_phandalin_arrival(self) -> None:
        player = build_character(
            name="Cairn",
            race="Tiefling",
            class_name="Warlock",
            background="Charlatan",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 10, "WIS": 12, "CHA": 15},
            class_skill_choices=["Intimidation", "Investigation"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(3011))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        option_key, option_text = game.scene_identity_options("phandalin_arrival")[0]
        self.assertIn("look ominous enough to trust", option_text)
        game.handle_scene_identity_action("phandalin_arrival", option_key)
        rendered = self.plain_output(log)
        self.assertIn("Embarrassed honesty starts doing", rendered)

    def test_point_buy_can_repick_scores_at_end(self) -> None:
        answers = iter(
            [
                "2",
                "8",
                "8",
                "8",
                "8",
                "8",
                "8",
                "2",
                "15",
                "14",
                "13",
                "10",
                "10",
                "8",
                "1",
            ]
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(31))
        scores = game.choose_ability_scores()
        self.assertEqual(scores, {"STR": 15, "DEX": 14, "CON": 13, "INT": 10, "WIS": 10, "CHA": 8})
        rendered = self.plain_output(log)
        self.assertIn("Points left:", rendered)
        self.assertIn("Let's repick the full stat spread.", rendered)

    def test_background_choice_hides_descriptions_until_selected(self) -> None:
        answers = iter(["1", "1"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(32))
        selected = game.choose_named_option("Choose a background", BACKGROUNDS)
        self.assertEqual(selected, "Soldier")
        rendered = self.plain_output(log)
        self.assertIn("  1. Soldier", rendered)
        self.assertNotIn("1. Soldier: A veteran of militia drills", rendered)
        self.assertIn("Extra proficiencies: Land Vehicles, Gaming", rendered)

    def test_build_character_includes_background_bonus_proficiencies(self) -> None:
        character = build_character(
            name="Nim",
            race="Halfling",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        self.assertEqual(character.bonus_proficiencies, ["Thieves' Tools", "Disguise Kit"])

    def test_party_limit_sends_extra_companion_to_camp(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(33))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.recruit_companion(create_tolan_ironshield())
        game.recruit_companion(create_kaelis_starling())
        game.recruit_companion(create_elira_dawnmantle())
        self.assertEqual(len(game.state.companions), 3)
        game.recruit_companion(create_rhogar_valeguard())
        self.assertEqual(len(game.state.companions), 3)
        self.assertEqual(len(game.state.camp_companions), 1)
        self.assertEqual(game.state.camp_companions[0].name, "Rhogar Valeguard")

    def test_talking_to_companion_improves_disposition(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_tolan_ironshield()
        answers = iter(["1", "1", "5"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(34))
        game.state = GameState(player=player, companions=[companion], current_scene="phandalin_hub")
        game.talk_to_companion()
        self.assertEqual(companion.disposition, 1)
        self.assertIn("old_road", companion.bond_flags["talked_topics"])

    def test_companion_talk_uses_quotes_and_actions(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_tolan_ironshield()
        log: list[str] = []
        answers = iter(["1", "1", "4", "5"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(341))
        game.state = GameState(player=player, companions=[companion], current_scene="phandalin_hub")
        game.talk_to_companion()
        rendered = self.plain_output(log)
        self.assertIn('"Tell me about the worst road you ever guarded."', rendered)
        self.assertIn('Tolan Ironshield: "Sleet, broken axles', rendered)
        self.assertIn("*Ask how they see you now.", rendered)

    def test_terrible_relationship_causes_companion_to_leave(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_tolan_ironshield()
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(35))
        game.state = GameState(player=player, companions=[companion], current_scene="phandalin_hub")
        game.adjust_companion_disposition(companion, -6, "testing cruelty")
        self.assertFalse(any(member.name == "Tolan Ironshield" for member in game.state.all_companions()))
        self.assertIn("Tolan Ironshield", game.state.flags["departed_companions"])

    def test_magic_mirror_respec_costs_gold_and_preserves_level(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        player.level = 2
        answers = iter(
            [
                "1",  # confirm respec
                "3", "1",  # Elf
                "1", "1",  # Fighter
                "4", "1",  # Sage
                "2",  # point buy
                "15", "14", "13", "10", "10", "8",
                "1",  # keep scores
                "1", "1",  # fighter skills
                "1",  # level-up skill at level 2
            ]
        )
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(36))
        game.state = GameState(player=player, current_scene="phandalin_hub", gold=150)
        game.visit_magic_mirror()
        self.assertEqual(game.state.gold, 50)
        self.assertEqual(game.state.player.level, 2)
        self.assertEqual(game.state.player.race, "Elf")
        self.assertEqual(game.state.player.background, "Sage")

    def test_choose_paginates_when_list_is_long(self) -> None:
        answers = iter(["10", "2"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(2))
        result = game.choose("Pick one", [f"Option {index}" for index in range(1, 12)], allow_meta=False)
        self.assertEqual(result, 11)

    def test_single_option_still_requires_manual_selection(self) -> None:
        answers = iter(["2", "1"])
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(204))
        result = game.choose("Only one path is open.", ["Continue"], allow_meta=False)
        self.assertEqual(result, 1)
        rendered = self.plain_output(log)
        self.assertIn("Only one path is open.", rendered)
        self.assertIn("1. Continue", rendered)
        self.assertIn("Please enter a listed number.", rendered)

    def test_road_ambush_scales_for_solo_party(self) -> None:
        player = build_character(
            name="Nyra",
            race="Elf",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        captured: dict[str, object] = {}

        def fake_run(encounter):
            captured["enemy_count"] = len(encounter.enemies)
            captured["parley_dc"] = encounter.parley_dc
            captured["temp_hp"] = game.state.player.temp_hp
            return "victory"

        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(5))
        game.state = GameState(player=player, current_scene="road_ambush", clues=[], journal=[])
        game.run_encounter = fake_run
        game.scene_road_ambush()
        self.assertEqual(captured["enemy_count"], 2)
        self.assertEqual(captured["parley_dc"], 12)
        self.assertGreaterEqual(captured["temp_hp"], 6)

    def test_road_ambush_scales_for_two_member_party(self) -> None:
        player = build_character(
            name="Nyra",
            race="Elf",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        companion = create_kaelis_starling()
        captured: dict[str, object] = {}

        def fake_run(encounter):
            captured["enemy_count"] = len(encounter.enemies)
            captured["parley_dc"] = encounter.parley_dc
            return "victory"

        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(45))
        game.state = GameState(player=player, companions=[companion], current_scene="road_ambush", clues=[], journal=[])
        game.run_encounter = fake_run
        game.scene_road_ambush()
        self.assertEqual(captured["enemy_count"], 2)
        self.assertEqual(captured["parley_dc"], 12)

    def test_road_ambush_intimidation_works_for_solo_party(self) -> None:
        player = build_character(
            name="Velkor",
            race="Half-Orc",
            class_name="Paladin",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 10, "CON": 13, "INT": 8, "WIS": 12, "CHA": 14},
            class_skill_choices=["Athletics", "Intimidation"],
        )
        answers = iter(["3", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(11))
        game.state = GameState(player=player, current_scene="road_ambush", clues=[], journal=[])
        game.run_encounter = lambda encounter: "victory"
        game.scene_road_ambush()
        self.assertEqual(game.state.current_scene, "phandalin_hub")

    def test_road_ambush_athletics_success_grants_real_combat_advantage(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1", "1"])
        captured: dict[str, object] = {}

        def fake_run(encounter):
            captured["enemy_conditions"] = [dict(enemy.conditions) for enemy in encounter.enemies]
            return "victory"

        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(111))
        game.state = GameState(player=player, current_scene="road_ambush", clues=[], journal=[])
        game.skill_check = lambda actor, skill, dc, context: skill == "Athletics"
        game.run_encounter = fake_run
        game.scene_road_ambush()
        self.assertEqual(player.conditions.get("emboldened"), 2)
        self.assertEqual(captured["enemy_conditions"][0].get("prone"), 1)

    def test_road_ambush_intimidation_failure_emboldens_enemies(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["3", "1"])
        captured: dict[str, object] = {}

        def fake_run(encounter):
            captured["enemy_conditions"] = [dict(enemy.conditions) for enemy in encounter.enemies]
            return "victory"

        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(112))
        game.state = GameState(player=player, current_scene="road_ambush", clues=[], journal=[])
        game.skill_check = lambda actor, skill, dc, context: False
        game.run_encounter = fake_run
        game.scene_road_ambush()
        self.assertTrue(all("emboldened" in conditions for conditions in captured["enemy_conditions"]))

    def test_road_ambush_intimidation_choice_renders_as_action(self) -> None:
        player = build_character(
            name="Riven Ashguard",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["3", "1"])
        log: list[str] = []

        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(113))
        game.state = GameState(player=player, current_scene="road_ambush", clues=[], journal=[])
        game.skill_check = lambda actor, skill, dc, context: False
        game.run_encounter = lambda encounter: "victory"
        game.scene_road_ambush()
        rendered = self.plain_output(log)
        self.assertIn("*Break their nerve with a warning shout.", rendered)
        self.assertNotIn('Riven Ashguard: "Break their nerve with a warning shout."', rendered)

    def test_all_heroes_use_player_controlled_turns(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = build_character(
            name="Kaelis",
            race="Half-Elf",
            class_name="Ranger",
            background="Criminal",
            base_ability_scores={"STR": 10, "DEX": 15, "CON": 13, "INT": 11, "WIS": 14, "CHA": 12},
            class_skill_choices=["Perception", "Stealth", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(12))
        game.state = GameState(player=player, companions=[companion], current_scene="road_ambush")
        called: list[str] = []

        def fake_player_turn(actor, heroes, enemies, encounter, dodging):
            called.append(actor.name)
            return None

        game.player_turn = fake_player_turn
        result = game.hero_turn(companion, [player, companion], [create_enemy("goblin_skirmisher")], None, set())
        self.assertIsNone(result)
        self.assertEqual(called, ["Kaelis"])

    def test_knockout_message_happens_after_hit_message(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = build_character(
            name="Kaelis",
            race="Half-Elf",
            class_name="Ranger",
            background="Criminal",
            base_ability_scores={"STR": 10, "DEX": 15, "CON": 13, "INT": 11, "WIS": 14, "CHA": 12},
            class_skill_choices=["Perception", "Stealth", "Survival"],
        )
        companion.current_hp = 4
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(13))
        game.roll_with_advantage = lambda actor, advantage_state: SimpleNamespace(kept=18)
        enemy = create_enemy("bandit")
        enemy.weapon.damage = "1d4+3"
        game.perform_enemy_attack(enemy, companion, [player, companion], [enemy], set())
        hit_index = next(index for index, line in enumerate(log) if "hits Kaelis for" in line)
        down_index = next(index for index, line in enumerate(log) if "Kaelis falls unconscious" in line)
        self.assertLess(hit_index, down_index)

    def test_reward_party_grants_xp_gold_and_levels_player(self) -> None:
        answers = iter(["1"])
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(14))
        game.state = GameState(player=player, current_scene="phandalin_hub", clues=[], journal=[], xp=290, gold=5)
        game.reward_party(xp=20, gold=7, reason="testing rewards")
        self.assertEqual(game.state.xp, 310)
        self.assertEqual(game.state.gold, 12)
        self.assertEqual(game.state.player.level, 2)
        self.assertIn("action_surge", game.state.player.features)
        self.assertEqual(game.state.player.resources.get("action_surge"), 1)

    def test_combat_options_only_tag_skill_check_actions(self) -> None:
        player = build_character(
            name="Velkor",
            race="Dragonborn",
            class_name="Paladin",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 10, "CON": 13, "INT": 8, "WIS": 12, "CHA": 14},
            class_skill_choices=["Athletics", "Intimidation"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(15))
        game.state = GameState(player=player, inventory={"potion_healing": 1}, current_scene="road_ambush")
        options = game.get_player_combat_options(player, SimpleNamespace(allow_parley=True, allow_flee=True))
        self.assertIn("Attack with Divine Smite", options)
        self.assertIn("[PERSUASION / INTIMIDATION] Attempt Parley", options)
        self.assertIn("[STEALTH] Try to Flee", options)
        self.assertIn("Drink a Healing Potion", options)
        self.assertFalse(options[0].startswith("["))

    def test_second_wind_is_a_bonus_action_and_still_allows_attack(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        enemy = create_enemy("bandit")
        player.current_hp = max(1, player.current_hp - 5)
        answers = iter(["3", "1", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(8151))
        game.state = GameState(player=player, current_scene="road_ambush")
        game.perform_weapon_attack = lambda attacker, target, heroes, enemies, dodging, use_smite=False: setattr(target, "current_hp", target.current_hp - 1)
        game.player_turn(player, [player], [enemy], Encounter(title="Test", description="", enemies=[enemy], allow_flee=False), set())
        self.assertGreater(player.current_hp, 5)
        self.assertLess(enemy.current_hp, enemy.max_hp)

    def test_drinking_healing_potion_is_bonus_action_and_feeding_one_is_action(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        ally = create_tolan_ironshield()
        ally.current_hp = max(1, ally.current_hp - 5)
        enemy = create_enemy("bandit")

        self_answers = iter(["4", "1", "1"])
        self_game = TextDnDGame(input_fn=lambda _: next(self_answers), output_fn=lambda _: None, rng=random.Random(8152))
        self_game.state = GameState(player=player, companions=[ally], current_scene="road_ambush", inventory={"potion_healing": 1})
        player.current_hp = max(1, player.current_hp - 4)
        player_before = player.current_hp
        self_game.perform_weapon_attack = lambda attacker, target, heroes, enemies, dodging, use_smite=False: setattr(target, "current_hp", target.current_hp - 1)
        self_game.player_turn(player, [player, ally], [enemy], Encounter(title="Test", description="", enemies=[enemy], allow_flee=False), set())
        self.assertGreater(player.current_hp, player_before)
        self.assertLess(enemy.current_hp, enemy.max_hp)

        feed_answers = iter(["2", "1"])
        feed_game = TextDnDGame(input_fn=lambda _: next(feed_answers), output_fn=lambda _: None, rng=random.Random(8153))
        feed_player = build_character(
            name="Velkor",
            race="Human",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        feed_ally = create_tolan_ironshield()
        feed_ally.current_hp = max(1, feed_ally.current_hp - 5)
        ally_before = feed_ally.current_hp
        feed_enemy = create_enemy("bandit")
        feed_game.state = GameState(player=feed_player, companions=[feed_ally], current_scene="road_ambush", inventory={"potion_healing": 1})
        feed_game.player_turn(feed_player, [feed_player, feed_ally], [feed_enemy], Encounter(title="Test", description="", enemies=[feed_enemy], allow_flee=False), set())
        self.assertGreater(feed_ally.current_hp, ally_before)
        self.assertEqual(feed_enemy.current_hp, feed_enemy.max_hp)

    def test_bonus_action_spell_allows_cantrip_but_blocks_leveled_action_spell(self) -> None:
        player = build_character(
            name="Ash",
            race="Human",
            class_name="Cleric",
            background="Acolyte",
            base_ability_scores={"STR": 10, "DEX": 12, "CON": 13, "INT": 10, "WIS": 15, "CHA": 14},
            class_skill_choices=["Medicine", "Persuasion"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(8154))
        game.state = GameState(player=player, current_scene="road_ambush")
        options = game.get_player_combat_options(
            player,
            SimpleNamespace(allow_parley=False, allow_flee=False),
            turn_state=TurnState(bonus_action_spell_cast=True),
            heroes=[player],
        )
        self.assertIn("Cast Sacred Flame", options)
        self.assertNotIn("Cast Cure Wounds", options)

    def test_healing_word_is_bonus_action_and_still_allows_action_cantrip(self) -> None:
        player = build_character(
            name="Ash",
            race="Human",
            class_name="Cleric",
            background="Acolyte",
            base_ability_scores={"STR": 10, "DEX": 12, "CON": 13, "INT": 10, "WIS": 15, "CHA": 14},
            class_skill_choices=["Medicine", "Persuasion"],
        )
        ally = create_tolan_ironshield()
        ally.current_hp = max(1, ally.current_hp - 5)
        enemy = create_enemy("bandit")
        answers = iter(["5", "2", "2", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(8155))
        game.state = GameState(player=player, companions=[ally], current_scene="road_ambush")
        game.saving_throw = lambda actor, ability, dc, context, against_poison=False: False
        ally_before = ally.current_hp
        game.player_turn(player, [player, ally], [enemy], Encounter(title="Test", description="", enemies=[enemy], allow_flee=False), set())
        self.assertGreater(ally.current_hp, ally_before)
        self.assertLess(enemy.current_hp, enemy.max_hp)

    def test_monk_attack_can_chain_into_martial_arts_bonus_strike(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Monk",
            background="Hermit",
            base_ability_scores={"STR": 10, "DEX": 15, "CON": 13, "INT": 10, "WIS": 14, "CHA": 8},
            class_skill_choices=["Acrobatics", "Insight"],
        )
        enemy = create_enemy("bandit")
        answers = iter(["1", "1", "1", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(8156))
        game.state = GameState(player=player, current_scene="road_ambush")
        game.player_turn(player, [player], [enemy], Encounter(title="Test", description="", enemies=[enemy], allow_flee=False), set())
        self.assertLessEqual(enemy.current_hp, enemy.max_hp - 2)

    def test_dual_wield_off_hand_attack_unlocks_after_attack_action(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(8157))
        game.state = GameState(player=player, current_scene="road_ambush", inventory={"shortsword_common": 1, "dagger_common": 1})
        player.equipment_slots = {slot: None for slot in ["head", "ring_1", "ring_2", "neck", "chest", "gloves", "boots", "main_hand", "off_hand", "cape"]}
        player.equipment_slots["main_hand"] = "shortsword_common"
        player.equipment_slots["off_hand"] = "dagger_common"
        game.sync_equipment(player)
        options = game.get_player_combat_options(
            player,
            SimpleNamespace(allow_parley=False, allow_flee=False),
            turn_state=TurnState(attack_action_taken=True),
            heroes=[player],
        )
        self.assertIn("Make Off-Hand Attack", options)

    def test_level_two_rogue_gets_cunning_action_option(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Rogue",
            background="Criminal",
            base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 13},
            class_skill_choices=["Acrobatics", "Perception", "Sleight of Hand", "Stealth"],
            expertise_choices=["Stealth", "Perception"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(8158))
        game.state = GameState(player=player, current_scene="road_ambush")
        game.level_up_character(player, 2)
        options = game.get_player_combat_options(
            player,
            SimpleNamespace(allow_parley=False, allow_flee=False),
            turn_state=TurnState(),
            heroes=[player],
        )
        self.assertIn("Use Cunning Action", options)

    def test_level_two_monk_gets_ki_bonus_action_options(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Monk",
            background="Hermit",
            base_ability_scores={"STR": 10, "DEX": 15, "CON": 13, "INT": 10, "WIS": 14, "CHA": 8},
            class_skill_choices=["Acrobatics", "Insight"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(8159))
        game.state = GameState(player=player, current_scene="road_ambush")
        game.level_up_character(player, 2)
        options = game.get_player_combat_options(
            player,
            SimpleNamespace(allow_parley=False, allow_flee=False),
            turn_state=TurnState(attack_action_taken=True),
            heroes=[player],
        )
        self.assertIn("Use Flurry of Blows", options)
        self.assertIn("Use Patient Defense", options)
        self.assertIn("Use Step of the Wind", options)

    def test_help_downed_ally_can_restore_them_to_one_hp(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        ally = build_character(
            name="Tolan",
            race="Dwarf",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 10, "CON": 14, "INT": 8, "WIS": 12, "CHA": 13},
            class_skill_choices=["Perception", "Survival"],
        )
        ally.current_hp = 0
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(16))
        game.skill_check = lambda actor, skill, dc, context: True
        game.help_downed_ally(player, ally)
        self.assertEqual(ally.current_hp, 1)

    def test_spell_slots_start_with_bg3_style_class_tables(self) -> None:
        wizard = build_character(
            name="Nyra",
            race="Elf",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        warlock = build_character(
            name="Cairn",
            race="Tiefling",
            class_name="Warlock",
            background="Charlatan",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 10, "WIS": 12, "CHA": 15},
            class_skill_choices=["Intimidation", "Investigation"],
        )
        paladin = build_character(
            name="Velkor",
            race="Half-Orc",
            class_name="Paladin",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 10, "CON": 13, "INT": 8, "WIS": 12, "CHA": 14},
            class_skill_choices=["Athletics", "Intimidation"],
        )
        self.assertEqual(spell_slot_counts(wizard, maximum=True), {1: 2})
        self.assertEqual(spell_slot_counts(warlock, maximum=True), {1: 1})
        self.assertEqual(spell_slot_counts(paladin, maximum=True), {})
        self.assertNotIn("spell_slots", wizard.resources)
        self.assertNotIn("spell_slots", warlock.resources)

    def test_scale_level_resources_grows_spell_slots_by_level(self) -> None:
        wizard = build_character(
            name="Nyra",
            race="Elf",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        paladin = build_character(
            name="Velkor",
            race="Half-Orc",
            class_name="Paladin",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 10, "CON": 13, "INT": 8, "WIS": 12, "CHA": 14},
            class_skill_choices=["Athletics", "Intimidation"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(1601))
        wizard.level = 3
        paladin.level = 5
        game.scale_level_resources(wizard)
        game.scale_level_resources(paladin)
        self.assertEqual(spell_slot_counts(wizard, maximum=True), {1: 4, 2: 2})
        self.assertEqual(spell_slot_counts(paladin, maximum=True), {1: 4, 2: 2})

    def test_warlock_short_rest_restores_pact_slots(self) -> None:
        warlock = build_character(
            name="Cairn",
            race="Tiefling",
            class_name="Warlock",
            background="Charlatan",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 10, "WIS": 12, "CHA": 15},
            class_skill_choices=["Intimidation", "Investigation"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(1602))
        warlock.level = 3
        game.scale_level_resources(warlock)
        warlock.resources["spell_slots_2"] = 0
        game.state = GameState(player=warlock, current_scene="phandalin_hub", short_rests_remaining=2)
        game.short_rest()
        self.assertEqual(warlock.resources["spell_slots_2"], warlock.max_resources["spell_slots_2"])
        self.assertEqual(game.state.short_rests_remaining, 1)

    def test_long_rest_consumes_supply_points_and_resets_short_rests(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        player.current_hp = 3
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(17))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={"camp_stew_jar": 3, "bread_round": 4, "goat_cheese": 2},
            short_rests_remaining=0,
        )
        game.long_rest()
        self.assertEqual(game.state.player.current_hp, game.state.player.max_hp)
        self.assertEqual(game.state.short_rests_remaining, 2)
        self.assertLessEqual(game.current_supply_points(), 8)

    def test_short_rest_heals_half_maximum_hp_rounded_up(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        player.current_hp = 1
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(1701))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            short_rests_remaining=2,
        )
        game.short_rest()
        self.assertEqual(game.state.player.current_hp, min(player.max_hp, 1 + ((player.max_hp + 1) // 2)))
        self.assertEqual(game.state.short_rests_remaining, 1)

    def test_long_rest_restores_spell_slots_for_player_and_companion(self) -> None:
        player = build_character(
            name="Nyra",
            race="Elf",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        companion = build_character(
            name="Elira",
            race="Human",
            class_name="Cleric",
            background="Acolyte",
            base_ability_scores={"STR": 10, "DEX": 12, "CON": 13, "INT": 10, "WIS": 15, "CHA": 14},
            class_skill_choices=["Insight", "Medicine"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(1603))
        player.level = 3
        companion.level = 4
        game.scale_level_resources(player)
        game.scale_level_resources(companion)
        player.resources["spell_slots_1"] = 0
        player.resources["spell_slots_2"] = 1
        companion.resources["spell_slots_1"] = 1
        companion.resources["spell_slots_2"] = 0
        game.state = GameState(
            player=player,
            companions=[companion],
            current_scene="phandalin_hub",
            inventory={"camp_stew_jar": 3, "bread_round": 4, "goat_cheese": 2},
        )
        game.long_rest()
        self.assertEqual(spell_slot_counts(player), spell_slot_counts(player, maximum=True))
        self.assertEqual(spell_slot_counts(companion), spell_slot_counts(companion, maximum=True))

    def test_long_rest_does_not_revive_dead_companions(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_tolan_ironshield()
        companion.dead = True
        companion.current_hp = 0
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(171))
        game.state = GameState(
            player=player,
            companions=[companion],
            current_scene="phandalin_hub",
            inventory={"camp_stew_jar": 3, "bread_round": 4, "goat_cheese": 2},
        )
        game.long_rest()
        self.assertTrue(companion.dead)
        self.assertEqual(companion.current_hp, 0)

    def test_magic_missile_uses_highest_available_slot_when_lower_slots_are_empty(self) -> None:
        wizard = build_character(
            name="Nyra",
            race="Elf",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        target = create_enemy("goblin_skirmisher")
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(1604))
        wizard.level = 3
        game.scale_level_resources(wizard)
        wizard.resources["spell_slots_1"] = 0
        wizard.resources["spell_slots_2"] = 2
        expressions: list[str] = []
        game.roll_with_display_bonus = lambda expression, **kwargs: expressions.append(expression) or SimpleNamespace(total=10)
        game.cast_magic_missile(wizard, target)
        self.assertEqual(expressions, ["4d4+4"])
        self.assertEqual(wizard.resources["spell_slots_2"], 1)

    def test_camp_menu_shows_revivify_option_for_dead_companion(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_kaelis_starling()
        companion.dead = True
        companion.current_hp = 0
        log: list[str] = []
        answers = iter(["3", "4", "7"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(172))
        game.state = GameState(
            player=player,
            camp_companions=[companion],
            current_scene="phandalin_hub",
            inventory={"scroll_revivify": 1},
        )
        game.open_camp_menu()
        rendered = self.plain_output(log)
        self.assertIn("Rest and recovery", rendered)
        self.assertIn("Take a short rest", rendered)
        self.assertIn("Use Scroll of Revivify on a dead ally", rendered)

    def test_camp_revivify_restores_dead_companion(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_kaelis_starling()
        companion.dead = True
        companion.current_hp = 0
        log: list[str] = []
        answers = iter(["1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(173))
        game.state = GameState(
            player=player,
            camp_companions=[companion],
            current_scene="phandalin_hub",
            inventory={"scroll_revivify": 1},
        )
        self.assertTrue(game.use_scroll_of_revivify())
        rendered = self.plain_output(log)
        self.assertFalse(companion.dead)
        self.assertEqual(companion.current_hp, 1)
        self.assertNotIn("scroll_revivify", game.state.inventory)
        self.assertIn("returns to life at 1 HP", rendered)

    def test_scroll_of_revivify_exists_with_uncommon_pricing(self) -> None:
        item = ITEMS["scroll_revivify"]
        self.assertEqual(item.name, "Scroll of Revivify")
        self.assertEqual(item.rarity, "uncommon")
        self.assertEqual(item.value, 200)
        self.assertTrue(item.revive_dead)

    def test_two_handed_weapon_clears_offhand_slot(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(18))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={"longbow_common": 1, "shield_common": 1},
        )
        player.equipment_slots = {
            "head": None,
            "ring_1": None,
            "ring_2": None,
            "neck": None,
            "chest": None,
            "gloves": None,
            "boots": None,
            "main_hand": "longbow_common",
            "off_hand": "shield_common",
            "cape": None,
        }
        game.sync_equipment(player)
        self.assertIsNone(player.equipment_slots["off_hand"])
        self.assertEqual(player.weapon.hands_required, 2)

    def test_ensure_state_integrity_migrates_legacy_equipment_slots(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        player.equipment_slots = {
            "helmet": "iron_cap_common",
            "ring_1": None,
            "ring_2": None,
            "amulet": "soldiers_amulet_common",
            "chest": "chain_mail_common",
            "pants": "reinforced_breeches_common",
            "gloves": None,
            "boots": None,
            "main_hand": "longsword_common",
            "off_hand": None,
        }
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(181))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={
                "iron_cap_common": 1,
                "soldiers_amulet_common": 1,
                "reinforced_breeches_common": 1,
                "chain_mail_common": 1,
                "longsword_common": 1,
            },
        )
        game.ensure_state_integrity()
        self.assertEqual(player.equipment_slots["head"], "iron_cap_common")
        self.assertEqual(player.equipment_slots["neck"], "soldiers_amulet_common")
        self.assertEqual(player.equipment_slots["cape"], "reinforced_breeches_common")
        self.assertNotIn("helmet", player.equipment_slots)
        self.assertNotIn("amulet", player.equipment_slots)
        self.assertNotIn("pants", player.equipment_slots)

    def test_manage_equipment_can_assign_companion_offhand_weapon(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_tolan_ironshield()
        answers = iter(["2", "9", "2", "10", "2", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(182))
        game.state = GameState(player=player, companions=[companion], current_scene="phandalin_hub", inventory={"dagger_common": 1})
        game.ensure_state_integrity()
        game.state.inventory["dagger_common"] = 1
        game.manage_equipment()
        self.assertEqual(companion.equipment_slots["off_hand"], "dagger_common")

    def test_character_sheets_can_show_companion_details(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = create_kaelis_starling()
        log: list[str] = []
        answers = iter(["2", "2"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(183))
        game.state = GameState(player=player, companions=[companion], current_scene="phandalin_hub")
        game.ensure_state_integrity()
        game.show_character_sheets()
        rendered = self.plain_output(log)
        self.assertIn("Character Sheet: Kaelis Starling", rendered)
        self.assertIn("Ability Scores:", rendered)
        self.assertIn("Ability Scores:\n- STR", rendered)
        self.assertIn("\n\nCombat:", rendered)
        self.assertIn("Combat:\n- Weapon", rendered)
        self.assertIn("\n\nSaving Throws:", rendered)
        self.assertIn("Saving Throws:\n- STR", rendered)
        self.assertIn("\n\nSkills:", rendered)
        self.assertIn("Skills:\n- Acrobatics", rendered)
        self.assertIn("Equipment:", rendered)

    def test_selling_item_adds_gold_with_merchant(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(19))
        game.state = GameState(player=player, current_scene="phandalin_hub", gold=0, inventory={"bread_round": 1})
        player.equipment_slots = {slot: None for slot in ["head", "ring_1", "ring_2", "neck", "chest", "gloves", "boots", "main_hand", "off_hand", "cape"]}
        game.sell_items(merchant_id="linene_graywind", merchant_name="Linene Graywind")
        self.assertEqual(game.state.gold, 1)
        self.assertNotIn("bread_round", game.state.inventory)

    def test_cannot_sell_away_from_merchant(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(20))
        game.state = GameState(player=player, current_scene="phandalin_hub", gold=0, inventory={"bread_round": 1})
        player.equipment_slots = {slot: None for slot in ["head", "ring_1", "ring_2", "neck", "chest", "gloves", "boots", "main_hand", "off_hand", "cape"]}
        game.sell_items()
        self.assertEqual(game.state.gold, 0)
        self.assertEqual(game.state.inventory["bread_round"], 1)

    def test_sell_menu_allows_backing_out(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["2"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(21))
        game.state = GameState(player=player, current_scene="phandalin_hub", gold=0, inventory={"bread_round": 1})
        player.equipment_slots = {slot: None for slot in ["head", "ring_1", "ring_2", "neck", "chest", "gloves", "boots", "main_hand", "off_hand", "cape"]}
        game.sell_items(merchant_id="linene_graywind", merchant_name="Linene Graywind")
        self.assertEqual(game.state.gold, 0)
        self.assertEqual(game.state.inventory["bread_round"], 1)

    def test_general_inventory_menu_hides_sell_option(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "6", output_fn=log.append, rng=random.Random(22))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={"bread_round": 1})
        game.manage_inventory()
        rendered = "\n".join(log)
        self.assertNotIn("Sell items", rendered)
        self.assertIn("View inventory by category", rendered)

    def test_merchant_inventory_menu_shows_trade_tags(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "9", output_fn=log.append, rng=random.Random(221))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={"bread_round": 1})
        game.manage_inventory(merchant_id="barthen_provisions", merchant_name="Barthen")
        rendered = self.plain_output(log)
        self.assertIn("[TRADE] Browse Barthen's wares", rendered)
        self.assertIn("[TRADE] Buy items from Barthen", rendered)
        self.assertIn("[TRADE] Sell items to Barthen", rendered)
        self.assertIn("Trade terms with Barthen", rendered)

    def test_inventory_filter_view_can_focus_on_consumables(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(2211))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={"potion_healing": 2, "bread_round": 1, "longsword_common": 1},
        )
        game.show_inventory(filter_key="consumables")
        rendered = self.plain_output(log)
        self.assertIn("View: Consumables", rendered)
        self.assertIn("Potion of Healing", rendered)
        self.assertNotIn("Bread Round", rendered)
        self.assertNotIn("Longsword", rendered)

    def test_inventory_storefront_view_exposes_table_headers(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(2212))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={"potion_healing": 2, "longsword_common": 1},
        )
        game.show_inventory()
        rendered = self.plain_output(log)
        self.assertIn("On hand: Potion of Healing x2, Roadworn Longsword x1", rendered)
        if RICH_AVAILABLE:
            self.assertIn("Shared Inventory", rendered)
            self.assertIn("Qty", rendered)
            self.assertIn("Value", rendered)
            self.assertIn("Rules", rendered)

    def test_merchant_catalog_renders_trade_desk_columns(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(2213))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={})
        stock = game.get_merchant_stock("barthen_provisions")
        stock.clear()
        stock["bread_round"] = 3
        game.show_merchant_stock("barthen_provisions", "Barthen")
        rendered = self.plain_output(log)
        self.assertIn("Trade terms with Barthen", rendered)
        self.assertIn("Bread Round", rendered)
        if RICH_AVAILABLE:
            self.assertIn("Trade Desk", rendered)
            self.assertIn("Stock", rendered)
            self.assertIn("Buy", rendered)

    def test_merchant_pricing_uses_persuasion_and_attitude_formula(self) -> None:
        player = build_character(
            name="Mira",
            race="Human",
            class_name="Bard",
            background="Charlatan",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 10, "WIS": 12, "CHA": 16},
            class_skill_choices=["Insight", "Performance", "Persuasion"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(222))
        game.state = GameState(player=player, current_scene="phandalin_hub", inventory={})
        game.state.flags["merchant_attitudes"] = {"barthen_provisions": 50}
        self.assertEqual(game.trade_persuasion(), 5)
        self.assertAlmostEqual(game.buy_price_multiplier("barthen_provisions"), 1.75)
        self.assertAlmostEqual(game.sell_price_multiplier("barthen_provisions"), 1 / 1.75)

    def test_can_buy_multiple_items_from_merchant(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(23))
        game.state = GameState(player=player, current_scene="phandalin_hub", gold=15, inventory={})
        stock = game.get_merchant_stock("barthen_provisions")
        stock.clear()
        stock["bread_round"] = 5
        game.buy_items("barthen_provisions", "Barthen")
        self.assertEqual(game.state.inventory["bread_round"], 3)
        self.assertEqual(game.state.gold, 0)
        self.assertEqual(stock["bread_round"], 2)

    def test_early_item_prices_are_more_affordable(self) -> None:
        self.assertEqual(ITEMS["potion_healing"].value, 15)
        self.assertLess(ITEMS["longbow_common"].value, 50)
        self.assertLess(ITEMS["chain_shirt_uncommon"].value, 100)

    def test_can_sell_multiple_items_to_merchant(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1", "2"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(24))
        game.state = GameState(player=player, current_scene="phandalin_hub", gold=0, inventory={"bread_round": 3})
        player.equipment_slots = {slot: None for slot in ["head", "ring_1", "ring_2", "neck", "chest", "gloves", "boots", "main_hand", "off_hand", "cape"]}
        stock = game.get_merchant_stock("barthen_provisions")
        stock.clear()
        game.sell_items(merchant_id="barthen_provisions", merchant_name="Barthen")
        self.assertEqual(game.state.gold, 2)
        self.assertEqual(game.state.inventory["bread_round"], 1)
        self.assertEqual(stock["bread_round"], 2)

    def test_failed_skill_check_grants_no_xp(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(25))
        game.state = GameState(player=player, current_scene="neverwinter_briefing", xp=0, gold=0)
        game.skill_check = lambda actor, skill, dc, context: False
        game.handle_neverwinter_prep()
        self.assertEqual(game.state.xp, 0)

    def test_returning_from_ashfall_watch_guarantees_level_two_before_emberhall(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        answers = iter(["1", "3", "10", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(52))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            clues=["one", "two"],
            xp=180,
            flags={"ashfall_watch_cleared": True, "phandalin_arrived": True, "tresendar_cleared": True},
        )
        game.scene_phandalin_hub()
        self.assertEqual(game.state.player.level, 2)
        self.assertEqual(game.state.current_scene, "emberhall_cellars")

    def test_neverwinter_prep_skill_check_has_situation_specific_failure_text(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(251))
        game.state = GameState(player=player, current_scene="neverwinter_briefing", xp=0, gold=0)
        game.skill_check = lambda actor, skill, dc, context: False
        game.handle_neverwinter_prep()
        rendered = self.plain_output(log)
        self.assertIn("The ledgers are too incomplete and hastily corrected", rendered)

    def test_shrine_skill_choice_cannot_be_repeated(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["1", "4"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(26))
        game.state = GameState(player=player, current_scene="phandalin_hub", xp=0, gold=0)
        game.skill_check = lambda actor, skill, dc, context: True
        game.visit_shrine()
        rendered = self.plain_output(log)
        self.assertEqual(rendered.count('1. [MEDICINE] "Let me examine the poisoned miner."'), 1)

    def test_steward_question_cannot_be_repeated(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["1", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(29))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.visit_steward()
        rendered = self.plain_output(log)
        self.assertEqual(rendered.count('1. "Where is the Ashen Brand hurting you the most?"'), 1)

    def test_inn_question_cannot_be_repeated(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["1", "3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(30))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.visit_stonehill_inn()
        rendered = self.plain_output(log)
        self.assertEqual(rendered.count('1. "Mind if I buy you a drink and ask a few questions?"'), 1)

    def test_briefing_question_cannot_be_repeated(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["1", "1", "4", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(27))
        game.state = GameState(player=player, current_scene="neverwinter_briefing", flags={"briefing_seen": True})
        game.scene_neverwinter_briefing()
        rendered = self.plain_output(log)
        self.assertEqual(rendered.count('1. "How is Neverwinter holding together these days?"'), 1)

    def test_show_party_displays_xp_to_next_level(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(28))
        game.state = GameState(player=player, current_scene="phandalin_hub", xp=120, gold=9)
        game.show_party()
        rendered = self.plain_output(log)
        self.assertIn("Next level in 180 XP", rendered)
        self.assertIn("HP [", rendered)
        self.assertIn("conditions [none]", rendered)
        self.assertNotIn("Features:", rendered)

    def test_roll_initiative_handles_ties_without_character_comparison(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        companion = build_character(
            name="Kaelis",
            race="Half-Elf",
            class_name="Ranger",
            background="Criminal",
            base_ability_scores={"STR": 10, "DEX": 15, "CON": 13, "INT": 11, "WIS": 14, "CHA": 12},
            class_skill_choices=["Perception", "Stealth", "Survival"],
        )
        enemy = create_enemy("goblin_skirmisher")
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(23))
        game.roll_with_advantage = lambda actor, advantage_state: SimpleNamespace(kept=10)
        order = game.roll_initiative([player, companion], [enemy])
        self.assertEqual(len(order), 3)
        self.assertEqual(order[0].name, "Kaelis")
        self.assertIn(enemy, order)

    def test_offer_early_companion_lists_companion_classes(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(24))
        game.state = GameState(player=player, current_scene="neverwinter_briefing")
        game.offer_early_companion()
        rendered = self.plain_output(log)
        self.assertIn("Kaelis Starling, a ranger scout", rendered)
        self.assertIn("Rhogar Valeguard, a paladin caravan-guard", rendered)
        self.assertNotIn("Handle the road alone for now.", rendered)

    def test_help_command_lists_global_commands(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["help", "2"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(40))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.choose("Choose one.", ["First", "Second"])
        rendered = self.plain_output(log)
        self.assertIn("Global Commands", rendered)
        self.assertIn("load: Load another save slot immediately and continue from there.", rendered)
        self.assertIn("quit: Return to the main menu, or close the program if you are already there.", rendered)
        self.assertIn("camp: Open camp when you are not in combat.", rendered)
        self.assertIn("inventory / backpack / bag", rendered)
        self.assertIn("settings: Open the settings menu", rendered)

    def test_choose_displays_compact_hud_for_active_game_prompts(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "2", output_fn=log.append, rng=random.Random(4001))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            gold=9,
            inventory={"bread_round": 1},
            quests={"secure_miners_road": QuestLogEntry(quest_id="secure_miners_road")},
        )
        choice = game.choose("Choose one.", ["First", "Second"])
        self.assertEqual(choice, 2)
        rendered = self.plain_output(log)
        self.assertIn("[Act I] Phandalin | Objective: Stop the Watchtower Raids", rendered)
        self.assertIn("Resources: 9 gp | Short rests: 2 | Carry:", rendered)
        self.assertIn(f"Party: Velkor {player.current_hp}/{player.max_hp}", rendered)

    def test_target_selection_suppresses_compact_hud(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        enemy = create_enemy("goblin_skirmisher")
        log: list[str] = []
        answers = iter(["1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(4002))
        game.state = GameState(player=player, current_scene="road_ambush")
        target = game.choose_target([enemy], prompt="Choose a target.", allow_back=True)
        self.assertIs(target, enemy)
        rendered = self.plain_output(log)
        self.assertNotIn("[Act I]", rendered)
        self.assertIn("Choose a target.", rendered)

    def test_grouped_combat_menu_renders_action_sections(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(4005))
        game.state = GameState(player=player, current_scene="road_ambush", inventory={"potion_healing": 1})
        game._in_combat = True
        enemy = create_enemy("goblin_skirmisher")
        options = game.get_player_combat_options(
            player,
            SimpleNamespace(allow_parley=True, allow_flee=True),
            turn_state=TurnState(),
            heroes=[player],
        )
        selected = game.choose_grouped_combat_option("Your turn.", options, actor=player, heroes=[player], enemies=[enemy])
        self.assertEqual(selected, f"Attack with {player.weapon.name}")
        rendered = self.plain_output(log)
        self.assertIn("Action:", rendered)
        self.assertIn("Bonus Action:", rendered)
        self.assertIn("Tactical:", rendered)
        if RICH_AVAILABLE:
            self.assertIn("Party", rendered)
            self.assertIn("Enemies", rendered)

    def test_equipment_comparison_preview_shows_deltas(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["3"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(4006))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={"traveler_hood_common": 1, "iron_cap_common": 1},
        )
        game.ensure_state_integrity()
        player.equipment_slots["head"] = "iron_cap_common"
        game.sync_equipment(player)
        game.manage_equipment_slot(player, "head")
        rendered = self.plain_output(log)
        self.assertIn("Current Head: Roadworn Iron Cap", rendered)
        self.assertIn("Roadworn Traveler's Hood", rendered)
        self.assertIn("AC -1", rendered)
        self.assertIn("Perception +1", rendered)

    def test_compact_hud_only_renders_once_per_scene(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["1", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(4003))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.banner("Phandalin")
        game.choose("Choose one.", ["First", "Second"])
        game.banner("Stonehill Inn")
        game.choose("Choose again.", ["Only option"])
        rendered = self.plain_output(log)
        self.assertEqual(rendered.count("[Act I] Phandalin"), 1)

    def test_compact_hud_is_hidden_during_combat(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(4004))
        game.state = GameState(player=player, current_scene="road_ambush")
        game._in_combat = True
        game.banner("Ambush")
        game.choose("Choose one.", ["First"], allow_meta=False)
        rendered = self.plain_output(log)
        self.assertNotIn("[Act I]", rendered)
        self.assertIn("=== Ambush ===", rendered)
        self.assertIn("Choose one.", rendered)

    def test_settings_command_opens_settings_menu_from_prompt(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["settings", "7", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(401))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        choice = game.choose("Choose one.", ["First", "Second"])
        self.assertEqual(choice, 1)
        rendered = self.plain_output(log)
        self.assertIn("Settings", rendered)
        self.assertIn("Toggle sound effects", rendered)
        self.assertIn("Dice animation style", rendered)
        self.assertIn("Toggle typed dialogue and narration", rendered)
        self.assertIn("Toggle pacing pauses", rendered)
        self.assertIn("Toggle staggered option reveals", rendered)

    def test_settings_menu_can_disable_presentation_toggles(self) -> None:
        answers = iter(["3", "1", "4", "5", "6", "7"])
        game = TextDnDGame(
            input_fn=lambda _: next(answers),
            output_fn=print,
            rng=random.Random(402),
            animate_dice=True,
            pace_output=True,
            type_dialogue=True,
        )
        game._staggered_reveals_preference = True
        game.apply_staggered_reveal_preference()
        game.refresh_presentation_bundle_preference()
        with patch("sys.stdout", io.StringIO()):
            game.open_settings_menu()
        self.assertFalse(game.animate_dice)
        self.assertFalse(game.pace_output)
        self.assertFalse(game.type_dialogue)
        self.assertFalse(game.staggered_reveals_enabled)
        self.assertFalse(hasattr(game.rng, "dice_roll_animator"))
        self.assertFalse(game.current_settings_payload()["animations_and_delays_enabled"])

    def test_settings_persist_across_game_restarts(self) -> None:
        save_dir = Path.cwd() / "tests_output" / "settings_persistence"
        save_dir.mkdir(parents=True, exist_ok=True)
        settings_path = save_dir / "settings.json"
        settings_path.unlink(missing_ok=True)

        first_game = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=print,
            save_dir=save_dir,
            rng=random.Random(404),
        )
        first_game._music_supported = True
        first_game._music_assets_ready = True
        first_game._sfx_supported = True
        first_game._sfx_assets_ready = True
        first_game.refresh_scene_music = lambda default_to_menu=False: None

        with patch("sys.stdout", io.StringIO()):
            first_game.set_sound_effects_enabled(False)
            first_game.set_music_enabled(True)
            first_game.set_animations_and_delays_enabled(False)

        stored_settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(
            stored_settings,
            {
                "sound_effects_enabled": False,
                "music_enabled": True,
                "dice_animations_enabled": False,
                "dice_animation_mode": "off",
                "typed_dialogue_enabled": False,
                "pacing_pauses_enabled": False,
                "staggered_reveals_enabled": False,
                "animations_and_delays_enabled": False,
            },
        )

        second_game = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=lambda _: None,
            save_dir=save_dir,
            rng=random.Random(405),
        )
        self.assertFalse(second_game.animate_dice)
        self.assertFalse(second_game.pace_output)
        self.assertFalse(second_game.type_dialogue)
        self.assertFalse(second_game.staggered_reveals_enabled)
        self.assertFalse(second_game.current_settings_payload()["sound_effects_enabled"])
        self.assertTrue(second_game.current_settings_payload()["music_enabled"])
        self.assertFalse(second_game.current_settings_payload()["dice_animations_enabled"])
        self.assertEqual(second_game.current_settings_payload()["dice_animation_mode"], "off")
        self.assertFalse(second_game.current_settings_payload()["typed_dialogue_enabled"])
        self.assertFalse(second_game.current_settings_payload()["pacing_pauses_enabled"])
        self.assertFalse(second_game.current_settings_payload()["staggered_reveals_enabled"])
        self.assertFalse(second_game.current_settings_payload()["animations_and_delays_enabled"])

        settings_path.unlink(missing_ok=True)
        save_dir.rmdir()

    def test_load_menu_ignores_settings_file(self) -> None:
        save_dir = Path.cwd() / "tests_output" / "settings_menu_filter"
        save_dir.mkdir(parents=True, exist_ok=True)
        settings_path = save_dir / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "sound_effects_enabled": False,
                    "music_enabled": False,
                    "animations_and_delays_enabled": False,
                }
            ),
            encoding="utf-8",
        )

        player = build_character(
            name="Iri",
            race="Human",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        state = GameState(player=player, current_scene="phandalin_hub")
        writer = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=lambda _: None,
            save_dir=save_dir,
            rng=random.Random(406),
        )
        writer.state = state
        save_path = writer.save_game(slot_name="campaign")

        log: list[str] = []
        reader = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=log.append,
            save_dir=save_dir,
            rng=random.Random(407),
        )
        loaded = reader.load_from_menu()
        rendered = self.plain_output(log)
        self.assertTrue(loaded)
        self.assertIn("campaign", rendered)
        self.assertNotIn("settings", rendered)

        Path(save_path).unlink(missing_ok=True)
        settings_path.unlink(missing_ok=True)
        save_dir.rmdir()

    def test_main_menu_includes_settings_option(self) -> None:
        log: list[str] = []
        answers = iter(["4", "7", "5"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(403))
        game.run()
        rendered = self.plain_output(log)
        self.assertIn("4.", rendered)
        self.assertIn("Settings", rendered)

    def test_load_command_can_replace_active_game_mid_prompt(self) -> None:
        save_dir = Path.cwd() / "tests_output" / "midgame_load"
        save_dir.mkdir(parents=True, exist_ok=True)
        player = build_character(
            name="Iri",
            race="Human",
            class_name="Wizard",
            background="Sage",
            base_ability_scores={"STR": 8, "DEX": 14, "CON": 12, "INT": 15, "WIS": 13, "CHA": 10},
            class_skill_choices=["Arcana", "Investigation"],
        )
        writer = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=lambda _: None,
            save_dir=save_dir,
            rng=random.Random(501),
        )
        writer.state = GameState(player=player, current_scene="phandalin_hub", gold=27)
        save_path = writer.save_game(slot_name="campaign")

        other_player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        reader = TextDnDGame(
            input_fn=lambda _: "1",
            output_fn=lambda _: None,
            save_dir=save_dir,
            rng=random.Random(502),
        )
        reader.state = GameState(player=other_player, current_scene="road_ambush", gold=3)

        with self.assertRaises(gameplay_base.ResumeLoadedGame):
            reader.handle_meta_command("load")

        self.assertEqual(reader.state.player.name, "Iri")
        self.assertEqual(reader.state.current_scene, "phandalin_hub")
        self.assertEqual(reader.state.gold, 27)

        Path(save_path).unlink(missing_ok=True)
        (save_dir / "settings.json").unlink(missing_ok=True)
        save_dir.rmdir()

    def test_quit_command_returns_to_title_from_active_game(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(503))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.confirm = lambda prompt: True

        with self.assertRaises(gameplay_base.ReturnToTitleMenu):
            game.handle_meta_command("quit")

        self.assertIsNone(game.state)

    def test_main_menu_quit_command_confirms_before_exit(self) -> None:
        log: list[str] = []
        answers = iter(["quit", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(504))
        game.run()
        rendered = self.plain_output(log)
        self.assertIn("Quit the program and close the main menu?", rendered)
        self.assertIn("Safe travels, adventurer.", rendered)

    def test_dialogue_uses_colored_names_and_extra_spacing(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(205))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.player_speaker("We should move.")
        game.speaker("Lantern Keeper", "Then move quickly.")
        rendered = "\n".join(log)
        self.assertIn(colorize("Velkor", "blue"), rendered)
        self.assertIn(colorize("Lantern Keeper", "green"), rendered)
        self.assertEqual(log[0], "")
        self.assertEqual(log[2], "")
        self.assertEqual(log[3], "")
        self.assertEqual(log[5], "")

    def test_camp_command_opens_camp_out_of_combat(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        answers = iter(["camp", "7", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=log.append, rng=random.Random(41))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.choose("Choose one.", ["First", "Second"])
        rendered = self.plain_output(log)
        self.assertIn("=== Camp ===", rendered)
        self.assertIn("Party and roster", rendered)
        self.assertIn("Supplies and equipment", rendered)
        self.assertIn("Choose one.", rendered)

    def test_combat_target_selection_can_back_out(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        enemy = create_enemy("goblin_skirmisher")
        answers = iter(["1", "2", "4"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(42))
        game.state = GameState(player=player, current_scene="road_ambush")
        called: list[str] = []

        def fake_attack(actor, target, heroes, enemies, dodging, use_smite=False):
            called.append(target.name)

        game.perform_weapon_attack = fake_attack
        game.player_turn(player, [player], [enemy], SimpleNamespace(allow_parley=False, allow_flee=False), set())
        self.assertEqual(called, [])

    def test_failed_skill_check_adds_extra_failure_text(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(43))
        game.roll_with_advantage = lambda actor, advantage_state: SimpleNamespace(kept=1)
        result = game.skill_check(player, "Persuasion", 20, context="to calm a crowd")
        self.assertFalse(result)
        rendered = self.plain_output(log)
        self.assertNotIn("The attempt falls short", rendered)
        self.assertEqual(log[-1], "")

    def test_action_choice_output_adds_trailing_blank_line(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(430))
        game.state = GameState(player=player, current_scene="phandalin_hub")
        game.player_choice_output(game.action_option("Take the writ and head for the High Road."))
        self.assertEqual(log[-2], "*Take the writ and head for the High Road.")
        self.assertEqual(log[-1], "")

    def test_official_conditions_are_all_defined(self) -> None:
        official_conditions = {
            "blinded",
            "charmed",
            "deafened",
            "exhaustion",
            "frightened",
            "grappled",
            "incapacitated",
            "invisible",
            "paralyzed",
            "petrified",
            "poisoned",
            "prone",
            "restrained",
            "stunned",
            "unconscious",
        }
        self.assertTrue(official_conditions.issubset(STATUS_DEFINITIONS))

    def test_varyn_binding_hex_can_incapacitate_target(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        varyn = create_enemy("varyn")
        log: list[str] = []
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=log.append, rng=random.Random(114))
        game.state = GameState(player=player, current_scene="emberhall_cellars")
        varyn.resources["silver_tongue"] = 0
        game.saving_throw = lambda actor, ability, dc, context, against_poison=False: False
        game.enemy_turn(varyn, [player], [varyn], SimpleNamespace(), set())
        self.assertIn("incapacitated", player.conditions)
        rendered = self.plain_output(log)
        self.assertIn("binding hex", rendered)
        self.assertIn("locks them in place", rendered)

    def test_restorative_items_clear_new_official_conditions(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        player.conditions.update({"restrained": 2, "prone": 1, "petrified": 1, "exhaustion": 2})
        answers = iter(["2", "1"])
        game = TextDnDGame(input_fn=lambda _: next(answers), output_fn=lambda _: None, rng=random.Random(115))
        game.state = GameState(
            player=player,
            current_scene="phandalin_hub",
            inventory={"giantfire_balm": 1, "scroll_resurgent_flame": 1},
        )
        self.assertTrue(game.use_item_from_inventory())
        self.assertNotIn("restrained", player.conditions)
        self.assertNotIn("prone", player.conditions)
        self.assertTrue(game.use_item_from_inventory())
        self.assertNotIn("petrified", player.conditions)
        self.assertEqual(player.conditions.get("exhaustion"), 1)

    def test_burning_ticks_and_battle_cleanup_preserves_only_curses(self) -> None:
        player = build_character(
            name="Velkor",
            race="Human",
            class_name="Fighter",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        player.conditions["burning"] = 1
        player.conditions["cursed"] = -1
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(113))
        game.state = GameState(player=player, current_scene="road_ambush")
        before = player.current_hp
        game.tick_conditions(player)
        self.assertLess(player.current_hp, before)
        self.assertNotIn("burning", player.conditions)
        enemy = create_enemy("goblin_skirmisher")
        enemy.current_hp = 0
        enemy.dead = True
        outcome = game.run_encounter(SimpleNamespace(title="Cleanup Test", description="done", enemies=[enemy], allow_flee=False, allow_parley=False, parley_dc=0, hero_initiative_bonus=0, enemy_initiative_bonus=0))
        self.assertEqual(outcome, "victory")
        self.assertIn("cursed", player.conditions)
        self.assertNotIn("burning", player.conditions)


if __name__ == "__main__":
    unittest.main()
