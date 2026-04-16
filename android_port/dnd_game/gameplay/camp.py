from __future__ import annotations

from ..content import BACKGROUNDS, CLASSES, RACES, build_character
from ..items import get_item
from ..data.story.companions import COMPANION_PROFILES


class CampMixin:
    def open_camp_menu(self) -> None:
        assert self.state is not None
        self.banner("Camp")
        self.say(
            "Canvas, bedrolls, cookfire smoke, and the impossible magic mirror make camp the one place on the road "
            "where the party can breathe, reorganize, and speak honestly."
        )
        while True:
            dead_allies = self.dead_allies_in_company()
            revivify_ready = bool(dead_allies)
            revivify_text = (
                "Use Scroll of Revivify on a dead ally"
                if self.state.inventory.get("scroll_revivify", 0) > 0
                else "Use Scroll of Revivify on a dead ally (need one)"
            )
            options = [
                "Review the active party",
                "Review the full roster",
                "View character sheets",
                "Talk to a companion",
                "Manage the active party",
                "View journal",
                "View inventory",
                "Manage inventory",
                "Manage equipment",
                "Take a long rest",
                "Speak to the magic mirror (100 gp)",
            ]
            if revivify_ready:
                options.append(revivify_text)
            options.append("Break camp")
            choice = self.choose(
                "How do you spend this stop at camp?",
                options,
                allow_meta=False,
            )
            if choice == 1:
                self.show_party()
            elif choice == 2:
                self.show_full_roster()
            elif choice == 3:
                self.show_character_sheets()
            elif choice == 4:
                self.talk_to_companion()
            elif choice == 5:
                self.manage_party_roster()
            elif choice == 6:
                self.show_journal()
            elif choice == 7:
                self.show_inventory()
            elif choice == 8:
                self.manage_inventory()
            elif choice == 9:
                self.manage_equipment()
            elif choice == 10:
                self.apply_scene_companion_support("camp_rest")
                self.long_rest()
            elif choice == 11:
                self.visit_magic_mirror()
            elif revivify_ready and choice == 12:
                self.use_scroll_of_revivify()
            else:
                self.say("The campfire is banked, straps are tightened, and the road calls again.")
                return

    def dead_allies_in_company(self) -> list:
        assert self.state is not None
        return [companion for companion in self.state.all_companions() if companion.dead]

    def use_scroll_of_revivify(self) -> bool:
        assert self.state is not None
        dead_allies = self.dead_allies_in_company()
        if not dead_allies:
            self.say("No fallen ally in camp can be reached by revivify right now.")
            return False
        if self.state.inventory.get("scroll_revivify", 0) <= 0:
            self.say("You need a Scroll of Revivify in the shared inventory before you can attempt the rite.")
            return False
        choice = self.choose(
            "Choose who you restore with the scroll.",
            [self.companion_status_line(companion) for companion in dead_allies] + ["Back"],
            allow_meta=False,
        )
        if choice == len(dead_allies) + 1:
            return False
        target = dead_allies[choice - 1]
        if not self.remove_inventory_item("scroll_revivify"):
            self.say("The scroll is no longer in the shared inventory.")
            return False
        item = get_item("scroll_revivify")
        target.dead = False
        target.current_hp = min(target.max_hp, max(1, item.revive_hp))
        target.stable = False
        target.death_successes = 0
        target.death_failures = 0
        target.temp_hp = 0
        target.conditions.clear()
        self.say(f"The scroll burns down in silver ash, and {target.name} returns to life at {target.current_hp} HP.")
        self.add_journal(f"{target.name} was restored to life at camp with a Scroll of Revivify.")
        return True

    def show_full_roster(self) -> None:
        assert self.state is not None
        self.banner("Company Roster")
        self.say(f"Active party limit: {self.active_companion_limit() + 1} total, including you.")
        self.output_fn(f"- {self.state.player.name}: Player character | Level {self.state.player.level}")
        for companion in self.state.all_companions():
            self.output_fn(f"- {self.companion_status_line(companion)}")

    def manage_party_roster(self) -> None:
        assert self.state is not None
        while True:
            options = ["Send an active companion to camp"]
            if self.state.camp_companions:
                options.append("Call a camp companion into the active party")
            options.append("Back")
            choice = self.choose("Manage who travels in the active party.", options, allow_meta=False)
            if choice == 1:
                active = list(self.state.companions)
                if not active:
                    self.say("No companions are currently in the active party.")
                    continue
                picked = self.choose_ally(active, prompt="Choose who returns to camp.")
                self.move_companion_to_camp(picked)
            elif len(options) == 3 and choice == 2:
                picked = self.choose_ally(self.state.camp_companions, prompt="Choose who joins the active party.")
                self.move_companion_to_party(picked)
            else:
                return

    def talk_to_companion(self) -> None:
        assert self.state is not None
        roster = self.state.all_companions()
        if not roster:
            self.say("No companions are with your wider company yet.")
            return
        companion = self.choose_ally(roster, prompt="Choose who you want to talk to at camp.")
        profile = COMPANION_PROFILES[companion.companion_id]
        self.banner(companion.name)
        self.say(profile["summary"])
        self.say(f"Relationship: {self.relationship_label_for(companion)} ({companion.disposition}).")
        if companion.disposition >= 6:
            self.speaker(companion.name, profile["great_dialogue"])
        if companion.disposition >= 9:
            self.speaker(companion.name, profile["exceptional_dialogue"])
        while True:
            talked_topics = set(companion.bond_flags.get("talked_topics", []))
            options: list[tuple[str, str]] = []
            for topic in profile["camp_topics"]:
                prefix = "" if topic["id"] not in talked_topics else "(Already discussed) "
                options.append((topic["id"], prefix + topic["prompt"]))
            options.append(("view", self.action_option("Ask how they see you now.")))
            options.append(("leave", self.action_option("Return to the campfire.")))
            choice = self.choose(f"What do you say to {companion.name}?", [text for _, text in options], allow_meta=False)
            topic_id, _ = options[choice - 1]
            if topic_id == "view":
                self.describe_companion_relationship(companion)
                continue
            if topic_id == "leave":
                return
            topic = next(entry for entry in profile["camp_topics"] if entry["id"] == topic_id)
            self.player_choice_output(topic["prompt"])
            self.speaker(companion.name, topic["response"])
            if topic_id not in talked_topics:
                companion.bond_flags.setdefault("talked_topics", []).append(topic_id)
                self.adjust_companion_disposition(companion, int(topic["delta"]), reason=f"talking with {companion.name}")
                if companion not in self.state.all_companions():
                    return
            else:
                self.say(f"{companion.name} has already shared most of what they mean to on that subject.")

    def describe_companion_relationship(self, companion) -> None:
        label = self.relationship_label_for(companion)
        if label == "Exceptional":
            self.say(f"{companion.name} trusts you completely and speaks as if your futures are tied together.")
        elif label == "Great":
            self.say(f"{companion.name} trusts your judgment and volunteers more than they hide.")
        elif label == "Good":
            self.say(f"{companion.name} is warming to you and increasingly willing to confide in you.")
        elif label == "Bad":
            self.say(f"{companion.name} is frustrated and keeping emotional distance.")
        elif label == "Terrible":
            self.say(f"{companion.name} has almost no trust left to give.")
        else:
            self.say(f"{companion.name} is still measuring you carefully.")

    def visit_magic_mirror(self) -> None:
        assert self.state is not None
        if self.state.gold < 100:
            self.say("The mirror's silver frame hums once, then falls quiet. You need 100 gp for a full respec.")
            return
        self.say(
            "The magic mirror shows not your reflection, but a dozen possible versions of the life you might have led."
        )
        if not self.confirm("Spend 100 gp to fully respec your character?"):
            return
        previous_level = self.state.player.level
        previous_name = self.state.player.name
        self.state.gold -= 100
        race = self.choose_named_option("Choose a race", RACES)
        class_name = self.choose_named_option("Choose a class", CLASSES)
        background = self.choose_named_option("Choose a background", BACKGROUNDS)
        base_scores = self.choose_ability_scores()
        class_skills = self.choose_class_skills(race, class_name, background)
        expertise: list[str] = []
        if class_name == "Rogue":
            expertise = self.choose_expertise(race, background, class_skills)
        rebuilt = build_character(
            name=previous_name,
            race=race,
            class_name=class_name,
            background=background,
            base_ability_scores=base_scores,
            class_skill_choices=class_skills,
            expertise_choices=expertise,
            inventory={},
        )
        rebuilt.inventory.clear()
        self.state.player = rebuilt
        self.ensure_state_integrity()
        for next_level in range(2, previous_level + 1):
            self.level_up_character(self.state.player, next_level)
        self.state.player.current_hp = self.state.player.max_hp
        self.add_journal(f"The camp mirror reshaped {previous_name}'s training and talents for 100 gp.")
        self.say(f"The mirror settles. {previous_name} steps away remade, still level {previous_level}.")
