from __future__ import annotations

import time

from ..data.story.background_openings import BACKGROUND_STARTS, background_start_summary
from ..data.story.lore import BACKGROUND_LORE, CLASS_LORE, RACE_LORE
from ..data.story.public_terms import (
    ability_label,
    character_role_line,
    class_label,
    class_option_label,
    race_label,
    race_option_label,
    skill_option_label,
)
from ..content import (
    BACKGROUNDS,
    CLASSES,
    PRESET_CHARACTERS,
    RACES,
    STANDARD_ARRAY,
    build_character,
    build_preset_character,
    format_racial_bonuses,
)
from ..models import ABILITY_ORDER, Character, GameState
from ..ui.colors import rich_style_name
from ..ui.rich_render import Group, Panel, Table, box


BACK_OPTION = "Back"


class CharacterCreationMixin:
    def rich_creation_enabled(self) -> bool:
        return (
            callable(getattr(self, "should_use_rich_ui", None))
            and self.should_use_rich_ui()
            and Group is not None
            and Panel is not None
            and Table is not None
            and box is not None
        )

    def start_new_game(self) -> None:
        play_music_for_context = getattr(self, "play_music_for_context", None)
        if callable(play_music_for_context):
            play_music_for_context("main_menu")
        while True:
            self.banner("Character Creation")
            mode = self.choose(
                "Choose how you want to start.",
                [
                    "Preset Character",
                    "Custom Character",
                ],
                allow_meta=False,
            )
            if mode == 1:
                character = self.choose_preset_character()
            else:
                character = self.create_custom_character()
            if character is None:
                continue
            self.preview_character(character)
            if self.confirm("Begin the adventure with this character?"):
                self.begin_adventure(character)
                return
            self.say("Let's rebuild them from the start.")

    def create_custom_character(self) -> Character | None:
        name = ""
        race = ""
        class_name = ""
        background = ""
        base_scores: dict[str, int] = {}
        class_skills: list[str] = []
        expertise: list[str] = []
        step = 0
        while True:
            if step == 0:
                selected_name = self.ask_text_with_back("Name your adventurer")
                if selected_name is None:
                    return None
                name = selected_name
                step = 1
                continue
            if step == 1:
                selected_race = self.choose_named_option("Choose a people", RACES, allow_back=True)
                if selected_race is None:
                    step = 0
                    continue
                race = selected_race
                step = 2
                continue
            if step == 2:
                selected_class = self.choose_named_option("Choose a calling", CLASSES, allow_back=True)
                if selected_class is None:
                    step = 1
                    continue
                class_name = selected_class
                step = 3
                continue
            if step == 3:
                selected_background = self.choose_named_option("Choose a background", BACKGROUNDS, allow_back=True)
                if selected_background is None:
                    step = 2
                    continue
                background = selected_background
                step = 4
                continue
            if step == 4:
                selected_scores = self.choose_ability_scores(allow_back=True)
                if selected_scores is None:
                    step = 3
                    continue
                base_scores = selected_scores
                step = 5
                continue
            if step == 5:
                selected_skills = self.choose_class_skills(race, class_name, background, allow_back=True)
                if selected_skills is None:
                    step = 4
                    continue
                class_skills = selected_skills
                step = 6
                continue
            if class_name == "Rogue":
                selected_expertise = self.choose_expertise(race, background, class_skills, allow_back=True)
                if selected_expertise is None:
                    step = 5
                    continue
                expertise = selected_expertise
            else:
                expertise = []
            return build_character(
                name=name,
                race=race,
                class_name=class_name,
                background=background,
                base_ability_scores=base_scores,
                class_skill_choices=class_skills,
                expertise_choices=expertise,
                inventory={"Healing Potion": 1},
            )

    def ask_text_with_back(self, prompt: str) -> str | None:
        while True:
            self.output_fn("")
            value = self.read_input(f"{prompt} (or {BACK_OPTION}): ").strip()
            if self.handle_meta_command(value):
                continue
            if value.lower() == BACK_OPTION.lower():
                return None
            if value:
                return value
            self.say("Please enter a value.")

    def choose_preset_character(self) -> Character | None:
        class_names = list(PRESET_CHARACTERS)
        while True:
            options = [class_option_label(name) for name in class_names] + [BACK_OPTION]
            choice = self.choose("Choose a preset calling.", options, allow_meta=False)
            if choice == len(options):
                return None
            selected_class = class_names[choice - 1]
            self.describe_preset_character(selected_class)
            if self.confirm("Lock that preset in?"):
                return build_preset_character(selected_class)

    def describe_preset_character(self, class_name: str) -> None:
        preset = PRESET_CHARACTERS[class_name]
        if self.rich_creation_enabled():
            renderable = self.build_preset_character_rich_renderable(class_name)
            if self.emit_rich(renderable):
                self.output_fn("")
                return
        race = str(preset["race"])
        self.say(
            f"{class_label(class_name)} preset selected: {preset['name']}, {character_role_line(race, class_name)} ({preset['background']})."
        )
        self.say(str(preset["description"]))
        abilities = ", ".join(
            f"{ability_label(ability, include_code=True)} {preset['base_ability_scores'][ability]}"
            for ability in ABILITY_ORDER
        )
        self.say(f"Preset abilities: {abilities}")
        self.say(f"Preset calling skills: {', '.join(skill_option_label(skill) for skill in preset['class_skill_choices'])}")
        expertise = list(preset.get("expertise_choices", []))
        if expertise:
            self.say(f"Preset deep practice: {', '.join(skill_option_label(skill) for skill in expertise)}")

    def build_preset_character_rich_renderable(self, class_name: str):
        preset = PRESET_CHARACTERS[class_name]
        race = str(preset["race"])
        identity = Table.grid(expand=True, padding=(0, 1))
        identity.add_column(style=f"bold {rich_style_name('light_yellow')}", width=14)
        identity.add_column(ratio=1)
        identity.add_row("Selected", class_label(class_name))
        identity.add_row("Name", str(preset["name"]))
        identity.add_row("People / Role", character_role_line(race, class_name))
        identity.add_row("Background", str(preset["background"]))

        abilities = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False)
        abilities.add_column("Ability", style=f"bold {rich_style_name('light_yellow')}")
        abilities.add_column("Score", justify="center")
        for ability in ABILITY_ORDER:
            abilities.add_row(
                ability_label(ability, include_code=True),
                str(preset["base_ability_scores"][ability]),
            )

        training_lines = [
            self.rich_text(
                "Calling skills: " + ", ".join(skill_option_label(skill) for skill in preset["class_skill_choices"]),
                "light_green",
            ),
            self.rich_text(str(preset["description"]), "white"),
        ]
        expertise = list(preset.get("expertise_choices", []))
        if expertise:
            training_lines.insert(
                1,
                self.rich_text(
                    "Deep practice: " + ", ".join(skill_option_label(skill) for skill in expertise),
                    "light_aqua",
                ),
            )

        header_panel = Panel(
            identity,
            title=self.rich_text(f"{class_label(class_name)} Preset", "light_yellow", bold=True),
            border_style=rich_style_name("light_yellow"),
            box=box.ROUNDED,
            padding=(0, 1),
        )
        details_row = self.rich_panel_row_renderable(
            [
                Panel(
                    abilities,
                    title=self.rich_text("Preset Abilities", "light_red", bold=True),
                    border_style=rich_style_name("light_red"),
                    box=box.ROUNDED,
                    padding=(0, 1),
                ),
                Panel(
                    Group(*training_lines),
                    title=self.rich_text("Preset Training", "light_green", bold=True),
                    border_style=rich_style_name("light_green"),
                    box=box.ROUNDED,
                    padding=(0, 1),
                ),
            ],
            ratios=[1, 1],
            padding=(0, 1),
        )
        return Group(header_panel, details_row)

    def begin_adventure(self, character: Character) -> None:
        self.state = GameState(
            player=character,
            current_act=1,
            current_scene="background_prologue",
            flags={
                "act1_started": True,
                "background_prologue_pending": character.background,
                "opening_tutorial_pending": True,
            },
            clues=[],
            journal=[],
            completed_acts=[],
            xp=0,
            gold=20,
            inventory={
                "potion_healing": 2,
                "bread_round": 4,
                "travel_biscuits": 4,
                "dried_fish": 3,
                "goat_cheese": 2,
                "frontier_ale": 2,
                "root_vegetables": 2,
                "antitoxin_vial": 1,
            },
            short_rests_remaining=2,
        )
        self._playtime_checkpoint = time.monotonic()
        self.state.player.inventory.clear()
        self.ensure_state_integrity()
        start_note = BACKGROUND_STARTS.get(character.background, {}).get("arrival_note", "")
        self.add_journal(start_note or f"Your {character.background.lower()} path pulls you toward Greywake and the Emberway road to Iron Hollow.")
        self.add_journal("Word reaches you that Mira Thann is quietly gathering capable hands in Greywake against Ashen Brand pressure around Iron Hollow.")

    def choose_named_option(self, title: str, options: dict[str, dict[str, object]], *, allow_back: bool = False) -> str | None:
        names = list(options)
        while True:
            if options is RACES or options is CLASSES or options is BACKGROUNDS:
                if options is RACES:
                    labels = [race_option_label(name) for name in names]
                elif options is CLASSES:
                    labels = [class_option_label(name) for name in names]
                else:
                    labels = list(names)
            else:
                labels = [f"{name}: {options[name]['description']}" for name in names]
            menu_options = labels + ([BACK_OPTION] if allow_back else [])
            choice = self.choose(title, menu_options, allow_meta=False)
            if allow_back and choice == len(menu_options):
                return None
            selected = names[choice - 1]
            self.describe_selection(selected, options[selected], category=title)
            if self.confirm("Lock that in?"):
                return selected

    def describe_selection(self, name: str, details: dict[str, object], *, category: str) -> None:
        if category in {"Choose a race", "Choose a people"}:
            bonuses = format_racial_bonuses(name)
            skills = ", ".join(skill_option_label(skill) for skill in details["skills"]) if details["skills"] else "No automatic people skills"
            features = ", ".join(self.format_feature_name(feature) for feature in details["features"]) if details["features"] else "No special people traits"
            self.say(f"{race_label(name)} selected. Bonuses: {bonuses}. {details['description']}")
            self.say(f"People skills: {skills}. Traits: {features}.")
            if name in RACE_LORE:
                self.say(RACE_LORE[name]["text"])
            return
        if category in {"Choose a class", "Choose a calling"}:
            hit_die = details["hit_die"]
            saves = ", ".join(ability_label(save, include_code=True) for save in details["saving_throws"])
            self.say(f"{class_label(name)} selected. {details['description']}")
            self.say(f"Hit die: d{hit_die}. Resist proficiencies: {saves}.")
            if name in CLASS_LORE:
                self.say(CLASS_LORE[name]["text"])
            return
        if category == "Choose a background":
            skills = ", ".join(skill_option_label(skill) for skill in details["skills"])
            proficiencies = ", ".join(details.get("proficiencies", [])) or "No extra proficiencies"
            notes = " | ".join(details["notes"])
            self.say(f"{name} selected. {details['description']}")
            self.say(f"Background skills: {skills}. Extra training: {proficiencies}.")
            self.say(f"Background perks: {notes}")
            if name in BACKGROUND_LORE:
                self.say(BACKGROUND_LORE[name]["text"])
            return
        self.say(f"{name} selected. {details['description']}")

    def choose_ability_scores(self, *, allow_back: bool = False) -> dict[str, int] | None:
        while True:
            method_options = [
                "Standard array (15, 14, 13, 12, 10, 8)",
                "Point buy (27 points, scores from 8 to 15 before people bonuses)",
            ] + ([BACK_OPTION] if allow_back else [])
            method = self.choose(
                "Choose how to assign your ability scores.",
                method_options,
                allow_meta=False,
            )
            if allow_back and method == len(method_options):
                return None
            if method == 1:
                scores = self.choose_standard_array_scores(allow_back=allow_back)
                if scores is None:
                    continue
                return scores
            scores = self.choose_point_buy_scores(allow_back=allow_back)
            if scores is None:
                continue
            return scores

    def choose_standard_array_scores(self, *, allow_back: bool = False) -> dict[str, int] | None:
        remaining = list(STANDARD_ARRAY)
        picks: list[tuple[str, int]] = []
        while len(picks) < len(ABILITY_ORDER):
            ability = ABILITY_ORDER[len(picks)]
            options = [str(value) for value in remaining] + ([BACK_OPTION] if allow_back else [])
            index = self.choose(
                f"Assign a value to {ability_label(ability, include_code=True)}. Remaining scores: {', '.join(str(value) for value in remaining)}",
                options,
                allow_meta=False,
            )
            if allow_back and index == len(options):
                if not picks:
                    return None
                _previous_ability, previous_value = picks.pop()
                remaining.append(previous_value)
                remaining.sort(key=STANDARD_ARRAY.index)
                continue
            picks.append((ability, remaining.pop(index - 1)))
        return dict(picks)

    def choose_class_skills(self, race: str, class_name: str, background: str, *, allow_back: bool = False) -> list[str] | None:
        available = list(CLASSES[class_name]["skill_choices"])
        already_known = set(BACKGROUNDS[background]["skills"]) | set(RACES[race]["skills"])
        pool = [skill for skill in available if skill not in already_known]
        if len(pool) < CLASSES[class_name]["skill_picks"]:
            pool = available
        chosen: list[str] = []
        while len(chosen) < CLASSES[class_name]["skill_picks"]:
            skill_options = [skill for skill in pool if skill not in chosen]
            labels = [skill_option_label(skill) for skill in skill_options] + ([BACK_OPTION] if allow_back else [])
            choice = self.choose(
                f"Pick a {class_label(class_name)} skill.",
                labels,
                allow_meta=False,
            )
            if allow_back and choice == len(labels):
                if not chosen:
                    return None
                chosen.pop()
                continue
            chosen.append(skill_options[choice - 1])
        return chosen

    def choose_expertise(self, race: str, background: str, class_skills: list[str], *, allow_back: bool = False) -> list[str] | None:
        base_skills = set(BACKGROUNDS[background]["skills"]) | set(RACES[race]["skills"]) | set(class_skills)
        pool = sorted(base_skills)
        chosen: list[str] = []
        while len(chosen) < 2:
            expertise_options = [skill for skill in pool if skill not in chosen]
            labels = [skill_option_label(skill) for skill in expertise_options] + ([BACK_OPTION] if allow_back else [])
            choice = self.choose(
                "Choose a skill for Rogue deep practice.",
                labels,
                allow_meta=False,
            )
            if allow_back and choice == len(labels):
                if not chosen:
                    return None
                chosen.pop()
                continue
            chosen.append(expertise_options[choice - 1])
        return chosen

    def preview_character(self, character: Character) -> None:
        self.banner("Character Summary")
        if self.rich_creation_enabled():
            renderable = self.build_character_creation_summary_rich_renderable(character)
            if self.emit_rich(renderable):
                self.output_fn("")
                return
        self.say(
            f"{character.name}, {character.public_identity} ({character.background})\n"
            f"HP {character.current_hp}/{character.max_hp}, Defense {character.armor_class}, weapon: {character.weapon.name}"
        )
        abilities = ", ".join(f"{ability_label(ability, include_code=True)} {character.ability_scores[ability]}" for ability in ABILITY_ORDER)
        self.say(f"Abilities: {abilities}")
        self.say(f"Skills: {', '.join(skill_option_label(skill) for skill in character.skill_proficiencies)}")
        if character.skill_expertise:
            self.say(f"Deep practice: {', '.join(skill_option_label(skill) for skill in character.skill_expertise)}")
        if character.bonus_proficiencies:
            self.say(f"Background training: {', '.join(character.bonus_proficiencies)}")
        self.say(
            f"Features: {', '.join(self.format_feature_name(feature) for feature in character.features) if character.features else 'None'}"
        )
        self.say(f"Kit notes: {' | '.join(character.notes)}")
        self.say(f"Starting point: {background_start_summary(character.background)}")

    def build_character_creation_summary_rich_renderable(self, character: Character):
        header = Table.grid(expand=True, padding=(0, 1))
        header.add_column(style=f"bold {rich_style_name('light_yellow')}", width=14)
        header.add_column(ratio=1)
        header.add_row("Name", character.name)
        header.add_row("People / Role", f"Level {character.level} {character.public_identity}")
        header.add_row("Background", character.background)
        header.add_row("Health", f"{character.current_hp}/{character.max_hp}")
        header.add_row("Defense", str(character.armor_class))
        header.add_row("Weapon", character.weapon.name)

        abilities = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False)
        abilities.add_column("Ability", style=f"bold {rich_style_name('light_yellow')}")
        abilities.add_column("Score", justify="center")
        abilities.add_column("Mod", justify="center")
        for ability in ABILITY_ORDER:
            abilities.add_row(
                ability_label(ability, include_code=True),
                str(character.ability_scores[ability]),
                f"{character.ability_mod(ability):+d}",
            )

        details_lines = [
            self.rich_text(
                "Skills: " + ", ".join(skill_option_label(skill) for skill in character.skill_proficiencies),
                "light_green",
            ),
        ]
        if character.skill_expertise:
            details_lines.append(
                self.rich_text(
                    "Deep practice: " + ", ".join(skill_option_label(skill) for skill in character.skill_expertise),
                    "light_aqua",
                )
            )
        if character.bonus_proficiencies:
            details_lines.append(
                self.rich_text(
                    "Background training: " + ", ".join(character.bonus_proficiencies),
                    "light_green",
                )
            )
        details_lines.append(
            self.rich_text(
                "Features: "
                + (
                    ", ".join(self.format_feature_name(feature) for feature in character.features)
                    if character.features
                    else "None"
                ),
                "light_yellow",
            )
        )
        if character.notes:
            details_lines.extend(self.rich_text(f"Kit note: {note}", "white") for note in character.notes)
        details_lines.append(
            self.rich_text(
                f"Starting point: {background_start_summary(character.background)}",
                "light_red",
            )
        )

        header_panel = Panel(
            header,
            title=self.rich_text("Character Summary", "light_yellow", bold=True),
            border_style=rich_style_name("light_yellow"),
            box=box.ROUNDED,
            padding=(0, 1),
        )
        details_row = self.rich_panel_row_renderable(
            [
                Panel(
                    abilities,
                    title=self.rich_text("Ability Scores", "light_red", bold=True),
                    border_style=rich_style_name("light_red"),
                    box=box.ROUNDED,
                    padding=(0, 1),
                ),
                Panel(
                    Group(*details_lines),
                    title=self.rich_text("Loadout & Start", "light_green", bold=True),
                    border_style=rich_style_name("light_green"),
                    box=box.ROUNDED,
                    padding=(0, 1),
                ),
            ],
            ratios=[1, 1],
            padding=(0, 1),
        )
        return Group(header_panel, details_row)
