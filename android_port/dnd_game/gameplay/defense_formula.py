from __future__ import annotations

import math


DEFENSE_POINT_FLOOR = 10
DEFENSE_POINT_CAP = 22
DEFENSE_POINT_DR_CAP = 80.0
DEFENSE_POINT_CURVE_COEFFICIENT = 0.18
DEFENSE_POINT_LOG_NORMALIZER = math.log(
    1 + DEFENSE_POINT_CURVE_COEFFICIENT * (DEFENSE_POINT_CAP - DEFENSE_POINT_FLOOR)
)
PLAYER_DEFENSE_LEVEL_SCALING_RATE = 0.08
ORDINARY_ENEMY_DEFENSE_LEVEL_SCALING_RATE = 0.04
BOSS_ENEMY_DEFENSE_LEVEL_SCALING_RATE = 0.06


def base_damage_reduction_for_defense(defense: int | float) -> float:
    defense_value = float(defense)
    if defense_value <= DEFENSE_POINT_FLOOR:
        return 0.0
    if defense_value >= DEFENSE_POINT_CAP:
        return DEFENSE_POINT_DR_CAP
    scaled = math.log(1 + DEFENSE_POINT_CURVE_COEFFICIENT * (defense_value - DEFENSE_POINT_FLOOR))
    return max(0.0, min(DEFENSE_POINT_DR_CAP, DEFENSE_POINT_DR_CAP * scaled / DEFENSE_POINT_LOG_NORMALIZER))


def defense_points_for_damage_reduction(damage_reduction: int | float) -> int:
    reduction = max(0.0, min(DEFENSE_POINT_DR_CAP, float(damage_reduction)))
    return min(
        range(DEFENSE_POINT_FLOOR, DEFENSE_POINT_CAP + 1),
        key=lambda defense: abs(base_damage_reduction_for_defense(defense) - reduction),
    )


def defense_level_scaling_multiplier(
    defender_level: int,
    attacker_level: int,
    *,
    defender_is_enemy: bool = False,
    boss: bool = False,
) -> float:
    if defender_is_enemy:
        rate = BOSS_ENEMY_DEFENSE_LEVEL_SCALING_RATE if boss else ORDINARY_ENEMY_DEFENSE_LEVEL_SCALING_RATE
    else:
        rate = PLAYER_DEFENSE_LEVEL_SCALING_RATE
    return 1 + rate * (int(defender_level) - int(attacker_level))


def damage_reduction_for_defense(
    defense: int | float,
    defender_level: int,
    attacker_level: int,
    *,
    defender_is_enemy: bool = False,
    boss: bool = False,
) -> int:
    base_dr = base_damage_reduction_for_defense(defense)
    multiplier = defense_level_scaling_multiplier(
        defender_level,
        attacker_level,
        defender_is_enemy=defender_is_enemy,
        boss=boss,
    )
    return round(max(0.0, min(DEFENSE_POINT_DR_CAP, base_dr * multiplier)))
