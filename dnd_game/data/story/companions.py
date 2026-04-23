from __future__ import annotations

from ...models import Character


PARTY_LIMIT = 4
ACTIVE_COMPANION_LIMIT = PARTY_LIMIT - 1

COMPANION_PROFILES: dict[str, dict[str, object]] = {
    "tolan_ironshield": {
        "name": "Tolan Ironshield",
        "summary": "A dwarven shield veteran who measures people by whether they hold the line when it matters.",
        "lore": [
            "Tolan served on Emberway caravans out of Greywake for two decades, long enough to see three trade leagues fail and two rise in their place.",
            "He still carries a notched tower-shield rivet from the ambush that killed his older brother near the drowned flats west of Blackwake.",
            "He trusts steady action more than speeches, but remembers every promise anyone makes in his hearing.",
        ],
        "camp_topics": [
            {
                "id": "old_road",
                "prompt": "\"Tell me about the worst road you ever guarded.\"",
                "response": "Sleet, broken axles, and knee-deep mud. We stood there till dawn so frightened merchants could live long enough to complain about the weather.",
                "delta": 1,
            },
            {
                "id": "clan",
                "prompt": "\"What does your clan expect of you now?\"",
                "response": "That I keep going, I suppose. Stopping would mean looking too directly at who never came home with me.",
                "delta": 1,
            },
            {
                "id": "doubt",
                "prompt": "\"You sound like a relic from an older war.\"",
                "response": "Old habits are the reason more people are alive than dead.",
                "delta": -2,
            },
            {
                "id": "blackwake_ledgers_people",
                "prompt": "\"Would you have saved the ledgers or the people?\"",
                "response": "People. Then ledgers if the gods give you time. Proof can shame a city, but a breathing witness can still choose tomorrow.",
                "delta": 1,
                "requires_flags": ["blackwake_completed"],
            },
        ],
        "great_dialogue": "I'd trust your call in a blind pass.",
        "exceptional_dialogue": "Shield-kin. That's what you are to me now. This campfire feels more like home than any barracks has in years.",
        "great_bonuses": {"AC": 1},
        "exceptional_bonuses": {"CON_save": 1},
        "scene_support": {
            "ashfall_watch": {
                "text": "Tolan quietly maps the tower angles for you and helps the party tighten their approach.",
                "hero_bonus": 1,
                "ally_statuses": {"blessed": 1},
            },
            "blackwake_crossing": {
                "text": "Tolan plants himself where panicked survivors can see a shield, and the company moves with steadier purpose.",
                "hero_bonus": 1,
                "ally_statuses": {"blessed": 1},
            },
        },
    },
    "bryn_underbough": {
        "name": "Bryn Underbough",
        "summary": "A halfling scout who hides anxiety behind wit, speed, and relentless observation.",
        "lore": [
            "Bryn grew up between caravans, shrines, and borrowed rooms, learning early that knowing an exit mattered as much as knowing a friend.",
            "She ran messages for smugglers in her teens before deciding she preferred honest pay and fewer knives at her back.",
            "Her humor gets sharper whenever she is frightened enough to think someone might notice.",
        ],
        "camp_topics": [
            {
                "id": "smugglers",
                "prompt": "\"What finally made you leave the smuggling routes?\"",
                "response": "Watching good people pay for bad leaders who always slipped away first. That gets old faster than coin does.",
                "delta": 1,
            },
            {
                "id": "fear",
                "prompt": "\"What still scares you on the road?\"",
                "response": "People who stop talking before violence. By then they've already decided who matters.",
                "delta": 1,
            },
            {
                "id": "mock",
                "prompt": "\"You worry too much.\"",
                "response": "Surviving usually starts with worrying before anyone else does.",
                "delta": -2,
            },
            {
                "id": "blackwake_neverwinter_cares",
                "prompt": "\"Do you think Greywake's offices even care?\"",
                "response": "Greywake cares when caring has handles: names, seals, routes, someone to blame. Blackwake gave us handles. Now we see who grabs them.",
                "delta": 1,
                "requires_flags": ["blackwake_completed"],
            },
        ],
        "great_dialogue": "I start noticing more when you're around, mostly because I know you'll actually listen.",
        "exceptional_dialogue": "I don't plan my exit route first anymore when you walk into a room. That's new.",
        "great_bonuses": {"Stealth": 1, "initiative": 1},
        "exceptional_bonuses": {"Perception": 1},
        "scene_support": {
            "old_owl_well": {
                "text": "Bryn quietly points out the blind angles in the dig ring and the one trench line nobody is properly watching.",
                "hero_bonus": 1,
                "ally_statuses": {"invisible": 1},
            },
            "emberhall_cellars": {
                "text": "Bryn spots the safest shadow-line through the cellar and hands the party a cleaner opening.",
                "hero_bonus": 1,
                "ally_statuses": {"invisible": 1},
            },
            "blackwake_crossing": {
                "text": "Bryn reads the false roadwarden marks quickly enough to turn one bad paper trail into an opening.",
                "hero_bonus": 1,
                "ally_statuses": {"emboldened": 1},
            },
        },
    },
    "elira_dawnmantle": {
        "name": "Elira Dawnmantle",
        "summary": "A priestess of the Lantern whose compassion is sharpened, not softened, by the frontier's cruelty.",
        "lore": [
            "Elira learned battlefield triage from roadside shrines that treated lumber crews, miners, and pilgrims with equal urgency.",
            "She believes luck is not random mercy but a chance people build for one another with courage and timing.",
            "Under stress she gets quieter, not colder, as though she is measuring every word for whether it heals or harms.",
        ],
        "camp_topics": [
            {
                "id": "faith",
                "prompt": "\"What does faith mean when the road keeps taking good people?\"",
                "response": "Faith is choosing to keep showing up with clean hands and a steady voice even after grief teaches you not to.",
                "delta": 1,
            },
            {
                "id": "luck",
                "prompt": "\"Why does the Lantern still matter on the frontier?\"",
                "response": "Because a kept light matters most where survival depends on one brave person acting at exactly the right second.",
                "delta": 1,
            },
            {
                "id": "cruelty",
                "prompt": "\"Prayer won't save anyone who can't swing a blade.\"",
                "response": "Prayer alone won't, but contempt has never saved anyone either.",
                "delta": -2,
            },
            {
                "id": "blackwake_aftermath",
                "prompt": "\"What should I carry from Blackwake?\"",
                "response": "Carry the faces, not only the proof. Records can make officials move, but people are why movement matters.",
                "delta": 1,
                "requires_flags": ["blackwake_completed"],
            },
        ],
        "great_dialogue": "There are doubts I only trust you to hear.",
        "exceptional_dialogue": "I pray for your future by name now, not because I fear losing you, but because I believe in what you'll become.",
        "great_bonuses": {"healing": 1},
        "exceptional_bonuses": {"WIS_save": 1},
        "scene_support": {
            "camp_rest": {
                "text": "Elira blesses the camp before sleep, and everyone wakes steadier than expected.",
                "hero_bonus": 0,
                "ally_statuses": {"blessed": 2},
            },
            "blackwake_crossing": {
                "text": "Elira triages the burned and frightened with calm hands, buying the party cleaner testimony and a little mercy.",
                "hero_bonus": 1,
                "ally_statuses": {"blessed": 1},
            },
        },
    },
    "kaelis_starling": {
        "name": "Kaelis Starling",
        "summary": "A sharp-eyed ranger scout who learned to trust patterns before promises.",
        "lore": [
            "Kaelis spent years guiding outriders and woodsfolk through the northern edges of Greywake Wood, where bad judgment kills faster than steel does.",
            "He keeps private sketches of trails, ridges, and blind corners because memory alone has betrayed him once already.",
            "He rarely speaks first in a room, but once he commits to someone he watches over them with relentless attention.",
        ],
        "camp_topics": [
            {
                "id": "forest",
                "prompt": "\"What did Greywake Wood teach you first?\"",
                "response": "That every quiet place is full of messages if you slow down enough to read them.",
                "delta": 1,
            },
            {
                "id": "failure",
                "prompt": "\"What's the mistake you still think about?\"",
                "response": "I trusted a map over my gut once and buried friends because of it. I haven't forgiven the delay.",
                "delta": 1,
            },
            {
                "id": "press",
                "prompt": "\"You hide too much to be trusted.\"",
                "response": "Caution kept me alive long before trust became an option.",
                "delta": -2,
            },
            {
                "id": "blackwake_crossing",
                "prompt": "\"What happened at the crossing?\"",
                "response": "A clean road was taught to look dangerous, then dangerous people used the fear as cover. That is not banditry. That is logistics with a knife.",
                "delta": 1,
                "requires_flags": ["blackwake_completed"],
            },
        ],
        "great_dialogue": "You get the unspoken version of my scouting reports now. I don't hand that to many people.",
        "exceptional_dialogue": "I'd follow your trail by instinct even without prints to guide me.",
        "great_bonuses": {"Perception": 1, "initiative": 1},
        "exceptional_bonuses": {"attack": 1},
        "scene_support": {
            "wyvern_tor": {
                "text": "Kaelis reads the shelf wind and the worg tracks in one glance, giving you the cleaner first angle.",
                "hero_bonus": 1,
                "ally_statuses": {"emboldened": 1},
            },
            "road_ambush": {
                "text": "Kaelis reads the brush like a page and murmurs the exact second to strike.",
                "hero_bonus": 1,
                "ally_statuses": {"invisible": 1},
            },
            "blackwake_crossing": {
                "text": "Kaelis follows the ash-scored tracks and keeps the pursuit from stumbling into the obvious alarm lines.",
                "hero_bonus": 1,
                "ally_statuses": {"invisible": 1},
            },
        },
    },
    "rhogar_valeguard": {
        "name": "Rhogar Valeguard",
        "summary": "A Forged oathsworn who treats duty like a living thing that must be fed by action.",
        "lore": [
            "Rhogar was raised among caravan wardens who believed a sworn road was as sacred as any temple threshold.",
            "He carries every oath like a visible weight and grows restless whenever words are left unfinished.",
            "His confidence comes easily, but his forgiveness does not; once broken, his trust has to be rebuilt with deeds.",
        ],
        "camp_topics": [
            {
                "id": "oath",
                "prompt": "\"What oath still drives you?\"",
                "response": "To become the kind of guardian people run toward instead of away from when the road turns dark.",
                "delta": 1,
            },
            {
                "id": "honor",
                "prompt": "\"Has honor ever cost you too much?\"",
                "response": "Of course it has. Some losses are still cheaper than becoming the sort of person who counts every kindness as waste.",
                "delta": 1,
            },
            {
                "id": "taunt",
                "prompt": "\"You're naive for still believing in honor.\"",
                "response": "Belief is only naive when nobody is brave enough to defend it.",
                "delta": -2,
            },
            {
                "id": "blackwake_ledgers_people",
                "prompt": "\"Would you have saved the ledgers or the people?\"",
                "response": "A ledger cannot look you in the eye and ask whether your oath meant anything. Save the living first. Then make the guilty fear what testimony can do.",
                "delta": 1,
                "requires_flags": ["blackwake_completed"],
            },
        ],
        "great_dialogue": "Your plans feel less like arrangements now and more like shared vows.",
        "exceptional_dialogue": "Your banner would be one I could swear to without hesitation.",
        "great_bonuses": {"damage": 1},
        "exceptional_bonuses": {"AC": 1},
        "scene_support": {
            "ashfall_watch": {
                "text": "Rhogar's certainty steadies the campfire briefing and turns hesitation into resolve.",
                "hero_bonus": 1,
                "ally_statuses": {"blessed": 1},
            },
            "blackwake_crossing": {
                "text": "Rhogar's open challenge draws frightened eyes away from the wounded long enough for the company to act.",
                "hero_bonus": 1,
                "ally_statuses": {"emboldened": 1},
            },
        },
    },
    "nim_ardentglass": {
        "name": "Nim Ardentglass",
        "summary": "An Unrecorded ruin scholar who treats maps, mechanisms, and old promises like equally fragile machines.",
        "lore": [
            "Nim apprenticed under three different surveyors because no single mentor could answer every question the old Meridian routes raised.",
            "He masks nerves with precision, talking fastest when he is frightened enough to think everyone else has already noticed.",
            "Part of him still believes lost knowledge should be shared; another part has seen too many smart people killed for opening the wrong door first.",
        ],
        "camp_topics": [
            {
                "id": "maps",
                "prompt": "\"Why do old maps matter this much to you?\"",
                "response": "Because a bad map kills honest people and a good one lets them stop guessing where the dark begins.",
                "delta": 1,
            },
            {
                "id": "mentor",
                "prompt": "\"Who taught you to read ruins this way?\"",
                "response": "A stubborn old delver who said every collapsed hall is still trying to explain itself if you stop panicking long enough to listen.",
                "delta": 1,
            },
            {
                "id": "dismissive",
                "prompt": "\"All this theorizing sounds like fear wearing spectacles.\"",
                "response": "And swagger sounds like a cave-in waiting for a witness.",
                "delta": -2,
            },
        ],
        "great_dialogue": "You make dangerous planning feel almost respectable.",
        "exceptional_dialogue": "I trust you with unfinished notes now. That is either friendship or professional recklessness, and I think I'm all right with either.",
        "great_bonuses": {"Arcana": 1, "Investigation": 1},
        "exceptional_bonuses": {"spell_attack": 1},
        "scene_support": {
            "stonehollow_dig": {
                "text": "Nim sketches a cleaner route through the dig and quietly points out which noises mean 'duck now.'",
                "hero_bonus": 1,
                "ally_statuses": {"blessed": 1},
            },
            "wave_echo_outer_galleries": {
                "text": "Nim calls the old survey marks before the echoes turn them misleading, and the enemy line loses a heartbeat.",
                "hero_bonus": 1,
                "ally_statuses": {},
            },
        },
    },
    "irielle_ashwake": {
        "name": "Irielle Ashwake",
        "summary": "A Fire-Blooded escapee from the Quiet Choir who knows just enough about the whispers beneath the Vaults to fear them properly.",
        "lore": [
            "Irielle was drawn into the Quiet Choir by people who promised revelation and delivered obedience, secrecy, and the slow theft of self.",
            "She has learned to treat certainty with suspicion, especially when it arrives in a voice no one else can hear.",
            "Even at rest she listens for patterns in sound and silence alike, as though one wrong rhythm might open the door again.",
        ],
        "camp_topics": [
            {
                "id": "choir",
                "prompt": "\"What did the Quiet Choir promise you first?\"",
                "response": "Meaning. Then belonging. Then the kind of answers that stop sounding like your own thoughts halfway through.",
                "delta": 1,
            },
            {
                "id": "freedom",
                "prompt": "\"What does freedom look like to you now?\"",
                "response": "A night where silence is only silence and not a doorway pretending to be one.",
                "delta": 1,
            },
            {
                "id": "distrust",
                "prompt": "\"How do I know you won't lead us straight back into their hands?\"",
                "response": "You don't. You'll have to decide whether what I've risked escaping counts for anything.",
                "delta": -2,
            },
        ],
        "great_dialogue": "You ask the kind of careful questions that make panic less useful.",
        "exceptional_dialogue": "When the whispers start pressing at the edges, you're the reason they still sound like something outside me instead of inside.",
        "great_bonuses": {"spell_damage": 1, "Insight": 1},
        "exceptional_bonuses": {"WIS_save": 1},
        "scene_support": {
            "south_adit": {
                "text": "Irielle catches the cult's rhythm before it settles over the room and tears a clean opening through it.",
                "hero_bonus": 1,
                "ally_statuses": {"invisible": 1},
            },
            "forge_of_spells": {
                "text": "Irielle names the Choir's cadence out loud, and the thing posing as certainty finally sounds afraid.",
                "hero_bonus": 1,
                "ally_statuses": {},
            },
        },
    },
}


def apply_companion_profile(character: Character, companion_id: str) -> Character:
    profile = COMPANION_PROFILES[companion_id]
    character.companion_id = companion_id
    character.lore = list(profile["lore"])
    character.bond_flags = {"talked_topics": []}
    character.disposition = 0
    character.relationship_bonuses = {}
    character.notes.extend([profile["summary"]])
    return character


def relationship_label(disposition: int) -> str:
    if disposition <= -6:
        return "Terrible"
    if disposition <= -3:
        return "Bad"
    if disposition >= 9:
        return "Exceptional"
    if disposition >= 6:
        return "Great"
    if disposition >= 3:
        return "Good"
    return "Neutral"
