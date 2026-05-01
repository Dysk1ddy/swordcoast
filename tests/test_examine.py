from __future__ import annotations

from types import SimpleNamespace
import unittest

from dnd_game.data.story.factories import build_character
from dnd_game.gameplay.status_effects import STATUS_DEFINITIONS
from dnd_game.ui.examine import (
    character_examine_entry,
    current_location_examine_entry,
    examine_entry_for_text,
    feature_examine_entry,
    status_examine_entry,
)


class ExamineEntryTests(unittest.TestCase):
    def test_story_skill_option_uses_skill_lore(self) -> None:
        entry = examine_entry_for_text("[ATHLETICS] *Hold the line.")

        self.assertEqual(entry.title, "Athletics")
        self.assertEqual(entry.category, "Story Skill Check")
        self.assertIn("body's answer", entry.description)
        self.assertTrue(any("Strength" in detail for detail in entry.details))

    def test_channel_option_uses_feature_description_and_cost(self) -> None:
        entry = examine_entry_for_text("Arcane Bolt (Action, 1 MP)")

        self.assertEqual(entry.title, "Arcane Bolt")
        self.assertEqual(entry.category, "Channel")
        self.assertIn("force damage", entry.description)
        self.assertIn("Cost: 1 MP", entry.details)

    def test_named_character_uses_game_intro_text(self) -> None:
        entry = examine_entry_for_text("Tessa Harrow")

        self.assertEqual(entry.title, "Tessa Harrow")
        self.assertEqual(entry.category, "Character")
        self.assertIn("Iron Hollow", entry.description)

    def test_class_selection_option_uses_class_lore_before_colon(self) -> None:
        entry = examine_entry_for_text("Warrior: d10 hit die. Hold the line.")

        self.assertEqual(entry.title, "Warrior")
        self.assertEqual(entry.category, "Class")
        self.assertTrue(any("d10" in detail for detail in entry.details))

    def test_status_entry_summarizes_status_definition(self) -> None:
        entry = status_examine_entry("Burning")

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.title, "Burning")
        self.assertIn("1d6 fire", entry.description)
        self.assertIn("ongoing", " ".join(entry.details).lower())

    def test_reeling_entry_describes_accuracy_penalty(self) -> None:
        entry = status_examine_entry("Reeling")

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.title, "Reeling")
        self.assertIn("strike accuracy", entry.description.lower())
        self.assertIn("2", entry.description)
        self.assertIn("Strike penalty: 2", entry.details)

    def test_all_status_entries_avoid_generic_condition_descriptions(self) -> None:
        generic_descriptions = {
            "A tracked combat condition. Its modifiers apply while the condition remains on the character.",
            "This condition changes combat math while it lasts.",
        }

        for status_id in STATUS_DEFINITIONS:
            with self.subTest(status_id=status_id):
                entry = status_examine_entry(status_id)

                self.assertIsNotNone(entry)
                assert entry is not None
                self.assertNotIn(entry.description, generic_descriptions)
                self.assertNotIn("tracked combat condition", entry.description.lower())
                self.assertNotIn("changes combat math", entry.description.lower())
                self.assertNotIn("handled by the combat hook", entry.description.lower())

    def test_focused_status_from_scene_hooks_has_description(self) -> None:
        entry = status_examine_entry("Focused")

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.title, "Focused")
        self.assertIn("route read", entry.description.lower())

    def test_ward_feature_describes_damage_absorption(self) -> None:
        entry = feature_examine_entry("Ward")

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.title, "Ward")
        self.assertIn("stored magical shielding", entry.description)
        self.assertIn("before temp HP or HP", entry.description)
        self.assertNotIn("runtime sheet", entry.description.lower())

    def test_own_character_entry_uses_sheet_description(self) -> None:
        actor = build_character(
            name="Velkor",
            race="Human",
            class_name="Warrior",
            background="Soldier",
            base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 12, "CHA": 10},
            class_skill_choices=["Athletics", "Survival"],
        )

        entry = character_examine_entry(actor, game=SimpleNamespace(public_character_name=lambda name: name))

        self.assertEqual(entry.title, "Velkor")
        self.assertEqual(entry.category, "Character")
        self.assertIn("level 1", entry.description)
        self.assertIn("Warriors hold ground", entry.description)
        self.assertIn("soldier training", entry.description)
        self.assertIn("Background: Soldier", entry.details)
        self.assertIn("HP: 18/18 | Defense: 17 (DR 56.7%) | Contact: 18", entry.details)
        self.assertIn("Armor: Chain Mail | Dex cap +0", entry.details)
        self.assertNotIn("combatant or party member", entry.description.lower())

    def test_game_stat_terms_have_examine_entries(self) -> None:
        game = SimpleNamespace(
            state=SimpleNamespace(xp=120, gold=9, short_rests_remaining=2),
            xp_progress_summary=lambda: "Party XP: 120 | Next level in 180 XP",
            current_supply_points=lambda: 5,
        )
        cases = {
            "Party XP: 120 | Next level in 180 XP": ("Party XP", "Progression"),
            "Loot": ("Loot", "Inventory"),
            "Gold 9": ("Gold", "Currency"),
            "Supplies 5": ("Supplies", "Inventory"),
            "Short rests 2": ("Short Rests", "Rest"),
            "HP": ("HP", "Combat Stat"),
            "Defense": ("Defense", "Combat Stat"),
            "Inventory": ("Inventory", "Command"),
            "Journal": ("Journal", "Command"),
            "Camp": ("Camp", "Command"),
        }

        for text, (title, category) in cases.items():
            with self.subTest(text=text):
                entry = examine_entry_for_text(text, game=game)

                self.assertEqual(entry.title, title)
                self.assertEqual(entry.category, category)
                self.assertNotIn("highlighted term", entry.description.lower())

        xp_entry = examine_entry_for_text("Party XP: 120 | Next level in 180 XP", game=game)
        self.assertIn("Next level in 180 XP", " ".join(xp_entry.details))

    def test_location_entry_uses_location_lore(self) -> None:
        entry = examine_entry_for_text("Glasswater Intake")

        self.assertEqual(entry.title, "Glasswater Intake")
        self.assertEqual(entry.category, "Location")
        self.assertIn("waterworks", entry.description)

    def test_current_location_entry_includes_scene_objective(self) -> None:
        game = SimpleNamespace(
            state=SimpleNamespace(current_scene="glasswater_intake"),
            SCENE_LABELS={"glasswater_intake": "Glasswater Intake"},
            SCENE_OBJECTIVES={"glasswater_intake": "Stabilize the headgate."},
        )

        entry = current_location_examine_entry(game)

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.title, "Glasswater Intake")
        self.assertIn("Stabilize the headgate.", " ".join(entry.details))


if __name__ == "__main__":
    unittest.main()
