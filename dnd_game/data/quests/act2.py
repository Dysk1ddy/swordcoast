from __future__ import annotations

from .schema import QuestDefinition, QuestReward


ACT_2_QUESTS: dict[str, QuestDefinition] = {
    "recover_pact_waymap": QuestDefinition(
        quest_id="recover_pact_waymap",
        title="Recover the Pact Waymap",
        giver="Halia Thornton",
        location="Miner's Exchange",
        summary=(
            "Halia wants an old Phandelver survey route recovered before rival claimants, mercenary diggers, "
            "or worse walk away with the only clear route into the deeper workings."
        ),
        objective="Secure the pact waymap fragments and bring the findings back to the Miner's Exchange.",
        turn_in="Return to Halia Thornton at the Miner's Exchange.",
        completion_flags=("agatha_truth_secured", "wave_echo_reached"),
        reward=QuestReward(xp=60, gold=28, items={"resonance_tonic": 1}),
        accepted_text=(
            "Halia speaks of maps the way soldiers speak of walls: whoever controls the route controls the argument "
            "that follows."
        ),
        ready_text="The pact waymap can finally be pieced together. Halia Thornton should see what route survived.",
        turn_in_text=(
            "Halia studies the recovered route in absolute silence, then smiles like someone who has just seen the "
            "shape of next season's leverage."
        ),
    ),
    "seek_agathas_truth": QuestDefinition(
        quest_id="seek_agathas_truth",
        title="Ask the Banshee What Was Buried",
        giver="Elira Dawnmantle",
        location="Conyberry Road",
        summary=(
            "Elira believes the dead around Conyberry still remember what greed and fear tried to hide from the living."
        ),
        objective="Reach Agatha's old circuit, learn what was buried, and return with a cleaner truth.",
        turn_in="Return to Elira Dawnmantle once the Conyberry lead is settled.",
        completion_flags=("agatha_truth_secured",),
        reward=QuestReward(xp=55, items={"scroll_quell_the_deep": 1}),
        accepted_text=(
            "Elira does not call it safe. She only says that grief often keeps straighter records than the living do."
        ),
        ready_text="Conyberry's dead have given up what they know. Elira Dawnmantle should hear it clearly.",
        turn_in_text=(
            "Elira listens without interrupting, then bows her head once as if accepting testimony from both the living "
            "and the lost."
        ),
    ),
    "rescue_stonehollow_scholars": QuestDefinition(
        quest_id="rescue_stonehollow_scholars",
        title="Bring Back the Survey Team",
        giver="Linene Graywind",
        location="Stonehollow Dig",
        summary=(
            "Linene hired specialists to read the dig cleanly. Now they are missing, and every missing scholar means "
            "someone else gets to write the first version of the truth."
        ),
        objective="Find the missing Stonehollow survey team and bring back whoever still lives.",
        turn_in="Return to Linene Graywind after Stonehollow is resolved.",
        completion_flags=("stonehollow_dig_cleared",),
        reward=QuestReward(xp=60, gold=22, items={"miners_ration_tin": 2}),
        accepted_text=(
            "Linene's request sounds like logistics, but the steel under it is plain enough: she wants her people home."
        ),
        ready_text="Stonehollow's missing survey team has been accounted for. Linene should hear how bad the dig became.",
        turn_in_text=(
            "Linene absorbs the report the way a quartermaster absorbs casualty numbers: without flinching until the room "
            "is finally empty."
        ),
    ),
    "cut_woodland_saboteurs": QuestDefinition(
        quest_id="cut_woodland_saboteurs",
        title="Break the Woodland Saboteurs",
        giver="Daran Edermath",
        location="Neverwinter Wood Edge",
        summary=(
            "Daran believes someone in the woods is cutting survey lines, stealing provisions, and making sure every "
            "honest expedition starts half-blind."
        ),
        objective="Track the woodland saboteurs, break their line, and return with proof the route is breathing again.",
        turn_in="Return to Daran Edermath once the survey camp route is secured.",
        completion_flags=("woodland_survey_cleared",),
        reward=QuestReward(xp=60, gold=25, items={"delvers_amber": 1}),
        accepted_text=(
            "Daran frames it as fieldcraft, not heroics. A route only exists if scouts can live long enough to chart it."
        ),
        ready_text="The woodland sabotage line is broken. Daran Edermath should know the trees are no longer fighting for someone else.",
        turn_in_text=(
            "Daran nods like a man hearing that a bowstring he distrusted has finally been cut."
        ),
    ),
    "hold_the_claims_meet": QuestDefinition(
        quest_id="hold_the_claims_meet",
        title="Hold the Claims Meeting Together",
        giver="Linene Graywind",
        location="Phandalin",
        summary=(
            "Phandalin needs a claims meeting that ends with a plan instead of knives, bribes, or a panic-driven scramble."
        ),
        objective="See the claims meeting through the sabotage night and keep the expedition from splintering.",
        turn_in="Report back to Linene Graywind once the town stops shaking itself apart.",
        completion_flags=("claims_meet_held", "phandalin_sabotage_resolved"),
        reward=QuestReward(xp=50, gold=18),
        accepted_text=(
            "Linene is blunt: if the town tears itself apart over claims before the mine is even reached, everyone loses."
        ),
        ready_text="The claims meeting held and the sabotage did not finish the job. Linene should hear how close it came.",
        turn_in_text=(
            "Linene exhales through her nose and immediately starts talking about what order can still be salvaged."
        ),
    ),
    "free_wave_echo_captives": QuestDefinition(
        quest_id="free_wave_echo_captives",
        title="Free the South Adit Prisoners",
        giver="Elira Dawnmantle",
        location="South Adit",
        summary=(
            "The deeper cells are being used for prisoners, labor, and whatever the Quiet Choir cannot yet do to people in public."
        ),
        objective="Open the South Adit cells, free the prisoners, and get the survivors back aboveground.",
        turn_in="Return to Elira Dawnmantle after the captives are clear of the adit.",
        completion_flags=("south_adit_cleared",),
        reward=QuestReward(xp=70, gold=30, items={"scroll_echo_step": 1}),
        accepted_text=(
            "Elira's voice goes colder than usual when she realizes the mine has turned into a prison."
        ),
        ready_text="The South Adit captives are free. Elira Dawnmantle should know who made it out.",
        turn_in_text=(
            "Elira receives the names of the living with more visible relief than any coin reward could equal."
        ),
    ),
    "sever_quiet_choir": QuestDefinition(
        quest_id="sever_quiet_choir",
        title="Sever the Quiet Choir",
        giver="Town Council",
        location="Wave Echo Cave",
        summary=(
            "The expedition race is only surface noise now. A cult beneath the cave is using the mine's old magic to study "
            "something that should never have been found."
        ),
        objective="Identify the Quiet Choir's leader, break the cult cell, and cut their hold on the mine.",
        turn_in="There is no formal turn-in beyond surviving and bringing the truth back out.",
        completion_flags=("caldra_defeated",),
        reward=QuestReward(xp=100, gold=40, items={"forge_blessing_elixir": 1}),
        accepted_text=(
            "By the time the Quiet Choir has a name, nobody in Phandalin mistakes this for an ordinary mining dispute anymore."
        ),
        ready_text="The Quiet Choir's leader has fallen. The people above should hear what kind of threat was really under them.",
        turn_in_text=(
            "The report lands on the table like a weight nobody in the room was ready to carry, but at least now it has a name."
        ),
    ),
}

