# Act 1 Dialogue Reference

Status: compiled Act 1 source of truth for player-facing dialogue and social choice options.

Last compiled: 2026-04-21.

This file consolidates implemented Act 1 dialogue options, their required conditions, and their gameplay or story results. It supersedes the Act 1 portions of the older conversation drafts:

- `ACT1_PRE_NEVERWINTER_ELIRA_DRAFT.md`
- `MIRA_NEVERWINTER_DIALOGUE_DRAFT.md`
- `INN_EXPANSION_DRAFT.md`
- `HIGH_ROAD_LIARS_CIRCLE_PUZZLE_DRAFT.md`
- `COMPANION_DIALOGUE_INPUTS_DRAFT.md`
- `COMPANION_CAMP_BANTER_DRAFT.md`
- `BLACKWAKE_IMPLEMENTATION_CHECKLIST.md`

Primary runtime sources:

- `dnd_game/gameplay/story_intro.py`
- `dnd_game/gameplay/story_town_hub.py`
- `dnd_game/gameplay/story_town_services.py`
- `dnd_game/gameplay/story_act1_expanded.py`
- `dnd_game/gameplay/map_system.py`
- `dnd_game/gameplay/interaction_actions.py`
- `dnd_game/data/story/interaction_actions.py`
- `dnd_game/data/story/dialogue_inputs.py`
- `dnd_game/data/story/camp_banter.py`

Notes:

- "Condition" means the flag, quest state, party state, scene state, or Act 1 scenario that makes the option appear.
- "Result" summarizes flags, quest/clue/journal effects, rewards, companion disposition changes, combat setup, and routing.
- If a skill check fails and no special failure is listed, the scene usually continues with less proof, no bonus, or a weaker version of the same information.
- Class and race identity options are one-shot options. They disappear after their corresponding identity flag is set.
- The map-system room handlers are the most detailed implementation for Act 1 dungeon sites. Older linear handlers use many of the same choices; where they differ, the map-system version is treated as canonical here.

## Background Prologues

All background prologues require the matching player background and end at `wayside_luck_shrine`. All successful or combat-resolved routes set `background_prologue_completed`, seed `system_profile_seeded`, clear `background_prologue_pending`, add an opening clue, and route into the shared Act 1 road sequence.

| Background | Condition and scenario | Dialogue options | Results |
| --- | --- | --- | --- |
| Soldier | Player background is `Soldier`; South Barracks runner with stolen dispatches. | `[ATHLETICS] Hit the gate hard before the runner clears the yard.` | DC 11. Success gives player `emboldened` 2 and hero bonus 2 for `South Barracks Breakout`; failure applies `reeling` 1. Victory rewards 15 XP, 6 gp, and a clue that Phandalin attacks are organized. |
| Soldier | Same. | `[INSIGHT] Read the panic and pick the real escape lane.` | DC 11. Success weakens the runner and gives hero bonus 1; victory rewards as above. |
| Soldier | Same. | `[INTIMIDATION] Lock the teamsters in line and make the thief choose fear over speed.` | DC 11. Success frightens the runner 2; victory rewards as above. |
| Acolyte | Player background is `Acolyte`; hospice receives poisoned pilgrim wagon. | `[MEDICINE] Stabilize the poisoned teamster before the details vanish with them.` | DC 11. Success grants `blessed_salve`; combat at `Hospice Gate`; victory rewards 15 XP and a poison/discipline clue. |
| Acolyte | Same. | `[RELIGION] Lead the room in a sharp, steady prayer instead of letting fear set the pace.` | DC 11. Success blesses player 3; victory rewards as above. |
| Acolyte | Same. | `[NATURE] Read the toxin, claw marks, and scent trail outside the hospice gate.` | DC 11. Success applies `reeling` 1 to the wolf; victory rewards as above. |
| Criminal | Player background is `Criminal`; Blacklake warehouse seal deal. | `[DECEPTION] Pose as the collector's actual buyer and turn the meeting sideways.` | DC 12. Success bypasses combat, rewards 30 XP, 12 gp, and forged-seal clue. Failure triggers `Blacklake Warehouse`; victory rewards 10 XP, 6 gp. |
| Criminal | Same. | `[STEALTH] Slip above the warehouse floor and take the satchel before anyone notices.` | DC 12. Success bypasses combat, rewards 30 XP, 8 gp, and seal clue. Failure triggers combat. |
| Criminal | Same. | `[SLEIGHT OF HAND] Lift the ledger and leave the silver where it lies.` | DC 12. Success bypasses combat, rewards 30 XP, 10 gp, and stolen-ore/false-paper clue. Failure triggers combat. |
| Sage | Player background is `Sage`; archive folios are stolen. | `[INVESTIGATION] Follow the corrections, dust, and shelf gaps instead of the panic.` | DC 11. Success grants `focus_ink`, 30 XP, and old-cellar-route clue. Failure triggers `Archive Stair`; victory rewards 10 XP and damaged plan clue. |
| Sage | Same. | `[ARCANA] Decode the sigils and shorthand in the margins before the thief can profit from them.` | DC 11. Same success/failure structure as above. |
| Sage | Same. | `[HISTORY] Reconstruct which ruin-map would matter most to an organized gang.` | DC 11. Same success/failure structure as above. |
| Outlander | Player background is `Outlander`; dawn raid probes camp. | `[SURVIVAL] Set your ground where the tracks say they will come through.` | DC 11. Success gives hero bonus 2; victory rewards 15 XP, 5 gp, and raider-probe clue. |
| Outlander | Same. | `[PERCEPTION] Climb high, count movement, and refuse to be surprised.` | DC 11. Success surprises the wolf; victory rewards as above. |
| Outlander | Same. | `[STEALTH] Ghost into the brush and strike from the line they think is empty.` | DC 11. Success weakens the first enemy and gives hero bonus 1; victory rewards as above. |
| Charlatan | Player background is `Charlatan`; market fixer tries to recruit/coerce the player. | `[DECEPTION] Convince the fixer you already work for someone richer and harder to cross.` | DC 12. Success bypasses combat, rewards 30 XP, 10 gp, and forged-paper clue. Failure triggers `Market Corner`; victory rewards 10 XP, 6 gp. |
| Charlatan | Same. | `[PERFORMANCE] Turn the exchange into a public spectacle the fixer cannot control.` | DC 12. Same success/failure structure as above. |
| Charlatan | Same. | `[INSIGHT] Read what the fixer is really protecting and press there first.` | DC 12. Same success/failure structure as above. |
| Guild Artisan | Player background is `Guild Artisan`; counting-house manifest fraud. | `[INVESTIGATION] Audit the manifests until the missing route shows its shape.` | DC 11. Success grants `camp_stew_jar`, 30 XP, 8 gp, and manipulated-manifest clue. Failure triggers `Counting-House Yard`; victory rewards 10 XP, 4 gp. |
| Guild Artisan | Same. | `[PERSUASION] Settle the room and get the teamsters talking plainly.` | DC 11. Success rewards 30 XP, 6 gp, and hill-watch/teamster clue. Failure triggers combat. |
| Guild Artisan | Same. | `[ATHLETICS] Cut off the crate-haulers trying to leave before questions start.` | DC 11. Success applies `reeling` 1 to the runner; combat follows. |
| Hermit | Player background is `Hermit`; feverish courier collapses at shrine. | `[MEDICINE] Stabilize the courier before whatever hunted them closes the distance.` | DC 11. Success grants `moonmint_drops`; combat at `Wayside Pursuit`; victory rewards 15 XP and Ashfall Watch clue. |
| Hermit | Same. | `[NATURE] Read the spoor and choose where the pursuit will break cover.` | DC 11. Success surprises pursuer; victory rewards as above. |
| Hermit | Same. | `[RELIGION] Treat the courier's warning as omen and pattern, not nonsense.` | DC 11. Success blesses player 2; victory rewards as above. |
| Other background | Player background is not one of the implemented background prologues. | No menu. | Default prologue points the player to Mira Thann and routes to `wayside_luck_shrine`. |

## Wayside And Greywake

### Wayside Luck Shrine

Condition: first shared post-prologue scene; `wayside_luck_shrine_seen` is false. Sets `wayside_luck_shrine_seen`, `wayside_luck_bell_seen`, `elira_first_contact`, and `neverwinter_elira_met`.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[MEDICINE] Stabilize the poisoned drover with Elira.` | Always available on first visit. | DC 8. Sets `wayside_aid_route=wounded` and trust reason `warm_trust`. On success sets `elira_helped`, `wayside_drover_stabilized`, adds ash-bitter poison clue, and rewards 10 XP. Failure still lets Elira save the drover but gives no proof reward. |
| `[RELIGION] Lead Tymora's road-prayer so Elira can keep working.` | Always available. | DC 8. Sets trust reason `spiritual_kinship`. On success sets `elira_helped`, `wayside_prayer_steadied`, rewards 10 XP. Always grants `blessed_salve`. |
| `[INVESTIGATION] Inspect the harness marks and false authority signs.` | Always available. | DC 8. Success sets `elira_helped`, `wayside_false_road_marks_found`, `blackwake_millers_ford_lead`, trust reason `wary_respect`, adds false-roadwarden clue, and rewards 10 XP. Failure sets trust reason `reserved_kindness`. |
| `Keep the shrine moving and save your strength for the road.` | Always available. | Sets trust reason `reserved_kindness`, grants `potion_healing`, no check. |
| `"Come with me. The next wound will be on the road, not at this shrine."` | Appears after the aid choice if Elira is not already a companion. | If `elira_helped` is true, recruitment succeeds. Otherwise requires Persuasion DC 8. Success recruits Elira, sets `elira_pre_neverwinter_recruited`, `elira_neverwinter_recruited`, `elira_first_companion`, and `wayside_luck_bell_promised`; trust can raise Elira disposition. Failure sets `elira_wayside_recruit_failed` and `elira_phandalin_fallback_pending`. |
| `"Stay with them. I will carry your warning to Neverwinter."` | Same recruitment prompt. | Does not recruit Elira; sets `elira_phandalin_fallback_pending`. |

### Greywake Triage Yard

Condition: after Wayside; `greywake_triage_yard_seen` is false. Sets `greywake_triage_yard_seen`, `greywake_outcome_sorting_seen`, and adds a Greywake pre-sorting clue.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[INSIGHT] Challenge the outcome-marked manifest before the clerk can bury it.` | Always available. | DC 9. Success preserves manifest, sets `greywake_outcome_manifest_read`, `greywake_mira_evidence_kind=marked_manifest`, `system_profile_seeded`, `varyn_route_pattern_seen`, and adds pre-sorted-casualty clue. Failure records unverified board. |
| `[MEDICINE] Match the prewritten triage tags against the wounded with Elira.` | Always available. | DC 9. Success sets `greywake_wounded_stabilized`, `greywake_outcome_tags_matched_wounds`, evidence kind `matched_triage_tags`, `system_profile_seeded`, `elira_helped`, rewards 10 XP, and adds tag clue. Failure records unverified board. |
| `[PERSUASION] Make the clerks read the outcome marks aloud before panic swallows them.` | Always available. | DC 9. Success sets `greywake_yard_steadied`, `greywake_sorting_publicly_exposed`, evidence kind `yard_witnesses`, rewards 10 XP, and adds witness clue. Failure records unverified board. |
| `"Then walk with me now. We stop the wound before it reaches the shrine."` | Appears if Elira is not a companion after the yard choice. | Persuasion DC 6 if `elira_helped` or `greywake_wounded_stabilized`, otherwise DC 8. Success recruits Elira and sets `elira_greywake_recruited`, `elira_neverwinter_recruited`, `elira_first_companion`. Failure sets `elira_greywake_recruit_failed` and fallback. |
| `"Stay. If the road brings me back alive, I will find you again."` | Same recruitment prompt. | Does not recruit Elira; sets `elira_phandalin_fallback_pending`. |

### Greywake Road Breakout

Condition: after Greywake Yard. Combat scene against Ashen Brand cutters; routes to `neverwinter_briefing`.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[MEDICINE] Guard the wounded line before the cutters can turn it into leverage.` | Always available. | DC 10. Success sets `greywake_wounded_line_guarded`, adds hero bonus 1, and raises Elira disposition if she is active. |
| `[INVESTIGATION] Seize the manifest runner before the proof disappears.` | Always available. | DC 10. Success sets `greywake_manifest_preserved`, `system_profile_seeded`, `varyn_route_pattern_seen`, adds hero bonus 1, and adds manifest clue. |
| `[INTIMIDATION] Break the attackers' nerve loudly enough for the yard to hear.` | Always available. | DC 10. Success adds hero bonus 2 and frightens first enemy. |
| Flee from combat. | Encounter allows flee. | Sets `greywake_manifest_destroyed`, evidence kind `burned_manifest_corner`, possibly Elira fallback, adds burned-manifest clue, and routes to Mira with weaker proof. |
| Win combat. | Encounter victory. | Sets `greywake_breakout_resolved`, finalizes Mira evidence kind, rewards 25 XP and 8 gp, adds journal note, routes to `neverwinter_briefing`. |

## Mira And Neverwinter

### Mira Briefing Stages

`scene_neverwinter_briefing` uses a dialogue stage:

| Stage | Condition | Return options |
| --- | --- | --- |
| `initial_briefing` | Default before Phandalin arrival and before Blackwake report. | Initial briefing questions, prep stop, contract house, departure. |
| `blackwake_return` | `blackwake_completed` and `blackwake_return_destination == neverwinter`. | `"Blackwake was worse than a side road."`, city-beneficiary question if available, leave south. |
| `phandalin_return` | `phandalin_arrived` and no outer site cleared. | `"Phandalin is worse than your reports."`, city-beneficiary question if available, leave to Phandalin. |
| `mid_act1_return` | `old_owl_well_cleared` or `wyvern_tor_cleared`. | `"The outer sites are not random."`, city-beneficiary question if available, leave. |
| `post_ashfall_return` | `ashfall_watch_cleared`. | `"Ashfall Watch is broken."`, city-beneficiary question if available, leave. |
| `late_act1_return` | `tresendar_cleared` or `emberhall_revealed`. | `"The manor is not just a ruin."`, city-beneficiary question if available, leave. |
| `post_act1_return` | `varyn_body_defeated_act1` or `act1_victory_tier`. | `"Varyn is beaten."`, city-beneficiary question if available, leave. |

### Initial Mira Menu

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `"How is Neverwinter holding together these days?"` | Initial stage; not `briefing_q_neverwinter`. | Sets asked flag, provides city/road stakes, and reacts to Greywake/Blackwake flags. |
| `"Tell me what matters most about Phandalin before I ride."` | Initial stage; not `briefing_q_phandalin`. | Sets asked flag, explains town pressure, stewards, suppliers, shrine, and Stonehill value. |
| `"How dangerous is this Ashen Brand, really?"` | Initial stage; not `briefing_q_brand`. | Sets asked flag, frames Brand as organized logistics rather than raiders; reacts to Wayside, Greywake, Old Owl, Wyvern, and Cinderfall flags. |
| `"What do you make of Greywake?"` | `greywake_outcome_sorting_seen` and not asked. | Sets `mira_q_greywake_initial`, explains Greywake as system proof, reacts to manifest/witness/wounded-line outcomes, adds political pressure context. |
| `"You know Elira Dawnmantle?"` | `elira_first_contact` or Elira companion and not asked. | Sets `mira_q_elira_initial`, gives Elira trust read, reacts to recruitment/fallback/trust reason. |
| `"Who inside the city benefits from this?"` | `neverwinter_private_room_intel`, `neverwinter_contract_house_political_callback`, `false_manifest_circuit` active, or quest completed. | Sets city-beneficiary asked flag, points to corrupt paperwork and officials who normalize wrong paper. |
| `"What do you need from me before I leave?"` | Greywake proof, Blackwake completion, Elira early recruitment, or Elira companion, and not asked. | Sets need asked flag, advises visible/hidden writ use and facts clean enough to pressure officials. |
| `Make one more stop in Neverwinter before riding out.` | Initial stage and not `neverwinter_preparation_done`. | Opens Neverwinter prep choices. |
| `Stop by Oren Vale's contract house.` | Initial stage. | Opens Contract House social hub. |
| `Take the writ and head for the High Road.` | Initial stage. | Opens departure fork. |
| `Return to Phandalin.` / `Take the road south.` | Return stages. | Routes back to Phandalin if arrived, otherwise to the south-road departure. |

### Neverwinter Class Identity Options

Condition: player has the class and has not used the one-shot class identity action in `neverwinter_briefing`.

| Class | Dialogue option | Result |
| --- | --- | --- |
| Barbarian | `[INTIMIDATION] Rest a hand on your weapon and promise to break the gang's spine at the watchtower.` | DC 12. Success rewards 10 XP and clue about fear/shock tactics; failure cools Mira's trust. |
| Bard | `[PERSUASION] "If they're spreading fear, I can answer with a better story and a sharper tongue."` | DC 11. Success rewards 10 XP, 6 gp, and teamster prayer/route clue. |
| Cleric | `[INSIGHT] "Tell me who is suffering first. That's where the road really begins."` | DC 11. Success rewards 10 XP and clue about exhausted families choosing fear over wages. |
| Druid | `[NATURE] "Has the land changed where they strike? Smoke in the brush, foul water, ash on the roots?"` | DC 12. Success rewards 10 XP and clue about blackened scrub/runoff. |
| Fighter | `Lean over the map and ask for approach lanes, numbers, fallback ground, and discipline.` | No check. Rewards 10 XP and scout-perch/timing clue. |
| Monk | `[INSIGHT] "Slow down. Give me only what someone actually saw, not what fear made louder afterward."` | DC 12. Success rewards 10 XP and witness-pattern clue. |
| Paladin | `"Then I give you my word: this road will not stay in their hands."` | No check. Rewards 10 XP, 8 gp, and disciplined-leadership warning. |
| Ranger | `[SURVIVAL] Ask for ridge lines, blind turns, and places scouts vanish.` | DC 11. Success rewards 10 XP and clue about observer/retreat terrain. |
| Rogue | `[DECEPTION] "Smug little operation, then. The sort of crew that mistakes being organized for being untouchable."` | DC 12. Success rewards 10 XP, 4 gp, and stolen-ore clue. |
| Sorcerer | `[ARCANA] "If they're nesting in old ruins, show me the places where old stone and bad ambition start talking to each other."` | DC 12. Success rewards 10 XP and old-site/hidden-chamber clue. |
| Warlock | `[INTIMIDATION] "Fear leaves a shape behind. So does greed. Which one do these people kneel to first?"` | DC 12. Success rewards 6 XP and clue that profit comes first, fear protects it. |
| Wizard | `[INVESTIGATION] Ask for the original reports instead of the polished summary and compare repeats.` | DC 11. Success rewards 10 XP and repeated route/timing clue. |

### Neverwinter Preparation

Condition: player chooses a prep stop and `neverwinter_preparation_done` is false. All options set `neverwinter_preparation_done`.

| Dialogue option | Result |
| --- | --- |
| `[INVESTIGATION] Review missing-ledger fragments with Mira's clerk.` | DC 12. Success sets `system_profile_seeded`, `varyn_route_pattern_seen`, adds clue, rewards 15 XP and 8 gp. |
| `[RELIGION] Ask for a road blessing before departure.` | DC 12. Always grants `potion_healing`; success rewards 10 XP. |
| `[PERSUASION] Talk with teamsters and dockhands before the road.` | DC 12. Success adds stolen-ore clue, rewards 15 XP and 12 gp; failure gives 4 gp. |
| `Skip the extra stop and keep momentum.` | No reward or clue. |

### Contract House

Condition: player chooses Oren Vale's contract house from Mira's initial menu or equivalent return. Contract House choices can seed the false-manifest circuit, Blackwake leads, and city-side political callbacks.

| Area/NPC | Dialogue option | Required condition | Result |
| --- | --- | --- | --- |
| Oren Vale | Ask about the false manifest detail. | Quest/context active and not `false_manifest_oren_detail`. | Insight DC 12. Success sets `false_manifest_oren_detail` and adds contract-house proof. |
| Oren Vale | Ask about the private room. | Private room quest/reward available. | Points toward the private room scene. |
| Oren Vale | Ask about Mira. | Always while in Oren loop. | Gives Neverwinter liaison context. |
| Sabra Kestrel | Turn in or discuss the false-manifest circuit. | Quest ready/active. | Advances or completes `false_manifest_circuit`; can add corrected manifest proof. |
| Sabra Kestrel | Ask which ledger line is wrong. | Quest not granted. | Grants `false_manifest_circuit`. |
| Sabra Kestrel | Ask what she fears. | Not already asked. | Adds clue about paperwork being weaponized. |
| Vessa | Ask for the buyer phrase or card-table read. | Not already resolved. | Sleight of Hand DC 12. Success sets `neverwinter_smuggler_phrase_known`, rewards 10 XP and 8 gp, or primes `neverwinter_ash_in_the_ale_ready`. |
| Vessa | Use Liar's Blessing at the table. | `liars_blessing_active`. | Auto gains phrase/proof, rewards 10 XP and 4 gp. |
| Vessa | Ask about smoke near the river cut. | Not already asked. | Sets `blackwake_millers_ford_lead`. |
| Garren Flint | Ask for roadwarden cadence detail. | Not `false_manifest_garren_detail`. | Persuasion DC 12. Success sets `false_manifest_garren_detail`, `road_patrol_writ`, and route proof. |
| Garren Flint | Ask about route pressure. | Not already asked. | Sets `blackwake_gallows_copse_lead`. |
| Garren Flint | Pressure him hard. | Not already resolved. | Intimidation DC 12. Success gives Gallows lead; failure can trigger `Ash In The Ale`. |
| Ash In The Ale | Persuasion, Insight, Sleight of Hand, Intimidation, or Athletics. | `neverwinter_ash_in_the_ale_ready`. | DC 12. Success raises `neverwinter_oren_trust`, sets `blackwake_neverwinter_rumor`, rewards 15 XP and 6 gp. Failure applies `reeling` 1. |
| Ash In The Ale | Let the room settle. | Same. | Resolves without the stronger success reward. |
| Private room | `[INVESTIGATION]` review route papers. | Private room access. | DC 12. Success sets private-room intel and Blackwake leads. |
| Private room | `[INSIGHT]` read booking/cadence mismatch. | Private room access. | DC 12. Success sets `neverwinter_private_room_intel`, adds proof, rewards 10-15 XP. |
| Private room | `[PERSUASION]` press a witness. | Private room access. | DC 12. Success sets lead/proof flags. |
| Private room | Liar's Blessing route. | `liars_blessing_active`. | Auto success; sets private-room intel and route clue. |

### Departure Fork

Condition: player chooses to take the writ and leave.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| Recruit Kaelis Starling. | `early_companion_recruited` is false. | Recruits Kaelis and sets early companion flag. |
| Recruit Rhogar Valeguard. | `early_companion_recruited` is false. | Recruits Rhogar and sets early companion flag. |
| Ride south on the High Road. | Always after companion prompt. | Routes to `road_ambush`. |
| Investigate smoke near Blackwake Crossing. | Always from fork. | Sets `blackwake_started`, `blackwake_return_destination=undecided`, grants `trace_blackwake_cell`, routes to `blackwake_crossing`. |
| Circle back for one more rumor. | Available from fork. | If prep not done, opens prep; otherwise sets/uses `blackwake_neverwinter_rumor` and returns to the fork. |

## Blackwake Crossing

Condition: chosen from departure fork before Phandalin. `scene_blackwake_crossing` runs the Blackwake dungeon map; completion returns to `road_decision_post_blackwake`.

### Tollhouse And Mid-Routes

| Room/scenario | Dialogue option | Required condition | Result |
| --- | --- | --- | --- |
| Charred Tollhouse | `[INVESTIGATION] Reconstruct what was taken from the inspection room.` | Blackwake entry. | DC 12. Success sets `blackwake_millers_ford_lead`, adds Miller's Ford clue, weakens saboteur, hero bonus +1. Failure still adds route-authority clue. |
| Charred Tollhouse | `[MEDICINE] Stabilize a burned guard before their testimony fades.` | Entry. | DC 12. Success sets `blackwake_gallows_copse_lead`, increments `blackwake_survivors_saved`, adds prisoner-route clue, Rhogar +1. |
| Charred Tollhouse | `[INTIMIDATION] Force a panicked mercenary to stop babbling and name facts.` | Entry. | DC 12. Success sets Miller's Ford lead, frightens saboteur, hero bonus +1; failure applies player `reeling` 1. |
| Charred Tollhouse | `[PERSUASION] Calm the survivors and organize clean testimony.` | Entry. | DC 12. Success sets Gallows lead, saves survivor, Elira +1, avoids fight. Failure leads to fight. Victory rewards 15 XP and 6 gp. |
| Miller's Ford approach | `[SURVIVAL] Cross safely and find the flank through the shallows.` | Tollhouse complete and Ford route reached. | DC 12. Success sets `blackwake_ford_flank`. |
| Miller's Ford approach | `[ANIMAL HANDLING] Calm the trapped horse teams before panic breaks them.` | Same. | DC 12. Success saves survivor, sets `blackwake_horse_teams_saved`, Rhogar +1. |
| Miller's Ford approach | `[STEALTH] Survey the false checkpoint before anyone notices you.` | Same. | DC 12. Success sets `blackwake_ford_surveyed`, Kaelis +1. |
| Wagon Snarl | `Cut civilians free before cargo or cover.` | Ford cluster. | Saves 2 survivors, sets support ready, Elira +1. |
| Wagon Snarl | `Secure the cargo before the smugglers can move it.` | Ford cluster. | Sets `blackwake_cargo_secured`, rewards 8 gp. |
| Wagon Snarl | `Overturn carts for cover and prepare an ambush.` | Ford cluster. | Sets `blackwake_ford_ambush_prepared`, improves later fight. |
| Reedbank Camp | `[STEALTH] Steal the seal kit and papers quietly.` | Ford cluster. | DC 12. Success sets `blackwake_route_permits_found`, `blackwake_forged_papers_found`, adds forged-route clue, Bryn +1. |
| Reedbank Camp | `[INTIMIDATION] Drag the lookout behind the reeds and make them talk.` | Ford cluster. | DC 12. Success sets `blackwake_lookout_interrogated`, adds Neverwinter-side corruption clue. |
| Reedbank Camp | `[INVESTIGATION] Copy the names and route marks before disturbing anything.` | Ford cluster. | DC 12. Success sets `blackwake_route_names_copied`, `blackwake_forged_papers_found`, adds paymaster mark clue. |
| Ford Ledger Post | `[DECEPTION] Pose as higher authority and order the seizure halted.` | Ford finale. | DC 13. Success avoids fight, sets forged papers, Bryn +1. |
| Ford Ledger Post | `[PERSUASION] Split the hired guards from the true loyalists.` | Ford finale. | DC 13. Success reduces enemies and adds hero bonus. |
| Ford Ledger Post | `[ATHLETICS] Rush the barricade before they settle behind it.` | Ford finale. | DC 12. Success knocks first enemy prone and adds hero bonus 2. |
| Ford Ledger Post | `[INVESTIGATION] Use the seized ledgers to expose the fraud publicly.` | Ford finale. | DC 12. Success avoids fight, sets forged papers, adds selective-theft clue. Victory rewards 20 XP and 8 gp. |
| Gallows Hanging Path | `[RELIGION] Read whether the symbols are true rite or staged fear.` | Tollhouse complete and Gallows route reached. | DC 12. Success sets `blackwake_fear_symbols_staged`. |
| Gallows Hanging Path | `[PERCEPTION] Detect hidden sentries before they decide the route.` | Same. | DC 12. Success sets `blackwake_copse_sentries_spotted`. |
| Gallows Hanging Path | `[STEALTH] Approach without triggering the copse alarm.` | Same. | DC 12. Success sets `blackwake_copse_alarm_prevented`, Kaelis +1; failure sets alarm triggered. |
| Cage Clearing | `Free the captives now.` | Gallows cluster. | Saves 2 survivors, sets `blackwake_captive_support_ready`, Elira +1. |
| Cage Clearing | `Question the captives before cutting cages loose.` | Gallows cluster. | Sets `blackwake_transfer_pattern_learned`, adds cave/floodgate clue. |
| Cage Clearing | `Stay hidden and observe the next transfer pattern.` | Gallows cluster. | Sets transfer pattern and alarm prevention, Elira -1. |
| Watcher Tree | `[ATHLETICS] Climb and scout the transfer route.` | Gallows cluster. | DC 12. Success sets `blackwake_cavern_route_scouted`. |
| Watcher Tree | `Cut down the warning charms before they can be checked.` | Gallows cluster. | Sets `blackwake_copse_alarm_prevented`. |
| Watcher Tree | `[SURVIVAL] Leave the charms untouched and track who checks them.` | Gallows cluster. | DC 12. Success sets `blackwake_transfer_tail` and adds crate-tag clue. |
| Root Cellar Hollow | `Inspect the transfer crates.` | Gallows cluster. | Sets `blackwake_soot_crate_route_found`, adds seized-goods logistics clue. |
| Root Cellar Hollow | `[INVESTIGATION] Decode the route symbols.` | Gallows cluster. | DC 12. Success sets `blackwake_transfer_list_found`, adds southbound staging clue. |
| Root Cellar Hollow | `[ATHLETICS] Force open the hidden cellar door.` | Gallows cluster. | DC 12. Success sets transfer list and rewards 6 gp. Room completion always sets `blackwake_transfer_list_found`. |

### Store Cavern And Sereth

| Room/scenario | Dialogue option | Required condition | Result |
| --- | --- | --- | --- |
| Outer Cache | `[STEALTH] Slip through the loading shadow and bypass the front watch.` | Store cavern unlocked by route evidence. | DC 13. Success damages/surprises guard, hero bonus +2, Kaelis +1. |
| Outer Cache | `[DECEPTION] Enter as caravan inspectors using the forged papers.` | Best if `blackwake_forged_papers_found`. | DC 13 with forged papers. Success avoids fight, Bryn +1. Failure sets `blackwake_cache_alarm_triggered`. |
| Outer Cache | `[ATHLETICS] Break through the outer cache before they seal the passage.` | Store cavern. | DC 13. Success emboldens player and adds hero bonus. |
| Prison Pens | `Free prisoners quietly.` | Prison room reached. | Sets `blackwake_prisoners_freed_early`, saves 2 survivors, Elira +1. |
| Prison Pens | `Arm prisoners for an uprising.` | Prison room. | Sets `blackwake_prisoner_uprising`, saves 1 survivor, adds finale hero bonus. |
| Prison Pens | `Leave them until Sereth is handled to preserve stealth.` | Prison room. | Sets `blackwake_prisoners_delayed`, Elira -1. |
| Seal Workshop | `Seize the forgeries as evidence.` | Workshop reached. | Sets `blackwake_evidence_secured`, `blackwake_forged_papers_found`, adds seal-workshop clue. |
| Seal Workshop | `Destroy the workshop.` | Workshop. | Sets `blackwake_workshop_destroyed`, reduces `act1_ashen_strength` by 1. |
| Seal Workshop | `[INVESTIGATION] Copy names and route marks before sabotage.` | Workshop. | DC 13. Success sets copied names and evidence; always destroys workshop afterward. |
| Ash Office | `Trace the Phandalin pressure sites.` | Office reached. | Sets `blackwake_phandalin_pressure_clue`, adds Phandalin supply-timing clue. |
| Ash Office | `Read the caravan hijack summaries.` | Office. | Sets `blackwake_caravan_hijack_clue`, adds selective-theft clue. |
| Ash Office | `Search for the southern supervisor note.` | Office. | Sets `blackwake_hobgoblin_supervision_clue`, foreshadows High Road/Ashfall chain. |
| Floodgate Chamber | `[PERSUASION] Offer prisoners for Sereth's safe withdrawal.` | Sereth finale. | DC 14. Success sets `blackwake_partial_prisoner_surrender`, reels Sereth, hero bonus +1. Failure burns evidence. |
| Floodgate Chamber | `[INTIMIDATION] Threaten full exposure and a slaughtered supply line.` | Finale. | DC 14. Success frightens Sereth and hero bonus +2. Failure sets floodgate hazard. |
| Floodgate Chamber | `[INVESTIGATION] Confront Sereth with specific ledger facts.` | `blackwake_forged_papers_found` or `blackwake_transfer_list_found`. | DC 13. Success sets Sereth fate `captured`, reels Sereth 2, hero bonus +2. Failure burns evidence. |
| Floodgate Chamber | `[DECEPTION] Pretend to represent higher Ashen Brand authority.` | `blackwake_forged_papers_found`. | DC 14. Success removes a guard if present, hero bonus +1, Bryn +1. Failure sets enemy ambush advantage. |
| Floodgate Chamber | `[CONTRACT HOUSE INTEL] Name the booking, manifest, and false cadence at once.` | `neverwinter_private_room_intel`. | Auto success. Sets Sereth fate `captured`, reels Sereth 2, surprises guard, adds Oren/Sabra/Garren proof clue, hero bonus +2. |
| Floodgate Chamber | `Strike immediately before Sereth can spoil the room.` | Finale. | No check. Hero bonus +1. |
| Final collapse choice | `Save the prisoners and survivors first.` | After Sereth victory. | Sets `blackwake_resolution=rescue`, saves 3 more survivors, Elira +2, Rhogar +1, grants `potion_healing`, rewards 35 XP and 8 gp. |
| Final collapse choice | `Secure the ledgers and seal workshop.` | After Sereth victory. | Sets `blackwake_resolution=evidence`, `blackwake_evidence_secured`, `blackwake_ledgers_secured`, Bryn +1, Elira -1, rewards 35 XP and 22 gp, adds route-corruption proof. |
| Final collapse choice | `Sabotage the entire cache and floodgate.` | After Sereth victory. | Sets `blackwake_resolution=sabotage`, `blackwake_cache_sabotaged`, reduces `act1_ashen_strength` by 1, Kaelis +1, Bryn -1, grants `antitoxin_vial`, rewards 35 XP and 6 gp. |

### Post-Blackwake Decision

Condition: `blackwake_completed`.

| Dialogue option | Result |
| --- | --- |
| Report to Neverwinter. | Sets `blackwake_return_destination=neverwinter`, returns to Mira's Blackwake report stage. |
| Press south toward Phandalin. | Sets return destination south and routes to `road_ambush`. |
| Camp first. | Opens camp, then returns to the Blackwake decision. |

## High Road

### High Road Milehouse

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[INVESTIGATION] Expose the false writs.` | Milehouse/road approach. | DC 12. Success sets `neverwinter_false_writs_spotted`, `blackwake_millers_ford_lead`, `road_patrol_writ`, weakens enemies, hero bonus +1, clue. |
| `[SURVIVAL] Read the woodline path.` | Same. | DC 12. Success sets `neverwinter_woodline_path`, `road_ambush_scouted`, surprises enemy, hero bonus +1. |
| `[PERSUASION] Guard the pilgrims.` | Same. | DC 12. Success sets `neverwinter_pilgrims_guarded`, `blackwake_gallows_copse_lead`, hero bonus +1, Elira +1. |
| Flee/skip. | Encounter allows flee. | Sets `neverwinter_milehouse_bypassed`. |
| Win. | Encounter victory. | Rewards 20 XP and 5 gp. |

### Signal Cairn

| Dialogue option | Result |
| --- | --- |
| `[STEALTH] Cut the firekeeper off quietly.` | DC 12. Success sets `road_reinforcement_signal_cut`, surprises enemy, hero bonus +1. |
| `[SURVIVAL] Read fuel and trail.` | DC 12. Success sets signal cut and `road_second_wave_trail_read`, adds clue, hero bonus +1. |
| `[ARCANA] Read the ash-cloth signal.` | DC 12. Success sets signal cut and `road_ash_signal_understood`, weakens enemy, hero bonus +1. |
| Flee/skip. | Sets `neverwinter_signal_cairn_bypassed`. |
| Win. | Rewards 15 XP and 4 gp. |

### Road Ambush

Condition: party rides south from Neverwinter or post-Blackwake decision.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[ATHLETICS] Charge the first ambush line.` | First wave not cleared. | DC 12. Success emboldens player 2, knocks enemy prone, hero bonus +2; failure applies `reeling`. |
| `[STEALTH] Flank through the brush.` | First wave not cleared. | DC 12. Success weakens/surprises enemy, hero bonus +2; failure applies `reeling`. |
| `[INTIMIDATION] Warn them off loudly.` | First wave not cleared. | DC 12. Success weakens/frightens enemy; failure emboldens enemies. |
| `"If you can stand, stand with us."` | After wave one, Tolan rescue prompt. | Recruits Tolan and clears waiting flag. |
| `"Get to the inn. If we live, I will find you there."` | Same prompt. | Sets `tolan_waiting_at_inn`; Tolan can be recruited at Stonehill. |
| Second wave combat. | After wave one. | Signal/route flags affect difficulty. Victory sets `road_ambush_wave_two_cleared`, then `road_ambush_cleared`, adds hobgoblin/Ashfall clue, rewards 20 XP and 7 gp, and unlocks side branches. |

### Cleared High Road Travel Menu

Condition: `road_ambush_cleared`.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| Follow the High Road to Phandalin. | Always. | Routes to `phandalin_hub`. |
| Backtrack to the previous route node. | Backtrack history exists. | Returns to previous meaningful route node. |
| Follow the overgrown statue trail into the wilderness. | `liars_circle_branch_available` and puzzle not solved/failed/locked. | Routes to `high_road_liars_circle`. |
| Investigate the broken roadwarden milemarker. | False checkpoint branch available. | Routes to false checkpoint. |
| Challenge the false tollstones. | False tollstones branch available. | Routes to false tollstones. |

### Liar's Circle

Condition: optional side branch unlocked after road ambush; unavailable after solved, failed, or locked.

| Dialogue option | Result |
| --- | --- |
| `Inspect the Knight.` | Replays/marks Knight statement: if the Priest is lying, the King is telling the truth. |
| `Inspect the Priest.` | Replays/marks Priest statement: exactly one of the Knight or King is telling the truth. |
| `Inspect the Thief.` | Replays/marks Thief statement: exactly one of the Priest or Thief is telling the truth. |
| `Inspect the King.` | Replays/marks King statement: the Priest is lying iff the King is telling the truth. |
| `Name the statue that tells the truth.` | Opens answer prompt. |
| `Leave the circle.` | Leaves without reward, curse, or lock. |
| Answer `Knight`, `Priest`, or `King`. | Sets `liars_circle_failed`, `liars_circle_locked`, applies Liar's Curse until long rest: Deception -1 and Persuasion -1. |
| Answer `Thief`. | Sets `liars_circle_solved`, applies Liar's Blessing until death: Deception +2 and Persuasion +1, rewards 200 XP. |
| `Say nothing yet.` | Returns to inspection without resolving. |

### False Roadwarden Checkpoint

Condition: branch available and not resolved. Contract proof appears if private-room intel or enough false-manifest detail exists.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[CONTRACT HOUSE PROOF] Use contract-house proof.` | Contract proof available. | Auto success. Exposes checkpoint, sets Blackwake leads, rewards 30 XP and 14 gp, adds proof clue/journal. |
| `[DECEPTION] Bluff through the false authority.` | Always. | DC 13. Success resolves, rewards 20 XP and 10 gp. |
| `[INSIGHT] Read who knows the writ is false.` | Always. | DC 12. Success resolves, rewards 20 XP and 8 gp. |
| `[PERSUASION] Split frightened hands from guilty ones.` | Always. | DC 13. Success sets `high_road_false_checkpoint_hands_spared`, rewards 20 XP and 6 gp. |
| `[INTIMIDATION] Break the checkpoint's nerve.` | Always. | DC 13. Success resolves, rewards 20 XP and 8 gp. |
| Comply or fail. | On failed/soft route. | Pays up to 6 gp, applies `reeling`, leaves journal pressure. |

### False Tollstones

Condition: branch available and not resolved.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[LIAR'S BLESSING] Use the blessing to speak the right passphrase.` | `liars_blessing_active`. | Auto success. Sets blessing-used flag, obtains passphrase/ledger/antitoxin, rewards 25 XP and 16 gp, adds clue. |
| `[DECEPTION] Sell the wrong toll answer cleanly.` | Always; DC lower if blessing active. | DC 14, or DC 12 with blessing. Success gets ledger/antitoxin/clue, rewards 20 XP and 12 gp. |
| `[PERSUASION] Turn the contact without burning them.` | Always; DC lower if blessing active. | DC 13, or DC 11 with blessing. Success spares contact, adds clue, rewards 20 XP and 10 gp. |
| Leave. | Always. | Branch remains unresolved. |
| Fail. | Failed check. | Spotters scatter, player gains `reeling`, journal notes the missed branch. |

## Phandalin Hub

### First Arrival

Condition: first time in `phandalin_hub`; `phandalin_arrived` is false.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[INSIGHT] "I want to read the mood of the town before I speak."` | Always on arrival. | DC 12. Success adds town-fear direction clue and rewards 10 XP. |
| `[PERSUASION] "Let them know Neverwinter sent help."` | Always. | DC 12. Success steadies crowd, rewards 10 XP and 6 gp. |
| `[INVESTIGATION] Survey the tracks, barricades, and weak points first.` | Always. | DC 12. Success adds wagon-ruts/weak-points clue and rewards 10 XP. |
| Race identity option. | Player race has a one-shot Phandalin arrival option. | See race identity table below. |

### Phandalin Race Identity Options

Condition: player has the race and has not used the one-shot race identity action in `phandalin_arrival`.

| Race | Dialogue option | Result |
| --- | --- | --- |
| Forged | `[INTIMIDATION] "Enough staring. Point me at who needs help first."` | DC 12. Success rewards 10 XP, 4 gp, and old manor-side lane clue. |
| Dwarf | `[INVESTIGATION] Run a hand along the old stonework and ask which buried foundations the raiders favor.` | DC 11. Success rewards 10 XP and cellar-route clue. |
| Elf | `[INSIGHT] "This place still remembers the older town beneath it. Tell me which ruins people no longer trust."` | DC 11. Success rewards 10 XP and manor-ruins clue. |
| Unrecorded | `[INVESTIGATION] Crouch by the nearest barricade and point out exactly where it would fail.` | DC 11. Success rewards 10 XP and barricade/manor-lane clue. |
| Riverfolk | `[ATHLETICS] Shoulder a sagging beam back into place before asking any questions.` | DC 11. Success rewards 10 XP, 6 gp, and late-night manor movement clue. |
| Astral Elf | `[PERSUASION] "I'm not here to be one more voice speaking over you. Start with what you need answered first."` | DC 10. Success rewards 10 XP, 4 gp, and old manor-side lane clue. |
| Orc-Blooded | `[INTIMIDATION] Step into the lane, plant your feet, and demand the truth instead of whispers.` | DC 12. Success rewards 8 XP and watched-lanes clue. |
| Halfling | `[PERSUASION] "Easy now. You only get to panic after you tell me where the trouble actually starts."` | DC 11. Success rewards 10 XP, 6 gp, and manor-side trouble clue. |
| Human | `[PERSUASION] "I'm road-worn, underpaid, and short on patience, so let's skip the theater and help each other."` | DC 11. Success rewards 10 XP, 4 gp, and practical-trust clue. |
| Orc | `[INTIMIDATION] Bark at the nearest knot of onlookers to stop gawking and start naming where the road is bleeding.` | DC 12. Success rewards 8 XP and manor/foundation clue. |
| Fire-Blooded | `[DECEPTION] "If we're done deciding whether I look ominous enough to trust, tell me where your real trouble starts."` | DC 11. Success rewards 10 XP and watched-lane clue. |

### Phandalin Travel Menu

Condition: after arrival or on return to town.

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Report to Steward Tessa Harrow` | Steward interactions remain. | Opens steward loop. |
| `Visit the Stonehill Inn` | Always. | Opens Stonehill loop. |
| `Stop by the shrine of Tymora` | Shrine interactions remain. | Opens shrine loop. |
| `[TRADE] Browse Barthen's Provisions` | Always. | Opens Barthen loop/shop. |
| `[TRADE] Call on Linene Graywind at the Lionshield trading post` | Always. | Opens Linene loop/shop. |
| `Walk the old walls of Edermath Orchard` | Orchard interactions remain. | Opens Daran/Edermath loop. |
| `Step into the Miner's Exchange` | Exchange interactions remain. | Opens Halia loop. |
| `Return to camp` | Always. | Opens camp menu. |
| `Take a short rest` | Always. | Short rest. |
| `Investigate Old Owl Well` | Lead available or already allowed. | Routes to Old Owl Well. |
| `Investigate Old Owl Well (need a lead)` | No lead yet. | Disabled/informational style choice; town remains hub. |
| `Hunt the raiders at Wyvern Tor` | Lead available or already allowed. | Routes to Wyvern Tor; if under recommended level, warning appears. |
| `Hunt the raiders at Wyvern Tor (need a lead)` | No lead yet. | Disabled/informational style choice. |
| `Ride for Ashfall Watch` | Old Owl and Wyvern cleared, or enough clues in legacy flow. | Routes to Ashfall Watch. |
| `Ride for Ashfall Watch (clear Old Owl Well and Wyvern Tor first)` | Prereqs missing. | Disabled/informational style choice. |
| `Descend beneath Tresendar Manor` | Revealed after Ashfall/lantern vigil. | Routes to Tresendar. |
| `Descend beneath Tresendar Manor (wait for a firmer lead)` | Prereqs missing. | Disabled/informational style choice. |
| `Descend into Emberhall Cellars` | `emberhall_revealed`. | Routes to finale. |

### Wyvern Tor Level Warning

Condition: choosing Wyvern Tor while below recommended level.

| Dialogue option | Result |
| --- | --- |
| `Ride for Wyvern Tor anyway.` | Routes to Wyvern Tor despite warning. |
| `Wait and come back at level N.` | Returns to Phandalin menu. |

## Phandalin Town NPCs

### Steward Tessa Harrow

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Tessa what happened at Ashfall Watch.` | `secure_miners_road` ready. | Turns in quest. |
| `"Where is the Ashen Brand hurting you the most?"` | Not asked. | Adds Ashfall/cellar-route clue, grants `secure_miners_road`. |
| `"Tell me about the old ruins around town."` | Not asked. | Explains old foundations/cellar threat. |
| `Share what happened at Blackwake Crossing.` | `blackwake_completed` and not asked. | Reacts by `blackwake_resolution`; evidence grants 8 gp and proof clue, rescue adds survivor journal, sabotage adds supply-pressure clue; escaped Sereth warning if relevant; fires `steward_blackwake` companion input. |
| `"I'll break their grip on Phandalin."` | `secure_miners_road` active and vow not made. | Sets `steward_vow_made`, fires `steward_vow` companion input. |
| `Leave Tessa to her work and move on.` | Always. | Returns to town hub. |

### Shrine Of Tymora

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `[MEDICINE] "Let me examine the poisoned miner."` | Elira not already active from Neverwinter; not attempted. | DC 8. Success sets `elira_helped`, rewards 10 XP; failure still leaves care with Elira. |
| `[RELIGION] "I'll offer a prayer with you."` | Same. | DC 8. Success sets `elira_helped`, rewards 10 XP. |
| `"What have you learned about the raiders?"` | Not asked. | Adds clue that Brand uses ash-bitter poison and disciplined tactics. |
| `"Come with me. Phandalin needs you in the field."` | Elira not a companion, recruitment not attempted. | Auto succeeds if `elira_helped` or fallback pending; otherwise Persuasion DC 8. Success recruits Elira and sets Phandalin recruitment/fallback flags. |
| `Give Elira a moment to tend the shrine.` | Elira companion. | Return to hub. |
| `Step back and leave Elira to her work.` | Elira not companion. | Return to hub. |

If Elira was recruited before Neverwinter, the shrine has no menu on first visit; it adds a clue from Elira's triage notes and returns.

### Barthen's Provisions

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Barthen the watchtower road is open again.` | `restore_barthen_supplies` ready. | Turns in quest. |
| `"What does Phandalin run short on first when the road turns bad?"` | Not asked. | Grants `restore_barthen_supplies`, fires `barthen_shortage` companion input. |
| `[TRADE] Check the shelves for provisions and trail gear.` | Always. | Opens Barthen shop. |
| `Leave the provision house.` | Always. | Returns to town hub. |

### Lionshield Coster

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Report that Ashfall Watch has been broken.` | `reopen_lionshield_trade` ready. | Turns in quest. |
| `"How badly are the raiders strangling trade?"` | Not asked. | Adds trade/Ashfall clue, grants `reopen_lionshield_trade`, fires `lionshield_trade` companion input. |
| `[TRADE] Lay out the party's goods and talk prices.` | Always. | Opens Linene shop. |
| `Leave the trading post.` | Always. | Returns to town hub. |

### Edermath Orchard

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Daran what happened at Wyvern Tor.` | `break_wyvern_tor_raiders` ready. | Turns in quest. |
| `[NATURE] "Something is wrong with these trees. Let me see what the ash is doing."` | Blight not checked. | DC 12. Success adds orchard sabotage clue, grants `moonmint_drops`, rewards 10 XP. |
| `"You look like someone who knows the hills. What is happening at Wyvern Tor?"` | Not asked. | Sets orchard lead, adds Wyvern Tor clue, grants `break_wyvern_tor_raiders`. |
| `[ATHLETICS] "If you still drill, put me through a frontier warm-up."` | Training not done. | DC 12. Success rewards 10 XP and two `travel_biscuits`. |
| `[STEALTH] "If your old cache is still buried, we can reach it quietly."` | Cache not recovered. | DC 12. Success quietly recovers cache; failure triggers orchard watcher fight. Reward is `edermath_cache_compass`, 35 XP, 12 gp, Daran trust, Act 2 route hook. |
| `Leave the orchard and head back toward town.` | Always. | Returns to hub. |

### Miner's Exchange

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Halia the threat at Old Owl Well has been dealt with.` | `silence_old_owl_well` ready. | Turns in quest. |
| `"Which crews are missing, and where did they vanish?"` | Not asked. | Sets exchange lead, adds Old Owl clue, grants `silence_old_owl_well`. |
| `[INVESTIGATION] "Let me look at the tally books. Somebody is getting paid for this chaos."` | Ledgers not checked. | DC 12. Success adds Old Owl logistics clue and rewards 10 XP. |
| `[PERSUASION] "You two can stop shouting. Tell me what happened, and one of you gets to be right."` | Dispute not resolved. | DC 12. Success rewards 10 XP and 8 gp. |
| `Leave the exchange and step back into town.` | Always. | Returns to hub. |

## Stonehill Inn

### Common Room Menu

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `"Mind if I buy you a drink and ask a few questions?"` | Not asked. | Introduces Bryn and her role. |
| `"Tell me what the roads are saying about the Ashen Brand."` | Not asked. | Adds clue that Ashfall Watch is the field base. |
| `"What are people saying about Blackwake Crossing?"` | `blackwake_completed` and not asked. | Reacts by Blackwake resolution and escaped Sereth. |
| `Tell Mara Stonehill what you found about the marked keg.` | `marked_keg_investigation` ready. | Opens Mara turn-in. |
| `Talk to Mara Stonehill, who is keeping half the room from a fight.` | Mara interactions remain. | Opens Mara loop. |
| `Sit with Jerek Harl and hear what anger has left him.` | Jerek interactions remain. | Opens Jerek loop. |
| `Bring Sella Quill the three true details she asked for.` | `songs_for_the_missing` ready. | Opens Sella turn-in. |
| `Listen to Sella Quill and the room she keeps half-honest.` | Sella interactions remain. | Opens Sella loop. |
| `Hear Old Tam Veller out over his cooling cup.` | Tam interactions remain. | Opens Tam loop. |
| `Report the quiet-table scheme to Nera Doss.` | `quiet_table_sharp_knives` ready. | Opens Nera turn-in. |
| `[MEDICINE] "Let me look at that split lip."` | Nera present and not treated. | Opens Nera treatment. |
| `Check on Nera Doss at the wall table.` | Nera interactions remain. | Opens Nera loop. |
| `Step into the rising dispute before the whole room tips over.` | `stonehill_barfight_ready` and not resolved. | Opens barfight resolution. |
| `Take Nera up on the offer of the upstairs quiet room.` | Quiet-room reward access and not done. | Opens quiet-room packet scene. |
| `[PERSUASION] "Take a share of the contract and ride with me."` | Bryn not companion and first attempt not used. | DC 12. Success recruits Bryn; failure unlocks second attempt. Fires `stonehill_recruit_bryn` companion input. |
| `[INSIGHT] "You don't need luck. You need someone who listens. Tell me what you're waiting to hear."` | Bryn not companion, first attempt used, second not used. | DC 12. Success recruits Bryn; failure locks further immediate recruitment. Fires `stonehill_recruit_bryn_second` input. |
| `Wave Tolan over and ask him to gear up.` | `tolan_waiting_at_inn` and Tolan not companion. | Recruits Tolan. |
| `Rent beds for a long rest (10 gp per active party member).` | Always. | Paid long rest. |
| `Leave the common room for now.` | Always. | Returns to town hub. |

### Mara Stonehill

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Mara who marked the keg and why.` | `marked_keg_investigation` ready. | Turns in quest. |
| `"What has you watching the kegs instead of the door?"` | Quest not granted/completed. | Grants `marked_keg_investigation`. |
| `Read the room around Mara's marked keg.` | Quest active and keg not resolved. | Opens marked-keg investigation. |
| `"How are you keeping this room from breaking?"` | Not asked. | Adds Mara room-order context. |
| `Leave Mara to the floor and step back into the room.` | Always. | Returns to common room. |

Marked keg options:

| Dialogue option | Result |
| --- | --- |
| `[INVESTIGATION] Examine the keg chalk, cellar dust, and tap line.` | DC 12. Success sets `marked_keg_resolved`, `stonehill_marked_keg_named`, cancels barfight readiness, adds clue/journal. Failure sets `stonehill_barfight_ready`. |
| `[INSIGHT] Watch who cares too much whether the marked keg gets opened.` | DC 12. Same success/failure structure. |
| `[LIAR'S BLESSING] Smile like you already know who marked the cask and let the guilty hand correct you.` | Requires Liar's Blessing. Auto success. |
| `Leave the keg alone for the moment.` | No resolution. |

### Jerek Harl

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Jerek what you found of Dain Harl.` | `find_dain_harl` ready. | Turns in quest; if first closure share, lowers town fear. |
| `"If I go to Ashfall, what truth do you want carried back?"` | Quest not granted/completed. | Grants `find_dain_harl`; if Ashfall blue-scarf truth already found, immediately records Dain truth. |
| `"Tell me what would let me know I found Dain, not just another dead road hand."` | Dain truth not found and route marks not shared. | Adds blue-scarf/low-scrape clue. |
| `"Who are you angry at, really?"` | Not asked. | Adds east-road vanishing clue. |
| `[PERSUASION] "Tell me the missing man's name so the room stops calling him 'another crew'."` | Missing-song detail not recorded. | DC 12. Success sets `songs_for_missing_jerek_detail` and journal detail for Sella. |
| `Leave Jerek to his drink and his thoughts.` | Always. | Returns to common room. |

### Sella Quill

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Bring Sella the three true details she asked for.` | `songs_for_the_missing` ready. | Turns in quest. |
| `"Can a song do anything for the missing?"` | Quest not granted/completed. | Grants `songs_for_the_missing`. |
| `"Who do you still need me to hear properly?"` | Quest active and incomplete. | Lists missing detail sources: Jerek, Tam, Nera. |
| `"What does this room sound like to you?"` | Not asked. | Adds clue about the quiet table. |
| `[PERFORMANCE] "Let me trade you a verse for a rumor."` | Not attempted. | DC 12. Success rewards 10 XP and 4 gp. |
| `Tell Sella Jerek finally has Dain Harl's true ending.` | Songs and Dain quests completed; memorial not done. | Adds Dain memorial journal, rewards 10 XP. |
| `Leave Sella Quill to her listening.` | Always. | Returns to common room. |

### Old Tam Veller

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `"What old road are you remembering tonight?"` | Not asked. | Adds clue about manor-side cellar warmth/routes. |
| `[INSIGHT] "Stay with the part that still has a name in it."` | Missing-song Tam detail not recorded. | DC 12. Success sets `songs_for_missing_tam_detail` and journal detail for Sella. |
| `Leave Old Tam to his cooling cup.` | Always. | Returns to common room. |

### Nera Doss

| Dialogue option | Required condition | Result |
| --- | --- | --- |
| `Tell Nera what the quiet table was really doing.` | `quiet_table_sharp_knives` ready. | Turns in quest. |
| `[MEDICINE] "Let me look at that split lip."` | Nera not treated. | DC 12. Sets `stonehill_nera_treated`; success sets `songs_for_missing_nera_detail` and can raise Elira disposition. |
| `"That was not a fall. Who wanted your message changed?"` | Quest not granted/completed. | Grants `quiet_table_sharp_knives`. |
| `Shadow the quiet table Nera pointed out.` | Quest active and table not resolved. | Opens quiet-table scene. |
| `Leave Nera Doss to the wall table and the exits.` | Always. | Returns to common room. |

Quiet-table options:

| Dialogue option | Result |
| --- | --- |
| `[STEALTH] Move around the beams and hear the quiet table cleanly.` | DC 12. Success resolves quiet table, exposes instigator, cancels barfight, adds clue/journal, Bryn +1. Failure triggers barfight. |
| `[INSIGHT] Read which speaker thinks they are safest in the lie.` | DC 12. Same success/failure structure. |
| `[DECEPTION] Pass by like hired help and let them mistake you for nobody worth remembering.` | DC 13. Same success/failure structure. |
| `[LIAR'S BLESSING] Repeat the lie the quiet table expects to hear and wait for the correction.` | Requires blessing. Auto success. |
| `Leave the quiet table for another moment.` | No resolution. |

### Stonehill Barfight

| Dialogue option | Result |
| --- | --- |
| `[PERSUASION] Pull the room back from the edge before the first chair flies.` | DC 13. Success resolves cleanly, rewards 15 XP, lowers town fear, Tolan +1 if active. |
| `[INSIGHT] Name the real instigator and make the room turn the right way.` | DC 12. Same clean success. |
| `[INTIMIDATION] Shut the whole room down with one harder threat.` | DC 13. Same clean success. |
| `[ATHLETICS] Catch the first bench, shove the two worst fools apart, and own the middle.` | DC 12. Same clean success. |
| `[PERFORMANCE] Break the tension with a loud toast sharp enough to steal the room.` | DC 12. Same clean success. |
| `[LIAR'S BLESSING] Tell the liar exactly the lie he thinks nobody else heard.` | Requires blessing. Auto clean success. |
| `Join the fight and end it the hard way.` | Brawl route. Sets `stonehill_barfight_brawled`, may cost up to 2 gp, rewards 10 XP, still exposes paid mouth. |

### Quiet Room Packet

Condition: `quest_reward_stonehill_quiet_room_access` and not `stonehill_quiet_room_scene_done`.

| Dialogue option | Result |
| --- | --- |
| `[INVESTIGATION] Lay the payment note beside the courier strip and find the real route hidden between them.` | DC 12. Success raises reward to 15 XP; sets `stonehill_quiet_room_intel_decoded`, adds Ashfall countersign/Emberhall courier clue. |
| `[INSIGHT] Pick the lie out of the handoff and follow the correction instead.` | DC 12. Same result/reward structure. |
| `Have Nera walk you through the courier habits and take the cleanest lead she can name.` | Auto decodes packet, rewards 10 XP. |
| `[LIAR'S BLESSING] Speak the false countersign aloud and wait for the packet to correct you.` | Requires blessing. Auto success, rewards 15 XP. |

## Phandalin Council And Vigil

### Stonehill War Room

Condition: Old Owl Well and Wyvern Tor cleared; `phandalin_council_seen` is false.

| Dialogue option | Result |
| --- | --- |
| `[INVESTIGATION] "Show me the routes again. I want the exact pressure point."` | DC 13. Success adds route-pressure clue and rewards 20 XP. |
| `[PERSUASION] "If the town is going to hold, they need to hear that we can actually win this."` | DC 13. Success grants `potion_heroism`, rewards 20 XP and 8 gp. |
| `[INSIGHT] "Rukhar is disciplined. Tell me what he is protecting, not what he is saying."` | DC 13. Success adds Rukhar/Ashfall clue, rewards 20 XP. |

### Lantern Vigil

Condition: Ashfall Watch cleared; `phandalin_after_watch_seen` is false. The event reveals Tresendar/Emberhall route pressure.

| Dialogue option | Result |
| --- | --- |
| `[MEDICINE] "Bring me the wounded witness. If they saw the tunnels, I can keep them talking."` | DC 13. Success adds tunnel witness clue and rewards 20 XP. |
| `[RELIGION] "Let the vigil breathe. People remember more clearly when grief is not wrestling them to the ground."` | DC 13. Success grants `scroll_clarity` and rewards 20 XP. |
| `[INVESTIGATION] "Show me the soot-marked ledger scraps from Ashfall. I want the trail beneath the trail."` | DC 13. Success adds ledger trail clue and rewards 20 XP. |

## Act 1 Field Sites

### Old Owl Well

Condition: lead from Halia/Phandalin or route unlock; usually before Ashfall.

| Room/scenario | Dialogue option | Result |
| --- | --- | --- |
| Dig Ring | `[STEALTH] Move along the broken irrigation trench and get inside the ring quietly.` | DC 13. Success surprises/weakens sentry, hero bonus +2, then opens follow-up: sabotage salt, pick sentry, or slip deeper. Failure applies `reeling`. |
| Dig Ring follow-up | `Sabotage the ritual salt before the gravecaller feels the breach.` | Sets `old_owl_ritual_sabotaged`, reels enemies, hero bonus +1. |
| Dig Ring follow-up | `Pick off the nearest sentry before it can join the line.` | Sets `old_owl_sentry_picked`, weakens/surprises sentry, hero bonus +1. |
| Dig Ring follow-up | `Slip deeper toward the well mouth and keep the initiative for later.` | Sets `old_owl_deeper_infiltration`, player invisible 1, hero bonus +1. |
| Dig Ring | `[ARCANA] "Those sigils matter. Let me read what kind of wrongness is powering them."` | DC 13. Success gives player poison resistance 3, reels fixer, hero bonus +1. |
| Dig Ring | `[DECEPTION] "Call out as hired salvage come to collect the next cart of bones."` | DC 13. Success weakens/surprises fixer, hero bonus +1; failure surprises player. |
| Salt Cart | `[MEDICINE] "Cut them free and keep them steady long enough to speak."` | DC 12. Success adds payment/Ashfall/manor clue, rewards 10 XP. Always saves survivor and lowers town fear. |
| Salt Cart | `[PERSUASION] "Easy. You made it this far, so stay with me a little longer."` | DC 12. Success adds Ashfall salvage-route clue, rewards 10 XP. |
| Salt Cart | `Break the cart brace, drag them clear, and let the camp sort itself out later.` | Saves survivor, ruins quick reset, lowers town fear. |
| Supply Trench | `[INVESTIGATION] "Read the notes and sketch the route chain before the wind ruins them."` | DC 12. Success adds Ashfall/manor route clue, rewards 10 XP. |
| Supply Trench | `[ARCANA] "The ink itself looks wrong. I want to know what was mixed into it."` | DC 12. Success adds treated-ash clue, rewards 10 XP. |
| Supply Trench | `Pocket the cleanest pages and kick the rest into the trench water.` | Preserves useful scraps. |
| Supply Trench | `Let Bryn skim the soot ledgers for smuggler marks she used to know.` | Requires active Bryn disposition 6+. Adds Bryn cache/smuggler clue, can set `bryn_cache_found`, rewards 10 XP. |
| Supply Trench completion | Room clear. | Adds Cinderfall hidden-route clue, sets `varyn_filter_logic_seen`, unlocks hidden route. |
| Gravecaller Lip | `[RELIGION] "These dead are not yours to command. Let them go."` | DC 13. Success frightens support and reels Vaelith. |
| Gravecaller Lip | `[INTIMIDATION] "You are finished here. Step away from the well and survive it."` | DC 13. Success damages/frightens Vaelith; failure emboldens Vaelith. |
| Gravecaller Lip | `Rush the ritual line before another corpse can stand.` | Damages Vaelith and adds hero bonus +2. |
| Site victory | Defeat Vaelith. | Reduces `act1_ashen_strength`, clears Old Owl, adds supply-chain clue/journal, grants `scroll_lesser_restoration`, returns to Phandalin. |

### Wyvern Tor

| Room/scenario | Dialogue option | Result |
| --- | --- | --- |
| Goat Path | `[SURVIVAL] Use the goat path and the wind shadow to reach the upper shelf.` | DC 13. Success surprises raider, hero bonus +2. |
| Goat Path | `[STEALTH] Shadow the smoke line and hit the pickets first.` | DC 13. Success weakens/reels enemy, hero bonus +1; failure applies `reeling`. |
| Goat Path | `[NATURE] "The worg pack is the key. Let me read where it expects prey to run."` | DC 13. Success frightens worg, hero bonus +1. |
| Drover Hollow | `[MEDICINE] "Get the drover breathing right and find out how many are still above us."` | DC 12. Success adds Brughor/ogre clue, rewards 10 XP. Always saves survivor and lowers town fear. |
| Drover Hollow | `[INSIGHT] "Tell me what the chief values enough to guard this hard."` | DC 12. Success adds Brughor pride clue, rewards 10 XP. |
| Drover Hollow | `Cut them loose, arm them, and send them downslope before the chief arrives.` | Saves drover. |
| Drover follow-up | `Send them hard for town with the cleanest warning they can carry.` | Sends warning. |
| Drover follow-up | `Keep them hidden below the shelf to signal when Brughor commits his line.` | Sets `wyvern_spotter_signal`. |
| Drover follow-up | `Have them loose the remaining beasts uphill and turn the camp against itself.` | Sets `wyvern_beast_stampede`. |
| Drover completion | Room clear. | Adds Cinderfall hidden-route clue, sets `varyn_detour_logic_seen`, unlocks hidden route. |
| Shrine Ledge | `[RELIGION] "Set the cairn shrine right. I want the chief fighting under a bad sign."` | DC 12. Success blesses player 2, rewards 10 XP. |
| Shrine Ledge | `Cut the pack tethers and send the remaining beasts into the upper camp.` | Distracts upper camp. |
| Shrine Ledge | `Strip the tack, ruin the tethers, and leave the ledge empty.` | Denies staging point. |
| Shrine Ledge | `Let Rhogar reset the cairn and call the hill to witness against Brughor.` | Requires active Rhogar disposition 6+. Blesses player 2, sets `wyvern_rhogar_omen`. |
| High Shelf | `[INTIMIDATION] "You picked the wrong town to stalk."` | DC 13. Success damages/frightens Brughor; failure emboldens him. |
| High Shelf | `[ATHLETICS] "Then come down the rest of the way and see how long you stand."` | DC 13. Success emboldens player 2 and hero bonus +1. |
| High Shelf | `Hit the chief before the ogre can settle into the fight.` | Damages Brughor, hero bonus +2. |
| Site victory | Defeat Brughor. | Reduces `act1_ashen_strength`, clears Wyvern, adds Ashfall coordination clue/journal, grants `greater_healing_draught`, returns to Phandalin. |

### Cinderfall Ruins

Condition: hidden route unlocked from Old Owl notes or Wyvern drover.

| Room/scenario | Dialogue option | Result |
| --- | --- | --- |
| Collapsed Gate | `[STEALTH] Slide through the collapsed arch before the sentries settle.` | DC 13. Success surprises/weakens sentry, hero bonus +2; failure applies `reeling`. |
| Collapsed Gate | `[INVESTIGATION] "Show me the weak braces. I want the gate failing on my timing."` | DC 13. Success reels enemy, hero bonus +1. |
| Collapsed Gate | `[ATHLETICS] Rip the jammed gate wide enough that subtlety stops mattering.` | DC 13. Success emboldens player 2 and hero bonus +2; failure applies `reeling`. |
| Ash Chapel | `[MEDICINE] "Stay with me. I'll get the worst of the smoke out of your lungs first."` | DC 12. Success saves survivors and rewards/clue. |
| Ash Chapel | `[RELIGION] "The shrine still matters. Let me steady the room before we move."` | DC 12. Success steadies survivors/shrine. |
| Ash Chapel | `Break the rear wall wider and rush the survivors out through the ash scrub.` | Saves survivors through forceful evacuation. |
| Broken Storehouse | `[INVESTIGATION] "Read the manifests. I want to know what Ashfall still thinks it can call on."` | DC 12. Success adds reserve-route clue. |
| Broken Storehouse | `[SLEIGHT OF HAND] "Tuck the powder where it will matter most once the relay starts shouting."` | DC 12. Success prepares sabotage. |
| Broken Storehouse | `Kick the reserve crates open and ruin whatever they can still carry from here.` | Ruins reserve supplies. |
| Ember Relay | `[STEALTH] Slip to the basin braces and cut the line before the crew settles.` | DC 13. Success weakens relay fight. |
| Ember Relay | `[ARCANA] "The coals are being driven too hard. I can turn that against them."` | DC 13. Success turns relay energy against crew. |
| Ember Relay | `Charge the keeper and break the relay in plain sight.` | Direct combat opener. |
| Site victory | Break relay. | Sets Cinderfall cleared/relay destroyed, reduces Ashen reserve pressure, helps Ashfall by cutting reinforcements. |

### Ashfall Watch

Condition: Old Owl and Wyvern cleared, or enough legacy clues. Cinderfall sabotage can weaken Ashfall.

| Room/scenario | Dialogue option | Result |
| --- | --- | --- |
| Breach Gate | `[STEALTH] Slip up the ruin side and cut the outer line quietly.` | DC 13. Success surprises/weakens archer, hero bonus +2; failure applies `reeling`. |
| Breach Gate | `[DECEPTION] "Late relief from the tor. Open up before the ridge goes black."` | DC 13. Success surprises/weakens first guard, hero bonus +1; failure surprises player. |
| Breach Gate | `[ATHLETICS] Hit the wagon gate before the watch can settle.` | DC 13. Success emboldens player 2, knocks enemy prone, hero bonus +2; failure applies `reeling`. |
| Immediate yard choice | `[STEALTH] Snuff the signal basin before anyone can call the ridge.` | DC 12. Success sets `ashfall_signal_basin_cleanly_snuffed`; failure sets noisy signal. |
| Immediate yard choice | `[ATHLETICS] Break the prisoner cage and arm whoever can still stand.` | DC 12. Success emboldens player, rewards 15 XP, records blue-scarf truth. Failure still frees but less cleanly. |
| Immediate yard choice | `[INVESTIGATION] "Read the order board. If Rukhar thinks in patterns, I want them now."` | DC 12. Success sets `ashfall_orders_read`, adds rotation clue, rewards 15 XP, records blue-scarf truth. |
| Prisoner Yard | `[ATHLETICS] Break the prisoner cage and arm whoever can still stand.` | DC 12. Same prisoner result if not handled from breach gate. |
| Prisoner Yard | `[INVESTIGATION] Read the order board.` | DC 12. Same order-board result if not handled. |
| Prisoner Yard | `Cut the locks, shove the prisoners toward cover, and keep moving.` | Frees prisoners and records blue-scarf truth. |
| Signal Basin | `[STEALTH] Snuff the signal basin before anyone can call the ridge.` | DC 12. Success cleanly silences basin; failure noisy. |
| Signal Basin | `[SURVIVAL] "The wind is shifting. I can use it to turn the smoke back into the yard."` | DC 12. Success cleanly silences basin and rewards 10 XP; failure noisy. |
| Signal Basin | `Kick the braziers apart and drown the whole thing in grit.` | Noisy but silences basin. |
| Lower Barracks | Combat only. | Hero bonuses from signal/prison/order flags. Victory resolves Elira faith-under-ash hook if present. |
| Rukhar Command | `[QUIET ROOM INTEL] Use the stolen countersign and make Rukhar's own line doubt the next order.` | Requires `stonehill_quiet_room_intel_decoded`. Auto success: damages/reels Rukhar, may remove ally, rewards 10 XP. |
| Rukhar Command | `[INTIMIDATION] "Surrender the yard in Phandalin's name."` | Always. | DC 13. Success damages/frightens Rukhar; failure emboldens him. |
| Rukhar Command | `[PERSUASION] "Your paymaster is already losing. Walk away with the people who still can."` | Always. | DC 13. Success removes ally if present and reels Rukhar. |
| Rukhar Command | `Strike before he can settle the shield line.` | Always. | Damages Rukhar and hero bonus +2. |
| Site victory | Defeat Rukhar. | Clears Ashfall, records Dain/blue-scarf truth if needed, adds Tresendar key clue/journal, routes to Phandalin vigil. |

### Tresendar Manor

Condition: revealed after Ashfall/vigil.

| Room/scenario | Dialogue option | Result |
| --- | --- | --- |
| Hidden Stair | `[INVESTIGATION] "There is a hidden stair here somewhere. Let me find the one they trust."` | DC 13. Success sets hidden entry; first cellar enemy surprised. |
| Hidden Stair | `[STEALTH] Slip through the collapsed chapel side and into the cellars.` | DC 13. Success weakens/reels archer; failure applies `reeling`. |
| Hidden Stair | `[ATHLETICS] Rip the old cistern grate open and take the straight drop.` | DC 13. Success emboldens player and knocks enemy prone; failure applies prone. |
| Cellar Intake | Combat/parley. | Entry flags alter combat. Victory opens cistern and cage store. |
| Cistern Walk | `[INSIGHT] "It is testing us. Let me read what it wants before it strikes."` | DC 13. Success sets `tresendar_eye_read`. |
| Cistern Walk | `[ARCANA] "That is no simple cellar monster. I want its pattern before it gets mine."` | DC 13. Success sets `tresendar_eye_read` and blesses player 1. |
| Cistern Walk | `Throw a ration sack into the dark and charge while it turns.` | Sets `tresendar_eye_ambushed`, hero bonus later. |
| Cage Store | `[INVESTIGATION] "Give me the ledgers. I want the shape of Varyn's exits and lies."` | DC 13. Success adds Emberhall route clue and rewards 10 XP. |
| Cage Store | `[SLEIGHT OF HAND] "Open the coffer quietly and take whatever matters before the hinges scream."` | DC 13. Grants `scroll_arcane_refresh`; success cleaner narration. |
| Cage Store | `Take the whole coffer and drag it back the hard way.` | Grants `scroll_arcane_refresh`. |
| Cistern Eye | `Kill it before it pries any deeper.` | Sets nothic route `kill`; Tolan can gain disposition for refusing bargain. |
| Cistern Eye | `[TRADE] "A memory, a truth, or betrayal. Name the price and speak what you know."` | Opens price prompt; records Emberhall truth. |
| Trade price | `Give it a memory from your own past.` | Sets memory-paid flags, applies `reeling` 1, records Emberhall truth. |
| Trade price | `[TRUTH] "The truth I keep walking around is mine to speak."` | Sets self-truth flag, grants `Clear-Eyed Wound`: +1 Arcana, Insight, Persuasion through Act 1 finale. |
| Trade price | `[BETRAY BRYN] "Bryn knows the old smuggler marks because she used to run them."` | Requires active Bryn. Exposes secret, Bryn disposition -2 or -3, records truth. |
| Trade price | `[BETRAY RHOGAR] "Rhogar's oath has a crack in it. He knows the sound."` | Requires active Rhogar. Exposes secret, Rhogar -2, sets pending conflict. |
| Cistern Eye | `Bargain for every secret it is willing to spit up.` | Starts deep bargain: first Emberhall truth, optional Cinderfall truth, optional Wave Echo warning; adds sanity/status costs and companion penalties if pushed. |
| Deep bargain | `Take the Emberhall truth and end the bargain.` | Stops after first truth. |
| Deep bargain | `[BARGAIN AGAIN] "What did Cinderfall really feed?"` | Adds Cinderfall lore, applies frightened, companion -1, enemy bonus +1. |
| Deep bargain | `Stop before the bargain takes anything else.` | Stops after second truth. |
| Deep bargain | `[BARGAIN AGAIN] "What waits past the Ashen Brand?"` | Adds Wave Echo lore, applies `Whispered Through`: -1 Insight and Persuasion through finale, more status penalties, companion -1, enemy bonus +2. |
| Cistern Eye | `[DECEPTION] "All right. I will give you a secret. A good one."` | DC 15. Success sets nothic deceived and records all three lore truths with hero bonus +2. Failure surprises/reels player and enemy bonus +2. |
| Site victory | Defeat Cistern Eye. | Clears Tresendar, reveals Emberhall, adds route clue/journal, grants `scroll_arcane_refresh` if not already secured, returns to Phandalin. |

### Emberhall Cellars

Condition: `emberhall_revealed`.

| Room/scenario | Dialogue option | Result |
| --- | --- | --- |
| Antechamber | `[STEALTH] Slip through the drainage run and hit the antechamber from behind.` | DC 13. Success weakens/surprises sniper, hero bonus +2; failure applies `reeling`. |
| Antechamber | `[ATHLETICS] Kick in the main cellar door and force the issue immediately.` | DC 13. Success emboldens player, knocks enemy prone, hero bonus +2; failure applies prone. |
| Antechamber | `[PERSUASION] "Call for surrender before the last of them decides to die for Varyn."` | DC 14. Success removes a defender and hero bonus +1. |
| Ledger Chain | `[QUIET ROOM INTEL] Match the quiet-room courier strip to these ledgers before the ink goes warm.` | Requires `stonehill_quiet_room_intel_decoded` and ledger not read. Auto sets `emberhall_ledger_read`, rewards 15 XP. |
| Ledger Chain | `[MEDICINE] "The chained clerk is fading. Get them talking before the poison finishes the job."` | DC 13. Success sets `emberhall_clerk_saved`, grants `antitoxin_vial`, rewards 15 XP. |
| Ledger Chain | `[INVESTIGATION] "Give me the ledgers. I want the shape of Varyn's exits and lies."` | DC 13. Success sets `emberhall_ledger_read`, rewards 15 XP. |
| Ledger Chain | `Smash the poison table and flood the hall with glass, fumes, and noise.` | Sets `emberhall_poison_table_broken`, improves final fight. |
| Ash Archive | `[INVESTIGATION] "Search the ledgers and map which exits Varyn still believes in."` | DC 13. Success sets `emberhall_archive_tip`, adds reserve-route clue, rewards 10 XP. |
| Ash Archive | `[PERCEPTION] "There is something else hidden in here besides paperwork."` | DC 13. Success sets archive tip and grants `potion_healing`. |
| Ash Archive | `Sweep the room fast, pocket anything sharp, and keep moving.` | No special clue; proceeds. |
| Black Reserve | Combat only. | Archive tip grants hero bonus; victory clears reserve room. |
| Varyn Sanctum | `[PERSUASION] "It is over. Walk up the stairs alive, or do not walk them at all."` | DC 15. Success removes a defender and hero bonus +1; failure gives Varyn rebuttal. |
| Varyn Sanctum | `[INTIMIDATION] "You are out of road, out of men, and out of time."` | DC 15. Success damages/reels Varyn; failure emboldens him. |
| Varyn Sanctum | `No more speeches. End this now.` | Damages Varyn and hero bonus +2. |
| Finale victory | Defeat Varyn. | Sets `varyn_body_defeated_act1`, `varyn_route_displaced`, `act1_ashen_brand_broken`, records victory tier, rewards 250 XP and 80 gp, completes Act 1, saves Act 1 complete slot. |

## Companion Reactive Dialogue Inputs

These are not player menu options. They are companion interjections fired by `run_dialogue_input(topic)` when the listed scene option resolves. Conditions include an active companion match, Act 1 gating, and sometimes flag values.

| Topic | Fired by | Companion conditions | Result |
| --- | --- | --- | --- |
| `phandalin_arrival_insight` | Successful or attempted Phandalin arrival Insight route. | Bryn or Elira active; Act 1. | Companion frames town fear and witness value. |
| `phandalin_arrival_persuasion` | Phandalin arrival Persuasion route. | Rhogar or Tolan active; Act 1. | Companion supports public steadiness. |
| `phandalin_arrival_investigation` | Phandalin arrival Investigation route. | Kaelis or Bryn active; Act 1. | Companion points to tracks, lanes, and hidden pressure. |
| `barthen_shortage` | Asking Barthen about shortages. | Tolan, Bryn, or Elira active. | Companion reacts to food/medicine scarcity; reinforces supply stakes. |
| `lionshield_trade` | Asking Linene about trade pressure. | Kaelis, Rhogar, or Tolan active. | Companion reacts to route strangulation and trade fear. |
| `steward_vow` | Making the vow to Tessa. | Elira or Rhogar active. | Companion reinforces moral weight of vow. |
| `steward_blackwake` | Sharing Blackwake with Tessa. | Tolan if rescue, Kaelis if evidence, Bryn if sabotage. | Companion reacts to Blackwake resolution and its political meaning. |
| `stonehill_recruit_bryn` | First Bryn recruitment attempt. | Kaelis or Elira active. | Companion colors Bryn's hesitation. |
| `stonehill_recruit_bryn_second` | Second Bryn recruitment attempt. | Tolan active. | Tolan reacts to Bryn's need to be heard accurately. |

## Campfire Banter

Condition: player chooses the campfire/listen option in camp; required companions are in the party; topic is unseen; listed flags are present. Results usually add small relationship changes, journal/clue text, and sometimes status or Act 1 metric changes.

| Topic | Required companions | Required Act 1 flags | Results |
| --- | --- | --- | --- |
| The Wounded Line | Elira and Tolan | `greywake_triage_yard_seen` plus one of `greywake_wounded_stabilized`, `greywake_wounded_line_guarded`, or `greywake_manifest_preserved`. | Sets `camp_greywake_testimony_threaded`, seeds system profile, Elira +1, Tolan +1, adds journal/clue, may bless player or reinforce manifest/wounded-line proof. |
| Small Promises | Elira and Rhogar | Wayside, Greywake, or road ambush progress. | Sets `camp_faith_oath_anchor`, Elira +1, Rhogar +1, usually grants a brief blessing. |
| Exits and Chimneys | Bryn and Kaelis | `road_ambush_cleared` or `blackwake_completed`. | Sets `camp_route_angles_read`, Bryn +1, Kaelis +1, can grant invisibility/route insight; after Blackwake may reduce Ashen pressure or add clue. |
| Line and Oath | Tolan and Rhogar | `road_ambush_cleared` or `ashfall_watch_cleared`. | Sets `camp_line_oath_drill`, Tolan +1, Rhogar +1, defensive/guarded benefit. |
| Quiet Mercy | Bryn and Elira | Nera treated, Greywake protected, or Nera detail for Sella. | Sets `camp_quiet_mercy_named`, Bryn +1, Elira +1, can lower town fear if Nera was treated. |
| Public Truth | Bryn and Rhogar | Cinderfall cleared or Bryn quest/route truth resolved. | Sets `camp_public_truth_tension_named`, adds clue/journal, adjusts dispositions by truth-vs-exposure stance. |
| Half A Breath | Kaelis and Tolan | `road_ambush_cleared`. | Sets `camp_timing_drill`, Kaelis +1, Tolan +1, grants emboldened timing benefit. |
| What Silence Means | Elira and Kaelis | Old Owl cleared, Greywake progress, or Agatha truth. | Sets silence/truth journal thread, Elira +1, Kaelis +1. |
| Bad Wheels | Tolan and Bryn | Phandalin council/road pressure or Stonehill/route trouble. | Frames practical road repair and dirty logistics; relationship and journal benefits if available. |

Later-act camp topics are intentionally excluded from this Act 1 reference.

## Draft Cleanup Notes

The draft files listed at the top of this document should now be treated as historical source material, not the place to add new Act 1 dialogue. New Act 1 dialogue options should be added here after implementation, with the runtime source and result summarized.
