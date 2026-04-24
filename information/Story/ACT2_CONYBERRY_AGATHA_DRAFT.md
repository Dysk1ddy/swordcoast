# Act 2 Location Draft: Conyberry and Agatha's Circuit

## Purpose

This file upgrades `Conyberry and Agatha's Circuit` from a mostly single-scene early lead into a branch-heavy Act 2 location draft.

It should preserve the core live payoff already present in `dnd_game/gameplay/story_act2_scaffold.py`:

- Agatha can confirm the southern adit matters.
- Agatha can warn that the Forge is being used as a listening lens.
- Delaying Conyberry should still damage the quality of that warning.

What changes here is everything around that payoff. Conyberry should become a location about who can carry a frightening truth, how damaged warning becomes political material, and whether the old Pact reads as fear, law, or moral restraint.

## Story Role

Conyberry is the early lead that teaches the player three things before the act turns more overtly subterranean:

1. The old Pact distributed custody so no one claimant could weaponize Wave Echo's deeper properties alone.
2. The Quiet Choir is already attacking systems of restraint and the people who keep them.
3. The party will keep facing the same question in Act 2:
   - do you tell everyone what is wrong
   - tell only the people who can use it
   - or bind the truth to something safer than public speech

Conyberry should play like a test case for the whole act. Pilgrims, graves, and ward signs let the player handle public warning before the story drops underground.

## Placement

- Best taken as the first or second early lead.
- If completed before `Sabotage Night`, it becomes one of the cleanest warning routes in the act.
- If delayed past the midpoint trigger, the site should still be playable, but the warning arrives through damaged sanctity, worse rumor, and more obvious Quiet Choir interference.

## Core Theme

The branch packet is about:

- warning versus leverage
- grief versus use
- sacred restraint versus frontier opportunism

Conyberry should ask whether the party can carry truth without immediately turning it into property.

## Local Mechanic: Circuit Strain

Conyberry should use a small location-specific state that determines how cleanly Agatha's warning survives the route.

### Definition

- `Circuit Strain` measures how damaged, frightened, or overdrawn Agatha's circuit has become while the party is inside it.
- It is not the same as global `Whisper Pressure`, but it should feed into it.

### Starting Value

- normal route: `0`
- delayed route: `1`

### Raises Strain

- choosing fear-heavy or coercive options in front of fragile witnesses
- stripping holy or funerary space for expedient leverage
- copying the defiled sigil instead of simply breaking it
- forcing a third branch scene after the circuit is already calling the party inward
- leaving the dead unnamed while harvesting information from their resting place

### Lowers Or Holds Strain

- calming the pilgrims
- relighting the chapel
- naming the dead aloud
- breaking the sigil cleanly
- treating Agatha like testimony rather than an extraction target

### Payoff Thresholds

- `0 to 1`: clean warning
- `2 to 3`: bruised warning
- `4 or more`: fractured warning

The site can still be completed at higher strain, but the truth leaves Conyberry colder, less shareable, and more politically unstable.

## Structural Model

Recommended total shape:

- 7 to 9 scenes
- 1 opening social pressure scene
- 3 mid-route branch sites
- 1 optional watcher pursuit or witness scene
- 1 final Agatha audience
- 1 exit decision about custody of the warning

Recommended physical route:

1. `Hushed Pilgrim Road`
2. `Waymarker Cairn`
3. branch into:
   - `Chapel of Lamps`
   - `Grave Ring`
   - `Defiled Sigil`
4. optional `Watcher Cut`
5. `Agatha's Bower`
6. `Return Road`

## Flow Rule: Two Clean Sites, Then A Cost

Conyberry should not let the player have every branch without pressure.

- After the opening road scene, the party can choose the order of the three core branch sites.
- The first two branch sites can be resolved cleanly.
- After the second site, Agatha's bower starts actively calling the route inward.
- The player can still force the third site before meeting Agatha, but doing so should:
  - add `+1 Circuit Strain`
  - shift the tone from careful testimony to intrusive delay
  - make Agatha treat the party as claimants who kept her waiting on purpose

This keeps the branch structure rich without making Conyberry feel consequence-free.

## Companion Hooks

### Elira Dawnmantle

Conyberry should be one of Elira's defining early Act 2 field-faith locations.

Strongest beats:

- calming the pilgrims
- relighting the chapel
- naming the dead
- choosing whether warning should be carried publicly or bound to warding

Key thematic role:

- Elira should keep insisting that sacred work is not less practical because it is holy.
- She should frame Conyberry as a place where the living still owe discipline to the dead.

### Bryn Underbough

Bryn should turn Conyberry's social scenes into sharper investigative scenes.

Strongest beats:

- isolating the clean witness from the pilgrim cluster
- reading who is lying from fear versus advantage
- spotting claimant marks in the grave ring
- noticing where a defiled sigil has been handled by practical hands rather than zealots alone

Key thematic role:

- Bryn should remind the player that frightened people still move papers, hide names, and make deals.

### Halia / Sponsor Pressure

Halia should not be present in the field, but Conyberry's exit decision should be able to create a later sponsor reaction.

- She dislikes broad warning.
- She respects controlled truth.
- She is suspicious of bound or withheld warning unless it produces a usable edge.

### Linene / Sponsor Pressure

- Linene should favor a warning that can actually keep workers and routes alive.
- She respects public clarity more than Halia does.
- She can tolerate restricted warning if the player has a clear operational reason.

### Elira + Daran / Warden Pressure

- They strongly favor the civic and containment routes.
- They are the least comfortable with leverage-driven use of Agatha's truth.

## Exact Dialogue Packet: Elira, Bryn, and Agatha

This packet is meant to give the route a usable writing voice before implementation. These are not all mandatory lines, but they establish how the three most important speakers should sound across the full Conyberry route.

## Elira Packet

Elira should sound disciplined, reverent, and practical in a way that keeps proving those are not separate things.

### Route Offer

- "Ask cleanly. The dead can tell when the living arrive already rehearsing what they want to hear."

### Hushed Pilgrim Road

- "Panic spreads faster when someone respectable pretends it is caution. Start with the frightened. The rest will follow what the room becomes."
- If the player chooses the clean-witness route:
  - "Take the clearest witness if you must. Just do not teach the others that only precise fear is worth answering."
- If the player follows the wrongness first:
  - "Then do it quickly. I will not have the road think we stepped around the living to get to the mystery."

### Chapel Of Lamps

- "This is not ornamental faith. This is maintenance made holy because strangers depended on it."
- If the player relights the chapel:
  - "Good. Let the road remember that service and obedience were not meant to become the same word."
- If the player takes the basin lantern:
  - "If we carry it, we carry it as responsibility, not salvage."
- If the player quarantines the chapel:
  - "I do not like leaving it dark. I dislike teaching wounded sanctity to perform for us even less."

### Grave Ring

- "Say the names if you can. The dead should not have to compete with our urgency to stay real."
- If claim marks are found:
  - "Then the living have already tried to use grief as cover. That is a smaller sin than murder and closer to the same shape than people admit."

### Defiled Sigil

- "Look at the neatness of it. Somebody wanted the ward to keep the posture of service while answering the wrong will."
- If the player copies the sigil:
  - "Be careful. There is a kind of understanding that always pretends it can stay clean."
- If the player breaks it:
  - "Better broken than obedient to the wrong voice."

### Agatha Audience

- "We are here to hear, not to own."
- If the player asks for public warning:
  - "Then ask for what the town can survive hearing, not for the sharpest shape of the wound."
- If the player asks about Pact restraint:
  - "Ask what the dead were still disciplined enough to fear."

### Exit Decision

- If the player shares the warning:
  - "Good. Fear travels easily enough. Truth should not arrive gagged."
- If the player restricts the warning:
  - "Then keep your hands clean enough to know when control becomes vanity."
- If the player binds the warning:
  - "That is still a burden, not an escape from one."

## Bryn Packet

Bryn should sound sharp, practical, and unromantic without collapsing the route into cynicism. She is useful because she notices where fear is already becoming paperwork.

### Route Offer

- "Everyone gets mystical about ruins right before someone starts profiting from them. If Conyberry is active again, somebody is already bookkeeping the holiness."

### Hushed Pilgrim Road

- "Watch which one keeps correcting their own story. That is never just fear. That is someone testing which version sounds safest."
- If the player steadies the whole group:
  - "Fair. Just remember half the room will tell the cleanest lie they can once they calm down enough to choose one."
- If the player isolates a witness:
  - "Good. The truth is usually in the person trying hardest not to sound like they own any."

### Waymarker Cairn

- "Old stone, new handling marks. Somebody wants this road to stay abandoned in public and usable in private."

### Grave Ring

- "There. See the later scratch? Not devotional, not funerary, and much too careful. Somebody hid practical business under sacred neglect."
- If claim marks are found:
  - "That is not cult handwriting. That is claimant handwriting wearing cult weather."

### Defiled Sigil

- "The clever part is not the sigil. It is making the damage look like nobody practical could have been involved."
- If the player baits a watcher:
  - "Good. Dead wards do not file reports. Living hands do."
- If the player copies the sigil:
  - "Take only what you can explain later without sounding like them."

### Agatha Audience

- "Ask the question that gives us a person, a payment, or a route. Dread is easy to come by."
- If the player asks who is lying in the claims war:
  - "Good. Hauntings are miserable. Hauntings with ledgers are how towns actually get taken."

### Exit Decision

- If the player shares the warning publicly:
  - "Useful, if your goal is to make sure nobody can quietly move around it anymore."
- If the player restricts it:
  - "That is not dishonorable. It is only dishonorable if we start pretending control and stewardship are the same thing."
- If the player binds it:
  - "Then we had better mean it. Bound truth is still controlled truth with prettier manners."

## Agatha Packet

Agatha should sound like testimony that resents extraction but still recognizes disciplined listeners when she sees them.

### First Appearance

- "You are late enough to be dangerous and early enough to matter."
- "The living always arrive wanting warning clean enough to carry and terrible enough to obey."

### If The Road Was Handled Well

- If pilgrims were steadied:
  - "At least you did not begin by teaching the frightened that fear must earn eloquence before it deserves mercy."
- If the chapel was relit:
  - "Someone still remembered the lamps were for service, not display."
- If the dead were named:
  - "Good. The road is less lonely than when you arrived."

### If The Road Was Handled Poorly

- If the sigil was copied:
  - "You brought me theft with your reverence and expect me to separate the two."
- If the route was overdrawn:
  - "You made the circuit wait like a claimant at a locked office and still expect witness from it."
- If delayed:
  - "They touched the circuit before you did. That is why I sound smaller than the truth."

### Public Warning Ask

- "Then hear what can still be carried without breaking in transit: the southern handling road was never dead, and the Forge is being taught to listen instead of merely make."

### Claims-War Ask

- "You still want names. Very well. The living always trust corruption more quickly when it has handwriting."

### Pact-Restraint Ask

- "The Pact divided the burden because no one hand was meant to turn this place into an answer."
- "Wave Echo was valuable. That is not why they feared it."

### On The Quiet Choir

- "They teach as they defile. That is why their damage keeps the posture of order."
- "They would rather teach a ward to obey than simply shatter it. That is how wrong devotion announces ambition."

### Exit-Decision Reactions

- If the warning is shared widely:
  - "Then let it travel honestly, even if honesty makes cowards of half the room for a while."
- If the warning is restricted:
  - "Control is the oldest temptation of anyone who survives hearing too much."
- If the warning is bound:
  - "Better bound than cheaply spent. Better shared than hoarded. You are learning why the living kept failing this place."

## Exact Scene Beat Sheet

## Beat 0: The Route Offer

This can remain mostly a hub or dialogue-input beat, but the framing should sharpen.

Suggested opening line:

- "Conyberry is not where you go for a shortcut. It is where you go when the dead may still be the cleanest witnesses left."

Suggested prompt:

- "Why are you going to Conyberry first?"

Suggested answer families:

1. "The town needs warning before it needs courage."
2. "Somebody is already using old holy ground as cover. I want the hand behind the cover."
3. "If the mine is teaching something wrong, I want the oldest place that might still know the right lesson."

These choices should not lock the route, but they can color the first companion commentary and the earliest flag.

Suggested flags:

- `conyberry_entry_civic`
- `conyberry_entry_leverage`
- `conyberry_entry_containment`

## Beat 1: Hushed Pilgrim Road

### Opening Text

- "The road to Conyberry is all blown grass, old stone, and the feeling that too many footsteps ended here without ever becoming history. Ahead, a knot of pilgrims, peddlers, and hired carriers stands in the road like people who are ashamed of how frightened they already are."

If delayed:

- "The knot in the road is smaller than it should be. Someone already left rather than be seen here, and the ones who remained have had longer to teach each other the wrong version."

### Primary Prompt

- "How do you answer the frightened road before the circuit answers it for you?"

### Options

1. `Persuasion` or `Religion`: steady the whole group openly.
2. `Insight` or `Investigation`: isolate the cleanest witness quietly.
3. `Survival` or `Arcana`: follow the one story that changed in the telling.

### Outcomes

#### Civic Outcome: Steady The Road

- lowers or holds `Circuit Strain`
- improves later public-warning credibility
- gives Elira a strong opening beat

Suggested flag:

- `conyberry_pilgrims_steadied`

#### Leverage Outcome: Take The Clean Witness

- increases route precision
- gives the player one cleaner question later
- leaves the larger group shakier

Suggested flag:

- `conyberry_clean_witness_taken`

#### Containment Outcome: Track The Wrongness

- best anti-whisper read
- rougher social tone
- can reveal the location of the defiled sigil or watcher cut early

Suggested flag:

- `conyberry_whisper_track_named`

## Beat 2: Waymarker Cairn

This beat should convert the road from mood into route logic.

### Opening Text

- "A broken waymarker cairn still points nowhere useful, but somebody has touched it recently. Old devotional scratches sit beside newer handling marks, as if practical hands wanted the road to keep looking abandoned while still being readable to the right people."

### Function

- This is the route-shaping beat.
- It should set which branch site the party reaches first, and whether they understand the circuit as holy route, claimant cover, or contamination line.

### Options

1. Read the cairn as a warded waymarker.
   - points first toward `Chapel of Lamps`
2. Read the cairn as tampered funerary marking.
   - points first toward `Grave Ring`
3. Read the cairn as a disguised trail correction.
   - points first toward `Defiled Sigil`

Suggested flags:

- `conyberry_cairn_ward_read`
- `conyberry_cairn_grave_read`
- `conyberry_cairn_trail_read`

## Beat 3A: Chapel Of Lamps

### Opening Text

- "The chapel is hardly bigger than a roadside shelter: lamp niches, a basin, and a wall hammered with the sort of practical prayer people write when they know strangers live or die by unseen maintenance."

### Core Question

- Is the chapel a public sacred site, a field resource, or something too damaged to use at all?

### Options

1. Relight the chapel and wake one clean ward.
2. Take the basin lantern and field wards into the circuit.
3. Seal the chapel and leave it untouched by further hands.

### Outcomes

#### Relight

- strongest civic route
- lowers or holds `Circuit Strain`
- best public-warning support
- strong Elira scene

Suggested flags:

- `conyberry_chapel_relit`
- `elira_field_lantern` if Elira is present and the player invites her to carry it

#### Field Lantern

- hybrid route
- grants practical anti-whisper edge later
- sacrifices some public sanctity

Suggested flag:

- `conyberry_field_lantern_taken`

#### Quarantine

- strongest containment route
- denies everyone easy use
- makes Agatha more likely to see the party as careful rather than reverent

Suggested flag:

- `conyberry_chapel_quarantined`

## Beat 3B: Grave Ring

### Opening Text

- "The grave ring is not dramatic. That is what makes it worse. Low stones, weather-soft names, and a circle that still feels organized enough to shame anyone trying to treat it like scenery."

### Core Question

- Does the party treat the dead here as witnesses, a source of hidden route logic, or a boundary that should not be mined for either?

### Options

1. Read the markers historically.
2. Name the dead aloud and stabilize the ring as memory.
3. Search for later claimant additions and hidden handling marks.

### Outcomes

#### Historical Read

- best Pact-lore route
- helps later shrine and threshold interpretation

Suggested flag:

- `conyberry_grave_history_read`

#### Dead Named

- strongest moral route
- lowers or holds `Circuit Strain`
- makes Agatha more willing to treat the party as people

Suggested flag:

- `conyberry_dead_named`

#### Claim Marks Found

- strongest leverage route
- may implicate a modern claimant or sponsor-adjacent operator
- increases political complexity at the debrief

Suggested flags:

- `conyberry_claim_marks_found`
- `agatha_claim_cover_suspected`

## Beat 3C: Defiled Sigil

### Opening Text

- "Silver nails, chalk geometry, and a wrong neatness sit over older marks like somebody tried to teach a roadside ward to serve a new master without changing its posture."

### Core Question

- Does the player destroy the Choir's touch, study it, or use it to bait a living operator?

### Options

1. Break the sigil cleanly.
2. Copy the pattern before breaking it.
3. Leave it live long enough to draw a watcher.

### Outcomes

#### Break Cleanly

- strongest containment route
- lowers `Circuit Strain`
- improves the quality of Agatha's audience

Suggested flag:

- `conyberry_sigil_broken`

#### Copy Before Breaking

- strongest leverage route
- improves later cult logic reads
- raises `Circuit Strain`
- makes Agatha more suspicious

Suggested flag:

- `conyberry_sigil_copied`

#### Bait A Watcher

- highest-risk route
- can produce a human witness, captured operator, or live confession
- best if Bryn or Kaelis are strong

Suggested flags:

- `conyberry_watcher_baited`
- `conyberry_watcher_seen`

## Beat 4: The Third Site Cost

If the player chooses to visit a third core branch site before Agatha after already stabilizing two:

- `Circuit Strain +1`
- Agatha's opening tone shifts from wary witness to coldly delayed witness
- the final conversation should acknowledge that the party asked a grieving circuit to wait while they harvested everything else first

Suggested flag:

- `conyberry_circuit_overdrawn`

## Beat 5: Watcher Cut

This beat is optional. Use it when a human enemy needs to prove that Conyberry still has living operators inside the haunting.

### Unlocks

- appears if `conyberry_watcher_baited`
- can also appear if `conyberry_claim_marks_found` and the player chooses to pursue the marks

### Core Outcomes

1. Capture a living watcher.
   - best leverage route
   - can produce names, handoff points, or claimant links
2. Scatter the watcher and recover only scraps.
   - partial route truth
3. Lose the watcher but confirm the circuit was being actively monitored.
   - stronger containment texture than pure tactical gain

Suggested flags:

- `conyberry_watcher_captured`
- `conyberry_watcher_scraps_taken`
- `conyberry_circuit_under_watch`

## Beat 6: Agatha's Bower

### Opening Text

- "Agatha does not rise like a monster out of a tale. She arrives like a grief the air was already carrying."

If `Circuit Strain` is high:

- "She arrives wrong at the edges, as if the circuit had to spend part of her shape getting your attention through damage."

### Tone Modifiers

- if `conyberry_dead_named`, she is colder but more human
- if `conyberry_sigil_copied`, she treats the party as possible looters of warning
- if `conyberry_chapel_relit`, she speaks more clearly about civic duty
- if delayed, the audience starts already bruised

## Beat 7: Agatha's Bargain

The live scaffold currently resolves this as one high-level skill gate. The expanded draft should split it into two layers:

1. how the party earns the right to ask
2. what kind of truth they choose to carry

### Layer 1: Earn The Audience

Suggested approaches:

1. `Persuasion`: "We are not here to plunder your dead. We need the warning only you still remember."
2. `Religion`: "Tell me what vow was broken here, and what the living are about to repeat."
3. `Arcana`: "If the cave's old song is changing, describe the change exactly."

These are already close to the live scene and should remain recognizable.

### Layer 2: Choose The Shape Of Truth

After access is earned, the player chooses one primary ask.

#### Ask 1: The Warning The Town Most Needs

Best for:

- civic route
- later public warning
- shrine lane and camp trust

Clean answer:

- the southern adit is real
- it was once used for labor and handling
- the Forge is being tuned to listen and carry an answer back

Suggested flag:

- `agatha_public_warning_known`

#### Ask 2: Who Is Lying In The Claims War

Best for:

- leverage route
- sponsor tension
- later barracks and relay logic

Clean answer:

- Agatha names one claimant, fixer, sponsor-adjacent broker, or hidden hand who has been profiting from damaged warning and false route custody
- the location packet should avoid hard-canon naming for now until the larger sponsor thread is settled

Suggested flag:

- `agatha_claimant_names_known`

#### Ask 3: What The Old Pact Feared Most

Best for:

- containment route
- Black Lake shrine
- Forge threshold interpretation

Clean answer:

- the Pact divided custody because Wave Echo was never meant to belong to a single listener
- the danger sat with whoever could feed intention into the mine without restraint

Suggested flag:

- `agatha_pact_restraint_known`

### Warning Quality Outcomes

#### Clean Warning

Requirements:

- low `Circuit Strain`
- at least one reverent or stabilizing branch outcome

Effect:

- full southern adit truth
- full listening-lens warning
- strongest metric payoff

Suggested live-facing flags:

- `agatha_truth_secured`
- `agatha_truth_clear`

#### Bruised Warning

Requirements:

- medium `Circuit Strain` or delayed state

Effect:

- still confirms the southern adit matters
- still points toward the Forge as a listening lens
- less fit for public sharing

Suggested live-facing flags:

- `agatha_truth_secured`
- `agatha_truth_clear = False`

#### Fractured Warning

Requirements:

- high `Circuit Strain`

Effect:

- gives fragments, dread, and direction without clean interpretation
- may still be enough to keep the route playable
- stronger fear cost

Suggested live-facing flags:

- `agatha_truth_secured`
- `agatha_warning_fragmented`

## Beat 8: The Exit Decision

Conyberry should end not with "you learned the truth," but with "who now holds the truth?"

### Civic Resolution: Share The Warning Widely

- bring the warning back to town and expedition leadership as common defensive truth
- best `Town Stability`
- weaker sponsor comfort
- strongest moral clarity

Suggested flags:

- `agatha_warning_shared`
- metric tendency: `Town Stability +1`

### Leverage Resolution: Restrict The Sharpest Truth

- share only the broad warning publicly
- keep the most precise names or route insights controlled
- best `Route Control`
- strongest Halia-compatible route

Suggested flags:

- `agatha_warning_restricted`
- metric tendency: `Route Control +1`

### Containment Resolution: Bind The Warning To Warding

- anchor the truth to a relic, lantern, or chosen circle instead of broad public speech
- best `Whisper Pressure`
- strongest Elira-aligned route
- weakest immediate claims-war leverage

Suggested flags:

- `agatha_warning_bound`
- `agatha_warded_warning`
- metric tendency: `Whisper Pressure -1`

## Agatha Dialogue Packet

### Core Voice

Agatha should sound:

- wounded, not theatrical
- exact when respected
- hostile to ownership language
- more like a grief forced to testify than a quest dispenser

### Safe Core Lines

- "You are late enough to be dangerous and early enough to matter."
- "The living always call it a warning when they still think they can choose what to hear."
- "The cave was never the prize. It was the vessel people kept mistaking for permission."
- "Do not ask me who deserves it. Ask who can bear it without teaching it to hunger."

### Conditional Lines

- If `conyberry_dead_named`:
  - "At least you had the discipline to notice whose road this still is."
- If `conyberry_sigil_copied`:
  - "You brought me theft with your reverence and expect me to separate the two."
- If delayed:
  - "They touched the circuit before you did. That is why I sound smaller than the truth."

### Response To Public-Warning Ask

- "Then hear it in the shape people can survive: the southern handling road was never dead, and the Forge is being taught to listen instead of merely make."

### Response To Claims-War Ask

- "You still want names. Very well. The living always trust corruption more quickly when it has handwriting."

### Response To Pact-Restraint Ask

- "The Pact divided the burden because no one hand was meant to turn this place into an answer."

## Rewards

Conyberry should reward the shape of truth the party carries out, alongside gear.

### Baseline Reward Ideas

- `scroll_quell_the_deep x1`
- `resonance_tonic x1`
- modest coin or devotional relic value
- one major clue packet

### Branch Reward Tendencies

- civic branch:
  - stronger social trust
  - steadier camp language
- leverage branch:
  - sharper sponsor or route options later
- containment branch:
  - lower contamination and stronger ward language later

## Later Payoff Hooks

- `agatha_warning_shared` should soften panic language in town scenes and camp rumors.
- `agatha_warning_restricted` should open a cleaner hidden option during `Sabotage Night` or a sponsor debrief.
- `agatha_warning_bound` should enable a special shrine, lantern, or Forge-threshold ward scene later.
- `agatha_claimant_names_known` should help expose one false authority line in late Act 2.
- `agatha_pact_restraint_known` should strengthen the philosophical continuity of `Black Lake` and the `Forge of Spells`.

## Suggested Runtime Flags

- `conyberry_entry_civic`
- `conyberry_entry_leverage`
- `conyberry_entry_containment`
- `conyberry_pilgrims_steadied`
- `conyberry_clean_witness_taken`
- `conyberry_whisper_track_named`
- `conyberry_cairn_ward_read`
- `conyberry_cairn_grave_read`
- `conyberry_cairn_trail_read`
- `conyberry_chapel_relit`
- `conyberry_field_lantern_taken`
- `conyberry_chapel_quarantined`
- `conyberry_grave_history_read`
- `conyberry_dead_named`
- `conyberry_claim_marks_found`
- `conyberry_sigil_broken`
- `conyberry_sigil_copied`
- `conyberry_watcher_baited`
- `conyberry_watcher_captured`
- `conyberry_circuit_overdrawn`
- `agatha_public_warning_known`
- `agatha_claimant_names_known`
- `agatha_pact_restraint_known`
- `agatha_warning_shared`
- `agatha_warning_restricted`
- `agatha_warning_bound`

## Implementation Recommendation

Best order:

1. Expand the current single-scene Conyberry implementation into a multi-beat scripted route in `story_act2_scaffold.py`.
2. Keep the existing core Agatha warning intact so current Act 2 progression does not break.
3. Add `Circuit Strain` and two branch-site scenes first:
   - `Hushed Pilgrim Road`
   - `Chapel of Lamps`
   - `Defiled Sigil`
4. Add `Grave Ring`, `Watcher Cut`, and exit-custody logic next.
5. Only after the beats feel stable should Conyberry be considered for a local room-map scaffold like `Glasswater Intake`.

## Bottom Line

Conyberry should become the Act 2 route where the player learns that truth is not automatically a public good just because it is true.

That is why it matters so early:

- it tests whether the expedition will treat warning as stewardship, leverage, or containment
- it defines one of Elira's cleanest moral battlegrounds
- and it lets Agatha become more than a lore checkpoint by making her the first witness the party might still fail even while technically succeeding
