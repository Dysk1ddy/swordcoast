# Sword Coast Act 1 Content Reference

This file collects the current campaign-facing content that is most useful for debugging story flow, enemy setups, recruitment, and rewards.

The summary sections at the top reflect the expanded Act 1 route and should be treated as the current source of truth where they differ from older shorter-arc notes later in the file.

## Act 1 Scope

- Opening arc: background prologue -> Neverwinter briefing -> High Road ambush -> Phandalin hub
- Branching middle route: `Old Owl Well` and `Wyvern Tor` can be tackled in either order, with a hidden optional strike into `Cinderfall Ruins`
- Convergence points: Stonehill war-room event, Ashfall Watch assault, Phandalin lantern vigil
- Late route: `Tresendar Manor` -> `Emberhall Cellars`
- Named minibosses: `Vaelith Marr`, `Brughor Skullcleaver`, and `Rukhar Cinderfang`
- Final boss: `Varyn Sable`
- Total potential Act 1 combats now comfortably exceeds 10 before counting random encounters
- New non-combat support hubs: `Edermath Orchard`, `Miner's Exchange`, Stonehill war-room, and the post-Ashfall lantern vigil
- Quest set currently defined in data: 7 Act 1 quests, including 5 town quests and 2 companion personal quests
- Reactivity layer now tracks `Town Fear`, `Ashen Strength`, and `Survivors Saved`, then resolves Act 1 as `clean_victory`, `costly_victory`, or `fractured_victory`

## Expanded Act 1 Route

1. Neverwinter setup and one background-specific opening encounter or shortcut
2. High Road ambush and Tolan recruitment point
3. Phandalin arrival, inn / shrine / shop / steward loops, orchard / exchange hubs, and a possible early `Cinderfall` reveal on a strong `Insight` read
4. Old Owl Well route:
   dig-ring fight -> salt cart or supply trench branch -> Vaelith Marr miniboss
5. Wyvern Tor route:
   outer shelf fight -> drover hollow or shrine ledge branch -> Brughor Skullcleaver miniboss
6. Optional `Cinderfall Ruins` route if the hidden relay is uncovered:
   collapsed gate -> ash chapel or broken storehouse -> ember relay node
7. Stonehill war-room fixed event once both major side routes are cleared
8. Ashfall Watch route:
   gate fight -> prisoner yard / signal event -> lower barracks fight -> Rukhar miniboss
9. Lantern vigil fixed event back in Phandalin
10. Tresendar Manor route:
   cellar intake fight -> cistern event -> Cistern Eye fight
11. Emberhall finale:
   antechamber fight -> chained clerk / ledger event -> Varyn boss fight

## Drafted Future Inserts

- `information/Story/HIGH_ROAD_LIARS_CIRCLE_PUZZLE_DRAFT.md`: optional post-ambush High Road wilderness branch built around four lying statues, with `Liar's Blessing` or `Liar's Curse` social-skill consequences.

## Companion Reference

| Companion | Race / Class | Summary | Recruitment point | Relationship bonuses |
| --- | --- | --- | --- | --- |
| Kaelis Starling | Half-Elf Ranger | scout and ambush reader | optional contract companion in Neverwinter before the road | Great: `+1 Perception`, `+1 initiative`; Exceptional: `+1 attack` |
| Rhogar Valeguard | Dragonborn Paladin | oathsworn caravan guardian | optional contract companion in Neverwinter before the road | Great: `+1 damage`; Exceptional: `+1 AC` |
| Tolan Ironshield | Dwarf Fighter | shield-wall caravan veteran | joins after Roadside Ambush or later from the inn | Great: `+1 AC`; Exceptional: `+1 CON saves` |
| Bryn Underbough | Halfling Rogue | trail scout and rumor-reader | recruited at Stonehill Inn on Persuasion success | Great: `+1 Stealth`, `+1 initiative`; Exceptional: `+1 Perception` |
| Elira Dawnmantle | Human Cleric | shrine healer and faith anchor | recruited at the shrine, easier if the player helped her first | Great: `+1 healing`; Exceptional: `+1 WIS saves` |

### Scene support hooks

- Kaelis: `road_ambush`, gives hero bonus and player Invisible
- Kaelis: `wyvern_tor`, gives hero bonus and party Emboldened
- Tolan: `ashfall_watch`, gives hero bonus and player Blessed
- Rhogar: `ashfall_watch`, gives hero bonus and player Blessed
- Bryn: `old_owl_well`, gives hero bonus and player Invisible
- Bryn: `emberhall_cellars`, gives hero bonus and player Invisible
- Elira: `camp_rest`, gives player Blessed before rest

### Great-threshold combat abilities

- Kaelis at disposition `6+`: `Shadow Volley`, which grants the conscious party `Invisible 1` at combat start
- Tolan at disposition `6+`: `Hold the Line`, which grants the conscious party `Guarded 2` at combat start

### Personal quest hooks and conflict beats

- Bryn at disposition `3+`: unlocks `Loose Ends`, which resolves once her old cache ledger is found through trench notes or the smuggler encounter chain
- Elira at disposition `3+`: unlocks `Faith Under Ash`, which resolves in Ashfall's lower barracks when you decide the fate of a captured zealot
- Bryn and Rhogar at disposition `6+` after `Cinderfall` sabotage: can trigger a trust-splitting conflict over whether the route list is buried or publicly exposed

### Relationship thresholds

- `0-2`: Neutral
- `3-5`: Good
- `6-8`: Great
- `9+`: Exceptional
- `-3` to `-5`: Bad
- `-6` or worse: companion leaves the company

## Enemy Archetypes

| Archetype | Display name | Level | HP | AC | Weapon | XP | Gold | Notes |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| `goblin_skirmisher` | Goblin Skirmisher | 1 | 6 | 13 | Scimitar `1d4+1` | 50 | 4 | feature tag `nimble`, but no dedicated runtime hook yet |
| `wolf` | Ash Wolf | 1 | 11 | 13 | Bite `1d6+1` | 50 | 6 | Pack Tactics style behavior and prone rider |
| `worg` | Worg | 1 | 18 | 13 | Rending Bite `2d4+1` | 75 | 8 | stronger pack hunter with prone rider |
| `bandit` | Ashen Brand Bandit | 1 | 11 | 12 | Scimitar `1d6` | 50 | 8 | parley-capable basic humanoid |
| `bandit_archer` | Ashen Brand Lookout | 1 | 9 | 12 | Shortbow `1d6` | 50 | 9 | has once-per-fight control shots |
| `ash_brand_enforcer` | Ashen Brand Enforcer | 2 | 18 | 13 | Hooked Falchion `1d8+1` | 100 | 14 | punishes buffed or marked heroes and can strip `Blessed` |
| `ember_channeler` | Ember Channeler | 2 | 15 | 12 | Ember Brand `1d6+1` | 100 | 12 | support caster that applies `Marked` for team focus fire |
| `carrion_stalker` | Carrion Stalker | 2 | 17 | 14 | Serrated Talons `1d6+2` | 100 | 0 | stealth predator that opens Invisible and applies `Bleeding` |
| `skeletal_sentry` | Skeletal Sentry | 1 | 13 | 12 | Rusty Spear `1d6` | 50 | 2 | undead site defender used around Old Owl Well and the manor |
| `orc_raider` | Orc Raider | 1 | 16 | 14 | Battleaxe `1d8+1` | 75 | 10 | hill raider used at Wyvern Tor and sometimes Ashfall |
| `orc_bloodchief` | Orc Bloodchief | 2 | 33 | 15 | Great Axe `1d12+1` | 150 | 30 | named Wyvern Tor miniboss template with self-buff war cry |
| `ogre_brute` | Ogre Brute | 2 | 38 | 11 | Maul Club `2d8` | 125 | 18 | heavy hitter used in hill and boss-support fights |
| `gravecaller` | Gravecaller | 2 | 26 | 13 | Gravehook Dagger `1d6` | 125 | 24 | caster-style undead handler with fear and ash-blind control |
| `nothic` | Nothic | 2 | 29 | 14 | Hooked Claws `2d4` | 150 | 22 | manor horror with Weird Insight style control |
| `rukhar` | Rukhar Cinderfang | 2 | 27 | 16 | Longsword `1d8` | 125 | 35 | leader miniboss with poison and control |
| `varyn` | Varyn Sable | 2 | 38 | 14 | Blackened Rapier `1d8` | 200 | 60 | leader boss with charm, hex, petrify, poison, and rally |

## Enemy Behavior Details

### Wolf

- Gains practical Pack Tactics style advantage if any other enemy is conscious
- On hit, target makes STR save DC `11` or becomes Prone `1`

### Worg

- Uses the same pack-advantage and prone-rush behavior as the wolf template, but with sturdier HP and higher damage

### Bandit

- On high hit roll (`18+`) against a conscious target, target makes STR save DC `11` or becomes Grappled `1`

### Bandit Archer

- `snare_shot`: once, DEX save DC `12` or Restrained `2`
- `ash_shot`: once, DEX save DC `12` or Blinded `1`

### Ashen Brand Enforcer

- `punishing_strike`: once, lunges at a buffed or marked hero, adds an extra `1d6` slashing damage on hit, and strips `Blessed`
- Prefers targets carrying momentum buffs such as `Blessed`, `Emboldened`, or `Invisible`

### Ember Channeler

- `ember_mark`: once, WIS save DC `12` or target gains `Marked 2` and `Reeling 1`
- Teamwide synergy: enemies now prioritize `Marked` heroes when possible, so the mark acts like a visible focus-fire signal

### Carrion Stalker

- Opens combat with `Invisible 1`
- `shadow_hide`: once, can vanish again mid-fight
- On hit, applies `Bleeding 2`

### Gravecaller

- `grave_fear`: once, WIS save DC `12` or Frightened `2`
- `ash_veil`: once, CON save DC `12` or Blinded `1`

### Orc Bloodchief

- `war_cry`: once, gains `6` temp HP and Emboldened `2`

### Nothic

- `weird_insight`: once, WIS save DC `12` or Reeling `2`
- `rotting_gaze`: once, CON save DC `12` or Poisoned `2`
- On a high claw roll (`18+`), target makes WIS save DC `12` or becomes Frightened `1`

### Rukhar Cinderfang

- War Shout: once, CON save DC `12` or Deafened `2`
- Martial Advantage: adds `2d6` weapon damage while another enemy is still conscious
- Poisoned strike:
  - CON save DC `12` or take `1d4` poison and become Poisoned `2`
  - second CON save DC `12` or become Paralyzed `1`

### Varyn Sable

- Silver Tongue: once, WIS save DC `12` or Charmed `1`
- Binding Hex: once, WIS save DC `12` or Incapacitated `1`
- Ashen Gaze: once, CON save DC `12` or Petrified `1`
- Rally: once at half HP or below, gains `6` temp HP and Emboldened `2`
- Poisoned strike:
  - CON save DC `12` or take `1d4` poison and become Poisoned `2`
  - second CON save DC `12` or gain Exhaustion `2`

## Main Quests

| Quest id | Title | Giver | Location | Completion flag | Reward |
| --- | --- | --- | --- | --- | --- |
| `secure_miners_road` | Stop the Watchtower Raids | Tessa Harrow | Steward's Hall | `ashfall_watch_cleared` | `45 XP`, `25 gp` |
| `restore_barthen_supplies` | Keep the Shelves Full | Barthen | Barthen's Provisions | `ashfall_watch_cleared` | `30 XP`, `12 gp`, `bread_round x2`, `camp_stew_jar x1` |
| `reopen_lionshield_trade` | Reopen the Trade Lane | Linene Graywind | Lionshield Coster | `ashfall_watch_cleared` | `35 XP`, `18 gp`, `potion_healing x1`, `antitoxin_vial x1` |
| `silence_old_owl_well` | Silence Old Owl Well | Halia Thornton | Miner's Exchange | `old_owl_well_cleared` | `50 XP`, `24 gp`, `scroll_clarity x1` |
| `break_wyvern_tor_raiders` | Break the Wyvern Tor Raiders | Daran Edermath | Edermath Orchard | `wyvern_tor_cleared` | `50 XP`, `20 gp`, `greater_healing_draught x1` |
| `bryn_loose_ends` | Loose Ends | Bryn Underbough | personal / road chain | `bryn_loose_ends_resolved` | no listed item reward; resolves by ledger choice |
| `elira_faith_under_ash` | Faith Under Ash | Elira Dawnmantle | personal / Ashfall field scene | `elira_faith_under_ash_resolved` | no listed item reward; resolves by mercy or execution choice |

### Quest state logic

- Quests are stored as `active`, `ready_to_turn_in`, or `completed`
- `ready_to_turn_in` is computed from completion flags, not from scene position alone
- The journal view groups quests by readiness and appends accepted, ready, and completed notes over time
- Bryn and Elira's personal quests are auto-granted from trust thresholds instead of a town giver menu

## Act 1 Reactivity State

### Global metrics

- `act1_town_fear`
  - default `2`
  - lowered by public reassurance, rescues, and mercy choices
- `act1_ashen_strength`
  - default `3`
  - reduced by clearing enemy outer sites and can be driven to `0` by `Cinderfall` sabotage
- `act1_survivors_saved`
  - default `0`
  - raised through rescue branches such as Old Owl, Wyvern Tor, and Cinderfall

### Hidden route unlocks

- `Phandalin` arrival `Insight` success can reveal `Cinderfall Ruins`
- `Old Owl Well` supply trench notes can reveal `Cinderfall Ruins`
- `Wyvern Tor` rescued-drover follow-up can reveal `Cinderfall Ruins`

### Ashfall consequences

- Destroying the `Cinderfall` ember relay removes one lower-barracks reinforcement and prevents `Rukhar` from opening with his `4` temp HP reserve edge
- Elira's `Faith Under Ash` resolution also feeds into Ashfall's boss setup:
  - mercy grants a later `Blessed` opener
  - hard judgment increases pressure and hardens the finale tone

### Ending tiers

- `clean_victory`: low fear, low Ashen strength, enough survivors saved, and no major strained companion fallout
- `costly_victory`: the middle state when Phandalin wins but carries visible damage or tension
- `fractured_victory`: high fear, high remaining enemy pressure, or a strained late-game moral path with too few rescues
- The game records `act2_starting_pressure` from these outcomes so Act 2 can open under different levels of strain

## Early Story Recruitment And Encounter Notes

### Neverwinter briefing

- The player can choose:
  - Kaelis Starling
  - Rhogar Valeguard
  - no early companion

### Roadside Ambush

- Small parties receive encounter scaling help:
  - solo players get weakened enemies, temp HP, Blessed, and initiative help
  - duo parties get lighter scaling support
- The player chooses an opening approach:
  - Athletics rush
  - Stealth flank
  - Intimidation warning
- On victory:
  - clue: the goblins carry Ashen Brand markings
  - clue: the raiders answer to a hobgoblin sergeant tied to Ashfall Watch
  - extra reward: `25 XP`, `15 gp`
  - Tolan can be recruited immediately or left waiting at the inn

### Stonehill Inn

- Bryn can be recruited with Persuasion DC `12`
- If Tolan was sent to recover instead of recruited on the road, he can be picked up here

### Shrine

- Elira can be recruited after shrine interactions
- If the player already helped her, recruitment skips the Persuasion check
- Otherwise the recruitment check is Persuasion DC `12`

## Post-Combat Random Encounter Chains

- `Wounded Messenger`
  - a successful rescue sets up `Messenger Returns`, where the same courier can come back later with coin, healing supplies, and more road intel
- `Smuggler Cookfire`
  - if the camp is disrupted, it can unlock `Smuggler Revenge Squad`
  - if Bryn's personal quest is active, the cookfire can also expose her old cache
- `Abandoned Cottage`
  - once Bryn's cache trail is live, the cellar holdout can point toward `Emberhall`

## Story Flags Worth Watching

These flags show up repeatedly in Act 1 flow and are useful when debugging saves or scene transitions.

- `background_prologue_pending`
- `act1_started`
- `early_companion_recruited`
- `road_approach_chosen`
- `tolan_waiting_at_inn`
- `inn_recruit_bryn_attempted`
- `shrine_recruit_attempted`
- `elira_helped`
- `hidden_route_unlocked`
- `cinderfall_relay_destroyed`
- `bryn_cache_found`
- `bryn_ledger_burned`
- `bryn_ledger_sold`
- `elira_mercy_blessing`
- `elira_hard_verdict`
- `act1_companion_conflict_side`
- `act1_town_fear`
- `act1_ashen_strength`
- `act1_survivors_saved`
- `act1_victory_tier`
- `act2_starting_pressure`
- `ashfall_watch_cleared`

## Debugging Pointers

- Enemy special behavior is keyed by `archetype`, so a renamed enemy still uses the base archetype logic
- Companion scene support only activates when the companion is in the active party and has disposition `6+`
- Great-threshold companion combat openers are separate from scene-support bonuses, so a companion can matter both in the room setup and again when initiative starts
- Quest completion is mostly flag-driven, so a missing `completion_flag` is often more important than a missing journal entry
- The same companion can be offered from multiple story branches, but `has_companion()` prevents duplicate recruitment
