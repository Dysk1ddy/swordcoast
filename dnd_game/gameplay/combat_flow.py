from __future__ import annotations

from dataclasses import dataclass

from ..content import create_enemy
from ..items import get_item
from ..models import Character
from ..ui.colors import rich_style_name, strip_ansi
from ..ui.rich_render import Group, Live, Panel, Table, Text, box
from .encounter import Encounter
from .magic_points import has_magic_points, magic_point_cost
from .combat_resolution import ELEMENTALIST_ELEMENT_LABELS, ELEMENTALIST_ELEMENT_ORDER, STANCE_ORDER, WEAPON_MASTER_STYLE_ORDER


HEALING_POTION_NAME = get_item("potion_healing").name
DRINK_HEALING_POTION_ACTION = f"Drink a {HEALING_POTION_NAME}"


@dataclass(slots=True)
class TurnState:
    actions_remaining: int = 1
    bonus_action_available: bool = True
    attack_action_taken: bool = False
    bonus_action_spell_cast: bool = False
    non_cantrip_action_spell_cast: bool = False
    free_flee: bool = False


PUBLIC_COMBAT_ACTION_KEYS = {
    "Make Off-Hand Strike": "Make Off-Hand Attack",
    "Use Veil Step": "Use Cunning Action",
    DRINK_HEALING_POTION_ACTION: "Drink a Healing Potion",
}

BONUS_ACTION_COMBAT_KEYS = {
    "Use Cunning Action",
    "Warrior Rally",
    "Iron Draw",
    "Shoulder In",
    "Weapon Read",
    "Measure Twice",
    "Style Wheel",
    "Redline",
    "Teeth Set",
    "Drink The Hurt",
    "Red Mark",
    "Blood Price",
    "Mark Target",
    "Tool Read",
    "Feint",
    "Skirmish",
    "False Target",
    "Cover The Healer",
    "Death Mark",
    "Black Drop",
    "Arcane Bolt",
    "Pattern Read",
    "Marked Angle",
    "Change Weather",
    "Ground",
    "Anchor Shell",
    "Pulse Restore",
    "Overflow Shell",
    "Quick Mix",
    "Raise Shield",
    "Change Stance",
    "Cast Healing Word",
    "Make Off-Hand Attack",
    "Drink a Healing Potion",
}


class CombatFlowMixin:
    def combat_keyboard_choice_menu_supported(self) -> bool:
        return self.keyboard_choice_menu_supported()

    def run_encounter(self, encounter: Encounter) -> str:
        assert self.state is not None
        self.clear_pending_scaled_check_reward()
        encounter_outcome: str | None = None
        previous_active_encounter = getattr(self, "_active_encounter", None)
        previous_active_heroes = getattr(self, "_active_combat_heroes", None)
        previous_active_enemies = getattr(self, "_active_combat_enemies", None)
        previous_active_dodging = getattr(self, "_active_dodging_names", frozenset())
        previous_active_round = getattr(self, "_active_round_number", None)
        self._in_combat = True
        heroes: list[Character] = []
        enemies: list[Character] = []
        play_encounter_music = getattr(self, "play_encounter_music", None)
        refresh_scene_music = getattr(self, "refresh_scene_music", None)
        try:
            heroes = [member for member in self.state.party_members() if not member.dead]
            self.prepare_encounter_for_party(encounter, heroes=heroes)
            enemies = encounter.enemies
            for actor in [*heroes, *enemies]:
                actor.bond_flags.pop("quiet_mercy_used", None)
            self._active_encounter = encounter
            self._active_combat_heroes = heroes
            self._active_combat_enemies = enemies
            self.banner(encounter.title)
            self.say(encounter.description, typed=True)
            if callable(play_encounter_music):
                play_encounter_music(encounter)
            self.pause_for_combat_transition()
            self.introduce_encounter_characters(enemies)
            for actor in [*heroes, *enemies]:
                self.prepare_class_resources_for_combat(actor)
            self.apply_companion_combat_openers(heroes, enemies, encounter)
            for enemy in enemies:
                if enemy.is_conscious() and enemy.archetype == "carrion_stalker" and not self.has_status(enemy, "invisible"):
                    self.apply_status(enemy, "invisible", 1, source=f"{enemy.name}'s stalking entry")
            dodging: set[str] = set()
            self._active_dodging_names = dodging
            self._active_round_number = 1
            initiative = self.roll_initiative(
                heroes,
                enemies,
                hero_bonus=encounter.hero_initiative_bonus,
                enemy_bonus=encounter.enemy_initiative_bonus,
            )
            round_number = 1
            while True:
                self._active_round_number = round_number
                if not any(enemy.is_conscious() for enemy in enemies):
                    encounter_outcome = self.resolve_encounter_victory(encounter, enemies)
                    return encounter_outcome
                if not any(hero.is_conscious() for hero in heroes):
                    encounter_outcome = "defeat"
                    return encounter_outcome

                round_start_hook = getattr(self, "on_encounter_round_start", None)
                if callable(round_start_hook):
                    round_start_hook(encounter, heroes, enemies, initiative, round_number)
                    if not any(enemy.is_conscious() for enemy in enemies):
                        encounter_outcome = self.resolve_encounter_victory(encounter, enemies)
                        return encounter_outcome
                    if not any(hero.is_conscious() for hero in heroes):
                        encounter_outcome = "defeat"
                        return encounter_outcome
                show_combat_actor = getattr(self, "show_combat_actor", None)
                for actor in initiative:
                    if actor.name in dodging:
                        dodging.discard(actor.name)
                    if actor.dead:
                        continue
                    if callable(show_combat_actor):
                        show_combat_actor(actor)
                    if actor in heroes and actor.is_dying():
                        self.resolve_death_save(actor)
                        if actor.dead:
                            self.say(f"{self.style_name(actor)} slips away.")
                        self.tick_conditions(actor)
                        continue
                    if not actor.is_conscious():
                        continue
                    if not self.resolve_start_of_turn_statuses(actor):
                        self.tick_conditions(actor)
                        continue
                    if not any(hero.is_conscious() for hero in heroes):
                        encounter_outcome = "defeat"
                        return encounter_outcome
                    if not any(enemy.is_conscious() for enemy in enemies):
                        encounter_outcome = self.resolve_encounter_victory(encounter, enemies)
                        return encounter_outcome

                    if actor in heroes:
                        result = self.hero_turn(actor, heroes, enemies, encounter, dodging)
                        if result == "fled":
                            self.recover_after_battle()
                            encounter_outcome = "fled"
                            return encounter_outcome
                    else:
                        self.enemy_turn(actor, heroes, enemies, encounter, dodging)
                    self.tick_conditions(actor)
                round_number += 1
        finally:
            self.clear_after_encounter([*heroes, *enemies])
            self._active_encounter = previous_active_encounter
            self._active_combat_heroes = previous_active_heroes
            self._active_combat_enemies = previous_active_enemies
            self._active_dodging_names = previous_active_dodging
            self._active_round_number = previous_active_round
            self._in_combat = False
            show_combat_actor = getattr(self, "show_combat_actor", None)
            if callable(show_combat_actor):
                show_combat_actor(None)
            deferred_refresh_outcomes = getattr(self, "_defer_scene_music_refresh_on_outcomes", frozenset())
            if encounter_outcome not in deferred_refresh_outcomes and callable(refresh_scene_music):
                refresh_scene_music()

    def run_encounter_wave(
        self,
        encounter: Encounter,
        *,
        continue_on: tuple[str, ...] = ("victory",),
    ) -> str:
        previous_deferred_outcomes = getattr(self, "_defer_scene_music_refresh_on_outcomes", frozenset())
        previous_random_suppressed = getattr(self, "_post_combat_random_encounter_suppressed", False)
        self._defer_scene_music_refresh_on_outcomes = frozenset(continue_on)
        self._post_combat_random_encounter_suppressed = True
        try:
            return self.run_encounter(encounter)
        finally:
            self._defer_scene_music_refresh_on_outcomes = previous_deferred_outcomes
            self._post_combat_random_encounter_suppressed = previous_random_suppressed

    def prepare_encounter_for_party(self, encounter: Encounter, *, heroes: list[Character] | None = None) -> None:
        assert self.state is not None
        party = heroes if heroes is not None else [member for member in self.state.party_members() if not member.dead]
        if not party:
            return
        target_level = max(1, max(member.level for member in party))
        original_living_enemies = [enemy for enemy in encounter.enemies if "enemy" in enemy.tags and not enemy.dead]
        if not original_living_enemies:
            return

        minimum_enemy_level = max(1, target_level - 1)
        scaling_slots = 2 if len(original_living_enemies) >= 4 else 1
        self.scale_encounter_enemies_to_party_level(original_living_enemies, target_level, slots=scaling_slots)
        self.scale_encounter_enemies_to_minimum_level(original_living_enemies, minimum_enemy_level)

        allow_party_size_scaling = getattr(encounter, "allow_party_size_scaling", True)
        if len(party) >= 3 and allow_party_size_scaling:
            minimum_enemy_count = getattr(encounter, "minimum_enemy_count", None)
            if minimum_enemy_count is None:
                minimum_enemy_count = 3 if target_level >= self.minimum_enemy_scaling_level() else len(original_living_enemies)
            self.ensure_minimum_encounter_enemies(
                encounter,
                target_level=target_level,
                minimum=minimum_enemy_count,
                max_added=getattr(encounter, "max_added_supports", None),
            )
            living_enemies = [enemy for enemy in encounter.enemies if "enemy" in enemy.tags and not enemy.dead]
            self.scale_encounter_enemies_to_minimum_level(living_enemies, minimum_enemy_level)

    def scale_encounter_enemies_to_minimum_level(self, enemies: list[Character], minimum_level: int) -> None:
        for enemy in enemies:
            if enemy.is_conscious() and enemy.level < minimum_level:
                self.scale_enemy_to_party_level(enemy, minimum_level)

    def scale_encounter_enemies_to_party_level(
        self,
        enemies: list[Character],
        target_level: int,
        *,
        slots: int,
    ) -> None:
        candidates = [enemy for enemy in enemies if enemy.is_conscious() and enemy.level < target_level]
        candidates.sort(
            key=lambda enemy: (
                "leader" in enemy.tags,
                enemy.xp_value,
                enemy.max_hp,
                enemy.level,
            ),
            reverse=True,
        )
        for enemy in candidates[: max(0, slots)]:
            self.scale_enemy_to_party_level(enemy, target_level)

    def scale_enemy_to_party_level(self, enemy: Character, target_level: int) -> None:
        if target_level <= enemy.level:
            return
        original_level = enemy.level
        level_gap = target_level - original_level
        hp_deficit = max(0, enemy.max_hp - enemy.current_hp)
        for _ in range(level_gap):
            hp_gain = max(1, enemy.hit_die // 2 + 1 + enemy.ability_mod("CON"))
            enemy.max_hp += hp_gain
        enemy.level = target_level
        if enemy.current_hp > 0:
            enemy.current_hp = max(1, enemy.max_hp - hp_deficit)
        if level_gap >= 2:
            enemy.weapon.damage_bonus += level_gap // 2
        enemy.xp_value = self.scaled_enemy_reward(enemy.xp_value, level_gap, xp=True)
        enemy.gold_value = self.scaled_enemy_reward(enemy.gold_value, level_gap, xp=False)
        enemy.notes.append(f"Pseudo-scaled from level {original_level} to {target_level}.")

    def scaled_enemy_reward(self, base_value: int, level_gap: int, *, xp: bool) -> int:
        if base_value <= 0 or level_gap <= 0:
            return base_value
        per_level = 0.5 if xp else 0.35
        return max(base_value + 1, int(round(base_value * (1 + per_level * level_gap))))

    def ensure_minimum_encounter_enemies(
        self,
        encounter: Encounter,
        *,
        target_level: int,
        minimum: int,
        max_added: int | None = None,
    ) -> None:
        added = 0
        while len([enemy for enemy in encounter.enemies if "enemy" in enemy.tags and not enemy.dead]) < minimum:
            if max_added is not None and added >= max(0, max_added):
                return
            template = self.support_enemy_template_for_encounter(encounter.enemies, target_level=target_level)
            support = create_enemy(template)
            support.notes.append("Added by party-size encounter scaling.")
            encounter.enemies.append(support)
            added += 1

    def support_enemy_template_for_encounter(self, enemies: list[Character], *, target_level: int) -> str:
        living = [enemy for enemy in enemies if "enemy" in enemy.tags and not enemy.dead]
        tags = {tag for enemy in living for tag in enemy.tags}
        archetypes = {enemy.archetype for enemy in living}
        races = {enemy.race for enemy in living}

        if archetypes & {
            "caldra_voss",
            "choir_adept",
            "cult_lookout",
            "choir_executioner",
            "claimbinder_notary",
            "choir_cartographer",
            "memory_taker_adept",
            "obelisk_chorister",
        }:
            return "false_map_skirmisher" if target_level >= 4 else "cult_lookout"
        if "undead" in tags or "Undead" in races:
            if target_level >= 5:
                return "survey_chain_revenant"
            return "lantern_fen_wisp" if target_level >= 3 else "skeletal_sentry"
        if "construct" in tags or "Construct" in races:
            return "pact_archive_warden" if target_level >= 4 else "animated_armor"
        if "plant" in tags or "Plant" in races:
            return "briar_twig"
        if "ooze" in tags or "Ooze" in races:
            return "ochre_slime"
        if "beast" in tags or "Beast" in races:
            return "stirge_swarm" if target_level >= 3 else "wolf"
        if "aberration" in tags or "Aberration" in races:
            if target_level >= 6:
                return "forge_echo_stalker"
            if target_level >= 4:
                return "blackglass_listener"
            return "nothic"
        if "monstrosity" in tags or "Monstrosity" in races:
            if target_level >= 4:
                return "carrion_lash_crawler"
            return "rust_shell_scuttler"
        if "giant" in tags or "Giant" in races:
            return "goblin_skirmisher"
        if "Orc" in races:
            return "orc_raider"
        if "Bugbear" in races:
            return "bugbear_reaver"
        if "Kobold" in races:
            return "cinder_kobold"
        if "Goblin" in races:
            return "goblin_skirmisher"
        if "humanoid" in tags or races & {"Human", "Humanoid", "Hobgoblin"}:
            if archetypes & {"gutter_zealot", "ember_channeler"}:
                return "gutter_zealot"
            if target_level >= 5 and archetypes & {"expedition_reaver", "false_map_skirmisher", "claimbinder_notary"}:
                return "claimbinder_notary"
            if target_level >= 3 and archetypes & {"expedition_reaver", "starblighted_miner"}:
                return "expedition_reaver"
            return "bandit_archer"
        return "bandit"

    def resolve_encounter_victory(self, encounter: Encounter, enemies: list[Character]) -> str:
        assert self.state is not None
        self.clear_pending_scaled_check_reward()
        total_xp = sum(enemy.xp_value for enemy in enemies)
        total_gold = sum(enemy.gold_value for enemy in enemies)
        if total_xp or total_gold:
            self.reward_party(xp=total_xp, gold=total_gold, reason=encounter.title)
        self.collect_loot(enemies, source=encounter.title)
        self.recover_after_battle()
        play_sound_effect = getattr(self, "play_sound_effect", None)
        if callable(play_sound_effect):
            play_sound_effect("fight_victory")
        self.say("The encounter is yours.")
        self.pause_for_combat_transition()
        maybe_run_post_combat_random_encounter = getattr(self, "maybe_run_post_combat_random_encounter", None)
        if callable(maybe_run_post_combat_random_encounter) and not getattr(self, "_post_combat_random_encounter_suppressed", False):
            maybe_run_post_combat_random_encounter(encounter)
        create_autosave = getattr(self, "create_autosave", None)
        if callable(create_autosave):
            label = getattr(encounter, "title", "") or getattr(self.state, "current_scene", "combat")
            create_autosave(label=label)
        return "victory"

    def marked_priority_target(self, heroes: list[Character]) -> Character | None:
        marked = [hero for hero in heroes if hero.is_conscious() and self.has_status(hero, "marked")]
        if not marked:
            return None
        return max(marked, key=lambda hero: (hero.attack_bonus(), hero.current_hp))

    def hero_has_positive_combat_status(self, hero: Character) -> bool:
        return any(self.has_status(hero, status) for status in ("blessed", "emboldened", "guarded", "invisible"))

    def act2_expansion_enemy_turn(
        self,
        actor: Character,
        conscious_heroes: list[Character],
        conscious_allies: list[Character],
        heroes: list[Character],
        enemies: list[Character],
        dodging: set[str],
        marked_target: Character | None,
    ) -> bool:
        if actor.archetype == "false_map_skirmisher" and actor.resources.get("route_splice", 0) > 0:
            target = marked_target or max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["route_splice"] = 0
            self.apply_status(actor, "emboldened", 1, source=f"{actor.name}'s route splice")
            self.apply_status(target, "marked", 1, source=f"{actor.name}'s false trail")
            self.say(f"{actor.name} cuts a false route into the fight and leaves {target.name} standing where every ally can read the trap.")
            return True
        if actor.archetype == "false_map_skirmisher" and actor.resources.get("mislead_step", 0) > 0:
            target = marked_target or max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["mislead_step"] = 0
            self.say(f"{actor.name} vanishes behind a survey post and steps back into the line at {target.name}'s blind angle.")
            degree, _ = self.control_save_degree(target, "DEX", 13, context=f"against {actor.name}'s mislead step")
            if degree == "fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s mislead step")
            elif degree == "close_fail":
                self.apply_status(target, "marked", 1, source=f"{actor.name}'s mislead step")
                self.say(f"{target.name} catches the blind angle late, leaving a readable line for the next strike.")
            else:
                self.say(f"{target.name} refuses the wrong angle and keeps their footing.")
            return True
        if actor.archetype == "claimbinder_notary" and actor.resources.get("seizure_order", 0) > 0:
            target = marked_target or max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
            actor.resources["seizure_order"] = 0
            self.say(f"{actor.name} raises a seal-stamped writ and declares {target.name}'s footing unauthorized.")
            degree, _ = self.control_save_degree(target, "WIS", 14, context=f"against {actor.name}'s seizure order")
            if degree == "fail":
                removed: list[str] = []
                for status in ("blessed", "emboldened", "guarded"):
                    if self.has_status(target, status):
                        self.clear_status(target, status)
                        removed.append(status)
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s seizure order")
                if removed:
                    self.say(f"{target.name}'s {', '.join(removed)} buffer collapses under the notary's verdict.")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s seizure order")
                self.say(f"{target.name} keeps their footing, but the verdict still bites into their rhythm.")
            else:
                self.say(f"{target.name} refuses to let paperwork become a weapon.")
            return True
        if actor.archetype == "claimbinder_notary" and actor.resources.get("filed_objection", 0) > 0 and marked_target is None:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["filed_objection"] = 0
            actor.bond_flags["objection_target"] = target.name
            target.bond_flags["marked_by_claimbinder"] = True
            self.apply_status(target, "marked", 2, source=f"{actor.name}'s filed objection")
            self.say(f"{actor.name} names {target.name} in a cutting objection and every ally in earshot immediately starts hunting the citation.")
            return True
        if actor.archetype == "echo_sapper" and actor.resources.get("survey_charge", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["survey_charge"] = 0
            self.say(f"{actor.name} slams a breach hammer into the floor and sends a survey charge under {target.name}'s feet.")
            if not self.saving_throw(target, "DEX", 14, context=f"against {actor.name}'s survey charge"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s survey charge",
                        outcome_kind="damage",
                    ).total,
                    damage_type="force",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} force damage as the ground kicks up under them.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "prone", 1, source=f"{actor.name}'s survey charge")
            else:
                self.say(f"{target.name} rides the crack and keeps clear of the worst of it.")
            return True
        if actor.archetype == "echo_sapper" and actor.resources.get("dust_blind", 0) > 0:
            target = min(
                conscious_heroes,
                key=lambda hero: (
                    0 if self.has_status(hero, "prone") or self.has_status(hero, "reeling") else 1,
                    hero.current_hp,
                    hero.armor_class,
                ),
            )
            actor.resources["dust_blind"] = 0
            self.say(f"{actor.name} follows the collapse with a shovel-kick of grit and lamp ash at {target.name}.")
            degree, _ = self.control_save_degree(target, "CON", 14, context=f"against {actor.name}'s dust blind")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s dust blind")
                if target.is_conscious() and (self.has_status(target, "prone") or self.has_status(target, "reeling")):
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s dust blind")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s dust blind")
                self.say(f"{target.name} keeps sight through the grit, half a beat behind the collapse.")
            else:
                self.say(f"{target.name} keeps enough of their vision to stay dangerous.")
            return True
        if actor.archetype == "pact_archive_warden" and actor.resources.get("access_denied", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
            actor.resources["access_denied"] = 0
            self.say(f"{actor.name} plants its spear and projects a hard ward line across {target.name}'s advance.")
            degree, _ = self.control_save_degree(target, "STR", 14, context=f"against {actor.name}'s access denied")
            if degree == "fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s access denied")
                if target.is_conscious() and self.has_status(target, "reeling"):
                    self.apply_status(target, "prone", 1, source=f"{actor.name}'s access denied")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s access denied")
                self.say(f"{target.name} shoves through the ward line, but the angle is ugly.")
            else:
                self.say(f"{target.name} holds against the ward's shove.")
            return True
        if actor.archetype == "blackglass_listener" and actor.resources.get("overhear_intent", 0) > 0:
            target = max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    1 if hero.class_name == "Mage" else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
            actor.resources["overhear_intent"] = 0
            self.say(f"{actor.name} tilts its glass-black head and answers the thought {target.name} has not acted on yet.")
            degree, _ = self.control_save_degree(target, "WIS", 14, context=f"against {actor.name}'s overheard intent")
            if degree == "fail":
                self.apply_status(target, "frightened", 1, source=f"{actor.name}'s overheard intent")
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s overheard intent")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s overheard intent")
                self.say(f"{target.name} keeps the fear from taking hold, but the stolen thought lands anyway.")
            else:
                self.say(f"{target.name} forces the private thought back behind steel.")
            return True
        if actor.archetype == "blackglass_listener" and actor.resources.get("feedback_pulse", 0) > 0:
            target = max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    1 if hero.class_name == "Mage" else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
            actor.resources["feedback_pulse"] = 0
            self.say(f"{actor.name} snaps a feedback pulse into {target.name} where certainty and preparation are loudest.")
            actual = self.apply_damage(
                target,
                self.roll_with_display_bonus(
                    "2d6",
                    style="damage",
                    context_label=f"{actor.name}'s feedback pulse",
                    outcome_kind="damage",
                ).total,
                damage_type="psychic",
            )
            self.say(f"{target.name} takes {self.style_damage(actual)} psychic damage from the pulse.")
            self.announce_downed_target(target)
            if target.is_conscious():
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s feedback pulse")
            return True
        if actor.archetype == "choir_cartographer" and actor.resources.get("map_the_weakness", 0) > 0 and marked_target is None:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["map_the_weakness"] = 0
            self.apply_status(target, "marked", 2, source=f"{actor.name}'s mapped weakness")
            self.say(f"{actor.name} sketches one killing line through the fight and every ally around them immediately starts reading it.")
            if conscious_allies:
                ally = max(conscious_allies, key=lambda candidate: (candidate.attack_bonus(), candidate.current_hp))
                self.apply_status(ally, "emboldened", 1, source=f"{actor.name}'s mapped weakness")
            return True
        if actor.archetype == "choir_cartographer" and actor.resources.get("stolen_route", 0) > 0 and conscious_allies:
            actor.resources["stolen_route"] = 0
            ally = min(conscious_allies, key=lambda candidate: (candidate.current_hp, candidate.armor_class))
            self.apply_status(actor, "blessed", 1, source=f"{actor.name}'s stolen route")
            self.apply_status(ally, "guarded", 1, source=f"{actor.name}'s stolen route")
            self.say(f"{actor.name} folds one route over another and steals a safer angle for {ally.name}.")
            return True
        if actor.archetype == "resonance_leech" and actor.resources.get("drain_cadence", 0) > 0:
            target = max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    1 if self.has_status(hero, "frightened") or self.has_status(hero, "reeling") else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
            actor.resources["drain_cadence"] = 0
            self.say(f"{actor.name} latches onto the rhythm around {target.name} and starts drinking the strongest beat out of it.")
            if not self.saving_throw(target, "CON", 14, context=f"against {actor.name}'s drain cadence"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s drain cadence",
                        outcome_kind="damage",
                    ).total,
                    damage_type="psychic",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} psychic damage as the leech feeds.")
                self.announce_downed_target(target)
                for status in ("blessed", "emboldened", "guarded", "invisible"):
                    if self.has_status(target, status):
                        self.clear_status(target, status)
                        break
                actor.grant_temp_hp(8)
            else:
                self.say(f"{target.name} keeps the rhythm from settling into the leech's mouth.")
            return True
        if actor.archetype == "survey_chain_revenant" and actor.resources.get("drag_to_marker", 0) > 0 and not any(self.has_status(hero, "grappled") for hero in conscious_heroes):
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["drag_to_marker"] = 0
            self.say(f"{actor.name} whips a survey chain around {target.name} and hauls them toward an old, unfinished mark.")
            degree, _ = self.control_save_degree(target, "STR", 15, context=f"against {actor.name}'s drag to marker")
            if degree == "fail":
                self.apply_status(target, "grappled", 2, source=f"{actor.name}'s drag to marker")
                if target.is_conscious():
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s drag to marker")
            elif degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s drag to marker")
                self.say(f"{target.name} tears clear, though the chain drags one ankle out of line.")
            else:
                self.say(f"{target.name} tears clear before the chain can set.")
            return True
        if actor.archetype == "censer_horror" and actor.resources.get("hush_smoke", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["hush_smoke"] = 0
            self.say(f"{actor.name} swings wide, and the censer split spills hush-smoke straight into {target.name}'s lungs and eyes.")
            degree, _ = self.control_save_degree(target, "CON", 14, context=f"against {actor.name}'s hush smoke")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s hush smoke")
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s hush smoke")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s hush smoke")
                self.say(f"{target.name} coughs the smoke out, but the censer keeps the tempo crooked.")
            else:
                self.say(f"{target.name} coughs through the smoke without fully losing the line.")
            return True
        if actor.archetype == "memory_taker_adept" and actor.resources.get("erase_witness", 0) > 0:
            target = max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
            actor.resources["erase_witness"] = 0
            self.say(f"{actor.name} cuts for the part of the fight {target.name} will still remember afterward.")
            degree, _ = self.control_save_degree(target, "WIS", 14, context=f"against {actor.name}'s erase witness")
            if degree == "fail":
                for status in ("guarded", "blessed", "emboldened"):
                    if self.has_status(target, status):
                        self.clear_status(target, status)
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s erase witness")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s erase witness")
                self.say(f"{target.name} keeps the memory whole, but loses a step proving it.")
            else:
                self.say(f"{target.name} keeps hold of what matters and refuses the edit.")
            return True
        if actor.archetype == "obelisk_chorister" and actor.resources.get("shard_hymn", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["shard_hymn"] = 0
            self.say(f"{actor.name} lifts a staff of shard-glass and sings one note the chamber was never meant to carry.")
            if not self.saving_throw(target, "WIS", 15, context=f"against {actor.name}'s shard hymn"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "3d6",
                        style="damage",
                        context_label=f"{actor.name}'s shard hymn",
                        outcome_kind="damage",
                    ).total,
                    damage_type="psychic",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} psychic damage from the hymn.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "frightened", 2, source=f"{actor.name}'s shard hymn")
                    self.apply_status(target, "reeling", 2, source=f"{actor.name}'s shard hymn")
            else:
                self.say(f"{target.name} hears the hymn without letting it become a command.")
            return True
        if actor.archetype == "obelisk_chorister" and actor.resources.get("choral_screen", 0) > 0:
            actor.resources["choral_screen"] = 0
            self.say(f"{actor.name} throws up a choral screen of shard-light and disciplined breath.")
            for ally in [actor, *conscious_allies]:
                ally.grant_temp_hp(6)
                self.clear_status(ally, "frightened")
            return True
        if actor.archetype == "blacklake_adjudicator" and actor.resources.get("sentence_of_entry", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["sentence_of_entry"] = 0
            self.say(f"{actor.name} levels its pike and pronounces a sentence no trespasser was meant to survive hearing.")
            degree, _ = self.control_save_degree(target, "WIS", 15, context=f"against {actor.name}'s sentence of entry")
            if degree == "fail":
                self.apply_status(target, "frightened", 1, source=f"{actor.name}'s sentence of entry")
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s sentence of entry")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s sentence of entry")
                self.say(f"{target.name} holds against the verdict, though the sentence still shakes the line.")
            else:
                self.say(f"{target.name} holds their ground against the verdict.")
            return True
        if actor.archetype == "forge_echo_stalker" and actor.resources.get("heatshadow_prowl", 0) > 0 and not self.has_status(actor, "invisible"):
            actor.resources["heatshadow_prowl"] = 0
            self.apply_status(actor, "invisible", 1, source=f"{actor.name}'s heatshadow prowl")
            self.apply_status(actor, "emboldened", 1, source=f"{actor.name}'s heatshadow prowl")
            self.say(f"{actor.name} smears into forge-light and vanishes into the heatshadow between one blink and the next.")
            return True
        if actor.archetype == "forge_echo_stalker" and actor.resources.get("answering_screech", 0) > 0:
            target = next((hero for hero in conscious_heroes if self.has_status(hero, "reeling")), None)
            if target is not None:
                actor.resources["answering_screech"] = 0
                self.say(f"{actor.name} answers {target.name}'s stagger with a shriek that sounds like the forge itself recognizing weakness.")
                if not self.saving_throw(target, "CON", 15, context=f"against {actor.name}'s answering screech"):
                    actual = self.apply_damage(
                        target,
                        self.roll_with_display_bonus(
                            "2d6",
                            style="damage",
                            context_label=f"{actor.name}'s answering screech",
                            outcome_kind="damage",
                        ).total,
                        damage_type="thunder",
                    )
                    self.say(f"{target.name} takes {self.style_damage(actual)} thunder damage from the screech.")
                    self.announce_downed_target(target)
                    if target.is_conscious():
                        self.apply_status(target, "prone", 1, source=f"{actor.name}'s answering screech")
                else:
                    self.say(f"{target.name} braces before the screech can fold them to the floor.")
                return True
        if actor.archetype == "covenant_breaker_wight" and actor.resources.get("break_the_line", 0) > 0:
            target = marked_target or max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    1 if hero.class_name == "Mage" else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
            actor.resources["break_the_line"] = 0
            self.say(f"{actor.name} lowers its split oathblade and drives straight for the place your line expects to hold.")
            degree, _ = self.control_save_degree(target, "STR", 15, context=f"against {actor.name}'s break the line")
            if degree == "fail":
                self.apply_status(target, "prone", 1, source=f"{actor.name}'s break the line")
                if target.is_conscious():
                    self.apply_status(target, "frightened", 1, source=f"{actor.name}'s break the line")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s break the line")
                self.say(f"{target.name} stops the rush from breaking the company, but the impact still jars them.")
            else:
                self.say(f"{target.name} absorbs the rush without letting the whole company buckle.")
            return True
        if actor.archetype == "hollowed_survey_titan" and actor.resources.get("bearing_collapse", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
            actor.resources["bearing_collapse"] = 0
            self.say(f"{actor.name} hammers its maul down and the whole line answers like load-bearing stone finally giving way.")
            if not self.saving_throw(target, "DEX", 15, context=f"against {actor.name}'s bearing collapse"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "3d6",
                        style="damage",
                        context_label=f"{actor.name}'s bearing collapse",
                        outcome_kind="damage",
                    ).total,
                    damage_type="bludgeoning",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} bludgeoning damage from the collapse.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "prone", 1, source=f"{actor.name}'s bearing collapse")
            else:
                self.say(f"{target.name} dives clear before the worst of the collapse lands.")
            return True
        return False

    def act2_expansion_priority_target(
        self,
        actor: Character,
        conscious_heroes: list[Character],
        marked_target: Character | None,
    ) -> Character | None:
        if actor.archetype in {
            "false_map_skirmisher",
            "claimbinder_notary",
            "blackglass_listener",
            "choir_cartographer",
            "memory_taker_adept",
            "obelisk_chorister",
        }:
            return marked_target or max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    1 if hero.class_name == "Mage" else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
        if actor.archetype in {"echo_sapper", "pact_archive_warden", "blacklake_adjudicator", "hollowed_survey_titan"}:
            return min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
        if actor.archetype in {"resonance_leech", "censer_horror", "forge_echo_stalker"}:
            return min(
                conscious_heroes,
                key=lambda hero: (
                    0 if any(self.has_status(hero, status) for status in ("reeling", "frightened", "deafened", "blinded")) else 1,
                    hero.current_hp,
                    hero.armor_class,
                ),
            )
        if actor.archetype == "survey_chain_revenant":
            return min(
                conscious_heroes,
                key=lambda hero: (0 if self.has_status(hero, "grappled") else 1, hero.current_hp, hero.armor_class),
            )
        if actor.archetype == "covenant_breaker_wight":
            return marked_target or max(
                conscious_heroes,
                key=lambda hero: (
                    1 if self.hero_has_positive_combat_status(hero) else 0,
                    1 if hero.class_name == "Mage" else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
        return None

    def apply_companion_combat_openers(
        self,
        heroes: list[Character],
        enemies: list[Character],
        encounter: Encounter,
    ) -> None:
        if self.state is None:
            return
        for companion in heroes:
            if not companion.is_conscious() or not companion.companion_id:
                continue
            opener_getter = getattr(self, "companion_combat_opener", None)
            opener = opener_getter(companion) if callable(opener_getter) else {}
            if not opener:
                continue
            opener_name = str(opener.get("name") or "trusted opener")
            if companion.disposition < 6:
                if companion.disposition <= -3 and not companion.bond_flags.get("low_trust_opener_warning_seen"):
                    self.say(f"{companion.name} keeps their own counsel and offers no {opener_name} opener.")
                    companion.bond_flags["low_trust_opener_warning_seen"] = True
                    recorder = getattr(self, "record_companion_trust_event", None)
                    if callable(recorder):
                        recorder(f"{companion.name} withheld {opener_name} in combat at low trust.")
                continue
            opener_text = str(opener.get("text") or f"{companion.name} creates a trusted opening.")
            self.say(opener_text)
            status_payload = dict(opener.get("ally_statuses", {}))
            if companion.disposition >= 9:
                for status, duration in dict(opener.get("exceptional_ally_statuses", {})).items():
                    status_payload[status] = max(int(status_payload.get(status, 0)), int(duration))
            for hero in heroes:
                if not hero.is_conscious():
                    continue
                for status, duration in status_payload.items():
                    self.apply_status(hero, str(status), int(duration), source=f"{companion.name}'s {opener_name}")

    def hero_turn(
        self,
        actor: Character,
        heroes: list[Character],
        enemies: list[Character],
        encounter: Encounter,
        dodging: set[str],
    ) -> str | None:
        return self.player_turn(actor, heroes, enemies, encounter, dodging)

    def player_turn(
        self,
        actor: Character,
        heroes: list[Character],
        enemies: list[Character],
        encounter: Encounter,
        dodging: set[str],
    ) -> str | None:
        turn_state = TurnState()
        while True:
            conscious_enemies = [enemy for enemy in enemies if enemy.is_conscious()]
            if not conscious_enemies:
                return None
            options = self.get_player_combat_options(actor, encounter, turn_state=turn_state, heroes=heroes)
            if options == ["End Turn"]:
                return None
            selected_option = self.choose_grouped_combat_option(
                self.turn_prompt(actor, turn_state),
                options,
                actor=actor,
                heroes=heroes,
                enemies=enemies,
            )
            action = self.combat_action_key(selected_option)
            if action == "End Turn":
                return None
            if action.startswith("Attack"):
                target = self.choose_target(conscious_enemies, prompt="Choose a target for your attack.", allow_back=True)
                if target is None:
                    continue
                self.perform_weapon_attack(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                turn_state.attack_action_taken = True
                continue
            if action == "Make Off-Hand Attack":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for your off-hand attack.", allow_back=True)
                if target is None:
                    continue
                self.perform_offhand_attack(actor, target, heroes, enemies, dodging)
                turn_state.bonus_action_available = False
                continue
            if action == "Use Cunning Action":
                cunning_choice = self.choose(
                    "Choose a Veil Step.",
                    [
                        self.skill_tag("STEALTH", self.action_option("Hide in the fight's blind spots.")),
                        self.action_option("Dash and line up a clean escape."),
                        self.action_option("Disengage and break away safely."),
                        "Back",
                    ],
                    allow_meta=False,
                    show_hud=False,
                )
                if cunning_choice == 4:
                    continue
                if cunning_choice == 1:
                    success = self.skill_check(actor, "Stealth", 12, context="to vanish back into the melee's blind spots")
                    if success:
                        self.apply_status(actor, "invisible", 2, source="Veil Step")
                        self.grant_rogue_edge(actor, source="a clean Hide")
                        self.say(f"{self.style_name(actor)} slips back out of the enemy's direct line.")
                    else:
                        self.say(f"{self.style_name(actor)} cannot quite disappear into the chaos.")
                elif cunning_choice == 2:
                    turn_state.free_flee = True
                    self.apply_status(actor, "emboldened", 1, source="Veil Step: Dash")
                    self.say(f"{self.style_name(actor)} surges for open ground and can break away cleanly this turn.")
                else:
                    turn_state.free_flee = True
                    self.say(f"{self.style_name(actor)} disengages cleanly and can flee without needing another opening this turn.")
                turn_state.bonus_action_available = False
                continue
            if action == "Take Guard Stance":
                if self.use_guard_stance(actor):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Raise Shield":
                self.use_raise_shield(actor)
                turn_state.bonus_action_available = False
                continue
            if action == "Change Stance":
                if self.choose_combat_stance(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Shove":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to shove.", allow_back=True)
                if target is None:
                    continue
                self.use_warrior_shove(actor, target)
                turn_state.actions_remaining -= 1
                continue
            if action == "Pin":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to pin.", allow_back=True)
                if target is None:
                    continue
                self.use_warrior_pin(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Clean Line":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Clean Line.", allow_back=True)
                if target is None:
                    continue
                self.use_clean_line(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Dent The Shell":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to Dent The Shell.", allow_back=True)
                if target is None:
                    continue
                self.use_dent_the_shell(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Hook The Guard":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to Hook The Guard.", allow_back=True)
                if target is None:
                    continue
                self.use_hook_the_guard(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Reckless Cut":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Reckless Cut.", allow_back=True)
                if target is None:
                    continue
                self.use_reckless_cut(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "War-Salve Strike":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for War-Salve Strike.", allow_back=True)
                if target is None:
                    continue
                self.use_war_salve_strike(actor, target, heroes, enemies, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Open The Ledger":
                target = self.choose_target(conscious_enemies, prompt="Choose a Red Mark target for Open The Ledger.", allow_back=True)
                if target is None:
                    continue
                if self.use_open_the_ledger(actor, target, heroes, enemies, dodging):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Dirty Trick":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Dirty Trick.", allow_back=True)
                if target is None:
                    continue
                trick_choice = self.choose(
                    "Choose a Dirty Trick.",
                    [
                        self.action_option("Distract and expose the target."),
                        self.action_option("Throw dust or flash powder into their eyes."),
                        self.action_option("Trip or tangle their footing."),
                        self.action_option("Cut a strap or expose an armor seam."),
                        "Back",
                    ],
                    allow_meta=False,
                    show_hud=False,
                )
                if trick_choice == 5:
                    continue
                trick_kind = ("distract", "blind", "trip", "seam")[trick_choice - 1]
                if self.use_dirty_trick(actor, target, trick_kind):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Smoke Pin":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Smoke Pin.", allow_back=True)
                if target is None:
                    continue
                if self.use_smoke_pin(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Quiet Knife":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Quiet Knife.", allow_back=True)
                if target is None:
                    continue
                if self.use_quiet_knife(actor, target, heroes, enemies, dodging):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Between Plates":
                target = self.choose_target(conscious_enemies, prompt="Choose a Death Mark target for Between Plates.", allow_back=True)
                if target is None:
                    continue
                if self.use_between_plates(actor, target, heroes, enemies, dodging):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Sudden End":
                target = self.choose_target(conscious_enemies, prompt="Choose a Death Mark target for Sudden End.", allow_back=True)
                if target is None:
                    continue
                if self.use_sudden_end(actor, target, heroes, enemies, dodging):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Green Needle":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Green Needle.", allow_back=True)
                if target is None:
                    continue
                if self.use_green_needle(actor, target, heroes, enemies, dodging):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Bitter Cloud":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Bitter Cloud.", allow_back=True)
                if target is None:
                    continue
                if self.use_bitter_cloud(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Rot Thread":
                target = self.choose_target(conscious_enemies, prompt="Choose a poisoned target for Rot Thread.", allow_back=True)
                if target is None:
                    continue
                if self.use_rot_thread(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Bloom In The Blood":
                target = self.choose_target(conscious_enemies, prompt="Choose a poisoned target for Bloom In The Blood.", allow_back=True)
                if target is None:
                    continue
                if self.use_bloom_in_the_blood(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Minor Channel":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Minor Channel.", allow_back=True)
                if target is None:
                    continue
                if self.use_minor_channel(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Arcane Bolt":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Arcane Bolt.", allow_back=True)
                if target is None:
                    continue
                action_cast = self.combat_option_group(selected_option) == "Action"
                if self.use_arcane_bolt(actor, target, heroes, enemies, dodging, action_cast=action_cast):
                    if action_cast:
                        turn_state.actions_remaining -= 1
                    else:
                        turn_state.bonus_action_available = False
                continue
            if action == "Arc Pulse":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Arc Pulse.", allow_back=True)
                if target is None:
                    continue
                if self.use_arc_pulse(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Detonate Pattern":
                target = self.choose_target(conscious_enemies, prompt="Choose a charged target for Detonate Pattern.", allow_back=True)
                if target is None:
                    continue
                if self.use_detonate_pattern(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Ember Lance":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Ember Lance.", allow_back=True)
                if target is None:
                    continue
                if self.use_ember_lance(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Frost Shard":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Frost Shard.", allow_back=True)
                if target is None:
                    continue
                if self.use_frost_shard(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Volt Grasp":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Volt Grasp.", allow_back=True)
                if target is None:
                    continue
                if self.use_volt_grasp(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Burning Line":
                if self.use_burning_line(actor, conscious_enemies):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Lockfrost":
                if self.use_lockfrost(actor, conscious_enemies):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Blue Glass Palm":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Blue Glass Palm.", allow_back=True)
                if target is None:
                    continue
                if self.use_blue_glass_palm(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Lockstep Field":
                if self.use_lockstep_field(actor, heroes):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Field Mend":
                target = self.choose_ally(heroes, prompt="Choose an ally for Field Mend.", allow_back=True)
                if target is None:
                    continue
                if self.use_field_mend(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Triage Line":
                if self.use_triage_line(actor, heroes):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Clean Breath":
                target = self.choose_ally(heroes, prompt="Choose an ally for Clean Breath.", allow_back=True)
                if target is None:
                    continue
                if self.use_clean_breath(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Redcap Tonic":
                target = self.choose_ally(heroes, prompt="Choose an ally for Redcap Tonic.", allow_back=True)
                if target is None:
                    continue
                if self.use_redcap_tonic(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Smoke Jar":
                target = self.choose_ally(heroes, prompt="Choose an ally to anchor Smoke Jar cover.", allow_back=True)
                if target is None:
                    continue
                if self.use_smoke_jar(actor, target, heroes):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Bitter Acid":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Bitter Acid.", allow_back=True)
                if target is None:
                    continue
                if self.use_bitter_acid(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Field Stitch":
                target = self.choose_ally(heroes, prompt="Choose an ally for Field Stitch.", allow_back=True)
                if target is None:
                    continue
                if self.use_field_stitch(actor, target):
                    turn_state.actions_remaining -= 1
                continue
            if action == "Weapon Read":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to read.", allow_back=True)
                if target is None:
                    continue
                self.use_weapon_read(actor, target)
                turn_state.bonus_action_available = False
                continue
            if action == "Measure Twice":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to Measure Twice.", allow_back=True)
                if target is None:
                    continue
                if self.use_measure_twice(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Style Wheel":
                style_result = self.choose_weapon_master_style(actor)
                if style_result == "combo":
                    turn_state.bonus_action_available = False
                continue
            if action == "Redline":
                if self.use_redline(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Teeth Set":
                if self.use_teeth_set(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Drink The Hurt":
                if self.use_drink_the_hurt(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Red Mark":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Red Mark.", allow_back=True)
                if target is None:
                    continue
                if self.use_red_mark(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Blood Price":
                target = self.choose_ally(heroes, prompt="Choose an ally for Blood Price.", allow_back=True)
                if target is None:
                    continue
                if self.use_blood_price(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Mark Target":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to mark.", allow_back=True)
                if target is None:
                    continue
                if self.use_rogue_mark(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Tool Read":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Tool Read.", allow_back=True)
                if target is None:
                    continue
                if self.use_tool_read(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Feint":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to Feint.", allow_back=True)
                if target is None:
                    continue
                if self.use_rogue_feint(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Skirmish":
                if self.use_rogue_skirmish(actor):
                    turn_state.free_flee = True
                    turn_state.bonus_action_available = False
                continue
            if action == "False Target":
                target = self.choose_ally(heroes, prompt="Choose an ally for False Target.", allow_back=True)
                if target is None:
                    continue
                if self.use_false_target(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Cover The Healer":
                target = self.choose_ally(heroes, prompt="Choose an ally to cover.", allow_back=True)
                if target is None:
                    continue
                if self.use_cover_the_healer(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Death Mark":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Death Mark.", allow_back=True)
                if target is None:
                    continue
                if self.use_death_mark(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Black Drop":
                if self.use_black_drop(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Pattern Read":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Pattern Read.", allow_back=True)
                if target is None:
                    continue
                if self.use_pattern_read(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Marked Angle":
                target = self.choose_target(conscious_enemies, prompt="Choose a Pattern Read target for Marked Angle.", allow_back=True)
                if target is None:
                    continue
                if self.use_marked_angle(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Change Weather":
                weather_options = [ELEMENTALIST_ELEMENT_LABELS[element] for element in ELEMENTALIST_ELEMENT_ORDER] + ["Back"]
                weather_choice = self.choose(
                    "Choose an element to hold.",
                    weather_options,
                    allow_meta=False,
                    show_hud=False,
                )
                if weather_choice == len(weather_options):
                    continue
                if self.use_change_weather_hand(actor, ELEMENTALIST_ELEMENT_ORDER[weather_choice - 1]):
                    turn_state.bonus_action_available = False
                continue
            if action == "Ground":
                if self.use_ground(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Anchor Shell":
                target = self.choose_ally(heroes, prompt="Choose an ally for Anchor Shell.", allow_back=True)
                if target is None:
                    continue
                if self.use_anchor_shell(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Pulse Restore":
                target = self.choose_ally(heroes, prompt="Choose an ally for Pulse Restore.", allow_back=True)
                if target is None:
                    continue
                if self.use_pulse_restore(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Overflow Shell":
                target = self.choose_ally(heroes, prompt="Choose an ally for Overflow Shell.", allow_back=True)
                if target is None:
                    continue
                if self.use_overflow_shell(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Quick Mix":
                mix_choice = self.choose(
                    "Choose a Quick Mix rider.",
                    [
                        self.action_option("Numbing paste for temporary hit points."),
                        self.action_option("Clinging smoke for longer cover."),
                        self.action_option("Acid-cut solvent for sharper armor work."),
                        "Back",
                    ],
                    allow_meta=False,
                    show_hud=False,
                )
                if mix_choice == 4:
                    continue
                rider = ("numbed", "smoke", "acid_cut")[mix_choice - 1]
                if self.use_quick_mix(actor, rider):
                    turn_state.bonus_action_available = False
                continue
            if action == "Warrior Rally":
                target = self.choose_ally(heroes, prompt="Choose an ally to Rally.", allow_back=True)
                if target is None:
                    continue
                if self.use_warrior_rally(actor, target):
                    turn_state.bonus_action_available = False
                continue
            if action == "Iron Draw":
                target = self.choose_target(conscious_enemies, prompt="Choose a target to Fixate.", allow_back=True)
                if target is None:
                    continue
                self.use_iron_draw(actor, target)
                turn_state.bonus_action_available = False
                continue
            if action == "Shoulder In":
                if self.use_shoulder_in(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Help a Downed Ally":
                target = self.choose_ally(
                    [hero for hero in heroes if hero.current_hp == 0 and not hero.dead],
                    prompt="Choose a downed ally to haul back into the fight.",
                    allow_back=True,
                )
                if target is None:
                    continue
                self.help_downed_ally(actor, target)
                turn_state.actions_remaining -= 1
                continue
            if action == "Take the Dodge action":
                dodging.add(actor.name)
                self.say(
                    f"{self.style_name(actor)} focuses on defense. "
                    "Attack rolls against them have strain, and DEX resists have edge until their next turn."
                )
                turn_state.actions_remaining -= 1
                continue
            if action == "Drink a Healing Potion":
                if self.drink_healing_potion_in_combat(actor):
                    turn_state.bonus_action_available = False
                continue
            if action == "Use an Item":
                if not self.use_item_from_inventory(combat=True, actor=actor, heroes=heroes, allow_self_healing_potion=False):
                    continue
                turn_state.actions_remaining -= 1
                continue
            if action == "Attempt Parley":
                self.attempt_parley(actor, enemies, encounter.parley_dc)
                turn_state.actions_remaining -= 1
                continue
            if action == "Try to Flee":
                if self.blocks_movement(actor):
                    self.say(f"{self.style_name(actor)} cannot break away while {self.describe_blocking_condition(actor)} or held fast.")
                    turn_state.actions_remaining -= 1
                    continue
                if turn_state.free_flee:
                    self.apply_status(actor, "emboldened", 1, source="using a clean opening")
                    self.say("You use the ground you bought yourself and lead the party clear of the fight.")
                    self.pause_for_combat_transition()
                    return "fled"
                flee_dc = max(8, 13 - self.status_value(actor, "flee_bonus"))
                success = self.skill_check(actor, "Stealth", flee_dc, context="to break from the fight")
                turn_state.actions_remaining -= 1
                if success:
                    self.apply_status(actor, "emboldened", 1, source="finding a clean escape lane")
                    self.say("You find an opening and lead the party out of the melee.")
                    self.pause_for_combat_transition()
                    return "fled"
                self.apply_status(actor, "reeling", 1, source="a failed retreat")
                self.say("The enemies close the gap before you can disengage cleanly.")
                continue

    def turn_prompt(self, actor: Character, turn_state: TurnState) -> str:
        bonus_text = "ready" if turn_state.bonus_action_available else "spent"
        return f"Your turn, {self.style_name(actor)}. Actions left: {turn_state.actions_remaining}. Bonus action: {bonus_text}."

    def maybe_apply_enemy_stance(
        self,
        actor: Character,
        target: Character,
        conscious_heroes: list[Character],
        conscious_allies: list[Character],
    ) -> None:
        current = self.current_combat_stance_key(actor)
        target_defense = self.effective_defense_percent(target, damage_type="slashing")
        actor_defense = self.effective_defense_percent(actor, damage_type="slashing")
        preferred = current
        if actor.current_hp <= max(1, actor.max_hp // 3):
            preferred = "guard" if actor_defense >= 25 or getattr(actor, "shield", False) else "mobile"
        elif target_defense >= 35 and not actor.weapon.ranged:
            preferred = "press"
        elif actor.weapon.ranged or "bow" in actor.weapon.name.lower():
            preferred = "aim"
        elif actor_defense >= 35:
            preferred = "brace"
        elif conscious_allies and actor.current_hp >= actor.max_hp // 2:
            preferred = "aggressive"
        if preferred != current:
            self.set_combat_stance(actor, preferred)

    def combat_action_key(self, option: str) -> str:
        action = self.choice_text(option)
        action = action.split(" (", 1)[0]
        if action in PUBLIC_COMBAT_ACTION_KEYS:
            return PUBLIC_COMBAT_ACTION_KEYS[action]
        if action.startswith("Strike with "):
            return action.replace("Strike with ", "Attack with ", 1)
        if action.startswith("Cast "):
            return action
        return action

    def can_afford_spell(self, actor: Character, spell_id: str) -> bool:
        return has_magic_points(actor, magic_point_cost(spell_id, actor))

    def choose_combat_stance(self, actor: Character) -> bool:
        options = [self.combat_stance_option(stance_key, actor) for stance_key in STANCE_ORDER] + ["Back"]
        choice = self.choose(
            "Choose a combat stance.",
            options,
            allow_meta=False,
            show_hud=False,
        )
        if choice == len(options):
            return False
        return self.set_combat_stance(actor, STANCE_ORDER[choice - 1])

    def choose_weapon_master_style(self, actor: Character) -> str | None:
        options = [self.weapon_master_style_option(style_key, actor) for style_key in WEAPON_MASTER_STYLE_ORDER] + ["Back"]
        choice = self.choose(
            "Choose a weapon style.",
            options,
            allow_meta=False,
            show_hud=False,
        )
        if choice == len(options):
            return None
        return self.use_weapon_master_style(actor, WEAPON_MASTER_STYLE_ORDER[choice - 1])

    def combat_option_group(self, option: str) -> str:
        action = self.combat_action_key(option)
        if action == "End Turn":
            return "End Turn"
        if action == "Arcane Bolt" and "Action" in self.choice_text(option):
            return "Action"
        if action == "Use an Item":
            return "Item"
        if action == "Attempt Parley":
            return "Social"
        if action == "Try to Flee":
            return "Escape"
        if action in BONUS_ACTION_COMBAT_KEYS:
            return "Bonus Action"
        return "Action"

    def group_combat_options(self, options: list[str]) -> tuple[dict[int, str], list[tuple[str, list[tuple[int, str]]]]]:
        indexed: dict[int, str] = {}
        section_lookup: dict[str, list[str]] = {}
        for option in options:
            section = self.combat_option_group(option)
            if section not in section_lookup:
                section_lookup[section] = []
            section_lookup[section].append(option)
        section_order = ("Action", "Bonus Action", "Item", "Social", "Escape", "End Turn")
        sections: list[tuple[str, list[tuple[int, str]]]] = []
        display_index = 1
        for section in section_order:
            options_in_section = section_lookup.get(section)
            if not options_in_section:
                continue
            grouped_options: list[tuple[int, str]] = []
            for option in options_in_section:
                grouped_options.append((display_index, option))
                indexed[display_index] = option
                display_index += 1
            sections.append((section, grouped_options))
        return indexed, sections

    def combat_dashboard_rendering_supported(self) -> bool:
        can_emit_rich_output = getattr(self, "can_emit_rich_output", None)
        return bool(callable(can_emit_rich_output) and can_emit_rich_output() and Panel is not None and Group is not None and box is not None)

    def combat_action_panel_title(self, actor: Character | None) -> str:
        return "Action Box" if actor is None else f"{actor.name}'s Turn"

    def build_combat_action_panel(self, action_items: list[object], *, actor: Character | None):
        return Panel(
            Group(*action_items),
            title=self.rich_text(self.combat_action_panel_title(actor), "light_yellow", bold=True),
            border_style=rich_style_name("light_yellow"),
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def build_combat_dashboard_renderable(self, action_panel, *, hero_lines: list[str], enemy_lines: list[str]):
        battlefield_row = self.combat_battlefield_row_renderable(hero_lines, enemy_lines)
        if battlefield_row is None:
            return action_panel
        return Group(battlefield_row, action_panel)

    def emit_static_combat_dashboard(
        self,
        prompt: str,
        sections: list[tuple[str, list[tuple[int, str]]]],
        *,
        actor: Character | None,
        heroes: list[Character],
        enemies: list[Character],
    ) -> bool:
        if not self.combat_dashboard_rendering_supported():
            return False
        hero_lines = self.describe_living_combatants(heroes)
        enemy_lines = self.describe_living_combatants(enemies)
        action_items: list[object] = [self.rich_from_ansi(prompt), self.rich_text("", dim=True)]
        for section_index, (section, grouped_options) in enumerate(sections):
            action_items.append(self.rich_text(f"{section}:", "light_yellow", bold=True))
            for display_index, option in grouped_options:
                action_items.append(self.rich_from_ansi(f"  {display_index}. {self.format_option_text(option)}"))
            if section_index < len(sections) - 1:
                action_items.append(self.rich_text("", dim=True))
        action_items.extend([self.rich_text("", dim=True), self.rich_text(self.command_shelf_text(), "light_aqua", dim=True)])
        level_reminder = self.rich_interaction_level_up_reminder()
        if level_reminder is not None:
            action_items.append(level_reminder)
        action_panel = self.build_combat_action_panel(action_items, actor=actor)
        return self.emit_rich(
            self.build_combat_dashboard_renderable(
                action_panel,
                hero_lines=hero_lines,
                enemy_lines=enemy_lines,
            ),
            width=self.safe_rich_render_width(),
        )

    def render_grouped_combat_sections_text(
        self,
        prompt: str,
        sections: list[tuple[str, list[tuple[int, str]]]],
    ) -> None:
        self.say(prompt)
        for section_index, (section, grouped_options) in enumerate(sections):
            if section_index:
                self.output_fn("")
            self.output_fn(self.style_text(f"{section}:", "light_yellow"))
            for display_index, option in grouped_options:
                self.output_fn(f"  {display_index}. {self.format_option_text(option)}")
        self.render_command_shelf()

    def build_grouped_combat_keyboard_menu(
        self,
        prompt: str,
        sections: list[tuple[str, list[tuple[int, str]]]],
        *,
        actor: Character | None,
        heroes: list[Character],
        enemies: list[Character],
        selected_index: int,
        typed_buffer: str,
        feedback: str | None,
        show_instructions: bool,
    ):
        hero_lines = self.describe_living_combatants(heroes)
        enemy_lines = self.describe_living_combatants(enemies)
        action_items: list[object] = [self.rich_text(prompt, bold=True)]
        if show_instructions:
            action_items.append(
                self.rich_text(
                    "Arrows move. Enter confirms. Type a number or command. Esc clears.",
                    "white",
                    dim=True,
                )
            )
        action_items.append(self.rich_text(self.command_shelf_text(), "light_aqua", dim=True))
        level_reminder = self.rich_interaction_level_up_reminder()
        if level_reminder is not None:
            action_items.append(level_reminder)
        action_items.append(self.rich_text("", dim=True))
        for section_index, (section, grouped_options) in enumerate(sections):
            action_items.append(self.rich_text(f"{section}:", "light_yellow", bold=True))
            option_table = Table.grid(expand=True, padding=(0, 0))
            option_table.add_column(width=2)
            option_table.add_column(width=3)
            option_table.add_column(ratio=1)
            for display_index, option in grouped_options:
                active = display_index - 1 == selected_index
                marker = self.rich_text("> ", "light_green", bold=True) if active else self.rich_text("  ", dim=True)
                number = self.rich_text(f"{display_index}.", "light_yellow" if active else "white", bold=active)
                label = self.rich_from_ansi(self.format_option_text(option))
                if Text is not None and isinstance(label, Text) and active:
                    label.stylize("bold")
                row_style = "on rgb(28,36,46)" if active else None
                option_table.add_row(marker, number, label, style=row_style)
            action_items.append(option_table)
            if section_index < len(sections) - 1:
                action_items.append(self.rich_text("", dim=True))

        input_line = self.rich_text(f"> {typed_buffer}_", "light_green", bold=True) if typed_buffer else self.rich_text("> ", "white")
        action_items.append(self.rich_text("", dim=True))
        action_items.append(input_line)
        if feedback:
            action_items.append(self.rich_text(feedback, "light_red"))

        action_panel = self.build_combat_action_panel(action_items, actor=actor)
        return self.build_combat_dashboard_renderable(
            action_panel,
            hero_lines=hero_lines,
            enemy_lines=enemy_lines,
        )

    def run_grouped_combat_keyboard_menu(
        self,
        prompt: str,
        options: list[str],
        sections: list[tuple[str, list[tuple[int, str]]]],
        *,
        actor: Character | None,
        heroes: list[Character],
        enemies: list[Character],
        indexed: dict[int, str] | None = None,
    ) -> str | None:
        if not self.combat_keyboard_choice_menu_supported():
            return None
        if Panel is None or Group is None or Table is None or box is None:
            return None
        selection_lookup = indexed or {index: option for index, option in enumerate(options, start=1)}

        return self.run_live_keyboard_choice_session(
            option_count=len(selection_lookup),
            renderable_builder=lambda **state: self.build_grouped_combat_keyboard_menu(
                prompt,
                sections,
                actor=actor,
                heroes=heroes,
                enemies=enemies,
                **state,
            ),
            width_factory=self.safe_rich_render_width,
            resolve_selection=lambda selected_index: selection_lookup[selected_index + 1],
            live_cls=Live,
        )

    def choose_grouped_combat_option(
        self,
        prompt: str,
        options: list[str],
        *,
        actor: Character | None = None,
        heroes: list[Character] | None = None,
        enemies: list[Character] | None = None,
    ) -> str:
        while True:
            self.output_fn("")
            indexed, sections = self.group_combat_options(options)
            if heroes is not None and enemies is not None:
                selected_option = self.run_grouped_combat_keyboard_menu(
                    prompt,
                    options,
                    sections,
                    actor=actor,
                    heroes=heroes,
                    enemies=enemies,
                    indexed=indexed,
                )
                if selected_option is not None:
                    return selected_option

            if heroes is not None and enemies is not None and self.combat_dashboard_rendering_supported():
                raw = self.read_resize_aware_input(
                    lambda: self.emit_static_combat_dashboard(
                        prompt,
                        sections,
                        actor=actor,
                        heroes=heroes,
                        enemies=enemies,
                    ),
                    prompt="> ",
                ).strip()
            else:
                self.render_grouped_combat_sections_text(prompt, sections)
                self.output_fn("")
                raw = self.read_input("> ").strip()
            if self.handle_meta_command(raw):
                continue
            if raw.isdigit():
                value = int(raw)
                if value in indexed:
                    return indexed[value]
            self.say("Please enter a listed number.")

    def can_make_off_hand_attack(self, actor: Character) -> bool:
        main_hand = self.equipped_weapon_item(actor)
        off_hand = self.equipped_off_hand_weapon_item(actor)
        if main_hand is None or main_hand.weapon is None or off_hand is None:
            return False
        if main_hand.weapon.hands_required >= 2 or off_hand.weapon.hands_required >= 2:
            return False
        if main_hand.weapon.ranged or off_hand.weapon.ranged:
            return False
        return "light" in (main_hand.properties or []) and "light" in (off_hand.properties or [])

    def has_action_item_option(self, actor: Character, heroes: list[Character]) -> bool:
        if self.state is None:
            return False
        for item_id, quantity in self.inventory_dict().items():
            if quantity <= 0 or not get_item(item_id).is_combat_usable():
                continue
            if item_id != "potion_healing":
                return True
            if any(hero is not actor and not hero.dead for hero in heroes):
                return True
        return False

    def enemy_targeting_round_counts(self) -> dict[int, int]:
        round_number = int(getattr(self, "_active_round_number", 0) or 0)
        if getattr(self, "_enemy_targeting_round_number", None) != round_number:
            self._enemy_targeting_round_number = round_number
            self._enemy_targeting_round_counts = {}
        counts = getattr(self, "_enemy_targeting_round_counts", None)
        if not isinstance(counts, dict):
            counts = {}
            self._enemy_targeting_round_counts = counts
        return counts

    def enemy_target_score(self, actor: Character, target: Character) -> int:
        ordinary = self.enemy_uses_ordinary_variance_profile(actor)
        max_hp = max(1, int(getattr(target, "max_hp", 1) or 1))
        current_hp = max(0, int(getattr(target, "current_hp", 0) or 0))
        missing_percent = max(0, min(100, (max_hp - current_hp) * 100 // max_hp))
        score = 50
        if ordinary and current_hp * 4 <= max_hp:
            score -= 5
        else:
            score += min(5, missing_percent // 15)
        score += max(0, target.attack_bonus() - 3) // 2
        assumed_damage_type = "piercing" if getattr(actor.weapon, "ranged", False) else "slashing"
        score -= self.effective_defense_percent(target, damage_type=assumed_damage_type) // 20
        if self.hero_has_positive_combat_status(target):
            score += 3
        if any(self.has_status(target, status) for status in ("reeling", "frightened", "blinded", "restrained")):
            score += 2
        if any(self.has_status(target, status) for status in ("guarded", "smoke_jar", "false_target", "anchor_shell")):
            score -= 3
        if ordinary:
            counts = self.enemy_targeting_round_counts()
            score -= 8 * int(counts.get(id(target), 0))
            if actor.bond_flags.get("last_targeted_hero_id") == id(target):
                score -= 4
        return score

    def choose_weighted_enemy_target(self, actor: Character, conscious_heroes: list[Character]) -> Character:
        indexed = list(enumerate(conscious_heroes))
        return max(
            indexed,
            key=lambda entry: (
                self.enemy_target_score(actor, entry[1]),
                -int(self.enemy_targeting_round_counts().get(id(entry[1]), 0)),
                int(getattr(entry[1], "current_hp", 0) or 0),
                -entry[0],
            ),
        )[1]

    def record_enemy_target_choice(self, actor: Character, target: Character) -> None:
        if not self.enemy_uses_ordinary_variance_profile(actor):
            return
        counts = self.enemy_targeting_round_counts()
        counts[id(target)] = int(counts.get(id(target), 0)) + 1
        actor.bond_flags["last_targeted_hero"] = target.name
        actor.bond_flags["last_targeted_hero_id"] = id(target)

    def companion_turn(
        self,
        actor: Character,
        heroes: list[Character],
        enemies: list[Character],
        encounter: Encounter,
        dodging: set[str],
    ) -> None:
        conscious_enemies = [enemy for enemy in enemies if enemy.is_conscious()]
        if not conscious_enemies:
            return
        if "field_mend" in actor.features and self.can_afford_spell(actor, "field_mend"):
            wounded = [ally for ally in heroes if not ally.dead and ally.current_hp < ally.max_hp]
            if wounded:
                target = min(wounded, key=lambda ally: ally.current_hp)
                if target.current_hp <= max(1, target.max_hp // 2):
                    self.use_field_mend(actor, target)
                    return
        leaders = [enemy for enemy in conscious_enemies if "leader" in enemy.tags]
        if "arc_pulse" in actor.features and self.can_afford_spell(actor, "arc_pulse") and leaders:
            self.use_arc_pulse(actor, leaders[0])
            return
        if "minor_channel" in actor.features and self.can_afford_spell(actor, "minor_channel"):
            self.use_minor_channel(actor, conscious_enemies[0])
            return
        if "warrior_guard" in actor.features and self.current_combat_stance_key(actor) != "guard":
            if self.use_guard_stance(actor):
                return
        if "rogue_feint" in actor.features and not self.has_status(conscious_enemies[0], "off_balance"):
            self.use_rogue_feint(actor, conscious_enemies[0])
            return
        target = min(conscious_enemies, key=lambda enemy: enemy.current_hp)
        self.perform_weapon_attack(actor, target, heroes, enemies, dodging)

    def enemy_turn(
        self,
        actor: Character,
        heroes: list[Character],
        enemies: list[Character],
        encounter: Encounter,
        dodging: set[str],
    ) -> None:
        conscious_heroes = [hero for hero in heroes if hero.is_conscious()]
        if not conscious_heroes:
            return
        conscious_allies = [enemy for enemy in enemies if enemy.is_conscious() and enemy is not actor]
        fixated_target = self.fixated_priority_target(actor, conscious_heroes)
        ward_draw_target = None if fixated_target is not None else self.ward_draw_priority_target(conscious_heroes)
        marked_target = fixated_target or ward_draw_target or self.marked_priority_target(conscious_heroes)
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} falters and cannot press a hostile attack while Charmed.")
            return
        if self.act2_expansion_enemy_turn(
            actor,
            conscious_heroes,
            conscious_allies,
            heroes,
            enemies,
            dodging,
            marked_target,
        ):
            return
        if actor.archetype == "ash_brand_enforcer" and actor.resources.get("punishing_strike", 0) > 0:
            target = next(
                (
                    hero
                    for hero in conscious_heroes
                    if any(self.has_status(hero, status) for status in ("blessed", "emboldened", "invisible"))
                ),
                marked_target,
            )
            if target is not None:
                actor.resources["punishing_strike"] = 0
                self.say(f"{actor.name} lunges at {target.name}, aiming to turn their own momentum against them.")
                hit = self.perform_enemy_attack(actor, target, heroes, enemies, dodging)
                if hit and target.is_conscious():
                    extra = self.apply_damage(
                        target,
                        self.roll_with_display_bonus(
                            "1d6",
                            style="damage",
                            context_label=f"{actor.name}'s punishing strike",
                            outcome_kind="damage",
                        ).total,
                        damage_type="slashing",
                    )
                    self.say(f"{actor.name} drives the opening deeper for {self.style_damage(extra)} extra damage.")
                    self.announce_downed_target(target)
                    if self.has_status(target, "blessed"):
                        self.clear_status(target, "blessed")
                        self.say(f"{target.name}'s blessing gutters out under the hit.")
                return
        if actor.archetype == "brand_saboteur" and actor.resources.get("flash_ash", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["flash_ash"] = 0
            self.say(f"{actor.name} cracks a palmful of flash ash across {target.name}'s face.")
            degree, _ = self.control_save_degree(target, "CON", 11, context=f"against {actor.name}'s flash ash")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s flash ash")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s flash ash")
                self.say(f"{target.name} keeps sight through the ash, but the grit catches in every breath.")
            else:
                self.say(f"{target.name} coughs through the ash without losing sight of the fight.")
            return
        if (
            actor.archetype == "brand_saboteur"
            and actor.resources.get("retreat_step", 0) > 0
            and actor.current_hp <= max(1, actor.max_hp // 2)
        ):
            actor.resources["retreat_step"] = 0
            self.apply_status(actor, "emboldened", 1, source=f"{actor.name}'s retreat step")
            self.say(f"{actor.name} hooks a boot behind cover, shifts the line, and looks for a cleaner exit.")
            return
        if actor.archetype == "sereth_vane" and actor.resources.get("silver_pressure", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["silver_pressure"] = 0
            self.say(f"{actor.name} names the price of every life in the chamber until {target.name}'s footing starts to feel negotiable.")
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s silver pressure")
            if degree == "fail":
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s silver pressure")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s silver pressure")
                self.say(f"{target.name} catches the lie late, leaving one bad step in their stance.")
            else:
                self.say(f"{target.name} refuses to let Sereth turn arithmetic into fear.")
            return
        if actor.archetype == "sereth_vane" and actor.resources.get("command_relocate", 0) > 0 and conscious_allies:
            ally = min(conscious_allies, key=lambda candidate: (candidate.current_hp, candidate.armor_class))
            actor.resources["command_relocate"] = 0
            self.apply_status(ally, "emboldened", 1, source=f"{actor.name}'s relocation order")
            self.say(f"{actor.name} snaps two fingers and sends {ally.name} into a better angle before the line can close.")
            return
        if actor.archetype == "sereth_vane" and actor.resources.get("flash_ash", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["flash_ash"] = 0
            self.say(f"{actor.name} crushes a glass ash capsule underfoot and kicks the burst toward {target.name}.")
            degree, _ = self.control_save_degree(target, "CON", 12, context=f"against {actor.name}'s flash ash")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s flash ash")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s flash ash")
                self.say(f"{target.name} sees through watering eyes, a half-beat behind Sereth's next order.")
            else:
                self.say(f"{target.name} turns aside before the ash takes their eyes.")
            return
        if actor.archetype == "ember_channeler" and actor.resources.get("ember_mark", 0) > 0 and marked_target is None:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["ember_mark"] = 0
            self.say(f"{actor.name} traces a burning sigil toward {target.name} and lets the whole enemy line see it.")
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s ember mark")
            if degree == "fail":
                self.apply_status(target, "marked", 2, source=f"{actor.name}'s ember mark")
                if target.is_conscious():
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s ember mark")
            elif degree == "close_fail":
                self.apply_status(target, "marked", 1, source=f"{actor.name}'s ember mark")
                self.say(f"{target.name} brushes the ember sign away, but the line reads the glow for a moment.")
            else:
                self.say(f"{target.name} shakes off the worst of the ember sign before it can settle.")
            return
        if actor.archetype == "carrion_stalker" and actor.resources.get("shadow_hide", 0) > 0 and not self.has_status(actor, "invisible"):
            actor.resources["shadow_hide"] = 0
            self.apply_status(actor, "invisible", 1, source=f"{actor.name}'s shadow hide")
            self.say(f"{actor.name} melts back into the blind angles of the fight.")
            return
        if actor.archetype == "cult_lookout" and actor.resources.get("blind_dust", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["blind_dust"] = 0
            self.say(f"{actor.name} snaps a pouch of bitter dust across {target.name}'s line of sight.")
            degree, _ = self.control_save_degree(target, "DEX", 12, context=f"against {actor.name}'s blinding dust")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s blind dust")
                if target.is_conscious():
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s blind dust")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s blind dust")
                self.say(f"{target.name} blinks the dust clear, but the pouch burst leaves them off rhythm.")
            else:
                self.say(f"{target.name} turns away before the worst of the dust can settle in.")
            return
        if actor.archetype == "cult_lookout" and actor.resources.get("marked_shot", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["marked_shot"] = 0
            self.apply_status(actor, "emboldened", 1, source=f"{actor.name}'s marked shot")
            self.say(f"{actor.name} exhales, waits for one clean heartbeat, and looses a marked shot at {target.name}.")
            hit = self.perform_enemy_attack(actor, target, heroes, enemies, dodging)
            if hit and target.is_conscious():
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s marked shot")
            return
        if actor.archetype == "choir_adept" and actor.resources.get("hush_prayer", 0) > 0:
            actor.resources["hush_prayer"] = 0
            self.say(f"{actor.name} intones a hush-prayer that steadies the Quiet Choir line into brutal focus.")
            for ally in [actor, *conscious_allies]:
                self.apply_status(ally, "blessed", 2, source=f"{actor.name}'s hush-prayer")
            return
        if actor.archetype == "choir_adept" and actor.resources.get("discordant_word", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["discordant_word"] = 0
            self.say(f"{actor.name} speaks one wrong note directly into {target.name}'s thoughts.")
            if not self.saving_throw(target, "WIS", 13, context=f"against {actor.name}'s discordant word"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s discordant word",
                        outcome_kind="damage",
                    ).total,
                    damage_type="psychic",
                )
                self.say(f"The word lands like a blade of static, dealing {self.style_damage(actual)} psychic damage to {self.style_name(target)}.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "frightened", 1, source=f"{actor.name}'s discordant word")
                    self.apply_status(target, "reeling", 2, source=f"{actor.name}'s discordant word")
            else:
                self.say(f"{target.name} forces the whisper back into noise before it can take hold.")
            return
        if actor.archetype == "animated_armor" and actor.resources.get("lockstep_bash", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
            actor.resources["lockstep_bash"] = 0
            self.say(f"{actor.name} advances in perfect mechanical rhythm and crashes forward with a lockstep bash.")
            hit = self.perform_enemy_attack(actor, target, heroes, enemies, dodging)
            if hit and target.is_conscious() and not self.saving_throw(target, "STR", 13, context=f"against {actor.name}'s lockstep bash"):
                self.apply_status(target, "prone", 1, source=f"{actor.name}'s lockstep bash")
            return
        if actor.archetype == "spectral_foreman" and actor.resources.get("hammer_order", 0) > 0 and conscious_allies:
            target_ally = max(conscious_allies, key=lambda ally: (ally.attack_bonus(), ally.current_hp))
            actor.resources["hammer_order"] = 0
            self.say(f"{actor.name} slams a phantom pick against stone and barks an old shift-order at {target_ally.name}.")
            self.apply_status(target_ally, "emboldened", 2, source=f"{actor.name}'s hammer order")
            self.apply_status(actor, "blessed", 1, source=f"{actor.name}'s hammer order")
            return
        if actor.archetype == "spectral_foreman" and actor.resources.get("dead_shift", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["dead_shift"] = 0
            self.say(f"{actor.name} calls the dead shift back to work, and the cold of old labor falls across {target.name}.")
            if not self.saving_throw(target, "CON", 13, context=f"against {actor.name}'s dead shift"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s dead shift",
                        outcome_kind="damage",
                    ).total,
                    damage_type="necrotic",
                )
                self.say(f"{target.name} is drained for {self.style_damage(actual)} necrotic damage.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "exhaustion", 1, source=f"{actor.name}'s dead shift")
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s dead shift")
            else:
                self.say(f"{target.name} keeps their footing against the graveyard rhythm of the command.")
            return
        if actor.archetype == "starblighted_miner" and actor.resources.get("whisper_glare", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["whisper_glare"] = 0
            self.say(f"{actor.name}'s eyes catch the forge-light wrong, and a whispering glare fixes on {target.name}.")
            degree, _ = self.control_save_degree(target, "WIS", 13, context=f"against {actor.name}'s whisper glare")
            if degree == "fail":
                self.apply_status(target, "frightened", 1, source=f"{actor.name}'s whisper glare")
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s whisper glare")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s whisper glare")
                self.say(f"{target.name} tears their focus loose, but the glare leaves a tremor behind.")
            else:
                self.say(f"{target.name} tears their focus loose before the whisper can sound like their own thought.")
            return
        if actor.archetype == "caldra_voss" and actor.resources.get("shard_veil", 0) > 0 and actor.current_hp <= (actor.max_hp * 2) // 3:
            actor.resources["shard_veil"] = 0
            actor.grant_temp_hp(8)
            self.apply_status(actor, "invisible", 1, source=f"{actor.name}'s shard veil")
            self.apply_status(actor, "blessed", 1, source=f"{actor.name}'s shard veil")
            self.say(f"{actor.name} draws a shard veil across herself and slips sideways through the forge-light.")
            return
        if actor.archetype == "caldra_voss" and actor.resources.get("quiet_choir_rally", 0) > 0 and conscious_allies:
            actor.resources["quiet_choir_rally"] = 0
            self.say(f"{actor.name} lifts her voice and the Quiet Choir answers in one terrible, disciplined breath.")
            for ally in [actor, *conscious_allies]:
                ally.grant_temp_hp(6)
                self.apply_status(ally, "emboldened", 2, source=f"{actor.name}'s rally")
            return
        if actor.archetype == "caldra_voss" and actor.resources.get("obelisk_whisper", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["obelisk_whisper"] = 0
            self.say(f"{actor.name} lets a shard-bent whisper through, aimed only at {target.name}.")
            if not self.saving_throw(target, "WIS", 14, context=f"against {actor.name}'s obelisk whisper"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d8",
                        style="damage",
                        context_label=f"{actor.name}'s obelisk whisper",
                        outcome_kind="damage",
                    ).total,
                    damage_type="psychic",
                )
                self.say(f"The whisper bites deep for {self.style_damage(actual)} psychic damage.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "frightened", 2, source=f"{actor.name}'s obelisk whisper")
                    self.apply_status(target, "reeling", 2, source=f"{actor.name}'s obelisk whisper")
            else:
                self.say(f"{target.name} hears the shape of the whisper without letting it settle inside.")
            return
        if actor.archetype == "caldra_voss" and actor.resources.get("echo_step", 0) > 0:
            if self.blocks_movement(actor) or self.has_status(actor, "reeling") or actor.current_hp <= actor.max_hp // 2:
                actor.resources["echo_step"] = 0
                for status in ("grappled", "restrained", "prone", "reeling"):
                    self.clear_status(actor, status)
                self.apply_status(actor, "invisible", 1, source=f"{actor.name}'s echo step")
                self.apply_status(actor, "emboldened", 1, source=f"{actor.name}'s echo step")
                self.say(f"{actor.name} blurs into reflected sound and reappears a heartbeat later with the line reset.")
                return
        if actor.archetype == "cinder_kobold" and actor.resources.get("cinder_pot", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["cinder_pot"] = 0
            self.say(f"{actor.name} hurls a clay cinder pot that bursts across {target.name}'s face in hot ash.")
            degree, _ = self.control_save_degree(target, "DEX", 11, context=f"against {actor.name}'s cinder pot")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s cinder pot")
                if target.is_conscious():
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s cinder pot")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s cinder pot")
                self.say(f"{target.name} keeps their eyes, coughing ember grit out of the line.")
            else:
                self.say(f"{target.name} turns aside before the ash can blind them cleanly.")
            return
        if actor.archetype == "mireweb_spider" and actor.resources.get("venom_web", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (0 if self.has_status(hero, "restrained") else 1, hero.current_hp))
            actor.resources["venom_web"] = 0
            self.say(f"{actor.name} spits a slick sheet of mirewebbing toward {target.name}.")
            degree, _ = self.control_save_degree(target, "DEX", 11, context=f"against {actor.name}'s mireweb")
            if degree == "fail":
                self.apply_status(target, "restrained", 2, source=f"{actor.name}'s mireweb")
            elif degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s mireweb")
                self.say(f"{target.name} tears loose, but strands cling to boots and buckles.")
            else:
                self.say(f"{target.name} tears free before the webbing can set.")
            return
        if actor.archetype == "gutter_zealot" and actor.resources.get("blood_prayer", 0) > 0 and actor.current_hp <= actor.max_hp // 2:
            actor.resources["blood_prayer"] = 0
            actor.grant_temp_hp(4)
            self.apply_status(actor, "blessed", 2, source=f"{actor.name}'s blood prayer")
            self.say(f"{actor.name} smears blood across a broken sigil and steadies into fanatic focus.")
            return
        if actor.archetype == "lantern_fen_wisp" and actor.resources.get("lure_glow", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["lure_glow"] = 0
            self.say(f"{actor.name}'s pale glow drifts close, trying to draw {target.name} one bad step off the safe line.")
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s lure glow")
            if degree == "fail":
                self.apply_status(target, "charmed", 1, source=f"{actor.name}'s lure glow")
                if target.is_conscious():
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s lure glow")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s lure glow")
                self.say(f"{target.name} rejects the invitation, but the pale glow leaves one step uncertain.")
            else:
                self.say(f"{target.name} refuses the ghostlight's invitation.")
            return
        if actor.archetype == "lantern_fen_wisp" and actor.resources.get("vanish", 0) > 0 and actor.current_hp <= actor.max_hp // 2:
            actor.resources["vanish"] = 0
            self.apply_status(actor, "invisible", 1, source=f"{actor.name}'s vanish")
            self.say(f"{actor.name} gutters out and slips invisible across the dark.")
            return
        if actor.archetype == "acidmaw_burrower" and actor.resources.get("acid_spray", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["acid_spray"] = 0
            self.say(f"{actor.name} rears up and blasts acid across {target.name}.")
            if not self.saving_throw(target, "DEX", 12, context=f"against {actor.name}'s acid spray"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s acid spray",
                        outcome_kind="damage",
                    ).total,
                    damage_type="acid",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} acid damage from the spray.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "acid", 2, source=f"{actor.name}'s acid spray")
            else:
                self.say(f"{target.name} dives clear of the worst of the spray.")
            return
        if actor.archetype == "ettervine_webherd" and actor.resources.get("reel_strand", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (0 if self.has_status(hero, "restrained") else 1, hero.current_hp))
            actor.resources["reel_strand"] = 0
            self.say(f"{actor.name} snaps a root-web strand around {target.name} and hauls hard.")
            degree, _ = self.control_save_degree(target, "DEX", 13, context=f"against {actor.name}'s reeling strand")
            if degree == "fail":
                if self.has_status(target, "restrained"):
                    self.apply_status(target, "grappled", 1, source=f"{actor.name}'s reeling strand")
                else:
                    self.apply_status(target, "restrained", 2, source=f"{actor.name}'s reeling strand")
            elif degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s reeling strand")
                self.say(f"{target.name} rips the strand loose, leaving roots wound around one boot.")
            else:
                self.say(f"{target.name} slips the strand before it can lock down.")
            return
        if actor.archetype == "carrion_lash_crawler" and actor.resources.get("carrion_tentacles", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["carrion_tentacles"] = 0
            self.say(f"{actor.name}'s feeder tendrils lash toward {target.name} with grave-cold numbness.")
            degree, _ = self.control_save_degree(target, "CON", 13, context=f"against {actor.name}'s carrion tentacles")
            if degree == "fail":
                was_poisoned = self.has_status(target, "poisoned")
                self.apply_status(target, "poisoned", 2, source=f"{actor.name}'s carrion tentacles")
                if was_poisoned and target.is_conscious():
                    self.apply_status(target, "paralyzed", 1, source=f"{actor.name}'s carrion tentacles")
            elif degree == "close_fail":
                self.apply_status(target, "poisoned", 1, source=f"{actor.name}'s carrion tentacles")
                self.say(f"{target.name} shakes off the numbness, but the grave-cold toxin lingers.")
            else:
                self.say(f"{target.name} shrugs off the first wave of paralysis.")
            return
        if actor.archetype == "cache_mimic" and actor.resources.get("adhesive_grab", 0) > 0 and not any(self.has_status(hero, "grappled") for hero in conscious_heroes):
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["adhesive_grab"] = 0
            self.say(f"{actor.name}'s false lid splits into grasping adhesive cords around {target.name}.")
            degree, _ = self.control_save_degree(target, "STR", 13, context=f"against {actor.name}'s adhesive lash")
            if degree == "fail":
                self.apply_status(target, "grappled", 2, source=f"{actor.name}'s adhesive lash")
            elif degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s adhesive lash")
                self.say(f"{target.name} tears free with adhesive still dragging from their gear.")
            else:
                self.say(f"{target.name} tears free before the mimic can lock on.")
            return
        if actor.archetype == "stonegaze_skulker" and actor.resources.get("petrifying_gaze", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["petrifying_gaze"] = 0
            self.say(f"{actor.name}'s milky eyes fix on {target.name} with a mineral hunger.")
            degree, _ = self.control_save_degree(target, "CON", 13, context=f"against {actor.name}'s petrifying gaze")
            if degree == "fail":
                if self.has_status(target, "restrained"):
                    self.apply_status(target, "petrified", 1, source=f"{actor.name}'s petrifying gaze")
                else:
                    self.apply_status(target, "restrained", 1, source=f"{actor.name}'s petrifying gaze")
            elif degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s petrifying gaze")
                self.say(f"{target.name} breaks eye contact, but stone-dust still stiffens the first step.")
            else:
                self.say(f"{target.name} breaks the gaze before their limbs can lock.")
            return
        if actor.archetype == "cliff_harpy" and actor.resources.get("luring_song", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["luring_song"] = 0
            self.say(f"{actor.name}'s song cuts through the fight with the ache of a false memory.")
            degree, _ = self.control_save_degree(target, "WIS", 13, context=f"against {actor.name}'s luring song")
            if degree == "fail":
                self.apply_status(target, "charmed", 1, source=f"{actor.name}'s luring song")
                if target.is_conscious():
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s luring song")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s luring song")
                self.say(f"{target.name} hears the false memory and steps back from it late.")
            else:
                self.say(f"{target.name} hears the beauty without trusting it.")
            return
        if actor.archetype == "whispermaw_blob":
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            degree, _ = self.control_save_degree(target, "WIS", 13, context=f"against {actor.name}'s gibbering chorus")
            if degree in {"fail", "close_fail"}:
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s gibbering chorus")
            if actor.resources.get("blinding_spittle", 0) > 0:
                actor.resources["blinding_spittle"] = 0
                self.say(f"{actor.name} spits a sheet of shining mucus at {target.name}.")
                degree, _ = self.control_save_degree(target, "DEX", 13, context=f"against {actor.name}'s blinding spittle")
                if degree == "fail":
                    self.apply_status(target, "blinded", 1, source=f"{actor.name}'s blinding spittle")
                elif degree == "close_fail":
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s blinding spittle")
                    self.say(f"{target.name} twists clear of the worst of the spittle, blinking through the shine.")
                else:
                    self.say(f"{target.name} twists clear of the worst of the spittle.")
                return
        if actor.archetype == "blacklake_pincerling" and actor.resources.get("shock_spines", 0) > 0:
            target = next((hero for hero in conscious_heroes if self.has_status(hero, "grappled")), None)
            if target is not None:
                actor.resources["shock_spines"] = 0
                self.say(f"{actor.name}'s shell-spines flare and discharge into {target.name}.")
                degree, _ = self.control_save_degree(target, "CON", 13, context=f"against {actor.name}'s shock spines")
                if degree == "fail":
                    self.apply_status(target, "paralyzed", 1, source=f"{actor.name}'s shock spines")
                elif degree == "close_fail":
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s shock spines")
                    self.say(f"{target.name} grits through the numbing pulse, muscles shaking as it fades.")
                else:
                    self.say(f"{target.name} grits through the numbing pulse.")
                return
        if actor.archetype == "graveblade_wight" and actor.resources.get("sunken_command", 0) > 0 and conscious_allies:
            actor.resources["sunken_command"] = 0
            target_ally = max(conscious_allies, key=lambda ally: (ally.attack_bonus(), ally.current_hp))
            self.say(f"{actor.name} raises a dead captain's blade and snaps an old field order at {target_ally.name}.")
            self.apply_status(target_ally, "emboldened", 2, source=f"{actor.name}'s sunken command")
            return
        if actor.archetype == "graveblade_wight" and actor.resources.get("life_drain", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["life_drain"] = 0
            self.say(f"{actor.name}'s blade draws a grave-cold arc toward {target.name}.")
            if not self.saving_throw(target, "CON", 14, context=f"against {actor.name}'s life drain"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s life drain",
                        outcome_kind="damage",
                    ).total,
                    damage_type="necrotic",
                )
                self.say(f"{target.name} is drained for {self.style_damage(actual)} necrotic damage.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "exhaustion", 1, source=f"{actor.name}'s life drain")
            else:
                self.say(f"{target.name} holds onto their breath and blood both.")
            return
        if actor.archetype == "cinderflame_skull" and actor.resources.get("fire_burst", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["fire_burst"] = 0
            self.say(f"{actor.name} detonates a wheel of ember-fire around {target.name}.")
            if not self.saving_throw(target, "DEX", 14, context=f"against {actor.name}'s fire burst"):
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "3d6",
                        style="damage",
                        context_label=f"{actor.name}'s fire burst",
                        outcome_kind="damage",
                    ).total,
                    damage_type="fire",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} fire damage from the burst.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "burning", 2, source=f"{actor.name}'s fire burst")
            else:
                self.say(f"{target.name} slips through the burst with only scorched air at their back.")
            return
        if actor.archetype == "obelisk_eye":
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            ray = self.rng.choice(("terror", "blinding", "binding"))
            self.say(f"{actor.name} turns and a new shard-ray locks onto {target.name}.")
            if ray == "terror":
                degree, _ = self.control_save_degree(target, "WIS", 14, context=f"against {actor.name}'s fear ray")
                if degree == "fail":
                    self.apply_status(target, "frightened", 2, source=f"{actor.name}'s fear ray")
                elif degree == "close_fail":
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s fear ray")
                    self.say(f"{target.name} refuses the ray's pressure, but it still turns the breath cold.")
                else:
                    self.say(f"{target.name} refuses the ray's pressure.")
            elif ray == "blinding":
                degree, _ = self.control_save_degree(target, "CON", 14, context=f"against {actor.name}'s blinding ray")
                if degree == "fail":
                    self.apply_status(target, "blinded", 1, source=f"{actor.name}'s blinding ray")
                    if target.is_conscious():
                        self.apply_status(target, "reeling", 1, source=f"{actor.name}'s blinding ray")
                elif degree == "close_fail":
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s blinding ray")
                    self.say(f"{target.name} tears their vision back, shard-light still swimming in the way.")
                else:
                    self.say(f"{target.name} tears their vision back out of the shard-light.")
            else:
                degree, _ = self.control_save_degree(target, "STR", 14, context=f"against {actor.name}'s binding ray")
                if degree == "fail":
                    self.apply_status(target, "restrained", 1, source=f"{actor.name}'s binding ray")
                elif degree == "close_fail":
                    self.apply_status(target, "slowed", 1, source=f"{actor.name}'s binding ray")
                    self.say(f"{target.name} breaks the ray's grip with hardening light still clinging to their legs.")
                else:
                    self.say(f"{target.name} breaks the ray's grip before it hardens around them.")
            return
        if actor.archetype == "iron_prayer_horror" and actor.resources.get("shield_bash", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
            actor.resources["shield_bash"] = 0
            self.say(f"{actor.name} marches through the line and slams a scripture-stamped shield into {target.name}.")
            hit = self.perform_enemy_attack(actor, target, heroes, enemies, dodging)
            if hit and target.is_conscious():
                degree, _ = self.control_save_degree(target, "STR", 14, context=f"against {actor.name}'s shield bash")
                if degree == "fail":
                    self.apply_status(target, "prone", 1, source=f"{actor.name}'s shield bash")
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s shield bash")
                elif degree == "close_fail":
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s shield bash")
            return
        if actor.archetype == "hookclaw_burrower" and actor.resources.get("shriek_pulse", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["shriek_pulse"] = 0
            self.say(f"{actor.name} unleashes a shriek that bounces off every wall at once.")
            degree, _ = self.control_save_degree(target, "CON", 14, context=f"against {actor.name}'s shriek pulse")
            if degree == "fail":
                self.apply_status(target, "deafened", 2, source=f"{actor.name}'s shriek pulse")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s shriek pulse")
                self.say(f"{target.name} keeps enough hearing to stay oriented, though the echo staggers them.")
            else:
                self.say(f"{target.name} keeps enough hearing to stay oriented.")
            return
        if actor.archetype == "thunderroot_mound" and actor.resources.get("engulf", 0) > 0:
            target = next((hero for hero in conscious_heroes if self.has_status(hero, "restrained")), None)
            if target is not None:
                actor.resources["engulf"] = 0
                self.say(f"{actor.name} heaves its mass over {target.name} and tries to bury them alive in roots and mud.")
                actual = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{actor.name}'s engulf",
                        outcome_kind="damage",
                    ).total,
                    damage_type="bludgeoning",
                )
                self.say(f"{target.name} takes {self.style_damage(actual)} bludgeoning damage inside the crush.")
                self.announce_downed_target(target)
                if target.is_conscious():
                    self.apply_status(target, "grappled", 2, source=f"{actor.name}'s engulf")
                return
        if actor.archetype == "oathbroken_revenant" and actor.resources.get("vengeance_mark", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["vengeance_mark"] = 0
            actor.bond_flags["marked_target"] = target.name
            self.say(f"{actor.name} points its ruined blade at {target.name} and names a debt that death did not cancel.")
            degree, _ = self.control_save_degree(target, "WIS", 14, context=f"against {actor.name}'s vengeance mark")
            if degree == "fail":
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s vengeance mark")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s vengeance mark")
                self.say(f"{target.name} refuses the hatred, but the named debt still drags at the line.")
            else:
                self.say(f"{target.name} refuses to let the revenant's hatred define the fight.")
            return
        if actor.archetype == "choir_executioner" and actor.resources.get("hush_command", 0) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["hush_command"] = 0
            self.say(f"{actor.name} speaks one verdict, and the air around {target.name} goes murderously still.")
            degree, _ = self.control_save_degree(target, "WIS", 15, context=f"against {actor.name}'s hush command")
            if degree == "fail":
                self.apply_status(target, "incapacitated", 1, source=f"{actor.name}'s hush command")
            elif degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s hush command")
                self.say(f"{target.name} forces movement back into their limbs, late and shaking.")
            else:
                self.say(f"{target.name} forces movement back into their own limbs.")
            return
        if actor.archetype == "duskmire_matriarch" and actor.resources.get("brood_command", 0) > 0 and conscious_allies:
            actor.resources["brood_command"] = 0
            self.say(f"{actor.name} rattles the cavern with a brood-command that sends every lesser hunter lunging harder.")
            for ally in [actor, *conscious_allies]:
                self.apply_status(ally, "emboldened", 2, source=f"{actor.name}'s brood command")
            return
        if actor.archetype == "duskmire_matriarch" and actor.resources.get("shadow_web", 0) > 0:
            target = min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
            actor.resources["shadow_web"] = 0
            self.say(f"{actor.name} hurls a shadow-thick web that blots out the light around {target.name}.")
            degree, _ = self.control_save_degree(target, "DEX", 15, context=f"against {actor.name}'s shadow web")
            if degree == "fail":
                self.apply_status(target, "restrained", 2, source=f"{actor.name}'s shadow web")
                if target.is_conscious():
                    self.apply_status(target, "blinded", 1, source=f"{actor.name}'s shadow web")
            elif degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s shadow web")
                self.say(f"{target.name} cuts free, shadow strands still knotting around their gear.")
            else:
                self.say(f"{target.name} cuts free before the web can cocoon them.")
            return
        if actor.archetype == "stirge_swarm":
            attached_to = str(actor.bond_flags.get("attached_to", "")).strip()
            if attached_to:
                target = next((hero for hero in conscious_heroes if hero.name == attached_to), None)
                if target is not None:
                    actual = self.apply_damage(
                        target,
                        self.roll_with_display_bonus(
                            "1d4",
                            style="damage",
                            context_label=f"{actor.name}'s feeding swarm",
                            outcome_kind="damage",
                        ).total,
                        damage_type="piercing",
                    )
                    self.say(f"{actor.name} stays latched onto {target.name} and drains {self.style_damage(actual)} blood from the wound.")
                    self.announce_downed_target(target)
                    if target.is_conscious():
                        self.apply_status(target, "grappled", 2, source=f"{actor.name}'s feeding swarm")
                    else:
                        actor.bond_flags.pop("attached_to", None)
                    return
                actor.bond_flags.pop("attached_to", None)
        if actor.archetype == "vaelith_marr" and actor.resources.get("ritual_surge", 0) > 0:
            actor.resources["ritual_surge"] = 0
            actor.grant_temp_hp(8)
            self.apply_status(actor, "blessed", 2, source=f"{actor.name}'s grave ward")
            if conscious_allies:
                target_ally = max(conscious_allies, key=lambda ally: (ally.attack_bonus(), ally.current_hp))
                self.apply_status(target_ally, "emboldened", 2, source=f"{actor.name}'s grave ward")
            self.say(f"{actor.name} drags soot-black sigils through the air and hardens the line behind a grave ward.")
            return
        if actor.archetype == "vaelith_marr" and actor.resources.get("grave_fear", 1) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["grave_fear"] = 0
            degree, _ = self.control_save_degree(target, "WIS", 13, context=f"against {actor.name}'s sepulchral chant")
            if degree == "fail":
                self.apply_status(target, "frightened", 2, source=f"{actor.name}'s grave chant")
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s grave chant")
                self.say(f"{actor.name}'s whisper turns old burial-cold into a command that rattles {target.name} badly.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s grave chant")
                self.say(f"{target.name} refuses the grave chant, but the cold thought still clips their footing.")
                return
        if actor.archetype == "vaelith_marr" and actor.resources.get("ash_veil", 1) > 0:
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
            actor.resources["ash_veil"] = 0
            degree, _ = self.control_save_degree(target, "CON", 13, context=f"against {actor.name}'s choking ash veil")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s ash veil")
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s ash veil")
                self.say(f"{actor.name} bursts a veil of hot grave-ash across {target.name}'s face.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s ash veil")
                self.say(f"{target.name} spits out ash before it blinds them, still coughing in the line.")
                return
        if actor.archetype == "gravecaller" and actor.resources.get("grave_fear", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["grave_fear"] = 0
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s sepulchral chant")
            if degree == "fail":
                self.apply_status(target, "frightened", 2, source=f"{actor.name}'s grave chant")
                self.say(f"{actor.name}'s whisper drags old burial-cold across {target.name}'s thoughts.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s grave chant")
                self.say(f"{target.name} refuses the grave chant, but the cold thought still clips their footing.")
                return
        if actor.archetype == "gravecaller" and actor.resources.get("ash_veil", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["ash_veil"] = 0
            degree, _ = self.control_save_degree(target, "CON", 12, context=f"against {actor.name}'s choking ash veil")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s ash veil")
                self.say(f"A veil of hot grave-ash bursts over {target.name}'s face.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s ash veil")
                self.say(f"{target.name} spits out ash before it blinds them, still coughing in the line.")
                return
        if actor.archetype == "orc_bloodchief" and actor.resources.get("war_cry", 1) > 0 and actor.current_hp <= actor.max_hp:
            actor.resources["war_cry"] = 0
            actor.grant_temp_hp(6)
            self.apply_status(actor, "emboldened", 2, source=f"{actor.name}'s war cry")
            self.say(f"{actor.name} hammers a fist to their chest and roars themselves into a killing fury.")
            return
        if actor.archetype == "nothic" and actor.resources.get("weird_insight", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["weird_insight"] = 0
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s hungry stare")
            if degree == "fail":
                self.apply_status(target, "reeling", 2, source=f"{actor.name}'s weird insight")
                self.say(f"{actor.name} speaks a private fear aloud, and {target.name} stumbles under the weight of being seen.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s weird insight")
                self.say(f"{actor.name} finds the private fear, but {target.name} keeps it from becoming a wound.")
                return
        if actor.archetype == "nothic" and actor.resources.get("rotting_gaze", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["rotting_gaze"] = 0
            degree, _ = self.control_save_degree(target, "CON", 12, context=f"against {actor.name}'s rotting gaze")
            if degree == "fail":
                self.apply_status(target, "poisoned", 2, source=f"{actor.name}'s rotting gaze")
                self.say(f"{target.name} feels flesh and courage both go sick beneath {actor.name}'s stare.")
                return
            if degree == "close_fail":
                self.apply_status(target, "poisoned", 1, source=f"{actor.name}'s rotting gaze")
                self.say(f"{target.name} chokes down the sickness, but it leaves a bitter edge.")
                return
        if actor.archetype == "varyn" and actor.resources.get("silver_tongue", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["silver_tongue"] = 0
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s silver-tongued lure")
            if degree == "fail":
                self.apply_status(target, "charmed", 1, source=actor.name)
                self.say(f"{actor.name}'s measured voice bends the moment around {target.name}.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=actor.name)
                self.say(f"{target.name} hears the lure and rejects it after one costly heartbeat.")
                return
        if actor.archetype == "varyn" and actor.resources.get("binding_hex", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["binding_hex"] = 0
            degree, _ = self.control_save_degree(target, "WIS", 12, context=f"against {actor.name}'s binding hex")
            if degree == "fail":
                self.apply_status(target, "incapacitated", 1, source=f"{actor.name}'s binding hex")
                self.say(f"A ring of ash-sigils clamps around {target.name}'s thoughts and locks them in place.")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s binding hex")
                self.say(f"{target.name} breaks the hex before it locks, ash-sparks still crawling over their focus.")
                return
        if actor.archetype == "varyn" and actor.resources.get("ashen_gaze", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["ashen_gaze"] = 0
            degree, _ = self.control_save_degree(target, "CON", 12, context=f"against {actor.name}'s ash-glass gaze")
            if degree == "fail":
                self.apply_status(target, "petrified", 1, source=f"{actor.name}'s ash-glass gaze")
                return
            if degree == "close_fail":
                self.apply_status(target, "restrained", 1, source=f"{actor.name}'s ash-glass gaze")
                self.say(f"{target.name} wrenches free of the ash-glass stare before it seals.")
                return
        if actor.archetype == "bandit_archer" and actor.resources.get("snare_shot", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["snare_shot"] = 0
            degree, _ = self.control_save_degree(target, "DEX", 12, context=f"against {actor.name}'s weighted line")
            if degree == "fail":
                self.apply_status(target, "restrained", 2, source=f"{actor.name}'s weighted line")
                self.say(f"{actor.name}'s weighted line tangles around {target.name} and holds them fast.")
                return
            if degree == "close_fail":
                self.apply_status(target, "slowed", 1, source=f"{actor.name}'s weighted line")
                self.say(f"{actor.name}'s weighted line catches a boot before {target.name} kicks free.")
                return
        if actor.archetype == "bandit_archer" and actor.resources.get("ash_shot", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["ash_shot"] = 0
            degree, _ = self.control_save_degree(target, "DEX", 12, context=f"against {actor.name}'s ash-blinding shot")
            if degree == "fail":
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s ash shot")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s ash shot")
                self.say(f"{target.name} keeps sight through the ash, but loses the clean angle.")
                return
        if actor.archetype == "rukhar" and actor.resources.get("war_shout", 1) > 0:
            actor.resources["war_shout"] = 0
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            degree, _ = self.control_save_degree(target, "CON", 12, context=f"against {actor.name}'s iron-bell war shout")
            if degree == "fail":
                self.apply_status(target, "deafened", 2, source=f"{actor.name}'s war shout")
                return
            if degree == "close_fail":
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s war shout")
                self.say(f"{target.name} keeps their hearing, but the iron-bell shout still rattles bone.")
                return
        if actor.archetype == "varyn" and actor.resources.get("rally", 1) > 0 and actor.current_hp <= actor.max_hp // 2:
            actor.resources["rally"] = 0
            actor.grant_temp_hp(6)
            self.apply_status(actor, "emboldened", 2, source="Varyn's rally")
            self.say(f"{actor.name} barks an order and hardens behind 6 temporary hit points.")
            return
        priority_target = self.act2_expansion_priority_target(actor, conscious_heroes, marked_target)
        if priority_target is not None:
            target = priority_target
        elif actor.archetype == "grimlock_tunneler":
            target = min(
                conscious_heroes,
                key=lambda hero: (0 if self.has_status(hero, "reeling") else 1, hero.current_hp, hero.armor_class),
            )
        elif actor.archetype == "hookclaw_burrower":
            target = min(
                conscious_heroes,
                key=lambda hero: (0 if self.has_status(hero, "reeling") else 1, hero.current_hp, hero.armor_class),
            )
        elif actor.archetype == "ochre_slime":
            target = min(
                conscious_heroes,
                key=lambda hero: (0 if self.has_status(hero, "acid") else 1, hero.current_hp, hero.armor_class),
            )
        elif actor.archetype == "rust_shell_scuttler":
            target = min(
                conscious_heroes,
                key=lambda hero: (0 if self.has_status(hero, "acid") else 1, hero.current_hp, hero.armor_class),
            )
        elif actor.archetype == "animated_armor":
            target = min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
        elif actor.archetype == "iron_prayer_horror":
            target = min(conscious_heroes, key=lambda hero: (hero.armor_class, hero.current_hp))
        elif actor.archetype == "thunderroot_mound":
            target = min(
                conscious_heroes,
                key=lambda hero: (0 if self.has_status(hero, "restrained") else 1, hero.current_hp, hero.armor_class),
            )
        elif actor.archetype == "oathbroken_revenant":
            marked = str(actor.bond_flags.get("marked_target", "")).strip()
            target = next((hero for hero in conscious_heroes if hero.name == marked), None)
            if target is None:
                target = min(conscious_heroes, key=lambda hero: hero.current_hp)
        elif actor.archetype == "ash_brand_enforcer":
            target = marked_target or max(
                conscious_heroes,
                key=lambda hero: (
                    1 if any(self.has_status(hero, status) for status in ("blessed", "emboldened", "invisible")) else 0,
                    hero.attack_bonus(),
                    hero.current_hp,
                ),
            )
        elif actor.archetype == "brand_saboteur":
            target = marked_target or min(
                conscious_heroes,
                key=lambda hero: (
                    0 if self.has_status(hero, "blinded") else 1,
                    hero.current_hp,
                    hero.armor_class,
                ),
            )
        elif actor.archetype == "sereth_vane":
            target = marked_target or min(
                conscious_heroes,
                key=lambda hero: (
                    0 if self.has_status(hero, "reeling") else 1,
                    hero.current_hp,
                    hero.armor_class,
                ),
            )
        elif actor.archetype == "ember_channeler":
            target = marked_target or max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
        elif actor.archetype == "carrion_stalker":
            target = marked_target or min(conscious_heroes, key=lambda hero: (hero.current_hp, hero.armor_class))
        elif actor.archetype == "whispermaw_blob":
            target = max(conscious_heroes, key=lambda hero: (hero.attack_bonus(), hero.current_hp))
        else:
            target = marked_target or self.choose_weighted_enemy_target(actor, conscious_heroes)
        self.record_enemy_target_choice(actor, target)
        self.maybe_apply_enemy_stance(actor, target, conscious_heroes, conscious_allies)
        self.perform_enemy_attack(actor, target, heroes, enemies, dodging)

    def get_player_combat_options(
        self,
        actor: Character,
        encounter: Encounter,
        *,
        turn_state: TurnState | None = None,
        heroes: list[Character] | None = None,
    ) -> list[str]:
        turn_state = turn_state or TurnState()
        heroes = heroes or (self.state.party_members() if self.state is not None else [actor])
        options: list[str] = []
        if turn_state.actions_remaining > 0:
            options.append(f"Strike with {actor.weapon.name}")
            if "warrior_guard" in actor.features:
                options.append("Take Guard Stance")
            if "warrior_shove" in actor.features:
                options.append("Shove")
            if "warrior_pin" in actor.features:
                options.append("Pin")
            if "clean_line" in actor.features:
                options.append("Clean Line")
            if "dent_the_shell" in actor.features:
                options.append("Dent The Shell")
            if "hook_the_guard" in actor.features:
                options.append("Hook The Guard")
            if "reckless_cut" in actor.features:
                options.append("Reckless Cut")
            if "war_salve_strike" in actor.features:
                options.append("War-Salve Strike")
            if "open_the_ledger" in actor.features and actor.resources.get("grit", 0) > 0:
                options.append("Open The Ledger")
            if "dirty_trick" in actor.features:
                options.append("Dirty Trick")
            if "smoke_pin" in actor.features and actor.resources.get("shadow", 0) > 0:
                options.append("Smoke Pin")
            if "quiet_knife" in actor.features:
                options.append("Quiet Knife")
            if "between_plates" in actor.features and actor.resources.get("edge", 0) >= 2:
                options.append("Between Plates")
            if "sudden_end" in actor.features and actor.resources.get("edge", 0) >= 3:
                options.append("Sudden End")
            if "green_needle" in actor.features:
                options.append("Green Needle")
            if "bitter_cloud" in actor.features and actor.resources.get("toxin", 0) > 0:
                options.append("Bitter Cloud")
            if "rot_thread" in actor.features and actor.resources.get("toxin", 0) > 0:
                options.append("Rot Thread")
            if "bloom_in_the_blood" in actor.features and actor.resources.get("toxin", 0) >= 2:
                options.append("Bloom In The Blood")
            if "minor_channel" in actor.features and has_magic_points(actor, magic_point_cost("minor_channel")):
                options.append("Minor Channel (1 MP)")
            if (
                "arcane_bolt" in actor.features
                and not self.arcane_bolt_on_cooldown(actor)
                and has_magic_points(actor, self.arcane_bolt_mp_cost(actor, action_cast=True))
            ):
                options.append(f"Arcane Bolt (Action, {self.arcane_bolt_mp_cost(actor, action_cast=True)} MP)")
            if "arc_pulse" in actor.features and has_magic_points(actor, magic_point_cost("arc_pulse")):
                options.append("Arc Pulse (1 MP)")
            if "detonate_pattern" in actor.features and actor.resources.get("arc", 0) >= 2:
                options.append("Detonate Pattern (2 Arc)")
            if "ember_lance" in actor.features and has_magic_points(actor, magic_point_cost("ember_lance")):
                options.append("Ember Lance (1 MP)")
            if "frost_shard" in actor.features and has_magic_points(actor, magic_point_cost("frost_shard")):
                options.append("Frost Shard (1 MP)")
            if "volt_grasp" in actor.features and has_magic_points(actor, magic_point_cost("volt_grasp")):
                options.append("Volt Grasp (1 MP)")
            if "burning_line" in actor.features and has_magic_points(actor, magic_point_cost("burning_line")):
                options.append("Burning Line (4 MP)")
            if "lockfrost" in actor.features and has_magic_points(actor, magic_point_cost("lockfrost")):
                options.append("Lockfrost (4 MP)")
            if "blue_glass_palm" in actor.features and has_magic_points(actor, magic_point_cost("blue_glass_palm")):
                options.append("Blue Glass Palm (1 MP)")
            if "lockstep_field" in actor.features and has_magic_points(actor, magic_point_cost("lockstep_field")):
                options.append("Lockstep Field (3 MP)")
            if "field_mend" in actor.features and has_magic_points(actor, magic_point_cost("field_mend")):
                options.append("Field Mend (3 MP)")
            if "triage_line" in actor.features and has_magic_points(actor, magic_point_cost("triage_line")):
                options.append("Triage Line (3 MP)")
            if "clean_breath" in actor.features and has_magic_points(actor, magic_point_cost("clean_breath")):
                options.append("Clean Breath (2 MP)")
            if actor.resources.get("satchel", 0) > 0:
                if "redcap_tonic" in actor.features:
                    options.append("Redcap Tonic")
                if "smoke_jar" in actor.features:
                    options.append("Smoke Jar")
                if "bitter_acid" in actor.features:
                    options.append("Bitter Acid")
                if "field_stitch" in actor.features:
                    options.append("Field Stitch")
            if any(hero.current_hp == 0 and not hero.dead for hero in heroes if hero is not actor):
                options.append(self.skill_tag("MEDICINE", "Help a Downed Ally"))
            if self.has_action_item_option(actor, heroes):
                options.append("Use an Item")
            if encounter.allow_parley:
                options.append(self.skill_tag("PERSUASION / INTIMIDATION", "Attempt Parley"))
            if encounter.allow_flee:
                options.append(self.skill_tag("STEALTH", "Try to Flee"))
        if turn_state.bonus_action_available:
            if "cunning_action" in actor.features:
                options.append("Use Veil Step")
            if "warrior_rally" in actor.features and actor.resources.get("grit", 0) > 0:
                options.append("Warrior Rally")
            if "iron_draw" in actor.features:
                options.append("Iron Draw")
            if "shoulder_in" in actor.features and actor.resources.get("grit", 0) > 0:
                options.append("Shoulder In")
            if "weapon_read" in actor.features:
                options.append("Weapon Read")
            if "measure_twice" in actor.features:
                options.append("Measure Twice")
            if "style_wheel" in actor.features:
                options.append("Style Wheel")
            if "redline" in actor.features and not self.has_status(actor, "redline"):
                options.append("Redline")
            if "teeth_set" in actor.features and actor.resources.get("fury", 0) > 0:
                options.append("Teeth Set")
            if "drink_the_hurt" in actor.features and actor.resources.get("fury", 0) >= 2 and not self.has_status(actor, "drink_the_hurt"):
                options.append("Drink The Hurt")
            if "red_mark" in actor.features:
                options.append("Red Mark")
            if "blood_price" in actor.features and actor.resources.get("blood_debt", 0) > 0:
                options.append("Blood Price")
            if "rogue_mark" in actor.features:
                options.append("Mark Target")
            if "tool_read" in actor.features:
                options.append("Tool Read")
            if "rogue_feint" in actor.features:
                options.append("Feint")
            if "rogue_skirmish" in actor.features and actor.resources.get("edge", 0) > 0:
                options.append("Skirmish")
            if "false_target" in actor.features and actor.resources.get("edge", 0) > 0:
                options.append("False Target")
            if "cover_the_healer" in actor.features and actor.resources.get("shadow", 0) >= 2:
                options.append("Cover The Healer")
            if "death_mark" in actor.features:
                options.append("Death Mark")
            if "black_drop" in actor.features and actor.resources.get("toxin", 0) > 0 and not self.has_status(actor, "black_drop"):
                options.append("Black Drop")
            if (
                "arcane_bolt" in actor.features
                and not self.arcane_bolt_on_cooldown(actor)
                and has_magic_points(actor, self.arcane_bolt_mp_cost(actor))
            ):
                options.append(f"Arcane Bolt (Bonus, {self.arcane_bolt_mp_cost(actor)} MP)")
            if "pattern_read" in actor.features:
                options.append("Pattern Read")
            if "marked_angle" in actor.features and has_magic_points(actor, magic_point_cost("marked_angle")):
                options.append("Marked Angle (1 MP)")
            if "change_weather_hand" in actor.features:
                options.append("Change Weather")
            if "ground" in actor.features and not self.has_status(actor, "grounded_channel"):
                options.append("Ground")
            if "anchor_shell" in actor.features and has_magic_points(actor, magic_point_cost("anchor_shell")):
                options.append("Anchor Shell (3 MP)")
            if "pulse_restore" in actor.features and has_magic_points(actor, magic_point_cost("pulse_restore")):
                options.append("Pulse Restore (4 MP)")
            if "overflow_shell" in actor.features and actor.resources.get("flow", 0) > 0:
                options.append("Overflow Shell (1 Flow)")
            if "alchemist_quick_mix" in actor.features and not self.has_status(actor, "quick_mix"):
                options.append("Quick Mix")
            if self.can_raise_shield(actor):
                options.append("Raise Shield")
            if turn_state.attack_action_taken and self.can_make_off_hand_attack(actor):
                options.append("Make Off-Hand Strike")
            if self.inventory_dict().get("potion_healing", 0) > 0:
                options.append(DRINK_HEALING_POTION_ACTION)
            options.append("Change Stance")
        options.append("End Turn")
        return options

    def initiative_bonus(self, actor: Character) -> int:
        return (
            actor.equipment_bonuses.get("initiative", 0)
            + actor.gear_bonuses.get("initiative", 0)
            + actor.relationship_bonuses.get("initiative", 0)
        )

    def critical_threshold(self, actor: Character) -> int:
        return 19 if "improved_critical" in actor.features else 20

    def spell_attack_bonus(self, caster: Character, ability: str) -> int:
        return (
            caster.proficiency_bonus
            + caster.ability_mod(ability)
            + caster.equipment_bonuses.get("spell_attack", 0)
            + caster.relationship_bonuses.get("spell_attack", 0)
        )

    def spell_damage_bonus(self, caster: Character) -> int:
        return caster.equipment_bonuses.get("spell_damage", 0) + caster.relationship_bonuses.get("spell_damage", 0)

    def healing_bonus(self, caster: Character) -> int:
        return caster.equipment_bonuses.get("healing", 0) + caster.relationship_bonuses.get("healing", 0)

    def rogue_sneak_attack_dice(self, actor: Character) -> str:
        return "2d6" if actor.level >= 3 else "1d6"

    def combatant_menu_options(self, combatants: list[Character]) -> list[str]:
        name_width = max((len(strip_ansi(self.style_name(combatant))) for combatant in combatants), default=0)
        return [self.describe_combatant(combatant, name_width=name_width) for combatant in combatants]

    def choose_target(self, enemies: list[Character], *, prompt: str, allow_back: bool = False) -> Character | None:
        options = self.combatant_menu_options(enemies)
        if allow_back:
            options.append("Back")
        index = self.choose(prompt, options, allow_meta=False, show_hud=False)
        if allow_back and index == len(enemies) + 1:
            return None
        return enemies[index - 1]

    def choose_ally(self, allies: list[Character], *, prompt: str, allow_back: bool = False) -> Character | None:
        valid = [ally for ally in allies if not ally.dead]
        options = self.combatant_menu_options(valid)
        if allow_back:
            options.append("Back")
        index = self.choose(prompt, options, allow_meta=False, show_hud=False)
        if allow_back and index == len(valid) + 1:
            return None
        return valid[index - 1]
