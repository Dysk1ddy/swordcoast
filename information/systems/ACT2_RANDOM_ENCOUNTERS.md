# Act 2 Random Encounters

Source: `dnd_game/gameplay/random_encounters.py`

This file documents the current Act 2 post-combat random encounter table. Act 2 currently has 15 scaffold encounters. They all use the shared `random_encounter_act2_scaffold` handler.

## System Rules

- Trigger type: post-combat random encounter.
- Trigger chance: `65%` after an encounter victory, unless that encounter has `allow_post_combat_random_encounter=False`.
- Selection weights:
  - unseen encounters have weight `10`
  - previously seen encounters have weight `1`
- Act 2 entries have a common three-option structure:
  - read the scene carefully with a listed skill check
  - take obvious salvage and move on
  - leave it alone
- If the careful check fails, the cave gives no direct combat or damage punishment in the scaffold; the scene simply yields no deeper reward.
- The obvious-salvage option has no skill check and grants a smaller reward.
- The leave option has no reward.

## Encounter List

| # | ID | Title | Careful skill | DC |
| --- | --- | --- | --- | --- |
| 1 | `echoing_supply_cache` | Echoing Supply Cache | Investigation | 13 |
| 2 | `whispering_lantern` | Whispering Lantern | Arcana | 13 |
| 3 | `collapsed_ore_sled` | Collapsed Ore Sled | Athletics | 13 |
| 4 | `silent_prayer_wall` | Silent Prayer Wall | Religion | 13 |
| 5 | `flooded_tool_chest` | Flooded Tool Chest | Sleight of Hand | 13 |
| 6 | `surveyor_ghostlight` | Surveyor Ghostlight | History | 14 |
| 7 | `stolen_claim_markers` | Stolen Claim Markers | Survival | 13 |
| 8 | `blackwater_drifter` | Blackwater Drifter | Perception | 13 |
| 9 | `chain_drag_tunnel` | Chain-Drag Tunnel | Perception | 14 |
| 10 | `mushroom_bloom_hall` | Mushroom Bloom Hall | Nature | 13 |
| 11 | `shattered_foreman_bell` | Shattered Foreman Bell | History | 13 |
| 12 | `hidden_prisoner_note` | Hidden Prisoner Note | Investigation | 12 |
| 13 | `obsidian_shard_outcrop` | Obsidian Shard Outcrop | Arcana | 14 |
| 14 | `broken_lift_cradle` | Broken Lift Cradle | Athletics | 13 |
| 15 | `hushed_campfire` | Hushed Campfire | Insight | 13 |

## 1. Echoing Supply Cache

Premise: A cache behind broken timbers answers footsteps with the wrong echo, making the wall feel deeper than it should.

Careful option:

- `Investigation DC 13`
- Context: identify the real cache rather than a planted lure.
- Success reward: `7 gp`, `miners_ration_tin x1`.

Obvious salvage:

- Reward: `mushroom_broth_flask x1`.

Leave:

- No reward.

## 2. Whispering Lantern

Premise: A dead miner's lantern still burns with pale fuel, hissing almost like a suppressed voice.

Careful option:

- `Arcana DC 13`
- Context: decide whether the lantern is warded, cursed, or simply wrong.
- Success reward: `thoughtward_draught x1`.

Obvious salvage:

- Reward: `5 gp`.

Leave:

- No reward.

## 3. Collapsed Ore Sled

Premise: An ore sled is half-crushed under a cave-in, with fresh tool marks showing someone abandoned the dig-out.

Careful option:

- `Athletics DC 13`
- Context: clear the sled without bringing down the rest of the debris.
- Success reward: `8 gp`, `miners_ration_tin x1`.

Obvious salvage:

- Reward: `mushroom_broth_flask x1`.

Leave:

- No reward.

## 4. Silent Prayer Wall

Premise: Old dwarven prayer marks line a side chamber wall, but almost every name has been scraped smooth.

Careful option:

- `Religion DC 13`
- Context: read the damaged prayer wall without disturbing what clings to it.
- Success reward: `delvers_amber x1`.

Obvious salvage:

- Reward: `4 gp`.

Leave:

- No reward.

## 5. Flooded Tool Chest

Premise: A tool chest rocks in black runoff water, opening and closing slightly whenever the cave trembles.

Careful option:

- `Sleight of Hand DC 13`
- Context: free the flooded chest without ruining the dry packet inside.
- Success reward: `resonance_tonic x1`.

Obvious salvage:

- Reward: `5 gp`.

Leave:

- No reward.

## 6. Surveyor Ghostlight

Premise: A pale light bobs down an unused survey branch, stopping like a guide that expects to be followed.

Careful option:

- `History DC 14`
- Context: judge whether the ghostlight follows an authentic Pact route marker sequence.
- Success reward: `6 gp`, `resonance_tonic x1`.

Obvious salvage:

- Reward: `4 gp`.

Leave:

- No reward.

## 7. Stolen Claim Markers

Premise: Fresh claim stakes marked with different guild symbols are hidden behind a support beam, ready to provoke future disputes.

Careful option:

- `Survival DC 13`
- Context: read who cached the markers and what route they were meant to poison.
- Success reward: `9 gp`, `miners_ration_tin x1`.

Obvious salvage:

- Reward: `6 gp`.

Leave:

- No reward.

## 8. Blackwater Drifter

Premise: An oilcloth bundle drifts at the black water's edge, snagged against a bent rail before the current can take it.

Careful option:

- `Perception DC 13`
- Context: time the drift and recover the bundle before it slides free.
- Success reward: `mushroom_broth_flask x1`, `delvers_amber x1`.

Obvious salvage:

- Reward: `4 gp`.

Leave:

- No reward.

## 9. Chain-Drag Tunnel

Premise: A side tunnel carries the slow scrape of chain over stone, too distant to tell whether it is approaching or circling.

Careful option:

- `Perception DC 14`
- Context: judge the chain-drag tunnel by sound before the source reaches the party.
- Success reward: `8 gp`, `thoughtward_draught x1`.

Obvious salvage:

- Reward: `5 gp`.

Leave:

- No reward.

## 10. Mushroom Bloom Hall

Premise: A collapsed side hall has become a pale mushroom field growing over old helmets, tools, and a ration satchel.

Careful option:

- `Nature DC 13`
- Context: identify edible or useful mushrooms without breathing the dangerous spores.
- Success reward: `mushroom_broth_flask x1`, `miners_ration_tin x1`.

Obvious salvage:

- Reward: `3 gp`.

Leave:

- No reward.

## 11. Shattered Foreman Bell

Premise: A cracked foreman's handbell answers the cave echo with a note that no longer belongs to the mine.

Careful option:

- `History DC 13`
- Context: remember what a Pact foreman's bell signaled before the echoes changed.
- Success reward: `delvers_amber x1`, `resonance_tonic x1`.

Obvious salvage:

- Reward: `5 gp`.

Leave:

- No reward.

## 12. Hidden Prisoner Note

Premise: A folded scrap is wedged into a support seam the way a prisoner hides hope: small, deliberate, and easy to miss.

Careful option:

- `Investigation DC 12`
- Context: tell whether the note is a warning, a lure, or both.
- Success reward: `4 gp`, `thoughtward_draught x1`.
- Success clue: a prisoner note confirms the Quiet Choir rotated captives through the South Adit before the wider expedition understood people were disappearing below.

Obvious salvage:

- Reward: `2 gp`.

Leave:

- No reward.

## 13. Obsidian Shard Outcrop

Premise: A dark glassy outcrop hums around a fist-sized shard, and the air tastes like a storm trying to think.

Careful option:

- `Arcana DC 14`
- Context: bleed off the dangerous charge without carrying the wrong part away.
- Success reward: `thoughtward_draught x1`, `resonance_tonic x1`.

Obvious salvage:

- Reward: `6 gp`.

Leave:

- No reward.

## 14. Broken Lift Cradle

Premise: A lift cradle hangs crooked over a shaft, with a snapped chain and field packs dangling just out of easy reach.

Careful option:

- `Athletics DC 13`
- Context: steady the broken lift long enough to recover the field packs.
- Success reward: `8 gp`, `miners_ration_tin x1`, `mushroom_broth_flask x1`.

Obvious salvage:

- Reward: `5 gp`.

Leave:

- No reward.

## 15. Hushed Campfire

Premise: A recently smothered campfire has warm stones and bedrolls rolled too neatly, like a crew meant to return and never did.

Careful option:

- `Insight DC 13`
- Context: tell whether the camp was abandoned in fear, discipline, or ritual.
- Success reward: `7 gp`, `delvers_amber x1`.

Obvious salvage:

- Reward: `4 gp`.

Leave:

- No reward.
