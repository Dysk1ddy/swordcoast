from __future__ import annotations

from .act1 import ACT_1_QUESTS
from .schema import QuestDefinition, QuestLogEntry, QuestReward

QUESTS = dict(ACT_1_QUESTS)
QUEST_ORDER = tuple(QUESTS)

__all__ = [
    "QUESTS",
    "QUEST_ORDER",
    "QuestDefinition",
    "QuestLogEntry",
    "QuestReward",
]
