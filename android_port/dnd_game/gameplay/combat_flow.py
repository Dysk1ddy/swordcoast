from __future__ import annotations

from dataclasses import dataclass

from ..items import get_item
from ..models import Character
from .encounter import Encounter


@dataclass(slots=True)
class TurnState:
    actions_remaining: int = 1
    bonus_action_available: bool = True
    attack_action_taken: bool = False
    bonus_action_spell_cast: bool = False
    non_cantrip_action_spell_cast: bool = False
    free_flee: bool = False


class CombatFlowMixin:
    def run_encounter(self, encounter: Encounter) -> str:
        assert self.state is not None
        self._in_combat = True
        heroes: list[Character] = []
        enemies: list[Character] = []
        try:
            self.banner(encounter.title)
            self.say(encounter.description, typed=True)
            self.pause_for_combat_transition()
            heroes = [member for member in self.state.party_members() if not member.dead]
            enemies = encounter.enemies
            self.introduce_encounter_characters(enemies)
            dodging: set[str] = set()
            initiative = self.roll_initiative(
                heroes,
                enemies,
                hero_bonus=encounter.hero_initiative_bonus,
                enemy_bonus=encounter.enemy_initiative_bonus,
            )
            round_number = 1
            while True:
                if not any(enemy.is_conscious() for enemy in enemies):
                    total_xp = sum(enemy.xp_value for enemy in enemies)
                    total_gold = sum(enemy.gold_value for enemy in enemies)
                    if total_xp or total_gold:
                        self.reward_party(xp=total_xp, gold=total_gold, reason=encounter.title)
                    self.collect_loot(enemies, source=encounter.title)
                    self.recover_after_battle()
                    self.say("The encounter is yours.")
                    self.pause_for_combat_transition()
                    maybe_run_post_combat_random_encounter = getattr(self, "maybe_run_post_combat_random_encounter", None)
                    if callable(maybe_run_post_combat_random_encounter):
                        maybe_run_post_combat_random_encounter(encounter)
                    return "victory"
                if not any(hero.is_conscious() for hero in heroes):
                    return "defeat"

                self.say(f"Round {round_number}")
                self.print_battlefield(heroes, enemies)
                for actor in initiative:
                    if actor.name in dodging:
                        dodging.discard(actor.name)
                    if actor.dead:
                        continue
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
                        return "defeat"
                    if not any(enemy.is_conscious() for enemy in enemies):
                        return "victory"

                    if actor in heroes:
                        result = self.hero_turn(actor, heroes, enemies, encounter, dodging)
                        if result == "fled":
                            return "fled"
                    else:
                        self.enemy_turn(actor, heroes, enemies, encounter, dodging)
                    self.tick_conditions(actor)
                round_number += 1
        finally:
            self.clear_after_encounter([*heroes, *enemies])
            self._in_combat = False

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
            choice = self.choose(self.turn_prompt(actor, turn_state), options, allow_meta=False)
            action = self.choice_text(options[choice - 1])
            if action == "End Turn":
                return None
            if action == "Use Action Surge":
                if self.activate_action_surge(actor, turn_state):
                    continue
                return None
            if action == "Attack with Divine Smite":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Divine Smite.", allow_back=True)
                if target is None:
                    continue
                self.perform_weapon_attack(actor, target, heroes, enemies, dodging, use_smite=True)
                turn_state.actions_remaining -= 1
                turn_state.attack_action_taken = True
                continue
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
            if action == "Use Martial Arts":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Martial Arts.", allow_back=True)
                if target is None:
                    continue
                self.use_martial_arts(actor, target, heroes, enemies, dodging)
                turn_state.bonus_action_available = False
                continue
            if action == "Use Flurry of Blows":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Flurry of Blows.", allow_back=True)
                if target is None:
                    continue
                self.use_flurry_of_blows(actor, target, heroes, enemies, dodging)
                turn_state.bonus_action_available = False
                continue
            if action == "Use Patient Defense":
                if not actor.spend_resource("ki"):
                    self.say(f"{self.style_name(actor)} has no ki left for Patient Defense.")
                    return None
                dodging.add(actor.name)
                self.say(f"{self.style_name(actor)} spends 1 ki point and slips into Patient Defense.")
                turn_state.bonus_action_available = False
                continue
            if action == "Use Step of the Wind":
                if not actor.spend_resource("ki"):
                    self.say(f"{self.style_name(actor)} has no ki left for Step of the Wind.")
                    return None
                step_choice = self.choose(
                    "Step of the Wind lets you move on sudden breath and balance.",
                    [
                        self.action_option("Dash through the fight and set up a clean escape."),
                        self.action_option("Disengage and peel free of immediate pressure."),
                        "Back",
                    ],
                    allow_meta=False,
                )
                if step_choice == 3:
                    actor.resources["ki"] += 1
                    continue
                if step_choice == 1:
                    turn_state.free_flee = True
                    self.apply_status(actor, "emboldened", 1, source="Step of the Wind")
                    self.say(f"{self.style_name(actor)} bursts through the melee with impossible speed.")
                else:
                    turn_state.free_flee = True
                    self.say(f"{self.style_name(actor)} flows clear of the immediate crush.")
                turn_state.bonus_action_available = False
                continue
            if action == "Use Cunning Action":
                cunning_choice = self.choose(
                    "Choose a Cunning Action.",
                    [
                        self.skill_tag("STEALTH", self.action_option("Hide in the fight's blind spots.")),
                        self.action_option("Dash and line up a clean escape."),
                        self.action_option("Disengage and break away safely."),
                        "Back",
                    ],
                    allow_meta=False,
                )
                if cunning_choice == 4:
                    continue
                if cunning_choice == 1:
                    success = self.skill_check(actor, "Stealth", 12, context="to vanish back into the melee's blind spots")
                    if success:
                        self.apply_status(actor, "invisible", 2, source="Cunning Action")
                        self.say(f"{self.style_name(actor)} slips back out of the enemy's direct line.")
                    else:
                        self.say(f"{self.style_name(actor)} cannot quite disappear into the chaos.")
                elif cunning_choice == 2:
                    turn_state.free_flee = True
                    self.apply_status(actor, "emboldened", 1, source="Cunning Action: Dash")
                    self.say(f"{self.style_name(actor)} surges for open ground and can break away cleanly this turn.")
                else:
                    turn_state.free_flee = True
                    self.say(f"{self.style_name(actor)} disengages cleanly and can flee without needing another opening this turn.")
                turn_state.bonus_action_available = False
                continue
            if action == "Enter Rage":
                self.use_rage(actor)
                turn_state.bonus_action_available = False
                continue
            if action == "Use Second Wind":
                self.use_second_wind(actor)
                turn_state.bonus_action_available = False
                continue
            if action == "Use Bardic Inspiration":
                target = self.choose_ally(heroes, prompt="Choose an ally to inspire.", allow_back=True)
                if target is None:
                    continue
                self.use_bardic_inspiration(actor, target)
                turn_state.bonus_action_available = False
                continue
            if action == "Use Lay on Hands":
                target = self.choose_ally(heroes, prompt="Choose an ally to heal with Lay on Hands.", allow_back=True)
                if target is None:
                    continue
                self.use_lay_on_hands(actor, target)
                turn_state.actions_remaining -= 1
                continue
            if action == "Invoke Channel Divinity":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Channel Divinity.", allow_back=True)
                if target is None:
                    continue
                self.use_channel_divinity(actor, target)
                turn_state.actions_remaining -= 1
                continue
            if action == "Cast Sacred Flame":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Sacred Flame.", allow_back=True)
                if target is None:
                    continue
                self.cast_sacred_flame(actor, target)
                turn_state.actions_remaining -= 1
                continue
            if action == "Cast Cure Wounds":
                target = self.choose_ally(heroes, prompt="Choose an ally to heal with Cure Wounds.", allow_back=True)
                if target is None:
                    continue
                self.cast_cure_wounds(actor, target)
                turn_state.actions_remaining -= 1
                turn_state.non_cantrip_action_spell_cast = True
                continue
            if action == "Cast Healing Word":
                target = self.choose_ally(heroes, prompt="Choose an ally to heal with Healing Word.", allow_back=True)
                if target is None:
                    continue
                self.cast_healing_word(actor, target)
                turn_state.bonus_action_available = False
                turn_state.bonus_action_spell_cast = True
                continue
            if action == "Cast Produce Flame":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Produce Flame.", allow_back=True)
                if target is None:
                    continue
                self.cast_produce_flame(actor, target, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Cast Vicious Mockery":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Vicious Mockery.", allow_back=True)
                if target is None:
                    continue
                self.cast_vicious_mockery(actor, target)
                turn_state.actions_remaining -= 1
                continue
            if action == "Cast Fire Bolt":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Fire Bolt.", allow_back=True)
                if target is None:
                    continue
                self.cast_fire_bolt(actor, target, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Cast Eldritch Blast":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Eldritch Blast.", allow_back=True)
                if target is None:
                    continue
                self.cast_eldritch_blast(actor, target, dodging)
                turn_state.actions_remaining -= 1
                continue
            if action == "Cast Magic Missile":
                target = self.choose_target(conscious_enemies, prompt="Choose a target for Magic Missile.", allow_back=True)
                if target is None:
                    continue
                self.cast_magic_missile(actor, target)
                turn_state.actions_remaining -= 1
                turn_state.non_cantrip_action_spell_cast = True
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
                    f"{self.style_name(actor)} focuses on defense. Attacks against them have disadvantage until their next turn."
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
                success = self.skill_check(actor, "Stealth", 13, context="to break from the fight")
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

    def activate_action_surge(self, actor: Character, turn_state: TurnState) -> bool:
        if not actor.spend_resource("action_surge"):
            self.say(f"{self.style_name(actor)} has already spent Action Surge this rest.")
            return False
        turn_state.actions_remaining += 1
        self.say(f"{self.style_name(actor)} digs deep and surges into another action.")
        return True

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
        if actor.class_name == "Fighter" and actor.resources.get("second_wind", 0) > 0 and actor.current_hp <= actor.max_hp // 2:
            self.use_second_wind(actor)
            return
        if actor.class_name == "Barbarian" and actor.resources.get("rage", 0) > 0 and not self.has_status(actor, "emboldened"):
            self.use_rage(actor)
            return
        if actor.class_name == "Bard" and actor.resources.get("bardic_inspiration", 0) > 0:
            target = min([ally for ally in heroes if ally.is_conscious()], key=lambda ally: ally.current_hp)
            if not self.has_status(target, "blessed"):
                self.use_bardic_inspiration(actor, target)
                return
        if actor.class_name == "Cleric" and actor.resources.get("spell_slots", 0) > 0:
            wounded = [ally for ally in heroes if not ally.dead and ally.current_hp < ally.max_hp]
            if wounded:
                target = min(wounded, key=lambda ally: ally.current_hp)
                if target.current_hp <= max(1, target.max_hp // 2):
                    self.cast_cure_wounds(actor, target)
                    return
        if actor.class_name == "Paladin":
            leaders = [enemy for enemy in conscious_enemies if "leader" in enemy.tags]
            if actor.resources.get("channel_divinity", 0) > 0 and leaders:
                self.use_channel_divinity(actor, leaders[0])
                return
            wounded = [ally for ally in heroes if ally.is_conscious() and ally.current_hp < max(1, ally.max_hp // 2)]
            if actor.resources.get("lay_on_hands", 0) > 0 and wounded:
                self.use_lay_on_hands(actor, min(wounded, key=lambda ally: ally.current_hp))
                return
        if actor.class_name == "Wizard":
            leaders = [enemy for enemy in conscious_enemies if "leader" in enemy.tags]
            if actor.resources.get("spell_slots", 0) > 0 and leaders:
                self.cast_magic_missile(actor, leaders[0])
                return
            self.cast_fire_bolt(actor, conscious_enemies[0], dodging)
            return
        if actor.class_name == "Bard":
            self.cast_vicious_mockery(actor, conscious_enemies[0])
            return
        if actor.class_name == "Cleric":
            self.cast_sacred_flame(actor, conscious_enemies[0])
            return
        if actor.class_name == "Warlock":
            self.cast_eldritch_blast(actor, conscious_enemies[0], dodging)
            return
        if actor.class_name == "Sorcerer":
            if actor.resources.get("spell_slots", 0) > 0:
                self.cast_magic_missile(actor, conscious_enemies[0])
                return
            self.cast_fire_bolt(actor, conscious_enemies[0], dodging)
            return
        if actor.class_name == "Monk":
            self.use_martial_arts(actor, conscious_enemies[0], heroes, enemies, dodging)
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
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} falters and cannot press a hostile attack while Charmed.")
            return
        if actor.archetype == "varyn" and actor.resources.get("silver_tongue", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["silver_tongue"] = 0
            if not self.saving_throw(target, "WIS", 12, context=f"against {actor.name}'s silver-tongued lure"):
                self.apply_status(target, "charmed", 1, source=actor.name)
                self.say(f"{actor.name}'s measured voice bends the moment around {target.name}.")
                return
        if actor.archetype == "varyn" and actor.resources.get("binding_hex", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["binding_hex"] = 0
            if not self.saving_throw(target, "WIS", 12, context=f"against {actor.name}'s binding hex"):
                self.apply_status(target, "incapacitated", 1, source=f"{actor.name}'s binding hex")
                self.say(f"A ring of ash-sigils clamps around {target.name}'s thoughts and locks them in place.")
                return
        if actor.archetype == "varyn" and actor.resources.get("ashen_gaze", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["ashen_gaze"] = 0
            if not self.saving_throw(target, "CON", 12, context=f"against {actor.name}'s ash-glass gaze"):
                self.apply_status(target, "petrified", 1, source=f"{actor.name}'s ash-glass gaze")
                return
        if actor.archetype == "bandit_archer" and actor.resources.get("snare_shot", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["snare_shot"] = 0
            if not self.saving_throw(target, "DEX", 12, context=f"against {actor.name}'s weighted line"):
                self.apply_status(target, "restrained", 2, source=f"{actor.name}'s weighted line")
                self.say(f"{actor.name}'s weighted line tangles around {target.name} and holds them fast.")
                return
        if actor.archetype == "bandit_archer" and actor.resources.get("ash_shot", 1) > 0:
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            actor.resources["ash_shot"] = 0
            if not self.saving_throw(target, "DEX", 12, context=f"against {actor.name}'s ash-blinding shot"):
                self.apply_status(target, "blinded", 1, source=f"{actor.name}'s ash shot")
                return
        if actor.archetype == "rukhar" and actor.resources.get("war_shout", 1) > 0:
            actor.resources["war_shout"] = 0
            target = min(conscious_heroes, key=lambda hero: hero.current_hp)
            if not self.saving_throw(target, "CON", 12, context=f"against {actor.name}'s iron-bell war shout"):
                self.apply_status(target, "deafened", 2, source=f"{actor.name}'s war shout")
                return
        if actor.archetype == "varyn" and actor.resources.get("rally", 1) > 0 and actor.current_hp <= actor.max_hp // 2:
            actor.resources["rally"] = 0
            actor.grant_temp_hp(6)
            self.apply_status(actor, "emboldened", 2, source="Varyn's rally")
            self.say(f"{actor.name} barks an order and hardens behind 6 temporary hit points.")
            return
        target = min(conscious_heroes, key=lambda hero: hero.current_hp)
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
        if "action_surge" in actor.features and actor.resources.get("action_surge", 0) > 0:
            options.append("Use Action Surge")
        if turn_state.actions_remaining > 0:
            options.append(f"Attack with {actor.weapon.name}")
            if actor.class_name == "Paladin" and actor.resources.get("spell_slots", 0) > 0:
                options.append("Attack with Divine Smite")
            if actor.class_name == "Paladin" and actor.resources.get("lay_on_hands", 0) > 0:
                options.append("Use Lay on Hands")
            if actor.class_name == "Cleric":
                if actor.resources.get("channel_divinity", 0) > 0:
                    options.append("Invoke Channel Divinity")
                options.append("Cast Sacred Flame")
                if actor.resources.get("spell_slots", 0) > 0 and not turn_state.bonus_action_spell_cast:
                    options.append("Cast Cure Wounds")
            if actor.class_name == "Druid":
                options.append("Cast Produce Flame")
                if actor.resources.get("spell_slots", 0) > 0 and not turn_state.bonus_action_spell_cast:
                    options.append("Cast Cure Wounds")
            if actor.class_name == "Bard":
                options.append("Cast Vicious Mockery")
                if actor.resources.get("spell_slots", 0) > 0 and not turn_state.bonus_action_spell_cast:
                    options.append("Cast Cure Wounds")
            if actor.class_name == "Sorcerer":
                options.append("Cast Fire Bolt")
                if actor.resources.get("spell_slots", 0) > 0 and not turn_state.bonus_action_spell_cast:
                    options.append("Cast Magic Missile")
            if actor.class_name == "Warlock":
                options.append("Cast Eldritch Blast")
            if actor.class_name == "Wizard":
                options.append("Cast Fire Bolt")
                if actor.resources.get("spell_slots", 0) > 0 and not turn_state.bonus_action_spell_cast:
                    options.append("Cast Magic Missile")
            if any(hero.current_hp == 0 and not hero.dead for hero in heroes if hero is not actor):
                options.append(self.skill_tag("MEDICINE", "Help a Downed Ally"))
            if self.has_action_item_option(actor, heroes):
                options.append("Use an Item")
            if encounter.allow_parley:
                options.append(self.skill_tag("PERSUASION / INTIMIDATION", "Attempt Parley"))
            if encounter.allow_flee:
                options.append(self.skill_tag("STEALTH", "Try to Flee"))
            options.append("Take the Dodge action")
        if turn_state.bonus_action_available:
            if actor.class_name == "Monk" and turn_state.attack_action_taken:
                options.append("Use Martial Arts")
                if actor.resources.get("ki", 0) > 0:
                    options.append("Use Flurry of Blows")
            if actor.class_name == "Monk" and actor.resources.get("ki", 0) > 0:
                options.append("Use Patient Defense")
                options.append("Use Step of the Wind")
            if "cunning_action" in actor.features:
                options.append("Use Cunning Action")
            if actor.class_name == "Barbarian" and actor.resources.get("rage", 0) > 0 and not self.has_status(actor, "emboldened"):
                options.append("Enter Rage")
            if actor.class_name == "Bard" and actor.resources.get("bardic_inspiration", 0) > 0:
                options.append("Use Bardic Inspiration")
            if actor.class_name == "Fighter" and actor.resources.get("second_wind", 0) > 0:
                options.append("Use Second Wind")
            if actor.class_name in {"Bard", "Cleric", "Druid"} and actor.resources.get("spell_slots", 0) > 0 and not turn_state.non_cantrip_action_spell_cast:
                options.append("Cast Healing Word")
            if turn_state.attack_action_taken and self.can_make_off_hand_attack(actor):
                options.append("Make Off-Hand Attack")
            if self.inventory_dict().get("potion_healing", 0) > 0:
                options.append("Drink a Healing Potion")
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

    def choose_target(self, enemies: list[Character], *, prompt: str, allow_back: bool = False) -> Character | None:
        options = [self.describe_combatant(enemy) for enemy in enemies]
        if allow_back:
            options.append("Back")
        index = self.choose(prompt, options, allow_meta=False)
        if allow_back and index == len(enemies) + 1:
            return None
        return enemies[index - 1]

    def choose_ally(self, allies: list[Character], *, prompt: str, allow_back: bool = False) -> Character | None:
        valid = [ally for ally in allies if not ally.dead]
        options = [self.describe_combatant(ally) for ally in valid]
        if allow_back:
            options.append("Back")
        index = self.choose(prompt, options, allow_meta=False)
        if allow_back and index == len(valid) + 1:
            return None
        return valid[index - 1]
