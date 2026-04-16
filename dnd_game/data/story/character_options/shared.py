from __future__ import annotations


POINT_BUY_COSTS = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
}

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

ACTS = [
    {"number": 1, "title": "Ashes on the Triboar Trail", "status": "playable"},
    {"number": 2, "title": "Echoes Beneath the Sword Mountains", "status": "planned"},
    {"number": 3, "title": "The Jewel and the Chasm", "status": "planned"},
]


def point_buy_total(scores: dict[str, int]) -> int:
    return sum(POINT_BUY_COSTS[value] for value in scores.values())
