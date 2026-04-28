from __future__ import annotations

import unittest

from dnd_game.gameplay.act1_route_fixtures import (
    CANONICAL_ACT1_ROUTE_KEY,
    act1_route_fixture,
    build_act1_route_game,
)
from dnd_game.gameplay.combat_simulator import simulate_route_chain


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
                game, party = build_act1_route_game(segment, route)
                chain = simulate_route_chain(
                    game,
                    segment.title,
                    party,
                    segment.build_route_specs(),
                    party_damage_multiplier=0.0,
                    spend_party_resources=False,
                )

                self.assertEqual(len(chain.steps), len(segment.encounters))
                self.assertEqual(chain.final_snapshot["short_rests_remaining"], 2)
                self.assertGreater(chain.final_snapshot["party_hp"], 0)
                self.assertTrue(all(step.encounter.enemy_names for step in chain.steps))


if __name__ == "__main__":
    unittest.main()
