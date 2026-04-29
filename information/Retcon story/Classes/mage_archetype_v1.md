# Mage Archetype V1

## Class Role

Mages solve combat by shaping fields, signals, heat, pressure, memory, and attention. They do their best work before the wound appears: a ward catches the spear, a cold line slows the charge, a resonance knot waits under the floor until the enemy steps wrong.

The combat redesign gives Mages a clean split. Physical channel attacks can use Accuracy against Avoidance, then Defense if the effect has a material carrier. Most battlefield channels use Resist Checks. Armor can stop a shard of ice; it cannot talk a frightened mind out of hearing the wrong bell.

Defense values in this draft use percentages. Old shorthand such as `+1 Defense` should be read as `+5% Defense`, and `Armor Break 1` means `-10 percentage points`.

## Shared Mage Rules

### Primary Stats

| Stat | Mage use |
| --- | --- |
| Reason / INT | pattern reading, Arcanist charge logic, channel precision, relic handling |
| Instinct / WIS | field sense, Aethermancer triage, stable channels, signal resistance |
| Presence / CHA | force of projection, command channels, pressure effects, some Elementalist expression |
| Endurance / CON | concentration, backlash survival, overchannel tolerance |
| Agility / DEX | Avoidance, initiative, physical channel aim, escape from melee |
| Might / STR | rare; anchors heavy apparatus and resists forced movement |

Mage builds should pick a casting stat through subclass or discipline. Reason favors sequence and study. Instinct favors healing, wards, and field stability. Presence favors force, fear, and visible projection.

### Baseline Durability

Recommended starting profile:

| Value | Recommendation |
| --- | --- |
| Hit die feel | low to medium HP tier |
| Armor access | clothing, light armor, warded coats |
| Shield access | no mundane shields by default |
| Weapon access | simple weapons, focuses, rods, knives, slings |
| Base Defense scaling | low from gear, higher from wards and sustained channels |
| Base Avoidance scaling | Agility, distance, Mobile stance, reactive channels |
| Save strengths | Reason / INT and Instinct / WIS or Presence / CHA by discipline |

### Mage Resource: Charge

Charge is the broad spellcasting resource. It can represent MP, channel bands, battery pressure, prepared inscriptions, or breath-counted working time in implementation.

Recommended rules:

```text
Maximum Charge = 6 + 4 * level + casting stat modifier, minimum 6
Minor channels cost 1 Charge in combat
Standard channels cost 3 to 5 Charge
Reactive channels cost 2 to 4 Charge
Overchannels cost the base channel plus extra Charge and risk
Recover Charge through long rest, selected short-rest features, items, and rare scene anchors
```

The existing MP system can serve as Charge during migration.

### Secondary Resource: Focus

Focus is optional for advanced Mage builds. It rewards setup and protects the class from turning every turn into the same channel.

```text
Focus cap = 5
Gain 1 Focus when a channel changes the battlefield, exploits a prepared condition, protects an ally from real damage, or hits a target's weak resist lane
Spend Focus on quickened wards, overchannel control, extra riders, and subclass releases
Focus clears after combat unless a feature preserves 1
```

Focus should be smaller than Charge and more tactical.

### Shared Mage Actions

| Action | Cost | Effect |
| --- | --- | --- |
| Minor Channel | action, 1 Charge | Reliable low-cost channel. Uses attack roll or Resist Check by design. |
| Standard Channel | action, 3-5 Charge | Main combat channel. Damage, healing, control, summon, or field effect. |
| Reactive Channel | reaction, 2-4 Charge | Ward, interrupt, redirect, or emergency shield. |
| Sustain | action or bonus action | Maintain an active field, ward, or summoned effect. |
| Pattern Read | bonus action | Identify lowest Resist Check, active channel, ward shell, or terrain conductor. |
| Ground | bonus action | Reduce backlash risk and gain `+1` on concentration-style checks. |
| Overchannel | rider | Spend extra Charge for stronger effect with backlash chance. |
| Break Channel | action | Attempt to disrupt an enemy channel through a Resist Check or opposed casting stat. |

### Channel Categories

| Category | Main job | Resolution hook |
| --- | --- | --- |
| Pulse | direct force or energy | Accuracy or Resist Check by shape |
| Field | zone, barrier, aura, ground effect | Resist Check on entry or start of turn |
| Ward | prevention, shield, reflect | reaction or sustain |
| Mend | healing, stabilization, condition repair | no attack roll, sometimes triage limit |
| Pattern | reveal, mark, debuff, prediction | Resist Check or utility check |
| Element | fire, cold, lightning, acid, stone, air | often Resist Check with terrain riders |
| Signal | fear, charm, command, memory pressure | Resist Check |
| Anchor | lock movement, protect space, stabilize field | sustain and Stability interaction |

### Shared Mage Stances

| Stance | Effect | Notes |
| --- | --- | --- |
| Grounded | `+2` to backlash and concentration checks, `-1` Avoidance | safer overchannels |
| Quickcast | `+1` initiative and reactive channel timing, `-1` channel DC | fast warding |
| Wide Pattern | `+1` area size or secondary target, `+1` Charge cost | field control |
| Narrow Pattern | `+1` channel DC or Accuracy against one target | duels and bosses |
| Veiled | `+1` Avoidance, channel reveal effects are weaker | defensive caster stance |

### Shared Passive Tags

| Passive | Effect |
| --- | --- |
| Channel Habit | Minor channels cost no extra focus action to prepare. |
| Steady Hands | `+1` to checks that maintain channels after damage. |
| Field Sense | Pattern Read can identify hazardous terrain and enemy fields. |
| Backlash Scar | Once per combat, reduce overchannel backlash by training bonus. |
| Long Breath | Sustained channels last one additional round. |
| Warded Coat | Clothing or light armor grants `+5%` Defense while a ward is active. |
| Counter-Cadence | Gain `+1` Resist Check against signal, fear, and charm channels. |
| Focused Eye | First successful Pattern Read each combat grants `1` Focus. |

## Level Progression

| Level | Mage progression |
| ---: | --- |
| 1 | Choose Mage. Gain Minor Channel, Pattern Read, Ground, one discipline channel, and one Tier 1 technique. |
| 2 | Choose one Tier 1 technique or passive. Gain Focus if the build uses it. |
| 3 | Choose Spellguard, Aethermancer, Arcanist, or Elementalist. Gain signature feature and one subclass technique. |
| 4 | Choose class or subclass technique. Choose stat increase or feat. |
| 5 | Power spike: gain Overchannel or an archetype equivalent. Upgrade one known technique. |
| 6 | Choose utility technique and passive. Unlock improved stances. |
| 7 | Choose subclass specialization path. |
| 8 | Choose any known-tier technique. Choose stat increase or feat. |
| 9 | Gain advanced technique. Master one existing technique. |
| 10 | Choose capstone. Gain final archetype passive. |

### Overchannel

At level 5, most Mages gain Overchannel: spend extra Charge to intensify a known channel.

| Overchannel type | Effect |
| --- | --- |
| Force | increase damage or healing dice |
| Reach | increase range or target count |
| Shape | make a field safer for allies or harder for enemies |
| Hold | extend duration |
| Pierce | raise channel DC or ignore partial resistance |

Backlash check:

```text
d20 + Endurance or casting stat modifier vs 10 + extra Charge spent
Failure causes self-damage, Reeling, Charge leak, or field instability by channel type
```

## Archetype 1: Spellguard

### Combat Read

Spellguards are ward tanks. They turn Charge into layered protection, catch hostile channels, and anchor allies inside safer space. Their Defense comes from projected shells, pressure lines, and enemy eyes pulled to the brightest ward.

The Spellguard's best turn feels like a door drawn in the air. The enemy can see the party through it. Getting through is the problem.

### Role

| Role axis | Spellguard position |
| --- | --- |
| Party role | Tank |
| Damage style | reflected pressure, pulse counters, ward bursts |
| Protection style | wards, anchors, ward-draw, redirects, damage splitting |
| Preferred armor | warded coats, light armor, focus bracers |
| Preferred focuses | shields of glass, iron rings, rods, chalk lines, sigil plates |
| Primary stats | Instinct or Reason |
| Secondary stats | Endurance, Presence |
| Weak points | Charge drain, silence, anti-channel enemies, physical grapples |

### Resource: Ward

Ward is a temporary barrier value created by Spellguard techniques.

```text
Ward cap = 8 + level + casting stat modifier
Gain Ward by casting defensive channels, grounding, or intercepting channel damage
Ward absorbs damage before temporary HP
Physical attacks reduce Ward after Defense if the ward is personal
Field wards can protect allies before their own Defense
Unused Ward fades after combat
```

Ward should feel sturdy, but it needs upkeep and Charge.

### Signature Feature: Anchor Shell

Create an Anchor Shell around self or an adjacent ally for `2` rounds.

Effects:

- target gains Ward equal to `2 + casting stat modifier`
- target gains `+5%` Defense against physical damage while Ward remains
- target pulls enemy priority while Ward remains
- enemies attacking another ally take `-1` Accuracy if they can perceive the shell
- first hostile channel against the target grants the Spellguard `1` Focus
- if the shell breaks from a single hit, the attacker becomes Reeling 1

### Spellguard Techniques

| Technique | Tier | Cost | Effect |
| --- | ---: | --- | --- |
| Anchor Shell | signature | bonus action, 3 Charge | Grant Ward and `+5%` Defense to self or ally. While Ward remains, the shelled target pulls enemy priority. |
| Ward Shell | 1 | reaction, 2 Charge | Reduce incoming damage by `1d6 + casting stat modifier`. |
| Lockstep Field | 1 | action, 3 Charge | Adjacent allies gain Guarded 1 and `+1` Stability. |
| Blue Glass Palm | 1 | action, 1 Charge | Minor force pulse. On failed Resist Check, apply Reeling 1 and Fixated 1 on the Spellguard. |
| Brace The Pattern | 1 | bonus action | Gain `+2` to the next channel maintenance check. |
| Catch Spark | 2 | reaction, 3 Charge | Reduce elemental or force channel damage. If reduced to `0`, gain `1` Focus. |
| Return The Edge | 2 | 2 Focus | After a ward absorbs damage, deal small force damage to the attacker. |
| Quiet Ring | 2 | action, 4 Charge | Field zone. Allies inside gain `+1` Resist Checks against fear, charm, and signal. |
| Iron Air | 2 | passive | While Grounded, personal Ward also grants `+1` Stability. |
| Split Harm | 3 | reaction, 2 Focus | Divide one incoming hit between two warded allies before Defense. |
| Hold The Door | 3 | action, 5 Charge | Create a barrier lane. Enemies crossing make a Resist Check or lose movement and become Reeling. |
| Shell Memory | 3 | passive | First ward broken each combat refunds `1` Charge. |
| Turn Channel | 4 | reaction, 5 Charge, 2 Focus | Attempt to redirect a hostile channel to a new legal target or empty space. |
| Redoubt Pulse | 4 | action, 4 Focus | Burst from all active wards, damaging nearby enemies and refreshing Guarded 1 on allies. |
| Last Blue Wall | capstone | 6 Charge, 5 Focus | For one round, all allies gain Ward. The first ally reduced to `0` HP stays at `1` if any Ward remains. |

### Spellguard Specialization Paths

| Path | Focus | Features |
| --- | --- | --- |
| Redoubt | party-wide protection | larger fields, shared Ward, barrier lanes |
| Mirror | counter-channeling | reflects, redirects, interrupts |
| Anchor | personal tanking | higher Ward, better Stability, anti-grapple tools |

### Spellguard Upgrade Examples

| Base technique | Upgrade | Effect |
| --- | --- | --- |
| Anchor Shell | Deep Nail | Shell grants extra Stability and resists forced movement. |
| Ward Shell | Clean Angle | If damage is reduced to `0`, apply Reeling 1 to attacker. |
| Catch Spark | Bottle Lightning | Store a reduced elemental hit for bonus damage on next pulse. |
| Hold The Door | Painted Threshold | Allies can cross the barrier without losing movement. |
| Turn Channel | Empty Hand | On success, regain `1` Focus. |

### Spellguard Combat Loop

1. Place Anchor Shell on the ally meant to catch pressure.
2. Ground when a large channel or boss turn is coming.
3. Use reactions to catch spikes.
4. Build Focus from absorbed damage and hostile channels.
5. Spend Focus on reflection, splitting harm, or a redoubt burst.

### Spellguard Tuning Notes

- Ward should prevent spikes, then require real upkeep.
- Spellguard should struggle when enemies use grapples, poison delivery, mundane swarms, or Charge drain.
- Reflections should be satisfying without replacing DPS classes.
- Their turn economy needs tension between shielding now and setting a stronger field later.

## Archetype 2: Aethermancer

### Combat Read

Aethermancers are resource healers. They mend bodies, stabilize breath, turn excess healing into shields, and use field placement to make recovery predictable. They are strongest when the party plays inside their prepared routes.

Their work should feel practical. Bandage clips hang from the focus strap. The floor mark is chalk over old blood. The healing field hums like a kettle left too long on iron.

### Role

| Role axis | Aethermancer position |
| --- | --- |
| Party role | Heal |
| Damage style | low direct damage, pressure through radiant or force pulses |
| Healing style | burst heals, fields, shield overflow, condition repair |
| Preferred armor | clothing, light armor, medic harness |
| Preferred focuses | lantern focus, bone needle, silver spool, field kit |
| Primary stats | Instinct |
| Secondary stats | Reason, Endurance |
| Weak points | burst damage through multiple allies, anti-heal effects, forced movement from healing fields |

### Resource: Flow

Flow tracks healing rhythm.

```text
Flow cap = 5
Gain 1 Flow when you heal an ally below half HP
Gain 1 Flow when a field heals two or more allies
Gain 1 Flow when excess healing becomes Ward or temporary HP
Spend Flow on quick heals, condition clearing, overflow shields, and field pulses
Flow falls by 1 at combat end, unless a feature stores it as a scene support flag
```

### Signature Feature: Field Mend

Heal one ally for `1d8 + casting stat modifier`. Excess healing becomes Ward up to the Aethermancer's training bonus.

If the target was at `0` HP, the heal costs `1` extra Charge or applies Reeling 1 to the Aethermancer. Emergency recovery should have a visible price.

### Aethermancer Techniques

| Technique | Tier | Cost | Effect |
| --- | ---: | --- | --- |
| Field Mend | signature | action, 3 Charge | Heal target. Excess becomes small Ward. |
| Pulse Restore | 1 | bonus action, 4 Charge | Small ranged heal, `1d4 + casting stat modifier`. |
| Triage Line | 1 | action, 3 Charge | Place a short field. First ally entering or starting there heals `1d4`. |
| Clean Breath | 1 | action, 2 Charge | Reduce Poisoned, Bleeding, or Reeling duration by `1`; heal `1`. |
| Steady Pulse | 1 | passive | Healing an ally below half HP grants `1` Flow once per round. |
| Overflow Shell | 2 | 1 Flow | Convert excess healing into Ward for another ally in range. |
| Silver Thread | 2 | action, 4 Charge | Link two allies. The next heal on one also heals the other for half. |
| Pain Map | 2 | bonus action | Pattern Read for ally injuries. Next heal gains `+1` per harmful condition on target, max `+3`. |
| Soft Floor | 2 | action, 4 Charge | Field zone. Allies inside gain `+5%` Defense against the first physical hit each round. |
| Borrowed Breath | 3 | reaction, 2 Flow, 4 Charge | When an ally drops to `0`, heal them for `1d4` and apply Reeling 1. |
| Overmend | 3 | overchannel | Add extra healing dice. Backlash applies self-Reeling or Charge leak. |
| Clear Fever | 3 | action, 5 Charge | Remove one major condition or reduce two minor conditions. |
| Wound Choir | 4 | 4 Flow | Heal all allies for a small amount; allies below half HP heal extra. |
| Field Surgeon | 4 | passive | First condition clear each combat refunds `1` Charge. |
| Everyone Still Breathing | capstone | 6 Charge, 5 Flow | Restore all conscious allies and revive one ally at `0` HP. Excess healing becomes Ward. |

### Aethermancer Specialization Paths

| Path | Focus | Features |
| --- | --- | --- |
| Field Doctor | condition clearing | stronger triage, poison and bleeding answers |
| Wellspring | throughput | bigger heals, overflow shields |
| Route-Keeper | field placement | persistent healing zones, movement support |

### Aethermancer Upgrade Examples

| Base technique | Upgrade | Effect |
| --- | --- | --- |
| Field Mend | Warm Hand | Target also clears Reeling if healed above half HP. |
| Triage Line | Chalked Route | Field can move one step each round as a bonus action. |
| Clean Breath | Bitter Draught | Also grants `+1` Endurance Resist Check until next turn. |
| Silver Thread | Double Knot | Link lasts one extra heal. |
| Wound Choir | Low Hymn | Allies at `0` HP stabilize before healing resolves. |

### Aethermancer Combat Loop

1. Read the party's injury shape.
2. Place a field where the party can stand without losing tempo.
3. Heal low allies to build Flow.
4. Turn excess healing into Ward.
5. Save reactions and Flow for collapse moments.

### Aethermancer Tuning Notes

- Healing should be strong enough to change plans, but Charge should matter.
- Field placement should reward party formation.
- Overhealing into Ward gives skilled players value without wasting turns.
- Anti-heal, displacement, and multi-target pressure should create hard choices.

## Archetype 3: Arcanist

### Combat Read

Arcanists are sequence casters. They place marks, build charge patterns, then release a burst that feels earned. They reward planning, target reading, and clean timing.

An Arcanist fight should leave little evidence before the release: three chalk cuts on a pillar, a copper taste in the air, then every loose nail in the room points the same way.

### Role

| Role axis | Arcanist position |
| --- | --- |
| Party role | DPS |
| Damage style | setup into burst, force and signal damage |
| Protection style | distance, Veiled stance, small wards |
| Preferred armor | clothing, light armor |
| Preferred focuses | rods, etched cards, rings, geometry plates |
| Primary stats | Reason |
| Secondary stats | Endurance, Agility |
| Weak points | interrupted setup, target death before release, fast melee pressure |

### Resource: Arc

Arc marks a prepared pattern.

```text
Arc cap = 6
Gain 1 Arc when a channel hits, a target fails a Resist Check, Pattern Read reveals a weakness, or a setup field triggers
Spend Arc on releases, extra targets, precision, and overchannel control
Arc on a target fades by 1 each round if the Arcanist does not affect that target
```

Arc can be tracked globally for simplicity, or per target for deeper implementation.

### Signature Feature: Pattern Charge

After successfully affecting a target with a channel, place Pattern Charge 1 on it. At Pattern Charge 3, the Arcanist can release the pattern for bonus damage or control.

Pattern Charge should appear in the UI as a small count:

```text
Pattern Charge: 2
```

### Arcanist Techniques

| Technique | Tier | Cost | Effect |
| --- | ---: | --- | --- |
| Pattern Charge | signature | passive | Channels build charges on affected targets. |
| Arc Pulse | 1 | action, 1 Charge | Minor force channel. Reliable damage, builds Pattern Charge on hit. |
| Marked Angle | 1 | bonus action, 1 Charge | Apply Pattern Charge 1 if Pattern Read succeeded this turn. |
| Glass Step | 1 | reaction, 2 Charge | Gain `+2` Avoidance against one attack, then move a short distance if it misses. |
| Quiet Sum | 1 | passive | First Pattern Read each combat grants `1` Arc. |
| Detonate Pattern | 2 | action, 2 Arc | Consume Pattern Charge for force damage. Damage scales with charges. |
| Forked Proof | 2 | 1 Arc | Next single-target channel can jump to a second target for reduced effect. |
| Exact Line | 2 | stance upgrade | Narrow Pattern grants an additional `+1` channel DC against charged targets. |
| Lock Formula | 2 | action, 3 Charge | Target makes Reason or Instinct Resist Check. On failure, Reeling and Pattern Charge 1. |
| Stored Answer | 3 | reaction, 2 Arc | When a charged target attacks, release one charge to impose `-2` Accuracy. |
| Collapse Sequence | 3 | action, 3 Arc, 4 Charge | Burst charged target. If it drops, remaining charge jumps to nearby enemy. |
| Patient Diagram | 3 | passive | Pattern Charge cap increases by `1`; charges fade slower. |
| Prism Release | 4 | 4 Arc, 5 Charge | Release charges from up to three targets at once. |
| Clean The Board | 4 | passive | Dropping a charged target refunds `1` Charge and grants `1` Arc. |
| The Last Equation | capstone | 6 Arc, 6 Charge | Convert all Pattern Charges in the encounter into a single burst, then apply Reeling to survivors that failed Resist Checks. |

### Arcanist Specialization Paths

| Path | Focus | Features |
| --- | --- | --- |
| Geometer | controlled setup | stronger marks, safer releases |
| Rupturist | burst damage | bigger detonations, riskier overchannels |
| Mnemonicist | signal and mind | memory pressure, debuffs, prediction |

### Arcanist Upgrade Examples

| Base technique | Upgrade | Effect |
| --- | --- | --- |
| Arc Pulse | Needle Pulse | Gains `+1` Accuracy or DC against charged targets. |
| Marked Angle | Chalk Under Nail | Can be used after an ally hits the target. |
| Detonate Pattern | Clean Break | If released at max charges, apply Reeling 1. |
| Stored Answer | Already Solved | If the attack misses, gain `1` Arc. |
| Prism Release | Three Cut Proof | One released target can be behind partial cover. |

### Arcanist Combat Loop

1. Pattern Read the best target.
2. Apply Pattern Charge with minor and standard channels.
3. Protect setup with Glass Step or distance.
4. Release when the charge count or battlefield shape is right.
5. Chain charge to a new target if the first target drops.

### Arcanist Tuning Notes

- Baseline turns should feel useful while building toward release.
- Burst should beat other Mage paths only after setup.
- Enemies that cleanse marks, force movement, or die too early create friction.
- UI needs clear charge counts and release previews.

## Archetype 4: Elementalist

### Combat Read

Elementalists shape fire, cold, lightning, acid, stone, air, and pressure. They are flexible damage casters with terrain memory. Their best fights become messy in a controlled way: water carries lightning, frost locks mud, flame eats rope, stone dust blinds a corridor.

They reward a player who notices the room.

### Role

| Role axis | Elementalist position |
| --- | --- |
| Party role | DPS |
| Damage style | flexible elements, AoE, terrain riders |
| Protection style | range, control fields, resistance tricks |
| Preferred armor | clothing, light armor |
| Preferred focuses | ember glass, frost wire, storm nail, acid vial, stone tile |
| Primary stats | Presence or Reason |
| Secondary stats | Instinct, Agility |
| Weak points | resistant enemies, friendly-fire risk, tight rooms, Charge hunger |

### Resource: Attunement

Attunement tracks the current element and combo potential.

```text
Choose one active Attunement: fire, cold, lightning, acid, stone, or air
Gain 1 Attunement stack when you cast an element channel matching the active element
Switching element clears stacks unless a feature preserves them
Spend stacks on riders, combo channels, resistance pierce, and terrain effects
Attunement cap = 4
```

### Signature Feature: Elemental Weave

The Elementalist can combine the current element with a previous element once per round.

| Pair | Rider |
| --- | --- |
| Fire + Air | spread Burning or extend flame field |
| Fire + Acid | reduce Defense or apply Armor Break to physical gear |
| Fire + Stone | create hot shrapnel, partial Defense applies |
| Cold + Water/Mud | slow, Prone risk, movement penalty |
| Cold + Lightning | shock lock, Reeling on failed Resist Check |
| Lightning + Metal | bonus Accuracy or DC against armored targets |
| Stone + Air | dust screen, Avoidance changes |
| Acid + Stone | weaken cover and armor |

The implementation can start with three elements, then expand.

### Elementalist Techniques

| Technique | Tier | Cost | Effect |
| --- | ---: | --- | --- |
| Elemental Weave | signature | passive | Combine current and previous element for a rider once per round. |
| Ember Lance | 1 | action, 1 Charge | Fire minor channel. Damage plus Burning chance. |
| Frost Shard | 1 | action, 1 Charge | Cold minor channel. Damage plus movement penalty. |
| Volt Grasp | 1 | action, 1 Charge | Lightning melee channel. Damage plus reaction disruption. |
| Stone Flick | 1 | action, 1 Charge | Physical channel. Accuracy vs Avoidance, then Defense. |
| Change Weather In The Hand | 2 | bonus action | Switch active element and preserve `1` Attunement stack. |
| Burning Line | 2 | action, 4 Charge | Fire field. Enemies crossing make Agility Resist Check or burn. |
| Lockfrost | 2 | action, 4 Charge | Cold field. Slows and can apply Prone on failed Resist Check. |
| Storm Hook | 2 | action, 4 Charge | Lightning jumps to Marked or metal-bearing target. |
| Bitter Rain | 3 | action, 5 Charge | Acid zone. Reduces Defense by `10 percentage points` for enemies that fail Resist Check. |
| Glass Heat | 3 | 2 Attunement | Fire overchannel with reduced backlash if target is already Burning. |
| Thundering Nail | 3 | 2 Attunement | Lightning burst. Applies Reeling and interrupts channels on failed Resist Check. |
| Stone Lung | 3 | reaction, 3 Charge | Gain resistance to physical shrapnel or debris; create dust cover. |
| Weather Turns Mean | 4 | 4 Attunement | Cast two different element minor channels as one action against legal targets. |
| Elemental Focus | 4 | passive | Choose one element. Ignore the first point of matching resistance. |
| The Room Remembers | capstone | 6 Charge, 4 Attunement | Trigger every active elemental field once, then apply a combined rider to the largest enemy cluster. |

### Elementalist Specialization Paths

| Path | Focus | Features |
| --- | --- | --- |
| Pyre-Singer | fire and spread | Burning, field growth, morale pressure |
| Stormwright | lightning and metal | jumps, interrupts, armored target punishment |
| Cold Mason | cold and stone | slow, cover, choke control |
| Bitter Hand | acid and armor | Defense reduction, cover destruction |

### Elementalist Upgrade Examples

| Base technique | Upgrade | Effect |
| --- | --- | --- |
| Ember Lance | Coal Bite | Burning lasts one extra round on failed Resist Check. |
| Frost Shard | White Joint | Slowed targets also lose `1` Avoidance. |
| Storm Hook | Copper Knows | Marked metal-bearing targets take extra damage. |
| Bitter Rain | Pitted Buckle | Defense reduction can become Armor Break 1 on strong failure. |
| The Room Remembers | Old Ash Answers | The capstone leaves one field active after triggering. |

### Elementalist Combat Loop

1. Read enemy resistances and room materials.
2. Choose an active element.
3. Create or exploit a field.
4. Switch elements when a combo rider is worth the stack cost.
5. Spend Attunement on field bursts, resistance pierce, or multi-channel turns.

### Elementalist Tuning Notes

- Elementalist should have the broadest damage coverage.
- Their strongest turns should need terrain, Attunement, or enemy clustering.
- Friendly-fire and field placement should matter in cramped rooms.
- Resistant enemies should redirect choices rather than shut the archetype down.

## Mage Ability Tiers

### Tier 1: Levels 1-3

| Ability | Archetype | Use |
| --- | --- | --- |
| Ward Shell | Spellguard | emergency prevention |
| Field Mend | Aethermancer | direct healing |
| Arc Pulse | Arcanist | charge setup |
| Ember Lance | Elementalist | baseline fire pressure |
| Pattern Read | shared | reveal resist lanes |
| Ground | shared | safer overchannels |

### Tier 2: Levels 3-6

| Ability | Archetype | Use |
| --- | --- | --- |
| Catch Spark | Spellguard | channel mitigation |
| Silver Thread | Aethermancer | linked healing |
| Detonate Pattern | Arcanist | release setup |
| Burning Line | Elementalist | field damage |

### Tier 3: Levels 5-8

| Ability | Archetype | Use |
| --- | --- | --- |
| Hold The Door | Spellguard | barrier control |
| Borrowed Breath | Aethermancer | emergency recovery |
| Collapse Sequence | Arcanist | burst chain |
| Bitter Rain | Elementalist | Defense pressure |

### Tier 4: Levels 9-10

| Ability | Archetype | Use |
| --- | --- | --- |
| Last Blue Wall | Spellguard | party survival round |
| Everyone Still Breathing | Aethermancer | mass recovery |
| The Last Equation | Arcanist | encounter-wide release |
| The Room Remembers | Elementalist | field climax |

## Feat Ideas For Mages

| Feat | Effect |
| --- | --- |
| Warded Hands | Reactive channels cost `1` less Charge once per combat. |
| Longform Channeler | Sustained fields last one additional round outside combat. |
| Bitter Focus | Overchannel backlash cannot reduce you below `1` HP once per long rest. |
| Signal Anchor | Gain `+1` Resist Checks against fear, charm, and signal. |
| Field Cartographer | Pattern Read also reveals terrain conductors. |
| Quick Chalk | First field placed each combat costs no bonus action setup. |
| Elemental Tolerance | After taking elemental damage, gain brief resistance to that element. |
| Clean Release | Detonations and field triggers spare one adjacent ally once per combat. |

## Equipment Hooks

| Item trait | Mage interaction |
| --- | --- |
| Warded | Grants small Ward when combat starts. |
| Conductive | Improves lightning channels and increases lightning risk. |
| Insulated | Improves elemental resistance, weakens some projection channels. |
| Etched | Pattern Read gains `+1` against channels of matching school. |
| Reservoir | Stores `1` Charge, refills after rest or anchor scene. |
| Focused | `+1` DC or Accuracy for one channel family. |
| Grounding | Reduces backlash and movement. |
| Lantern-Bound | Healing and signal channels gain range in dark or smoky scenes. |

## Party Synergies

| Partner style | Mage synergy |
| --- | --- |
| Juggernaut | pins enemies inside fields and protects caster setup |
| Bloodreaver | marks help channel focus; healing layers with Ward |
| Berserker | Aethermancer temp Ward supports risk windows |
| Weapon Master | Pattern Read and Weapon Read combine into weakness play |
| Shadowguard | decoys and misdirection keep casters safe |
| Alchemist | oils and reagents create terrain conductors |
| Assassin | Arcanist marks help execute setup |
| Poisoner | Elementalist fields slow enemies inside poison zones |

## Enemy Counters

| Counter | Best against | Why |
| --- | --- | --- |
| Charge drain | all Mages | pressures the resource base |
| Silence or channel disruption | Arcanist, Aethermancer | interrupts setup and healing |
| Fast grapplers | Spellguard, Arcanist | bypass distance and force physical checks |
| Element resistance | Elementalist | forces switching and stack loss |
| Anti-heal curses | Aethermancer | blocks recovery loop |
| Ward-piercing attacks | Spellguard | cuts through prevention |
| Mark cleansing | Arcanist | resets Pattern Charge |
| Scatter AI | Elementalist | avoids field clusters |

## UI Presentation

Mage turns should show resource and active setup.

```text
Elira - HP 19/24 - Defense 10% - Avoidance +2 - Charge 18/24 - Focus 2 - Stance: Grounded
Arcanist target: Pattern Charge 2
Elementalist: Active Attunement Fire 3
Spellguard: Ward 7
```

Resolution text should say whether armor, a save, or a ward mattered.

```text
Ward Shell catches the spear. 8 damage meets Defense 10%, then Ward absorbs 6 -> 1 HP damage.
The raider fails the cold Resist Check. Lockfrost takes their footing and leaves them Reeling.
Pattern Charge reaches 3. The copper marks hum under the target's boots.
Ember Lance hits the shield edge. Defense reduces the physical carrier, but Burning still tests Endurance.
```

## Implementation Notes

Recommended first Mage slice:

1. Treat current MP as Charge.
2. Keep current save-based spells on Resist Checks.
3. Add Pattern Read for enemy weakest save and resistance tags.
4. Implement Spellguard Ward because it tests prevention against new Defense.
5. Implement Aethermancer Field Mend and Overflow Shell after Ward exists.
6. Implement Arcanist Pattern Charge after status counters are stable.
7. Implement Elementalist with fire, cold, and lightning before adding acid, stone, and air.

## Open Design Questions

- Should every Mage use the same Charge formula, or should subclasses alter recovery?
- Should Focus be a shared Mage resource or a subclass-only system?
- Should physical channels apply Defense before or after elemental riders?
- Should Overchannel backlash be self-damage, Charge loss, a condition, or field instability by channel?
- Should Spellguard Ward be temporary HP in code or a separate shield layer?
- Should Aethermancer healing fields follow map positions, abstract party lanes, or both?
- Should Arcanist Pattern Charge track per target for depth or globally for speed?
- Should Elementalist launch with three elements and expand later?
