# Hybrid Map System Draft

This folder started as a draft-only add-on for a future map layer. Parts of it now feed the playable game through the Act 1 and Act 2 map work, while the docs, examples, and helper runtime here still serve as the source-facing design sandbox.

## Subfolders

- `docs/`: design notes and flow documentation
- `runtime/`: draft models, unlock logic, and presentation helpers
- `data/`: Act 1 sample blueprint and Act 2 enemy-driven blueprint
- `examples/`: small preview script

## Design direction

This draft uses a hybrid structure:

- node-based overworld travel for macro progression
- grid-room local maps for hostile sites
- linear quest and flag gates for story pacing

The presentation pass now uses native `rich` layout and panels when available, with a plain-text fallback:

- fixed HUD panel
- overworld map panel
- local map panel for dungeon mode
- rich scene panel and plain-text fallback

## Live integration status

The current playable game now uses ideas from this draft in several places:

- playable Act 1 overworld routing through `Phandalin`, `Old Owl Well`, hidden `Cinderfall Ruins`, `Wyvern Tor`, `Ashfall Watch`, `Tresendar Manor`, and `Emberhall Cellars`
- room-based Act 1 dungeon progression for those hostile sites, including branch-and-reconverge layouts
- Act 1 route reactivity such as hidden-route unlocks, `Town Fear` / `Ashen Strength` / `Survivors Saved` tracking, and the `clean` / `costly` / `fractured` ending-tier carryover
- Ashfall-specific payoff hooks where `Cinderfall` sabotage changes later enemy setup
- richer Act 2 map requirements such as flag counts, numeric thresholds, and route-order checks
- read-only Act 2 route rendering through the in-game `map` command
- playable local maps for `Stonehollow Dig`, `Broken Prospect`, `South Adit`, `Wave Echo Outer Galleries`, `Black Lake Causeway`, and the `Forge of Spells`
- Act II pressure panels, journal summaries, and camp digest surfaces tied to the expedition state
- Act 3 handoff flags for Forge route state, cleared subroutes, and resonance-lens outcome

## Preview

```bash
python -m dnd_game.drafts.map_system.examples.act1_preview
python -m dnd_game.drafts.map_system.examples.act2_preview
```
