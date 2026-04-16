from __future__ import annotations

import re
from typing import Any

from .engine import available_travel_edges, current_room_exits, requirement_met, room_direction, room_travel_path
from .models import DraftMapState, DungeonMap, HybridMapBlueprint, TravelNode

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    Console = Any  # type: ignore[assignment]
    Group = None
    Panel = None
    Table = None
    Text = Any  # type: ignore[assignment]
    box = None
    Align = None
    RICH_AVAILABLE = False


ROLE_SYMBOLS = {
    "entrance": "D",
    "combat": "E",
    "event": "*",
    "treasure": "T",
    "boss": "B",
    "exit": "X",
}


def _box_panel(title: str, lines: list[str], width: int = 62) -> str:
    inner_width = max(width - 4, len(title) + 2, *(len(line) for line in lines or [""]))
    top = f"+- {title} " + "-" * max(0, inner_width - len(title) - 2) + "+"
    body = [f"| {line.ljust(inner_width)} |" for line in lines] or [f"| {' ' * inner_width} |"]
    bottom = f"+{'-' * (inner_width + 2)}+"
    return "\n".join([top, *body, bottom])


def _node_is_known(node: TravelNode, state: DraftMapState) -> bool:
    return node.node_id == state.current_node_id or node.node_id in state.visited_nodes


def _hidden_node_label(node: TravelNode) -> str:
    return "?" * len(node.short_label)


def _node_inner_width(blueprint: HybridMapBlueprint) -> int:
    return max(len(node.short_label) for node in blueprint.nodes.values()) + 2


def _node_label(node: TravelNode, state: DraftMapState) -> str:
    if _node_is_known(node, state):
        return node.short_label
    return _hidden_node_label(node)


def _node_status(node: TravelNode, state: DraftMapState) -> str:
    if node.node_id == state.current_node_id:
        return "Current"
    if node.node_id in state.visited_nodes:
        return "Explored"
    if requirement_met(state, node.requirement):
        return "Unexplored"
    return "Unknown"


def _node_card_token(node: TravelNode, blueprint: HybridMapBlueprint, state: DraftMapState) -> str:
    label = _node_label(node, state).center(_node_inner_width(blueprint))
    if node.node_id == state.current_node_id:
        return f"({label})"
    return f"[{label}]"


def _node_style(node: TravelNode, state: DraftMapState) -> str:
    if node.node_id == state.current_node_id:
        return "bold black on bright_cyan"
    if node.node_id in state.visited_nodes:
        return "bold green"
    if requirement_met(state, node.requirement):
        return "dim"
    return "dim"


def _unknown_travel_count(blueprint: HybridMapBlueprint, state: DraftMapState) -> int:
    return sum(
        1
        for edge in available_travel_edges(blueprint, state)
        if not _node_is_known(blueprint.nodes[edge.to_node_id], state)
    )


def _overworld_node_levels(blueprint: HybridMapBlueprint) -> list[list[TravelNode]]:
    levels: list[list[TravelNode]] = []
    for row in blueprint.overworld_template:
        node_ids = re.findall(r"\{([^}]+)\}", row)
        if not node_ids:
            continue
        levels.append([blueprint.nodes[node_id] for node_id in node_ids])
    return levels


def _row_positions(count: int, *, width: int, token_width: int, gap: int = 7) -> list[int]:
    total_width = count * token_width + max(0, count - 1) * gap
    left = max(0, (width - total_width) // 2)
    return [left + index * (token_width + gap) for index in range(count)]


def _render_card_row(nodes: list[TravelNode], *, blueprint: HybridMapBlueprint, state: DraftMapState, width: int) -> str:
    token_width = _node_inner_width(blueprint) + 2
    line = [" "] * width
    for position, node in zip(_row_positions(len(nodes), width=width, token_width=token_width), nodes):
        token = _node_card_token(node, blueprint, state)
        line[position : position + len(token)] = list(token)
    return "".join(line).rstrip()


def _render_card_row_rich(nodes: list[TravelNode], *, blueprint: HybridMapBlueprint, state: DraftMapState, width: int) -> Text:
    token_width = _node_inner_width(blueprint) + 2
    line = Text()
    cursor = 0
    for position, node in zip(_row_positions(len(nodes), width=width, token_width=token_width), nodes):
        if position > cursor:
            line.append(" " * (position - cursor), style="dim")
        token = _node_card_token(node, blueprint, state)
        line.append(token, style=_node_style(node, state))
        cursor = position + len(token)
    if cursor < width:
        line.append(" " * (width - cursor), style="dim")
    return line


def _render_connection_lines(
    blueprint: HybridMapBlueprint,
    current_nodes: list[TravelNode],
    next_nodes: list[TravelNode],
    *,
    width: int,
) -> list[str]:
    token_width = _node_inner_width(blueprint) + 2
    current_positions = _row_positions(len(current_nodes), width=width, token_width=token_width)
    next_positions = _row_positions(len(next_nodes), width=width, token_width=token_width)
    current_centers = [position + token_width // 2 for position in current_positions]
    next_centers = [position + token_width // 2 for position in next_positions]

    def make_line(*marks: tuple[int, str]) -> str:
        line = [" "] * width
        for column, glyph in marks:
            if 0 <= column < width:
                line[column] = glyph
        return "".join(line).rstrip()

    if len(current_nodes) == 1 and len(next_nodes) == 1:
        return [make_line((current_centers[0], "|"))]
    if len(current_nodes) == 1 and len(next_nodes) > 1:
        source = current_centers[0]
        branch_marks = [((source + target) // 2, "/" if target < source else "\\") for target in next_centers]
        return [make_line((source, "|")), make_line(*branch_marks)]
    if len(current_nodes) > 1 and len(next_nodes) == 1:
        target = next_centers[0]
        merge_marks = [((source + target) // 2, "\\" if source < target else "/") for source in current_centers]
        return [make_line(*merge_marks), make_line((target, "|"))]
    return [make_line(*[(center, "|") for center in current_centers])]


def _overworld_card_lines(blueprint: HybridMapBlueprint, state: DraftMapState) -> list[str]:
    levels = _overworld_node_levels(blueprint)
    token_width = _node_inner_width(blueprint) + 2
    max_nodes = max((len(level) for level in levels), default=1)
    width = max(60, token_width * max_nodes + max(0, max_nodes - 1) * 7, token_width + 10)
    lines: list[str] = []
    for index, level in enumerate(levels):
        lines.append(_render_card_row(level, blueprint=blueprint, state=state, width=width))
        if index < len(levels) - 1:
            lines.extend(_render_connection_lines(blueprint, level, levels[index + 1], width=width))
    return lines


def _overworld_card_lines_rich(blueprint: HybridMapBlueprint, state: DraftMapState) -> list[Text]:
    levels = _overworld_node_levels(blueprint)
    token_width = _node_inner_width(blueprint) + 2
    max_nodes = max((len(level) for level in levels), default=1)
    width = max(60, token_width * max_nodes + max(0, max_nodes - 1) * 7, token_width + 10)
    lines: list[Text] = []
    for index, level in enumerate(levels):
        lines.append(_render_card_row_rich(level, blueprint=blueprint, state=state, width=width))
        if index < len(levels) - 1:
            lines.extend(Text(line, style="dim") for line in _render_connection_lines(blueprint, level, levels[index + 1], width=width))
    return lines


def _directional_exit_lines(dungeon: DungeonMap, state: DraftMapState) -> list[str]:
    room = dungeon.rooms[state.current_room_id or dungeon.entrance_room_id]
    exits = current_room_exits(dungeon, state)
    if not exits:
        return ["- None"]
    return [f"- {room_direction(room, exit_room, dungeon)} -> {exit_room.title}" for exit_room in exits]


def _directional_exit_text(dungeon: DungeonMap, state: DraftMapState) -> str:
    room = dungeon.rooms[state.current_room_id or dungeon.entrance_room_id]
    exits = current_room_exits(dungeon, state)
    if not exits:
        return "None"
    return ", ".join(f"{room_direction(room, exit_room, dungeon)} -> {exit_room.title}" for exit_room in exits)


def build_hud_panel_text(
    *,
    player_name: str = "Draft Hero",
    hp_text: str = "34/40",
    gold: int = 27,
    quest_text: str = "Stop the Watchtower Raids",
) -> str:
    lines = [
        f"{player_name}    HP: {hp_text}    Gold: {gold}",
        f"Quest: {quest_text}",
        "Layout order: HUD -> map -> scene text -> actions",
    ]
    return _box_panel("HUD", lines)


def build_hud_panel(
    *,
    player_name: str = "Draft Hero",
    hp_text: str = "34/40",
    gold: int = 27,
    quest_text: str = "Stop the Watchtower Raids",
) -> Panel:
    table = Table.grid(expand=True)
    table.add_column(ratio=3)
    table.add_column(ratio=2, justify="center")
    table.add_column(ratio=2, justify="right")
    table.add_row(
        Text(player_name, style="bold white"),
        Text(f"HP {hp_text}", style="bold red"),
        Text(f"Gold {gold}", style="bold yellow"),
    )
    table.add_row(
        Text(f"Quest: {quest_text}", style="cyan"),
        Text("Mode: Hybrid Draft", style="magenta"),
        Text("Act 1", style="green"),
    )
    return Panel(table, title="HUD", border_style="cyan", box=box.ROUNDED, padding=(0, 1))


def build_overworld_panel_text(blueprint: HybridMapBlueprint, state: DraftMapState) -> str:
    lines = _overworld_card_lines(blueprint, state)
    edges = available_travel_edges(blueprint, state)
    known_edges = [edge for edge in edges if _node_is_known(blueprint.nodes[edge.to_node_id], state)]
    unknown_edge_count = _unknown_travel_count(blueprint, state)
    lines.append("")
    lines.append("Travel Routes:")
    if known_edges:
        lines.extend(f"- {edge.label}" for edge in known_edges)
    if unknown_edge_count:
        lines.append(f"- {unknown_edge_count} unexplored route(s) branch from here")
    if not known_edges and not unknown_edge_count:
        lines.append("- No unlocked travel from here")
    lines.append("")
    lines.append("Known Places:")
    known_nodes = [node for node in blueprint.nodes.values() if _node_is_known(node, state)]
    for node in known_nodes:
        lines.append(f"- {node.title}: {_node_status(node, state)}")
    hidden_count = len(blueprint.nodes) - len(known_nodes)
    if hidden_count > 0:
        lines.append(f"- {hidden_count} destination(s) remain unknown")
    lines.append("")
    lines.append("Legend: (NAME) current, [NAME] explored, [?] unknown")
    return _box_panel("Overworld Route Map", lines, width=78)


def build_overworld_panel(blueprint: HybridMapBlueprint, state: DraftMapState) -> Panel:
    content = Group(*_overworld_card_lines_rich(blueprint, state))

    edges = available_travel_edges(blueprint, state)

    meta = Table.grid(expand=True, padding=(0, 1))
    meta.add_column(ratio=2)
    meta.add_column(ratio=2)

    travel = Table.grid()
    travel.add_column()
    known_edges = [edge for edge in edges if _node_is_known(blueprint.nodes[edge.to_node_id], state)]
    unknown_edge_count = _unknown_travel_count(blueprint, state)
    if known_edges:
        for edge in known_edges:
            travel.add_row(Text(f"- {edge.label}", style="green"))
    if unknown_edge_count:
        travel.add_row(Text(f"- {unknown_edge_count} unexplored route(s) branch from here", style="yellow"))
    if not known_edges and not unknown_edge_count:
        travel.add_row(Text("- No unlocked travel from here", style="dim"))

    locations = Table.grid(expand=True)
    locations.add_column(ratio=3)
    locations.add_column(ratio=2)
    known_nodes = [node for node in blueprint.nodes.values() if _node_is_known(node, state)]
    for node in known_nodes:
        status = _node_status(node, state)
        status_style = "bright_cyan" if status == "Current" else "green"
        locations.add_row(
            Text(node.title, style="white"),
            Text(status, style=status_style),
        )
    hidden_count = len(blueprint.nodes) - len(known_nodes)
    if hidden_count > 0:
        locations.add_row(
            Text(f"{hidden_count} unknown destination(s)", style="dim"),
            Text("Hidden", style="dim"),
        )

    meta.add_row(
        Panel(travel, title="Travel", border_style="green", box=box.SIMPLE),
        Panel(locations, title="Route Key", border_style="cyan", box=box.SIMPLE),
    )

    legend = Text.assemble(
        ("(NAME) ", "bold black on bright_cyan"),
        ("current   ", "white"),
        ("[NAME] ", "bold green"),
        ("explored   ", "white"),
        ("[????] ", "dim"),
        ("unknown", "white"),
    )

    group = Group(content, meta, Align.center(legend))
    return Panel(group, title="Overworld Route Map", border_style="green", box=box.ROUNDED, padding=(0, 1))


def _room_symbol(dungeon: DungeonMap, room_id: str, state: DraftMapState) -> str:
    room = dungeon.rooms[room_id]
    if state.current_room_id == room_id:
        return "P"
    if room_id in state.cleared_rooms:
        return "."
    if requirement_met(state, room.requirement):
        return ROLE_SYMBOLS.get(room.role, "?")
    return "?"


def _rich_room_symbol(dungeon: DungeonMap, room_id: str, state: DraftMapState) -> Text:
    room = dungeon.rooms[room_id]
    if state.current_room_id == room_id:
        return Text(" P ", style="bold black on bright_cyan")
    if room_id in state.cleared_rooms:
        return Text(" . ", style="green")
    if requirement_met(state, room.requirement):
        symbol = ROLE_SYMBOLS.get(room.role, "?")
        style_by_role = {
            "entrance": "bold cyan",
            "combat": "bold red",
            "event": "bold yellow",
            "treasure": "bold yellow",
            "boss": "bold magenta",
            "exit": "bold green",
        }
        return Text(f" {symbol} ", style=style_by_role.get(room.role, "white"))
    return Text(" ? ", style="dim")


def _room_anchor(room) -> tuple[int, int]:
    return (room.x * 2, room.y * 2)


def _visible_room(room_id: str, dungeon: DungeonMap, state: DraftMapState) -> bool:
    room = dungeon.rooms[room_id]
    return room_id == (state.current_room_id or dungeon.entrance_room_id) or room_id in state.cleared_rooms or requirement_met(state, room.requirement)


def _corridor_connections(dungeon: DungeonMap, state: DraftMapState) -> dict[tuple[int, int], set[str]]:
    connections: dict[tuple[int, int], set[str]] = {}
    for room in dungeon.rooms.values():
        if not _visible_room(room.room_id, dungeon, state):
            continue
        for target_id in room.exits:
            if not _visible_room(target_id, dungeon, state):
                continue
            target = dungeon.rooms[target_id]
            path = room_travel_path(dungeon, room, target)
            if not path:
                continue
            points = [_room_anchor(room), *path]
            for index in range(1, len(points) - 1):
                prev_x, prev_y = points[index - 1]
                current = points[index]
                next_x, next_y = points[index + 1]
                curr_x, curr_y = current
                cell_connections = connections.setdefault(current, set())
                if prev_x < curr_x:
                    cell_connections.add("L")
                elif prev_x > curr_x:
                    cell_connections.add("R")
                elif prev_y < curr_y:
                    cell_connections.add("U")
                elif prev_y > curr_y:
                    cell_connections.add("D")
                if next_x < curr_x:
                    cell_connections.add("L")
                elif next_x > curr_x:
                    cell_connections.add("R")
                elif next_y < curr_y:
                    cell_connections.add("U")
                elif next_y > curr_y:
                    cell_connections.add("D")
    return connections


def _corridor_glyph(directions: set[str]) -> str:
    if not directions:
        return "   "
    if directions.issubset({"L", "R"}):
        return "---"
    if directions.issubset({"U", "D"}):
        return " | "
    return " + "


def _rich_corridor_glyph(directions: set[str]) -> Text:
    glyph = _corridor_glyph(directions)
    if not directions:
        return Text(glyph)
    if directions.issubset({"L", "R"}):
        return Text(glyph, style="cyan")
    if directions.issubset({"U", "D"}):
        return Text(glyph, style="cyan")
    return Text(glyph, style="bold cyan")


def _dungeon_render_rows(dungeon: DungeonMap, state: DraftMapState) -> list[list[str]]:
    fine_width = max(1, dungeon.width * 2 - 1)
    fine_height = max(1, dungeon.height * 2 - 1)
    room_lookup = {_room_anchor(room): room for room in dungeon.rooms.values()}
    corridor_lookup = _corridor_connections(dungeon, state)
    rows: list[list[str]] = []
    for y in range(fine_height):
        row: list[str] = []
        for x in range(fine_width):
            room = room_lookup.get((x, y))
            if room is not None:
                row.append(_room_symbol(dungeon, room.room_id, state))
            else:
                row.append(_corridor_glyph(corridor_lookup.get((x, y), set())))
        rows.append(row)
    return rows


def _dungeon_render_rows_rich(dungeon: DungeonMap, state: DraftMapState) -> list[list[Text]]:
    fine_width = max(1, dungeon.width * 2 - 1)
    fine_height = max(1, dungeon.height * 2 - 1)
    room_lookup = {_room_anchor(room): room for room in dungeon.rooms.values()}
    corridor_lookup = _corridor_connections(dungeon, state)
    rows: list[list[Text]] = []
    for y in range(fine_height):
        row: list[Text] = []
        for x in range(fine_width):
            room = room_lookup.get((x, y))
            if room is not None:
                row.append(_rich_room_symbol(dungeon, room.room_id, state))
            else:
                row.append(_rich_corridor_glyph(corridor_lookup.get((x, y), set())))
        rows.append(row)
    return rows


def build_dungeon_panel_text(dungeon: DungeonMap, state: DraftMapState) -> str:
    grid = _dungeon_render_rows(dungeon, state)
    lines: list[str] = []
    border = "+" + "-" * (len(grid[0]) * 3) + "+"
    lines.append(border)
    for row in grid:
        lines.append("|" + "".join(f" {cell} " if len(cell) == 1 else cell for cell in row) + "|")
    lines.append(border)

    room = dungeon.rooms[state.current_room_id or dungeon.entrance_room_id]
    lines.append("")
    lines.append(f"Current room: {room.title}")
    lines.append("Available moves:")
    lines.extend(_directional_exit_lines(dungeon, state))
    lines.append("")
    lines.append("Legend: P you, . cleared, E combat, * event, T treasure, B boss, ? locked, corridors show open routes")
    return _box_panel(dungeon.title, lines, width=78)


def build_dungeon_panel(dungeon: DungeonMap, state: DraftMapState) -> Panel:
    grid = Table.grid(padding=0)
    rendered_rows = _dungeon_render_rows_rich(dungeon, state)
    for _ in range(len(rendered_rows[0])):
        grid.add_column(justify="center", width=3)

    for row in rendered_rows:
        grid.add_row(*row)

    room = dungeon.rooms[state.current_room_id or dungeon.entrance_room_id]
    info = Table.grid(expand=True, padding=(0, 1))
    info.add_column(ratio=2)
    info.add_column(ratio=3)
    info.add_row(Text("Current Room", style="bold cyan"), Text(room.title, style="bold white"))
    info.add_row(Text("Role", style="cyan"), Text(room.role.upper(), style="magenta"))
    info.add_row(Text("Summary", style="cyan"), Text(room.summary, style="white"))
    info.add_row(
        Text("Available Moves", style="cyan"),
        Text(_directional_exit_text(dungeon, state), style="green" if current_room_exits(dungeon, state) else "dim"),
    )

    legend = Table.grid(expand=True)
    legend.add_column(justify="center")
    legend.add_column(justify="center")
    legend.add_column(justify="center")
    legend.add_row(
        Text("P player", style="bold black on bright_cyan"),
        Text(". cleared  E fight  * event  T treasure", style="bold yellow"),
        Text("B boss  ? locked  corridors mark open routes", style="bold magenta"),
    )

    group = Group(Align.center(grid), info, legend)
    return Panel(group, title=dungeon.title, border_style="magenta", box=box.ROUNDED, padding=(0, 1))


def build_screen_text(
    *,
    blueprint: HybridMapBlueprint,
    state: DraftMapState,
    dungeon: DungeonMap | None = None,
    player_name: str = "Draft Hero",
    hp_text: str = "34/40",
    gold: int = 27,
    quest_text: str = "Stop the Watchtower Raids",
    scene_text: str = "A draft presentation pass using a rich-guided panel layout.",
) -> str:
    sections = [
        build_hud_panel_text(player_name=player_name, hp_text=hp_text, gold=gold, quest_text=quest_text),
        build_overworld_panel_text(blueprint, state),
    ]
    if dungeon is not None:
        sections.append(build_dungeon_panel_text(dungeon, state))
    sections.append(_box_panel("Scene", [scene_text, "Actions would render below the active map panel."]))
    return "\n\n".join(sections)


def build_scene_panel(scene_text: str) -> Panel:
    table = Table.grid(expand=True)
    table.add_column()
    table.add_row(Text(scene_text, style="white"))
    table.add_row(Text("Actions would render below the active map panel.", style="dim"))
    return Panel(table, title="Scene", border_style="yellow", box=box.ROUNDED, padding=(0, 1))


def render_screen_with_rich(
    *,
    blueprint: HybridMapBlueprint,
    state: DraftMapState,
    dungeon: DungeonMap | None = None,
    player_name: str = "Draft Hero",
    hp_text: str = "34/40",
    gold: int = 27,
    quest_text: str = "Stop the Watchtower Raids",
    scene_text: str = "A draft presentation pass using a rich-guided panel layout.",
    console: Console | None = None,
) -> str:
    if not RICH_AVAILABLE:
        return build_screen_text(
            blueprint=blueprint,
            state=state,
            dungeon=dungeon,
            player_name=player_name,
            hp_text=hp_text,
            gold=gold,
            quest_text=quest_text,
            scene_text=scene_text,
        )

    active_console = console or Console()

    hud = build_hud_panel(
        player_name=player_name,
        hp_text=hp_text,
        gold=gold,
        quest_text=quest_text,
    )

    if dungeon is None:
        body = build_overworld_panel(blueprint, state)
    else:
        if active_console.width >= 140:
            body = Table.grid(expand=True)
            body.add_column(ratio=5)
            body.add_column(ratio=4)
            body.add_row(
                build_overworld_panel(blueprint, state),
                build_dungeon_panel(dungeon, state),
            )
        else:
            body = Group(
                build_overworld_panel(blueprint, state),
                build_dungeon_panel(dungeon, state),
            )

    active_console.print(Group(hud, body, build_scene_panel(scene_text)))
    return ""
