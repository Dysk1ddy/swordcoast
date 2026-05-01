from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from ..data.items.catalog import ITEMS, item_category_label, item_rules_text, item_type_label
from ..data.story.character_options.backgrounds import BACKGROUNDS
from ..data.story.character_options.classes import CLASSES, CLASS_LEVEL_PROGRESSION
from ..data.story.character_options.races import RACES
from ..data.story.lore import (
    ABILITY_LORE,
    BACKGROUND_LORE,
    CLASS_LORE,
    FEATURE_LORE,
    LOCATION_LORE,
    RACE_LORE,
    SKILL_LORE,
)
from ..data.story.public_terms import (
    ability_label,
    class_label,
    feature_label,
    race_label,
    resource_label,
    spell_label,
    FEATURE_PUBLIC_LABELS,
    SPELL_NAME_TO_ID,
    SPELL_PUBLIC_LABELS,
)
from ..gameplay.class_framework import CLASS_RESOURCE_LABELS
from ..gameplay.defense_formula import base_damage_reduction_for_defense
from ..gameplay.magic_points import SPELL_MP_COSTS
from ..gameplay.status_effects import STATUS_DEFINITIONS
from ..models import SKILL_TO_ABILITY
from ..ui.colors import strip_ansi


@dataclass(frozen=True)
class ExamineEntry:
    title: str
    category: str
    description: str
    details: tuple[str, ...] = field(default_factory=tuple)


ABILITY_CODES_BY_PUBLIC_LABEL = {
    ability_label(code).lower(): code for code in ABILITY_LORE
}
ABILITY_CODES_BY_PUBLIC_LABEL.update({code.lower(): code for code in ABILITY_LORE})


FEATURE_DESCRIPTION_OVERRIDES = {
    "warrior_grit": "Grit is a Warrior resource earned from hard contact. Spend it on rallying, line pressure, and training that turns pain into control.",
    "warrior_guard": "Guard Stance raises Defense and Stability while lowering Accuracy. Use it when holding space matters more than landing a clean strike.",
    "warrior_shove": "Shove tests force and footing. A successful shove knocks the target prone and can leave them reeling.",
    "warrior_pin": "Pin turns a weapon strike into control. A successful pin deals damage and can leave the target reeling.",
    "warrior_rally": "Warrior Rally spends Grit to steady an ally and put them back in the fight.",
    "weapon_read": "Weapon Read studies an enemy's guard and makes the next opening easier to punish.",
    "mage_charge": "Charge is the Mage's working pressure: measured force held in pattern until it becomes a channel.",
    "mage_focus": "Focus represents a Mage holding attention under pressure. It supports cleaner channeling and sharper reads.",
    "arcane_bolt": "Arcane Bolt is a quick channel strike that spends MP for force damage. It can be used as an action or bonus action when ready.",
    "minor_channel": "Minor Channel spends 1 MP for a small force strike shaped through a caster's pattern.",
    "mage_ward": "Ward is stored magical shielding. Damage resolution spends Ward after armor and Defense, before temp HP or HP.",
    "pattern_read": "Pattern Read marks a target's weak angle and makes incoming attacks against them easier.",
    "ground": "Ground steadies the caster against channel strain and improves resistance for a short time.",
    "focused_eye": "Focused Eye marks a Mage's habit of reading small pressure shifts before they become danger.",
    "juggernaut_momentum": "Momentum rewards a Warrior for staying in contact and turning physical pressure into tempo.",
    "iron_draw": "Iron Draw pulls enemy attention and rewards a Warrior for controlling the line.",
    "shoulder_in": "Shoulder In spends Grit to harden the Warrior's Defense for a short window.",
    "line_holder": "Line Holder adds Stability while the Warrior stays conscious and keeps space for the party.",
    "weapon_familiarity": "Weapon Familiarity adds steady strike and damage bonuses from repeated practice.",
    "weapon_master_combo": "Combo is a Weapon Master resource spent on clean follow-through and pressure strings.",
    "style_wheel": "Style Wheel opens a set of weapon options for reading, breaking, and redirecting guard.",
    "measure_twice": "Measure Twice sets up a cleaner weapon strike by taking time to read the angle.",
    "clean_line": "Clean Line makes a disciplined weapon strike with reduced noise and cleaner payoff.",
    "dent_the_shell": "Dent The Shell pressures Defense and makes armor or guard easier to crack.",
    "hook_the_guard": "Hook The Guard attacks a defended target's stance and can disrupt their guard.",
    "berserker_fury": "Fury builds when a Berserker takes or deals hard damage. Spend it on violent tempo.",
    "redline": "Redline raises attack and damage pressure while exposing the Berserker to danger.",
    "reckless_cut": "Reckless Cut trades safety for a harder strike lane.",
    "teeth_set": "Teeth Set spends Fury to endure the next exchange.",
    "drink_the_hurt": "Drink The Hurt spends Fury to blunt incoming punishment for a short window.",
    "bloodreaver_blood_debt": "Blood Debt tracks owed violence. The Bloodreaver turns wounds into leverage.",
    "red_mark": "Red Mark names a target for Bloodreaver pressure and future payoff.",
    "blood_price": "Blood Price spends Blood Debt for an immediate combat swing.",
    "war_salve_strike": "War-Salve Strike applies brutal field treatment through a weapon hit.",
    "open_the_ledger": "Open The Ledger spends Grit against a Red Mark target for a heavy finishing pressure.",
    "rogue_edge": "Edge is the Rogue's tempo resource. It appears through openings, exposed targets, and near misses.",
    "rogue_mark": "Mark Work names a target for a Rogue's precision and setup pressure.",
    "rogue_satchel": "Satchel Kit tracks field tools, thrown mixtures, and quick fixes carried into danger.",
    "rogue_poison": "Poison Work prepares toxins that stack pressure through careful hits.",
    "cunning_action": "Veil Step is a quick Rogue movement option for repositioning under pressure.",
    "tool_read": "Tool Read studies a target's gear, footing, and habits to create an attack opening.",
    "rogue_skirmish": "Skirmish spends Edge to slip into Mobile Stance and keep the Rogue moving.",
    "slip_away": "Slip Away helps a Rogue escape a strike line before the enemy can settle their aim.",
    "rogue_feint": "Feint tests the target's read and can expose them while granting Edge.",
    "dirty_trick": "Dirty Trick uses grit, dust, leverage, or misdirection to create a bad moment for the target.",
    "shadowguard_shadow": "Shadow tracks defensive misdirection for a Shadowguard.",
    "false_target": "False Target spends Edge to make an ally harder to hit and punish misses.",
    "smoke_pin": "Smoke Pin spends Shadow to blind and expose a target while veiling the Rogue.",
    "cover_the_healer": "Cover The Healer spends Shadow to guard an ally who is keeping the line alive.",
    "death_mark": "Death Mark names a target for Assassin pressure.",
    "quiet_knife": "Quiet Knife favors a precise strike where panic and noise would waste the opening.",
    "between_plates": "Between Plates spends Edge to drive damage through a guarded target.",
    "sudden_end": "Sudden End spends heavy Edge for a finishing strike when the target is exposed.",
    "poisoner_toxin": "Toxin is the Poisoner's prepared resource for applying and detonating poison pressure.",
    "black_drop": "Black Drop spends Toxin to prepare the next weapon hit for poison damage.",
    "green_needle": "Green Needle applies poison through a quick attack.",
    "bitter_cloud": "Bitter Cloud spends Toxin to spread poisonous pressure across a target's space.",
    "rot_thread": "Rot Thread spends Toxin to weaken armor and keep poison pressure active.",
    "bloom_in_the_blood": "Bloom In The Blood spends Toxin to cash out poison stacks as direct damage.",
    "alchemist_quick_mix": "Quick Mix prepares an alchemist tool for immediate combat use.",
    "redcap_tonic": "Redcap Tonic spends Satchel supplies for fast combat recovery.",
    "smoke_jar": "Smoke Jar spends Satchel supplies to create cover and grant the Rogue a cleaner escape lane.",
    "bitter_acid": "Bitter Acid spends Satchel supplies for acid damage against a target.",
    "field_stitch": "Field Stitch spends Satchel supplies to patch an ally in combat.",
    "arcanist_arc": "Arc is the Arcanist's stored pattern pressure.",
    "pattern_charge": "Pattern Charge stacks on a target and can be detonated by Arcanist techniques.",
    "arc_pulse": "Arc Pulse spends 1 MP for psychic pressure and can build Arc against leaders.",
    "marked_angle": "Marked Angle spends 1 MP to open a cleaner attack lane against a target.",
    "quiet_sum": "Quiet Sum rewards an Arcanist for patient pressure and precise pattern math.",
    "detonate_pattern": "Detonate Pattern spends Arc to turn Pattern Charges into damage.",
    "elementalist_attunement": "Attunement tracks the Elementalist's current elemental pressure.",
    "elemental_weave": "Elemental Weave lets an Elementalist carry elemental pressure between channel choices.",
    "ember_lance": "Ember Lance spends 1 MP for a fire channel against one target.",
    "frost_shard": "Frost Shard spends 1 MP for a cold channel that tests the target's body under pressure.",
    "volt_grasp": "Volt Grasp spends 1 MP for lightning pressure at close range.",
    "change_weather_hand": "Change Weather In The Hand shifts the Elementalist's read of the fight.",
    "burning_line": "Burning Line spends 4 MP to burn across multiple enemies and leave ongoing fire.",
    "lockfrost": "Lockfrost spends 4 MP to slow and pin down a group with cold pressure.",
    "aethermancer_flow": "Flow is the Aethermancer's resource for healing tempo and overflow protection.",
    "field_mend": "Field Mend spends 3 MP to heal an ally through a controlled channel.",
    "pulse_restore": "Pulse Restore spends 4 MP for stronger emergency healing.",
    "triage_line": "Triage Line spends 3 MP to steady the party's resist checks for a short window.",
    "clean_breath": "Clean Breath spends 2 MP to clear poison and restore a little breathing room.",
    "steady_pulse": "Steady Pulse improves the Aethermancer's reliability under healing pressure.",
    "overflow_shell": "Overflow Shell spends Flow to convert excess healing pressure into protection.",
    "spellguard_ward": "Ward is the Spellguard's defensive resource. It catches damage before HP does.",
    "anchor_shell": "Anchor Shell spends 3 MP to place ward protection on an ally.",
    "ward_shell": "Ward Shell spends ward pressure to absorb incoming damage.",
    "blue_glass_palm": "Blue Glass Palm spends 1 MP for force damage and can fixate a target.",
    "lockstep_field": "Lockstep Field spends 3 MP to steady allies and improve Stability.",
}


ACTION_DESCRIPTION_OVERRIDES = {
    "strike": "A basic weapon strike using the actor's equipped weapon, strike bonus, and damage rules.",
    "take guard stance": FEATURE_DESCRIPTION_OVERRIDES["warrior_guard"],
    "shove": FEATURE_DESCRIPTION_OVERRIDES["warrior_shove"],
    "pin": FEATURE_DESCRIPTION_OVERRIDES["warrior_pin"],
    "warrior rally": FEATURE_DESCRIPTION_OVERRIDES["warrior_rally"],
    "use veil step": FEATURE_DESCRIPTION_OVERRIDES["cunning_action"],
    "mark target": FEATURE_DESCRIPTION_OVERRIDES["rogue_mark"],
    "attempt parley": "A combat social action. The party tries to bend the encounter with Persuasion or Intimidation before blades decide everything.",
    "try to flee": "An escape action. The actor uses Stealth and positioning to break away from the fight.",
    "help a downed ally": "A Medicine action used to stabilize or revive a fallen party member when the fight allows it.",
    "use an item": "Opens usable inventory for potions, scripts, supplies, and other combat-ready items.",
    "raise shield": "Uses the shield to increase Defense for the next exchange.",
    "change stance": "Changes the combat stance, trading accuracy, Defense, Stability, or mobility.",
    "make off-hand strike": "Uses an off-hand weapon after the main attack when the actor has a valid second weapon.",
    "end turn": "Ends the acting character's turn and passes tempo to the next combatant.",
}


GROUP_DESCRIPTIONS = {
    "action": "Actions spend the main turn resource: weapon strikes, forceful maneuvers, heavy channels, and other committed moves.",
    "bonus action": "Bonus actions are quick follow-through moves: stance shifts, short channels, marks, rallies, and class tempo tools.",
    "item": "Item actions use carried potions, scripts, tools, or supplies.",
    "social": "Social actions try to change a fight through pressure, fear, trust, or leverage.",
    "escape": "Escape actions try to leave the fight or change position before the encounter closes.",
    "end turn": "End Turn passes control to the next combatant.",
}


RESOURCE_DESCRIPTIONS = {
    "mp": "MP fuels channeling. Mages and other channel-capable characters spend it on attack, ward, and healing abilities.",
    "grit": "Grit is Warrior toughness turned into usable tempo.",
    "momentum": "Momentum tracks sustained physical pressure.",
    "combo": "Combo tracks weapon rhythm for follow-up techniques.",
    "fury": "Fury grows from violence and danger, then pays for Berserker pressure.",
    "blood_debt": "Blood Debt tracks owed harm for Bloodreaver techniques.",
    "ward": "Ward catches incoming damage before HP when Spellguard tools are active.",
    "flow": "Flow supports Aethermancer healing and overflow protection.",
    "arc": "Arc stores Arcanist pattern pressure.",
    "attunement": "Attunement tracks an Elementalist's active elemental tempo.",
    "edge": "Edge is Rogue advantage in motion: openings, near misses, and exposed targets.",
    "shadow": "Shadow stores Shadowguard misdirection.",
    "satchel": "Satchel measures field tools available to Rogue and Alchemist techniques.",
    "toxin": "Toxin measures prepared poison pressure.",
    "focus": "Focus represents a Mage keeping a clean pattern under stress.",
}


GAME_TERM_DESCRIPTIONS = {
    "party xp": (
        "Party XP",
        "Progression",
        "Party XP is shared experience for the whole crew. When it reaches the next threshold, the party levels together and new training comes online.",
    ),
    "loot": (
        "Loot",
        "Inventory",
        "Loot comes from defeated enemies, caches, quest rewards, and scene discoveries. Collected items go into shared inventory unless the reward is gold or supplies.",
    ),
    "gold": (
        "Gold",
        "Currency",
        "Gold is shared party money for shops, services, gear work, and camp choices that need payment.",
    ),
    "supplies": (
        "Supplies",
        "Inventory",
        "Supplies cover food, packs, repair bits, fuel, and trade goods. Camp and inventory screens track the shared supply pool.",
    ),
    "short rests": (
        "Short Rests",
        "Rest",
        "Short rests patch the party up between dangerous pushes. They restore some HP and class resources without the full reset of a long rest.",
    ),
    "hp": (
        "HP",
        "Combat Stat",
        "HP is hit points. A character at 0 HP is down, and recovery actions or rest are needed to get them fighting again.",
    ),
    "defense": (
        "Defense",
        "Combat Stat",
        "Defense covers both the contact number enemies must beat and the physical damage reduction from armor, shields, gear, and statuses.",
    ),
    "inventory": (
        "Inventory",
        "Command",
        "Inventory shows shared items, gold, supplies, consumables, and equipment that can be used or assigned when the current scene allows it.",
    ),
    "journal": (
        "Journal",
        "Command",
        "Journal tracks quests, clues, recent notes, major choices, and consequences carried forward by the story.",
    ),
    "camp": (
        "Camp",
        "Command",
        "Camp manages active companions, resting, recovery, camp conversations, and party logistics between dangerous scenes.",
    ),
    "party": (
        "Party",
        "Command",
        "Party shows the active crew, current location, objective, HP, Defense, resources, conditions, and other sheet details.",
    ),
    "quests": (
        "Quests",
        "Journal",
        "Quests track active jobs, ready turn-ins, completed work, objectives, and rewards.",
    ),
    "clues": (
        "Clues",
        "Journal",
        "Clues are unresolved evidence, leads, and remembered details that can open or alter later choices.",
    ),
}


GAME_TERM_ALIASES = {
    "xp": "party xp",
    "experience": "party xp",
    "party experience": "party xp",
    "short rest": "short rests",
    "rest": "short rests",
    "ac": "defense",
    "armor class": "defense",
    "active party": "party",
    "quest load": "quests",
    "unresolved clues": "clues",
}


STATUS_BEHAVIOR_DESCRIPTIONS = {
    "surprised": "Surprised costs the bearer their next turn, then clears.",
    "blinded": "Blinded breaks sight. Attacks strain unless Blind Sense applies, and Perception, Investigation, and Survival checks strain while it lasts.",
    "charmed": "Charmed prevents hostile actions until the effect clears.",
    "deafened": "Deafened strains Perception checks tied to hearing, listening, sound, or noise.",
    "exhaustion": "Exhaustion stacks. One stack strains non-attack checks, two stacks add a strike penalty, and three stacks add a resist penalty plus attack strain.",
    "focused": "Focused records a clean route read or timing read from the scene. It is a short-lived attention state and clears with other temporary statuses.",
    "frightened": "Frightened strains attacks and checks while it lasts.",
    "grappled": "Grappled locks movement, blocks fleeing, strains attacks, and drags Stability down.",
    "incapacitated": "Incapacitated prevents the bearer from acting on their turn.",
    "invisible": "Invisible grants a cleaner attack line, can spoil enemy dodges, and breaks when the bearer makes a hostile action.",
    "paralyzed": "Paralyzed prevents turns, blocks movement and fleeing, drops Avoidance and Stability, and auto-fails Strength or Dexterity resist checks.",
    "petrified": "Petrified prevents turns, blocks movement and fleeing, halves incoming damage, and auto-fails Strength or Dexterity resist checks.",
    "poisoned": "Poisoned strains attacks and checks. Poison stacks can also tick for poison damage through Rogue toxin hooks.",
    "reeling": "Reeling knocks timing loose.",
    "restrained": "Restrained blocks movement and fleeing, strains attacks, and drags Stability down.",
    "prone": "Prone gives melee attackers a cleaner angle, makes ranged attacks harder, and strains the bearer's attacks.",
    "raised_shield": "Raised Shield adds shield-based physical damage Defense while the bearer has a shield raised.",
    "fixated": "Fixated pulls the bearer toward the named source. Attacks against anyone else take a -2 focus penalty.",
    "drink_the_hurt": "Drink The Hurt waits for the bearer's next Wound, then heals from the hit and clears.",
    "arcane_bolt_cooldown": "Arcane Bolt Cooldown blocks another Arcane Bolt until the timer ticks down.",
    "anchor_shell": "Anchor Shell adds ward-backed Defense, draws enemy pressure toward the protected ally, and can leave the attacker reeling when the ward breaks.",
    "pattern_charge": "Pattern Charge stores Arcanist setup on the target. Detonate Pattern cashes out the stored charges as damage.",
    "exposed": "Exposed counts as an open target for Rogue and Assassin pressure.",
    "slip_away": "Slip Away is a reaction window that can turn a near hit into a miss.",
    "false_target": "False Target shields an ally with misdirection. If the attack misses, the Shadowguard gains Shadow and a close miss can leave the attacker reeling.",
    "quick_mix": "Quick Mix stores the chosen satchel rider for the next alchemist mixture: numbing paste, clinging smoke, or acid-cut solvent.",
    "black_drop": "Black Drop readies the next clean Wound to force a poison resist check and add poison stacks.",
    "marked": "Marked names a target for focused pressure. Enemy targeting, Rogue openings, Bloodreaver healing, and Assassin techniques can all read it.",
    "resist_fire": "Fire-Resistant halves incoming fire damage through the resistance check.",
    "resist_cold": "Cold-Resistant halves incoming cold damage through the resistance check.",
    "resist_lightning": "Lightning-Resistant halves incoming lightning damage through the resistance check.",
    "resist_poison": "Poison-Resistant halves incoming poison damage through the resistance check.",
    "armor_broken": "Armor Broken cuts physical damage Defense by 10% and counts as an opened target for Rogue and Weapon Master pressure.",
    "stunned": "Stunned prevents turns, blocks movement and fleeing, drops Avoidance and Stability, and auto-fails Strength or Dexterity resist checks.",
    "unconscious": "Unconscious prevents turns, blocks movement and fleeing, drops Avoidance and Stability, and auto-fails Strength or Dexterity resist checks.",
}


LOCATION_LORE_ALIASES = {
    "frontier primer": "Aethrune",
    "prologue": "Aethrune",
    "greywake briefing": "Greywake",
    "emberway ambush": "Emberway",
    "road decision after blackwake": "Blackwake Crossing",
    "act ii hub": "Act II Expedition Hub",
    "claims council": "Ashlamp Claims Council",
    "iron hollow claims council": "Ashlamp Claims Council",
    "greywake survey camp": "Greywake Wood",
    "wayside lantern shrine": "Wayside Luck Shrine",
    "resonant vault outer galleries": "Resonant Vaults",
    "resonant vaults outer galleries": "Resonant Vaults",
    "act ii complete": "Resonant Vaults",
}


def _normalize_lookup_key(value: object) -> str:
    text = strip_ansi(str(value))
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = text.replace("*", " ")
    return " ".join(re.findall(r"[a-z0-9']+", text.lower()))


def _plain_text(value: object) -> str:
    return " ".join(strip_ansi(str(value)).replace("*", "").split()).strip()


def _entry_from_lore(title: str, category: str, lore: dict[str, object], *, details: Iterable[str] = ()) -> ExamineEntry:
    menu = str(lore.get("menu", "")).strip()
    body = str(lore.get("text", "")).strip()
    description = body or menu or "No description recorded yet."
    rendered_details = tuple(detail for detail in details if detail)
    if menu and menu not in description:
        rendered_details = (menu, *rendered_details)
    return ExamineEntry(title=title, category=category, description=description, details=rendered_details)


def _feature_descriptions_from_progression() -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for levels in CLASS_LEVEL_PROGRESSION.values():
        for level_data in levels.values():
            feature_ids = list(level_data.get("feature_ids", []))
            features = list(level_data.get("features", []))
            named_descriptions = {
                _normalize_lookup_key(name): str(description)
                for name, description in features
            }
            for feature_id in feature_ids:
                public_name = feature_label(str(feature_id))
                normalized_name = _normalize_lookup_key(public_name)
                if normalized_name in named_descriptions:
                    descriptions[str(feature_id)] = named_descriptions[normalized_name]
    return descriptions


PROGRESSION_FEATURE_DESCRIPTIONS = _feature_descriptions_from_progression()


def ability_examine_entry(code_or_name: str) -> ExamineEntry | None:
    code = ABILITY_CODES_BY_PUBLIC_LABEL.get(str(code_or_name).strip().lower())
    if code is None:
        return None
    lore = ABILITY_LORE.get(code)
    if not lore:
        return None
    linked_skills = sorted(skill for skill, ability in SKILL_TO_ABILITY.items() if ability == code)
    return _entry_from_lore(
        ability_label(code),
        "Ability",
        lore,
        details=(f"Linked skills: {', '.join(linked_skills)}" if linked_skills else "",),
    )


def skill_examine_entry(skill_name: str) -> ExamineEntry | None:
    skill = next((name for name in SKILL_TO_ABILITY if name.lower() == skill_name.lower()), None)
    if skill is None:
        return None
    lore = SKILL_LORE.get(skill)
    if not lore:
        return None
    ability = SKILL_TO_ABILITY[skill]
    return _entry_from_lore(skill, "Skill", lore, details=(f"Governing ability: {ability_label(ability)}",))


def class_examine_entry(class_name: str) -> ExamineEntry | None:
    class_key = next((name for name in CLASSES if name.lower() == class_name.lower()), None)
    if class_key is None:
        class_key = next((name for name in CLASSES if class_label(name).lower() == class_name.lower()), None)
    if class_key is None:
        return None
    lore = CLASS_LORE.get(class_key, {})
    class_data = CLASSES[class_key]
    details = (
        f"Hit die: d{class_data['hit_die']}",
        f"Resist checks: {', '.join(class_data['saving_throws'])}",
        f"Starting features: {', '.join(feature_label(feature) for feature in class_data['features'][:5])}",
    )
    if lore:
        return _entry_from_lore(class_label(class_key), "Class", lore, details=details)
    return ExamineEntry(class_label(class_key), "Class", str(class_data["description"]), details)


def race_examine_entry(race_name: str) -> ExamineEntry | None:
    race_key = next((name for name in RACES if name.lower() == race_name.lower()), None)
    if race_key is None:
        race_key = next((name for name in RACES if race_label(name).lower() == race_name.lower()), None)
    if race_key is None:
        return None
    lore = RACE_LORE.get(race_key, {})
    race_data = RACES[race_key]
    details = (
        f"Bonuses: {', '.join(f'{ability_label(key)} +{value}' for key, value in race_data['bonuses'].items())}",
        f"Features: {', '.join(feature_label(feature) for feature in race_data['features']) or 'None'}",
    )
    if lore:
        return _entry_from_lore(race_label(race_key), "People", lore, details=details)
    return ExamineEntry(race_label(race_key), "People", str(race_data["description"]), details)


def background_examine_entry(background_name: str) -> ExamineEntry | None:
    background_key = next((name for name in BACKGROUNDS if name.lower() == background_name.lower()), None)
    if background_key is None:
        background_key = next(
            (
                name
                for name, lore in BACKGROUND_LORE.items()
                if str(lore.get("label", name)).lower() == background_name.lower()
            ),
            None,
        )
    if background_key is None:
        return None
    lore = BACKGROUND_LORE.get(background_key, {})
    data = BACKGROUNDS[background_key]
    title = str(lore.get("label", background_key))
    details = (f"Skills: {', '.join(data['skills'])}",)
    if lore:
        return _entry_from_lore(title, "Background", lore, details=details)
    return ExamineEntry(title, "Background", str(data.get("description", "")), details)


def feature_examine_entry(feature_id_or_label: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(feature_id_or_label)
    feature_id = None
    for candidate_id, public_label in FEATURE_PUBLIC_LABELS.items():
        if normalized in {_normalize_lookup_key(candidate_id), _normalize_lookup_key(public_label)}:
            feature_id = candidate_id
            break
    if feature_id is None and normalized in {_normalize_lookup_key(key) for key in FEATURE_LORE}:
        feature_id = next(key for key in FEATURE_LORE if _normalize_lookup_key(key) == normalized)
    if feature_id is None:
        return None

    title = feature_label(feature_id)
    lore = FEATURE_LORE.get(feature_id)
    if lore:
        return _entry_from_lore(title, "Feature / Passive", lore)
    description = (
        FEATURE_DESCRIPTION_OVERRIDES.get(feature_id)
        or PROGRESSION_FEATURE_DESCRIPTIONS.get(feature_id)
        or "A character feature currently attached to the runtime sheet. Its exact behavior is handled by combat and character code."
    )
    return ExamineEntry(title=title, category="Feature / Passive", description=description)


def spell_examine_entry(spell_id_or_label: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(spell_id_or_label)
    spell_id = None
    for candidate_id, public_label in SPELL_PUBLIC_LABELS.items():
        if normalized in {_normalize_lookup_key(candidate_id), _normalize_lookup_key(public_label)}:
            spell_id = candidate_id
            break
    if spell_id is None:
        for public_label, candidate_id in SPELL_NAME_TO_ID.items():
            if normalized == _normalize_lookup_key(public_label):
                spell_id = candidate_id
                break
    if spell_id is None:
        return None
    feature_entry = feature_examine_entry(spell_id)
    cost = SPELL_MP_COSTS.get(spell_id)
    details = []
    if cost is not None:
        details.append(f"Cost: {cost} MP")
    if feature_entry is None:
        return ExamineEntry(spell_label(spell_id), "Channel", "A channeling ability powered by MP.", tuple(details))
    return ExamineEntry(
        title=feature_entry.title,
        category="Channel",
        description=feature_entry.description,
        details=(*feature_entry.details, *details),
    )


def resource_examine_entry(resource_name: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(resource_name)
    resource_id = None
    for candidate_id, label in {**CLASS_RESOURCE_LABELS, "mp": "MP"}.items():
        if normalized in {_normalize_lookup_key(candidate_id), _normalize_lookup_key(label), _normalize_lookup_key(resource_label(candidate_id))}:
            resource_id = candidate_id
            break
    if resource_id is None:
        return None
    return ExamineEntry(
        title=resource_label(resource_id).title() if resource_id != "mp" else "MP",
        category="Resource",
        description=RESOURCE_DESCRIPTIONS.get(resource_id, "A tracked combat resource."),
    )


def _game_term_key(text: str) -> str | None:
    normalized = _normalize_lookup_key(text)
    if not normalized:
        return None
    if normalized in GAME_TERM_DESCRIPTIONS:
        return normalized
    alias = GAME_TERM_ALIASES.get(normalized)
    if alias is not None:
        return alias
    tokens = normalized.split()
    if len(tokens) >= 2 and tokens[:2] == ["party", "xp"]:
        return "party xp"
    if len(tokens) >= 2 and tokens[0] == "short" and tokens[1] in {"rest", "rests"}:
        return "short rests"
    if tokens and tokens[0] in {"gold", "supplies", "hp", "ac"} and (len(tokens) == 1 or tokens[1].isdigit()):
        return GAME_TERM_ALIASES.get(tokens[0], tokens[0])
    return None


def _game_term_details(key: str, game=None) -> tuple[str, ...]:
    if game is None:
        return ()
    state = getattr(game, "state", None)
    details: list[str] = []
    if key == "party xp":
        xp_summary = getattr(game, "xp_progress_summary", None)
        if callable(xp_summary):
            details.append(str(xp_summary()))
        elif state is not None:
            details.append(f"Current XP: {getattr(state, 'xp', 0)}")
    elif key == "gold" and state is not None:
        details.append(f"Current gold: {getattr(state, 'gold', 0)}")
    elif key == "supplies":
        supply_getter = getattr(game, "current_supply_points", None)
        if callable(supply_getter):
            details.append(f"Current supplies: {supply_getter()}")
    elif key == "short rests" and state is not None:
        details.append(f"Short rests remaining: {getattr(state, 'short_rests_remaining', 0)}")
    elif key == "party" and state is not None:
        party_members = getattr(state, "party_members", None)
        if callable(party_members):
            details.append(f"Active members: {len(party_members())}")
    return tuple(details)


def game_term_examine_entry(text: str, *, game=None) -> ExamineEntry | None:
    key = _game_term_key(text)
    if key is None:
        return None
    title, category, description = GAME_TERM_DESCRIPTIONS[key]
    return ExamineEntry(title=title, category=category, description=description, details=_game_term_details(key, game))


def _join_clauses(clauses: list[str]) -> str:
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == 2:
        return f"{clauses[0]} and {clauses[1]}"
    return f"{', '.join(clauses[:-1])}, and {clauses[-1]}"


def _status_value_clause(
    definition: dict[str, object],
    key: str,
    *,
    positive: str,
    negative: str,
    suffix: str = "",
    negative_suffix: str | None = None,
    value_style: str = "by",
) -> str:
    value = int(definition.get(key, 0) or 0)

    def render(phrase: str, amount: int, rendered_suffix: str) -> str:
        if value_style == "prefix":
            return f"{phrase}{amount}{rendered_suffix}"
        return f"{phrase} by {amount}{rendered_suffix}"

    if value > 0:
        return render(positive, value, suffix)
    if value < 0:
        return render(negative, abs(value), negative_suffix if negative_suffix is not None else suffix)
    return ""


def _status_math_clauses(definition: dict[str, object]) -> list[str]:
    clauses: list[str] = []
    if definition.get("ongoing_damage"):
        damage_type = str(definition.get("damage_type", "damage")).strip() or "damage"
        clauses.append(f"deals {definition['ongoing_damage']} {damage_type} damage when conditions tick")

    clauses.extend(
        clause
        for clause in (
            _status_value_clause(
                definition,
                "attack_bonus",
                positive="raises strike accuracy",
                negative="lowers strike accuracy",
            ),
            _status_value_clause(
                definition,
                "attack_penalty",
                positive="lowers strike accuracy",
                negative="raises strike accuracy",
            ),
            _status_value_clause(
                definition,
                "incoming_attack_bonus",
                positive="gives attackers +",
                negative="gives attackers -",
                suffix=" strike accuracy",
                value_style="prefix",
            ),
            _status_value_clause(
                definition,
                "incoming_attack_penalty",
                positive="gives attackers -",
                negative="gives attackers +",
                suffix=" strike accuracy",
                value_style="prefix",
            ),
            _status_value_clause(
                definition,
                "damage_bonus",
                positive="adds ",
                negative="removes ",
                suffix=" damage to the bearer's weapon hits",
                negative_suffix=" damage from the bearer's weapon hits",
                value_style="prefix",
            ),
            _status_value_clause(
                definition,
                "save_bonus",
                positive="raises resist checks",
                negative="lowers resist checks",
            ),
            _status_value_clause(
                definition,
                "save_penalty",
                positive="lowers resist checks",
                negative="raises resist checks",
            ),
            _status_value_clause(
                definition,
                "ac_bonus",
                positive="raises Defense rating",
                negative="lowers Defense rating",
            ),
            _status_value_clause(
                definition,
                "ac_penalty",
                positive="lowers Defense rating",
                negative="raises Defense rating",
            ),
            _status_value_clause(
                definition,
                "defense_bonus_points",
                positive="raises physical damage Defense",
                negative="lowers physical damage Defense",
            ),
            _status_value_clause(
                definition,
                "stability_bonus",
                positive="raises Stability",
                negative="lowers Stability",
            ),
            _status_value_clause(
                definition,
                "stability_penalty",
                positive="lowers Stability",
                negative="raises Stability",
            ),
            _status_value_clause(
                definition,
                "avoidance_bonus",
                positive="raises Avoidance",
                negative="lowers Avoidance",
            ),
            _status_value_clause(
                definition,
                "avoidance_penalty",
                positive="lowers Avoidance",
                negative="raises Avoidance",
            ),
            _status_value_clause(
                definition,
                "armor_break_percent",
                positive="cuts the bearer's armor Defense",
                negative="restores the bearer's armor Defense",
                suffix="%",
            ),
            _status_value_clause(
                definition,
                "outgoing_armor_break_percent",
                positive="cuts enemy armor Defense when the bearer attacks",
                negative="restores enemy armor Defense when the bearer attacks",
                suffix="%",
            ),
            _status_value_clause(
                definition,
                "flee_bonus",
                positive="lowers flee DCs",
                negative="raises flee DCs",
            ),
        )
        if clause
    )
    return clauses


def _status_math_sentence(definition: dict[str, object]) -> str:
    clauses = _status_math_clauses(definition)
    if not clauses:
        return ""
    return f"It {_join_clauses(clauses)}."


def _status_description(status_id: str, title: str, definition: dict[str, object]) -> str:
    behavior = STATUS_BEHAVIOR_DESCRIPTIONS.get(status_id, "")
    math = _status_math_sentence(definition)
    if behavior and math:
        return f"{behavior} {math}"
    if behavior:
        return behavior
    if math:
        return math
    return f"{title} is handled by the combat hook that applied it."


def _status_detail_lines(definition: dict[str, object]) -> tuple[str, ...]:
    details: list[str] = []
    if definition.get("ongoing_damage"):
        damage_type = str(definition.get("damage_type", "damage")).strip() or "damage"
        details.append(f"Ongoing damage: {definition['ongoing_damage']} {damage_type}")
    for key, label in (
        ("attack_bonus", "Strike bonus"),
        ("attack_penalty", "Strike penalty"),
        ("incoming_attack_bonus", "Incoming strike bonus"),
        ("incoming_attack_penalty", "Incoming strike penalty"),
        ("damage_bonus", "Damage bonus"),
        ("save_bonus", "Resist bonus"),
        ("save_penalty", "Resist penalty"),
        ("ac_bonus", "Defense bonus"),
        ("ac_penalty", "Defense penalty"),
        ("defense_bonus_points", "Defense shift"),
        ("stability_bonus", "Stability bonus"),
        ("stability_penalty", "Stability penalty"),
        ("avoidance_bonus", "Avoidance bonus"),
        ("avoidance_penalty", "Avoidance penalty"),
        ("armor_break_percent", "Armor break"),
        ("outgoing_armor_break_percent", "Outgoing armor break"),
        ("flee_bonus", "Flee bonus"),
    ):
        value = definition.get(key)
        if value:
            suffix = "%" if key.endswith("_percent") else ""
            details.append(f"{label}: {value}{suffix}")
    return tuple(details)


def status_examine_entry(status_id_or_label: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(status_id_or_label)
    status_id = None
    for candidate_id, definition in STATUS_DEFINITIONS.items():
        if normalized in {_normalize_lookup_key(candidate_id), _normalize_lookup_key(definition.get("name", candidate_id))}:
            status_id = candidate_id
            break
    if status_id is None:
        return None
    definition = STATUS_DEFINITIONS[status_id]
    title = str(definition.get("name", status_id.replace("_", " ").title()))
    details = _status_detail_lines(definition)
    description = _status_description(status_id, title, definition)
    return ExamineEntry(title=title, category="Condition", description=description, details=details)


def item_examine_entry(text: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(text)
    for item in ITEMS.values():
        if normalized in {
            _normalize_lookup_key(item.name),
            _normalize_lookup_key(item.item_id),
            _normalize_lookup_key(item.legacy_id),
            _normalize_lookup_key(item.catalog_id),
        }:
            rules = item_rules_text(item)
            details = (
                f"{item.rarity_title} {item_category_label(item.category)} / {item_type_label(item.item_type)}",
                f"Value: {item.value} gold | Weight: {item.weight:g} lb",
                f"Rules: {rules}" if rules else "",
            )
            return ExamineEntry(item.name, "Item", item.description, tuple(detail for detail in details if detail))
    return None


def _location_lore_key_for_label(label: object) -> str | None:
    normalized = _normalize_lookup_key(label)
    for key in LOCATION_LORE:
        if normalized == _normalize_lookup_key(key):
            return key
    for alias, lore_key in LOCATION_LORE_ALIASES.items():
        if normalized == _normalize_lookup_key(alias) and lore_key in LOCATION_LORE:
            return lore_key
    return None


def _location_description(lore: dict[str, object]) -> str:
    menu = str(lore.get("menu", "")).strip()
    if menu:
        return menu
    text = str(lore.get("text", "")).strip()
    if not text:
        return "No location note recorded yet."
    return text.split("\n\n", 1)[0].strip()


def _location_entry_from_lore(title: str, lore: dict[str, object], *, details: Iterable[str] = ()) -> ExamineEntry:
    return ExamineEntry(
        title=title,
        category="Location",
        description=_location_description(lore),
        details=tuple(detail for detail in details if detail),
    )


def _current_room_location_entry(game, title: str) -> ExamineEntry | None:
    for dungeon_getter_name, room_getter_name in (
        ("current_act1_dungeon", "current_act1_room"),
        ("current_act2_dungeon", "current_act2_room"),
    ):
        dungeon_getter = getattr(game, dungeon_getter_name, None)
        room_getter = getattr(game, room_getter_name, None)
        if not callable(dungeon_getter) or not callable(room_getter):
            continue
        try:
            dungeon = dungeon_getter()
            if dungeon is None:
                continue
            room = room_getter(dungeon)
        except Exception:
            continue
        room_title = str(getattr(room, "title", "")).strip()
        display_title = title
        if room_title and _normalize_lookup_key(room_title) not in _normalize_lookup_key(title):
            display_title = f"{title} / {room_title}"
        description = str(getattr(room, "summary", "")).strip() or "A mapped room in the current site."
        details = []
        dungeon_title = str(getattr(dungeon, "title", "")).strip()
        if dungeon_title:
            details.append(f"Site: {dungeon_title}")
        role = str(getattr(room, "role", "")).strip()
        if role:
            details.append(f"Map role: {role.title()}")
        return ExamineEntry(display_title, "Location", description, tuple(details))
    return None


def current_location_examine_entry(game) -> ExamineEntry | None:
    state = getattr(game, "state", None)
    if state is None:
        return None
    hud_location = getattr(game, "hud_location_label", None)
    if callable(hud_location):
        title = str(hud_location()).strip()
    else:
        scene_labels = getattr(game, "SCENE_LABELS", {})
        scene_key = str(getattr(state, "current_scene", ""))
        title = str(scene_labels.get(scene_key, scene_key.replace("_", " ").title() or "Adventure"))

    room_entry = _current_room_location_entry(game, title)
    if room_entry is not None:
        return room_entry

    scene_key = str(getattr(state, "current_scene", ""))
    scene_labels = getattr(game, "SCENE_LABELS", {})
    label = scene_labels.get(scene_key, title)
    lore_key = (
        _location_lore_key_for_label(label)
        or _location_lore_key_for_label(title)
        or _location_lore_key_for_label(scene_key.replace("_", " "))
    )
    if lore_key is None:
        return None
    objective = str(getattr(game, "SCENE_OBJECTIVES", {}).get(scene_key, "")).strip()
    return _location_entry_from_lore(title or lore_key, LOCATION_LORE[lore_key], details=(f"Objective: {objective}",))


def location_examine_entry(text: str, *, game=None) -> ExamineEntry | None:
    if game is not None:
        current_entry = current_location_examine_entry(game)
        if current_entry is not None and _normalize_lookup_key(text) == _normalize_lookup_key(current_entry.title):
            return current_entry
        scene_labels = getattr(game, "SCENE_LABELS", {})
        for scene_key, label in scene_labels.items():
            if _normalize_lookup_key(text) in {
                _normalize_lookup_key(scene_key),
                _normalize_lookup_key(label),
            }:
                lore_key = (
                    _location_lore_key_for_label(label)
                    or _location_lore_key_for_label(scene_key.replace("_", " "))
                )
                if lore_key is not None:
                    return _location_entry_from_lore(str(label), LOCATION_LORE[lore_key])

    lore_key = _location_lore_key_for_label(text)
    if lore_key is None:
        return None
    return _location_entry_from_lore(lore_key, LOCATION_LORE[lore_key])


def named_character_examine_entry(text: str, game=None) -> ExamineEntry | None:
    name = _plain_text(text)
    intros = getattr(game, "NAMED_CHARACTER_INTROS", None)
    public_character_name = getattr(game, "public_character_name", None)
    if intros is None:
        from ..gameplay.base import GameBase

        intros = GameBase.NAMED_CHARACTER_INTROS
        public_character_name = None
    public_name = str(public_character_name(name) if callable(public_character_name) else name)
    description = intros.get(name) or intros.get(public_name)
    if not description:
        return None
    return ExamineEntry(public_name, "Character", description)


def _character_sheet_description(actor, public_name: str) -> str:
    race_name = str(getattr(actor, "race", "")).strip()
    class_name = str(getattr(actor, "class_name", "")).strip()
    background_name = str(getattr(actor, "background", "")).strip()
    level = getattr(actor, "level", "?")

    race_display = race_label(race_name) if race_name else "unknown people"
    class_display = class_label(class_name) if class_name else "adventurer"
    background_phrase = f" with {background_name.lower()} training" if background_name else ""
    sentences = [f"{public_name} is a level {level} {race_display} {class_display}{background_phrase}."]

    class_description = str(CLASSES.get(class_name, {}).get("description", "")).strip()
    if class_description:
        sentences.append(class_description)
    background_description = str(BACKGROUNDS.get(background_name, {}).get("description", "")).strip()
    if background_description:
        sentences.append(background_description)
    if not class_description and not background_description:
        race_description = str(RACES.get(race_name, {}).get("description", "")).strip()
        if race_description:
            sentences.append(race_description)

    notes = [str(note).strip() for note in getattr(actor, "notes", []) if str(note).strip()]
    for note in notes:
        lowered = note.lower()
        if "kit:" in lowered or "preset build:" in lowered:
            continue
        if note not in sentences:
            sentences.append(note)
        break

    if len(sentences) == 1:
        weapon = getattr(getattr(actor, "weapon", None), "name", "")
        weapon_text = f" with {weapon}" if weapon else ""
        sentences.append(f"Their sheet drives HP, Defense, skills, conditions, and combat options{weapon_text}.")
    return " ".join(sentences)


def _character_defense_detail(actor, game=None) -> str:
    contact = getattr(actor, "armor_class", "?")
    actor_uses_points = getattr(game, "actor_uses_defense_points", None)
    effective_points = getattr(game, "effective_defense_points", None)
    effective_dr = getattr(game, "effective_defense_percent", None)
    if callable(actor_uses_points) and callable(effective_points) and callable(effective_dr):
        if actor_uses_points(actor):
            defense = effective_points(actor)
            dr = effective_dr(actor, damage_type="slashing")
            return f"Defense: {defense} (DR {dr}%) | Contact: {contact}"
        dr = effective_dr(actor, damage_type="slashing")
        return f"Defense: DR {dr}% | Contact: {contact}"

    armor = getattr(actor, "armor", None)
    defense_points = getattr(armor, "defense_points", None)
    if defense_points is not None or (armor is not None and getattr(armor, "defense_percent", None) is None):
        if defense_points is None:
            defense = max(0, int(getattr(armor, "base_ac", 10) or 10))
        else:
            defense = max(0, int(defense_points))
        shield_points = 0
        support_points = 0
        for bonuses in (
            getattr(actor, "equipment_bonuses", {}) or {},
            getattr(actor, "gear_bonuses", {}) or {},
            getattr(actor, "relationship_bonuses", {}) or {},
        ):
            shield_points += int(bonuses.get("shield_defense_points", 0) or 0)
            support_points += int(bonuses.get("defense_points", 0) or 0)
        defense += shield_points or (1 if getattr(actor, "shield", False) else 0)
        defense += max(0, min(2, support_points))
        return f"Defense: {defense} (DR {base_damage_reduction_for_defense(defense):.1f}%) | Contact: {contact}"
    return f"Defense: {contact}"


def _character_armor_detail(actor) -> str:
    armor = getattr(actor, "armor", None)
    if armor is None:
        return ""
    dex_text = "full Dex" if getattr(armor, "dex_cap", None) is None else f"Dex cap +{armor.dex_cap}"
    return f"Armor: {getattr(armor, 'name', 'Armor')} | {dex_text}"


def character_examine_entry(actor, game=None) -> ExamineEntry:
    raw_name = str(getattr(actor, "name", "Unknown"))
    public_character_name = getattr(game, "public_character_name", None)
    public_name = str(public_character_name(raw_name) if callable(public_character_name) else raw_name)
    named_entry = named_character_examine_entry(public_name, game=game) or named_character_examine_entry(raw_name, game=game)
    description = (
        named_entry.description
        if named_entry is not None
        else _character_sheet_description(actor, public_name)
    )
    current_hp = int(getattr(actor, "current_hp", 0) or 0)
    max_hp = int(getattr(actor, "max_hp", 0) or 0)
    features = [feature_label(feature) for feature in list(getattr(actor, "features", []))[:6]]
    details = [
        f"Level {getattr(actor, 'level', '?')} {race_label(getattr(actor, 'race', ''))} {class_label(getattr(actor, 'class_name', ''))}".strip(),
        f"Background: {getattr(actor, 'background', 'Unknown')}",
        f"HP: {current_hp}/{max_hp} | {_character_defense_detail(actor, game=game)}",
    ]
    armor_detail = _character_armor_detail(actor)
    if armor_detail:
        details.append(armor_detail)
    if features:
        details.append(f"Features: {', '.join(features)}")
    conditions = getattr(actor, "conditions", {}) or {}
    active_conditions = [
        str(STATUS_DEFINITIONS.get(status, {}).get("name", status.replace("_", " ").title()))
        for status, value in conditions.items()
        if value
    ]
    if active_conditions:
        details.append(f"Conditions: {', '.join(active_conditions)}")
    return ExamineEntry(public_name, "Character", description, tuple(details))


def _option_tag_and_body(option: str) -> tuple[str | None, str]:
    plain = _plain_text(option)
    match = re.match(r"^\[([^\]]+)\]\s*(.*)$", plain)
    if match is None:
        return None, plain
    return match.group(1).strip(), match.group(2).strip()


def _entry_from_story_skill_tag(tag: str, body: str) -> ExamineEntry | None:
    skills = [part.strip().title() for part in re.split(r"/|,", tag) if part.strip()]
    matched = [skill for skill in SKILL_TO_ABILITY if skill.upper() in {candidate.upper() for candidate in skills}]
    if not matched:
        return None
    if len(matched) == 1:
        skill_entry = skill_examine_entry(matched[0])
        if skill_entry is None:
            return None
        details = (*skill_entry.details, f"Action: {body}" if body else "")
        return ExamineEntry(skill_entry.title, "Story Skill Check", skill_entry.description, tuple(detail for detail in details if detail))
    descriptions = []
    details = []
    for skill in matched:
        entry = skill_examine_entry(skill)
        if entry is None:
            continue
        descriptions.append(f"{entry.title}: {entry.description}")
        details.extend(entry.details)
    details.append(f"Action: {body}" if body else "")
    return ExamineEntry(
        " / ".join(matched),
        "Story Skill Check",
        "\n\n".join(descriptions),
        tuple(detail for detail in details if detail),
    )


def _entry_from_group_tag(tag: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(tag)
    if normalized not in GROUP_DESCRIPTIONS:
        return None
    return ExamineEntry(tag.title(), "Combat Option Group", GROUP_DESCRIPTIONS[normalized])


def _entry_from_action_label(label: str) -> ExamineEntry | None:
    normalized = _normalize_lookup_key(label)
    if normalized.startswith("strike with"):
        return ExamineEntry("Strike", "Combat Action", ACTION_DESCRIPTION_OVERRIDES["strike"], (label,))
    if normalized in ACTION_DESCRIPTION_OVERRIDES:
        return ExamineEntry(label, "Combat Action", ACTION_DESCRIPTION_OVERRIDES[normalized])
    return spell_examine_entry(label) or feature_examine_entry(label)


def examine_entry_for_text(text: str, *, game=None) -> ExamineEntry:
    tag, body = _option_tag_and_body(text)
    if tag:
        group_entry = _entry_from_group_tag(tag)
        if group_entry is not None:
            return group_entry
        skill_entry = _entry_from_story_skill_tag(tag, body)
        if skill_entry is not None:
            return skill_entry

    plain = body if tag else _plain_text(text)
    plain = re.sub(r"^\d+\.\s*", "", plain).strip()
    plain = re.sub(r"\s*\([^)]*\)\s*$", "", plain).strip()
    candidates = [plain]
    for separator in (":", " - ", " -- "):
        if separator in plain:
            candidates.append(plain.split(separator, 1)[0].strip())
    candidates = [candidate for index, candidate in enumerate(candidates) if candidate and candidate not in candidates[:index]]

    for candidate in candidates:
        game_term_entry = game_term_examine_entry(candidate, game=game)
        if game_term_entry is not None:
            return game_term_entry

        for builder in (
            ability_examine_entry,
            skill_examine_entry,
            spell_examine_entry,
            feature_examine_entry,
            resource_examine_entry,
            status_examine_entry,
            item_examine_entry,
            class_examine_entry,
            race_examine_entry,
            background_examine_entry,
        ):
            entry = builder(candidate)
            if entry is not None:
                return entry

        location_entry = location_examine_entry(candidate, game=game)
        if location_entry is not None:
            return location_entry

        character_entry = named_character_examine_entry(candidate, game=game)
        if character_entry is not None:
            return character_entry

        action_entry = _entry_from_action_label(candidate)
        if action_entry is not None:
            return action_entry

    description = "This highlighted term has no dedicated description in the current data files. It is available in the present scene or rules context."
    details = (f"Context text: {plain}",) if plain else ()
    return ExamineEntry(plain or "Examine", "Examine", description, details)
