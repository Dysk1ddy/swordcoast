from __future__ import annotations

from ..data.story.background_openings import BACKGROUND_STARTS
from ..content import (
    create_elira_dawnmantle,
    create_enemy,
    create_kaelis_starling,
    create_rhogar_valeguard,
    create_tolan_ironshield,
)
from .encounter import Encounter


class StoryIntroMixin:
    def intro_pick_enemy(self, templates, *, name: str | None = None):
        return create_enemy(self.rng.choice(tuple(templates)), name=name)

    def scene_background_prologue(self) -> None:
        assert self.state is not None
        background = self.state.player.background
        handlers = {
            "Soldier": self.prologue_soldier,
            "Acolyte": self.prologue_acolyte,
            "Criminal": self.prologue_criminal,
            "Sage": self.prologue_sage,
            "Outlander": self.prologue_outlander,
            "Charlatan": self.prologue_charlatan,
            "Guild Artisan": self.prologue_guild_artisan,
            "Hermit": self.prologue_hermit,
        }
        handlers.get(background, self.prologue_default)()

    def background_prologue_header(self, background: str) -> None:
        entry = BACKGROUND_STARTS.get(background, {})
        self.banner(f"{background} Prologue: {entry.get('title', 'Opening')}")
        self.say(
            f"Starting point: {entry.get('summary', 'You begin close to Neverwinter, with the frontier already pulling at your day.')}",
            typed=True,
        )

    def finish_background_prologue(self, background: str, closing_text: str, *, clue: str = "", journal_note: str = "") -> None:
        assert self.state is not None
        if clue:
            self.add_clue(clue)
        self.say(closing_text)
        self.add_journal(
            journal_note
            or f"Your {background.lower()} prologue ends with the trail leading toward Mira Thann's private briefing in Neverwinter."
        )
        self.state.flags["background_prologue_completed"] = background
        self.state.flags.pop("background_prologue_pending", None)
        self.state.current_scene = "neverwinter_briefing"

    def resolve_background_encounter(
        self,
        *,
        title: str,
        description: str,
        enemies,
        hero_bonus: int = 0,
        parley_dc: int = 12,
    ) -> bool:
        encounter = Encounter(
            title=title,
            description=description,
            enemies=enemies,
            allow_flee=False,
            allow_parley=True,
            parley_dc=parley_dc,
            hero_initiative_bonus=hero_bonus,
            allow_post_combat_random_encounter=False,
        )
        outcome = self.run_encounter(encounter)
        if outcome == "defeat":
            self.handle_defeat("The opening turns against you before the wider road south can even begin.")
            return False
        return True

    def prologue_default(self) -> None:
        assert self.state is not None
        background = self.state.player.background
        self.background_prologue_header(background)
        self.say(
            "You arrive in Neverwinter carrying the instincts of your old life, and before the day is out someone points you toward "
            "Mira Thann, who is buying competence more quietly than most officers buy noise.",
            typed=True,
        )
        self.finish_background_prologue(
            background,
            "By dusk, those loose directions become a destination: a discreet briefing in Neverwinter about the road to Phandalin.",
        )

    def prologue_soldier(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Soldier")
        self.say(
            "The day begins in shouted counts and buckled straps. A courier from the south arrives bloodied and furious, "
            "and an Ashen Brand runner tries to cut through the mustering yard with dispatches that were never meant to leave it.",
            typed=True,
        )
        choice = self.scenario_choice(
            "How do you respond?",
            [
                self.skill_tag("ATHLETICS", self.action_option("Hit the gate hard before the runner clears the yard.")),
                self.skill_tag("INSIGHT", self.action_option("Read the panic and pick the real escape lane.")),
                self.skill_tag("INTIMIDATION", self.action_option("Lock the teamsters in line and make the thief choose fear over speed.")),
            ],
            allow_meta=False,
        )
        enemies = [create_enemy("bandit", name="Ashen Brand Runner")]
        enemies[0].current_hp = enemies[0].max_hp = 8
        hero_bonus = 0
        if choice == 1:
            self.player_action("Hit the gate hard before the runner clears the yard.")
            if self.skill_check(self.state.player, "Athletics", 11, context="to catch the runner before the lane opens"):
                self.apply_status(self.state.player, "emboldened", 2, source="drilled momentum")
                hero_bonus = 2
                self.say("You turn the breakout into a stand-up fight on your own timing.")
            else:
                self.apply_status(self.state.player, "reeling", 1, source="a rushed impact")
                self.say("You still get there first, but not as cleanly as you wanted.")
        elif choice == 2:
            self.player_action("Read the panic and pick the real escape lane.")
            if self.skill_check(self.state.player, "Insight", 11, context="to identify the true breakout line"):
                enemies[0].current_hp = 5
                hero_bonus = 1
                self.say("You ignore the decoy panic and ruin the runner's best chance to disappear.")
            else:
                self.say("You find the pattern a half-second late and have to recover with steel instead of foresight.")
        else:
            self.player_action("Lock the teamsters in line and make the thief choose fear over speed.")
            if self.skill_check(self.state.player, "Intimidation", 11, context="to bark order into a breaking yard"):
                self.apply_status(enemies[0], "frightened", 2, source="your command voice")
                self.say("The yard remembers discipline before it remembers fear.")
            else:
                self.say("The teamsters move, but panic still keeps the lane ugly.")
        if not self.resolve_background_encounter(
            title="South Barracks Breakout",
            description="An Ashen Brand runner tries to cut through the barracks yard with stolen dispatches.",
            enemies=enemies,
            hero_bonus=hero_bonus,
        ):
            return
        self.reward_party(xp=15, gold=6, reason="holding the barracks line")
        self.finish_background_prologue(
            "Soldier",
            "The recovered dispatch names Mira Thann as the officer quietly gathering capable hands for a harder answer than routine patrols can offer.",
            clue="A stolen dispatch confirms the attacks around Phandalin are organized enough to rattle Neverwinter's quartermasters.",
        )

    def prologue_acolyte(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Acolyte")
        self.say(
            "At the hospice, the road arrives as wounds first and explanation later. A pilgrim wagon limps in with poison in one teamster's veins, "
            "char on the axle wood, and survivors too shaken to tell their story cleanly.",
            typed=True,
        )
        choice = self.scenario_choice(
            "What do you do first?",
            [
                self.skill_tag("MEDICINE", self.action_option("Stabilize the poisoned teamster before the details vanish with them.")),
                self.skill_tag("RELIGION", self.action_option("Lead the room in a sharp, steady prayer instead of letting fear set the pace.")),
                self.skill_tag("NATURE", self.action_option("Read the toxin, claw marks, and scent trail outside the hospice gate.")),
            ],
            allow_meta=False,
        )
        enemies = [create_enemy("wolf")]
        enemies[0].current_hp = enemies[0].max_hp = 8
        if choice == 1:
            self.player_action("Stabilize the poisoned teamster before the details vanish with them.")
            if self.skill_check(self.state.player, "Medicine", 11, context="to keep the poison from closing the throat"):
                self.add_inventory_item("blessed_salve", source="the hospice stores")
                self.say("You buy the patient enough breath to confirm ash-bitter poison and disciplined raiders.")
            else:
                self.say("You keep them alive, but only scraps of the story come back with the breath.")
        elif choice == 2:
            self.player_action("Lead the room in a sharp, steady prayer instead of letting fear set the pace.")
            if self.skill_check(self.state.player, "Religion", 11, context="to turn ritual into usable calm"):
                self.apply_status(self.state.player, "blessed", 3, source="a centered prayer")
                self.say("The prayer leaves you moving through panic with cleaner purpose.")
            else:
                self.say("The words help, but only after fear has already had its first say.")
        else:
            self.player_action("Read the toxin, claw marks, and scent trail outside the hospice gate.")
            if self.skill_check(self.state.player, "Nature", 11, context="to identify what the raiders drove ahead of them"):
                self.apply_status(enemies[0], "reeling", 1, source="tracking its weak angle")
                self.say("The spoor tells you exactly how the beast will circle back.")
            else:
                self.say("The signs are muddied by too many feet, but danger is still moving your way.")
        if not self.resolve_background_encounter(
            title="Hospice Gate",
            description="An ash wolf bolts back toward the hospice, trying to finish the panic the raiders started.",
            enemies=enemies,
        ):
            return
        self.reward_party(xp=15, reason="protecting the hospice gate")
        self.finish_background_prologue(
            "Acolyte",
            "When the worst passes, a temple contact quietly points you toward Mira Thann, who is trying to treat the road south as more than an accounting problem.",
            clue="Survivors from the south speak of poison, disciplined raiders, and attacks designed to terrorize as much as steal.",
        )

    def prologue_criminal(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Criminal")
        self.say(
            "The Blacklake job is supposed to be simple: a fence, a courier, and a satchel full of stolen wagon seals. "
            "Instead, an Ashen Brand collector arrives early and starts talking like everyone in the room already belongs to someone.",
            typed=True,
        )
        choice = self.scenario_choice(
            "How do you play the room?",
            [
                self.skill_tag("DECEPTION", self.action_option("Pose as the collector's actual buyer and turn the meeting sideways.")),
                self.skill_tag("STEALTH", self.action_option("Slip above the warehouse floor and take the satchel before anyone notices.")),
                self.skill_tag("SLEIGHT OF HAND", self.action_option("Lift the ledger and leave the silver where it lies.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Pose as the collector's actual buyer and turn the meeting sideways.")
            if self.skill_check(self.state.player, "Deception", 12, context="to make two criminals distrust each other instead of you"):
                self.reward_party(xp=30, gold=12, reason="turning a dockside deal inside out")
                self.finish_background_prologue(
                    "Criminal",
                    "You walk out with the satchel and one useful name: Mira Thann, the officer quietly tracing where those forged seals keep ending up.",
                    clue="A stolen dockside ledger ties forged caravan seals to Phandalin-bound cargo.",
                )
                return
            self.say("The lie nearly lands, but not cleanly enough to stop steel from coming out.")
        elif choice == 2:
            self.player_action("Slip above the warehouse floor and take the satchel before anyone notices.")
            if self.skill_check(self.state.player, "Stealth", 12, context="to cross the beams without warning the floor below"):
                self.reward_party(xp=30, gold=8, reason="ghosting through the warehouse rafters")
                self.finish_background_prologue(
                    "Criminal",
                    "You vanish into the fog with exactly the sort of evidence Mira Thann has been paying quiet coin to find.",
                    clue="The satchel holds seals meant to mark southbound cargo as safe for Ashen Brand middlemen.",
                )
                return
            self.say("A creaking beam turns the theft into a chase.")
        else:
            self.player_action("Lift the ledger and leave the silver where it lies.")
            if self.skill_check(self.state.player, "Sleight of Hand", 12, context="to steal the real value out from under armed men"):
                self.reward_party(xp=30, gold=10, reason="lifting the ledger out of a live exchange")
                self.finish_background_prologue(
                    "Criminal",
                    "The ledger puts you on the same trail Mira Thann has been following from the lawful side of the city, which is inconvenient but useful.",
                    clue="The ledger shows stolen ore and false caravan papers moving through Blacklake before reaching the road south.",
                )
                return
            self.say("Your fingers are quick, but not quick enough to keep the room from erupting.")
        enemies = [create_enemy("bandit", name="Ashen Brand Collector")]
        enemies[0].current_hp = enemies[0].max_hp = 9
        if not self.resolve_background_encounter(
            title="Blacklake Warehouse",
            description="An Ashen Brand collector finally decides the room would be safer if you stopped breathing.",
            enemies=enemies,
            parley_dc=13,
        ):
            return
        self.reward_party(xp=10, gold=6, reason="surviving the Blacklake warehouse fight")
        self.finish_background_prologue(
            "Criminal",
            "Among the spilled papers is the one name worth following next: Mira Thann, who has begun asking the same questions from a safer side of the law.",
            clue="Blacklake smugglers are laundering forged wagon seals tied to Phandalin cargo.",
        )

    def prologue_sage(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Sage")
        self.say(
            "In the archive, old surveys of Phandalin and cellar plans beneath ruined manors stop looking academic once someone starts stealing only the pages that matter. "
            "A nervous scrivener insists the missing folios vanished just before dawn.",
            typed=True,
        )
        choice = self.scenario_choice(
            "How do you respond?",
            [
                self.skill_tag("INVESTIGATION", self.action_option("Follow the corrections, dust, and shelf gaps instead of the panic.")),
                self.skill_tag("ARCANA", self.action_option("Decode the sigils and shorthand in the margins before the thief can profit from them.")),
                self.skill_tag("HISTORY", self.action_option("Reconstruct which ruin-map would matter most to an organized gang.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Follow the corrections, dust, and shelf gaps instead of the panic.")
            success = self.skill_check(self.state.player, "Investigation", 11, context="to catch the thief's route through the archive")
        elif choice == 2:
            self.player_action("Decode the sigils and shorthand in the margins before the thief can profit from them.")
            success = self.skill_check(self.state.player, "Arcana", 11, context="to read the hidden notation in the copied plans")
        else:
            self.player_action("Reconstruct which ruin-map would matter most to an organized gang.")
            success = self.skill_check(self.state.player, "History", 11, context="to identify the ruin line the theft was really after")
        if success:
            self.add_inventory_item("focus_ink", source="a grateful archive keeper")
            self.reward_party(xp=30, reason="untangling the archive theft")
            self.finish_background_prologue(
                "Sage",
                "The archivist sends you straight to Mira Thann, who needs someone able to connect raiders, ruin plans, and frontier logistics into one coherent problem.",
                clue="Archive notes point to old cellar routes beneath manor-side stonework in and around Phandalin.",
            )
            return
        self.say("You solve enough of the pattern to know the theft matters, but not fast enough to stop the getaway cleanly.")
        enemies = [create_enemy("bandit_archer", name="Archive Cutout")]
        enemies[0].current_hp = enemies[0].max_hp = 7
        if not self.resolve_background_encounter(
            title="Archive Stair",
            description="A hired cutout bolts for the service stair with copied ruin plans under one arm.",
            enemies=enemies,
        ):
            return
        self.reward_party(xp=10, reason="recovering the copied plans")
        self.finish_background_prologue(
            "Sage",
            "The copied folios are damaged but readable, and the one official in Neverwinter who will care immediately is Mira Thann.",
            clue="Someone is stealing exactly the plans that would make hidden cellar routes under frontier ruins usable.",
        )

    def prologue_outlander(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Outlander")
        self.say(
            "The camp wakes to the wrong kind of quiet. No birds, fresh spoor, and a cooking fire kicked apart in the dark tell you raiders tested the trail line before sunrise and may still be circling back.",
            typed=True,
        )
        choice = self.scenario_choice(
            "What do you trust first?",
            [
                self.skill_tag("SURVIVAL", self.action_option("Set your ground where the tracks say they will come through.")),
                self.skill_tag("PERCEPTION", self.action_option("Climb high, count movement, and refuse to be surprised.")),
                self.skill_tag("STEALTH", self.action_option("Ghost into the brush and strike from the line they think is empty.")),
            ],
            allow_meta=False,
        )
        enemies = [
            self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold")),
            self.intro_pick_enemy(("wolf", "mireweb_spider")),
        ]
        enemies[0].current_hp = enemies[0].max_hp = 5
        enemies[1].current_hp = enemies[1].max_hp = 7
        hero_bonus = 0
        if choice == 1:
            self.player_action("Set your ground where the tracks say they will come through.")
            if self.skill_check(self.state.player, "Survival", 11, context="to build the fight on your chosen ground"):
                hero_bonus = 2
                self.say("When they come, they come exactly where your instincts said they would.")
            else:
                self.say("The pattern is there, but not cleanly enough to fully own the opening.")
        elif choice == 2:
            self.player_action("Climb high, count movement, and refuse to be surprised.")
            if self.skill_check(self.state.player, "Perception", 11, context="to catch the circling wolf before it closes"):
                self.apply_status(enemies[1], "surprised", 1, source="your high-ground warning")
                self.say("You spot the wolf's angle early and force the whole approach into the open.")
            else:
                self.say("You see enough to know the danger is real, but not enough to own every angle.")
        else:
            self.player_action("Ghost into the brush and strike from the line they think is empty.")
            if self.skill_check(self.state.player, "Stealth", 11, context="to disappear from the camp's expected defense line"):
                enemies[0].current_hp = 3
                hero_bonus = 1
                self.say("Your first strike lands before the goblin can decide whether this camp is prey or trap.")
            else:
                self.say("The brush hides you until the last second, and then everyone finds everyone at once.")
        if not self.resolve_background_encounter(
            title="Camp at First Light",
            description="A goblin outrider and ash wolf press into camp to test whether the road guides are easy prey.",
            enemies=enemies,
            hero_bonus=hero_bonus,
        ):
            return
        self.reward_party(xp=15, gold=5, reason="breaking the dawn raid")
        self.finish_background_prologue(
            "Outlander",
            "Among the raiders' gear is a scrap pointing toward Phandalin, and before noon a road warden tells you Mira Thann has been trying to get ahead of exactly this pattern.",
            clue="The raiders are probing camps north of Phandalin, not just hitting wagons once they reach the frontier town itself.",
        )

    def prologue_charlatan(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Charlatan")
        self.say(
            "The market loves a polished lie until someone more dangerous than a customer decides your talent is useful. "
            "An Ashen Brand fixer corners you between stalls and offers a choice between quiet employment and louder regret.",
            typed=True,
        )
        choice = self.scenario_choice(
            "How do you answer?",
            [
                self.skill_tag("DECEPTION", self.action_option("Convince the fixer you already work for someone richer and harder to cross.")),
                self.skill_tag("PERFORMANCE", self.action_option("Turn the exchange into a public spectacle the fixer cannot control.")),
                self.skill_tag("INSIGHT", self.action_option("Read what the fixer is really protecting and press there first.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Convince the fixer you already work for someone richer and harder to cross.")
            success = self.skill_check(self.state.player, "Deception", 12, context="to sell a lie dangerous enough to earn caution")
        elif choice == 2:
            self.player_action("Turn the exchange into a public spectacle the fixer cannot control.")
            success = self.skill_check(self.state.player, "Performance", 12, context="to weaponize the crowd's attention")
        else:
            self.player_action("Read what the fixer is really protecting and press there first.")
            success = self.skill_check(self.state.player, "Insight", 12, context="to find the pressure point in the fixer's confidence")
        if success:
            self.reward_party(xp=30, gold=10, reason="turning the market scene your way")
            self.finish_background_prologue(
                "Charlatan",
                "Once the fixer peels off, a watching clerk quietly suggests you share that information with Mira Thann before somebody deadlier turns it into policy.",
                clue="The fixer lets slip that the Ashen Brand is paying well for forged southbound papers and quiet buyers.",
            )
            return
        self.say("The read is close, but not close enough, and the fixer reaches for steel rather than pride.")
        enemies = [create_enemy("bandit", name="Ashen Brand Fixer")]
        enemies[0].current_hp = enemies[0].max_hp = 8
        if not self.resolve_background_encounter(
            title="Market Corner",
            description="The fixer decides a crowded market is still quiet enough for one quick killing blow.",
            enemies=enemies,
        ):
            return
        self.reward_party(xp=10, gold=6, reason="surviving the market confrontation")
        self.finish_background_prologue(
            "Charlatan",
            "The fixer's purse and papers both point toward the same next stop: Mira Thann's private recruiting effort in Neverwinter.",
            clue="Forged identities and caravan papers are part of how the Ashen Brand keeps its trade side alive.",
        )

    def prologue_guild_artisan(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Guild Artisan")
        self.say(
            "The counting-house is a battlefield disguised as a ledger. Too many southbound crates are arriving light, too many teamsters are revising weights after the fact, "
            "and somebody expects the fraud to drown in ordinary confusion.",
            typed=True,
        )
        choice = self.scenario_choice(
            "What do you do first?",
            [
                self.skill_tag("INVESTIGATION", self.action_option("Audit the manifests until the missing route shows its shape.")),
                self.skill_tag("PERSUASION", self.action_option("Settle the room and get the teamsters talking plainly.")),
                self.skill_tag("ATHLETICS", self.action_option("Cut off the crate-haulers trying to leave before questions start.")),
            ],
            allow_meta=False,
        )
        enemies = [create_enemy("bandit_archer", name="Ashen Brand Teamster")]
        enemies[0].current_hp = enemies[0].max_hp = 8
        if choice == 1:
            self.player_action("Audit the manifests until the missing route shows its shape.")
            if self.skill_check(self.state.player, "Investigation", 11, context="to catch where the numbers stop being honest"):
                self.add_inventory_item("camp_stew_jar", source="a grateful warehouse master")
                self.reward_party(xp=30, gold=8, reason="breaking the warehouse fraud pattern")
                self.finish_background_prologue(
                    "Guild Artisan",
                    "The master factor sends you to Mira Thann before the next caravan leaves, because somebody needs to fix the road rather than merely price the loss.",
                    clue="Manipulated manifests keep bending southbound cargo toward the same vulnerable approach to Phandalin.",
                )
                return
            self.say("You find the fraud, but not before one culprit tries to bolt with the evidence.")
        elif choice == 2:
            self.player_action("Settle the room and get the teamsters talking plainly.")
            if self.skill_check(self.state.player, "Persuasion", 11, context="to turn a shouting match into usable testimony"):
                self.reward_party(xp=30, gold=6, reason="untangling the teamsters' testimony")
                self.finish_background_prologue(
                    "Guild Artisan",
                    "With the testimony in hand, you are pointed toward Mira Thann, who needs someone that understands how trade panic becomes a weapon.",
                    clue="Multiple teamsters name the same hill watch and the same fear of being singled out on the road to Phandalin.",
                )
                return
            self.say("You settle part of the room, but one liar still decides leaving is safer than talking.")
        else:
            self.player_action("Cut off the crate-haulers trying to leave before questions start.")
            if self.skill_check(self.state.player, "Athletics", 11, context="to block the runaway teamster before the lane opens"):
                self.apply_status(enemies[0], "reeling", 1, source="your shoulder-check")
                self.say("You stop the escape hard enough that the culprit has to fight or talk in the yard.")
            else:
                self.say("You get there only just, and now the lane turns violent instead of orderly.")
        if not self.resolve_background_encounter(
            title="Counting-House Yard",
            description="A compromised teamster tries to flee the warehouse row with altered manifests and a bow at their back.",
            enemies=enemies,
        ):
            return
        self.reward_party(xp=10, gold=4, reason="stopping the warehouse runner")
        self.finish_background_prologue(
            "Guild Artisan",
            "The recovered manifests are enough to interest Mira Thann immediately, because the missing goods are no longer abstract numbers once they start mapping a campaign.",
            clue="Trade sabotage around Neverwinter is being shaped to soften the routes feeding Phandalin.",
        )

    def prologue_hermit(self) -> None:
        assert self.state is not None
        self.background_prologue_header("Hermit")
        self.say(
            "The shrine keeps a quieter watch than any city tower. Before sunrise, a feverish courier collapses near the offerings stone, and the signs around them—drag marks, ash scent, and broken brush—say they were pushed hard for a reason."
        )
        choice = self.scenario_choice(
            "What do you trust first?",
            [
                self.skill_tag("MEDICINE", self.action_option("Stabilize the courier before whatever hunted them closes the distance.")),
                self.skill_tag("NATURE", self.action_option("Read the spoor and choose where the pursuit will break cover.")),
                self.skill_tag("RELIGION", self.action_option("Treat the courier's warning as omen and pattern, not nonsense.")),
            ],
            allow_meta=False,
        )
        enemies = [self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold"))]
        enemies[0].current_hp = enemies[0].max_hp = 5
        if choice == 1:
            self.player_action("Stabilize the courier before whatever hunted them closes the distance.")
            if self.skill_check(self.state.player, "Medicine", 11, context="to keep the courier conscious long enough to speak clearly"):
                self.add_inventory_item("moonmint_drops", source="the shrine stores")
                self.say("You buy the courier enough clarity to name the watchtower haunting the road south.")
            else:
                self.say("You save their life, but not their full account of the chase.")
        elif choice == 2:
            self.player_action("Read the spoor and choose where the pursuit will break cover.")
            if self.skill_check(self.state.player, "Nature", 11, context="to read the hunter's angle before it becomes an attack"):
                self.apply_status(enemies[0], "surprised", 1, source="your omen-read ground")
                self.say("The trail gives away the pursuer's confidence, and that lets you meet it where it is weakest.")
            else:
                self.say("The signs are real but half-scrubbed, and the pursuer still gets close before you pin them down.")
        else:
            self.player_action("Treat the courier's warning as omen and pattern, not nonsense.")
            if self.skill_check(self.state.player, "Religion", 11, context="to hear meaning inside the courier's fractured warning"):
                self.apply_status(self.state.player, "blessed", 2, source="a hard-won omen")
                self.say("The warning stops sounding random and starts sounding directional.")
            else:
                self.say("The omen stays clouded, and the answer arrives on a blade instead of in words.")
        if not self.resolve_background_encounter(
            title="Wayside Pursuit",
            description="A goblin outrider follows the courier to the shrine, hoping the quiet place will make the finish easier.",
            enemies=enemies,
        ):
            return
        self.reward_party(xp=15, reason="protecting the courier at the shrine")
        self.finish_background_prologue(
            "Hermit",
            "Once the courier is safe enough to hand off, the one name they insist you hear next is Mira Thann's. Whatever stalks the road south has moved beyond omen into open work.",
            clue="A hunted courier names Ashfall Watch as a key pressure point on the road toward Phandalin.",
        )

    def scene_neverwinter_briefing(self) -> None:
        assert self.state is not None
        self.banner("Act I: Ashes on the Triboar Trail")
        if not self.state.flags.get("briefing_seen"):
            self.say(
                "Warm mist drifts off the Neverwinter River as you enter the Jewel of the North. "
                "Even after the devastation tied to Mount Hotenow, craftsmen, traders, and laborers "
                "keep the city rebuilding itself with stubborn pride.",
                typed=True,
            )
            self.speaker(
                "Mira Thann",
                "Caravans bound for Phandalin have vanished, miners are being shaken down, and a new gang calling itself the Ashen Brand is using the frontier's old ruins for cover.",
            )
            self.state.flags["briefing_seen"] = True

        while True:
            options: list[tuple[str, str]] = []
            if not self.state.flags.get("briefing_q_neverwinter"):
                options.append(("neverwinter", "\"How is Neverwinter holding together these days?\""))
            if not self.state.flags.get("briefing_q_phandalin"):
                options.append(("phandalin", "\"Tell me what matters most about Phandalin before I ride.\""))
            if not self.state.flags.get("briefing_q_brand"):
                options.append(("brand", "\"How dangerous is this Ashen Brand, really?\""))
            options.extend(self.scene_identity_options("neverwinter_briefing"))
            if not self.state.flags.get("neverwinter_preparation_done"):
                options.append(("prep", self.action_option("Make one more stop in Neverwinter before riding out.")))
            options.append(("inn", self.action_option("Rest at a Neverwinter inn (5 gp per active party member).")))
            options.append(("leave", self.action_option("Take the writ and head for the High Road.")))
            choice = self.scenario_choice("Choose your response to Mira.", [text for _, text in options])
            selection_key, selection = options[choice - 1]
            if selection_key.startswith(("class:", "race:")):
                if self.handle_scene_identity_action("neverwinter_briefing", selection_key):
                    continue
            self.player_choice_output(selection)
            if selection_key == "neverwinter":
                self.state.flags["briefing_q_neverwinter"] = True
                self.speaker(
                    "Mira Thann",
                    "Neverwinter is bruised, not broken. Trade is flowing again, and Lord Neverember wants the road to Phandalin secure before fear spreads back north.",
                )
            elif selection_key == "phandalin":
                self.state.flags["briefing_q_phandalin"] = True
                self.speaker(
                    "Mira Thann",
                    "Phandalin is a resettled frontier town south of here. It was lost for centuries after monsters destroyed the old settlement, and the folk there still live like every roof beam matters.",
                )
            elif selection_key == "brand":
                self.state.flags["briefing_q_brand"] = True
                self.speaker(
                    "Mira Thann",
                    "Dangerous enough that witnesses keep mentioning goblin outriders, poisoned blades, and a hobgoblin sergeant running the field work from a hill watchtower east of town.",
                )
            elif selection_key == "prep":
                self.handle_neverwinter_prep()
            elif selection_key == "inn":
                self.paid_inn_long_rest("a Neverwinter inn")
            else:
                self.handle_neverwinter_departure_fork()
                return

    def handle_neverwinter_prep(self) -> None:
        assert self.state is not None
        choice = self.scenario_choice(
            "Pick one last preparation before you leave Neverwinter.",
            [
                self.quoted_option("INVESTIGATION", "Let me review the missing caravan ledgers."),
                self.quoted_option("RELIGION", "I want a blessing and road-prayer before I leave."),
                self.quoted_option("PERSUASION", "Point me to the teamsters and dockhands. Rumors travel fast."),
                self.action_option("Skip the detour and ride now."),
            ],
            allow_meta=False,
        )
        if choice == 1:
            success = self.skill_check(self.state.player, "Investigation", 12, context="to piece together the caravan trail")
            if success:
                self.say("The ledger gaps stop looking random and start forming a route pattern with one ugly choke point in common.")
                self.add_clue("Caravan ledgers point to repeated disappearances near the old switchback east of Phandalin.")
                self.reward_party(xp=15, gold=8, reason="reviewing caravan ledgers")
            else:
                self.say("The ledgers are too incomplete and hastily corrected to yield more than suspicion.")
        elif choice == 2:
            success = self.skill_check(self.state.player, "Religion", 12, context="to center yourself with a road prayer")
            self.add_inventory_item("potion_healing", source="the Neverwinter temple")
            if success:
                self.say("The prayer settles over you cleanly, and for a moment the road ahead feels chosen rather than feared.")
                self.reward_party(xp=10, reason="seeking a blessing before the road")
            else:
                self.say("The words do not quite settle, but the ritual still steadies your breathing before departure.")
            self.say("A temple acolyte presses an extra healing draught into your hands before you leave.")
        elif choice == 3:
            success = self.skill_check(self.state.player, "Persuasion", 12, context="to loosen anxious tongues on the docks")
            if success:
                self.say("Once one dockhand starts talking, the rest fill in the gaps with the kind of details only workers notice.")
                self.add_clue("Dockside rumors say the Ashen Brand sells stolen ore through quiet middlemen.")
                self.reward_party(xp=15, gold=12, reason="working the rumor mill")
            else:
                self.say("The dockworkers stay guarded, but a few half-finished warnings still leave you with something useful to carry south.")
                self.reward_party(gold=4, reason="working the rumor mill")
        else:
            self.say("You keep your focus on the road ahead.")
        self.state.flags["neverwinter_preparation_done"] = True

    def handle_neverwinter_tymora_shrine(self) -> None:
        assert self.state is not None
        if self.state.flags.get("neverwinter_tymora_shrine_seen"):
            return
        self.state.flags["neverwinter_tymora_shrine_seen"] = True
        self.state.flags["neverwinter_elira_met"] = True
        self.banner("South Gate Shrine of Tymora")
        self.say(
            "Mira's writ takes you through Neverwinter's southern gate, where a temporary Tymoran shrine has been lashed "
            "to a rebuilt watch alcove. A priestess is treating a drover whose arm has gone gray around an ash-bitter cut, "
            "while Helm's Hold pilgrims and Phandalin teamsters wait in a nervous half-circle.",
            typed=True,
        )
        self.speaker(
            "Elira Dawnmantle",
            "If the road is teaching its wounds this close to the city, then Phandalin will be seeing worse by nightfall.",
        )
        choice = self.scenario_choice(
            "How do you help at the shrine before the road takes you south?",
            [
                self.skill_tag("MEDICINE", self.action_option("Stabilize the poisoned drover with Elira.")),
                self.skill_tag("RELIGION", self.action_option("Lead Tymora's road-prayer for the waiting caravan.")),
                self.skill_tag("INVESTIGATION", self.action_option("Study the ash toxin and the false road marks on the harness.")),
                self.action_option("Keep the shrine moving and save your strength for the road."),
            ],
            allow_meta=False,
        )
        helped_elira = False
        if choice == 1:
            self.player_action("Stabilize the poisoned drover with Elira.")
            helped_elira = self.skill_check(self.state.player, "Medicine", 12, context="to slow the ash-bitter poison")
            if helped_elira:
                self.state.flags["elira_helped"] = True
                self.state.flags["neverwinter_elira_helped"] = True
                self.state.flags["road_poison_pattern_known"] = True
                self.add_clue("Elira identifies an ash-bitter poison reaching victims before Phandalin.")
                self.reward_party(xp=10, reason="helping Elira stabilize a poisoned drover")
                self.say("The gray edge of the wound stops spreading, and Elira gives you a small, approving nod.")
            else:
                self.say("The poison keeps moving, but your pressure and clean bandage buy Elira enough time to save the drover.")
        elif choice == 2:
            self.player_action("Lead Tymora's road-prayer for the waiting caravan.")
            helped_elira = self.skill_check(self.state.player, "Religion", 12, context="to steady the shrine and caravan")
            self.add_inventory_item("blessed_salve", source="Elira's shrine satchel")
            if helped_elira:
                self.state.flags["elira_helped"] = True
                self.state.flags["neverwinter_elira_blessing"] = True
                self.reward_party(xp=10, reason="steadying the South Gate shrine")
                self.say("The prayer quiets the panic without softening the danger, which may be Tymora's cleanest kind of luck.")
            else:
                self.say("The words land unevenly, but the caravan still leaves with steadier hands and one less argument.")
        elif choice == 3:
            self.player_action("Study the ash toxin and the false road marks on the harness.")
            helped_elira = self.skill_check(self.state.player, "Investigation", 12, context="to connect poison, harness marks, and forged authority")
            if helped_elira:
                self.state.flags["elira_helped"] = True
                self.state.flags["neverwinter_false_road_marks_found"] = True
                self.state.flags["blackwake_millers_ford_lead"] = True
                self.add_clue("Harness marks at Neverwinter's gate match false roadwarden inspections near Miller's Ford.")
                self.reward_party(xp=10, reason="reading the poisoned road evidence")
                self.say("The harness cuts are too neat for panic. Someone with copied authority pulled this wagon out of line.")
            else:
                self.say("You catch the pattern too late to name it cleanly, but the false inspection cuts stay in your mind.")
        else:
            self.player_action("Keep the shrine moving and save your strength for the road.")
            self.add_inventory_item("potion_healing", source="Elira's road charity basket")
            self.say("Elira presses a healing draught into your hands anyway. Luck, apparently, dislikes going unused.")

        if self.has_companion("Elira Dawnmantle"):
            return
        options = [
            self.quoted_option("RECRUIT", "Walk with us. The road needs a field priest more than a waiting shrine."),
            self.quoted_option("SAFE", "Finish your work here. If Phandalin still needs you, we will find you there."),
        ]
        recruit_choice = self.scenario_choice("Elira looks from the shrine to the south road.", options, allow_meta=False)
        self.player_choice_output(options[recruit_choice - 1])
        if recruit_choice == 1:
            if self.state.flags.get("elira_helped") or self.skill_check(
                self.state.player,
                "Persuasion",
                12,
                context="to convince Elira the field needs her now",
            ):
                self.recruit_companion(create_elira_dawnmantle())
                self.state.flags["elira_neverwinter_recruited"] = True
                self.state.flags["shrine_recruit_attempted"] = True
                self.speaker("Elira Dawnmantle", "Then I walk now. Tymora can keep a shrine; people need hands.")
            else:
                self.state.flags["neverwinter_elira_recruit_failed"] = True
                self.speaker("Elira Dawnmantle", "Not yet. Earn the road's trust, and ask me again in Phandalin.")
        else:
            self.state.flags["elira_neverwinter_available_in_phandalin"] = True
            self.speaker("Elira Dawnmantle", "Then I will finish here and follow the wounded south. We may meet again before the day is done.")

    def handle_neverwinter_high_road_milehouse(self) -> None:
        assert self.state is not None
        if self.state.flags.get("neverwinter_high_road_milehouse_seen"):
            return
        self.state.flags["neverwinter_high_road_milehouse_seen"] = True
        self.banner("High Road Milehouse")
        self.say(
            "Past the last Neverwinter stones, the High Road narrows around a shuttered milehouse used by Helm's Hold pilgrims, "
            "Lord Neverember's roadwardens, and Phandalin-bound wagons. Fresh ash has been rubbed into the milemark, trying to "
            "turn a lawful stop into a frightened detour.",
            typed=True,
        )
        enemies = [create_enemy("brand_saboteur")]
        if self.act1_party_size() >= 3:
            enemies.append(create_enemy("bandit"))
        else:
            enemies[0].current_hp = enemies[0].max_hp = 7
        hero_bonus = 0
        choice = self.scenario_choice(
            "Which path do you secure from the milehouse?",
            [
                self.skill_tag("INVESTIGATION", self.action_option("Inspect the false roadwarden writs before anyone moves on.")),
                self.skill_tag("SURVIVAL", self.action_option("Scout the Neverwinter Wood verge for the ambush line.")),
                self.skill_tag("PERSUASION", self.action_option("Organize the Helm's Hold pilgrims and refugee wagons into one guarded column.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Inspect the false roadwarden writs before anyone moves on.")
            if self.skill_check(self.state.player, "Investigation", 12, context="to expose forged roadwarden authority"):
                self.state.flags["neverwinter_false_writs_spotted"] = True
                self.state.flags["blackwake_millers_ford_lead"] = True
                self.state.flags["road_patrol_writ"] = True
                enemies[0].current_hp = max(1, enemies[0].current_hp - 3)
                hero_bonus += 1
                self.add_clue("False roadwarden writs near Neverwinter point toward forged authority before Phandalin.")
                self.say("The writ seal copies Lord Neverember's road mark closely enough to fool scared teamsters, but not a calm look.")
        elif choice == 2:
            self.player_action("Scout the Neverwinter Wood verge for the ambush line.")
            if self.skill_check(self.state.player, "Survival", 12, context="to read the woodline before the Brand springs it"):
                self.state.flags["neverwinter_woodline_path"] = True
                self.state.flags["road_ambush_scouted"] = True
                self.apply_status(enemies[0], "surprised", 1, source="your woodline scout")
                hero_bonus += 1
                self.say("The ash line hides badly under pine needles. You find the waiting knife before it finds the wagon.")
        else:
            self.player_action("Organize the Helm's Hold pilgrims and refugee wagons into one guarded column.")
            if self.skill_check(self.state.player, "Persuasion", 12, context="to turn frightened travelers into an orderly column"):
                self.state.flags["neverwinter_pilgrims_guarded"] = True
                self.state.flags["blackwake_gallows_copse_lead"] = True
                hero_bonus += 1
                elira = self.find_companion("Elira Dawnmantle")
                if elira is not None:
                    self.adjust_companion_disposition(elira, 1, "you protected pilgrims before chasing the faster lead")
                self.say("The column tightens around the weakest carts, and a pilgrim points out where two wagons were taken south alive.")

        outcome = self.run_encounter(
            Encounter(
                title="High Road Milehouse Intercept",
                description="Ashen Brand cutters try to turn forged authority and pilgrim fear into another missing wagon.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=12,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The milehouse falls quiet, and the road south learns fear before your name.")
            return
        if outcome == "fled":
            self.state.flags["neverwinter_milehouse_bypassed"] = True
            self.say("You break away from the milehouse before the false roadwardens can pin the company in place.")
            return
        self.state.flags["neverwinter_milehouse_secured"] = True
        self.reward_party(xp=20, gold=5, reason="securing the High Road milehouse")
        self.add_journal("You secured a Neverwinter-side milehouse and chose how the road south would open.")

    def handle_neverwinter_signal_cairn(self) -> None:
        assert self.state is not None
        if self.state.flags.get("neverwinter_signal_cairn_seen"):
            return
        self.state.flags["neverwinter_signal_cairn_seen"] = True
        self.banner("Neverwinter Wood Signal Cairn")
        self.say(
            "A little farther south, the road bends past an old signal cairn on the Neverwinter Wood side of the ditch. "
            "Its stones are older than the new roadwarden paint, and someone has packed the top with green pine, lamp oil, "
            "and a strip of ash-black cloth waiting for a match.",
            typed=True,
        )
        enemies = [self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold"))]
        if self.act1_party_size() >= 3:
            enemies.append(create_enemy("bandit_archer"))
        else:
            enemies[0].current_hp = enemies[0].max_hp = 6
        hero_bonus = 0
        choice = self.scenario_choice(
            "How do you handle the signal cairn?",
            [
                self.skill_tag("STEALTH", self.action_option("Take the firekeeper quietly before the signal rises.")),
                self.skill_tag("SURVIVAL", self.action_option("Spoil the fuel and read where the watchers came from.")),
                self.skill_tag("ARCANA", self.action_option("Check the ash-cloth for a magical or alchemical trigger.")),
            ],
            allow_meta=False,
        )
        if choice == 1:
            self.player_action("Take the firekeeper quietly before the signal rises.")
            if self.skill_check(self.state.player, "Stealth", 12, context="to silence the signal watcher"):
                self.state.flags["road_reinforcement_signal_cut"] = True
                self.apply_status(enemies[0], "surprised", 1, source="your quiet approach")
                hero_bonus += 1
                self.say("The watcher turns too late, flint still in hand, and the signal never becomes more than intent.")
        elif choice == 2:
            self.player_action("Spoil the fuel and read where the watchers came from.")
            if self.skill_check(self.state.player, "Survival", 12, context="to spoil the cairn and follow the sign-cut trail"):
                self.state.flags["road_reinforcement_signal_cut"] = True
                self.state.flags["road_second_wave_trail_read"] = True
                hero_bonus += 1
                self.add_clue("A signal cairn south of Neverwinter was meant to call a harder Ashen Brand wave onto the High Road.")
                self.say("The fuel goes wet and useless, and the footprints point toward a second ambush pocket farther south.")
        else:
            self.player_action("Check the ash-cloth for a magical or alchemical trigger.")
            if self.skill_check(self.state.player, "Arcana", 12, context="to disarm the ash-cloth flash trigger"):
                self.state.flags["road_reinforcement_signal_cut"] = True
                self.state.flags["road_ash_signal_understood"] = True
                enemies[0].current_hp = max(1, enemies[0].current_hp - 2)
                hero_bonus += 1
                self.say("The cloth is treated to flare high and dirty. You pinch the trigger out before the Brand can paint the sky.")

        outcome = self.run_encounter(
            Encounter(
                title="Neverwinter Wood Signal Cairn",
                description="A hidden firekeeper tries to warn the High Road ambush before you can stop the signal.",
                enemies=enemies,
                allow_flee=True,
                allow_parley=True,
                parley_dc=12,
                hero_initiative_bonus=hero_bonus,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.handle_defeat("The signal fire climbs over the trees, and the High Road closes around you before Phandalin ever sees your face.")
            return
        if outcome == "fled":
            self.state.flags["neverwinter_signal_cairn_bypassed"] = True
            self.say("You leave the cairn burning low behind you, knowing someone farther south may have seen enough.")
            return
        self.state.flags["neverwinter_signal_cairn_cleared"] = True
        self.reward_party(xp=15, gold=4, reason="silencing the Neverwinter Wood signal cairn")
        self.add_journal("You found and broke a signal cairn meant to harden the High Road ambush.")

    def handle_neverwinter_departure_fork(self) -> None:
        assert self.state is not None
        if not self.state.flags.get("early_companion_recruited"):
            self.offer_early_companion()
        self.handle_neverwinter_tymora_shrine()
        if self.state is None or self.state.current_scene != "neverwinter_briefing":
            return
        self.handle_neverwinter_high_road_milehouse()
        if self.state is None or self.state.current_scene != "neverwinter_briefing":
            return
        self.handle_neverwinter_signal_cairn()
        if self.state is None or self.state.current_scene != "neverwinter_briefing":
            return
        self.add_journal("Mira Thann sent you south with a writ for Phandalin's steward.")

        while True:
            self.banner("Leaving Neverwinter")
            self.say(
                "The south road opens beyond the last city stones, but smoke smears the river cut to the east. "
                "A panicked wagon team hammers past with a charred toll seal hanging from the harness.",
                typed=True,
            )
            choice = self.scenario_choice(
                "Which route do you take?",
                [
                    self.action_option("Take the direct south road toward Phandalin."),
                    self.action_option("Investigate the smoke and caravan panic near the river cut."),
                    self.skill_tag("BACKTRACK", self.action_option("Circle back long enough to gather one more rumor in Neverwinter.")),
                ],
                allow_meta=False,
            )
            if choice == 1:
                self.player_action("Take the direct south road toward Phandalin.")
                self.travel_to_act1_node("high_road_ambush")
                return
            if choice == 2:
                self.player_action("Investigate the smoke and caravan panic near the river cut.")
                self.state.flags["blackwake_started"] = True
                self.state.flags["blackwake_return_destination"] = "undecided"
                self.grant_quest(
                    "trace_blackwake_cell",
                    note="Smoke outside Neverwinter points toward Blackwake Crossing before the wider High Road opens.",
                )
                self.add_journal("You turned off toward Blackwake Crossing to trace smoke, forged toll seals, and missing caravans.")
                self.travel_to_act1_node("blackwake_crossing")
                return

            self.player_action("Circle back long enough to gather one more rumor in Neverwinter.")
            if not self.state.flags.get("blackwake_neverwinter_rumor"):
                self.state.flags["blackwake_neverwinter_rumor"] = True
                self.add_clue(
                    "A Neverwinter drover says forged river-cut inspections are bleeding southbound caravans before they ever reach the High Road."
                )
                self.say(
                    "A drover near the north gate swears the missing wagons were waved aside by men carrying good-looking papers and bad patience."
                )
            else:
                self.say("The rumor loop has gone thin. The smoke east of the road is still the only fresh lead.")
            self.state.current_scene = "neverwinter_briefing"
            return

    def offer_early_companion(self) -> None:
        assert self.state is not None
        if self.state.flags.get("early_companion_recruited"):
            self.say("Mira has already assigned someone to your company for the ride south.")
            return
        self.speaker(
            "Mira Thann",
            "You are not riding into this alone. Choose the road-shield you want beside you: Kaelis for eyes in the brush, or Rhogar for a sworn lineholder.",
        )
        options = [
            self.action_option("Send Kaelis Starling, a ranger scout, with me."),
            self.action_option("Rhogar Valeguard, a paladin caravan-guard, sounds right for this road."),
        ]
        choice = self.scenario_choice(
            "Mira glances across the tavern and taps two names on the contract roster.",
            options,
            allow_meta=False,
        )
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            self.recruit_companion(create_kaelis_starling())
            self.state.flags["early_companion_recruited"] = "Kaelis Starling"
            self.say("Kaelis checks the fletching on an arrow, nods once, and agrees to ride with you.")
        else:
            self.recruit_companion(create_rhogar_valeguard())
            self.state.flags["early_companion_recruited"] = "Rhogar Valeguard"
            self.say("Rhogar lifts his shield, swears to see the road cleared, and joins your company.")

    def liars_circle_branch_available(self) -> bool:
        assert self.state is not None
        if not self.state.flags.get("liars_circle_branch_available"):
            return False
        return not (
            self.state.flags.get("liars_circle_locked")
            or self.state.flags.get("liars_circle_solved")
            or self.state.flags.get("liars_circle_failed")
        )

    def discover_liars_circle_branch(self) -> None:
        assert self.state is not None
        if self.state.flags.get("liars_circle_branch_discovered"):
            return
        self.state.flags["liars_circle_branch_discovered"] = True
        self.state.flags["liars_circle_branch_available"] = True
        self.say(
            "Past the broken ambush wagon, a deer track slips west into thorn and old stone. Four weathered shapes wait there "
            "in a clearing just far enough from the road to feel deliberate."
        )
        self.add_clue("A side trail near the High Road ambush leads to a circle of four talking statues.")
        self.add_journal("A wilderness side trail from the High Road leads to a statue puzzle called Liar's Circle.")

    def high_road_tollstones_branch_available(self) -> bool:
        assert self.state is not None
        return bool(self.state.flags.get("high_road_tollstones_branch_available")) and not bool(
            self.state.flags.get("high_road_tollstones_resolved")
        )

    def discover_high_road_tollstones_branch(self) -> None:
        assert self.state is not None
        if self.state.flags.get("high_road_tollstones_branch_discovered"):
            return
        self.state.flags["high_road_tollstones_branch_discovered"] = True
        self.state.flags["high_road_tollstones_branch_available"] = True
        self.say(
            "Beyond the wagon wreck, a second mark catches your eye: fresh black paint on a broken roadwarden milemarker, "
            "laid too neatly to be weather or accident."
        )
        self.add_clue("A broken High Road milemarker still carries fresh false-roadwarden paint.")
        self.add_journal("A broken milemarker near the High Road ambush points to another false toll operation.")

    def discover_high_road_side_branches(self) -> None:
        self.discover_liars_circle_branch()
        self.discover_high_road_tollstones_branch()

    def scene_high_road_liars_circle(self) -> None:
        assert self.state is not None
        self.banner("Liar's Circle")
        self.state.flags["liars_circle_seen"] = True
        self.say(
            "The trail opens into a small clearing where four stone statues stand in a ring: Knight, Priest, Thief, and King. "
            "Their carved eyes point inward, as if the answer has been standing between them for years.",
            typed=True,
        )
        self.say('A cracked plaque reads: "Exactly one of us speaks the truth. The others always lie."')
        if self.state.flags.get("liars_circle_locked"):
            self.say("The statues are locked in their chosen silence now. Whatever judgment they made will not be remade today.")
            self.travel_to_act1_node(
                "phandalin_hub",
                transition_text="You return to the High Road and continue toward Phandalin.",
            )
            return

        statue_lines = {
            "knight": ("Knight", "If the Priest is lying, then the King is telling the truth."),
            "priest": ("Priest", "Exactly one of the Knight or the King is telling the truth."),
            "thief": ("Thief", "Exactly one of the Priest or I is telling the truth."),
            "king": ("King", "The Priest is lying if and only if I am telling the truth."),
        }
        inspect_options = [
            ("knight", self.action_option("Inspect the Knight statue.")),
            ("priest", self.action_option("Inspect the Priest statue.")),
            ("thief", self.action_option("Inspect the Thief statue.")),
            ("king", self.action_option("Inspect the King statue.")),
            ("answer", self.skill_tag("LOGIC", self.action_option("Name the only truthful statue."))),
            ("leave", self.action_option("Leave the circle unresolved.")),
        ]
        while True:
            choice = self.scenario_choice(
                "What do you do in Liar's Circle?",
                [text for _, text in inspect_options],
                allow_meta=False,
            )
            selection_key, selection_text = inspect_options[choice - 1]
            if selection_key in statue_lines:
                self.player_choice_output(selection_text)
                speaker_name, line = statue_lines[selection_key]
                self.speaker(speaker_name, line)
                self.state.flags[f"liars_circle_inspected_{selection_key}"] = True
                continue
            if selection_key == "answer":
                self.player_choice_output(selection_text)
                answer_options = [
                    ("knight", self.quoted_option("KNIGHT", "The Knight tells the truth.")),
                    ("priest", self.quoted_option("PRIEST", "The Priest tells the truth.")),
                    ("thief", self.quoted_option("THIEF", "The Thief tells the truth.")),
                    ("king", self.quoted_option("KING", "The King tells the truth.")),
                    ("back", self.action_option("Step back and keep thinking.")),
                ]
                answer_choice = self.scenario_choice(
                    "Which statue is the only truthful one?",
                    [text for _, text in answer_options],
                    allow_meta=False,
                )
                answer_key, answer_text = answer_options[answer_choice - 1]
                if answer_key == "back":
                    self.player_choice_output(answer_text)
                    continue
                self.resolve_liars_circle_answer(answer_key, answer_text)
                break
            self.player_choice_output(selection_text)
            self.say("You leave the four statues arguing with the wind and follow the trail back to the High Road.")
            break

        self.travel_to_act1_node(
            "phandalin_hub",
            transition_text="You return to the High Road and continue toward Phandalin.",
        )

    def resolve_liars_circle_answer(self, answer_key: str, answer_text: str) -> None:
        assert self.state is not None
        self.player_choice_output(answer_text)
        self.state.flags["liars_circle_locked"] = True
        self.state.flags["liars_circle_branch_available"] = False
        self.state.flags["liars_circle_answer"] = answer_key
        if answer_key == "thief":
            self.state.flags["liars_circle_solved"] = True
            self.speaker("Thief", "Finally. Someone heard the shape of the lie instead of the polish on the crown.")
            self.say("The Thief statue bows with a scrape of old stone, and the circle exhales like a held secret.")
            self.apply_liars_blessing()
            return
        self.state.flags["liars_circle_failed"] = True
        self.speaker("King", "A confident answer is still an answer.")
        self.say("The ring snaps shut with a sound like a lock turning under your tongue.")
        self.apply_liars_curse()

    def scene_high_road_false_tollstones(self) -> None:
        assert self.state is not None
        self.banner("False Tollstones")
        self.state.flags["high_road_tollstones_seen"] = True
        self.say(
            "The broken milemarker stands beside a narrow service path, its old roadwarden notches painted over with "
            "Ashen Brand ash-black lines. Two nervous spotters wait in the scrub with a ledger, a lockbox, and the wrong kind of confidence.",
            typed=True,
        )
        if self.state.flags.get("high_road_tollstones_resolved"):
            self.say("The false toll is already broken. Only trampled brush and a scraped-clean milemarker remain.")
            self.travel_to_act1_node(
                "phandalin_hub",
                transition_text="You leave the milemarker behind and follow the High Road south.",
            )
            return

        has_blessing = self.has_story_skill_modifier(self.state.player, self.LIARS_BLESSING_MODIFIER_ID)
        if has_blessing:
            self.say("Liar's Blessing warms behind your teeth. The false paint almost seems to arrange itself into a passphrase.")

        options: list[tuple[str, str]] = []
        if has_blessing:
            options.append(
                (
                    "blessing",
                    self.skill_tag(
                        "LIAR'S BLESSING",
                        self.action_option("Speak the lie the false tollkeepers expect to hear."),
                    ),
                )
            )
        options.extend(
            [
                ("deception", self.skill_tag("DECEPTION", self.action_option("Bluff as an Ashen Brand courier."))),
                ("persuasion", self.skill_tag("PERSUASION", self.action_option("Offer the spotters a cleaner way out."))),
                ("leave", self.action_option("Leave the milemarker and stay on the main road.")),
            ]
        )
        choice = self.scenario_choice("How do you handle the false toll?", [text for _, text in options], allow_meta=False)
        selection_key, selection_text = options[choice - 1]
        if selection_key == "leave":
            self.player_choice_output(selection_text)
            self.say("You mark the painted stone for later and keep the party moving before the spotters find their nerve.")
            self.travel_to_act1_node(
                "phandalin_hub",
                transition_text="You leave the milemarker behind and follow the High Road south.",
            )
            return

        self.player_choice_output(selection_text)
        if selection_key == "blessing":
            self.say(
                "You give them a courier's lie with a thief-statue's perfect angle. The ledger opens before either spotter realizes "
                "they never asked for proof."
            )
            self.resolve_high_road_tollstones(success=True, method="blessing")
        elif selection_key == "deception":
            dc = 12 if has_blessing else 14
            success = self.skill_check(
                self.state.player,
                "Deception",
                dc,
                context="to pass as a courier collecting the false toll ledger",
            )
            self.resolve_high_road_tollstones(success=success, method="deception")
        else:
            dc = 11 if has_blessing else 13
            success = self.skill_check(
                self.state.player,
                "Persuasion",
                dc,
                context="to convince the spotters that running now is wiser than dying loyal",
            )
            self.resolve_high_road_tollstones(success=success, method="persuasion")

        self.travel_to_act1_node(
            "phandalin_hub",
            transition_text="You leave the milemarker behind and follow the High Road south.",
        )

    def resolve_high_road_tollstones(self, *, success: bool, method: str) -> None:
        assert self.state is not None
        self.state.flags["high_road_tollstones_resolved"] = True
        self.state.flags["high_road_tollstones_branch_available"] = False
        self.state.flags["high_road_tollstones_resolution"] = method if success else "failed"
        if not success:
            self.state.flags["high_road_tollstones_spotters_scattered"] = True
            self.apply_status(self.state.player, "reeling", 1, source="a false toll scramble")
            self.say("The spotters panic, scatter the ledger leaves into the brush, and leave you with only smoke, bootprints, and a foul mood.")
            self.add_journal("The false toll at the broken milemarker scattered before you could secure its ledger.")
            return

        self.state.flags["high_road_tollstones_ledger_taken"] = True
        self.add_inventory_item("antitoxin_vial", 1, source="the false toll lockbox")
        if method == "blessing":
            self.state.flags["high_road_tollstones_blessing_used"] = True
            self.state.flags["high_road_tollstones_passphrase_known"] = True
            self.say(
                "The lockbox yields a vial of antitoxin, a neat stack of toll coins, and a passphrase keyed to Ashen Brand patrols farther south."
            )
            self.add_clue("Liar's Blessing exposed an Ashen Brand passphrase from the false tollstone ledger.")
            self.reward_party(xp=25, gold=16, reason="turning Liar's Blessing against the false tollstones")
            self.add_journal("Liar's Blessing cracked the false tollstone operation and revealed an Ashen Brand passphrase.")
        elif method == "persuasion":
            self.state.flags["high_road_tollstones_contact_spared"] = True
            self.say("One spotter drops the ledger and runs. The other leaves the lockbox behind after whispering where the next Brand patrol listens.")
            self.add_clue("A frightened tollstone spotter named a southern Ashen Brand listening post.")
            self.reward_party(xp=20, gold=10, reason="breaking the false tollstones without bloodshed")
            self.add_journal("You talked the false tollstone spotters into abandoning their post.")
        else:
            self.say("Your bluff opens the ledger long enough to lift the lockbox and copy the next patrol mark before the spotters bolt.")
            self.add_clue("The false tollstone ledger names a southern Ashen Brand patrol mark.")
            self.reward_party(xp=20, gold=12, reason="bluffing through the false tollstones")
            self.add_journal("You bluffed through the false tollstone post and took its ledger mark.")

    def scene_road_ambush(self) -> None:
        assert self.state is not None
        self._sync_map_state_with_scene(force_node_id="high_road_ambush")
        self.banner("High Road")
        if self.state.flags.get("road_ambush_cleared") or self.state.flags.get("phandalin_arrived"):
            if self.state.flags.get("road_ambush_cleared"):
                self.discover_high_road_side_branches()
            self.render_act1_overworld_map(force=True)
            self.say(
                "The ambush site has gone quiet: ash-dark wagon ribs, old hoof churn, and the track south toward Phandalin "
                "all sit under a wind that knows the worst of this fight already passed."
            )
            options: list[tuple[str, str]] = [
                ("south", self.action_option("Follow the High Road back to Phandalin.")),
            ]
            backtrack_node = self.peek_act1_overworld_backtrack_node()
            if backtrack_node is not None:
                options.append(("backtrack", self.skill_tag("BACKTRACK", self.action_option(f"Backtrack to {backtrack_node.title}"))))
            if self.liars_circle_branch_available():
                options.append(
                    (
                        "liars_circle",
                        self.skill_tag("PUZZLE", self.action_option("Follow the overgrown statue trail into the wilderness.")),
                    )
                )
            if self.high_road_tollstones_branch_available():
                options.append(
                    (
                        "tollstones",
                        self.skill_tag("PARLEY", self.action_option("Investigate the broken roadwarden milemarker.")),
                    )
                )
            choice = self.scenario_choice("Where do you go from the High Road?", [text for _, text in options], allow_meta=False)
            selection_key, _ = options[choice - 1]
            if selection_key == "backtrack":
                if not self.backtrack_act1_overworld_node():
                    self.say("There is no familiar road behind you to backtrack right now.")
                    return
                return
            if selection_key == "liars_circle":
                self.player_action("Follow the overgrown statue trail into the wilderness.")
                self.travel_to_act1_node(
                    "liars_circle",
                    transition_text="You follow the thorn track away from the road until four old statues come into view.",
                )
                return
            if selection_key == "tollstones":
                self.player_action("Investigate the broken roadwarden milemarker.")
                self.travel_to_act1_node(
                    "false_tollstones",
                    transition_text="You follow the paint-scarred markers to a broken roadwarden stone and a waiting false toll.",
                )
                return
            self.travel_to_act1_node(
                "phandalin_hub",
                transition_text="You turn south again, letting the familiar road carry you back to Phandalin's lanterns.",
            )
            return
        self.say(
            "South of Neverwinter, smoke rises from a wrecked wagon just off the road. Goblin voices bark "
            "from the scrub while a chained ash wolf snaps at a wounded caravan guard trying to hold them back.",
            typed=True,
        )
        if (
            self.state.flags.get("blackwake_sereth_fate") == "escaped"
            and not self.state.flags.get("blackwake_sereth_road_note_seen")
        ):
            self.state.flags["blackwake_sereth_road_note_seen"] = True
            self.say(
                "A waxy scrap pinned inside the wagon bed bears a careful S.V. mark and one fresh instruction: "
                "move the useful cargo south before the crossing story spreads."
            )
            self.add_clue("A High Road note suggests Sereth Vane survived Blackwake and is still moving useful cargo south.")
            self.add_journal("Sereth Vane's initials surfaced on a High Road note after Blackwake.")
        if not self.state.flags.get("road_ambush_wave_one_cleared"):
            party_size = len(self.state.party_members())
            if party_size == 1:
                enemies = [
                    self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold")),
                    self.intro_pick_enemy(("wolf", "mireweb_spider")),
                ]
                enemies[0].current_hp = enemies[0].max_hp = 5
                enemies[1].current_hp = enemies[1].max_hp = 5
                hero_bonus = 2
                self.state.player.temp_hp = max(self.state.player.temp_hp, 6)
                self.apply_status(self.state.player, "blessed", 1, source="the guard's desperate cover")
                self.say(
                    "The wounded guard has already bloodied both threats and buys you a cleaner lane to enter the fight. "
                    "You begin with 6 temporary hit points and a brief surge of confidence."
                )
            elif party_size == 2:
                enemies = [
                    self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold")),
                    self.intro_pick_enemy(("wolf", "mireweb_spider")),
                ]
                enemies[1].current_hp = enemies[1].max_hp = 7
                hero_bonus = 1
                self.say("The wounded guard buys your smaller company a narrow opening before the ambush can fully close.")
            else:
                enemies = [
                    self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold")),
                    self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold", "briar_twig")),
                    self.intro_pick_enemy(("wolf", "mireweb_spider")),
                ]
                hero_bonus = 0
            hero_bonus += self.apply_scene_companion_support("road_ambush")
            parley_dc = 12 if party_size <= 2 else 13
            if self.state.flags.get("road_ambush_scouted") and enemies:
                hero_bonus += 1
                self.apply_status(enemies[0], "surprised", 1, source="the milehouse woodline scout")
                self.say("Because you read the woodline at the milehouse, the ambush starts with one raider looking the wrong way.")
            if self.state.flags.get("road_patrol_writ") and enemies:
                enemies[-1].current_hp = max(1, enemies[-1].current_hp - 2)
                parley_dc = max(10, parley_dc - 1)
                self.say("The exposed roadwarden writ makes the raiders hesitate before committing to another false seizure.")
            if self.state.flags.get("neverwinter_pilgrims_guarded"):
                hero_bonus += 1
                self.say("The Helm's Hold column keeps its nerve behind you, leaving fewer panicked bodies for the raiders to exploit.")
            if not self.state.flags.get("road_approach_chosen"):
                approach_options = [
                    ("athletics", self.skill_tag("ATHLETICS", self.action_option("Charge in before the guard falls."))),
                    ("stealth", self.skill_tag("STEALTH", self.action_option("Flank through the brush."))),
                    ("intimidation", self.skill_tag("INTIMIDATION", self.action_option("Break their nerve with a warning shout."))),
                ]
                backtrack_node = self.peek_act1_overworld_backtrack_node()
                if backtrack_node is not None:
                    approach_options.append(
                        (
                            "backtrack",
                            self.skill_tag(
                                "BACKTRACK",
                                self.action_option("Backtrack toward Neverwinter and reconsider the river smoke."),
                            ),
                        )
                    )
                choice = self.scenario_choice(
                    "How do you approach the ambush?",
                    [text for _, text in approach_options],
                    allow_meta=False,
                )
                selection_key, _ = approach_options[choice - 1]
                if selection_key == "backtrack":
                    if not self.backtrack_act1_overworld_node():
                        self.say("There is no familiar road behind you to backtrack right now.")
                    return
                self.state.flags["road_approach_chosen"] = True
                if selection_key == "athletics":
                    self.player_action("Charge in before the guard falls.")
                    success = self.skill_check(self.state.player, "Athletics", 12, context="to hit the ambush line like a battering ram")
                    if success:
                        self.apply_status(self.state.player, "emboldened", 2, source="a crashing opening charge")
                        if enemies:
                            self.apply_status(enemies[0], "prone", 1, source="your shoulder-first impact")
                        self.say("You smash into the raiders hard enough to break their shape before the melee is even set.")
                        hero_bonus += 2
                    else:
                        self.apply_status(self.state.player, "reeling", 1, source="an overextended charge")
                        self.say("You still hit the fight fast, but the first impact jars you off balance instead of breaking the line.")
                elif selection_key == "stealth":
                    self.player_action("Flank through the brush.")
                    success = self.skill_check(self.state.player, "Stealth", 12, context="to slip through the brush")
                    if success:
                        enemies[0].current_hp = max(1, enemies[0].current_hp - 4)
                        self.apply_status(enemies[0], "surprised", 1, source="your hidden approach")
                        hero_bonus += 2
                        self.say("You strike from cover before the goblins fully understand what hit them.")
                    else:
                        self.apply_status(self.state.player, "reeling", 1, source="getting caught in the open")
                        self.say("A snapped branch gives you away, and the goblins whirl toward you.")
                else:
                    self.player_action("Break their nerve with a warning shout.")
                    success = self.skill_check(self.state.player, "Intimidation", 12, context="to rattle the raiders")
                    if success:
                        enemies[-1].current_hp = max(1, enemies[-1].current_hp - 3)
                        self.apply_status(enemies[-1], "frightened", 2, source="your warning roar")
                        self.say("The wolf hesitates just long enough for the guard to pull free and draw breath.")
                    else:
                        for enemy in enemies:
                            if enemy.is_conscious():
                                self.apply_status(enemy, "emboldened", 1, source="seeing the bluff fail")
                        self.say("The goblins only cackle harder and close in.")

            outcome = self.run_encounter(
                Encounter(
                    title="Roadside Ambush: First Wave",
                    description="Roadside raiders and a hunting beast rush the ruined wagon.",
                    enemies=enemies,
                    allow_flee=True,
                    allow_parley=True,
                    parley_dc=parley_dc,
                    hero_initiative_bonus=hero_bonus,
                    allow_post_combat_random_encounter=False,
                )
            )
            if outcome == "defeat":
                self.handle_defeat("The High Road falls silent around the wreckage.")
                return
            if outcome == "fled":
                self.say("You circle wide, catch your breath, and try the road again.")
                return

            self.state.flags["road_ambush_wave_one_cleared"] = True
            self.add_clue("A scorched badge on the first High Road raiders marks the Ashen Brand.")
            self.reward_party(xp=15, gold=8, reason="breaking the first High Road wave")
            self.say(
                "Once the first rush breaks, the wounded guard introduces himself as Tolan Ironshield, a caravan veteran "
                "who was escorting ore and temple supplies to Phandalin."
            )
            self.speaker("Tolan Ironshield", "That was only the hook. I can still stand for the hammer blow if you'll have me.")
            options = [
                self.quoted_option("RECRUIT", "If you can stand, stand with us."),
                self.quoted_option("SAFE", "Get to the inn and recover. We'll talk there."),
            ]
            choice = self.scenario_choice("Tolan tightens the straps on his shield.", options, allow_meta=False)
            self.player_choice_output(options[choice - 1])
            if choice == 1:
                self.recruit_companion(create_tolan_ironshield())
                self.speaker(
                    "Tolan Ironshield",
                    "Good. Give me a minute to cinch the shield and I'll see you all the way to Phandalin.",
                )
            else:
                self.state.flags["tolan_waiting_at_inn"] = True
                self.add_journal("Tolan Ironshield is waiting at the Stonehill Inn if you need another shield arm.")
        else:
            self.say("The first ambush wave is already broken, but the road ahead still carries signal calls and running feet.")

        if self.state is None:
            return
        if not self.state.flags.get("road_ambush_wave_two_cleared"):
            self.say(
                "A horn coughs from the pines before the wagon dust can settle. The second wave comes in tighter: "
                "not scavengers this time, but the crew meant to punish anyone who survived the first rush.",
                typed=True,
            )
            party_size = len(self.state.party_members())
            if party_size <= 2:
                enemies = [create_enemy("bandit"), self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold"))]
                enemies[0].current_hp = min(enemies[0].current_hp, 9)
                enemies[0].max_hp = min(enemies[0].max_hp, 9)
                hero_bonus = 1
            elif party_size == 3:
                enemies = [create_enemy("ash_brand_enforcer"), self.intro_pick_enemy(("goblin_skirmisher", "cinder_kobold"))]
                hero_bonus = 0
            else:
                enemies = [
                    create_enemy("ash_brand_enforcer"),
                    create_enemy("bandit_archer"),
                    self.intro_pick_enemy(("cinder_kobold", "goblin_skirmisher", "wolf")),
                ]
                hero_bonus = 0
            if self.state.flags.get("road_reinforcement_signal_cut"):
                hero_bonus += 1
                if enemies:
                    self.apply_status(enemies[0], "reeling", 1, source="the broken signal cairn")
                self.say("Because the signal cairn went dark, the second wave arrives angry instead of coordinated.")
            if self.state.flags.get("road_second_wave_trail_read") and enemies:
                self.apply_status(enemies[-1], "surprised", 1, source="your read on the second-wave trail")
                self.say("You already read this approach at the cairn; the trailing raider walks straight into your angle.")

            outcome = self.run_encounter(
                Encounter(
                    title="High Road Second Wave",
                    description="A harder Ashen Brand reserve crew hits the wagon wreck after Tolan has a chance to join the line.",
                    enemies=enemies,
                    allow_flee=True,
                    allow_parley=True,
                    parley_dc=13 if party_size <= 2 else 14,
                    hero_initiative_bonus=hero_bonus,
                    allow_post_combat_random_encounter=False,
                )
            )
            if outcome == "defeat":
                self.handle_defeat("The second High Road wave breaks the caravan line before Phandalin can be warned.")
                return
            if outcome == "fled":
                self.say("You fall back from the second wave and will need to retake the road before Phandalin is safe.")
                return

            self.state.flags["road_ambush_wave_two_cleared"] = True
            self.add_clue("The harder High Road reserve was working under a hobgoblin sergeant tied to Ashfall Watch.")
            self.reward_party(xp=20, gold=7, reason="breaking the High Road reserve wave")

        self.state.flags["road_ambush_cleared"] = True
        self.discover_high_road_side_branches()
        self.travel_to_act1_node("phandalin_hub")
