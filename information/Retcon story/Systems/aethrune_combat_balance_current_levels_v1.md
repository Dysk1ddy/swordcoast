# Aethrune Combat Balance: Current Level Scale V1

## Scope

This balance pass scales the new Accuracy, Avoidance, and percentage Defense combat model against the current playable rules layer.

Current code assumptions:

- Current level cap: `4`
- Proficiency bonus at levels `1-4`: `+2`
- Starting HP: hit die + CON modifier
- Level-up HP: `hit_die // 2 + 1 + CON modifier`, minimum `1`
- Current attack model: `d20 + attack bonus` against Armor Class
- New attack model: `d20 + Accuracy` against `10 + Avoidance`
- New mitigation model: physical damage reduced by Defense percentage
- Save-based spells stay on current DC/save math

The numbers below are design targets for implementation. The new Warrior, Mage, and Rogue archetypes are still draft classes, so their tests use synthetic profiles scaled from current HP, proficiency, weapon dice, and enemy stats.

## Conversion Goal

The conversion should preserve the current game's expected damage within a small band while changing the feel.

Old feel:

```text
Armor makes attacks miss.
```

New feel:

```text
Agility, cover, and conditions make attacks miss.
Armor makes hits hurt less.
```

## Defense Conversion

Use these values as the current level 1-4 baseline.

| Armor or protection | Defense |
| --- | ---: |
| Ordinary clothing | `0%` |
| Heavy coat, padded jack, thick hide | `10%` |
| Leather / light armor | `10%` |
| Studded or reinforced light armor | `15%` |
| Scale / brigandine / medium armor | `25%` |
| Strong medium armor | `30%` |
| Chain / heavy armor | `35%` |
| Reinforced heavy armor | `45%` |
| Passive shield | `+5%` |
| Raised shield | `+10%` or `+1` Avoidance against one visible attacker |
| Guard stance | `+20%`, `+2` Stability, `+1` Avoidance, `-2` Accuracy; movement from the guarded lane ends the stance |
| Guarded status | `+5%` |
| Brace action | `+15%` against the next physical hit |
| Spellguard shell | usually `+5%` while Ward remains |

Recommended caps:

| Profile | Defense cap |
| --- | ---: |
| Ordinary combatant | `75%` |
| Light/no armor without ward | `45%` |
| Heavy armor specialist | `80%` |
| Special shell or siege-scale creature | `85%` |

## Current Class Conversion Check

Test case:

- Incoming attacker: `+4` attack
- Incoming average weapon damage: `6.5`
- Old expected damage: current AC system
- New expected damage: Avoidance + percentage Defense

| Current class | Old AC | Avoidance | Defense | Old hit | New hit | Old eDmg | New eDmg |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Barbarian | `12` | `+2` | `0%` | `65%` | `65%` | `4.23` | `3.90` |
| Bard | `14` | `+3` | `10%` | `55%` | `60%` | `3.58` | `3.00` |
| Cleric | `17` | `+1` | `30%` | `40%` | `70%` | `2.60` | `2.80` |
| Druid | `15` | `+2` | `15%` | `50%` | `65%` | `3.25` | `3.25` |
| Fighter | `18` | `+0` | `40%` | `35%` | `75%` | `2.27` | `2.25` |
| Monk | `13` | `+3` | `0%` | `60%` | `60%` | `3.90` | `3.60` |
| Paladin | `18` | `+0` | `40%` | `35%` | `75%` | `2.27` | `2.25` |
| Ranger | `15` | `+3` | `15%` | `50%` | `60%` | `3.25` | `3.00` |
| Rogue | `14` | `+3` | `10%` | `55%` | `60%` | `3.58` | `3.00` |
| Sorcerer | `12` | `+2` | `0%` | `65%` | `65%` | `4.23` | `3.90` |
| Warlock | `13` | `+2` | `10%` | `60%` | `65%` | `3.90` | `3.25` |
| Wizard | `12` | `+2` | `0%` | `65%` | `65%` | `4.23` | `3.90` |

Read:

- Heavy shield users are almost exact against current AC math.
- Cleric-style medium armor plus shield is close enough and feels more hittable.
- Light armor and robes become slightly safer under this draft because `floor` rounds down small reduced hits. That is acceptable at levels `1-4`, where low HP makes spike prevention valuable.
- If low-level fights become too forgiving, switch damage reduction rounding from `floor` to `round` for enemies only.

## Enemy Baseline From Current Templates

Representative templates sampled from current enemy factory data.

| Enemy level | Count | Avg HP | Avg attack | Avg weapon damage | Avg Defense target | Avg Avoidance |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `8` | `11.8` | `+3.2` | `5.4` | `17.5%` | `+0.6` |
| 2 | `11` | `23.8` | `+4.2` | `8.0` | `23.2%` | `+0.5` |
| 3 | `6` | `33.7` | `+4.0` | `8.3` | `25.8%` | `+0.2` |
| 4 | `4` | `41.8` | `+4.5` | `10.8` | `30.0%` | `+0.0` |

Sampled enemy range:

| Metric | Range |
| --- | --- |
| HP | `6` to `45` in the level 1-4 sample |
| AC | `7` to `16` in the level 1-4 sample |
| Attack bonus | `+2` to `+6` |
| Average weapon damage | `3.5` to `13.0` |

Design read:

- Current enemies already lean toward low Avoidance and moderate armor.
- Most level 1 enemies should sit around `0%` to `20%` Defense.
- Most level 2-3 enemies should sit around `15%` to `35%` Defense.
- Level 4 leaders and shell creatures can sit around `30%` to `45%`.
- `55%+` Defense should be saved for obvious stone, plate, construct, shell, boss, or warded profiles.

## Current Enemy Defense Bands

| Enemy profile | Avoidance | Defense | HP adjustment |
| --- | ---: | ---: | --- |
| Unarmored raider | `+1` to `+3` | `0%` to `10%` | none |
| Leather scout | `+3` to `+5` | `10%` to `15%` | none |
| Shieldhand | `+0` to `+2` | `25%` to `40%` | none |
| Brute | `-1` to `+1` | `20%` to `35%` | HP carries durability |
| Plated elite | `+0` to `+2` | `40%` to `55%` | reduce HP by `10%` if fights drag |
| Huge beast | `-2` to `+0` | `20%` to `45%` | HP carries durability |
| Warded caster | `+1` to `+3` | `0%` to `15%`, plus Ward | fragile after shell breaks |
| Stone shell creature | `-2` to `+0` | `55%` to `70%` | add break weakness |

## New Archetype Stat Targets

These profiles use current level `1-4` HP growth with conservative stat assumptions.

### Level 1

Test target:

- Incoming enemy attack: `+4`
- Incoming average damage: `6.5`
- Damage uses percentage Defense and `floor`

| Archetype | Role | HP | Avoidance | Defense | Incoming hit | eDmg taken / attack | Attacks to down |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Juggernaut | tank | `12` | `+0` | `40%` | `75%` | `2.25` | `5.3` |
| Bloodreaver | heal | `12` | `+1` | `30%` | `70%` | `2.80` | `4.3` |
| Berserker | DPS | `12` | `+0` | `25%` | `75%` | `3.00` | `4.0` |
| Weapon Master | DPS | `12` | `+2` | `20%` | `65%` | `3.25` | `3.7` |
| Spellguard | tank | `10` | `+1` | `15%` | `70%` | `3.50` | `2.9` |
| Aethermancer | heal | `10` | `+1` | `10%` | `70%` | `3.50` | `2.9` |
| Arcanist | DPS | `8` | `+2` | `5%` | `65%` | `3.90` | `2.1` |
| Elementalist | DPS | `8` | `+2` | `5%` | `65%` | `3.90` | `2.1` |
| Shadowguard | tank | `10` | `+5` | `10%` | `50%` | `2.50` | `4.0` |
| Alchemist | heal | `10` | `+3` | `10%` | `60%` | `3.00` | `3.3` |
| Assassin | DPS | `10` | `+4` | `10%` | `55%` | `2.75` | `3.6` |
| Poisoner | DPS | `10` | `+4` | `10%` | `55%` | `2.75` | `3.6` |

### Level 4

Same incoming test:

| Archetype | Role | HP | Avoidance | Defense | Incoming hit | eDmg taken / attack | Attacks to down |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Juggernaut | tank | `36` | `+0` | `45%` | `75%` | `2.25` | `16.0` |
| Bloodreaver | heal | `36` | `+1` | `30%` | `70%` | `2.80` | `12.9` |
| Berserker | DPS | `36` | `+0` | `20%` | `75%` | `3.75` | `9.6` |
| Weapon Master | DPS | `36` | `+2` | `20%` | `65%` | `3.25` | `11.1` |
| Spellguard | tank | `31` | `+1` | `15%` | `70%` | `3.50` | `8.9` |
| Aethermancer | heal | `31` | `+1` | `10%` | `70%` | `3.50` | `8.9` |
| Arcanist | DPS | `26` | `+2` | `5%` | `65%` | `3.90` | `6.7` |
| Elementalist | DPS | `26` | `+2` | `5%` | `65%` | `3.90` | `6.7` |
| Shadowguard | tank | `31` | `+5` | `10%` | `50%` | `2.50` | `12.4` |
| Alchemist | heal | `31` | `+3` | `10%` | `60%` | `3.00` | `10.3` |
| Assassin | DPS | `31` | `+4` | `10%` | `55%` | `2.75` | `11.3` |
| Poisoner | DPS | `31` | `+4` | `10%` | `55%` | `2.75` | `11.3` |

## New Archetype Damage Tests

Targets:

| Target | HP | Avoidance | Defense |
| --- | ---: | ---: | ---: |
| Ashen Brand Cutter | `11` | `+1` | `10%` |
| Ashen Brand Enforcer | `18` | `+0` | `25%` |
| Sereth Vane | `30` | `+2` | `15%` |

### Level 1 DPR

| Archetype | Cutter DPR | Cutter rounds | Enforcer DPR | Sereth DPR |
| --- | ---: | ---: | ---: | ---: |
| Juggernaut | `4.50` | `2.4` | `4.00` | `4.20` |
| Bloodreaver | `4.50` | `2.4` | `4.00` | `4.20` |
| Berserker | `7.20` | `1.5` | `5.95` | `6.00` |
| Weapon Master | `4.80` | `2.3` | `4.25` | `4.50` |
| Spellguard | `5.25` | `2.1` | `4.80` | `4.90` |
| Aethermancer | `4.50` | `2.4` | `4.00` | `4.20` |
| Arcanist | `5.25` | `2.1` | `4.80` | `4.90` |
| Elementalist | `5.25` | `2.1` | `4.80` | `4.90` |
| Shadowguard | `4.50` | `2.4` | `4.00` | `4.20` |
| Alchemist | `3.75` | `2.9` | `3.20` | `3.50` |
| Assassin | `7.20` | `1.5` | `6.80` | `6.75` |
| Poisoner | `5.25` | `2.1` | `4.80` | `4.90` |

### Level 4 DPR

| Archetype | Cutter DPR | Cutter rounds | Enforcer DPR | Sereth DPR |
| --- | ---: | ---: | ---: | ---: |
| Juggernaut | `5.25` | `2.1` | `4.80` | `4.90` |
| Bloodreaver | `5.25` | `2.1` | `4.80` | `4.90` |
| Berserker | `8.80` | `1.2` | `7.65` | `7.50` |
| Weapon Master | `6.40` | `1.7` | `5.95` | `6.00` |
| Spellguard | `5.25` | `2.1` | `4.80` | `4.90` |
| Aethermancer | `4.50` | `2.4` | `4.00` | `4.20` |
| Arcanist | `6.00` | `1.8` | `5.60` | `5.60` |
| Elementalist | `6.00` | `1.8` | `5.60` | `5.60` |
| Shadowguard | `4.50` | `2.4` | `4.00` | `4.20` |
| Alchemist | `3.75` | `2.9` | `3.20` | `3.50` |
| Assassin | `11.20` | `1.0` | `9.35` | `9.75` |
| Poisoner | `6.00` | `1.8` | `5.60` | `5.60` |

## Runtime Variance Snapshot

Command:

```text
py -3 tools\combat_variance_report.py --seeds 100
```

Seeds: `1001` to `1100`

### Action Profiles

| Action | Samples | Mean | CV | Zero | P10 | P50 | P90 | Crit | Crit damage share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L4 Warrior weapon vs bandit | `100` | `6.95` | `0.38` | `5.0%` | `4` | `7` | `10` | `4.0%` | `6.2%` |
| L4 Warrior weapon vs false_map_skirmisher | `100` | `5.09` | `0.72` | `5.0%` | `0` | `5` | `10` | `4.0%` | `8.1%` |
| L4 Warrior weapon vs animated_armor | `100` | `3.99` | `0.44` | `5.0%` | `2` | `4` | `6` | `4.0%` | `6.5%` |
| L4 Mage Arcane Bolt bonus cycle vs bandit | `200` | `3.98` | `1.11` | `52.5%` | `0` | `0` | `10` | `2.0%` | `6.8%` |

### Encounter Profiles

| Encounter | Seeds | Victory | Rounds P10 | Rounds P50 | Rounds P90 | Downed mean | Downed P90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Basic raiders | `100` | `100.0%` | `2` | `3` | `3` | `0.00` | `0` |
| High Defense brutes | `100` | `100.0%` | `5` | `7` | `7` | `0.11` | `1` |
| Sereth group | `100` | `100.0%` | `4` | `4` | `5` | `0.01` | `0` |

Read:

- Ordinary raiders now stay inside a tight two-to-three-round band with no P90 downed allies.
- High-Defense brutes still drag mud on the boots, but Glance pressure and chipped armor keep the P90 clear time at `7` rounds with P90 downed allies at `1`.
- Sereth's group stays predictable across seeds: P10/P50/P90 rounds are `4/4/5`, and downed allies almost vanish in the fixed-seed pass.
- Arcane Bolt still has a cooldown-shaped zero-result rate. Its crit damage share is low; further work should focus on miss follow-up or Pattern Charge rather than damage reduction.

## Balance Read

### Looks Good

- Fighter/Paladin-style heavy armor plus shield stays nearly equal to old AC survivability.
- Guard stance now creates a major defensive turn without changing base armor math.
- Cleric-style medium armor plus shield remains close, while feeling more hittable.
- Rogue and Ranger profiles gain survival through Avoidance instead of armor.
- Juggernaut and Shadowguard both tank, but in different ways:
  - Juggernaut gets hit often and reduces damage.
  - Shadowguard gets hit less often and folds if hit by area/save pressure.
- Bloodreaver and Aethermancer have lower raw DPR because they bring healing.
- Alchemist has the lowest DPR, which is correct if Satchel control is strong.

### Watchlist

- Assassin burst is high by level 3-4 because current Rogue sneak attack scaling is strong. Keep the burst, but gate it behind Hidden, exposed target, Death Mark, or once-per-round execution rules.
- Arcanist and Elementalist are fragile at level 1. Their level 1 kit needs either distance, a minor ward, or reliable control.
- Berserker survivability drops during Redline. The damage is healthy, but self-heal should require a Wound.
- Heavy Defense enemies can slow Bloodreaver and Poisoner because both need Wounds. Give those classes cloud, mark, acid, or setup lanes that bypass Wound delivery slowly.
- Guard can become a default answer if lane movement rarely matters. Put flanks, forced movement, Armor Break, save effects, and timed objectives into encounters that expect turtling.

## Recommended Archetype Targets

### Tank Targets

| Archetype | Level 1 target | Level 4 target |
| --- | --- | --- |
| Juggernaut | `12 HP`, `40% Defense`, `+0 Avoidance` | `36 HP`, `45% Defense`, `+0 Avoidance` |
| Spellguard | `10 HP`, `15% Defense`, `+1 Avoidance`, `4-8 Ward` | `31 HP`, `15% Defense`, `+1 Avoidance`, stronger Ward |
| Shadowguard | `10 HP`, `10% Defense`, `+5 Avoidance` | `31 HP`, `10% Defense`, `+5 Avoidance`, better decoys |

### Healer Targets

| Archetype | Level 1 target | Level 4 target |
| --- | --- | --- |
| Bloodreaver | `12 HP`, `30% Defense`, `+1 Avoidance`, heal `3-5/round` while attacking | `36 HP`, same Defense, stronger mark healing |
| Aethermancer | `10 HP`, `10% Defense`, `+1 Avoidance`, heal `1d8+3` | `31 HP`, stronger overflow Ward |
| Alchemist | `10 HP`, `10% Defense`, `+3 Avoidance`, heal `1d6+3` by Satchel | `31 HP`, stronger Satchel economy |

### DPS Targets

| Archetype | Level 1 target | Level 4 target |
| --- | --- | --- |
| Berserker | `7.0-7.5` DPR vs Cutter, `25% Defense` before Redline | `8.5-9.0` DPR vs Cutter, `20% Defense` during risk windows |
| Weapon Master | `4.5-5.0` DPR plus Armor Break setup | `6.0-6.5` DPR plus combo payoff |
| Arcanist | `5.0-5.5` DPR while building Pattern Charge | `6.0` DPR baseline, burst after setup |
| Elementalist | `5.0-5.5` DPR with field risk | `6.0` DPR baseline, higher with terrain |
| Assassin | `7.0` opener DPR | `9.0-11.0` opener DPR, then taper |
| Poisoner | `5.0-5.5` DPR including poison tick | `6.0` DPR baseline, higher over long fights |

## Guard Stance Buff Test

Guard now adds `+20%` Defense, `+2` Stability, `+1` Avoidance, and `-2` Accuracy. Leaving the guarded lane ends the stance.

Incoming test:

- Enemy Accuracy: `+4`
- Enemy average damage: `6.5`
- Damage reduction uses `floor`

| Profile | Base eDmg / attack | Guard eDmg / attack | Attacks to down before | Attacks to down in Guard |
| --- | ---: | ---: | ---: | ---: |
| Juggernaut L1, `12 HP`, `40%` Defense | `2.25` | `1.40` | `5.3` | `8.6` |
| Juggernaut L4, `36 HP`, `45%` Defense | `2.25` | `1.40` | `16.0` | `25.7` |
| Shadowguard L1, `10 HP`, `10%` Defense, `+5` Avoidance | `2.50` | `1.80` | `4.0` | `5.6` |
| Heavy shield spike, `12 HP`, `40%` Defense plus raised shield | `2.25` | `0.70` | `5.3` | `17.1` |

Read:

- The ordinary Guard turn increases Juggernaut survival by roughly `60%`.
- Shadowguard gains a smaller but visible defensive spike because their base tanking comes from Avoidance.
- Guard plus raised shield creates a huge single-lane wall. Keep the `75%` ordinary Defense cap, and make enemies answer it with movement, saves, Armor Break, grapples, and objectives.
- The `-2` Accuracy cost lowers a `75%` hit chance to `65%` against a common Avoidance `+1` target, so Guard carries a clear tempo cost.

## Additional Balance Suggestions

1. Give shield enemies the same Guard rules as players. A shieldhand holding a doorway becomes readable, then hammers, hooks, acid, shoves, and flanks gain purpose.
2. Keep Guard incompatible with Mobile, Aim, Aggressive, and Redline. The stance should ask for a place on the map, a shield angle, and a slower turn.
3. Put Armor Break 1 on more enemy brutes by level 3. A rusted pick, hooked bill, acid vial, siege claw, or snapped tower shield can all tell the player why the wall started failing.
4. Let mages answer Guard through saves, fields, and forced choices. Fire underfoot, charm pressure, a ringing fear sigil, or a collapsing roof should bypass armor Defense through existing saving throw rules.
5. Give Rogues counterplay through position rather than raw Armor Break. Backstab can ignore `10` percentage points of Defense from behind, Poisoner can attack Endurance, and Shadowguard can mark a lane for ally flanks.
6. Add a pressure timer only if testing shows players pass turns in Guard. A light rule is enough: each consecutive Guard round after the first gives `-1` Accuracy until the character moves, Strikes successfully, or spends Grit.
7. Keep high-Defense enemies rare before level 4. Let early fights teach Guard, Glance, and Armor Break with one plated unit beside faster, softer threats.
8. Give Arcanist and Elementalist a level 1 defensive button. A `4` point Ward, a once-per-fight shove field, or a low-damage blind pulse helps them survive the first bad initiative roll.
9. Gate Assassin spike damage behind Hidden, Death Mark, exposed targets, or once-per-round timing. Their level 4 opener can stay frightening if their second round drops back toward normal Rogue DPR.
10. Give Bloodreaver and Poisoner slow lanes against armor. Acid mark, bleeding curse, choking dust, or woundless poison ticks keep them useful when a target reaches `55%+` Defense.

## Implementation Recommendations

1. Keep `floor` rounding for player-facing Defense at levels `1-4`.
2. Use `round` instead of `floor` only if low-level enemy attacks become too soft.
3. Use Defense caps early:
   - normal cap `75%`
   - heavy specialist cap `80%`
   - special shell cap `85%`
4. Convert current armor:
   - leather `10%`
   - studded/reinforced leather `15%`
   - scale/brigandine `25%`
   - chain `35%`
   - shield `+5%`
5. Keep high-Defense enemies rare before level 4.
6. Put Armor Break on hammers, picks, acid, Weapon Master, Juggernaut, and select monsters.
7. Preserve old spell DC math for save-based spells until the weapon side is stable.
8. Test every new class against:
   - `bandit`
   - `ash_brand_enforcer`
   - `sereth_vane`
   - one high-Avoidance target
   - one high-Defense target

## Test Method

The simulation used deterministic probability over d20 outcomes, current model formulas, and average damage dice. It did not run full game encounters with AI, resources, healing turns, multi-enemy focus fire, or spell menus.

Use this as the first balance pass. Runtime implementation should add encounter simulations once the new combat code exists.
