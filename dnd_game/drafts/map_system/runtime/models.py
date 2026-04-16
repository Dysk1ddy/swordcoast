from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


NodeKind = Literal["story", "hub", "site", "dungeon_entry"]
RoomRole = Literal["entrance", "combat", "event", "treasure", "boss", "exit"]


@dataclass(slots=True)
class Requirement:
    all_flags: tuple[str, ...] = ()
    any_flags: tuple[str, ...] = ()
    blocked_flags: tuple[str, ...] = ()
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


@dataclass(slots=True)
class DraftMapState:
    current_node_id: str
    current_room_id: str | None = None
    flags: set[str] = field(default_factory=set)
    active_quests: set[str] = field(default_factory=set)
    completed_quests: set[str] = field(default_factory=set)
    visited_nodes: set[str] = field(default_factory=set)
    cleared_rooms: set[str] = field(default_factory=set)
    seen_story_beats: set[str] = field(default_factory=set)
