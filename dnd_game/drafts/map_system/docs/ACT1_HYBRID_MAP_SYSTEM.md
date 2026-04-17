# Act 1 Hybrid Map System Draft

## Purpose

This draft started as an isolated Act 1 map concept and now closely mirrors the playable runtime route.

The structure combines three layers:

- node-based overworld travel
- grid-room local site maps
- linear unlocks driven by flags, quests, and light reactivity state

That matches the current Act 1 shape already present in the project:

- `phandalin_hub` is the central hub
- `old_owl_well` and `wyvern_tor` are the branch sites
- `cinderfall_ruins` is the hidden optional mid-act route
- `ashfall_watch` is the convergence assault
- `tresendar_manor` and `emberhall_cellars` are late linear descents
- Act 1 also tracks `Town Fear`, `Ashen Strength`, and `Survivors Saved` for late-act reactivity

## Rich-Guided Visual Direction

This draft now uses the `rich` design system directly for the preview and renderer layer.

The important part is the layout philosophy:

1. Keep a fixed screen order.
2. Use boxed sections instead of loose print spam.
3. Show different map scales in different modes.
4. Redraw from state rather than continuously appending text.
5. Use symbols consistently so the map is readable at a glance.

### Target screen order

1. HUD
2. Overworld or local map
3. Scene text
4. Action list

### Target visual roles

- cyan or blue: HUD and system information
- green: safe travel or currently available routes
- yellow: quest goals, treasure, and interactables
- red: danger and combat pressure
- magenta: boss rooms, magical locations, or special event beats

### Fallback rule

If `rich` is unavailable in another environment, the same structure still falls back to boxed ASCII panels and plain text.

## Folder Layout

The draft lives in a separate add-on structure:

- `dnd_game/drafts/map_system/README.md`
- `dnd_game/drafts/map_system/runtime/models.py`
- `dnd_game/drafts/map_system/runtime/engine.py`
- `dnd_game/drafts/map_system/runtime/presentation.py`
- `dnd_game/drafts/map_system/data/act1_hybrid_map.py`
- `dnd_game/drafts/map_system/examples/act1_preview.py`

## Core Map Philosophy

Act 1 should not use a single map format for every problem.

### Overworld

Use nodes for major travel and campaign pacing.

This layer answers:

- where can the player go next
- what routes are currently unlocked
- what the broad story shape looks like

### Local site map

When the player enters a hostile site, switch to a compact room grid.

This layer answers:

- what room am I in
- what is adjacent
- what branch did I skip
- what is still locked

### Story gate layer

Use flags and quests to decide when major destinations and boss rooms open.

This layer answers:

- when Ashfall becomes available
- when the hidden `Cinderfall` path becomes visible
- when Tresendar is revealed
- when Emberhall becomes the final route
- what kind of ending pressure gets handed into Act 2

## Overworld Node Draft

### Node list

| Node id | Scene key | Role | Unlock rule |
| --- | --- | --- | --- |
| `neverwinter_briefing` | `neverwinter_briefing` | story | `act1_started` |
| `high_road_ambush` | `road_ambush` | story | `act1_started` |
| `phandalin_hub` | `phandalin_hub` | hub | `phandalin_arrived` |
| `old_owl_well` | `old_owl_well` | dungeon entry | `miners_exchange_lead` or quest `silence_old_owl_well` |
| `cinderfall_ruins` | `cinderfall_ruins` | dungeon entry | `hidden_route_unlocked` |
| `wyvern_tor` | `wyvern_tor` | dungeon entry | `edermath_orchard_lead` or quest `break_wyvern_tor_raiders` |
| `ashfall_watch` | `ashfall_watch` | dungeon entry | `old_owl_well_cleared` and `wyvern_tor_cleared` |
| `tresendar_manor` | `tresendar_manor` | dungeon entry | `tresendar_revealed` |
| `emberhall_cellars` | `emberhall_cellars` | dungeon entry | `tresendar_cleared` and `emberhall_revealed` |

### World-map draft feel

```text
                 [NEVERWINTER]
                       |
                  [HIGH ROAD]
                       |
                  [PHANDALIN*]
               /       |       \
      [OLD OWL] [CINDERFALL] [WYVERN TOR]
               \       |       /
                    [ASHFALL]
                       |
                  [TRESENDAR]
                       |
                  [EMBERHALL]
```

Visual rules:

- current node gets a marker such as `*`
- locked nodes can render as `[?]`
- revealed but not entered nodes use their normal label
- optional story beats can be listed below the map panel

## Story Beats

These are linear progress points hosted by the hub rather than separate travel nodes.

| Beat id | Host | Requirement | Grants |
| --- | --- | --- | --- |
| `stonehill_council` | `phandalin_hub` | `old_owl_well_cleared` and `wyvern_tor_cleared` | `phandalin_council_seen`, `ashfall_route_confirmed` |
| `lantern_vigil` | `phandalin_hub` | `ashfall_watch_cleared` | `phandalin_after_watch_seen`, `tresendar_revealed` |

This keeps the map readable while still preserving strong authored pacing.

## Local Site Map Drafts

Local maps should be small enough to read quickly and rich enough to feel spatial.

Recommended symbol meanings:

- `P` player
- `E` combat room
- `*` event room
- `T` treasure or clue room
- `B` boss room
- `?` locked or undiscovered room
- `#` no room
- `.` cleared room

## Old Owl Well

### Goal

Turn the site into a short branch-first dig map.

### Structure

```text
[Dig Ring] -> [Salt Cart Hollow] -> [Buried Dark Lip]
     |
     v
[Supply Trench] ----------------> [Buried Dark Lip]
```

### Room logic

- `well_ring`
  - opening fight
  - grants `old_owl_ring_cleared`
- `salt_cart`
  - rescue branch
  - grants `old_owl_prospector_rescued`
- `supply_trench`
  - clue branch
  - grants `old_owl_notes_found`
- `gravecaller_lip`
  - boss room
  - opens when either branch flag is complete

This is the first example of the hybrid rule you asked for:

the boss room is structurally locked behind site progress instead of simply being the last scene in a line.

## Wyvern Tor

### Goal

Keep the site outdoors while still using room-grid pacing.

### Structure

```text
[Goat Path] -> [Drover Hollow] -> [Broken High Shelf]
     |
     v
[Shrine Ledge] ----------------> [Broken High Shelf]
```

### Room logic

- `goat_path`
  - opening shelf fight
- `drover_hollow`
  - rescue and tactical info
- `shrine_ledge`
  - optional side branch
- `high_shelf`
  - Brughor boss room
  - opens once one side branch has been resolved

## Cinderfall Ruins

### Goal

Add a hidden third route that lets the player cut Ashfall's reserve relay before the main assault.

### Structure

```text
[Collapsed Gate] -> [Ash Chapel] -------> [Ember Relay Node]
       |
       v
[Broken Storehouse] --------------------> [Ember Relay Node]
```

### Room logic

- `collapsed_gate`
  - opening breach and first fight
- `ash_chapel`
  - rescue and shrine branch
- `broken_storehouse`
  - reserve-slate and supply branch
- `ember_relay`
  - relay boss room
  - clearing it grants `cinderfall_relay_destroyed`

### Story function

- Exposes the Ashen Brand's reserve-supply line before `Ashfall Watch`
- Gives a real payoff branch where optional site progress makes the later fortress assault easier

## Ashfall Watch

### Goal

Make the assault feel like a defended fortress with meaningful objective sequencing.

### Structure

```text
            [Prisoner Yard]
                  |
[Gate Breach] -> [Lower Barracks] -> [Rukhar Command]
                  ^
                  |
            [Signal Basin]
```

### Room logic

- `breach_gate`
  - opening gate fight
- `prisoner_yard`
  - rescue branch
- `signal_basin`
  - sabotage branch
- `lower_barracks`
  - reconvergence combat room
- `rukhar_command`
  - boss room
  - requires both `ashfall_signal_basin_silenced` and `ashfall_lower_barracks_cleared`

This is the clearest Act 1 use of a linear unlock inside a grid site.

## Tresendar Manor

### Goal

Give the manor descent one mandatory combat lane and one clue lane.

### Structure

```text
[Hidden Stair] -> [Cellar Intake] -> [Cistern Eye]
      |
      v
[Cistern Walk] -> [Cage Store] ---> [Cistern Eye]
```

### Room logic

- `hidden_stair`
  - entrance
- `cellar_intake`
  - required combat room
- `cistern_walk`
  - clue route
- `cage_store`
  - optional follow-up clue room
- `nothic_lair`
  - boss room requiring the intake clear and at least one clue flag

## Emberhall Cellars

### Goal

Make the finale feel like a pressure descent where one route is mandatory and one route deepens context.

### Structure

```text
[Antechamber] -> [Ledger Chain Room] -----> [Varyn Sanctum]
      |
      v
[Ash Archive] -> [Black Reserve] ---------> [Varyn Sanctum]
```

### Room logic

- `antechamber`
  - threshold fight
- `ledger_chain`
  - mandatory route
- `ash_archive`
  - optional lore branch
- `black_reserve`
  - optional support combat room
- `varyn_sanctum`
  - boss room requiring `emberhall_chain_broken` and one secondary branch flag

## Draft HUD Direction

The HUD should always be present and compact.

Example:

```text
+- HUD ------------------------------------------------------+
| Tolan's Company    HP: 52/64    Gold: 143                  |
| Quest: Stop the Watchtower Raids                           |
| Layout order: HUD -> map -> scene text -> actions          |
+------------------------------------------------------------+
```

The player should never lose sight of:

- party condition
- active quest
- current mode

## Presentation Rules

### Fixed layout

Always render in this order:

1. title or chapter banner if needed
2. HUD
3. overworld or local map
4. scene text
5. actions

### Redraw behavior

Do not let the screen grow forever.

Instead:

- clear or redraw on major state change
- update the active panel
- keep the action list anchored

### Fog of war

A future version can hide unexplored rooms by rendering them as `?`.

That would fit very naturally into this draft because the room grid already distinguishes:

- room exists
- room is unlocked
- room is cleared
- room is still hidden or locked

## Flag Strategy

### Existing story-facing flags reused by the draft

- `act1_started`
- `phandalin_arrived`
- `miners_exchange_lead`
- `edermath_orchard_lead`
- `hidden_route_unlocked`
- `old_owl_well_cleared`
- `wyvern_tor_cleared`
- `cinderfall_relay_destroyed`
- `ashfall_watch_cleared`
- `tresendar_revealed`
- `tresendar_cleared`
- `emberhall_revealed`
- `act1_complete`

### Live room progression flags

- `old_owl_ring_cleared`
- `old_owl_prospector_rescued`
- `old_owl_notes_found`
- `wyvern_lower_path_cleared`
- `wyvern_drover_rescued`
- `wyvern_shrine_secured`
- `cinderfall_gate_opened`
- `cinderfall_chapel_secured`
- `cinderfall_storehouse_searched`
- `ashfall_gate_breached`
- `ashfall_prisoners_freed`
- `ashfall_signal_basin_silenced`
- `ashfall_lower_barracks_cleared`
- `tresendar_stair_found`
- `tresendar_intake_cleared`
- `tresendar_cistern_found`
- `tresendar_records_secured`
- `emberhall_threshold_crossed`
- `emberhall_chain_broken`
- `emberhall_archive_searched`
- `emberhall_reserve_opened`

These are now part of the playable Act 1 route rather than a purely hypothetical draft layer.

## Suggested Integration Path Later

If you decide to move beyond the draft, a low-risk path would be:

1. keep `current_scene` as the live scene authority
2. add a small `map_state` object to saves
3. let the hub choose destinations through the node system
4. let dungeon-entry scenes hand off to room progression
5. reuse existing combat and event content inside each room

That way the writing, quests, and scene content do not need a full rewrite.

## Preview Support Included In This Draft

The draft includes:

- a native `rich` renderer with panels, tables, alignment, and split-screen layout
- a boxed plain-text fallback renderer
- an overworld template for Act 1
- a grid-based dungeon renderer for room maps
- a small example script that previews the Ashfall Watch version of the layout

## Best Next Decisions For Us

These are the most useful choices to make next as you guide the draft:

1. Whether Phandalin should remain one hub node or split into subnodes later.
2. Whether dungeon maps should use full fog of war or simply locked-room markers.
3. Whether side rooms should grant clues only or also mechanical bonuses.
4. Whether backtracking inside a site should be free, limited, or scene-based.
5. Whether the local mini-map should be always visible or only shown on demand.

## Current Scope

This draft is still Act 1 focused, but it now describes a route structure that materially feeds the live game rather than an isolated prototype.
