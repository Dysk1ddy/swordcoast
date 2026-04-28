from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from math import ceil, inf
import re

from .magic_points import magic_point_cost, spend_magic_points


_DICE_RE = re.compile(r"\s*(?P<count>\d*)d(?P<sides>\d+)(?P<modifier>[+-]\d+)?\s*")
_ACTION_SPELL_IDS = {
    "Minor Channel": "minor_channel",
    "Arc Pulse": "arc_pulse",
    "Ember Lance": "ember_lance",
    "Frost Shard": "frost_shard",
    "Volt Grasp": "volt_grasp",
    "Blue Glass Palm": "blue_glass_palm",
    "Action: Arcane Bolt": "arcane_bolt",
    "Bonus: Arcane Bolt": "arcane_bolt",
}


@dataclass(frozen=True, slots=True)
class AttackRollSimulation:
    target_number: int
    accuracy_bonus: int
    required_roll: int
    advantage_state: int
    miss_chance: float
    normal_hit_chance: float
    critical_chance: float

    @property
    def hit_chance(self) -> float:
        return self.normal_hit_chance + self.critical_chance


@dataclass(frozen=True, slots=True)
class DamageSimulation:
    defense_percent: int
    armor_break_percent: int
    expected_hp_damage_on_normal_hit: float
    expected_hp_damage_on_critical_hit: float
    glance_chance_on_normal_hit: float
    glance_chance_on_critical_hit: float
    wound_chance_on_normal_hit: float
    wound_chance_on_critical_hit: float


@dataclass(frozen=True, slots=True)
class WeaponAttackSimulation:
    attack_roll: AttackRollSimulation
    damage: DamageSimulation

    @property
    def target_number(self) -> int:
        return self.attack_roll.target_number

    @property
    def accuracy_bonus(self) -> int:
        return self.attack_roll.accuracy_bonus

    @property
    def hit_chance(self) -> float:
        return self.attack_roll.hit_chance

    @property
    def miss_chance(self) -> float:
        return self.attack_roll.miss_chance

    @property
    def normal_hit_chance(self) -> float:
        return self.attack_roll.normal_hit_chance

    @property
    def critical_chance(self) -> float:
        return self.attack_roll.critical_chance

    @property
    def expected_hp_damage(self) -> float:
        return (
            self.normal_hit_chance * self.damage.expected_hp_damage_on_normal_hit
            + self.critical_chance * self.damage.expected_hp_damage_on_critical_hit
        )

    @property
    def glance_chance(self) -> float:
        return (
            self.normal_hit_chance * self.damage.glance_chance_on_normal_hit
            + self.critical_chance * self.damage.glance_chance_on_critical_hit
        )

    @property
    def wound_chance(self) -> float:
        return (
            self.normal_hit_chance * self.damage.wound_chance_on_normal_hit
            + self.critical_chance * self.damage.wound_chance_on_critical_hit
        )


@dataclass(frozen=True, slots=True)
class OffensiveActionSimulation:
    actor_name: str
    target_name: str
    action_name: str
    expected_hp_damage: float
    hit_chance: float | None = None
    miss_chance: float | None = None
    save_success_chance: float | None = None
    wound_chance: float = 0.0
    defense_percent: int = 0
    armor_break_percent: int = 0


@dataclass(frozen=True, slots=True)
class EncounterPassSimulation:
    name: str
    party_actions: tuple[OffensiveActionSimulation, ...]
    enemy_actions: tuple[OffensiveActionSimulation, ...]
    party_names: tuple[str, ...]
    enemy_names: tuple[str, ...]
    party_hp: int
    enemy_hp: int
    max_enemy_defense_percent: int
    max_enemy_avoidance: int

    @property
    def party_expected_damage_per_round(self) -> float:
        return sum(action.expected_hp_damage for action in self.party_actions)

    @property
    def enemy_expected_damage_per_round(self) -> float:
        return sum(action.expected_hp_damage for action in self.enemy_actions)

    @property
    def rounds_to_clear(self) -> float:
        if self.party_expected_damage_per_round <= 0:
            return inf
        return self.enemy_hp / self.party_expected_damage_per_round

    @property
    def rounds_to_party_defeat(self) -> float:
        if self.enemy_expected_damage_per_round <= 0:
            return inf
        return self.party_hp / self.enemy_expected_damage_per_round

    @property
    def survival_margin_rounds(self) -> float:
        return self.rounds_to_party_defeat - self.rounds_to_clear


@dataclass(frozen=True, slots=True)
class RouteChainEncounterSpec:
    name: str
    enemies: tuple
    wave_group: str | None = None
    party_armor_break_percent: int = 0


@dataclass(frozen=True, slots=True)
class RouteChainStepSimulation:
    name: str
    wave_index: int
    wave_group: str | None
    encounter: EncounterPassSimulation
    resource_snapshot_before: dict[str, object]
    resource_snapshot_after_encounter: dict[str, object]
    resource_snapshot_after_rest: dict[str, object]
    rest_decision: str
    simulated_rounds: int
    expected_party_damage_applied: int


@dataclass(frozen=True, slots=True)
class RouteChainSimulation:
    name: str
    steps: tuple[RouteChainStepSimulation, ...]

    @property
    def final_snapshot(self) -> dict[str, object]:
        if not self.steps:
            return {}
        return self.steps[-1].resource_snapshot_after_rest

    @property
    def rest_decisions(self) -> tuple[str, ...]:
        return tuple(step.rest_decision for step in self.steps)

    @property
    def short_rest_count(self) -> int:
        return self.rest_decisions.count("short_rest")

    @property
    def long_rest_count(self) -> int:
        return self.rest_decisions.count("long_rest")

    @property
    def blocked_rest_count(self) -> int:
        return self.rest_decisions.count("long_rest_blocked")

    @property
    def deferred_wave_count(self) -> int:
        return self.rest_decisions.count("deferred_wave")

    @property
    def minimum_survival_margin_rounds(self) -> float:
        if not self.steps:
            return inf
        return min(step.encounter.survival_margin_rounds for step in self.steps)

    @property
    def total_expected_party_damage_applied(self) -> int:
        return sum(step.expected_party_damage_applied for step in self.steps)


def d20_kept_distribution(*, advantage_state: int = 0, lucky: bool = False) -> dict[int, float]:
    roll_count = 2 if advantage_state else 1
    totals: dict[int, float] = defaultdict(float)
    raw_weight = 1 / (20**roll_count)
    for raw_rolls in product(range(1, 21), repeat=roll_count):
        processed_options: list[list[tuple[int, float]]] = []
        for raw in raw_rolls:
            if lucky and raw == 1:
                processed_options.append([(reroll, 1 / 20) for reroll in range(1, 21)])
            else:
                processed_options.append([(raw, 1.0)])
        for processed_rolls in product(*processed_options):
            rolls = [value for value, _ in processed_rolls]
            chance = raw_weight
            for _, option_weight in processed_rolls:
                chance *= option_weight
            if advantage_state > 0:
                kept = max(rolls)
            elif advantage_state < 0:
                kept = min(rolls)
            else:
                kept = rolls[0]
            totals[kept] += chance
    return dict(totals)


def simulate_attack_roll(
    *,
    target_number: int,
    accuracy_bonus: int,
    advantage_state: int = 0,
    critical_threshold: int = 20,
    lucky: bool = False,
    critical_immunity: bool = False,
) -> AttackRollSimulation:
    miss = 0.0
    normal = 0.0
    critical = 0.0
    for kept, chance in d20_kept_distribution(advantage_state=advantage_state, lucky=lucky).items():
        if kept == 1:
            miss += chance
            continue
        is_critical = kept >= critical_threshold and not critical_immunity
        if is_critical:
            critical += chance
            continue
        if kept + accuracy_bonus < target_number:
            miss += chance
        else:
            normal += chance
    required_roll = max(2, min(20, target_number - accuracy_bonus))
    return AttackRollSimulation(
        target_number=target_number,
        accuracy_bonus=accuracy_bonus,
        required_roll=required_roll,
        advantage_state=advantage_state,
        miss_chance=miss,
        normal_hit_chance=normal,
        critical_chance=critical,
    )


def dice_total_distribution(expression: str, *, critical: bool = False) -> dict[int, float]:
    match = _DICE_RE.fullmatch(expression)
    if match is None:
        raise ValueError(f"Unsupported dice expression: {expression}")
    count = int(match.group("count") or "1")
    sides = int(match.group("sides"))
    modifier = int(match.group("modifier") or "0")
    if critical:
        count *= 2
    totals: dict[int, int] = {0: 1}
    for _ in range(count):
        next_totals: dict[int, int] = defaultdict(int)
        for subtotal, ways in totals.items():
            for face in range(1, sides + 1):
                next_totals[subtotal + face] += ways
        totals = dict(next_totals)
    total_ways = sides**count
    return {total + modifier: ways / total_ways for total, ways in totals.items()}


def add_damage_bonus(distribution: dict[int, float], bonus: int) -> dict[int, float]:
    if bonus == 0:
        return dict(distribution)
    return {total + bonus: chance for total, chance in distribution.items()}


def multiply_damage_distribution(distribution: dict[int, float], multiplier: int) -> dict[int, float]:
    multiplier = max(1, int(multiplier))
    if multiplier == 1:
        return dict(distribution)
    return {total * multiplier: chance for total, chance in distribution.items()}


def half_damage_distribution(distribution: dict[int, float]) -> dict[int, float]:
    totals: dict[int, float] = defaultdict(float)
    for total, chance in distribution.items():
        totals[max(1, total // 2)] += chance
    return dict(totals)


def combine_damage_distributions(first: dict[int, float], second: dict[int, float]) -> dict[int, float]:
    totals: dict[int, float] = defaultdict(float)
    for left_total, left_chance in first.items():
        for right_total, right_chance in second.items():
            totals[left_total + right_total] += left_chance * right_chance
    return dict(totals)


def _resisted_damage(game, target, damage: int, damage_type: str) -> int:
    resisted = False
    if game.has_status(target, "petrified"):
        damage //= 2
    if damage_type == "poison" and "dwarven_resilience" in target.features:
        resisted = True
    if damage_type == "fire" and "hellish_resistance" in target.features:
        resisted = True
    if game.has_damage_resistance(target, damage_type):
        resisted = True
    if resisted:
        damage //= 2
    return damage


def simulate_damage_after_defense(
    game,
    target,
    damage_distribution: dict[int, float],
    *,
    damage_type: str = "",
    defense_percent: int = 0,
    apply_defense: bool = True,
    minimum_raw_damage: int = 1,
) -> tuple[float, float, float]:
    expected_hp_damage = 0.0
    glance_chance = 0.0
    wound_chance = 0.0
    for raw_total, chance in damage_distribution.items():
        raw_damage = max(minimum_raw_damage, raw_total)
        resisted_damage = _resisted_damage(game, target, raw_damage, damage_type)
        mitigated_damage = resisted_damage
        if apply_defense and game.damage_type_uses_defense(damage_type):
            mitigated_damage = mitigated_damage * (100 - defense_percent) // 100
        hp_damage = max(0, mitigated_damage)
        expected_hp_damage += hp_damage * chance
        if apply_defense and raw_damage > 0 and resisted_damage > 0 and mitigated_damage <= 0:
            glance_chance += chance
        if hp_damage > 0:
            wound_chance += chance
    return expected_hp_damage, glance_chance, wound_chance


def simulate_weapon_damage(
    game,
    attacker,
    target,
    *,
    damage_type: str = "",
    armor_break_percent: int = 0,
    armor_break: int = 0,
    extra_damage: str | None = None,
) -> DamageSimulation:
    total_armor_break = game.total_armor_break_percent(
        target,
        source_actor=attacker,
        incoming_percent=armor_break_percent,
        incoming_steps=armor_break,
    )
    defense_percent = game.effective_defense_percent(
        target,
        damage_type=damage_type,
        armor_break_percent=total_armor_break,
    )
    damage_bonus = attacker.damage_bonus() + game.status_damage_modifier(attacker)
    normal_distribution = add_damage_bonus(dice_total_distribution(attacker.weapon.damage), damage_bonus)
    critical_distribution = add_damage_bonus(dice_total_distribution(attacker.weapon.damage, critical=True), damage_bonus)
    if extra_damage:
        normal_distribution = combine_damage_distributions(
            normal_distribution,
            dice_total_distribution(extra_damage),
        )
        critical_distribution = combine_damage_distributions(
            critical_distribution,
            dice_total_distribution(extra_damage, critical=True),
        )
    normal_expected, normal_glance, normal_wound = simulate_damage_after_defense(
        game,
        target,
        normal_distribution,
        damage_type=damage_type,
        defense_percent=defense_percent,
    )
    critical_expected, critical_glance, critical_wound = simulate_damage_after_defense(
        game,
        target,
        critical_distribution,
        damage_type=damage_type,
        defense_percent=defense_percent,
    )
    return DamageSimulation(
        defense_percent=defense_percent,
        armor_break_percent=total_armor_break,
        expected_hp_damage_on_normal_hit=normal_expected,
        expected_hp_damage_on_critical_hit=critical_expected,
        glance_chance_on_normal_hit=normal_glance,
        glance_chance_on_critical_hit=critical_glance,
        wound_chance_on_normal_hit=normal_wound,
        wound_chance_on_critical_hit=critical_wound,
    )


def simulate_weapon_attack(
    game,
    attacker,
    target,
    *,
    heroes: list | None = None,
    enemies: list | None = None,
    dodging: set[str] | frozenset[str] | None = None,
    advantage_state: int | None = None,
    damage_type: str | None = None,
    armor_break_percent: int = 0,
    armor_break: int = 0,
    attacker_allies: list | None = None,
) -> WeaponAttackSimulation:
    heroes = heroes if heroes is not None else [attacker]
    enemies = enemies if enemies is not None else []
    attacker_allies = attacker_allies if attacker_allies is not None else heroes
    dodging = dodging if dodging is not None else frozenset()
    if advantage_state is None:
        advantage_state = game.attack_advantage_state(
            attacker,
            target,
            heroes,
            enemies,
            dodging,
            ranged=attacker.weapon.ranged,
        )
        target_number = game.effective_attack_target_number(target)
    accuracy_bonus = (
        attacker.attack_bonus()
        + game.ally_pressure_bonus(attacker, attacker_allies, ranged=attacker.weapon.ranged)
        + game.status_accuracy_modifier(attacker)
        + game.attack_focus_modifier(attacker, target)
        + game.weapon_master_style_accuracy_modifier(attacker, target)
        + game.assassin_accuracy_modifier(attacker, target, attacker_allies)
        + game.target_accuracy_modifier(target)
    )
    critical_threshold = game.critical_threshold(attacker) if hasattr(game, "critical_threshold") else 20
    attack_roll = simulate_attack_roll(
        target_number=target_number,
        accuracy_bonus=accuracy_bonus,
        advantage_state=advantage_state,
        critical_threshold=critical_threshold,
        lucky="lucky" in getattr(attacker, "features", []),
        critical_immunity=bool(getattr(target, "gear_bonuses", {}).get("crit_immunity", 0)),
    )
    weapon_item = game.equipped_weapon_item(attacker)
    resolved_damage_type = damage_type
    if resolved_damage_type is None:
        resolved_damage_type = weapon_item.damage_type if weapon_item is not None else ""
    extra_damage = None
    if getattr(attacker, "class_name", "") == "Rogue" and advantage_state >= 0 and game.can_sneak_attack(attacker, attacker_allies, target):
        extra_damage = game.rogue_sneak_attack_dice(attacker)
    damage = simulate_weapon_damage(
        game,
        attacker,
        target,
        damage_type=resolved_damage_type or "",
        armor_break_percent=armor_break_percent,
        armor_break=armor_break,
        extra_damage=extra_damage,
    )
    return WeaponAttackSimulation(attack_roll=attack_roll, damage=damage)


def weapon_action_simulation(
    game,
    attacker,
    target,
    *,
    heroes: list,
    enemies: list,
    attacker_allies: list,
    armor_break_percent: int = 0,
) -> OffensiveActionSimulation:
    result = simulate_weapon_attack(
        game,
        attacker,
        target,
        heroes=heroes,
        enemies=enemies,
        attacker_allies=attacker_allies,
        armor_break_percent=armor_break_percent,
    )
    return OffensiveActionSimulation(
        actor_name=attacker.name,
        target_name=target.name,
        action_name=f"Weapon: {attacker.weapon.name}",
        expected_hp_damage=result.expected_hp_damage,
        hit_chance=result.hit_chance,
        miss_chance=result.miss_chance,
        wound_chance=result.wound_chance,
        defense_percent=result.damage.defense_percent,
        armor_break_percent=result.damage.armor_break_percent,
    )


def save_success_chance(game, target, ability: str, dc: int) -> float:
    if game.auto_fail_save(target, ability):
        return 0.0
    advantage = 0
    if ability == "DEX" and game.actor_is_dodging(target):
        advantage += 1
    if game.has_status(target, "restrained") and ability == "DEX":
        advantage -= 1
    if max(0, int(getattr(target, "conditions", {}).get("exhaustion", 0))) >= 3:
        advantage -= 1
    advantage_state = 1 if advantage > 0 else -1 if advantage < 0 else 0
    total_modifier = (
        target.save_bonus(ability)
        + game.status_value(target, "save_bonus")
        - game.status_value(target, "save_penalty")
    )
    chance = 0.0
    for kept, roll_chance in d20_kept_distribution(advantage_state=advantage_state, lucky="lucky" in getattr(target, "features", [])).items():
        if kept + total_modifier >= dc:
            chance += roll_chance
    return chance


def save_damage_action_simulation(
    game,
    caster,
    target,
    *,
    action_name: str,
    damage_expression: str,
    save_ability: str,
    damage_type: str,
    dc: int,
    damage_bonus: int = 0,
) -> OffensiveActionSimulation:
    success_chance = save_success_chance(game, target, save_ability, dc)
    full_distribution = add_damage_bonus(dice_total_distribution(damage_expression), damage_bonus)
    half_distribution = half_damage_distribution(full_distribution)
    full_expected, _, full_wound = simulate_damage_after_defense(
        game,
        target,
        full_distribution,
        damage_type=damage_type,
        defense_percent=0,
    )
    half_expected, _, half_wound = simulate_damage_after_defense(
        game,
        target,
        half_distribution,
        damage_type=damage_type,
        defense_percent=0,
    )
    expected_hp_damage = ((1 - success_chance) * full_expected) + (success_chance * half_expected)
    wound_chance = ((1 - success_chance) * full_wound) + (success_chance * half_wound)
    return OffensiveActionSimulation(
        actor_name=caster.name,
        target_name=target.name,
        action_name=action_name,
        expected_hp_damage=expected_hp_damage,
        save_success_chance=success_chance,
        wound_chance=wound_chance,
        defense_percent=0,
        armor_break_percent=0,
    )


def attack_damage_action_simulation(
    game,
    caster,
    target,
    *,
    action_name: str,
    damage_expression: str,
    damage_type: str,
    accuracy_bonus: int,
    damage_bonus: int = 0,
    damage_multiplier: int = 1,
    advantage_state: int = 0,
    cooldown_cycle_turns: int = 1,
) -> OffensiveActionSimulation:
    target_number = game.effective_attack_target_number(target)
    critical_threshold = game.critical_threshold(caster) if hasattr(game, "critical_threshold") else 20
    attack_roll = simulate_attack_roll(
        target_number=target_number,
        accuracy_bonus=accuracy_bonus,
        advantage_state=advantage_state,
        critical_threshold=critical_threshold,
        lucky="lucky" in getattr(caster, "features", []),
        critical_immunity=bool(getattr(target, "gear_bonuses", {}).get("crit_immunity", 0)),
    )
    normal_distribution = multiply_damage_distribution(
        add_damage_bonus(dice_total_distribution(damage_expression), damage_bonus),
        damage_multiplier,
    )
    critical_distribution = multiply_damage_distribution(
        add_damage_bonus(dice_total_distribution(damage_expression, critical=True), damage_bonus),
        damage_multiplier,
    )
    normal_expected, _, normal_wound = simulate_damage_after_defense(
        game,
        target,
        normal_distribution,
        damage_type=damage_type,
        defense_percent=0,
    )
    critical_expected, _, critical_wound = simulate_damage_after_defense(
        game,
        target,
        critical_distribution,
        damage_type=damage_type,
        defense_percent=0,
    )
    expected_hp_damage = (
        attack_roll.normal_hit_chance * normal_expected
        + attack_roll.critical_chance * critical_expected
    ) / max(1, cooldown_cycle_turns)
    wound_chance = (
        attack_roll.normal_hit_chance * normal_wound
        + attack_roll.critical_chance * critical_wound
    ) / max(1, cooldown_cycle_turns)
    return OffensiveActionSimulation(
        actor_name=caster.name,
        target_name=target.name,
        action_name=action_name,
        expected_hp_damage=expected_hp_damage,
        hit_chance=attack_roll.hit_chance,
        miss_chance=attack_roll.miss_chance,
        wound_chance=wound_chance,
        defense_percent=0,
        armor_break_percent=0,
    )


def mage_offensive_action_candidates(game, actor, target, *, heroes: list | None = None, enemies: list | None = None) -> list[OffensiveActionSimulation]:
    if not hasattr(game, "mage_channel_dc"):
        return []
    features = set(getattr(actor, "features", []))
    dc = game.mage_channel_dc(actor)
    spell_damage_bonus = game.spell_damage_bonus(actor) if hasattr(game, "spell_damage_bonus") else 0
    specs: list[tuple[str, str, str, str]] = []
    if "minor_channel" in features:
        specs.append(("Minor Channel", "1d6", "DEX", "force"))
    if "arc_pulse" in features:
        specs.append(("Arc Pulse", "1d8", "DEX", "force"))
    if "ember_lance" in features:
        specs.append(("Ember Lance", "1d8", "DEX", "fire"))
    if "frost_shard" in features:
        specs.append(("Frost Shard", "1d8", "DEX", "cold"))
    if "volt_grasp" in features:
        specs.append(("Volt Grasp", "1d8", "CON", "lightning"))
    if "blue_glass_palm" in features:
        specs.append(("Blue Glass Palm", "1d6", "STR", "force"))
    candidates = [
        save_damage_action_simulation(
            game,
            actor,
            target,
            action_name=name,
            damage_expression=damage,
            save_ability=save_ability,
            damage_type=damage_type,
            dc=dc,
            damage_bonus=spell_damage_bonus,
        )
        for name, damage, save_ability, damage_type in specs
    ]
    if "arcane_bolt" in features and hasattr(game, "arcane_bolt_damage_expression"):
        damage_bonus = max(0, actor.ability_mod("INT"))
        if hasattr(game, "spell_damage_bonus"):
            damage_bonus += game.spell_damage_bonus(actor)
        accuracy_bonus = (
            game.spell_attack_bonus(actor, "INT")
            + game.ally_pressure_bonus(actor, heroes or [actor], ranged=True)
            + game.status_accuracy_modifier(actor)
            + game.attack_focus_modifier(actor, target)
            + game.target_accuracy_modifier(target)
        )
        advantage = game.attack_advantage_state(actor, target, heroes or [actor], enemies or [], frozenset(), ranged=True)
        candidates.append(
            attack_damage_action_simulation(
                game,
                actor,
                target,
                action_name="Action: Arcane Bolt",
                damage_expression=game.arcane_bolt_damage_expression(actor),
                damage_type="force",
                accuracy_bonus=accuracy_bonus,
                damage_bonus=damage_bonus,
                damage_multiplier=2,
                advantage_state=advantage,
                cooldown_cycle_turns=3,
            )
        )
    return candidates


def mage_bonus_offensive_action_candidates(game, actor, target, *, heroes: list, enemies: list) -> list[OffensiveActionSimulation]:
    features = set(getattr(actor, "features", []))
    if "arcane_bolt" not in features or not hasattr(game, "arcane_bolt_damage_expression"):
        return []
    damage_bonus = max(0, actor.ability_mod("INT"))
    if hasattr(game, "spell_damage_bonus"):
        damage_bonus += game.spell_damage_bonus(actor)
    accuracy_bonus = (
        game.spell_attack_bonus(actor, "INT")
        + game.ally_pressure_bonus(actor, heroes, ranged=True)
        + game.status_accuracy_modifier(actor)
        + game.attack_focus_modifier(actor, target)
        + game.target_accuracy_modifier(target)
    )
    advantage = game.attack_advantage_state(actor, target, heroes, enemies, frozenset(), ranged=True)
    return [
        attack_damage_action_simulation(
            game,
            actor,
            target,
            action_name="Bonus: Arcane Bolt",
            damage_expression=game.arcane_bolt_damage_expression(actor),
            damage_type="force",
            accuracy_bonus=accuracy_bonus,
            damage_bonus=damage_bonus,
            damage_multiplier=1,
            advantage_state=advantage,
            cooldown_cycle_turns=3,
        )
    ]


def best_offensive_action(
    game,
    attacker,
    targets: list,
    *,
    heroes: list,
    enemies: list,
    attacker_allies: list,
    armor_break_percent: int = 0,
) -> OffensiveActionSimulation | None:
    candidates: list[OffensiveActionSimulation] = []
    for target in targets:
        if not target.is_conscious():
            continue
        candidates.append(
            weapon_action_simulation(
                game,
                attacker,
                target,
                heroes=heroes,
                enemies=enemies,
                attacker_allies=attacker_allies,
                armor_break_percent=armor_break_percent,
            )
        )
        if getattr(attacker, "class_name", "") == "Mage":
            candidates.extend(mage_offensive_action_candidates(game, attacker, target, heroes=heroes, enemies=enemies))
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            action.expected_hp_damage,
            action.wound_chance,
            action.hit_chance if action.hit_chance is not None else 1 - (action.save_success_chance or 0.0),
        ),
    )


def best_bonus_offensive_action(
    game,
    attacker,
    targets: list,
    *,
    heroes: list,
    enemies: list,
) -> OffensiveActionSimulation | None:
    candidates: list[OffensiveActionSimulation] = []
    for target in targets:
        if not target.is_conscious():
            continue
        if getattr(attacker, "class_name", "") == "Mage":
            candidates.extend(mage_bonus_offensive_action_candidates(game, attacker, target, heroes=heroes, enemies=enemies))
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            action.expected_hp_damage,
            action.wound_chance,
            action.hit_chance if action.hit_chance is not None else 0.0,
        ),
    )


def simulate_encounter_pass(
    game,
    name: str,
    party: list,
    enemies: list,
    *,
    party_armor_break_percent: int = 0,
) -> EncounterPassSimulation:
    living_party = [actor for actor in party if actor.is_conscious()]
    living_enemies = [actor for actor in enemies if actor.is_conscious()]
    party_action_list: list[OffensiveActionSimulation] = []
    for actor in living_party:
        main_action = best_offensive_action(
            game,
            actor,
            living_enemies,
            heroes=living_party,
            enemies=living_enemies,
            attacker_allies=living_party,
            armor_break_percent=party_armor_break_percent,
        )
        if main_action is not None:
            party_action_list.append(main_action)
        if main_action is None or main_action.action_name != "Action: Arcane Bolt":
            bonus_action = best_bonus_offensive_action(
                game,
                actor,
                living_enemies,
                heroes=living_party,
                enemies=living_enemies,
            )
            if bonus_action is not None:
                party_action_list.append(bonus_action)
    party_actions = tuple(party_action_list)
    enemy_actions = tuple(
        action
        for action in (
            best_offensive_action(
                game,
                enemy,
                living_party,
                heroes=living_party,
                enemies=living_enemies,
                attacker_allies=living_enemies,
            )
            for enemy in living_enemies
        )
        if action is not None
    )
    enemy_defenses = [
        game.effective_defense_percent(enemy, damage_type="slashing")
        for enemy in living_enemies
    ]
    enemy_avoidance = [game.effective_avoidance(enemy) for enemy in living_enemies]
    return EncounterPassSimulation(
        name=name,
        party_actions=party_actions,
        enemy_actions=enemy_actions,
        party_names=tuple(actor.name for actor in living_party),
        enemy_names=tuple(enemy.name for enemy in living_enemies),
        party_hp=sum(max(0, actor.current_hp) for actor in living_party),
        enemy_hp=sum(max(0, actor.current_hp) for actor in living_enemies),
        max_enemy_defense_percent=max(enemy_defenses, default=0),
        max_enemy_avoidance=max(enemy_avoidance, default=0),
    )


def _encounter_round_count(encounter: EncounterPassSimulation) -> int:
    if encounter.rounds_to_clear == inf:
        return 1
    return max(1, ceil(max(0.0, encounter.rounds_to_clear)))


def _expected_party_damage(encounter: EncounterPassSimulation, *, multiplier: float) -> int:
    if multiplier <= 0 or encounter.enemy_expected_damage_per_round <= 0:
        return 0
    active_rounds = 1.0 if encounter.rounds_to_clear == inf else max(1.0, encounter.rounds_to_clear)
    return max(0, int(round(encounter.enemy_expected_damage_per_round * active_rounds * multiplier)))


def _apply_expected_party_damage(party: list, amount: int) -> int:
    remaining = max(0, int(amount))
    applied = 0
    living = [member for member in party if not getattr(member, "dead", False) and member.current_hp > 0]
    cursor = 0
    while remaining > 0 and living:
        target = living[cursor % len(living)]
        target.current_hp = max(0, target.current_hp - 1)
        remaining -= 1
        applied += 1
        living = [member for member in living if member.current_hp > 0 and not getattr(member, "dead", False)]
        cursor += 1
    return applied


def _action_magic_point_cost(game, actor, action_name: str) -> int:
    spell_id = _ACTION_SPELL_IDS.get(action_name)
    if spell_id is None:
        return 0
    if spell_id == "arcane_bolt" and hasattr(game, "arcane_bolt_mp_cost"):
        return game.arcane_bolt_mp_cost(actor, action_cast=action_name.startswith("Action:"))
    return magic_point_cost(spell_id, actor)


def _action_uses_for_encounter(action_name: str, simulated_rounds: int) -> int:
    if action_name.endswith("Arcane Bolt"):
        return max(1, ceil(max(1, simulated_rounds) / 3))
    return max(1, simulated_rounds)


def _spend_simulated_party_resources(game, party: list, actions: tuple[OffensiveActionSimulation, ...], *, simulated_rounds: int) -> None:
    actors_by_name = {actor.name: actor for actor in party}
    for action in actions:
        actor = actors_by_name.get(action.actor_name)
        if actor is None:
            continue
        cost = _action_magic_point_cost(game, actor, action.action_name)
        if cost <= 0:
            continue
        for _ in range(_action_uses_for_encounter(action.action_name, simulated_rounds)):
            if not spend_magic_points(actor, cost):
                break


def _defer_rest_until_wave_group_finishes(specs: tuple[RouteChainEncounterSpec, ...], index: int) -> bool:
    wave_group = specs[index].wave_group
    if wave_group is None or index + 1 >= len(specs):
        return False
    return specs[index + 1].wave_group == wave_group


def simulate_route_chain(
    game,
    name: str,
    party: list,
    encounters: list[RouteChainEncounterSpec] | tuple[RouteChainEncounterSpec, ...],
    *,
    party_damage_multiplier: float = 1.0,
    spend_party_resources: bool = True,
) -> RouteChainSimulation:
    specs = tuple(encounters)
    steps: list[RouteChainStepSimulation] = []
    previous_wave_group: str | None = None
    wave_index = 0
    for index, spec in enumerate(specs):
        if spec.wave_group is not None and spec.wave_group == previous_wave_group:
            wave_index += 1
        else:
            wave_index = 1
        previous_wave_group = spec.wave_group
        enemies = list(spec.enemies)
        if hasattr(game, "_active_combat_heroes"):
            game._active_combat_heroes = party
        if hasattr(game, "_active_combat_enemies"):
            game._active_combat_enemies = enemies
        before = game.route_resource_snapshot()
        encounter = simulate_encounter_pass(
            game,
            spec.name,
            party,
            enemies,
            party_armor_break_percent=spec.party_armor_break_percent,
        )
        simulated_rounds = _encounter_round_count(encounter)
        if spend_party_resources:
            _spend_simulated_party_resources(game, party, encounter.party_actions, simulated_rounds=simulated_rounds)
        expected_damage = _expected_party_damage(encounter, multiplier=party_damage_multiplier)
        damage_applied = _apply_expected_party_damage(party, expected_damage)
        after_encounter = game.route_resource_snapshot()
        if _defer_rest_until_wave_group_finishes(specs, index):
            rest_decision = "deferred_wave"
            after_rest = after_encounter
        else:
            rest_decision = game.apply_route_rest_policy()
            after_rest = game.route_resource_snapshot()
        steps.append(
            RouteChainStepSimulation(
                name=spec.name,
                wave_index=wave_index,
                wave_group=spec.wave_group,
                encounter=encounter,
                resource_snapshot_before=before,
                resource_snapshot_after_encounter=after_encounter,
                resource_snapshot_after_rest=after_rest,
                rest_decision=rest_decision,
                simulated_rounds=simulated_rounds,
                expected_party_damage_applied=damage_applied,
            )
        )
    return RouteChainSimulation(name=name, steps=tuple(steps))
