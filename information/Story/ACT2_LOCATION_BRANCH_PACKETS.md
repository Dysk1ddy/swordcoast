# Act 2 Location Branch Packets

This file expands several Act 2 locations into heavier branch webs intended for future implementation. It should be read alongside `information/Story/ACT2_CONTENT_REFERENCE.md` and not as a replacement for the main route order.

It intentionally does not re-draft `Glasswater Intake`, because that location already has a dedicated packet in `information/Story/ACT2_GLASSWATER_INTAKE_DRAFT.md`.

## Design Rules

- Every branch should answer three questions:
  - who gets the truth
  - who pays the cost
  - what system leaves the room changed
- Every location should offer at least three resolution families:
  - civic / witness-first
  - leverage / route-control-first
  - containment / anti-whisper-first
- Branches should be allowed to hybridize, but a player should rarely be able to have every benefit at once.
- Each packet should pay into at least two of the three live Act 2 pressures:
  - `Town Stability`
  - `Route Control`
  - `Whisper Pressure`
- The Quiet Choir should keep feeling like a cult that hijacks ordinary systems before it feels like a cosmic cult in a final dungeon.
- Companion hooks should not be flavor-only. If a companion branch exists, it should change later options, metrics, or what information becomes legible.

## Cross-Location Logic

- `Conyberry and Agatha's Circuit` shapes how much the party understands sacred restraint, public warning, and what the old Pact was trying to prevent.
- `Neverwinter Wood Survey Camp` determines how honest the expedition's map becomes before the midpoint.
- `Stonehollow Dig` determines how much of the deeper route is understood through rescue, scholarship, or sealed loss.
- `Broken Prospect` determines whether the expedition owns Wave Echo's threshold publicly, secretly, or not at all.
- `Black Lake Causeway` sends the party to the Forge carrying one of three victories:
  - cleaner, holier, and less informed
  - harsher, sharper, and more militarized
  - or strategically brilliant but spiritually compromised

## Packet 1: Conyberry And Agatha's Circuit

Detailed expansion draft: `information/Story/ACT2_CONYBERRY_AGATHA_DRAFT.md`

### Packet Focus

`Conyberry` carries warning, grief, and the politics of who gets to carry a truth that should frighten everyone.

Agatha opens the packet. The lasting questions are:

- whether the truth becomes public warning, private leverage, or sacred restraint
- whether Elira's mercy-oriented faith can survive contact with a place that was already abandoned badly
- whether the old Pact reads as superstition, moral discipline, or exploitable old law

### Branch Axes

| Axis | Civic branch | Leverage branch | Containment branch |
| --- | --- | --- | --- |
| Entry response | protect pilgrims and steady the road | quietly isolate the most informed witness | shadow the wrongness to its source |
| Sacred site handling | restore the chapel and carry warning outward | bargain for specific names and route facts | bind the warning to warding instead of public speech |
| Final use of Agatha's truth | share it widely | keep it controlled | limit it to those who can bear it safely |

### Phase 1: The Hushed Pilgrims

The approach to Conyberry opens on a frightened cluster of travelers, shrine visitors, and rumor-carriers who have started editing their own story because they do not trust what they heard on the road.

Primary options:

1. Protect the pilgrims openly.
   - The player treats the scene as a public calm-down and names the road as still belonging to the living.
   - Best for `Town Stability`.
   - Costs stealth deeper in the circuit because the party becomes the new center of attention.
   - Elira approval path.
2. Pull one witness aside and extract the cleanest version.
   - The player behaves like an investigator, not a comforter.
   - Best for `Route Control`.
   - Gives a more accurate route note into the circuit but leaves the larger group shakier.
   - Bryn can be useful here by reading who is lying from fear versus lying from habit.
3. Follow the one pilgrim whose story changed mid-sentence.
   - The player treats the approach as contamination tracking.
   - Best for `Whisper Pressure` control later.
   - Leads to a rougher, more uncanny first scene because the party chooses the wrongness first and people second.

Suggested runtime flags:

- `conyberry_pilgrims_steadied`
- `conyberry_clean_witness_taken`
- `conyberry_whisper_track_named`

### Phase 2: The Circuit Split

After the approach, the route should split into three concurrent concerns. The player can meaningfully complete two cleanly, but the third should always feel somewhat neglected or bruised.

#### Branch 2A: Chapel Of Lamps

The chapel should be less about loot and more about what kind of field faith Act 2 wants to be.

Key choices:

- Relight the chapel and wake one clean ward.
  - Best civic route.
  - Enables a stronger public-warning ending.
  - Gives Elira a strong field-faith scene.
- Strip the chapel for practical warding gear and take the basin lantern into the field.
  - Best hybrid route.
  - Gives anti-whisper leverage now, but weakens the town-facing sanctity of the site.
- Leave the chapel sealed and untouched.
  - Strong containment route if the player wants to avoid spreading a damaged ward.
  - Makes Conyberry feel more like a quarantined holy place than a reclaimed one.

Suggested follow-up flags:

- `conyberry_chapel_relit`
- `conyberry_field_lantern_taken`
- `conyberry_chapel_quarantined`

#### Branch 2B: Grave Ring

This is where the player learns whether the dead in this place feel robbed, misused, or still partially ordered by old rites.

Key choices:

- Read the grave markers historically.
  - Reveals the old Pact culture of distributed guardianship.
  - Helps later `Broken Prospect` and `Black Lake shrine` reads.
- Name the dead aloud and stabilize the ring as memory rather than puzzle.
  - Best moral route.
  - Better for `Town Stability` style texture and camp digest.
- Search the ring for hidden claimant marks and later additions.
  - Best leverage route.
  - May expose that somebody in the modern claims race has already been using Conyberry as a place to hide ugly paperwork.

Suggested follow-up flags:

- `conyberry_grave_history_read`
- `conyberry_dead_named`
- `conyberry_claim_marks_found`

#### Branch 2C: Defiled Sigil

This is the first place where the player can directly see the Quiet Choir trying to overwrite old restraint without yet going fully late-act spectacle.

Key choices:

- Break the sigil and push the cult mark out.
  - Cleaner spiritual route.
  - Better for `Whisper Pressure`.
- Copy part of the sigil before breaking it.
  - Dirtier but more useful.
  - Better for `Route Control` and later cult logic.
- Leave the sigil active long enough to bait a watcher.
  - Riskiest route.
  - Best for catching a human operator instead of only seeing aftermath.

Suggested follow-up flags:

- `conyberry_sigil_broken`
- `conyberry_sigil_copied`
- `conyberry_watcher_baited`

### Phase 3: Agatha's Bargain

The player should not simply ask one generic lore question. The branch web should frame Agatha as someone who can give different kinds of truth, all costly in different ways.

Primary asks:

1. Ask for the warning the town most needs.
   - This is the civic branch.
   - Agatha gives a truth that is broad enough to protect people, but less precise than route hunters would like.
   - Supports later public warning, shrine steadiness, and camp trust.
2. Ask who is lying in the claims war.
   - This is the leverage branch.
   - Agatha gives names, hidden motive, or buried transaction history.
   - Strong for sponsor tension and later barracks/relay reads.
3. Ask what the old Pact was actually afraid of.
   - This is the containment branch.
   - Agatha gives less actionable route information and more structural truth about restraint, resonance, and why the Pact divided custody.
   - Strong for later Black Lake and Forge spiritual reads.

Conditional modifiers:

- If `conyberry_chapel_relit`, Agatha is colder but clearer about civic warning.
- If `conyberry_sigil_copied`, Agatha is more suspicious and may only answer leverage questions reluctantly.
- If `conyberry_dead_named`, she treats the party like mourners and witnesses. The claimant cadence drops from her voice.

Suggested follow-up flags:

- `agatha_public_warning_known`
- `agatha_claimant_names_known`
- `agatha_pact_restraint_known`

### Phase 4: The Exit Decision

The final branch decides how the truth leaves Conyberry and who has to carry it.

Resolution families:

#### Civic Resolution: Carry The Warning Out Loud

- The player returns with a warning intended to steady town and expedition alike.
- Best for `Town Stability`.
- Halia and the more ruthless route operators see this as wastefully broad.
- Gives stronger council and camp language later.
- Best later payoff:
  - shrine lane during `Sabotage Night`
  - public trust if Black Lake goes badly

Suggested flag:

- `agatha_warning_shared`

#### Leverage Resolution: Keep The Sharpest Truth Controlled

- The player limits who hears the precise warning.
- Best for `Route Control`.
- Helps sponsor politics, ambush prevention, and later hidden-route options.
- Costs some trust because the expedition starts sounding like it owns knowledge before it has earned the right to.

Suggested flag:

- `agatha_warning_restricted`

#### Containment Resolution: Bind The Warning To Warding

- The player chooses not to spread the truth widely, and instead anchors it to a ward, relic, or chosen circle of listeners.
- Best for `Whisper Pressure`.
- Strongest Elira-aligned ending.
- Less useful in the immediate claims war, but stronger as Act 2 turns spiritually wrong.

Suggested flags:

- `agatha_warning_bound`
- `elira_field_lantern`

### Later Payoff Hooks

- `agatha_public_warning_known` can soften panic language in town and camp scenes.
- `agatha_claimant_names_known` can expose later sponsor or barracks fraud without a hard skill gate.
- `agatha_pact_restraint_known` can grant a special option at Black Lake shrine, Broken Prospect markers, or the Forge threshold.
- `agatha_warning_bound` can create an anti-whisper special read in late Act 2 even if the town never fully understands why.

## Packet 2: Neverwinter Wood Survey Camp

### Packet Focus

`Neverwinter Wood Survey Camp` carries map truth, hidden routes, and the risk of learning dirty route logic too well.

This packet turns on:

- whether the party wants an honest map, a superior ambush network, or a scorched-clean woods
- whether Kaelis's old scout instincts remain an asset or become a morally dangerous reflex
- whether the enemy is just cutting survey lines or teaching the expedition to distrust its own map

### Branch Axes

| Axis | Civic branch | Leverage branch | Containment branch |
| --- | --- | --- | --- |
| First approach | secure living survey hands | read the false map and hunt its author | burn infected caches and deny the line |
| Midpoint goal | reopen a trusted route | keep a hidden counter-route | prevent the woods from becoming a whisper nursery |
| Final map result | publish the clean route | keep the hidden route private | destroy enough knowledge that nobody owns it easily |

### Phase 1: The Outer Wood Split

The route into the camp should split before the actual camp appears.

#### Branch 1A: Watch-Ridge Crawl

- Scout-heavy approach.
- Strong Kaelis branch.
- Lets the player read watcher discipline and identify whether the enemy trusts human sight, alarms, or falsified survey confidence.
- Best for building a later counter-ambush path.

Suggested flag:

- `wood_watch_ridge_read`

#### Branch 1B: Burned Survey Lane

- The most direct route.
- Focuses on destroyed markers, sabotaged trust, and what it feels like when a frontier line has been edited faster than the workers can reassert it.
- Best for civic reclamation.

Suggested flag:

- `wood_lane_damage_named`

#### Branch 1C: Witness Coppice

- The player follows frightened runners, escaped laborers, or hired camp hands instead of the map itself.
- Best for human truth and later town-facing proof.
- Gives worse tactical approach but stronger social evidence.

Suggested flag:

- `wood_witnesses_sheltered`

### Phase 2: The Camp Core Split

Once inside the zone, the player should choose one primary concern first. The other two remain reachable, but one will always degrade.

#### Branch 2A: Reclaim The Camp

This route is about restoring function in public view.

Primary beats:

- stabilize remaining workers
- secure food, tools, and route slates
- prove the camp is not abandoned to rumor

Best for:

- `Town Stability`
- Linene-style disciplined logistics
- later cleaner sabotage-night morale

Suggested flags:

- `wood_camp_reclaimed`
- `wood_workers_rallied`

#### Branch 2B: Hunt The False Survey Line

This route is about learning how the sabotage really worked.

Primary beats:

- follow copied markers to a hidden blind
- identify who was rewriting the route versus only cutting it
- capture the logic of the false line instead of merely erasing it

Best for:

- `Route Control`
- Kaelis branch
- later special ambush or counter-infiltration options

Suggested flags:

- `wood_false_line_decoded`
- `wood_hidden_trail_known`

#### Branch 2C: Purge The Ash Caches

This route is about preventing the woods from becoming a low-grade relay zone for the Choir.

Primary beats:

- destroy blind caches, treated ash marks, and half-ritual signaling points
- deny contaminated trail logic to both sides
- preserve the region at the cost of immediate route dominance

Best for:

- `Whisper Pressure`
- harder-edged Rhogar or Elira interpretations of duty
- safer Act 3 contamination profile

Suggested flags:

- `wood_ash_caches_burned`
- `wood_signal_marks_denied`

### Phase 3: The Quartermaster Branch

The heart of the packet is a logistics scene with manifests, boots, and frightened runners in it.

The player corners a quartermaster, fixer, or line-runner who knows:

- which manifests were false
- which stores were allowed to vanish
- who benefited from the camp staying uncertain

Resolution options:

1. Public testimony.
   - Strongest civic route.
   - Best for `Town Stability`.
   - Weakest immediate tactical leverage because the liar becomes evidence, not an asset.
2. Quiet blackmail.
   - Strongest leverage route.
   - Best for `Route Control`.
   - Opens later dirty sponsor or barracks options.
3. Turn them into a double line.
   - Highest complexity route.
   - Best short-term tactical outcome.
   - Highest later betrayal risk.
   - Can create a later delayed-scene callback if the player relied too much on this.

Suggested flags:

- `wood_quartermaster_exposed`
- `wood_quartermaster_blackmailed`
- `wood_double_runner_seeded`

### Phase 4: Decide What Map Exists Afterward

After the zone is cleared, the player decides what kind of map survives it.

#### Civic Resolution: Publish The Clean Route

- The expedition circulates one honest map.
- Best for `Town Stability`.
- Modest `Route Control` gain.
- Reduces the enemy's ability to operate through pure uncertainty.
- Weaker at catching future infiltrators than the dirtier branches.

Suggested flag:

- `wood_clean_map_published`

#### Leverage Resolution: Keep The Hidden Counter-Route Private

- The expedition publicly reopens one lane while secretly keeping a better one for scouts and trusted operators.
- Best for `Route Control`.
- Strong Kaelis path.
- Costs trust if discovered.
- Can create later special options during `Sabotage Night` or `Broken Prospect`.

Suggested flags:

- `wood_counter_route_kept`
- `kaelis_hidden_trail_preserved`

#### Containment Resolution: Burn The Tainted Map Layer Entirely

- The player decides the woods have carried too much wrong instruction to leave easy routes alive.
- Best for `Whisper Pressure`.
- Slows the expedition but denies the Choir and the greediest claimants alike.
- Can improve late-act spiritual tone while weakening midpoint readiness.

Suggested flags:

- `wood_tainted_lines_burned`
- `kaelis_hidden_trail_burned`

### Later Payoff Hooks

- `wood_clean_map_published` improves town and worker morale during `Sabotage Night`.
- `wood_counter_route_kept` can create a hidden angle during sabotage, Broken Prospect, or even Black Lake courier interception.
- `wood_double_runner_seeded` can become a powerful midpoint special option or a later betrayal scene.
- `wood_tainted_lines_burned` can lower ambient contamination text later, even if it makes the claims race harder.

## Packet 3: Stonehollow Dig

### Packet Focus

`Stonehollow Dig` carries rescue, dangerous scholarship, and the question of whether saving people and preserving knowledge belong to the same duty.

This packet turns on:

- whether the party prioritizes bodies, notes, or containment
- whether Nim enters the act as a grateful rescued scholar, a furious survivor of delay, or a keeper of knowledge nobody should have carried out intact
- whether the deeper route becomes more legible because the party learned enough, or safer because they chose not to

### Branch Axes

| Axis | Civic branch | Leverage branch | Containment branch |
| --- | --- | --- | --- |
| First priority | save the trapped team | recover the survey truth | seal the resonant breach |
| Nim's role | survivor and witness | cartographer and theorem reader | reluctant keeper of what should not travel |
| Final outcome | more lives, fewer notes | stronger route, more risk carried out | less contamination, weaker route depth |

### Phase 1: The Dig Split

The opening rooms should push the player toward one working theory about the site.

#### Branch 1A: Main Cut

- Best for direct rescue urgency.
- Fastest route to living scholars.
- Worst route for preserving deeper notes cleanly.

Suggested flag:

- `stonehollow_main_cut_forced`

#### Branch 1B: Warded Side-Run

- Best for Pact reading and Nim-specific insight.
- Helps later theorem or ward options.
- Slower, more thoughtful branch.

Suggested flag:

- `stonehollow_ward_path_read`

#### Branch 1C: Hanging Bucket Lift

- Best for dirty, practical extraction.
- Good hybrid between route leverage and rescue.
- Higher structural risk, lower spiritual safety.

Suggested flag:

- `stonehollow_bucket_lift_taken`

### Phase 2: The Scholar Pocket Decision

Once the survivors are located, the player should face a sharper choice than a simple rescue check.

Primary priorities:

1. Stabilize the wounded first.
   - Best civic route.
   - Strongest `Town Stability` result.
   - Costs some note quality or route precision.
2. Secure the theorem cases and route slates first.
   - Best leverage route.
   - Strongest `Route Control` result.
   - Risks turning Stonehollow into a morally uglier rescue.
3. Seal the most dangerous pages and take only what can be carried safely.
   - Best containment route.
   - Strongest `Whisper Pressure` result.
   - Nim may respect this, resent it, or be divided depending on delay and disposition.

Suggested flags:

- `stonehollow_wounded_prioritized`
- `stonehollow_theorem_cases_secured`
- `stonehollow_corrupt_pages_sealed`

### Phase 3: Nim's Missing Theorem

This is where Nim's optional quest should truly branch rather than wait until a later side room.

The theorem should land as a practical countermeasure theory. It can strengthen later route reading and tempt the party to work closer to resonance.

Resolution families:

#### Preserve The Theorem

- Nim enters later scenes with stronger authority and sharper options.
- Best for late route and Forge leverage.
- Raises contamination risk and Act 3 signal-carry consequences.

Suggested flag:

- `nim_countermeasure_notes`

#### Redact The Theorem

- The party keeps the safe structure but destroys the unstable pieces.
- Hybrid route.
- Good compromise if Nim is trusted but not indulged fully.

Suggested flag:

- `stonehollow_notes_redacted`

#### Burn The Theorem

- Strong containment route.
- Lowest later contamination.
- Can wound Nim's trust if not handled with care.
- Makes certain late special options impossible.

Suggested flag:

- `stonehollow_theorem_burned`

### Phase 4: The Breakout Choice

The lower breakout decides what relationship the campaign has with Stonehollow after the extraction.

#### Civic Resolution: Bring Everyone Out, Even If The Notes Suffer

- Best `Town Stability`.
- Stonehollow becomes a story of rescue and duty.
- Route truth survives, but imperfectly.

Suggested flag:

- `stonehollow_survivors_prioritized`

#### Leverage Resolution: Bring Out The Notes And The One Scholar Who Can Read Them

- Best `Route Control`.
- Strongest Nim route.
- Morally rougher if less useful labor or wounded hands are left with less protection.

Suggested flag:

- `stonehollow_route_truth_preserved`

#### Containment Resolution: Seal The Lower Archive And Accept Partial Loss

- Best `Whisper Pressure`.
- Stonehollow becomes a deliberate sacrifice of knowledge for safety.
- Some route uncertainty stays alive through the whole act.

Suggested flags:

- `stonehollow_archive_sealed`
- `stonehollow_resonance_cut_off`

### Later Payoff Hooks

- `stonehollow_route_truth_preserved` gives cleaner reads in `Broken Prospect`, `Wave Echo Outer Galleries`, or Forge subroutes.
- `nim_countermeasure_notes` can open special late options but worsen contamination tone.
- `stonehollow_archive_sealed` can lower late-act whisper flavor even when the act remains strategically harder.
- `stonehollow_survivors_prioritized` improves town memory of the expedition, even if the route race stays messier.

## Packet 4: Broken Prospect

### Packet Focus

`Broken Prospect` carries threshold ownership, dead labor memory, and the question of who deserves custody.

This packet turns on:

- whether the expedition wants a public claim, a hidden edge, or a denied threshold
- whether Tolan's pragmatism becomes necessary leadership or profitable rot
- whether the old Pact markers are treated as law, salvage, or obstacle

### Branch Axes

| Axis | Civic branch | Leverage branch | Containment branch |
| --- | --- | --- | --- |
| Threshold reading | honor old route law | exploit hidden access | deny tainted passage |
| Rival claimants | expose or disperse them publicly | absorb or blackmail them | leave no workable foothold for anyone |
| Final route state | daylight claim | secret hold | broken but spiritually safer threshold |

### Phase 1: The Shelf Split

The location should open on three usable but differently meaningful branches.

#### Branch 1A: Pact Markers

- Best for reading old law and disciplined access.
- Strong civic and containment branch foundation.
- Helps the player understand what the threshold was supposed to be.

Suggested flag:

- `prospect_markers_decoded`

#### Branch 1B: Dead Wagon Road

- Best Tolan branch.
- Brings caravan memory, survivor guilt, and profitable wrongness to the front.
- Can reveal whether modern claimants have been using old dead as labor-theater.

Suggested flag:

- `prospect_dead_wagon_found`

#### Branch 1C: Rival Blind

- Best leverage route.
- Lets the player interact with human claimants before the site collapses into purely haunted threshold logic.
- Can end in intimidation, bargain, or covert recruitment.

Suggested flag:

- `prospect_rival_blind_reached`

### Phase 2: Tolan's Decision Space

`last_wagon_standing` belongs inside the location's main route logic. It should change how the player reads the whole road.

Tolan should push the player toward one of three readings:

1. Salvage tainted structure because people still need roads.
   - Best leverage route.
   - Strong `Route Control`.
   - Risks normalizing profitable wrongness.
2. Destroy the compromised span so nobody can quietly own it.
   - Best containment route.
   - Strong `Whisper Pressure`.
   - Weakens immediate access.
3. Rebuild only what can be publicly marked and witnessed.
   - Best civic route.
   - Hybrid `Town Stability` plus modest `Route Control`.

Suggested flags:

- `tolan_tainted_span_salvaged`
- `tolan_tainted_span_destroyed`
- `tolan_public_span_rebuilt`

### Phase 3: Rival Claimant Resolution

The rival crew are an ideological fork in miniature. They show the kind of claimant the expedition might become.

Resolution families:

#### Public Exposure

- Name their false stakes and copied claims in daylight.
- Best civic route.
- Helps later sponsor and council scenes.

Suggested flag:

- `prospect_false_claim_public`

#### Coerced Incorporation

- Force them to serve the expedition line under watch.
- Best leverage route.
- Gives faster route labor but worsens moral texture.

Suggested flag:

- `prospect_rivals_absorbed`

#### Drive Everyone Out And Break The Shelf

- Best containment route.
- Nobody gets easy access.
- The expedition reaches Wave Echo slower but cleaner.

Suggested flag:

- `prospect_shelf_denied`

### Phase 4: Dead Foreman's Shift

The boss should still be the dead foreman's shift, but what happens after the fight matters as much as winning it.

#### Civic Resolution: Daylight Claim

- The player marks the threshold publicly, names what was found, and accepts slower but more legitimate access.
- Best `Town Stability`.
- Good `Route Control`, not maximal.

Suggested flag:

- `broken_prospect_daylight_claim`

#### Leverage Resolution: Hidden Approach

- The player keeps the cleanest route private and uses the public shelf as partial misdirection.
- Best `Route Control`.
- Strong later tactical advantage.
- Higher later sponsor distrust if exposed.

Suggested flags:

- `broken_prospect_hidden_approach_kept`
- `broken_prospect_public_map_partial`

#### Containment Resolution: Deny The Threshold

- The player secures only what is necessary, then damages or seals the easy line.
- Best `Whisper Pressure`.
- Makes `Black Lake` or outer-gallery progression harsher but spiritually cleaner.

Suggested flags:

- `broken_prospect_threshold_denied`
- `broken_prospect_dead_shift_quieted`

### Later Payoff Hooks

- `broken_prospect_daylight_claim` helps town-facing legitimacy.
- `broken_prospect_hidden_approach_kept` creates stronger tactical options in outer galleries or Black Lake.
- `broken_prospect_threshold_denied` improves contamination tone but keeps the route race costly.
- Tolan's branch should explicitly color whether the expedition reads as morally practical or spiritually compromised.

## Packet 5: Black Lake Causeway

### Packet Focus

`Black Lake Causeway` is where the act finally asks what victory is for.

This packet turns on:

- whether the player protects sanctity, witnesses, or tactical control first
- whether Irielle's counter-cadence becomes a tool, a doctrine, or a buried mercy
- whether the approach to the Forge is made cleaner, harsher, or more compromised

This is the act's last major branch location before the Forge. Every choice here should expose the party's values in shrine rooms, barracks ledgers, and anchor machinery.

### Branch Axes

| Axis | Civic branch | Leverage branch | Containment branch |
| --- | --- | --- | --- |
| First priority | shrine / survivors / sacred steadiness | barracks / orders / reserve logic | anchors / lake-hum / structural denial |
| Irielle's role | witness and healing counterpoint | teacher of a usable dangerous cadence | advocate for burying what should not spread |
| Final crossing state | defended crossing for people | militarized crossing for advantage | starved, damaged crossing that carries less signal |

### Phase 1: Choose The First Duty

The location already wants shrine, barracks, and anchors. Run them as a fully branching sequence with order-based consequences.

#### Priority A: Drowned Shrine First

Best for:

- `Whisper Pressure`
- Irielle and Elira scenes
- making the crossing spiritually legible

Costs:

- barracks may move or burn documents
- anchors may harden tactically

Suggested flag:

- `black_lake_shrine_first`

#### Priority B: Barracks First

Best for:

- `Route Control`
- reserve-order intelligence
- punishing the Quiet Choir as an organization rather than a spiritual stain

Costs:

- shrine worsens
- witness and survivor texture may suffer

Suggested flag:

- `black_lake_barracks_first`

#### Priority C: Anchors First

Best for:

- immediate tactical safety
- preventing the crossing from becoming a trap
- harder containment style players

Costs:

- you may save structure while losing meaning
- shrine and barracks both degrade while you work on the physical line

Suggested flag:

- `black_lake_anchors_first`

### Phase 2: Internal Branches By Objective

#### Shrine Internal Branch: Irielle's `starved_signal`

The shrine should become a true companion branch packet inside the larger location.

Irielle's options:

1. Teach the counter-cadence.
   - Best leverage route.
   - Helps the Forge.
   - Risks carrying more dangerous knowledge forward.
2. Bury the counter-cadence with the shrine.
   - Best containment route.
   - Cleaner Act 3 handoff.
   - Weaker immediate Forge advantage.
3. Consecrate the shrine without fully teaching or burying.
   - Hybrid civic route.
   - Best for town and survivor memory.

Suggested flags:

- `irielle_counter_cadence_taught`
- `irielle_counter_cadence_buried`
- `black_lake_shrine_consecrated`

#### Barracks Internal Branch: Orders, Witnesses, Or False Orders

The barracks should let the player choose what kind of tactical win they want.

Options:

1. Take the reserve orders cleanly.
   - Best leverage route.
   - Strongest `Route Control`.
2. Free conscripts, porters, or coerced labor first.
   - Best civic route.
   - Strongest `Town Stability`.
3. Plant false orders and let the Choir move wrong.
   - Most complex dirty route.
   - Extremely strong short-term leverage.
   - Can create ugly later consequences if overused.

Suggested flags:

- `black_lake_orders_taken`
- `black_lake_laborers_freed`
- `black_lake_false_orders_planted`

#### Anchors Internal Branch: Break, Hold, Or Retune

The anchor scene should offer break, hold, and retune outcomes.

Options:

1. Break the anchors and destabilize the crossing.
   - Best containment route.
   - Lowers some late-act confidence but can reduce signal integrity.
2. Hold the anchors and make the crossing usable.
   - Best civic route.
   - Lets more people move cleanly later.
3. Retune the anchors to favor your side.
   - Best leverage route.
   - Powerful, but spiritually compromised.
   - Strong parallel to Glasswater's repurpose ending.

Suggested flags:

- `black_lake_anchors_broken`
- `black_lake_anchors_held`
- `black_lake_anchors_retuned`

### Phase 3: Far Landing Resolution

After the three internal objectives, the player should still face one final act-defining choice at the far landing.

#### Civic Resolution: A Crossing For People

- Preserve shrine sanctity where possible.
- Get witnesses and survivors over.
- Secure the far side enough that the expedition does not look like a private war machine.

Best for:

- `Town Stability`
- cleaner post-Black-Lake morale
- a more humane Forge staging tone

Suggested flag:

- `black_lake_people_first_crossing`

#### Leverage Resolution: A Crossing For War

- Hold the far side, keep orders, use retuned anchors or false orders, and enter the Forge with sharper intelligence.
- Best `Route Control`.
- Strongest tactical route into the Forge.
- Also the clearest sign that the expedition is starting to think like the systems it hates.

Suggested flag:

- `black_lake_militarized_crossing`

#### Containment Resolution: A Starved Crossing

- Deny the lake a clean channel, protect against signal carry, and accept a rougher approach into the Forge.
- Best `Whisper Pressure`.
- Weakest immediate tactical outcome.
- Strongest thematic continuity if the player has consistently chosen anti-whisper restraint.

Suggested flag:

- `black_lake_signal_starved`

### Cross-Payoff Conditions

This packet should remember earlier branches aggressively.

- If `agatha_pact_restraint_known`, the shrine can be answered with a deeper Pact reading.
- If `glasswater_relay_route_decoded`, barracks logic becomes easier to parse and false orders become a cleaner option.
- If `act2_captive_outcome` is `many_saved`, a survivor witness can help interpret barracks movement without a hard skill gate.
- If `nim_countermeasure_notes` survived, the anchors or far landing can be read as engineered resonance instead of pure haunting.
- If `broken_prospect_hidden_approach_kept`, the far landing opens with a tactical edge.
- If `broken_prospect_threshold_denied`, the crossing is spiritually cleaner but tactically uglier.

### Later Payoff Hooks

- `black_lake_people_first_crossing` makes the Forge feel like a rescue pushed too far rather than a private crusade.
- `black_lake_militarized_crossing` gives the strongest tactical Forge start, but later companion and Act 3 text should notice the party is starting to keep dangerous systems if they are useful.
- `black_lake_signal_starved` weakens some Forge-side leverage but can materially improve the Act 3 contamination profile.
- `irielle_counter_cadence_taught` should strengthen Forge opening options.
- `irielle_counter_cadence_buried` should weaken the Forge tactically but protect the party from carrying more signal out.

## Suggested Next Implementation Order

If these packets are used for actual content work, the cleanest order is:

1. `Neverwinter Wood Survey Camp`
   - strongest midpoint payoff
   - ties directly into sabotage-night infiltration logic
2. `Broken Prospect`
   - already live, already important, and benefits immediately from a more complex threshold identity
3. `Black Lake Causeway`
   - biggest late-act payoff, but best once earlier branch memories exist
4. `Conyberry and Agatha's Circuit`
   - spiritually important and high-tone-setting, but easier to write once the later payoff destinations are settled
5. `Stonehollow Dig`
   - especially strong once Nim's optional theorem logic is ready to propagate into the Forge and Act 3

## Bottom Line

These location packets should make Act 2 feel less like a line of good dungeons and more like a campaign where every reclaimed site changes what kind of expedition the party is becoming.

Act 2 turns on three outcomes:

- who reaches Wave Echo
- what habits, debts, and compromises they carry to the threshold
- whether they keep resisting the Quiet Choir's worldview or start using its methods with steadier hands
