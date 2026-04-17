from __future__ import annotations

from ..content import create_bryn_underbough, create_tolan_ironshield
from .constants import LEVEL_XP_THRESHOLDS


class StoryTownHubMixin:
    def describe_blackwake_phandalin_arrival(self) -> None:
        assert self.state is not None
        if self.state.flags.get("phandalin_blackwake_arrival_seen"):
            return
        self.state.flags["phandalin_blackwake_arrival_seen"] = True
        resolution = self.state.flags.get("blackwake_resolution")
        if resolution == "rescue":
            self.say(
                "Blackwake's rescued teamsters have already become road-talk by the time you reach Phandalin. "
                "A few townsfolk look at you less like hired steel and more like someone who might actually bring people home."
            )
        elif resolution == "evidence":
            self.say(
                "The copied seals and ledgers from Blackwake make Phandalin's route permits look less like paperwork and more like a battlefield. "
                "Merchants notice the proof before they trust the promise behind it."
            )
        elif resolution == "sabotage":
            self.say(
                "Rumor reaches Phandalin ahead of you: a riverside cache burned, and the Ashen Brand's northbound supply rhythm stumbled. "
                "The town does not know whether to call it rescue, warning, or war."
            )
        else:
            self.say(
                "The Blackwake crossing follows you into town as a rumor of smoke, false seals, and caravans disappearing before Phandalin ever saw them."
            )
        if self.state.flags.get("blackwake_sereth_fate") == "escaped":
            self.say("One road hand lowers their voice over Sereth Vane's name, as if saying it too clearly might invite him south.")

    def scene_phandalin_hub(self) -> None:
        assert self.state is not None
        self.banner("Phandalin")
        if not self.state.flags.get("phandalin_arrived"):
            self.say(
                "Phandalin rises from rocky foothills in a scatter of simple homes, muddy lanes, and broken "
                "stonework left behind by an older, larger town. There are no real walls, no proper garrison, "
                "and too many people keeping weapons close at hand.",
                typed=True,
            )
            self.state.flags["phandalin_arrived"] = True
            self.add_journal("You reached Phandalin, a resettled frontier town under pressure from the Ashen Brand.")
            if self.state.flags.get("blackwake_completed"):
                self.describe_blackwake_phandalin_arrival()
            choice = self.scenario_choice(
                "How do you enter town?",
                [
                    self.quoted_option("INSIGHT", "I want to read the mood of the town before I speak."),
                    self.quoted_option("PERSUASION", "Let them know Neverwinter sent help."),
                    self.skill_tag("INVESTIGATION", self.action_option("Survey the tracks, barricades, and weak points first.")),
                ]
                + [text for _, text in self.scene_identity_options("phandalin_arrival")],
                allow_meta=False,
            )
            identity_options = self.scene_identity_options("phandalin_arrival")
            if choice > 3:
                selection_key, _ = identity_options[choice - 4]
                if self.handle_scene_identity_action("phandalin_arrival", selection_key):
                    return self.scene_phandalin_hub()
            elif choice == 1:
                self.player_speaker("I want to read the mood of the town before I speak.")
                success = self.skill_check(self.state.player, "Insight", 12, context="to gauge the town's fear")
                if success:
                    self.say("You catch the way fear keeps pulling the crowd's attention toward the old ruins whenever the gang is mentioned.")
                    self.add_clue("The crowd keeps glancing toward the old manor ruins whenever the Ashen Brand is named.")
                    self.reward_party(xp=10, reason="reading Phandalin's mood on arrival")
                else:
                    self.say("The town's fear is real, but too tangled and contradictory for one quick read to untangle.")
            elif choice == 2:
                self.player_speaker("Let them know Neverwinter sent help.")
                success = self.skill_check(self.state.player, "Persuasion", 12, context="to steady the town's nerves")
                if success:
                    self.say("A few shoulders ease as your words cut through the panic and sound like a promise worth believing.")
                    self.reward_party(xp=10, gold=6, reason="reassuring Phandalin on arrival")
                    self.say("A grateful merchant presses a few coins into your hand for road expenses.")
                else:
                    self.say("Your words land, but suspicion clings harder than hope in a town this strained.")
            else:
                self.player_action("Show me the tracks, barricades, and weak points first.")
                success = self.skill_check(self.state.player, "Investigation", 12, context="to assess the town's defenses")
                if success:
                    self.say("Fresh ruts, hurried repairs, and trampled lanes start to line up into a pattern you can actually use.")
                    self.add_clue("Fresh wagon ruts and bootprints suggest the gang watches the manor-side lanes closely.")
                    self.reward_party(xp=10, reason="surveying Phandalin's defenses")
                else:
                    self.say("Too many wagon ruts and bootprints overlap for a clean read before the trail goes cold.")
        elif self.state.flags.get("ashfall_watch_cleared") and not self.state.flags.get("phandalin_after_watch_seen"):
            self.say(
                "When you return from Ashfall Watch, Phandalin feels changed in all the small ways that matter. "
                "Doors open faster, wagon talk replaces funeral whispers, and more than one townsman studies the road "
                "east like it might finally belong to honest travelers again.",
                typed=True,
            )
            if self.state.player.level < 2:
                xp_to_level_two = max(0, LEVEL_XP_THRESHOLDS[2] - self.state.xp)
                if xp_to_level_two > 0:
                    self.reward_party(xp=xp_to_level_two, reason="regrouping after Ashfall Watch")
            self.state.flags["phandalin_after_watch_seen"] = True

        while True:
            if self.state.flags.get("ashfall_watch_cleared"):
                ready_text = self.action_option("Descend into Emberhall Cellars")
            else:
                ready_text = self.action_option("Ride for Ashfall Watch") if len(self.state.clues) >= 2 else self.action_option("Ride for Ashfall Watch (need 2 clues)")
            choice = self.scenario_choice(
                "Where do you go next?",
                [
                    self.action_option("Report to Steward Tessa Harrow"),
                    self.action_option("Visit the Stonehill Inn"),
                    self.action_option("Stop by the shrine of Tymora"),
                    self.skill_tag("TRADE", self.action_option("Browse Barthen's Provisions")),
                    self.skill_tag("TRADE", self.action_option("Call on Linene Graywind at the Lionshield trading post")),
                    self.action_option("Return to camp"),
                    self.action_option("Take a short rest"),
                    ready_text,
                ],
            )
            if choice == 1:
                self.visit_steward()
            elif choice == 2:
                self.visit_stonehill_inn()
            elif choice == 3:
                self.visit_shrine()
            elif choice == 4:
                self.visit_barthen_provisions()
            elif choice == 5:
                self.visit_trading_post()
            elif choice == 6:
                self.open_camp_menu()
            elif choice == 7:
                self.short_rest()
            else:
                if not self.state.flags.get("ashfall_watch_cleared") and len(self.state.clues) < 2:
                    self.say("You still need firmer leads before marching on the watchtower.")
                elif self.state.flags.get("ashfall_watch_cleared"):
                    self.state.current_scene = "emberhall_cellars"
                    return
                else:
                    self.state.current_scene = "ashfall_watch"
                    return

    def visit_steward(self) -> None:
        assert self.state is not None
        self.banner("Steward's Hall")
        if not self.state.flags.get("steward_seen"):
            self.say(
                "Steward Tessa Harrow stands over a desk buried in route maps, supply notes, and half-dried ink. "
                "She looks like someone trying to hold a frontier town together with ledgers, stubbornness, and not "
                "nearly enough sleep.",
                typed=True,
            )
            self.state.flags["steward_seen"] = True
        while True:
            options: list[tuple[str, str]] = []
            if self.quest_is_ready("secure_miners_road"):
                options.append(("turn_in", self.action_option("Tell Tessa what happened at Ashfall Watch.")))
            if not self.state.flags.get("steward_pressure_asked"):
                options.append(("pressure", "\"Where is the Ashen Brand hurting you the most?\""))
            if not self.state.flags.get("steward_ruins_asked"):
                options.append(("ruins", "\"Tell me about the old ruins around town.\""))
            if self.state.flags.get("blackwake_completed") and not self.state.flags.get("steward_blackwake_asked"):
                options.append(("blackwake", self.action_option("Share what happened at Blackwake Crossing.")))
            if not self.state.flags.get("steward_vow_made"):
                options.append(("vow", "\"I'll break their grip on Phandalin.\""))
            options.append(("leave", self.action_option("Leave Tessa to her work and move on.")))
            choice = self.scenario_choice("Choose what you say to Tessa.", [text for _, text in options])
            selection_key, _ = options[choice - 1]
            if selection_key == "turn_in":
                self.player_action("Ashfall Watch is broken. Your road can breathe again.")
                self.speaker(
                    "Tessa Harrow",
                    "Then the town gets one honest stretch of hope before the next problem starts knocking. That's more than we've had in months.",
                )
                self.turn_in_quest("secure_miners_road")
            elif selection_key == "pressure":
                self.state.flags["steward_pressure_asked"] = True
                self.player_speaker("Where is the Ashen Brand hurting you the most?")
                self.speaker(
                    "Tessa Harrow",
                    "Miners and supply runners take the worst of it. Every crew that stays home means less ore, less pay, and one more family buying food like it's a luxury. "
                    "Survivors keep naming a ruined watchtower east of town and cellar routes beneath older stonework, and every retelling sounds less like rumor and more like logistics.",
                )
                self.add_clue("Steward Harrow ties the gang to Ashfall Watch and cellar routes under old ruins.")
                if self.grant_quest(
                    "secure_miners_road",
                    note="Tessa says the watchtower is throttling miners, couriers, and every road-dependent family in town.",
                ):
                    self.speaker(
                        "Tessa Harrow",
                        "Break that watchtower and you won't just win a fight. You'll give this town room to breathe.",
                    )
            elif selection_key == "ruins":
                self.state.flags["steward_ruins_asked"] = True
                self.player_speaker("Tell me about the old ruins around town.")
                self.speaker(
                    "Tessa Harrow",
                    "The old foundations are blessing and curse alike. We build against them because the stone is already here, but every buried wall and forgotten cellar gives brigands another place to vanish before decent folk even know to look.",
                )
            elif selection_key == "blackwake":
                self.state.flags["steward_blackwake_asked"] = True
                self.player_action("Share what happened at Blackwake Crossing.")
                resolution = self.state.flags.get("blackwake_resolution")
                if resolution == "evidence":
                    self.speaker(
                        "Tessa Harrow",
                        "False seals this close to Neverwinter changes every petition on my desk. Give me names and route marks, and I can make officials answer a harder question than 'why are you afraid?'",
                    )
                    self.add_clue("Tessa can use the Blackwake ledgers to argue that the Ashen Brand is corrupting route authority, not merely raiding wagons.")
                    self.reward_party(gold=8, reason="sharing Blackwake proof with Phandalin's steward")
                elif resolution == "rescue":
                    self.speaker(
                        "Tessa Harrow",
                        "Then some of those families may reach us alive. That matters here. Proof can travel later; people need the road under their feet first.",
                    )
                    self.add_journal("Tessa Harrow promised to watch for survivors and teamsters pulled out of Blackwake Crossing.")
                elif resolution == "sabotage":
                    self.speaker(
                        "Tessa Harrow",
                        "A burned cache buys us time even if it leaves me with fewer papers to wave in a magistrate's face. I'll take time. Time lets a town move grain, tools, and children.",
                    )
                    self.add_clue("Blackwake's destroyed cache may weaken Ashen Brand supply pressure south of Neverwinter.")
                else:
                    self.speaker(
                        "Tessa Harrow",
                        "That is too organized to dismiss as roadside theft. Blackwake tells me the rot starts before wagons ever reach our hills.",
                    )
                if self.state.flags.get("blackwake_sereth_fate") == "escaped":
                    self.speaker("Tessa Harrow", "And if Sereth Vane is still breathing, I want that name in every watchman's ear by sundown.")
            elif selection_key == "vow":
                self.state.flags["steward_vow_made"] = True
                self.player_speaker("I'll break their grip on Phandalin.")
                self.speaker(
                    "Tessa Harrow",
                    "Then give me a result I can build a safer week on, and Phandalin will remember your name for the right reason.",
                )
            else:
                self.player_action("You leave Tessa to her work and move on.")
                return

    def visit_stonehill_inn(self) -> None:
        assert self.state is not None
        play_music_for_context = getattr(self, "play_music_for_context", None)
        refresh_scene_music = getattr(self, "refresh_scene_music", None)
        if callable(play_music_for_context):
            play_music_for_context("inn", restart=True)
        try:
            self.banner("Stonehill Inn")
            if not self.state.flags.get("inn_seen"):
                self.say(
                    "The inn smells of stew, wet wool, and the kind of caution that settles into a room after too many bad nights. "
                    "A halfling scout with quick eyes watches the door over the rim of her mug, and every armed traveler gets weighed "
                    "for danger before they earn the right to be background noise.",
                    typed=True,
                )
                self.state.flags["inn_seen"] = True
            while True:
                options: list[tuple[str, str]] = []
                if not self.state.flags.get("inn_buy_drink_asked"):
                    options.append(("drink", "\"Mind if I buy you a drink and ask a few questions?\""))
                if not self.state.flags.get("inn_road_rumors_asked"):
                    options.append(("rumors", "\"Tell me what the roads are saying about the Ashen Brand.\""))
                if self.state.flags.get("blackwake_completed") and not self.state.flags.get("inn_blackwake_rumor_asked"):
                    options.append(("blackwake", "\"What are people saying about Blackwake Crossing?\""))
                if not self.state.flags.get("inn_recruit_bryn_attempted") and not self.has_companion("Bryn Underbough"):
                    options.append(("recruit_bryn", self.quoted_option("PERSUASION", "Take a share of the contract and ride with me.")))
                elif (
                    not self.state.flags.get("inn_recruit_bryn_second_attempted")
                    and not self.has_companion("Bryn Underbough")
                ):
                    options.append(
                        (
                            "recruit_bryn_second",
                            self.quoted_option("INSIGHT", "You don't need luck. You need someone who listens. Tell me what you're waiting to hear."),
                        )
                    )
                if self.state.flags.get("tolan_waiting_at_inn") and not self.has_companion("Tolan Ironshield"):
                    options.append(("recruit_tolan", self.action_option("Wave Tolan over and ask him to gear up.")))
                options.append(("leave", self.action_option("Leave the common room for now.")))
                choice = self.scenario_choice("The common room quiets for a moment as you enter.", [text for _, text in options])
                selection_key, _ = options[choice - 1]
                if selection_key == "drink":
                    self.state.flags["inn_buy_drink_asked"] = True
                    self.player_speaker("Mind if I buy you a drink and ask a few questions?")
                    self.speaker(
                        "Bryn Underbough",
                        "Depends. If your questions are useful, so are my answers. Bryn Underbough. I know the trail, I know who's lying, and I know the difference between a worried town and one that's about to make desperate mistakes.",
                    )
                elif selection_key == "rumors":
                    self.state.flags["inn_road_rumors_asked"] = True
                    self.player_speaker("Tell me what the roads are saying about the Ashen Brand.")
                    self.speaker(
                        "Bryn Underbough",
                        "That they rotate scouts between Phandalin and a hillfort called Ashfall Watch, and that the scouts always seem to know which wagons are worth hurting first. "
                        "If the gang has a spine, that's where it'll be. Break that, and the rest starts looking mortal.",
                    )
                    self.add_clue("Bryn confirms Ashfall Watch is the gang's field base.")
                elif selection_key == "blackwake":
                    self.state.flags["inn_blackwake_rumor_asked"] = True
                    self.player_speaker("What are people saying about Blackwake Crossing?")
                    resolution = self.state.flags.get("blackwake_resolution")
                    if resolution == "rescue":
                        self.speaker(
                            "Stonehill Teamster",
                            "That some folk walked out of smoke who had no right surviving it. People remember that kind of help, even when they pretend they only care about freight.",
                        )
                    elif resolution == "evidence":
                        self.speaker(
                            "Stonehill Teamster",
                            "That the stolen seals were real enough to fool honest clerks. If you've got proof, keep it dry and close. Paper scares cowards when steel can't reach them yet.",
                        )
                    elif resolution == "sabotage":
                        self.speaker(
                            "Stonehill Teamster",
                            "That someone taught the Brand what a supply loss feels like. Makes the room nervous, that does, but not all nervous is bad.",
                        )
                    else:
                        self.speaker(
                            "Stonehill Teamster",
                            "That Blackwake was never just a burned crossing. It was a door, and somebody mean was deciding who got through.",
                        )
                    if self.state.flags.get("blackwake_sereth_fate") == "escaped":
                        self.speaker("Stonehill Teamster", "Also heard a name: Sereth Vane. Folk say he leaves clean desks and dirty roads behind him.")
                elif selection_key == "recruit_bryn":
                    self.state.flags["inn_recruit_bryn_attempted"] = True
                    self.player_speaker("Take a share of the contract and ride with me.")
                    success = self.skill_check(self.state.player, "Persuasion", 12, context="to convince Bryn the risk is worth it")
                    if success:
                        self.recruit_companion(create_bryn_underbough())
                        self.speaker(
                            "Bryn Underbough",
                            "Fair split, honest cause, and a chance to make bandits miserable before they make anyone else bury family? I'm in.",
                        )
                    else:
                        self.speaker("Bryn Underbough", "Not yet. You sound useful, but useful and lucky are not always the same thing.")
                elif selection_key == "recruit_bryn_second":
                    self.state.flags["inn_recruit_bryn_second_attempted"] = True
                    self.player_speaker("You don't need luck. You need someone who listens. Tell me what you're waiting to hear.")
                    success = self.skill_check(self.state.player, "Insight", 12, context="to read Bryn's hesitation and answer it plainly")
                    if success:
                        self.recruit_companion(create_bryn_underbough())
                        self.speaker(
                            "Bryn Underbough",
                            "There it is. Most people hear a scout and think boots and arrows. You heard judgment. Fine. I'll lend you mine.",
                        )
                    else:
                        self.speaker(
                            "Bryn Underbough",
                            "Closer. But if I ride with you, I need to know you'll read a room before it turns into a graveyard. Ask me again after you've proven that.",
                        )
                elif selection_key == "recruit_tolan":
                    self.player_action("You wave Tolan over and ask him to gear up again.")
                    self.state.flags.pop("tolan_waiting_at_inn", None)
                    self.recruit_companion(create_tolan_ironshield())
                    self.speaker("Tolan Ironshield", "About time. I was getting tired of waiting on soup.")
                else:
                    self.player_action("You leave the common room for now.")
                    return
        finally:
            if callable(refresh_scene_music):
                refresh_scene_music()
