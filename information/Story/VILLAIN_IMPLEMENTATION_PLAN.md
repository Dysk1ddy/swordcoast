# Villain Implementation Plan

This plan turns `VILLAIN_INTEGRATION_DRAFT.md` into staged code and content work.

Primary rule:

- Varyn Sable can be explicit from Act 1 onward.
- Malzurath must not be apparent as a second villain until the middle of planned Act 3.
- Pre-reveal runtime text may imply "the signal," "the answer," "the deep ledger," or "something below," but must not name Malzurath or confirm a hidden architect.

## Current Code Seams

The existing code already supports the implementation without a save migration.

| Area | Current seam | Implementation use |
| --- | --- | --- |
| Save state | `GameState.flags` in `dnd_game/models.py` serializes arbitrary keys. | Add villain telemetry and Act 3 handoff flags directly. |
| Act 1 live route | `dnd_game/gameplay/map_system.py` owns the current room-based Act 1 path. | Primary place for Varyn route-pattern flags, Cistern Eye hints, and Varyn defeat retcon. |
| Legacy Act 1 route | `dnd_game/gameplay/story_act1_expanded.py` still has older parallel scene text. | Mirror only critical text if reachable or if tests cover it; avoid broad legacy churn. |
| Act 2 scaffold | `dnd_game/gameplay/story_act2_scaffold.py` records metrics and Act 3 handoff flags. | Add masked signal flags and future Act 3 profile derivation here. |
| Act 2 live map scenes | `dnd_game/gameplay/map_system.py` owns playable local-map Act 2 dungeons. | Add masked language and hidden flags in South Adit, Forge, and Caldra resolution. |
| Journal/clues | `dnd_game/gameplay/journal.py` dedupes clues and journal entries. | Use normal clues for visible facts; use flags only for secret Malzurath setup. |
| Tests | `tests/test_core.py` already covers Act 1/Act 2 flags, clues, journal, and save round trips. | Add regression tests for flags and spoiler discipline. |

## Implementation Strategy

Implement in four slices:

1. Act 1 Varyn retcon and hidden telemetry.
2. Act 2 masked signal and Act 3 handoff prep.
3. Act 3 planning scaffolds and derived profile helpers.
4. Act 3 reveal and post-reveal mechanics.

Slices 1 and 2 are safe to implement now because they improve existing playable/scaffolded content without requiring a full Act 3 runtime.

Slices 3 and 4 should wait until the Act 3 route structure is being built.

## Progress

- Slice 1 is implemented: Act 1 now records Varyn route telemetry, preserves the Act 1 victory, and avoids naming the secret villain in runtime text.
- Slice 2 is implemented: Act 2 now records masked signal/lens/counter-cadence handoff flags, Sabotage Night pattern profile flags, and spoiler-safe Caldra foreshadowing.
- Slice 3 is implemented: Act 3 setup helpers now derive map integrity, Varyn's apparent prediction profile, masked pressure labels, and future counterplay tokens without changing the playable flow.
- Slice 4 is implemented as a gated midpoint reveal: `act3_ninth_ledger_opens` names Malzurath, converts hidden pressure into visible Ninth Ledger pressure, and exposes unrecorded choice tokens for post-reveal counterplay.
- Optional secret Act 4 planning lives in `SECRET_ACT4_PLAN.md` as a capstone route after the Act 3 finale.

## Slice 1: Act 1 Varyn Retcon And Telemetry

Goal:

- Preserve the player's Act 1 victory.
- Make Varyn's return possible through route-displacement language.
- Begin tracking player understanding of Varyn's system without exposing Malzurath.

### Code touch points

Primary:

- `dnd_game/gameplay/map_system.py`

Likely methods/scenes:

- High Road false checkpoint and false tollstone resolution.
- Old Owl Well supply trench route-note resolution.
- Wyvern Tor drover/shrine route evidence.
- Cinderfall relay completion.
- Tresendar Cistern Eye bargain/deceive lore.
- Emberhall ledger/archive choices.
- Varyn boss resolution around the Act 1 completion text.

Secondary:

- `dnd_game/gameplay/story_intro.py`
  - Only if adding prologue or High Road telemetry not already covered by map flow.
- `dnd_game/gameplay/story_act1_expanded.py`
  - Only mirror changes if those legacy methods remain reachable or tests assert their text.

### Flags to add

| Flag | Set when | Visible to player |
| --- | --- | --- |
| `system_profile_seeded` | Early predictive paperwork or route authority touches the player. | No |
| `varyn_route_pattern_seen` | Player exposes fake checkpoint, false toll, or route-authority corruption. | No |
| `varyn_filter_logic_seen` | Player reads Old Owl Well or equivalent filtering notes. | No |
| `varyn_detour_logic_seen` | Player learns detours are used to control travelers. | No |
| `varyn_relay_broken` | Player destroys Cinderfall's relay. | No |
| `deep_ledger_hint_count` | Player accepts risky Cistern Eye knowledge. | No |
| `emberhall_impossible_exit_seen` | Player decoded Varyn's exits before the boss and notices one impossible route after. | Optional clue, but not as Malzurath lore |
| `varyn_body_defeated_act1` | Varyn boss encounter is won. | No |
| `varyn_route_displaced` | Act 1 end records that Varyn exited through route displacement. | No |
| `act1_ashen_brand_broken` | Act 1 still resolves as a real victory. | No |

### Text changes

Varyn finale should change from:

- "Varyn falls..." and "Varyn is dead..."

To:

- The Ashen Brand falls.
- Varyn's Act 1 body or local presence is defeated.
- The last route behaves impossibly if the player earned the ledger context.
- The town still wins Act 1.

Safe wording target:

> Varyn falls, but not cleanly. The body, cloak, and blade hit the cellar stones while the route behind him seems to fold the wrong way. The Ashen Brand breaks around that absence, and the pressure that bent every road into Phandalin finally snaps.

For fractured victory, avoid "Varyn is dead." Use:

> Varyn's local command is broken, but too many threads were left burning behind him.

### Tests

Add or update tests in `tests/test_core.py`:

- Act 1 epilogue flags include `varyn_body_defeated_act1`, `varyn_route_displaced`, and `act1_ashen_brand_broken`.
- Act 1 victory tier logic is unchanged.
- Varyn finale text no longer requires `Varyn is dead`.
- Save/load round trip preserves new flags through `GameState.to_dict()` and `from_dict()`.
- Pre-Act 3 runtime Act 1 text added by this slice does not contain `Malzurath`.

### Acceptance criteria

- Existing Act 1 flow still completes and saves.
- Act 2 can still begin from `scene_act1_complete`.
- No visible Malzurath reveal is introduced.
- Player victory is not undercut: Phandalin is safer and the Ashen Brand is broken.

## Slice 2: Act 2 Masked Signal And Handoff Prep

Goal:

- Make Act 2 feel like control of truth and dangerous knowledge.
- Record enough hidden state for Act 3 without telling the player there is a second villain.
- Keep Caldra Voss and the Quiet Choir as the surface antagonists.

### Code touch points

Primary:

- `dnd_game/gameplay/story_act2_scaffold.py`
  - `act2_record_epilogue_flags`
  - `start_act2_scaffold`
  - claims council
  - sabotage night helper logic
  - Act 2 complete summary

- `dnd_game/gameplay/map_system.py`
  - South Adit and Irielle recruitment/support beats
  - Black Lake shrine/causeway beats
  - Forge threshold, choir pit, anvil, shard channels, resonance lens, and Caldra dais

Secondary:

- `dnd_game/drafts/map_system/data/act2_enemy_map.py`
  - Only update summaries/tags if map previews or docs need the new handoff concepts.

### Flags to add

| Flag | Set when | Purpose |
| --- | --- | --- |
| `act3_signal_carried` | Act 2 ends with high whisper pressure or the party carries contaminated knowledge. | Starts Act 3 with stronger hidden pressure. |
| `act3_lens_understood` | Forge lens is mapped before or during Caldra resolution. | Lets Act 3 name the instrument accurately after reveal. |
| `act3_lens_blinded` | Caldra is defeated without lens mapping. | Lets Act 3 work from damaged aftermath instead of clean explanation. |
| `counter_cadence_known` | Irielle is recruited or her counter-cadence is preserved. | Later counter to post-reveal Ledger pressure. |
| `pattern_preserves_institutions` | Sabotage Night priority protects claims hall / civic order. | Varyn prediction profile input. |
| `pattern_preserves_people` | Sabotage Night priority protects shrine lane / civilians. | Varyn prediction profile input. |
| `pattern_hunts_systems` | Sabotage Night priority hunts infiltrators / route rewriting. | Varyn prediction profile input. |

### Text changes

Act 2 text may use:

- "the signal"
- "the answer"
- "the account"
- "the ninth page" only as Pact/Choir numerology, not a named villain
- "the Forge is a lens"
- "the mine answers"

Act 2 text must not use:

- `Malzurath`
- "the true master"
- "the hidden architect" as a literal entity
- "second villain"
- "devil behind the Choir"

Recommended Caldra line additions:

- "The Forge does not create. It clarifies."
- "Every vow has an echo. Every echo has an owner."
- "The world is loud because it fears being counted."

### Tests

Add tests in `tests/test_core.py`:

- `act2_record_epilogue_flags` sets `act3_signal_carried` when `act2_whisper_pressure >= 4`.
- `act2_record_epilogue_flags` sets `act3_lens_understood` when `forge_lens_mapped` is true.
- `act2_record_epilogue_flags` sets `act3_lens_blinded` when Caldra is defeated without `forge_lens_mapped`.
- Irielle recruitment or her support scene sets `counter_cadence_known`.
- Sabotage Night priority sets exactly one of the three profile seed flags.
- Pre-reveal Act 2 visible clue/journal text does not contain `Malzurath`.

### Acceptance criteria

- Act 2 still records existing handoff flags:
  - `act3_phandalin_state`
  - `act3_claims_balance`
  - `act3_whisper_state`
  - `act3_forge_route_state`
  - `act3_forge_subroutes_cleared`
  - `act3_forge_lens_state`
- New flags are additive and do not break existing tests.
- Caldra remains the visible Act 2 finale villain.

## Slice 3: Act 3 Planning Scaffolds

Goal:

- Prepare Act 3 without implementing the full act yet.
- Derive Varyn's early Act 3 prediction profile from prior choices.
- Keep Malzurath unrevealed until the planned midpoint.

### New code shape

Preferred new module:

- `dnd_game/gameplay/story_act3_scaffold.py`

Composition change:

- Import `StoryAct3ScaffoldMixin` in `dnd_game/game.py`.
- Place it before `StoryEndgameMixin` if it owns new scene methods.

Core helper methods:

- `act3_map_integrity() -> int`
- `act3_player_pattern_profile() -> str`
- `act3_unrecorded_choice_tokens() -> int`
- `act3_hidden_pressure_label() -> str`
- `malzurath_revealed() -> bool`

Reserved flags:

| Flag | Purpose |
| --- | --- |
| `act3_started` | Act 3 has begun. |
| `act3_map_integrity` | Derived map stability value. |
| `player_pattern_profile` | Varyn prediction profile. |
| `act3_varyn_apparent_primary` | Act 3 opens with Varyn as apparent main villain. |
| `malzurath_revealed` | Midpoint reveal has happened. |
| `ninth_ledger_pressure` | Visible post-reveal pressure. |
| `unrecorded_choice_tokens` | Player-facing resource after reveal. |

### Derived map integrity

Initial formula target:

- Start at `2`.
- Add `+1` for `act1_victory_tier == clean_victory`.
- Add `+1` for `act3_claims_balance == secured`.
- Add `+1` for `act3_forge_route_state in {"mastered", "broken"}`.
- Add `+1` for `act3_forge_lens_state == mapped`.
- Subtract `1` for `act3_whisper_state == carried_out`.
- Clamp to `0..5`.

### Derived profile

Initial profile inputs:

- `pattern_preserves_people`
- `pattern_preserves_institutions`
- `pattern_hunts_systems`
- `bryn_ledger_burned` vs `bryn_ledger_sold`
- `elira_mercy_blessing` vs `elira_hard_verdict`
- `act2_sponsor`
- `act2_first_late_route`

Output options:

- `mercy_first`
- `institution_first`
- `route_first`
- `secrecy_first`
- `force_first`
- `chaos_first`
- `balanced`

### Tests

- Helper formula tests with synthetic `GameState` objects.
- Save/load preserves derived values if stored.
- `malzurath_revealed` defaults false.
- Before reveal, Act 3 pressure labels use `Signal`, `Whisper`, or `Map Pressure`, not `Ninth Ledger`.

### Acceptance criteria

- Act 3 scaffold can be imported without changing current playable flow.
- Developer/test snapshots can compute Act 3 setup from existing Act 2 flags.
- No Act 3 early helper exposes Malzurath by default.

## Slice 4: Act 3 Reveal And Post-Reveal Mechanics

Goal:

- Implement the midpoint reveal where the second villain becomes apparent.
- Reframe prior hidden state as the Ninth Ledger.
- Add player-facing counterplay.

### Scene target

Scene:

- `The Ninth Ledger Opens`

Recommended scene id:

- `act3_ninth_ledger_opens`

Reveal sequence:

1. Player corners or disrupts Varyn's living map.
2. A route appears that Varyn did not design.
3. A page records a choice the player has not made yet.
4. Varyn admits the route is not his.
5. Irielle, Nim, or the narration names Malzurath depending on party composition and prior clues.
6. Set `malzurath_revealed = True`.
7. Convert hidden pressure to visible `ninth_ledger_pressure`.

### Post-reveal mechanics

Player-facing systems:

- `ninth_ledger_pressure`
- `unrecorded_choice_tokens`

Counterplay sources:

- Great/Exceptional companion trust.
- Resolved companion arcs.
- `counter_cadence_known`.
- `act3_lens_understood`.
- Messy or mercy-driven choices that resisted pure optimization.

Possible uses for `unrecorded_choice_tokens`:

- Unlock a choice the Ledger marks as closed.
- Cancel one predicted enemy opening.
- Prevent a repeated-tactic penalty.
- Preserve a companion's contradictory testimony against a binding record.

### Tests

- Midpoint scene sets `malzurath_revealed`.
- After reveal, journal/pressure labels may use `Malzurath`, `Ninth Ledger`, and `recorded choice`.
- Before reveal, those strings remain absent from runtime story surfaces.
- Token calculation rewards companion trust/arcs and does not require one exact party composition.

### Acceptance criteria

- Reveal makes earlier clues retroactively meaningful.
- Varyn remains culpable and important, not a decoy.
- Malzurath is not visible as a villain before the reveal scene.
- Post-reveal mechanics preserve choice instead of locking the player into a single correct answer.

## Spoiler Discipline Checks

Add a small test helper or reviewer checklist for visible runtime text.

Pre-reveal forbidden terms:

- `Malzurath`
- `Keeper of the Ninth Ledger`
- `Quiet Architect`
- `true master`
- `second villain`

Allowed pre-reveal terms:

- `signal`
- `answer`
- `deep ledger`
- `ninth page`
- `completed account`
- `Forge lens`
- `something below`

Suggested test approach:

- Do not scan all repository markdown, because planning docs intentionally contain spoilers.
- Scan only runtime Python strings in:
  - `dnd_game/gameplay/story_intro.py`
  - `dnd_game/gameplay/story_act1_expanded.py`
  - `dnd_game/gameplay/story_act2_scaffold.py`
  - `dnd_game/gameplay/map_system.py`
  - future `dnd_game/gameplay/story_act3_scaffold.py`, excluding functions or constants explicitly gated by `malzurath_revealed`.

## First Implementation Task List

Start with Slice 1.

1. Update Varyn Act 1 finale text in `map_system.py`.
2. Set `varyn_body_defeated_act1`, `varyn_route_displaced`, and `act1_ashen_brand_broken` after the Varyn boss win.
3. Add `emberhall_impossible_exit_seen` when the player decoded Emberhall exits before the boss.
4. Set `varyn_relay_broken` when Cinderfall is destroyed.
5. Set `varyn_filter_logic_seen` in Old Owl Well route-note success branches.
6. Set `varyn_detour_logic_seen` in Wyvern Tor drover/detour evidence branches.
7. Increment `deep_ledger_hint_count` only on risky Cistern Eye knowledge paths.
8. Add focused tests for the new flags and text changes.
9. Run `npm.cmd run test:run` if the repo test command is still the active test entrypoint; otherwise run the existing Python test command used by the project.

## Open Decisions

- Should Varyn leave behind an actual body, an empty coat, or a corpse-like echo?
  - Recommendation: corpse-like echo. It preserves the win while making route displacement unsettling.
- Should `deep_ledger_hint_count` be visible in debug views?
  - Recommendation: hidden in normal UI, visible only in developer/debug state dumps if those exist later.
- Should Act 3 make Varyn a bitter temporary ally?
  - Recommendation: allow it as one route, but never require forgiving him for the best ending.
- Should the Ninth Ledger become a journal UI mode after reveal?
  - Recommendation: yes, but only after `malzurath_revealed` is set.
