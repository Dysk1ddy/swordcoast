from __future__ import annotations

import unittest

from dnd_game.gameplay.act1_route_fixtures import (
    ACT1_ATTRITION_DAMAGE_MULTIPLIER,
    CANONICAL_ACT1_ROUTE_KEY,
    act1_route_fixture,
    act1_route_attrition_report,
    format_act1_route_attrition_report,
    simulate_act1_route_segment,
)


class Act1RouteFixtureTests(unittest.TestCase):
    def test_canonical_act1_route_tracks_recruitment_shape(self) -> None:
        route = act1_route_fixture()

        self.assertEqual(route.key, CANONICAL_ACT1_ROUTE_KEY)
        self.assertEqual(route.encounter_count, 25)
        self.assertEqual(route.segments[0].party_member_ids, ("player",))
        self.assertEqual(route.segments[1].joins_before, ("elira_dawnmantle",))
        self.assertEqual(route.segments[2].joins_before, ("kaelis_starling",))
        self.assertEqual(route.segments[4].joins_after, ("tolan_ironshield",))
        self.assertEqual(route.segments[5].joins_before, ("tolan_ironshield",))
        self.assertEqual(route.segments[6].joins_before, ("bryn_underbough",))
        self.assertEqual(route.segments[-1].party_level, 5)
        self.assertEqual(route.segments[-1].expected_party_size, 5)

    def test_canonical_act1_route_marks_back_to_back_emberway_waves(self) -> None:
        route = act1_route_fixture()
        first_wave = route.segments[4].build_route_specs()[0]
        second_wave = route.segments[5].build_route_specs()[0]

        self.assertEqual(first_wave.wave_group, "emberway_ambush")
        self.assertEqual(second_wave.wave_group, "emberway_ambush")
        self.assertIsNot(first_wave.enemies[0], route.segments[4].build_route_specs()[0].enemies[0])

    def test_canonical_act1_route_segments_build_valid_encounter_specs(self) -> None:
        route = act1_route_fixture()

        for segment in route.segments:
            with self.subTest(segment=segment.key):
                specs = segment.build_route_specs()

                self.assertEqual(len(specs), len(segment.encounters))
                self.assertTrue(all(spec.enemies for spec in specs))
                self.assertTrue(all(enemy.is_conscious() for spec in specs for enemy in spec.enemies))

    def test_canonical_act1_route_segments_smoke_through_simulator(self) -> None:
        route = act1_route_fixture()

        for segment in route.segments:
            with self.subTest(segment=segment.key):
                chain = simulate_act1_route_segment(
                    segment,
                    route,
                    party_damage_multiplier=0.0,
                    spend_party_resources=False,
                )

                self.assertEqual(len(chain.steps), len(segment.encounters))
                self.assertEqual(chain.final_snapshot["short_rests_remaining"], 2)
                self.assertGreater(chain.final_snapshot["party_hp"], 0)
                self.assertTrue(all(step.encounter.enemy_names for step in chain.steps))

    def test_canonical_act1_route_attrition_report_applies_expected_damage(self) -> None:
        route = act1_route_fixture()

        reports = act1_route_attrition_report(route)
        total_damage = sum(report.total_expected_party_damage_applied for report in reports)
        total_short_rests = sum(report.short_rest_count for report in reports)
        total_long_rests = sum(report.long_rest_count for report in reports)
        total_blocked_rests = sum(report.blocked_rest_count for report in reports)
        lowest_survival_margin = min(report.minimum_survival_margin_rounds for report in reports)
        lowest_final_hp_percent = min(report.final_party_hp_percent for report in reports)

        self.assertEqual(ACT1_ATTRITION_DAMAGE_MULTIPLIER, 1.0)
        self.assertEqual(len(reports), len(route.segments))
        self.assertEqual(sum(report.encounter_count for report in reports), route.encounter_count)
        self.assertGreaterEqual(total_damage, 560)
        self.assertLessEqual(total_damage, 680)
        self.assertGreaterEqual(total_short_rests, 4)
        self.assertLessEqual(total_short_rests, 7)
        self.assertEqual(total_long_rests, 0)
        self.assertEqual(total_blocked_rests, 0)
        self.assertGreater(lowest_survival_margin, 0.05)
        self.assertGreater(lowest_final_hp_percent, 0.45)
        self.assertTrue(all(report.final_party_hp > 0 for report in reports))

        pressure_segments = {
            report.segment_key
            for report in reports
            if report.minimum_survival_margin_rounds < 3.0
        }
        self.assertIn("blackwake_crossing", pressure_segments)
        self.assertIn("red_mesa_hold", pressure_segments)
        self.assertIn("emberhall_cellars", pressure_segments)

    def test_canonical_act1_route_attrition_report_formats_summary_rows(self) -> None:
        reports = act1_route_attrition_report()

        rendered = format_act1_route_attrition_report(reports[:2])

        self.assertIn("Segment | Lv | Party | Fights | Damage", rendered)
        self.assertIn("opening_soldier_solo", rendered)
        self.assertIn("greywake_elira_breakout", rendered)


if __name__ == "__main__":
    unittest.main()
