# AETHRUNE — QUEST TO VARIABLE MATRIX (V1)

## PURPOSE

This document maps major quests, branch resolutions, and key scenes to gameplay variable changes.

It is designed to work with the variable framework in:
- companion approval
- faction reputation
- Act 1 pressure variables
- Act 2 pressure variables
- hidden system variables

This is a tuning sheet, not implementation code.

---

# VARIABLE LEGEND

## Companion Approval
- `KAE` = Kaelis
- `RHO` = Rhogar
- `TOL` = Tolan
- `BRY` = Bryn
- `ELI` = Elira
- `NIM` = Nim
- `IRI` = Irielle

## Faction Reputation
- `COUNCIL` = Iron Hollow Council
- `BRAND` = Ashen Brand
- `CHOIR` = Quiet Choir
- `RECLAIM` = Meridian Reclaimers
- `FREE` = Free Operators

## Act 1 Pressure
- `FEAR` = town_fear
- `ASH` = ashen_strength
- `SAVE` = survivors_saved

## Act 2 Pressure
- `STAB` = act2_town_stability
- `ROUTE` = act2_route_control
- `WHISPER` = act2_whisper_pressure

## Hidden Variables
- `PREDICT` = player_predictability
- `ALIGN` = system_alignment
- `TOKENS` = unrecorded_choice_tokens
- `MAP` = map_integrity

---

# ACT 1 — CORE OPENING

## Background Prologue — Resolve cleanly
### Outcome
Player succeeds without collateral, secures clue, stabilizes opening scene.

### Variable Changes
- `COUNCIL +1`
- `FEAR -1`
- `SAVE +1`

### Companion Notes
No major companion adjustments unless one is present.

---

## Background Prologue — Brutal / reckless resolution
### Outcome
Player still succeeds, but causes fear or obvious damage.

### Variable Changes
- `COUNCIL -1`
- `FEAR +1`
- `ALIGN +1`

### Notes
This reflects “ordered through force” or “results first” logic.

---

# ACT 1 — GREYWAKE TO EMBERWAY

## Greywake Briefing — disciplined, transparent approach
### Outcome
Player accepts structured assignment, asks clear questions, builds trust.

### Variable Changes
- `COUNCIL +1`
- `ALIGN +1`
- `RHO +1`

---

## Greywake Briefing — skeptical / independent approach
### Outcome
Player questions authority, pushes for flexibility.

### Variable Changes
- `FREE +1`
- `ALIGN -1`
- `BRY +1`
- `RHO -1`

---

## Emberway Ambush — protect civilians / companions first
### Outcome
Player prioritizes rescue and stabilization.

### Variable Changes
- `SAVE +1`
- `FEAR -1`
- `KAE +1`
- `TOL +1`
- `ELI +1`

---

## Emberway Ambush — hard pursuit / efficiency first
### Outcome
Player ends threat decisively but with less care for the vulnerable.

### Variable Changes
- `ASH -1`
- `ALIGN +1`
- `RHO +1`
- `ELI -1`

---

# ACT 1 — CLEARED ROAD SIDE BRANCHES

## Liar's Circle — solve carefully, seek truth
### Outcome
Player treats the site as a truth-test and proceeds cautiously.

### Variable Changes
- `KAE +1`
- `NIM +1` if present
- `PREDICT -1`
- `TOKENS +1`

---

## Liar's Circle — force through / ignore nuance
### Outcome
Player treats the puzzle as obstacle only.

### Variable Changes
- `ALIGN +1`
- `PREDICT +1`
- `BRY -1`

---

## False Checkpoint — expose fraud publicly
### Outcome
Player breaks fake authority and restores confidence in the route.

### Variable Changes
- `COUNCIL +1`
- `FREE +1`
- `FEAR -1`
- `ASH -1`

### Companion Notes
- `RHO +1`
- `BRY +1`

---

## False Checkpoint — exploit or bluff through quietly
### Outcome
Player benefits, but the fraud structure survives.

### Variable Changes
- `FREE +1`
- `ASH +1`
- `PREDICT +1`

### Companion Notes
- `BRY +1`
- `RHO -1`

---

# ACT 1 — IRON HOLLOW HUB QUESTS

## Keep the Shelves Full / supply stabilization
### Outcome
Player secures practical goods for the town.

### Variable Changes
- `COUNCIL +1`
- `STAB` not used yet
- `FEAR -1`
- `SAVE +1`

### Companion Notes
- `TOL +1`
- `ELI +1`

---

## Songs for the Missing / public mourning support
### Outcome
Player helps civilians process grief and preserve names.

### Variable Changes
- `COUNCIL +1`
- `FEAR -1`
- `TOKENS +1`

### Companion Notes
- `ELI +1`
- `KAE +1`

---

## Quiet Table, Sharp Knives / rumor-control or underworld management
### Outcome A — defuse quietly
- `FREE +1`
- `FEAR -1`
- `BRY +1`

### Outcome B — crack down visibly
- `COUNCIL +1`
- `ALIGN +1`
- `BRY -1`
- `RHO +1`

---

# ACT 1 — OLD RISE BRANCH / BLACKGLASS WELL

## Blackglass Well — rescue-focused resolution
### Outcome
Player prioritizes survivors and contained recovery.

### Variable Changes
- `SAVE +1`
- `FEAR -1`
- `ASH -1`
- `TOKENS +1`

### Companion Notes
- `ELI +1`
- `TOL +1`
- `BRY +1`

---

## Blackglass Well — purge the site completely
### Outcome
Player destroys the threat but loses nuance and survivors.

### Variable Changes
- `ASH -2`
- `SAVE -1`
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `RHO +1`
- `ELI -1`

---

## Vaelith Marr — interrogate or extract truth
### Outcome
Player seeks knowledge instead of only elimination.

### Variable Changes
- `TOKENS +1`
- `PREDICT -1`
- `MAP +1`

### Companion Notes
- `KAE +1`
- `NIM +1` if present
- `ELI +1` if mercy involved

---

## Vaelith Marr — execute and destroy all evidence
### Outcome
Player chooses certainty over uncertainty.

### Variable Changes
- `ALIGN +1`
- `PREDICT +1`
- `ASH -1`

### Companion Notes
- `RHO +1`
- `NIM -1`
- `ELI -1` if harsh

---

# ACT 1 — RED MESA HOLD BRANCH

## Red Mesa Hold — break raider leadership cleanly
### Outcome
Player destroys enemy cohesion.

### Variable Changes
- `ASH -2`
- `COUNCIL +1`
- `FEAR -1`

### Companion Notes
- `TOL +1`
- `RHO +1`

---

## Red Mesa Hold — negotiate fracture / divide the hold
### Outcome
Player weakens enemy structure through leverage rather than total slaughter.

### Variable Changes
- `ASH -1`
- `FREE +1`
- `TOKENS +1`
- `PREDICT -1`

### Companion Notes
- `BRY +1`
- `KAE +1`
- `RHO -1`

---

# ACT 1 — OPTIONAL HIDDEN STRIKE

## Cinderfall Ruins — relay sabotage complete
### Outcome
Player successfully destroys a route-control node.

### Variable Changes
- `ASH -2`
- `MAP +1`
- `COUNCIL +1`

### Companion Notes
- `KAE +1`
- `TOL +1`

---

## Cinderfall Ruins — intel extraction before sabotage
### Outcome
Player studies the system before breaking it.

### Variable Changes
- `ASH -1`
- `MAP +1`
- `TOKENS +1`
- `PREDICT -1`

### Companion Notes
- `NIM +1` if present
- `KAE +1`
- `RHO -1` if delay feels risky

---

# ACT 1 — RECONVERGENCE

## War-room participation — transparent civic strategy
### Outcome
Player shares what they know and commits to open defense.

### Variable Changes
- `COUNCIL +1`
- `FEAR -1`
- `ALIGN +1`

### Companion Notes
- `RHO +1`
- `TOL +1`
- `ELI +1`

---

## War-room participation — hold back information for leverage
### Outcome
Player keeps knowledge compartmentalized.

### Variable Changes
- `FREE +1`
- `PREDICT +1`
- `TOKENS +1`

### Companion Notes
- `BRY +1`
- `RHO -1`
- `NIM +1` if information is held for analysis, not profit

---

# ACT 1 — ASHFALL WATCH

## Ashfall Watch — prisoner-first route
### Outcome
Player prioritizes captives and living outcomes.

### Variable Changes
- `SAVE +1`
- `FEAR -1`
- `ASH -1`

### Companion Notes
- `ELI +1`
- `TOL +1`
- `RHO +1`

---

## Ashfall Watch — signal/control-first route
### Outcome
Player prioritizes collapse of enemy command systems.

### Variable Changes
- `ASH -2`
- `ALIGN +1`
- `MAP +1`

### Companion Notes
- `RHO +1`
- `KAE +1`
- `ELI -1` if captives are lost

---

# ACT 1 — LATE DESCENT

## Duskmere Manor — investigate deeply
### Outcome
Player pursues system truth below the surface.

### Variable Changes
- `MAP +1`
- `PREDICT -1`
- `TOKENS +1`

### Companion Notes
- `NIM +1`
- `KAE +1`
- `ELI -1` if recklessness is perceived

---

## Duskmere Manor — move fast, suppress the anomaly
### Outcome
Player limits exposure and prioritizes tactical control.

### Variable Changes
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `RHO +1`
- `NIM -1`

---

## Cistern Eye — study / contain
### Outcome
Player learns from the anomaly without fully yielding to it.

### Variable Changes
- `MAP +1`
- `TOKENS +1`
- `PREDICT -1`

### Companion Notes
- `NIM +1`
- `IRI +1` if present
- `ELI -1` if the act feels too dangerous

---

## Cistern Eye — destroy immediately
### Outcome
Player rejects dangerous knowledge.

### Variable Changes
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `RHO +1`
- `NIM -1`

---

# ACT 1 — FINALE

## Emberhall / Varyn — victory with mercy toward witnesses and survivors
### Outcome
Player wins while preserving as much human structure as possible.

### Variable Changes
- `COUNCIL +2`
- `FEAR -1`
- `SAVE +1`
- `TOKENS +1`

### Companion Notes
- `ELI +2`
- `TOL +1`
- `KAE +1`

---

## Emberhall / Varyn — ruthless cleanup
### Outcome
Player wins decisively, minimizing future resistance but at human cost.

### Variable Changes
- `ASH -2`
- `ALIGN +1`
- `PREDICT +1`
- `SAVE -1`

### Companion Notes
- `RHO +1`
- `ELI -2`
- `BRY -1`

---

# ACT 2 — CLAIMS COUNCIL OPENING

## Sponsor with order / infrastructure-first faction
### Outcome
Player values control and discipline.

### Variable Changes
- `RECLAIM +1`
- `COUNCIL +1`
- `ALIGN +1`

### Companion Notes
- `RHO +1`
- `NIM +1`

---

## Sponsor with people / caution-first faction
### Outcome
Player values containment and survival.

### Variable Changes
- `COUNCIL +1`
- `STAB +1`
- `WHISPER -1`

### Companion Notes
- `ELI +1`
- `IRI +1`

---

## Sponsor with speed / leverage-first faction
### Outcome
Player values tempo and access.

### Variable Changes
- `FREE +1`
- `ROUTE +1`
- `PREDICT +1`

### Companion Notes
- `BRY +1`
- `KAE +1`
- `IRI -1`

---

# ACT 2 — EARLY LEADS

## Hushfen / Pale Circuit — public warning path
### Outcome
Player shares truth broadly despite fear.

### Variable Changes
- `STAB +1`
- `WHISPER +1`
- `TOKENS +1`

### Companion Notes
- `ELI +1`
- `IRI -1`
- `NIM +1`

---

## Hushfen / Pale Circuit — controlled truth path
### Outcome
Player restricts dangerous knowledge to a few.

### Variable Changes
- `WHISPER -1`
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `IRI +1`
- `ELI -1`
- `NIM +1`

---

## Greywake Survey Camp — honest map recovery
### Outcome
Player protects route truth over leverage.

### Variable Changes
- `ROUTE +1`
- `MAP +1`
- `TOKENS +1`

### Companion Notes
- `NIM +1`
- `KAE +1`

---

## Greywake Survey Camp — exploit the map strategically
### Outcome
Player secures advantage but reduces public truth.

### Variable Changes
- `ROUTE +1`
- `PREDICT +1`
- `ALIGN +1`

### Companion Notes
- `BRY +1`
- `NIM -1`

---

## Stonehollow Dig — rescue and recovery focus
### Outcome
Player saves scholars and secures usable truth.

### Variable Changes
- `STAB +1`
- `ROUTE +1`
- `MAP +1`

### Companion Notes
- `NIM +2`
- `ELI +1`

---

## Stonehollow Dig — research-first / costly knowledge focus
### Outcome
Player prioritizes understanding over safety.

### Variable Changes
- `MAP +1`
- `WHISPER +1`
- `PREDICT +1`

### Companion Notes
- `NIM +1`
- `ELI -1`
- `IRI -1`

---

# ACT 2 — OPTIONAL EARLY DUNGEON

## Glasswater Intake — stabilize the system
### Outcome
Player restores function and prevents contamination spread.

### Variable Changes
- `STAB +1`
- `WHISPER -1`
- `ROUTE +1`

### Companion Notes
- `ELI +1`
- `IRI +1`
- `NIM +1`

---

## Glasswater Intake — seize it for leverage
### Outcome
Player gains control but leaves deeper contamination risks.

### Variable Changes
- `ROUTE +1`
- `RECLAIM +1`
- `WHISPER +1`
- `PREDICT +1`

### Companion Notes
- `NIM +1`
- `IRI -1`
- `ELI -1`

---

# ACT 2 — MIDPOINT

## Sabotage Night — protect civilians first
### Outcome
Player chooses immediate human survival.

### Variable Changes
- `STAB +2`
- `ROUTE -1`
- `TOKENS +1`

### Companion Notes
- `ELI +1`
- `IRI +1`
- `RHO +1`

---

## Sabotage Night — protect route records / infrastructure first
### Outcome
Player protects structure over immediate human loss.

### Variable Changes
- `ROUTE +2`
- `STAB -1`
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `RHO +1`
- `NIM +1`
- `ELI -1`

---

## Sabotage Night — hunt infiltrators first
### Outcome
Player focuses on striking the hostile pattern itself.

### Variable Changes
- `WHISPER -1`
- `ROUTE +1`
- `TOKENS +1`
- `PREDICT -1`

### Companion Notes
- `KAE +1`
- `IRI +1`
- `ELI` unchanged

---

# ACT 2 — DELAY CONSEQUENCE

## Delay one early lead past midpoint
### Outcome
The site remains playable, but damage has already been done.

### Variable Changes
- `STAB -1` or `ROUTE -1` depending on the delayed site
- `WHISPER +1` if contamination spread is involved

### Design Rule
This is not a player choice reward.
It is a structural consequence.

---

# ACT 2 — LATE ROUTES

## Broken Prospect first
### Outcome
Player secures expedition leverage and threshold ownership.

### Variable Changes
- `ROUTE +2`
- `RECLAIM +1`
- `STAB -1`

### Companion Notes
- `NIM +1`
- `IRI -1`

---

## South Adit first
### Outcome
Player prioritizes captives and human containment.

### Variable Changes
- `STAB +1`
- `WHISPER -1`
- `TOKENS +1`

### Companion Notes
- `IRI +2`
- `ELI +1`
- `NIM` unchanged or `-1` if he views it as strategic delay

---

## South Adit — free captives aggressively
### Outcome
Player disrupts the Choir's holding structure.

### Variable Changes
- `STAB +1`
- `WHISPER -1`
- `CHOIR -1` in hostility terms if used narratively
- `TOKENS +1`

### Companion Notes
- `IRI +1`
- `ELI +1`

---

## South Adit — mine for information first
### Outcome
Player preserves knowledge but risks people.

### Variable Changes
- `MAP +1`
- `PREDICT +1`
- `WHISPER +1`

### Companion Notes
- `NIM +1`
- `IRI -2`
- `ELI -1`

---

# ACT 2 — DEEP APPROACH

## Resonant Vault Outer Galleries — disciplined advance
### Outcome
Player secures forward movement carefully.

### Variable Changes
- `ROUTE +1`
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `RHO +1`
- `NIM +1`

---

## Resonant Vault Outer Galleries — exploratory advance
### Outcome
Player follows strange signals and unstable truths.

### Variable Changes
- `MAP +1`
- `TOKENS +1`
- `PREDICT -1`
- `WHISPER +1`

### Companion Notes
- `NIM +1`
- `IRI +1`
- `RHO -1`

---

# ACT 2 — PRE-FINALE

## Blackglass Causeway — sacred/restraint route
### Outcome
Player advances with care, containment, and witness preservation.

### Variable Changes
- `WHISPER -1`
- `STAB +1`
- `TOKENS +1`

### Companion Notes
- `ELI +1`
- `IRI +1`

---

## Blackglass Causeway — militarized route
### Outcome
Player clears the path through force.

### Variable Changes
- `ROUTE +1`
- `ALIGN +1`
- `PREDICT +1`

### Companion Notes
- `RHO +1`
- `ELI -1`

---

## Blackglass Causeway — crossing-first tactical route
### Outcome
Player secures movement priority.

### Variable Changes
- `ROUTE +2`
- `MAP +1`

### Companion Notes
- `KAE +1`
- `NIM +1`
- `IRI -1` if human cost rises

---

# ACT 2 — FINALE

## Meridian Forge — blind / disrupt the lens
### Outcome
Player rejects system domination through listening.

### Variable Changes
- `WHISPER -2`
- `TOKENS +1`
- `ALIGN -1`

### Companion Notes
- `IRI +2`
- `ELI +1`
- `NIM -1`

---

## Meridian Forge — understand the lens without serving it
### Outcome
Player gains dangerous knowledge while resisting full submission.

### Variable Changes
- `MAP +1`
- `counter_cadence_known = true` if supported by earlier setup
- `TOKENS +1`
- `PREDICT -1`

### Companion Notes
- `NIM +2`
- `IRI +1`
- `RHO -1`

---

## Meridian Forge — seize the lens for structured control
### Outcome
Player uses the system as a tool.

### Variable Changes
- `ALIGN +2`
- `PREDICT +1`
- `ROUTE +1`
- `WHISPER +1`

### Companion Notes
- `RHO +1`
- `NIM +1`
- `IRI -2`
- `ELI -1`

---

# PERSONAL QUEST MATRIX — COMPANIONS

## Kaelis — route truth exposed
### Mercy / expose path
- `KAE +2`
- `TOKENS +1`
- `PREDICT -1`

### Kill path
- `KAE +1`
- set direction toward `decisive` or `paranoid`
- `ALIGN +1`

---

## Rhogar — oath conflict
### Reform path
- `RHO +2`
- `TOKENS +1`
- `ALIGN` unchanged or `-1`

### Enforce order path
- `RHO +1`
- `ALIGN +1`
- set direction toward `enforcer`

---

## Bryn — ledger route
### Burn it
- `BRY +2`
- `TOKENS +1`
- `FREE +1`

### Sell it
- `BRY +1`
- `FREE +1`
- `PREDICT +1`

### Expose it
- `BRY +1`
- `COUNCIL +1`
- `FEAR +1` or `STAB -1` if truth destabilizes the public

---

## Elira — faith under pressure
### Mercy path
- `ELI +2`
- `TOKENS +1`

### Safety-first execution path
- `ELI -2`
- `ALIGN +1`

---

## Nim — living map
### Study path
- `NIM +2`
- `MAP +1`
- `WHISPER +1`
- `PREDICT +1`

### Destroy path
- `NIM -2`
- `WHISPER -1`
- `ALIGN +1`

### Balanced path
- `NIM +1`
- `MAP +1`
- `TOKENS +1`
- `PREDICT -1`

---

## Irielle — quiet voice
### Sever path
- `IRI +2`
- `WHISPER -1`
- `counter_cadence_known = true` if supported

### Embrace path
- `IRI -1` or `+1` depending on framing
- `WHISPER +1`
- `ALIGN +1` or special corruption flag

### Balance path
- `IRI +1`
- `TOKENS +1`
- `PREDICT -1`

---

# PROFILE OUTPUT NOTES

At the end of each act, the game should summarize variable trends rather than raw numbers.

## Act 1 summary examples
- “Iron Hollow steadied under visible leadership.”
- “The Ashen Brand was broken, but the road still remembers blood.”
- “Too many were lost for victory to feel clean.”

## Act 2 summary examples
- “The expedition won access, but not trust.”
- “Containment held, though the truth narrowed.”
- “Too much of the deep signal escaped into the living town.”

---

# TUNING NOTES

## Do not reward everything
A choice that increases one variable should often cost another.

## Preserve contradiction
The strongest narrative choices usually:
- improve one human outcome
- weaken one structural outcome
or
- improve structure
- cost trust, mercy, or surprise

## Use hidden variables sparingly
Do not change `PREDICT`, `TOKENS`, or `ALIGN` on every quest.
Reserve those for identity-defining moments.

---

# NEXT STEP

Suggested follow-up docs:
- Act 1 full event matrix
- Act 2 full event matrix
- companion approval event sheet
- faction reputation event sheet
- Act 3 handoff rules using these results

---

# END
