from __future__ import annotations


RACES = {
    "Human": {
        "description": "Humans are adaptable survivors found across Aethrune's roads, ports, farms, and rebuilt towns.",
        "bonuses": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "features": [],
        "skills": [],
    },
    "Dwarf": {
        "description": "Dwarves are hardy folk shaped by stone halls, clan honor, and stubborn resolve.",
        "bonuses": {"CON": 2},
        "features": ["darkvision", "dwarven_resilience"],
        "skills": [],
    },
    "Elf": {
        "description": "Elves are graceful wanderers whose keen senses and long memories suit subtle work.",
        "bonuses": {"DEX": 2},
        "features": ["darkvision", "keen_senses", "fey_ancestry"],
        "skills": ["Perception"],
    },
    "Halfling": {
        "description": "Halflings survive by quick feet, luck, and refusing to stay intimidated for long.",
        "bonuses": {"DEX": 2},
        "features": ["lucky", "brave"],
        "skills": [],
    },
    "Dragonborn": {
        "description": "Dragonborn carry proud draconic bloodlines and often meet danger head-on.",
        "bonuses": {"STR": 2, "CHA": 1},
        "features": ["draconic_presence"],
        "skills": [],
    },
    "Gnome": {
        "description": "Gnomes are clever tinkerers and illusion-prone scholars with restless, curious minds.",
        "bonuses": {"INT": 2},
        "features": ["gnome_cunning"],
        "skills": ["Investigation"],
    },
    "Half-Elf": {
        "description": "Half-elves bridge worlds with adaptable talent, charm, and sharp instincts.",
        "bonuses": {"CHA": 2, "DEX": 1, "WIS": 1},
        "features": ["fey_ancestry"],
        "skills": ["Insight", "Persuasion"],
    },
    "Half-Orc": {
        "description": "Half-orcs are relentless survivors who rely on power, grit, and fierce presence.",
        "bonuses": {"STR": 2, "CON": 1},
        "features": ["relentless_endurance", "menacing"],
        "skills": ["Intimidation"],
    },
    "Tiefling": {
        "description": "Tieflings carry infernal marks openly or not, and learn early how to turn suspicion into poise.",
        "bonuses": {"INT": 1, "CHA": 2},
        "features": ["darkvision", "hellish_resistance"],
        "skills": [],
    },
    "Goliath": {
        "description": "Goliaths are mountain-bred competitors who meet hardship with endurance and pride.",
        "bonuses": {"STR": 2, "CON": 1},
        "features": ["stone_endurance"],
        "skills": ["Athletics"],
    },
    "Orc": {
        "description": "Orcs bring forceful presence, darkvision, and a refusal to stop when momentum matters most.",
        "bonuses": {"STR": 2, "CON": 1},
        "features": ["darkvision", "adrenaline_rush"],
        "skills": ["Intimidation"],
    },
}


def format_racial_bonuses(race: str) -> str:
    bonuses = RACES[race]["bonuses"]
    return ", ".join(f"{ability} +{value}" for ability, value in bonuses.items())


def format_race_selection(race: str) -> str:
    return f"{race}: {format_racial_bonuses(race)}. {RACES[race]['description']}"
