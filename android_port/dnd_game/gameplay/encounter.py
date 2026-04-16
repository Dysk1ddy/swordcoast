from __future__ import annotations

from dataclasses import dataclass

from ..models import Character


@dataclass(slots=True)
class Encounter:
    title: str
    description: str
    enemies: list[Character]
    allow_flee: bool = True
    allow_parley: bool = False
    parley_dc: int = 14
    hero_initiative_bonus: int = 0
    enemy_initiative_bonus: int = 0
    allow_post_combat_random_encounter: bool = True
