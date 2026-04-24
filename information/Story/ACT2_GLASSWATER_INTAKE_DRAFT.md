# Act 2 Dungeon Draft: Glasswater Intake

## Placement

- Best unlocked after the player clears one of the three early leads and before they commit to the second.
- This should no longer be treated as a tiny stopover. It works best as a medium optional dungeon: substantial enough to feel like a real Act 2 outing, but still shorter than a full late-route site.
- Target length: roughly 40 to 60 minutes on a clean run.
- If skipped until after `Sabotage Night`, the site should still be playable, but it should read as partially stripped, politically dirtier, and more obviously contaminated.

## Unlock Logic

- Trigger source:
  - sponsor report about fouled water and missing courier satchels
  - Stonehill rumor that the lower pumps are carrying grit and "voices" into camp buckets
  - a recovered survey note from any first-cleared early lead mentioning an annex below the old Glasswater run
- Recommended timing:
  - offered after the first early lead
  - strongest if completed before the second early lead
  - weakened but still meaningful if completed before the midpoint
  - late, damaged version if attempted after the midpoint

## Narrative Role

- `Glasswater Intake` is a Pact-era water-control annex buried in the lower slopes between Phandalin and the Wave Echo approaches.
- On the surface it is practical dwarfwork: sluice gates, pressure valves, lamp niches, and a relay office that once tracked safe flow and ration timing.
- Under Quiet Choir use, it becomes an early-act proof point that the cult is seizing infrastructure, falsifying logistics, and turning ordinary systems into listening lines.
- The dungeon bridges the tone between:
  - frontier recovery and claims politics
  - expedition routework
  - the first believable signs that the mine's resonance can be weaponized

## Experience Goals

- Teach that Act 2's battlefield includes flow control, supply truth, and who gets to name a working route.
- Give `Town Stability`, `Route Control`, and `Whisper Pressure` a physical, player-readable location before the midpoint.
- Foreshadow `South Adit` with courier discipline, prisoner-routing hints, and anti-whisper improvisation in a less catastrophic form.
- Give early-Act-2 companions and sponsors a place to speak with authority before Nim and Irielle dominate the underground story.

## Scope

- Recommended structure:
  - 10 to 12 rooms
  - 4 mandatory combats
  - 1 optional or branch-dependent combat
  - 2 major skill scenes
  - 1 social or pressure-cooker negotiation that can break either way
  - 1 final chamber choice that cleanly changes later state
- This should feel more like a compact late-Act-1 dungeon than a tiny Act 2 detour.

## Tone And Look

- Wet stone, rusting gearwork, algae-dark channels, and lamp housings that still imply care even after neglect.
- Sound design should matter in the writing: the intake hums, drips, rattles, and occasionally almost sounds like a breath catching in pipes.
- The horror stays restrained. No full Black Lake spectacle, no Forge-light grandeur, no obvious cosmic revelation. The wrongness should still be deniable by frightened practical people.

## Physical Layout

The annex should read as functional dwarfwork, not a cave maze. A player should be able to picture what the place was built to do.

### Zone 1: Surface Switchyard

- `Rock Weir Approach`
- `Intake Yard`
- `Gatehouse Winch`

This zone establishes that the annex still matters to living people. Tracks, carts, rope marks, and recent boot prints prove the intake is in active use.

### Zone 2: Upper Works

- `Valve Hall`
- `Settling Cistern`
- `Lamp Chapel`

This is the old operating core: pressure control, flow routing, and the first moral question about whether the party is here to reclaim, expose, or exploit.

### Zone 3: Relay Annex

- `Relay Office`
- `Ledger Vault`
- `Overflow Crawl`

This zone shifts the dungeon from engineering to logistics. The player learns that the annex is helping the Quiet Choir move messages, manifests, and people without looking like a cult site.

### Zone 4: Deep Works

- `Filter Beds`
- `Pump Gallery`
- `Headgate Chamber`

This is the contaminated lower end. The ritual pressure is still small by Act 2 standards, but it is enough to prove the system is being tuned into something worse.

## Traversal Shape

- The main route should fork in the Upper Works:
  - a cleaner stabilizer path through valves and the chapel
  - a dirtier intelligence path through runoff, relay traffic, and hidden ledgers
- Both paths reconnect before the Deep Works.
- A small optional crawlspace loop should allow:
  - an ambush setup
  - a stealth bypass
  - or a delayed-state shortcut with a cost

## Encounter Budget

### Encounter 1: Intake Yard Watch

- Enemy package:
  - `cult_lookout`
  - `expedition_reaver` or hired fixer
  - delayed version adds another `cult_lookout`
- Function:
  - teaches that the annex is being defended as a work site, not a shrine
  - establishes courier traffic and stake-driven human opposition

### Encounter 2: Valve Hall Sentinels

- Enemy package:
  - `animated_armor`
  - optional second `animated_armor` if the player enters loud or late
- Gimmick:
  - the room is full of pressure wheels and vent bursts
  - clean route players can spend effort stabilizing the room before the fight

### Encounter 3: Settling Cistern Sludge

- Enemy package:
  - `ochre_slime`
  - optional `grimlock_tunneler` on the delayed version
- Gimmick:
  - bad footing, collapsing walkways, and corrosive sludge reward positioning instead of pure damage racing

### Encounter 4: Relay Office Scramble

- Default form:
  - pressure scene, ledger snatch, or negotiation
- Failure or aggressive play turns it into combat:
  - `expedition_reaver`
  - `cult_lookout`
- Function:
  - one of the best places in the dungeon to reward Bryn, Nera-style courier logic, or pure player caution

### Encounter 5: Filter Beds Pressure Line

- Enemy package:
  - `choir_adept`
  - `cult_lookout`
  - one slime or labor-horror support body depending on route state
- Gimmick:
  - the room fights like a half-finished system, with filtration grates, murky sightlines, and whisper-heavy runoff

### Encounter 6: Headgate Chamber Finale

- Boss shell:
  - `Brother Merik Sorn`, Quiet Choir field operator and waterworks quartermaster
  - support from one `animated_armor` or hired `expedition_reaver`
- Function:
  - this should feel like shutting down a dangerous process with one operator at its center
- Core pressure:
  - the headgate is being tuned into a low-grade listening pipe that can carry rumor, chant cadence, and altered runoff toward camp lines

## Room-By-Room Draft

| Room | Role | Likely checks | Encounter pressure | Main payoff |
| --- | --- | --- | --- | --- |
| Rock Weir Approach | entry read | `Survival`, `Stealth`, `Investigation` | none or scouting pressure | identify recent route traffic and whether the site is actively worked |
| Intake Yard | first commitment | `Deception`, `Stealth`, `Athletics` | Encounter 1 | decide between infiltration, false authority, or hard breach |
| Gatehouse Winch | utility room | `Athletics`, `Sleight of Hand`, `Investigation` | optional short hazard | unlock safer route, open flood bypass, or make later retreat possible |
| Valve Hall | control room | `Investigation`, `Arcana`, `Athletics` | Encounter 2 | stabilize pressure or worsen later contamination |
| Settling Cistern | environmental danger | `Survival`, `Acrobatics`, `Medicine` | Encounter 3 | rescue trapped workers, collect runoff sample, or lose time |
| Lamp Chapel | moral and spiritual scene | `Religion`, `Insight`, `Persuasion` | no combat unless badly mishandled | lower `Whisper Pressure`, reveal Pact maintenance culture, unlock Elira beat |
| Relay Office | logistics scene | `Investigation`, `Stealth`, `Deception` | Encounter 4 if blown | seize route ledgers, expose false manifests, identify sponsor leverage |
| Ledger Vault | hidden info room | `Sleight of Hand`, `Investigation`, `History` | low direct danger | discover prisoner-routing hints and claims fraud evidence |
| Overflow Crawl | optional loop | `Stealth`, `Survival`, `Athletics` | possible ambush | gain shortcut, flank finale, or recover emergency cache |
| Filter Beds | hard attrition room | `Athletics`, `Arcana`, `Stealth` | Encounter 5 | decide whether to purge contamination or follow it to the source |
| Pump Gallery | pre-finale setup | `Investigation`, `Medicine`, `Religion` | hazard or support scene | ready the party for boss, free trapped workers, or sabotage support lines |
| Headgate Chamber | finale | `Arcana`, `Persuasion`, `Athletics` | Encounter 6 | purge, claim, or repurpose the headgate |

## Detailed Flow Notes

### Rock Weir Approach

- The party first sees watermarks, hauling grooves, and a stone apron built to keep flood damage off the old path.
- The scene should answer a simple question: who has been using this place recently, and how carefully?
- Clean success here should set one of:
  - a stealth advantage into the yard
  - a clue about courier schedules
  - an early sign that the runoff is being intentionally misdirected

### Intake Yard

- This is the "humans are using the ruin" scene.
- There should be signs of:
  - temporary camp discipline
  - ordinary tools being repurposed for bad work
  - ledgers or satchels treated as more important than salvage
- The best version of this scene supports three play styles:
  - infiltrate as a survey crew
  - use false quartermaster or sponsor authority
  - hit the yard hard before the report can run

### Gatehouse Winch

- A compact mechanical room that makes the dungeon feel physical.
- It should offer an immediate tactical choice:
  - open the safe route
  - jam the emergency flood release
  - prepare a loud fallback escape
- This is also a good place for Kaelis or Tolan to sound competent.

### Valve Hall

- The first "systems room" fight.
- The room should reward people who understood the approach instead of just winning initiative.
- A stabilized Valve Hall should matter later by:
  - softening the Filter Beds
  - lowering contamination
  - or keeping the headgate from entering the finale at full pressure

### Settling Cistern

- This room is where the intake stops being merely suspicious and starts feeling unhealthy.
- Include:
  - partially dissolved prayer strips
  - contaminated runoff
  - one trapped worker, guard, or coerced laborer if the player is early enough
- That trapped person can become:
  - witness testimony
  - a human cost beat
  - or a missed opportunity if the player prioritizes speed

### Lamp Chapel

- Small shrine alcove for the crews who maintained the intake.
- This room proves the old Pact culture included labor dignity, maintenance ritual, and limits on what the system was supposed to do.
- If Elira is present, this should be one of her cleanest early Act 2 field-faith scenes.
- If desecrated or ignored, the dungeon should feel colder after this point.

### Relay Office

- One of the dungeon's most important rooms.
- This is where the player learns that the intake was used to move:
  - courier satchels
  - false manifests
  - reserve schedules
  - occasional "special transfers" that hint at South Adit without fully revealing it
- The office should support:
  - Bryn reading the live satchel
  - a stealth steal
  - a hard interrogation
  - a public-document route that helps `Town Stability`

### Ledger Vault

- A narrow records room or sealed locker space behind the office.
- Strong place for a history-of-claims beat.
- Evidence here can name:
  - one sponsor-adjacent opportunist
  - one quietly complicit foreman
  - or a false claimant who wanted the route left unstable

### Overflow Crawl

- A wet side passage that is miserable but useful.
- This should be optional, not mandatory.
- It exists to make the dungeon feel deeper and more interconnected.
- Good location for:
  - emergency anti-whisper supplies
  - an ambush setup on the finale
  - or a delayed-state sign that workers were moved through the annex in a hurry

### Filter Beds

- This should be the dungeon's messiest fight.
- Visibility is bad, footing is unreliable, and the enemy has partial control of the terrain.
- If the party stabilized the Valve Hall earlier, this room gets fairer.
- If they rushed, the beds are fouler and the room should push `Whisper Pressure` harder.

### Pump Gallery

- The pause before the finale.
- A place to:
  - free or triage survivors
  - sabotage support pressure
  - or overhear the headgate operator's intent
- This is a strong companion-reaction room because it asks whether the party is still doing rescue work or has pivoted fully into strategic war.

### Headgate Chamber

- The finale should feel procedural and dangerous:
  - valves opening on wrong beats
  - runoff carrying chant fragments
  - the room trying to turn water pressure into a listening line
- The boss should be a field operator, not a mystic mastermind.
- Best version:
  - phase one is stopping the process
  - phase two is winning the fight
  - phase three is deciding what to do with the headgate once it is theirs

## Major Branches

### Branch 1: Stabilize The Water Or Chase The Ledgers

- Stabilize path:
  - better `Town Stability`
  - lower `Whisper Pressure`
  - stronger human approval
  - weaker immediate route leverage
- Ledger path:
  - better `Route Control`
  - more precise sabotage-night or Black Lake leverage
  - morally murkier because the intake keeps hurting people longer

### Branch 2: Public Exposure Or Quiet Exploitation

- Public exposure:
  - raises trust
  - creates sponsor friction
  - gives camp and council scenes stronger political footing
- Quiet exploitation:
  - creates sharper route leverage
  - gives a more cynical expedition tone
  - risks making later sponsor scenes more transactional

### Branch 3: Purge Or Repurpose The Headgate

- Purge:
  - cleaner campaign contamination profile
  - likely `Whisper Pressure -1`
  - more Elira approval
  - less later route intelligence
- Repurpose:
  - likely `Route Control +1`
  - future special read on one later site
  - but `Whisper Pressure` becomes more volatile
  - more likely to trigger ominous midpoint or forge-adjacent text later

## Delayed-State Version

If the player reaches the dungeon after `Sabotage Night`, the annex should not feel preserved for their convenience.

- Surface changes:
  - the intake yard has been partially stripped
  - one set of ledgers is already gone
  - evidence is harder to expose publicly because someone started cleaning the story
- Mechanical changes:
  - one extra enemy on the first or fourth encounter
  - the trapped-worker beat becomes a corpse, escaped witness, or failed rescue instead
  - `Whisper Pressure` starts one notch worse inside the dungeon
- Story changes:
  - sponsor blame is uglier
  - the annex reads less like a recoverable system and more like a site the expedition has already failed to keep ahead of

## Sponsors And Faction Hooks

### Halia / Exchange

- Best at reading the profit motive in the false manifests.
- Can offer a special line that turns the Relay Office into leverage instead of a public scandal.
- More likely to favor repurposing the headgate than purging it.

### Linene / Lionshield

- Best at quartermaster logic and securing the site cleanly.
- Gives the most coherent "make this annex useful again" framing.
- Strong support for public proof and disciplined reclamation.

### Elira + Daran / Wardens

- Best moral fit for restoring clean water and naming the annex as civic infrastructure rather than prize salvage.
- Strongest support for purge path and trapped-worker rescue.

## Companion Hooks

### Elira Dawnmantle

- Lamp Chapel scene
- trapped-worker triage support
- strongest reaction against repurposing the headgate without safeguards

### Bryn Underbough

- Relay Office satchel read
- Ledger Vault fraud logic
- can support quiet exploitation without making it feel stupid

### Kaelis Starling

- approach and crawlspace route logic
- reads watch patterns and yard weaknesses
- frames the place as a system to out-scout, not a mystery to fear

### Tolan Ironshield

- Gatehouse and Valve Hall authority
- strongest voice on whether holding a dangerous site is ever worth the risk
- good moral counterweight if the player starts making purely strategic decisions

## Rewards

### Baseline Rewards

- `thoughtward_draught x1`
- `scroll_clarity x1`
- modest gold and supply value
- one strong clue packet tying the Quiet Choir to ordinary routework

### Milestone Reward Options

- `glasswater_gate_seal`
  - unique utility item
  - likely `Investigation +1` or `Perception +1`
  - minor anti-whisper edge
- `intake_foreman_token`
  - logistics-leaning reward
  - favors `Route Control` style players
- Or keep the dungeon item-light and let its main reward be state changes plus future special options

## Future Payoff Hooks

- If the player decoded the relay traffic:
  - grant a future special option in `Sabotage Night`, `Black Lake Barracks`, or a sponsor debrief
- If the player restored clean flow:
  - `Town Stability` scenes in camp and town should sound less frightened
- If the player repurposed the headgate:
  - later scenes should remember the party chose to stand close to the signal for leverage
- If the player exposed claims fraud publicly:
  - council and sponsor scenes should treat that as a real political move, not a footnote

## Exact Scene Beat Sheet

This section is meant to be implementation-facing. The writing can still be tightened later, but these are the intended beats, prompts, and spoken lines to build toward.

### Beat 0: Offer And Hook In Camp

- Opening image:
  - a camp hand opens a barrel meant for drinking water and gets cold mineral stink, black grit, and a taste that makes everyone in earshot fall quiet too fast
- Intended first description:
  - "The barrel should smell like wet iron and old wood. Instead it smells like stone that listened to something it should not have heard."
- Sponsor-facing hook lines:
  - `Halia Thornton`: "If somebody is poisoning a route and the panic around it, I want the ledger before I want the sermon."
  - `Linene Graywind`: "Bad water breaks a camp faster than arrows. Fix the intake or I start counting this expedition by how many people it makes sick."
  - `Elira Dawnmantle`: "Water should not make a room sound frightened before anyone speaks. Go see what is being taught to it."
- Player-facing prompt:
  - "How do you answer the Glasswater report?"
- Recommended options:
  - `"Move now. If the annex is live, every hour gives someone time to clean the lie."`
  - `"Bring me the oldest route note first. I want the intake's real purpose before I see what they did to it."`
  - `"Question the runner. Fear edits reports faster than ink does."`
- Exit beat:
  - the choice does not change the route destination, but determines whether the first approach favors stealth, logistics context, or human testimony

### Beat 1: Rock Weir Approach

- Opening text:
  - "The Glasswater run begins as practical dwarfwork cut into a wet slope: a rock apron, a spill channel, and old maintenance posts silvered by mist. Fresh boot marks cut across all of it like insults."
- Core observation:
  - this place was not rediscovered by romantics or treasure hunters; it is being used by people who understand schedules
- Companion hooks:
  - `Kaelis`: "Watch how the prints cross the runoff, not how many there are. Somebody here trusts the water to hide noise."
  - `Tolan`: "Those braces were serviced recently. Not well. Recently."
- Prompt:
  - "How do you read the annex before the yard sees you?"
- Recommended options:
  - `Survival`: trace the hauling and drainage rhythm
  - `Stealth`: get close enough to hear the yard cadence
  - `Investigation`: read the engineering scars instead of the footsteps
- Success beats:
  - identify recent courier traffic
  - mark a blind approach into the Intake Yard
  - foreshadow that someone is venting altered runoff intentionally
- Rough beat:
  - the party still advances, but enters the yard as observed pressure instead of unknown trouble

### Beat 2: Intake Yard

- Opening text:
  - "The yard is a working lie. Rope slings, valve keys, repair sledges, and stacked supply tins make it look like a maintenance annex held together by hard people. Then you notice which crates are guarded harder than the tools."
- Human truth of the room:
  - the defended objects are satchels, order boards, and sealed tubes, not salvage
- First spoken line if the party is challenged:
  - `Yard Lookout`: "Late relief or bad luck? Choose fast. We only have patience budgeted for one."
- Player-facing prompt:
  - "How do you enter the Intake Yard?"
- Recommended options:
  - `"Official route inspection. Open the line and stop wasting my time."`
  - `"Keep low, cut the nearest watcher, and let the yard realize too late what changed."`
  - `"Hit them hard before the report runs."`
- If deception works:
  - the party gets a brief walk through the working yard and overhears that "the headgate only needs one more clean count"
- If stealth works:
  - the party learns the courier stack matters more than the pump stack
- If force is chosen:
  - Encounter 1 begins with the yard half-set and the whole place sounding louder than it should

### Beat 3: Gatehouse Winch

- Opening text:
  - "A narrow gear room hangs over the first drop channel. The winch brake is warm. Somebody has been making the intake choose between flood safety and hidden traffic."
- Prompt:
  - "What do you do with the gatehouse controls?"
- Recommended options:
  - `"Open the maintenance route and give the party a cleaner line through the upper works."`
  - `"Jam the emergency release. If somebody downstream needs a panic flood, they do not get one."`
  - `"Set the brake to fail on our timing and keep an exit plan in reserve."`
- Exact support lines:
  - `Tolan`: "This room is the difference between a site and a trap. Decide which one we are walking into."
  - `Kaelis`: "If we leave ourselves one honest exit, I will take it. If not, I would rather know that now."

### Beat 4A: Valve Hall

- Opening text:
  - "Bronze wheels, pressure rods, and mineral-white spray turn the Valve Hall into a storm someone taught to obey numbers."
- Room truth:
  - the Quiet Choir did not build new magic here; it taught an old system a wrong priority
- Prompt:
  - "How do you take control of the Valve Hall?"
- Recommended options:
  - `"Read the pressure map and shut the dangerous line first."`
  - `"Force the wheels over before the sentinels can lock the room down."`
  - `"Break the wrong valve and make the hall punish its current masters."`
- Success beats:
  - lower finale pressure
  - make the Filter Beds fairer
  - mark `glasswater_valves_stabilized`
- Encounter note:
  - if the party came in loud, the sentinel armor activates while spray and vent bursts change footing

### Beat 4B: Settling Cistern

- Opening text:
  - "The cistern should be a quiet basin where silt drops out before clean flow continues. Instead the surface looks filmed over with thinking darkness."
- Human-cost beat:
  - one trapped worker or coerced laborer is reachable if the player is early enough
- Prompt:
  - "What matters most in the cistern?"
- Recommended options:
  - `"Cut the trapped worker free and keep them talking."`
  - `"Read the runoff and learn what was mixed into it."`
  - `"Cross fast before the room decides we belong in it."`
- Exact support line if Elira is present:
  - `Elira Dawnmantle`: "If someone is still breathing in this room, that is the first clean task we have had since entering it."

### Beat 5: Lamp Chapel

- Opening text:
  - "The chapel is hardly larger than a pantry: six lamp niches, a worn basin, and a hammered plaque reminding crews that steady hands keep whole towns alive."
- Function:
  - this is where the dungeon proves the old Pact treated maintenance as moral work, not invisible labor
- Prompt:
  - "How do you answer the chapel?"
- Recommended options:
  - `"Wake the old maintenance rite and force one clean line through the annex."`
  - `"Read what kind of people wrote a prayer for valves and lamp oil."`
  - `"Take the basin water and move. Reverence can wait until the route is safe."`
- Exact lines:
  - `Elira Dawnmantle`: "This is a shrine for people who kept strangers alive without ever meeting them. I would rather not fail them in their own room."
  - If the player answers the chapel well: "One lamp catches cleanly. The whole annex does not become holy. It only remembers, for a moment, that service and obedience were not meant to be the same thing."

### Beat 6: Relay Office

- Opening text:
  - "The Relay Office is too orderly for a ruin. Satchels hang by route mark, manifests are weighted against damp, and one wall is given over entirely to copied names."
- Core revelation:
  - this annex has been used to edit traffic, with fouled water serving as cover
- Prompt:
  - "What do you seize before the room scatters?"
- Recommended options:
  - `"Take the live satchel. Real orders matter more than neat shelves."`
  - `"Read the claim manifests and name who profits from the intake staying sick."`
  - `"Pressure the clerk or fixer before fear turns them useless."`
- Exact support line if Bryn is present:
  - `Bryn Underbough`: "Ignore the polished case. The live packet is always the one trying hardest not to look like the room is built around it."
- Exact clue beat:
  - one ledger references "special transfers" moving through lower rooms on nights when town water ran foul, foreshadowing South Adit without explaining it

### Beat 7: Ledger Vault

- Opening text:
  - "The vault door is small, ugly, and expensive in the way only practical secrets ever are."
- Intended discoveries:
  - claims fraud
  - deliberate delays in repair allotments
  - coded traffic references that can later support sponsor scenes, sabotage reads, or Black Lake barracks logic
- Prompt:
  - "Which truth do you take out first?"
- Recommended options:
  - `"The proof that someone profited from the intake staying unstable."`
  - `"The route ledgers. We need the living pattern before the guilty names."`
  - `"The prisoner-transfer notations. Someone is moving people under cover of ordinary supply work."`

### Beat 8: Overflow Crawl

- Opening text:
  - "The crawl smells like old metal, wet lime, and the kind of panic people leave behind when they had to move through a space not built for standing."
- Function:
  - gives a grim side-read on how the annex was used
- Intended discoveries:
  - emergency anti-whisper kits
  - evidence of rushed movement through the annex
  - one flanking route into the Deep Works

### Beat 9: Filter Beds

- Opening text:
  - "The filtration floor should slow water down until it clarifies. Instead it turns every step into an argument about what deserves to keep moving."
- Prompt:
  - "How do you break the Filter Beds line?"
- Recommended options:
  - `"Push straight through while the room is still trying to decide where to hold us."`
  - `"Use the valvework we stabilized and make the beds turn against them."`
  - `"Follow the adepts' safe lane and then cut it out from under them."`
- Key combat feel:
  - murky sightlines
  - shifting footing
  - the sense that the room itself is sorting the living into useful and discardable categories

### Beat 10: Pump Gallery

- Opening text:
  - "The pump gallery is where the annex stops pretending to be neglected. The housings are warm, the rods are greased, and somebody has been keeping this machine alive on purpose."
- Pre-boss truth:
  - the headgate is being tuned into a listening pipe, with fouling used as cover
- Prompt:
  - "What do you secure before the headgate chamber?"
- Recommended options:
  - `"Free the trapped workers and force the room to remember witnesses exist."`
  - `"Sabotage the support pressure before the operator can use it."`
  - `"Listen at the chamber door and learn what kind of doctrine talks to pipes."`

### Beat 11: Headgate Chamber

- Opening text:
  - "The chamber yawns open around a great iron wheel above a black running channel. Brass rods hum in their brackets. Prayer-strips float in the runoff like things too tired to sink."
- Immediate visual:
  - Brother Merik Sorn has one hand on the wheel and the other on a relay slate, running a ritual that looks half like maintenance and half like accounting
- Pre-fight script:
  - `Brother Merik Sorn`: "Hold the wheel where it is. The count is almost clean."
  - `Brother Merik Sorn`: "Do you hear how quiet the room gets when every line knows its place?"
  - If the player exposed fraud earlier: `Brother Merik Sorn`: "So you found the paper lie before the water lie. Most people need the sickness first."
- Player-facing confrontation prompt:
  - "How do you open the Headgate confrontation?"
- Recommended options:
  - `"Open the gate and step away from it."`
  - `"You poisoned a town to test whether fear would travel faster than truth."`
  - `"Break the tuning line now. We end this before the whole valley starts listening."`

### Beat 12: Aftermath Choice

- Once Merik falls or the chamber is secured, the player should get a final exact-choice moment:
  - `"Purge the headgate. Let water be water again."`
  - `"Lock the annex down and drag every ledger into daylight."`
  - `"Strip the Choir's tuning and keep the headgate for the expedition."`
- Outcome intent:
  - purge is the clean moral resolution
  - lockdown is the civic-truth resolution
  - repurpose is the leverage resolution

## Boss Dialogue Packet: Brother Merik Sorn

### Role

- Merik is not a mystic mastermind.
- He is a field theologian of systems, pressure, and compliance.
- He believes any network becomes truer when resistance is filtered out of it.
- He should sound like a quartermaster, engineer, and cult believer whose language has started to fuse into one thing.

### Safe Core Lines

- "Water is honest. It only looks cruel when the channel is."
- "Noise is not life. Most of the time it is waste pretending to be freedom."
- "A line that carries everything clearly carries too much."
- "You call this poisoning because you still think every useful thing must also be gentle."
- "The annex is not sick. It is finally being asked to choose."

### First-Sight Lines

- `Brother Merik Sorn`: "Hold the wheel where it is. The count is almost clean."
- `Brother Merik Sorn`: "One more turn and the whole intake starts teaching the same lesson to everyone downstream."
- `Brother Merik Sorn`: "You came all this way to defend confusion, then."

### Conditional First-Sight Variants

- If `glasswater_chapel_answered`:
  - `Brother Merik Sorn`: "You woke a maintenance prayer in a room built for service. Admirable. Wrong. Service without obedience is only delay."
- If `glasswater_relay_ledgers_taken`:
  - `Brother Merik Sorn`: "The papers mattered less than the rhythm they protected, but people like you always need ink before they trust a wound."
- If delayed-state:
  - `Brother Merik Sorn`: "You are late. We already sent the cleaner copies and the dirtier water."

### Responses To Player Openers

- If the player chooses `"Open the gate and step away from it."`
  - `Brother Merik Sorn`: "Step away? From the first honest work this annex has done in a century?"
  - `Brother Merik Sorn`: "No. You do not open a line like this and then hand it back to people who still think mercy means disorder."

- If the player chooses `"You poisoned a town to test whether fear would travel faster than truth."`
  - `Brother Merik Sorn`: "Not poisoned. Tuned."
  - `Brother Merik Sorn`: "Fear only moves faster than truth when truth insists on arriving in pieces."

- If the player chooses `"Break the tuning line now. We end this before the whole valley starts listening."`
  - `Brother Merik Sorn`: "Then you do understand what this is."
  - `Brother Merik Sorn`: "Good. Understanding usually arrives one room before disobedience."

### Companion Counter-Lines

- `Elira Dawnmantle`: "You do not get to call sickness discipline because you wrote it down neatly."
- `Bryn Underbough`: "He talks like a clerk who found religion at the bottom of a lockbox."
- `Tolan Ironshield`: "Enough. It is a waterworks annex, not a chapel for frightened accountants."
- `Kaelis Starling`: "He keeps saying 'line' because he wants the room to do the threatening for him."

### Combat Callouts

- On first pressure spike:
  - `Brother Merik Sorn`: "Feel that? Even the water prefers a single answer."
- When support joins him:
  - `Brother Merik Sorn`: "Hold your places. The room punishes movement better than you do."
- If the player breaks a valve or tuning rod:
  - `Brother Merik Sorn`: "Careless. You would rather break a system than admit it was working."
- At half health:
  - `Brother Merik Sorn`: "You think this is victory because you still measure by bodies and noise."
- If chapel or trapped-worker beats were resolved well:
  - `Brother Merik Sorn`: "There it is. Witnesses, mercy, names. You drag all that weight into every clean mechanism and call the failure virtue."

### Near-Defeat Lines

- `Brother Merik Sorn`: "Too loud. Always too loud."
- `Brother Merik Sorn`: "The valley could have learned one clean fear together."
- `Brother Merik Sorn`: "Now it will go on teaching itself the hard way."

### Defeat And Capture Lines

- If Merik dies in the fight:
  - his last line should not reveal a deeper villain
  - best final phrase: "You broke the channel, not the need."
- If spared or made to stand down:
  - `Brother Merik Sorn`: "You will use it too. Every expedition does. The only difference is whether you lie to yourselves while it happens."

### Post-Fight Choice Lines

- If the player purges the headgate:
  - `Brother Merik Sorn`: "Back to waste, then. Back to a town teaching itself ten fears badly."
- If the player locks the annex down:
  - `Brother Merik Sorn`: "Better. Locks admit that value exists."
- If the player repurposes the headgate:
  - `Brother Merik Sorn`: "There. That is the first honest choice you have made since entering."

### Writing Guardrails

- Merik should never mention Malzurath or any true deep-cosmic name.
- He should sound convinced that he is improving a system, not summoning horror.
- His menace comes from treating people as flow variables.
- He should read as a dangerous middle-manager of revelation: not grand enough to be the act's final ideology, but more than grounded enough to make the annex memorable.

## Suggested Runtime Flags

- `glasswater_intake_seen`
- `glasswater_route_offered`
- `glasswater_valves_stabilized`
- `glasswater_chapel_answered`
- `glasswater_relay_ledgers_taken`
- `glasswater_claim_fraud_named`
- `glasswater_trapped_workers_saved`
- `glasswater_headgate_purged`
- `glasswater_headgate_repurposed`
- `glasswater_relay_route_decoded`

These do not all need to ship at once, but the draft should think in flags so the eventual playable version has room to breathe.

## Implementation Recommendation

- Phase 1:
  - ship the dungeon as a playable medium optional site with 8 to 10 rooms and 4 combats
- Phase 2:
  - add delayed-state variation, stronger sponsor hooks, and payoff flags into the midpoint
- Phase 3:
  - pay forward the relay intelligence and headgate choice into Black Lake, sponsor politics, or Act 3 contamination tone

## Bottom Line

- `Glasswater Intake` should feel like the place where Act 2 stops being "who gets the mine?" and becomes "who is already rewriting the systems around it?"
- It earns its place by making the expedition war tangible, giving the metrics a real body, and letting the player choose between cleaner recovery and sharper leverage before the midpoint forces harder losses elsewhere.
