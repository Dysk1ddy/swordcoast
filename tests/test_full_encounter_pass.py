from __future__ import annotations

import random
import unittest

from dnd_game.content import build_character, create_enemy
from dnd_game.game import TextDnDGame
from dnd_game.gameplay.combat_simulator import (
    EncounterPassSimulation,
    RouteChainEncounterSpec,
    simulate_encounter_pass,
    simulate_route_chain,
)
from dnd_game.models import GameState


def build_level_four_mixed_party() -> tuple[TextDnDGame, list[object]]:
    warrior = build_character(
        name="Vale",
        race="Human",
        class_name="Warrior",
        background="Soldier",
        base_ability_scores={"STR": 15, "DEX": 12, "CON": 14, "INT": 8, "WIS": 12, "CHA": 10},
        class_skill_choices=["Athletics", "Survival"],
    )
    rogue = build_character(
        name="Kael",
        race="Human",
        class_name="Rogue",
        background="Criminal",
        base_ability_scores={"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        class_skill_choices=["Stealth", "Sleight of Hand"],
    )
    mage = build_character(
        name="Mira",
        race="Human",
        class_name="Mage",
        background="Sage",
        base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        class_skill_choices=["Arcana", "Insight"],
    )
    game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(49217))
    party = [warrior, rogue, mage]
    game.state = GameState(player=warrior, companions=[rogue, mage], current_scene="encounter_pass")
    game._in_combat = True
    game._active_round_number = 1
    game._active_combat_heroes = party
    for member in party:
        for level in (2, 3, 4):
            game.level_up_character_automatically(member, level, announce=False)
        game.prepare_class_resources_for_combat(member)
    return game, party


class FullEncounterPassTests(unittest.TestCase):
    def scenario_result(self, name: str, enemies: list[object]) -> EncounterPassSimulation:
        game, party = build_level_four_mixed_party()
        game._active_combat_enemies = enemies
        return simulate_encounter_pass(game, name, party, enemies)

    def test_full_encounter_pass_covers_required_enemy_shapes(self) -> None:
        game, party = build_level_four_mixed_party()
        shieldhand = create_enemy("rukhar", name="Ashen Brand Shieldhand")
        game.apply_status(shieldhand, "raised_shield", 2, source="shield wall drill")
        scenarios = {
            "basic raiders": [create_enemy("bandit"), create_enemy("bandit_archer"), create_enemy("goblin_skirmisher")],
            "shieldhands": [shieldhand, create_enemy("ash_brand_enforcer")],
            "high-Avoidance scouts": [create_enemy("false_map_skirmisher"), create_enemy("blackglass_listener")],
            "high-Defense brutes": [create_enemy("animated_armor"), create_enemy("blacklake_pincerling")],
            "Sereth-style named enemy": [create_enemy("sereth_vane"), create_enemy("bandit"), create_enemy("bandit_archer")],
        }

        results = {
            name: simulate_encounter_pass(game, name, party, enemies)
            for name, enemies in scenarios.items()
        }

        for name, result in results.items():
            with self.subTest(name=name):
                self.assertGreaterEqual(len(result.party_actions), 3)
                self.assertTrue(any(action.action_name.endswith("Arcane Bolt") for action in result.party_actions))
                self.assertGreater(result.party_expected_damage_per_round, 8.0)
                self.assertGreater(result.enemy_expected_damage_per_round, 1.0)
                self.assertLess(result.rounds_to_clear, result.rounds_to_party_defeat)
                self.assertGreater(result.survival_margin_rounds, 1.0)

        self.assertLessEqual(results["basic raiders"].max_enemy_defense_percent, 15)
        self.assertGreaterEqual(results["shieldhands"].max_enemy_defense_percent, 40)
        self.assertGreaterEqual(results["high-Avoidance scouts"].max_enemy_avoidance, 3)
        self.assertGreaterEqual(results["high-Defense brutes"].max_enemy_defense_percent, 40)
        self.assertIn("Sereth Vane", results["Sereth-style named enemy"].enemy_names)

    def test_full_encounter_pass_boss_armor_break_weakness_moves_the_numbers(self) -> None:
        game, party = build_level_four_mixed_party()
        boss = create_enemy("pact_archive_warden", name="Ledger-Bound Bulwark")

        base = simulate_encounter_pass(game, "boss baseline", party, [boss])
        broken = simulate_encounter_pass(
            game,
            "boss Armor Break weakness",
            party,
            [boss],
            party_armor_break_percent=20,
        )

        self.assertEqual(base.max_enemy_defense_percent, 55)
        self.assertGreater(broken.party_expected_damage_per_round, base.party_expected_damage_per_round)
        self.assertLess(broken.rounds_to_clear, base.rounds_to_clear * 0.9)
        self.assertTrue(
            any(
                action.armor_break_percent >= 20 and action.defense_percent <= 35
                for action in broken.party_actions
                if action.action_name.startswith("Weapon:")
            )
        )

    def test_route_chain_harness_tracks_resources_and_short_rests_after_fights(self) -> None:
        game, party = build_level_four_mixed_party()
        game.state.gold = 11
        game.state.inventory = {"camp_stew_jar": 3, "potion_healing": 1}
        game.state.short_rests_remaining = 2
        party[0].current_hp = 1

        chain = simulate_route_chain(
            game,
            "emberway roadside",
            party,
            [RouteChainEncounterSpec("cutters at the ditch", (create_enemy("goblin_skirmisher"),))],
            party_damage_multiplier=0.0,
        )
        step = chain.steps[0]

        self.assertEqual(step.rest_decision, "short_rest")
        self.assertEqual(chain.short_rest_count, 1)
        self.assertEqual(step.resource_snapshot_before["gold"], 11)
        self.assertEqual(step.resource_snapshot_after_encounter["healing_potions"], 1)
        self.assertLess(
            step.resource_snapshot_after_encounter["magic_points"],
            step.resource_snapshot_before["magic_points"],
        )
        self.assertEqual(chain.final_snapshot["short_rests_remaining"], 1)
        self.assertEqual(chain.final_snapshot["supply_points"], 12)
        self.assertGreater(chain.final_snapshot["party_hp"], step.resource_snapshot_after_encounter["party_hp"])

    def test_route_chain_harness_defers_rest_until_wave_group_finishes(self) -> None:
        game, party = build_level_four_mixed_party()
        game.state.inventory = {"camp_stew_jar": 3}
        game.state.short_rests_remaining = 2
        party[0].current_hp = 1

        chain = simulate_route_chain(
            game,
            "reserve wave ambush",
            party,
            [
                RouteChainEncounterSpec("first rush", (create_enemy("goblin_skirmisher"),), wave_group="reserve"),
                RouteChainEncounterSpec("second rush", (create_enemy("bandit"),), wave_group="reserve"),
            ],
            party_damage_multiplier=0.0,
            spend_party_resources=False,
        )

        self.assertEqual(chain.rest_decisions, ("deferred_wave", "short_rest"))
        self.assertEqual(chain.deferred_wave_count, 1)
        self.assertEqual(chain.steps[0].wave_index, 1)
        self.assertEqual(chain.steps[1].wave_index, 2)
        self.assertEqual(chain.steps[0].resource_snapshot_after_rest["short_rests_remaining"], 2)
        self.assertEqual(chain.final_snapshot["short_rests_remaining"], 1)
        self.assertGreater(chain.final_snapshot["party_hp"], chain.steps[1].resource_snapshot_after_encounter["party_hp"])

    def test_route_chain_harness_uses_long_rest_when_short_rests_are_out(self) -> None:
        game, party = build_level_four_mixed_party()
        game.state.inventory = {"camp_stew_jar": 3}
        game.state.short_rests_remaining = 0
        party[0].current_hp = 1
        party[2].resources["mp"] = 0

        chain = simulate_route_chain(
            game,
            "spent company",
            party,
            [RouteChainEncounterSpec("last sentry pair", (create_enemy("bandit"),))],
            party_damage_multiplier=0.0,
            spend_party_resources=False,
        )

        self.assertEqual(chain.rest_decisions, ("long_rest",))
        self.assertEqual(chain.long_rest_count, 1)
        self.assertEqual(chain.final_snapshot["short_rests_remaining"], 2)
        self.assertEqual(chain.final_snapshot["supply_points"], 0)
        self.assertEqual(party[0].current_hp, party[0].max_hp)
        self.assertEqual(party[2].resources["mp"], party[2].max_resources["mp"])

    def test_route_chain_harness_reports_blocked_long_rest_when_supplies_are_short(self) -> None:
        game, party = build_level_four_mixed_party()
        game.state.inventory = {"bread_round": 1}
        game.state.short_rests_remaining = 0
        party[0].current_hp = 1

        chain = simulate_route_chain(
            game,
            "empty packs",
            party,
            [RouteChainEncounterSpec("ditch knife", (create_enemy("goblin_skirmisher"),))],
            party_damage_multiplier=0.0,
            spend_party_resources=False,
        )

        self.assertEqual(chain.rest_decisions, ("long_rest_blocked",))
        self.assertEqual(chain.blocked_rest_count, 1)
        self.assertEqual(chain.final_snapshot["short_rests_remaining"], 0)
        self.assertEqual(chain.final_snapshot["supply_points"], 1)
        self.assertEqual(party[0].current_hp, 1)


if __name__ == "__main__":
    unittest.main()
