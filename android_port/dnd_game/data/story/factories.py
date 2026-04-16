from __future__ import annotations

from dataclasses import replace

from ...dice import ability_modifier
from ...models import Armor, Character, Weapon
from .companions import apply_companion_profile
from .options import BACKGROUNDS, CLASSES, RACES


def apply_racial_bonuses(race: str, ability_scores: dict[str, int]) -> dict[str, int]:
    result = dict(ability_scores)
    for ability, bonus in RACES[race]["bonuses"].items():
        result[ability] = result.get(ability, 0) + bonus
    return result

def build_character(
    *,
    name: str,
    race: str,
    class_name: str,
    background: str,
    base_ability_scores: dict[str, int],
    class_skill_choices: list[str],
    expertise_choices: list[str] | None = None,
    notes: list[str] | None = None,
    inventory: dict[str, int] | None = None,
    tags: list[str] | None = None,
) -> Character:
    class_data = CLASSES[class_name]
    background_data = BACKGROUNDS[background]
    race_data = RACES[race]
    final_scores = apply_racial_bonuses(race, base_ability_scores)
    skills = sorted(set(background_data["skills"] + race_data["skills"] + class_skill_choices))
    expertise = sorted(set(expertise_choices or []))
    features = sorted(set(class_data["features"] + race_data["features"]))
    hp = max(1, class_data["hit_die"] + ability_modifier(final_scores["CON"]))
    merged_notes = [*background_data["notes"], *(notes or [])]
    return Character(
        name=name,
        race=race,
        class_name=class_name,
        background=background,
        level=1,
        ability_scores=final_scores,
        skill_proficiencies=skills,
        saving_throw_proficiencies=list(class_data["saving_throws"]),
        features=features,
        weapon=replace(class_data["weapon"]),
        armor=replace(class_data["armor"]) if class_data["armor"] is not None else None,
        hit_die=class_data["hit_die"],
        current_hp=hp,
        max_hp=hp,
        shield=class_data["shield"],
        spellcasting_ability=class_data["spellcasting_ability"],
        skill_expertise=expertise,
        bonus_proficiencies=list(background_data.get("proficiencies", [])),
        resources=dict(class_data["resources"]),
        max_resources=dict(class_data["resources"]),
        inventory={"Healing Potion": 1, **(inventory or {})},
        equipment_bonuses=dict(background_data["equipment_bonuses"]),
        notes=merged_notes,
        tags=list(tags or ["hero"]),
        archetype=class_name.lower(),
    )


def create_tolan_ironshield() -> Character:
    return apply_companion_profile(build_character(
        name="Tolan Ironshield",
        race="Dwarf",
        class_name="Fighter",
        background="Soldier",
        base_ability_scores={"STR": 15, "DEX": 10, "CON": 14, "INT": 8, "WIS": 12, "CHA": 13},
        class_skill_choices=["Perception", "Survival"],
        notes=["A caravan guard from Neverwinter with a shield wall mindset."],
        inventory={"Healing Potion": 1},
        tags=["hero", "companion"],
    ), "tolan_ironshield")


def create_bryn_underbough() -> Character:
    character = build_character(
        name="Bryn Underbough",
        race="Halfling",
        class_name="Rogue",
        background="Criminal",
        base_ability_scores={"STR": 8, "DEX": 15, "CON": 12, "INT": 13, "WIS": 14, "CHA": 10},
        class_skill_choices=["Acrobatics", "Insight", "Perception", "Sleight of Hand"],
        expertise_choices=["Stealth", "Perception"],
        notes=["A caravan scout who knows every shortcut between Phandalin and Neverwinter."],
        inventory={"Healing Potion": 1},
        tags=["hero", "companion"],
    )
    character.weapon = Weapon(name="Shortsword", damage="1d6", ability="FINESSE", finesse=True)
    return apply_companion_profile(character, "bryn_underbough")


def create_elira_dawnmantle() -> Character:
    return apply_companion_profile(build_character(
        name="Elira Dawnmantle",
        race="Human",
        class_name="Cleric",
        background="Acolyte",
        base_ability_scores={"STR": 10, "DEX": 12, "CON": 13, "INT": 10, "WIS": 15, "CHA": 14},
        class_skill_choices=["Medicine", "Persuasion"],
        notes=["A priestess of Tymora tending the frontier faithful in Phandalin."],
        inventory={"Healing Potion": 1},
        tags=["hero", "companion"],
    ), "elira_dawnmantle")


def create_kaelis_starling() -> Character:
    return apply_companion_profile(build_character(
        name="Kaelis Starling",
        race="Half-Elf",
        class_name="Ranger",
        background="Criminal",
        base_ability_scores={"STR": 10, "DEX": 15, "CON": 13, "INT": 11, "WIS": 14, "CHA": 12},
        class_skill_choices=["Perception", "Stealth", "Survival"],
        notes=["A Neverwinter scout who knows how to read an ambush before it closes."],
        inventory={"Healing Potion": 1},
        tags=["hero", "companion"],
    ), "kaelis_starling")


def create_rhogar_valeguard() -> Character:
    return apply_companion_profile(build_character(
        name="Rhogar Valeguard",
        race="Dragonborn",
        class_name="Paladin",
        background="Soldier",
        base_ability_scores={"STR": 15, "DEX": 10, "CON": 13, "INT": 8, "WIS": 12, "CHA": 14},
        class_skill_choices=["Athletics", "Persuasion"],
        notes=["A dragonborn sworn to protect caravans on the road south of Neverwinter."],
        inventory={"Healing Potion": 1},
        tags=["hero", "companion"],
    ), "rhogar_valeguard")


def create_enemy(template: str, *, name: str | None = None) -> Character:
    templates = {
        "goblin_skirmisher": Character(
            name="Goblin Skirmisher",
            race="Goblin",
            class_name="Skirmisher",
            background="",
            level=1,
            ability_scores={"STR": 8, "DEX": 14, "CON": 10, "INT": 10, "WIS": 8, "CHA": 8},
            skill_proficiencies=["Stealth"],
            saving_throw_proficiencies=[],
            features=["nimble"],
            weapon=Weapon(name="Scimitar", damage="1d4+1", ability="FINESSE", finesse=True),
            armor=Armor(name="Leather Armor", base_ac=11),
            hit_die=6,
            current_hp=6,
            max_hp=6,
            shield=False,
            inventory={},
            tags=["enemy", "cowardly"],
            archetype="goblin",
            xp_value=50,
            gold_value=4,
        ),
        "wolf": Character(
            name="Ash Wolf",
            race="Beast",
            class_name="Hunter",
            background="",
            level=1,
            ability_scores={"STR": 12, "DEX": 15, "CON": 12, "INT": 3, "WIS": 12, "CHA": 6},
            skill_proficiencies=["Perception", "Stealth"],
            saving_throw_proficiencies=[],
            features=["pack_tactics"],
            weapon=Weapon(name="Bite", damage="1d6+1", ability="STR"),
            armor=Armor(name="Natural Hide", base_ac=13, dex_cap=0),
            hit_die=8,
            current_hp=11,
            max_hp=11,
            shield=False,
            inventory={},
            tags=["enemy", "beast"],
            archetype="wolf",
            xp_value=50,
            gold_value=6,
        ),
        "bandit": Character(
            name="Ashen Brand Bandit",
            race="Human",
            class_name="Bandit",
            background="",
            level=1,
            ability_scores={"STR": 11, "DEX": 12, "CON": 12, "INT": 10, "WIS": 10, "CHA": 10},
            skill_proficiencies=["Intimidation"],
            saving_throw_proficiencies=[],
            features=[],
            weapon=Weapon(name="Scimitar", damage="1d6", ability="FINESSE", finesse=True),
            armor=Armor(name="Leather Armor", base_ac=11),
            hit_die=8,
            current_hp=11,
            max_hp=11,
            shield=False,
            inventory={},
            tags=["enemy", "humanoid", "parley"],
            archetype="bandit",
            xp_value=50,
            gold_value=8,
        ),
        "bandit_archer": Character(
            name="Ashen Brand Lookout",
            race="Human",
            class_name="Lookout",
            background="",
            level=1,
            ability_scores={"STR": 9, "DEX": 13, "CON": 11, "INT": 10, "WIS": 12, "CHA": 9},
            skill_proficiencies=["Perception"],
            saving_throw_proficiencies=[],
            features=[],
            weapon=Weapon(name="Shortbow", damage="1d6", ability="DEX", ranged=True),
            armor=Armor(name="Leather Armor", base_ac=11),
            hit_die=8,
            current_hp=9,
            max_hp=9,
            shield=False,
            inventory={},
            tags=["enemy", "humanoid", "parley"],
            archetype="bandit_archer",
            xp_value=50,
            gold_value=9,
        ),
        "rukhar": Character(
            name="Rukhar Cinderfang",
            race="Hobgoblin",
            class_name="Sergeant",
            background="",
            level=2,
            ability_scores={"STR": 14, "DEX": 12, "CON": 12, "INT": 10, "WIS": 10, "CHA": 11},
            skill_proficiencies=["Athletics", "Intimidation"],
            saving_throw_proficiencies=["STR", "CON"],
            features=["martial_advantage", "cinder_poison"],
            weapon=Weapon(name="Longsword", damage="1d8", ability="STR"),
            armor=Armor(name="Chain Shirt", base_ac=13, dex_cap=2),
            hit_die=10,
            current_hp=27,
            max_hp=27,
            shield=True,
            inventory={},
            tags=["enemy", "humanoid", "leader", "parley"],
            archetype="rukhar",
            xp_value=125,
            gold_value=35,
        ),
        "varyn": Character(
            name="Varyn Sable",
            race="Human",
            class_name="Captain",
            background="",
            level=2,
            ability_scores={"STR": 12, "DEX": 15, "CON": 14, "INT": 12, "WIS": 11, "CHA": 14},
            skill_proficiencies=["Deception", "Intimidation", "Persuasion"],
            saving_throw_proficiencies=["DEX", "WIS"],
            features=["ashen_poison", "rally"],
            weapon=Weapon(name="Blackened Rapier", damage="1d8", ability="FINESSE", finesse=True, to_hit_bonus=1),
            armor=Armor(name="Studded Leather", base_ac=12),
            hit_die=10,
            current_hp=38,
            max_hp=38,
            shield=False,
            inventory={},
            tags=["enemy", "humanoid", "leader", "parley"],
            archetype="varyn",
            xp_value=200,
            gold_value=60,
        ),
    }
    template_character = templates[template]
    enemy = Character.from_dict(template_character.to_dict())
    if name is not None:
        enemy.name = name
    return enemy
