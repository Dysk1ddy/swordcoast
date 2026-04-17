# Embers Before the Road: Repo-Specific Implementation Checklist

This checklist maps the Blackwake Crossing branch onto the current codebase. The existing Act 1 flow is a Python text RPG with scene handlers, a draft-backed route map, room-grid site logic, quest definitions, enemy factories, and companion profiles.

## Current Status

### Completed

- Route fork after leaving Neverwinter: direct road, Blackwake smoke investigation, and one-rumor loop.
- `blackwake_crossing` and `road_decision_post_blackwake` scene dispatch, objectives, and map entries.
- Blackwake Crossing dungeon blueprint with tollhouse, Miller's Ford, Gallows Copse, Store Cavern, and Floodgate Chamber rooms.
- Room handlers for the branch's investigation, rescue, forged-paper, prisoner, workshop, command-office, and finale scenes.
- `trace_blackwake_cell` quest definition and completion readiness via `blackwake_completed`.
- `brand_saboteur` and `sereth_vane` enemy templates, loot tables, and special combat behaviors.
- Finale moral choices for `rescue`, `evidence`, and `sabotage`, including rewards, flags, trust deltas, and route reconvergence.
- Post-Blackwake return choice: report to Neverwinter, press south, or camp first.
- Phandalin arrival, steward, inn, and camp conversation aftermath hooks.
- Sereth escape follow-up on the High Road through `blackwake_sereth_road_note_seen`.
- Act 2 escaped-Sereth callback stub through `act2_sereth_shadow_active`.

### Still Useful To Add Later

- Full interactive route tests that walk through Miller's Ford-only and Gallows Copse-only clears via navigation prompts.
- Full Act 2 Sereth encounter or claim-chain scene if `act2_sereth_shadow_active`.
- More Blackwake-specific journal stage notes for each room, if the journal needs finer-grained progress breadcrumbs.

## Current Ownership Map

- `dnd_game/gameplay/story_intro.py`
  - Owns the beginning of Act 1.
  - `scene_neverwinter_briefing()` currently sends the player directly to `road_ambush` after the early companion choice.
  - `scene_road_ambush()` owns the existing High Road ambush, Tolan recruitment, and transition to `phandalin_hub`.

- `dnd_game/gameplay/base.py`
  - Owns scene metadata and dispatch.
  - Add new scene keys to `SCENE_OBJECTIVES` and `_scene_handlers`.
  - Add `Sereth Vane` to `NAMED_CHARACTER_INTROS` so boss introductions render consistently.

- `dnd_game/drafts/map_system/data/act1_hybrid_map.py`
  - Owns the Act 1 overworld and dungeon-map blueprints.
  - Existing Act 1 route starts as `neverwinter_briefing -> high_road_ambush -> phandalin_hub`.
  - Existing Act 1 dungeon maps are declared as `DungeonMap` objects with `DungeonRoom` rooms, requirements, clear flags, and boss rooms.

- `dnd_game/gameplay/map_system.py`
  - Imports `ACT1_HYBRID_MAP`.
  - Owns Act 1 map state, navigation, site scene wrappers, room dispatch, room completion, and Act 1 metrics.
  - `run_act1_dungeon()` currently assumes Act 1 site withdrawal returns to Phandalin. Blackwake needs special return handling because it occurs before Phandalin.

- `dnd_game/data/story/factories.py`
  - Owns `create_enemy()`.
  - Add `brand_saboteur` and `sereth_vane` templates here.

- `dnd_game/gameplay/combat_flow.py`
  - Owns special enemy archetype behavior in `enemy_turn()`.
  - Add `brand_saboteur` behavior for `flash_ash` and `retreat_step`.
  - Add `sereth_vane` behavior for `silver_pressure`, `flash_ash`, `command_relocate`, and the high-roll poison rider if implementing it centrally.

- `dnd_game/data/quests/act1.py`
  - Owns Act 1 quest definitions.
  - Add `trace_blackwake_cell`.

- `dnd_game/gameplay/quests.py`
  - Quest readiness is currently flag-based: all `completion_flags` must be truthy.
  - Blackwake quest completion should use `blackwake_completed`.
  - Intermediate journal stages should be added through `append_quest_note()` and `add_journal()`.

- `dnd_game/data/story/companions.py`
  - Owns companion camp topics, trust deltas for camp dialogue, relationship bonuses, and scene support.
  - Add Blackwake camp topics and optional scene support here.

- `dnd_game/gameplay/companions.py`
  - Owns `adjust_companion_disposition()` and `apply_scene_companion_support()`.
  - Field-scene trust changes should be called from Blackwake scene code.

- `tests/test_core.py`
  - Contains route, map, quest, enemy, combat, and companion tests.
  - Add focused tests as each milestone lands.

## Suggested Implementation Shape

Use one new pre-Phandalin scene key plus one new Act 1 map node:

- Scene key: `blackwake_crossing`
- Travel node id: `blackwake_crossing`
- Dungeon id: `blackwake_crossing_branch`
- Return scene key: `road_decision_post_blackwake`

This matches the current room-grid site architecture without forcing the branch into separate fully independent overworld nodes. Model Charred Tollhouse, Miller's Ford, Gallows Copse, and Blackwake Store Cavern as rooms and gated room clusters inside one `DungeonMap`.

Keep the explicit narrative structure in code with comments or helper names:

```python
blackwake_branch = {
    "entry": "charred_tollhouse",
    "mid_routes": ["millers_ford", "gallows_copse"],
    "finale": "blackwake_store_cavern",
    "return_hub": "road_decision_post_blackwake",
}
```

## Milestone 1: Route Skeleton

- In `dnd_game/gameplay/story_intro.py`
  - Change the departure branch in `scene_neverwinter_briefing()` so leaving Neverwinter opens a route fork after the early companion offer.
  - Add a helper such as `handle_neverwinter_departure_fork()`.
  - Route choices:
    - Direct south road: set `current_scene = "road_ambush"`.
    - Investigate smoke near the river cut: set `blackwake_started = True`, grant `trace_blackwake_cell`, set `current_scene = "blackwake_crossing"`.
    - Circle back for one more rumor: reuse or lightly expand `handle_neverwinter_prep()` only if `neverwinter_preparation_done` is false; otherwise provide a short flavor line and show the fork again.

- In `dnd_game/gameplay/base.py`
  - Add `blackwake_crossing` and `road_decision_post_blackwake` to `SCENE_OBJECTIVES`.
  - Add both to `_scene_handlers`.
  - Add `Sereth Vane` to `NAMED_CHARACTER_INTROS`.

- In `dnd_game/drafts/map_system/data/act1_hybrid_map.py`
  - Update `overworld_template` so Blackwake appears between Neverwinter and High Road.
  - Add `TravelNode("blackwake_crossing", scene_key="blackwake_crossing", kind="dungeon_entry", enters_dungeon_id="blackwake_crossing_branch")`.
  - Add a story or hub node for `road_decision_post_blackwake` only if the map needs to display it; otherwise keep it as a scene-only return node.
  - Add edges:
    - `neverwinter_briefing -> blackwake_crossing`
    - `blackwake_crossing -> high_road_ambush` gated by `blackwake_completed`
    - optionally `blackwake_crossing -> neverwinter_briefing` gated by `blackwake_completed` or represented through the return scene.

- In `dnd_game/gameplay/map_system.py`
  - Add `scene_blackwake_crossing()` that calls `run_act1_dungeon("blackwake_crossing")`.
  - Add `scene_road_decision_post_blackwake()`.
  - Add Blackwake room ids to `_run_act1_room()`.
  - Add a Blackwake-specific return helper instead of using `return_to_phandalin()`.
  - Extend withdrawal/navigation labels so Blackwake does not offer `Withdraw to Phandalin` before Phandalin exists.

- In `dnd_game/data/quests/act1.py`
  - Add `trace_blackwake_cell` with `completion_flags=("blackwake_completed",)`.

- Tests to add in `tests/test_core.py`
  - Leaving Neverwinter can still choose direct road and reach `road_ambush`.
  - Leaving Neverwinter can choose Blackwake and reach `blackwake_crossing`.
  - `trace_blackwake_cell` is granted when Blackwake starts.
  - Act 1 map can initialize for `blackwake_crossing`.

## Milestone 2: Blackwake Map Blueprint

Add a `DungeonMap` to `ACT1_HYBRID_MAP.dungeons`:

- `dungeon_id="blackwake_crossing_branch"`
- `title="Blackwake Crossing"`
- `entry_node_id="blackwake_crossing"`
- `entrance_room_id="charred_tollhouse"`
- `exit_to_node_id="road_decision_post_blackwake"`
- `completion_flags=("blackwake_completed",)`
- `boss_room_id="floodgate_chamber"`

Recommended room structure:

- `charred_tollhouse`
  - Mandatory entrance.
  - Exits to `millers_ford_flooded_approach` and `gallows_copse_hanging_path` after completion.

- Miller's Ford cluster
  - `millers_ford_flooded_approach`
  - `millers_ford_wagon_snarl`
  - `millers_ford_reedbank_camp`
  - `millers_ford_ledger_post`

- Gallows Copse cluster
  - `gallows_copse_hanging_path`
  - `gallows_copse_cage_clearing`
  - `gallows_copse_watcher_tree`
  - `gallows_copse_root_cellar`

- Store Cavern cluster
  - `blackwake_outer_cache`
  - `blackwake_prison_pens`
  - `blackwake_seal_workshop`
  - `blackwake_ash_office`
  - `blackwake_floodgate_chamber`

Gating rules:

- Cavern entrance requires at least one of:
  - `blackwake_forged_papers_found`
  - `blackwake_transfer_list_found`
  - `blackwake_tollhouse_partial_clue`
- Strong finale options require both:
  - `blackwake_forged_papers_found`
  - `blackwake_transfer_list_found`
- Reduced final pressure if both mid-routes are substantially resolved:
  - `blackwake_ford_secured`
  - `blackwake_captives_freed`

Tests to add:

- Tollhouse is always the entrance room.
- Miller's Ford and Gallows Copse are both reachable after Tollhouse.
- Store Cavern is locked before at least one clue.
- Store Cavern unlocks after either mid-route clue.
- Strong finale condition is true only after both route clues.

## Milestone 3: Room Handlers and Scene Content

Add room handlers in `dnd_game/gameplay/map_system.py`.

Required handlers:

- `_blackwake_charred_tollhouse()`
  - Grant quest if missing.
  - Choices: Investigation, Medicine, Intimidation, Persuasion.
  - Set one or more clue flags.
  - Optional small fight using `bandit`, `bandit_archer`, `wolf`, `brand_saboteur`.

- `_blackwake_ford_flooded_approach()`
  - Choices: Survival, Animal Handling, Stealth.

- `_blackwake_ford_wagon_snarl()`
  - Choices: free civilians, secure cargo, prep ambush.
  - Track `blackwake_survivors_saved`.

- `_blackwake_ford_reedbank_camp()`
  - Choices: infiltrate, interrogate lookout, steal seal kit.
  - Track `blackwake_forged_papers_found`.

- `_blackwake_ford_ledger_post()`
  - Fight, parley, or expose fake authority.
  - Track `blackwake_ford_secured`.

- `_blackwake_copse_hanging_path()`
  - Choices: Religion, Perception, Stealth.

- `_blackwake_copse_cage_clearing()`
  - Choices: free captives now, question first, observe transfer.
  - Track `blackwake_captives_freed`.

- `_blackwake_copse_watcher_tree()`
  - Choices: climb and scout, cut charms, leave and track.
  - Track alarm state if appropriate.

- `_blackwake_copse_root_cellar()`
  - Choices: inspect crates, decode symbols, force cellar.
  - Track `blackwake_transfer_list_found`.

- `_blackwake_outer_cache()`
  - Choices: Stealth, Deception if papers found, Athletics.

- `_blackwake_prison_pens()`
  - Choices: free quietly, arm prisoners, leave for later.

- `_blackwake_seal_workshop()`
  - Choices: seize evidence, destroy workshop, copy names.

- `_blackwake_ash_office()`
  - Add Phandalin pressure clues and hobgoblin supervision foreshadowing.

- `_blackwake_floodgate_chamber()`
  - Sereth conversation, miniboss encounter, ending choice.

## Milestone 4: Enemies and Combat Behaviors

- In `dnd_game/data/story/factories.py`
  - Add `brand_saboteur`.
  - Add `sereth_vane`.
  - Give both `tags=["enemy", "humanoid", "parley"]`; add `"leader"` to Sereth.

- In `dnd_game/gameplay/combat_flow.py`
  - Add `brand_saboteur` resource checks:
    - `flash_ash`: CON save DC 11 or `blinded` 1.
    - `retreat_step`: when low HP or after a hit, self `emboldened` or shift targeting. Keep this simple unless the combat engine exposes movement.
  - Add `sereth_vane` resource checks:
    - `silver_pressure`: WIS save DC 12 or `reeling` 2.
    - `flash_ash`: CON save DC 12 or `blinded` 1.
    - `command_relocate`: one ally gains `emboldened` 1.
    - High-roll poison rider may be added to `perform_enemy_attack()` if there is already a clean critical/high-roll hook; otherwise implement Sereth as a normal special turn first.

- In `dnd_game/data/items/catalog.py`
  - Add loot-table entries for `brand_saboteur` and `sereth_vane`.
  - Prefer existing item ids first: `potion_healing`, `antitoxin_vial`, `travel_biscuits`, `scroll_clarity`, `dust_of_disappearance`.

Tests to add:

- `create_enemy("brand_saboteur")` returns expected name, HP, XP, archetype, resources.
- `create_enemy("sereth_vane")` returns expected name, HP, XP, leader/parley tags.
- `brand_saboteur` flash ash can apply `blinded`.
- `sereth_vane` silver pressure can apply `reeling`.

## Milestone 5: Finale, Consequences, and Rejoin

- In `dnd_game/gameplay/map_system.py`
  - Add Sereth's pre-fight conversation.
  - Gate stronger confrontation by both mid-route evidence flags.
  - Resolve `blackwake_sereth_fate` as `dead`, `escaped`, or `captured`.
  - Add final choice:
    - `rescue`
    - `evidence`
    - `sabotage`
  - Set:
    - `blackwake_completed = True`
    - `blackwake_resolution`
    - `blackwake_return_destination`

- Add `scene_road_decision_post_blackwake()`
  - Return to Neverwinter.
  - Press south toward Phandalin by setting `current_scene = "road_ambush"`.
  - Camp first, then return to this decision scene.

- Add a Neverwinter payoff helper in `story_intro.py` or `map_system.py`
  - Report to Mira.
  - Give reward based on `blackwake_resolution`.
  - Re-offer departure south.

- Add downstream hooks:
  - `blackwake_resolution == "sabotage"` should reduce later Ashen Brand pressure. Reuse `act1_adjust_metric("act1_ashen_strength", -1)` and/or update `act1_relay_sabotaged()` to include this flag.
  - `blackwake_resolution == "evidence"` should affect Phandalin/Neverwinter dialogue lines.
  - `blackwake_resolution == "rescue"` should affect survivor/townsfolk warmth.
  - `blackwake_sereth_fate == "escaped"` should leave a future rumor/note flag.

Tests to add:

- Rescue ending sets completion and resolution flags.
- Evidence ending sets completion and resolution flags.
- Sabotage ending reduces later Ashen pressure or thins a later fight.
- Return to Neverwinter payoff leads back to departure.
- Press south after Blackwake leads to existing `road_ambush`.

## Milestone 6: Companion and Camp Integration

- In `dnd_game/data/story/companions.py`
  - Add Blackwake camp topics to Kaelis, Rhogar, Bryn, Elira, and optionally Tolan.
  - Use ids such as:
    - `blackwake_crossing`
    - `ledgers_or_people`
    - `neverwinter_cares`
  - Add `scene_support` entries for `blackwake_crossing` where appropriate.

- In room/finale handlers
  - Apply small trust deltas with `adjust_companion_disposition()` only at meaningful decision points:
    - Kaelis: +1 stealth/patterns, -1 sloppy destruction.
    - Rhogar: +1 protecting civilians/direct confrontation, -1 cruel deception or abandoned prisoners.
    - Bryn: +1 forged papers/smuggler intel/infiltration, -1 trusting officials too easily.
    - Elira: +1 healing/rescue/mercy, -1 evidence over lives or abandoning wounded.
  - Do not depend on Tolan because this branch happens before his normal recruitment.

Tests to add:

- Rescue-first ending can improve Elira/Rhogar trust if present.
- Evidence-over-lives can reduce Elira trust if present.
- Blackwake camp topics appear after `blackwake_completed`.
- Tolan absence does not break the branch.

## Minimal Test Matrix

- Skip Blackwake entirely and reach `road_ambush`.
- Enter Blackwake, complete only Miller's Ford, unlock and finish finale.
- Enter Blackwake, complete only Gallows Copse, unlock and finish finale.
- Complete both mid-routes and get stronger Sereth option.
- Finish with `rescue`.
- Finish with `evidence`.
- Finish with `sabotage`.
- Return to Neverwinter, then depart south.
- Continue south immediately.
- Camp at the post-Blackwake decision and return to the decision.

## Main Risk Notes

- `run_act1_dungeon()` currently assumes all Act 1 site withdrawal returns to Phandalin. Blackwake needs a branch-aware return destination before full content is added.
- `ACT1_SCENE_TO_NODE_ID` is built at import time from `ACT1_HYBRID_MAP`, so any new scene key must be present in the blueprint before map rendering can recognize it.
- Key evidence objects are not currently a separate key-item category. First pass should track papers, ledgers, and seal kits with flags and journal/clue text unless the item catalog is intentionally expanded.
- The existing `road_ambush` test inputs assume "Take the writ" is option 6. Adding a departure fork will require updating creation/briefing tests to account for the extra choice.
