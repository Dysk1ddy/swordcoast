# Defense Point Rebalance Draft

## Purpose

This draft converts the current percent-based Defense system into a point scale that reads like armor class and feeds Damage Reduction.

Defense 10 or lower gives 0% DR. Defense 22 or higher gives 80% DR. Chest armor supplies most of the value. Shields, helmets, and short buffs can push a build upward, but ordinary gear should rarely add more than 1 or 2 Defense outside the chest slot.

## Formula

Use the curve from `damage_reduction_level_scaling.md`, with the final clamp set to 80.

```text
base_dr = 80 * ln(1 + 0.18 * (Defense - 10)) / ln(3.16)
final_dr = clamp(base_dr * level_multiplier, 0, 80)
```

Recommended level multiplier:

```text
player_or_companion_defender = 1 + 0.08 * (defender_level - attacker_level)
ordinary_enemy_defender = 1 + 0.04 * (defender_level - attacker_level)
boss_enemy_defender = 1 + 0.06 * (defender_level - attacker_level)
```

Enemy scaling is softer so high-level enemies stay threatening through actions, HP, pressure, and tactics instead of turning every fight into a long armor grind.

## Defense Curve

| Defense | Equal-Level DR |
|---:|---:|
| 10 | 0.0% |
| 11 | 11.5% |
| 12 | 21.4% |
| 13 | 30.0% |
| 14 | 37.7% |
| 15 | 44.6% |
| 16 | 50.9% |
| 17 | 56.7% |
| 18 | 62.0% |
| 19 | 67.0% |
| 20 | 71.6% |
| 21 | 75.9% |
| 22 | 80.0% |

## Stat Model

Defense points come from the armor profile, then a small number of supplements.

```text
total_defense =
    chest_defense
    + shield_defense_bonus
    + helmet_defense_bonus
    + limited_misc_defense_bonus
    + temporary_status_defense_bonus
```

Guidelines:

- Chest armor carries the build: 10-20 Defense in normal itemization.
- Passive shield bonus: +1 Defense. Rare or named shield: +2 Defense.
- Helmet bonus: +1 Defense. Late rare named helmet: +2 Defense.
- Passive non-chest gear support should usually cap at +2 total before shield.
- Temporary combat buffs can add +1 or +2, with the final DR calculation capped at Defense 22.
- Dex affects contact defense and avoidance. Dex does not add DR.

## Armor Item Targets

All current armor items can be converted onto the point scale like this.

| Current armor item | Type | Dex cap | Proposed Defense | Equal-Level DR | Notes |
|---|---|---:|---:|---:|---|
| Roadworn Traveler Clothes | Clothing | Full | 10 | 0.0% | Baseline travel wear. |
| Roadworn Padded Armor | Light | Full | 11 | 11.5% | Cheap soft protection. |
| Roadworn Leather Armor | Light | Full | 11 | 11.5% | Scout baseline. |
| Ash-Kissed Leather Armor | Light | Full | 12 | 21.4% | Uncommon light armor. |
| Roadworn Studded Leather | Light | Full | 12 | 21.4% | Better mundane light armor. |
| Ash-Kissed Studded Leather | Light | Full | 13 | 30.0% | High light protection. |
| Starforged Studded Leather | Light | Full | 13 | 30.0% | Keep light armor from overtaking medium. |
| Roadworn Chain Shirt | Medium | +2 | 13 | 30.0% | Elira's new survivability floor. |
| Ash-Kissed Chain Shirt | Medium | +2 | 14 | 37.7% | Strong medium-light armor. |
| Roadworn Scale Mail | Medium | +2 | 14 | 37.7% | Heavier medium baseline. |
| Ash-Kissed Scale Mail | Medium | +2 | 15 | 44.6% | Medium armor with strain. |
| Roadworn Breastplate | Medium | +2 | 14 | 37.7% | Clean medium armor with no stealth strain. |
| Ash-Kissed Breastplate | Medium | +2 | 15 | 44.6% | Better medium protection. |
| Starforged Breastplate | Medium | +2 | 16 | 50.9% | Rare specialized medium armor. |
| Kingshard Breastplate | Medium | +2 | 16 | 50.9% | Epic medium armor stays below very-heavy thresholds. |
| Roadworn Chain Mail | Heavy | +0 | 15 | 44.6% | Common heavy armor. |
| Ash-Kissed Chain Mail | Heavy | +0 | 16 | 50.9% | Heavy armor with a useful enchantment. |
| Starforged Chain Mail | Heavy | +0 | 16 | 50.9% | Rare heavy armor, same shell with better secondary traits. |
| Roadworn Splint Armor | Very Heavy | +0 | 17 | 56.7% | Very-heavy entry point. |
| Starforged Splint Armor | Very Heavy | +0 | 18 | 62.0% | Rare very-heavy armor. |
| Kingshard Splint Armor | Very Heavy | +0 | 19 | 67.0% | Epic very-heavy armor. |
| Mythwake Splint Armor | Very Heavy | +0 | 20 | 71.6% | Best chestpiece before supplements and buffs. |

## Supplementary Gear

| Gear family | Proposed Defense | Rule |
|---|---:|---|
| Standard shield | +1 | Requires one free hand. |
| Rare or named shield | +2 | Reserve for late shield builds or quest rewards. |
| Raised Shield status | +1 temporary | Stacks with shield, expires normally. |
| Guard or Brace stance | +1 temporary | Lets armored defenders hold a lane without pushing baseline gear too high. |
| Iron Cap | +1 | Keep common, uncommon, and rare caps at +1 unless a named version is added. |
| Late named helmet | +2 | Rare story reward or boss cache. |
| Reinforced Cloak | +1 | Count against the passive support budget; consider moving this to utility if helmets become common. |
| Anchor Shell / magical ward shell | +1 or +2 temporary | Use +2 for costly class-resource versions. |

The practical player ceiling becomes:

| Build | Defense |
|---|---:|
| Chain Shirt + no supplements | 13 |
| Breastplate + shield | 15 |
| Chain Mail + shield + iron cap | 18 |
| Roadworn Splint + shield + iron cap | 19 |
| Mythwake Splint + shield + iron cap | 22 |
| Starforged Breastplate + shield + iron cap + temporary buff | 19-20 |

Defense 22 should require a best-in-slot chestpiece plus at least two support pieces, or a strong heavy chestpiece plus active defensive buffs.

## Enemy Defense Budgets

Enemies should usually sit below player Defense. Their threat should come from numbers, pressure, action patterns, control effects, and encounter scripts.

| Enemy band | Level range | Ordinary Defense | Armored/Brute Defense | Elite or miniboss Defense | Boss Defense |
|---|---:|---:|---:|---:|---:|
| Road trouble | 1 | 10-11 | 12 | 13 | 14 |
| Early Act I | 2 | 10-12 | 13 | 14 | 15 |
| Late Act I | 3 | 10-12 | 13-14 | 15 | 16 |
| Act II opening | 4 | 10-13 | 14 | 15-16 | 17 |
| Act II depth | 5 | 10-13 | 14-15 | 16 | 17-18 |
| Late Act II / Act III bridge | 6 | 11-14 | 15-16 | 17 | 18-19 |

Hard limits:

- Ordinary enemies cap at 13 Defense unless their entire identity is armor, shell, or stone.
- Ordinary brutes cap at 14 until level 5.
- Minibosses can reach 15-17 depending on level.
- Bosses can reach 17-19.
- Defense 20 belongs to rare capstone enemies.
- Defense 21-22 should stay player-facing or appear only on telegraphed raid-style bosses with armor-break answers.

## Current Enemy Archetype Targets

| Enemy archetype | Level | Role | Proposed Defense |
|---|---:|---|---:|
| `goblin_skirmisher` | 1 | cowardly skirmisher | 11 |
| `wolf` | 1 | beast | 11 |
| `bandit` | 1 | ordinary humanoid | 11 |
| `bandit_archer` | 1 | ordinary ranged humanoid | 11 |
| `brand_saboteur` | 1 | ordinary control humanoid | 11 |
| `skeletal_sentry` | 1 | brittle armored undead | 12 |
| `worg` | 1 | beast bruiser | 11 |
| `orc_raider` | 1 | armored raider | 12 |
| `cinder_kobold` | 1 | cowardly skirmisher | 11 |
| `briar_twig` | 1 | plant | 11 |
| `mireweb_spider` | 1 | shelled beast | 12 |
| `gutter_zealot` | 1 | fragile caster | 10 |
| `rust_shell_scuttler` | 1 | shelled monstrosity | 12 |
| `sereth_vane` | 2 | early leader | 13 |
| `ash_brand_enforcer` | 2 | armored enforcer | 13 |
| `ember_channeler` | 2 | fragile caster | 10 |
| `carrion_stalker` | 2 | hide-armored monstrosity | 12 |
| `orc_bloodchief` | 2 | armored leader | 14 |
| `ogre_brute` | 2 | large low-skill brute | 12 |
| `gravecaller` | 2 | caster leader | 12 |
| `expedition_reaver` | 2 | ordinary humanoid | 12 |
| `cult_lookout` | 2 | scout humanoid | 12 |
| `grimlock_tunneler` | 2 | tunneling brute | 12 |
| `stirge_swarm` | 2 | evasive swarm | 10 |
| `ochre_slime` | 2 | ooze | 10 |
| `animated_armor` | 2 | construct miniboss | 15 |
| `lantern_fen_wisp` | 2 | evasive undead | 10 |
| `ashstone_percher` | 2 | stone elemental | 13 |
| `acidmaw_burrower` | 2 | plated burrower | 13 |
| `bugbear_reaver` | 2 | armored brute | 13 |
| `nothic` | 3 | aberration | 12 |
| `rukhar` | 3 | boss leader | 15 |
| `choir_adept` | 3 | caster leader | 11 |
| `spectral_foreman` | 3 | undead miniboss | 14 |
| `starblighted_miner` | 3 | ordinary humanoid | 11 |
| `ettervine_webherd` | 3 | webbed monstrosity | 12 |
| `carrion_lash_crawler` | 3 | crawler | 12 |
| `cache_mimic` | 3 | ambush brute | 13 |
| `stonegaze_skulker` | 3 | defensive miniboss | 15 |
| `cliff_harpy` | 3 | aerial skirmisher | 11 |
| `whispermaw_blob` | 3 | soft aberration | 10 |
| `vaelith_marr` | 4 | major caster boss | 14 |
| `false_map_skirmisher` | 4 | high-evasion skirmisher | 11 |
| `claimbinder_notary` | 4 | control leader | 13 |
| `echo_sapper` | 4 | siege specialist | 14 |
| `pact_archive_warden` | 4 | construct sentinel miniboss | 16 |
| `blackglass_listener` | 4 | aberration scout | 11 |
| `blacklake_pincerling` | 4 | armored aberration | 15 |
| `graveblade_wight` | 4 | undead leader | 16 |
| `cinderflame_skull` | 4 | flying undead caster | 11 |
| `obelisk_eye` | 4 | aberration leader | 12 |
| `varyn` | 5 | assassin boss | 14 |
| `caldra_voss` | 5 | caster leader | 13 |
| `choir_cartographer` | 5 | tactical leader | 13 |
| `resonance_leech` | 5 | aberration | 12 |
| `survey_chain_revenant` | 5 | undead bruiser | 14 |
| `censer_horror` | 5 | construct horror | 15 |
| `memory_taker_adept` | 5 | assassin caster | 12 |
| `iron_prayer_horror` | 5 | armored construct | 15 |
| `hookclaw_burrower` | 5 | plated monstrosity | 14 |
| `thunderroot_mound` | 5 | plant brute | 13 |
| `obelisk_chorister` | 6 | caster leader | 14 |
| `blacklake_adjudicator` | 6 | construct leader | 17 |
| `forge_echo_stalker` | 6 | ambusher | 13 |
| `covenant_breaker_wight` | 6 | undead boss | 17 |
| `hollowed_survey_titan` | 6 | construct brute | 16 |
| `oathbroken_revenant` | 6 | undead leader | 16 |
| `choir_executioner` | 6 | armored humanoid leader | 16 |
| `duskmire_matriarch` | 6 | monstrosity boss | 17 |

## Enemy Armor Pattern Notes

Humanoid grunts should usually wear Defense 10-12 protection: road leathers, vests, coats, and scavenged plates. Their survival comes from numbers and position.

Beasts and monstrosities should use hide, carapace, or mass as a flavor reason for Defense 11-13. Large creatures can have more HP instead of high Defense.

Constructs can carry higher Defense, but most ordinary constructs should sit at 14-15. Sentinels and named constructs can reach 16-17. A construct with Defense 18 or higher needs an armor-break route, exposed weak point, or telegraphed charge window.

Undead should split by body type. Ghostly or flame skull enemies stay at 10-12. Mail-wrapped revenants and wights can sit at 15-17 when they are minibosses or leaders.

Casters and assassins should usually stay low: 10-13. Their danger belongs in control, burst windows, mobility, or summons.

## Implementation Plan

1. Add a point-based helper:

```python
def damage_reduction_for_defense(defense: int, defender_level: int, attacker_level: int, *, defender_is_enemy: bool, boss: bool = False) -> int:
    if defense <= 10:
        return 0
    defense = min(22, defense)
    base = 80 * math.log(1 + 0.18 * (defense - 10)) / math.log(3.16)
    level_rate = 0.08
    if defender_is_enemy:
        level_rate = 0.06 if boss else 0.04
    multiplier = 1 + level_rate * (defender_level - attacker_level)
    return round(max(0, min(80, base * multiplier)))
```

2. Convert armor data:

- Rename or reinterpret armor `defense_percent` as `defense_points`.
- Keep `base_ac` and `defense_points` aligned for armor entries.
- Use item rarity to add points only where the armor story supports it.
- Keep light armor at 13 or below.
- Keep medium armor mostly at 13-15, with rare breastplates at 16.
- Keep heavy armor at 15-16.
- Keep very-heavy armor at 17-20.

3. Convert gear bonuses:

- `shield_defense_percent` becomes `shield_defense_points`.
- `defense_percent` on helmets and cloaks becomes `defense_points_bonus`.
- Cap passive non-chest support to keep the chestpiece dominant.

4. Convert enemy profiles:

- Replace `LOW_LEVEL_ENEMY_COMBAT_PROFILES["defense_percent"]` with `defense`.
- Write current enemy armor objects with point values instead of percent values.
- Add role caps so ordinary enemies cannot drift above the intended range through future profile edits.

5. Update display text:

- Show `Defense 14 (DR 37.7%)` on armor item cards.
- Show enemy examine text as `Defense 12`, plus DR after level scaling if useful.
- Keep Dex cap visible beside armor because it affects contact defense and avoidance.

6. Update tests:

- Armor catalog table tests for the proposed item values.
- DR formula tests for 10, 14, 17, 20, and 22 Defense.
- Enemy archetype budget test that fails if ordinary level 1-3 enemies exceed 13 Defense.
- Boss budget test that allows 17+ only for leader/miniboss/boss tags.

## Balance Risks

Defense 13 already gives roughly 30% DR at equal level. Low-level enemies with Defense 13 will feel tougher than current 10-15% grunts, so ordinary Act I enemies should mostly sit at 10-12.

Defense 17 gives roughly 57% DR. This value should announce a heavy shell. The player needs armor break, pressure, poison, spell damage, or a visible tactical answer.

Defense 20 gives roughly 72% DR before level scaling. This belongs on the strongest chestpieces and rare boss shells.

Defense 22 reaches the cap. Let players build toward it. Use it on enemies only for set-piece fights with a clear breach mechanic.
