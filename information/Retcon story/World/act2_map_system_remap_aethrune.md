# ACT 2 MAP SYSTEM REMAP — AETHRUNE COMPATIBILITY PASS

## Purpose

This document remaps the current Act 2 scaffold and playable local-map content into the Aethrune setting **without breaking the current route framework, hub logic, pressure tracking, local maps, or Act 3 handoff**.

The goal is:

- keep the current Act 2 route order
- keep the current expedition-hub structure
- keep current branching lead logic
- keep current pressure tracking
- keep the current playable local-map dungeons
- keep current midpoint and late-route dependencies
- keep current end-of-act handoff flags
- replace player-facing setting/lore labels with original Aethrune equivalents

This matches the same compatibility-first approach used for Act 1:
- preserve internal scaffolding first
- rewrite player-facing names and story wrapper text first
- postpone deep internal id refactors until later

---

# CORE IMPLEMENTATION RULE

## Keep Internal IDs Stable For Now

To avoid breaking progression, tests, saves, route gating, and Act 3 handoff:

- keep current internal scene ids
- keep current pressure variable names
- keep current quest ids unless intentionally rewritten later
- keep current route unlock logic intact
- keep current local-map handler structure intact
- keep current Act 2 completion/handoff logic intact

### This means:

For now, internal references such as these can remain:
- `story_act2_scaffold`
- `phandelver_claims_council_seen`
- `act2_town_stability`
- `act2_route_control`
- `act2_whisper_pressure`
- `stonehollow_dig`
- `broken_prospect`
- `south_adit`
- `wave_echo_outer_galleries`
- `black_lake_causeway`
- `forge_of_spells`

But the **player-facing runtime labels and world framing** should shift to Aethrune.

This is the safest rewrite path and preserves the live scaffold and local maps.

---

# ACT 2 REMAP PHILOSOPHY

The current Act 2 skeleton is strong and should stay intact.

Canonical existing Act 2 structure:

1. Act 1 aftermath in the frontier hub
2. claims council / political reconvergence
3. expedition sponsor choice
4. first early lead selection
5. optional medium side-dungeon after first cleared early lead
6. three early leads, any two of which can unlock the midpoint
7. midpoint convergence / sabotage night
8. delayed third early lead remains recoverable but degraded
9. two required late routes in either order
10. deep ruin approach
11. causeway / shrine / barracks priority zone
12. Forge finale
13. Act 3 handoff based on pressure and route outcomes

That structure should remain unchanged.

---

# WORLD REMAP — ACT 2 SURFACE LAYER

## Region

- Old public framing: Sword Mountains / Wave Echo frontier
- New framing: **The Vein of Glass**

This is the buried Accord region beneath and beyond Iron Hollow:
- excavation lines
- drowned annexes
- broken route engines
- old civic-mechanical infrastructure
- signal-contaminated ruins

## Main frontier hub

- Old: Phandalin
- New: **Iron Hollow**

Keep the same Act 1 carryover town hub identity in public text for continuity.

## Deeper ruin complex

- Old: Wave Echo Cave
- New: **The Resonant Vaults**

This should become the major buried Accord complex beneath the Vein of Glass.

## Old civilization framing

- Old: Phandelver Pact
- New: **Meridian Compact**

This is the old civic-engineering coalition or founding infrastructure compact that first built and governed the buried systems.

---

# ACT 2 PUBLIC RENAME MAP

| Current public location / concept | New public-facing Aethrune name | Keep internal id now? | Notes |
| --- | --- | --- | --- |
| Phandalin claims council | Iron Hollow claims council | Yes | main Act 2 opening political beat |
| Miner's Exchange | Delvers' Exchange | Yes | reuse Act 1 remap |
| Wave Echo Cave | Resonant Vaults | Yes | overall buried Act 2 megasite |
| Phandelver Pact | Meridian Compact | Yes | old buried system builders |
| Conyberry | Hushfen | Yes | early lead region |
| Agatha's Circuit | The Pale Circuit | Yes | ghost/ritual truth route |
| Neverwinter Wood Survey Camp | Greywake Survey Camp | Yes | early lead region |
| Stonehollow Dig | Stonehollow Dig | Yes | already original-facing enough |
| Glasswater Intake | Glasswater Intake | Yes | already original-facing enough |
| Broken Prospect | Broken Prospect | Yes | already original-facing enough |
| South Adit | South Adit | Yes | already original-facing enough |
| Wave Echo Outer Galleries | Resonant Vault Outer Galleries | Yes | late ruin approach |
| Black Lake Causeway | Blackglass Causeway | Yes | late priority zone |
| Forge of Spells | Meridian Forge | Yes | finale chamber/system |
| Quiet Choir | Quiet Choir | Yes | already original-facing enough |
| Sister Caldra Voss | Sister Caldra Voss | Yes | already original-facing enough |

---

# ACT 2 CORE PREMISE — AETHRUNE VERSION

Act 2 is no longer framed around reopening a famous fantasy mine.

Instead, it is framed around **who gets to name, reopen, and control the buried Meridian systems beneath Iron Hollow**.

Public conflict:
- a claims war over salvage, route authority, and infrastructure access

Private conflict:
- the Quiet Choir has learned that the Meridian Forge can function as a **listening lens** as well as a power or shaping site

Act 2 should feel layered:
1. local recovery and claim politics
2. expedition race and route-truth conflict
3. buried Accord ruin-crawl
4. only near the end, unmistakable deeper wrongness

---

# ACT 1 CARRYOVER INTO ACT 2

## Keep carryover structure intact

Preserve:
- Iron Hollow state carryover
- companion continuity
- Act 1 victory tier influence
- route sabotage memory
- civic trust/fear aftermath
- Varyn fallout without undercutting the Act 1 victory

### Surface rewrite
Act 1 established that the Ashen Brand were not random raiders.
Act 2 confirms they were filtering access to older Meridian routes beneath the Vein of Glass.

This should preserve the current story spine:
- Act 1 victory remains real
- the frontier is safer
- but the buried system war is only beginning

---

# ACT 2 OPENING

## Iron Hollow Claims Council (Was Phandalin Claims Council)

### Core rule
Keep this scene intact as the political reconvergence point that opens Act 2.

Preserve:
- town reconvergence role
- faction argument structure
- sponsor setup
- route pressure framing
- opening of expedition logic

### Surface rewrite
The claims council is now explicitly about:
- salvage rights
- buried-route authority
- civic ownership of reopened infrastructure
- who gets to define the future of Iron Hollow

### Recommended public framing
The Delvers' Exchange hosts the council:
- miners want access
- traders want stability
- civic leaders want control
- opportunists want leverage
- the Quiet Choir wants access without visibility

This preserves the current “public politics before ruin descent” function.

---

# SPONSOR CHOICE

## Keep sponsor structure intact

Preserve:
- the sponsor-choice beat
- the act-opening tone assignment
- expedition identity differences
- later midpoint implications

### Aethrune framing
Sponsors now represent three expedition philosophies:

#### 1. Speed-first sponsor
- reopen routes quickly
- seize access before rivals
- accepts instability for momentum

#### 2. Discipline-first sponsor
- secure each layer carefully
- prioritize logistics and control
- stronger in route authority framing

#### 3. Caution-first sponsor
- preserve lives and containment
- avoid waking deeper systems recklessly
- stronger on stability and witness handling

Do not change the underlying structure—only the public wrapper and rhetoric.

---

# EARLY LEAD STRUCTURE

## Core rule
Keep the current early-lead rule exactly intact:

- three early leads
- any two can unlock the midpoint
- the third remains recoverable later
- delaying the third lead causes a one-time permanent consequence
- the consequence should never repeatedly stack

This is one of Act 2's key structural strengths and should not be changed.

---

# EARLY LEAD A — Hushfen and the Pale Circuit
## (Was Conyberry and Agatha's Circuit)

### Core role
Preserve this as:
- warning / witness / sacred truth route
- ritual and grief-heavy lead
- public-truth vs controlled-truth branch
- old-law / old-memory route

### New surface framing
Hushfen is:
- a half-abandoned marsh hamlet and drowned shrine path
- known for old witness rites and dangerous memory pools

The Pale Circuit is:
- a ritual path built by Meridian Compact wardens
- built to regulate which truths could travel safely

### The Agatha equivalent
Do not frame this as a direct banshee replacement.
Instead, use a **Pale Witness**:
- a dead or half-bound custodian of forbidden route-memory
- a preserved witness tied to old compact-law and warning rites

### Why this works
It preserves the current branch role:
- truth, warning, grief, and the politics of who should carry dangerous knowledge

---

# EARLY LEAD B — Greywake Survey Camp
## (Was Neverwinter Wood Survey Camp)

### Core role
Preserve this as:
- map-truth route
- expedition and cartography pressure route
- route honesty vs leverage route
- practical overland systems lead

### New surface framing
Greywake Survey Camp is:
- a frontier engineering and survey outpost
- tasked with rebuilding the expedition map into the Vein of Glass
- compromised by fear, rival pressure, and bad records

### Story function
This lead teaches:
- route truth matters
- map control is political
- incomplete or falsified surveys can be as dangerous as monsters

### Why this works
It preserves the current “survey / map / route integrity” role while aligning tightly to Aethrune's systems-and-roads theme.

---

# EARLY LEAD C — Stonehollow Dig

### Core rule
Keep Stonehollow Dig intact.

It is already original-facing and well-suited to Aethrune.

### Core role
Preserve this as:
- excavation route
- buried-knowledge and rescue route
- Nim recruitment site
- first deeper proof that the buried system is larger than expected

### Aethrune framing
Stonehollow Dig is:
- an excavation breach into a Meridian subnetwork
- a labor and survey site where salvage, scholarship, and survival collide

### Nim's role
Keep Nim Ardentglass's entry role intact.
He remains:
- a scholar / mapper / incomplete-knowledge companion
- someone who helps the player interpret buried system truth
- a strong fit for Meridian-ruin framing

Do not alter his recruitment timing or route importance.

---

# OPTIONAL EARLY SIDE-DUNGEON

## Glasswater Intake

### Core rule
Keep this site intact in structure and timing:
- unlock after the first cleared early lead
- strongest before the second lead
- still meaningful before midpoint
- degraded if delayed until after sabotage night

### Why it matters
This dungeon already perfectly fits Aethrune:
- water control
- courier traffic
- claims fraud
- the conversion of practical systems into listening infrastructure

### Aethrune framing
Glasswater Intake is:
- a Meridian hydraulic annex below the lower slopes near Iron Hollow
- once used to regulate pressure, rationing, and clean flow timing
- now hijacked by the Quiet Choir and hostile operators

### Preserve experience goals
This remains the physical proof point that Act 2's battlefield is:
- flow control
- supply truth
- infrastructure ownership
- routework pressure and contested infrastructure

### Preserve map expectations
Keep its structure as a medium dungeon:
- 10 to 12 rooms
- practical industrial layout
- branch fork through stabilizer path vs intelligence path
- moral / logistics choice at the end

Do not shrink it into a throwaway stop.

---

# EARLY ACT HUB LOOP

## Keep the expedition hub behavior intact

Preserve:
- lead selection loop
- camp and rest loop
- route panel behavior
- pressure displays
- sponsor context
- companion fallout visibility
- later midpoint trigger after two early leads

### Public text direction
Act 2 hub UI and summaries should emphasize:
- expedition status
- civic pressure
- control of access
- survey truth
- buried-system contamination

---

# MIDPOINT RULE

## Sabotage Night

### Core rule
Keep Sabotage Night intact as the midpoint convergence.

Preserve:
- trigger after any two early leads
- the delayed third lead's consequence applying exactly once
- player choosing what to protect first
- accepting a matching loss elsewhere
- pattern-profile seeding for later acts

### Aethrune framing
Sabotage Night is:
- a coordinated pressure event across Iron Hollow
- sabotage of civic trust, route order, and containment infrastructure
- the moment Act 2 stops being “expedition prep” and becomes open system war

### Recommended public priorities
Keep existing structure but reframe as:
- protect the claims hall / route records
- protect civilians and shrine lanes
- hunt infiltrators and route-rewriters

These choices should continue to feed:
- stability
- route control
- whisper pressure
- later prediction-profile inputs

---

# DELAYED EARLY LEAD RULE

## Do not change this structure

If one early lead is delayed past Sabotage Night:
- it remains playable later
- its damage is already done
- the player can recover some value
- the player cannot fully undo the consequence

This is crucial to Act 2's identity and should remain intact.

---

# LATE ROUTE STRUCTURE

## Core rule
Keep the current late-route structure intact:
- `Broken Prospect` and `South Adit` both required
- can be taken in either order
- the order materially changes tone and consequences
- first choice improves one front while worsening the other

This should not be flattened into a fixed sequence.

---

# LATE ROUTE A — Broken Prospect

### Core role
Preserve this as:
- route race site
- claim and salvage pressure site
- expedition ownership conflict
- public-facing “who controls the threshold?” route

### Aethrune framing
Broken Prospect is:
- a failed Meridian access breach
- a partially collapsed approach camp built by modern claimants
- the place where route ownership turns from politics into possession

### Outcome emphasis
Broken Prospect first should still mean:
- better expedition posture and route leverage
- but human/prisoner cost elsewhere if South Adit waits

---

# LATE ROUTE B — South Adit

### Core role
Preserve this as:
- captive / rescue / anti-Choir route
- Irielle recruitment site
- deeper contamination warning site
- practical proof of how the Quiet Choir processes people and signal discipline

### Aethrune framing
South Adit is:
- a lower Meridian work-cut repurposed into a holding and routing site
- a place where living people are being fed into a larger pattern of control

### Irielle's role
Keep Irielle Ashwake's recruitment role intact.
She remains:
- someone who understands the Choir's listening practices
- someone who knows the method, not the final hidden architect
- a key bridge toward counter-cadence and later anti-system resistance

### Outcome emphasis
South Adit first should still mean:
- more captives live
- but rival route posture hardens elsewhere

---

# DEEP APPROACH

## Resonant Vault Outer Galleries
### (Was Wave Echo Outer Galleries)

### Core rule
Keep this playable local-map site intact.

### Role
Preserve this as:
- the first true deep ruin threshold
- large-scale buried infrastructure reveal
- proof that the expedition has crossed from frontier salvage into system-depth territory

### Aethrune framing
The Outer Galleries are:
- collapsed Meridian approach halls
- survey catwalks
- old transit galleries
- active resonance corridors that still answer movement and sound

### Important tone shift
This is where the act begins to feel unmistakably stranger.
But it should still stop short of fully explicit cosmic explanation.

---

# PRIORITY ZONE

## Blackglass Causeway
### (Was Black Lake Causeway)

### Core rule
Keep this site intact as the pre-finale priority zone.

Preserve:
- shrine / barracks / causeway decision structure
- multi-priority conflict
- route-state consequences before the Forge

### Aethrune framing
Blackglass Causeway is:
- a dark water crossing through submerged Meridian infrastructure
- part shrine remnant
- part military barracks
- part transit spine

### Why this works
It preserves the current excellent function:
- a layered decision-space about what kind of victory reaches the finale

### Public option framing
Keep the choice families structurally similar:
- cleaner / sacred / restraint-first
- militarized / barracks / force-first
- route-securement / crossing-first

---

# FINALE

## Meridian Forge
### (Was Forge of Spells)

### Core rule
Keep the finale structure intact.

Preserve:
- Caldra as the visible Act 2 final villain
- the Forge-lens framing
- Act 3 handoff flags
- the possibility of understanding, blinding, or carrying signal-state consequences out

### Aethrune framing
The Meridian Forge is:
- an Accord-era shaping and resonance engine
- a civic-technical instrument for shaping, amplifying, and transmitting resonance
- capable of:
  - amplification
  - alignment
  - transmission
  - and, in corrupted use, listening

### Caldra Voss
Keep Caldra intact as the surface antagonist of Act 2.
She remains:
- a Quiet Choir agent
- convinced the Forge clarifies truth
- unaware of the deeper hidden intelligence as a fully named being

### Safe text direction
Act 2 visible text may speak of:
- the signal
- the answer
- the account
- the lens
- the world being counted

Act 2 visible text must not prematurely reveal the hidden Act 3 villain.

---

# ACT 2 PRESSURE TRACKING

## Keep current pressure variables intact

Preserve:
- `Town Stability`
- `Route Control`
- `Whisper Pressure`

These are structurally important to Act 2 and already fit Aethrune well.

### Aethrune interpretation

#### Town Stability
How intact Iron Hollow remains as a living civic community.

#### Route Control
How much of the expedition map and buried access network your side truly owns.

#### Whisper Pressure
How much contaminated signal, listening-horror, and buried-system wrongness is escaping containment.

Do not rename the variables internally yet unless you want to update all connected logic later.

---

# ACT 2 COMPANION INTEGRATION

## Keep current companion entry points intact

Preserve:
- Nim through Stonehollow Dig
- Irielle through South Adit
- existing trust and side-arc logic
- companion fallout visibility in the expedition hub
- Act 3 setup relevance

### Thematic alignment in Aethrune
These companions already fit naturally:

#### Nim
- unfinished map
- incomplete knowledge
- buried-system scholarship
- useful precisely because he does not over-complete the truth

#### Irielle
- counter-cadence
- survival against the Choir's listening doctrine
- knows the method without naming the hidden architect

---

# REQUIRED ACT 2 FLOW — DO NOT CHANGE

## Structural order to preserve

1. Act 1 aftermath in Iron Hollow
2. Iron Hollow claims council
3. sponsor choice
4. first early lead selection
5. optional Glasswater Intake after the first early lead
6. early lead trio:
   - Hushfen / Pale Circuit
   - Greywake Survey Camp
   - Stonehollow Dig
7. once any two early leads are cleared, Sabotage Night becomes available
8. delayed third lead remains recoverable but degraded
9. late route pair:
   - Broken Prospect
   - South Adit
10. Resonant Vault Outer Galleries
11. Blackglass Causeway
12. Meridian Forge
13. Act 2 completion summary and Act 3 handoff

This is the route spine that should remain stable.

---

# MAP-SYSTEM COMPATIBILITY NOTES

## Overworld / hub behavior to preserve
- expedition-hub lead selection
- pressure panel updates
- sponsor state visibility
- delayed-lead consequence behavior
- camp / rest / fallout visibility
- late-route unlock timing
- Act 2 completion summary behavior

## Local-map dungeon behavior to preserve
- playable maps already called out in current project status:
  - Stonehollow Dig
  - Broken Prospect
  - South Adit
  - Outer Galleries
  - Blackglass Causeway
  - Meridian Forge
- room-based exploration and reconvergence
- route-order consequences
- clue and flag insertion points
- Act 3 handoff data recording

## Flags and tests this rewrite should not break
Preserve behavior around:
- `act2_started`
- `act2_town_stability`
- `act2_route_control`
- `act2_whisper_pressure`
- sponsor choice
- delayed early lead consequence
- Nim recruitment
- Sabotage Night priority
- Broken Prospect / South Adit order consequences
- Irielle recruitment
- Forge-lens outcomes
- Act 2 epilogue flags
- Act 3 handoff flags

---

# SURFACE REWRITE PRIORITY ORDER

## Phase 1 — Safe player-facing relabel
Rewrite only:
- displayed location names
- expedition map labels
- council and hub labels
- ruin labels
- public codex text
- player-facing summaries
- descriptive narration

Do not yet rewrite:
- internal scene ids
- save-state keys
- pressure variable names
- map handler method names
- Act 3 handoff flag names

## Phase 2 — Story wrapper rewrite
Rewrite:
- claims-war framing into salvage-rights / buried-route authority framing
- Wave Echo language into Resonant Vaults language
- old Pact language into Meridian Compact language
- public ruin history and sponsor rhetoric
- all settlement-facing lore references

## Phase 3 — Optional deeper runtime cleanup
Only after the public rewrite is stable:
- rename internal location ids if desired
- rename flags if desired
- update tests and save migration only if needed

---

# OLD TO NEW ACT 2 QUICK MAP

| Internal structure role | Current public label | New public label |
| --- | --- | --- |
| main Act 2 hub | Phandalin | Iron Hollow |
| claims council location | Miner's Exchange | Delvers' Exchange |
| early lead A region | Conyberry | Hushfen |
| early lead A ritual route | Agatha's Circuit | The Pale Circuit |
| early lead B | Neverwinter Wood Survey Camp | Greywake Survey Camp |
| early lead C | Stonehollow Dig | Stonehollow Dig |
| optional side-dungeon | Glasswater Intake | Glasswater Intake |
| late route A | Broken Prospect | Broken Prospect |
| late route B | South Adit | South Adit |
| deep ruin complex | Wave Echo Cave | Resonant Vaults |
| late deep approach | Wave Echo Outer Galleries | Resonant Vault Outer Galleries |
| pre-finale zone | Black Lake Causeway | Blackglass Causeway |
| finale | Forge of Spells | Meridian Forge |
| old buried civilization | Phandelver Pact | Meridian Compact |

---

# SHORT IMPLEMENTATION SUMMARY

If the priority is **not breaking the current game**, then Act 2 should be rewritten like this:

- keep the current scaffold and route framework
- keep the current expedition-hub logic
- keep the current pressure tracking
- keep the current local-map dungeons
- keep the current midpoint and late-route dependencies
- keep the current Act 3 handoff flags
- replace only player-facing labels and narrative wrapper text
- reinterpret the act through:
  Iron Hollow -> claims war over buried Meridian systems -> Hushfen / Survey Camp / Stonehollow -> Glasswater -> Sabotage Night -> Broken Prospect / South Adit -> Resonant Vaults -> Blackglass Causeway -> Meridian Forge

That gives you:
- the same gameplay structure
- the same progression logic
- the same route consequences
- the same companion timing
- the same Act 3 setup
- a much safer path toward a fully original setting

---

# END
