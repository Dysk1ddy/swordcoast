from __future__ import annotations

from ..content import BACKGROUNDS, CLASSES, RACES, build_character
from ..items import get_item
from ..data.story.companions import COMPANION_PROFILES
from ..ui.colors import rich_style_name
from ..ui.rich_render import Columns, Group, Panel, Table, box


class CampMixin:
    def render_camp_overview(self) -> None:
        assert self.state is not None
        if not (
            callable(getattr(self, "should_use_rich_ui", None))
            and self.should_use_rich_ui()
            and Columns is not None
            and Group is not None
            and Panel is not None
            and Table is not None
            and box is not None
        ):
            return
        status = Table.grid(expand=True, padding=(0, 1))
        status.add_column(style=f"bold {rich_style_name('light_yellow')}", width=12)
        status.add_column(ratio=1)
        status.add_row("Gold", f"{self.state.gold} gp")
        status.add_row("Short rests", str(self.state.short_rests_remaining))
        status.add_row(
            "Carry",
            f"{self.current_inventory_weight():.1f}/{self.carrying_capacity()} lb",
        )
        status.add_row("Active party", str(len(self.state.party_members())))
        status.add_row("Camp roster", str(len(self.state.camp_companions)))

        active_party = Group(
            *(
                self.rich_from_ansi(
                    f"{member.name}: {self.character_health_summary(member)} | AC {member.armor_class} | "
                    f"{self.character_condition_summary(member)}"
                )
                for member in self.state.party_members()
            )
        )
        camp_roster = (
            Group(*(self.rich_from_ansi(self.companion_status_line(companion)) for companion in self.state.camp_companions))
            if self.state.camp_companions
            else self.rich_text("No companions are resting at camp right now.", "light_aqua", dim=True)
        )
        options = Group(
            self.rich_text("1. Party and roster", "light_green"),
            self.rich_text("2. Supplies and equipment", "light_green"),
            self.rich_text("3. Rest and recovery", "light_green"),
            self.rich_text("4. Talk to a companion", "light_green"),
            self.rich_text("5. View journal", "light_green"),
            self.rich_text("6. Speak to the magic mirror", "light_green"),
            self.rich_text("7. Break camp", "light_green"),
        )
        self.emit_rich(
            Group(
                Panel(
                    status,
                    title=self.rich_text("Camp Ledger", "light_yellow", bold=True),
                    border_style=rich_style_name("light_yellow"),
                    box=box.ROUNDED,
                    padding=(0, 1),
                ),
                Columns(
                    [
                        Panel(
                            active_party,
                            title=self.rich_text("Around The Fire", "light_green", bold=True),
                            border_style=rich_style_name("light_green"),
                            box=box.ROUNDED,
                            padding=(0, 1),
                        ),
                        Panel(
                            camp_roster,
                            title=self.rich_text("Camp Roster", "light_aqua", bold=True),
                            border_style=rich_style_name("light_aqua"),
                            box=box.ROUNDED,
                            padding=(0, 1),
                        ),
                        Panel(
                            options,
                            title=self.rich_text("Camp Actions", "light_red", bold=True),
                            border_style=rich_style_name("light_red"),
                            box=box.ROUNDED,
                            padding=(0, 1),
                        ),
                    ],
                    expand=True,
                    equal=True,
                ),
            ),
            width=max(108, self.rich_console_width()),
        )

    def open_camp_menu(self) -> None:
        play_music_for_context = getattr(self, "play_music_for_context", None)
        refresh_scene_music = getattr(self, "refresh_scene_music", None)
        if callable(play_music_for_context):
            play_music_for_context("camp", restart=True)
        try:
            self.banner("Camp")
            self.say(
                "Canvas, bedrolls, cookfire smoke, and the impossible magic mirror make camp the one place on the road "
                "where the party can breathe, reorganize, and speak honestly."
            )
            while True:
                self.render_camp_overview()
                options = [
                    "Party and roster",
                    "Supplies and equipment",
                    "Rest and recovery",
                    "Talk to a companion",
                    "View journal",
                    "Speak to the magic mirror (100 gp)",
                    "Break camp",
                ]
                choice = self.choose(
                    "How do you spend this stop at camp?",
                    options,
                    allow_meta=False,
                )
                if choice == 1:
                    self.open_camp_party_menu()
                elif choice == 2:
                    self.open_camp_supplies_menu()
                elif choice == 3:
                    self.open_camp_recovery_menu()
                elif choice == 4:
                    self.talk_to_companion()
                elif choice == 5:
                    self.show_journal()
                elif choice == 6:
                    self.visit_magic_mirror()
                else:
                    self.say("The campfire is banked, straps are tightened, and the road calls again.")
                    return
        finally:
            if callable(refresh_scene_music):
                refresh_scene_music()

    def open_camp_party_menu(self) -> None:
        while True:
            choice = self.choose(
                "Choose a party task.",
                [
                    "Review the active party",
                    "Review the full roster",
                    "View character sheets",
                    "Manage the active party",
                    "Back",
                ],
                allow_meta=False,
            )
            if choice == 1:
                self.show_party()
            elif choice == 2:
                self.show_full_roster()
            elif choice == 3:
                self.show_character_sheets()
            elif choice == 4:
                self.manage_party_roster()
            else:
                return

    def open_camp_supplies_menu(self) -> None:
        while True:
            choice = self.choose(
                "Choose how the company handles supplies and gear.",
                [
                    "View all inventory",
                    "View inventory by category",
                    "Use a consumable or scroll",
                    "Manage inventory",
                    "Manage equipment",
                    "Back",
                ],
                allow_meta=False,
            )
            if choice == 1:
                self.show_inventory()
            elif choice == 2:
                self.review_inventory_by_filter()
            elif choice == 3:
                self.use_item_from_inventory()
            elif choice == 4:
                self.manage_inventory()
            elif choice == 5:
                self.manage_equipment()
            else:
                return

    def open_camp_recovery_menu(self) -> None:
        assert self.state is not None
        while True:
            dead_allies = self.dead_allies_in_company()
            revivify_ready = bool(dead_allies)
            revivify_text = (
                "Use Scroll of Revivify on a dead ally"
                if self.state.inventory.get("scroll_revivify", 0) > 0
                else "Use Scroll of Revivify on a dead ally (need one)"
            )
            short_rest_text = "Take a short rest"
            if self.state.short_rests_remaining <= 0:
                short_rest_text = "Take a short rest (none remaining)"
            options = [short_rest_text, "Take a long rest"]
            if revivify_ready:
                options.append(revivify_text)
            options.append("Back")
            choice = self.choose("Choose how the party recovers tonight.", options, allow_meta=False)
            if choice == 1:
                self.short_rest()
            elif choice == 2:
                self.apply_scene_companion_support("camp_rest")
                self.long_rest()
            elif revivify_ready and choice == 3:
                self.use_scroll_of_revivify()
            else:
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
        if (
            callable(getattr(self, "should_use_rich_ui", None))
            and self.should_use_rich_ui()
            and Columns is not None
            and Group is not None
            and Panel is not None
            and box is not None
        ):
            active = [self.state.player, *self.state.companions]
            active_panel = Panel(
                Group(
                    *(
                        self.rich_from_ansi(
                            f"{member.name}: Level {member.level} {member.race} {member.class_name} | "
                            f"{self.character_health_summary(member)}"
                        )
                        for member in active
                    )
                ),
                title=self.rich_text("Active Party", "light_green", bold=True),
                border_style=rich_style_name("light_green"),
                box=box.ROUNDED,
                padding=(0, 1),
            )
            camp_panel = Panel(
                Group(*(self.rich_from_ansi(self.companion_status_line(companion)) for companion in self.state.camp_companions))
                if self.state.camp_companions
                else self.rich_text("No one is assigned to camp.", "light_aqua", dim=True),
                title=self.rich_text("Camp Companions", "light_aqua", bold=True),
                border_style=rich_style_name("light_aqua"),
                box=box.ROUNDED,
                padding=(0, 1),
            )
            if self.emit_rich(
                Group(
                    Panel(
                        self.rich_text(
                            f"Active party limit: {self.active_companion_limit() + 1} total, including you.",
                            "light_yellow",
                        ),
                        title=self.rich_text("Company Roster", "light_yellow", bold=True),
                        border_style=rich_style_name("light_yellow"),
                        box=box.ROUNDED,
                        padding=(0, 1),
                    ),
                    Columns([active_panel, camp_panel], expand=True, equal=True),
                ),
                width=max(108, self.rich_console_width()),
            ):
                return
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
