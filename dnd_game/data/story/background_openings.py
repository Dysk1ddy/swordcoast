from __future__ import annotations


BACKGROUND_STARTS: dict[str, dict[str, str]] = {
    "Soldier": {
        "title": "South Barracks Muster",
        "summary": "You begin at Neverwinter's south barracks, where caravan guards, militia veterans, and worried quartermasters are trying to keep the High Road open by force of habit and drilled discipline.",
        "arrival_note": "Your soldier's opening leaves you with a live look at how hard Neverwinter is leaning on thin patrol lines and tired veterans to protect the road south.",
    },
    "Acolyte": {
        "title": "Hall of Justice Hospice",
        "summary": "You begin at a temple hospice near Neverwinter's Hall of Justice, tending road-worn pilgrims and teamsters as poison, fear, and frontier rumors arrive faster than proper supplies do.",
        "arrival_note": "Your acolyte's opening shows the human cost of the Ashen Brand before anyone reduces it to caravan ledgers and patrol reports.",
    },
    "Criminal": {
        "title": "Blacklake Docks",
        "summary": "You begin along the Blacklake docks, where smugglers, fences, and hired blades trade in whispers, false manifests, and stolen cargo under Neverwinter's respectable face.",
        "arrival_note": "Your criminal's opening puts you close enough to the underworld to hear how stolen ore, poisoned blades, and frightened middlemen all connect to the same frontier trouble.",
    },
    "Sage": {
        "title": "House of Knowledge Archives",
        "summary": "You begin in a Neverwinter archive reading old surveys, ruined maps, and half-corrected histories that tie Phandalin, lost cellars, and the old frontier roads together.",
        "arrival_note": "Your sage's opening frames the campaign as a puzzle of old stone, missing records, and dangerous people trying very hard to keep those pieces apart.",
    },
    "Outlander": {
        "title": "Neverwinter Wood Trail Camp",
        "summary": "You begin in a rough camp on the edge of Neverwinter Wood, where charcoal burners, hunters, and road guides measure danger by tracks, smoke, and the sudden silence of birds.",
        "arrival_note": "Your outlander's opening starts with the frontier itself sounding the warning before city officials ever get around to naming the threat.",
    },
    "Charlatan": {
        "title": "Protector's Enclave Market",
        "summary": "You begin in a busy market quarter of Neverwinter, surrounded by hawkers, pilgrims, quick coin, and the kind of crowd that lets a skilled liar disappear in plain sight.",
        "arrival_note": "Your charlatan's opening makes the Ashen Brand feel less like a distant raider gang and more like a business arrangement with blood already baked into it.",
    },
    "Guild Artisan": {
        "title": "River District Counting-House",
        "summary": "You begin in a counting-house and warehouse row near the Neverwinter River, where craftspeople, factors, and caravan agents argue over shortages, breakage, and missing goods bound south.",
        "arrival_note": "Your guild artisan's opening shows the campaign through supply chains, missing shipments, and the quiet panic that hits trade before swords are ever drawn.",
    },
    "Hermit": {
        "title": "Wayside Shrine on the High Road",
        "summary": "You begin at a lonely shrine and cave shelter just north of Neverwinter, where wounded travelers leave offerings, fears, and strange signs for whoever still watches the road carefully.",
        "arrival_note": "Your hermit's opening gives the campaign an omen-heavy beginning, with sickness, spoor, and silence warning you before the city can turn those signs into policy.",
    },
}


def background_start_summary(background: str) -> str:
    entry = BACKGROUND_STARTS.get(background)
    if entry is None:
        return "You begin near Neverwinter, already close enough to the frontier to feel the road tugging south."
    return entry["summary"]
