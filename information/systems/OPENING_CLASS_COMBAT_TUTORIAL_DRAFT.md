# Opening Class Combat Tutorial Draft

Greywake's sparring rail needs one lesson that changes shape around the player's class. The drill should sit on the current Frontier Primer board beside companions, equipment, trading, and resting.

## Goals

- Teach the player's class through combat actions the player can repeat later.
- Keep the drill sandboxed like the other opening tutorial lanes.
- Use a live combat action menu for the sparring move, with no enemy turn and no reward payout.
- Track completion through tutorial flags, then restore the player's real state.

## Warrior Track

The Warrior lesson uses the split-rail dummy and the shield line.

- Weapon Read: read Defense, Avoidance, Stability, and the best answer.
- Take Guard Stance: feel the defensive tradeoff.
- Shove: see Stability become the target.
- Warrior Rally: spend Grit to guard or steady an ally.

## Mage Track

The Mage lesson uses a copper-wired dummy that answers with weak sparks.

- Pattern Read: identify the weakest resist lane.
- Ground: spend the bonus action to steady the next channel.
- Minor Channel: spend MP and attack the read lane.

## Rogue Track

The Rogue lesson uses a dummy with a loose red strap around the ribs.

- Mark Target: make the next hit matter.
- Strike with the class weapon: trigger Veilstrike from the mark and show Edge pressure.

## Runtime Notes

- Add `combat` to `OPENING_TUTORIAL_LESSON_ORDER`.
- Create a tutorial-only sparring target with high HP and no post-combat reward path.
- Track combat events through `record_opening_tutorial_event` while `opening_tutorial_combat_lesson_active` is set.
- Add a level-one Rogue `Mark Target` bonus action so the Rogue tutorial teaches a visible action instead of a hidden helper.
