from __future__ import annotations

from .schema import QuestDefinition, QuestReward


ACT_1_QUESTS: dict[str, QuestDefinition] = {
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
}
