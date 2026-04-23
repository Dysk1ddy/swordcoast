# AETHRUNE — GAMEPLAY VARIABLES TUNING (V1)

## PURPOSE
This document turns the faction and relationship framework into concrete gameplay variables that can be implemented in code.

It is designed to fit the current structure of the project:
- companion approval
- route progression
- Act pressure tracking
- hidden flags
- branch and support logic

This is not full implementation code.
It is a design-facing variable reference for tuning.

---

# DESIGN GOALS

The variables should:

- preserve the current game's readable structure
- reinforce the themes of route control, information control, and system pressure
- avoid excessive stat bloat
- create meaningful but manageable branching
- support Act 1 and Act 2 immediately
- seed Act 3 and Secret Act 4 naturally

---

# VARIABLE LAYERS

The game should track four major layers of variables:

## 1. Companion Variables
How individual companions feel about the player and what they become.

## 2. Faction Variables
How major power groups perceive and respond to the player.

## 3. Regional Pressure Variables
How stable or unstable a region becomes over time.

## 4. Hidden System Variables
How much the player is being predicted, recorded, resisted, or destabilized by deeper structures.

---

# 1. COMPANION VARIABLES

## Core Approval Variable
Each companion should keep one primary signed integer:

- `companion_<id>_approval`

Recommended range:
- `-10` to `+10`

### Thresholds
| Score | State | Meaning |
| ---: | --- | --- |
| `8 to 10` | Bound | Maximum trust; unique support, unique interjections, possible Act 3 loyalty lock |
| `5 to 7` | Loyal | Strong support and personal quest resolution strength |
| `2 to 4` | Friendly | Moderate support, more open dialogue |
| `-1 to 1` | Neutral | Default state |
| `-2 to -4` | Strained | Reduced support, conflict scenes more likely |
| `-5 to -7` | Fractured | May refuse support or challenge the player directly |
| `-8 to -10` | Broken | Departure, betrayal risk, or permanent shutdown of companion arc |

### Design Rule
Approval should move in increments of:
- `+1 / -1` for most dialogue and scene choices
- `+2 / -2` for major moral or route decisions
- `+3 / -3` only for personal quest climax moments

Do not overuse large jumps.

---

## Companion Direction Variables
Each companion should also have one hidden evolution variable:

- `companion_<id>_direction`

This is not purely “good vs evil.”
It is the direction the companion is becoming because of the player.

Recommended values:
- `ordered`
- `merciful`
- `pragmatic`
- `ruthless`
- `curious`
- `guarded`
- `free`
- `dependent`

Not every companion uses every value.

### Example Use
- Kaelis: `decisive`, `paranoid`, `balanced`
- Rhogar: `reformer`, `enforcer`, `broken_oath`
- Tolan: `mentor`, `hardened`, `fatalist`
- Bryn: `loyal`, `opportunist`, `escaped_self`
- Elira: `hopeful`, `hardened`, `burdened`
- Nim: `disciplined`, `consumed`, `balanced`
- Irielle: `free`, `controlled`, `unstable`

This variable should be set or locked during personal quest climax scenes.

---

## Companion Presence / Utility Flags
Recommended boolean or compact flags:

- `companion_<id>_recruited`
- `companion_<id>_available`
- `companion_<id>_left_party`
- `companion_<id>_personal_quest_started`
- `companion_<id>_personal_quest_resolved`
- `companion_<id>_final_state`

These should stay simple and explicit.

---

# 2. FACTION VARIABLES

Use a signed reputation value for each major faction.

Recommended variables:

- `rep_iron_hollow_council`
- `rep_ashen_brand`
- `rep_quiet_choir`
- `rep_meridian_reclaimers`
- `rep_free_operators`

Recommended range:
- `-5` to `+5`

### Thresholds
| Score | State | Meaning |
| ---: | --- | --- |
| `+4 to +5` | Trusted | Better access, discounts, stronger intel, support scenes |
| `+2 to +3` | Favored | Moderate support, easier social checks |
| `-1 to +1` | Mixed | Default stance |
| `-2 to -3` | Distrusted | Worse rewards, resistance, fewer options |
| `-4 to -5` | Opposed | Active obstruction, ambushes, denial of access |

### Design Rule
Faction reputation should move more slowly than companion approval.

Typical changes:
- `+1 / -1` for a major quest outcome
- rarely more than `2` from one event

Factions should feel structural, not emotional.

---

## Faction Visibility Flags
Recommended hidden booleans:

- `ashen_brand_alerted`
- `quiet_choir_tracking_player`
- `reclaimers_consider_player_useful`
- `council_considers_player_reliable`
- `free_operators_open_to_trade`

These allow route-specific or scene-specific logic without overloading the rep score.

---

# 3. REGIONAL PRESSURE VARIABLES

These are the most important mid-scale world variables.

## Act 1 Variables
Keep or reinterpret the current structure:

- `town_fear`
- `ashen_strength`
- `survivors_saved`

Recommended ranges:
- `town_fear`: `0 to 5`
- `ashen_strength`: `0 to 5`
- `survivors_saved`: `0 to 5`

### Act 1 Tuning
#### `town_fear`
Tracks:
- civilian anxiety
- trust in leadership
- emotional collapse

Increase when:
- visible losses occur
- civilians die
- rumors spread unchecked

Decrease when:
- rescues succeed
- the player restores visible order
- key public victories occur

#### `ashen_strength`
Tracks:
- Ashen Brand operational integrity
- route enforcement strength
- ability to retaliate

Increase when:
- sabotage is missed
- side targets are ignored
- route-control nodes remain active

Decrease when:
- hidden relay sites are hit
- minibosses are defeated
- supply lines are exposed or broken

#### `survivors_saved`
Tracks:
- concrete life-preserving action
- rescued captives and witnesses
- later testimony quality

Increase when:
- people are rescued
- optional civilian saves happen
- side scenes are resolved compassionately and effectively

---

## Act 1 Resolution Thresholds
Recommended end-state logic:

### Clean Victory
- `town_fear <= 2`
- `ashen_strength <= 2`
- `survivors_saved >= 3`

### Costly Victory
Default middle result if clean and fractured are both false.

### Fractured Victory
If two or more are true:
- `town_fear >= 4`
- `ashen_strength >= 4`
- `survivors_saved <= 1`

This keeps the current feel while making the tuning more explicit.

---

## Act 2 Variables
Keep the current triad:

- `act2_town_stability`
- `act2_route_control`
- `act2_whisper_pressure`

Recommended range:
- each from `0 to 6`

### Act 2 Tuning
#### `act2_town_stability`
Tracks:
- civic cohesion
- civilian survivability
- whether Iron Hollow is still functioning as a town

Increase when:
- civilians are protected
- crisis response is prioritized
- the council survives with legitimacy

Decrease when:
- sabotage lands
- captives die
- faction conflict overwhelms town structure

#### `act2_route_control`
Tracks:
- expedition authority
- map ownership
- physical control of access routes

Increase when:
- surveys are secured
- routes are reclaimed
- rival control is broken
- key sites are taken in good order

Decrease when:
- rival parties hold territory
- delayed routes collapse
- the player yields leverage to other groups

#### `act2_whisper_pressure`
Tracks:
- signal contamination
- listening-horror spread
- how much deeper system wrongness escapes

Increase when:
- Choir actions succeed
- corrupted nodes are left intact
- dangerous truths are mishandled
- contaminated survivors spread instability

Decrease when:
- contaminated sites are contained
- signal lenses are disrupted
- player chooses costly containment over easier leverage

---

## Act 2 Pressure State Bands
| Value | State |
| ---: | --- |
| `0-1` | low |
| `2-3` | rising |
| `4-5` | severe |
| `6` | critical |

These bands should feed:
- hub descriptions
- NPC dialogue tone
- available public options
- Act 2 summary text
- Act 3 handoff profile

---

# 4. HIDDEN SYSTEM VARIABLES

These are long-term variables that shape later acts and special routes.

## Core Hidden Variables

### `player_predictability`
Recommended range:
- `0 to 6`

Tracks how easy the player has become to model.

Increase when:
- player consistently chooses the same strategic philosophy
- player optimizes hard in obvious patterns
- player solves problems through narrow, repeated methods

Decrease or remain low when:
- player acts inconsistently in meaningful ways
- mercy interrupts efficiency
- player preserves contradictory outcomes

### `system_alignment`
Recommended range:
- `-3` to `+3`

Tracks how much the player reinforces ordered structures.

High values mean:
- trusts systems
- favors disciplined control
- restores infrastructure even at moral cost

Low values mean:
- distrusts systems
- favors human judgment over structure
- breaks tools that would centralize control

### `unrecorded_choice_tokens`
Recommended range:
- `0 to 4`

Tracks meaningful choices the deeper system could not cleanly classify.

Gain tokens when:
- player makes a costly, contradictory, or compassionate choice that breaks predicted incentives
- player preserves lives when optimization says not to
- player maintains conflicting loyalties
- player uses restraint where domination would be easier

Spend or lose tokens when:
- player fully submits to predictable optimization
- player collapses uncertainty into pure control choices

### `counter_cadence_known`
Type:
- boolean

True if the party has learned how to resist system pressure through method, ritual, or understanding rather than raw force.

This should be seeded through:
- Irielle
- certain Choir routes
- specific Forge outcomes
- certain Pale Witness truths

### `map_integrity`
Recommended range:
- `0 to 5`

Tracks whether the world still has usable, living routes rather than fully captured ones.

Increase when:
- routes are saved
- civilians and couriers survive
- surveys remain honest
- infrastructure is stabilized without being fully monopolized

Decrease when:
- routes are militarized
- access narrows
- maps are falsified
- too much control centralizes

---

# APPROVAL AND REP CROSS-TALK

Variables should affect each other selectively.

## Recommended Cross-Talk Examples

### Companion ↔ Faction
- Helping the Council may increase Tessa trust and Rhogar approval
- Working with Free Operators may help Bryn but hurt Council rep
- studying dangerous systems may help Nim and hurt Elira
- containment-first choices may help Irielle and lower Reclaimer satisfaction

### Pressure ↔ Reputation
- low `town_stability` should make Council rep gains harder
- high `route_control` can improve Reclaimer and Council perception
- high `whisper_pressure` should make Quiet Choir scenes more aggressive and unstable

### Hidden Variables ↔ Dialogue Availability
- high `player_predictability` may unlock enemy taunts or trap routes
- high `unrecorded_choice_tokens` may unlock special trust scenes
- low `system_alignment` may open system-breaking solutions
- high `map_integrity` should influence Act 3 travel and Secret Act 4 access

---

# RECOMMENDED EVENT VALUE TUNING

## Small scene choice
- companion approval: `±1`
- faction rep: `0`
- pressure: `0` or `±1`

## Quest branch resolution
- companion approval: `±1` to `±2`
- faction rep: `±1`
- pressure: `±1`

## Major site outcome
- companion approval: `±2`
- faction rep: `±1` to `±2`
- pressure: `±1` to `±2`
- hidden variables: maybe `±1`

## Personal quest climax / act finale
- companion approval: `±3`
- faction rep: `±2`
- pressure: `±2`
- hidden variables: `±1` or boolean unlock

Do not move too many layers at once unless it is a true climax moment.

---

# FAILSTATE / CONSEQUENCE DESIGN

Variables should not mostly create hard failstates.
They should create:
- altered tone
- changed support
- different rewards
- more difficult routes
- altered epilogues
- stronger or weaker late-game options

### Good design
- “This choice weakened route control but saved trust.”

### Bad design
- “You picked one wrong option and lost half the game.”

---

# MINIMUM IMPLEMENTATION SET

If you want the cleanest implementation without too much complexity, use this minimum set:

## Companions
- approval
- recruited
- final state

## Factions
- one rep value per major faction

## Act 1
- town_fear
- ashen_strength
- survivors_saved

## Act 2
- act2_town_stability
- act2_route_control
- act2_whisper_pressure

## Hidden
- player_predictability
- system_alignment
- unrecorded_choice_tokens
- counter_cadence_known

This is enough to drive a strong narrative system without becoming unmanageable.

---

# EXPANDED IMPLEMENTATION SET

If you want deeper late-game payoff, add:

- `map_integrity`
- `quiet_choir_tracking_player`
- `council_considers_player_reliable`
- `reclaimers_consider_player_useful`
- companion direction variables
- personal quest resolution flags

This supports:
- richer Act 3 summaries
- more meaningful companion evolutions
- Secret Act 4 gating
- more dynamic travel and trust logic

---

# EXAMPLE PROFILE STATES

## Ordered Protector
- high Council rep
- high town stability
- high system alignment
- medium predictability
- lower unrecorded tokens

## Adaptive Survivor
- medium faction reps
- moderate route control
- lower system alignment
- low predictability
- higher unrecorded tokens

## Ruthless Controller
- high route control
- low town stability
- high predictability
- high system alignment
- low survivor count

## Compassionate Disruptor
- high companion loyalty
- lower predictability
- low to medium system alignment
- high unrecorded tokens
- moderate route control with stronger human outcomes

These profile patterns should feed summaries and late-game pathing.

---

# IMPLEMENTATION NOTES

## Save Simplicity
Prefer explicit integers and booleans.
Avoid nested structures unless needed.

## UI Simplicity
Do not show every variable to the player.
Public-facing variables should likely be:
- companion approval feel
- major Act pressure summaries
- maybe faction reputation at most

Keep hidden:
- predictability
- system alignment
- unrecorded tokens
- tracking flags

## Narrative Clarity
Every variable should answer a question:
- who trusts you?
- what is falling apart?
- what are you reinforcing?
- what are you resisting?
- how much of you can still surprise the system?

If a variable cannot answer one of those questions, it may not be needed.

---

# NEXT STEP

Possible follow-up documents:
- variable-to-quest trigger mapping
- companion approval event matrix
- faction reputation event matrix
- Act 3 handoff profile rules
- Secret Act 4 unlock logic tuned to these variables

---

# END
