# ACT 1 MAP SYSTEM REMAP — AETHRUNE COMPATIBILITY PASS

## Purpose

This document remaps the current playable Act 1 into the Aethrune setting **without breaking the existing code or gameplay flow**.

The goal is:

- keep the current Act 1 route order
- keep the current map-system logic
- keep the current dungeon progression structure
- keep current unlock dependencies and hub logic
- preserve the live room-based flow owned by `MapSystemMixin`
- replace player-facing setting/lore labels with original Aethrune equivalents

This follows the safer cleanup strategy recommended in the IP cleanup notes:

- preserve code architecture and encounter/state systems
- rewrite public-facing runtime labels first
- postpone deep internal id renames until later if needed

---

# CORE IMPLEMENTATION RULE

## Keep Internal IDs Stable For Now

To avoid breaking Act 1 progression, tests, saves, and route unlocks:

- keep existing internal scene ids
- keep existing internal flags
- keep existing quest ids unless they are explicitly rewritten later
- keep map unlock logic intact
- keep room graph structure intact
- keep route dependencies intact

### This means:

For now:
- `phandalin_hub` can still exist internally
- `old_owl_well`
- `wyvern_tor`
- `ashfall_watch`
- `tresendar_manor`
- `emberhall_cellars`

But the **player-facing runtime labels** should be rewritten to Aethrune equivalents.

This is the lowest-risk path and matches the cleanup guidance that public labels should be rewritten before deeper runtime refactors.

---

# ACT 1 REMAP PHILOSOPHY

The Act 1 skeleton is already strong and should be preserved.

Canonical route structure from the current playable Act 1:

1. background-specific prologue
2. shared pre-frontier road sequence
3. major city briefing
4. road ambush
5. optional side branches on the cleared road
6. frontier hub town
7. two major branch leads in either order
8. optional hidden relay dungeon
9. reconvergence council / war-room beat
10. major fortress assault
11. town aftermath / vigil
12. manor descent
13. final cellars dungeon
14. Act 1 completion / Act 2 handoff

That structure should remain unchanged.

---

# WORLD REMAP — ACT 1 SURFACE LAYER

## Region

- Old public framing: Sword Coast frontier
- New framing: **Shatterbelt Frontier**

## Major city opening

- Old: Neverwinter
- New: **Greywake**

## Main frontier hub town

- Old: Phandalin
- New: **Iron Hollow**

## Main road

- Old: High Road / Triboar Trail framing
- New: **Emberway**

The Emberway is the primary overland artery through the Shatterbelt: damaged, surveilled, and increasingly filtered by hostile route-control forces.

---

# ACT 1 RENAME MAP

## Public-Facing Location Rename Table

| Current public location | New public-facing Aethrune name | Keep internal id now? | Notes |
| --- | --- | --- | --- |
| Neverwinter | Greywake | Yes | major city opening and contract/briefing center |
| High Road | Emberway | Yes | main Act 1 travel spine |
| Wayside Luck Shrine | Wayside Lantern Shrine | Yes | early shared shrine stop |
| Greywake Triage Yard | Greywake Triage Yard | Yes | already original enough; keep |
| Greywake Road Breakout | Greywake Road Breakout | Yes | already original enough; keep |
| Phandalin | Iron Hollow | Yes | main Act 1 hub town |
| Stonehill Inn | Ashlamp Inn | Yes | Act 1 inn hub |
| Shrine of Tymora | Lantern Shrine | Yes | remove deity-specific reference |
| Barthen's Provisions | Hadrik's Provisions | Yes | shop reskin |
| Lionshield Trading Post | Ironbound Trading Post | Yes | shop/faction reskin |
| Edermath Orchard | Orchard Wall | Yes | keep function, rename surface label |
| Miner's Exchange | Delvers' Exchange | Yes | town political/economic hub |
| Old Owl Well | Blackglass Well | Yes | ruin/dig branch |
| Wyvern Tor | Red Mesa Hold | Yes | raider branch |
| Cinderfall Ruins | Cinderfall Ruins | Yes | already original enough; keep |
| Ashfall Watch | Ashfall Watch | Yes | already original enough; keep |
| Tresendar Manor | Duskmere Manor | Yes | late Act 1 descent site |
| Emberhall Cellars | Emberhall Cellars | Yes | already original enough; keep |
| Blackwake Crossing | Blackwake Crossing | Yes | already original enough; keep |

---

# ACT 1 CANONICAL ROUTE — AETHRUNE VERSION

## 1. Background Prologues

Keep the structure of the current background-specific openings.

### Goal
Preserve:
- same background gating
- same opening choice pattern
- same early combat / bypass logic
- same `system_profile_seeded` role
- same route into the shared Act 1 opening

### Surface rewrite
The prologues are now framed as Greywake district incidents, frontier breakdowns, forged route papers, missing surveys, poisoned caravans, and supply manipulation tied to the Shatterbelt.

### Recommended city-facing renames
- South Barracks Muster -> South Gate Muster
- Hall of Justice Hospice -> Lantern Hospice
- Blacklake Docks -> South Quay Docks
- House of Knowledge Archives -> Greywake Archive Hall
- Protector's Enclave Market -> Iron Quarter Market
- River District Counting-House -> Lower Ledger Hall
- Neverwinter Wood Trail Camp -> Greywake Wood Trail Camp

Functionally, these should behave the same.

---

## 2. Shared Early Road Sequence

Keep:
- Wayside shrine beat
- triage sequence
- breakout sequence
- movement into the contract / briefing phase

### Surface rewrite
This is now the shift from urban stability into frontier instability:
- Lantern Shrine
- Greywake Triage Yard
- Greywake Road Breakout

This part should establish:
- the Ashen Brand as structured route saboteurs
- Greywake as a city losing grip on its frontier
- the Emberway as the critical road into Iron Hollow

---

## 3. Greywake Briefing (Was Neverwinter Briefing)

Keep the same logic:
- central exposition scene
- final preparation choice
- early companion choice
- departure toward the road ambush

### Story function
This remains the “city sends you frontierward” launch scene.

### Surface rewrite
The briefing now frames:
- Iron Hollow as a mining and route hub under pressure
- the Ashen Brand as a logistical control force
- the ruined infrastructure as Accord-era remnants beneath the frontier

Companion selection remains structurally identical.

---

## 4. Emberway Road Ambush (Was High Road Ambush)

Keep:
- two-wave ambush structure
- Tolan recruitment pivot
- immediate branch unlock behavior after victory
- same combat/opening choice pattern

### Surface rewrite
This is no longer simply a road ambush outside Phandalin.

It is an attack on the Emberway:
- a controlled disruption point
- a proof that the Ashen Brand is sorting traffic
- a first major example of route pressure

### Keep support logic
- Kaelis still supports this scene
- Tolan can still join immediately or wait at the inn
- side branches still unlock after clearing the second wave

---

## 5. Cleared Emberway Side Branches

Preserve the cleared-road travel menu and all backtrack behavior.

Canonical existing side branch structure:
- main route to the hub
- liar puzzle side branch
- false checkpoint branch
- false tollstones branch
- backtrack memory behavior

### Aethrune rewrite

#### Liar's Circle
Keep mechanically identical.
New surface framing:
- an Accord-era roadside test circle
- old civic truth puzzle turned into a cursed roadside relic

#### False Roadwarden Checkpoint
Keep mechanically identical.
New framing:
- fake Emberway authority post
- copied Greywake civic language
- route categorization, false inspections, predictive control

#### False Tollstones
Keep mechanically identical.
New framing:
- old Accord toll markers reactivated or imitated
- extortion disguised as route order

These branches are especially important because they teach the player that road authority has been weaponized.

---

# IRON HOLLOW HUB (Was Phandalin Hub)

## Core Rule
Keep the hub menu structure intact.

### Current hub functions that should remain:
- steward / leadership loop
- inn loop
- shrine loop
- merchant loop
- trade-post loop
- orchard / walls loop
- exchange / claim politics loop
- camp access
- rest access
- branch-site departures
- gated late-act departures

## New hub identity: Iron Hollow

Iron Hollow is:
- a route town
- a mining settlement
- a civic chokepoint
- a settlement living on top of broken Accord foundations

It should feel:
- tense
- half-defended
- politically fragile
- strategically important

---

## Hub rename map

| Current public label | New public-facing label |
| --- | --- |
| Report to Steward Tessa Harrow | Report to Steward Tessa Harrow |
| Visit the Stonehill Inn | Visit the Ashlamp Inn |
| Stop by the shrine of Tymora | Stop by the Lantern Shrine |
| Barthen's Provisions | Hadrik's Provisions |
| Lionshield trading post | Ironbound Trading Post |
| Walk the old walls of Edermath Orchard | Walk the old orchard wall |
| Step into the Miner's Exchange | Step into the Delvers' Exchange |

### NPC carryover note
Strong original-facing characters can stay:
- Tessa Harrow
- Elira Dawnmantle
- Kaelis Starling
- Rhogar Valeguard
- Tolan Ironshield
- Bryn Underbough

But deity- and setting-specific bios should be rewritten later.

---

# MAJOR ACT 1 BRANCH SITES

## Branch A — Blackglass Well (Was Old Owl Well)

### Core role
Preserve this as:
- one of the two required mid-Act branch sites
- a ruin/dig site
- undead / excavation / filtered-route pressure zone
- Vaelith-associated site
- supply-trench clue site

### New surface framing
Blackglass Well is:
- an Accord-era intake shaft / vertical observatory well
- later reused as a salvage and burial site
- now being excavated under hostile protection

### Why this works
It preserves the current gameplay role:
- “old ruin with dangerous digging and undead pressure”
while removing the official place anchor.

### Map role
Do not change the route slot or dependency.
This remains one of the two gates before Ashfall Watch.

---

## Branch B — Red Mesa Hold (Was Wyvern Tor)

### Core role
Preserve this as:
- raider / brute / beast branch
- second required mid-Act branch site
- site of pressure-based detour logic
- Rukhar-adjacent hostile route-control zone

### New surface framing
Red Mesa Hold is:
- a wind-cut plateau stronghold overlooking Emberway detours
- used by raiders to force travelers into predictable route lanes

### Why this works
This keeps the exact same branch purpose:
- aggressive pressure from above
- enemy force controlling movement
- optional intimidation / route-reading payoff

---

## Optional Hidden Branch — Cinderfall Ruins

### Core rule
Keep this location exactly as a major optional hidden branch.

This location is already original-facing enough to preserve.

### Role
- hidden strike site
- relay / sabotage dungeon
- proof that the Ashen Brand operates as a network with relay discipline
- optional weakening action before Ashfall Watch

### Surface framing in Aethrune
Cinderfall was once an Accord relay station managing:
- emergency route reroutes
- signal timing
- reserve movement
- controlled traffic overflow

Now it has been repurposed by the Ashen Brand as a relay node.

### Important
Do not alter:
- hidden unlock logic
- optional status
- sabotage payoff
- act progression value

---

# RECONVERGENCE

## Iron Hollow War-Room Event

Keep the Stonehill war-room style reconvergence after the two major branch sites are cleared.

### New surface version
This becomes:
- Ashlamp Inn back-room map table
or
- Iron Hollow council map room

Both are valid.
For safest compatibility, keep the same underlying trigger and conversation role.

### Story purpose
- reconverge the act
- show growing civic pressure
- aim the player toward Ashfall Watch
- reflect consequences of prior branch work

---

# MAJOR ASSAULT SITE

## Ashfall Watch

### Core rule
Keep this site intact as the major Act 1 fortress assault.

This is already original-facing and fits Aethrune well.

### Role
- route-control fortress
- regional command point
- late-mid Act military target
- support for the Ashen Brand's wider network

### Story function
Ashfall Watch should now read as:
- the Ashen Brand's fixed route-command post on the Emberway
- a place where local fear, supply, and military order are being turned into structure

### Gameplay
Preserve:
- side branches
- reconvergence
- prisoner / signal / yard logic
- post-sabotage effect if Cinderfall was cleared

---

# TOWN AFTERMATH

## Vigil / Recovery Beat

Keep the post-Ashfall town aftermath beat.

### New surface framing
This remains a vigil or communal recovery night in Iron Hollow.
It should:
- acknowledge the player's progress
- show civilian cost
- reveal or solidify the manor lead

This emotional reset is important and should not be cut.

---

# LATE ACT DESCENT

## Duskmere Manor (Was Tresendar Manor)

### Core role
Preserve this as:
- the late Act haunted/occupied descent site
- transition from frontier conflict into deeper buried-system horror
- location of the Cistern Eye subtext
- pre-finale descent into the act's strangest layer

### New surface framing
Duskmere Manor is:
- an old route-lord estate built over buried Accord works
- partially collapsed, partially occupied, and structurally wrong beneath the visible manor

### Why this works
It preserves the current gameplay role and supports the thematic escalation from:
- road conflict
to
- structural horror below civilization

### Important subtext
Keep the Cistern Eye functionally equivalent:
- strange knowledge
- route-depth hints
- no early hidden-villain reveal
- foreshadowing that the map is older than Varyn's system

---

# FINALE

## Emberhall Cellars

### Core rule
Keep this location and end-of-act role intact.

It is already original-facing and strong.

### Role
- final Act 1 dungeon
- Ashen Brand local command collapse
- Varyn confrontation
- Act 2 handoff site

### Aethrune framing
Emberhall is:
- a buried command archive / subcellar complex
- partially Accord-era foundation, partially recent Ashen Brand retrofit
- a place where route ledgers, fear, and command timing converge

### Varyn resolution
Preserve the implemented retcon logic:
- the player truly wins Act 1
- the Ashen Brand is genuinely broken locally
- Varyn's route-displacement allows continuation without invalidating the victory

---

# REQUIRED ACT 1 FLOW — DO NOT CHANGE

## Structural order to preserve

1. background prologue
2. shared opening
3. Greywake briefing
4. Emberway ambush
5. cleared-road optional branches
6. Iron Hollow hub
7. Blackglass Well and Red Mesa Hold in either order
8. optional Cinderfall Ruins
9. Iron Hollow war-room reconvergence
10. Ashfall Watch
11. Iron Hollow vigil
12. Duskmere Manor
13. Emberhall Cellars
14. Act 1 completion / Act 2 foreshadow

This route order is part of current gameplay expectations and should remain stable.

---

# MAP-SYSTEM COMPATIBILITY NOTES

## Overworld behavior to preserve
- unlocked route visibility
- backtrack history behavior
- side-branch cleanup after resolution
- hidden-route unlock behavior
- town hub return behavior
- gating on major sites

## Dungeon behavior to preserve
- branching room progression
- room-based map display
- previously visited room return support
- reconvergence after side rooms
- support scene insertion points
- clue and flag resolution points

## Tests this rewrite should not break
Preserve behavior around:
- Act 1 map-state initialization
- post-ambush route unlocks
- side-branch routing and cleanup
- hidden-route unlocks
- Ashfall sabotage impact
- branching room progression
- Act 1 ending-tier carryover
- Act 2 handoff

---

# SURFACE REWRITE PRIORITY ORDER

## Phase 1 — Safe player-facing relabel
Rewrite only:
- displayed location names
- menu labels
- town labels
- shrine labels
- public codex/world text
- descriptive narration

Do not yet rename:
- internal scene ids
- save-state keys
- quest ids
- map handler method names

## Phase 2 — Story wrapper rewrite
Rewrite:
- Greywake city framing
- Iron Hollow politics
- Lantern faith references
- Accord-era ruin mythology
- Emberway route-control framing

## Phase 3 — Optional deeper runtime cleanup
Only after the public rewrite is stable:
- rename internal scene ids if desired
- rename flags if desired
- update tests and save migration only if necessary

---

# OLD TO NEW ACT 1 QUICK MAP

| Internal structure role | Current public label | New public label |
| --- | --- | --- |
| major city | Neverwinter | Greywake |
| main road | High Road | Emberway |
| main hub | Phandalin | Iron Hollow |
| inn | Stonehill Inn | Ashlamp Inn |
| shrine | Shrine of Tymora | Lantern Shrine |
| orchard / local elder loop | Edermath Orchard | Orchard Wall |
| exchange / mining politics | Miner's Exchange | Delvers' Exchange |
| ruin branch A | Old Owl Well | Blackglass Well |
| ruin branch B | Wyvern Tor | Red Mesa Hold |
| hidden relay | Cinderfall Ruins | Cinderfall Ruins |
| fortress assault | Ashfall Watch | Ashfall Watch |
| late descent site | Tresendar Manor | Duskmere Manor |
| finale | Emberhall Cellars | Emberhall Cellars |

---

# SHORT IMPLEMENTATION SUMMARY

If the priority is **not breaking the current game**, then Act 1 should be rewritten like this:

- keep the current map structure
- keep the current room graph
- keep the current route unlock logic
- keep the current branch ordering
- keep the current internal IDs for now
- replace only player-facing setting labels and narrative wrapper text
- reinterpret the whole route through Greywake -> Emberway -> Iron Hollow -> Blackglass Well / Red Mesa Hold -> Cinderfall -> Ashfall -> Duskmere -> Emberhall

That gives you:
- the same gameplay
- the same progression
- the same code stability
- a much safer path toward a fully original setting

---

# END
