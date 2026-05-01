from __future__ import annotations

import random
import unittest

from dnd_game.content import build_character
from dnd_game.content import create_enemy
from dnd_game.data.items.catalog import ITEMS, item_rules_text
from dnd_game.data.story.factories import (
    AVOIDANCE_BANDS,
    BASELINE_HIT_CHANCE_TARGET,
    HIGH_AVOIDANCE_ENEMY_TEMPLATES,
    LOW_LEVEL_ENEMY_COMBAT_PROFILES,
)
from dnd_game.dice import D20Outcome, RollOutcome
from dnd_game.game import TextDnDGame
from dnd_game.gameplay.combat_simulator import simulate_weapon_attack
from dnd_game.gameplay.encounter import Encounter
from dnd_game.models import Armor, GameState, Weapon


def build_game_with_player(class_name: str, scores: dict[str, int]) -> tuple[TextDnDGame, object]:
    player = build_character(
        name="Vale",
        race="Human",
        class_name=class_name,
        background="Soldier",
        base_ability_scores=scores,
        class_skill_choices=["Athletics", "Survival"],
    )
    game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(90101))
    game.state = GameState(player=player, current_scene="road_ambush")
    return game, player


class ScriptedRandom(random.Random):
    def __init__(self, *, randint_values: list[int] | None = None, random_values: list[float] | None = None) -> None:
        super().__init__(0)
        self.randint_values = list(randint_values or [])
        self.random_values = list(random_values or [])

    def randint(self, a: int, b: int) -> int:
        if not self.randint_values:
            return super().randint(a, b)
        value = self.randint_values.pop(0)
        if not a <= value <= b:
            raise AssertionError(f"Scripted randint value {value} outside {a}..{b}")
        return value

    def random(self) -> float:
        if not self.random_values:
            return super().random()
        return self.random_values.pop(0)

    def choice(self, sequence):  # type: ignore[override]
        if not sequence:
            raise IndexError("Cannot choose from an empty sequence")
        return sequence[0]


class CombatResolverTests(unittest.TestCase):
    def test_story_mode_recovers_quarter_max_hp_after_battle(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        companion = build_character(
            name="Elira",
            race="Human",
            class_name="Mage",
            background="Acolyte",
            base_ability_scores={"STR": 8, "DEX": 12, "CON": 13, "INT": 15, "WIS": 14, "CHA": 10},
            class_skill_choices=["Arcana", "Medicine"],
        )
        game.state = GameState(player=Warrior, companions=[companion], current_scene="road_ambush")
        game.difficulty_mode = "story"
        Warrior.max_hp = 20
        Warrior.current_hp = 10
        companion.max_hp = 13
        companion.current_hp = 0
        companion.death_failures = 2

        game.recover_after_battle()

        self.assertEqual(Warrior.current_hp, 15)
        self.assertEqual(companion.current_hp, 4)
        self.assertFalse(companion.stable)
        self.assertEqual(companion.death_failures, 0)

    def test_standard_mode_revives_downed_party_after_battle(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        companion = build_character(
            name="Elira",
            race="Human",
            class_name="Mage",
            background="Acolyte",
            base_ability_scores={"STR": 8, "DEX": 12, "CON": 13, "INT": 15, "WIS": 14, "CHA": 10},
            class_skill_choices=["Arcana", "Medicine"],
        )
        game.state = GameState(player=Warrior, companions=[companion], current_scene="road_ambush")
        game.difficulty_mode = "standard"
        Warrior.max_hp = 20
        Warrior.current_hp = 10
        companion.max_hp = 13
        companion.current_hp = 0

        game.recover_after_battle()

        self.assertEqual(Warrior.current_hp, 10)
        self.assertEqual(companion.current_hp, 1)

    def test_help_downed_ally_restores_twenty_percent_max_hp(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        companion = build_character(
            name="Elira",
            race="Human",
            class_name="Mage",
            background="Acolyte",
            base_ability_scores={"STR": 8, "DEX": 12, "CON": 13, "INT": 15, "WIS": 14, "CHA": 10},
            class_skill_choices=["Arcana", "Medicine"],
        )
        game.skill_check = lambda actor, skill, dc, context: True  # type: ignore[method-assign]
        companion.max_hp = 13
        companion.current_hp = 0
        companion.death_failures = 2

        game.help_downed_ally(Warrior, companion)

        self.assertEqual(companion.current_hp, 3)
        self.assertEqual(companion.death_failures, 0)

    def test_catalog_armor_and_shields_emit_percent_defense(self) -> None:
        self.assertEqual(ITEMS["traveler_clothes_common"].armor.defense_percent, 0)
        self.assertEqual(ITEMS["leather_armor_common"].armor.defense_percent, 10)
        self.assertEqual(ITEMS["studded_leather_common"].armor.defense_percent, 15)
        self.assertEqual(ITEMS["chain_mail_common"].armor.defense_percent, 35)
        self.assertEqual(ITEMS["chain_mail_rare"].armor.defense_percent, 40)
        self.assertEqual(ITEMS["breastplate_epic"].armor.defense_percent, 40)
        self.assertEqual(ITEMS["splint_armor_legendary"].armor.defense_percent, 60)

        self.assertEqual(ITEMS["chain_mail_rare"].armor.base_ac, 16)
        self.assertEqual(ITEMS["chain_mail_rare"].armor.defense_cap_percent, 80)
        self.assertEqual(ITEMS["shield_common"].shield_defense_percent, 5)
        self.assertEqual(ITEMS["shield_rare"].shield_defense_percent, 10)
        self.assertEqual(ITEMS["shield_rare"].raised_shield_defense_percent, 10)
        self.assertIn("Defense 35%", item_rules_text(ITEMS["chain_mail_common"]))
        self.assertIn("shield Defense +5%", item_rules_text(ITEMS["shield_common"]))

    def test_accuracy_targets_avoidance_instead_of_armor_class(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        rogue_game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )

        self.assertEqual(Warrior.armor_class, 18)
        self.assertEqual(game.effective_avoidance(Warrior), 0)
        self.assertEqual(game.effective_attack_target_number(Warrior), 8)
        self.assertEqual(rogue_game.effective_avoidance(rogue), 3)
        self.assertEqual(rogue_game.effective_attack_target_number(rogue), 11)

    def test_karmic_failure_debt_can_force_next_success(self) -> None:
        rng = ScriptedRandom(randint_values=[2], random_values=[0.0])
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game.rng = rng
        game.karmic_dice_enabled = True

        first = game.roll_check_d20(
            Warrior,
            0,
            target_number=12,
            target_label="DC 12",
            modifier=0,
            style="skill",
            outcome_kind="check",
        )
        second = game.roll_check_d20(
            Warrior,
            0,
            target_number=12,
            target_label="DC 12",
            modifier=0,
            style="skill",
            outcome_kind="check",
        )

        self.assertEqual(first.kept, 2)
        self.assertGreaterEqual(second.kept, 12)
        self.assertEqual(game.karmic_dice_bucket_state("dialogue")["failure"], 0)
        self.assertGreater(game.karmic_dice_bucket_state("dialogue")["success"], 0)

    def test_karmic_success_debt_can_force_next_failure(self) -> None:
        rng = ScriptedRandom(randint_values=[18], random_values=[0.0])
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game.rng = rng
        game.karmic_dice_enabled = True

        first = game.roll_check_d20(
            Warrior,
            0,
            target_number=12,
            target_label="DC 12",
            modifier=0,
            style="skill",
            outcome_kind="check",
        )
        second = game.roll_check_d20(
            Warrior,
            0,
            target_number=12,
            target_label="DC 12",
            modifier=0,
            style="skill",
            outcome_kind="check",
        )

        self.assertEqual(first.kept, 18)
        self.assertLess(second.kept, 12)
        self.assertEqual(game.karmic_dice_bucket_state("dialogue")["success"], 0)
        self.assertGreater(game.karmic_dice_bucket_state("dialogue")["failure"], 0)

    def test_karmic_disabled_uses_plain_rolls(self) -> None:
        rng = ScriptedRandom(randint_values=[2, 2], random_values=[0.0])
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game.rng = rng
        game.karmic_dice_enabled = False

        first = game.roll_check_d20(Warrior, 0, target_number=12, modifier=0, style="skill", outcome_kind="check")
        second = game.roll_check_d20(Warrior, 0, target_number=12, modifier=0, style="skill", outcome_kind="check")

        self.assertEqual(first.kept, 2)
        self.assertEqual(second.kept, 2)
        self.assertFalse(hasattr(game, "_karmic_dice_debts"))

    def test_karmic_near_miss_no_longer_creates_pressure_result(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        game._in_combat = True
        game.karmic_dice_enabled = True
        game.prepare_class_resources_for_combat(Warrior)
        starting_hp = target.current_hp
        starting_grit = int(Warrior.resources.get("grit", 0))
        target_number = game.effective_attack_target_number(target)
        total_modifier = (
            Warrior.attack_bonus()
            + game.ally_pressure_bonus(Warrior, [Warrior], ranged=Warrior.weapon.ranged)
            + game.status_accuracy_modifier(Warrior)
            + game.attack_focus_modifier(Warrior, target)
            + game.weapon_master_style_accuracy_modifier(Warrior, target)
            + game.assassin_accuracy_modifier(Warrior, target, [Warrior])
            + game.target_accuracy_modifier(target)
        )
        near_miss_roll = target_number - total_modifier - 1
        self.assertGreater(near_miss_roll, 1)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=near_miss_roll, rolls=[near_miss_roll], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        game.perform_weapon_attack(Warrior, target, [Warrior], [target], set())

        self.assertEqual(target.current_hp, starting_hp)
        self.assertFalse(game.has_status(target, "exposed"))
        self.assertFalse(game.has_status(target, "chipped_armor"))
        self.assertEqual(int(Warrior.resources.get("grit", 0)), starting_grit)
        self.assertNotIn("karmic_empty_hostile_actions", Warrior.bond_flags)

    def test_karmic_close_control_failure_uses_final_roll_result(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        archer = create_enemy("bandit_archer")
        archer.resources["ash_shot"] = 0
        game._in_combat = True
        game.karmic_dice_enabled = True
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=8, rolls=[8], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        game.enemy_turn(archer, [Warrior], [archer], Encounter("Test", "", [archer]), set())

        self.assertTrue(game.has_status(Warrior, "restrained"))
        self.assertFalse(game.has_status(Warrior, "slowed"))

    def test_extreme_heavy_armor_can_reach_eighty_percent_defense(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        Warrior.armor = Armor(
            name="Test Bulwark Plate",
            base_ac=18,
            dex_cap=0,
            heavy=True,
            defense_percent=70,
        )
        Warrior.gear_bonuses.clear()
        Warrior.gear_bonuses["defense_percent"] = 15

        self.assertEqual(game.defense_cap_percent(Warrior), 80)
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 80)

    def test_equipment_sync_converts_old_ac_gear_to_percent_defense(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        Warrior.equipment_slots = {
            "head": "iron_cap_common",
            "ring_1": None,
            "ring_2": None,
            "neck": None,
            "chest": "chain_mail_common",
            "gloves": None,
            "boots": None,
            "main_hand": "longsword_common",
            "off_hand": "shield_common",
            "cape": None,
        }

        game.sync_equipment(Warrior)

        self.assertNotIn("AC", Warrior.gear_bonuses)
        self.assertEqual(Warrior.gear_bonuses["defense_percent"], 5)
        self.assertEqual(Warrior.gear_bonuses["shield_defense_percent"], 5)
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 45)

    def test_raised_shield_adds_temporary_percent_defense(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter("Sparring", "A shield drill.", [enemy])

        self.assertIn("Raise Shield", game.get_player_combat_options(Warrior, encounter, heroes=[Warrior]))
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 40)

        game.use_raise_shield(Warrior)

        self.assertTrue(game.has_status(Warrior, "raised_shield"))
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 50)
        self.assertNotIn("Raise Shield", game.get_player_combat_options(Warrior, encounter, heroes=[Warrior]))

    def test_combat_stances_are_mutually_exclusive_and_adjust_stats(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        self.assertEqual(game.current_combat_stance_key(Warrior), "neutral")
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 40)
        self.assertEqual(game.effective_avoidance(Warrior), 0)
        self.assertEqual(game.effective_stability(Warrior), 3)

        game.set_combat_stance(Warrior, "guard")
        self.assertEqual(game.current_combat_stance_key(Warrior), "guard")
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 60)
        self.assertEqual(game.effective_avoidance(Warrior), 0)
        self.assertEqual(game.effective_stability(Warrior), 5)
        self.assertEqual(game.status_accuracy_modifier(Warrior), -2)

        game.set_combat_stance(Warrior, "brace")
        self.assertEqual(game.current_combat_stance_key(Warrior), "brace")
        self.assertFalse(game.has_status(Warrior, "stance_guard"))
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 50)
        self.assertEqual(game.effective_avoidance(Warrior), -1)
        self.assertEqual(game.effective_stability(Warrior), 7)
        self.assertEqual(game.status_accuracy_modifier(Warrior), -1)

        game.set_combat_stance(Warrior, "mobile")
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 35)
        self.assertEqual(game.effective_avoidance(Warrior), 2)
        self.assertEqual(game.effective_stability(Warrior), 2)
        self.assertEqual(game.status_value(Warrior, "flee_bonus"), 2)

        game.set_combat_stance(Warrior, "aggressive")
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 30)
        self.assertEqual(game.effective_avoidance(Warrior), -1)
        self.assertEqual(game.status_accuracy_modifier(Warrior), 2)
        self.assertEqual(game.status_damage_modifier(Warrior), 2)

        game.set_combat_stance(Warrior, "aim")
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 35)
        self.assertEqual(game.effective_avoidance(Warrior), -2)
        self.assertEqual(game.effective_stability(Warrior), 2)
        self.assertEqual(game.status_accuracy_modifier(Warrior), 2)

        game.set_combat_stance(Warrior, "neutral")
        self.assertEqual(game.current_combat_stance_key(Warrior), "neutral")
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 40)

    def test_press_stance_applies_outgoing_armor_break_without_self_vulnerability(self) -> None:
        game, attacker = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, target = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        game.set_combat_stance(attacker, "press")
        self.assertEqual(game.effective_defense_percent(attacker, damage_type="slashing"), 35)
        self.assertEqual(game.effective_defense_percent(target, damage_type="slashing"), 40)

        actual = game.apply_damage(target, 10, damage_type="slashing", source_actor=attacker, apply_defense=True)

        result = game.last_damage_resolution()
        self.assertEqual(result.armor_break_percent, 10)
        self.assertEqual(result.defense_percent, 30)
        self.assertEqual(actual, 7)

    def test_routine_guard_and_cover_statuses_do_not_stack_avoidance(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        game.apply_status(Warrior, "guarded", 1, source="test guard")
        game.apply_status(Warrior, "false_target", 1, source="test decoy")
        game.apply_status(Warrior, "smoke_jar", 1, source="test smoke")

        self.assertEqual(game.effective_avoidance(Warrior), 0)
        self.assertEqual(game.effective_defense_percent(Warrior, damage_type="slashing"), 45)
        self.assertEqual(game.target_accuracy_modifier(Warrior), -3)

    def test_rogue_mobile_stance_preserves_avoidance_identity(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )

        self.assertEqual(game.effective_avoidance(rogue), 3)

        game.set_combat_stance(rogue, "mobile")

        self.assertEqual(game.effective_avoidance(rogue), 5)

    def test_player_can_choose_combat_stance_as_bonus_action(self) -> None:
        answers = iter(["2"])
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game.input_fn = lambda _: next(answers)

        self.assertTrue(game.choose_combat_stance(Warrior))

        self.assertEqual(game.current_combat_stance_key(Warrior), "guard")

    def test_enemy_ai_selects_press_against_high_defense_target(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")

        game.maybe_apply_enemy_stance(enemy, Warrior, [Warrior], [])

        self.assertEqual(game.current_combat_stance_key(enemy), "press")

    def test_level_one_raiders_use_explicit_avoidance_and_defense_bands(self) -> None:
        game, _ = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        bandit = create_enemy("bandit")
        archer = create_enemy("bandit_archer")
        scuttler = create_enemy("rust_shell_scuttler")

        self.assertEqual(game.effective_defense_percent(bandit, damage_type="slashing"), 10)
        self.assertEqual(game.effective_avoidance(bandit), 0)
        self.assertEqual(game.effective_attack_target_number(bandit), 8)
        self.assertGreaterEqual(6 + 3, game.effective_attack_target_number(bandit))
        self.assertEqual(game.effective_defense_percent(archer, damage_type="slashing"), 15)
        self.assertEqual(game.effective_avoidance(archer), 1)
        self.assertEqual(game.effective_defense_percent(scuttler, damage_type="slashing"), 25)
        self.assertEqual(game.effective_avoidance(scuttler), 0)

    def test_low_level_ordinary_enemy_damage_dice_are_smoothed(self) -> None:
        cases = {
            "bandit": "1d4+1",
            "bandit_archer": "1d4+1",
            "ash_brand_enforcer": "1d4+3",
            "acidmaw_burrower": "1d4+4",
            "bugbear_reaver": "1d4+4",
            "ochre_slime": "2d4+2",
        }

        for template, expected_damage in cases.items():
            with self.subTest(template=template):
                enemy = create_enemy(template)
                self.assertEqual(enemy.weapon.damage, expected_damage)
                self.assertEqual(enemy.bond_flags["smoothed_damage_expression"]["smoothed"], expected_damage)

        self.assertEqual(create_enemy("orc_bloodchief").weapon.damage, "1d12+1")

    def test_low_level_scout_brute_shieldhand_and_named_profiles_are_converted(self) -> None:
        game, _ = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        cases = {
            "false_map_skirmisher": (15, 3),
            "ogre_brute": (20, -1),
            "rukhar": (30, 0),
            "sereth_vane": (25, 2),
        }

        for template, (defense, avoidance) in cases.items():
            with self.subTest(template=template):
                enemy = create_enemy(template)
                self.assertEqual(game.effective_defense_percent(enemy, damage_type="slashing"), defense)
                self.assertEqual(game.effective_avoidance(enemy), avoidance)
                self.assertEqual(enemy.bond_flags["combat_profile"]["defense_percent"], defense)
                self.assertEqual(enemy.bond_flags["combat_profile"]["avoidance"], avoidance)

    def test_high_defense_enemies_stay_rare_before_level_four(self) -> None:
        game, _ = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        high_defense_before_four: list[str] = []
        high_defense_at_four: set[str] = set()
        for template in LOW_LEVEL_ENEMY_COMBAT_PROFILES:
            enemy = create_enemy(template)
            defense = game.effective_defense_percent(enemy, damage_type="slashing")
            if enemy.level < 4 and defense >= 35:
                high_defense_before_four.append(template)
            if enemy.level == 4 and defense >= 35:
                high_defense_at_four.add(template)

        self.assertEqual(high_defense_before_four, ["animated_armor", "stonegaze_skulker"])
        self.assertEqual(
            high_defense_at_four,
            {"echo_sapper", "pact_archive_warden", "blacklake_pincerling", "graveblade_wight"},
        )

    def test_all_level_one_to_four_profiles_apply_exact_targets(self) -> None:
        game, _ = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        for template, profile in LOW_LEVEL_ENEMY_COMBAT_PROFILES.items():
            with self.subTest(template=template):
                enemy = create_enemy(template)
                self.assertLessEqual(enemy.level, 4)
                self.assertEqual(
                    game.effective_defense_percent(enemy, damage_type="slashing"),
                    profile["defense_percent"],
                )
                self.assertEqual(game.effective_avoidance(enemy), profile["avoidance"])

    def test_enemy_avoidance_profiles_follow_declared_bands(self) -> None:
        covered_values = {
            value
            for minimum, maximum in AVOIDANCE_BANDS.values()
            for value in range(minimum, maximum + 1)
        }
        high_avoidance_templates = {
            template
            for template, profile in LOW_LEVEL_ENEMY_COMBAT_PROFILES.items()
            if profile["avoidance"] >= AVOIDANCE_BANDS["high"][0]
        }

        for template, profile in LOW_LEVEL_ENEMY_COMBAT_PROFILES.items():
            with self.subTest(template=template):
                self.assertIn(profile["avoidance"], covered_values)
                self.assertLessEqual(profile["avoidance"], AVOIDANCE_BANDS["high"][1])

        self.assertEqual(high_avoidance_templates, HIGH_AVOIDANCE_ENEMY_TEMPLATES)

    def test_ordinary_enemy_profiles_land_in_baseline_hit_target(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        ordinary_templates = [
            "bandit",
            "bandit_archer",
            "brand_saboteur",
            "ash_brand_enforcer",
            "gutter_zealot",
            "rukhar",
        ]
        minimum, maximum = BASELINE_HIT_CHANCE_TARGET

        for template in ordinary_templates:
            with self.subTest(template=template):
                result = simulate_weapon_attack(game, Warrior, create_enemy(template))
                self.assertGreaterEqual(result.hit_chance, minimum)
                self.assertLessEqual(result.hit_chance, maximum + 0.000001)

    def test_combat_simulator_reports_exact_hit_chance_against_avoidance(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        bandit = create_enemy("bandit")
        skirmisher = create_enemy("false_map_skirmisher")

        bandit_result = simulate_weapon_attack(game, Warrior, bandit)
        skirmisher_result = simulate_weapon_attack(game, Warrior, skirmisher)

        self.assertEqual(bandit_result.target_number, 8)
        self.assertEqual(bandit_result.accuracy_bonus, 5)
        self.assertAlmostEqual(bandit_result.miss_chance, 0.10)
        self.assertAlmostEqual(bandit_result.normal_hit_chance, 0.85)
        self.assertAlmostEqual(bandit_result.critical_chance, 0.05)
        self.assertAlmostEqual(bandit_result.hit_chance, 0.90)
        self.assertEqual(skirmisher_result.target_number, 11)
        self.assertAlmostEqual(skirmisher_result.hit_chance, 0.75)

    def test_combat_simulator_expected_damage_uses_percentage_defense(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        bandit = create_enemy("bandit")

        result = simulate_weapon_attack(game, Warrior, bandit)

        self.assertEqual(result.damage.defense_percent, 10)
        self.assertEqual(result.damage.armor_break_percent, 0)
        self.assertAlmostEqual(result.damage.expected_hp_damage_on_normal_hit, 6.375)
        self.assertAlmostEqual(result.damage.expected_hp_damage_on_critical_hit, 10.328125)
        self.assertAlmostEqual(result.expected_hp_damage, 5.93515625)

    def test_combat_simulator_guard_stance_reduces_incoming_weapon_damage(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        bandit = create_enemy("bandit")

        base = simulate_weapon_attack(game, bandit, Warrior, heroes=[bandit], enemies=[])
        game.set_combat_stance(Warrior, "guard", announce=False)
        guarded = simulate_weapon_attack(game, bandit, Warrior, heroes=[bandit], enemies=[])

        self.assertEqual(base.target_number, 8)
        self.assertEqual(base.damage.defense_percent, 40)
        self.assertAlmostEqual(base.hit_chance, 0.80)
        self.assertAlmostEqual(base.expected_hp_damage, 1.8781250000000003)
        self.assertEqual(guarded.target_number, 8)
        self.assertEqual(guarded.damage.defense_percent, 60)
        self.assertAlmostEqual(guarded.hit_chance, 0.80)
        self.assertAlmostEqual(guarded.expected_hp_damage, 1.2437500000000001)
        self.assertLess(guarded.expected_hp_damage, base.expected_hp_damage)

    def test_ordinary_enemy_critical_damage_is_capped_by_target_max_hp(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        enemy.weapon.damage = "2d8+10"
        cap = game.enemy_critical_hp_damage_cap(enemy, Warrior, critical_hit=True)
        assert cap is not None
        self.assertEqual(cap, (Warrior.max_hp * 35 + 99) // 100)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 30, [10, 10], 10)  # type: ignore[method-assign]

        self.assertTrue(game.perform_enemy_attack(enemy, Warrior, [Warrior], [enemy], set()))

        self.assertEqual(game.last_damage_resolution().hp_damage, cap)
        self.assertEqual(Warrior.current_hp, Warrior.max_hp - cap)

    def test_boss_critical_cap_requires_telegraphed_attack_exception(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        boss = create_enemy("orc_bloodchief")
        boss.weapon.damage = "2d8+10"
        boss_cap = game.enemy_critical_hp_damage_cap(boss, Warrior, critical_hit=True)
        assert boss_cap is not None
        self.assertEqual(boss_cap, (Warrior.max_hp * 45 + 99) // 100)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 30, [10, 10], 10)  # type: ignore[method-assign]

        self.assertTrue(game.perform_enemy_attack(boss, Warrior, [Warrior], [boss], set()))
        self.assertEqual(game.last_damage_resolution().hp_damage, boss_cap)

        Warrior.current_hp = Warrior.max_hp
        Warrior.dead = False
        boss.bond_flags["telegraphed_attack"] = True
        self.assertIsNone(game.enemy_critical_hp_damage_cap(boss, Warrior, critical_hit=True))

        self.assertTrue(game.perform_enemy_attack(boss, Warrior, [Warrior], [boss], set()))
        self.assertGreater(game.last_damage_resolution().hp_damage, boss_cap)

    def test_combat_simulator_armor_break_raises_expected_damage(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        animated_armor = create_enemy("animated_armor")

        armored = simulate_weapon_attack(game, Warrior, animated_armor)
        broken = simulate_weapon_attack(game, Warrior, animated_armor, armor_break_percent=20)

        self.assertEqual(armored.damage.defense_percent, 45)
        self.assertEqual(broken.damage.armor_break_percent, 20)
        self.assertEqual(broken.damage.defense_percent, 25)
        self.assertAlmostEqual(armored.expected_hp_damage, 3.56796875)
        self.assertAlmostEqual(broken.expected_hp_damage, 5.15625)
        self.assertGreater(broken.expected_hp_damage, armored.expected_hp_damage)

    def test_combat_simulator_tracks_glance_without_wound(self) -> None:
        game, attacker = build_game_with_player(
            "Warrior",
            {"STR": 10, "DEX": 10, "CON": 10, "INT": 8, "WIS": 10, "CHA": 10},
        )
        _, target = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        attacker.weapon = Weapon(name="Needle", damage="1d1", ability="STR")
        target.armor = Armor(
            name="Test Plate",
            base_ac=16,
            dex_cap=0,
            heavy=True,
            defense_percent=75,
            defense_cap_percent=75,
        )
        target.shield = False
        target.equipment_bonuses.clear()
        target.gear_bonuses.clear()
        target.relationship_bonuses.clear()

        result = simulate_weapon_attack(game, attacker, target)

        self.assertEqual(result.damage.defense_percent, 75)
        self.assertAlmostEqual(result.expected_hp_damage, 0.0)
        self.assertAlmostEqual(result.glance_chance, result.hit_chance)
        self.assertAlmostEqual(result.wound_chance, 0.0)

    def test_wound_riders_require_hp_damage_after_glance(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        Warrior.armor = Armor(
            name="Test Plate",
            base_ac=16,
            dex_cap=0,
            heavy=True,
            defense_percent=75,
            defense_cap_percent=75,
        )
        Warrior.shield = False
        Warrior.equipment_bonuses.clear()
        Warrior.gear_bonuses.clear()
        Warrior.relationship_bonuses.clear()
        stalker = create_enemy("carrion_stalker")
        stalker.weapon = Weapon(name="Serrated Talon", damage="1d1", ability="STR")
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=15, rolls=[15], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 1, [1], 0)  # type: ignore[method-assign]

        game.perform_enemy_attack(stalker, Warrior, [Warrior], [stalker], set())

        self.assertTrue(game.last_damage_was_glance())
        self.assertFalse(game.last_damage_caused_wound())
        self.assertFalse(game.has_status(Warrior, "bleeding"))

        Warrior.armor.defense_percent = 0
        Warrior.armor.defense_cap_percent = 75
        game.perform_enemy_attack(stalker, Warrior, [Warrior], [stalker], set())

        self.assertFalse(game.last_damage_was_glance())
        self.assertTrue(game.last_damage_caused_wound())
        self.assertTrue(game.has_status(Warrior, "bleeding"))

    def test_shared_class_framework_prepares_grit_edge_satchel_toxin_and_ward(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        _, Mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        Mage.features.append("mage_ward")

        for actor in (warrior, rogue, Mage):
            game.prepare_class_resources_for_combat(actor)

        self.assertEqual(warrior.max_resources["grit"], 6)
        self.assertEqual(warrior.resources["grit"], 1)
        self.assertEqual(rogue.max_resources["edge"], 5)
        self.assertEqual(rogue.resources["edge"], 1)
        self.assertEqual(rogue.max_resources["satchel"], 5)
        self.assertEqual(rogue.resources["satchel"], 5)
        self.assertEqual(rogue.max_resources["toxin"], 5)
        self.assertEqual(rogue.resources["toxin"], 0)
        self.assertEqual(Mage.max_resources["ward"], 12)
        self.assertEqual(Mage.resources["ward"], 0)

    def test_ward_absorbs_after_defense_before_temp_hp(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        Warrior.features.append("mage_ward")
        game.synchronize_class_resources(Warrior, refill=True)
        Warrior.temp_hp = 10

        game.grant_ward(Warrior, 4, source="test shell")
        actual = game.apply_damage(Warrior, 10, damage_type="slashing", apply_defense=True)

        result = game.last_damage_resolution()
        self.assertEqual(result.defense_percent, 40)
        self.assertEqual(result.mitigated_damage, 6)
        self.assertEqual(result.ward_absorbed, 4)
        self.assertEqual(result.temp_hp_absorbed, 2)
        self.assertEqual(actual, 0)
        self.assertFalse(result.glance)
        self.assertFalse(result.wound)
        self.assertEqual(Warrior.resources["ward"], 0)
        self.assertEqual(Warrior.temp_hp, 8)

    def test_shared_mage_starts_with_charge_focus_and_combat_options(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)

        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertEqual(mage.max_resources["mp"], 13)
        self.assertEqual(mage.resources["mp"], 13)
        self.assertEqual(mage.max_resources["focus"], 5)
        self.assertEqual(mage.resources["focus"], 0)
        self.assertEqual(game.effective_defense_percent(mage, damage_type="slashing"), 10)
        self.assertIn("Arcane Bolt (Action, 2 MP)", options)
        self.assertIn("Arcane Bolt (Bonus, 1 MP)", options)
        self.assertIn("Minor Channel (1 MP)", options)
        self.assertIn("Pattern Read", options)
        self.assertIn("Ground", options)
        self.assertEqual(game.combat_option_group("Arcane Bolt (Action, 2 MP)"), "Action")
        self.assertEqual(game.combat_option_group("Arcane Bolt (Bonus, 1 MP)"), "Bonus Action")
        self.assertEqual(game.combat_option_group("Pattern Read"), "Bonus Action")
        self.assertEqual(game.combat_option_group("Ground"), "Bonus Action")

    def test_pattern_read_marks_weakest_resist_lane_and_grants_focus_once(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("animated_armor")
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)

        expected_ability, _ = game.mage_lowest_resist_lane(target)

        self.assertTrue(game.use_pattern_read(mage, target))
        self.assertTrue(game.target_is_pattern_read_by(mage, target))
        self.assertEqual(target.bond_flags["mage_pattern_read_lowest_save"], expected_ability)
        self.assertTrue(game.has_status(target, "pattern_read"))
        self.assertEqual(mage.resources["focus"], 1)

        self.assertTrue(game.use_pattern_read(mage, target))

        self.assertEqual(mage.resources["focus"], 1)

    def test_ground_trades_avoidance_for_resist_and_stability(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        before_avoidance = game.effective_avoidance(mage)
        before_stability = game.effective_stability(mage)

        self.assertTrue(game.use_ground(mage))

        self.assertTrue(game.has_status(mage, "grounded_channel"))
        self.assertEqual(game.effective_avoidance(mage), before_avoidance - 1)
        self.assertEqual(game.effective_stability(mage), before_stability + 1)
        self.assertEqual(game.status_value(mage, "save_bonus"), 1)

    def test_arcane_bolt_uses_action_bonus_scaling_cost_damage_and_shared_cooldown(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        target.current_hp = target.max_hp = 30
        encounter = Encounter(title="Test", description="", enemies=[target], allow_flee=False)
        game._in_combat = True
        game._active_round_number = 1
        game._active_combat_heroes = [mage]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(mage)
        captured: dict[str, str | int] = {}

        self.assertEqual(game.arcane_bolt_mp_cost(mage), 1)
        self.assertEqual(game.arcane_bolt_mp_cost(mage, action_cast=True), 2)
        self.assertEqual(game.arcane_bolt_damage_expression(mage), "1d4")
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])
        self.assertIn("Arcane Bolt (Action, 2 MP)", options)
        self.assertIn("Arcane Bolt (Bonus, 1 MP)", options)

        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=12, rolls=[12])  # type: ignore[method-assign]

        def fixed_damage(expression, *args, **kwargs):
            captured["expression"] = expression
            captured["bonus"] = kwargs.get("bonus", 0)
            return RollOutcome(expression, 2, [2], 0)

        game.roll_with_display_bonus = fixed_damage  # type: ignore[method-assign]
        before_hp = target.current_hp

        self.assertTrue(game.use_arcane_bolt(mage, target, [mage], [target], set()))

        self.assertEqual(mage.resources["mp"], 12)
        self.assertEqual(captured["expression"], "1d4")
        self.assertEqual(captured["bonus"], mage.ability_mod("INT"))
        self.assertEqual(target.current_hp, before_hp - 5)
        self.assertEqual(mage.conditions.get("arcane_bolt_cooldown"), 2)
        cooldown_options = game.get_player_combat_options(mage, encounter, heroes=[mage])
        self.assertNotIn("Arcane Bolt (Action, 2 MP)", cooldown_options)
        self.assertNotIn("Arcane Bolt (Bonus, 1 MP)", cooldown_options)

        mage.conditions.pop("arcane_bolt_cooldown")
        target.current_hp = before_hp
        self.assertTrue(game.use_arcane_bolt(mage, target, [mage], [target], set(), action_cast=True))

        self.assertEqual(mage.resources["mp"], 10)
        self.assertEqual(target.current_hp, before_hp - 10)
        self.assertEqual(mage.conditions.get("arcane_bolt_cooldown"), 2)

        for level in (2, 3, 4):
            game.level_up_character(mage, level)
        self.assertEqual(game.arcane_bolt_mp_cost(mage), 2)
        self.assertEqual(game.arcane_bolt_mp_cost(mage, action_cast=True), 4)
        self.assertEqual(game.arcane_bolt_damage_expression(mage), "2d4")

    def test_minor_channel_uses_pattern_read_save_lane_and_builds_focus(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(mage)
        game.use_pattern_read(mage, target)
        captured: dict[str, int | str] = {}

        def fail_save(actor, ability, dc, **kwargs):
            captured["ability"] = ability
            captured["dc"] = dc
            return False

        game.saving_throw = fail_save  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 5, [5], 0)  # type: ignore[method-assign]
        before_hp = target.current_hp

        self.assertTrue(game.use_minor_channel(mage, target))

        self.assertEqual(mage.resources["mp"], 12)
        self.assertEqual(captured["ability"], target.bond_flags["mage_pattern_read_lowest_save"])
        self.assertEqual(captured["dc"], 13)
        self.assertEqual(target.current_hp, before_hp - 5)
        self.assertTrue(game.has_status(target, "reeling"))
        self.assertEqual(mage.resources["focus"], 2)

    def test_spellguard_training_adds_ward_and_combat_options(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(mage, 2)
        game.level_up_character(mage, 3)
        game.level_up_character(mage, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertIn("spellguard_ward", mage.features)
        self.assertEqual(mage.max_resources["ward"], 15)
        self.assertEqual(mage.resources["ward"], 0)
        self.assertIn("Anchor Shell (3 MP)", options)
        self.assertIn("Blue Glass Palm (1 MP)", options)
        self.assertIn("Lockstep Field (3 MP)", options)
        self.assertEqual(game.combat_option_group("Anchor Shell (3 MP)"), "Bonus Action")

    def test_anchor_shell_grants_ward_defense_and_reels_when_broken(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        attacker = create_enemy("bandit")
        mage.features.extend(["spellguard_ward", "anchor_shell"])
        game.state.companions = [ally]
        game._in_combat = True
        game._active_round_number = 1
        game._active_combat_heroes = [mage, ally]
        game._active_combat_enemies = [attacker]
        game.prepare_class_resources_for_combat(mage)
        defense_before = game.effective_defense_percent(ally, damage_type="slashing")

        self.assertTrue(game.use_anchor_shell(mage, ally))

        self.assertEqual(mage.resources["mp"], 10)
        self.assertEqual(ally.resources["ward"], 5)
        self.assertTrue(game.has_status(ally, "anchor_shell"))
        self.assertEqual(game.effective_defense_percent(ally, damage_type="slashing"), defense_before + 5)
        self.assertIs(game.ward_draw_priority_target([mage, ally]), ally)
        self.assertEqual(game.attack_focus_modifier(attacker, mage), -1)
        self.assertEqual(game.attack_focus_modifier(attacker, ally), 0)

        actual = game.apply_damage(ally, 10, damage_type="slashing", source_actor=attacker, apply_defense=True)

        self.assertEqual(actual, 0)
        self.assertEqual(game.last_damage_resolution().ward_absorbed, 5)
        self.assertEqual(ally.resources.get("ward", 0), 0)
        self.assertFalse(game.has_status(ally, "anchor_shell"))
        self.assertTrue(game.has_status(attacker, "reeling"))

    def test_ward_shell_auto_reaction_spends_charge_before_temp_hp(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        attacker = create_enemy("bandit")
        mage.features.append("ward_shell")
        mage.temp_hp = 4
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(mage)
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 6, [6], 0)  # type: ignore[method-assign]

        actual = game.apply_damage(mage, 10, damage_type="slashing", source_actor=attacker, apply_defense=True)

        self.assertEqual(actual, 0)
        self.assertEqual(game.last_damage_resolution().ward_absorbed, 9)
        self.assertEqual(game.last_damage_resolution().temp_hp_absorbed, 0)
        self.assertEqual(mage.temp_hp, 4)
        self.assertEqual(mage.resources["mp"], 11)
        self.assertEqual(mage.bond_flags["class_reaction_used_round"], 1)

    def test_lockstep_field_spends_charge_and_guards_allies(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        mage.features.append("lockstep_field")
        game.state.companions = [ally]
        game._in_combat = True
        game._active_combat_heroes = [mage, ally]
        game.prepare_class_resources_for_combat(mage)
        ally_stability = game.effective_stability(ally)

        self.assertTrue(game.use_lockstep_field(mage))

        self.assertEqual(mage.resources["mp"], 10)
        for target in (mage, ally):
            self.assertTrue(game.has_status(target, "guarded"))
            self.assertTrue(game.has_status(target, "lockstep_field"))
        self.assertEqual(game.effective_stability(ally), ally_stability + 1)

    def test_blue_glass_palm_spends_charge_damages_and_reels_on_failed_save(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        mage.features.append("blue_glass_palm")
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]
        before_hp = target.current_hp

        self.assertTrue(game.use_blue_glass_palm(mage, target))

        self.assertEqual(mage.resources["mp"], 12)
        self.assertEqual(target.current_hp, before_hp - 4)
        self.assertTrue(game.has_status(target, "reeling"))
        self.assertTrue(game.target_is_fixated_by(mage, target))
        self.assertIs(game.fixated_priority_target(target, [ally, mage]), mage)
        self.assertEqual(game.attack_focus_modifier(target, ally), -2)
        self.assertEqual(game.attack_focus_modifier(target, mage), 0)

    def test_arcanist_training_adds_arc_pattern_charge_and_combat_options(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(mage, 2)
        game.level_up_character(mage, 3)
        game.level_up_character(mage, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertIn("arcanist_arc", mage.features)
        self.assertIn("pattern_charge", mage.features)
        self.assertEqual(mage.max_resources["arc"], 6)
        self.assertEqual(mage.resources["arc"], 0)
        self.assertIn("Arc Pulse (1 MP)", options)
        self.assertIn("Marked Angle (1 MP)", options)
        self.assertNotIn("Detonate Pattern (2 Arc)", options)

        mage.resources["arc"] = 2
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertIn("Detonate Pattern (2 Arc)", options)
        self.assertEqual(game.combat_option_group("Marked Angle (1 MP)"), "Bonus Action")

    def test_pattern_read_quiet_sum_and_marked_angle_build_arcanist_setup(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        mage.features.extend(["arcanist_arc", "pattern_charge", "marked_angle", "quiet_sum"])
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(mage)

        self.assertTrue(game.use_pattern_read(mage, target))

        self.assertEqual(mage.resources["arc"], 1)

        self.assertTrue(game.use_pattern_read(mage, target))

        self.assertEqual(mage.resources["arc"], 1)

        self.assertTrue(game.use_marked_angle(mage, target))

        self.assertEqual(mage.resources["mp"], 12)
        self.assertEqual(mage.resources["arc"], 2)
        self.assertEqual(game.arcanist_pattern_charges(mage, target), 1)
        self.assertIn("Pattern Charge 1", game.describe_combatant(target))

    def test_arc_pulse_uses_save_damage_and_builds_pattern_charge_on_failed_save(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        mage.features.extend(["arcanist_arc", "pattern_charge", "arc_pulse"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        captured: dict[str, int | str] = {}

        def fail_save(actor, ability, dc, **kwargs):
            captured["ability"] = ability
            captured["dc"] = dc
            return False

        game.saving_throw = fail_save  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 5, [5], 0)  # type: ignore[method-assign]
        before_hp = target.current_hp

        self.assertTrue(game.use_arc_pulse(mage, target))

        self.assertEqual(mage.resources["mp"], 12)
        self.assertEqual(captured["ability"], "DEX")
        self.assertEqual(captured["dc"], 13)
        self.assertEqual(target.current_hp, before_hp - 5)
        self.assertEqual(mage.resources["arc"], 1)
        self.assertEqual(game.arcanist_pattern_charges(mage, target), 1)

    def test_detonate_pattern_spends_arc_consumes_charges_and_scales_damage(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("animated_armor")
        mage.features.extend(["arcanist_arc", "pattern_charge", "detonate_pattern"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        game.set_arcanist_pattern_charges(mage, target, 3)
        mage.resources["arc"] = 2
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 12, [4, 4, 4], 0)  # type: ignore[method-assign]
        before_hp = target.current_hp

        self.assertTrue(game.use_detonate_pattern(mage, target))

        self.assertEqual(mage.resources["arc"], 0)
        self.assertEqual(game.arcanist_pattern_charges(mage, target), 0)
        self.assertFalse(game.has_status(target, "pattern_charge"))
        self.assertEqual(target.current_hp, before_hp - 12)

    def test_minor_channel_failed_save_feeds_arcanist_pattern_charge(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        target = create_enemy("bandit")
        mage.features.extend(["arcanist_arc", "pattern_charge"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 5, [5], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_minor_channel(mage, target))

        self.assertEqual(mage.resources["arc"], 1)
        self.assertEqual(game.arcanist_pattern_charges(mage, target), 1)

    def test_elementalist_training_adds_attunement_fields_and_combat_options(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(mage, 2)
        game.level_up_character(mage, 3)
        game.level_up_character(mage, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertIn("elementalist_attunement", mage.features)
        self.assertIn("elemental_weave", mage.features)
        self.assertEqual(mage.max_resources["attunement"], 4)
        self.assertEqual(mage.resources["attunement"], 0)
        self.assertIn("Ember Lance (1 MP)", options)
        self.assertIn("Frost Shard (1 MP)", options)
        self.assertIn("Volt Grasp (1 MP)", options)
        self.assertIn("Burning Line (4 MP)", options)
        self.assertIn("Lockfrost (4 MP)", options)
        self.assertIn("Change Weather", options)
        self.assertEqual(game.combat_option_group("Change Weather"), "Bonus Action")

    def test_elementalist_minor_channels_gain_attunement_and_apply_riders(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        fire_target = create_enemy("bandit")
        cold_target = create_enemy("bandit")
        shock_target = create_enemy("bandit")
        mage.features.extend(["elementalist_attunement", "elemental_weave", "ember_lance", "frost_shard", "volt_grasp"])
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(mage)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 5, [5], 0)  # type: ignore[method-assign]
        fire_hp = fire_target.current_hp

        self.assertTrue(game.use_ember_lance(mage, fire_target))

        self.assertEqual(fire_target.current_hp, fire_hp - 5)
        self.assertTrue(game.has_status(fire_target, "burning"))
        self.assertEqual(game.elementalist_active_element(mage), "fire")
        self.assertEqual(mage.resources["attunement"], 1)

        self.assertTrue(game.use_frost_shard(mage, cold_target))

        self.assertEqual(game.elementalist_active_element(mage), "cold")
        self.assertEqual(game.elementalist_previous_element(mage), "fire")
        self.assertEqual(mage.resources["attunement"], 1)
        self.assertTrue(game.has_status(cold_target, "slowed"))
        self.assertTrue(game.has_status(cold_target, "blinded"))

        game._active_round_number = 2

        self.assertTrue(game.use_volt_grasp(mage, shock_target))

        self.assertEqual(game.elementalist_active_element(mage), "lightning")
        self.assertEqual(game.elementalist_previous_element(mage), "cold")
        self.assertEqual(mage.resources["attunement"], 1)
        self.assertTrue(game.has_status(shock_target, "reeling"))
        self.assertEqual(shock_target.bond_flags["class_reaction_used_round"], 2)

    def test_change_weather_preserves_one_attunement_stack(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        mage.features.extend(["elementalist_attunement", "change_weather_hand"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        mage.resources["attunement"] = 3
        game.set_elementalist_active_element(mage, "fire")

        self.assertTrue(game.use_change_weather_hand(mage, "cold"))

        self.assertEqual(game.elementalist_active_element(mage), "cold")
        self.assertEqual(game.elementalist_previous_element(mage), "fire")
        self.assertEqual(mage.resources["attunement"], 1)

    def test_burning_line_area_save_hits_multiple_targets_and_leaves_field(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        first = create_enemy("bandit")
        second = create_enemy("ash_brand_enforcer")
        mage.features.extend(["elementalist_attunement", "burning_line"])
        game._in_combat = True
        game._active_combat_heroes = [mage]
        game._active_combat_enemies = [first, second]
        game.prepare_class_resources_for_combat(mage)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]
        first_hp = first.current_hp
        second_hp = second.current_hp

        self.assertTrue(game.use_burning_line(mage))

        self.assertEqual(mage.resources["mp"], 9)
        self.assertEqual(mage.resources["attunement"], 1)
        self.assertEqual(first.current_hp, first_hp - 4)
        self.assertEqual(second.current_hp, second_hp - 4)
        for target in (first, second):
            self.assertTrue(game.has_status(target, "burning_line"))
            self.assertTrue(game.has_status(target, "burning"))

    def test_lockfrost_area_save_slows_and_drops_already_slowed_targets(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        first = create_enemy("bandit")
        second = create_enemy("ash_brand_enforcer")
        mage.features.extend(["elementalist_attunement", "lockfrost"])
        game._in_combat = True
        game._active_combat_heroes = [mage]
        game._active_combat_enemies = [first, second]
        game.prepare_class_resources_for_combat(mage)
        game.apply_status(first, "slowed", 1, source="test setup")
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]
        second_stability = game.effective_stability(second)

        self.assertTrue(game.use_lockfrost(mage))

        self.assertEqual(mage.resources["mp"], 9)
        self.assertEqual(mage.resources["attunement"], 1)
        self.assertEqual(game.elementalist_active_element(mage), "cold")
        self.assertTrue(game.has_status(first, "prone"))
        for target in (first, second):
            self.assertTrue(game.has_status(target, "slowed"))
            self.assertTrue(game.has_status(target, "lockfrost_field"))
        self.assertEqual(game.effective_stability(second), second_stability - 3)

    def test_aethermancer_training_adds_flow_healing_and_support_options(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(mage, 2)
        game.level_up_character(mage, 3)
        game.level_up_character(mage, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertIn("aethermancer_flow", mage.features)
        self.assertIn("field_mend", mage.features)
        self.assertEqual(mage.max_resources["flow"], 5)
        self.assertEqual(mage.resources["flow"], 0)
        self.assertIn("Field Mend (3 MP)", options)
        self.assertIn("Triage Line (3 MP)", options)
        self.assertIn("Clean Breath (2 MP)", options)
        self.assertIn("Pulse Restore (4 MP)", options)
        self.assertEqual(game.combat_option_group("Pulse Restore (4 MP)"), "Bonus Action")

        mage.resources["flow"] = 1
        options = game.get_player_combat_options(mage, encounter, heroes=[mage])

        self.assertIn("Overflow Shell (1 Flow)", options)
        self.assertEqual(game.combat_option_group("Overflow Shell (1 Flow)"), "Bonus Action")

    def test_field_mend_heals_and_overflow_becomes_ward_and_flow(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        mage.features.extend(["aethermancer_flow", "field_mend"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        ally.current_hp = ally.max_hp - 3
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 8, [8], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_field_mend(mage, ally))

        self.assertEqual(mage.resources["mp"], 10)
        self.assertEqual(ally.current_hp, ally.max_hp)
        self.assertEqual(ally.resources.get("ward", 0), 4)
        self.assertEqual(mage.resources["flow"], 1)

    def test_field_mend_on_downed_ally_costs_extra_charge(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        mage.features.extend(["aethermancer_flow", "field_mend"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        ally.current_hp = 0
        ally.death_failures = 1
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_field_mend(mage, ally))

        self.assertEqual(mage.resources["mp"], 9)
        self.assertEqual(ally.current_hp, 7)
        self.assertEqual(ally.death_failures, 0)

    def test_pulse_restore_bonus_heal_and_overflow_shell(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        mage.features.extend(["aethermancer_flow", "pulse_restore", "overflow_shell"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        ally.current_hp = ally.max_hp - 2
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_pulse_restore(mage, ally))

        self.assertEqual(mage.resources["mp"], 9)
        self.assertEqual(ally.current_hp, ally.max_hp)
        self.assertEqual(ally.resources.get("ward", 0), 4)
        self.assertEqual(mage.resources["flow"], 1)

        self.assertTrue(game.use_overflow_shell(mage, ally))

        self.assertEqual(mage.resources["flow"], 0)
        self.assertEqual(ally.resources.get("ward", 0), 9)

    def test_triage_line_heals_multiple_allies_and_grants_flow(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, first = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, second = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        mage.features.extend(["aethermancer_flow", "triage_line"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        first.current_hp -= 5
        second.current_hp -= 5
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 3, [3], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_triage_line(mage, [mage, first, second]))

        self.assertEqual(mage.resources["mp"], 10)
        self.assertEqual(first.current_hp, first.max_hp - 2)
        self.assertEqual(second.current_hp, second.max_hp - 2)
        for target in (mage, first, second):
            self.assertTrue(game.has_status(target, "triage_line"))
        self.assertEqual(mage.resources["flow"], 1)

    def test_clean_breath_reduces_condition_heals_and_grants_flow(self) -> None:
        game, mage = build_game_with_player(
            "Mage",
            {"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        mage.features.extend(["aethermancer_flow", "clean_breath"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(mage)
        ally.current_hp -= 2
        ally.conditions["poisoned"] = 2

        self.assertTrue(game.use_clean_breath(mage, ally))

        self.assertEqual(mage.resources["mp"], 11)
        self.assertEqual(ally.conditions["poisoned"], 1)
        self.assertEqual(ally.current_hp, ally.max_hp - 1)
        self.assertEqual(mage.resources["flow"], 1)

    def test_rogue_mark_poison_and_wound_hooks_award_resources(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)

        game.mark_class_target(rogue, target)
        stacks = game.add_rogue_poison_stack(rogue, target)
        actual = game.apply_damage(target, 10, damage_type="piercing", source_actor=rogue, apply_defense=True)

        self.assertEqual(stacks, 1)
        self.assertTrue(game.target_is_marked_by(rogue, target))
        self.assertTrue(game.has_status(target, "poisoned"))
        self.assertGreater(actual, 0)
        self.assertTrue(game.last_damage_caused_wound())
        self.assertEqual(rogue.resources["edge"], 2)
        self.assertEqual(rogue.resources["toxin"], 1)
        self.assertEqual(target.bond_flags["class_mark_last_wounded_by"], rogue.name)

    def test_shared_rogue_progression_adds_combat_actions(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(rogue, 2)
        game.level_up_character(rogue, 3)
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        options = game.get_player_combat_options(rogue, encounter, heroes=[rogue])

        self.assertIn("Tool Read", options)
        self.assertIn("Skirmish", options)
        self.assertIn("Feint", options)
        self.assertIn("Dirty Trick", options)
        self.assertIn("slip_away", rogue.features)

    def test_tool_read_marks_exposes_and_grants_edge(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("bandit")
        rogue.features.append("tool_read")
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["edge"] = 0

        self.assertTrue(game.use_tool_read(rogue, target))

        self.assertTrue(game.target_is_marked_by(rogue, target))
        self.assertTrue(game.target_is_tool_read_by(rogue, target))
        self.assertTrue(game.has_status(target, "tool_read"))
        self.assertTrue(game.rogue_target_is_exposed(rogue, target, [rogue]))
        self.assertEqual(game.target_accuracy_modifier(target), 1)
        self.assertEqual(rogue.resources["edge"], 1)

    def test_feint_and_dirty_trick_create_exposed_rogue_openings(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        feint_target = create_enemy("bandit")
        trick_target = create_enemy("ash_brand_enforcer")
        rogue.features.extend(["rogue_feint", "dirty_trick"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["edge"] = 0
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=12, rolls=[12], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        self.assertTrue(game.use_rogue_feint(rogue, feint_target))

        self.assertTrue(game.has_status(feint_target, "reeling"))
        self.assertTrue(game.has_status(feint_target, "exposed"))
        self.assertEqual(rogue.resources["edge"], 1)

        rogue.resources["edge"] = 0
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        self.assertTrue(game.use_dirty_trick(rogue, trick_target, "seam"))

        self.assertTrue(game.has_status(trick_target, "armor_broken"))
        self.assertEqual(game.total_armor_break_percent(trick_target), 10)
        self.assertEqual(rogue.resources["edge"], 1)

    def test_skirmish_near_miss_and_slip_away_spend_edge_around_avoidance(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        attacker = create_enemy("bandit")
        rogue.features.extend(["rogue_skirmish", "slip_away"])
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(rogue)

        self.assertTrue(game.use_rogue_skirmish(rogue))

        self.assertEqual(rogue.resources["edge"], 0)
        self.assertEqual(game.current_combat_stance_key(rogue), "mobile")

        game.clear_combat_stance(rogue)
        target_number = game.effective_attack_target_number(rogue)
        total_modifier = (
            attacker.attack_bonus()
            + game.ally_pressure_bonus(attacker, [attacker], ranged=attacker.weapon.ranged)
            + game.status_accuracy_modifier(attacker)
            + game.attack_focus_modifier(attacker, rogue)
            + game.target_accuracy_modifier(rogue)
        )
        near_miss_roll = target_number - total_modifier - 1
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=near_miss_roll, rolls=[near_miss_roll], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        self.assertFalse(game.perform_enemy_attack(attacker, rogue, [rogue], [attacker], set()))
        self.assertEqual(rogue.resources["edge"], 1)

        game._active_round_number = 2
        hit_by_one_roll = target_number - total_modifier + 1
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=hit_by_one_roll, rolls=[hit_by_one_roll], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        before_hp = rogue.current_hp

        self.assertFalse(game.perform_enemy_attack(attacker, rogue, [rogue], [attacker], set()))

        self.assertEqual(rogue.current_hp, before_hp)
        self.assertEqual(rogue.resources["edge"], 0)
        self.assertEqual(rogue.bond_flags["class_reaction_used_round"], 2)

    def test_shadowguard_training_adds_shadow_resource_and_options(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(rogue, 2)
        game.level_up_character(rogue, 3)
        game.level_up_character(rogue, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["shadow"] = 2
        options = game.get_player_combat_options(rogue, encounter, heroes=[rogue])

        self.assertEqual(rogue.max_resources["shadow"], 5)
        self.assertIn("False Target", options)
        self.assertIn("Smoke Pin", options)
        self.assertIn("Cover The Healer", options)

    def test_false_target_spends_edge_protects_ally_and_grants_shadow_on_miss(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        _, ally = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        attacker = create_enemy("bandit")
        rogue.features.extend(["shadowguard_shadow", "false_target"])
        game.state.companions = [ally]
        game._in_combat = True
        game._active_round_number = 1
        game._active_combat_heroes = [rogue, ally]
        game._active_combat_enemies = [attacker]
        game.prepare_class_resources_for_combat(rogue)

        self.assertTrue(game.use_false_target(rogue, ally))

        self.assertEqual(rogue.resources["edge"], 0)
        self.assertTrue(game.has_status(ally, "false_target"))
        self.assertEqual(game.target_accuracy_modifier(ally), -2)

        target_number = game.effective_attack_target_number(ally)
        total_modifier = (
            attacker.attack_bonus()
            + game.ally_pressure_bonus(attacker, [attacker], ranged=attacker.weapon.ranged)
            + game.status_accuracy_modifier(attacker)
            + game.attack_focus_modifier(attacker, ally)
            + game.target_accuracy_modifier(ally)
        )
        near_miss_roll = target_number - total_modifier - 1
        before_hp = ally.current_hp
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=near_miss_roll, rolls=[near_miss_roll], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        self.assertFalse(game.perform_enemy_attack(attacker, ally, [rogue, ally], [attacker], set()))

        self.assertEqual(ally.current_hp, before_hp)
        self.assertFalse(game.has_status(ally, "false_target"))
        self.assertEqual(rogue.resources["shadow"], 1)
        self.assertTrue(game.has_status(attacker, "reeling"))

    def test_shadowguard_shadow_smoke_pin_and_cover_the_healer(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        _, ally = build_game_with_player(
            "Mage",
            {"STR": 10, "DEX": 12, "CON": 13, "INT": 10, "WIS": 15, "CHA": 14},
        )
        attacker = create_enemy("bandit")
        target = create_enemy("ash_brand_enforcer")
        rogue.features.extend(["shadowguard_shadow", "smoke_pin", "cover_the_healer"])
        game.state.companions = [ally]
        game._in_combat = True
        game._active_round_number = 1
        game._active_combat_heroes = [rogue, ally]
        game._active_combat_enemies = [attacker, target]
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["shadow"] = 0

        target_number = game.effective_attack_target_number(rogue)
        total_modifier = (
            attacker.attack_bonus()
            + game.ally_pressure_bonus(attacker, [attacker], ranged=attacker.weapon.ranged)
            + game.status_accuracy_modifier(attacker)
            + game.attack_focus_modifier(attacker, rogue)
            + game.target_accuracy_modifier(rogue)
        )
        miss_roll = target_number - total_modifier - 5
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=miss_roll, rolls=[miss_roll], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        self.assertFalse(game.perform_enemy_attack(attacker, rogue, [rogue, ally], [attacker], set()))
        self.assertEqual(rogue.resources["shadow"], 1)

        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        self.assertTrue(game.use_smoke_pin(rogue, target))

        self.assertEqual(rogue.resources["shadow"], 0)
        self.assertTrue(game.has_status(target, "blinded"))
        self.assertTrue(game.has_status(target, "exposed"))
        self.assertTrue(game.has_status(rogue, "invisible"))

        rogue.resources["shadow"] = 2

        self.assertTrue(game.use_cover_the_healer(rogue, ally))

        self.assertEqual(rogue.resources["shadow"], 0)
        self.assertTrue(game.has_status(ally, "false_target"))
        self.assertTrue(game.has_status(ally, "guarded"))
        self.assertTrue(game.has_status(ally, "shadow_lane"))

    def test_assassin_training_adds_death_mark_and_combat_options(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(rogue, 2)
        game.level_up_character(rogue, 3)
        game.level_up_character(rogue, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["edge"] = 3
        options = game.get_player_combat_options(rogue, encounter, heroes=[rogue])

        self.assertIn("Death Mark", options)
        self.assertIn("Quiet Knife", options)
        self.assertIn("Between Plates", options)
        self.assertIn("Sudden End", options)

    def test_death_mark_replaces_previous_mark_and_grants_assassin_accuracy(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        first = create_enemy("bandit")
        second = create_enemy("ash_brand_enforcer")
        rogue.features.append("death_mark")
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [first, second]

        self.assertTrue(game.use_death_mark(rogue, first))
        self.assertTrue(game.target_is_death_marked_by(rogue, first))

        self.assertTrue(game.use_death_mark(rogue, second))

        self.assertFalse(game.target_is_death_marked_by(rogue, first))
        self.assertTrue(game.target_is_death_marked_by(rogue, second))
        self.assertEqual(game.assassin_accuracy_modifier(rogue, second, [rogue]), 1)

    def test_quiet_knife_uses_opener_and_first_death_mark_wound_damage(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("ash_brand_enforcer")
        rogue.features.extend(["death_mark", "quiet_knife"])
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        game.use_death_mark(rogue, target)
        game.apply_status(rogue, "invisible", 1, source="test setup")
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=8, rolls=[8], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_quiet_knife(rogue, target, [rogue], [target], set()))

        self.assertTrue(game.last_damage_caused_wound())
        self.assertTrue(rogue.bond_flags[game.assassin_first_wound_key(target)])
        self.assertEqual(target.bond_flags["assassin_death_mark_first_wounded_by"], rogue.name)
        self.assertLess(target.current_hp, target.max_hp - 7)

    def test_between_plates_spends_edge_and_ignores_defense(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("animated_armor")
        rogue.features.extend(["death_mark", "between_plates"])
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["edge"] = 2
        game.use_death_mark(rogue, target)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=12, rolls=[12], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_between_plates(rogue, target, [rogue], [target], set()))

        self.assertEqual(rogue.resources["edge"], 1)
        self.assertGreaterEqual(game.last_damage_resolution().armor_break_percent, 10)

    def test_sudden_end_spends_edge_for_execution_pressure(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("ogre_brute")
        rogue.features.extend(["death_mark", "sudden_end"])
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["edge"] = 3
        target.current_hp = target.max_hp // 2
        before_hp = target.current_hp
        game.use_death_mark(rogue, target)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=8, rolls=[8], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_sudden_end(rogue, target, [rogue], [target], set()))

        self.assertEqual(rogue.resources["edge"], 1)
        self.assertTrue(game.last_damage_caused_wound())
        self.assertLess(target.current_hp, before_hp - 7)

    def test_poisoner_training_starts_with_toxin_and_combat_options(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(rogue, 2)
        game.level_up_character(rogue, 3)
        game.level_up_character(rogue, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        options = game.get_player_combat_options(rogue, encounter, heroes=[rogue])

        self.assertEqual(rogue.max_resources["toxin"], 5)
        self.assertEqual(rogue.resources["toxin"], 5)
        self.assertIn("Black Drop", options)
        self.assertIn("Green Needle", options)
        self.assertIn("Bitter Cloud", options)
        self.assertIn("Rot Thread", options)
        self.assertIn("Bloom In The Blood", options)

    def test_black_drop_spends_toxin_and_delivers_poison_on_next_wound(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("bandit")
        rogue.features.extend(["poisoner_toxin", "black_drop"])
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=9, rolls=[9], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_black_drop(rogue))
        self.assertEqual(rogue.resources["toxin"], 4)

        game.perform_weapon_attack(rogue, target, [rogue], [target], set())

        self.assertFalse(game.has_status(rogue, "black_drop"))
        self.assertTrue(game.last_damage_caused_wound())
        self.assertEqual(game.rogue_poison_stacks(rogue, target), 2)
        self.assertTrue(game.has_status(target, "poisoned"))

    def test_rogue_poison_stacks_tick_damage_and_fade(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("bandit")
        rogue.features.append("poisoner_toxin")
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        game.add_rogue_poison_stack(rogue, target, 3, duration=3)
        before_hp = target.current_hp

        game.tick_conditions(target)

        self.assertEqual(target.current_hp, before_hp - 3)
        self.assertEqual(game.rogue_poison_stacks(rogue, target), 2)
        self.assertTrue(game.has_status(target, "poisoned"))

    def test_bitter_cloud_applies_poison_through_save_pressure(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("animated_armor")
        rogue.features.extend(["poisoner_toxin", "bitter_cloud"])
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        before_hp = target.current_hp

        self.assertTrue(game.use_bitter_cloud(rogue, target))

        self.assertEqual(rogue.resources["toxin"], 4)
        self.assertEqual(game.rogue_poison_stacks(rogue, target), 2)
        self.assertTrue(game.has_status(target, "reeling"))

        game.tick_conditions(target)

        self.assertEqual(target.current_hp, before_hp - 2)

    def test_rot_thread_and_bloom_in_the_blood_work_around_armor(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("animated_armor")
        rogue.features.extend(["poisoner_toxin", "rot_thread", "bloom_in_the_blood"])
        game._in_combat = True
        game._active_combat_heroes = [rogue]
        game._active_combat_enemies = [target]
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["toxin"] = 4
        game.add_rogue_poison_stack(rogue, target, 4, duration=3)

        self.assertTrue(game.use_rot_thread(rogue, target))

        self.assertTrue(game.has_status(target, "rot_thread"))
        self.assertTrue(game.has_status(target, "armor_broken"))
        self.assertGreaterEqual(game.total_armor_break_percent(target), 20)

        before_hp = target.current_hp

        self.assertTrue(game.use_bloom_in_the_blood(rogue, target))

        self.assertEqual(target.current_hp, before_hp - 8)
        self.assertEqual(game.rogue_poison_stacks(rogue, target), 2)

    def test_alchemist_training_adds_satchel_options(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter(title="Test", description="", enemies=[enemy], allow_flee=False)

        game.level_up_character(rogue, 2)
        game.level_up_character(rogue, 3)
        game.level_up_character(rogue, 4)
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        options = game.get_player_combat_options(rogue, encounter, heroes=[rogue])

        self.assertEqual(rogue.max_resources["satchel"], 5)
        self.assertEqual(rogue.resources["satchel"], 5)
        self.assertIn("Quick Mix", options)
        self.assertIn("Redcap Tonic", options)
        self.assertIn("Smoke Jar", options)
        self.assertIn("Bitter Acid", options)
        self.assertIn("Field Stitch", options)

    def test_quick_mix_redcap_tonic_spends_satchel_heals_and_grants_temp_hp(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        ally = build_character(
            name="Mara",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 10, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        rogue.features.extend(["alchemist_quick_mix", "redcap_tonic"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        ally.current_hp = ally.max_hp - 8
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 5, [5], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_quick_mix(rogue))
        self.assertTrue(game.use_redcap_tonic(rogue, ally))

        self.assertEqual(rogue.resources["satchel"], rogue.max_resources["satchel"] - 1)
        self.assertEqual(ally.current_hp, ally.max_hp - 2)
        self.assertEqual(ally.temp_hp, rogue.proficiency_bonus + rogue.ability_mod("INT"))
        self.assertFalse(game.has_status(rogue, "quick_mix"))

    def test_smoke_jar_spends_satchel_and_creates_cover_lane(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        ally = build_character(
            name="Mara",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 10, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        rogue.features.append("smoke_jar")
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        rogue.resources["edge"] = 0

        self.assertTrue(game.use_smoke_jar(rogue, ally, [rogue, ally]))

        self.assertEqual(rogue.resources["satchel"], rogue.max_resources["satchel"] - 1)
        self.assertTrue(game.has_status(rogue, "smoke_jar"))
        self.assertTrue(game.has_status(ally, "smoke_jar"))
        self.assertTrue(game.has_status(ally, "invisible"))
        self.assertEqual(game.target_accuracy_modifier(ally), -1)
        self.assertEqual(rogue.resources["edge"], 1)

    def test_bitter_acid_applies_acid_and_armor_break_on_failed_save(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("animated_armor")
        rogue.features.extend(["alchemist_quick_mix", "bitter_acid"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        game.saving_throw = lambda *args, **kwargs: False  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_quick_mix(rogue, "acid_cut"))
        self.assertTrue(game.use_bitter_acid(rogue, target))

        self.assertEqual(rogue.resources["satchel"], rogue.max_resources["satchel"] - 1)
        self.assertTrue(game.has_status(target, "acid"))
        self.assertTrue(game.has_status(target, "armor_broken"))
        self.assertTrue(game.has_status(target, "reeling"))
        self.assertGreaterEqual(game.total_armor_break_percent(target), 20)

    def test_field_stitch_clears_bleeding_and_stabilizes_downed_ally(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        ally = build_character(
            name="Mara",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 10, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )
        rogue.features.append("field_stitch")
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        ally.current_hp = 0
        ally.death_failures = 2
        game.apply_status(ally, "bleeding", 2, source="test setup")

        self.assertTrue(game.use_field_stitch(rogue, ally))

        self.assertEqual(rogue.resources["satchel"], rogue.max_resources["satchel"] - 1)
        self.assertEqual(ally.current_hp, 1)
        self.assertEqual(ally.death_failures, 0)
        self.assertFalse(game.has_status(ally, "bleeding"))

    def test_on_hit_hook_grants_edge_against_exposed_target(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(rogue)
        game.apply_status(target, "reeling", 1, source="test setup")

        game.trigger_on_hit_hooks(
            rogue,
            target,
            actual_damage=3,
            margin=1,
            critical_hit=False,
            heroes=[rogue],
            enemies=[target],
        )

        self.assertEqual(rogue.resources["edge"], 2)

    def test_stance_upgrade_and_reaction_hooks_are_data_driven(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(warrior)
        warrior.bond_flags["stance_upgrades"] = {
            "guard": {
                "statuses": {"guarded": 1},
                "resources": {"grit": 1},
            }
        }

        game.set_combat_stance(warrior, "guard", announce=False)

        self.assertTrue(game.has_status(warrior, "guarded"))
        self.assertEqual(warrior.resources["grit"], 2)
        self.assertTrue(game.can_use_class_reaction(warrior))
        self.assertTrue(game.spend_class_reaction(warrior, source="test reaction"))
        self.assertFalse(game.can_use_class_reaction(warrior))
        self.assertFalse(game.spend_class_reaction(warrior, source="test reaction"))
        game._active_round_number = 2
        self.assertTrue(game.can_use_class_reaction(warrior))

    def test_class_combat_cleanup_clears_temporary_resources_marks_and_reactions(self) -> None:
        game, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        target = create_enemy("bandit")
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(rogue)
        game.mark_class_target(rogue, target)
        game.add_rogue_poison_stack(rogue, target)
        game.grant_class_resource(rogue, "toxin", source="test")
        game.spend_class_reaction(rogue, source="test")

        game.clear_after_encounter([rogue, target])

        self.assertEqual(rogue.resources["edge"], 0)
        self.assertEqual(rogue.resources["toxin"], 0)
        self.assertEqual(rogue.resources["satchel"], rogue.max_resources["satchel"])
        self.assertNotIn("class_reaction_used_round", rogue.bond_flags)
        self.assertFalse(any(key.startswith("rogue_mark") for key in target.bond_flags))
        self.assertFalse(any(key.startswith("rogue_poison") for key in target.bond_flags))

    def test_percentage_defense_reduces_physical_damage_after_resistance(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        Warrior.gear_bonuses["resist_slashing"] = 1

        actual = game.apply_damage(Warrior, 10, damage_type="slashing", apply_defense=True)

        result = game.last_damage_resolution()
        self.assertEqual(result.resisted_damage, 5)
        self.assertEqual(result.defense_percent, 40)
        self.assertEqual(actual, 3)
        self.assertTrue(result.wound)

    def test_armor_break_lowers_defense_by_percentage_points(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        actual = game.apply_damage(Warrior, 10, damage_type="slashing", apply_defense=True, armor_break_percent=10)

        result = game.last_damage_resolution()
        self.assertEqual(result.armor_break_percent, 10)
        self.assertEqual(result.defense_percent, 30)
        self.assertEqual(actual, 7)

    def test_glance_and_wound_are_recorded_after_defense_and_temp_hp(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        glancing = game.apply_damage(Warrior, 1, damage_type="slashing", apply_defense=True)
        glancing_result = game.last_damage_resolution()
        self.assertEqual(glancing, 0)
        self.assertTrue(glancing_result.glance)
        self.assertFalse(glancing_result.wound)

        Warrior.temp_hp = 10
        absorbed = game.apply_damage(Warrior, 10, damage_type="slashing", apply_defense=True)
        absorbed_result = game.last_damage_resolution()
        self.assertEqual(absorbed, 0)
        self.assertEqual(absorbed_result.temp_hp_absorbed, 6)
        self.assertFalse(absorbed_result.glance)
        self.assertFalse(absorbed_result.wound)

    def test_glance_does_not_create_karmic_chipped_armor(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        attacker = create_enemy("bandit")
        game._in_combat = True
        game.karmic_dice_enabled = True

        game.apply_damage(Warrior, 1, damage_type="slashing", source_actor=attacker, apply_defense=True)
        self.assertTrue(game.last_damage_was_glance())
        self.assertNotIn("chipped_armor", Warrior.conditions)
        self.assertEqual(game.total_armor_break_percent(Warrior), 0)

    def test_temp_hp_blocked_physical_hit_does_not_chip_armor(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        attacker = create_enemy("bandit")
        Warrior.temp_hp = 10
        game._in_combat = True
        game.karmic_dice_enabled = True

        actual = game.apply_damage(Warrior, 10, damage_type="slashing", source_actor=attacker, apply_defense=True)

        self.assertEqual(actual, 0)
        self.assertFalse(game.last_damage_was_glance())
        self.assertFalse(game.has_status(Warrior, "chipped_armor"))

    def test_non_physical_spell_damage_bypasses_defense(self) -> None:
        game, Warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        actual = game.apply_damage(Warrior, 10, damage_type="fire", apply_defense=True)

        result = game.last_damage_resolution()
        self.assertEqual(result.defense_percent, 0)
        self.assertEqual(actual, 10)

    def test_warrior_class_gets_base_grit_and_combat_actions(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        encounter = Encounter("Sparring", "A quick pressure test.", [enemy])

        game.prepare_warrior_grit_for_combat(warrior)

        self.assertEqual(warrior.resources["grit"], 1)
        self.assertEqual(warrior.max_resources["grit"], 6)
        options = game.get_player_combat_options(warrior, encounter, heroes=[warrior])
        self.assertIn("Take Guard Stance", options)
        self.assertIn("Shove", options)
        self.assertIn("Pin", options)
        self.assertIn("Warrior Rally", options)
        self.assertIn("Weapon Read", options)

    def test_warrior_guard_stance_uses_buffed_defense_avoidance_and_stability(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )

        self.assertEqual(game.effective_defense_percent(warrior, damage_type="slashing"), 40)
        self.assertEqual(game.effective_avoidance(warrior), 0)
        self.assertEqual(game.effective_stability(warrior), 3)

        game.use_guard_stance(warrior)

        self.assertEqual(game.effective_defense_percent(warrior, damage_type="slashing"), 60)
        self.assertEqual(game.effective_avoidance(warrior), 0)
        self.assertEqual(game.effective_stability(warrior), 5)
        self.assertEqual(game.status_value(warrior, "attack_penalty"), 2)

    def test_warrior_gains_grit_from_wounds_and_glances_during_combat(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game.prepare_warrior_grit_for_combat(warrior)

        game.apply_damage(warrior, 10, damage_type="slashing", apply_defense=True)
        self.assertEqual(warrior.resources["grit"], 1)

        game._in_combat = True
        game.apply_damage(warrior, 10, damage_type="slashing", apply_defense=True)
        self.assertEqual(warrior.resources["grit"], 2)

        game.apply_damage(warrior, 1, damage_type="slashing", apply_defense=True)
        self.assertTrue(game.last_damage_was_glance())
        self.assertEqual(warrior.resources["grit"], 3)

    def test_warrior_shove_targets_stability_and_grants_grit_on_strong_shove(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        game.prepare_warrior_grit_for_combat(warrior)
        game._in_combat = True
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]

        game.use_warrior_shove(warrior, enemy)

        self.assertTrue(game.has_status(enemy, "prone"))
        self.assertTrue(game.has_status(enemy, "reeling"))
        self.assertEqual(warrior.resources["grit"], 2)

    def test_warrior_rally_spends_grit_to_clear_reeling_or_guard_an_ally(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)

        game.apply_status(ally, "reeling", 1, source="test setup")
        self.assertTrue(game.use_warrior_rally(warrior, ally))

        self.assertFalse(game.has_status(ally, "reeling"))
        self.assertEqual(warrior.resources["grit"], 0)

        game.grant_warrior_grit(warrior, source="test refill")
        self.assertTrue(game.use_warrior_rally(warrior, ally))

        self.assertTrue(game.has_status(ally, "guarded"))
        self.assertEqual(warrior.resources["grit"], 0)

    def test_warrior_pin_damages_reels_and_fixates_on_strong_hit(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        enemy = create_enemy("bandit")
        game._in_combat = True
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_warrior_pin(warrior, enemy, [warrior], [enemy], set()))

        self.assertTrue(game.has_status(enemy, "reeling"))
        self.assertTrue(game.target_is_fixated_by(warrior, enemy))
        self.assertGreater(game.last_damage_resolution().hp_damage, 0)

    def test_juggernaut_momentum_builds_from_defense_and_glances(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.append("juggernaut_momentum")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)

        game.apply_damage(warrior, 10, damage_type="slashing", apply_defense=True)

        self.assertEqual(game.last_damage_resolution().defense_percent, 40)
        self.assertEqual(warrior.resources["momentum"], 1)
        self.assertEqual(warrior.resources["grit"], 2)

        game.apply_damage(warrior, 1, damage_type="slashing", apply_defense=True)

        self.assertTrue(game.last_damage_was_glance())
        self.assertEqual(warrior.resources["momentum"], 2)
        self.assertEqual(warrior.resources["grit"], 3)

    def test_iron_draw_fixates_enemy_and_penalizes_other_targets(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        enemy = create_enemy("bandit")

        game.set_combat_stance(warrior, "guard", announce=False)
        game.use_iron_draw(warrior, enemy)

        self.assertTrue(game.target_is_fixated_by(warrior, enemy))
        self.assertEqual(enemy.conditions["fixated"], 2)
        self.assertIs(game.fixated_priority_target(enemy, [rogue, warrior]), warrior)
        self.assertEqual(game.attack_focus_modifier(enemy, rogue), -2)
        self.assertEqual(game.attack_focus_modifier(enemy, warrior), 0)

    def test_shoulder_in_spends_grit_and_spikes_guard_defense(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["juggernaut_momentum", "shoulder_in"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)

        self.assertTrue(game.use_shoulder_in(warrior))

        self.assertEqual(game.current_combat_stance_key(warrior), "guard")
        self.assertTrue(game.has_status(warrior, "shoulder_in"))
        self.assertEqual(game.effective_defense_percent(warrior, damage_type="slashing"), 65)
        self.assertEqual(warrior.resources["grit"], 0)

        game.grant_warrior_grit(warrior, source="test refill")
        self.assertTrue(game.use_shoulder_in(warrior))

        self.assertEqual(warrior.resources["momentum"], 1)

    def test_weapon_master_training_adds_combo_and_combat_options(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend([
            "weapon_master_combo",
            "style_wheel",
            "measure_twice",
            "clean_line",
            "dent_the_shell",
            "hook_the_guard",
        ])
        enemy = create_enemy("bandit")
        encounter = Encounter("Sparring", "A quick pressure test.", [enemy])
        game._in_combat = True

        game.prepare_class_resources_for_combat(warrior)
        options = game.get_player_combat_options(warrior, encounter, heroes=[warrior])

        self.assertEqual(warrior.max_resources["combo"], 5)
        self.assertEqual(warrior.resources["combo"], 0)
        self.assertIn("Clean Line", options)
        self.assertIn("Dent The Shell", options)
        self.assertIn("Hook The Guard", options)
        self.assertIn("Measure Twice", options)
        self.assertIn("Style Wheel", options)

    def test_measure_twice_reads_weakness_and_grants_combo(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["weapon_master_combo", "measure_twice"])
        enemy = create_enemy("animated_armor")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)

        self.assertTrue(game.use_measure_twice(warrior, enemy))

        self.assertEqual(warrior.resources["combo"], 1)
        self.assertEqual(enemy.bond_flags["weapon_master_measured_by_id"], id(warrior))

    def test_style_wheel_free_swap_then_costs_combo(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["weapon_master_combo", "style_wheel"])
        game._in_combat = True
        game._active_round_number = 1
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["combo"] = 1

        self.assertEqual(game.weapon_master_style_key(warrior), "cleave")
        self.assertEqual(game.use_weapon_master_style(warrior, "pierce"), "free")
        self.assertEqual(warrior.resources["combo"], 1)
        self.assertEqual(game.weapon_master_style_key(warrior), "pierce")

        self.assertEqual(game.use_weapon_master_style(warrior, "crush"), "combo")

        self.assertEqual(warrior.resources["combo"], 0)
        self.assertEqual(game.weapon_master_style_key(warrior), "crush")

    def test_dent_the_shell_breaks_armor_for_current_and_followup_hits(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["weapon_master_combo", "style_wheel", "dent_the_shell"])
        enemy = create_enemy("animated_armor")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 8, [8], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_dent_the_shell(warrior, enemy, [warrior], [enemy], set()))

        result = game.last_damage_resolution()
        self.assertEqual(result.armor_break_percent, 10)
        self.assertEqual(result.defense_percent, 35)
        self.assertTrue(game.has_status(enemy, "armor_broken"))
        self.assertGreater(warrior.resources["combo"], 0)

        game.apply_damage(enemy, 10, damage_type="slashing", source_actor=warrior, apply_defense=True)

        followup = game.last_damage_resolution()
        self.assertEqual(followup.armor_break_percent, 10)
        self.assertEqual(followup.defense_percent, 35)

    def test_hook_the_guard_clears_guard_layers_and_reels_on_strong_hit(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["weapon_master_combo", "style_wheel", "hook_the_guard"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        game.set_combat_stance(enemy, "guard", announce=False)
        game.apply_status(enemy, "guarded", 1, source="test guard")
        game.apply_status(enemy, "raised_shield", 1, source="test shield")
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 1, [1], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_hook_the_guard(warrior, enemy, [warrior], [enemy], set()))

        self.assertEqual(game.current_combat_stance_key(enemy), "neutral")
        self.assertFalse(game.has_status(enemy, "guarded"))
        self.assertFalse(game.has_status(enemy, "raised_shield"))
        self.assertTrue(game.has_status(enemy, "reeling"))

    def test_weapon_master_pierce_style_adds_accuracy_to_simulator(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["weapon_master_combo", "style_wheel"])
        enemy = create_enemy("bandit")

        cleave = simulate_weapon_attack(game, warrior, enemy)
        game.set_weapon_master_style(warrior, "pierce", announce=False)
        pierce = simulate_weapon_attack(game, warrior, enemy)

        self.assertEqual(pierce.accuracy_bonus, cleave.accuracy_bonus + 1)

    def test_berserker_training_adds_fury_and_combat_options(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["berserker_fury", "redline", "reckless_cut", "teeth_set", "drink_the_hurt"])
        enemy = create_enemy("bandit")
        encounter = Encounter("Sparring", "A quick pressure test.", [enemy])
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["fury"] = 2

        options = game.get_player_combat_options(warrior, encounter, heroes=[warrior])

        self.assertEqual(warrior.max_resources["fury"], 6)
        self.assertIn("Reckless Cut", options)
        self.assertIn("Redline", options)
        self.assertIn("Teeth Set", options)
        self.assertIn("Drink The Hurt", options)

    def test_berserker_fury_builds_from_wounds_aggressive_hits_and_kills(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.append("berserker_fury")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)

        game.apply_damage(warrior, 10, damage_type="slashing", apply_defense=True)

        self.assertEqual(warrior.resources["fury"], 1)

        enemy = create_enemy("animated_armor")
        game.set_combat_stance(warrior, "aggressive", announce=False)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 1, [1], 0)  # type: ignore[method-assign]

        game.perform_weapon_attack(warrior, enemy, [warrior], [enemy], set())

        self.assertGreaterEqual(warrior.resources["fury"], 2)

        enemy.current_hp = 1
        game.perform_weapon_attack(warrior, enemy, [warrior], [enemy], set())

        self.assertGreaterEqual(warrior.resources["fury"], 3)

    def test_redline_spends_fury_for_burst_and_lowers_defenses(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["berserker_fury", "redline"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["fury"] = 3

        self.assertTrue(game.use_redline(warrior))

        self.assertEqual(warrior.resources["fury"], 0)
        self.assertTrue(game.has_status(warrior, "redline"))
        self.assertEqual(game.status_accuracy_modifier(warrior), 2)
        self.assertEqual(game.status_damage_modifier(warrior), 3)
        self.assertEqual(game.effective_defense_percent(warrior, damage_type="slashing"), 35)
        self.assertEqual(game.effective_avoidance(warrior), -1)

    def test_reckless_cut_adds_accuracy_and_invites_counterpressure(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["berserker_fury", "reckless_cut"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        before = simulate_weapon_attack(game, enemy, warrior, heroes=[enemy], enemies=[warrior])
        self.assertTrue(game.use_reckless_cut(warrior, enemy, [warrior], [enemy], set()))
        after = simulate_weapon_attack(game, enemy, warrior, heroes=[enemy], enemies=[warrior])

        self.assertTrue(game.has_status(warrior, "reckless_opening"))
        self.assertEqual(game.target_accuracy_modifier(warrior), 1)
        self.assertEqual(after.accuracy_bonus, before.accuracy_bonus + 1)

    def test_teeth_set_spends_fury_and_grants_temp_hp(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["berserker_fury", "teeth_set"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["fury"] = 1

        self.assertTrue(game.use_teeth_set(warrior))

        self.assertEqual(warrior.resources["fury"], 0)
        self.assertEqual(warrior.temp_hp, warrior.proficiency_bonus + warrior.ability_mod("CON"))

    def test_drink_the_hurt_spends_fury_and_heals_after_wounding(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["berserker_fury", "drink_the_hurt"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["fury"] = 2
        warrior.current_hp = 6
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_drink_the_hurt(warrior))
        game.perform_weapon_attack(warrior, enemy, [warrior], [enemy], set())

        self.assertEqual(warrior.resources["fury"], 0)
        self.assertFalse(game.has_status(warrior, "drink_the_hurt"))
        self.assertGreater(warrior.current_hp, 6)

    def test_bloodreaver_training_adds_blood_debt_and_combat_options(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["bloodreaver_blood_debt", "red_mark", "blood_price", "war_salve_strike", "open_the_ledger"])
        enemy = create_enemy("bandit")
        encounter = Encounter("Sparring", "A quick pressure test.", [enemy])
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["blood_debt"] = 1

        options = game.get_player_combat_options(warrior, encounter, heroes=[warrior])

        self.assertEqual(warrior.max_resources["blood_debt"], 5)
        self.assertIn("Red Mark", options)
        self.assertIn("Blood Price", options)
        self.assertIn("War-Salve Strike", options)
        self.assertIn("Open The Ledger", options)

    def test_red_mark_heals_first_wound_each_round_and_grants_blood_debt(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, rogue = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        warrior.features.extend(["bloodreaver_blood_debt", "red_mark"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game._active_round_number = 1
        game._active_combat_heroes = [warrior, rogue]
        game.prepare_class_resources_for_combat(warrior)
        rogue.current_hp = 5

        self.assertTrue(game.use_red_mark(warrior, enemy))
        game.apply_damage(enemy, 6, damage_type="slashing", source_actor=rogue, apply_defense=True)

        self.assertEqual(rogue.current_hp, 8)
        self.assertEqual(warrior.resources["blood_debt"], 1)

        game.apply_damage(enemy, 6, damage_type="slashing", source_actor=rogue, apply_defense=True)

        self.assertEqual(rogue.current_hp, 8)
        self.assertEqual(warrior.resources["blood_debt"], 1)

        game._active_round_number = 2
        game.apply_damage(enemy, 6, damage_type="slashing", source_actor=rogue, apply_defense=True)

        self.assertEqual(rogue.current_hp, 11)
        self.assertEqual(warrior.resources["blood_debt"], 2)

    def test_blood_debt_builds_from_own_wounds_ally_wounds_and_marked_wounds(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        warrior.features.extend(["bloodreaver_blood_debt", "red_mark"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game._active_combat_heroes = [warrior, ally]
        game.prepare_class_resources_for_combat(warrior)

        game.apply_damage(warrior, 10, damage_type="slashing", apply_defense=True)
        self.assertEqual(warrior.resources["blood_debt"], 1)

        game.apply_damage(ally, 5, damage_type="slashing", apply_defense=True)
        self.assertEqual(warrior.resources["blood_debt"], 2)

        game.use_red_mark(warrior, enemy)
        game.apply_damage(enemy, 6, damage_type="slashing", source_actor=warrior, apply_defense=True)

        self.assertGreaterEqual(warrior.resources["blood_debt"], 3)

    def test_blood_price_spends_debt_heals_ally_and_reels_bloodreaver(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        warrior.features.extend(["bloodreaver_blood_debt", "blood_price"])
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        warrior.resources["blood_debt"] = 1
        ally.current_hp = 4
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_blood_price(warrior, ally))

        self.assertEqual(warrior.resources["blood_debt"], 0)
        self.assertEqual(ally.current_hp, 10)
        self.assertTrue(game.has_status(warrior, "reeling"))

    def test_war_salve_strike_heals_lowest_ally_on_wound(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        _, ally = build_game_with_player(
            "Rogue",
            {"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        )
        warrior.features.extend(["bloodreaver_blood_debt", "war_salve_strike"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        ally.current_hp = 4
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=20, rolls=[20], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_war_salve_strike(warrior, enemy, [warrior, ally], [enemy], set()))

        self.assertEqual(ally.current_hp, 5)
        self.assertGreater(game.last_damage_resolution().hp_damage, 0)

    def test_open_the_ledger_costs_grit_and_applies_bleeding_to_red_mark(self) -> None:
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        warrior.features.extend(["bloodreaver_blood_debt", "red_mark", "open_the_ledger"])
        enemy = create_enemy("bandit")
        game._in_combat = True
        game.prepare_class_resources_for_combat(warrior)
        game.use_red_mark(warrior, enemy)
        game.roll_check_d20 = lambda *args, **kwargs: D20Outcome(kept=6, rolls=[6], rerolls=[], advantage_state=0)  # type: ignore[method-assign]
        game.roll_with_display_bonus = lambda expression, *args, **kwargs: RollOutcome(expression, 4, [4], 0)  # type: ignore[method-assign]

        self.assertTrue(game.use_open_the_ledger(warrior, enemy, [warrior], [enemy], set()))

        self.assertEqual(warrior.resources["grit"], 0)
        self.assertTrue(game.has_status(enemy, "bleeding"))
        self.assertGreaterEqual(warrior.resources["blood_debt"], 1)

    def test_weapon_read_reports_defense_avoidance_and_stability(self) -> None:
        log: list[str] = []
        game, warrior = build_game_with_player(
            "Warrior",
            {"STR": 15, "DEX": 12, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
        )
        game.output_fn = log.append
        enemy = create_enemy("animated_armor")

        game.use_weapon_read(warrior, enemy)

        rendered = "\n".join(log)
        self.assertIn("Weapon Read:", rendered)
        self.assertIn("Defense", rendered)
        self.assertIn("Avoidance", rendered)
        self.assertIn("Stability", rendered)
        self.assertIn("Best answer:", rendered)


if __name__ == "__main__":
    unittest.main()
