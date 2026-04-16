from __future__ import annotations

from collections import deque

from .models import DraftMapState, DungeonMap, DungeonRoom, HybridMapBlueprint, Requirement, StoryBeat, TravelEdge, TravelNode


def requirement_met(state: DraftMapState, requirement: Requirement) -> bool:
    if requirement.all_flags and not set(requirement.all_flags).issubset(state.flags):
        return False
    if requirement.any_flags or requirement.active_quests:
        has_any_unlock = bool(set(requirement.any_flags).intersection(state.flags)) or bool(
            set(requirement.active_quests).intersection(state.active_quests)
        )
        if not has_any_unlock:
            return False
    if requirement.blocked_flags and set(requirement.blocked_flags).intersection(state.flags):
        return False
    if requirement.completed_quests and not set(requirement.completed_quests).issubset(state.completed_quests):
        return False
    return True


def unlocked_nodes(blueprint: HybridMapBlueprint, state: DraftMapState) -> list[TravelNode]:
    return [
        node
        for node in blueprint.nodes.values()
        if requirement_met(state, node.requirement)
    ]


def available_travel_edges(
    blueprint: HybridMapBlueprint,
    state: DraftMapState,
    from_node_id: str | None = None,
) -> list[TravelEdge]:
    current_node_id = from_node_id or state.current_node_id
    available: list[TravelEdge] = []
    for edge in blueprint.edges:
        if edge.from_node_id != current_node_id:
            continue
        destination = blueprint.nodes[edge.to_node_id]
        if requirement_met(state, edge.requirement) and requirement_met(state, destination.requirement):
            available.append(edge)
    return available


def available_story_beats(
    blueprint: HybridMapBlueprint,
    state: DraftMapState,
    host_node_id: str | None = None,
) -> list[StoryBeat]:
    current_host = host_node_id or state.current_node_id
    beats: list[StoryBeat] = []
    for beat in blueprint.story_beats:
        if beat.host_node_id != current_host:
            continue
        if beat.once_only and beat.beat_id in state.seen_story_beats:
            continue
        if requirement_met(state, beat.requirement):
            beats.append(beat)
    return beats


def current_room(dungeon: DungeonMap, state: DraftMapState) -> DungeonRoom:
    room_id = state.current_room_id or dungeon.entrance_room_id
    return dungeon.rooms[room_id]


def current_room_exits(dungeon: DungeonMap, state: DraftMapState) -> list[DungeonRoom]:
    room = current_room(dungeon, state)
    exits: list[DungeonRoom] = []
    for room_id in room.exits:
        candidate = dungeon.rooms[room_id]
        if requirement_met(state, candidate.requirement):
            exits.append(candidate)
    return exits


def _room_anchor(room: DungeonRoom) -> tuple[int, int]:
    return (room.x * 2, room.y * 2)


def room_travel_path(dungeon: DungeonMap, from_room: DungeonRoom, to_room: DungeonRoom) -> list[tuple[int, int]]:
    start = _room_anchor(from_room)
    goal = _room_anchor(to_room)
    if start == goal:
        return []

    width = max(1, dungeon.width * 2 - 1)
    height = max(1, dungeon.height * 2 - 1)
    blocked = {
        _room_anchor(room)
        for room in dungeon.rooms.values()
        if room.room_id not in {from_room.room_id, to_room.room_id}
    }

    frontier = deque([start])
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while frontier:
        current = frontier.popleft()
        if current == goal:
            break
        cx, cy = current
        gx, gy = goal
        preferred_steps: list[tuple[int, int]] = []
        if gx > cx:
            preferred_steps.append((1, 0))
        elif gx < cx:
            preferred_steps.append((-1, 0))
        if gy > cy:
            preferred_steps.append((0, 1))
        elif gy < cy:
            preferred_steps.append((0, -1))
        for step in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            if step not in preferred_steps:
                preferred_steps.append(step)
        for dx, dy in preferred_steps:
            nxt = (cx + dx, cy + dy)
            nx, ny = nxt
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            if nxt in blocked or nxt in came_from:
                continue
            came_from[nxt] = current
            frontier.append(nxt)

    if goal not in came_from:
        return []

    path: list[tuple[int, int]] = []
    cursor = goal
    while cursor != start:
        path.append(cursor)
        previous = came_from[cursor]
        assert previous is not None
        cursor = previous
    path.reverse()
    return path


def room_direction(from_room: DungeonRoom, to_room: DungeonRoom, dungeon: DungeonMap | None = None) -> str:
    if dungeon is not None:
        path = room_travel_path(dungeon, from_room, to_room)
        if path:
            start_x, start_y = _room_anchor(from_room)
            step_x, step_y = path[0]
            dx = step_x - start_x
            dy = step_y - start_y
            if dx > 0:
                return "RIGHT"
            if dx < 0:
                return "LEFT"
            if dy > 0:
                return "DOWN"
            if dy < 0:
                return "UP"
    dx = to_room.x - from_room.x
    dy = to_room.y - from_room.y
    if dx == 0 and dy == 0:
        return "HERE"
    if dx == 0:
        return "DOWN" if dy > 0 else "UP"
    if dy == 0:
        return "RIGHT" if dx > 0 else "LEFT"
    if abs(dy) >= abs(dx):
        return "DOWN" if dy > 0 else "UP"
    return "RIGHT" if dx > 0 else "LEFT"
