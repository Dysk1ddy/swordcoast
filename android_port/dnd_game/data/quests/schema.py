from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class QuestReward:
    xp: int = 0
    gold: int = 0
    items: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "xp": self.xp,
            "gold": self.gold,
            "items": dict(self.items),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "QuestReward":
        return cls(
            xp=int(data.get("xp", 0)),
            gold=int(data.get("gold", 0)),
            items={str(key): int(value) for key, value in dict(data.get("items", {})).items()},
        )


@dataclass(slots=True)
class QuestDefinition:
    quest_id: str
    title: str
    giver: str
    location: str
    summary: str
    objective: str
    turn_in: str
    completion_flags: tuple[str, ...] = ()
    reward: QuestReward = field(default_factory=QuestReward)
    accepted_text: str = ""
    ready_text: str = ""
    turn_in_text: str = ""


@dataclass(slots=True)
class QuestLogEntry:
    quest_id: str
    status: str = "active"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "quest_id": self.quest_id,
            "status": self.status,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "QuestLogEntry":
        return cls(
            quest_id=str(data["quest_id"]),
            status=str(data.get("status", "active")),
            notes=[str(note) for note in list(data.get("notes", []))],
        )
