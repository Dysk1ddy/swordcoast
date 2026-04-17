from __future__ import annotations

from .schema import QuestDefinition, QuestReward


ACT_1_QUESTS: dict[str, QuestDefinition] = {
    "trace_blackwake_cell": QuestDefinition(
        quest_id="trace_blackwake_cell",
        title="Embers Before the Road",
        giver="Mira Thann",
        location="Blackwake Crossing",
        summary=(
            "Smoke near the river cut points to burned toll records, forged route authority, and an Ashen Brand supply cell operating closer to Neverwinter than expected."
        ),
        objective="Investigate Blackwake Crossing, uncover the cache behind the forged papers, and decide what survives the floodgate chamber.",
        turn_in="Report the Blackwake outcome to Mira in Neverwinter or carry the proof south toward Phandalin.",
        completion_flags=("blackwake_completed",),
        reward=QuestReward(),
        accepted_text=(
            "The road to Phandalin can wait long enough to answer one ugly question: why are caravans vanishing before they even reach the wider High Road?"
        ),
        ready_text="The Blackwake cell has been resolved. The crossing's prisoners, ledgers, and cache damage will shape what the road hears next.",
        turn_in_text=(
            "Mira reads the Blackwake account without interrupting. By the end, the Ashen Brand is no longer a distant frontier gang on her board. It is a supply network with city-side shadows."
        ),
    ),
    "secure_miners_road": QuestDefinition(
        quest_id="secure_miners_road",
        title="Stop the Watchtower Raids",
        giver="Steward Tessa Harrow",
        location="Steward's Hall",
        summary=(
            "Tessa Harrow needs Ashfall Watch broken so miners, messengers, and supply runners can take "
            "the east road without vanishing into smoke and ambush."
        ),
        objective="Break the Ashen Brand's hold on Ashfall Watch, then return to Tessa Harrow.",
        turn_in="Return to Tessa Harrow in Steward's Hall.",
        completion_flags=("ashfall_watch_cleared",),
        reward=QuestReward(xp=45, gold=25),
        accepted_text=(
            "Tessa does not dress it up as heroics. She needs the watchtower raiders stopped before a frightened "
            "town begins starving by caution alone."
        ),
        ready_text="Ashfall Watch has fallen. Tessa Harrow should hear that the east road can breathe again.",
        turn_in_text=(
            "Relief finally reaches Tessa's face in full. For the first time all day, she speaks like someone "
            "who believes tomorrow's wagons might actually arrive."
        ),
    ),
    "restore_barthen_supplies": QuestDefinition(
        quest_id="restore_barthen_supplies",
        title="Keep the Shelves Full",
        giver="Barthen",
        location="Barthen's Provisions",
        summary="Barthen wants the raiders at Ashfall Watch driven off before Phandalin's simplest needs become luxuries.",
        objective="Clear Ashfall Watch and report back to Barthen once the road is safer.",
        turn_in="Return to Barthen's Provisions.",
        completion_flags=("ashfall_watch_cleared",),
        reward=QuestReward(xp=30, gold=12, items={"bread_round": 2, "camp_stew_jar": 1}),
        accepted_text=(
            "Barthen's request is practical to the point of pain: make the road safe enough that flour, bandages, "
            "and lamp oil stop feeling rarer than courage."
        ),
        ready_text="With Ashfall Watch broken, Barthen can finally start planning for steady wagons again.",
        turn_in_text=(
            "Barthen laughs once under his breath, more tired than cheerful, then immediately starts talking about "
            "what full shelves will mean for families who have been rationing every meal."
        ),
    ),
    "reopen_lionshield_trade": QuestDefinition(
        quest_id="reopen_lionshield_trade",
        title="Reopen the Trade Lane",
        giver="Linene Graywind",
        location="Lionshield Coster",
        summary=(
            "Linene needs proof that the Ashen Brand's chokehold is weakening so honest trade can move without paying "
            "for fear on both ends."
        ),
        objective="Break Ashfall Watch and return to Linene Graywind with the news.",
        turn_in="Return to Linene Graywind at the Lionshield trading post.",
        completion_flags=("ashfall_watch_cleared",),
        reward=QuestReward(xp=35, gold=18, items={"potion_healing": 1, "antitoxin_vial": 1}),
        accepted_text=(
            "Linene frames it in ledgers and steel, but the meaning is simple enough: if the watchtower stands, "
            "every honest caravan keeps bleeding coin to men with ash on their badges."
        ),
        ready_text="Ashfall Watch is down. Linene Graywind should know the trade lane finally has room to recover.",
        turn_in_text=(
            "Linene studies the soot on your gear, nods once, and starts reordering tomorrow in her head before you "
            "finish speaking."
        ),
    ),
    "silence_old_owl_well": QuestDefinition(
        quest_id="silence_old_owl_well",
        title="Silence Old Owl Well",
        giver="Halia Thornton",
        location="Miner's Exchange",
        summary=(
            "Halia Thornton wants the grave-salvage operation at Old Owl Well destroyed before more prospectors and exchange crews vanish into its dig lines."
        ),
        objective="Break the operation at Old Owl Well and return to Halia Thornton.",
        turn_in="Return to Halia Thornton at the Miner's Exchange.",
        completion_flags=("old_owl_well_cleared",),
        reward=QuestReward(xp=50, gold=24, items={"scroll_clarity": 1}),
        accepted_text=(
            "Halia phrases it like a ledger problem, but the meaning is simple enough: Old Owl Well is swallowing people, and every day it stays active makes the town smaller."
        ),
        ready_text="Old Owl Well is quiet. Halia Thornton should hear the grave-salvage line has been broken.",
        turn_in_text=(
            "Halia's expression barely changes, but the room around her seems to unclench all the same. Even polished pragmatism has room for relief when missing crews stop becoming permanent."
        ),
    ),
    "break_wyvern_tor_raiders": QuestDefinition(
        quest_id="break_wyvern_tor_raiders",
        title="Break the Wyvern Tor Raiders",
        giver="Daran Edermath",
        location="Edermath Orchard",
        summary=(
            "Daran Edermath wants the raiders at Wyvern Tor scattered before they keep turning the eastern hills into hunting ground for scouts, drovers, and herders."
        ),
        objective="Clear Wyvern Tor and report back to Daran Edermath.",
        turn_in="Return to Daran Edermath at the orchard.",
        completion_flags=("wyvern_tor_cleared",),
        reward=QuestReward(xp=50, gold=20, items={"greater_healing_draught": 1}),
        accepted_text=(
            "Daran does not romanticize the work. Wyvern Tor is a practical threat on practical roads, and he would prefer the town's scouts stop dying to prove it."
        ),
        ready_text="Wyvern Tor is clear. Daran Edermath should know the high-ground raiders are gone.",
        turn_in_text=(
            "Daran nods once, the kind of nod old soldiers reserve for work done cleanly. The hills will still be dangerous tomorrow, but at least now they will be honestly dangerous."
        ),
    ),
    "bryn_loose_ends": QuestDefinition(
        quest_id="bryn_loose_ends",
        title="Loose Ends",
        giver="Bryn Underbough",
        location="The road and whatever old cache still remembers her",
        summary=(
            "Bryn suspects one of her abandoned smuggler caches has been folded into the Ashen Brand's side traffic. She wants the ledger inside found and judged before someone else profits from it."
        ),
        objective="Track down Bryn's old cache trail and decide what to do with the ledger inside it.",
        turn_in="Resolve the ledger question with Bryn once the cache is found.",
        completion_flags=("bryn_loose_ends_resolved",),
        reward=QuestReward(),
        accepted_text=(
            "Bryn admits this one quietly: there is an old cache she never meant anyone worth saving to find. If the Brand reached it first, she wants your help ending the story cleanly."
        ),
        ready_text="Bryn's cache has been found. She needs your call on whether the ledger burns or gets sold.",
        turn_in_text=(
            "Bryn takes your answer without pretending it costs nothing. Whatever route that ledger once kept alive ends here, one way or another."
        ),
    ),
    "elira_faith_under_ash": QuestDefinition(
        quest_id="elira_faith_under_ash",
        title="Faith Under Ash",
        giver="Elira Dawnmantle",
        location="Wherever mercy has to stand under pressure",
        summary=(
            "Elira wants to see what kind of justice survives once the Ashen Brand is beaten badly enough to beg. She is asking about you as much as about them."
        ),
        objective="Face a captive servant of the Ashen Brand and decide whether mercy or fear carries the day.",
        turn_in="Make the call when Elira asks for it in the field.",
        completion_flags=("elira_faith_under_ash_resolved",),
        reward=QuestReward(),
        accepted_text=(
            "Elira says it gently, which somehow makes it harder: anyone can sound righteous before the blood is close. What matters is the answer you choose after."
        ),
        ready_text="Elira's question has reached the point where a real answer is needed, not another good intention.",
        turn_in_text=(
            "Elira does not praise or condemn you cheaply. She simply carries your answer forward, which is heavier in its own way than either reaction would have been."
        ),
    ),
}
