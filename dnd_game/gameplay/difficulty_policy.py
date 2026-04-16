from __future__ import annotations

"""Canonical skill-check difficulty ladder and scenario bands.

This file is the source of truth for the campaign's skill-check policy.

Difficulty ladder:
- Very Easy: 6
- Easy: 8
- Medium: 10
- Slightly Hard: 12
- Hard: 15
- Very Hard: 18
- Extremely Hard: 20

Act 1 ranges:
- Recruitment: Very Easy to Easy
- Regular non-combat and town scenes: Easy to Medium
- Random encounters: Easy to Hard
- Potential combat and active combat: Medium to Slightly Hard
- Minibosses and bosses: Hard to Very Hard

Act 2 ranges:
- Same structure as Act 1, but each category shifts up by one tier
"""

TIER_VALUES: dict[str, int] = {
    "very_easy": 6,
    "easy": 8,
    "medium": 10,
    "slightly_hard": 12,
    "hard": 15,
    "very_hard": 18,
    "extremely_hard": 20,
}

TIER_ORDER: tuple[str, ...] = tuple(TIER_VALUES)

ACT_DIFFICULTY_BANDS: dict[int, dict[str, tuple[str, str]]] = {
    1: {
        "recruitment": ("very_easy", "easy"),
        "regular": ("easy", "medium"),
        "random": ("easy", "hard"),
        "combat": ("medium", "slightly_hard"),
        "boss": ("hard", "very_hard"),
    },
    2: {
        "recruitment": ("easy", "medium"),
        "regular": ("medium", "slightly_hard"),
        "random": ("medium", "very_hard"),
        "combat": ("slightly_hard", "hard"),
        "boss": ("very_hard", "extremely_hard"),
    },
}


def nearest_tier_value(raw_dc: int) -> int:
    nearest_name = min(
        TIER_ORDER,
        key=lambda tier_name: (abs(TIER_VALUES[tier_name] - raw_dc), TIER_VALUES[tier_name]),
    )
    return TIER_VALUES[nearest_name]


def clamp_dc_to_band(raw_dc: int, minimum_tier: str, maximum_tier: str) -> int:
    minimum_value = TIER_VALUES[minimum_tier]
    maximum_value = TIER_VALUES[maximum_tier]
    return max(minimum_value, min(maximum_value, nearest_tier_value(raw_dc)))
