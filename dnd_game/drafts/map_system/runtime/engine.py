from __future__ import annotations

from collections import deque

from .models import DraftMapState, DungeonMap, DungeonRoom, HybridMapBlueprint, Requirement, StoryBeat, TravelEdge, TravelNode


def _flag_is_present(state: DraftMapState, flag_name: str) -> bool:
    if flag_name in state.flags:
        return True
    value = state.flag_values.get(flag_name)
    return bool(value)


def _numeric_flag_value(state: DraftMapState, flag_name: str) -> float | None:
    value = state.flag_values.get(flag_name)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return float(value)
    return None


def requirement_met(state: DraftMapState, requirement: Requirement) -> bool:
    if requirement.all_flags and not all(_flag_is_present(state, flag_name) for flag_name in requirement.all_flags):
        return False
    if requirement.any_flags or requirement.active_quests:
        has_any_unlock = any(_flag_is_present(state, flag_name) for flag_name in requirement.any_flags) or bool(
            set(requirement.active_quests).intersection(state.active_quests)
        )
        if not has_any_unlock:
            return False
    if requirement.blocked_flags and any(_flag_is_present(state, flag_name) for flag_name in requirement.blocked_flags):
        return False
    for flag_count in requirement.flag_count_requirements:
        count = sum(1 for flag_name in flag_count.flags if _flag_is_present(state, flag_name))
        if count < flag_count.minimum:
            return False
        if flag_count.maximum is not None and count > flag_count.maximum:
            return False
    for flag_value in requirement.flag_value_requirements:
        actual_value = state.flag_values.get(flag_value.flag_name)
        if actual_value is None and flag_value.flag_name in state.flags:
            actual_value = True
        if actual_value != flag_value.expected_value:
            return False
    for numeric_flag in requirement.numeric_flag_requirements:
        actual_value = _numeric_flag_value(state, numeric_flag.flag_name)
        if actual_value is None:
            return False
        if numeric_flag.minimum is not None and actual_value < numeric_flag.minimum:
            return False
        if numeric_flag.maximum is not None and actual_value > numeric_flag.maximum:
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


def _coordinate_direction(from_room: DungeonRoom, to_room: DungeonRoom) -> str:
    dx = to_room.x - from_room.x
    dy = to_room.y - from_room.y
    if dx == 0 and dy == 0:
        return "HERE"

    direction_parts: list[str] = []
    if dy < 0:
        direction_parts.append("NORTH")
    elif dy > 0:
        direction_parts.append("SOUTH")
    if dx < 0:
        direction_parts.append("WEST")
    elif dx > 0:
        direction_parts.append("EAST")
    return "-".join(direction_parts)


def _step_direction(from_position: tuple[int, int], to_position: tuple[int, int]) -> str:
    dx = to_position[0] - from_position[0]
    dy = to_position[1] - from_position[1]
    if dx > 0:
        return "EAST"
    if dx < 0:
        return "WEST"
    if dy > 0:
        return "SOUTH"
    if dy < 0:
        return "NORTH"
    return "HERE"


def _path_direction(dungeon: DungeonMap, from_room: DungeonRoom, to_room: DungeonRoom) -> str:
    path = room_travel_path(dungeon, from_room, to_room)
    if not path:
        return _coordinate_direction(from_room, to_room)

    previous = _room_anchor(from_room)
    directions: list[str] = []
    seen_directions: set[str] = set()
    for step in path:
        direction = _step_direction(previous, step)
        previous = step
        if direction == "HERE" or direction in seen_directions:
            continue
        directions.append(direction)
        seen_directions.add(direction)
    return "-".join(directions) or "HERE"


def room_direction(from_room: DungeonRoom, to_room: DungeonRoom, dungeon: DungeonMap | None = None) -> str:
    if dungeon is not None:
        return _path_direction(dungeon, from_room, to_room)
    return _coordinate_direction(from_room, to_room)


def room_precise_direction(from_room: DungeonRoom, to_room: DungeonRoom, dungeon: DungeonMap | None = None) -> str:
    return room_direction(from_room, to_room, dungeon)


def room_exit_directions(
    from_room: DungeonRoom,
    exits: list[DungeonRoom],
    *,
    dungeon: DungeonMap | None = None,
    reserved_directions: set[str] | None = None,
) -> dict[str, str]:
    _ = reserved_directions
    return {exit_room.room_id: room_direction(from_room, exit_room, dungeon) for exit_room in exits}
