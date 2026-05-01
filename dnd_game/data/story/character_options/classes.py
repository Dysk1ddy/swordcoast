from __future__ import annotations

from ....models import Armor, Weapon
from ..public_terms import class_option_label, rules_text


CLASSES = {
    "Warrior": {
        "description": "Warriors hold ground with reach, leverage, practiced shell, and the nerve to make enemies spend force where it helps the party.",
        "hit_die": 10,
        "saving_throws": ["STR", "CON"],
        "skill_choices": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"],
        "skill_picks": 2,
        "weapon": Weapon(name="Longsword", damage="1d8", ability="STR", properties=["versatile"]),
        "armor": Armor(name="Chain Mail", base_ac=16, dex_cap=0, heavy=True),
        "shield": True,
        "features": [
            "warrior_grit",
            "warrior_guard",
            "warrior_shove",
            "warrior_pin",
            "warrior_rally",
            "weapon_read",
        ],
        "resources": {"grit": 1},
        "spellcasting_ability": None,
    },
    "Mage": {
        "description": "Mages shape charge through fields, wards, signals, and pressure before a wound has time to land.",
        "hit_die": 6,
        "saving_throws": ["INT", "WIS"],
        "skill_choices": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Nature", "Perception", "Religion"],
        "skill_picks": 3,
        "weapon": Weapon(name="Quarterstaff", damage="1d6", ability="STR"),
        "armor": Armor(name="Warded Coat", base_ac=11, armor_type="light", defense_percent=10, defense_cap_percent=45, defense_points=11, defense_cap_points=22),
        "shield": False,
        "features": ["mage_charge", "mage_focus", "arcane_bolt", "minor_channel", "pattern_read", "ground", "focused_eye"],
        "resources": {},
        "spellcasting_ability": "INT",
    },
    "Rogue": {
        "description": "Rogues win with precision, timing, misdirection, and nerve.",
        "hit_die": 8,
        "saving_throws": ["DEX", "INT"],
        "skill_choices": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"],
        "skill_picks": 4,
        "weapon": Weapon(name="Rapier", damage="1d8", ability="FINESSE", finesse=True),
        "armor": Armor(name="Leather Armor", base_ac=11),
        "shield": False,
        "features": ["sneak_attack", "expertise", "rogue_edge", "rogue_mark", "rogue_satchel", "rogue_poison"],
        "resources": {},
        "spellcasting_ability": None,
    },
}

CLASS_LEVEL_PROGRESSION = {
    "Warrior": {
        2: {
            "features": [("Hard Lesson", "The first wound or glancing hit of a fight teaches fast. Your Grit maximum follows Endurance and training.")],
            "feature_ids": ["hard_lesson"],
        },
        3: {
            "features": [
                ("Juggernaut Training", "Gain Momentum, Iron Draw, and Shoulder In for Guard-driven pressure."),
                ("Line Holder", "Gain +1 Stability while conscious and guarding space for the party."),
            ],
            "feature_ids": ["juggernaut_momentum", "iron_draw", "shoulder_in", "line_holder"],
            "equipment_bonuses": {"stability": 1},
        },
        4: {
            "features": [
                ("Weapon Familiarity", "Gain +1 to weapon strike checks and weapon damage."),
                ("Style Wheel", "Gain Combo, Measure Twice, Clean Line, Dent The Shell, and Hook The Guard."),
                ("Berserker Training", "Gain Fury, Redline, Reckless Cut, Teeth Set, and Drink The Hurt."),
                ("Bloodreaver Training", "Gain Blood Debt, Red Mark, Blood Price, War-Salve Strike, and Open The Ledger."),
            ],
            "feature_ids": [
                "weapon_familiarity",
                "weapon_master_combo",
                "style_wheel",
                "measure_twice",
                "clean_line",
                "dent_the_shell",
                "hook_the_guard",
                "berserker_fury",
                "redline",
                "reckless_cut",
                "teeth_set",
                "drink_the_hurt",
                "bloodreaver_blood_debt",
                "red_mark",
                "blood_price",
                "war_salve_strike",
                "open_the_ledger",
            ],
            "equipment_bonuses": {"attack": 1, "damage": 1},
        },
    },
    "Mage": {
        2: {
            "features": [
                ("Field Sense", "Pattern Read also calls out ward pressure, Defense, and the weakest resist lane."),
                ("Steady Hands", "Gain +1 Endurance resists for channel strain."),
            ],
            "feature_ids": ["field_sense", "steady_hands"],
            "equipment_bonuses": {"CON_save": 1},
        },
        3: {
            "features": [("Counter-Cadence", "Gain +1 Wisdom resists against signal, fear, and charm pressure.")],
            "feature_ids": ["counter_cadence"],
            "equipment_bonuses": {"WIS_save": 1},
        },
        4: {
            "features": [
                ("Channel Focus", "Gain +1 channel strike checks as your patterns tighten."),
                ("Spellguard Training", "Gain Ward Shell, Anchor Shell ward-draw, Blue Glass Palm Fixated pressure, and Lockstep Field."),
                ("Arcanist Training", "Gain Arc, Pattern Charge, Arc Pulse, Marked Angle, Quiet Sum, and Detonate Pattern."),
                ("Elementalist Training", "Gain Attunement, Elemental Weave, Ember Lance, Frost Shard, Volt Grasp, Burning Line, and Lockfrost."),
                ("Aethermancer Training", "Gain Flow, Field Mend, Pulse Restore, Triage Line, Clean Breath, Steady Pulse, and Overflow Shell."),
            ],
            "feature_ids": [
                "arcane_focus",
                "spellguard_ward",
                "arcanist_arc",
                "elementalist_attunement",
                "aethermancer_flow",
                "anchor_shell",
                "ward_shell",
                "blue_glass_palm",
                "lockstep_field",
                "pattern_charge",
                "arc_pulse",
                "marked_angle",
                "quiet_sum",
                "detonate_pattern",
                "elemental_weave",
                "ember_lance",
                "frost_shard",
                "volt_grasp",
                "change_weather_hand",
                "burning_line",
                "lockfrost",
                "field_mend",
                "pulse_restore",
                "triage_line",
                "clean_breath",
                "steady_pulse",
                "overflow_shell",
            ],
            "equipment_bonuses": {"spell_attack": 1},
        },
    },
    "Rogue": {
        2: {
            "features": [
                ("Veil Step", "Gain sharper battlefield movement, adding +2 to initiative and Stealth checks."),
                ("Skirmish Kit", "Gain Tool Read, Skirmish, and Slip Away for shared Rogue tempo."),
            ],
            "feature_ids": ["cunning_action", "tool_read", "rogue_skirmish", "slip_away"],
            "equipment_bonuses": {"Stealth": 2, "initiative": 2},
        },
        3: {
            "features": [
                ("Deadly Veilstrike", "Your Veilstrike improves to 2d6 damage."),
                ("Dirty Work", "Gain Feint and Dirty Trick for shared Rogue setup."),
            ],
            "feature_ids": ["improved_sneak_attack", "rogue_feint", "dirty_trick"],
        },
        4: {
            "features": [
                ("Evasion", "Gain +2 to Agility resists."),
                ("Shadowguard Training", "Gain Shadow, False Target, Smoke Pin, and Cover The Healer."),
                ("Assassin Training", "Gain Death Mark, Quiet Knife, Between Plates, and Sudden End."),
                ("Poisoner Training", "Gain prepared Toxin, Black Drop, Green Needle, Bitter Cloud, Rot Thread, and Bloom In The Blood."),
                ("Alchemist Training", "Gain Quick Mix, Redcap Tonic, Smoke Jar, Bitter Acid, and Field Stitch."),
            ],
            "feature_ids": [
                "evasion",
                "shadowguard_shadow",
                "false_target",
                "smoke_pin",
                "cover_the_healer",
                "death_mark",
                "quiet_knife",
                "between_plates",
                "sudden_end",
                "poisoner_toxin",
                "black_drop",
                "green_needle",
                "bitter_cloud",
                "rot_thread",
                "bloom_in_the_blood",
                "alchemist_quick_mix",
                "redcap_tonic",
                "smoke_jar",
                "bitter_acid",
                "field_stitch",
            ],
            "equipment_bonuses": {"DEX_save": 2},
        },
    },
}


def format_class_selection(class_name: str) -> str:
    class_data = CLASSES[class_name]
    return f"{class_option_label(class_name)}: d{class_data['hit_die']} hit die. {rules_text(class_data['description'])}"
