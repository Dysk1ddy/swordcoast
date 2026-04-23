# NPC Reference

This file documents the non-player cast currently surfaced by the game, including recruitable companions, quest and service NPCs, support NPC groups, enemy archetypes, and named enemy aliases.

## Scope And Scan Notes

- Scanned sources:
  - `dnd_game/data/story/factories.py`
  - `dnd_game/data/story/companions.py`
  - `dnd_game/gameplay/base.py`
  - `dnd_game/gameplay/map_system.py`
  - `dnd_game/gameplay/story_intro.py`
  - `dnd_game/gameplay/story_act1_expanded.py`
  - `dnd_game/gameplay/story_act2_scaffold.py`
  - `dnd_game/gameplay/story_town_hub.py`
  - `dnd_game/gameplay/story_town_services.py`
  - `dnd_game/gameplay/random_encounters.py`
  - `dnd_game/data/quests/act1.py`
  - `dnd_game/data/quests/act2.py`
  - `information/Story/ACT1_CONTENT_REFERENCE.md`
  - `information/Story/ACT2_CONTENT_REFERENCE.md`
  - `information/catalogs/enemies.md`
- Enemy stats use the runtime `Character.armor_class` value from the live factory, not just armor base AC.
- A named enemy alias keeps the base template's mechanics unless it is listed as its own factory key.
- `gravecaller` is still factory-defined, but the current map content uses `vaelith_marr` as the Old Owl Well boss implementation.
- Some supporting NPC entries are groups rather than named individuals because the story uses them as interactable witnesses, captives, patients, or quest-facing groups.

## Recruitable Companions

| NPC | Companion ID | Race / Class | Recruitment | Combat sheet | Relationship and story role |
| --- | --- | --- | --- | --- | --- |
| Kaelis Starling | `kaelis_starling` | Astral Elf Ranger | Optional Greywake contract companion before the Emberway | Level 1, 11 HP, AC 15, Longbow `1d8`, attack +6 | Scout and ambush reader. Great: `+1 Perception`, `+1 initiative`; Exceptional: `+1 attack`. Supports `road_ambush`, `wyvern_tor`, and `blackwake_crossing`. |
| Rhogar Valeguard | `rhogar_valeguard` | Forged Paladin | Optional Greywake contract companion before the Emberway | Level 1, 11 HP, AC 18, Longsword `1d8`, attack +5 | Oathsworn caravan guardian. Great: `+1 damage`; Exceptional: `+1 AC`. Supports `ashfall_watch` and `blackwake_crossing`. |
| Tolan Ironshield | `tolan_ironshield` | Dwarf Fighter | Joins after the Emberway ambush, or later from Ashlamp Inn if not recruited immediately | Level 1, 13 HP, AC 18, Longsword `1d8`, attack +4 | Shield-wall caravan veteran. Great: `+1 AC`; Exceptional: `+1 CON save`. Supports `ashfall_watch` and `blackwake_crossing`. |
| Bryn Underbough | `bryn_underbough` | Halfling Rogue | Recruited at Ashlamp Inn through Persuasion or Insight | Level 1, 9 HP, AC 14, Shortsword `1d6`, attack +5 | Trail scout, rumor-reader, and old smuggling contact. Great: `+1 Stealth`, `+1 initiative`; Exceptional: `+1 Perception`. Supports `old_owl_well`, `emberhall_cellars`, and `blackwake_crossing`; unlocks `Loose Ends`. |
| Elira Dawnmantle | `elira_dawnmantle` | Human Cleric | Met at Wayside or Iron Hollow's shrine; easier to recruit after helping her | Level 1, 10 HP, AC 17, Mace `1d6`, attack +2 | Lantern priestess and field healer. Great: `+1 healing`; Exceptional: `+1 WIS save`. Supports `camp_rest` and `blackwake_crossing`; unlocks `Faith Under Ash`. |
| Nim Ardentglass | `nim_ardentglass` | Unrecorded Wizard | Act 2 recruit around Stonehollow Dig or early-route convergence | Level 1, 7 HP, AC 11, Quarterstaff `1d6`, attack +1 | Pact cartographer and ruin scholar. Great: `+1 Arcana`, `+1 Investigation`; Exceptional: `+1 spell attack`. Supports `stonehollow_dig` and `wave_echo_outer_galleries`. |
| Irielle Ashwake | `irielle_ashwake` | Fire-Blooded Warlock | Freed and recruited during South Adit | Level 1, 9 HP, AC 12, Quarterstaff `1d6`, attack +1 | Escaped Quiet Choir augur and witness against the cult. Great: `+1 spell damage`, `+1 Insight`; Exceptional: `+1 WIS save`. Supports `south_adit` and `forge_of_spells`. |

### Companion Relationship Thresholds

| Disposition | Label | Gameplay meaning |
| ---: | --- | --- |
| `9+` | Exceptional | Great bonuses plus exceptional bonuses are active. |
| `6-8` | Great | Great relationship bonuses and scene support can apply. |
| `3-5` | Good | Personal quest hooks can unlock for some companions. |
| `0-2` | Neutral | Default relationship state. |
| `-3` to `-5` | Bad | Relationship has meaningfully degraded. |
| `-6` or worse | Terrible | Companion leaves the company. |

## Named Quest, Service, And Story NPCs

| NPC / Group | Type | Primary location | Game use | Notes |
| --- | --- | --- | --- | --- |
| Mira Thann | Named officer | Greywake, Blackwake follow-up | Briefing authority and `Embers Before the Road` quest source | Sharp-eyed Greywake officer tracing the Ashen Brand's city-side supply network. |
| Oren Vale | Named inn steward / fixer | Oren Vale's Contract House, Greywake | Greywake contract-house host, upstairs private-room gatekeeper, room-trust tracker, and later witness-pressure callback | Polite, dry, and almost impossible to surprise; he keeps dangerous people useful by keeping them quiet. |
| Sabra Kestrel | Named caravan bookkeeper | Oren Vale's Contract House, Greywake | `False Manifest Circuit` quest giver, ledger-intel source, and later false-manifest witness | A frayed but razor-sharp logistics clerk who notices when loss has been prewritten into the paperwork. |
| Vessa Marr | Named card sharp / rumor broker | Oren Vale's Contract House, Greywake | Card-table scene, smoke-side rumor source, one of Sabra's manifest-detail speakers, and later buyer-phrase witness | Charming enough to make dishonesty sound recreational right up until someone loses money or face. |
| Garren Flint | Named roadwarden veteran | Oren Vale's Contract House, Greywake | False-seal dialogue source, one of Sabra's manifest-detail speakers, possible bar-fight spark, and later roadwarden-cadence witness | Proud, guarded, and ashamed that copied roadwarden cadence is getting honest travelers hurt. |
| Tessa Harrow | Named civic leader | Iron Hollow Steward's Hall | `Stop the Watchtower Raids` quest giver, war-room planner, Blackwake consequence receiver | Exhausted steward trying to hold Iron Hollow together with maps, ledgers, and resolve. |
| Barthen | Named merchant | Barthen's Provisions | Merchant and `Keep the Shelves Full` quest giver | Provisioner whose shop models food, bandages, lamp oil, and everyday survival pressure. |
| Halia Thornton | Named faction agent | Miner's Exchange, Act 2 claims council | `Silence Old Owl Well` and `Recover the Pact Waymap` quest giver; Act 2 Exchange sponsor | Polished guild agent who treats routes and claims as leverage. |
| Daran Edermath | Named veteran | Edermath Orchard, Act 2 warden lane | `Break the Wyvern Tor Raiders`, old adventurer's cache scene, and woodland-saboteur quest source | Retired half-elf adventurer who reads Phandalin's roads like old battle lines. |
| Linene Graywind | Named merchant / quartermaster | Lionshield Coster, Act 2 claims council | Merchant, `Reopen the Trade Lane`, `Bring Back the Survey Team`, and `Hold the Claims Meeting Together` quest source | Disciplined quartermaster who values clean supply lines and proof over charm. |
| Mara Stonehill | Named innkeeper / floorkeeper | Stonehill Inn | Stonehill regular, `The Marked Keg` quest giver, and barfight stabilizer | Runs the common room like triage: warm when possible, hard when needed, and never fooled for long by panic pretending to be fate. |
| Jerek Harl | Named grieving local | Stonehill Inn | Stonehill regular, `Bring Back Dain's Name` quest giver, grief dialogue source, and one of Sella's truth-detail speakers | Angry miner whose missing brother keeps the room from treating road deaths like weather until the player turns that grief into a real road-side answer. |
| Sella Quill | Named singer / rumor-collector | Stonehill Inn | Stonehill regular and `Songs for the Missing` quest giver | A traveling singer who hears more by making other people want to be quotable. |
| Old Tam Veller | Named retired prospector | Stonehill Inn | Stonehill regular, ruin-memory clue source, and one of Sella's truth-detail speakers | Rambling until he suddenly is not, especially when old stone, dead roads, or bad cellar air come up. |
| Nera Doss | Named courier | Stonehill Inn | Stonehill regular, `Quiet Table, Sharp Knives` quest giver, and one of Sella's truth-detail speakers | A battered courier who notices when messages start arriving half-rewritten by fear, money, or both. |
| Agatha | Named spirit / truth source | Conyberry and Agatha's Circuit | Act 2 route lead tied to dead testimony and buried Pact truth | Treated as a warning source, not a standard combat enemy. |
| Stonehill Teamster | Local witness group | Stonehill Inn | Blackwake rumor and Sereth Vane callback speaker | Represents road-workers carrying fresh rumor and survivor testimony into Phandalin. |
| Town Council | Collective quest source | Phandalin, Wave Echo Cave aftermath | `Sever the Quiet Choir` quest source | Represents the combined civic response once the mine threat becomes larger than a single sponsor. |
| Blackwake survivors, teamsters, guards, and prisoners | Support NPC groups | Blackwake Crossing | Rescue objectives, clue sources, Blackwake outcome metrics | Their survival shapes `blackwake_resolution`, `blackwake_survivors_saved`, testimony, and companion trust changes. |
| Poisoned miner | Support patient | Shrine of Tymora | Elira recruitment and `elira_helped` flag | Stabilizing the miner helps prove the player can be trusted with mercy and field care. |
| Rescued teamster / wounded witnesses | Support witnesses | Lantern vigil and Ashfall aftermath | Clue sources for Tresendar and Emberhall | Their testimony helps push Act 1 from Ashfall Watch toward the manor routes. |
| Stonehollow scholars and survey survivors | Support NPC group | Stonehollow Dig | Rescue objective and Nim recruitment context | Their notes and survival affect Act 2 route control and the quality of Stonehollow truth. |
| South Adit captives / prisoners | Support NPC group | South Adit | Rescue objective and Irielle recruitment context | Their outcome affects Act 2 captive state, town stability, and later witness memory. |
| Wounded messenger | Random encounter NPC | Roadside random encounter | Optional rescue and later reward callback | A non-combat support encounter that can pay off through `messenger_returns_with_reward`. |
| False roadwardens | Support antagonist group | High Road False Roadwarden Checkpoint | Non-combat social pressure encounter; collapses under Deception, Insight, Persuasion, Intimidation, or Oren/Sabra/Garren proof | Borrowed-authority checkpoint hands who make the contract-house false-manifest thread matter before Blackwake. |
| Frightened draft horse | Random encounter creature | Roadside random encounter | Optional Animal Handling / salvage event | Can be calmed for supplies; failure can expose a lurking wolf. |

## Enemy Archetype Roster

Every row below is a unique `create_enemy()` template currently present in `dnd_game/data/story/factories.py`.

| Factory key | Display name | Type | Lvl | HP / AC | Typical use | Signature |
| --- | --- | --- | ---: | ---: | --- | --- |
| `goblin_skirmisher` | Goblin Skirmisher | Goblin Skirmisher | 1 | 6 / 13 | Prologues, High Road, random scavenger fights | Cowardly nimble raider. |
| `wolf` | Ash Wolf | Beast Hunter | 1 | 11 / 13 | Prologue threats, High Road pressure, road random encounters | Pack tactics and prone pressure. |
| `bandit` | Ashen Brand Bandit | Human Bandit | 1 | 11 / 12 | Baseline Ashen Brand raider across Act 1 | Parley-capable humanoid; can grapple on strong hits. |
| `bandit_archer` | Ashen Brand Lookout | Human Lookout | 1 | 9 / 12 | Ranged Ashen Brand support and random encounters | Snare and ash-shot style control. |
| `brand_saboteur` | Ashen Brand Saboteur | Human Saboteur | 1 | 10 / 12 | Blackwake Crossing pressure and false-roadwarden scenes | `flash_ash`, `retreat_step`. |
| `sereth_vane` | Sereth Vane | Human Quartermaster | 2 | 30 / 14 | Blackwake Crossing boss / negotiator | Leader with `silver_pressure`, ash tricks, command movement, and poison. |
| `ash_brand_enforcer` | Ashen Brand Enforcer | Human Enforcer | 2 | 18 / 13 | Ashfall, Cinderfall, Varyn support, revenge squads | Anti-momentum bruiser with `punishing_strike`. |
| `ember_channeler` | Ember Channeler | Human Channeler | 2 | 15 / 13 | Cinderfall relay and Varyn support | Marks targets and enables enemy focus fire. |
| `carrion_stalker` | Carrion Stalker | Monstrosity Stalker | 2 | 17 / 15 | Cinderfall gate / relay ambushes | Invisible opener, bleed pressure, shadow hide. |
| `skeletal_sentry` | Skeletal Sentry | Undead Sentry | 1 | 13 / 12 | Old Owl Well and Tresendar undead guards | Site defender with undead fortitude flavor. |
| `worg` | Worg | Monstrosity Hunter | 1 | 18 / 13 | Wyvern Tor and Ashfall support beast | Stronger pack hunter with prone rush. |
| `orc_raider` | Orc Raider | Orc Raider | 1 | 16 / 13 | Wyvern Tor and Ashfall muscle | Aggressive melee humanoid. |
| `orc_bloodchief` | Orc Bloodchief | Orc Bloodchief | 2 | 33 / 15 | Wyvern Tor boss base, usually Brughor Skullcleaver | Leader with `war_cry`. |
| `ogre_brute` | Ogre Brute | Ogre Brute | 2 | 38 / 10 | Wyvern Tor heavy support | Big prone-causing hitter. |
| `gravecaller` | Gravecaller | Human Occultist | 2 | 26 / 13 | Factory-defined grave-salvage leader; legacy/backup for Old Owl Well style content | Fear and ash-veil caster. |
| `vaelith_marr` | Vaelith Marr | Human Occultist | 3 | 36 / 15 | Old Owl Well named boss | Upgraded gravecaller with ritual surge. |
| `nothic` | Nothic | Aberration Seer | 3 | 34 / 14 | Tresendar cistern horror, often named Cistern Eye | Weird insight and rotting gaze. |
| `rukhar` | Rukhar Cinderfang | Hobgoblin Sergeant | 2 | 27 / 16 | Ashfall Watch named miniboss | Martial advantage, cinder poison, war shout. |
| `varyn` | Varyn Sable | Human Captain | 3 | 46 / 15 | Emberhall / Act 1 final boss | Silver tongue, binding hex, ashen gaze, rally, poison. |
| `expedition_reaver` | Rival Expedition Reaver | Human Reaver | 2 | 18 / 14 | Act 2 rival expedition muscle | Parley-capable treasure-race bruiser. |
| `cult_lookout` | Quiet Choir Lookout | Human Lookout | 2 | 16 / 14 | Act 2 cult ranged support | Blind dust and marked shot. |
| `choir_adept` | Quiet Choir Adept | Human Adept | 3 | 24 / 13 | Act 2 cult caster and Caldra support | Hush prayer and discordant psychic pressure. |
| `grimlock_tunneler` | Grimlock Tunneler | Monstrosity Tunneler | 2 | 20 / 14 | Stonehollow, South Adit, Wave Echo tunnels | Blind sense and grapple drag pressure. |
| `stirge_swarm` | Stirge Swarm | Beast Swarm | 2 | 17 / 17 | Act 2 cramped cave nuisance | Latch-on grapple and follow-up drain damage. |
| `ochre_slime` | Ochre Slime | Ooze Slime | 2 | 28 / 6 | Stonehollow, Wave Echo, side-route chokepoints | Slow acid body / ooze hazard. |
| `animated_armor` | Pact Sentinel Armor | Construct Sentinel | 2 | 26 / 15 | Broken Prospect and Black Lake old-Pact guardians | Construct guardian. |
| `spectral_foreman` | Spectral Foreman | Undead Foreman | 3 | 31 / 15 | Broken Prospect command unit | Dead-shift and hammer-order leader pressure. |
| `starblighted_miner` | Starblighted Miner | Humanoid Miner | 3 | 29 / 13 | South Adit, Black Lake, Caldra support | Whisper-static victim with `whisper_glare`. |
| `caldra_voss` | Sister Caldra Voss | Human Cult Agent | 5 | 54 / 16 | Act 2 final boss at the Forge of Spells | Obelisk whisper, shard veil, Choir rally, echo step. |
| `cinder_kobold` | Cinder Kobold Sneak | Kobold Sneak | 1 | 7 / 13 | Prologue / High Road threat and Cinderfall support | Pack tactics and cinder pot. |
| `briar_twig` | Briar Twig Ambusher | Plant Ambusher | 1 | 8 / 13 | Old Owl Well optional route pressure | False appearance and thorn burst. |
| `mireweb_spider` | Mireweb Spider | Beast Hunter | 1 | 12 / 14 | Tresendar / cave-side optional support | Web-walker restrainer with venom web. |
| `gutter_zealot` | Gutter Cult Zealot | Human Zealot | 1 | 10 / 13 | Cinderfall, Act 1/2 cult color, mercy scenes | Dark devotion and blood prayer. |
| `rust_shell_scuttler` | Rust-Shell Scuttler | Monstrosity Scuttler | 1 | 14 / 13 | Old Owl Well and route hazard support | Corrosion nuisance. |
| `lantern_fen_wisp` | Lantern Fen Wisp | Undead Wisp | 2 | 16 / 16 | Old Owl Well boss support and eerie route hazards | Lure glow and vanish. |
| `ashstone_percher` | Ashstone Percher | Elemental Percher | 2 | 20 / 15 | Old Owl Well and Cinderfall ruin ambusher | False appearance, flyby, drop-strike style pressure. |
| `acidmaw_burrower` | Acidmaw Burrower | Monstrosity Burrower | 2 | 24 / 14 | Stonehollow and tunnel side pressure | Burrower with acid spray. |
| `bugbear_reaver` | Bugbear Tunnel Reaver | Bugbear Reaver | 2 | 25 / 15 | Wyvern Tor and cave ambush support | Surprise attack and abduct pressure. |
| `ettervine_webherd` | Ettervine Webherd | Monstrosity Webherd | 3 | 28 / 15 | Wyvern Tor optional support | Spider-climb web controller with reel strand. |
| `carrion_lash_crawler` | Carrion Lash Crawler | Monstrosity Crawler | 3 | 30 / 15 | Old Owl Well and Stonehollow side pressure | Ceiling hunter with carrion tentacles. |
| `cache_mimic` | Cache Mimic | Monstrosity Mimic | 3 | 34 / 13 | Tresendar / treasure-trap support | Adhesive false treasure with greedy lure. |
| `stonegaze_skulker` | Stonegaze Skulker | Monstrosity Skulker | 3 | 36 / 15 | Tresendar optional support | Petrifying gaze and stone hide. |
| `cliff_harpy` | Shrieking Cliff Harpy | Monstrosity Harpy | 3 | 32 / 14 | Wyvern Tor optional ridge threat | Luring song and swoop. |
| `whispermaw_blob` | Whispermaw Blob | Aberration Blob | 3 | 42 / 7 | Wave Echo / high-whisper Act 2 pressure | Gibbering field, warped ground, blinding spittle. |
| `blacklake_pincerling` | Blacklake Pincerling | Aberration Pincerling | 4 | 40 / 15 | Black Lake Causeway | Grapple-lock hunter with shock spines. |
| `graveblade_wight` | Graveblade Wight | Undead Captain | 4 | 45 / 15 | Old Owl Well boss support and undead route pressure | Life drain and sunken command. |
| `cinderflame_skull` | Cinderflame Skull | Undead Flameskull | 4 | 38 / 15 | Emberhall and late Act 1 support | Fire burst and rekindle. |
| `obelisk_eye` | Eye of the Obelisk | Aberration Sentinel | 4 | 44 / 15 | Forge shard-channel route | Eye rays, levitation, allseeing pressure. |
| `iron_prayer_horror` | Iron Prayer Horror | Construct Horror | 5 | 52 / 16 | Broken Prospect and late Act 2 construct pressure | Spellward plating and relentless march. |
| `hookclaw_burrower` | Hookclaw Burrower | Monstrosity Burrower | 5 | 54 / 16 | Stonehollow, Wave Echo, Black Lake tunnel pressure | Blind sense, echo locator, cave drag. |
| `thunderroot_mound` | Thunderroot Mound | Plant Mound | 5 | 62 / 12 | Act 2 Conyberry / wilderness scaffold threat | Grasping vines, engulf, lightning feed. |
| `oathbroken_revenant` | Oathbroken Revenant | Undead Revenant | 6 | 58 / 16 | South Adit / Act 2 vengeance pressure | Vengeance mark and relentless return. |
| `choir_executioner` | Choir Executioner | Human Executioner | 6 | 64 / 16 | Forge and elite Quiet Choir pressure | Hush command, finishing stroke, dark devotion. |
| `duskmire_matriarch` | Duskmire Matriarch | Monstrosity Matriarch | 6 | 72 / 17 | Black Lake / apex monster support | Shadow web, brood command, widow venom. |

## Named Enemy Variants And Aliases

These entries are unique names or aliases used in scenes, intros, or reference material. Unless the base is "unique template", they inherit the mechanics of their base template.

| Name | Base mechanics | Where it appears | Notes |
| --- | --- | --- | --- |
| Sereth Vane | Unique template `sereth_vane` | Blackwake Crossing | Ashen Brand quartermaster and Blackwake branch boss. |
| Vaelith Marr | Unique template `vaelith_marr` | Old Owl Well | Named gravecaller boss. |
| Brughor Skullcleaver | `orc_bloodchief` | Wyvern Tor | Named orc blood-chief boss. |
| Rukhar Cinderfang | Unique template `rukhar` | Ashfall Watch | Hobgoblin sergeant miniboss. |
| Varyn Sable | Unique template `varyn` | Emberhall Cellars | Act 1 final boss. |
| Sister Caldra Voss | Unique template `caldra_voss` | Forge of Spells | Act 2 final boss and Quiet Choir field theologian. |
| Ashen Brand Runner | `bandit` or `ash_brand_enforcer` depending on scene | Soldier prologue, Cinderfall relay | Courier / runner label for Ashen Brand field agents. |
| Ashen Brand Collector | `bandit` | Blacklake Warehouse, Tresendar Cellars | Dockside broker-enforcer variant. |
| Archive Cutout | `bandit_archer` | Sage prologue, Tresendar Cellars | Hired bow-hand connected to archive theft. |
| Ashen Brand Fixer | `bandit` | Market prologue, Old Owl Well, Emberhall | Broker-like knife fighter and problem solver. |
| Ashen Brand Teamster | `bandit_archer` | Guild Artisan prologue | Wagon hand gone bad. |
| Ashen Brand Barracks Archer | `bandit_archer` | Ashfall lower barracks | Barracks archer variant. |
| Ashen Brand Enforcer | `ash_brand_enforcer`; in one support placement may be a renamed `bandit` | Ashfall, Varyn support, Emberhall reserve | Use the enemy's `archetype` to determine exact behavior. |
| Relay Cutout | `bandit` | Cinderfall collapsed gate | Cinderfall relay guard. |
| Ember Relay Keeper | `ember_channeler` | Cinderfall ember relay | Named channeler maintaining the relay. |
| Cellar Sniper | `bandit_archer` | Emberhall antechamber | Ranged cellar support. |
| Reserve Sniper | `bandit_archer` | Emberhall black reserve | Ranged reserve support. |
| Goblin Scavenger | `goblin_skirmisher` | Random goblin pair encounters | Named scavenger variant for larger parties. |
| Goblin Cutthroat | `goblin_skirmisher` | Named intro / enemy reference | Intro-supported goblin variant; no current literal spawn found in handlers. |
| Tor Lookout | `orc_raider` | Enemy reference | Documented Wyvern Tor named variant. |
| Cragmaw-Ogre Thane | `ogre_brute` | Enemy reference / Brughor support concept | Intro-supported ogre variant; current map uses `ogre_brute` support without literal rename. |
| Cistern Eye | `nothic` | Tresendar nothic lair | Named cellar horror. |

## Faction And Role Index

| Faction / Role | NPCs |
| --- | --- |
| Neverwinter / civic authority | Mira Thann, Tessa Harrow |
| Phandalin commerce and claims | Barthen, Halia Thornton, Linene Graywind, Town Council |
| Wardens and local defenders | Daran Edermath, Elira Dawnmantle, Rhogar Valeguard, Tolan Ironshield |
| Scouts and route readers | Kaelis Starling, Bryn Underbough, Nim Ardentglass |
| Quiet Choir witnesses or defectors | Irielle Ashwake, South Adit captives |
| Ashen Brand named leadership | Sereth Vane, Rukhar Cinderfang, Varyn Sable |
| Old Owl / Wyvern / frontier bosses | Vaelith Marr, Brughor Skullcleaver, Cistern Eye |
| Quiet Choir leadership | Sister Caldra Voss, Choir Executioner, Quiet Choir Adept, Quiet Choir Lookout |

## Maintenance Notes

- Add new companions to `dnd_game/data/story/companions.py`, their factory function in `dnd_game/data/story/factories.py`, and the companion table above.
- Add new enemy templates to the enemy roster once they are present in `create_enemy()`.
- Add renamed scene enemies to the alias table when a scene passes `name=` to `create_enemy()`.
- Keep this file in sync with `information/catalogs/enemies.md` when enemy stats, loot, or encounter placement changes.
