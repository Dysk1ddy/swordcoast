from __future__ import annotations

from ..data.act1_hybrid_map import ACT1_HYBRID_MAP
from ..runtime import DraftMapState, render_screen_with_rich


def main() -> None:
    state = DraftMapState(
        current_node_id="phandalin_hub",
        current_room_id="breach_gate",
        flags={
            "act1_started",
            "phandalin_arrived",
            "old_owl_well_cleared",
            "wyvern_tor_cleared",
            "ashfall_gate_breached",
        },
        active_quests={"secure_miners_road"},
        cleared_rooms={"breach_gate"},
    )
    dungeon = ACT1_HYBRID_MAP.dungeons["ashfall_watch_fort"]
    render_screen_with_rich(
        blueprint=ACT1_HYBRID_MAP,
        state=state,
        dungeon=dungeon,
        player_name="Tolan's Company",
        hp_text="52/64",
        gold=143,
        quest_text="Stop the Watchtower Raids",
        scene_text="Ashfall Watch is framed as a node-based destination that opens into a room-grid assault.",
    )


if __name__ == "__main__":
    main()
