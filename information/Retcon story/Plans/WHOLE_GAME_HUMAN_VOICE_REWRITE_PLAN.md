# Whole-Game Human Voice Rewrite Plan

This pass keeps canon, branching logic, metrics, scene order, and named concepts in place.

The job is sentence surgery. We are changing rhythm, syntax, framing, and word choice so the game reads like somebody walked the road, touched the wet rope, and wrote down what mattered.

You can hear the drift most clearly when a scene explains itself twice before it trusts the image on the page.

## Rewrite Guardrails

Keep these fixed unless a separate canon plan says otherwise:

- Act structure, scene order, quest flow, and branch consequences
- Factions, companions, villains, towns, roads, ruins, and approved Aethrune proper nouns
- Scene ids, quest ids, save keys, flags, method names, and test-facing internal identifiers
- Reward logic, companion thresholds, metric changes, and combat behavior
- Public lore direction already established in the Aethrune retcon docs

Change these everywhere the prose feels machine-shaped:

- Thesis-first sentence structure
- Mirror-heavy sentence pairs
- Abstract emphasis words that float above the scene
- Repeated contrast phrases such as `not just`, `not merely`, `not only`, `in truth`, `at its core`, and `the real`
- Filler section labels such as `overview`, `core identity`, and `importance`

## Audit Snapshot

The direct phrase scan is already enough to show where the first passes belong. This count only tracks the hard-rule phrases from `AGENTS.md`; it does not catch every bland or symmetric sentence.

- `dnd_game`: 14 files with direct phrase hits
- `information/Story`: 15 files with direct phrase hits
- `information/Retcon story`: 12 files with direct phrase hits
- `information/catalogs`: 3 files with direct phrase hits
- `information/systems`: 1 file with direct phrase hits
- `android_port`: 2 files with direct phrase hits

Highest-value live files from the scan:

- `dnd_game/gameplay/story_intro.py`
- `dnd_game/gameplay/map_system.py`
- `dnd_game/gameplay/story_town_hub.py`
- `dnd_game/gameplay/story_act2_scaffold.py`
- `dnd_game/data/story/lore.py`

Highest-value design and lore files from the scan:

- `information/Story/ACT2_LOCATION_BRANCH_PACKETS.md`
- `information/Story/archive/legacy_drafts/ACT2_CONYBERRY_AGATHA_DRAFT.md`
- `information/Story/ACT2_GLASSWATER_INTAKE_DRAFT.md`
- `information/Story/ACT2_CONTENT_REFERENCE.md`
- `information/Story/ACT1_DIALOGUE_REFERENCE.md`
- `information/Retcon story/World/emberway_aethrune_v1.md`
- `information/Retcon story/World/greywake_aethrune_v2.md`

One caution from the audit: `information/catalogs/ITEM_CATALOG.md` throws a huge raw match count if the search includes words like `key`, because the file is full of internal item labels. It still needs a style pass, but it should sit behind the live scene writing.

## Rewrite Target

Every rewritten file should follow the repo voice already set by `information/Story/archive/legacy_drafts/ACT1_PRE_NEVERWINTER_ELIRA_DRAFT.md`, especially the opening around the shrine.

Use these habits on every pass:

- State what the place, person, or conflict is in the first sentence.
- Follow the statement with a concrete object, bodily action, or practical consequence.
- Keep one sentence per section that sounds observed: mud on boots, smoke in cloth, a ledger clasp digging into a thumb.
- Break the symmetry when the paragraph starts to march.
- Let lists hold mechanics, flags, and implementation notes. Let prose carry place and voice.

Preferred sentence moves:

- Direct: `Greywake is a survey city that turned triage into routine.`
- Historical: `Iron Hollow grew around hard claims work and never shook the dust out of its teeth.`
- Observer lens: `Travelers call the Emberway a road; drovers treat it like a wager they keep making anyway.`
- Cause and effect: `Because the Quiet Choir edits infrastructure instead of smashing it, people obey the wrong valve, gate, or route mark before they know they were touched.`

## Pass Order

### 1. Live Desktop Runtime

Start with the text players actually see in the current desktop build.

Primary files:

- `dnd_game/gameplay/story_intro.py`
- `dnd_game/gameplay/story_town_hub.py`
- `dnd_game/gameplay/story_act1_expanded.py`
- `dnd_game/gameplay/story_act2_scaffold.py`
- `dnd_game/gameplay/map_system.py`
- `dnd_game/gameplay/act2/council.py`
- `dnd_game/gameplay/act2/conyberry.py`
- `dnd_game/data/story/lore.py`
- `dnd_game/data/story/dialogue_inputs.py`
- `dnd_game/data/story/camp_banter.py`
- `dnd_game/gameplay/random_encounters.py`

Why this lane comes first:

- it changes what the player reads right now
- it sets the voice target for every later reference doc
- it exposes tests and formatting issues early

Special handling:

- split `map_system.py` by scene cluster instead of doing a blind full-file sweep
- treat choice text, clue text, NPC speech, and room description as the first rewrite targets inside mixed gameplay files

### 2. Active Source-Of-Truth Story Docs

These files feed future implementation and should match the runtime voice.

Primary files:

- `information/Story/ACT1_CONTENT_REFERENCE.md`
- `information/Story/ACT1_DIALOGUE_REFERENCE.md`
- `information/Story/ACT2_CONTENT_REFERENCE.md`
- `information/Story/ACT2_LOCATION_BRANCH_PACKETS.md`
- `information/Story/ACT2_GLASSWATER_INTAKE_DRAFT.md`
- `information/Story/archive/legacy_drafts/COMPANION_DIALOGUE_INPUTS_DRAFT.md`
- `information/Story/archive/legacy_drafts/COMPANION_CAMP_BANTER_DRAFT.md`

Rules for this lane:

- keep tables, condition notes, and implementation bullets
- rewrite any player-facing line, paragraph lead, scene prompt, or location prose
- keep compiled reference files blunt and usable

### 3. Retcon World And Lore Docs

These files decide how later writing sounds. They need cleaner prose before we draft more content from them.

Primary files:

- `information/Retcon story/World/aethrune_world_v1.md`
- `information/Retcon story/World/greywake_aethrune_v2.md`
- `information/Retcon story/World/emberway_aethrune_v1.md`
- `information/Retcon story/World/iron_hollow_aethrune_v5.md`
- `information/Retcon story/World/resonant_vaults_aethrune_v2.md`
- `information/Retcon story/World/stonehollow_aethrune_v1.md`
- `information/Retcon story/Lore/aethrune_v2_world.md`

Special handling:

- keep mechanics notes and implementation checklists in bullets
- turn lore sections back into place-writing with physical detail and motive

### 4. Catalogs, Systems, And Tooling Docs

This lane matters once story voice is stable.

Primary files:

- `information/catalogs/ITEM_CATALOG.md`
- `information/catalogs/NPCS.md`
- `information/catalogs/NPCs_expanded_v3_final.md`
- `information/catalogs/ACT2_ENEMY_EXPANSION_DRAFT.md`
- `information/systems/GAME_SYSTEMS_REFERENCE.md`
- `information/systems/QUEST_SYSTEM_REFERENCE.md`

Rules for this lane:

- keep data dense
- strip puffed-up flavor lines
- replace generic rarity or lore filler with one usable image or one practical consequence

### 5. Historical Drafts And Old Planning Notes

Some files are worth keeping as history. They do not all deserve a full polish pass.

Check these after the live and active-doc lanes are stable:

- `information/Story/archive/legacy_drafts/ACT1_PRE_NEVERWINTER_ELIRA_DRAFT.md`
- `information/Story/archive/legacy_drafts/MIRA_NEVERWINTER_DIALOGUE_DRAFT.md`
- `information/Story/archive/legacy_drafts/ACT2_CONYBERRY_AGATHA_DRAFT.md`
- older plan files that still guide implementation

For each historical file, choose one:

- rewrite it because the team still reads from it
- trim it and add a stronger historical note
- archive it from the active workflow

### 6. Android Mirror

Mirror only after the desktop wording is settled.

Primary files:

- `android_port/dnd_game/gameplay/story_intro.py`
- `android_port/dnd_game/data/story/lore.py`
- any Android mirror file that still exposes desktop prose from rewritten desktop sources

The Android pass should copy approved desktop wording where the code paths still match. It should not invent a second voice.

## Working Method

Use small batches. A good batch is two to four files from the same lane.

For each file:

1. Scan for the hard-rule phrases and obvious thesis leads.
2. Mark the canon facts, flags, rewards, and route consequences that must survive untouched.
3. Rewrite paragraph by paragraph, starting with scene openers, NPC speech, clues, and branch-result text.
4. Read the changed section aloud. Flat rhythm shows up fast when you hear it.
5. Run targeted tests if the file is part of runtime code.
6. Record any remaining weak sections instead of pretending the file is fully clean.

## Acceptance Checklist

A file is ready to leave the batch when all of these are true:

- no direct hard-rule phrase hits remain unless they appear inside a quoted rule list or a historical note
- the opening sentence of each prose section states the subject cleanly
- the section carries at least one local detail, human motive, or concrete consequence
- mirrored sentence structure has been broken where it made the prose sound staged
- scene logic, ids, quest flow, rewards, and branching outcomes still match the old version
- tests pass for any runtime edit

## First Rewrite Queue

Start here unless another production need interrupts the order:

1. `dnd_game/gameplay/story_intro.py`
2. `dnd_game/data/story/lore.py`
3. `dnd_game/gameplay/story_town_hub.py`
4. `dnd_game/gameplay/map_system.py` Act 1 slices
5. `dnd_game/gameplay/story_act2_scaffold.py`
6. `information/Story/ACT2_CONTENT_REFERENCE.md`
7. `information/Story/ACT2_LOCATION_BRANCH_PACKETS.md`
8. `information/Retcon story/World/greywake_aethrune_v2.md`
9. `information/Retcon story/World/emberway_aethrune_v1.md`
10. Android mirror sync for the rewritten desktop files

That queue puts the road, the town, the lore codex, and the first big planning packets under the same hand before the rewrite spreads outward.
