# Act 1 Random Encounters

Source: `dnd_game/gameplay/random_encounters.py`

This file documents the current Act 1 post-combat random encounter table. The user-facing target has often been described as "15 random encounters," but the implemented Act 1 table currently contains 18 entries. All 18 are detailed here so the reference matches the live code.

## System Rules

- Trigger type: post-combat random encounter.
- Trigger chance: `65%` after an encounter victory, unless that encounter has `allow_post_combat_random_encounter=False`.
- Selection weights:
  - unseen encounters have weight `10`
  - previously seen encounters have weight `1`
- Spawned fights from random encounters disable further chained post-combat random encounters.
- If a random encounter fight defeats the party, the party recovers after battle and may lose `2-8 gp`.
- Conditional unlocks:
  - `messenger_returns_with_reward` only appears after `saved_wounded_messenger=True` and before `messenger_return_paid=True`.
  - `smuggler_revenge_squad` only appears after `smuggler_revenge_pending=True` and before `smuggler_revenge_resolved=True`.

## Encounter List

| # | ID | Title | Type |
| --- | --- | --- | --- |
| 1 | `locked_chest_under_ferns` | Locked Chest Under the Ferns | treasure / trap / possible bandit fight |
| 2 | `abandoned_cottage` | Abandoned Cottage | exploration / clue / possible fight |
| 3 | `bandit_toll_line` | Bandit Toll Line | road extortion / avoidance or fight |
| 4 | `wounded_messenger` | Wounded Messenger | rescue / clue / callback setup |
| 5 | `messenger_returns_with_reward` | Messenger Returns | conditional callback / reward |
| 6 | `hunter_snare` | Hunter's Snare | trap / salvage / possible ambush |
| 7 | `lone_wolf` | Lone Wolf at the Kill | beast standoff / optional loot |
| 8 | `smuggler_cookfire` | Smuggler Cookfire | stealth or deception / Bryn hook / revenge setup |
| 9 | `smuggler_revenge_squad` | Smuggler Revenge Squad | conditional reprisal fight |
| 10 | `shrine_of_tymora` | Shrine of Tymora | shrine choice / blessing-flavored salvage |
| 11 | `half_sunk_satchel` | Half-Sunk Satchel | roadside salvage / hazard |
| 12 | `ruined_wayhouse` | Ruined Wayhouse | ruin search / negotiation / possible fight |
| 13 | `scavenger_cart` | Scavenger Cart | salvage / hidden compartment / possible fight |
| 14 | `loose_flagstones` | Loose Flagstones | cache / poison hazard |
| 15 | `frightened_draft_horse` | Frightened Draft Horse | animal handling / salvage / possible wolf |
| 16 | `rain_barrel_cache` | Rain Barrel Cache | hidden cache / hazard |
| 17 | `watchfire_embers` | Watchfire Embers | campsite read / stash / possible bandits |
| 18 | `broken_milestone` | Broken Milestone | road marker cache / possible bandits |

## 1. Locked Chest Under the Ferns

Premise: Ferns hide a traveler's chest under a fallen marker stone. The lock is intact and the hinges are partly rusted.

Choices:

- `Investigation DC 12`: check latch and seams for a hidden catch.
  - Success: `8-14 gp`, `bread_round x1`.
  - Failure: player takes `2 poison` damage from a spring needle.
- `Sleight of Hand DC 15`: pick the travel lock quietly.
  - Success: `10-16 gp`, `potion_healing x1`.
  - Failure: starts `Chest Scavengers`, a bandit-pair fight.
- `Athletics DC 13`: wrench the lid open by force.
  - Success: `6-12 gp`, `goat_cheese x1`.
  - Failure: player takes `3` damage from a snapping hinge.

Follow-up flags: none.

## 2. Abandoned Cottage

Premise: A soot-stained cottage has one open shutter and a cellar door newer than the walls.

Special hook: if `bryn_cache_found=True` and `abandoned_cottage_survivor_met` is not set, this scene can reveal an Emberhall survivor clue.

Choices:

- `Perception DC 12`: scout windows and chimney from the yard.
  - Success: `4 gp`, `camp_stew_jar x1`, `bread_round x1`.
  - Special success: sets `abandoned_cottage_survivor_met=True` and adds the clue that a terrified holdout names Emberhall as the Ashen Brand's deeper cellar route.
  - Failure: starts `Cottage Squatters`, using a goblin pair.
- `Persuasion DC 11`: call out to anyone inside and promise safe passage.
  - Success: `6 gp`, `goat_cheese x1`.
  - Special success: sets `abandoned_cottage_survivor_met=True` and adds a clue tying Emberhall to black-ink cellar ledgers.
  - Failure: starts `Panicked Holdouts`, usually a `bandit_archer`.
- Force entry: shoulder the cellar door open.
  - Starts `Cellar Door Rush`, using a goblin pair.

Follow-up flags: `abandoned_cottage_survivor_met` when the special survivor appears.

## 3. Bandit Toll Line

Premise: A rope across the road promises "safe passage" for coin while hidden voices wait nearby.

Choices:

- Cut the rope and move on.
  - No check, no reward, avoids the collectors.
- `Stealth DC 12`: slip around through the brush.
  - Success: `5 gp`.
  - Failure: starts `Road Toll Collectors`, using a bandit pair.
- `Intimidation DC 13`: threaten the hidden collectors into showing themselves.
  - Success: `5-10 gp`.
  - Failure: starts `Toll Line Standoff`, using a bandit pair.

Follow-up flags: none.

## 4. Wounded Messenger

Premise: A messenger in torn livery lies behind a milepost, bleeding from the leg beside a split satchel.

Choices:

- `Medicine DC 11`: bind the wound before asking questions.
  - Success: `9 gp`, `bread_round x1`, clue about more Ashen Brand scouts probing side trails, and `saved_wounded_messenger=True`.
  - Failure: slows the bleeding, but the messenger passes out before useful details.
- `Investigation DC 12`: search the scattered satchel.
  - Success: `7 gp`, `scroll_clarity x1`.
  - Failure: little useful paper remains.
- Leave water and move on.
  - No reward.

Follow-up flags: `saved_wounded_messenger=True`, which unlocks `Messenger Returns`.

## 5. Messenger Returns

Premise: The saved messenger returns later, walking stiffly with a sealed runner's tube.

Unlock condition: `saved_wounded_messenger=True` and `messenger_return_paid` not set.

On entry: sets `messenger_return_paid=True`.

Choices:

- `Persuasion DC 12`: ask what the messenger learned after surviving.
  - Success: `8 gp`, `potion_healing x1`, clue that the Ashen Brand is leaning on more side roads than the town realized.
  - Failure: `5 gp`.
- Take the reward and tell the messenger to keep breathing.
  - Reward: `7 gp`, `bread_round x1`.
- Refuse the coin and tell them to spend it in Phandalin.
  - No gold reward.
  - If `act1_adjust_metric` is available, reduces `act1_town_fear` by `1`.

Follow-up flags: `messenger_return_paid=True`.

## 6. Hunter's Snare

Premise: A taut snare line glints between alder roots beside the road.

Choices:

- `Perception DC 12`: trace the snare to its anchor.
  - Success: `5 gp`, `goat_cheese x1`, `bread_round x1`.
  - Failure: player takes `2` damage from the snapping line.
- `Survival DC 12`: follow the trapper's line back to stored catch.
  - Success: `6 gp`, `potion_healing x1`.
  - Failure: starts `Snare-Line Ambushers`, with `bandit_archer` and `bandit`.
- Cut the snare and ruin it.
  - No reward, but removes the road hazard in story text.

Follow-up flags: none.

## 7. Lone Wolf at the Kill

Premise: An ash-gray wolf guards a fresh carcass beside the road, with a torn purse nearby.

Choices:

- Back away.
  - No reward and no fight.
- `Survival DC 12`: read the wolf and edge toward the purse.
  - Success: `6-11 gp`.
  - Failure: starts `Wolf on the Trail`, a wolf fight with no parley.
- `Intimidation DC 12`: drive the wolf off with noise and steel.
  - Success: `7-12 gp`.
  - Failure: starts `Cornered Wolf`, a wolf fight with no parley.

Follow-up flags: none.

## 8. Smuggler Cookfire

Premise: A hidden cookfire with half-packed bundles sits off-road under a tarp.

Special hook: if Bryn's `bryn_loose_ends` quest is active and `bryn_cache_found` is not set, Bryn recognizes old smuggler shorthand.

Choices:

- `Stealth DC 12`: circle wide and lift supplies before the campers notice.
  - Success: `4 gp`, `potion_healing x1`, camp disrupted, cache recovered.
  - Failure: starts `Smuggler Camp`, using a bandit pair. Victory counts as cache recovered.
- `Deception DC 12`: warn that riders are coming from Neverwinter.
  - Success: `7 gp`, `bread_round x1`, camp disrupted, cache recovered.
  - Failure: starts `Smuggler Panic`, using a bandit pair. Victory counts as cache recovered.
- Leave the camp alone.
  - No reward and no disruption.

Follow-up flags:

- Any disrupted camp sets `smuggler_revenge_pending=True`.
- If Bryn's cache hook is live and the cache is recovered, sets `bryn_cache_found=True`.

## 9. Smuggler Revenge Squad

Premise: Smugglers and Ashen Brand muscle set a reprisal ambush on a brush road.

Unlock condition: `smuggler_revenge_pending=True` and `smuggler_revenge_resolved` not set.

On entry:

- sets `smuggler_revenge_resolved=True`
- sets `smuggler_revenge_pending=False`

Enemy setup:

- `ash_brand_enforcer`
- `bandit_archer`
- if the party has 3 or more members, add `ember_channeler`

Choices:

- `Stealth DC 13`: spot the ambush first and break the line.
  - Success: `8 gp`, `scroll_clarity x1`.
  - Failure: starts `Smuggler Revenge Squad`.
- `Intimidation DC 13`: break their nerve before the charge.
  - Success: `9 gp`.
  - Failure: starts `Smuggler Revenge Squad`.
- Meet them head-on.
  - Starts `Smuggler Revenge Squad`.
  - Victory adds `6 gp`.

Follow-up flags: `smuggler_revenge_resolved=True`.

## 10. Shrine of Tymora

Premise: A weathered roadside shrine to Tymora leans beneath an oak with a dry offering bowl.

Choices:

- `Religion DC 11`: set the shrine right and offer a frontier prayer.
  - Success: `potion_healing x1`.
  - Failure: no reward.
- Leave a coin.
  - If the party has gold, spends `1 gp`.
  - If not, gives a respectful nod.
- `Athletics DC 13`: pry up stones around the shrine base.
  - Success: `6 gp`.
  - Failure: player takes `2` damage from a falling stone.

Follow-up flags: none.

## 11. Half-Sunk Satchel

Premise: A leather satchel lies trapped under ditch runoff while silver buckles flash beneath the water.

Choices:

- `Survival DC 11`: read the current and pin the satchel.
  - Success: `8-13 gp`, `scroll_clarity x1`.
  - Failure: satchel slips deeper.
- `Athletics DC 12`: yank it free.
  - Success: `6-10 gp`, `bread_round x1`.
  - Failure: player takes `2` damage from a collapsing bank.
- Leave it.
  - No reward.

Follow-up flags: none.

## 12. Ruined Wayhouse

Premise: An old roofless wayhouse has fresh scrape marks around the cellar trapdoor.

Choices:

- `Perception DC 12`: study upper windows and the cellar lip.
  - Success: `5 gp`, `goat_cheese x1`, `camp_stew_jar x1`.
  - Failure: starts `Wayhouse Scavengers`, using a goblin pair.
- `Persuasion DC 12`: call for the squatters to leave with less bloodshed.
  - Success: `6 gp`, `bread_round x1`.
  - Failure: starts `Wayhouse Holdouts`, using a goblin pair.
- Drop through the trapdoor.
  - Starts `Trapdoor Drop`, using a goblin pair.

Follow-up flags: none.

## 13. Scavenger Cart

Premise: A broken handcart lies in the ditch with spilled sacks and a jammed axle pin.

Choices:

- `Athletics DC 12`: set the cart upright.
  - Success: `4 gp`, `bread_round x2`.
  - Failure: player takes `2` damage from the axle pin.
- `Investigation DC 12`: check sacks and hidden panels first.
  - Success: `8 gp`, `goat_cheese x1`.
  - Failure: starts `Returning Scavengers`, with `bandit` and `bandit_archer`.
- Keep walking.
  - No reward.

Follow-up flags: none.

## 14. Loose Flagstones

Premise: Old roadside flagstones sit wrong in the mud, with one slab raised like something below is pushing back.

Choices:

- `Investigation DC 12`: test seams and look for a cache.
  - Success: `9 gp`, `scroll_mending_word x1`.
  - Failure: no reward.
- `Sleight of Hand DC 12`: lift the edge carefully.
  - Success: `6 gp`, `potion_healing x1`.
  - Failure: player takes `2 poison` damage from a broken vial.
- Stamp the stones flat.
  - No reward.

Follow-up flags: none.

## 15. Frightened Draft Horse

Premise: A panicked draft horse is tangled in a snapped trace line with a half-loose pack roll.

Choices:

- `Animal Handling DC 12`: calm the horse and free the line.
  - Success: `5 gp`, `bread_round x1`, `goat_cheese x1`.
  - Failure: the horse bolts with most of the gear.
- `Sleight of Hand DC 12`: work the pack roll loose.
  - Success: `6 gp`, `camp_stew_jar x1`.
  - Failure: player takes `2` damage from the rolling pack.
- `Intimidation DC 12`: scare off whatever is lurking nearby.
  - Success: `7 gp`.
  - Failure: starts `Brush Stalker`, a wolf fight with no parley.

Follow-up flags: none.

## 16. Rain Barrel Cache

Premise: A weighted rain barrel behind a split rail fence hides a hollow clunk beneath the water.

Choices:

- `Investigation DC 11`: probe for a false floor.
  - Success: `7 gp`, `scroll_guardian_light x1`.
  - Failure: cache shifts deeper into the muck.
- `Athletics DC 12`: tip the barrel over.
  - Success: `6 gp`, `potion_healing x1`.
  - Failure: player takes `2` damage from bursting boards.
- Leave it.
  - No reward.

Follow-up flags: none.

## 17. Watchfire Embers

Premise: A watchfire has just gone to embers beside the trail, with warm bedroll hollows and fresh bootprints.

Choices:

- `Perception DC 12`: read the campsite before touching anything.
  - Success: `5 gp`, `bread_round x1`, `goat_cheese x1`.
  - Failure: no reward.
- `Stealth DC 12`: follow the freshest bootprints to find the stash.
  - Success: `8 gp`, `scroll_ember_ward x1`.
  - Failure: starts `Returning Campers`, using a bandit pair.
- Kick dirt over the embers.
  - No reward.

Follow-up flags: none.

## 18. Broken Milestone

Premise: A shattered milestone lies in chunks across the roadside, with fresh pry marks around it.

Choices:

- `History DC 11`: study the carving and remember the mason's trick.
  - Success: `7 gp`, `scroll_battle_psalm x1`.
  - Failure: no reward.
- `Athletics DC 12`: split the largest chunk.
  - Success: `9 gp`.
  - Failure: starts `Milestone Scavengers`, using a bandit pair.
- Roll the stone off the road.
  - No reward.

Follow-up flags: none.
