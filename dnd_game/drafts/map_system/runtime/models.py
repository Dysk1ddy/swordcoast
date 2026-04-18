from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


NodeKind = Literal["story", "hub", "site", "dungeon_entry"]
RoomRole = Literal["entrance", "combat", "event", "treasure", "boss", "exit"]


@dataclass(slots=True)
class FlagCountRequirement:
    flags: tuple[str, ...]
    minimum: int
    maximum: int | None = None
    notes: str = ""

    def describe(self) -> str:
        count_text = f"at least {self.minimum}"
        if self.maximum is not None:
            count_text = f"{self.minimum}-{self.maximum}"
        suffix = f" ({self.notes})" if self.notes else ""
        return f"{count_text} of: {', '.join(self.flags)}{suffix}"


@dataclass(slots=True)
class FlagValueRequirement:
    flag_name: str
    expected_value: Any
    notes: str = ""

    def describe(self) -> str:
        suffix = f" ({self.notes})" if self.notes else ""
        return f"{self.flag_name} == {self.expected_value!r}{suffix}"


@dataclass(slots=True)
class NumericFlagRequirement:
    flag_name: str
    minimum: int | float | None = None
    maximum: int | float | None = None
    notes: str = ""

    def describe(self) -> str:
        parts: list[str] = []
        if self.minimum is not None:
            parts.append(f">= {self.minimum}")
        if self.maximum is not None:
            parts.append(f"<= {self.maximum}")
        suffix = f" ({self.notes})" if self.notes else ""
        return f"{self.flag_name} {' and '.join(parts) or 'numeric'}{suffix}"


@dataclass(slots=True)
class Requirement:
    all_flags: tuple[str, ...] = ()
    any_flags: tuple[str, ...] = ()
    blocked_flags: tuple[str, ...] = ()
    flag_count_requirements: tuple[FlagCountRequirement, ...] = ()
    flag_value_requirements: tuple[FlagValueRequirement, ...] = ()
    numeric_flag_requirements: tuple[NumericFlagRequirement, ...] = ()
    active_quests: tuple[str, ...] = ()
    completed_quests: tuple[str, ...] = ()
    notes: str = ""

    def describe(self) -> list[str]:
        parts: list[str] = []
        if self.all_flags:
            parts.append(f"all flags: {', '.join(self.all_flags)}")
        if self.any_flags:
            parts.append(f"any flag: {', '.join(self.any_flags)}")
        if self.blocked_flags:
            parts.append(f"blocked by: {', '.join(self.blocked_flags)}")
        for flag_count in self.flag_count_requirements:
            parts.append(f"flag count: {flag_count.describe()}")
        for flag_value in self.flag_value_requirements:
            parts.append(f"flag value: {flag_value.describe()}")
        for numeric_flag in self.numeric_flag_requirements:
            parts.append(f"numeric flag: {numeric_flag.describe()}")
        if self.active_quests:
            parts.append(f"active quest: {', '.join(self.active_quests)}")
        if self.completed_quests:
            parts.append(f"completed quest: {', '.join(self.completed_quests)}")
        if self.notes:
            parts.append(self.notes)
        return parts


@dataclass(slots=True)
class TravelNode:
    node_id: str
    scene_key: str
    title: str
    short_label: str
    kind: NodeKind
    summary: str
    requirement: Requirement = field(default_factory=Requirement)
    enters_dungeon_id: str | None = None
    parent_hub_id: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class TravelEdge:
    edge_id: str
    from_node_id: str
    to_node_id: str
    label: str
    requirement: Requirement = field(default_factory=Requirement)
    travel_text: str = ""


@dataclass(slots=True)
class StoryBeat:
    beat_id: str
    title: str
    host_node_id: str
    summary: str
    requirement: Requirement = field(default_factory=Requirement)
    grants_flags: tuple[str, ...] = ()
    reveals_node_ids: tuple[str, ...] = ()
    once_only: bool = True


@dataclass(slots=True)
class DungeonRoom:
    room_id: str
    title: str
    x: int
    y: int
    role: RoomRole
    summary: str
    exits: tuple[str, ...] = ()
    requirement: Requirement = field(default_factory=Requirement)
    clear_grants_flags: tuple[str, ...] = ()
    encounter_key: str | None = None
    scene_note: str = ""


@dataclass(slots=True)
class DungeonMap:
    dungeon_id: str
    title: str
    entry_node_id: str
    entrance_room_id: str
    width: int
    height: int
    rooms: dict[str, DungeonRoom]
    completion_flags: tuple[str, ...] = ()
    exit_to_node_id: str = "phandalin_hub"
    boss_room_id: str | None = None
    summary: str = ""


@dataclass(slots=True)
class HybridMapBlueprint:
    act: int
    title: str
    start_node_id: str
    nodes: dict[str, TravelNode]
    edges: tuple[TravelEdge, ...]
    story_beats: tuple[StoryBeat, ...]
    dungeons: dict[str, DungeonMap]
    overworld_template: tuple[str, ...]
    overworld_positions: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass(slots=True)
class DraftMapState:
    current_node_id: str
    current_room_id: str | None = None
    flags: set[str] = field(default_factory=set)
    active_quests: set[str] = field(default_factory=set)
    completed_quests: set[str] = field(default_factory=set)
    flag_values: dict[str, Any] = field(default_factory=dict)
    visited_nodes: set[str] = field(default_factory=set)
    cleared_rooms: set[str] = field(default_factory=set)
    seen_story_beats: set[str] = field(default_factory=set)
