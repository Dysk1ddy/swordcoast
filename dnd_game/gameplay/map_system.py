from __future__ import annotations

from typing import Any

from ..content import create_enemy
from ..drafts.map_system import ACT1_HYBRID_MAP
from ..drafts.map_system.runtime import (
    DraftMapState,
    DungeonMap,
    DungeonRoom,
    build_dungeon_panel,
    build_dungeon_panel_text,
    build_overworld_panel,
    build_overworld_panel_text,
    current_room_exits,
    requirement_met,
    room_direction,
)
from ..ui.rich_render import RICH_AVAILABLE
from .encounter import Encounter


def _requirement_flag_names(*, requirement) -> set[str]:
    return {
        *requirement.all_flags,
        *requirement.any_flags,
        *requirement.blocked_flags,
    }


def _collect_act1_flag_names() -> set[str]:
    flag_names: set[str] = set()
    for node in ACT1_HYBRID_MAP.nodes.values():
        flag_names.update(_requirement_flag_names(requirement=node.requirement))
    for edge in ACT1_HYBRID_MAP.edges:
        flag_names.update(_requirement_flag_names(requirement=edge.requirement))
    for beat in ACT1_HYBRID_MAP.story_beats:
        flag_names.update(_requirement_flag_names(requirement=beat.requirement))
        flag_names.update(beat.grants_flags)
    for dungeon in ACT1_HYBRID_MAP.dungeons.values():
        flag_names.update(dungeon.completion_flags)
        for room in dungeon.rooms.values():
            flag_names.update(_requirement_flag_names(requirement=room.requirement))
            flag_names.update(room.clear_grants_flags)
    return flag_names


ACT1_MAP_FLAG_NAMES = _collect_act1_flag_names()
ACT1_SCENE_TO_NODE_ID = {node.scene_key: node_id for node_id, node in ACT1_HYBRID_MAP.nodes.items()}


class MapSystemMixin:
    MAP_STATE_KEY = "map_state"

    def ensure_state_integrity(self) -> None:
        super().ensure_state_integrity()
        if self.state is None:
            self._clear_map_view_cache()
            self._act1_map_cache_state_owner_id = None
            return
        owner_id = id(self.state)
        if getattr(self, "_act1_map_cache_state_owner_id", None) != owner_id:
            self._act1_map_cache_state_owner_id = owner_id
            self._clear_map_view_cache()
        self._ensure_map_state_payload()
        self._sync_map_state_with_scene()

    def compact_hud_scene_key(self) -> tuple[int, str] | None:
        base = super().compact_hud_scene_key()
        if base is None or self.state is None:
            return base
        dungeon = self.current_act1_dungeon()
        if dungeon is None:
            return base
        room_id = str(self._map_state_payload().get("current_room_id") or "")
        return (base[0], f"{base[1]}::{room_id}")

    def hud_location_label(self) -> str:
        base = super().hud_location_label()
        dungeon = self.current_act1_dungeon()
        if dungeon is None:
            return base
        room = self.current_act1_room(dungeon)
        return f"{base} / {room.title}"

    def hud_objective_label(self) -> str:
        dungeon = self.current_act1_dungeon()
        if dungeon is None:
            return super().hud_objective_label()
        room = self.current_act1_room(dungeon)
        if not self.room_is_cleared(room.room_id):
            if room.role == "boss":
                return f"Break {room.title}."
            return f"Secure {room.title}."
        exits = current_room_exits(dungeon, self.act1_map_state())
        uncleared_exits = [candidate for candidate in exits if not self.room_is_cleared(candidate.room_id)]
        if uncleared_exits:
            if len(uncleared_exits) == 1:
                return f"Advance to {uncleared_exits[0].title}."
            return "Choose the next route."
        return "Find the open wing or withdraw."

    def _ensure_map_state_payload(self) -> None:
        assert self.state is not None
        raw = self.state.flags.get(self.MAP_STATE_KEY)
        if not isinstance(raw, dict):
            raw = {}
        payload = {
            "current_node_id": str(raw.get("current_node_id") or ACT1_HYBRID_MAP.start_node_id),
            "current_dungeon_id": raw.get("current_dungeon_id"),
            "current_room_id": raw.get("current_room_id"),
            "visited_nodes": self._string_list(raw.get("visited_nodes")),
            "cleared_rooms": self._string_list(raw.get("cleared_rooms")),
            "seen_story_beats": self._string_list(raw.get("seen_story_beats")),
            "room_history": self._string_list(raw.get("room_history")),
        }
        self.state.flags[self.MAP_STATE_KEY] = payload

    def _map_state_payload(self) -> dict[str, Any]:
        assert self.state is not None
        self._ensure_map_state_payload()
        payload = self.state.flags[self.MAP_STATE_KEY]
        assert isinstance(payload, dict)
        return payload

    def _string_list(self, raw: Any) -> list[str]:
        if isinstance(raw, list):
            values = raw
        elif isinstance(raw, tuple):
            values = list(raw)
        else:
            values = []
        seen: set[str] = set()
        normalized: list[str] = []
        for value in values:
            if not isinstance(value, str):
                continue
            if value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    def _map_view_cache(self) -> dict[str, Any]:
        cache = getattr(self, "_act1_map_view_cache", None)
        if not isinstance(cache, dict):
            cache = {"overworld": None, "dungeon": None}
            self._act1_map_view_cache = cache
        return cache

    def _map_state_signature(self, state: DraftMapState) -> tuple[Any, ...]:
        return (
            state.current_node_id,
            state.current_room_id,
            tuple(sorted(state.flags)),
            tuple(sorted(state.active_quests)),
            tuple(sorted(state.completed_quests)),
            tuple(sorted(state.visited_nodes)),
            tuple(sorted(state.cleared_rooms)),
            tuple(sorted(state.seen_story_beats)),
        )

    def _clear_map_view_cache(self, *views: str) -> None:
        cache = self._map_view_cache()
        targets = views or ("overworld", "dungeon")
        for view in targets:
            cache[view] = None

    def _sync_story_beats_from_flags(self) -> None:
        if self.state is None:
            return
        payload = self._map_state_payload()
        seen = set(payload["seen_story_beats"])
        if self.state.flags.get("phandalin_council_seen"):
            seen.add("stonehill_council")
        if self.state.flags.get("phandalin_after_watch_seen"):
            seen.add("lantern_vigil")
        payload["seen_story_beats"] = sorted(seen)

    def _sync_map_state_with_scene(self, *, force_node_id: str | None = None) -> None:
        assert self.state is not None
        payload = self._map_state_payload()
        node_id = force_node_id or ACT1_SCENE_TO_NODE_ID.get(self.state.current_scene)
        if node_id is None and self.state.current_scene == "act1_complete":
            node_id = "emberhall_cellars"
        if node_id is None:
            self._sync_story_beats_from_flags()
            return
        node = ACT1_HYBRID_MAP.nodes[node_id]
        payload["current_node_id"] = node_id
        if node_id not in payload["visited_nodes"]:
            payload["visited_nodes"].append(node_id)
        if node.enters_dungeon_id is None or self.state.current_scene != node.scene_key:
            payload["current_dungeon_id"] = None
            payload["current_room_id"] = None
            payload["room_history"] = []
            self._compact_hud_last_scene_key = None
            self._sync_story_beats_from_flags()
            return
        dungeon = ACT1_HYBRID_MAP.dungeons[node.enters_dungeon_id]
        payload["current_dungeon_id"] = dungeon.dungeon_id
        if payload.get("current_room_id") not in dungeon.rooms:
            payload["current_room_id"] = dungeon.entrance_room_id
        payload["room_history"] = [room_id for room_id in payload["room_history"] if room_id in dungeon.rooms]
        self._compact_hud_last_scene_key = None
        self._sync_story_beats_from_flags()

    def act1_map_state(self) -> DraftMapState:
        assert self.state is not None
        self._sync_map_state_with_scene()
        payload = self._map_state_payload()
        active_quests = {
            quest_id
            for quest_id, entry in self.state.quests.items()
            if getattr(entry, "status", "") in {"active", "ready_to_turn_in"}
        }
        completed_quests = {
            quest_id
            for quest_id, entry in self.state.quests.items()
            if getattr(entry, "status", "") == "completed"
        }
        flags = {
            flag_name
            for flag_name in ACT1_MAP_FLAG_NAMES
            if self.state.flags.get(flag_name)
        }
        return DraftMapState(
            current_node_id=str(payload["current_node_id"]),
            current_room_id=str(payload["current_room_id"]) if payload.get("current_room_id") else None,
            flags=flags,
            active_quests=active_quests,
            completed_quests=completed_quests,
            visited_nodes=set(payload["visited_nodes"]),
            cleared_rooms=set(payload["cleared_rooms"]),
            seen_story_beats=set(payload["seen_story_beats"]),
        )

    def current_act1_dungeon(self) -> DungeonMap | None:
        if self.state is None:
            return None
        payload = self._map_state_payload()
        dungeon_id = payload.get("current_dungeon_id")
        if not isinstance(dungeon_id, str):
            return None
        return ACT1_HYBRID_MAP.dungeons.get(dungeon_id)

    def current_act1_room(self, dungeon: DungeonMap) -> DungeonRoom:
        payload = self._map_state_payload()
        room_id = payload.get("current_room_id")
        if not isinstance(room_id, str) or room_id not in dungeon.rooms:
            room_id = dungeon.entrance_room_id
        return dungeon.rooms[room_id]

    def room_is_cleared(self, room_id: str) -> bool:
        return room_id in set(self._map_state_payload()["cleared_rooms"])

    def complete_map_room(self, dungeon: DungeonMap, room_id: str) -> None:
        assert self.state is not None
        payload = self._map_state_payload()
        if room_id not in payload["cleared_rooms"]:
            payload["cleared_rooms"].append(room_id)
        room = dungeon.rooms[room_id]
        for flag_name in room.clear_grants_flags:
            self.state.flags[flag_name] = True
        self._clear_map_view_cache("dungeon")
        self._compact_hud_last_scene_key = None

    def set_current_map_room(self, room_id: str, *, announce: bool = False, movement_text: str = "") -> None:
        payload = self._map_state_payload()
        current_room_id = payload.get("current_room_id")
        if current_room_id == room_id:
            return
        if isinstance(current_room_id, str) and current_room_id:
            payload["room_history"].append(current_room_id)
        payload["current_room_id"] = room_id
        self._clear_map_view_cache("dungeon")
        self._compact_hud_last_scene_key = None
        if announce:
            self.say(movement_text or f"You move toward {room_id.replace('_', ' ')}.")
        dungeon = self.current_act1_dungeon()
        if dungeon is not None:
            self.render_act1_dungeon_map(dungeon, force=True)

    def backtrack_map_room(self, dungeon: DungeonMap) -> bool:
        payload = self._map_state_payload()
        while payload["room_history"]:
            previous_room_id = payload["room_history"].pop()
            if previous_room_id in dungeon.rooms:
                payload["current_room_id"] = previous_room_id
                self._clear_map_view_cache("dungeon")
                self._compact_hud_last_scene_key = None
                self.say(f"You backtrack toward {dungeon.rooms[previous_room_id].title}.")
                self.render_act1_dungeon_map(dungeon, force=True)
                return True
        return False

    def peek_backtrack_room(self, dungeon: DungeonMap) -> DungeonRoom | None:
        payload = self._map_state_payload()
        for room_id in reversed(payload["room_history"]):
            if room_id in dungeon.rooms:
                return dungeon.rooms[room_id]
        return None

    def travel_to_act1_node(self, node_id: str) -> None:
        assert self.state is not None
        payload = self._map_state_payload()
        node = ACT1_HYBRID_MAP.nodes[node_id]
        payload["current_node_id"] = node_id
        if node_id not in payload["visited_nodes"]:
            payload["visited_nodes"].append(node_id)
        if node.enters_dungeon_id is None:
            payload["current_dungeon_id"] = None
            payload["current_room_id"] = None
            payload["room_history"] = []
        else:
            dungeon = ACT1_HYBRID_MAP.dungeons[node.enters_dungeon_id]
            payload["current_dungeon_id"] = dungeon.dungeon_id
            payload["current_room_id"] = dungeon.entrance_room_id
            payload["room_history"] = []
        self.state.current_scene = node.scene_key
        self._clear_map_view_cache()
        self._compact_hud_last_scene_key = None
        self.render_act1_overworld_map(force=True)

    def return_to_phandalin(self, text: str) -> None:
        assert self.state is not None
        payload = self._map_state_payload()
        payload["current_node_id"] = "phandalin_hub"
        if "phandalin_hub" not in payload["visited_nodes"]:
            payload["visited_nodes"].append("phandalin_hub")
        payload["current_dungeon_id"] = None
        payload["current_room_id"] = None
        payload["room_history"] = []
        self.state.current_scene = "phandalin_hub"
        self._clear_map_view_cache()
        self._compact_hud_last_scene_key = None
        self.say(text)
        self.render_act1_overworld_map(force=True)

    def act1_hybrid_map_available(self) -> bool:
        if self.state is None:
            return False
        return self.state.current_scene in ACT1_SCENE_TO_NODE_ID or self.state.current_scene == "act1_complete"

    def render_act1_overworld_map(self, *, force: bool = False) -> None:
        if not self.act1_hybrid_map_available():
            return
        state = self.act1_map_state()
        cache = self._map_view_cache()
        cache_key = self._map_state_signature(state)
        if not force and cache.get("overworld") == cache_key:
            return
        panel = build_overworld_panel(ACT1_HYBRID_MAP, state)
        if self.should_use_rich_ui() and RICH_AVAILABLE and self.emit_rich(panel, width=max(108, self.rich_console_width())):
            cache["overworld"] = cache_key
            self.output_fn("")
            return
        for line in build_overworld_panel_text(ACT1_HYBRID_MAP, state).splitlines():
            self.output_fn(line)
        cache["overworld"] = cache_key
        self.output_fn("")

    def render_act1_dungeon_map(self, dungeon: DungeonMap, *, force: bool = False) -> None:
        state = self.act1_map_state()
        cache = self._map_view_cache()
        cache_key = (dungeon.dungeon_id, self._map_state_signature(state))
        if not force and cache.get("dungeon") == cache_key:
            return
        if self.should_use_rich_ui() and RICH_AVAILABLE and self.emit_rich(
            build_dungeon_panel(dungeon, state),
            width=max(108, self.rich_console_width()),
        ):
            cache["dungeon"] = cache_key
            self.output_fn("")
            return
        for line in build_dungeon_panel_text(dungeon, state).splitlines():
            self.output_fn(line)
        cache["dungeon"] = cache_key
        self.output_fn("")

    def _movement_option_label(self, room: DungeonRoom, candidate: DungeonRoom) -> str:
        dungeon = self.current_act1_dungeon()
        direction = room_direction(room, candidate, dungeon)
        verb = "Advance to" if not self.room_is_cleared(candidate.room_id) else "Return to"
        return self.skill_tag(f"MOVE {direction}", self.action_option(f"{verb} {candidate.title}"))

    def act1_room_navigation_options(self, dungeon: DungeonMap) -> list[tuple[str, str, str]]:
        room = self.current_act1_room(dungeon)
        options: list[tuple[str, str, str]] = []
        seen_targets: set[str] = set()
        exits = current_room_exits(dungeon, self.act1_map_state())
        ordered_exits = sorted(
            exits,
            key=lambda candidate: (
                self.room_is_cleared(candidate.room_id),
                {"UP": 0, "RIGHT": 1, "DOWN": 2, "LEFT": 3, "HERE": 4}[room_direction(room, candidate, dungeon)],
                candidate.title,
            ),
        )
        for candidate in ordered_exits:
            options.append(("move", candidate.room_id, self._movement_option_label(room, candidate)))
            seen_targets.add(candidate.room_id)
        previous_room = self.peek_backtrack_room(dungeon)
        if previous_room is not None and previous_room.room_id not in seen_targets:
            options.append(("move", previous_room.room_id, self._movement_option_label(room, previous_room)))
        options.append(("withdraw", "phandalin_hub", self.action_option("Withdraw to Phandalin")))
        return options

    def open_map_menu(self) -> None:
        if not self.act1_hybrid_map_available():
            self.say("There is no active hybrid map at this point in the adventure.")
            return
        dungeon = self.current_act1_dungeon()
        while True:
            choice = self.choose(
                "Map menu",
                [
                    "Overworld",
                    dungeon.title if dungeon is not None else "Dungeon (not available here)",
                    "Back",
                ],
                allow_meta=False,
                show_hud=False,
            )
            if choice == 1:
                self.banner("Overworld Map")
                self.render_act1_overworld_map(force=True)
                continue
            if choice == 2:
                if dungeon is None:
                    self.say("There is no dungeon map to show from this location.")
                    continue
                self.banner(dungeon.title)
                self.render_act1_dungeon_map(dungeon, force=True)
                continue
            return

    def handle_meta_command(self, raw: str) -> bool:
        if raw.lower() == "map":
            if self.state is None:
                self.say("There is no active map yet.")
            else:
                self.open_map_menu()
            return True
        return super().handle_meta_command(raw)

    def scene_phandalin_hub(self) -> None:
        assert self.state is not None
        self._sync_map_state_with_scene(force_node_id="phandalin_hub")
        self.banner("Phandalin")
        if not self.state.flags.get("phandalin_arrived"):
            self.say(
                "Phandalin rises from rocky foothills in a scatter of rebuilt homes, old stone scars, orchard walls, wagon sheds, and lantern-lit mud lanes. "
                "There are no proper walls, no garrison worth the name, and too many decent people living one bad week away from disaster.",
                typed=True,
            )
            self.state.flags["phandalin_arrived"] = True
            self.add_journal("You reached Phandalin, a hard-bitten frontier town under growing Ashen Brand pressure.")
            choice = self.scenario_choice(
                "How do you enter town?",
                [
                    self.quoted_option("INSIGHT", "I want to read the mood of the town before I speak."),
                    self.quoted_option("PERSUASION", "Let them know Neverwinter sent help."),
                    self.skill_tag("INVESTIGATION", self.action_option("Survey the tracks, barricades, and weak points first.")),
                ]
                + [text for _, text in self.scene_identity_options("phandalin_arrival")],
                allow_meta=False,
            )
            identity_options = self.scene_identity_options("phandalin_arrival")
            if choice > 3:
                selection_key, _ = identity_options[choice - 4]
                if self.handle_scene_identity_action("phandalin_arrival", selection_key):
                    return self.scene_phandalin_hub()
            elif choice == 1:
                self.player_speaker("I want to read the mood of the town before I speak.")
                success = self.skill_check(self.state.player, "Insight", 12, context="to gauge the town's fear")
                if success:
                    self.say(
                        "You catch the way fear keeps pulling the crowd's attention toward manor-side ruins, the east road, and a handful of people everybody seems to quietly trust."
                    )
                    self.add_clue(
                        "Phandalin's fear points in three directions: the east road, the old manor hill, and the few locals still holding the place together."
                    )
                    self.reward_party(xp=10, reason="reading Phandalin's mood on arrival")
                else:
                    self.say("The town's fear is real, but too tangled to untangle in one glance.")
            elif choice == 2:
                self.player_speaker("Let them know Neverwinter sent help.")
                success = self.skill_check(self.state.player, "Persuasion", 12, context="to steady the town's nerves")
                if success:
                    self.say("A few shoulders ease as your words sound more like a promise than a performance.")
                    self.reward_party(xp=10, gold=6, reason="reassuring Phandalin on arrival")
                else:
                    self.say("People listen, but frontier caution clings harder than hope.")
            else:
                self.player_action("Show me the tracks, barricades, and weak points first.")
                success = self.skill_check(self.state.player, "Investigation", 12, context="to assess the town's defenses")
                if success:
                    self.say("Fresh wagon ruts, anxious repairs, and redirected lanes give you a usable picture of how fear is reshaping the town.")
                    self.add_clue("Recent wagon ruts suggest the Ashen Brand watches both the east road and the manor-side lanes.")
                    self.reward_party(xp=10, reason="surveying Phandalin's defenses")
                else:
                    self.say("There are too many overlapping tracks and half-finished repairs for a quick clean read.")

        self.run_phandalin_council_event()
        self.run_after_watch_gathering()
        self._sync_story_beats_from_flags()

        while True:
            self.banner("Phandalin")
            self.render_act1_overworld_map()
            options: list[tuple[str, str]] = [
                ("steward", self.action_option("Report to Steward Tessa Harrow")),
                ("inn", self.action_option("Visit the Stonehill Inn")),
                ("shrine", self.action_option("Stop by the shrine of Tymora")),
                ("barthen", self.skill_tag("TRADE", self.action_option("Browse Barthen's Provisions"))),
                ("linene", self.skill_tag("TRADE", self.action_option("Call on Linene Graywind at the Lionshield trading post"))),
                ("orchard", self.action_option("Walk the old walls of Edermath Orchard")),
                ("exchange", self.action_option("Step into the Miner's Exchange")),
                ("camp", self.action_option("Return to camp")),
                ("rest", self.action_option("Take a short rest")),
            ]
            if not self.state.flags.get("old_owl_well_cleared"):
                label = self.action_option("Investigate Old Owl Well")
                if not self.can_visit_old_owl_well():
                    label = self.action_option("Investigate Old Owl Well (need a lead)")
                options.append(("old_owl", label))
            if not self.state.flags.get("wyvern_tor_cleared"):
                label = self.action_option("Hunt the raiders at Wyvern Tor")
                if not self.can_visit_wyvern_tor():
                    label = self.action_option("Hunt the raiders at Wyvern Tor (need a lead)")
                elif self.should_warn_for_wyvern_tor():
                    label = self.action_option(
                        f"Hunt the raiders at Wyvern Tor (recommended level {self.wyvern_tor_recommended_level()})"
                    )
                options.append(("wyvern", label))
            if not self.state.flags.get("ashfall_watch_cleared"):
                label = self.action_option("Ride for Ashfall Watch")
                if not self.act1_side_paths_cleared():
                    label = self.action_option("Ride for Ashfall Watch (clear Old Owl Well and Wyvern Tor first)")
                options.append(("ashfall", label))
            elif not self.state.flags.get("tresendar_cleared"):
                label = self.action_option("Descend beneath Tresendar Manor")
                if not self.state.flags.get("tresendar_revealed"):
                    label = self.action_option("Descend beneath Tresendar Manor (wait for a firmer lead)")
                options.append(("tresendar", label))
            else:
                options.append(("emberhall", self.action_option("Descend into Emberhall Cellars")))

            choice = self.scenario_choice("Where do you go next?", [text for _, text in options])
            selection_key, _ = options[choice - 1]
            if selection_key == "steward":
                self.visit_steward()
            elif selection_key == "inn":
                self.visit_stonehill_inn()
            elif selection_key == "shrine":
                self.visit_shrine()
            elif selection_key == "barthen":
                self.visit_barthen_provisions()
            elif selection_key == "linene":
                self.visit_trading_post()
            elif selection_key == "orchard":
                self.visit_edermath_orchard()
            elif selection_key == "exchange":
                self.visit_miners_exchange()
            elif selection_key == "camp":
                self.open_camp_menu()
            elif selection_key == "rest":
                self.short_rest()
            elif selection_key == "old_owl":
                if not self.can_visit_old_owl_well():
                    self.say("You need a firmer lead on the well before marching the party into empty scrub.")
                    continue
                self.travel_to_act1_node("old_owl_well")
                return
            elif selection_key == "wyvern":
                if not self.can_visit_wyvern_tor():
                    self.say("You still need somebody to point you toward the tor and the raiders haunting it.")
                    continue
                if not self.confirm_wyvern_tor_departure():
                    continue
                self.travel_to_act1_node("wyvern_tor")
                return
            elif selection_key == "ashfall":
                if not self.act1_side_paths_cleared():
                    self.say("Ashfall Watch is still too dangerous to take cleanly without dealing with the outer threats first.")
                    continue
                self.travel_to_act1_node("ashfall_watch")
                return
            elif selection_key == "tresendar":
                if not self.state.flags.get("tresendar_revealed"):
                    self.say("You need a firmer lead before committing to the buried manor routes.")
                    continue
                self.travel_to_act1_node("tresendar_manor")
                return
            else:
                self.travel_to_act1_node("emberhall_cellars")
                return

    def scene_old_owl_well(self) -> None:
        self.run_act1_dungeon("old_owl_well")

    def scene_wyvern_tor(self) -> None:
        self.run_act1_dungeon("wyvern_tor")

    def scene_ashfall_watch(self) -> None:
        self.run_act1_dungeon("ashfall_watch")

    def scene_tresendar_manor(self) -> None:
        self.run_act1_dungeon("tresendar_manor")

    def scene_emberhall_cellars(self) -> None:
        self.run_act1_dungeon("emberhall_cellars")

    def run_act1_dungeon(self, node_id: str) -> None:
        assert self.state is not None
        self._sync_map_state_with_scene(force_node_id=node_id)
        node = ACT1_HYBRID_MAP.nodes[node_id]
        dungeon = ACT1_HYBRID_MAP.dungeons[str(node.enters_dungeon_id)]

        while self.state is not None and self.state.current_scene == node.scene_key:
            room = self.current_act1_room(dungeon)
            self.banner(node.title)
            self.render_act1_dungeon_map(dungeon)
            if not self.room_is_cleared(room.room_id):
                self._run_act1_room(node_id, dungeon, room)
                if self.state.current_scene != node.scene_key:
                    return
                continue

            exits = current_room_exits(dungeon, self.act1_map_state())
            remaining_open_rooms = [
                candidate
                for candidate in dungeon.rooms.values()
                if candidate.room_id != room.room_id
                and not self.room_is_cleared(candidate.room_id)
                and requirement_met(self.act1_map_state(), candidate.requirement)
            ]
            if not exits and remaining_open_rooms:
                self.say(f"{room.title} is secure, but another wing is still open: {remaining_open_rooms[0].title}.")

            options = self.act1_room_navigation_options(dungeon)

            choice = self.scenario_choice(
                f"What do you do from {room.title}?",
                [text for _, _, text in options],
                allow_meta=False,
            )
            action, destination, _ = options[choice - 1]
            if action == "move":
                next_room = dungeon.rooms[destination]
                self.set_current_map_room(
                    destination,
                    announce=True,
                    movement_text=f"You move {room_direction(room, next_room, dungeon).lower()} toward {next_room.title}.",
                )
                continue
            self.return_to_phandalin(f"You withdraw from {node.title} and ride back to Phandalin to regroup.")
            return

    def _run_act1_room(self, node_id: str, dungeon: DungeonMap, room: DungeonRoom) -> None:
        handlers = {
            ("old_owl_well", "well_ring"): self._old_owl_well_ring,
            ("old_owl_well", "salt_cart"): self._old_owl_salt_cart,
            ("old_owl_well", "supply_trench"): self._old_owl_supply_trench,
            ("old_owl_well", "gravecaller_lip"): self._old_owl_gravecaller_lip,
            ("wyvern_tor", "goat_path"): self._wyvern_goat_path,
            ("wyvern_tor", "drover_hollow"): self._wyvern_drover_hollow,
            ("wyvern_tor", "shrine_ledge"): self._wyvern_shrine_ledge,
            ("wyvern_tor", "high_shelf"): self._wyvern_high_shelf,
            ("ashfall_watch", "breach_gate"): self._ashfall_breach_gate,
            ("ashfall_watch", "prisoner_yard"): self._ashfall_prisoner_yard,
            ("ashfall_watch", "signal_basin"): self._ashfall_signal_basin,
            ("ashfall_watch", "lower_barracks"): self._ashfall_lower_barracks,
            ("ashfall_watch", "rukhar_command"): self._ashfall_rukhar_command,
            ("tresendar_manor", "hidden_stair"): self._tresendar_hidden_stair,
            ("tresendar_manor", "cellar_intake"): self._tresendar_cellar_intake,
            ("tresendar_manor", "cistern_walk"): self._tresendar_cistern_walk,
            ("tresendar_manor", "cage_store"): self._tresendar_cage_store,
            ("tresendar_manor", "nothic_lair"): self._tresendar_nothic_lair,
            ("emberhall_cellars", "antechamber"): self._emberhall_antechamber,
            ("emberhall_cellars", "ledger_chain"): self._emberhall_ledger_chain,
            ("emberhall_cellars", "ash_archive"): self._emberhall_ash_archive,
            ("emberhall_cellars", "black_reserve"): self._emberhall_black_reserve,
            ("emberhall_cellars", "varyn_sanctum"): self._emberhall_varyn_sanctum,
        }
        handler = handlers[(node_id, room.room_id)]
        handler(dungeon, room)

    def _old_owl_well_ring(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        if not self.state.flags.get("old_owl_well_seen"):
            self.say(
                "The old watchtower rises from the scrub like a cracked finger of Netherese stone. Dig lines, corpse-salt circles, and half-collapsed tents surround the well itself, "
                "and every gust of wind seems to carry up dust that should have stayed buried.",
                typed=True,
            )
            self.state.flags["old_owl_well_seen"] = True
        party_size = self.act1_party_size()
        enemies = [create_enemy("skeletal_sentry"), create_enemy("bandit", name="Ashen Brand Fixer")]
        if party_size >= 3:
            enemies.append(self.act1_pick_enemy(("skeletal_sentry", "rust_shell_scuttler", "ashstone_percher", "briar_twig")))
        hero_bonus = self.apply_scene_companion_support("old_owl_well")
        choice = self.scenario_choice(
            "How do you work the edge of the dig ring?",
            [
                self.skill_tag("STEALTH", self.action_option("Move along the broken irrigation trench and get inside the ring quietly.")),
                self.quoted_option("ARCANA", "Those sigils matter. Let me read what kind of wrongness is powering them."),
                self.quoted_option("DECEPTION", "Call out as hired salvage come to collect the next cart of bones."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Move along the broken irrigation trench and get inside the ring quietly.")
            success = self.skill_check(self.state.player, "Stealth", 13, context="to slip into the dig site unseen")
            if success:
                self.apply_status(enemies[0], "surprised", 1, source="your trench approach")
                enemies[0].current_hp = max(1, enemies[0].current_hp - 4)
                hero_bonus += 2
                self.say("You are inside the ward-ring before the first skull-lantern turns your way.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="loose stone and a snapped old bucket chain")
                self.say("A snapped chain and shower of stone give the site plenty of warning.")
        elif choice == 2:
            self.player_speaker("Those sigils matter. Let me read what kind of wrongness is powering them.")
            success = self.skill_check(self.state.player, "Arcana", 13, context="to read the ward sigils before they flare")
            if success:
                self.apply_status(self.state.player, "resist_poison", 3, source="ward-script countermeasures")
                self.apply_status(enemies[1], "reeling", 2, source="your disruption of the ritual ring")
                hero_bonus += 1
                self.say("You spoil the smooth flow of the ritual enough to leave the defenders moving through their own half-broken pattern.")
            else:
                self.say("The symbols are older and uglier than you wanted them to be, and the answer comes back as a pulse of cold air instead of clarity.")
        else:
            self.player_speaker("Hired salvage. Open the line before the carts start backing up.")
            success = self.skill_check(self.state.player, "Deception", 13, context="to bluff your way into the dig perimeter")
            if success:
                enemies[1].current_hp = max(1, enemies[1].current_hp - 3)
                self.apply_status(enemies[1], "surprised", 1, source="your sudden betrayal")
                hero_bonus += 1
                self.say("The bluff holds just long enough for your first strike to turn the whole ring inside out.")
            else:
                self.apply_status(self.state.player, "surprised", 1, source="a suspicious foreman's shout")
                self.say("The closest hireling narrows their eyes, then starts yelling for the dead to rise.")

        outcome = self.run_encounter(
            Encounter(
                title="Old Owl Well Dig Ring",
                description="Bone-haulers and animated sentries close around the well mouth.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=False,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The dead keep their watch at Old Owl Well.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You fall back from the well before the site can swallow the whole party.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.say("The outer ring collapses. A salt cart lies off to one side, and a half-buried trench still holds soot-black notes and salvage tallies.")

    def _old_owl_salt_cart(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("A prospector is lashed to the salt cart, shaking hard enough that even the rope knots twitch with them.")
        choice = self.scenario_choice(
            "How do you handle the rescue?",
            [
                self.quoted_option("MEDICINE", "Cut them free and keep them steady long enough to speak."),
                self.quoted_option("PERSUASION", "Easy. You made it this far, so stay with me a little longer."),
                self.action_option("Break the cart brace, drag them clear, and let the camp sort itself out later."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Cut them free and keep them steady long enough to speak.")
            success = self.skill_check(
                self.state.player,
                "Medicine",
                12,
                context="to stabilize the prospector before shock takes their memory with it",
            )
            if success:
                self.say("The prospector gasps out one useful truth: the gravecaller answers to Ashfall's coin and the manor's keys.")
                self.add_clue("A rescued prospector says the gravecaller at Old Owl Well was being paid through Ashfall Watch for work tied to the manor hill.")
                self.reward_party(xp=10, reason="saving the prospector at Old Owl Well")
            else:
                self.say("You save the prospector's life, but not a clean version of what they saw.")
        elif choice == 2:
            self.player_speaker("Easy. You made it this far, so stay with me a little longer.")
            success = self.skill_check(self.state.player, "Persuasion", 12, context="to keep the prospector focused")
            if success:
                self.say("The prospector steadies enough to point out the same payment trail running through Ashfall Watch.")
                self.add_clue("The prospector confirms the dig ring was part of Ashfall Watch's wider salvage route.")
                self.reward_party(xp=10, reason="steadying the Old Owl prospector")
            else:
                self.say("The prospector survives, but the answers stay ragged.")
        else:
            self.player_action("Break the cart brace, drag them clear, and let the camp sort itself out later.")
            self.say("You haul the prospector clear and leave the salt cart collapsed in the trench, ruining any quick reset of the ring.")

        self.complete_map_room(dungeon, room.room_id)

    def _old_owl_supply_trench(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("Half-buried trench ledgers and soot-black route slips still cling to the damp soil under the supply tarp.")
        choice = self.scenario_choice(
            "What do you do with the recovered notes?",
            [
                self.quoted_option("INVESTIGATION", "Read the notes and sketch the route chain before the wind ruins them."),
                self.quoted_option("ARCANA", "The ink itself looks wrong. I want to know what was mixed into it."),
                self.action_option("Pocket the cleanest pages and kick the rest into the trench water."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Read the notes and sketch the route chain before the wind ruins them.")
            success = self.skill_check(self.state.player, "Investigation", 12, context="to preserve the gravecaller notes before they scatter")
            if success:
                self.say("The page names Ashfall Watch as the collection point and mentions a soot-key transfer beneath the old manor hill.")
                self.add_clue("The Old Owl Well notes point to Ashfall Watch as the collection point for salvage moved toward the manor hill.")
                self.reward_party(xp=10, reason="securing the Old Owl Well route notes")
            else:
                self.say("You save fragments, but the ugliest details go spinning away with the dust.")
        elif choice == 2:
            self.player_speaker("The ink itself looks wrong. I want to know what was mixed into it.")
            success = self.skill_check(self.state.player, "Arcana", 12, context="to read the tainted route slips")
            if success:
                self.say("The ash-ink still carries the smell of the signal basin at Ashfall, which ties the sites together even more cleanly.")
                self.add_clue("The trench notes were written in the same treated ash used by Ashfall Watch's signaling crews.")
                self.reward_party(xp=10, reason="decoding the tainted ledgers at Old Owl Well")
            else:
                self.say("The ritual residue is obvious, but the deeper trail slips away from you.")
        else:
            self.player_action("Pocket the cleanest pages and kick the rest into the trench water.")
            self.say("You take the useful scraps and ruin the rest rather than leave them for the next scavenger.")

        self.complete_map_room(dungeon, room.room_id)

    def _old_owl_gravecaller_lip(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say(
            "A hooded gravecaller rises from the well mouth itself, one hand blackened to the wrist by ritual soot. Their voice is calm in the way only committed fools and true fanatics manage."
        )
        self.speaker(
            "Vaelith Marr",
            "You are late. The dead were almost ready to remember who owned this land before your little town learned to squat on it.",
        )
        party_size = self.act1_party_size()
        boss_enemies = [create_enemy("vaelith_marr")]
        if party_size >= 2:
            boss_enemies.append(create_enemy("carrion_lash_crawler"))
        if party_size >= 4:
            boss_enemies.append(self.act1_pick_enemy(("skeletal_sentry", "graveblade_wight", "lantern_fen_wisp")))
        boss_bonus = int(self.state.flags.get("old_owl_prospector_rescued", False)) + int(self.state.flags.get("old_owl_notes_found", False))
        choice = self.scenario_choice(
            "How do you answer the gravecaller?",
            [
                self.quoted_option("RELIGION", "These dead are not yours to command. Let them go."),
                self.quoted_option("INTIMIDATION", "You are finished here. Step away from the well and survive it."),
                self.action_option("Rush the ritual line before another corpse can stand."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("These dead are not yours to command. Let them go.")
            success = self.skill_check(self.state.player, "Religion", 13, context="to break the gravecaller's hold on the risen dead")
            if success:
                if len(boss_enemies) > 1:
                    self.apply_status(boss_enemies[1], "frightened", 2, source="your command over the dead")
                self.apply_status(boss_enemies[0], "reeling", 1, source="a broken ritual cadence")
                self.say("For one sharp moment the dead hesitate as if something older than Vaelith has finally been heard.")
            else:
                self.say("The words are right. The gravecaller simply believes the wrong thing harder.")
        elif choice == 2:
            self.player_speaker("You are finished here. Step away from the well and survive it.")
            success = self.skill_check(self.state.player, "Intimidation", 13, context="to crack the gravecaller's composure")
            if success:
                boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 4)
                self.apply_status(boss_enemies[0], "frightened", 1, source="your iron-edged demand")
                self.say("Vaelith gives ground almost without meaning to, and the dead feel the break in confidence.")
            else:
                self.apply_status(boss_enemies[0], "emboldened", 2, source="your failed threat")
                self.speaker("Vaelith Marr", "You speak like the living have ever held a thing permanently.")
        else:
            self.player_action("Rush the ritual line before another corpse can stand.")
            boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 3)
            boss_bonus += 2
            self.say("You break the distance fast enough to make the first exchange happen inside Vaelith's own ward-ring.")

        outcome = self.run_encounter(
            Encounter(
                title="Miniboss: Vaelith Marr",
                description="The gravecaller of Old Owl Well fights from the lip of the buried dark.",
                enemies=boss_enemies,
                allow_flee=True,
                allow_parley=False,
                hero_initiative_bonus=boss_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The well's corpse-lights burn on above the fallen party.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You break contact and retreat to Phandalin with the well still active behind you.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.add_clue("Old Owl Well is cleared, and its notes tie grave-salvage, Ashfall Watch, and the manor hill into one supply chain.")
        self.add_journal("You silenced Old Owl Well and broke one of the Ashen Brand's outer operations.")
        self.refresh_quest_statuses(announce=False)
        self.add_inventory_item("scroll_lesser_restoration", source="Vaelith's ritual satchel")
        self.return_to_phandalin("Old Owl Well falls quiet behind you as the road back to Phandalin opens again.")

    def _wyvern_goat_path(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        if not self.state.flags.get("wyvern_tor_seen"):
            self.say(
                "Wyvern Tor looms out of the hills in broken shelves of wind-cut stone. Goat paths, old watch cairns, and smoke-stained hollows twist around the ridge, "
                "and something large has been pacing the high ground long enough to turn the dust into habitual scars.",
                typed=True,
            )
            self.state.flags["wyvern_tor_seen"] = True
        party_size = self.act1_party_size()
        enemies = [create_enemy("orc_raider"), create_enemy("worg")]
        if party_size >= 3:
            enemies.append(self.act1_pick_enemy(("orc_raider", "bugbear_reaver", "acidmaw_burrower", "cliff_harpy")))
        hero_bonus = self.apply_scene_companion_support("wyvern_tor")
        choice = self.scenario_choice(
            "How do you take the outer shelf?",
            [
                self.skill_tag("SURVIVAL", self.action_option("Use the goat path and the wind shadow to reach the upper shelf.")),
                self.skill_tag("STEALTH", self.action_option("Shadow the smoke line and hit the pickets first.")),
                self.quoted_option("NATURE", "The worg pack is the key. Let me read where it expects prey to run."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Use the goat path and the wind shadow to reach the upper shelf.")
            success = self.skill_check(self.state.player, "Survival", 13, context="to take the hidden path up Wyvern Tor")
            if success:
                self.apply_status(enemies[0], "surprised", 1, source="your high approach")
                hero_bonus += 2
                self.say("You come out above the outer camp instead of below it, which changes the whole feel of the fight.")
            else:
                self.say("The path is real, but not as forgiving as the goats make it look.")
        elif choice == 2:
            self.player_action("Shadow the smoke line and hit the pickets first.")
            success = self.skill_check(self.state.player, "Stealth", 13, context="to get onto the shelf before the pickets spot you")
            if success:
                enemies[-1].current_hp = max(1, enemies[-1].current_hp - 4)
                self.apply_status(enemies[-1], "reeling", 1, source="your opening strike")
                hero_bonus += 1
                self.say("The closest lookout goes down hard enough that the alarm comes late and ugly.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="gravel underfoot")
                self.say("Loose scree gives you away and the shelf erupts into motion.")
        else:
            self.player_speaker("The worg pack is the key. Let me read where it expects prey to run.")
            success = self.skill_check(self.state.player, "Nature", 13, context="to predict the worg's line of attack")
            if success:
                self.apply_status(enemies[1], "frightened", 1, source="your perfect read of its momentum")
                hero_bonus += 1
                self.say("You move before the beast commits, which steals its best rush cleanly away.")
            else:
                self.say("You read enough to know the worg is clever, not enough to stop it from choosing the angle first.")

        outcome = self.run_encounter(
            Encounter(
                title="Wyvern Tor Shelf Fight",
                description="Orc raiders and a hunting worg defend the tor's outer shelf.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=False,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Wyvern Tor keeps the high ground and the road below it.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You break away from the tor and retreat before the shelf turns into a killing bowl.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.say("The outer shelf breaks. One hollow holds a terrified drover; another ledge keeps a half-defaced cairn shrine and the raiders' beast tethers.")

    def _wyvern_drover_hollow(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("A captured drover is bound in the hollow, bruised but still watching the upper shelf with desperate focus.")
        choice = self.scenario_choice(
            "How do you handle the drover?",
            [
                self.quoted_option("MEDICINE", "Get the drover breathing right and find out how many are still above us."),
                self.quoted_option("INSIGHT", "Tell me what the chief values enough to guard this hard."),
                self.action_option("Cut them loose, arm them, and send them downslope before the chief arrives."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Get the drover breathing right and find out how many are still above us.")
            success = self.skill_check(self.state.player, "Medicine", 12, context="to steady the captured drover before shock takes over")
            if success:
                self.say("The drover coughs out one clean answer: a blood-chief named Brughor, one ogre, and enough ego to think the hill already belongs to him.")
                self.add_clue("A captured drover confirms Brughor holds Wyvern Tor with an ogre and a small disciplined raiding party.")
                self.reward_party(xp=10, reason="saving the captured drover at Wyvern Tor")
            else:
                self.say("The drover lives, but the useful details come back in broken pieces.")
        elif choice == 2:
            self.player_speaker("Tell me what the chief values enough to guard this hard.")
            success = self.skill_check(self.state.player, "Insight", 12, context="to read the chief through a terrified witness")
            if success:
                self.say("The drover points toward Brughor's pride more than his supplies, which makes the coming challenge easier to shape.")
                self.add_clue("Brughor cares more about holding the high shelf in sight of his crew than about any one crate or beast.")
                self.reward_party(xp=10, reason="reading Brughor through the drover")
            else:
                self.say("You get fear, blood, and smoke, but not the clean edge of an answer.")
        else:
            self.player_action("Cut them loose, arm them, and send them downslope before the chief arrives.")
            self.say("The drover staggers away with a stolen knife and a promise to tell Phandalin exactly what waits on this hill.")

        self.complete_map_room(dungeon, room.room_id)

    def _wyvern_shrine_ledge(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("A cairn shrine to Tempus leans in the wind beside the raiders' remaining tethers and a scatter of stolen tack.")
        choice = self.scenario_choice(
            "What do you do on the ledge?",
            [
                self.quoted_option("RELIGION", "Set the cairn shrine right. I want the chief fighting under a bad sign."),
                self.action_option("Cut the pack tethers and send the remaining beasts into the upper camp."),
                self.action_option("Strip the tack, ruin the tethers, and leave the ledge empty."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Set the cairn shrine right. I want the chief fighting under a bad sign.")
            success = self.skill_check(self.state.player, "Religion", 12, context="to restore the cairn shrine enough to unsettle the raiders")
            if success:
                self.apply_status(self.state.player, "blessed", 2, source="the restored cairn shrine")
                self.say("You set the cairn stones true again, and the hill stops feeling entirely like theirs.")
                self.reward_party(xp=10, reason="restoring the shrine on Wyvern Tor")
            else:
                self.say("You do what you can with the broken shrine, but the best of the omen slips through your fingers.")
        elif choice == 2:
            self.player_action("Cut the pack tethers and send the remaining beasts into the upper camp.")
            self.say("Goats and half-starved pack animals scatter uphill in a chaos of bells and hooves, dragging the upper camp's attention sideways.")
        else:
            self.player_action("Strip the tack, ruin the tethers, and leave the ledge empty.")
            self.say("You leave the ledge useless as a staging point and deny the upper shelf one more clean response.")

        self.complete_map_room(dungeon, room.room_id)

    def _wyvern_high_shelf(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say(
            "A broad-shouldered orc in scavenged scale laughs once as he comes down from the upper shelf, great axe low in one hand and old blood drying on his bracers. "
            "An ogre lumbers after him, dragging a club over stone."
        )
        self.speaker("Brughor Skullcleaver", "Good. I was getting tired of prey that ran downhill.")
        party_size = self.act1_party_size()
        boss_enemies = [create_enemy("orc_bloodchief", name="Brughor Skullcleaver")]
        if party_size >= 2:
            boss_enemies.append(self.act1_pick_enemy(("ogre_brute", "ettervine_webherd")))
        if party_size >= 4:
            boss_enemies.append(self.act1_pick_enemy(("orc_raider", "bugbear_reaver")))
        boss_bonus = int(self.state.flags.get("wyvern_drover_rescued", False)) + int(self.state.flags.get("wyvern_shrine_secured", False))
        choice = self.scenario_choice(
            "How do you answer the blood-chief?",
            [
                self.quoted_option("INTIMIDATION", "You picked the wrong town to stalk."),
                self.quoted_option("ATHLETICS", "Then come down the rest of the way and see how long you stand."),
                self.action_option("Hit the chief before the ogre can settle into the fight."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("You picked the wrong town to stalk.")
            success = self.skill_check(self.state.player, "Intimidation", 13, context="to meet Brughor's violence with greater certainty")
            if success:
                boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 4)
                self.apply_status(boss_enemies[0], "frightened", 1, source="your refusal to yield ground")
                self.say("Brughor's grin slips for a heartbeat, and the hill feels smaller around him.")
            else:
                self.apply_status(boss_enemies[0], "emboldened", 2, source="your challenge feeding his pride")
                self.speaker("Brughor Skullcleaver", "Better. Fearless prey usually swings harder.")
        elif choice == 2:
            self.player_speaker("Then come down the rest of the way and see how long you stand.")
            success = self.skill_check(self.state.player, "Athletics", 13, context="to own the footing and force the chief into your timing")
            if success:
                self.apply_status(self.state.player, "emboldened", 2, source="holding the shelf against Brughor's rush")
                boss_bonus += 1
                self.say("You take the rock shelf like a shield line, and Brughor has to meet you on terms he did not choose.")
            else:
                self.say("The footing is uglier than your confidence suggested, and the chief sees it.")
        else:
            self.player_action("Hit the chief before the ogre can settle into the fight.")
            boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 3)
            boss_bonus += 2
            self.say("You crash into the upper shelf before the whole enemy line can come together cleanly.")

        outcome = self.run_encounter(
            Encounter(
                title="Miniboss: Brughor Skullcleaver",
                description="The blood-chief of Wyvern Tor makes his stand on the broken high shelf.",
                enemies=boss_enemies,
                allow_flee=True,
                allow_parley=False,
                hero_initiative_bonus=boss_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Brughor leaves the hill red and the road below it empty.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You pull clear of the upper shelf and retreat to Phandalin to regroup.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.add_clue("Wyvern Tor is cleared, and its raiders were coordinating with Ashfall Watch rather than acting alone.")
        self.add_journal("You broke the raiders at Wyvern Tor and stripped another outer shield away from the Ashen Brand.")
        self.refresh_quest_statuses(announce=False)
        self.add_inventory_item("greater_healing_draught", source="Brughor's travel chest")
        self.return_to_phandalin("Wyvern Tor falls behind you as the ridge wind finally goes clean.")

    def _ashfall_breach_gate(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say(
            "Ashfall Watch crouches over the road in layered ruin and fresh timber: a snapped tower, palisade repairs, prisoner cages, and a signal basin built to spit smoke across the hills. "
            "It is no longer just a raider den. It is a frontier choke point built on fear and scheduling.",
            typed=True,
        )
        party_size = self.act1_party_size()
        enemies = [create_enemy("bandit"), create_enemy("bandit_archer")]
        if party_size >= 3:
            enemies.append(self.act1_pick_enemy(("worg", "gutter_zealot", "rust_shell_scuttler")))
        hero_bonus = self.apply_scene_companion_support("ashfall_watch")
        choice = self.scenario_choice(
            "How do you open the assault?",
            [
                self.skill_tag("STEALTH", self.action_option("Slip up the ruin side and cut the outer line quietly.")),
                self.quoted_option("DECEPTION", "Late relief from the tor. Open up before the ridge goes black."),
                self.skill_tag("ATHLETICS", self.action_option("Hit the wagon gate before the watch can settle.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Slip up the ruin side and cut the outer line quietly.")
            success = self.skill_check(self.state.player, "Stealth", 13, context="to reach the outer ruin unseen")
            if success:
                self.apply_status(enemies[1], "surprised", 1, source="your silent wall-climb")
                enemies[1].current_hp = max(1, enemies[1].current_hp - 4)
                hero_bonus += 2
                self.say("You are inside the outer ruin before the first lookout can call the line.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="slipping on loose stone")
                self.say("Loose stone skips down the wall and the alarm comes early.")
        elif choice == 2:
            self.player_speaker("Late relief from the tor. Open up before the ridge goes black.")
            success = self.skill_check(self.state.player, "Deception", 13, context="to sell a field report at the gate")
            if success:
                self.apply_status(enemies[0], "surprised", 1, source="your sudden betrayal")
                enemies[0].current_hp = max(1, enemies[0].current_hp - 3)
                hero_bonus += 1
                self.say("The lie holds exactly long enough to put the first defender down badly.")
            else:
                self.apply_status(self.state.player, "surprised", 1, source="the sentry's barked alarm")
                self.say("The sentry does not buy it, and now the whole gate is shouting.")
        else:
            self.player_action("Hit the wagon gate before the watch can settle.")
            success = self.skill_check(self.state.player, "Athletics", 13, context="to burst through the wagon gate with momentum")
            if success:
                self.apply_status(self.state.player, "emboldened", 2, source="blasting through the gate")
                self.apply_status(enemies[0], "prone", 1, source="the splintered rush")
                hero_bonus += 2
                self.say("The gate gives under force and the outer line loses shape immediately.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="hitting the gate wrong")
                self.say("The gate still gives, but the impact costs you the clean opening.")

        outcome = self.run_encounter(
            Encounter(
                title="Ashfall Gate",
                description="Outer sentries scramble between ruined stone, cages, and signal braziers.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=13,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Ashfall Watch remains in enemy hands.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You fall back to Phandalin to rethink the assault.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.say("With the gate broken, you reach a prisoner yard, the tower's smoke basin, and a half-charred order board marked with Rukhar's hand.")
        choice = self.scenario_choice(
            "What do you handle before the inner barracks can form up?",
            [
                self.skill_tag("STEALTH", self.action_option("Snuff the signal basin before anyone can call the ridge.")),
                self.skill_tag("ATHLETICS", self.action_option("Break the prisoner cage and arm whoever can still stand.")),
                self.quoted_option("INVESTIGATION", "Read the order board. If Rukhar thinks in patterns, I want them now."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Snuff the signal basin before anyone can call the ridge.")
            success = self.skill_check(self.state.player, "Stealth", 12, context="to kill the signal basin without drawing the whole court")
            if success:
                self.say("You smother the basin under wet tarp and grit. No help is coming from the ridge in time to matter.")
            else:
                self.say("You kill the signal late and loud, but late still counts for something.")
            self.complete_map_room(dungeon, "signal_basin")
        elif choice == 2:
            self.player_action("Break the prisoner cage and arm whoever can still stand.")
            success = self.skill_check(self.state.player, "Athletics", 12, context="to break the cage open fast enough to matter")
            if success:
                self.apply_status(self.state.player, "emboldened", 1, source="freed prisoners roaring for revenge")
                self.reward_party(xp=15, reason="freeing Ashfall's prisoners under fire")
                self.say("A few freed prisoners grab dropped clubs and stones, throwing the barracks response into chaos.")
            else:
                self.say("You free them, but not cleanly enough to keep the barracks from organizing.")
            self.complete_map_room(dungeon, "prisoner_yard")
        else:
            self.player_speaker("Read the order board. If Rukhar thinks in patterns, I want them now.")
            success = self.skill_check(
                self.state.player,
                "Investigation",
                12,
                context="to read Rukhar's order board in the middle of the assault",
            )
            if success:
                self.state.flags["ashfall_orders_read"] = True
                self.add_clue("Rukhar rotates his strongest fighters through the lower barracks before taking the courtyard himself.")
                self.reward_party(xp=15, reason="reading Rukhar's order board under pressure")
                self.say("You catch enough of the rotation to know exactly which door the inner response will use.")
            else:
                self.say("You get fragments, but not the whole shape of his defense.")
            self.complete_map_room(dungeon, "prisoner_yard")

        self.set_current_map_room("lower_barracks")

    def _ashfall_prisoner_yard(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("The prisoner yard reeks of smoke, rope, and panic. A half-charred order board still hangs beside the cages.")
        choice = self.scenario_choice(
            "What do you handle first?",
            [
                self.skill_tag("ATHLETICS", self.action_option("Break the prisoner cage and arm whoever can still stand.")),
                self.quoted_option("INVESTIGATION", "Read the order board. If Rukhar thinks in patterns, I want them now."),
                self.action_option("Cut the locks, shove the prisoners toward cover, and keep moving."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Break the prisoner cage and arm whoever can still stand.")
            success = self.skill_check(self.state.player, "Athletics", 12, context="to break the cage open fast enough to matter")
            if success:
                self.apply_status(self.state.player, "emboldened", 1, source="freed prisoners roaring for revenge")
                self.reward_party(xp=15, reason="freeing Ashfall's prisoners under fire")
                self.say("A few freed prisoners grab dropped clubs and stones, throwing the barracks response into chaos.")
            else:
                self.say("You free them, but not cleanly enough to keep the barracks from organizing.")
        elif choice == 2:
            self.player_speaker("Read the order board. If Rukhar thinks in patterns, I want them now.")
            success = self.skill_check(
                self.state.player,
                "Investigation",
                12,
                context="to read Rukhar's order board in the middle of the assault",
            )
            if success:
                self.state.flags["ashfall_orders_read"] = True
                self.add_clue("Rukhar rotates his strongest fighters through the lower barracks before taking the courtyard himself.")
                self.reward_party(xp=15, reason="reading Rukhar's order board under pressure")
                self.say("You catch enough of the rotation to know exactly which door the inner response will use.")
            else:
                self.say("You get fragments, but not the whole shape of his defense.")
        else:
            self.player_action("Cut the locks, shove the prisoners toward cover, and keep moving.")
            self.say("The cages swing open and the yard turns from a pen into a problem the watch can no longer ignore.")

        self.complete_map_room(dungeon, room.room_id)

    def _ashfall_signal_basin(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("The signal basin spits oily smoke toward the ridges, half-fed and still dangerous.")
        choice = self.scenario_choice(
            "How do you kill the signal line?",
            [
                self.skill_tag("STEALTH", self.action_option("Snuff the signal basin before anyone can call the ridge.")),
                self.quoted_option("SURVIVAL", "The wind is shifting. I can use it to turn the smoke back into the yard."),
                self.action_option("Kick the braziers apart and drown the whole thing in grit."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Snuff the signal basin before anyone can call the ridge.")
            success = self.skill_check(self.state.player, "Stealth", 12, context="to kill the signal basin without drawing the whole court")
            if success:
                self.say("You smother the basin under wet tarp and grit. No help is coming from the ridge in time to matter.")
            else:
                self.say("You kill the signal late and loud, but late still counts for something.")
        elif choice == 2:
            self.player_speaker("The wind is shifting. I can use it to turn the smoke back into the yard.")
            success = self.skill_check(self.state.player, "Survival", 12, context="to use the crosswind against the signal basin")
            if success:
                self.say("The smoke whips back into the yard and wrecks the timing of anyone still trying to form a line.")
                self.reward_party(xp=10, reason="turning Ashfall's signal smoke back on the fort")
            else:
                self.say("The wind helps, but not cleanly enough to hide the sabotage.")
        else:
            self.player_action("Kick the braziers apart and drown the whole thing in grit.")
            self.say("The basin collapses into a coughing ruin of sparks, ash, and wet earth.")

        self.complete_map_room(dungeon, room.room_id)

    def _ashfall_lower_barracks(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        party_size = self.act1_party_size()
        second_enemies = [create_enemy("bandit"), create_enemy("bandit_archer", name="Ashen Brand Barracks Archer")]
        if party_size >= 2:
            second_enemies.append(self.act1_pick_enemy(("bandit", "orc_raider", "gutter_zealot", "ashstone_percher")))
        if party_size >= 4:
            second_enemies.append(self.act1_pick_enemy(("orc_raider", "rust_shell_scuttler", "bugbear_reaver")))
        hero_bonus = int(self.state.flags.get("ashfall_signal_basin_silenced", False)) * 2
        if self.state.flags.get("ashfall_prisoners_freed"):
            hero_bonus += 2
        if self.state.flags.get("ashfall_orders_read"):
            hero_bonus += 1
        self.say("Veterans and hired blades spill out of the lower barracks in a hard organized rush.")
        outcome = self.run_encounter(
            Encounter(
                title="Ashfall Lower Barracks",
                description="Veterans and hired blades spill out of the lower barracks in a hard organized rush.",
                enemies=second_enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=14,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Ashfall's lower barracks break the party in the smoke.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You drag the party clear of the lower yard and retreat before the courtyard can close on you.")
            return

        self.complete_map_room(dungeon, room.room_id)
        if not self.state.flags.get("ashfall_signal_basin_silenced"):
            self.say("The barracks are broken, but the command post is still shielded by the active signal line. Another wing needs clearing first.")

    def _ashfall_rukhar_command(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("At the tower court's heart, a disciplined hobgoblin in darkened mail steps through the smoke with the calm of a soldier who has already sorted the dead from the living.")
        self.speaker(
            "Rukhar Cinderfang",
            "You have cost my employers time, coin, and useful subordinates. I will not pretend that leaves us room for civility.",
        )
        party_size = self.act1_party_size()
        boss_enemies = [create_enemy("rukhar")]
        if party_size >= 2:
            boss_enemies.append(self.act1_pick_enemy(("bandit", "gutter_zealot", "bugbear_reaver")))
        if party_size >= 4:
            boss_enemies.append(self.act1_pick_enemy(("orc_raider", "rust_shell_scuttler")))
        boss_bonus = 1 if self.state.flags.get("ashfall_orders_read") else 0
        choice = self.scenario_choice(
            "Rukhar raises his blade and waits to see how you answer.",
            [
                self.quoted_option("INTIMIDATION", "Surrender the yard in Phandalin's name."),
                self.quoted_option("PERSUASION", "Your paymaster is already losing. Walk away with the people who still can."),
                self.action_option("Strike before he can settle the shield line."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Surrender the yard in Phandalin's name.")
            success = self.skill_check(self.state.player, "Intimidation", 13, context="to crack Rukhar's command posture")
            if success:
                boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 4)
                self.apply_status(boss_enemies[0], "frightened", 1, source="your iron-edged demand")
                self.say("Rukhar's line tightens too hard, which is its own kind of weakness.")
            else:
                self.apply_status(boss_enemies[0], "emboldened", 2, source="your failed demand")
                self.speaker("Rukhar Cinderfang", "Good. You arrived with a spine.")
        elif choice == 2:
            self.player_speaker("Your paymaster is already losing. Walk away with the people who still can.")
            success = self.skill_check(self.state.player, "Persuasion", 13, context="to separate Rukhar from the men still taking his orders")
            if success:
                fleeing = boss_enemies.pop() if len(boss_enemies) > 1 else None
                if fleeing is not None:
                    self.say(f"{fleeing.name} looks at the smoke, looks at Rukhar, and decides not to die for bookkeeping.")
                self.apply_status(boss_enemies[0], "reeling", 1, source="his line cracking around him")
            else:
                self.say("Rukhar's discipline holds harder than your mercy can pry apart.")
        else:
            self.player_action("Strike before he can settle the shield line.")
            boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 3)
            boss_bonus += 2
            self.say("Steel answers before speeches can, and the final fight begins in motion.")

        outcome = self.run_encounter(
            Encounter(
                title="Miniboss: Rukhar Cinderfang",
                description="The Ashfall sergeant rallies the last disciplined core of the Ashen Brand field force.",
                enemies=boss_enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=14,
                hero_initiative_bonus=boss_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Rukhar drives the party from the tower in blood and smoke.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You escape the watchtower and retreat to Phandalin to regroup.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.add_clue("Rukhar carried a soot-black key stamped with the Tresendar crest and orders to move captives beneath the manor hill.")
        self.add_journal("Ashfall Watch is broken, but the Ashen Brand's cellar routes beneath Phandalin are still active.")
        self.refresh_quest_statuses(announce=False)
        self.say(
            "Among Rukhar's orders you find a blackened key bearing the Tresendar crest, prisoner transfer notes, and references to a deeper reserve called Emberhall. "
            "The field base is broken, but the gang's thinking parts are still below town."
        )
        self.return_to_phandalin("Ashfall Watch breaks under the assault, and the road home finally opens.")

    def _tresendar_hidden_stair(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say(
            "The ruined manor crouches over Phandalin like a memory that never learned to stay buried. Beneath the broken shell, a hidden stair drops into wet stone, cistern corridors, and ash-marked cellars where the Ashen Brand keeps its quieter work.",
            typed=True,
        )
        choice = self.scenario_choice(
            "How do you enter the buried manor?",
            [
                self.quoted_option("INVESTIGATION", "There is a hidden stair here somewhere. Let me find the one they trust."),
                self.skill_tag("STEALTH", self.action_option("Slip through the collapsed chapel side and into the cellars.")),
                self.skill_tag("ATHLETICS", self.action_option("Rip the old cistern grate open and take the straight drop.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("There is a hidden stair here somewhere. Let me find the one they trust.")
            success = self.skill_check(self.state.player, "Investigation", 13, context="to find the concealed manor intake route")
            self.state.flags["tresendar_hidden_entry"] = success
            if success:
                self.say("You find the concealed stair and enter on the defenders' blind side.")
            else:
                self.say("You find the route, just not before the noise of the search carries below.")
        elif choice == 2:
            self.player_action("Slip through the collapsed chapel side and into the cellars.")
            success = self.skill_check(self.state.player, "Stealth", 13, context="to cross the broken chapel without warning the cellars")
            self.state.flags["tresendar_chapel_entry"] = success
            if success:
                self.say("You come through the chapel rubble already moving and the first lookout never gets set.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="a falling stone saint-head")
                self.say("A broken stone saint tumbles and announces you to the lower rooms.")
        else:
            self.player_action("Rip the old cistern grate open and take the straight drop.")
            success = self.skill_check(self.state.player, "Athletics", 13, context="to force the old grate without losing balance on the drop")
            self.state.flags["tresendar_cistern_breach"] = success
            if success:
                self.apply_status(self.state.player, "emboldened", 2, source="a brutal manor breach")
                self.say("The grate comes free in a crash of iron and you land already driving the fight.")
            else:
                self.apply_status(self.state.player, "prone", 1, source="a bad landing through the cistern grate")
                self.say("The grate gives, but the landing is uglier than planned.")

        self.complete_map_room(dungeon, room.room_id)

    def _tresendar_cellar_intake(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        party_size = self.act1_party_size()
        enemies = [create_enemy("bandit", name="Ashen Brand Collector"), create_enemy("bandit_archer", name="Archive Cutout")]
        if party_size >= 3:
            enemies.append(self.act1_pick_enemy(("skeletal_sentry", "mireweb_spider", "cache_mimic", "ashstone_percher")))
        if party_size >= 4:
            enemies.append(self.act1_pick_enemy(("stonegaze_skulker", "cache_mimic", "ashstone_percher")))
        hero_bonus = self.apply_scene_companion_support("tresendar_manor")
        if self.state.flags.pop("tresendar_hidden_entry", False):
            self.apply_status(enemies[0], "surprised", 1, source="your hidden entry")
            hero_bonus += 2
        if self.state.flags.pop("tresendar_chapel_entry", False):
            enemies[1].current_hp = max(1, enemies[1].current_hp - 4)
            self.apply_status(enemies[1], "reeling", 1, source="your chapel-side opening")
            hero_bonus += 1
        if self.state.flags.pop("tresendar_cistern_breach", False):
            self.apply_status(self.state.player, "emboldened", 2, source="a brutal manor breach")
            self.apply_status(enemies[0], "prone", 1, source="the crashing grate and falling iron")
            hero_bonus += 1
        outcome = self.run_encounter(
            Encounter(
                title="Tresendar Cellars",
                description="Collectors, cutouts, and buried sentries hold the intake route beneath the manor.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=13,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The buried manor swallows the party beneath Phandalin.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You pull back from the manor tunnels before the whole cellar network can close around you.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.say("The intake route is broken. Wet corridors open toward the cistern walk, and a barred side store lies deeper in the dark.")

    def _tresendar_cistern_walk(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("The cracked cistern walk stinks of wet stone and secrets. Something with a single reflective eye is moving through the dark water below.")
        choice = self.scenario_choice(
            "How do you handle the thing in the cistern before it fully commits?",
            [
                self.quoted_option("INSIGHT", "It is testing us. Let me read what it wants before it strikes."),
                self.quoted_option("ARCANA", "That is no simple cellar monster. I want its pattern before it gets mine."),
                self.action_option("Throw a ration sack into the dark and charge while it turns."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("It is testing us. Let me read what it wants before it strikes.")
            success = self.skill_check(self.state.player, "Insight", 13, context="to read the cistern horror's attention before it breaks cover")
            if success:
                self.state.flags["tresendar_eye_read"] = True
                self.say("The creature wants secrets and weakness first, flesh second. Knowing that lets you meet its gaze without offering either too freely.")
            else:
                self.say("You catch hunger, curiosity, and malice all at once, which is not the same as understanding.")
        elif choice == 2:
            self.player_speaker("That is no simple cellar monster. I want its pattern before it gets mine.")
            success = self.skill_check(self.state.player, "Arcana", 13, context="to identify the cistern horror before it opens the fight")
            if success:
                self.state.flags["tresendar_eye_read"] = True
                self.apply_status(self.state.player, "blessed", 1, source="naming the cistern horror correctly")
                self.say("Putting the creature into words steals some of the fear it was trying to weaponize.")
            else:
                self.say("Naming the horror correctly does not stop it from grinning at you out of the dark.")
        else:
            self.player_action("Throw a ration sack into the dark and charge while it turns.")
            self.state.flags["tresendar_eye_ambushed"] = True
            self.say("The sack hits water, the yellow eye turns, and you use the half-second it gives you.")

        self.complete_map_room(dungeon, room.room_id)

    def _tresendar_cage_store(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("The cage store holds ledger scraps, old chains, and one sealed coffer the Ashen Brand never got around to moving.")
        choice = self.scenario_choice(
            "What do you secure here?",
            [
                self.quoted_option("INVESTIGATION", "Give me the ledgers. I want the shape of Varyn's exits and lies."),
                self.quoted_option("SLEIGHT OF HAND", "Open the coffer quietly and take whatever matters before the hinges scream."),
                self.action_option("Take the whole coffer and drag it back the hard way."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Give me the ledgers. I want the shape of Varyn's exits and lies.")
            success = self.skill_check(self.state.player, "Investigation", 13, context="to decode the cage-store papers before the boss room")
            if success:
                self.add_clue("Rukhar's ledger chain confirms Emberhall as Varyn's deeper reserve beneath town.")
                self.reward_party(xp=10, reason="decoding the cage-store records")
                self.say("The papers make it plain: Tresendar was only the intake route, not the final refuge.")
            else:
                self.say("You get enough to confirm the route, but not every name attached to it.")
        elif choice == 2:
            self.player_speaker("Open the coffer quietly and take whatever matters before the hinges scream.")
            success = self.skill_check(self.state.player, "Sleight of Hand", 13, context="to open the coffer without wrecking the contents")
            if success:
                self.add_inventory_item("scroll_arcane_refresh", source="a sealed coffer in the cistern alcove")
                self.say("The coffer opens cleanly and gives up one preserved scroll case before the hinges complain.")
            else:
                self.add_inventory_item("scroll_arcane_refresh", source="a dented coffer in the cistern alcove")
                self.say("The lock gives badly, but the scroll case inside survives well enough.")
        else:
            self.player_action("Take the whole coffer and drag it back the hard way.")
            self.add_inventory_item("scroll_arcane_refresh", source="a sealed coffer in the cistern alcove")
            self.say("You do not solve the lock so much as decide it is now a surface problem.")

        self.complete_map_room(dungeon, room.room_id)

    def _tresendar_nothic_lair(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        party_size = self.act1_party_size()
        second_enemies = [create_enemy("nothic", name="Cistern Eye")]
        if party_size >= 3:
            second_enemies.append(self.act1_pick_enemy(("skeletal_sentry", "stonegaze_skulker", "whispermaw_blob", "lantern_fen_wisp")))
        if party_size >= 4:
            second_enemies.append(self.act1_pick_enemy(("stonegaze_skulker", "whispermaw_blob", "graveblade_wight")))
        boss_bonus = int(self.state.flags.get("tresendar_eye_read", False)) + (2 if self.state.flags.get("tresendar_eye_ambushed", False) else 0)
        outcome = self.run_encounter(
            Encounter(
                title="The Cistern Eye",
                description="A warped cellar horror rises from the dark water below Tresendar Manor.",
                enemies=second_enemies,
                allow_flee=True,
                allow_parley=False,
                hero_initiative_bonus=boss_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The cistern horror keeps its secrets and your bodies with them.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You retreat from the cistern dark before the manor can claim the rest of the night.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.add_clue("Tresendar Manor was the Ashen Brand's intake route; Varyn's remaining core has withdrawn into Emberhall below.")
        self.add_journal("You cleared the buried Tresendar route and confirmed Varyn has fallen back to Emberhall for the final stand.")
        if not self.state.flags.get("tresendar_records_secured"):
            self.add_inventory_item("scroll_arcane_refresh", source="a sealed coffer in the cistern alcove")
        self.return_to_phandalin("The cistern goes still, and the buried route beneath Tresendar finally breaks open.")

    def _emberhall_antechamber(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say(
            "Near midnight, you descend into Emberhall: old stone vaults, stolen crates, poison tables, ash-marked banners, and the last disciplined knot of the Ashen Brand. "
            "This is not a hideout anymore. It is an answer the gang built under the town while decent people slept overhead.",
            typed=True,
        )
        party_size = self.act1_party_size()
        enemies = [create_enemy("bandit", name="Ashen Brand Fixer"), create_enemy("bandit_archer", name="Cellar Sniper")]
        if party_size >= 3:
            enemies.append(self.act1_pick_enemy(("bandit", "gutter_zealot", "cache_mimic", "cinderflame_skull")))
        if party_size >= 4:
            enemies.append(self.act1_pick_enemy(("bandit_archer", "gutter_zealot", "cinderflame_skull")))
        hero_bonus = self.apply_scene_companion_support("emberhall_cellars")
        choice = self.scenario_choice(
            "How do you break the final approach open?",
            [
                self.skill_tag("STEALTH", self.action_option("Slip through the drainage run and hit the antechamber from behind.")),
                self.skill_tag("ATHLETICS", self.action_option("Kick in the main cellar door and force the issue immediately.")),
                self.quoted_option("PERSUASION", "Call for surrender before the last of them decides to die for Varyn."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Slip through the drainage run and hit the antechamber from behind.")
            success = self.skill_check(self.state.player, "Stealth", 13, context="to reach the antechamber quietly")
            if success:
                enemies[1].current_hp = max(1, enemies[1].current_hp - 5)
                self.apply_status(enemies[1], "surprised", 1, source="your tunnel approach")
                hero_bonus += 2
                self.say("You come out behind stacked crates and the first lookout never finds a clean line.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="a shrieking drainage grate")
                self.say("The grate screams and the last defenders know exactly where you are.")
        elif choice == 2:
            self.player_action("Kick in the main cellar door and force the issue immediately.")
            success = self.skill_check(self.state.player, "Athletics", 13, context="to blast the cellar door off its hinges")
            if success:
                self.apply_status(self.state.player, "emboldened", 2, source="blasting into Emberhall")
                self.apply_status(enemies[0], "prone", 1, source="the crashing cellar door")
                hero_bonus += 2
                self.say("The door explodes inward and the antechamber never really gets to become a line.")
            else:
                self.apply_status(self.state.player, "prone", 1, source="a collapsing door frame")
                self.say("The door gives badly and drags you down with it.")
        else:
            self.player_speaker("Call for surrender before the last of them decides to die for Varyn.")
            success = self.skill_check(self.state.player, "Persuasion", 14, context="to shake the final defenders before steel is fully drawn")
            if success:
                fleeing = enemies.pop()
                self.say(f"{fleeing.name} bolts for the far stair instead of dying for someone else's cut.")
                hero_bonus += 1
            else:
                self.say("The room tightens instead of yielding, and the last defenders settle in behind Varyn's certainty.")

        outcome = self.run_encounter(
            Encounter(
                title="Emberhall Antechamber",
                description="The gang's last disciplined guard line forms among poison tables and stolen crates.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=14,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Emberhall's last guard line leaves the cellars to the Ashen Brand.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You retreat to the surface before the last chamber can close around you.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.say("Beyond the antechamber, the ledger chain room and a smoke-choked archive split the last approach.")

    def _emberhall_ledger_chain(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("A chained clerk, a table full of ledgers, and a stack of poison vials wait in the narrow room outside the sanctum.")
        choice = self.scenario_choice(
            "What do you do in the lull?",
            [
                self.quoted_option("MEDICINE", "The chained clerk is fading. Get them talking before the poison finishes the job."),
                self.quoted_option("INVESTIGATION", "Give me the ledgers. I want the shape of Varyn's exits and lies."),
                self.action_option("Smash the poison table and flood the hall with glass, fumes, and noise."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("The chained clerk is fading. Get them talking before the poison finishes the job.")
            success = self.skill_check(self.state.player, "Medicine", 13, context="to keep the poisoned clerk alive long enough for a final warning")
            if success:
                self.state.flags["emberhall_clerk_saved"] = True
                self.add_inventory_item("antitoxin_vial", source="the chained clerk's hidden pocket")
                self.reward_party(xp=15, reason="saving the chained clerk in Emberhall")
                self.say("The clerk rasps out one useful warning: Varyn keeps a reserve vial for the first enemy who lands a real hit.")
            else:
                self.say("You save what life you can, but the warning dies in fragments.")
        elif choice == 2:
            self.player_speaker("Give me the ledgers. I want the shape of Varyn's exits and lies.")
            success = self.skill_check(self.state.player, "Investigation", 13, context="to decode Varyn's fallback routes before the last fight")
            if success:
                self.state.flags["emberhall_ledger_read"] = True
                self.reward_party(xp=15, reason="decoding Varyn's fallback plan")
                self.say("You map the hall fast enough to know where Varyn intended to break line and reposition.")
            else:
                self.say("You get the broad shape of the chamber, but not every escape seam.")
        else:
            self.player_action("Smash the poison table and flood the hall with glass, fumes, and noise.")
            self.state.flags["emberhall_poison_table_broken"] = True
            self.say("Glass and reeking poison spread across the hall entrance, forcing the final fight to start amid chaos you chose.")

        self.complete_map_room(dungeon, room.room_id)

    def _emberhall_ash_archive(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        self.say("The ash archive is part record room, part panic stash, with soot-marked ledgers stacked beside reserve doors.")
        choice = self.scenario_choice(
            "How do you work the archive?",
            [
                self.quoted_option("INVESTIGATION", "Search the ledgers and map which exits Varyn still believes in."),
                self.quoted_option("PERCEPTION", "There is something else hidden in here besides paperwork."),
                self.action_option("Sweep the room fast, pocket anything sharp, and keep moving."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("Search the ledgers and map which exits Varyn still believes in.")
            success = self.skill_check(self.state.player, "Investigation", 13, context="to search the ash archive under pressure")
            if success:
                self.state.flags["emberhall_archive_tip"] = True
                self.add_clue("The archive confirms Varyn planned to break toward a reserve room if the sanctum line folded.")
                self.reward_party(xp=10, reason="mapping Emberhall's reserve route")
                self.say("You trace the reserve route cleanly enough to turn the final chamber into a known problem.")
            else:
                self.say("You get the broad shape of the reserve route, but not every seam.")
        elif choice == 2:
            self.player_speaker("There is something else hidden in here besides paperwork.")
            success = self.skill_check(self.state.player, "Perception", 13, context="to find a useful reserve in the archive")
            if success:
                self.state.flags["emberhall_archive_tip"] = True
                self.add_inventory_item("potion_healing", source="a hidden archive shelf")
                self.say("A false shelf gives up a sealed potion case and a cleaner line on the reserve door.")
            else:
                self.say("You find the clutter, but not the clever part of it.")
        else:
            self.player_action("Sweep the room fast, pocket anything sharp, and keep moving.")
            self.say("You leave the archive in disorder and make sure whatever comes after you has to work harder than you did.")

        self.complete_map_room(dungeon, room.room_id)

    def _emberhall_black_reserve(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        party_size = self.act1_party_size()
        enemies = [create_enemy("bandit", name="Ashen Brand Enforcer"), create_enemy("bandit_archer", name="Reserve Sniper")]
        if party_size >= 3:
            enemies.append(self.act1_pick_enemy(("bandit", "cinderflame_skull", "whispermaw_blob")))
        if party_size >= 4:
            enemies.append(self.act1_pick_enemy(("bandit_archer", "cinderflame_skull", "whispermaw_blob")))
        self.say("The reserve room opens on a last cache of disciplined muscle, poison, and backup steel.")
        outcome = self.run_encounter(
            Encounter(
                title="Emberhall Black Reserve",
                description="The reserve room empties itself into the fight rather than let you reach Varyn cleanly.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=False,
                hero_initiative_bonus=1 if self.state.flags.get("emberhall_archive_tip") else 0,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("Emberhall's reserve room slams shut around the party.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You pull back from the reserve room before it can close around you.")
            return

        self.complete_map_room(dungeon, room.room_id)

    def _emberhall_varyn_sanctum(self, dungeon: DungeonMap, room: DungeonRoom) -> None:
        assert self.state is not None
        party_size = self.act1_party_size()
        boss_enemies = [create_enemy("varyn"), create_enemy("bandit", name="Ashen Brand Enforcer"), create_enemy("bandit_archer")]
        if party_size >= 3:
            boss_enemies.append(self.act1_pick_enemy(("bandit", "cinderflame_skull", "whispermaw_blob")))
        if party_size >= 4:
            boss_enemies.append(self.act1_pick_enemy(("bandit_archer", "cinderflame_skull", "gutter_zealot")))
        boss_bonus = 0
        if self.state.flags.get("emberhall_clerk_saved"):
            boss_bonus += 1
        if self.state.flags.get("emberhall_ledger_read"):
            boss_bonus += 1
        if self.state.flags.get("emberhall_poison_table_broken"):
            boss_bonus += 2
        if self.state.flags.get("emberhall_archive_tip"):
            boss_bonus += 1
        choice = self.scenario_choice(
            "Varyn Sable waits in the last chamber with ash banners at their back.",
            [
                self.quoted_option("PERSUASION", "It is over. Walk up the stairs alive, or do not walk them at all."),
                self.quoted_option("INTIMIDATION", "You are out of road, out of men, and out of time."),
                self.action_option("No more speeches. End this now."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_speaker("It is over. Walk up the stairs alive, or do not walk them at all.")
            success = self.skill_check(self.state.player, "Persuasion", 15, context="to make Varyn feel the walls finally closing in")
            if success:
                fleeing = boss_enemies.pop()
                self.say(f"{fleeing.name} breaks for the stairs before the first strike lands.")
                boss_bonus += 1
            else:
                self.speaker("Varyn Sable", "If it were over, you would not still be trying to talk me out of surviving it.")
        elif choice == 2:
            self.player_speaker("You are out of road, out of men, and out of time.")
            success = self.skill_check(self.state.player, "Intimidation", 15, context="to crack the captain's final composure")
            if success:
                boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 5)
                self.apply_status(boss_enemies[0], "reeling", 2, source="your certainty finally landing")
                self.say("For the first time, Varyn looks less amused than calculating.")
            else:
                self.apply_status(boss_enemies[0], "emboldened", 2, source="defying your threat")
                self.speaker("Varyn Sable", "That is what people say right before they become examples.")
        else:
            self.player_action("No more speeches. End this now.")
            boss_enemies[0].current_hp = max(1, boss_enemies[0].current_hp - 3)
            boss_bonus += 2
            self.say("Steel and spell-fire answer before Varyn can turn the room into a conversation again.")

        outcome = self.run_encounter(
            Encounter(
                title="Boss: Varyn Sable",
                description="The captain of the Ashen Brand makes the final stand beneath Phandalin.",
                enemies=boss_enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=15,
                hero_initiative_bonus=boss_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The cellar banners remain standing above a fallen company.")
            return
        if outcome == "fled":
            self.return_to_phandalin("You escape the cellars and return to the surface to recover.")
            return

        self.complete_map_room(dungeon, room.room_id)
        self.say(
            "Varyn falls, the remaining brigands scatter, and the pressure that has bent every road into Phandalin finally breaks. Among the captain's ledgers are references to older powers stirring beneath the Sword Mountains, "
            "with whispers pointing toward deeper ruins, buried wealth, and unfinished business near Wave Echo Cave."
        )
        self.add_journal("You broke the Ashen Brand and secured Phandalin through the end of Act 1.")
        self.reward_party(xp=250, gold=80, reason="securing Phandalin at the end of Act I")
        if 1 not in self.state.completed_acts:
            self.state.completed_acts.append(1)
        payload = self._map_state_payload()
        payload["current_dungeon_id"] = None
        payload["current_room_id"] = None
        payload["room_history"] = []
        payload["current_node_id"] = "emberhall_cellars"
        self.state.current_scene = "act1_complete"
        self._compact_hud_last_scene_key = None
        self.save_game(slot_name=f"{self.state.player.name}_act1_complete")
