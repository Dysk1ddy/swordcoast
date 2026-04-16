from __future__ import annotations

from ..content import create_enemy
from .encounter import Encounter


POST_COMBAT_RANDOM_ENCOUNTER_CHANCE = 0.65
POST_COMBAT_RANDOM_ENCOUNTERS: tuple[tuple[str, str, str], ...] = (
    ("locked_chest_under_ferns", "Locked Chest Under the Ferns", "random_encounter_locked_chest_under_ferns"),
    ("abandoned_cottage", "Abandoned Cottage", "random_encounter_abandoned_cottage"),
    ("bandit_toll_line", "Bandit Toll Line", "random_encounter_bandit_toll_line"),
    ("wounded_messenger", "Wounded Messenger", "random_encounter_wounded_messenger"),
    ("hunter_snare", "Hunter's Snare", "random_encounter_hunter_snare"),
    ("lone_wolf", "Lone Wolf at the Kill", "random_encounter_lone_wolf"),
    ("smuggler_cookfire", "Smuggler Cookfire", "random_encounter_smuggler_cookfire"),
    ("shrine_of_tymora", "Shrine of Tymora", "random_encounter_shrine_of_tymora"),
    ("half_sunk_satchel", "Half-Sunk Satchel", "random_encounter_half_sunk_satchel"),
    ("ruined_wayhouse", "Ruined Wayhouse", "random_encounter_ruined_wayhouse"),
    ("scavenger_cart", "Scavenger Cart", "random_encounter_scavenger_cart"),
    ("loose_flagstones", "Loose Flagstones", "random_encounter_loose_flagstones"),
    ("frightened_draft_horse", "Frightened Draft Horse", "random_encounter_frightened_draft_horse"),
    ("rain_barrel_cache", "Rain Barrel Cache", "random_encounter_rain_barrel_cache"),
    ("watchfire_embers", "Watchfire Embers", "random_encounter_watchfire_embers"),
    ("broken_milestone", "Broken Milestone", "random_encounter_broken_milestone"),
)


class RandomEncounterMixin:
    def post_combat_random_encounter_ids(self) -> list[str]:
        return [encounter_id for encounter_id, _, _ in POST_COMBAT_RANDOM_ENCOUNTERS]

    def random_encounter_intro(self, text: str) -> None:
        self.say(text, typed=True)

    def weighted_post_combat_random_encounter_pool(self) -> list[tuple[str, str, str]]:
        if self.state is None:
            return list(POST_COMBAT_RANDOM_ENCOUNTERS)
        seen = set(self.state.flags.get("random_encounters_seen", []))
        weighted: list[tuple[str, str, str]] = []
        for encounter in POST_COMBAT_RANDOM_ENCOUNTERS:
            encounter_id = encounter[0]
            weight = 1 if encounter_id in seen else 10
            weighted.extend([encounter] * weight)
        return weighted

    def maybe_run_post_combat_random_encounter(self, source_encounter: Encounter) -> None:
        if self.state is None or not getattr(source_encounter, "allow_post_combat_random_encounter", True):
            return
        if self.rng.random() > POST_COMBAT_RANDOM_ENCOUNTER_CHANCE:
            return
        encounter_id, _, _ = self.rng.choice(self.weighted_post_combat_random_encounter_pool())
        self.run_named_post_combat_random_encounter(encounter_id)

    def run_named_post_combat_random_encounter(self, encounter_id: str) -> None:
        if self.state is None:
            return
        for current_id, title, handler_name in POST_COMBAT_RANDOM_ENCOUNTERS:
            if current_id != encounter_id:
                continue
            seen = self.state.flags.setdefault("random_encounters_seen", [])
            if encounter_id not in seen:
                seen.append(encounter_id)
            self.banner(f"After the Battle: {title}")
            getattr(self, handler_name)()
            return
        raise ValueError(f"Unknown post-combat random encounter '{encounter_id}'.")

    def grant_random_encounter_rewards(
        self,
        *,
        reason: str,
        gold: int = 0,
        items: dict[str, int] | None = None,
    ) -> None:
        assert self.state is not None
        if gold > 0:
            self.state.gold += gold
            self.say(f"You secure {gold} gp from {reason}.")
            self.pause_for_loot_reveal()
        for item_id, quantity in (items or {}).items():
            added = self.add_inventory_item(item_id, quantity, source=reason)
            if added or quantity:
                self.pause_for_loot_reveal()

    def suffer_random_encounter_damage(self, target, amount: int, *, damage_type: str = "", source: str = "") -> int:
        if target.dead or target.current_hp <= 1:
            if source:
                self.say(source)
            return 0
        actual = min(max(1, amount), target.current_hp - 1)
        target.current_hp -= actual
        prefix = f"{source} " if source else ""
        typed = f" {damage_type}" if damage_type else ""
        self.say(f"{prefix}{self.style_name(target)} takes {self.style_damage(actual)}{typed} damage.")
        return actual

    def random_bandit_pair(self) -> list:
        assert self.state is not None
        enemies = [create_enemy("bandit")]
        if len(self.state.party_members()) >= 3:
            enemies.append(create_enemy("bandit_archer"))
        return enemies

    def random_goblin_pair(self) -> list:
        assert self.state is not None
        enemies = [create_enemy("goblin_skirmisher")]
        if len(self.state.party_members()) >= 3:
            enemies.append(create_enemy("goblin_skirmisher", name="Goblin Scavenger"))
        return enemies

    def resolve_random_encounter_fight(
        self,
        *,
        title: str,
        description: str,
        enemies: list,
        allow_parley: bool = True,
        parley_dc: int = 13,
        setback_text: str = "",
        flee_text: str = "",
    ) -> str:
        assert self.state is not None
        outcome = self.run_encounter(
            Encounter(
                title=title,
                description=description,
                enemies=enemies,
                allow_flee=True,
                allow_parley=allow_parley,
                parley_dc=parley_dc,
                allow_post_combat_random_encounter=False,
            )
        )
        if outcome == "defeat":
            self.recover_after_battle()
            gold_loss = min(self.state.gold, self.rng.randint(2, 8))
            if gold_loss > 0:
                self.state.gold -= gold_loss
                self.say(
                    setback_text
                    or f"The side skirmish leaves the party bloodied, and the victors strip away {gold_loss} gp before scattering."
                )
            else:
                self.say(setback_text or "The side skirmish leaves the party bloodied, but the attackers vanish before they can do worse.")
        elif outcome == "fled":
            self.say(flee_text or "You break away before the surprise clash can turn uglier.")
        return outcome

    def random_encounter_locked_chest_under_ferns(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "Fern fronds hide a traveler's chest tucked beneath a fallen marker stone, its lock still intact and its hinges only half-rusted."
        )
        options = [
            self.skill_tag("INVESTIGATION", self.action_option("Check the latch and seams for a hidden catch.")),
            self.skill_tag("SLEIGHT OF HAND", self.action_option("Work the lock open carefully.")),
            self.skill_tag("ATHLETICS", self.action_option("Wrench the lid open by force.")),
        ]
        choice = self.scenario_choice("How do you handle the chest?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Investigation", 12, context="to spot the trap before touching the chest"):
                self.grant_random_encounter_rewards(reason="the fern-hidden chest", gold=self.rng.randint(8, 14), items={"bread_round": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    damage_type="poison",
                    source="A spring needle pricks your hand before you can pull back.",
                )
        elif choice == 2:
            if self.skill_check(self.state.player, "Sleight of Hand", 15, context="to pick the travel lock quietly"):
                self.grant_random_encounter_rewards(
                    reason="the fern-hidden chest",
                    gold=self.rng.randint(10, 16),
                    items={"potion_healing": 1},
                )
            else:
                self.say("The tumblers click loud enough to rouse armed scavengers from the brush.")
                self.resolve_random_encounter_fight(
                    title="Chest Scavengers",
                    description="Bandits rush the chest the moment they hear the failed lockpick.",
                    enemies=self.random_bandit_pair(),
                    parley_dc=12,
                )
        else:
            if self.skill_check(self.state.player, "Athletics", 13, context="to break the warped lid open cleanly"):
                self.grant_random_encounter_rewards(reason="the broken chest", gold=self.rng.randint(6, 12), items={"goat_cheese": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    3,
                    source="The chest splinters apart and a jagged hinge snaps across your knuckles.",
                )

    def random_encounter_abandoned_cottage(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A soot-stained cottage slumps beside the trail, with one shutter hanging open and a cellar door that looks newer than the walls around it."
        )
        options = [
            self.skill_tag("PERCEPTION", self.action_option("Scout the windows and chimney before going near.")),
            self.quoted_option("PERSUASION", "Anyone inside can keep their roof if they answer plainly."),
            self.action_option("Shoulder the cellar door open and clear the place fast."),
        ]
        choice = self.scenario_choice("What do you do with the cottage?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Perception", 12, context="to read the cottage from the yard"):
                self.grant_random_encounter_rewards(reason="the cottage rafters", gold=4, items={"camp_stew_jar": 1, "bread_round": 1})
            else:
                self.say("A loose shutter bangs open, and the squatters inside answer with drawn steel.")
                self.resolve_random_encounter_fight(
                    title="Cottage Squatters",
                    description="Desperate scavengers rush out of the abandoned cottage with knives already in hand.",
                    enemies=self.random_goblin_pair(),
                )
        elif choice == 2:
            if self.skill_check(self.state.player, "Persuasion", 11, context="to promise safe passage to whoever is hiding inside"):
                self.grant_random_encounter_rewards(reason="the cottage table", gold=6, items={"goat_cheese": 1})
            else:
                self.say("The reply is a crossbow quarrel through the boards.")
                self.resolve_random_encounter_fight(
                    title="Panicked Holdouts",
                    description="A pair of frightened holdouts decide to shoot their way free.",
                    enemies=[create_enemy("bandit_archer")],
                    parley_dc=11,
                )
        else:
            self.resolve_random_encounter_fight(
                title="Cellar Door Rush",
                description="Your hard entry startles goblin scavengers into a frantic knife fight.",
                enemies=self.random_goblin_pair(),
                parley_dc=12,
            )

    def random_encounter_bandit_toll_line(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A rope strung across the road is tied to a rough sign promising 'safe passage' for a handful of coin, while voices wait just out of sight."
        )
        options = [
            self.action_option("Cut the rope and move on before the hidden collectors close in."),
            self.skill_tag("STEALTH", self.action_option("Slip around the line through the brush.")),
            self.quoted_option("INTIMIDATION", "Come out now or lose the hand that tied this rope."),
        ]
        choice = self.scenario_choice("How do you answer the toll line?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            self.say("You cut the rope and keep moving before the would-be collectors can gather their courage.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Stealth", 12, context="to skirt the toll line unseen"):
                self.grant_random_encounter_rewards(reason="the brush by the toll line", gold=5)
            else:
                self.say("A hidden bell twitches on the rope and the collectors come running.")
                self.resolve_random_encounter_fight(
                    title="Road Toll Collectors",
                    description="Bandits burst from the brush to defend their roadside racket.",
                    enemies=self.random_bandit_pair(),
                )
        else:
            if self.skill_check(self.state.player, "Intimidation", 13, context="to break the nerve of the hidden collectors"):
                self.grant_random_encounter_rewards(reason="the abandoned toll pouch", gold=self.rng.randint(5, 10))
            else:
                self.resolve_random_encounter_fight(
                    title="Toll Line Standoff",
                    description="The bluff fails, and the hidden collectors decide to rush you.",
                    enemies=self.random_bandit_pair(),
                )

    def random_encounter_wounded_messenger(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A messenger in torn livery lies behind a milepost with a split satchel, trying to hold one boot against a bleeding leg."
        )
        options = [
            self.skill_tag("MEDICINE", self.action_option("Bind the wound before asking questions.")),
            self.skill_tag("INVESTIGATION", self.action_option("Search the scattered satchel for whatever mattered enough to attack for.")),
            self.action_option("Leave the messenger with water and keep moving."),
        ]
        choice = self.scenario_choice("How do you deal with the messenger?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Medicine", 11, context="to stop the bleeding in time"):
                self.grant_random_encounter_rewards(reason="the grateful messenger", gold=9, items={"bread_round": 1})
                self.add_clue("A roadside messenger mentioned more Ashen Brand scouts probing side trails around Phandalin.")
            else:
                self.say("You slow the bleeding, but the messenger can only rasp thanks before passing out.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Investigation", 12, context="to gather the useful papers before the wind takes them"):
                self.grant_random_encounter_rewards(reason="the torn satchel", gold=7, items={"scroll_clarity": 1})
            else:
                self.say("You find little that still matters and lose time in the reeds.")
        else:
            self.say("You leave water within reach and let the road take the rest of the choice from you.")

    def random_encounter_hunter_snare(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A taut line glints between alder roots beside the road, with a snare knot drawn tight enough to catch a careless traveler by the ankle."
        )
        options = [
            self.skill_tag("PERCEPTION", self.action_option("Trace the snare and find the hidden anchor point.")),
            self.skill_tag("SURVIVAL", self.action_option("Follow the trapper's line back to wherever they stored their catch.")),
            self.action_option("Cut the snare and leave the setup ruined behind you."),
        ]
        choice = self.scenario_choice("What do you do with the snare?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Perception", 12, context="to read the snare before it snaps"):
                self.grant_random_encounter_rewards(reason="the trapper's blind", gold=5, items={"goat_cheese": 1, "bread_round": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    source="The line lashes your wrist when the knot lets go.",
                )
        elif choice == 2:
            if self.skill_check(self.state.player, "Survival", 12, context="to follow the hidden drag marks through the brush"):
                self.grant_random_encounter_rewards(reason="the trapper's blind", gold=6, items={"potion_healing": 1})
            else:
                self.say("The trail circles you right into the trapper's lookout.")
                self.resolve_random_encounter_fight(
                    title="Snare-Line Ambushers",
                    description="Bandit hunters rise from the brush when you follow their line too boldly.",
                    enemies=[create_enemy("bandit_archer"), create_enemy("bandit")],
                    parley_dc=12,
                )
        else:
            self.say("The cord parts and the trap goes slack, leaving the road one danger lighter.")

    def random_encounter_lone_wolf(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A lean ash-gray wolf crouches over a fresh carcass just off the trail, yellow eyes fixed on you while a torn purse glints beside the body."
        )
        options = [
            self.action_option("Back away and give the animal its ground."),
            self.skill_tag("SURVIVAL", self.action_option("Read the wolf's posture and edge toward the purse.")),
            self.skill_tag("INTIMIDATION", self.action_option("Drive the wolf off with noise and steel.")),
        ]
        choice = self.scenario_choice("How do you deal with the wolf?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            self.say("You leave the kill to the wolf and keep the road instead of tempting the wrong hunger.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Survival", 12, context="to move inside the wolf's comfort without triggering a rush"):
                self.grant_random_encounter_rewards(reason="the purse beside the carcass", gold=self.rng.randint(6, 11))
            else:
                self.resolve_random_encounter_fight(
                    title="Wolf on the Trail",
                    description="The wolf decides you're too close to its kill and lunges.",
                    enemies=[create_enemy("wolf")],
                    allow_parley=False,
                    parley_dc=99,
                )
        else:
            if self.skill_check(self.state.player, "Intimidation", 12, context="to break the wolf's nerve with a hard shout"):
                self.grant_random_encounter_rewards(reason="the purse beside the carcass", gold=self.rng.randint(7, 12))
            else:
                self.resolve_random_encounter_fight(
                    title="Cornered Wolf",
                    description="Your threat only convinces the wolf to charge before you can press the advantage.",
                    enemies=[create_enemy("wolf")],
                    allow_parley=False,
                    parley_dc=99,
                )

    def random_encounter_smuggler_cookfire(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A narrow plume of smoke rises from a hidden cookfire ahead, where half-packed bundles sit under a tarp and someone has been careful not to camp on the road itself."
        )
        options = [
            self.skill_tag("STEALTH", self.action_option("Circle wide and lift what you can before the campers notice.")),
            self.quoted_option("DECEPTION", "Riders are coming from Neverwinter. Run while you still can."),
            self.action_option("Leave the hidden camp alone."),
        ]
        choice = self.scenario_choice("How do you approach the hidden fire?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Stealth", 12, context="to reach the tarp without a snapped twig giving you away"):
                self.grant_random_encounter_rewards(reason="the smuggler tarp", gold=4, items={"potion_healing": 1})
            else:
                self.resolve_random_encounter_fight(
                    title="Smuggler Camp",
                    description="The hidden campers catch you in the act and come up armed.",
                    enemies=self.random_bandit_pair(),
                )
        elif choice == 2:
            if self.skill_check(self.state.player, "Deception", 12, context="to sell the story of riders on the road"):
                self.grant_random_encounter_rewards(reason="the abandoned cookfire", gold=7, items={"bread_round": 1})
            else:
                self.resolve_random_encounter_fight(
                    title="Smuggler Panic",
                    description="The campers spot the lie, snatch up their weapons, and rush the tree line.",
                    enemies=self.random_bandit_pair(),
                )
        else:
            self.say("You let the hidden camp keep its secrets and deny the road one more reason to bleed tonight.")

    def random_encounter_shrine_of_tymora(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A weathered roadside shrine to Tymora leans beneath a white-streaked oak, its tiny offering bowl still dry despite the last night's rain."
        )
        options = [
            self.skill_tag("RELIGION", self.action_option("Set the shrine right and offer a quick frontier prayer.")),
            self.action_option("Leave a single coin and move on."),
            self.skill_tag("ATHLETICS", self.action_option("Pry up the stones around the shrine base.")),
        ]
        choice = self.scenario_choice("How do you treat the shrine?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Religion", 11, context="to settle the shrine the way a proper caretaker would"):
                self.grant_random_encounter_rewards(reason="the shrine's hidden niche", items={"potion_healing": 1})
            else:
                self.say("The prayer steadies the moment, but the shrine yields nothing except silence.")
        elif choice == 2:
            if self.state.gold > 0:
                self.state.gold -= 1
                self.say("You leave 1 gp in the bowl and take the quiet blessing of moving on with a clean conscience.")
            else:
                self.say("You reach for a coin you do not have and settle for a respectful nod instead.")
        else:
            if self.skill_check(self.state.player, "Athletics", 13, context="to heave up the old base stones without collapse"):
                self.grant_random_encounter_rewards(reason="the shrine base", gold=6)
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    source="A loosened stone crushes down onto your boot before you can clear away.",
                )

    def random_encounter_half_sunk_satchel(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "At a muddy roadside ditch, a leather satchel is trapped beneath a sheet of runoff water while silver buckles flash below the surface."
        )
        options = [
            self.skill_tag("SURVIVAL", self.action_option("Read the current and pin the satchel before it slips downstream.")),
            self.skill_tag("ATHLETICS", self.action_option("Reach in and yank it free in one pull.")),
            self.action_option("Let the ditch keep it and stay dry."),
        ]
        choice = self.scenario_choice("What do you do with the satchel?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Survival", 11, context="to work with the current instead of against it"):
                self.grant_random_encounter_rewards(reason="the waterlogged satchel", gold=self.rng.randint(8, 13), items={"scroll_clarity": 1})
            else:
                self.say("The satchel slips deeper into the culvert before you can pin it.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Athletics", 12, context="to haul the satchel out before the bank gives way"):
                self.grant_random_encounter_rewards(reason="the waterlogged satchel", gold=self.rng.randint(6, 10), items={"bread_round": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    source="The bank collapses and sends you hard onto the stones.",
                )
        else:
            self.say("You leave the satchel to the ditch and keep the road under your feet.")

    def random_encounter_ruined_wayhouse(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "The shell of an old wayhouse stands with its roof gone and its front room open to the sky, but the cellar trapdoor has fresh scrape marks around it."
        )
        options = [
            self.skill_tag("PERCEPTION", self.action_option("Study the upper windows and the cellar lip before committing.")),
            self.quoted_option("PERSUASION", "Come out and we can all leave with less blood on the floor."),
            self.action_option("Drop through the trapdoor and take the space by force."),
        ]
        choice = self.scenario_choice("How do you approach the wayhouse?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Perception", 12, context="to catch the cellar glint before it catches you"):
                self.grant_random_encounter_rewards(reason="the wayhouse stash", gold=5, items={"goat_cheese": 1, "camp_stew_jar": 1})
            else:
                self.resolve_random_encounter_fight(
                    title="Wayhouse Scavengers",
                    description="Goblin scavengers rush the ladder the moment you show yourself at the opening.",
                    enemies=self.random_goblin_pair(),
                    parley_dc=11,
                )
        elif choice == 2:
            if self.skill_check(self.state.player, "Persuasion", 12, context="to convince the cellar squatters to trade space for safety"):
                self.grant_random_encounter_rewards(reason="the cellar handoff", gold=6, items={"bread_round": 1})
            else:
                self.resolve_random_encounter_fight(
                    title="Wayhouse Holdouts",
                    description="The hidden squatters answer your offer with a hard charge up the stairs.",
                    enemies=self.random_goblin_pair(),
                    parley_dc=11,
                )
        else:
            self.resolve_random_encounter_fight(
                title="Trapdoor Drop",
                description="You drop into the cellar before the hidden squatters can bolt, and the scramble turns violent fast.",
                enemies=self.random_goblin_pair(),
                parley_dc=11,
            )

    def random_encounter_scavenger_cart(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A broken handcart sits canted in the ditch with sacks spilling grain and one axle pin still jammed half through the wheel."
        )
        options = [
            self.skill_tag("ATHLETICS", self.action_option("Set the cart upright and see what was worth dragging.")),
            self.skill_tag("INVESTIGATION", self.action_option("Check the sacks and hidden panels before touching the axle.")),
            self.action_option("Keep walking before whoever lost it comes back."),
        ]
        choice = self.scenario_choice("How do you deal with the cart?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Athletics", 12, context="to right the cart without dumping the last salvageable sack"):
                self.grant_random_encounter_rewards(reason="the salvaged cart", gold=4, items={"bread_round": 2})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    source="The axle pin tears free and clips your shoulder on the way down.",
                )
        elif choice == 2:
            if self.skill_check(self.state.player, "Investigation", 12, context="to find the hidden compartment before the obvious grain sacks distract you"):
                self.grant_random_encounter_rewards(reason="the cart's false bottom", gold=8, items={"goat_cheese": 1})
            else:
                self.say("You linger too long and hear returning footsteps in the scrub.")
                self.resolve_random_encounter_fight(
                    title="Returning Scavengers",
                    description="A pair of scavengers comes running back to reclaim the broken cart.",
                    enemies=[create_enemy("bandit"), create_enemy("bandit_archer")],
                    parley_dc=12,
                )
        else:
            self.say("You leave the cart where it lies and keep your pace instead of your curiosity.")

    def random_encounter_loose_flagstones(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A patch of old flagstones peeks through the roadside mud, one slab sitting slightly higher than the rest as if something underneath has started to push back."
        )
        options = [
            self.skill_tag("INVESTIGATION", self.action_option("Test the seams and look for a deliberate cache.")),
            self.skill_tag("SLEIGHT OF HAND", self.action_option("Lift the edge carefully with a blade and cloth.")),
            self.action_option("Stamp the stones flat and deny anyone else the hiding place."),
        ]
        choice = self.scenario_choice("How do you handle the stones?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Investigation", 12, context="to tell cachework from ordinary road ruin"):
                self.grant_random_encounter_rewards(reason="the flagstone cache", gold=9, items={"scroll_mending_word": 1})
            else:
                self.say("The pattern still looks wrong, but you cannot make it yield before the light shifts.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Sleight of Hand", 12, context="to lift the stone without tipping the hidden vial beneath it"):
                self.grant_random_encounter_rewards(reason="the flagstone cache", gold=6, items={"potion_healing": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    damage_type="poison",
                    source="A brittle vial shatters under the stone and splashes your hand.",
                )
        else:
            self.say("You grind the raised stone back into the road and move on without learning what it once protected.")

    def random_encounter_frightened_draft_horse(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A lathered draft horse stands tangled in a snapped trace line beside the road, ears pinned back while a pack roll hangs half loose from its saddle."
        )
        options = [
            self.skill_tag("ANIMAL HANDLING", self.action_option("Quiet the horse and free the line carefully.")),
            self.skill_tag("SLEIGHT OF HAND", self.action_option("Work the pack roll loose without spooking the animal further.")),
            self.skill_tag("INTIMIDATION", self.action_option("Drive off whatever is lurking nearby before it bolts again.")),
        ]
        choice = self.scenario_choice("How do you handle the horse?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Animal Handling", 12, context="to settle the horse and work the line free"):
                self.grant_random_encounter_rewards(reason="the grateful beast's gear", gold=5, items={"bread_round": 1, "goat_cheese": 1})
            else:
                self.say("The horse tears free and leaves only mud and a few loose oats behind.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Sleight of Hand", 12, context="to free the pack roll before the horse jerks away"):
                self.grant_random_encounter_rewards(reason="the loosened pack roll", gold=6, items={"camp_stew_jar": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    source="The horse jerks sideways and the rolling pack catches you across the ribs.",
                )
        else:
            if self.skill_check(self.state.player, "Intimidation", 12, context="to blast the brush with enough force to scare off the watcher"):
                self.grant_random_encounter_rewards(reason="the dropped watcher pouch", gold=7)
            else:
                self.resolve_random_encounter_fight(
                    title="Brush Stalker",
                    description="A hungry ash wolf bursts from the brush instead of retreating from the shout.",
                    enemies=[create_enemy("wolf")],
                    allow_parley=False,
                    parley_dc=99,
                )

    def random_encounter_rain_barrel_cache(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "Behind a split rail fence, a rain barrel has been weighted down with stones, and the hollow clunk beneath the water says someone hid more than water inside it."
        )
        options = [
            self.skill_tag("INVESTIGATION", self.action_option("Probe the barrel bottom and find the false floor.")),
            self.skill_tag("ATHLETICS", self.action_option("Tip the whole barrel over and collect whatever drops out.")),
            self.action_option("Leave the barrel and let the owner keep their hiding spot."),
        ]
        choice = self.scenario_choice("What do you do with the barrel?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Investigation", 11, context="to feel out the false floor without dunking the goods"):
                self.grant_random_encounter_rewards(reason="the rain barrel cache", gold=7, items={"scroll_guardian_light": 1})
            else:
                self.say("Your fingers find the seam too late and the little cache shifts deeper into the muck.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Athletics", 12, context="to heave the barrel over before the fence gives out"):
                self.grant_random_encounter_rewards(reason="the rain barrel cache", gold=6, items={"potion_healing": 1})
            else:
                self.suffer_random_encounter_damage(
                    self.state.player,
                    2,
                    source="The barrel bursts against the fence and slams muddy boards into your shin.",
                )
        else:
            self.say("You let the fence, barrel, and secret beneath it keep their peace.")

    def random_encounter_watchfire_embers(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A watchfire has only just gone to embers beside the trail, with two bedroll hollows still warm and bootprints leading into the dark."
        )
        options = [
            self.skill_tag("PERCEPTION", self.action_option("Read the campsite before touching anything.")),
            self.skill_tag("STEALTH", self.action_option("Follow the freshest bootprints just far enough to find the stash.")),
            self.action_option("Kick dirt over the embers and deny the campers their return point."),
        ]
        choice = self.scenario_choice("How do you handle the cold camp?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "Perception", 12, context="to judge whether the campers left in panic or on purpose"):
                self.grant_random_encounter_rewards(reason="the abandoned watchfire", gold=5, items={"bread_round": 1, "goat_cheese": 1})
            else:
                self.say("The clues stay muddy and the camp yields little beyond smoke scent.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Stealth", 12, context="to track the bootprints without brushing the hidden sentry line"):
                self.grant_random_encounter_rewards(reason="the hidden bedroll stash", gold=8, items={"scroll_ember_ward": 1})
            else:
                self.resolve_random_encounter_fight(
                    title="Returning Campers",
                    description="The owners of the warm camp catch you on their back trail and come in fast.",
                    enemies=self.random_bandit_pair(),
                )
        else:
            self.say("The last glow dies under your boot, and the road keeps its next secret a little longer.")

    def random_encounter_broken_milestone(self) -> None:
        assert self.state is not None
        self.random_encounter_intro(
            "A shattered milestone lies in chunks across the roadside, and fresh pry marks show someone recently checked whether anything had ever been hidden inside it."
        )
        options = [
            self.skill_tag("HISTORY", self.action_option("Study the carving and look for the original mason's trick.")),
            self.skill_tag("ATHLETICS", self.action_option("Split the largest chunk and see if the smugglers missed anything.")),
            self.action_option("Roll the stone off the road and leave it at that."),
        ]
        choice = self.scenario_choice("How do you deal with the broken stone?", options, allow_meta=False)
        self.player_choice_output(options[choice - 1])
        if choice == 1:
            if self.skill_check(self.state.player, "History", 11, context="to recall how old road markers sometimes hid courier niches"):
                self.grant_random_encounter_rewards(reason="the milestone niche", gold=7, items={"scroll_battle_psalm": 1})
            else:
                self.say("You remember enough old roadcraft to know there was a trick here once, but not enough to reclaim it.")
        elif choice == 2:
            if self.skill_check(self.state.player, "Athletics", 12, context="to crack the stone along an old seam"):
                self.grant_random_encounter_rewards(reason="the milestone niche", gold=9)
            else:
                self.say("The stone cracks louder than expected, and scavengers answer the noise.")
                self.resolve_random_encounter_fight(
                    title="Milestone Scavengers",
                    description="Bandits rush in, convinced the broken stone is covering someone else's hidden cut.",
                    enemies=self.random_bandit_pair(),
                )
        else:
            self.say("You clear the road and leave the old marker's secrets where they fell.")
