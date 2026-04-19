# Secret Act 4 Plan: The Unwritten Road

This document plans an optional secret Act 4 unlocked after the Act 3 midpoint reveal and finale work.

Design rule:

- Secret Act 4 must not reveal a bigger villain behind Malzurath.
- Malzurath remains the final true antagonist.
- Act 4 exists to resolve the deeper consequence of the Ninth Ledger: whether anyone, god, devil, institution, or story system should be allowed to own the record of choices before they are made.

## Core Pitch

Secret Act 4 is `The Unwritten Road`.

After the party exposes Malzurath, Keeper of the Ninth Ledger, Act 3 can end with the Ledger damaged, sealed, bargained with, or partially rewritten. Secret Act 4 opens only if the party has enough contradictory, mercy-driven, companion-anchored, or system-breaking choices to find a route the Ledger cannot pre-count.

The act is not about defeating a stronger enemy. It is about entering the blank margin beneath the Ledger and deciding what freedom costs.

Player-facing fantasy:

> You walk the road made from every choice the world failed to predict.

## Unlock Philosophy

Secret Act 4 should feel earned but not require a perfect run.

It should reward:

- Resisting optimization when mercy mattered.
- Preserving companion trust and contradictory testimony.
- Understanding the Forge lens before the reveal.
- Carrying counter-cadence instead of only raw power.
- Keeping enough map integrity that the world has routes left to defend.
- Saving some `unrecorded_choice_tokens` through the Act 3 finale.

It should not require:

- One exact party composition.
- Perfect Act 1 or Act 2 play.
- Forgiving Varyn.
- Choosing every "good" option.
- Having all companions alive and present.

## Unlock Conditions

Recommended implementation:

Use a helper such as `secret_act4_unlocked() -> bool`.

Minimum gate:

- `malzurath_revealed == True`
- `act3_ninth_ledger_opened == True`
- `act3_finale_resolved == True`

Then require either the primary route or a narrow fallback route.

### Primary Route

Unlock if at least four of these are true:

| Condition | Meaning |
| --- | --- |
| `counter_cadence_known` | The party preserved a way to answer Ledger pressure without obeying it. |
| `act3_lens_understood` | The party understands the Forge as a lens rather than only a battlefield. |
| `act3_map_integrity >= 3` | The world still has coherent routes to defend. |
| `unrecorded_choice_tokens >= 2` | The party saved enough unrecorded agency to cross the blank route. |
| `ninth_ledger_pressure <= 2` | Malzurath is weakened enough that the margin can be reached. |
| `act3_varyn_outcome in {"witness", "unmade", "bitter_ally"}` | Varyn's route-knowledge is available as testimony, absence, or reluctant proof. |
| `act3_companion_testimony_count >= 2` | Companions have enough trust or resolved arcs to contradict the Ledger. |
| `act3_mercy_or_contradiction_count >= 2` | The player repeatedly chose outcomes the Ledger could not reduce to profit or force. |

### Fallback Route

Unlock if all of these are true:

- `unrecorded_choice_tokens >= 3`
- `act3_lens_understood == True`
- `ninth_ledger_pressure <= 3`

This lets a smaller, lonelier party reach Act 4 through exceptional mechanical counterplay.

## New Flags

| Flag | Purpose |
| --- | --- |
| `secret_act4_unlocked` | Secret Act 4 is available after the Act 3 finale. |
| `act4_started` | Secret Act 4 has begun. |
| `act4_unwritten_road_entered` | The party crossed into the blank margin beneath the Ledger. |
| `act4_margin_integrity` | Derived value for how stable the Unwritten Road remains. |
| `act4_record_debt` | Cost accumulated when the party spends future-defying choices. |
| `act4_companion_anchor_count` | Number of companions whose trust or resolved arcs can anchor the road. |
| `act4_varyn_testimony` | Whether Varyn contributes as witness, absence, prisoner, or bitter ally. |
| `act4_ledger_authority_broken` | Malzurath no longer owns future records. |
| `act4_ledger_sealed` | The Ledger is contained rather than destroyed. |
| `act4_ledger_burned` | The Ledger is destroyed at high cost. |
| `act4_ninth_page_rewritten` | Secret best ending state. |
| `act4_bargain_accepted` | Ambiguous or bad secret ending state. |

## Derived Values

### `act4_margin_integrity() -> int`

Initial formula target:

- Start at `2`.
- Add `+1` if `act3_map_integrity >= 4`.
- Add `+1` if `act3_lens_understood`.
- Add `+1` if `counter_cadence_known`.
- Add `+1` if `act3_companion_testimony_count >= 2`.
- Subtract `1` if `ninth_ledger_pressure >= 4`.
- Subtract `1` if `act4_record_debt >= 2`.
- Clamp to `0..5`.

### `act4_companion_anchor_count() -> int`

Count companions who meet at least one of:

- Disposition is Great or Exceptional.
- Personal arc resolved.
- They were directly involved in Ledger counterplay.
- They were protected by an unrecorded choice.

Recommended cap for mechanical use: `0..3`.

### `act4_record_debt`

Record debt is the price of forcing impossible outcomes.

Increase it when the player:

- Spends an unrecorded choice token to erase a recorded consequence.
- Saves a companion from a Ledger-locked fate.
- Opens an ending route that should be closed.
- Forces Varyn's testimony to remain coherent if he is unstable or half-unmade.

High record debt should not hard-fail the act, but it should change the ending cost.

## Act Structure

Secret Act 4 should be short, dense, and reactive. It should feel like a capstone, not a second campaign.

Recommended route:

1. `act4_unwritten_threshold`
2. `act4_witness_crossroads`
3. `act4_blank_archive`
4. `act4_varyn_last_route`
5. `act4_ninth_page`
6. `act4_final_accounting`

## Scene Drafts

### 1. Unwritten Threshold

Purpose:

- Confirm Act 4 unlock.
- Spend or preserve the first unrecorded choice.
- Establish that the party has entered a road the Ledger cannot pre-count.

Core image:

- A road made of blank milestones.
- The party's shadows point in different directions.
- The map shows a route only while nobody looks directly at it.

Choices:

- Step onto the road with no explanation.
- Ask a companion to anchor the first mile.
- Force the Ledger to acknowledge the blank route.

Flags:

- Set `act4_started`.
- Set `act4_unwritten_road_entered`.
- Initialize `act4_margin_integrity`.

### 2. Witness Crossroads

Purpose:

- Let companion trust matter.
- Convert companion arcs into active testimony against the Ledger.

Possible witnesses:

- Irielle answers the Ledger with counter-cadence.
- Nim proves the Forge lens was a reader, not an author.
- Bryn testifies that hidden routes can be mercy, not only evasion.
- Elira testifies that mercy is not an accounting error.
- Rhogar testifies that vows can bind the speaker without owning the future.
- Tolan testifies that survival is not proof the dead were meant to die.

Mechanic:

- Each successful witness adds to `act4_companion_anchor_count`.
- Failed or absent witnesses may raise `act4_record_debt`.

### 3. Blank Archive

Purpose:

- Reveal what Malzurath cannot understand: choices without extractable value.
- Give the player a non-combat puzzle or moral route.

Core image:

- Shelves filled with empty ledgers.
- Pages that remain blank when touched by calculation.
- A ninth page that stains only when someone tries to own it.

Choices:

- Preserve the blank archive.
- Burn every record that tries to predict a person.
- Search for the page Malzurath feared.

Outcomes:

- Preserve improves `act4_margin_integrity`.
- Burn lowers pressure but raises `act4_record_debt`.
- Search unlocks `act4_ninth_page_rewrite_ready`.

### 4. Varyn's Last Route

Purpose:

- Resolve Varyn without making him secretly innocent.
- Make his route logic matter one last time.

Possible Varyn states:

| Prior Act 3 outcome | Act 4 use |
| --- | --- |
| `witness` | Varyn names the first route he did not design and accepts blame without controlling the answer. |
| `bitter_ally` | Varyn helps break the Ledger because he cannot bear being owned by a better accountant. |
| `prisoner` | The party can use his testimony, abandon him, or spend a token to preserve his memory. |
| `unmade` | Varyn exists as a missing route; his absence proves Malzurath can erase useful servants too. |
| `destroyed` | No testimony, but the party may find the wound his route logic left behind. |

Rule:

- Do not require forgiving Varyn for the best ending.
- Do not erase his culpability.
- Let him matter because he understood roads, not because he deserves redemption.

### 5. The Ninth Page

Purpose:

- Final choice before ending.
- Turn the Ledger's central mechanism into a player-facing decision.

Core image:

- A page recording the next choice before the player sees the options.
- The words change if the player waits.
- Companions can hold the margins open.

Choices:

- Seal the page.
- Burn the page.
- Rewrite the page.
- Bargain over the page.
- Give Varyn the page, if his Act 4 route permits it.

### 6. Final Accounting

Purpose:

- Resolve Malzurath and the Ledger.
- Apply ending state.
- Return to the world with consequences.

No new villain.

Malzurath's final pressure should be conceptual and personal:

- It offers certainty.
- It offers painless accountability.
- It offers to make every future mistake "someone else's recorded necessity."
- The player rejects, seals, burns, rewrites, or bargains with that offer.

## Endings

### Seal the Ledger

Flags:

- `act4_ledger_sealed = True`
- `act4_ledger_authority_broken = True`

Tone:

- Safest good ending.
- Malzurath is contained.
- Some records survive in sealed custody.
- Future harm is possible, but not inevitable.

Requirements:

- Moderate `act4_margin_integrity`.
- Low or moderate `act4_record_debt`.

### Burn the Ledger

Flags:

- `act4_ledger_burned = True`
- `act4_ledger_authority_broken = True`

Tone:

- Violent freedom ending.
- Predictions break.
- Some true histories are damaged with the false future-records.

Cost:

- Lose some clues, records, public legitimacy, or companion certainty.
- High `act4_record_debt` may scar Phandalin's memory of the campaign.

### Rewrite the Ninth Page

Flags:

- `act4_ninth_page_rewritten = True`
- `act4_ledger_authority_broken = True`

Tone:

- Best secret ending.
- The party does not destroy recordkeeping; they deny it ownership of living choice.
- The Ninth Page becomes a witness page, not a command page.

Requirements:

- `act4_margin_integrity >= 4`
- `act4_companion_anchor_count >= 2`
- `unrecorded_choice_tokens >= 1`
- `act3_lens_understood`
- `counter_cadence_known`

Recommended final line target:

> The page keeps the history. It loses the right to write the next breath.

### Bargain With the Ledger

Flags:

- `act4_bargain_accepted = True`

Tone:

- Bad or ambiguous secret ending.
- The party wins a local mercy or impossible rescue, but leaves a future hook.
- Malzurath's authority is reduced, not ended.

Use when:

- `act4_record_debt` is high.
- The player chooses a closed outcome without enough anchors.
- Varyn or a companion is preserved at a cost the world cannot absorb cleanly.

### Give Varyn the Page

Flags depend on sub-choice:

- `act4_varyn_erased_self`
- `act4_varyn_stole_page`
- `act4_varyn_broke_route`
- `act4_varyn_betrayed_party`

Tone:

- Dangerous alternate ending.
- Available only if Varyn is present in a meaningful Act 4 state.

Possible outcomes:

- Varyn erases himself to break a route he helped build.
- Varyn steals the page and becomes a future problem.
- Varyn breaks the route but refuses redemption.
- Varyn betrays the party if prior mercy/trust was shallow or purely tactical.

## Malzurath In Act 4

Malzurath should be terrifying because he offers a clean answer.

He should not rant.

His language should be precise:

- "I did not steal your choices. I preserved their costs."
- "Freedom without record is merely violence with better lighting."
- "A future uncounted is a debt assigned to the innocent."
- "You call it agency because you survived the outcome."

Counter-language from the party should stress:

- Witness without ownership.
- Memory without prediction.
- Consequence without predestination.
- Responsibility without cosmic accounting.

## Gameplay Mechanics

### Unrecorded Choice Tokens

Act 4 uses remaining `unrecorded_choice_tokens` as the main player-facing resource.

Spend tokens to:

- Reopen a locked choice.
- Prevent a companion fate from being finalized.
- Reject a Ledger-predicted combat opener.
- Change an ending cost.
- Preserve a contradictory witness.

Tokens should be scarce. Recommended Act 4 maximum: `5`.

### Record Debt

Record debt is the shadow of token use.

It should rise when the player forces outcomes the world cannot easily reconcile.

Use debt to:

- Increase final DCs.
- Change ending text.
- Require companion anchors.
- Make the Bargain ending tempting.

### Companion Anchors

Companion anchors are not generic friendship points. Each should name the actual contradiction the companion holds.

Examples:

- Bryn: a hidden road can protect people instead of exploiting them.
- Elira: mercy can be costly without being false.
- Irielle: a learned enemy cadence can become resistance.
- Nim: proof can expose a system without worshiping it.
- Rhogar: a vow can bind the self without controlling another person's future.

## Implementation Slices

### Slice A: Planning And Unlock Helpers

Files:

- `dnd_game/gameplay/story_act4_secret.py`
- `dnd_game/game.py`
- `tests/test_core.py`

Tasks:

1. Add `StoryAct4SecretMixin`.
2. Add `secret_act4_unlocked()`.
3. Add `act4_margin_integrity()`.
4. Add `act4_companion_anchor_count()`.
5. Add tests with synthetic `GameState` objects.

### Slice B: Threshold And Witness Scenes

Scenes:

- `act4_unwritten_threshold`
- `act4_witness_crossroads`

Tasks:

1. Register scene handlers.
2. Add initial Act 4 text and flags.
3. Implement companion anchor beats.
4. Add tests for at least three companion witness paths.

### Slice C: Blank Archive And Varyn Route

Scenes:

- `act4_blank_archive`
- `act4_varyn_last_route`

Tasks:

1. Implement archive choices.
2. Add `act4_record_debt` changes.
3. Implement Varyn state handling.
4. Test Varyn as witness, absence, and betrayal/failure state.

### Slice D: Ninth Page Finale

Scenes:

- `act4_ninth_page`
- `act4_final_accounting`

Tasks:

1. Implement ending choices.
2. Apply ending flags.
3. Add final journal/clue entries.
4. Add ending tests.

### Slice E: Polish And Spoiler Discipline

Tasks:

1. Ensure Act 4 files are not scanned by pre-reveal spoiler tests unless gated appropriately.
2. Add a post-reveal text test that confirms Malzurath may be named in Act 4.
3. Add save/load tests for Act 4 flags.
4. Add player-facing status summary after `malzurath_revealed`.

## Testing Checklist

- Secret Act 4 does not unlock before `malzurath_revealed`.
- Secret Act 4 does not unlock before the Act 3 finale.
- Primary unlock route works with multiple party compositions.
- Fallback unlock route works without perfect companion coverage.
- `act4_margin_integrity` clamps to `0..5`.
- `act4_record_debt` changes ending text but does not hard-crash the act.
- Rewrite ending requires anchors, lens understanding, counter-cadence, and at least one unrecorded choice.
- Varyn can matter without being forgiven.
- Malzurath remains final antagonist; no bigger villain is introduced.

## Open Decisions

- Should Secret Act 4 be reachable after every Act 3 ending, or only after non-bargain endings?
  - Recommendation: every non-total-failure ending, but Bargain starts Act 4 with higher `act4_record_debt`.
- Should Varyn be required for any ending?
  - Recommendation: no. He can improve or complicate routes, but should not be mandatory.
- Should Rewrite the Ninth Page be the canonical best ending?
  - Recommendation: yes, but only as a secret ending.
- Should burning the Ledger damage saved clues or journal entries mechanically?
  - Recommendation: represent this in ending text and flags, not by deleting player records.
- Should Act 4 include combat?
  - Recommendation: one symbolic or pressure-driven encounter at most. The act should lean on choices, witnesses, and route logic.
