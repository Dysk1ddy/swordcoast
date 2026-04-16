from __future__ import annotations


BACKGROUNDS = {
    "Soldier": {
        "description": "A veteran of militia drills, frontier patrols, or a mercenary banner.",
        "skills": ["Athletics", "Intimidation"],
        "proficiencies": ["Land Vehicles", "Gaming Set"],
        "equipment_bonuses": {"Athletics": 1, "Intimidation": 1},
        "notes": ["Veteran's kit: +1 to Athletics and Intimidation checks."],
    },
    "Acolyte": {
        "description": "A devotee of a temple, shrine, or wandering faith.",
        "skills": ["Insight", "Religion"],
        "proficiencies": ["Calligrapher's Supplies", "Celestial"],
        "equipment_bonuses": {"Medicine": 1, "Religion": 1},
        "notes": ["Healer's satchel: +1 to Medicine and Religion checks."],
    },
    "Criminal": {
        "description": "A burglar, smuggler, or confidence artist who knows how to vanish.",
        "skills": ["Deception", "Stealth"],
        "proficiencies": ["Thieves' Tools", "Disguise Kit"],
        "equipment_bonuses": {"Stealth": 1, "Sleight of Hand": 1},
        "notes": ["Thieves' tools: +1 to Stealth and Sleight of Hand checks."],
    },
    "Sage": {
        "description": "A scholar of histories, magic, and old tales carried across Faerun.",
        "skills": ["Arcana", "History"],
        "proficiencies": ["Calligrapher's Supplies", "Draconic"],
        "equipment_bonuses": {"Arcana": 1, "History": 1},
        "notes": ["Field journal: +1 to Arcana and History checks."],
    },
    "Outlander": {
        "description": "A wanderer of old trails, wild camps, and the long miles between towns.",
        "skills": ["Athletics", "Survival"],
        "proficiencies": ["Herbalism Kit", "One Musical Instrument"],
        "equipment_bonuses": {"Nature": 1, "Survival": 1},
        "notes": ["Forager's kit: +1 to Nature and Survival checks."],
    },
    "Charlatan": {
        "description": "A smooth liar, card sharp, or traveling fraud who lives by nerve and timing.",
        "skills": ["Deception", "Sleight of Hand"],
        "proficiencies": ["Forgery Kit", "Disguise Kit"],
        "equipment_bonuses": {"Deception": 1, "Performance": 1},
        "notes": ["False papers and stage tricks: +1 to Deception and Performance checks."],
    },
    "Guild Artisan": {
        "description": "A trained craftsperson used to fair prices, supply ledgers, and trade politics.",
        "skills": ["Insight", "Persuasion"],
        "proficiencies": ["Artisan's Tools", "Merchant's Scales"],
        "equipment_bonuses": {"History": 1, "Persuasion": 1},
        "notes": ["Merchant's ledger: +1 to History and Persuasion checks."],
    },
    "Hermit": {
        "description": "A secluded seeker with a patient eye for signs, sickness, and omens.",
        "skills": ["Medicine", "Religion"],
        "proficiencies": ["Herbalism Kit", "Sylvan"],
        "equipment_bonuses": {"Insight": 1, "Medicine": 1},
        "notes": ["Herb satchel: +1 to Insight and Medicine checks."],
    },
}
