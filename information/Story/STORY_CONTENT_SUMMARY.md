# Aethrune Story Content Summary

Last updated: 2026-04-23

This summary keeps the useful story map and drops the old module-style setting writeup. It is intentionally short; detailed implementation behavior should live in code, tests, or focused act references.

## Current State

- Act I is playable.
- Act II is playable as a scaffolded expedition campaign.
- Act III is roadmap content.
- The live route uses the map system and several save-safe legacy scene ids.
- `android_port/` is a legacy mirror and should be updated only after stable desktop retcon passes.

## Canon Direction

- Setting: Aethrune.
- Opening city: Greywake.
- Main Act I route: the Emberway.
- Frontier hub: Iron Hollow.
- Act I region: the Shatterbelt Frontier.
- Act II region: the Vein of Glass and the Resonant Vaults.
- Old infrastructure frame: the Meridian Accord.
- Act I threat: the Ashen Brand, using route control, forged authority, and supply pressure.
- Act II threat: the Quiet Choir, using record control, listening systems, and obedience framed as peace.

## Save-Safe Legacy Ids

These names may remain in code, saves, tests, and old flags until a migration exists. Do not treat them as player-facing canon.

| Internal id | Public direction |
| --- | --- |
| `neverwinter_briefing` | Greywake briefing |
| `phandalin_hub` | Iron Hollow hub |
| `high_road_*` | Emberway side routes |
| `old_owl_well` | Blackglass Well |
| `wyvern_tor` | Red Mesa Hold |
| `tresendar_manor` | Duskmere Manor |
| `wave_echo_outer_galleries` | Resonant Vaults |
| `forge_of_spells` | Meridian Forge |

## Core Cast To Keep

- Mira Thann: Greywake officer and pressure-point reader.
- Oren Vale, Sabra Kestrel, Vessa Marr, and Garren Flint: contract-house witnesses and city-side logistics pressure.
- Tessa Harrow: Iron Hollow steward.
- Halia Vey, Linene Ironward, Daran Orchard, Hadrik, and Mara Ashlamp: hub civic and trade pressure.
- Elira Lanternward: Lantern priestess and field healer.
- Kaelis Starling: Astral Elf scout.
- Rhogar Valeguard: Forged oathsworn.
- Tolan Ironshield: shield-wall veteran.
- Bryn Underbough: trail scout and rumor-reader.
- Nim Ardentglass: Unrecorded ruin scholar.
- Irielle Ashwake: Fire-Blooded Quiet Choir escapee.

## Character Labels

Internal mechanics keys can remain while public labels move Aethrune-facing:

- `Dragonborn` -> Forged
- `Gnome` -> Unrecorded
- `Half-Elf` -> Astral Elf
- `Half-Orc` -> Orc-Blooded
- `Tiefling` -> Fire-Blooded
- `Goliath` -> Riverfolk

## Main Cleanup Rules

- Keep original Aethrune factions, locations, characters, route pressure systems, and companion structure.
- Keep internal ids when changing them would risk saves or tests.
- Rewrite player-facing text before deep renaming.
- Shorten old design docs instead of preserving long D&D-era lore dumps.
- Keep SRD-derived mechanics only through an explicit rules-lane decision and attribution plan.

## Primary Source Files

- Story runtime: `dnd_game/gameplay/`
- Story data: `dnd_game/data/story/`
- Quest data: `dnd_game/data/quests/`
- Codex: `dnd_game/data/story/lore.py`
- Public vocabulary adapters: `dnd_game/data/story/public_terms.py`
- Active retcon plan: `information/Retcon story/Plans/AETHRUNE_RETCON_IMPLEMENTATION_PLAN.md`
- Cleanup audit: `information/Retcon story/Plans/IP_CLEANUP_PLAN.md`
