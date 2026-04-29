from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from ..data.items.catalog import ITEMS, item_category_label, item_rules_text, item_type_label
from ..data.story.character_options.backgrounds import BACKGROUNDS
from ..data.story.character_options.classes import CLASSES, CLASS_LEVEL_PROGRESSION
from ..data.story.character_options.races import RACES
from ..data.story.lore import ABILITY_LORE, BACKGROUND_LORE, CLASS_LORE, FEATURE_LORE, RACE_LORE, SKILL_LORE
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
        ("save_bonus", "Resist bonus"),
        ("save_penalty", "Resist penalty"),
        ("ac_bonus", "Defense bonus"),
        ("ac_penalty", "Defense penalty"),
        ("defense_bonus_percent", "Defense shift"),
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
    description = "A tracked combat condition. Its modifiers apply while the condition remains on the character."
    if details:
        description = "This condition changes combat math while it lasts."
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


def character_examine_entry(actor, game=None) -> ExamineEntry:
    raw_name = str(getattr(actor, "name", "Unknown"))
    public_character_name = getattr(game, "public_character_name", None)
    public_name = str(public_character_name(raw_name) if callable(public_character_name) else raw_name)
    named_entry = named_character_examine_entry(public_name, game=game) or named_character_examine_entry(raw_name, game=game)
    description = (
        named_entry.description
        if named_entry is not None
        else "A combatant or party member currently present in the game state."
    )
    current_hp = int(getattr(actor, "current_hp", 0) or 0)
    max_hp = int(getattr(actor, "max_hp", 0) or 0)
    features = [feature_label(feature) for feature in list(getattr(actor, "features", []))[:6]]
    details = [
        f"Level {getattr(actor, 'level', '?')} {race_label(getattr(actor, 'race', ''))} {class_label(getattr(actor, 'class_name', ''))}".strip(),
        f"HP: {current_hp}/{max_hp} | Defense: {getattr(actor, 'armor_class', '?')}",
    ]
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

        character_entry = named_character_examine_entry(candidate, game=game)
        if character_entry is not None:
            return character_entry

        action_entry = _entry_from_action_label(candidate)
        if action_entry is not None:
            return action_entry

    description = "This highlighted term has no dedicated description in the current data files. It is available in the present scene or rules context."
    details = (f"Context text: {plain}",) if plain else ()
    return ExamineEntry(plain or "Examine", "Examine", description, details)
