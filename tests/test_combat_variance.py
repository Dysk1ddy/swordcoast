from __future__ import annotations

import random
import unittest

from dnd_game.content import create_enemy
from dnd_game.gameplay.combat_variance import (
    ActionSample,
    build_default_variance_report,
    build_level_four_mixed_party,
    simulate_weapon_action_once,
    summarize_action_samples,
)


class ScriptedRandom(random.Random):
    def __init__(self, rolls: list[int]) -> None:
        super().__init__(0)
        self.rolls = list(rolls)

    def randint(self, a: int, b: int) -> int:
        if not self.rolls:
            return super().randint(a, b)
        value = self.rolls.pop(0)
        if not a <= value <= b:
            raise AssertionError(f"Scripted randint value {value} outside {a}..{b}")
        return value


class CombatVarianceReportTests(unittest.TestCase):
    def test_action_summary_tracks_zero_results_percentiles_and_crit_share(self) -> None:
        profile = summarize_action_samples(
            "sample action",
            (
                ActionSample(0, result_kind="miss"),
                ActionSample(0, result_kind="pressure"),
                ActionSample(5, result_kind="wound"),
                ActionSample(10, critical=True, result_kind="wound"),
            ),
        )

        self.assertEqual(profile.sample_count, 4)
        self.assertAlmostEqual(profile.zero_result_chance, 0.25)
        self.assertEqual(profile.p10_damage, 0)
        self.assertEqual(profile.p50_damage, 5)
        self.assertEqual(profile.p90_damage, 10)
        self.assertAlmostEqual(profile.critical_chance, 0.25)
        self.assertAlmostEqual(profile.critical_damage_share, 10 / 15)
        self.assertGreater(profile.coefficient_of_variation, 0)

    def test_default_variance_report_uses_fixed_seed_count_for_encounters(self) -> None:
        seeds = tuple(range(1001, 1006))

        report = build_default_variance_report(seeds)

        self.assertGreaterEqual(len(report.action_profiles), 4)
        self.assertGreaterEqual(len(report.encounter_profiles), 3)
        self.assertTrue(all(profile.sample_count >= len(seeds) for profile in report.action_profiles))
        self.assertTrue(all(profile.seed_count == len(seeds) for profile in report.encounter_profiles))
        for profile in report.encounter_profiles:
            self.assertGreaterEqual(profile.rounds_p10, 1)
            self.assertLessEqual(profile.rounds_p10, profile.rounds_p50)
            self.assertLessEqual(profile.rounds_p50, profile.rounds_p90)
            self.assertGreaterEqual(profile.downed_allies_mean, 0)
            self.assertGreaterEqual(profile.downed_allies_p90, 0)

    def test_weapon_action_harness_counts_near_miss_pressure_as_nonblank(self) -> None:
        game, party = build_level_four_mixed_party()
        warrior = party[0]
        target = create_enemy("false_map_skirmisher")

        sample = simulate_weapon_action_once(game, warrior, target, ScriptedRandom([3]))

        self.assertEqual(sample.result_kind, "pressure")
        self.assertFalse(sample.zero_result)
        self.assertEqual(sample.damage, 0)


if __name__ == "__main__":
    unittest.main()
