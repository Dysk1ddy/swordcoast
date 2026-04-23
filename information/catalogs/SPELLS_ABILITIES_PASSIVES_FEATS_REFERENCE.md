# Aethrune Mechanics Surface Reference

Last updated: 2026-04-23

This file replaces the old long spell, feature, passive, and feat draft that paraphrased external tabletop and video-game references. Keep this document implementation-facing and retcon-safe: it should point to live code, name what is actually implemented, and avoid carrying unused source-lore summaries forward.

## Live Sources

- Runtime character options: `dnd_game/data/story/character_options/`
- Public labels and term adapters: `dnd_game/data/story/public_terms.py`
- Combat actions and spell handling: `dnd_game/gameplay/combat_flow.py`
- Damage, healing, resist checks, and death state: `dnd_game/gameplay/combat_resolution.py`
- Status effects: `dnd_game/gameplay/status_effects.py`
- Item effects: `dnd_game/data/items/catalog.py`
- Regression coverage: `tests/test_core.py`

## Current Rules Lane

- The game still uses a compact SRD-derived d20 math chassis internally.
- Player-facing text should prefer Aethrune terms: `Guard`, `resist check`, `strike check`, `edge`, `strain`, `channeling`, `channel reserve`, `draught`, `script`, `relic`, and `marks`.
- Internal class, spell, feature, and item ids may remain legacy-shaped until save migration and display-name adapters are finished.
- Do not re-add external spell descriptions, feat catalogs, subclass prose, borrowed setting lore, or comparison notes here.

## Implemented Channel Labels

The authoritative mapping is `SPELL_PUBLIC_LABELS` in `public_terms.py`.

| Internal id | Public label |
| --- | --- |
| `sacred_flame` | Lantern Flare |
| `produce_flame` | Embercall |
| `vicious_mockery` | Cutting Cadence |
| `fire_bolt` | Ember Lance |
| `eldritch_blast` | Void Surge |
| `cure_wounds` | Field Mend |
| `healing_word` | Pulse Restore |
| `magic_missile` | Arc Pulse |
| `divine_smite` | Oathflare Strike |

## Implemented Feature Labels

The authoritative mapping is `FEATURE_PUBLIC_LABELS` in `public_terms.py`. Keep new feature text short, mechanical, and original to this game.

Important public labels already in place include:

- Battle Surge
- Rally Note
- Lantern Surge
- Field Medic Doctrine
- Second Breath
- Close Form
- Oath Mend
- Route Sense
- Veilstrike
- Pattern Recovery
- Lowlight Sight
- Signal Distance
- Forged Presence
- Riverfolk Endurance

## Future Work

1. Decide whether the released rules layer keeps an explicit SRD attribution path or continues toward fully original surface language.
2. Keep all future spell or feature design in short original implementation notes, not adapted rulebook prose.
3. Update tests only after player-facing labels are wired through the relevant display helpers.
