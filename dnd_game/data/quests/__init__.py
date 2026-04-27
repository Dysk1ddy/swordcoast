from __future__ import annotations

from .act2 import ACT_2_QUESTS
from .act1 import ACT_1_QUESTS
from .schema import QuestDefinition, QuestLogEntry, QuestReward

QUEST_ID_ALIASES = {
    "seek_agathas_truth": "seek_pale_witness_truth",
}


def resolve_quest_id(quest_id: str | None) -> str | None:
    if quest_id is None:
        return None
    token = str(quest_id).strip()
    if not token:
        return token
    return QUEST_ID_ALIASES.get(token, token)


class QuestCatalogDict(dict[str, QuestDefinition]):
    def _canonical_key(self, key: object) -> object:
        if isinstance(key, str):
            return resolve_quest_id(key)
        return key

    def __contains__(self, key: object) -> bool:
        return dict.__contains__(self, self._canonical_key(key))

    def __getitem__(self, key: str) -> QuestDefinition:
        return dict.__getitem__(self, self._canonical_key(key))

    def get(self, key: str, default=None):
        return dict.get(self, self._canonical_key(key), default)


QUESTS = QuestCatalogDict(ACT_1_QUESTS)
QUESTS.update(ACT_2_QUESTS)
QUEST_ORDER = tuple(QUESTS)

__all__ = [
    "QUESTS",
    "QUEST_ORDER",
    "QUEST_ID_ALIASES",
    "QuestDefinition",
    "QuestLogEntry",
    "QuestReward",
    "resolve_quest_id",
]
