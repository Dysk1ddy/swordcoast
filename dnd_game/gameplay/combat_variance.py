from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
import random
import re
from typing import Callable, Iterable

from ..content import build_character, create_enemy
from ..game import TextDnDGame
from ..models import GameState


_DICE_RE = re.compile(r"\s*(?P<count>\d*)d(?P<sides>\d+)(?P<modifier>[+-]\d+)?\s*")
DEFAULT_VARIANCE_SEEDS = tuple(range(1001, 1101))


@dataclass(frozen=True, slots=True)
class ActionSample:
    damage: int
    critical: bool = False
    result_kind: str = "wound"

    @property
    def zero_result(self) -> bool:
        return self.damage <= 0 and self.result_kind in {"miss", "cooldown"}


@dataclass(frozen=True, slots=True)
class ActionVarianceProfile:
    name: str
    sample_count: int
    mean_damage: float
    standard_deviation: float
    coefficient_of_variation: float
    zero_result_chance: float
    p10_damage: int
    p50_damage: int
    p90_damage: int
    critical_chance: float
    critical_damage_share: float


@dataclass(frozen=True, slots=True)
class EncounterVarianceProfile:
    name: str
    seed_count: int
    victory_rate: float
    rounds_p10: int
    rounds_p50: int
    rounds_p90: int
    downed_allies_mean: float
    downed_allies_p90: int


@dataclass(frozen=True, slots=True)
class CombatVarianceReport:
    action_profiles: tuple[ActionVarianceProfile, ...]
    encounter_profiles: tuple[EncounterVarianceProfile, ...]


def _roll_expression(rng: random.Random, expression: str, *, critical: bool = False) -> int:
    match = _DICE_RE.fullmatch(expression)
    if match is None:
        raise ValueError(f"Unsupported dice expression: {expression}")
    count = int(match.group("count") or "1")
    if critical:
        count *= 2
    sides = int(match.group("sides"))
    modifier = int(match.group("modifier") or "0")
    return sum(rng.randint(1, sides) for _ in range(count)) + modifier


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile)
    return ordered[max(0, min(len(ordered) - 1, index))]


def summarize_action_samples(name: str, samples: Iterable[ActionSample]) -> ActionVarianceProfile:
    sample_list = tuple(samples)
    damages = [sample.damage for sample in sample_list]
    total_damage = sum(damages)
    count = len(sample_list)
    mean = total_damage / count if count else 0.0
    variance = sum((damage - mean) ** 2 for damage in damages) / count if count else 0.0
    standard_deviation = sqrt(variance)
    critical_damage = sum(sample.damage for sample in sample_list if sample.critical)
    return ActionVarianceProfile(
        name=name,
        sample_count=count,
        mean_damage=mean,
        standard_deviation=standard_deviation,
        coefficient_of_variation=standard_deviation / mean if mean else 0.0,
        zero_result_chance=sum(1 for sample in sample_list if sample.zero_result) / count if count else 0.0,
        p10_damage=_percentile(damages, 0.10),
        p50_damage=_percentile(damages, 0.50),
        p90_damage=_percentile(damages, 0.90),
        critical_chance=sum(1 for sample in sample_list if sample.critical) / count if count else 0.0,
        critical_damage_share=critical_damage / total_damage if total_damage > 0 else 0.0,
    )


def _damage_after_defense(game: TextDnDGame, attacker, target, raw_damage: int, damage_type: str) -> int:
    damage = max(0, raw_damage)
    if not game.damage_type_uses_defense(damage_type):
        return damage
    defense = game.effective_defense_percent(
        target,
        damage_type=damage_type,
        armor_break_percent=game.total_armor_break_percent(target, source_actor=attacker),
    )
    return max(0, damage * (100 - defense) // 100)


def _near_miss_pressure(game: TextDnDGame, attacker, target, total: int, target_number: int) -> bool:
    return False


def simulate_weapon_action_once(game: TextDnDGame, attacker, target, rng: random.Random) -> ActionSample:
    target_number = game.effective_attack_target_number(target)
    accuracy = (
        attacker.attack_bonus()
        + game.ally_pressure_bonus(attacker, [attacker], ranged=attacker.weapon.ranged)
        + game.status_accuracy_modifier(attacker)
        + game.attack_focus_modifier(attacker, target)
        + game.weapon_master_style_accuracy_modifier(attacker, target)
        + game.assassin_accuracy_modifier(attacker, target, [attacker])
        + game.target_accuracy_modifier(target)
    )
    roll = rng.randint(1, 20)
    total = roll + accuracy
    critical = roll >= game.critical_threshold(attacker)
    if roll == 1 or (not critical and total < target_number):
        return ActionSample(
            0,
            critical=False,
            result_kind="pressure" if roll != 1 and _near_miss_pressure(game, attacker, target, total, target_number) else "miss",
        )
    weapon_item = game.equipped_weapon_item(attacker)
    damage_type = weapon_item.damage_type if weapon_item is not None else ""
    raw_damage = _roll_expression(rng, attacker.weapon.damage, critical=critical) + attacker.damage_bonus() + game.status_damage_modifier(attacker)
    if getattr(attacker, "class_name", "") == "Rogue" and game.can_sneak_attack(attacker, [attacker], target):
        raw_damage += _roll_expression(rng, game.rogue_sneak_attack_dice(attacker), critical=critical)
    damage = _damage_after_defense(game, attacker, target, max(1, raw_damage), damage_type)
    cap_getter = getattr(game, "enemy_critical_hp_damage_cap", None)
    if callable(cap_getter):
        cap = cap_getter(attacker, target, critical_hit=critical)
        if cap is not None:
            damage = min(damage, cap)
    return ActionSample(damage, critical=critical, result_kind="wound" if damage > 0 else "glance")


def simulate_arcane_bolt_once(game: TextDnDGame, actor, target, rng: random.Random, *, action_cast: bool = False) -> ActionSample:
    target_number = game.effective_attack_target_number(target)
    accuracy = (
        game.spell_attack_bonus(actor, "INT")
        + game.ally_pressure_bonus(actor, [actor], ranged=True)
        + game.status_accuracy_modifier(actor)
        + game.attack_focus_modifier(actor, target)
        + game.target_accuracy_modifier(target)
    )
    roll = rng.randint(1, 20)
    total = roll + accuracy
    critical = roll >= game.critical_threshold(actor)
    if roll == 1 or (not critical and total < target_number):
        return ActionSample(
            0,
            critical=False,
            result_kind="pressure" if roll != 1 and _near_miss_pressure(game, actor, target, total, target_number) else "miss",
        )
    damage_bonus = max(0, actor.ability_mod("INT")) + game.spell_damage_bonus(actor)
    multiplier = 2 if action_cast else 1
    damage = max(1, (_roll_expression(rng, game.arcane_bolt_damage_expression(actor), critical=critical) + damage_bonus) * multiplier)
    return ActionSample(damage, critical=critical, result_kind="wound")


def action_profile_for_weapon(
    name: str,
    game: TextDnDGame,
    attacker,
    target_factory: Callable[[], object],
    seeds: Iterable[int] = DEFAULT_VARIANCE_SEEDS,
) -> ActionVarianceProfile:
    samples = [
        simulate_weapon_action_once(game, attacker, target_factory(), random.Random(seed))
        for seed in seeds
    ]
    return summarize_action_samples(name, samples)


def action_profile_for_arcane_bolt(
    name: str,
    game: TextDnDGame,
    actor,
    target_factory: Callable[[], object],
    seeds: Iterable[int] = DEFAULT_VARIANCE_SEEDS,
    *,
    action_cast: bool = False,
    include_cooldown_turns: bool = True,
) -> ActionVarianceProfile:
    samples: list[ActionSample] = []
    for seed in seeds:
        samples.append(simulate_arcane_bolt_once(game, actor, target_factory(), random.Random(seed), action_cast=action_cast))
        if include_cooldown_turns:
            for _ in range(max(0, game.arcane_bolt_cooldown_duration() - 1)):
                samples.append(ActionSample(0, result_kind="cooldown"))
    return summarize_action_samples(name, samples)


def build_level_four_mixed_party(seed: int = 49217) -> tuple[TextDnDGame, list[object]]:
    warrior = build_character(
        name="Vale",
        race="Human",
        class_name="Warrior",
        background="Soldier",
        base_ability_scores={"STR": 15, "DEX": 12, "CON": 14, "INT": 8, "WIS": 12, "CHA": 10},
        class_skill_choices=["Athletics", "Survival"],
    )
    rogue = build_character(
        name="Kael",
        race="Human",
        class_name="Rogue",
        background="Criminal",
        base_ability_scores={"STR": 10, "DEX": 16, "CON": 13, "INT": 12, "WIS": 10, "CHA": 12},
        class_skill_choices=["Stealth", "Sleight of Hand"],
    )
    mage = build_character(
        name="Mira",
        race="Human",
        class_name="Mage",
        background="Sage",
        base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 10},
        class_skill_choices=["Arcana", "Insight"],
    )
    game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(seed))
    party = [warrior, rogue, mage]
    game.state = GameState(player=warrior, companions=[rogue, mage], current_scene="variance_report")
    game._in_combat = True
    game._active_round_number = 1
    game._active_combat_heroes = party
    game.karmic_dice_enabled = True
    for member in party:
        for level in (2, 3, 4):
            game.level_up_character_automatically(member, level, announce=False)
        game.prepare_class_resources_for_combat(member)
    return game, party


def _apply_sample_damage(target, sample: ActionSample) -> None:
    if sample.damage <= 0:
        return
    target.current_hp = max(0, target.current_hp - sample.damage)
    if target.current_hp <= 0 and "enemy" in getattr(target, "tags", []):
        target.dead = True


def _apply_pressure_statuses(target, sample: ActionSample) -> None:
    return


def simulate_simple_encounter_once(enemy_factories: tuple[Callable[[], object], ...], seed: int, *, max_rounds: int = 12) -> tuple[bool, int, int]:
    game, party = build_level_four_mixed_party(seed)
    enemies = [factory() for factory in enemy_factories]
    game._active_combat_enemies = enemies
    rng = random.Random(seed)
    downed_names: set[str] = set()
    round_number = 0
    mage_cooldowns: dict[str, int] = {}
    while round_number < max_rounds and any(enemy.is_conscious() for enemy in enemies) and any(member.is_conscious() for member in party):
        round_number += 1
        game._active_round_number = round_number
        for actor in party:
            if not actor.is_conscious() or not any(enemy.is_conscious() for enemy in enemies):
                continue
            target = min((enemy for enemy in enemies if enemy.is_conscious()), key=lambda enemy: enemy.current_hp)
            cooldown = max(0, mage_cooldowns.get(actor.name, 0))
            if getattr(actor, "class_name", "") == "Mage" and cooldown <= 0:
                sample = simulate_arcane_bolt_once(game, actor, target, rng, action_cast=False)
                mage_cooldowns[actor.name] = game.arcane_bolt_cooldown_duration() - 1
            else:
                sample = simulate_weapon_action_once(game, actor, target, rng)
                if cooldown > 0:
                    mage_cooldowns[actor.name] = cooldown - 1
            _apply_pressure_statuses(target, sample)
            _apply_sample_damage(target, sample)
        for enemy in enemies:
            if not enemy.is_conscious() or not any(member.is_conscious() for member in party):
                continue
            target = game.choose_weighted_enemy_target(enemy, [member for member in party if member.is_conscious()])
            game.record_enemy_target_choice(enemy, target)
            sample = simulate_weapon_action_once(game, enemy, target, rng)
            _apply_pressure_statuses(target, sample)
            _apply_sample_damage(target, sample)
            if target.current_hp <= 0:
                downed_names.add(target.name)
    return not any(enemy.is_conscious() for enemy in enemies), max(1, round_number), len(downed_names)


def encounter_variance_profile(
    name: str,
    enemy_factories: tuple[Callable[[], object], ...],
    seeds: Iterable[int] = DEFAULT_VARIANCE_SEEDS,
) -> EncounterVarianceProfile:
    outcomes = [simulate_simple_encounter_once(enemy_factories, seed) for seed in seeds]
    victories = [victory for victory, _, _ in outcomes]
    rounds = [round_count for _, round_count, _ in outcomes]
    downed = [downed_count for _, _, downed_count in outcomes]
    count = len(outcomes)
    return EncounterVarianceProfile(
        name=name,
        seed_count=count,
        victory_rate=sum(1 for victory in victories if victory) / count if count else 0.0,
        rounds_p10=_percentile(rounds, 0.10),
        rounds_p50=_percentile(rounds, 0.50),
        rounds_p90=_percentile(rounds, 0.90),
        downed_allies_mean=sum(downed) / count if count else 0.0,
        downed_allies_p90=_percentile(downed, 0.90),
    )


def build_default_variance_report(seeds: Iterable[int] = DEFAULT_VARIANCE_SEEDS) -> CombatVarianceReport:
    seed_tuple = tuple(seeds)
    warrior_game, warrior_party = build_level_four_mixed_party(seed_tuple[0] if seed_tuple else 1001)
    warrior = warrior_party[0]
    warrior_game.state.companions = []
    warrior_game._active_combat_heroes = [warrior]

    mage_game, party = build_level_four_mixed_party((seed_tuple[0] if seed_tuple else 1001) + 1)
    mage = next(member for member in party if getattr(member, "class_name", "") == "Mage")

    action_profiles = (
        action_profile_for_weapon("L4 Warrior weapon vs bandit", warrior_game, warrior, lambda: create_enemy("bandit"), seed_tuple),
        action_profile_for_weapon("L4 Warrior weapon vs false_map_skirmisher", warrior_game, warrior, lambda: create_enemy("false_map_skirmisher"), seed_tuple),
        action_profile_for_weapon("L4 Warrior weapon vs animated_armor", warrior_game, warrior, lambda: create_enemy("animated_armor"), seed_tuple),
        action_profile_for_arcane_bolt("L4 Mage Arcane Bolt bonus cycle vs bandit", mage_game, mage, lambda: create_enemy("bandit"), seed_tuple),
    )
    encounter_profiles = (
        encounter_variance_profile(
            "basic raiders",
            (lambda: create_enemy("bandit"), lambda: create_enemy("bandit_archer"), lambda: create_enemy("goblin_skirmisher")),
            seed_tuple,
        ),
        encounter_variance_profile(
            "high defense brutes",
            (lambda: create_enemy("animated_armor"), lambda: create_enemy("blacklake_pincerling")),
            seed_tuple,
        ),
        encounter_variance_profile(
            "sereth group",
            (lambda: create_enemy("sereth_vane"), lambda: create_enemy("bandit"), lambda: create_enemy("bandit_archer")),
            seed_tuple,
        ),
    )
    return CombatVarianceReport(action_profiles=action_profiles, encounter_profiles=encounter_profiles)
