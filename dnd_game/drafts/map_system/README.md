# Hybrid Map System Draft

This folder is a draft-only add-on for a future map layer. Nothing here is wired into the current playable game.

## Subfolders

- `docs/`: design notes and flow documentation
- `runtime/`: draft models, unlock logic, and presentation helpers
- `data/`: Act 1 sample blueprint
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

## Preview

```bash
python -m dnd_game.drafts.map_system.examples.act1_preview
```
