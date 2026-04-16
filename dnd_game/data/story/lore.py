from __future__ import annotations

"""Expanded lore codex entries used by the title-screen reference menu.

The text in this module is adapted from official Dungeons & Dragons material,
primarily the 2014 Basic Rules, the 2024 Free Rules, and official D&D Beyond
Forgotten Realms location features. A few local entries such as Ashfall Watch
and Emberhall Cellars are clearly marked as game-original locations that sit on
top of the official Sword Coast frame used by this project.
"""

from collections.abc import Mapping

from ...models import SKILL_TO_ABILITY
from .character_options.backgrounds import BACKGROUNDS
from .character_options.classes import CLASSES, CLASS_LEVEL_PROGRESSION
from .character_options.races import RACES


LoreEntry = dict[str, str]
LoreSection = Mapping[str, LoreEntry]


LORE_INTRO = (
    "This codex expands the title-screen lore notes into a browsable reference for the "
    "Forgotten Realms frame behind the game. The class, race, background, ability, and "
    "skill entries are grounded in official D&D rules text and D&D Beyond lore articles. "
    "Locations drawn directly from the Sword Coast are presented as official setting lore, "
    "while original adventure sites created for this game are labeled as adaptations."
)


LOCATION_LORE: dict[str, LoreEntry] = {
    "Forgotten Realms": {
        "menu": "The wider fantasy world that holds the Sword Coast and its rival powers.",
        "text": (
            "The Forgotten Realms is a crowded, ancient world where living faith, old empires, "
            "wandering monsters, and buried magic all overlap. Temples speak to gods who answer, "
            "ruins hide the work of long-fallen civilizations, and even small frontier towns may "
            "sit on layers of history older than the people now living there.\n\n"
            "For this game, that matters because adventurers are never moving through empty ground. "
            "A caravan road is also a trade artery, a political pressure point, and a line drawn "
            "across old danger. A shrine is both a place of worship and a practical refuge. In the "
            "Realms, lore is rarely decorative; it is usually the reason a place is prosperous, haunted, "
            "contested, or worth defending."
        ),
    },
    "Sword Coast": {
        "menu": "The famous western shore where trade, ruins, and frontier danger meet.",
        "text": (
            "The Sword Coast is one of the best-known regions in the Forgotten Realms: a long belt of "
            "ports, roads, farm country, wild stretches, and dangerous ruins along Faerun's western edge. "
            "Civilized centers such as Neverwinter, Waterdeep, and Baldur's Gate are linked by trade, but "
            "the countryside between them is never fully tame. Banditry, goblin tribes, local monsters, "
            "weather, and old magical scars make even an ordinary road feel like part of the adventure.\n\n"
            "That mix of commerce and peril is exactly why the Sword Coast works so well as a campaign frame. "
            "A single missing caravan can become a regional problem. A ruined tower can throttle a town's food, "
            "ore, medicine, and morale. The setting rewards heroes who can fight, negotiate, investigate, and "
            "understand how local trouble fits into a much older landscape."
        ),
    },
    "Neverwinter": {
        "menu": "The Jewel of the North, rebuilding beneath the shadow of Mount Hotenow.",
        "text": (
            "Neverwinter is one of the North's great cities, often called the Jewel of the North and the "
            "City of Skilled Hands. Official lore consistently presents it as a place of craft, trade, and "
            "stubborn recovery. The warmth of the Neverwinter River, touched by geothermal heat from nearby "
            "Mount Hotenow, historically kept the city greener and milder than outsiders expected.\n\n"
            "Modern Neverwinter lives with the memory of catastrophe. Mount Hotenow's eruption shattered the "
            "city, opened the Chasm, and left the region unstable for years, but the city did not stay broken. "
            "In this game's opening, Neverwinter functions exactly as official lore suggests it should: a place "
            "where order is trying to reassert itself, trade routes matter, and local authorities understand that "
            "protecting the road south is part of protecting the city's future."
        ),
    },
    "Mount Hotenow": {
        "menu": "The volcano whose eruption changed Neverwinter and the surrounding frontier.",
        "text": (
            "Mount Hotenow is the volcanic wound at the edge of Neverwinter's recent history. In official Sword "
            "Coast lore, its eruption devastated Neverwinter, reshaped nearby territory, and turned what had been "
            "a prosperous northern center into a place defined by rebuilding, factional pressure, and lingering "
            "fear. Even when the mountain is quiet, the eruption remains a living fact in the memories of locals.\n\n"
            "That legacy explains why the region feels slightly raw even when trade is flowing. Rebuilt walls, "
            "careful ledgers, and nervous road patrols are not just flavor. They are the social aftershocks of a "
            "city that learned how fast security, wealth, and civic pride can burn away."
        ),
    },
    "High Road": {
        "menu": "The northern trade route linking settlements along the coast.",
        "text": (
            "The High Road is one of the Sword Coast's defining overland routes, the kind of road that exists "
            "half as infrastructure and half as story engine. Merchants, messengers, mercenaries, pilgrims, and "
            "adventurers all move along it, which means news, coin, and danger do the same.\n\n"
            "In practical terms, whoever threatens the High Road threatens more than a single wagon. Raids on a "
            "major route raise prices, slow messages, isolate settlements, and convince frightened travelers to "
            "stay home. That is why the game's first ambush matters immediately: it puts the player into the "
            "official Sword Coast pattern where road safety is a political and economic concern, not merely a fight."
        ),
    },
    "Triboar Trail": {
        "menu": "The inland road branching toward Phandalin and the frontier beyond.",
        "text": (
            "The Triboar Trail is the inland road that pulls travelers away from the better-known coastal routes "
            "and into the frontier spaces that make Phandalin such a classic D&D hub. In official adventures tied "
            "to Phandalin, the trail serves as a threshold: once travelers leave the main arteries behind, the land "
            "feels less supervised, less settled, and much more vulnerable to local threats.\n\n"
            "That frontier quality is important to the tone of this game. The trail is where rumor turns into direct "
            "risk. It is close enough to civilization that caravans keep using it, but rough enough that goblins, "
            "brigands, and hidden strongholds can shape daily life for everyone living nearby."
        ),
    },
    "Phandalin": {
        "menu": "A resettled mining town where everyday survival and old ruins live side by side.",
        "text": (
            "Phandalin is one of fifth edition's most recognizable starter towns: a small frontier settlement built "
            "near the ruins of an older community and supported by miners, traders, laborers, and practical local "
            "leaders. Official material repeatedly treats it as a place where small-scale problems matter a great "
            "deal because each wagon, roof beam, work crew, and guard shift genuinely affects the town's chances.\n\n"
            "That makes Phandalin ideal for grounded heroics. Saving the town is not abstract. Reopening a road means "
            "ore moves, shelves fill, wages return, and people stop planning around fear. The game leans into that "
            "official identity: Phandalin is not a glittering capital, but it is the kind of place the Realms are "
            "worth protecting for."
        ),
    },
    "Ashfall Watch": {
        "menu": "A game-original watchtower built to feel like a believable Sword Coast frontier ruin.",
        "text": (
            "Ashfall Watch is original to this game, not an established official location, but it is intentionally "
            "designed to fit the logic of official Sword Coast adventures. Frontier D&D regularly uses old keeps, "
            "watchtowers, shrines, and ruined fortifications as pressure points where raiders can choke roads and "
            "test local authority.\n\n"
            "Within the story, Ashfall Watch represents the militarized version of a bandit problem. It is not only a "
            "hideout; it is a forward base, lookout, and symbol of intimidation. That makes it a natural escalation from "
            "roadside raids to organized coercion, which is exactly the kind of regional danger Phandalin-era adventures "
            "often build toward."
        ),
    },
    "Emberhall Cellars": {
        "menu": "A game-original ruin that echoes the buried-cellar mysteries common to Phandalin stories.",
        "text": (
            "Emberhall Cellars is another original location created for this project, but it follows an official Phandalin "
            "tradition closely. Adventures around the town love hidden lower levels, forgotten foundations, cellar routes, "
            "and older stonework beneath newer buildings because Phandalin's identity is tied to resettlement over ruins.\n\n"
            "As a result, Emberhall feels like a natural extension of the setting rather than a break from it. It stands for "
            "the older layer beneath frontier life: the buried masonry, secret storage, and inherited danger that can turn a "
            "simple settlement problem into a deeper mystery with historical roots."
        ),
    },
}


CLASS_LORE: dict[str, LoreEntry] = {
    "Barbarian": {
        "menu": "Primal warriors who survive by instinct, fury, and endurance.",
        "text": (
            "Official D&D lore does not treat barbarians as mindless berserkers. A barbarian is a warrior whose culture, "
            "training, or personal philosophy embraces primal instinct over polished civilization. The class fantasy is tied "
            "to ferocity, toughness, and the refusal to be domesticated by walls, etiquette, or fear. In many Realms-flavored "
            "stories, barbarians come from harsh homelands where physical resilience and decisive action are the difference "
            "between a living tribe and a dead one.\n\n"
            "Mechanically and narratively, rage is the center of the class. It is not simple anger so much as a battle state "
            "that channels pain into momentum. A barbarian in this campaign fits naturally as a northern outrider, tribal exile, "
            "mercenary shock trooper, or frontier guardian whose instincts are often sharper than a courtier's polished manners."
        ),
    },
    "Bard": {
        "menu": "Keepers of stories and magic whose art still carries the echo of creation.",
        "text": (
            "Bards are one of D&D's most distinctive classes because their magic is rooted in expression itself. Official class "
            "lore describes bardic power as an echo of the song of creation, a reminder that words, rhythm, memory, and performance "
            "can shape reality as surely as a wizard's formula. That makes the bard both entertainer and scholar, diplomat and spy, "
            "magician and historian.\n\n"
            "In a Sword Coast campaign, bards are often the people who know how stories travel between cities and why rumor matters. "
            "A bard can read a room, rally frightened allies, embarrass a liar, or turn an inn into an intelligence network. Their "
            "power is social without being soft: a skilled bard controls morale, reputation, and tempo before steel ever clears a sheath."
        ),
    },
    "Cleric": {
        "menu": "Divine servants whose faith becomes miracles, judgment, and refuge.",
        "text": (
            "Clerics embody one of the Forgotten Realms' defining truths: the gods are real, active, and powerful enough to answer. "
            "Official D&D material presents clerics as chosen or devoted servants whose magic comes from direct relationship with a deity, "
            "pantheon, or sacred ideal. They are not just healers. They are champions, judges, exorcists, keepers of ritual, and living "
            "proof that the divine still touches mortal affairs.\n\n"
            "On the Sword Coast, a cleric might travel as a road-priest, temple emissary, battlefield chaplain, or pilgrim tasked with "
            "repairing a wounded community. In this game's frontier context, a cleric is especially potent because faith is practical: "
            "blessings steady frightened people, healing preserves manpower, and radiant judgment pushes back the darkness old ruins invite."
        ),
    },
    "Druid": {
        "menu": "Guardians of the Old Faith who read the land as law, memory, and warning.",
        "text": (
            "Druids channel the oldest spiritual current in the game: the power of nature as a living order rather than a scenery backdrop. "
            "Official lore frames them as priests of the Old Faith, protectors of sacred groves, weather-readers, and interpreters of the "
            "balance between settlement and wilderness. Their authority comes from attunement, patience, and the refusal to see forests, "
            "storms, beasts, and seasons as lesser than cities.\n\n"
            "That perspective makes druids excellent frontier protagonists. They understand what happens when roads cut too deeply, when "
            "mines wake the wrong thing, or when desperate people ignore the health of the land that feeds them. In this campaign, a druid "
            "can feel like a quiet corrective force: never fully tame, never truly lost, and always aware that civilization survives only by "
            "negotiating with older powers."
        ),
    },
    "Fighter": {
        "menu": "Disciplined professionals who master arms, armor, and battlefield judgment.",
        "text": (
            "The fighter is the broad martial class of D&D, intentionally built to represent trained excellence rather than one narrow fantasy. "
            "Official lore supports knights, caravan guards, duelists, militia captains, mercenaries, veterans, and aristocratic weapon masters "
            "all under the same banner. What unites them is not mysticism but practiced competence.\n\n"
            "That flexibility makes fighters central to Sword Coast stories. Roads need escorts, towns need defenders, and every faction trusts "
            "some version of a well-trained warrior. A fighter in this game feels immediately at home as a shield-wall veteran, scout captain, "
            "bodyguard, or ex-soldier who understands that good steel matters most when everyone else starts panicking."
        ),
    },
    "Monk": {
        "menu": "Ascetic martial adepts who turn discipline inward until body and spirit move as one.",
        "text": (
            "Monks are D&D's spiritual martial artists, shaped by monasteries, strict traditions, and the cultivation of inner energy called ki. "
            "Official descriptions emphasize self-mastery over mere athleticism. A monk does not simply fight without armor; they refine posture, "
            "breath, timing, and perception until motion becomes defense and will becomes force.\n\n"
            "In the wider Realms, monks often arrive in a story as travelers from disciplined orders, temple-trained wanderers, or seekers testing "
            "themselves against the world. On the frontier, that creates a compelling contrast: the monk brings calm structure into places ruled by "
            "mud, fear, haste, and improvisation. Their presence implies that restraint can be just as dangerous as fury."
        ),
    },
    "Paladin": {
        "menu": "Holy champions whose sworn vows become martial and moral power.",
        "text": (
            "Paladins are not only armored warriors with a touch of healing. Official D&D lore treats them as people transformed by sacred oaths "
            "strong enough to shape reality. Their power is bound to conviction: justice, devotion, vengeance, protection, or another principle "
            "held with absolute seriousness. That is why paladins feel larger than life even at low level. They are carrying an ideal into places "
            "where compromise has become ordinary.\n\n"
            "In a frontier campaign, a paladin represents certainty under pressure. Villagers read them as reassurance, criminals read them as a "
            "problem, and allies often rally around the simple fact that someone has arrived who still believes honor can survive hardship. Their "
            "magic is the glow around that certainty, not a substitute for it."
        ),
    },
    "Ranger": {
        "menu": "Hunters, scouts, and wardens who know what the wild remembers.",
        "text": (
            "Rangers thrive where maps start thinning out. Official class lore portrays them as wanderers, hunters, trackers, monster-slayers, and "
            "guardians of borderlands who understand terrain in a way city-dwellers rarely do. A ranger does not merely travel through wilderness; "
            "they interpret it. Tracks, weather, silence, and broken branches become evidence.\n\n"
            "That makes the ranger almost perfectly matched to a Phandalin-style campaign. Frontier towns survive because someone can read danger at "
            "a distance, pick the right trail, and strike first when raiders grow bold. Whether played as a patient archer, a hard-bitten scout, or "
            "a local guide who knows every ridge and wash, the ranger gives the party a relationship with the land itself."
        ),
    },
    "Rogue": {
        "menu": "Precision specialists who win through timing, nerve, and impossible angles.",
        "text": (
            "Rogues are the class of leverage. Official D&D descriptions cover thieves, scouts, spies, assassins, gamblers, burglars, and con artists, "
            "but the core fantasy is always the same: the rogue notices the opening others miss and turns it into advantage. They survive by accuracy, "
            "mobility, and a willingness to act in the moment when hesitation would be fatal.\n\n"
            "In story terms, rogues often know how cities really function. Locks, rumors, fences, coded signals, false papers, and side doors all sit "
            "within their wheelhouse. On the frontier, that talent remains valuable because law is thinner there. A rogue can be the party's scout, "
            "interrogator, infiltrator, or practical realist when everyone else starts thinking too loudly."
        ),
    },
    "Sorcerer": {
        "menu": "Innate spellcasters whose magic erupts from bloodline, accident, or destiny.",
        "text": (
            "Sorcerers wield arcane power without the years of book-study a wizard depends on. Official lore frames that power as raw magic living inside "
            "the character: perhaps from draconic blood, a planar touch, a wild magical event, or some other force powerful enough to leave a lasting mark. "
            "Because their magic is innate, sorcerers often experience it as identity as much as technique.\n\n"
            "That creates a distinct narrative flavor. A wizard asks what spell is prepared; a sorcerer asks what power wants out. In a Sword Coast story, "
            "sorcerers can feel uncanny even when trusted, because their gift reminds everyone that magic is not always learned, licensed, or safe. Their "
            "presence is often dramatic before they ever cast a spell."
        ),
    },
    "Warlock": {
        "menu": "Occult wielders whose power comes from bargains with forces beyond the ordinary.",
        "text": (
            "Warlocks stand at the intersection of ambition and risk. Official D&D lore defines them by pact magic: power granted through a bargain, bond, "
            "or deep supernatural relationship with an otherworldly patron. That patron might be infernal, fey, cosmic, or something stranger, but the class "
            "always carries the question of cost. Who granted this power, and why?\n\n"
            "Narratively, warlocks bring tension wherever they go. They often know secrets respectable mages avoid, and they carry a confidence that can feel "
            "either seductive or alarming depending on who is watching. In a frontier campaign, a warlock is a reminder that desperation breeds bargains and "
            "that not every useful power arrives with a temple's blessing or a school's approval."
        ),
    },
    "Wizard": {
        "menu": "Scholars of the arcane who shape reality through study, memory, and written formulae.",
        "text": (
            "Wizards are the classic learned spellcasters of D&D: researchers, collectors of formulae, keepers of spellbooks, and intellectual engineers of "
            "the impossible. Official class lore emphasizes that wizardry is earned through study, discipline, and relentless curiosity. Where a sorcerer is "
            "born with power, a wizard builds power piece by piece.\n\n"
            "That makes the wizard deeply tied to ruins, libraries, lost cities, and old mistakes. Wizards adventure because ancient magic is rarely sitting "
            "conveniently on a classroom shelf. In a Sword Coast game, the wizard often becomes the party member most alert to hidden meaning: old inscriptions, "
            "strange symbols, magical residue, and the terrifying possibility that a forgotten cellar contains something the present age was wise to forget."
        ),
    },
}


RACE_LORE: dict[str, LoreEntry] = {
    "Human": {
        "menu": "Adaptable, ambitious people whose short lives often push them to act quickly.",
        "text": (
            "Humans are the great generalists of official D&D lore. They are everywhere, build quickly, adapt quickly, and rarely wait for history to slow down "
            "for them. Their shorter lives compared with elves and dwarves often translate into urgency: kingdoms rise fast, fortunes change fast, and human ambition "
            "reshapes the map generation by generation.\n\n"
            "On the Sword Coast, humans are common in cities, villages, mercenary companies, trade houses, temples, and frontier settlements alike. That ubiquity gives "
            "them narrative flexibility. A human adventurer might be ordinary by ancestry, but that very flexibility suits a game about roads, reinvention, and choices "
            "made under pressure."
        ),
    },
    "Dwarf": {
        "menu": "Stone-blooded folk of clan, craft, endurance, and long memory.",
        "text": (
            "Dwarves are defined in official lore by resilience, craftsmanship, and loyalty to clan and tradition. Their stories are saturated with halls delved from "
            "mountain roots, ancestral pride, grudges remembered across decades, and beauty found in enduring work rather than fleeting fashion.\n\n"
            "A dwarf on the frontier often reads as fundamentally dependable. They value sturdy walls, honest labor, and promises meant to last. In a region where towns "
            "can be half-built and roads half-secured, dwarven steadiness carries both emotional and practical weight."
        ),
    },
    "Elf": {
        "menu": "Long-lived people of grace, memory, and sharpened senses.",
        "text": (
            "Official D&D elves are shaped by time. Their long lives produce patience, perspective, and an almost haunting sense that the present is only one brief movement "
            "in a much longer song. They are often described as graceful, perceptive, and touched by fey ancestry, which helps explain their elegance, discipline, and distance.\n\n"
            "That long memory can be a gift or burden on the Sword Coast. An elf may recognize patterns others dismiss, remember old names buried beneath new settlements, or "
            "treat today's panic as one more turn in a cycle already centuries deep."
        ),
    },
    "Halfling": {
        "menu": "Small wanderers whose luck, courage, and practicality keep them alive.",
        "text": (
            "Halflings are often underestimated, which official D&D lore treats as a mistake people keep making. They are small, yes, but also steady, resourceful, socially warm, "
            "and astonishingly difficult to break. Their stories value comfort, food, fellowship, and quick wits, but that does not make them timid. It makes them people who know "
            "exactly what is worth preserving.\n\n"
            "A halfling adventurer brings a grounded tone to a frontier campaign. They understand campfire morale, practical travel, and the difference between reckless heroics and "
            "brave action taken for the right reasons."
        ),
    },
    "Dragonborn": {
        "menu": "Proud draconic heirs marked by honor, will, and elemental ancestry.",
        "text": (
            "Dragonborn carry the visual and spiritual echo of dragons without being dragons themselves. Official lore emphasizes pride, personal honor, self-mastery, and the deep "
            "importance of clan or inherited legacy. Their draconic ancestry is not cosmetic; it shapes how they think about strength, reputation, and the proper use of power.\n\n"
            "In a frontier game, a dragonborn often enters a scene already commanding attention. Their bearing can suggest nobility, severity, or disciplined intensity, and their "
            "presence reminds other characters that ancient bloodlines still walk the common road."
        ),
    },
    "Gnome": {
        "menu": "Sharp-minded folk of invention, curiosity, and quietly stubborn optimism.",
        "text": (
            "Official gnome lore mixes intellect with delight. Gnomes are clever, inquisitive, playful, and often drawn toward craft, illusion, investigation, and invention. They are "
            "the kind of people who take the world seriously without surrendering their sense of wonder.\n\n"
            "That combination makes gnomes particularly strong fits for mystery-heavy adventures. A gnome can be the party member who sees the strange hinge, the forged seal, or the "
            "arcane pattern everyone else stepped over. Their curiosity is not idle. It is often how danger gets recognized in time."
        ),
    },
    "Half-Elf": {
        "menu": "Bridge-walkers who often learn to read more than one world at once.",
        "text": (
            "Half-elves are defined in official lore by dual belonging and partial exclusion. They often move between human and elven cultures without being entirely claimed by either, "
            "which can produce flexibility, empathy, loneliness, or sharpened social awareness depending on the character.\n\n"
            "That makes them excellent adventurers in a setting full of mixed loyalties and shifting alliances. A half-elf often knows how to listen across differences, adapt without "
            "forgetting themselves, and survive the quiet work of never assuming a room will welcome them automatically."
        ),
    },
    "Half-Orc": {
        "menu": "Intense, resilient survivors who feel everything with frightening force.",
        "text": (
            "Official half-orc lore stresses emotional intensity as much as physical power. Half-orcs are strong and durable, but also passionate, easily roused, deeply loyal, and often "
            "forced to define themselves against other people's fear or prejudice. They may carry scars proudly, bitterly, or both.\n\n"
            "In a frontier campaign, that intensity can become a dramatic strength. A half-orc hero often reads as someone who knows hardship personally and therefore refuses to look away "
            "when others are being cornered by the same forces."
        ),
    },
    "Tiefling": {
        "menu": "Marked descendants of infernal influence who survive through poise and self-definition.",
        "text": (
            "Tieflings occupy one of D&D's most durable social roles: visibly uncanny people who must decide for themselves what their inherited mark means. Official lore repeatedly notes "
            "that tieflings are treated with suspicion, often living as minorities inside human-majority settlements, and learn early to rely on self-possession, wit, and carefully chosen loyalty.\n\n"
            "That gives tieflings strong natural tension in any town-centered story. A tiefling adventurer may understand mistrust better than most and can turn that hard-earned composure "
            "into either charisma, defiance, mischief, or relentless control."
        ),
    },
    "Goliath": {
        "menu": "Mountain nomads who measure life by hardship, honor, and earned worth.",
        "text": (
            "Official goliath lore presents them as reclusive highland people shaped by cold air, thin resources, and a culture where every individual must prove useful to the tribe. Their "
            "stone-like appearance, physical power, and competitive spirit all grow from a homeland where failure can cost more than pride.\n\n"
            "A goliath adventurer often carries that mountain ethic into lower lands. Deeds matter, excuses do not, and survival is a team responsibility. On the Sword Coast, a goliath can "
            "feel both alien and deeply honorable: a wanderer carved by places most townsfolk would never willingly climb."
        ),
    },
    "Orc": {
        "menu": "Forceful, direct people associated with endurance, momentum, and fierce pride.",
        "text": (
            "Official modern D&D treatments of orcs emphasize strength, drive, and cultural variety rather than flattening them into a single stereotype. They are often portrayed as intense, "
            "hardy, and action-oriented, with a strong sense of presence and a willingness to press forward when others would balk.\n\n"
            "Used thoughtfully in a frontier campaign, an orc character can embody momentum and refusal. They are especially effective in stories about survival, contested belonging, and the "
            "choice to become protector rather than raider."
        ),
    },
}


BACKGROUND_LORE: dict[str, LoreEntry] = {
    "Soldier": {
        "menu": "A veteran of organized violence who knows discipline, rank, and survival.",
        "text": (
            "Official soldier backgrounds assume more than weapon familiarity. A soldier has lived inside structure: rank, orders, camp routine, battlefield fear, and the practical skills that "
            "keep a line from collapsing. Whether that service was national, mercenary, or local militia, it leaves habits that do not disappear when the uniform comes off.\n\n"
            "In this game, a soldier background ties naturally into road security, patrol logic, and the sober understanding that weak logistics lose wars before swords ever cross."
        ),
    },
    "Acolyte": {
        "menu": "A temple servant shaped by ritual, devotion, and sacred obligations.",
        "text": (
            "The acolyte background in official D&D speaks to service more than power. An acolyte performs rites, studies doctrine, tends shrines, and acts as an intermediary between everyday "
            "people and the sacred world. Some become full clerics, but many are simply devout and well-trained.\n\n"
            "That background adds social weight to religion in the story. An acolyte knows how temples operate, how pilgrims think, and why sacred places remain practical institutions as well "
            "as spiritual ones."
        ),
    },
    "Criminal": {
        "menu": "An underworld survivor who understands secrecy, leverage, and bad neighborhoods.",
        "text": (
            "Official criminal backgrounds are about more than theft. They imply familiarity with vice, hidden markets, coded trust, fences, safehouses, and the social underside that respectable "
            "people prefer not to name. A criminal survives by reading danger, spotting opportunity, and knowing which rules are real only because someone can enforce them.\n\n"
            "On the Sword Coast frontier, that perspective is often useful. Smuggling routes, forged papers, and quiet middlemen matter whenever raiders start turning trade into an extortion game."
        ),
    },
    "Sage": {
        "menu": "A learned researcher whose curiosity and memory are as useful as any weapon.",
        "text": (
            "Official sages are people who spent years with manuscripts, libraries, lectures, and unanswered questions. Their strength lies not only in what they know, but in how they pursue what "
            "they do not know yet. A sage expects mystery to have context.\n\n"
            "That makes the background especially potent in a setting full of ruins and inherited trouble. A sage sees old inscriptions, local legends, and strange magical residue as leads rather "
            "than decoration."
        ),
    },
    "Outlander": {
        "menu": "A wanderer of wild places who trusts trailcraft more than walls.",
        "text": (
            "The outlander background represents people shaped by life beyond settled roads: hunters, guides, scouts, nomads, and drifters who know how to find food, read weather, and keep moving. "
            "Official D&D uses the background to mark someone who belongs to the margins of civilization without necessarily rejecting it.\n\n"
            "In a campaign around Phandalin, outlanders carry immediate credibility. They understand why a missing trail sign, dead cookfire, or badly cut track can say more than a frightened witness."
        ),
    },
    "Charlatan": {
        "menu": "A confidence artist who survives by performance, disguise, and nerve.",
        "text": (
            "Official charlatans are professional fabricators: swindlers, forgers, false healers, stage magicians, and social predators who know exactly how badly people want a convincing lie. "
            "Their craft depends on showmanship, timing, and reading weakness without flinching.\n\n"
            "That background can produce an especially flavorful adventurer because the same talents that support fraud also support infiltration, improvisation, and fast social recovery when a plan breaks."
        ),
    },
    "Guild Artisan": {
        "menu": "A trained craftsperson who understands quality, contracts, and civic reputation.",
        "text": (
            "Guild artisans in official lore belong to the working machinery of a city or town. They know trade standards, supply chains, craftsmanship, pricing, apprenticeships, and the fragile web "
            "of trust that lets strangers buy one another's labor. They are practical professionals, not just flavor text.\n\n"
            "In a frontier economy, that knowledge becomes quietly heroic. An artisan knows what shortages mean, what a damaged road does to livelihoods, and how much civilization depends on people "
            "doing ordinary work well."
        ),
    },
    "Hermit": {
        "menu": "A secluded seeker whose solitude sharpened insight rather than softening it.",
        "text": (
            "The official hermit background is built around withdrawal, contemplation, and a truth discovered in solitude. Hermits may be healers, visionaries, exiles, mystics, or people who stepped "
            "away from society long enough to see it more clearly on their return.\n\n"
            "That makes the background excellent for characters who feel slightly offset from the rest of the world. In this game's tone, a hermit often reads as someone who recognizes omens, sickness, "
            "patterns, and spiritual danger before more worldly people admit anything is wrong."
        ),
    },
}


ABILITY_LORE: dict[str, LoreEntry] = {
    "STR": {
        "menu": "Strength measures force, lifting power, and the ability to impose yourself physically.",
        "text": (
            "Strength governs raw physical might in official D&D. It covers pushing, climbing, jumping, grappling, hauling, forcing doors, and turning mass into action. A high-Strength character is "
            "not automatically huge, but they do possess the kind of bodily authority that changes a scene the moment force becomes relevant.\n\n"
            "In this game, Strength-heavy characters feel direct and decisive. They solve problems by breaking lines, holding positions, dragging allies clear, and making sure a hostile body stays exactly "
            "where they put it."
        ),
    },
    "DEX": {
        "menu": "Dexterity measures balance, speed, precision, and controlled movement.",
        "text": (
            "Dexterity is official D&D's measure of agility and finesse. It influences stealth, initiative, careful handwork, missile accuracy, evasive movement, and the physical confidence needed to place "
            "your body exactly where danger is not.\n\n"
            "A high-Dexterity adventurer feels sharp even while standing still. They are the ones who slip through gaps, react before the crowd finishes gasping, and make difficult actions look effortless."
        ),
    },
    "CON": {
        "menu": "Constitution measures stamina, toughness, and the ability to keep going.",
        "text": (
            "Constitution represents the body's staying power: resistance to fatigue, pain, poison, exposure, and the general wear of being alive in dangerous circumstances. Official rules tie it directly "
            "to hit points because tough bodies remain functional longer under pressure.\n\n"
            "In narrative terms, high Constitution is the quality that lets a character travel sick, fight hurt, or finish the climb when everyone else is already shaking."
        ),
    },
    "INT": {
        "menu": "Intelligence measures study, recall, analysis, and disciplined reasoning.",
        "text": (
            "Intelligence is the official home of learned knowledge and careful inference. Arcana, History, Nature, Investigation, and Religion all draw on it because Intelligence characters understand patterns, "
            "classifications, records, and the logic beneath appearances.\n\n"
            "A high-Intelligence adventurer is often the person who notices that a strange event is not random, a symbol is not decorative, and a local rumor sounds like a damaged version of an older fact."
        ),
    },
    "WIS": {
        "menu": "Wisdom measures perception, intuition, judgment, and spiritual attunement.",
        "text": (
            "Wisdom in official D&D is less about book learning and more about awareness. It governs noticing, reading people, tending wounds, surviving outdoors, handling animals, and sensing what the moment "
            "actually requires. Wisdom characters are grounded in present reality.\n\n"
            "That can look quiet, but it is invaluable. Wisdom is the score that catches lies in a voice, danger in a treeline, and panic in a patient's breathing before the room realizes anything is wrong."
        ),
    },
    "CHA": {
        "menu": "Charisma measures force of presence, persuasion, identity, and social weight.",
        "text": (
            "Officially, Charisma is not just charm. It is the strength of personality that lets a character persuade, deceive, command, perform, intimidate, and anchor magic through pure selfhood. High Charisma "
            "means other people feel you, whether they adore you, fear you, or simply cannot ignore you.\n\n"
            "In play, Charisma often decides whether a tense scene becomes a fight, a confession, a bargain, or a memorable lie somebody almost believes."
        ),
    },
}


SKILL_LORE: dict[str, LoreEntry] = {
    "Acrobatics": {
        "menu": "Keeping balance, landing safely, and controlling motion under pressure.",
        "text": "Acrobatics is the skill of balance, dives, tumbling, and staying upright when the environment turns unfriendly. It is the language of rope bridges, slick stone, leaps, sudden drops, and movement that has to be elegant because clumsy would be fatal.",
    },
    "Animal Handling": {
        "menu": "Calming, guiding, and reading beasts without treating them like machines.",
        "text": "Animal Handling reflects the judgment needed to soothe mounts, assess temperament, and work with living creatures instead of against them. In a Sword Coast campaign, it covers road horses, farm animals, trained hounds, and frightened beasts that react badly to panic.",
    },
    "Arcana": {
        "menu": "Recognizing magical theory, traditions, symbols, and supernatural structures.",
        "text": "Arcana is learned magical literacy. It helps a character identify spells, magical schools, occult signs, planar influences, and the habits of arcane practice. It is how a party member stops seeing 'weird' and starts seeing specific danger.",
    },
    "Athletics": {
        "menu": "Climbing, swimming, forcing movement, and winning physical contests.",
        "text": "Athletics is applied Strength: climbing with purpose, swimming in bad conditions, jumping cleanly, wrestling, and overpowering resistance. It is the skill of bodies doing hard things when there is no elegant shortcut.",
    },
    "Deception": {
        "menu": "Lies, misdirection, false confidence, and social sleight of hand.",
        "text": "Deception governs a character's ability to mislead without immediately collapsing under scrutiny. Good deception is not only lying well. It is offering the right lie for the listener, with the right timing, tone, and amount of detail.",
    },
    "History": {
        "menu": "Remembering states, wars, bloodlines, events, and the shape of the past.",
        "text": "History is the skill that turns names and ruins into context. It covers old kingdoms, noble lines, battles, treaties, famous disasters, and the kinds of buried precedent that keep haunting the present in the Forgotten Realms.",
    },
    "Insight": {
        "menu": "Reading motives, tension, sincerity, and emotional fractures.",
        "text": "Insight is social perception. It measures how well a character notices hesitation, fear, hidden hostility, guilt, or genuine conviction. Strong Insight often keeps a scene from being interpreted too literally.",
    },
    "Intimidation": {
        "menu": "Applying threat, force of personality, or implied violence to control a scene.",
        "text": "Intimidation is the art of making someone believe resistance will cost them. It can sound like a growl, a cold promise, an unblinking stare, or quiet certainty from someone obviously able to follow through.",
    },
    "Investigation": {
        "menu": "Searching carefully, connecting clues, and noticing how things fit together.",
        "text": "Investigation is deliberate reasoning applied to physical evidence. It covers searching rooms, studying ledgers, spotting hidden compartments, reconstructing events, and identifying the pattern underneath scattered clues.",
    },
    "Medicine": {
        "menu": "Diagnosing wounds, stabilizing the hurt, and understanding bodily distress.",
        "text": "Medicine measures practical knowledge of illness, injury, anatomy, and emergency care. It is the skill that knows the difference between dramatic blood and dangerous blood, or between someone who is dying now and someone who can still be saved.",
    },
    "Nature": {
        "menu": "Knowing terrain, weather, plants, beasts, and the logic of the wild.",
        "text": "Nature is learned knowledge about the natural world rather than instinctive field sense. It helps identify dangerous flora, local fauna, weather patterns, minerals, and the environmental context surrounding an expedition.",
    },
    "Perception": {
        "menu": "Noticing what is present right now before it notices you.",
        "text": "Perception is immediate awareness: hidden movement, distant shapes, odd sounds, shifted dust, fresh smoke, or the expression someone thought they concealed. It is one of the most important survival skills on any dangerous road.",
    },
    "Performance": {
        "menu": "Captivating an audience through music, acting, or deliberate spectacle.",
        "text": "Performance is not casual charm. It is crafted expression meant to move a crowd, hold attention, sell emotion, or create a persona stronger than the person underneath it. Bards love it, but con artists and nobles can weaponize it too.",
    },
    "Persuasion": {
        "menu": "Winning cooperation through honesty, reason, empathy, or social grace.",
        "text": "Persuasion is influence without overt coercion. It covers diplomacy, negotiation, reassurance, appeals to duty, and the ability to make someone feel that agreeing with you is sensible, honorable, or safe.",
    },
    "Religion": {
        "menu": "Knowing gods, rites, sacred signs, heresies, and divine traditions.",
        "text": "Religion is learned understanding of the sacred order: deities, temples, ceremonies, celestial and fiendish symbolism, holy law, and the practical habits of faith communities. In the Realms, that knowledge matters because divine power is not hypothetical.",
    },
    "Sleight of Hand": {
        "menu": "Fine manual control used for palming, planting, hiding, or lifting objects.",
        "text": "Sleight of Hand is delicate dexterity with intent behind it. Picking pockets is the obvious example, but the skill also covers concealment, silent object work, cheating tricks, and any movement of the fingers that must happen cleanly and unnoticed.",
    },
    "Stealth": {
        "menu": "Moving unseen, unheard, or unremarked despite active risk.",
        "text": "Stealth is more than crouching. It is light placement, timing, shadow use, breath control, and understanding lines of sight. Good stealth often depends as much on patience and judgment as on agility.",
    },
    "Survival": {
        "menu": "Tracking, foraging, navigation, and staying alive outside comfort.",
        "text": "Survival is the fieldcraft skill. It covers reading tracks, finding safe routes, locating food and water, predicting practical dangers, and making decisions that keep a group alive when walls and supply rooms are far away.",
    },
}


FEATURE_LORE: dict[str, LoreEntry] = {
    "rage": {"menu": "Barbarian fury turned into a deliberate battle state.", "text": "Rage is the barbarian's defining ability: a focused eruption of primal ferocity that hardens the body against pain and drives each strike harder. In lore terms, it is the moment instinct stops being background emotion and becomes a weapon."},
    "unarmored_defense_barbarian": {"menu": "Surviving through toughness and instinct instead of armor.", "text": "Barbarian Unarmored Defense reflects the idea that some warriors are so physically hardened and so combat-aware that plates and mail become optional. Their durability comes from body knowledge, not polished equipment."},
    "bard_spellcasting": {"menu": "Magic expressed through art, words, memory, and rhythm.", "text": "Bardic spellcasting channels the official idea that creation itself has a song-like structure. A bard's magic feels social and artistic, but it is no less real than any wizard's formula."},
    "bardic_inspiration": {"menu": "A bard's gift for turning timing and morale into real advantage.", "text": "Bardic Inspiration is the mechanical proof that courage, confidence, and good words can change outcomes. It turns the bard from a performer into an active shaper of the party's momentum."},
    "cleric_spellcasting": {"menu": "Miracles granted through faith and divine favor.", "text": "Cleric spellcasting exists because the gods answer. Each prayer, invocation, or sacred sign reflects a channel between mortal service and divine power."},
    "druid_spellcasting": {"menu": "Nature's power called through reverence, balance, and old rites.", "text": "Druid spellcasting feels ancient because it is rooted in weather, flame, growth, decay, and the living cycles that existed before many kingdoms did. It is natural power treated as sacred law."},
    "second_wind": {"menu": "A fighter's trained ability to rally even while hurt.", "text": "Second Wind represents the veteran trick of forcing the body to recover enough to keep fighting. It is discipline made physical: the refusal to surrender the battle just because the battle is finally hurting back."},
    "martial_arts": {"menu": "Monastic combat built on timing, precision, and disciplined repetition.", "text": "Martial Arts lets the monk turn the body into a practiced weapon. The feature reflects years of training rather than brute force, which is why speed and control matter more than heavy gear."},
    "unarmored_defense_monk": {"menu": "Avoiding harm through awareness, posture, and inner balance.", "text": "Monk Unarmored Defense expresses the fantasy that perfect discipline can replace armor. The monk survives not by absorbing the blow, but by being centered enough that the blow lands poorly or not at all."},
    "lay_on_hands": {"menu": "Paladin healing delivered through sacred touch and will.", "text": "Lay on Hands is one of the clearest signs that a paladin's oath has real power. It turns conviction into healing, making the paladin a frontline protector rather than a warrior who merely talks about mercy."},
    "divine_smite": {"menu": "Radiant judgment poured through a weapon strike.", "text": "Divine Smite is what happens when righteous conviction stops arguing and starts landing. It is a perfect paladin feature because it fuses martial presence and sacred wrath into one decisive moment."},
    "natural_explorer": {"menu": "A ranger's practiced edge in wild and roadless places.", "text": "Natural Explorer reflects the ranger's comfort in difficult terrain and uncertain travel. It marks someone who has spent enough time outdoors that the land itself becomes an ally rather than an obstacle."},
    "sneak_attack": {"menu": "Rogue precision that punishes distraction and exposed openings.", "text": "Sneak Attack is not about cowardice. It is about accuracy. The rogue waits for imbalance, distraction, or vulnerability and then turns a normal hit into a fight-changing strike."},
    "expertise": {"menu": "Exceptional specialization that pushes a trained skill into mastery.", "text": "Expertise represents focus so practiced that ordinary proficiency is no longer enough to describe it. Rogues excel at it because their fantasy revolves around being meaningfully better at a few critical things than almost anyone else."},
    "sorcerer_spellcasting": {"menu": "Arcane power flowing from within instead of from a book.", "text": "Sorcerer spellcasting feels immediate and personal because the magic is part of the caster. It often reads as instinct, temperament, lineage, or destiny made visible."},
    "warlock_spellcasting": {"menu": "Occult magic granted by pact, patronage, and dangerous knowledge.", "text": "Warlock magic carries the flavor of a relationship behind every spell. Its power feels compact, forceful, and slightly unsettling because someone or something beyond the caster helped open that door."},
    "wizard_spellcasting": {"menu": "Arcane power structured through study, preparation, and written craft.", "text": "Wizard spellcasting is the most scholarly magic in the game. Its reliability comes from preparation, not spontaneity, which is why wizards feel like researchers even in the middle of danger."},
    "arcane_recovery": {"menu": "A wizard's ability to reclaim focus through disciplined rest.", "text": "Arcane Recovery reflects efficient magical scholarship. A practiced wizard can pause, reorganize, and pull a little more utility from a mind trained to treat spellcasting as controlled intellectual work."},
    "darkvision": {"menu": "Seeing in darkness better than ordinary folk.", "text": "Darkvision is one of the most common fantasy heritage traits in D&D. In story terms, it marks peoples shaped by subterranean halls, moonlit forests, or other environments where darkness is normal rather than exceptional."},
    "dwarven_resilience": {"menu": "Dwarven toughness against poison and bodily hardship.", "text": "Dwarven resilience embodies the old fantasy of stout folk who outlast what would drop others. It fits a people famous for hard labor, strong drink, stubborn lungs, and underground endurance."},
    "keen_senses": {"menu": "Elven sharpness of hearing, sight, and notice.", "text": "Keen Senses reflects the heightened awareness that official lore often attaches to elves. It is less a trick than a way of being: their attention catches more of the world before it fades."},
    "fey_ancestry": {"menu": "Resistance rooted in ancient ties to the Feywild.", "text": "Fey Ancestry marks peoples whose blood still carries the influence of the fey. It suggests a mind shaped by an older, stranger heritage that does not submit easily to enchantment."},
    "lucky": {"menu": "Halfling fortune that keeps disaster from landing cleanly.", "text": "Halfling luck is one of D&D's most charming racial signatures. It turns the halfling fantasy into mechanics: disaster almost catches them, then somehow does not."},
    "brave": {"menu": "Halfling courage that resists fear better than outsiders expect.", "text": "Brave suits halflings because official lore treats them as warm and practical rather than naive. They know fear, but they do not let it own them for long."},
    "draconic_presence": {"menu": "The social and spiritual weight of draconic heritage.", "text": "Draconic presence represents the way dragonborn often carry themselves with unmistakable force. Even before a dragonborn speaks, their ancestry suggests intensity, pride, and command."},
    "gnome_cunning": {"menu": "Sharp gnomish resistance against mental intrusion and trickery.", "text": "Gnome Cunning captures the race's official association with intellect, wit, and mental resilience. Gnomes are hard to fool in the deeper magical sense because their minds stay quick and active."},
    "relentless_endurance": {"menu": "Half-orc refusal to fall when the fight says they should.", "text": "Relentless Endurance is the half-orc fantasy made concrete: too angry, proud, or stubborn to stay down just because the body reached its limit a heartbeat ago."},
    "menacing": {"menu": "A fearsome bearing that turns presence into pressure.", "text": "Menacing does not require cruelty. It reflects the reality that some people have a naturally intimidating edge, and others decide quickly not to test them."},
    "hellish_resistance": {"menu": "Tiefling endurance against the fires linked to infernal blood.", "text": "Hellish Resistance gives tieflings a visible reminder that their ancestry has consequences. The fire that harms others does not own them so easily."},
    "stone_endurance": {"menu": "Goliath grit that weathers punishment like mountain rock.", "text": "Stone's Endurance expresses the goliath ideal of bodily toughness forged by brutal terrain. The feature feels like a mountain-bred instinct to absorb hardship and keep climbing."},
    "adrenaline_rush": {"menu": "Orc momentum turned into sudden explosive drive.", "text": "Adrenaline Rush matches the orc image of forceful forward motion. It is the moment when urgency becomes physical acceleration and hesitation simply disappears."},
}


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_condition_entry(menu: str, summary: str, rules: list[str]) -> LoreEntry:
    return {
        "menu": menu,
        "text": summary + "\n\nRules reference:\n" + bullet_list(rules),
    }


def build_deity_roster_text(intro: str, deities: list[tuple[str, str, str, str, str]]) -> str:
    lines = [
        f"{name} ({alignment}): {portfolio}; domains {domains}; symbol {symbol}."
        for name, portfolio, alignment, domains, symbol in deities
    ]
    return intro + "\n\nRoster:\n" + bullet_list(lines)


def build_appendix_contents_text(intro: str, sections: list[str], *, footer: str = "") -> str:
    text = intro + "\n\nContents:\n" + bullet_list(sections)
    if footer:
        text += "\n\n" + footer
    return text


APPENDIX_A_ENTRIES: dict[str, LoreEntry] = {}
FORGOTTEN_REALMS_DEITIES: list[tuple[str, str, str, str, str]] = []
CELTIC_DEITIES: list[tuple[str, str, str, str, str]] = []
GREEK_DEITIES: list[tuple[str, str, str, str, str]] = []
EGYPTIAN_DEITIES: list[tuple[str, str, str, str, str]] = []
NORSE_DEITIES: list[tuple[str, str, str, str, str]] = []
APPENDIX_LORE: dict[str, LoreEntry] = {}


FORGOTTEN_REALMS_DEITIES.extend(
    [
        ("Auril", "goddess of winter", "NE", "Nature, Tempest", "six-pointed snowflake"),
        ("Azuth", "god of wizards", "LN", "Knowledge", "left hand pointing upward, outlined in fire"),
        ("Bane", "god of tyranny", "LE", "War", "upright black right hand, thumb and fingers together"),
        ("Beshaba", "goddess of misfortune", "CE", "Trickery", "black antlers"),
        ("Bhaal", "god of murder", "NE", "Death", "skull surrounded by a ring of blood droplets"),
        ("Chauntea", "goddess of agriculture", "NG", "Life", "sheaf of grain or a blooming rose over grain"),
        ("Cyric", "god of lies", "CE", "Trickery", "white jawless skull on black or purple sunburst"),
        ("Deneir", "god of writing", "NG", "Knowledge", "lit candle above an open eye"),
        ("Eldath", "goddess of peace", "NG", "Life, Nature", "waterfall plunging into still pool"),
        ("Gond", "god of craft", "N", "Knowledge", "toothed cog with four spokes"),
        ("Helm", "god of protection", "LN", "Life, Light", "staring eye on upright left gauntlet"),
        ("Ilmater", "god of endurance", "LG", "Life", "hands bound at the wrist with red cord"),
        ("Kelemvor", "god of the dead", "LN", "Death", "upright skeletal arm holding balanced scales"),
        ("Lathander", "god of birth and renewal", "NG", "Life, Light", "road traveling into a sunrise"),
        ("Leira", "goddess of illusion", "CN", "Trickery", "point-down triangle containing a swirl of mist"),
        ("Lliira", "goddess of joy", "CG", "Life", "triangle of three six-pointed stars"),
        ("Loviatar", "goddess of pain", "LE", "Death", "nine-tailed barbed scourge"),
        ("Malar", "god of the hunt", "CE", "Nature", "clawed paw"),
        ("Mask", "god of thieves", "CN", "Trickery", "black mask"),
        ("Mielikki", "goddess of forests", "NG", "Nature", "unicorn's head"),
        ("Milil", "god of poetry and song", "NG", "Light", "five-stringed harp made of leaves"),
        ("Myrkul", "god of death", "NE", "Death", "white human skull"),
        ("Mystra", "goddess of magic", "NG", "Knowledge", "circle of seven stars, or nine stars encircling a flowing red mist, or a single star"),
        ("Oghma", "god of knowledge", "N", "Knowledge", "blank scroll"),
        ("Savras", "god of divination and fate", "LN", "Knowledge", "crystal ball containing many kinds of eyes"),
        ("Selune", "goddess of the moon", "CG", "Knowledge, Life", "pair of eyes surrounded by seven stars"),
        ("Shar", "goddess of darkness and loss", "NE", "Death, Trickery", "black disk encircled with a border"),
        ("Silvanus", "god of wild nature", "N", "Nature", "oak leaf"),
        ("Sune", "goddess of love and beauty", "CG", "Life, Light", "face of a beautiful red-haired woman"),
        ("Talona", "goddess of disease and poison", "CE", "Death", "three teardrops on a triangle"),
        ("Talos", "god of storms", "CE", "Tempest", "three lightning bolts radiating from a central point"),
        ("Tempus", "god of war", "N", "War", "upright flaming sword"),
        ("Torm", "god of courage and self-sacrifice", "LG", "War", "white right gauntlet"),
        ("Tymora", "goddess of good fortune", "CG", "Trickery", "face-up coin"),
        ("Tyr", "god of justice", "LG", "War", "balanced scales resting on a warhammer"),
        ("Umberlee", "goddess of the sea", "CE", "Tempest", "wave curling left and right"),
        ("Waukeen", "goddess of trade", "N", "Knowledge, Trickery", "upright coin with Waukeen's profile facing left"),
    ]
)

CELTIC_DEITIES.extend(
    [
        ("The Daghdha", "god of weather and crops", "CG", "Nature, Trickery", "bubbling cauldron or shield"),
        ("Arawn", "god of life and death", "NE", "Life, Death", "black star on gray background"),
        ("Belenus", "god of sun, light, and warmth", "NG", "Light", "solar disk and standing stones"),
        ("Brigantia", "goddess of rivers and livestock", "NG", "Life", "footbridge"),
        ("Diancecht", "god of medicine and healing", "LG", "Life", "crossed oak and mistletoe branches"),
        ("Dunatis", "god of mountains and peaks", "N", "Nature", "red sun-capped mountain peak"),
        ("Goibhniu", "god of smiths and healing", "NG", "Knowledge, Life", "giant mallet over sword"),
        ("Lugh", "god of arts, travel, and commerce", "CN", "Knowledge, Life", "pair of long hands"),
        ("Manannan mac Lir", "god of oceans and sea creatures", "LN", "Nature, Tempest", "wave of white water on green"),
        ("Math Mathonwy", "god of magic", "NE", "Knowledge", "staff"),
        ("Morrigan", "goddess of battle", "CE", "War", "two crossed spears"),
        ("Nuada", "god of war and warriors", "N", "War", "silver hand on black background"),
        ("Oghma", "god of speech and writing", "NG", "Knowledge", "unfurled scroll"),
        ("Silvanus", "god of nature and forests", "N", "Nature", "summer oak tree"),
    ]
)

GREEK_DEITIES.extend(
    [
        ("Zeus", "god of the sky, ruler of the gods", "N", "Tempest", "fist full of lightning bolts"),
        ("Aphrodite", "goddess of love and beauty", "CG", "Light", "sea shell"),
        ("Apollo", "god of light, music, and healing", "CG", "Knowledge, Life, Light", "lyre"),
        ("Ares", "god of war and strife", "CE", "War", "spear"),
        ("Artemis", "goddess of hunting and childbirth", "NG", "Life, Nature", "bow and arrow on lunar disk"),
        ("Athena", "goddess of wisdom and civilization", "LG", "Knowledge, War", "owl"),
        ("Demeter", "goddess of agriculture", "NG", "Life", "mare's head"),
        ("Dionysus", "god of mirth and wine", "CN", "Life", "thyrsus (staff tipped with pine cone)"),
        ("Hades", "god of the underworld", "LE", "Death", "black ram"),
        ("Hecate", "goddess of magic and the moon", "CE", "Knowledge, Trickery", "setting moon"),
        ("Hephaestus", "god of smithing and craft", "NG", "Knowledge", "hammer and anvil"),
        ("Hera", "goddess of marriage and intrigue", "CN", "Trickery", "fan of peacock feathers"),
        ("Hercules", "god of strength and adventure", "CG", "Tempest, War", "lion's head"),
        ("Hermes", "god of travel and commerce", "CG", "Trickery", "caduceus (winged staff and serpents)"),
        ("Hestia", "goddess of home and family", "NG", "Life", "hearth"),
        ("Nike", "goddess of victory", "LN", "War", "winged woman"),
        ("Pan", "god of nature", "CN", "Nature", "syrinx (pan pipes)"),
        ("Poseidon", "god of the sea and earthquakes", "CN", "Tempest", "trident"),
        ("Tyche", "goddess of good fortune", "N", "Trickery", "red pentagram"),
    ]
)

EGYPTIAN_DEITIES.extend(
    [
        ("Re-Horakhty", "god of the sun, ruler of the gods", "LG", "Life, Light", "solar disk encircled by serpent"),
        ("Anubis", "god of judgment and death", "LN", "Death", "black jackal"),
        ("Apep", "god of evil, fire, and serpents", "NE", "Trickery", "flaming snake"),
        ("Bast", "goddess of cats and vengeance", "CG", "War", "cat"),
        ("Bes", "god of luck and music", "CN", "Trickery", "image of the misshapen deity"),
        ("Hathor", "goddess of love, music, and motherhood", "NG", "Life, Light", "horned cow's head with lunar disk"),
        ("Imhotep", "god of crafts and medicine", "NG", "Knowledge", "step pyramid"),
        ("Isis", "goddess of fertility and magic", "NG", "Knowledge, Life", "ankh and star"),
        ("Nephthys", "goddess of death and grief", "CG", "Death", "horns around a lunar disk"),
        ("Osiris", "god of nature and the underworld", "LG", "Life, Nature", "crook and flail"),
        ("Ptah", "god of crafts, knowledge, and secrets", "LN", "Knowledge", "bull"),
        ("Set", "god of darkness and desert storms", "CE", "Death, Tempest, Trickery", "coiled cobra"),
        ("Sobek", "god of water and crocodiles", "LE", "Nature, Tempest", "crocodile head with horns and plumes"),
        ("Thoth", "god of knowledge and wisdom", "N", "Knowledge", "ibis"),
    ]
)

NORSE_DEITIES.extend(
    [
        ("Odin", "god of knowledge and war", "NG", "Knowledge, War", "watching blue eye"),
        ("Aegir", "god of the sea and storms", "NE", "Tempest", "rough ocean waves"),
        ("Balder", "god of beauty and poetry", "NG", "Life, Light", "gem-encrusted silver chalice"),
        ("Forseti", "god of justice and law", "N", "Light", "head of a bearded man"),
        ("Frey", "god of fertility and the sun", "NG", "Life, Light", "ice-blue greatsword"),
        ("Freya", "goddess of fertility and love", "NG", "Life", "falcon"),
        ("Frigga", "goddess of birth and fertility", "N", "Life, Light", "cat"),
        ("Heimdall", "god of watchfulness and loyalty", "LG", "Light, War", "curling musical horn"),
        ("Hel", "goddess of the underworld", "NE", "Death", "woman's face, rotting on one side"),
        ("Hermod", "god of luck", "CN", "Trickery", "winged scroll"),
        ("Loki", "god of thieves and trickery", "CE", "Trickery", "flame"),
        ("Njord", "god of sea and wind", "NG", "Nature, Tempest", "gold coin"),
        ("Odur", "god of light and the sun", "CG", "Light", "solar disk"),
        ("Sif", "goddess of war", "CG", "War", "upraised sword"),
        ("Skadi", "god of earth and mountains", "N", "Nature", "mountain peak"),
        ("Surtur", "god of fire giants and war", "LE", "War", "flaming sword"),
        ("Thor", "god of storms and thunder", "CG", "Tempest, War", "hammer"),
        ("Thrym", "god of frost giants and cold", "CE", "War", "white double-bladed axe"),
        ("Tyr", "god of courage and strategy", "LN", "Knowledge, War", "sword"),
        ("Uller", "god of hunting and winter", "CN", "Nature", "longbow"),
    ]
)


APPENDIX_A_ENTRIES.update(
    {
        "Appendix A: Blinded": build_condition_entry(
            "Sight is gone, and the creature fights at a severe perception disadvantage.",
            "Blinded covers creatures that cannot see at all, whether from darkness, injury, magic, or another effect. It is one of the clearest examples of a condition bundling multiple penalties into a single rules label.",
            [
                "The creature cannot see.",
                "Any ability check that depends on sight fails automatically.",
                "Attack rolls against the creature have advantage.",
                "The creature's own attack rolls have disadvantage.",
            ],
        ),
        "Appendix A: Charmed": build_condition_entry(
            "Hostility toward the charmer is locked out while social influence becomes easier.",
            "Charmed does not mean full mind control. It means the target is magically or emotionally constrained in how it can act toward the charmer, and that social leverage shifts sharply in the charmer's favor.",
            [
                "The creature cannot attack the charmer.",
                "The creature cannot target the charmer with harmful abilities or magical effects.",
                "The charmer has advantage on social ability checks made to interact with the creature.",
            ],
        ),
        "Appendix A: Deafened": build_condition_entry(
            "Hearing-based awareness and checks stop working.",
            "Deafened is simple but important whenever a scene depends on spoken warning, approaching danger, or listening for clues.",
            [
                "The creature cannot hear.",
                "Any ability check that depends on hearing fails automatically.",
            ],
        ),
        "Appendix A: Exhaustion": build_condition_entry(
            "Accumulating hardship that worsens in six escalating stages.",
            "Exhaustion is the long-burn survival condition of the Basic Rules. It often comes from hunger, exposure, or punishing special effects, and it stacks rather than replacing itself.",
            [
                "Level 1: disadvantage on ability checks.",
                "Level 2: speed is halved.",
                "Level 3: disadvantage on attack rolls and saving throws.",
                "Level 4: hit point maximum is halved.",
                "Level 5: speed becomes 0.",
                "Level 6: death.",
                "New exhaustion adds to the current level.",
                "A creature suffers the effects of its current level and every lower level.",
                "Removing exhaustion lowers the level by the amount specified by the effect.",
                "A long rest lowers exhaustion by 1 if the creature also had food and drink.",
                "Being raised from the dead also lowers exhaustion by 1.",
            ],
        ),
        "Appendix A: Frightened": build_condition_entry(
            "Fear hampers competence and prevents closing with the source of terror.",
            "Frightened ties narrative fear directly to battlefield behavior. The condition matters most when a creature can still see what it fears.",
            [
                "The creature has disadvantage on ability checks and attack rolls while the source of fear is in line of sight.",
                "The creature cannot willingly move closer to the source of fear.",
            ],
        ),
        "Appendix A: Grappled": build_condition_entry(
            "Movement is pinned until the hold is broken.",
            "Grappled is mainly a movement condition. It stops repositioning and can set up later danger, but it does not automatically stop attacks or spellcasting by itself.",
            [
                "The creature's speed becomes 0.",
                "The creature cannot benefit from bonuses to speed.",
                "The condition ends if the grappler becomes incapacitated.",
                "The condition also ends if the creature is moved out of the grappler's reach by an effect.",
            ],
        ),
        "Appendix A: Incapacitated": build_condition_entry(
            "The core action-lock condition used by several harsher states.",
            "Incapacitated is a short rules tag, but it sits under several nastier conditions such as paralyzed, stunned, and unconscious.",
            [
                "The creature cannot take actions.",
                "The creature cannot take reactions.",
            ],
        ),
        "Appendix A: Invisible": build_condition_entry(
            "The creature cannot be seen normally, but it still leaves clues.",
            "Invisible is not perfect erasure. Other creatures can still infer location from noise, tracks, or magic, but normal sight no longer reveals the target.",
            [
                "The creature is impossible to see without magic or a special sense.",
                "For hiding purposes, the creature counts as heavily obscured.",
                "Its location can still be detected from noise or tracks.",
                "Attack rolls against the creature have disadvantage.",
                "The creature's attack rolls have advantage.",
            ],
        ),
    }
)


APPENDIX_LORE.update(
    {
        "Appendix A: Conditions": {
            "menu": "The rules appendix that defines every standard 2014 Basic Rules condition.",
            "text": build_appendix_contents_text(
                "Appendix A is the condition reference used across the 2014 Basic Rules. Instead of repeating status text in every spell, monster, trap, and hazard, "
                "the rules point back here for the named conditions that change what a creature can do, perceive, or survive.",
                [
                    "Blinded",
                    "Charmed",
                    "Deafened",
                    "Exhaustion",
                    "Frightened",
                    "Grappled",
                    "Incapacitated",
                    "Invisible",
                    "Paralyzed",
                    "Petrified",
                    "Poisoned",
                    "Prone",
                    "Restrained",
                    "Stunned",
                    "Unconscious",
                ],
                footer=(
                    "Open any condition entry in this section to read the rule effects directly as a quick-reference breakdown."
                ),
            ),
        },
    }
)

APPENDIX_LORE.update(
    {
        "Appendix C: The Five Factions": {
            "menu": "The official Realms appendix for the Harpers, Gauntlet, Enclave, Alliance, and Zhentarim.",
            "text": build_appendix_contents_text(
                "Appendix C explains that many Forgotten Realms characters, especially in organized play, belong to one of five major factions. Each faction has its own goals and methods, "
                "but the appendix notes that they can still unite when a threat grows large enough to endanger the Realms as a whole.",
                [
                    "Harpers: secretive idealists who use information, contacts, and quiet intervention to protect the innocent.",
                    "Order of the Gauntlet: disciplined crusaders who seek out evil and destroy it before it spreads.",
                    "Emerald Enclave: scattered wardens of the wild who preserve balance and teach others how to survive it.",
                    "Lords' Alliance: city-backed agents and rulers who defend civilization, stability, and shared security.",
                    "Zhentarim: the Black Network, using ambition, money, leverage, and elite muscle as tools of power.",
                ],
                footer=(
                    "The faction entries that follow work best as a field guide: what each group values, how it acts, and what kind of adventurer fits it."
                ),
            ),
        },
        "Appendix C: Harpers": {
            "menu": "Secretive defenders who use intelligence, mobility, and quiet intervention.",
            "text": (
                "The Harpers are a clandestine network of spies, spellcasters, and idealists who try to tilt the balance toward the innocent, the weak, and the oppressed. They work behind "
                "the scenes whenever possible, preferring quiet disruption of tyrants and rising evil to visible conquest.\n\n"
                "Harper agents often operate alone, leaning on information networks, secret caches, trusted contacts, and false identities. They prize incorruptibility, self-reliance, and "
                "knowledge gathered before a conflict breaks open. In campaign terms, they are the faction of intelligence work, soft power, and principled interference."
            ),
        },
        "Appendix C: Order of the Gauntlet": {
            "menu": "Zealous doers who seek out evil directly and smash it before it grows.",
            "text": (
                "The Order of the Gauntlet is a comparatively young organization devoted to confronting evil head-on. It believes darkness hides, spreads through weakness, and must be met with "
                "vigilance, prayer, discipline, and decisive force.\n\n"
                "Its members ride toward dangerous ruins and foul lairs rather than away from them, but the Order also stresses inward discipline: before cleansing the world, its paladins, clerics, "
                "and monks are expected to confront the capacity for evil within themselves. It is a faction of honor, faith, and righteous action."
            ),
        },
        "Appendix C: Emerald Enclave": {
            "menu": "Wardens of the wild who preserve balance and teach others how to survive it.",
            "text": (
                "The Emerald Enclave is a scattered but far-reaching network that opposes threats to the natural world and helps people endure wilderness on its own terms. Its branches are often isolated, "
                "which breeds self-reliance, fieldcraft, and a practical respect for nature.\n\n"
                "The Enclave does not reject civilization outright. Instead, it tries to stop civilization and wilderness from destroying one another, while resisting what it sees as unnatural corruption. "
                "Rangers, druids, and frontier defenders fit here naturally."
            ),
        },
        "Appendix C: Lords' Alliance": {
            "menu": "A coalition of city rulers and loyal agents defending civilized order.",
            "text": (
                "The Lords' Alliance is an association of rulers from major towns and cities, especially in the North, who believe solidarity is necessary to keep large threats at bay. Its leaders care deeply "
                "about the fortune and safety of their own settlements, which gives the faction both strength and friction.\n\n"
                "Alliance agents tend to be well-equipped professionals backed by wealth, rank, and infrastructure. They fight for security, prosperity, and political stability, often acting before ordinary people "
                "even know a danger exists. It is the faction of order, statecraft, and hard-nosed civic defense."
            ),
        },
        "Appendix C: Zhentarim": {
            "menu": "The Black Network of ambitious operators who treat wealth and influence as weapons.",
            "text": (
                "The Zhentarim are mercenaries, rogues, traders, and warlocks who want influence, leverage, and the ability to shape events instead of obeying them. They are willing to work near or across legal lines "
                "if that is what it takes to get results.\n\n"
                "To the Black Network, wealth is power made visible. Its members provide elite protection, muscle, and logistics, and they understand that gold can command loyalty as surely as ideology can. In a campaign, "
                "the Zhentarim are the faction of ambition, private power, and ruthlessly practical opportunity."
            ),
        },
        "Appendix D: The Planes of Existence": {
            "menu": "The 2014 Basic Rules cosmology appendix for worlds, planes, portals, and demiplanes.",
            "text": build_appendix_contents_text(
                "Appendix D opens by explaining that the cosmos includes the Material Plane, other planes of raw elemental matter and energy, realms of pure thought and ethos, and the homes of angels, fiends, and gods. "
                "It also frames planar travel as the stuff of legendary quests rather than routine movement.",
                [
                    "The Material Plane: the starting point for ordinary mortal life and all fantasy campaign worlds.",
                    "Beyond the Material: the shift from mundane adventuring into mythic, spiritual, and elemental reality.",
                    "Planar Travel: spells and portals that let adventurers cross between planes.",
                    "Transitive Planes: the Astral Plane and Ethereal Plane as routes to elsewhere.",
                    "Inner Planes: Air, Earth, Fire, Water, and the Elemental Chaos.",
                    "Outer Planes: divine and spiritual realms shaped by thought, purpose, and alignment.",
                    "Upper and Lower Planes: the broad divide between good-aligned and evil-aligned outer realms.",
                    "Demiplanes: small pocket realities with their own rules and points of access.",
                ],
                footer=(
                    "The entries below keep those appendix titles and turn them into readable reference pages for the game's lore menu."
                ),
            ),
        },
        "Appendix D: The Material Plane": {
            "menu": "The mortal baseline from which the rest of the multiverse is understood.",
            "text": (
                "The Material Plane is the meeting point where elemental substance and philosophical forces collide into ordinary life, mundane matter, and the playable worlds most campaigns begin in. All fantasy worlds "
                "used by DMs exist here.\n\n"
                "The appendix emphasizes its diversity: desert worlds, island worlds, worlds where magic mingles with advanced technology, worlds abandoned by gods, and worlds where gods still walk openly. Everything else "
                "in the multiverse is defined in relation to this baseline."
            ),
        },
        "Appendix D: Beyond the Material": {
            "menu": "A shift from ordinary worldbuilding into realms of mythic principle.",
            "text": (
                "Beyond the Material Plane lie other planes that are not merely distant worlds, but different qualities of existence. They are shaped by spiritual and elemental principles abstracted away from ordinary reality.\n\n"
                "This is the jump from familiar fantasy geography to full mythic cosmology: raw elemental domains, divine homes, infernal and celestial regions, and stranger states of being that answer to thought, ethos, or pure energy."
            ),
        },
        "Appendix D: Planar Travel": {
            "menu": "How spells and portals move adventurers across the boundaries of reality.",
            "text": (
                "Planar travel is framed as a legendary journey rather than casual transport. Reaching the realms of the dead, bargaining in an efreet's city, or seeking celestial aid is the stuff of major quests and stories.\n\n"
                "The appendix gives two major routes. Spells such as plane shift, gate, etherealness, and astral projection can open direct or indirect access. Portals can also bridge planes, whether they appear as doors, fog passages, "
                "standing stones, towers, ships, whole settlements, or vortices tied to places like volcanoes and ocean depths."
            ),
        },
        "Appendix D: Transitive Planes": {
            "menu": "The Astral and Ethereal ways between worlds and larger realities.",
            "text": (
                "The Ethereal Plane and Astral Plane are called transitive because they mainly function as routes to somewhere else. Characters enter them to pass from one plane to another rather than to settle there permanently.\n\n"
                "The Ethereal is a mist-heavy border overlapping the Material and Inner Planes, with a deeper region of swirling fog beyond. The Astral is a vast silvery expanse of thought and dream where travelers move like disembodied souls toward divine and demonic realms."
            ),
        },
        "Appendix D: Inner Planes": {
            "menu": "The elemental engines from which worlds are built.",
            "text": (
                "The Inner Planes surround and enfold the Material Plane, providing the raw elemental substance of creation. Air, Earth, Fire, and Water form the main elemental ring around the Material world, all suspended in the Elemental Chaos.\n\n"
                "Near the Material Plane, these realms resemble recognizable land, sea, and sky. Farther out, they become pure and hostile element: endless stone, blazing fire, clear water, or unsullied air. At the far reaches, the elements break down into the violent churn of the Elemental Chaos."
            ),
        },
        "Appendix D: Outer Planes": {
            "menu": "Planes of spirit, purpose, gods, and moral direction rather than matter.",
            "text": (
                "If the Inner Planes are the material of the multiverse, the Outer Planes are its purpose and alignment. Sages often describe them as divine or spiritual planes because they are most famously the homes of deities.\n\n"
                "The appendix warns that Outer Planes should be understood metaphorically as much as geographically. Their apparent landscapes can shift according to the will of greater powers, and distance may mean almost nothing there. The best-known grouping is a set of sixteen planes corresponding to the non-neutral alignments and the spaces between them."
            ),
        },
        "Appendix D: Upper and Lower Planes": {
            "menu": "The broad moral split between celestial and fiendish outer realms.",
            "text": (
                "The Upper Planes are those that contain some measure of good, and they are home to celestials such as angels and pegasi. The Lower Planes contain some measure of evil, and fiends such as demons and devils dwell there.\n\n"
                "A plane's alignment is not just flavor. The appendix says it is the plane's essence, and creatures whose alignment clashes with that essence feel profound dissonance there. A good visitor to Elysium may feel at home, while an evil one feels fundamentally out of tune."
            ),
        },
        "Appendix D: Demiplanes": {
            "menu": "Small pocket realities with their own rules, origins, and points of entry.",
            "text": (
                "Demiplanes are tiny extradimensional realities that do not fit cleanly anywhere else in the multiverse. Some are built by spells such as demiplane, some are made by deities or other great powers, and some arise naturally as folds or splinters of reality.\n\n"
                "They may be reached through a single touchpoint with another plane, and while plane shift can theoretically reach them, the required tuning fork is difficult to obtain. Gate is more dependable if the caster already knows the demiplane exists."
            ),
        },
    }
)

APPENDIX_LORE.update(APPENDIX_A_ENTRIES)

APPENDIX_LORE.update(
    {
        "Appendix B: Gods of the Multiverse": {
            "menu": "The official deity appendix covering worship, pantheons, domains, and symbols.",
            "text": build_appendix_contents_text(
                "Appendix B explains that religion is a visible, practical force in D&D worlds: clerics channel divine power, paladins embody sacred ideals, cults serve darker patrons, "
                "and ordinary people may honor different gods in different moments of life. It also notes that a character can dedicate themselves to one deity or simply invoke the gods "
                "most relevant to their culture, background, or class.",
                [
                    "D&D Pantheons: each campaign world has its own divine roster, with this appendix focusing first on the Forgotten Realms.",
                    "The Forgotten Realms: the main Faerunian pantheon used as the appendix's primary reference.",
                    "Nonhuman Deities: gods shared across peoples such as dwarves and other nonhuman cultures.",
                    "Fantasy-Historical Pantheons: Celtic, Greek, Egyptian, and Norse divine rosters adapted for D&D play.",
                    "Deities of the Forgotten Realms: names, alignments, suggested domains, and symbols.",
                    "Celtic Deities, Greek Deities, Egyptian Deities, Norse Deities: roster tables for those campaign flavors.",
                ],
                footer=(
                    "The roster entries in this section keep the appendix's game-facing details such as alignment, suggested cleric domains, and holy symbols."
                ),
            ),
        },
        "Appendix B: Forgotten Realms Deities": {
            "menu": "The main Faerunian roster of widely known gods, domains, and holy symbols.",
            "text": build_deity_roster_text(
                "The Forgotten Realms section names the deities most commonly recognized across Faerun. People often honor several of them situationally, while priests, "
                "champions, and devoted servants may commit themselves to one above all others.",
                FORGOTTEN_REALMS_DEITIES,
            ),
        },
        "Appendix B: Nonhuman Deities": {
            "menu": "Shared racial gods and the wider pantheons surrounding nonhuman cultures.",
            "text": (
                "The appendix notes that some gods closely tied to nonhuman peoples are honored across multiple settings, including the Forgotten Realms and Greyhawk. "
                "It also points out that many nonhuman races have full pantheons of their own rather than a single patron.\n\n"
                "The dwarf example is the clearest: beyond Moradin, the source names Berronar Truesilver, Abbathor, Clangeddin Silverbeard, Dugmaren Brightmantle, "
                "Dumathoin, Gorm Gulthyn, Haela Brightaxe, Marthammor Duin, Sharindlar, Thard Harr, and Vergadain. Different clans and kingdoms may revere some, all, "
                "or none of these deities, and some may know the same powers by different names."
            ),
        },
        "Appendix B: Fantasy-Historical Pantheons": {
            "menu": "Celtic, Greek, Egyptian, and Norse pantheons adapted into D&D campaign use.",
            "text": build_appendix_contents_text(
                "The appendix presents Celtic, Egyptian, Greek, and Norse pantheons as fantasy interpretations suited to D&D play rather than strict historical reconstructions. "
                "These rosters are included so a campaign can lean into a mythic flavor while still using the same cleric-domain and symbol structure as the rest of the rules.",
                [
                    "Celtic Deities: wild, landscape-bound gods tied to brook, oak, mistletoe, and moor.",
                    "Greek Deities: Olympian figures of storm, war, wisdom, beauty, home, sea, and fate.",
                    "Egyptian Deities: a divine family shaped by rulership, order, craft, fertility, death, and judgment.",
                    "Norse Deities: hard-country gods of thunder, winter, luck, war, fertility, and survival.",
                ],
            ),
        },
        "Appendix B: Celtic Pantheon": {
            "menu": "Wild, nature-suffused gods tied to streams, woods, moors, and druidic reverence.",
            "text": build_deity_roster_text(
                "The Celtic pantheon is presented as primal and landscape-bound. Its gods feel tied to brook, oak, mistletoe, and moor, and the appendix explicitly notes "
                "that they are often served by druids as well as clerics.",
                CELTIC_DEITIES,
            ),
        },
        "Appendix B: Greek Pantheon": {
            "menu": "Olympian deities of sea, storm, city, beauty, war, fate, and hearth.",
            "text": build_deity_roster_text(
                "The Greek pantheon centers the gods of Olympus, whose presence echoes through sea, thunder, wooded hills, and the human heart. In game terms it offers a broad "
                "spread of domains for civilized, heroic, and mythic campaigns.",
                GREEK_DEITIES,
            ),
        },
        "Appendix B: Egyptian Pantheon": {
            "menu": "A divine dynasty shaped by order, rulership, judgment, craft, fertility, and death.",
            "text": build_deity_roster_text(
                "The Egyptian pantheon is framed around an ancient divine family that maintains Ma'at: truth, justice, law, and right order. The appendix specifically calls out "
                "that Anubis, Set, and Nephthys all touch the Death domain from different moral positions.",
                EGYPTIAN_DEITIES,
            ),
        },
        "Appendix B: Norse Pantheon": {
            "menu": "Hard-country gods of storm, war, winter, luck, fertility, and fate.",
            "text": build_deity_roster_text(
                "The Norse pantheon is rooted in fjords, glaciers, longships, and severe survival. The appendix describes the Aesir and Vanir as allied divine families whose domains "
                "reflect leadership, battle, fertility, prosperity, and the brutal logic of northern life.",
                NORSE_DEITIES,
            ),
        },
    }
)

APPENDIX_A_ENTRIES.update(
    {
        "Appendix A: Paralyzed": build_condition_entry(
            "Body locked in place, leaving the victim helpless in melee.",
            "Paralyzed is one of the most dangerous combat conditions because it removes action, movement, and defense at once, then turns nearby hits into critical strikes.",
            [
                "The creature is incapacitated.",
                "The creature cannot move or speak.",
                "The creature automatically fails Strength and Dexterity saving throws.",
                "Attack rolls against the creature have advantage.",
                "A hit from within 5 feet is a critical hit.",
            ],
        ),
        "Appendix A: Petrified": build_condition_entry(
            "Turned into inert matter and nearly frozen out of normal life.",
            "Petrified transforms a creature and what it is carrying into lifeless substance, usually stone. It is one of the heaviest status effects in the appendix because it changes physical state as well as combat capability.",
            [
                "The creature and its nonmagical worn or carried objects become a solid inanimate substance, usually stone.",
                "Its weight increases tenfold and aging stops.",
                "The creature is incapacitated, cannot move or speak, and is unaware of its surroundings.",
                "Attack rolls against the creature have advantage.",
                "The creature automatically fails Strength and Dexterity saving throws.",
                "The creature has resistance to all damage.",
                "The creature is immune to poison and disease, though existing poison or disease is suspended rather than cured.",
            ],
        ),
        "Appendix A: Poisoned": build_condition_entry(
            "Sickness and impairment drag down offense and general capability.",
            "Poisoned is a broad penalty condition that weakens both combat performance and noncombat competence.",
            [
                "The creature has disadvantage on attack rolls.",
                "The creature has disadvantage on ability checks.",
            ],
        ),
        "Appendix A: Prone": build_condition_entry(
            "Knocked down, better against distant fire and worse against nearby threats.",
            "Prone is one of the most positional conditions in the Basic Rules. It changes movement and flips the math on incoming attacks depending on distance.",
            [
                "The creature can only crawl unless it stands up to end the condition.",
                "The creature has disadvantage on attack rolls.",
                "Attack rolls from within 5 feet have advantage.",
                "Attack rolls from farther away have disadvantage.",
            ],
        ),
        "Appendix A: Restrained": build_condition_entry(
            "Held fast, exposing the creature to attacks and failed dodges.",
            "Restrained is harsher than grappled because it not only stops movement but also makes the victim easier to hit and worse at avoiding effects.",
            [
                "The creature's speed becomes 0.",
                "The creature cannot benefit from bonuses to speed.",
                "Attack rolls against the creature have advantage.",
                "The creature's attack rolls have disadvantage.",
                "The creature has disadvantage on Dexterity saving throws.",
            ],
        ),
        "Appendix A: Stunned": build_condition_entry(
            "Awareness is broken and the body barely responds.",
            "Stunned resembles paralyzed in danger level, but the text frames it as a shattered nervous system or mind rather than rigid immobility.",
            [
                "The creature is incapacitated.",
                "The creature cannot move.",
                "The creature can speak only falteringly.",
                "The creature automatically fails Strength and Dexterity saving throws.",
                "Attack rolls against the creature have advantage.",
            ],
        ),
        "Appendix A: Unconscious": build_condition_entry(
            "Fully senseless, dropped to the ground, and easy prey in close combat.",
            "Unconscious wraps together several other effects and represents complete lack of awareness, whether from sleep, trauma, or magic.",
            [
                "The creature is incapacitated.",
                "The creature cannot move or speak.",
                "The creature is unaware of its surroundings.",
                "The creature drops whatever it is holding.",
                "The creature falls prone.",
                "The creature automatically fails Strength and Dexterity saving throws.",
                "Attack rolls against the creature have advantage.",
                "A hit from within 5 feet is a critical hit.",
            ],
        ),
    }
)


APPENDIX_LORE = {
    "Appendix A: Conditions": APPENDIX_LORE["Appendix A: Conditions"],
    **APPENDIX_A_ENTRIES,
    "Appendix B: Gods of the Multiverse": APPENDIX_LORE["Appendix B: Gods of the Multiverse"],
    "Appendix B: Forgotten Realms Deities": APPENDIX_LORE["Appendix B: Forgotten Realms Deities"],
    "Appendix B: Nonhuman Deities": APPENDIX_LORE["Appendix B: Nonhuman Deities"],
    "Appendix B: Fantasy-Historical Pantheons": APPENDIX_LORE["Appendix B: Fantasy-Historical Pantheons"],
    "Appendix B: Celtic Pantheon": APPENDIX_LORE["Appendix B: Celtic Pantheon"],
    "Appendix B: Greek Pantheon": APPENDIX_LORE["Appendix B: Greek Pantheon"],
    "Appendix B: Egyptian Pantheon": APPENDIX_LORE["Appendix B: Egyptian Pantheon"],
    "Appendix B: Norse Pantheon": APPENDIX_LORE["Appendix B: Norse Pantheon"],
    "Appendix C: The Five Factions": APPENDIX_LORE["Appendix C: The Five Factions"],
    "Appendix C: Harpers": APPENDIX_LORE["Appendix C: Harpers"],
    "Appendix C: Order of the Gauntlet": APPENDIX_LORE["Appendix C: Order of the Gauntlet"],
    "Appendix C: Emerald Enclave": APPENDIX_LORE["Appendix C: Emerald Enclave"],
    "Appendix C: Lords' Alliance": APPENDIX_LORE["Appendix C: Lords' Alliance"],
    "Appendix C: Zhentarim": APPENDIX_LORE["Appendix C: Zhentarim"],
    "Appendix D: The Planes of Existence": APPENDIX_LORE["Appendix D: The Planes of Existence"],
    "Appendix D: The Material Plane": APPENDIX_LORE["Appendix D: The Material Plane"],
    "Appendix D: Beyond the Material": APPENDIX_LORE["Appendix D: Beyond the Material"],
    "Appendix D: Planar Travel": APPENDIX_LORE["Appendix D: Planar Travel"],
    "Appendix D: Transitive Planes": APPENDIX_LORE["Appendix D: Transitive Planes"],
    "Appendix D: Inner Planes": APPENDIX_LORE["Appendix D: Inner Planes"],
    "Appendix D: Outer Planes": APPENDIX_LORE["Appendix D: Outer Planes"],
    "Appendix D: Upper and Lower Planes": APPENDIX_LORE["Appendix D: Upper and Lower Planes"],
    "Appendix D: Demiplanes": APPENDIX_LORE["Appendix D: Demiplanes"],
}


PLANNED_ACTS_LORE = {
    "Act Roadmap": {
        "menu": "How the current campaign arc is structured inside the game.",
        "text": (
            "Act I, Ashes on the Triboar Trail, is the currently playable chapter and focuses on caravans, frontier pressure, and the Ashen Brand threat around Neverwinter and Phandalin.\n\n"
            "Act II, Echoes Beneath the Sword Mountains, is framed as a deeper descent into buried danger and older stone. Act III, The Jewel and the Chasm, points back toward Neverwinter itself and the larger consequences of power, rebuilding, and urban unrest. Together the roadmap keeps the campaign anchored in official Sword Coast geography while giving the game room to escalate from local road trouble to regional stakes."
        ),
    }
}


TITLE_LORE_SECTIONS: tuple[tuple[str, LoreSection], ...] = (
    ("World & Locations", LOCATION_LORE),
    ("Classes", CLASS_LORE),
    ("Races", RACE_LORE),
    ("Backgrounds", BACKGROUND_LORE),
    ("Core Abilities", ABILITY_LORE),
    ("Skills", SKILL_LORE),
    ("Features & Abilities", FEATURE_LORE),
    ("Appendices", APPENDIX_LORE),
    ("Campaign Roadmap", PLANNED_ACTS_LORE),
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
    "Barbarian": ["STR", "CON"],
    "Bard": ["CHA", "DEX"],
    "Cleric": ["WIS", "CON"],
    "Druid": ["WIS", "CON"],
    "Fighter": ["STR", "CON"],
    "Monk": ["DEX", "WIS"],
    "Paladin": ["STR", "CHA"],
    "Ranger": ["DEX", "WIS"],
    "Rogue": ["DEX", "WIS"],
    "Sorcerer": ["CHA", "CON"],
    "Warlock": ["CHA", "CON"],
    "Wizard": ["INT", "DEX"],
}


ABILITY_GAMEPLAY_NOTES = {
    "STR": "Used for melee force, Athletics, carrying capacity, and physical contests.",
    "DEX": "Used for initiative, stealth, finesse or ranged accuracy, and many reflex-based saves.",
    "CON": "Adds to hit points and helps endure poison, fatigue, and punishment.",
    "INT": "Used for learned knowledge, investigation, and wizard spellcasting.",
    "WIS": "Used for awareness, intuition, survival, medicine, and cleric or druid spellcasting.",
    "CHA": "Used for social pressure, presence, deception, and bard, sorcerer, paladin, or warlock spellcasting.",
}


def ability_label(code: str) -> str:
    return ABILITY_LABELS.get(code, code)


def format_bonus_list(bonuses: Mapping[str, int]) -> str:
    return ", ".join(f"{ability_label(ability)} +{value}" for ability, value in bonuses.items())


def format_feature_label(feature_id: str) -> str:
    label = feature_id.replace("_barbarian", "").replace("_monk", "")
    return label.replace("_", " ").title()


def format_feature_entry(feature_id: str, index: int) -> str:
    description = FEATURE_LORE.get(feature_id, {}).get("text", "No description recorded yet.")
    return f"{index}. {format_feature_label(feature_id)}: {description}"


def format_weapon_summary(class_name: str) -> str:
    weapon = CLASSES[class_name]["weapon"]
    attack_stat = weapon.ability
    if attack_stat == "FINESSE":
        attack_stat = "Strength or Dexterity"
    elif attack_stat == "SPELL":
        attack_stat = "Spellcasting ability"
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
    armor_bits = [f"{armor.name} (base AC {armor.base_ac})", shield]
    if armor.heavy:
        armor_bits.append("heavy armor")
    elif armor.dex_cap is None:
        armor_bits.append("full Dexterity modifier applies")
    else:
        armor_bits.append(f"Dexterity bonus capped at +{armor.dex_cap}")
    return ". ".join([armor_bits[0], ", ".join(armor_bits[1:])]) + "."


def format_resource_summary(resources: Mapping[str, int]) -> str:
    if not resources:
        return "No tracked class resources at level 1."
    return ", ".join(f"{name.replace('_', ' ')} {amount}" for name, amount in resources.items())


def format_class_manual(class_name: str) -> str:
    details = CLASSES[class_name]
    lines = [
        "Gameplay Manual",
        f"Main stats: {', '.join(ability_label(stat) for stat in CLASS_PRIMARY_STATS.get(class_name, [])) or 'Flexible'}",
        f"Hit die: d{details['hit_die']}",
        f"Saving throw proficiencies: {', '.join(ability_label(save) for save in details['saving_throws'])}",
        f"Skill picks: choose {details['skill_picks']} from {', '.join(details['skill_choices'])}",
        f"Starting weapon: {format_weapon_summary(class_name)}",
        f"Armor profile: {format_armor_summary(class_name)}",
        (
            f"Spellcasting: uses {ability_label(details['spellcasting_ability'])}; "
            f"starting resources {format_resource_summary(details['resources'])}."
            if details["spellcasting_ability"]
            else f"Spellcasting: none at level 1. Starting resources: {format_resource_summary(details['resources'])}."
        ),
        "Starting abilities:",
    ]
    lines.extend(format_feature_entry(feature_id, index) for index, feature_id in enumerate(details["features"], start=1))
    progression = CLASS_LEVEL_PROGRESSION.get(class_name, {})
    if progression:
        lines.append("Early progression in this game:")
        for level in sorted(progression):
            features = progression[level]["features"]
            feature_text = "; ".join(f"{name}: {description}" for name, description in features)
            lines.append(f"- Level {level}: {feature_text}")
    return "\n".join(lines)


def format_race_manual(race_name: str) -> str:
    details = RACES[race_name]
    lines = [
        "Gameplay Manual",
        f"Ability bonuses: {format_bonus_list(details['bonuses'])}",
        f"Automatic racial skills: {', '.join(details['skills']) if details['skills'] else 'None'}",
        "Racial traits:",
    ]
    if details["features"]:
        lines.extend(format_feature_entry(feature_id, index) for index, feature_id in enumerate(details["features"], start=1))
    else:
        lines.append("1. No extra racial traits beyond the listed ability increases.")
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
        class_name
        for class_name, stats in CLASS_PRIMARY_STATS.items()
        if ability_code in stats
    )
    return "\n".join(
        [
            "Gameplay Manual",
            f"Full name: {ability_label(ability_code)}",
            f"Linked skills: {', '.join(linked_skills) if linked_skills else 'None'}",
            f"Common main stat for: {', '.join(matching_classes) if matching_classes else 'No class listed as primary'}",
            f"Gameplay role: {ABILITY_GAMEPLAY_NOTES.get(ability_code, 'No note recorded yet.')}",
        ]
    )


def format_skill_manual(skill_name: str) -> str:
    linked_ability = SKILL_TO_ABILITY[skill_name]
    class_sources = sorted(class_name for class_name, details in CLASSES.items() if skill_name in details["skill_choices"])
    race_sources = sorted(race_name for race_name, details in RACES.items() if skill_name in details["skills"])
    background_sources = sorted(name for name, details in BACKGROUNDS.items() if skill_name in details["skills"])
    return "\n".join(
        [
            "Gameplay Manual",
            f"Governing ability: {ability_label(linked_ability)}",
            f"Class access: {', '.join(class_sources) if class_sources else 'No class grants selection access'}",
            f"Automatic race access: {', '.join(race_sources) if race_sources else 'None'}",
            f"Automatic background access: {', '.join(background_sources) if background_sources else 'None'}",
            f"Gameplay role: {SKILL_LORE[skill_name]['text']}",
        ]
    )


def format_feature_manual(feature_name: str) -> str:
    class_sources = sorted(class_name for class_name, details in CLASSES.items() if feature_name in details["features"])
    race_sources = sorted(race_name for race_name, details in RACES.items() if feature_name in details["features"])
    return "\n".join(
        [
            "Gameplay Manual",
            f"Used by classes: {', '.join(class_sources) if class_sources else 'None at level 1'}",
            f"Used by races: {', '.join(race_sources) if race_sources else 'None'}",
            f"Gameplay role: {FEATURE_LORE[feature_name]['text']}",
        ]
    )


def manual_text_for_entry(section_title: str, entry_name: str) -> str:
    if section_title == "Classes" and entry_name in CLASSES:
        return format_class_manual(entry_name)
    if section_title == "Races" and entry_name in RACES:
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
