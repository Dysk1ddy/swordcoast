from __future__ import annotations

"""Aethrune lore codex entries used by the title-screen reference menu.

The public codex now presents Aethrune as the game's original setting.
Internal character-option keys still mirror the current mechanics so existing
saves, tests, and creation flow remain stable during the retcon.
"""

from collections.abc import Mapping

from ...gameplay.defense_formula import base_damage_reduction_for_defense
from ...models import SKILL_TO_ABILITY
from .character_options.backgrounds import BACKGROUNDS
from .character_options.classes import CLASSES, CLASS_LEVEL_PROGRESSION
from .character_options.races import RACES
from .public_terms import (
    ABILITY_PUBLIC_LABELS,
    CLASS_PUBLIC_LABELS,
    RACE_PUBLIC_LABELS,
    SKILL_PUBLIC_LABELS,
    rules_text,
)


LoreEntry = dict[str, str]
LoreSection = Mapping[str, LoreEntry]


LORE_INTRO = (
    "This codex covers the roads, factions, and rules language of Aethrune. "
    "Start with Greywake, the Emberway, Iron Hollow, the Resonant Vaults, and the Meridian works still moving under newer stone. "
    "Combat and character math still ride on an SRD-derived d20 chassis, while the public language leans on Aethrune terms such as "
    "channeling, relics, draughts, scripts, Defense, edge, strain, and resist checks."
)


LOCATION_LORE: dict[str, LoreEntry] = {
    "Aethrune": {
        "menu": "A broken world where old roads, records, and buried systems still answer.",
        "text": (
            "Aethrune grew over Meridian foundations that never fully died. The Accord once bound roads, cisterns, "
            "signal towers, vaults, and ledgers into one working body. Now people live among cracked milestones, "
            "sleeping gates, and records that still answer the right stamp.\n\n"
            "That leaves every town arguing with inheritance. A road can remember where a caravan belongs. A sealed "
            "culvert can still know an old title. A village ledger can ruin a family if the wrong hand learns how "
            "to wake it."
        ),
    },
    "Frontier Primer": {
        "menu": "A practice-table introduction to checks, choices, and road consequences.",
        "text": "The primer starts with chalk marks, scuffed boots, and a patient voice teaching the table how Aethrune spends risk.",
    },
    "Prologue": {
        "menu": "The character's first pressure point before the road opens.",
        "text": "The prologue keeps close to one origin: a door, a debt, a warning, or a habit the road will test before Greywake ever sees it.",
    },
    "Shatterbelt Frontier": {
        "menu": "The Act I borderland where trade, fear, and old roadwork collide.",
        "text": (
            "The Shatterbelt Frontier runs from Greywake's wet stone out into milehouses, quarry tracks, shrine lamps, "
            "farm cuts, and busted Accord masonry sticking through newer mud. Wagon ruts share the same ground as "
            "survey stakes and old drainage channels.\n\n"
            "No one governs it cleanly. Greywake wants order in the books, Iron Hollow wants breathing room, the "
            "Ashen Brand wants toll by fear, and buried Meridian machinery waits below them like cold weather trapped "
            "under stone."
        ),
    },
    "Greywake": {
        "menu": "A salt-gray harbor city trying to govern roads it can no longer fully secure.",
        "text": (
            "Greywake opens the campaign with salt on the wind, ash on the warehouse walls, and intake ropes strung "
            "across triage yards. The city runs on manifests, dock work, and wet-cloaked officials who know every road "
            "failure arrives at the harbor eventually.\n\n"
            "It is a pressured city. Wounded teamsters come in ahead of their wagons, missing freight turns into ledger "
            "fights, and every faction in town wants to decide whether the Emberway gets saved or written off."
        ),
    },
    "Wayside Luck Shrine": {
        "menu": "A road shrine where Elira spends lamp oil, bandages, and witness names on field care.",
        "text": "The shrine smells of wet wool and lamp smoke. Cots crowd the wall, and every name Elira writes down becomes one more person the road failed to erase.",
    },
    "Greywake Yard": {
        "menu": "An intake yard full of triage ropes, warehouse soot, and frightened route witnesses.",
        "text": "Greywake Yard catches the first human cost of the route attacks. Clerks count blankets while wounded teamsters argue over which wagon burned first.",
    },
    "Greywake Breakout": {
        "menu": "A road-yard fight where Ashen Brand cutters try to erase proof before it reaches Mira.",
        "text": "The breakout hits between wagons, cots, and rope lines. Someone wants the wounded quiet and the manifests gone before the city can make either count.",
    },
    "Blackwake Crossing": {
        "menu": "A wet side-branch of forged toll papers, prison pens, and a hidden supply cache.",
        "text": "Blackwake Crossing leaves ash in the reeds and crate slats in the mud. The place teaches the party how stolen goods become authority when the seals look clean.",
    },
    "Emberway": {
        "menu": "The old road artery whose milestones, shrines, and tollmarks still shape Act I.",
        "text": (
            "The Emberway is an Accord road laid over older survey lines, with culverts, milemarkers, watchpoints, "
            "signal stones, and shrine-lamps still doing half their jobs. Travelers keep using it because the side "
            "tracks are slower, meaner, and easier to disappear on.\n\n"
            "That makes control of the road a daily contest. False papers, copied seals, fake checkpoints, and staged "
            "rescues can bend traffic long before anyone admits the route changed hands."
        ),
    },
    "Liar's Circle": {
        "menu": "A roadside statue puzzle where cracked stone still cares about exact claims.",
        "text": "Four old figures stand in weathered argument beside the Emberway. Rain gathers in their carved mouths before anyone asks who is lying.",
    },
    "False Checkpoint": {
        "menu": "A copied roadwarden stop built from uniforms, nerve, and stolen cadence.",
        "text": "The checkpoint looks official from ten paces: a rope, a stamped board, a tired voice asking for papers. The wrongness lives in the pauses.",
    },
    "False Tollstones": {
        "menu": "A broken milemarker rigged into a toll trap with borrowed authority.",
        "text": "The tollstones lean beside the road with fresh chalk in old cracks. Someone has made a ruined marker sound like a law again.",
    },
    "Iron Hollow": {
        "menu": "A frontier hub built around claims, supply ledgers, and stubborn local survival.",
        "text": (
            "Iron Hollow lives by claims ledgers, spare tools, inn rooms, orchard walls, and whoever still shows up "
            "when a neighbor's axle snaps. The town looks patched together because it is.\n\n"
            "When the Emberway chokes, Iron Hollow feels it at once. Bread shortens, medicine stalls on the road, and "
            "families start planning around absence instead of work."
        ),
    },
    "Lantern Shrine Network": {
        "menu": "Wayside refuges where road faith, first aid, and rumor all meet.",
        "text": (
            "The Lantern Shrine Network grew out of small waystations that kept a lamp burning for late travelers. "
            "Some still have trained caretakers. Some have one volunteer, a kettle, and a good memory for names.\n\n"
            "A shrine holds bandages, weather shelter, road gossip, and witness work under the same roof. The order "
            "of the cots matters. The next report matters. So does who gets named aloud when the road starts taking people."
        ),
    },
    "Blackglass Well": {
        "menu": "A cracked waterwork where old salvage, grave dust, and route history surface.",
        "text": (
            "Blackglass Well is an Accord waterwork with a dark lining that still holds heat and memory. Salvagers "
            "come for copper, pumps, old seals, and anything a hungry market will buy. Some of those systems were "
            "buried for better reasons than forgetfulness.\n\n"
            "The danger here comes out of cracked masonry, old valves, and people selling dead infrastructure before "
            "anyone understands what they opened."
        ),
    },
    "Red Mesa Hold": {
        "menu": "A raider stronghold on broken red stone above the trade cuts.",
        "text": (
            "Red Mesa Hold sits above dry cuts and supply approaches where a disciplined raiding band can look larger "
            "than it is. One fortified height can decide which wagons move, which scouts vanish, and which town elders "
            "start bargaining with fear.\n\n"
            "The hold also shows what happens when old Accord watch positions fall into hungrier hands. A place built "
            "to survey the land can close around it like a fist."
        ),
    },
    "Ashfall Watch": {
        "menu": "A ruined watch height where command discipline turns extortion into siege work.",
        "text": "Ashfall Watch holds smoke-black stone, prisoner yards, and signal scars above Iron Hollow's approaches. Orders travel here faster than mercy.",
    },
    "Cinderfall Ruins": {
        "menu": "A scorched relay ruin that hints at older signal logic beneath Act I.",
        "text": (
            "Cinderfall Ruins carry one of the frontier's old signal scars. Burned stone, fused brackets, and relay "
            "fragments show where the Meridian Accord once pushed orders through faster than horses could haul them.\n\n"
            "That makes Cinderfall the point where roadside extortion starts touching something stranger. People can "
            "learn to imitate a system long after the world forgets how to challenge it."
        ),
    },
    "Duskmere Manor": {
        "menu": "A buried estate whose cellars turn local extortion into an older secret.",
        "text": (
            "Duskmere Manor is a broken estate over sealed rooms, smuggling paths, and old stone that never quite "
            "stopped listening. From the surface it reads like a gang hideout, which is why it serves that purpose so well.\n\n"
            "Below the rot and swagger, the manor points at the deeper campaign wound. People hide inside the ruins. "
            "The ruins keep a record of them."
        ),
    },
    "Emberhall Cellars": {
        "menu": "The cellar route beneath Iron Hollow where the Ashen Brand makes its final Act I stand.",
        "text": "Emberhall Cellars run under wet stone, ash ledgers, and locked rooms that learned too many names. The last Brand orders collect there like bad smoke.",
    },
    "Vein of Glass": {
        "menu": "The Act II region where claims, echoes, and old water-control systems converge.",
        "text": (
            "The Vein of Glass is a fractured region of mineral seams, flooded cuts, reflective stone, broken "
            "prospects, and old intake works. It draws miners, reclaimers, claim lawyers, scavengers, and zealots "
            "because every fresh break in the rock looks like evidence.\n\n"
            "Act II turns the campaign from road control toward memory control. Ownership still matters, but the sharper "
            "fight is over who gets to name what the buried world was trying to say."
        ),
    },
    "Ashlamp Claims Council": {
        "menu": "Iron Hollow's Act II table of claimants, sponsors, clerks, and frightened witnesses.",
        "text": "The council smells of lamp brass, damp wool, and fresh ink. Every faction brings a map, and every map wants the next expedition to owe it something.",
    },
    "Act II Expedition Hub": {
        "menu": "The working table for routes, sponsors, camp pressure, and Act II leads.",
        "text": "The hub is a room of pins, ration tallies, and muddy boots. The party chooses which trouble gets daylight before the others learn to move.",
    },
    "Hushfen and the Pale Circuit": {
        "menu": "A fen road where dead witness, old vows, and Choir defilement share the same mud.",
        "text": "Hushfen keeps low water, grave moss, and pale signal marks under the reeds. Travelers lower their voices there before they know why.",
    },
    "Greywake Wood": {
        "menu": "A cut survey line where rival claims and Quiet Choir lookouts edit the route.",
        "text": "Greywake Wood holds snapped stakes, spoiled stores, and sightlines trimmed by someone who knew the survey habits. The trees keep the freshest lies at boot height.",
    },
    "Stonehollow Dig": {
        "menu": "A collapsed dig site of trapped scholars, tunnel predators, and nervous claim marks.",
        "text": "Stonehollow Dig breathes grit from broken lifts and half-shored cuts. Every lantern beam finds another place where the floor stopped agreeing to be floor.",
    },
    "Glasswater Intake": {
        "menu": "A waterworks annex where permits, valves, and runoff carry Quiet Choir pressure.",
        "text": "Glasswater Intake starts with a wet rock apron and the clack of a gatehouse winch. Green wax in the wrong groove can make a whole valley drink a lie.",
    },
    "Siltlock Counting House": {
        "menu": "A claims office where water permits, ration tags, and wax seals turn harm into paperwork.",
        "text": "Siltlock keeps tidy counters over dirty records. Permit stacks, charity crocks, and a back till all know who profited before Glasswater sounded sick.",
    },
    "Sabotage Night": {
        "menu": "A three-front Iron Hollow crisis where delayed leads come due after dark.",
        "text": "Sabotage Night breaks across bells, smoke stores, and rooflines. The town learns which problem the party left breathing longest.",
    },
    "Broken Prospect": {
        "menu": "A shattered claim shelf at the edge of the Resonant Vaults.",
        "text": "Broken Prospect hangs on bad timber, pact markers, and rival survey shelves. The rock has been argued over so often the stakes look nervous.",
    },
    "South Adit": {
        "menu": "A prison cut where the Choir hides witnesses inside old mining work.",
        "text": "South Adit carries pick dust, silent cells, and wrist slates corrected by cold hands. The exit smells of drainage water and fear that almost made it out.",
    },
    "Resonant Vaults": {
        "menu": "The deep ruin complex beneath Act II, where record and reality begin to blur.",
        "text": (
            "The Resonant Vaults are a network of galleries, flooded crossings, tuned chambers, and command rooms where "
            "Meridian systems still answer patterns, titles, and lies. The place does not feel dead. It feels paused, "
            "as if the next order might wake it.\n\n"
            "The Quiet Choir wants that pause. A system that remembers authority can learn a new voice if someone feeds "
            "it enough ritual, pressure, and patience."
        ),
    },
    "Blackglass Causeway": {
        "menu": "A drowned crossing where old anchor chains and black water guard the lower route.",
        "text": "Blackglass Causeway stretches over water dark enough to swallow lantern light. Chains knock below the planks as if the crossing is counting weight.",
    },
    "Blackglass Relay House": {
        "menu": "A relay station where ledgers, bells, and cable sumps carry the route's old commands.",
        "text": "Blackglass Relay House keeps its teeth in cables, counterweights, and null-bell walks. The place answers hands that know which lever sounds official.",
    },
    "Meridian Forge": {
        "menu": "The Act II convergence point where old infrastructure can be repaired or weaponized.",
        "text": (
            "The Meridian Forge is a control chamber where broken systems can be brought back into alignment. In careful "
            "hands it could steady routes, waterworks, and signal relays. In cruel hands it could make oppression look "
            "like restored order.\n\n"
            "That puts the whole campaign argument in one room. The Forge can restore old permissions, or it can force "
            "survivors to decide which parts of the old world deserve to stay buried."
        ),
    },
    "Ninth Ledger": {
        "menu": "The Act III opening pressure point where hidden routes and old accounts wake.",
        "text": "The Ninth Ledger opens with paper that should have stayed blank. Names, debts, and route marks begin answering a hand no clerk admits training.",
    },
    "Ledger Aftermath": {
        "menu": "The follow-through after the Ninth Ledger starts naming old pressure.",
        "text": "Ledger Aftermath is quieter than the opening shock. People count who vanished from the page, who appeared, and whose seal suddenly feels heavy.",
    },
}


CLASS_LORE: dict[str, LoreEntry] = {
    "Warrior": {
        "label": "Warrior",
        "menu": "Line-holders who turn pressure, grit, and leverage into control.",
        "text": (
            "Warriors are the people who know where to put a shield, when to shove, and how long a road can survive "
            "with one tired guard holding the narrow place. They carry discipline in their hands: buckles checked, "
            "boots braced, blade kept low until the opening is worth spending.\n\n"
            "A Warrior belongs anywhere Aethrune asks someone to stand between frightened people and the next bad order."
        ),
    },
    "Mage": {
        "label": "Mage",
        "menu": "Field channelers who read pressure, charge, and old systems.",
        "text": (
            "Mages work by reading patterns before they become wounds. A cracked sigil, a wrong hum in a pipe, a "
            "lamp-flutter over old stone, or a trembling ward can tell them where force wants to go next.\n\n"
            "A Mage fits the campaign because Aethrune keeps leaving live systems under ordinary rooms. Someone has "
            "to understand the charge before the room spends it."
        ),
    },
    "Rogue": {
        "label": "Rogue",
        "menu": "Precision, nerve, and side-door thinking under pressure.",
        "text": (
            "Rogues survive by seeing openings other people miss. Locks, false papers, quiet steps, coded marks, "
            "crowd flow, and bad assumptions are all part of their toolkit.\n\n"
            "That makes Rogues useful wherever a route is under control. A Rogue is often the only person who can "
            "move through a controlled line without becoming part of the control."
        ),
    },
}


RACE_LORE: dict[str, LoreEntry] = {
    "Human": {
        "label": "Human",
        "menu": "Adaptable rebuilders who became the backbone of the post-Accord world.",
        "text": (
            "Humans are Aethrune's most numerous and varied people. During the Meridian Accord they were workers, "
            "traders, soldiers, clerks, couriers, and citizens. After the collapse, they became the survivors most "
            "likely to rebuild a town from whatever still stood.\n\n"
            "Human characters fit almost any path because adaptation is their inheritance."
        ),
    },
    "Dwarf": {
        "label": "Dwarf",
        "menu": "Deep infrastructure keepers shaped by stone, craft, and endurance.",
        "text": (
            "Dwarves maintained tunnels, foundations, load-bearing works, and deep systems under the old Accord. "
            "When surface authority failed, many endured below and emerged into a world that had become less reliable "
            "than the stone they trusted.\n\n"
            "They value craft because a bad join can kill generations later."
        ),
    },
    "Elf": {
        "label": "Elf",
        "menu": "Long-memory observers who carry fragments others forgot.",
        "text": (
            "Elves were archivists, continuity keepers, observers, and record minds within the old systems. "
            "They saw pieces of the collapse coming, but not enough to stop it cleanly.\n\n"
            "In play, an Elf character can make memory feel active rather than ornamental: a burden, a warning, "
            "and sometimes a weapon."
        ),
    },
    "Halfling": {
        "label": "Halfling",
        "menu": "Quick couriers and small-route survivors who thrive when systems fail.",
        "text": (
            "Halflings were messengers, small traders, and route improvisers even before the collapse. When big "
            "systems failed, they adapted faster than anyone who had depended on official permissions.\n\n"
            "Their courage is practical: keep moving, keep laughing when possible, and never let a giant institution "
            "convince you it is the whole world."
        ),
    },
    "Dragonborn": {
        "label": "Forged",
        "menu": "Forged survivors marked by ancient systems and visible power.",
        "text": (
            "Forged are living remnants of catastrophic fusion between flesh, authority, and old machinery. Some "
            "show metallic growth, strange heat, luminous eyes, or bodies that seem half-designed by a failed system.\n\n"
            "They are often feared because they make the Meridian past impossible to treat as safely dead."
        ),
    },
    "Gnome": {
        "label": "Unrecorded",
        "menu": "Unrecorded people whose presence resists easy categorization.",
        "text": (
            "Unrecorded people are rare and difficult to categorize. Old Accord records either missed them, erased them, or "
            "failed to hold them in a stable way. That absence has become part of their identity.\n\n"
            "An Unrecorded character suits curious, inventive, evasive, or pattern-breaking roles: someone the ledger cannot "
            "quite pin down."
        ),
    },
    "Half-Elf": {
        "label": "Astral Elf",
        "menu": "Pattern-sensitive observers partly out of sync with ordinary perception.",
        "text": (
            "Astral Elves emerged from elven lines exposed to unstable signal systems. They notice discontinuities, "
            "echoes, and false alignments others miss, but perception can become lonely when nobody else trusts the "
            "same evidence.\n\n"
            "They are excellent characters for reading the world's quiet wrongness before it becomes loud."
        ),
    },
    "Half-Orc": {
        "label": "Orc-Blooded",
        "menu": "Borderline inheritors of Orukh endurance and mixed-world pressure.",
        "text": (
            "Orc-Blooded people often move between communities that expect them to prove what should not need "
            "proving: loyalty, restraint, usefulness, or belonging. Many respond by becoming impossible to ignore.\n\n"
            "Their stories fit Aethrune's borderlands well because the Shatterbelt itself is built from mixed claims "
            "and disputed authority."
        ),
    },
    "Tiefling": {
        "label": "Fire-Blooded",
        "menu": "Fire-blooded people shaped by inner heat, restraint, and volatile inheritance.",
        "text": (
            "Fire-Blooded people descend from populations changed by proximity to old energy cores. Their bodies may show "
            "warm skin tones, emberlike eyes, or veins that glow under stress.\n\n"
            "Fire-Blooded culture values control because power that leaks at the wrong moment can become someone else's "
            "excuse to fear you."
        ),
    },
    "Goliath": {
        "label": "Riverfolk",
        "menu": "River and coast-adapted people who prize motion over rigidity.",
        "text": (
            "Riverfolk are tied to water-control systems, flood channels, rivers, and coastal change. Their cultures "
            "often prefer flexible agreements over rigid institutions because water has taught them that survival is "
            "movement with memory.\n\n"
            "A Riverfolk adventurer brings that flow into every hard place the party enters."
        ),
    },
    "Orc": {
        "label": "Orukh",
        "menu": "Powerful fringe survivors who learned not to depend on central systems.",
        "text": (
            "The Orukh lived at the edges of Accord benefit and often survived without trusting central promises. "
            "When the collapse came, that independence became preparation.\n\n"
            "Orukh characters carry strength, community loyalty, and suspicion of any authority that demands obedience "
            "before earning trust."
        ),
    },
}


BACKGROUND_LORE: dict[str, LoreEntry] = {
    "Soldier": {
        "label": "Route Veteran",
        "menu": "A guard, patrol hand, or militia survivor shaped by hard marches.",
        "text": (
            "Route Veterans know how quickly a checkpoint becomes a grave marker when command fails. They understand "
            "formations, ration math, frightened recruits, and the difference between bravery and simply having no "
            "safe place to retreat."
        ),
    },
    "Acolyte": {
        "label": "Lantern Acolyte",
        "menu": "A shrine-tender, field medic, or doctrine keeper from the road faiths.",
        "text": (
            "Lantern Acolytes keep lamps burning where travel turns dangerous. Their work is practical devotion: "
            "washing wounds, recording names, settling panic, and deciding what mercy requires when supplies run thin."
        ),
    },
    "Criminal": {
        "label": "Veil Broker",
        "menu": "A smuggler, lock hand, or papers-forger who knows hidden routes.",
        "text": (
            "Veil Brokers understand the underside of Aethrune's roads. False seals, quiet doors, smuggled food, "
            "coded favors, and borrowed identities can be crimes, survival tools, or both depending on who writes the law."
        ),
    },
    "Sage": {
        "label": "Accord Scholar",
        "menu": "A reader of old systems, failed ledgers, and dangerous precedent.",
        "text": (
            "Accord Scholars study ruins because old decisions still have teeth. They know that a treaty, relay note, "
            "or maintenance log can explain why a modern town is bleeding."
        ),
    },
    "Outlander": {
        "label": "Trail-Wise",
        "menu": "A camp survivor who trusts weather, tracks, and lived distance.",
        "text": (
            "Trail-Wise characters know the land outside official maps. They read firepits, river height, animal panic, "
            "and the human habit of pretending a bad road is safe because the alternative is expensive."
        ),
    },
    "Charlatan": {
        "label": "Maskwright",
        "menu": "A fraud, performer, or confidence reader who knows how belief moves.",
        "text": (
            "Maskwrights understand that identity is often a performance other people agree to believe. On the Emberway, "
            "that makes them useful against forged authority and dangerous when they decide to forge back."
        ),
    },
    "Guild Artisan": {
        "label": "Guildwright",
        "menu": "A craftsperson trained in prices, materials, supply, and reputation.",
        "text": (
            "Guildwrights know the practical machinery of town life: who supplies nails, who can repair a hinge, who "
            "owes whom, and why a missing wagon can break more than one household."
        ),
    },
    "Hermit": {
        "label": "Quiet Witness",
        "menu": "A secluded seeker who learned to notice signs before crowds do.",
        "text": (
            "Quiet Witnesses step away from noise long enough to hear pattern. Some study herbs, some omens, some old "
            "doctrine, and some merely know what people sound like when they are about to lie to themselves."
        ),
    },
}


ABILITY_LORE: dict[str, LoreEntry] = {
    "STR": {
        "label": "Strength",
        "menu": "Raw force, lifting, breaking, climbing, and close-quarters pressure.",
        "text": "Strength measures the ability to force doors, grapple, haul gear, and turn physical mass into action.",
    },
    "DEX": {
        "label": "Agility",
        "menu": "Speed, finesse, balance, stealth, and quick hands.",
        "text": "Agility covers initiative, careful movement, ranged aim, quiet steps, and the hand precision needed for delicate work.",
    },
    "CON": {
        "label": "Endurance",
        "menu": "Stamina, pain tolerance, poison resistance, and staying upright.",
        "text": "Endurance decides how much punishment, sickness, hunger, panic, and exhaustion a character can survive before breaking.",
    },
    "INT": {
        "label": "Intelligence",
        "menu": "Study, pattern recognition, memory, and system reasoning.",
        "text": "Intelligence helps decode Accord records, read old machinery, connect clues, and understand what a ruin was designed to do.",
    },
    "WIS": {
        "label": "Wisdom",
        "menu": "Perception, instinct, medicine, wayfinding, and reading the moment.",
        "text": "Wisdom is the sense that catches tracks, lies, infection, danger, weather, and the emotional shape of a room.",
    },
    "CHA": {
        "label": "Charisma",
        "menu": "Force of personality, social pressure, command, and performance.",
        "text": "Charisma is the ability to make people listen, believe, flinch, rally, confess, or follow when the outcome is uncertain.",
    },
}


SKILL_LORE: dict[str, LoreEntry] = {
    "Acrobatics": {"menu": "Balance, tumbling, slips, falls, and unstable footing.", "text": "Acrobatics keeps a character moving when roofs sag, bridges tilt, and a fight spills across broken ground."},
    "Animal Handling": {"menu": "Working with mounts, hounds, livestock, and frightened beasts.", "text": "Animal Handling reads the panic and trust of living creatures, especially on roads where horses often know trouble first."},
    "Arcana": {"label": "Arcana", "menu": "Knowledge of channeling, relics, old signals, and unstable forces.", "text": "Arcana explains Meridian machinery, channel patterns, relic behavior, and the difference between a miracle and a malfunction."},
    "Athletics": {"menu": "Climbing, swimming, jumping, grappling, and hard exertion.", "text": "Athletics is the body's answer when the route collapses, the gate sticks, or somebody has to hold a line by force."},
    "Deception": {"menu": "Lies, masks, forged confidence, and controlled misdirection.", "text": "Deception matters because Aethrune's factions often win by making false authority look official long enough to matter."},
    "History": {"menu": "Old records, battles, settlements, treaties, and ruins.", "text": "History turns names and buried stone into context, especially when the Meridian past keeps repeating through modern choices."},
    "Insight": {"label": "Insight", "menu": "Understanding motive, fear, pressure, and concealed intent.", "text": "Insight catches the moment when a witness edits the truth, a leader hides panic, or a negotiator smiles too late."},
    "Intimidation": {"menu": "Threat, command presence, and controlled menace.", "text": "Intimidation is the art of making consequences visible before anyone has to bleed for them."},
    "Investigation": {"menu": "Searching scenes, testing claims, and connecting evidence.", "text": "Investigation follows scratches, ledgers, footprints, missing objects, false seals, and the quiet math of what does not fit."},
    "Medicine": {"menu": "Triage, disease, wounds, fatigue, and field care.", "text": "Medicine keeps people alive when the shrine is full, the rain will not stop, and the next wagon is already overdue."},
    "Nature": {"menu": "Weather, terrain, plants, beasts, and living patterns.", "text": "Nature explains how the land reacts when roads, mines, and waterworks push too hard against it."},
    "Perception": {"menu": "Noticing threats, details, movement, sound, and ambush signs.", "text": "Perception is the skill of catching danger before it becomes a headline in someone else's ledger."},
    "Performance": {"menu": "Voice, rhythm, storytelling, public timing, and staged emotion.", "text": "Performance can rally survivors, distract a room, sell a false role, or make a truth memorable enough to travel."},
    "Persuasion": {"menu": "Honest pressure, negotiation, appeals, and earned trust.", "text": "Persuasion moves people without hiding the ask, which makes it precious in towns tired of being manipulated."},
    "Religion": {"label": "Religion", "menu": "Shrine law, ritual practice, oaths, cults, and sacred obligations.", "text": "Religion covers Lantern rites, funeral names, oath language, forbidden symbols, and the difference between faith and control."},
    "Sleight of Hand": {"label": "Sleight of Hand", "menu": "Quick fingers, hidden objects, small mechanisms, and misdirection.", "text": "Sleight of Hand handles palms, pins, seals, pockets, and the tiny movements that decide whether a plan survives contact."},
    "Stealth": {"menu": "Quiet movement, concealment, shadowing, and not being where eyes expect.", "text": "Stealth lets a character move through controlled roads, occupied ruins, and frightened towns without becoming another report."},
    "Survival": {"label": "Survival", "menu": "Tracking, foraging, route sense, weather reading, and camp judgment.", "text": "Survival keeps a party alive when maps are wrong, food is thin, and the road ahead has started lying."},
}


FEATURE_LORE: dict[str, LoreEntry] = {
    "sneak_attack": {"label": "Veilstrike", "menu": "Precision damage when an opening appears.", "text": "Veilstrike rewards the Rogue for choosing the exact moment when defense becomes assumption."},
    "expertise": {"label": "Deep Practice", "menu": "A skill refined past ordinary competence.", "text": "Deep Practice marks the difference between knowing a trick and building a life around it."},
    "darkvision": {"label": "Lowlight Sight", "menu": "Eyes adapted to dim routes, tunnels, and old chambers.", "text": "Lowlight Sight marks people whose bodies learned to treat darkness as information rather than absence."},
    "dwarven_resilience": {"label": "Dwarven Resilience", "menu": "Deep-born resistance to poison, fatigue, and bad air.", "text": "Dwarven Resilience comes from generations shaped by tunnels, minerals, pressure, and stubborn survival."},
    "keen_senses": {"label": "Keen Senses", "menu": "Long-trained perception and memory working together.", "text": "Keen Senses catch small details because the mind has learned to wait for them."},
    "fey_ancestry": {"label": "Signal Distance", "menu": "A mind that resists easy influence and false resonance.", "text": "Signal Distance makes outside pressure slide off because the self is tuned to an older, steadier rhythm."},
    "lucky": {"label": "Halfling Luck", "menu": "A small survivor's talent for disaster missing by inches.", "text": "Halfling Luck is not destiny. It is readiness, motion, and a lifetime of refusing to be where danger expected."},
    "brave": {"label": "Small Courage", "menu": "Fear acknowledged, then stepped through anyway.", "text": "Small Courage suits Halflings because they know fear well enough not to worship it."},
    "draconic_presence": {"label": "Forged Presence", "menu": "A Forged aura of visible power and old-system weight.", "text": "Forged Presence makes authority physical, whether the Forged character wants that attention or not."},
    "gnome_cunning": {"label": "Unrecorded Cunning", "menu": "A mind hard for old systems to categorize or corner.", "text": "Unrecorded Cunning lets an Unrecorded character slip through assumptions built by ledgers, categories, and tidy answers."},
    "relentless_endurance": {"label": "Orcish Grit", "menu": "The refusal to fall when collapse seems reasonable.", "text": "Orcish Grit is survival as an argument: the world says enough, and the body says not yet."},
    "menacing": {"label": "Hard Stare", "menu": "Charisma sharpened by a life of being tested.", "text": "Hard Stare makes a warning land before steel has to."},
    "hellish_resistance": {"label": "Fire-Blooded Resistance", "menu": "Fire-Blooded heat tolerance and inner fire control.", "text": "Fire-Blooded Resistance lets Fire-Blooded people survive heat, surge, and stress that would break a colder body."},
    "stone_endurance": {"label": "Riverfolk Endurance", "menu": "Riverfolk toughness shaped by pressure and motion.", "text": "Riverfolk Endurance absorbs impact the way water and stone share a lesson: bend, brace, continue."},
    "adrenaline_rush": {"label": "Orc Rush", "menu": "A sudden burst of forward survival.", "text": "Orc Rush closes distance before hesitation can become a cage."},
}


APPENDIX_A_ENTRIES: dict[str, LoreEntry] = {
    "Appendix A: Blinded": {"menu": "A creature cannot rely on sight.", "text": "Blinded means visual information is gone or unreliable. In Aethrune terms, the character suffers strain on sight-based actions and gives enemies edge when sight would protect them."},
    "Appendix A: Charmed / Swayed": {"menu": "Influence clouds judgment toward the source.", "text": "Swayed characters are socially or supernaturally tilted toward a source and cannot treat that source as a clear enemy until the effect breaks."},
    "Appendix A: Deafened": {"menu": "A creature cannot rely on hearing.", "text": "Deafened blocks sound cues, spoken warnings, and signal rhythms. It matters in ruins where sound often arrives before danger does."},
    "Appendix A: Frightened / Shaken": {"menu": "Fear interferes with direct action.", "text": "Shaken characters struggle while the source of fear dominates the scene. In public language, this usually appears as strain on direct pressure against the fear."},
    "Appendix A: Grappled": {"menu": "Movement is physically pinned or controlled.", "text": "Grappled means someone or something has locked down movement. Escape usually calls for Strength or Agility under pressure."},
    "Appendix A: Incapacitated": {"menu": "A creature cannot take meaningful actions.", "text": "Incapacitated is a severe state where the character cannot act normally, whether from shock, pain, binding, or overwhelming force."},
    "Appendix A: Invisible / Veiled": {"menu": "A creature cannot be seen without special help.", "text": "Veiled targets are hidden from ordinary sight. Attacks against them suffer strain unless another sense or clue reveals the right angle."},
    "Appendix A: Paralyzed / Locked": {"menu": "A creature is held rigid and cannot move.", "text": "Locked characters cannot move or speak effectively. Close-range danger becomes much worse because defense has collapsed."},
    "Appendix A: Petrified": {"menu": "A creature is transformed into inert matter.", "text": "Petrified is rare and terrifying: the body becomes rigid matter, suspending ordinary action until the effect is reversed."},
    "Appendix A: Poisoned": {"menu": "Toxin or sickness weakens action.", "text": "Poisoned characters act under strain as the body fights venom, illness, bad air, or contaminated relic residue."},
    "Appendix A: Prone": {"menu": "A creature is down on the ground.", "text": "Prone means footing has failed. Standing costs time, close enemies gain openings, and distant attacks become less certain."},
    "Appendix A: Restrained": {"menu": "Movement is limited by bindings, rubble, or force.", "text": "Restrained characters can still think and struggle, but their movement is limited enough that enemies can exploit the position."},
    "Appendix A: Stunned / Disrupted": {"menu": "A creature loses the thread of action.", "text": "Disrupted means shock, impact, or signal interference has broken the character's ability to act for a moment."},
    "Appendix A: Unconscious": {"menu": "A creature is down, unaware, and unable to act.", "text": "Unconscious characters cannot defend themselves, speak, move, or choose actions until restored or stabilized."},
}


APPENDIX_LORE: dict[str, LoreEntry] = {
    "Appendix A: Conditions": {
        "menu": "Aethrune-facing names for major combat states.",
        "text": (
            "Contents:\n"
            + "\n".join(f"- {name.removeprefix('Appendix A: ')}" for name in APPENDIX_A_ENTRIES)
            + "\n\nThese entries keep the combat chassis readable while moving the public vocabulary toward Aethrune terms."
        ),
    },
    **APPENDIX_A_ENTRIES,
    "Appendix B: Lantern Faith": {
        "menu": "Road shrines, witness lamps, field mercy, and practical doctrine.",
        "text": (
            "The Lantern Faith grew out of road practice: lamp tending, field triage, funeral witness, safe passage, "
            "and the belief that a lost traveler still deserves to be seen when systems fail."
        ),
    },
    "Appendix B: Shrine-Lanterns": {
        "menu": "Small lights that mark refuge, warning, and obligation.",
        "text": "Shrine-lanterns are practical sacred objects: part signal, part promise, part emergency sign that someone still accepts responsibility here.",
    },
    "Appendix B: Oaths": {
        "menu": "Public promises treated as load-bearing social structures.",
        "text": "In Aethrune, an oath matters because institutions are unreliable. A sworn person becomes a structure others may lean on, for good or harm.",
    },
    "Appendix B: Funeral Names": {
        "menu": "The practice of recording the dead so routes cannot erase them.",
        "text": "Lantern caretakers record names after ambushes, floods, cave-ins, and failed crossings. A name kept properly is a small refusal of disappearance.",
    },
    "Appendix B: False Doctrine": {
        "menu": "When faith language becomes a tool of control.",
        "text": "The Quiet Choir borrows the language of comfort, confession, and order. It uses those words to train obedience.",
    },
    "Appendix C: Factions Overview": {
        "menu": "The major powers competing over roads, records, claims, and truth.",
        "text": (
            "Aethrune's factions fight over roads, records, claims, and the right to define what happened. "
            "Each one has an answer for how the future should be run. The danger starts when one answer tries to close every other door."
        ),
    },
    "Appendix C: Ashen Brand": {
        "menu": "Route extortion, forged authority, and profitable fear.",
        "text": "The Ashen Brand wins by making travelers believe the road already belongs to them. Their tools include raids, fake checkpoints, stolen papers, and selective mercy.",
    },
    "Appendix C: Quiet Choir": {
        "menu": "Signal control, whispered doctrine, and obedience disguised as peace.",
        "text": "The Quiet Choir wants old systems to answer a new voice. They prefer alignment over argument and call that silence harmony.",
    },
    "Appendix C: Free Operators": {
        "menu": "Independent drivers, scouts, couriers, and troubleshooters.",
        "text": "Free Operators keep routes alive without waiting for permission. Some are heroic, some are opportunists, and most know exactly what a delayed wagon costs.",
    },
    "Appendix C: Meridian Reclaimers": {
        "menu": "Scholars and salvage crews trying to repair what can be trusted.",
        "text": "Meridian Reclaimers believe broken infrastructure can be studied, stabilized, and reused. Their best members are careful; their worst confuse usefulness with innocence.",
    },
    "Appendix C: Iron Hollow Council": {
        "menu": "Local leadership balancing fear, claims, trade, and survival.",
        "text": "The Iron Hollow Council works in a town that cannot afford grand language. Someone still has to decide whether the next wagon means guards, grain, labor, or trust.",
    },
    "Appendix C: Ironbound Guild": {
        "menu": "Supply, tools, claims, and the hard politics of repair.",
        "text": "The Ironbound Guild controls practical goods and skilled labor. That makes it essential in a crisis and tempting to anyone who wants leverage over the town.",
    },
    "Appendix C: Delvers' Exchange": {
        "menu": "Claim records, salvage reports, and dangerous information.",
        "text": "The Delvers' Exchange handles claims and discoveries. Its ledgers can settle disputes, start them, or reveal that someone has been mining the wrong truth.",
    },
    "Appendix D: Aethrune Cosmology": {
        "menu": "How the world treats echoes, channels, relics, and system memory.",
        "text": "Aethrune draws its wonder from resonance, buried command logic, living memory, and old systems that still lean on the present.",
    },
    "Appendix D: The Near World": {
        "menu": "The lived surface of roads, towns, ruins, rivers, and weather.",
        "text": "The Near World is ordinary life under extraordinary inheritance: markets, milehouses, shrines, flood channels, farms, towers, and the people trying to keep them working.",
    },
    "Appendix D: Resonance": {
        "menu": "Patterned force that lets channeling, signals, and old records matter.",
        "text": "Resonance is the setting's connective logic. Words, symbols, routes, tones, and titles can matter because the world still contains systems built to answer them.",
    },
    "Appendix D: Meridian Depths": {
        "menu": "The old lower systems where infrastructure becomes mythic.",
        "text": "The Meridian Depths are not one place but a category of buried spaces: vaults, drains, control rooms, sealed galleries, and machine-lit dark below the known map.",
    },
    "Appendix D: Echo Pockets": {
        "menu": "Localized spaces where memory, route, and cause behave strangely.",
        "text": "Echo pockets are small unstable zones where old events seem to repeat, answer, or resist being contradicted. Some are hazards; some are evidence.",
    },
    "Appendix D: Signal Paths": {
        "menu": "Old routes for command, warning, and coordination.",
        "text": "Signal paths once moved instructions across the Accord. Broken signal paths can still carry influence, especially when someone learns which phrases wake them.",
    },
    "Appendix E: SRD-Derived Mechanics": {
        "menu": "A plain-language note on the current rules chassis.",
        "text": (
            "Aethrune currently keeps an SRD-derived d20 math base for character creation, checks, combat timing, conditions, and equipment. "
            "The public presentation is being rewritten in phases so the story, setting, factions, and terminology all belong to Aethrune."
        ),
    },
    "Appendix E: Public Vocabulary": {
        "menu": "A quick bridge from old mechanics language to Aethrune language.",
        "text": (
            "Preferred public terms include Defense, strike check, resist check, edge, strain, channeling, draught, script, relic, and marks. "
            "Some internals still use legacy keys until the rules-presentation phase adds display-name adapters across combat, inventory, and saves."
        ),
    },
}


PLANNED_ACTS_LORE = {
    "Act Roadmap": {
        "menu": "How the Aethrune campaign arc is structured inside the game.",
        "text": (
            "Act I follows Greywake, the Emberway, Iron Hollow, and the Ashen Brand's attempt to turn route fear into rule. "
            "Act II descends into the Vein of Glass and the Resonant Vaults, where the Quiet Choir tries to teach old systems a new voice. "
            "Act III points toward the Meridian Depths, where survival depends on deciding what parts of the old world get restored and what parts stay broken."
        ),
    }
}


TITLE_LORE_SECTIONS: tuple[tuple[str, LoreSection], ...] = (
    ("World & Locations", LOCATION_LORE),
    ("Classes", CLASS_LORE),
    ("Peoples", RACE_LORE),
    ("Backgrounds", BACKGROUND_LORE),
    ("Core Abilities", ABILITY_LORE),
    ("Skills", SKILL_LORE),
    ("Features & Abilities", FEATURE_LORE),
    ("Appendices", APPENDIX_LORE),
)


ABILITY_LABELS = {
    "STR": "Strength",
    "DEX": "Dexterity",
    "CON": "Constitution",
    "INT": "Intelligence",
    "WIS": "Wisdom",
    "CHA": "Charisma",
}


CLASS_PRIMARY_STATS = {
    "Warrior": ["STR", "CON"],
    "Mage": ["INT", "WIS"],
    "Rogue": ["DEX", "WIS"],
}


ABILITY_GAMEPLAY_NOTES = {
    "STR": "Used for melee force, Athletics, and physical contests.",
    "DEX": "Used for initiative, stealth, finesse or ranged accuracy, and many reflex-based resist checks.",
    "CON": "Adds to hit points and helps endure poison, fatigue, and punishment.",
    "INT": "Used for learned knowledge, investigation, and studied Mage channeling.",
    "WIS": "Used for perception, intuition, wayfinding, medicine, and steady Mage channeling.",
    "CHA": "Used for social pressure, presence, deception, and forceful Mage channeling.",
}


def public_class_label(class_name: str) -> str:
    return CLASS_PUBLIC_LABELS.get(class_name, class_name)


def public_race_label(race_name: str) -> str:
    return RACE_PUBLIC_LABELS.get(race_name, race_name)


def ability_label(code: str) -> str:
    base = ABILITY_LABELS.get(code, code)
    public = ABILITY_PUBLIC_LABELS.get(code)
    return f"{public} ({base})" if public and public != base else base


def format_bonus_list(bonuses: Mapping[str, int]) -> str:
    return ", ".join(f"{ability_label(ability)} +{value}" for ability, value in bonuses.items())


def format_feature_label(feature_id: str) -> str:
    if feature_id in FEATURE_LORE and FEATURE_LORE[feature_id].get("label"):
        return FEATURE_LORE[feature_id]["label"]
    return feature_id.replace("_", " ").title()


def format_feature_entry(feature_id: str, index: int) -> str:
    description = FEATURE_LORE.get(feature_id, {}).get("text", "No description recorded yet.")
    return f"{index}. {format_feature_label(feature_id)}: {description}"


def format_weapon_summary(class_name: str) -> str:
    weapon = CLASSES[class_name]["weapon"]
    attack_stat = weapon.ability
    if attack_stat == "FINESSE":
        attack_stat = "Strength or Agility"
    elif attack_stat == "SPELL":
        attack_stat = "channeling ability"
    else:
        attack_stat = ability_label(attack_stat)
    tags: list[str] = []
    if weapon.ranged:
        tags.append("ranged")
    if weapon.finesse:
        tags.append("finesse")
    if weapon.properties:
        tags.extend(weapon.properties)
    extras = f"; properties: {', '.join(tags)}" if tags else ""
    return f"{weapon.name} dealing {weapon.damage} using {attack_stat}{extras}."


def format_armor_summary(class_name: str) -> str:
    armor = CLASSES[class_name]["armor"]
    shield = "shield included" if CLASSES[class_name]["shield"] else "no shield"
    if armor is None:
        return f"Starts unarmored with {shield}."
    defense = int(getattr(armor, "defense_points", armor.base_ac) or armor.base_ac)
    armor_bits = [f"{armor.name} (Defense {defense}, DR {base_damage_reduction_for_defense(defense):.1f}%)", shield]
    if armor.heavy:
        armor_bits.append("heavy shell")
    elif armor.dex_cap is None:
        armor_bits.append("full Agility modifier applies")
    else:
        armor_bits.append(f"Agility bonus capped at +{armor.dex_cap}")
    return ". ".join([armor_bits[0], ", ".join(armor_bits[1:])]) + "."


def format_resource_summary(resources: Mapping[str, int]) -> str:
    if not resources:
        return "No tracked class resources at level 1."
    return ", ".join(f"{name.replace('_', ' ')} {amount}" for name, amount in resources.items())


def format_class_manual(class_name: str) -> str:
    details = CLASSES[class_name]
    public_name = public_class_label(class_name)
    lines = [
        "Gameplay Manual",
        f"Public role: {public_name}",
        f"Main stats: {', '.join(ability_label(stat) for stat in CLASS_PRIMARY_STATS.get(class_name, [])) or 'Flexible'}",
        f"Hit die: d{details['hit_die']}",
        f"Resist proficiencies: {', '.join(ability_label(save) for save in details['saving_throws'])}",
        f"Skill picks: choose {details['skill_picks']} from {', '.join(details['skill_choices'])}",
        f"Starting weapon: {format_weapon_summary(class_name)}",
        f"Defense profile: {format_armor_summary(class_name)}",
        (
            f"Channeling: uses {ability_label(details['spellcasting_ability'])}; "
            f"starting resources {format_resource_summary(details['resources'])}."
            if details["spellcasting_ability"]
            else f"Channeling: none at level 1. Starting resources: {format_resource_summary(details['resources'])}."
        ),
        "Starting abilities:",
    ]
    lines.extend(format_feature_entry(feature_id, index) for index, feature_id in enumerate(details["features"], start=1))
    progression = CLASS_LEVEL_PROGRESSION.get(class_name, {})
    if progression:
        lines.append("Early progression in this game:")
        for level in sorted(progression):
            features = progression[level]["features"]
            feature_text = "; ".join(f"{rules_text(name)}: {rules_text(description)}" for name, description in features)
            lines.append(f"- Level {level}: {feature_text}")
    return "\n".join(lines)


def format_race_manual(race_name: str) -> str:
    details = RACES[race_name]
    lines = [
        "Gameplay Manual",
        f"Public people: {public_race_label(race_name)}",
        f"Ability bonuses: {format_bonus_list(details['bonuses'])}",
        f"Automatic people skills: {', '.join(details['skills']) if details['skills'] else 'None'}",
        "People traits:",
    ]
    if details["features"]:
        lines.extend(format_feature_entry(feature_id, index) for index, feature_id in enumerate(details["features"], start=1))
    else:
        lines.append("1. No extra traits beyond the listed ability increases.")
    return "\n".join(lines)


def format_background_manual(background_name: str) -> str:
    details = BACKGROUNDS[background_name]
    bonuses = details.get("equipment_bonuses", {})
    bonus_text = ", ".join(f"{key} +{value}" for key, value in bonuses.items()) if bonuses else "None"
    return "\n".join(
        [
            "Gameplay Manual",
            f"Background skills: {', '.join(details['skills'])}",
            f"Extra proficiencies: {', '.join(details.get('proficiencies', [])) or 'None'}",
            f"Game-specific passive bonuses: {bonus_text}",
            "Background perks:",
            *[f"- {note}" for note in details.get("notes", [])],
        ]
    )


def format_ability_manual(ability_code: str) -> str:
    linked_skills = sorted(skill for skill, ability in SKILL_TO_ABILITY.items() if ability == ability_code)
    matching_classes = sorted(
        public_class_label(class_name)
        for class_name, stats in CLASS_PRIMARY_STATS.items()
        if ability_code in stats
    )
    return "\n".join(
        [
            "Gameplay Manual",
            f"Public name: {ability_label(ability_code)}",
            f"Linked skills: {', '.join(linked_skills) if linked_skills else 'None'}",
            f"Common main stat for: {', '.join(matching_classes) if matching_classes else 'No class listed as primary'}",
            f"Gameplay role: {ABILITY_GAMEPLAY_NOTES.get(ability_code, 'No note recorded yet.')}",
        ]
    )


def format_skill_manual(skill_name: str) -> str:
    linked_ability = SKILL_TO_ABILITY[skill_name]
    class_sources = sorted(public_class_label(class_name) for class_name, details in CLASSES.items() if skill_name in details["skill_choices"])
    race_sources = sorted(public_race_label(race_name) for race_name, details in RACES.items() if skill_name in details["skills"])
    background_sources = sorted(BACKGROUND_LORE.get(name, {}).get("label", name) for name, details in BACKGROUNDS.items() if skill_name in details["skills"])
    return "\n".join(
        [
            "Gameplay Manual",
            f"Governing ability: {ability_label(linked_ability)}",
            f"Class access: {', '.join(class_sources) if class_sources else 'No class grants selection access'}",
            f"Automatic people access: {', '.join(race_sources) if race_sources else 'None'}",
            f"Automatic background access: {', '.join(background_sources) if background_sources else 'None'}",
            f"Gameplay role: {SKILL_LORE[skill_name]['text']}",
        ]
    )


def format_feature_manual(feature_name: str) -> str:
    class_sources = sorted(public_class_label(class_name) for class_name, details in CLASSES.items() if feature_name in details["features"])
    race_sources = sorted(public_race_label(race_name) for race_name, details in RACES.items() if feature_name in details["features"])
    return "\n".join(
        [
            "Gameplay Manual",
            f"Used by classes: {', '.join(class_sources) if class_sources else 'None at level 1'}",
            f"Used by peoples: {', '.join(race_sources) if race_sources else 'None'}",
            f"Gameplay role: {FEATURE_LORE[feature_name]['text']}",
        ]
    )


def manual_text_for_entry(section_title: str, entry_name: str) -> str:
    if section_title == "Classes" and entry_name in CLASSES:
        return format_class_manual(entry_name)
    if section_title in {"Races", "Peoples"} and entry_name in RACES:
        return format_race_manual(entry_name)
    if section_title == "Backgrounds" and entry_name in BACKGROUNDS:
        return format_background_manual(entry_name)
    if section_title == "Core Abilities" and entry_name in ABILITY_LABELS:
        return format_ability_manual(entry_name)
    if section_title == "Skills" and entry_name in SKILL_TO_ABILITY:
        return format_skill_manual(entry_name)
    if section_title == "Features & Abilities" and entry_name in FEATURE_LORE:
        return format_feature_manual(entry_name)
    return ""
