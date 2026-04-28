from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from ..data.story.public_terms import ability_label, spell_label
from ..dice import D20Outcome, roll, roll_d20
from ..items import ITEMS
from ..ui.colors import rich_style_name, strip_ansi
from ..ui.rich_render import Group, Panel, box
from .class_framework import CLASS_RESOURCE_COLORS, CLASS_RESOURCE_LABELS, CLASS_RESOURCE_ORDER
from .class_framework import actor_uses_class_resource, class_resource_cap, clear_class_combat_state
from .class_framework import synchronize_class_resources
from .difficulty_policy import ACT_DIFFICULTY_BANDS, clamp_dc_to_band
from .magic_points import current_magic_points, magic_point_cost, spend_magic_points
from .status_effects import STANCE_STATUS_BY_KEY, STANCE_STATUS_NAMES


PHYSICAL_DEFENSE_DAMAGE_TYPES = {"", "slashing", "piercing", "bludgeoning"}
BASE_ATTACK_TARGET_NUMBER = 8
STANCE_LABELS = {
    "neutral": "Neutral",
    "guard": "Guard",
    "brace": "Brace",
    "mobile": "Mobile",
    "aggressive": "Aggressive",
    "aim": "Aim",
    "press": "Press",
}
STANCE_SUMMARIES = {
    "neutral": "No stance modifiers.",
    "guard": "+20% Defense, +2 Stability, -2 Accuracy.",
    "brace": "+10% Defense, +4 Stability, -1 Avoidance, -1 Accuracy.",
    "mobile": "+2 Avoidance, +2 retreat checks, -5% Defense, -1 Stability.",
    "aggressive": "+2 Accuracy, +2 weapon damage, -10% Defense, -1 Avoidance.",
    "aim": "+2 Accuracy, -5% Defense, -2 Avoidance, -1 Stability.",
    "press": "+1 Accuracy, +10% Armor Break, +1 Stability, -5% Defense, -1 Avoidance.",
}
STANCE_ORDER = ("neutral", "guard", "brace", "mobile", "aggressive", "aim", "press")
WEAPON_MASTER_STYLE_LABELS = {
    "cleave": "Cleave",
    "pierce": "Pierce",
    "crush": "Crush",
    "hook": "Hook",
}
WEAPON_MASTER_STYLE_SUMMARIES = {
    "cleave": "Reliable cuts against low-Defense targets.",
    "pierce": "+1 Accuracy; critical hits ignore 10% Defense.",
    "crush": "Armor pressure; strong hits crack Defense.",
    "hook": "+1 Accuracy against Guard; hits disrupt Guard or Stability.",
}
WEAPON_MASTER_STYLE_ORDER = ("cleave", "pierce", "crush", "hook")
ELEMENTALIST_ELEMENT_LABELS = {
    "fire": "Fire",
    "cold": "Cold",
    "lightning": "Lightning",
}
ELEMENTALIST_ELEMENT_ORDER = ("fire", "cold", "lightning")


@dataclass(slots=True)
class DamageResolution:
    raw_damage: int = 0
    resisted_damage: int = 0
    defense_percent: int = 0
    armor_break_percent: int = 0
    mitigated_damage: int = 0
    ward_absorbed: int = 0
    temp_hp_absorbed: int = 0
    hp_damage: int = 0
    glance: bool = False
    wound: bool = False


class CombatResolutionMixin:
    @contextmanager
    def temporary_roll_display_bonus(self, bonus: int):
        with self.temporary_roll_animation_metadata(display_bonus=bonus):
            yield

    def roll_with_display_bonus(
        self,
        expression: str,
        *,
        bonus: int = 0,
        critical: bool = False,
        style: str | None = None,
        context_label: str | None = None,
        outcome_kind: str | None = None,
    ):
        return self.roll_with_animation_context(
            expression,
            bonus=bonus,
            critical=critical,
            style=style,
            context_label=context_label,
            outcome_kind=outcome_kind,
        )

    def spend_mp_for_spell(self, caster, spell_id: str, spell_name: str) -> bool:
        cost = magic_point_cost(spell_id, caster)
        if spend_magic_points(caster, cost):
            return True
        channel_name = spell_label(spell_id, spell_name)
        self.say(
            f"{self.style_name(caster)} needs {cost} MP to use {channel_name}, "
            f"but has {current_magic_points(caster)}."
        )
        return False

    def record_opening_tutorial_combat_event(self, event_key: str, actor=None, target=None) -> None:
        tutorial_tracker = getattr(self, "record_opening_tutorial_event", None)
        if not callable(tutorial_tracker):
            return
        tutorial_tracker(
            event_key,
            actor_name=getattr(actor, "name", ""),
            target_name=getattr(target, "name", ""),
            class_name=getattr(actor, "class_name", ""),
        )

    def equipped_weapon_item(self, actor):
        return ITEMS.get(actor.equipment_slots.get("main_hand", "")) if getattr(actor, "equipment_slots", None) else None

    def equipped_off_hand_weapon_item(self, actor):
        if not getattr(actor, "equipment_slots", None):
            return None
        item = ITEMS.get(actor.equipment_slots.get("off_hand", ""))
        if item is None or item.weapon is None:
            return None
        return item

    def actor_is_dodging(self, actor) -> bool:
        return getattr(actor, "name", None) in getattr(self, "_active_dodging_names", frozenset())

    def dodge_applies_against_attacker(self, defender, attacker) -> bool:
        if not self.actor_is_dodging(defender):
            return False
        defender_features = set(getattr(defender, "features", []))
        if self.has_status(defender, "blinded") and "blind_sense" not in defender_features:
            return False
        if self.has_status(attacker, "invisible") and "blind_sense" not in defender_features:
            return False
        return True

    def trigger_blacklake_adjudicator_reflection(self, attacker, target, *, source: str) -> None:
        if getattr(target, "archetype", "") != "blacklake_adjudicator":
            return
        if getattr(attacker, "dead", False) or getattr(attacker, "current_hp", 0) <= 0:
            return
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        if current_round and int(target.bond_flags.get("mirror_verdict_round", -1)) == current_round:
            return
        target.bond_flags["mirror_verdict_round"] = current_round
        actual = self.apply_damage(
            attacker,
            self.roll_with_display_bonus(
                "1d6",
                style="damage",
                context_label=f"{target.name}'s mirror verdict",
                outcome_kind="damage",
            ).total,
            damage_type="force",
        )
        self.say(f"{target.name}'s mirror verdict throws {self.style_damage(actual)} force back into {attacker.name} from {source}.")
        self.announce_downed_target(attacker)

    def break_invisibility_from_hostile_action(self, actor) -> None:
        if self.has_status(actor, "invisible"):
            self.clear_status(actor, "invisible")
            self.say(f"{self.style_name(actor)} gives away their position by striking.")

    def weapon_attack_ability_for(self, actor, weapon) -> str:
        if weapon.ability == "SPELL":
            return actor.spellcasting_ability or "INT"
        if weapon.ability == "DEX":
            return "DEX"
        if weapon.ability == "FINESSE" or weapon.finesse:
            return "DEX" if actor.ability_mod("DEX") >= actor.ability_mod("STR") else "STR"
        return weapon.ability

    def weapon_attack_bonus_for(self, actor, weapon) -> int:
        return (
            actor.ability_mod(self.weapon_attack_ability_for(actor, weapon))
            + actor.proficiency_bonus
            + weapon.to_hit_bonus
            + actor.equipment_bonuses.get("attack", 0)
            + actor.gear_bonuses.get("attack", 0)
            + actor.relationship_bonuses.get("attack", 0)
        )

    def weapon_damage_bonus_for(self, actor, weapon, *, include_ability_mod: bool = True) -> int:
        ability_mod = actor.ability_mod(self.weapon_attack_ability_for(actor, weapon))
        if not include_ability_mod:
            ability_mod = min(0, ability_mod)
        return (
            ability_mod
            + weapon.damage_bonus
            + actor.equipment_bonuses.get("damage", 0)
            + actor.gear_bonuses.get("damage", 0)
            + actor.relationship_bonuses.get("damage", 0)
        )

    def status_accuracy_modifier(self, actor) -> int:
        return self.status_value(actor, "attack_bonus") - self.status_value(actor, "attack_penalty")

    def target_accuracy_modifier(self, target) -> int:
        return self.status_value(target, "incoming_attack_bonus") - self.status_value(target, "incoming_attack_penalty")

    def status_damage_modifier(self, actor) -> int:
        total = self.status_value(actor, "damage_bonus")
        if self.has_status(actor, "redline"):
            total += max(0, int(actor.bond_flags.get("berserker_redline_damage_bonus", 0)))
        if "red_work_rhythm" in getattr(actor, "features", []) and actor.max_hp > 0:
            hp_percent = actor.current_hp * 100 // actor.max_hp
            if 30 <= hp_percent <= 69:
                total += 1
        return total

    def current_difficulty_act(self) -> int:
        if self.state is None:
            return 1
        return 2 if int(getattr(self.state, "current_act", 1)) >= 2 else 1

    def current_act1_room_role(self) -> str | None:
        dungeon_getter = getattr(self, "current_act1_dungeon", None)
        room_getter = getattr(self, "current_act1_room", None)
        if not callable(dungeon_getter) or not callable(room_getter):
            return None
        try:
            dungeon = dungeon_getter()
            if dungeon is None:
                return None
            room = room_getter(dungeon)
        except Exception:
            return None
        role = str(getattr(room, "role", "")).strip().lower()
        return role or None

    def is_recruitment_check(self, context: str) -> bool:
        lowered = context.lower()
        companion_markers = ("bryn", "nim", "irielle", "kaelis", "rhogar", "tolan")
        return "convince" in lowered and any(marker in lowered for marker in companion_markers)

    def in_boss_difficulty_scene(self) -> bool:
        if self.state is None:
            return False
        room_role = self.current_act1_room_role()
        if room_role == "boss":
            return True
        return self.state.current_scene in {"meridian_forge"}

    def in_hostile_skill_scene(self) -> bool:
        if self.state is None:
            return False
        room_role = self.current_act1_room_role()
        if room_role is not None:
            return room_role in {"entrance", "combat", "event", "treasure", "boss"}
        return self.state.current_scene in {
            "background_prologue",
            "road_ambush",
            "greywake_survey_camp",
            "stonehollow_dig",
            "act2_midpoint_convergence",
            "broken_prospect",
            "south_adit",
            "resonant_vault_outer_galleries",
            "blackglass_causeway",
            "meridian_forge",
        }

    def skill_check_category(self, context: str) -> str:
        if self.is_recruitment_check(context):
            return "recruitment"
        if self.in_boss_difficulty_scene():
            return "boss"
        if getattr(self, "_in_combat", False):
            return "combat"
        if getattr(self, "_random_encounter_active", False):
            return "random"
        if self.in_hostile_skill_scene():
            return "combat"
        return "regular"

    def effective_skill_dc(self, dc: int, *, context: str) -> int:
        if self.state is None:
            return dc
        act = self.current_difficulty_act()
        category = self.skill_check_category(context)
        minimum_tier, maximum_tier = ACT_DIFFICULTY_BANDS[act][category]
        return clamp_dc_to_band(dc, minimum_tier, maximum_tier)

    def ally_pressure_bonus(self, attacker, allies, *, ranged: bool) -> int:
        if not any(ally.is_conscious() and ally is not attacker for ally in allies):
            return 0
        # A light flanking-style bonus keeps fights dynamic without granting
        # near-constant full edge.
        return 1 if ranged else 2

    def has_damage_resistance(self, actor, damage_type: str) -> bool:
        if not damage_type:
            return False
        if actor.gear_bonuses.get(f"resist_{damage_type}", 0):
            return True
        return self.has_status(actor, f"resist_{damage_type}")

    def damage_type_uses_defense(self, damage_type: str) -> bool:
        return (damage_type or "").lower() in PHYSICAL_DEFENSE_DAMAGE_TYPES

    def armor_defense_percent(self, armor) -> int:
        if armor is None:
            return 0
        explicit = getattr(armor, "defense_percent", None)
        if explicit is not None:
            return max(0, int(explicit))
        armor_type = str(getattr(armor, "armor_type", "") or "").lower()
        base_ac = int(getattr(armor, "base_ac", 10))
        if armor_type == "clothing":
            return max(0, (base_ac - 10) * 5)
        if getattr(armor, "heavy", False) or armor_type == "heavy":
            return min(45, 35 + max(0, base_ac - 16) * 10)
        if armor_type == "medium":
            return 20 if base_ac <= 13 else min(35, 25 + max(0, base_ac - 14) * 5)
        if armor_type == "light":
            return min(25, 10 + max(0, base_ac - 11) * 5)
        return min(70, max(0, (base_ac - 10) * 5))

    def defense_bonus_percent(self, actor) -> int:
        total = 0
        for bonuses in (actor.equipment_bonuses, actor.gear_bonuses, actor.relationship_bonuses):
            total += int(bonuses.get("defense_percent", 0))
            total += int(bonuses.get("defense", 0)) * 5
            total += int(bonuses.get("AC", 0)) * 5
        if self.has_status(actor, "raised_shield") and getattr(actor, "shield", False):
            total += self.raised_shield_defense_percent(actor)
        total += self.status_value(actor, "defense_bonus_percent")
        if self.has_status(actor, "anchor_shell") and int(actor.resources.get("ward", 0)) > 0:
            total += 5
        return total

    def defense_cap_percent(self, actor) -> int:
        bonus_cap = 0
        for bonuses in (actor.equipment_bonuses, actor.gear_bonuses, actor.relationship_bonuses):
            cap = int(bonuses.get("defense_cap_percent", bonuses.get("defense_cap", 0)))
            if cap > 0:
                bonus_cap = max(bonus_cap, cap)
        armor = getattr(actor, "armor", None)
        armor_cap = int(getattr(armor, "defense_cap_percent", 0) or 0)
        armor_type = str(getattr(armor, "armor_type", "") or "").lower() if armor is not None else ""
        if armor_cap <= 0:
            if armor is None or (armor_type in {"clothing", "light"} and not getattr(armor, "heavy", False)):
                armor_cap = 45
            elif getattr(armor, "heavy", False) or armor_type == "heavy":
                armor_cap = 80
            else:
                armor_cap = 75
        if "heavy_armor_specialist" in getattr(actor, "features", []):
            armor_cap = max(armor_cap, 80)
        return max(bonus_cap, armor_cap)

    def shield_defense_percent(self, actor) -> int:
        if not getattr(actor, "shield", False):
            return 0
        total = 0
        for bonuses in (actor.equipment_bonuses, actor.gear_bonuses, actor.relationship_bonuses):
            total += int(bonuses.get("shield_defense_percent", 0))
            total += int(bonuses.get("shield_defense", 0)) * 5
        return total if total > 0 else 5

    def raised_shield_defense_percent(self, actor) -> int:
        total = 0
        for bonuses in (actor.equipment_bonuses, actor.gear_bonuses, actor.relationship_bonuses):
            total += int(bonuses.get("raised_shield_defense_percent", 0))
            total += int(bonuses.get("raised_shield_defense", 0)) * 5
        return total if total > 0 else 10

    def total_armor_break_percent(self, target, *, source_actor=None, incoming_percent: int = 0, incoming_steps: int = 0) -> int:
        total = max(0, int(incoming_percent)) + max(0, int(incoming_steps)) * 10
        if int(getattr(target, "conditions", {}).get("armor_broken", 0)) > 0:
            total += 10
        total += self.status_value(target, "armor_break_percent")
        if source_actor is not None:
            for bonuses in (source_actor.equipment_bonuses, source_actor.gear_bonuses, source_actor.relationship_bonuses):
                total += int(bonuses.get("armor_break_percent", 0))
                total += int(bonuses.get("armor_break", 0)) * 10
            total += self.status_value(source_actor, "outgoing_armor_break_percent")
            total += self.status_value(source_actor, "armor_break_percent")
            total += self.status_value(source_actor, "armor_break") * 10
        return max(0, total)

    def effective_defense_percent(
        self,
        actor,
        *,
        damage_type: str = "",
        armor_break_percent: int = 0,
    ) -> int:
        if not self.damage_type_uses_defense(damage_type):
            return 0
        defense = self.armor_defense_percent(getattr(actor, "armor", None))
        defense += self.shield_defense_percent(actor)
        defense += self.defense_bonus_percent(actor)
        defense -= max(0, int(armor_break_percent))
        return max(0, min(defense, self.defense_cap_percent(actor)))

    def effective_avoidance(self, actor) -> int:
        if any(self.has_status(actor, status) for status in ("stunned", "paralyzed", "unconscious")):
            return -5
        dex_mod = actor.ability_mod("DEX")
        armor = getattr(actor, "armor", None)
        if armor is not None:
            cap = 0 if getattr(armor, "heavy", False) else getattr(armor, "dex_cap", None)
            if cap is not None:
                dex_mod = min(dex_mod, int(cap))
        total = dex_mod
        for bonuses in (actor.equipment_bonuses, actor.gear_bonuses, actor.relationship_bonuses):
            total += int(bonuses.get("avoidance", 0))
            total += int(bonuses.get("avoidance_bonus", 0))
        total += self.status_value(actor, "avoidance_bonus")
        total -= self.status_value(actor, "avoidance_penalty")
        return total

    def effective_attack_target_number(self, actor) -> int:
        return max(1, BASE_ATTACK_TARGET_NUMBER + self.effective_avoidance(actor))

    def attack_target_label(self, target_number: int) -> str:
        return f"Contact {target_number}"

    def last_damage_resolution(self) -> DamageResolution:
        return getattr(self, "_last_damage_resolution", DamageResolution())

    def last_damage_was_glance(self) -> bool:
        return self.last_damage_resolution().glance

    def last_damage_caused_wound(self) -> bool:
        return self.last_damage_resolution().wound

    def actor_uses_class_resource(self, actor, resource: str) -> bool:
        return actor_uses_class_resource(actor, resource)

    def class_resource_label(self, resource: str) -> str:
        return CLASS_RESOURCE_LABELS.get(resource, resource.replace("_", " ").title())

    def class_resource_max(self, actor, resource: str) -> int:
        return class_resource_cap(actor, resource)

    def synchronize_class_resources(self, actor, *, refill: bool = False, encounter_start: bool = False) -> None:
        synchronize_class_resources(actor, refill=refill, encounter_start=encounter_start)

    def prepare_class_resources_for_combat(self, actor) -> None:
        self.synchronize_class_resources(actor, encounter_start=True)

    def grant_class_resource(self, actor, resource: str, amount: int = 1, *, source: str = "") -> int:
        if amount <= 0 or not self.actor_uses_class_resource(actor, resource):
            return 0
        if resource in {"grit", "momentum", "combo", "fury", "blood_debt", "flow", "arc", "attunement", "edge", "shadow", "toxin", "focus"} and not getattr(self, "_in_combat", False):
            return 0
        maximum = self.class_resource_max(actor, resource)
        if maximum <= 0:
            return 0
        actor.max_resources[resource] = maximum
        previous = max(0, int(actor.resources.get(resource, 0)))
        actor.resources[resource] = min(maximum, previous + amount)
        gained = actor.resources[resource] - previous
        if gained > 0:
            label = self.class_resource_label(resource)
            source_text = f" from {source}" if source else ""
            self.say(f"{self.style_name(actor)} gains {gained} {label}{source_text}.")
        return gained

    def spend_class_resource(self, actor, resource: str, amount: int = 1) -> bool:
        if amount <= 0:
            return True
        if not self.actor_uses_class_resource(actor, resource):
            return False
        self.synchronize_class_resources(actor)
        current = max(0, int(actor.resources.get(resource, 0)))
        if current < amount:
            return False
        actor.resources[resource] = current - amount
        return True

    def grant_ward(self, actor, amount: int, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "ward", amount, source=source)

    def absorb_ward_damage(self, actor, amount: int, *, source_actor=None, damage_type: str = "") -> int:
        if amount <= 0 or not self.actor_uses_class_resource(actor, "ward"):
            return 0
        current = max(0, int(actor.resources.get("ward", 0)))
        if current <= 0:
            return 0
        absorbed = min(current, amount)
        actor.resources["ward"] = current - absorbed
        if absorbed > 0:
            self.on_ward_absorbed(actor, source_actor, absorbed=absorbed, damage_type=damage_type)
        return absorbed

    def on_ward_absorbed(self, actor, source_actor, *, absorbed: int, damage_type: str) -> None:
        if absorbed <= 0:
            return
        actor.bond_flags["last_ward_absorbed"] = absorbed
        self.maybe_gain_mage_focus_from_ward(actor)
        if self.has_status(actor, "anchor_shell"):
            owner = self.spellguard_anchor_shell_owner(actor)
            if (
                owner is not None
                and owner.is_conscious()
                and not self.damage_type_uses_defense(damage_type)
                and not actor.bond_flags.get("mage_anchor_shell_focus_used")
            ):
                actor.bond_flags["mage_anchor_shell_focus_used"] = True
                self.grant_mage_focus(owner, source="Anchor Shell channel catch")
            if actor.resources.get("ward", 0) == 0:
                actor.bond_flags["ward_broken"] = True
                if source_actor is not None and source_actor.is_conscious():
                    self.apply_status(source_actor, "reeling", 1, source="Anchor Shell break")
                self.clear_anchor_shell(actor)
                return
        if actor.resources.get("ward", 0) == 0:
            actor.bond_flags["ward_broken"] = True

    def ensure_ward_capacity(self, target, source_actor=None) -> None:
        if "ward" not in getattr(target, "max_resources", {}) and not self.actor_uses_class_resource(target, "ward"):
            target.bond_flags["mage_temporary_ward_capacity"] = True
        source = source_actor or target
        source_cap = self.class_resource_max(source, "ward")
        target.max_resources["ward"] = max(int(target.max_resources.get("ward", 0)), source_cap)
        target.resources["ward"] = max(0, int(target.resources.get("ward", 0)))

    def spellguard_anchor_shell_owner(self, target):
        owner_id = target.bond_flags.get("mage_anchor_shell_by_id")
        owner_name = str(target.bond_flags.get("mage_anchor_shell_by", ""))
        candidates = []
        candidates.extend(getattr(self, "_active_combat_heroes", []) or [])
        candidates.extend(getattr(self, "_active_combat_enemies", []) or [])
        if self.state is not None:
            candidates.extend(self.state.party_members())
        for candidate in candidates:
            if owner_id is not None and id(candidate) == owner_id:
                return candidate
            if owner_id is None and owner_name and getattr(candidate, "name", "") == owner_name:
                return candidate
        return None

    def clear_anchor_shell(self, target) -> None:
        self.clear_status(target, "anchor_shell")
        for key in ("mage_anchor_shell_by", "mage_anchor_shell_by_id", "mage_anchor_shell_focus_used"):
            target.bond_flags.pop(key, None)
        if target.bond_flags.pop("mage_temporary_ward_capacity", None):
            target.resources.pop("ward", None)
            target.max_resources.pop("ward", None)

    def use_anchor_shell(self, actor, target) -> bool:
        if "anchor_shell" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Anchor Shell training.")
            return False
        if not self.spend_mp_for_spell(actor, "anchor_shell", "Anchor Shell"):
            return False
        self.ensure_ward_capacity(target, actor)
        amount = max(1, 2 + self.mage_casting_modifier(actor))
        target.bond_flags["mage_anchor_shell_by"] = actor.name
        target.bond_flags["mage_anchor_shell_by_id"] = id(actor)
        target.bond_flags.pop("mage_anchor_shell_focus_used", None)
        self.apply_status(target, "anchor_shell", 2, source=f"{actor.name}'s Anchor Shell")
        granted = self.grant_ward(target, amount, source=f"{actor.name}'s Anchor Shell")
        self.say(f"{self.style_name(actor)} hangs Anchor Shell on {self.style_name(target)} for {granted} Ward.")
        return True

    def maybe_use_ward_shell(self, actor, amount: int, *, source_actor=None, damage_type: str = "") -> int:
        if amount <= 0 or "ward_shell" not in getattr(actor, "features", []):
            return 0
        if not actor.is_conscious() or not self.can_use_class_reaction(actor):
            return 0
        cost = magic_point_cost("ward_shell")
        if current_magic_points(actor) < cost:
            return 0
        if not spend_magic_points(actor, cost):
            return 0
        self.spend_class_reaction(actor, source="Ward Shell")
        casting_modifier = self.mage_casting_modifier(actor)
        roll_result = self.roll_with_display_bonus(
            "1d6",
            bonus=casting_modifier,
            style="ward",
            context_label="Ward Shell",
            outcome_kind="ward",
        )
        reduction = max(0, roll_result.total + casting_modifier)
        absorbed = min(amount, reduction)
        source_text = f" against {self.style_name(source_actor)}" if source_actor is not None else ""
        self.say(f"{self.style_name(actor)} snaps Ward Shell shut{source_text}, absorbing {absorbed} damage.")
        return absorbed

    def use_blue_glass_palm(self, actor, target) -> bool:
        if "blue_glass_palm" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Blue Glass Palm training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot shape Blue Glass Palm toward harm while Charmed.")
            return False
        channel = spell_label("blue_glass_palm")
        if not self.spend_mp_for_spell(actor, "blue_glass_palm", "Blue Glass Palm"):
            return False
        try:
            dc = self.mage_channel_dc(actor)
            success = self.saving_throw(target, "STR", dc, context=f"against {actor.name}'s {channel}")
            damage = self.roll_with_display_bonus(
                "1d6",
                bonus=self.spell_damage_bonus(actor),
                style="damage",
                context_label=channel,
                outcome_kind="damage",
            ).total + self.spell_damage_bonus(actor)
            if success:
                damage = max(1, damage // 2)
            actual = self.apply_damage(target, max(1, damage), damage_type="force", source_actor=actor)
            self.say(f"{channel} hits {self.style_name(target)} for {self.style_damage(actual)} force damage.")
            self.announce_downed_target(target)
            self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            if not success and target.is_conscious():
                self.apply_status(target, "reeling", 1, source=channel)
            if not success and actual > 0 and target.is_conscious():
                self.add_arcanist_pattern_charge(actor, target, source=channel)
            self.maybe_gain_mage_focus_from_channel(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_lockstep_field(self, actor, allies: list | None = None) -> bool:
        if "lockstep_field" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Lockstep Field training.")
            return False
        if not self.spend_mp_for_spell(actor, "lockstep_field", "Lockstep Field"):
            return False
        targets = list(allies) if allies is not None else self.active_allies_for_actor(actor)
        if actor not in targets and actor.is_conscious():
            targets.append(actor)
        valid_targets = [target for target in targets if not target.dead]
        for target in valid_targets:
            self.apply_status(target, "guarded", 1, source=f"{actor.name}'s Lockstep Field")
            self.apply_status(target, "lockstep_field", 1, source=f"{actor.name}'s Lockstep Field")
        self.say(f"{self.style_name(actor)} lays Lockstep Field across {len(valid_targets)} allies.")
        return True

    def clear_class_combat_resources(self, actor) -> None:
        clear_class_combat_state(actor)

    def is_mage_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return getattr(actor, "class_name", "") == "Mage" or bool(
            features
            & {
                "mage_charge",
                "mage_focus",
                "arcane_bolt",
                "minor_channel",
                "pattern_read",
                "ground",
                "mage_ward",
                "spellguard_ward",
                "anchor_shell",
                "ward_shell",
                "blue_glass_palm",
                "lockstep_field",
                "arcanist_arc",
                "pattern_charge",
                "arc_pulse",
                "marked_angle",
                "quiet_sum",
                "detonate_pattern",
                "elementalist_attunement",
                "elemental_weave",
                "ember_lance",
                "frost_shard",
                "volt_grasp",
                "change_weather_hand",
                "burning_line",
                "lockfrost",
                "aethermancer_flow",
                "field_mend",
                "pulse_restore",
                "triage_line",
                "clean_breath",
                "steady_pulse",
                "overflow_shell",
            }
        )

    def mage_casting_ability(self, actor) -> str:
        ability = getattr(actor, "spellcasting_ability", None)
        if ability:
            return ability
        candidates = ("INT", "WIS", "CHA")
        return max(candidates, key=lambda key: actor.ability_mod(key))

    def mage_casting_modifier(self, actor) -> int:
        return actor.ability_mod(self.mage_casting_ability(actor))

    def mage_channel_dc(self, actor) -> int:
        return 8 + actor.proficiency_bonus + self.mage_casting_modifier(actor)

    def mage_lowest_resist_lane(self, target) -> tuple[str, int]:
        lanes = [(ability, target.save_bonus(ability)) for ability in ("STR", "DEX", "CON", "INT", "WIS", "CHA")]
        return min(lanes, key=lambda entry: (entry[1], entry[0]))

    def grant_mage_focus(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "focus", amount, source=source)

    def is_arcanist_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return bool(features & {"arcanist_arc", "pattern_charge", "arc_pulse", "marked_angle", "quiet_sum", "detonate_pattern"})

    def grant_arcanist_arc(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "arc", amount, source=source)

    def arcanist_pattern_charge_cap(self, actor) -> int:
        return 4 if "patient_diagram" in getattr(actor, "features", []) else 3

    def arcanist_pattern_charges(self, actor, target) -> int:
        charges_by_actor = target.bond_flags.get("arcanist_pattern_charges", {})
        if not isinstance(charges_by_actor, dict):
            return 0
        return max(0, int(charges_by_actor.get(actor.name, 0)))

    def total_arcanist_pattern_charges(self, target) -> int:
        charges_by_actor = target.bond_flags.get("arcanist_pattern_charges", {})
        if not isinstance(charges_by_actor, dict):
            return 0
        return sum(max(0, int(value)) for value in charges_by_actor.values())

    def set_arcanist_pattern_charges(self, actor, target, amount: int, *, duration: int = 99) -> int:
        charges_by_actor = target.bond_flags.setdefault("arcanist_pattern_charges", {})
        if not isinstance(charges_by_actor, dict):
            charges_by_actor = {}
            target.bond_flags["arcanist_pattern_charges"] = charges_by_actor
        charge_ids = target.bond_flags.setdefault("arcanist_pattern_charge_ids", {})
        if not isinstance(charge_ids, dict):
            charge_ids = {}
            target.bond_flags["arcanist_pattern_charge_ids"] = charge_ids
        normalized = max(0, min(self.arcanist_pattern_charge_cap(actor), int(amount)))
        if normalized <= 0:
            charges_by_actor.pop(actor.name, None)
            charge_ids.pop(actor.name, None)
        else:
            charges_by_actor[actor.name] = normalized
            charge_ids[actor.name] = id(actor)
            self.apply_status(target, "pattern_charge", duration, source=f"{actor.name}'s Pattern Charge")
        if not charges_by_actor:
            target.bond_flags.pop("arcanist_pattern_charges", None)
            target.bond_flags.pop("arcanist_pattern_charge_ids", None)
            self.clear_status(target, "pattern_charge")
        return normalized

    def add_arcanist_pattern_charge(
        self,
        actor,
        target,
        amount: int = 1,
        *,
        source: str = "",
        grant_arc: bool = True,
    ) -> int:
        if "pattern_charge" not in getattr(actor, "features", []) and not self.actor_uses_class_resource(actor, "arc"):
            return 0
        before = self.arcanist_pattern_charges(actor, target)
        after = self.set_arcanist_pattern_charges(actor, target, before + amount)
        gained = max(0, after - before)
        if gained > 0:
            source_text = f" from {source}" if source else ""
            self.say(f"{self.style_name(target)} carries Pattern Charge {after}{source_text}.")
            if grant_arc:
                self.grant_arcanist_arc(actor, source=source or "Pattern Charge")
        return after

    def clear_arcanist_pattern_charges(self, actor, target) -> int:
        current = self.arcanist_pattern_charges(actor, target)
        self.set_arcanist_pattern_charges(actor, target, 0)
        return current

    def maybe_gain_arcanist_arc_from_pattern_read(self, actor, target) -> None:
        if not self.is_arcanist_actor(actor) or not self.actor_uses_class_resource(actor, "arc"):
            return
        if "quiet_sum" not in getattr(actor, "features", []) and "arcanist_arc" not in getattr(actor, "features", []):
            return
        if actor.bond_flags.get("arcanist_pattern_read_arc_gained"):
            return
        actor.bond_flags["arcanist_pattern_read_arc_gained"] = True
        self.grant_arcanist_arc(actor, source="Pattern Read")

    def maybe_gain_mage_focus_from_ward(self, actor) -> None:
        if not self.is_mage_actor(actor) or not self.actor_uses_class_resource(actor, "focus"):
            return
        round_number = int(getattr(self, "_active_round_number", 0) or 0)
        key = f"mage_ward_focus_round_{round_number}"
        if actor.bond_flags.get(key):
            return
        actor.bond_flags[key] = True
        self.grant_mage_focus(actor, source="Ward absorption")

    def maybe_gain_mage_focus_from_channel(self, actor, target, *, source: str = "") -> None:
        if not self.is_mage_actor(actor) or not self.actor_uses_class_resource(actor, "focus"):
            return
        round_number = int(getattr(self, "_active_round_number", 0) or 0)
        key = f"mage_channel_focus_round_{round_number}"
        if actor.bond_flags.get(key):
            return
        if target is not None and not self.target_is_pattern_read_by(actor, target):
            return
        actor.bond_flags[key] = True
        self.grant_mage_focus(actor, source=source or "a shaped channel")

    def target_is_pattern_read_by(self, actor, target) -> bool:
        reader_id = target.bond_flags.get("mage_pattern_read_by_id")
        if reader_id is not None:
            return reader_id == id(actor)
        return target.bond_flags.get("mage_pattern_read_by") == actor.name

    def use_pattern_read(self, actor, target) -> bool:
        if "pattern_read" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Pattern Read training.")
            return False
        ability, save_bonus = self.mage_lowest_resist_lane(target)
        defense = self.effective_defense_percent(target, damage_type="slashing")
        avoidance = self.effective_avoidance(target)
        ward = int(getattr(target, "resources", {}).get("ward", 0))
        pattern_charge = self.total_arcanist_pattern_charges(target)
        target.bond_flags["mage_pattern_read_by"] = actor.name
        target.bond_flags["mage_pattern_read_by_id"] = id(actor)
        target.bond_flags["mage_pattern_read_lowest_save"] = ability
        actor.bond_flags["mage_last_pattern_read_target"] = target.name
        actor.bond_flags["mage_last_pattern_read_target_id"] = id(target)
        actor.bond_flags["mage_last_pattern_read_round"] = int(getattr(self, "_active_round_number", 0) or 0)
        self.apply_status(target, "pattern_read", 2, source=f"{actor.name}'s Pattern Read")
        if "focused_eye" in getattr(actor, "features", []) and not actor.bond_flags.get("mage_pattern_read_focus_gained"):
            actor.bond_flags["mage_pattern_read_focus_gained"] = True
            self.grant_mage_focus(actor, source="Focused Eye")
        self.maybe_gain_arcanist_arc_from_pattern_read(actor, target)
        ward_text = f", Ward {ward}" if ward else ""
        charge_text = f", Pattern Charge {pattern_charge}" if pattern_charge else ""
        self.say(
            f"Pattern Read: {self.style_name(target)} shows {ability_label(ability, include_code=True)} "
            f"{save_bonus:+d}, Defense {defense}%, Avoidance {avoidance:+d}{ward_text}{charge_text}."
        )
        self.record_opening_tutorial_combat_event("combat_pattern_read", actor=actor, target=target)
        return True

    def use_ground(self, actor) -> bool:
        if "ground" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Ground training.")
            return False
        self.apply_status(actor, "grounded_channel", 2, source=f"{actor.name}'s grounding breath")
        self.say(f"{self.style_name(actor)} grounds the channel and steadies the next pattern.")
        self.record_opening_tutorial_combat_event("combat_ground", actor=actor)
        return True

    def arcane_bolt_mp_cost(self, actor, *, action_cast: bool = False) -> int:
        base_cost = magic_point_cost("arcane_bolt", actor)
        return base_cost * 2 if action_cast else base_cost

    def arcane_bolt_damage_expression(self, actor) -> str:
        level = max(1, int(getattr(actor, "level", 1)))
        dice = min(5, 1 + (level - 1) // 2)
        return f"{dice}d4"

    def arcane_bolt_cooldown_duration(self) -> int:
        # Conditions tick at end of the current turn, so 3 blocks the next two turns.
        return 3

    def arcane_bolt_on_cooldown(self, actor) -> bool:
        return self.has_status(actor, "arcane_bolt_cooldown")

    def use_arcane_bolt(self, actor, target, heroes=None, enemies=None, dodging=None, *, action_cast: bool = False) -> bool:
        if "arcane_bolt" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Arcane Bolt training.")
            return False
        if self.arcane_bolt_on_cooldown(actor):
            self.say(f"{self.style_name(actor)} needs another breath before Arcane Bolt will answer.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot shape Arcane Bolt toward harm while Charmed.")
            return False
        channel = spell_label("arcane_bolt")
        cost = self.arcane_bolt_mp_cost(actor, action_cast=action_cast)
        if not spend_magic_points(actor, cost):
            self.say(
                f"{self.style_name(actor)} needs {cost} MP to use {channel}, "
                f"but has {current_magic_points(actor)}."
            )
            return False
        self.apply_status(actor, "arcane_bolt_cooldown", self.arcane_bolt_cooldown_duration(), source=channel)
        self.record_opening_tutorial_combat_event("combat_arcane_bolt", actor=actor, target=target)
        play_attack_sound_for = getattr(self, "play_attack_sound_for", None)
        if callable(play_attack_sound_for):
            play_attack_sound_for(actor)
        try:
            active_heroes = heroes if heroes is not None else self.active_allies_for_actor(actor)
            active_enemies = enemies if enemies is not None else list(getattr(self, "_active_combat_enemies", []) or [])
            active_dodging = dodging if dodging is not None else getattr(self, "_active_dodging_names", frozenset())
            target_number = self.effective_attack_target_number(target)
            advantage = self.attack_advantage_state(actor, target, active_heroes, active_enemies, active_dodging, ranged=True)
            total_modifier = (
                self.spell_attack_bonus(actor, "INT")
                + self.ally_pressure_bonus(actor, active_heroes, ranged=True)
                + self.status_accuracy_modifier(actor)
                + self.attack_focus_modifier(actor, target)
                + self.target_accuracy_modifier(target)
            )
            d20 = self.roll_check_d20(
                actor,
                advantage,
                target_number=target_number,
                target_label=self.attack_target_label(target_number),
                modifier=total_modifier,
                style="attack",
                outcome_kind="attack",
                context_label=f"{actor.name} casts {channel} at {target.name}",
            )
            total = d20.kept + total_modifier
            critical_hit = d20.kept >= self.critical_threshold(actor)
            if d20.kept == 1 or (not critical_hit and total < target_number):
                self.say(f"{channel} snaps past {self.style_name(target)} without finding a mark.")
                return True
            damage_bonus = max(0, actor.ability_mod("INT")) + self.spell_damage_bonus(actor)
            damage_roll = self.roll_with_display_bonus(
                self.arcane_bolt_damage_expression(actor),
                bonus=damage_bonus,
                critical=critical_hit,
                style="damage",
                context_label=channel,
                outcome_kind="damage",
            )
            damage_multiplier = 2 if action_cast else 1
            damage = max(1, (damage_roll.total + damage_bonus) * damage_multiplier)
            actual = self.apply_damage(target, damage, damage_type="force", source_actor=actor)
            self.say(f"{channel} strikes {self.style_name(target)} for {self.style_damage(actual)} force damage.")
            self.announce_downed_target(target)
            self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            if actual > 0 and target.is_conscious():
                self.add_arcanist_pattern_charge(actor, target, source=channel)
            self.maybe_gain_mage_focus_from_channel(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def mage_minor_channel_save_ability(self, actor, target) -> str:
        if self.target_is_pattern_read_by(actor, target):
            return str(target.bond_flags.get("mage_pattern_read_lowest_save") or self.mage_lowest_resist_lane(target)[0])
        return "DEX"

    def use_minor_channel(self, actor, target) -> bool:
        if "minor_channel" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Minor Channel training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot shape Minor Channel toward harm while Charmed.")
            return False
        channel = spell_label("minor_channel")
        if not self.spend_mp_for_spell(actor, "minor_channel", "Minor Channel"):
            return False
        self.record_opening_tutorial_combat_event("combat_minor_channel", actor=actor, target=target)
        try:
            ability = self.mage_minor_channel_save_ability(actor, target)
            dc = self.mage_channel_dc(actor)
            success = self.saving_throw(target, ability, dc, context=f"against {actor.name}'s {channel}")
            if success:
                self.say(f"{self.style_name(target)} breaks the line of {channel}.")
                return True
            damage = self.roll_with_display_bonus(
                "1d6",
                bonus=self.spell_damage_bonus(actor),
                style="damage",
                context_label=channel,
                outcome_kind="damage",
            ).total + self.spell_damage_bonus(actor)
            actual = self.apply_damage(target, max(1, damage), damage_type="force", source_actor=actor)
            self.say(f"{channel} snaps into {self.style_name(target)} for {self.style_damage(actual)} force damage.")
            self.announce_downed_target(target)
            self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            if target.is_conscious() and self.target_is_pattern_read_by(actor, target):
                self.apply_status(target, "reeling", 1, source=channel)
            if actual > 0 and target.is_conscious():
                self.add_arcanist_pattern_charge(actor, target, source=channel)
            self.maybe_gain_mage_focus_from_channel(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_marked_angle(self, actor, target) -> bool:
        if "marked_angle" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Marked Angle training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot mark an enemy pattern while Charmed.")
            return False
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        read_round = int(actor.bond_flags.get("mage_last_pattern_read_round", -999))
        read_target_id = actor.bond_flags.get("mage_last_pattern_read_target_id")
        read_target_name = actor.bond_flags.get("mage_last_pattern_read_target")
        same_target = read_target_id == id(target) if read_target_id is not None else read_target_name == target.name
        if read_round != current_round or not same_target or not self.target_is_pattern_read_by(actor, target):
            self.say(f"{self.style_name(actor)} needs a fresh Pattern Read before Marked Angle will hold.")
            return False
        if not self.spend_mp_for_spell(actor, "marked_angle", "Marked Angle"):
            return False
        self.add_arcanist_pattern_charge(actor, target, source="Marked Angle")
        self.say(f"{self.style_name(actor)} adds one clean line to {self.style_name(target)}'s pattern.")
        return True

    def arcanist_channel_save_ability(self, actor, target) -> str:
        if self.target_is_pattern_read_by(actor, target):
            return str(target.bond_flags.get("mage_pattern_read_lowest_save") or self.mage_lowest_resist_lane(target)[0])
        return "DEX"

    def use_arc_pulse(self, actor, target) -> bool:
        if "arc_pulse" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Arc Pulse training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot shape Arc Pulse toward harm while Charmed.")
            return False
        channel = spell_label("arc_pulse")
        if not self.spend_mp_for_spell(actor, "arc_pulse", "Arc Pulse"):
            return False
        try:
            ability = self.arcanist_channel_save_ability(actor, target)
            dc = self.mage_channel_dc(actor)
            success = self.saving_throw(target, ability, dc, context=f"against {actor.name}'s {channel}")
            damage = self.roll_with_display_bonus(
                "1d8",
                bonus=self.spell_damage_bonus(actor),
                style="damage",
                context_label=channel,
                outcome_kind="damage",
            ).total + self.spell_damage_bonus(actor)
            if success:
                damage = max(1, damage // 2)
            actual = self.apply_damage(target, max(1, damage), damage_type="force", source_actor=actor)
            self.say(f"{channel} snaps through {self.style_name(target)} for {self.style_damage(actual)} force damage.")
            self.announce_downed_target(target)
            self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            if not success and actual > 0 and target.is_conscious():
                self.add_arcanist_pattern_charge(actor, target, source=channel)
            self.maybe_gain_mage_focus_from_channel(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_detonate_pattern(self, actor, target) -> bool:
        if "detonate_pattern" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Detonate Pattern training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot Detonate Pattern while Charmed.")
            return False
        charges = self.arcanist_pattern_charges(actor, target)
        if charges <= 0:
            self.say(f"{self.style_name(target)} has no Pattern Charge for {self.style_name(actor)} to release.")
            return False
        if not self.spend_class_resource(actor, "arc", 2):
            self.say(f"{self.style_name(actor)} needs 2 Arc to Detonate Pattern.")
            return False
        self.clear_arcanist_pattern_charges(actor, target)
        try:
            ability = str(target.bond_flags.get("mage_pattern_read_lowest_save") or "CON")
            channel = "Detonate Pattern"
            success = self.saving_throw(target, ability, self.mage_channel_dc(actor), context=f"against {actor.name}'s {channel}")
            roll_expression = f"{charges}d6"
            damage = self.roll_with_display_bonus(
                roll_expression,
                bonus=self.spell_damage_bonus(actor),
                style="damage",
                context_label=channel,
                outcome_kind="damage",
            ).total + self.spell_damage_bonus(actor)
            if success:
                damage = max(1, damage // 2)
            actual = self.apply_damage(target, max(1, damage), damage_type="force", source_actor=actor)
            self.say(f"{self.style_name(actor)} releases {charges} Pattern Charge into {self.style_name(target)} for {self.style_damage(actual)} force damage.")
            self.announce_downed_target(target)
            self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def is_elementalist_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return bool(
            features
            & {
                "elementalist_attunement",
                "elemental_weave",
                "ember_lance",
                "frost_shard",
                "volt_grasp",
                "change_weather_hand",
                "burning_line",
                "lockfrost",
            }
        )

    def elementalist_active_element(self, actor) -> str:
        element = str(actor.bond_flags.get("elementalist_active_element", "")).lower().strip()
        return element if element in ELEMENTALIST_ELEMENT_ORDER else "fire"

    def elementalist_previous_element(self, actor) -> str:
        element = str(actor.bond_flags.get("elementalist_previous_element", "")).lower().strip()
        return element if element in ELEMENTALIST_ELEMENT_ORDER else ""

    def set_elementalist_active_element(self, actor, element: str, *, preserve_stacks: int = 0) -> bool:
        element = element.lower().strip()
        if element not in ELEMENTALIST_ELEMENT_ORDER:
            return False
        previous = self.elementalist_active_element(actor)
        if previous != element:
            actor.bond_flags["elementalist_previous_element"] = previous
            actor.resources["attunement"] = min(
                max(0, int(preserve_stacks)),
                max(0, int(actor.resources.get("attunement", 0))),
            )
        actor.bond_flags["elementalist_active_element"] = element
        return True

    def grant_elementalist_attunement(self, actor, element: str, *, source: str = "") -> int:
        if not self.actor_uses_class_resource(actor, "attunement"):
            return 0
        current_element = self.elementalist_active_element(actor)
        if current_element != element:
            self.set_elementalist_active_element(actor, element, preserve_stacks=0)
        else:
            actor.bond_flags["elementalist_active_element"] = element
        return self.grant_class_resource(actor, "attunement", source=source or ELEMENTALIST_ELEMENT_LABELS[element])

    def use_change_weather_hand(self, actor, element: str) -> bool:
        if "change_weather_hand" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Change Weather training.")
            return False
        element = element.lower().strip()
        if element not in ELEMENTALIST_ELEMENT_ORDER:
            self.say("That element is not ready in this rules slice.")
            return False
        if self.elementalist_active_element(actor) == element:
            self.say(f"{self.style_name(actor)} is already holding {ELEMENTALIST_ELEMENT_LABELS[element]}.")
            return False
        self.set_elementalist_active_element(actor, element, preserve_stacks=1)
        self.say(f"{self.style_name(actor)} turns the weather in hand toward {ELEMENTALIST_ELEMENT_LABELS[element]}.")
        return True

    def maybe_apply_elemental_weave(self, actor, target, element: str, *, failed_save: bool) -> None:
        if not failed_save or "elemental_weave" not in getattr(actor, "features", []):
            return
        previous = self.elementalist_previous_element(actor)
        if not previous or previous == element:
            return
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        if int(actor.bond_flags.get("elementalist_weave_round", -1)) == current_round:
            return
        actor.bond_flags["elementalist_weave_round"] = current_round
        pair = frozenset({previous, element})
        if pair == frozenset({"fire", "cold"}):
            self.apply_status(target, "blinded", 1, source=f"{actor.name}'s Elemental Weave")
        elif pair == frozenset({"cold", "lightning"}):
            self.apply_status(target, "reeling", 1, source=f"{actor.name}'s Elemental Weave")
        elif pair == frozenset({"fire", "lightning"}):
            self.apply_status(target, "burning", 1, source=f"{actor.name}'s Elemental Weave")

    def use_elementalist_minor_channel(self, actor, target, *, feature: str, spell_id: str, element: str, save_ability: str, damage_type: str) -> bool:
        if feature not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no {spell_label(spell_id)} training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot shape {spell_label(spell_id)} toward harm while Charmed.")
            return False
        channel = spell_label(spell_id)
        if not self.spend_mp_for_spell(actor, spell_id, channel):
            return False
        try:
            success = self.saving_throw(target, save_ability, self.mage_channel_dc(actor), context=f"against {actor.name}'s {channel}")
            damage = self.roll_with_display_bonus(
                "1d8",
                bonus=self.spell_damage_bonus(actor),
                style="damage",
                context_label=channel,
                outcome_kind="damage",
            ).total + self.spell_damage_bonus(actor)
            if success:
                damage = max(1, damage // 2)
            actual = self.apply_damage(target, max(1, damage), damage_type=damage_type, source_actor=actor)
            self.say(f"{channel} hits {self.style_name(target)} for {self.style_damage(actual)} {damage_type} damage.")
            self.announce_downed_target(target)
            self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            self.grant_elementalist_attunement(actor, element, source=channel)
            if not success and target.is_conscious():
                if element == "fire":
                    self.apply_status(target, "burning", 2, source=channel)
                elif element == "cold":
                    self.apply_status(target, "slowed", 2, source=channel)
                elif element == "lightning":
                    self.apply_status(target, "reeling", 1, source=channel)
                    target.bond_flags["class_reaction_used_round"] = int(getattr(self, "_active_round_number", 0) or 0)
                    target.bond_flags["class_reaction_source"] = channel
                self.maybe_apply_elemental_weave(actor, target, element, failed_save=True)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_ember_lance(self, actor, target) -> bool:
        return self.use_elementalist_minor_channel(
            actor,
            target,
            feature="ember_lance",
            spell_id="ember_lance",
            element="fire",
            save_ability="DEX",
            damage_type="fire",
        )

    def use_frost_shard(self, actor, target) -> bool:
        return self.use_elementalist_minor_channel(
            actor,
            target,
            feature="frost_shard",
            spell_id="frost_shard",
            element="cold",
            save_ability="DEX",
            damage_type="cold",
        )

    def use_volt_grasp(self, actor, target) -> bool:
        return self.use_elementalist_minor_channel(
            actor,
            target,
            feature="volt_grasp",
            spell_id="volt_grasp",
            element="lightning",
            save_ability="CON",
            damage_type="lightning",
        )

    def use_burning_line(self, actor, targets: list | None = None) -> bool:
        if "burning_line" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Burning Line training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot set Burning Line while Charmed.")
            return False
        channel = spell_label("burning_line")
        if not self.spend_mp_for_spell(actor, "burning_line", channel):
            return False
        try:
            self.grant_elementalist_attunement(actor, "fire", source=channel)
            valid_targets = [target for target in (targets or self.active_opponents_for_actor(actor)) if target.is_conscious()]
            for target in valid_targets:
                success = self.saving_throw(target, "DEX", self.mage_channel_dc(actor), context=f"against {actor.name}'s {channel}")
                damage = self.roll_with_display_bonus(
                    "1d6",
                    bonus=self.spell_damage_bonus(actor),
                    style="damage",
                    context_label=channel,
                    outcome_kind="damage",
                ).total + self.spell_damage_bonus(actor)
                if success:
                    damage = max(1, damage // 2)
                actual = self.apply_damage(target, max(1, damage), damage_type="fire", source_actor=actor)
                self.say(f"{channel} burns {self.style_name(target)} for {self.style_damage(actual)} fire damage.")
                self.apply_status(target, "burning_line", 2, source=channel)
                if not success and target.is_conscious():
                    self.apply_status(target, "burning", 2, source=channel)
                    self.maybe_apply_elemental_weave(actor, target, "fire", failed_save=True)
                self.announce_downed_target(target)
                self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_lockfrost(self, actor, targets: list | None = None) -> bool:
        if "lockfrost" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Lockfrost training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot set Lockfrost while Charmed.")
            return False
        channel = spell_label("lockfrost")
        if not self.spend_mp_for_spell(actor, "lockfrost", channel):
            return False
        try:
            self.grant_elementalist_attunement(actor, "cold", source=channel)
            valid_targets = [target for target in (targets or self.active_opponents_for_actor(actor)) if target.is_conscious()]
            for target in valid_targets:
                was_slowed = self.has_status(target, "slowed")
                success = self.saving_throw(target, "DEX", self.mage_channel_dc(actor), context=f"against {actor.name}'s {channel}")
                damage = self.roll_with_display_bonus(
                    "1d6",
                    bonus=self.spell_damage_bonus(actor),
                    style="damage",
                    context_label=channel,
                    outcome_kind="damage",
                ).total + self.spell_damage_bonus(actor)
                if success:
                    damage = max(1, damage // 2)
                actual = self.apply_damage(target, max(1, damage), damage_type="cold", source_actor=actor)
                self.say(f"{channel} locks around {self.style_name(target)} for {self.style_damage(actual)} cold damage.")
                self.apply_status(target, "lockfrost_field", 2, source=channel)
                if not success and target.is_conscious():
                    self.apply_status(target, "slowed", 2, source=channel)
                    if was_slowed:
                        self.apply_status(target, "prone", 1, source=channel)
                    self.maybe_apply_elemental_weave(actor, target, "cold", failed_save=True)
                self.announce_downed_target(target)
                self.trigger_blacklake_adjudicator_reflection(actor, target, source=channel)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def is_aethermancer_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return bool(
            features
            & {
                "aethermancer_flow",
                "field_mend",
                "pulse_restore",
                "triage_line",
                "clean_breath",
                "steady_pulse",
                "overflow_shell",
            }
        )

    def grant_aethermancer_flow(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "flow", amount, source=source)

    def aethermancer_overflow_ward_cap(self, actor) -> int:
        return max(1, 2 + actor.proficiency_bonus)

    def maybe_gain_aethermancer_flow_from_heal(
        self,
        actor,
        target,
        *,
        previous_hp: int,
        healed: int,
        overflow_ward: int,
        source: str = "",
    ) -> None:
        if not self.is_aethermancer_actor(actor) or not self.actor_uses_class_resource(actor, "flow"):
            return
        if "steady_pulse" in getattr(actor, "features", []) and healed > 0 and previous_hp * 2 < max(1, target.max_hp):
            current_round = int(getattr(self, "_active_round_number", 0) or 0)
            key = f"aethermancer_low_heal_flow_round_{current_round}"
            if not actor.bond_flags.get(key):
                actor.bond_flags[key] = True
                self.grant_aethermancer_flow(actor, source=source or "Steady Pulse")
        if overflow_ward > 0:
            self.grant_aethermancer_flow(actor, source=source or "overflow Ward")

    def apply_aethermancer_heal(
        self,
        actor,
        target,
        amount: int,
        *,
        source: str,
        allow_overflow: bool = True,
    ) -> tuple[int, int]:
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond {source}.")
            return (0, 0)
        amount = max(1, int(amount))
        previous_hp = target.current_hp
        healed = target.heal(amount)
        overflow = max(0, amount - healed)
        overflow_ward = 0
        if allow_overflow and overflow > 0:
            self.ensure_ward_capacity(target, actor)
            overflow_ward = self.grant_ward(
                target,
                min(overflow, self.aethermancer_overflow_ward_cap(actor)),
                source=f"{actor.name}'s {source}",
            )
        self.maybe_gain_aethermancer_flow_from_heal(
            actor,
            target,
            previous_hp=previous_hp,
            healed=healed,
            overflow_ward=overflow_ward,
            source=source,
        )
        play_heal_sound_for = getattr(self, "play_heal_sound_for", None)
        if healed > 0 and callable(play_heal_sound_for):
            play_heal_sound_for(actor)
        ward_text = f" and shapes {overflow_ward} excess into Ward" if overflow_ward > 0 else ""
        self.say(
            f"{self.style_name(actor)} uses {source} on {self.style_name(target)}, "
            f"restoring {self.style_healing(healed)} hit points{ward_text}."
        )
        return (healed, overflow_ward)

    def use_field_mend(self, actor, target) -> bool:
        if "field_mend" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Field Mend training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond Field Mend.")
            return False
        if not self.spend_mp_for_spell(actor, "field_mend", "Field Mend"):
            return False
        if target.current_hp == 0:
            if not spend_magic_points(actor, 1):
                self.apply_status(actor, "reeling", 1, source="Field Mend strain")
        bonus = self.mage_casting_modifier(actor) + self.healing_bonus(actor)
        healing = (
            self.roll_with_display_bonus(
                "1d8",
                bonus=bonus,
                style="healing",
                context_label="Field Mend",
                outcome_kind="healing",
            ).total
            + bonus
        )
        self.apply_aethermancer_heal(actor, target, healing, source="Field Mend")
        return True

    def use_pulse_restore(self, actor, target) -> bool:
        if "pulse_restore" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Pulse Restore training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond Pulse Restore.")
            return False
        if not self.spend_mp_for_spell(actor, "pulse_restore", "Pulse Restore"):
            return False
        bonus = self.mage_casting_modifier(actor) + self.healing_bonus(actor)
        healing = (
            self.roll_with_display_bonus(
                "1d4",
                bonus=bonus,
                style="healing",
                context_label="Pulse Restore",
                outcome_kind="healing",
            ).total
            + bonus
        )
        self.apply_aethermancer_heal(actor, target, healing, source="Pulse Restore")
        return True

    def use_triage_line(self, actor, allies: list | None = None) -> bool:
        if "triage_line" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Triage Line training.")
            return False
        if not self.spend_mp_for_spell(actor, "triage_line", "Triage Line"):
            return False
        targets = list(allies) if allies is not None else self.active_allies_for_actor(actor)
        if actor not in targets and actor.is_conscious():
            targets.append(actor)
        valid_targets = [target for target in targets if not getattr(target, "dead", False)]
        healed_targets = 0
        for target in valid_targets:
            self.apply_status(target, "triage_line", 2, source=f"{actor.name}'s Triage Line")
            if target.current_hp <= 0 or target.current_hp >= target.max_hp:
                continue
            healing = self.roll_with_display_bonus(
                "1d4",
                style="healing",
                context_label="Triage Line",
                outcome_kind="healing",
            ).total
            healed, _ = self.apply_aethermancer_heal(
                actor,
                target,
                healing,
                source="Triage Line",
                allow_overflow=False,
            )
            if healed > 0:
                healed_targets += 1
        if healed_targets >= 2:
            self.grant_aethermancer_flow(actor, source="Triage Line")
        self.say(f"{self.style_name(actor)} chalks Triage Line across {len(valid_targets)} allies.")
        return True

    def use_clean_breath(self, actor, target) -> bool:
        if "clean_breath" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Clean Breath training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond Clean Breath.")
            return False
        if not self.spend_mp_for_spell(actor, "clean_breath", "Clean Breath"):
            return False
        reduced_status = ""
        for status in ("poisoned", "bleeding", "reeling"):
            duration = int(target.conditions.get(status, 0))
            if duration <= 0:
                continue
            if duration == 1:
                self.clear_status(target, status)
            else:
                target.conditions[status] = duration - 1
            reduced_status = status
            break
        if reduced_status:
            self.grant_aethermancer_flow(actor, source="Clean Breath")
        self.apply_aethermancer_heal(actor, target, 1, source="Clean Breath", allow_overflow=False)
        status_text = f" and eases {self.status_name(reduced_status)}" if reduced_status else ""
        self.say(f"{self.style_name(actor)} steadies {self.style_name(target)}'s breath{status_text}.")
        return True

    def use_overflow_shell(self, actor, target) -> bool:
        if "overflow_shell" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Overflow Shell training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond Overflow Shell.")
            return False
        if not self.spend_class_resource(actor, "flow", 1):
            self.say(f"{self.style_name(actor)} needs 1 Flow for Overflow Shell.")
            return False
        self.ensure_ward_capacity(target, actor)
        amount = max(1, 2 + self.mage_casting_modifier(actor))
        granted = self.grant_ward(target, amount, source=f"{actor.name}'s Overflow Shell")
        self.say(f"{self.style_name(actor)} knots Overflow Shell around {self.style_name(target)} for {granted} Ward.")
        return True

    def is_warrior_actor(self, actor) -> bool:
        return "warrior_grit" in getattr(actor, "features", [])

    def warrior_grit_max(self, actor) -> int:
        return self.class_resource_max(actor, "grit")

    def prepare_warrior_grit_for_combat(self, actor) -> None:
        self.prepare_class_resources_for_combat(actor)

    def grant_warrior_grit(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "grit", amount, source=source)

    def grant_juggernaut_momentum(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "momentum", amount, source=source)

    def grant_weapon_master_combo(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "combo", amount, source=source)

    def grant_berserker_fury(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "fury", amount, source=source)

    def grant_bloodreaver_debt(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "blood_debt", amount, source=source)

    def grant_rogue_edge(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "edge", amount, source=source)

    def grant_shadowguard_shadow(self, actor, amount: int = 1, *, source: str = "") -> int:
        return self.grant_class_resource(actor, "shadow", amount, source=source)

    def maybe_gain_grit_from_strong_hit(self, attacker, margin: int) -> None:
        if margin >= 5:
            self.grant_warrior_grit(attacker, source="a strong hit")

    def effective_stability(self, actor) -> int:
        total = actor.ability_mod("STR")
        for bonuses in (actor.equipment_bonuses, actor.gear_bonuses, actor.relationship_bonuses):
            total += int(bonuses.get("stability", 0))
            total += int(bonuses.get("stability_bonus", 0))
        total += self.status_value(actor, "stability_bonus")
        total -= self.status_value(actor, "stability_penalty")
        if "red_work_rhythm" in getattr(actor, "features", []) and actor.max_hp > 0:
            hp_percent = actor.current_hp * 100 // actor.max_hp
            if 30 <= hp_percent <= 69:
                total += 1
        if self.has_status(actor, "prone"):
            total -= 2
        if self.has_status(actor, "restrained") or self.has_status(actor, "grappled"):
            total -= 2
        if self.has_status(actor, "stunned") or self.has_status(actor, "paralyzed") or self.has_status(actor, "unconscious"):
            total -= 5
        return total

    def stability_target_number(self, actor) -> int:
        return max(1, 10 + self.effective_stability(actor))

    def stability_target_label(self, target_number: int) -> str:
        return f"Stability {target_number}"

    def combat_defense_summary(self, actor) -> str:
        defense = self.effective_defense_percent(actor, damage_type="slashing")
        avoidance = self.effective_avoidance(actor)
        stability = self.effective_stability(actor)
        return f"Defense {defense}%, Avoidance {avoidance:+d}, Stability {stability:+d}"

    def combat_resource_summary_line(self, actor, *, width: int | None = None) -> str | None:
        resource_lines: list[str] = []
        for resource in CLASS_RESOURCE_ORDER:
            if not self.actor_uses_class_resource(actor, resource):
                continue
            maximum = max(0, int(actor.max_resources.get(resource, self.class_resource_max(actor, resource))))
            current = max(0, int(actor.resources.get(resource, 0)))
            if maximum <= 0 and current <= 0:
                continue
            label = self.class_resource_label(resource)
            color = CLASS_RESOURCE_COLORS.get(resource, "white")
            resource_lines.append(self.format_resource_bar(label, current, maximum, width=width, fill_color=color))
        if not resource_lines:
            return None
        return " | ".join(resource_lines)

    def clear_combat_stance(self, actor) -> None:
        for status in (*STANCE_STATUS_NAMES, "guard_stance"):
            actor.conditions.pop(status, None)

    def current_combat_stance_key(self, actor) -> str:
        for key, status in STANCE_STATUS_BY_KEY.items():
            if self.has_status(actor, status):
                return key
        if self.has_status(actor, "guard_stance"):
            return "guard"
        return "neutral"

    def combat_stance_label(self, actor) -> str:
        return STANCE_LABELS[self.current_combat_stance_key(actor)]

    def combat_stance_option(self, stance_key: str, actor) -> str:
        label = STANCE_LABELS[stance_key]
        active = "active" if self.current_combat_stance_key(actor) == stance_key else STANCE_SUMMARIES[stance_key]
        return f"{label} ({active})"

    def set_combat_stance(self, actor, stance_key: str, *, announce: bool = True) -> bool:
        stance_key = stance_key.lower().strip()
        if stance_key not in STANCE_LABELS:
            return False
        previous = self.current_combat_stance_key(actor)
        if stance_key == previous:
            if announce:
                self.say(f"{self.style_name(actor)} keeps {STANCE_LABELS[stance_key]} Stance.")
            return False
        self.clear_combat_stance(actor)
        if stance_key != "neutral":
            actor.conditions[STANCE_STATUS_BY_KEY[stance_key]] = 99
        if announce:
            self.say(f"{self.style_name(actor)} shifts into {STANCE_LABELS[stance_key]} Stance: {STANCE_SUMMARIES[stance_key]}")
        self.apply_stance_upgrade_hooks(actor, stance_key)
        return True

    def use_guard_stance(self, actor) -> bool:
        changed = self.set_combat_stance(actor, "guard", announce=False)
        if not changed:
            return False
        self.say(
            f"{self.style_name(actor)} sets a guarded lane: +20% Defense, +2 Stability, and -2 Accuracy while the stance holds."
        )
        self.record_opening_tutorial_combat_event("combat_guard_stance", actor=actor)
        return True

    def can_raise_shield(self, actor) -> bool:
        return bool(getattr(actor, "shield", False)) and not self.has_status(actor, "raised_shield")

    def use_raise_shield(self, actor) -> None:
        self.apply_status(actor, "raised_shield", 2, source=f"{actor.name}'s raised shield")
        defense = self.raised_shield_defense_percent(actor)
        self.say(f"{self.style_name(actor)} raises a shield and gains +{defense}% Defense until their next turn.")

    def use_weapon_read(self, actor, target) -> None:
        defense = self.effective_defense_percent(target, damage_type="slashing")
        avoidance = self.effective_avoidance(target)
        stability = self.effective_stability(target)
        armor_break = self.total_armor_break_percent(target)
        defense_band = "high" if defense >= 35 else "low" if defense <= 10 else "moderate"
        if avoidance >= 5:
            avoidance_band = "exceptional"
        elif avoidance >= 4:
            avoidance_band = "high"
        elif avoidance >= 3:
            avoidance_band = "dedicated"
        elif avoidance >= 2:
            avoidance_band = "skirmisher"
        elif avoidance >= 1:
            avoidance_band = "agile"
        elif avoidance <= -1:
            avoidance_band = "exposed"
        else:
            avoidance_band = "trained"
        stability_band = "high" if stability >= 4 else "low" if stability <= 0 else "moderate"
        answer = "Armor Break or save pressure"
        if avoidance >= 3 and defense_band != "high":
            answer = "accuracy pressure, marks, or forced saves"
        elif defense_band == "low":
            answer = "plain weapon wounds"
        elif stability_band == "low":
            answer = "shove, prone, or pin pressure"
        break_text = f", Armor Break {armor_break}%" if armor_break else ""
        self.say(
            f"Weapon Read: {self.style_name(target)} has {defense_band} Defense ({defense}%), "
            f"{avoidance_band} Avoidance ({avoidance:+d}), and {stability_band} Stability ({stability:+d}){break_text}. "
            f"Best answer: {answer}."
        )
        self.record_opening_tutorial_combat_event("combat_weapon_read", actor=actor, target=target)

    def use_warrior_rally(self, actor, target) -> bool:
        if not self.spend_class_resource(actor, "grit"):
            self.say(f"{self.style_name(actor)} needs 1 Grit to Rally.")
            return False
        if self.has_status(target, "reeling"):
            self.clear_status(target, "reeling")
            self.say(f"{self.style_name(actor)} snaps {self.style_name(target)} back into the line and clears Reeling.")
        else:
            self.apply_status(target, "guarded", 1, source=f"{actor.name}'s Rally")
            self.say(f"{self.style_name(actor)} steadies {self.style_name(target)} with a hard battlefield call.")
        self.record_opening_tutorial_combat_event("combat_warrior_rally", actor=actor, target=target)
        return True

    def fixate_target(self, actor, target, *, duration: int = 1) -> None:
        target.bond_flags["warrior_fixated_by"] = actor.name
        target.bond_flags["warrior_fixated_by_id"] = id(actor)
        self.apply_status(target, "fixated", duration, source=f"{actor.name}'s Iron Draw")

    def target_is_fixated_by(self, actor, target) -> bool:
        if not self.has_status(target, "fixated"):
            return False
        fixated_id = target.bond_flags.get("warrior_fixated_by_id")
        if fixated_id is not None:
            return fixated_id == id(actor)
        return target.bond_flags.get("warrior_fixated_by") == actor.name

    def fixated_priority_target(self, attacker, candidates: list) -> object | None:
        if not self.has_status(attacker, "fixated"):
            return None
        fixated_id = attacker.bond_flags.get("warrior_fixated_by_id")
        if fixated_id is not None:
            return next((candidate for candidate in candidates if candidate.is_conscious() and id(candidate) == fixated_id), None)
        fixated_by = str(attacker.bond_flags.get("warrior_fixated_by", ""))
        return next((candidate for candidate in candidates if candidate.is_conscious() and candidate.name == fixated_by), None)

    def attack_focus_modifier(self, attacker, target) -> int:
        if not self.has_status(attacker, "fixated"):
            return 0
        fixated_id = attacker.bond_flags.get("warrior_fixated_by_id")
        if fixated_id is not None:
            return 0 if id(target) == fixated_id else -2
        fixated_by = str(attacker.bond_flags.get("warrior_fixated_by", ""))
        if fixated_by and getattr(target, "name", None) != fixated_by:
            return -2
        return 0

    def use_iron_draw(self, actor, target) -> None:
        duration = 2 if self.current_combat_stance_key(actor) in {"guard", "brace"} else 1
        self.fixate_target(actor, target, duration=duration)
        self.say(f"{self.style_name(actor)} draws {self.style_name(target)} into the guarded lane.")

    def use_shoulder_in(self, actor) -> bool:
        if not self.spend_class_resource(actor, "grit"):
            self.say(f"{self.style_name(actor)} needs 1 Grit to Shoulder In.")
            return False
        already_guarding = self.current_combat_stance_key(actor) == "guard"
        self.set_combat_stance(actor, "guard", announce=False)
        self.apply_status(actor, "shoulder_in", 2, source=f"{actor.name}'s Shoulder In")
        if already_guarding:
            self.grant_juggernaut_momentum(actor, source="doubling down in Guard")
        self.say(f"{self.style_name(actor)} shoulders into the line and tightens Guard by +5% Defense.")
        return True

    def is_weapon_master_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return "style_wheel" in features or self.actor_uses_class_resource(actor, "combo")

    def weapon_master_style_key(self, actor) -> str:
        style_key = str(actor.bond_flags.get("weapon_master_style", "")).lower().strip()
        if style_key not in WEAPON_MASTER_STYLE_LABELS:
            style_key = "cleave"
            actor.bond_flags["weapon_master_style"] = style_key
        return style_key

    def weapon_master_style_label(self, actor) -> str:
        return WEAPON_MASTER_STYLE_LABELS[self.weapon_master_style_key(actor)]

    def weapon_master_style_option(self, style_key: str, actor) -> str:
        label = WEAPON_MASTER_STYLE_LABELS[style_key]
        active = "active" if self.weapon_master_style_key(actor) == style_key else WEAPON_MASTER_STYLE_SUMMARIES[style_key]
        return f"{label} ({active})"

    def set_weapon_master_style(self, actor, style_key: str, *, announce: bool = True) -> bool:
        style_key = style_key.lower().strip()
        if style_key not in WEAPON_MASTER_STYLE_LABELS:
            return False
        previous = self.weapon_master_style_key(actor)
        if previous == style_key:
            if announce:
                self.say(f"{self.style_name(actor)} keeps {WEAPON_MASTER_STYLE_LABELS[style_key]} style.")
            return False
        actor.bond_flags["weapon_master_style"] = style_key
        if announce:
            self.say(f"{self.style_name(actor)} shifts to {WEAPON_MASTER_STYLE_LABELS[style_key]} style.")
        return True

    def use_weapon_master_style(self, actor, style_key: str) -> str | None:
        if not self.is_weapon_master_actor(actor):
            self.say(f"{self.style_name(actor)} has no Style Wheel training.")
            return None
        style_key = style_key.lower().strip()
        if style_key not in WEAPON_MASTER_STYLE_LABELS:
            return None
        previous = self.weapon_master_style_key(actor)
        if previous == style_key:
            self.say(f"{self.style_name(actor)} keeps {WEAPON_MASTER_STYLE_LABELS[style_key]} style.")
            return "free"
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        if int(actor.bond_flags.get("weapon_master_free_style_round", -1)) != current_round:
            actor.bond_flags["weapon_master_free_style_round"] = current_round
            self.set_weapon_master_style(actor, style_key)
            return "free"
        if not self.spend_class_resource(actor, "combo"):
            self.say(f"{self.style_name(actor)} needs 1 Combo to switch style again this turn.")
            return None
        self.set_weapon_master_style(actor, style_key)
        return "combo"

    def target_has_guard_layer(self, target) -> bool:
        guarded_statuses = ("guarded", "raised_shield", "guard_stance", "stance_guard", "stance_brace")
        return any(self.has_status(target, status) for status in guarded_statuses)

    def clear_target_guard_layers(self, target) -> bool:
        removed = False
        for status in ("guarded", "raised_shield", "guard_stance"):
            if self.has_status(target, status):
                self.clear_status(target, status)
                removed = True
        if self.current_combat_stance_key(target) in {"guard", "brace"}:
            self.clear_combat_stance(target)
            removed = True
        return removed

    def weapon_master_style_accuracy_modifier(self, actor, target) -> int:
        if not self.is_weapon_master_actor(actor):
            return 0
        style_key = self.weapon_master_style_key(actor)
        bonus = 1 if style_key == "pierce" else 0
        if style_key == "hook" and self.target_has_guard_layer(target):
            bonus += 1
        if "first_flaw" in getattr(actor, "features", []) and target.bond_flags.get("weapon_master_measured_by_id") == id(actor):
            bonus += 1
        return bonus

    def weapon_master_hit_armor_break_percent(self, actor, target, *, critical_hit: bool) -> int:
        if not self.is_weapon_master_actor(actor):
            return 0
        if self.weapon_master_style_key(actor) == "pierce" and critical_hit:
            return 10
        return 0

    def weapon_master_target_has_readable_weakness(self, actor, target) -> bool:
        defense = self.effective_defense_percent(target, damage_type="slashing")
        avoidance = self.effective_avoidance(target)
        if defense >= 25 or avoidance >= 3 or self.target_has_guard_layer(target):
            return True
        exposed_statuses = ("armor_broken", "marked", "prone", "reeling", "restrained", "measured_line", "unbalanced")
        return any(self.has_status(target, status) for status in exposed_statuses)

    def weapon_master_style_exploits_target(self, actor, target, style_key: str) -> bool:
        defense = self.effective_defense_percent(target, damage_type="slashing")
        if style_key == "crush":
            return defense >= 25 or self.target_has_guard_layer(target)
        if style_key == "pierce":
            return self.effective_avoidance(target) >= 3
        if style_key == "hook":
            return self.target_has_guard_layer(target) or self.effective_stability(target) >= 3
        if style_key == "cleave":
            return defense <= 10
        return False

    def use_measure_twice(self, actor, target) -> bool:
        if not self.is_weapon_master_actor(actor):
            self.say(f"{self.style_name(actor)} has no measured style training.")
            return False
        self.use_weapon_read(actor, target)
        if self.weapon_master_target_has_readable_weakness(actor, target):
            target.bond_flags["weapon_master_measured_by"] = actor.name
            target.bond_flags["weapon_master_measured_by_id"] = id(actor)
            self.grant_weapon_master_combo(actor, source="Measure Twice")
            self.say(f"{self.style_name(actor)} finds a workable line in {self.style_name(target)}'s guard.")
        else:
            self.say(f"{self.style_name(actor)} reads the target cleanly but finds no immediate style opening.")
        return True

    def record_weapon_master_hit(self, actor, target) -> None:
        if not self.actor_uses_class_resource(actor, "combo"):
            return
        style_key = self.weapon_master_style_key(actor)
        last_style = str(actor.bond_flags.get("weapon_master_last_hit_style", ""))
        source = ""
        if not last_style or last_style != style_key:
            source = f"{WEAPON_MASTER_STYLE_LABELS[style_key]} variation"
        else:
            exposed_statuses = ("armor_broken", "marked", "prone", "reeling", "restrained", "measured_line", "unbalanced")
            if any(self.has_status(target, status) for status in exposed_statuses):
                source = "exploiting an opened target"
            elif self.weapon_master_style_exploits_target(actor, target, style_key):
                source = "matching style to weakness"
        if source:
            self.grant_weapon_master_combo(actor, source=source)
        actor.bond_flags["weapon_master_last_hit_style"] = style_key
        actor.bond_flags["weapon_master_last_weapon_hit_round"] = int(getattr(self, "_active_round_number", 0) or 0)

    def apply_weapon_master_style_rider(
        self,
        actor,
        target,
        *,
        actual_damage: int,
        margin: int,
        critical_hit: bool,
    ) -> None:
        if not self.is_weapon_master_actor(actor) or not target.is_conscious():
            return
        style_key = self.weapon_master_style_key(actor)
        if style_key == "crush" and (actual_damage > 0 or margin >= 5):
            self.apply_status(target, "armor_broken", 1, source=f"{actor.name}'s Crush style")
            self.say(f"{self.style_name(actor)} dents the shell and leaves {self.style_name(target)} easier to break.")
        elif style_key == "hook":
            if self.clear_target_guard_layers(target):
                self.say(f"{self.style_name(actor)} hooks through {self.style_name(target)}'s guard and tears the line open.")
            else:
                self.apply_status(target, "unbalanced", 1, source=f"{actor.name}'s Hook style")
            if margin >= 5:
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s Hook style")
        elif style_key == "pierce" and margin >= 5:
            self.apply_status(target, "measured_line", 1, source=f"{actor.name}'s Pierce style")

    def use_weapon_master_technique(
        self,
        actor,
        target,
        heroes,
        enemies,
        dodging,
        *,
        style_key: str,
        label: str,
        accuracy_bonus: int = 0,
        armor_break_percent: int = 0,
    ) -> bool:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't use {label} while Charmed.")
            return False
        self.set_weapon_master_style(actor, style_key, announce=False)
        advantage = self.attack_advantage_state(actor, target, heroes, enemies, dodging, ranged=actor.weapon.ranged)
        target_number = self.effective_attack_target_number(target)
        total_modifier = (
            actor.attack_bonus()
            + self.ally_pressure_bonus(actor, heroes, ranged=actor.weapon.ranged)
            + self.status_accuracy_modifier(actor)
            + self.attack_focus_modifier(actor, target)
            + self.weapon_master_style_accuracy_modifier(actor, target)
            + accuracy_bonus
        )
        d20 = self.roll_check_d20(
            actor,
            advantage,
            target_number=target_number,
            target_label=self.attack_target_label(target_number),
            modifier=total_modifier,
            style="attack",
            outcome_kind="attack",
            context_label=f"{actor.name} uses {label} on {target.name}",
        )
        total = d20.kept + total_modifier
        critical_hit = d20.kept >= self.critical_threshold(actor)
        if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
            self.say(f"{self.style_name(actor)} tries {label} on {self.style_name(target)}, but the angle fails.")
            return False
        self.maybe_gain_grit_from_strong_hit(actor, total - target_number)
        damage_bonus = actor.damage_bonus() + self.status_damage_modifier(actor)
        damage = max(
            1,
            self.roll_with_display_bonus(
                actor.weapon.damage,
                bonus=damage_bonus,
                critical=critical_hit,
                style="damage",
                context_label=f"{actor.name} {label} damage",
                outcome_kind="damage",
            ).total
            + damage_bonus,
        )
        weapon_item = self.equipped_weapon_item(actor)
        style_break = self.weapon_master_hit_armor_break_percent(actor, target, critical_hit=critical_hit)
        actual = self.apply_damage(
            target,
            damage,
            damage_type=weapon_item.damage_type if weapon_item is not None else "",
            source_actor=actor,
            apply_defense=True,
            armor_break_percent=armor_break_percent + style_break,
        )
        self.apply_weapon_master_style_rider(
            actor,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
        )
        if actual <= 0 and self.last_damage_was_glance():
            self.say(f"{self.style_name(actor)} lands {label}, but {self.style_name(target)} turns it into a Glance.")
        else:
            self.say(f"{self.style_name(actor)} lands {label} for {self.style_damage(actual)} damage.")
        self.announce_downed_target(target)
        self.trigger_on_hit_hooks(
            actor,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
            heroes=heroes,
            enemies=enemies,
        )
        return True

    def use_clean_line(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_weapon_master_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            style_key="pierce",
            label="Clean Line",
            accuracy_bonus=1,
        )

    def use_dent_the_shell(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_weapon_master_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            style_key="crush",
            label="Dent The Shell",
            armor_break_percent=10,
        )

    def use_hook_the_guard(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_weapon_master_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            style_key="hook",
            label="Hook The Guard",
        )

    def is_berserker_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return "berserker_fury" in features or self.actor_uses_class_resource(actor, "fury")

    def use_redline(self, actor, fury_spent: int | None = None) -> bool:
        if not self.is_berserker_actor(actor):
            self.say(f"{self.style_name(actor)} has no Redline training.")
            return False
        available = max(0, int(actor.resources.get("fury", 0)))
        spend = min(3, available if fury_spent is None else max(0, int(fury_spent)))
        if spend and not self.spend_class_resource(actor, "fury", spend):
            return False
        actor.bond_flags["berserker_redline_damage_bonus"] = spend
        self.apply_status(actor, "redline", 2, source=f"{actor.name}'s Redline")
        spend_text = f" and burns {spend} Fury" if spend else ""
        damage_text = f"+{spend} damage" if spend else "no extra damage"
        self.say(
            f"{self.style_name(actor)} hits Redline{spend_text}: +2 Accuracy, {damage_text}, -5% Defense, and -1 Avoidance."
        )
        return True

    def use_teeth_set(self, actor) -> bool:
        if not self.spend_class_resource(actor, "fury"):
            self.say(f"{self.style_name(actor)} needs 1 Fury to set their teeth.")
            return False
        amount = max(1, actor.proficiency_bonus + actor.ability_mod("CON"))
        actor.grant_temp_hp(amount)
        self.say(f"{self.style_name(actor)} sets their teeth and gains {self.style_healing(amount)} temporary hit points.")
        return True

    def use_drink_the_hurt(self, actor) -> bool:
        if not self.spend_class_resource(actor, "fury", 2):
            self.say(f"{self.style_name(actor)} needs 2 Fury to Drink The Hurt.")
            return False
        self.apply_status(actor, "drink_the_hurt", 2, source=f"{actor.name}'s bloodied rhythm")
        self.say(f"{self.style_name(actor)} turns pain into a waiting mouth. Their next Wound can heal them.")
        return True

    def use_berserker_weapon_technique(
        self,
        actor,
        target,
        heroes,
        enemies,
        dodging,
        *,
        label: str,
        accuracy_bonus: int = 0,
        apply_reckless_opening: bool = False,
    ) -> bool:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't use {label} while Charmed.")
            return False
        advantage = self.attack_advantage_state(actor, target, heroes, enemies, dodging, ranged=actor.weapon.ranged)
        target_number = self.effective_attack_target_number(target)
        total_modifier = (
            actor.attack_bonus()
            + self.ally_pressure_bonus(actor, heroes, ranged=actor.weapon.ranged)
            + self.status_accuracy_modifier(actor)
            + self.attack_focus_modifier(actor, target)
            + self.weapon_master_style_accuracy_modifier(actor, target)
            + self.target_accuracy_modifier(target)
            + accuracy_bonus
        )
        d20 = self.roll_check_d20(
            actor,
            advantage,
            target_number=target_number,
            target_label=self.attack_target_label(target_number),
            modifier=total_modifier,
            style="attack",
            outcome_kind="attack",
            context_label=f"{actor.name} uses {label} on {target.name}",
        )
        total = d20.kept + total_modifier
        critical_hit = d20.kept >= self.critical_threshold(actor)
        if apply_reckless_opening:
            self.apply_status(actor, "reckless_opening", 2, source=label)
        if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
            self.say(f"{self.style_name(actor)} throws {label} at {self.style_name(target)}, but the strike goes wide.")
            return False
        self.maybe_gain_grit_from_strong_hit(actor, total - target_number)
        damage_bonus = actor.damage_bonus() + self.status_damage_modifier(actor)
        damage = max(
            1,
            self.roll_with_display_bonus(
                actor.weapon.damage,
                bonus=damage_bonus,
                critical=critical_hit,
                style="damage",
                context_label=f"{actor.name} {label} damage",
                outcome_kind="damage",
            ).total
            + damage_bonus,
        )
        weapon_item = self.equipped_weapon_item(actor)
        actual = self.apply_damage(
            target,
            damage,
            damage_type=weapon_item.damage_type if weapon_item is not None else "",
            source_actor=actor,
            apply_defense=True,
            armor_break_percent=self.weapon_master_hit_armor_break_percent(actor, target, critical_hit=critical_hit),
        )
        self.apply_weapon_master_style_rider(
            actor,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
        )
        if actual <= 0 and self.last_damage_was_glance():
            self.say(f"{self.style_name(actor)} lands {label}, but {self.style_name(target)} turns it into a Glance.")
        else:
            self.say(f"{self.style_name(actor)} lands {label} for {self.style_damage(actual)} damage.")
        self.announce_downed_target(target)
        self.trigger_on_hit_hooks(
            actor,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
            heroes=heroes,
            enemies=enemies,
        )
        return True

    def use_reckless_cut(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_berserker_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="Reckless Cut",
            accuracy_bonus=2,
            apply_reckless_opening=True,
        )

    def is_bloodreaver_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return "bloodreaver_blood_debt" in features or self.actor_uses_class_resource(actor, "blood_debt")

    def use_red_mark(self, actor, target, *, duration: int = 3) -> bool:
        if not self.is_bloodreaver_actor(actor):
            self.say(f"{self.style_name(actor)} has no Red Mark training.")
            return False
        target.bond_flags["bloodreaver_red_mark_by"] = actor.name
        target.bond_flags["bloodreaver_red_mark_by_id"] = id(actor)
        self.apply_status(target, "marked", duration, source=f"{actor.name}'s Red Mark")
        self.say(f"{self.style_name(actor)} puts a red hand of debt on {self.style_name(target)}.")
        return True

    def target_is_red_marked_by(self, actor, target) -> bool:
        if not self.has_status(target, "marked"):
            return False
        marker_id = target.bond_flags.get("bloodreaver_red_mark_by_id")
        if marker_id is not None:
            return marker_id == id(actor)
        return target.bond_flags.get("bloodreaver_red_mark_by") == actor.name

    def bloodreaver_red_mark_owner(self, target):
        marker_id = target.bond_flags.get("bloodreaver_red_mark_by_id")
        marker_name = str(target.bond_flags.get("bloodreaver_red_mark_by", ""))
        candidates = []
        candidates.extend(getattr(self, "_active_combat_heroes", []) or [])
        candidates.extend(getattr(self, "_active_combat_enemies", []) or [])
        if self.state is not None:
            candidates.extend(self.state.party_members())
        for candidate in candidates:
            if marker_id is not None and id(candidate) == marker_id:
                return candidate
            if marker_id is None and marker_name and getattr(candidate, "name", "") == marker_name:
                return candidate
        return None

    def active_allies_for_actor(self, actor) -> list:
        heroes = list(getattr(self, "_active_combat_heroes", []) or [])
        enemies = list(getattr(self, "_active_combat_enemies", []) or [])
        if actor in enemies or "enemy" in getattr(actor, "tags", []):
            return [enemy for enemy in enemies if enemy.is_conscious()]
        if not heroes and self.state is not None:
            heroes = self.state.party_members()
        return [hero for hero in heroes if hero.is_conscious()]

    def bloodreaver_healing_recipient(self, attacker):
        allies = self.active_allies_for_actor(attacker)
        if getattr(attacker, "is_conscious", lambda: False)() and attacker.current_hp < attacker.max_hp:
            return attacker
        injured = [ally for ally in allies if ally.current_hp < ally.max_hp]
        if injured:
            return min(injured, key=lambda ally: (ally.current_hp / max(1, ally.max_hp), ally.current_hp))
        return attacker

    def maybe_trigger_red_mark_healing(self, attacker, target) -> None:
        owner = self.bloodreaver_red_mark_owner(target)
        if owner is None or not owner.is_conscious() or not self.target_is_red_marked_by(owner, target):
            return
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        round_key = f"bloodreaver_red_mark_heal_round_{id(owner)}"
        if int(target.bond_flags.get(round_key, -1)) == current_round:
            return
        target.bond_flags[round_key] = current_round
        healing = 1 + owner.proficiency_bonus
        if "butchers_mercy" in getattr(owner, "features", []) and owner.current_hp * 2 < owner.max_hp:
            healing += 1
        recipient = self.bloodreaver_healing_recipient(attacker)
        healed = recipient.heal(healing)
        if healed > 0:
            self.say(f"{self.style_name(recipient)} takes {self.style_healing(healed)} healing from {self.style_name(target)}'s Red Mark.")
        self.grant_bloodreaver_debt(owner, source="Red Mark healing")

    def grant_blood_debt_for_ally_wound(self, wounded) -> None:
        heroes = list(getattr(self, "_active_combat_heroes", []) or [])
        if not heroes and self.state is not None:
            heroes = self.state.party_members()
        if wounded not in heroes:
            return
        for ally in heroes:
            if ally is wounded or not ally.is_conscious():
                continue
            if self.actor_uses_class_resource(ally, "blood_debt"):
                self.grant_bloodreaver_debt(ally, source=f"{wounded.name} taking a Wound")

    def use_blood_price(self, actor, target) -> bool:
        if not self.spend_class_resource(actor, "blood_debt"):
            self.say(f"{self.style_name(actor)} needs 1 Blood Debt to pay the Blood Price.")
            return False
        heal_roll = self.roll_with_display_bonus(
            "1d4",
            bonus=actor.ability_mod("CON"),
            style="healing",
            context_label=f"{actor.name} Blood Price",
            outcome_kind="healing",
        )
        amount = max(1, heal_roll.total + actor.ability_mod("CON"))
        healed = target.heal(amount)
        self.apply_status(actor, "reeling", 1, source="Blood Price")
        self.say(f"{self.style_name(actor)} pays in red breath and restores {self.style_healing(healed)} to {self.style_name(target)}.")
        return True

    def use_bloodreaver_weapon_technique(
        self,
        actor,
        target,
        heroes,
        enemies,
        dodging,
        *,
        label: str,
        accuracy_bonus: int = 0,
        apply_bleeding_on_wound: bool = False,
        heal_lowest_on_wound: bool = False,
    ) -> bool:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't use {label} while Charmed.")
            return False
        advantage = self.attack_advantage_state(actor, target, heroes, enemies, dodging, ranged=actor.weapon.ranged)
        target_number = self.effective_attack_target_number(target)
        total_modifier = (
            actor.attack_bonus()
            + self.ally_pressure_bonus(actor, heroes, ranged=actor.weapon.ranged)
            + self.status_accuracy_modifier(actor)
            + self.attack_focus_modifier(actor, target)
            + self.weapon_master_style_accuracy_modifier(actor, target)
            + self.target_accuracy_modifier(target)
            + accuracy_bonus
        )
        d20 = self.roll_check_d20(
            actor,
            advantage,
            target_number=target_number,
            target_label=self.attack_target_label(target_number),
            modifier=total_modifier,
            style="attack",
            outcome_kind="attack",
            context_label=f"{actor.name} uses {label} on {target.name}",
        )
        total = d20.kept + total_modifier
        critical_hit = d20.kept >= self.critical_threshold(actor)
        if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
            self.say(f"{self.style_name(actor)} reaches for {label}, but the wound line closes.")
            return False
        self.maybe_gain_grit_from_strong_hit(actor, total - target_number)
        damage_bonus = actor.damage_bonus() + self.status_damage_modifier(actor)
        damage = max(
            1,
            self.roll_with_display_bonus(
                actor.weapon.damage,
                bonus=damage_bonus,
                critical=critical_hit,
                style="damage",
                context_label=f"{actor.name} {label} damage",
                outcome_kind="damage",
            ).total
            + damage_bonus,
        )
        weapon_item = self.equipped_weapon_item(actor)
        actual = self.apply_damage(
            target,
            damage,
            damage_type=weapon_item.damage_type if weapon_item is not None else "",
            source_actor=actor,
            apply_defense=True,
            armor_break_percent=self.weapon_master_hit_armor_break_percent(actor, target, critical_hit=critical_hit),
        )
        if target.is_conscious() and self.last_damage_caused_wound():
            if apply_bleeding_on_wound:
                self.apply_status(target, "bleeding", 2, source=label)
            if heal_lowest_on_wound:
                injured = [ally for ally in heroes if ally.current_hp < ally.max_hp and not ally.dead]
                recipient = min(injured, key=lambda ally: (ally.current_hp / max(1, ally.max_hp), ally.current_hp), default=None)
                if recipient is not None:
                    healing = max(1, actor.proficiency_bonus // 2)
                    healed = recipient.heal(healing)
                    if healed > 0:
                        self.say(f"{self.style_name(recipient)} catches {self.style_healing(healed)} from {label}.")
        self.say(f"{self.style_name(actor)} lands {label} for {self.style_damage(actual)} damage.")
        self.announce_downed_target(target)
        self.trigger_on_hit_hooks(
            actor,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
            heroes=heroes,
            enemies=enemies,
        )
        return True

    def use_war_salve_strike(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_bloodreaver_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="War-Salve Strike",
            heal_lowest_on_wound=True,
        )

    def use_open_the_ledger(self, actor, target, heroes, enemies, dodging) -> bool:
        if not self.target_is_red_marked_by(actor, target):
            self.say(f"{self.style_name(actor)} needs their Red Mark on {self.style_name(target)} to open the ledger.")
            return False
        if not self.spend_class_resource(actor, "grit"):
            self.say(f"{self.style_name(actor)} needs 1 Grit to Open The Ledger.")
            return False
        return self.use_bloodreaver_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="Open The Ledger",
            accuracy_bonus=1,
            apply_bleeding_on_wound=True,
        )

    def class_stance_upgrade_payload(self, actor, stance_key: str) -> dict[str, object]:
        upgrades = getattr(actor, "bond_flags", {}).get("stance_upgrades", {})
        if not isinstance(upgrades, dict):
            return {}
        payload = upgrades.get(stance_key) or upgrades.get("*") or {}
        return dict(payload) if isinstance(payload, dict) else {}

    def apply_stance_upgrade_hooks(self, actor, stance_key: str) -> None:
        payload = self.class_stance_upgrade_payload(actor, stance_key)
        if not payload:
            return
        for status, duration in dict(payload.get("statuses", {})).items():
            self.apply_status(actor, str(status), int(duration), source=f"{STANCE_LABELS[stance_key]} upgrade")
        for resource, amount in dict(payload.get("resources", {})).items():
            self.grant_class_resource(actor, str(resource), int(amount), source=f"{STANCE_LABELS[stance_key]} upgrade")

    def is_rogue_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return getattr(actor, "class_name", "") == "Rogue" or bool(
            features
            & {
                "rogue_edge",
                "tool_read",
                "rogue_skirmish",
                "shadowguard_shadow",
                "death_mark",
                "poisoner_toxin",
                "alchemist_quick_mix",
            }
        )

    def rogue_trick_modifier(self, actor) -> int:
        ability_bonus = max(actor.ability_mod("DEX"), actor.ability_mod("INT"), actor.ability_mod("CHA"))
        return (
            ability_bonus
            + actor.proficiency_bonus
            + actor.equipment_bonuses.get("attack", 0)
            + actor.gear_bonuses.get("attack", 0)
            + actor.relationship_bonuses.get("attack", 0)
            + self.status_accuracy_modifier(actor)
        )

    def rogue_trick_target_number(self, target, trick_kind: str = "") -> int:
        if trick_kind in {"trip", "shove", "tangle"}:
            return self.stability_target_number(target)
        return self.effective_attack_target_number(target)

    def resolve_rogue_trick_check(self, actor, target, *, trick_kind: str, context_label: str) -> tuple[bool, int]:
        target_number = self.rogue_trick_target_number(target, trick_kind)
        target_label = (
            self.stability_target_label(target_number)
            if trick_kind in {"trip", "shove", "tangle"}
            else self.attack_target_label(target_number)
        )
        modifier = self.rogue_trick_modifier(actor)
        d20 = self.roll_check_d20(
            actor,
            self.d20_disadvantage_state(actor, attack=True),
            target_number=target_number,
            target_label=target_label,
            modifier=modifier,
            style="attack",
            outcome_kind="attack",
            context_label=context_label,
        )
        total = d20.kept + modifier
        if d20.kept == 1:
            return False, total - target_number
        return d20.kept == 20 or total >= target_number, total - target_number

    def mark_class_target(self, actor, target, *, mark_key: str = "rogue_mark", duration: int = 2) -> None:
        target.bond_flags[f"{mark_key}_by"] = actor.name
        self.apply_status(target, "marked", duration, source=f"{actor.name}'s mark")

    def target_is_marked_by(self, actor, target, *, mark_key: str = "rogue_mark") -> bool:
        return target.bond_flags.get(f"{mark_key}_by") == actor.name

    def use_rogue_mark(self, actor, target) -> bool:
        if "rogue_mark" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Mark Work training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} cannot mark an enemy for harm while Charmed.")
            return False
        self.mark_class_target(actor, target, duration=2)
        self.say(f"{self.style_name(actor)} marks {self.style_name(target)}'s open line for the next clean strike.")
        self.record_opening_tutorial_combat_event("combat_rogue_mark", actor=actor, target=target)
        return True

    def use_tool_read(self, actor, target) -> bool:
        if "tool_read" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Tool Read training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't read an enemy for harm while Charmed.")
            return False
        defense = self.effective_defense_percent(target, damage_type="slashing")
        avoidance = self.effective_avoidance(target)
        stability = self.effective_stability(target)
        armor_break = self.total_armor_break_percent(target)
        poison_stacks = self.rogue_poison_stacks(actor, target)
        self.mark_class_target(actor, target, duration=2)
        target.bond_flags["rogue_tool_read_by"] = actor.name
        target.bond_flags["rogue_tool_read_by_id"] = id(actor)
        self.apply_status(target, "tool_read", 1, source=f"{actor.name}'s Tool Read")
        self.grant_rogue_edge(actor, source="Tool Read")
        poison_text = f", Poison stacks {poison_stacks}" if poison_stacks else ""
        break_text = f", Armor Break {armor_break}%" if armor_break else ""
        self.say(
            f"Tool Read: {self.style_name(target)} shows Defense {defense}%, "
            f"Avoidance {avoidance:+d}, Stability {stability:+d}{break_text}{poison_text}."
        )
        return True

    def target_is_tool_read_by(self, actor, target) -> bool:
        reader_id = target.bond_flags.get("rogue_tool_read_by_id")
        if reader_id is not None:
            return reader_id == id(actor)
        return target.bond_flags.get("rogue_tool_read_by") == actor.name

    def active_opponents_for_actor(self, actor) -> list:
        heroes = list(getattr(self, "_active_combat_heroes", []) or [])
        enemies = list(getattr(self, "_active_combat_enemies", []) or [])
        if not heroes and self.state is not None:
            heroes = self.state.party_members()
        if actor in enemies or "enemy" in getattr(actor, "tags", []):
            return [hero for hero in heroes if hero.is_conscious()]
        return [enemy for enemy in enemies if enemy.is_conscious()]

    def clear_death_mark(self, actor) -> None:
        for target in self.active_opponents_for_actor(actor):
            if self.target_is_death_marked_by(actor, target):
                target.bond_flags.pop("assassin_death_mark_by", None)
                target.bond_flags.pop("assassin_death_mark_by_id", None)
        actor.bond_flags.pop("assassin_death_mark_target", None)
        actor.bond_flags.pop("assassin_death_mark_target_id", None)

    def use_death_mark(self, actor, target) -> bool:
        if "death_mark" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Death Mark training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't name a death mark while Charmed.")
            return False
        self.clear_death_mark(actor)
        actor.bond_flags["assassin_death_mark_target"] = target.name
        actor.bond_flags["assassin_death_mark_target_id"] = id(target)
        target.bond_flags["assassin_death_mark_by"] = actor.name
        target.bond_flags["assassin_death_mark_by_id"] = id(actor)
        self.apply_status(target, "marked", 99, source=f"{actor.name}'s Death Mark")
        self.say(f"{self.style_name(actor)} sets Death Mark on {self.style_name(target)}.")
        return True

    def target_is_death_marked_by(self, actor, target) -> bool:
        marker_id = target.bond_flags.get("assassin_death_mark_by_id")
        if marker_id is not None:
            return marker_id == id(actor)
        return target.bond_flags.get("assassin_death_mark_by") == actor.name

    def assassin_accuracy_modifier(self, actor, target, heroes: list | None = None) -> int:
        if not self.target_is_death_marked_by(actor, target):
            return 0
        if self.has_status(actor, "invisible") or self.rogue_target_is_exposed(actor, target, heroes):
            return 1
        return 0

    def assassin_first_wound_key(self, target) -> str:
        return f"assassin_death_mark_first_wound_{id(target)}"

    def assassin_death_mark_first_wound_available(self, actor, target) -> bool:
        return self.target_is_death_marked_by(actor, target) and not actor.bond_flags.get(self.assassin_first_wound_key(target))

    def use_assassin_weapon_technique(
        self,
        actor,
        target,
        heroes,
        enemies,
        dodging,
        *,
        label: str,
        edge_cost: int = 0,
        require_death_mark: bool = False,
        accuracy_bonus: int = 0,
        armor_break_percent: int = 0,
        opener_damage_dice: str = "",
        execution_damage_dice: str = "",
    ) -> bool:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't use {label} while Charmed.")
            return False
        if require_death_mark and not self.target_is_death_marked_by(actor, target):
            self.say(f"{self.style_name(actor)} needs Death Mark on {self.style_name(target)} for {label}.")
            return False
        if edge_cost > 0 and not self.spend_class_resource(actor, "edge", edge_cost):
            self.say(f"{self.style_name(actor)} needs {edge_cost} Edge for {label}.")
            return False
        weapon_item = self.equipped_weapon_item(actor)
        try:
            target_number = self.effective_attack_target_number(target)
            advantage = self.attack_advantage_state(actor, target, heroes, enemies, dodging, ranged=actor.weapon.ranged)
            total_modifier = (
                actor.attack_bonus()
                + self.ally_pressure_bonus(actor, heroes, ranged=actor.weapon.ranged)
                + self.status_accuracy_modifier(actor)
                + self.attack_focus_modifier(actor, target)
                + self.weapon_master_style_accuracy_modifier(actor, target)
                + self.assassin_accuracy_modifier(actor, target, heroes)
                + self.target_accuracy_modifier(target)
                + accuracy_bonus
            )
            d20 = self.roll_check_d20(
                actor,
                advantage,
                target_number=target_number,
                target_label=self.attack_target_label(target_number),
                modifier=total_modifier,
                style="attack",
                outcome_kind="attack",
                context_label=f"{actor.name} uses {label} on {target.name}",
            )
            total = d20.kept + total_modifier
            critical_hit = d20.kept >= self.critical_threshold(actor)
            if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
                self.say(f"{self.style_name(actor)} reaches for {label}, but {self.style_name(target)} denies the angle.")
                return False
            damage_bonus = actor.damage_bonus() + self.status_damage_modifier(actor)
            damage = max(
                1,
                self.roll_with_display_bonus(
                    actor.weapon.damage,
                    bonus=damage_bonus,
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{actor.name} {label} damage",
                    outcome_kind="damage",
                ).total
                + damage_bonus,
            )
            if opener_damage_dice and (
                self.has_status(actor, "invisible")
                or self.target_is_death_marked_by(actor, target)
                or self.rogue_target_is_exposed(actor, target, heroes)
            ):
                opener = self.roll_with_display_bonus(
                    opener_damage_dice,
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{actor.name} {label} opener",
                    outcome_kind="damage",
                )
                damage += opener.total
                self.say(f"{label} opener adds {self.style_damage(opener.total)} damage.")
            first_mark_wound_available = self.assassin_death_mark_first_wound_available(actor, target)
            if first_mark_wound_available:
                first_wound = self.roll_with_display_bonus(
                    "1d6",
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{actor.name} Death Mark execution",
                    outcome_kind="damage",
                )
                damage += first_wound.total
                self.say(f"Death Mark execution adds {self.style_damage(first_wound.total)} damage.")
            if execution_damage_dice and (
                target.current_hp * 2 <= target.max_hp or self.rogue_target_is_exposed(actor, target, heroes)
            ):
                execution = self.roll_with_display_bonus(
                    execution_damage_dice,
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{actor.name} {label} execution",
                    outcome_kind="damage",
                )
                damage += execution.total
                self.say(f"{label} execution adds {self.style_damage(execution.total)} damage.")
            actual = self.apply_damage(
                target,
                damage,
                damage_type=weapon_item.damage_type if weapon_item is not None else "",
                source_actor=actor,
                apply_defense=True,
                armor_break_percent=armor_break_percent + self.weapon_master_hit_armor_break_percent(actor, target, critical_hit=critical_hit),
            )
            if first_mark_wound_available and self.last_damage_caused_wound():
                actor.bond_flags[self.assassin_first_wound_key(target)] = True
                target.bond_flags["assassin_death_mark_first_wounded_by"] = actor.name
            self.say(f"{self.style_name(actor)} lands {label} for {self.style_damage(actual)} damage.")
            self.announce_downed_target(target)
            self.trigger_on_hit_hooks(
                actor,
                target,
                actual_damage=actual,
                margin=total - target_number,
                critical_hit=critical_hit,
                heroes=heroes,
                enemies=enemies,
            )
            if getattr(target, "current_hp", 0) <= 0 and self.target_is_death_marked_by(actor, target):
                self.grant_rogue_edge(actor, source="dropping Death Mark")
                self.clear_death_mark(actor)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_quiet_knife(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_assassin_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="Quiet Knife",
            accuracy_bonus=1 if self.has_status(actor, "invisible") else 0,
            opener_damage_dice="1d6",
        )

    def use_between_plates(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_assassin_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="Between Plates",
            edge_cost=2,
            require_death_mark=True,
            armor_break_percent=10,
        )

    def use_sudden_end(self, actor, target, heroes, enemies, dodging) -> bool:
        return self.use_assassin_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="Sudden End",
            edge_cost=3,
            require_death_mark=True,
            accuracy_bonus=1,
            execution_damage_dice="2d6",
        )

    def add_rogue_poison_stack(self, actor, target, amount: int = 1, *, duration: int = 2) -> int:
        stacks_by_actor = target.bond_flags.setdefault("rogue_poison_stacks", {})
        if not isinstance(stacks_by_actor, dict):
            stacks_by_actor = {}
            target.bond_flags["rogue_poison_stacks"] = stacks_by_actor
        previous = max(0, int(stacks_by_actor.get(actor.name, 0)))
        stacks_by_actor[actor.name] = min(5, previous + max(0, amount))
        stack_ids = target.bond_flags.setdefault("rogue_poison_stack_ids", {})
        if isinstance(stack_ids, dict):
            stack_ids[actor.name] = id(actor)
        self.apply_status(target, "poisoned", duration, source=f"{actor.name}'s poison")
        return int(stacks_by_actor[actor.name])

    def rogue_poison_stacks(self, actor, target) -> int:
        stacks_by_actor = target.bond_flags.get("rogue_poison_stacks", {})
        if not isinstance(stacks_by_actor, dict):
            return 0
        return max(0, int(stacks_by_actor.get(actor.name, 0)))

    def set_rogue_poison_stacks(self, actor, target, amount: int, *, duration: int = 2) -> int:
        stacks_by_actor = target.bond_flags.setdefault("rogue_poison_stacks", {})
        if not isinstance(stacks_by_actor, dict):
            stacks_by_actor = {}
            target.bond_flags["rogue_poison_stacks"] = stacks_by_actor
        amount = max(0, min(5, int(amount)))
        if amount <= 0:
            stacks_by_actor.pop(actor.name, None)
        else:
            stacks_by_actor[actor.name] = amount
            self.apply_status(target, "poisoned", duration, source=f"{actor.name}'s poison")
        if not stacks_by_actor:
            target.bond_flags.pop("rogue_poison_stacks", None)
        return amount

    def rogue_poison_owner(self, target, owner_name: str, owner_id=None):
        candidates = []
        candidates.extend(getattr(self, "_active_combat_heroes", []) or [])
        candidates.extend(getattr(self, "_active_combat_enemies", []) or [])
        if self.state is not None:
            candidates.extend(self.state.party_members())
        for candidate in candidates:
            if owner_id is not None and id(candidate) == owner_id:
                return candidate
            if owner_id is None and owner_name and getattr(candidate, "name", "") == owner_name:
                return candidate
        return None

    def tick_rogue_poison_stacks(self, target) -> None:
        stacks_by_actor = target.bond_flags.get("rogue_poison_stacks", {})
        if not isinstance(stacks_by_actor, dict) or not stacks_by_actor or not target.is_conscious():
            return
        stack_ids = target.bond_flags.get("rogue_poison_stack_ids", {})
        if not isinstance(stack_ids, dict):
            stack_ids = {}
        for owner_name, raw_stacks in list(stacks_by_actor.items()):
            stacks = max(0, int(raw_stacks))
            if stacks <= 0:
                stacks_by_actor.pop(owner_name, None)
                continue
            owner = self.rogue_poison_owner(target, str(owner_name), stack_ids.get(owner_name))
            damage = min(5, stacks)
            actual = self.apply_damage(target, damage, damage_type="poison", source_actor=owner)
            self.say(f"{self.style_name(target)} suffers {self.style_damage(actual)} poison damage from {owner_name}'s toxin.")
            self.announce_downed_target(target)
            remaining = stacks - 1
            if remaining > 0 and target.is_conscious():
                stacks_by_actor[owner_name] = remaining
                target.conditions["poisoned"] = max(2, int(target.conditions.get("poisoned", 0)))
            else:
                stacks_by_actor.pop(owner_name, None)
        if not stacks_by_actor:
            target.bond_flags.pop("rogue_poison_stacks", None)
            target.bond_flags.pop("rogue_poison_stack_ids", None)

    def is_poisoner_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return bool(features & {"poisoner_toxin", "black_drop", "green_needle", "bitter_cloud", "rot_thread", "bloom_in_the_blood"})

    def poisoner_save_dc(self, actor) -> int:
        return 8 + actor.proficiency_bonus + max(actor.ability_mod("INT"), actor.ability_mod("DEX"))

    def use_black_drop(self, actor) -> bool:
        if "black_drop" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Black Drop training.")
            return False
        if self.has_status(actor, "black_drop"):
            self.say(f"{self.style_name(actor)} already has Black Drop ready.")
            return False
        if not self.spend_class_resource(actor, "toxin"):
            self.say(f"{self.style_name(actor)} needs 1 Toxin to ready Black Drop.")
            return False
        self.apply_status(actor, "black_drop", 3, source=f"{actor.name}'s poison kit")
        self.say(f"{self.style_name(actor)} thumbs open Black Drop for the next clean Wound.")
        return True

    def maybe_deliver_black_drop(self, attacker, target) -> None:
        if not self.has_status(attacker, "black_drop") or "black_drop" not in getattr(attacker, "features", []):
            return
        self.clear_status(attacker, "black_drop")
        save_success = self.saving_throw(
            target,
            "CON",
            self.poisoner_save_dc(attacker),
            context=f"against {attacker.name}'s Black Drop",
            against_poison=True,
        )
        stacks = 1 if save_success else 2
        self.add_rogue_poison_stack(attacker, target, stacks, duration=3)
        self.say(f"Black Drop catches under the seam and leaves Poison {stacks}.")

    def use_poisoner_weapon_technique(
        self,
        actor,
        target,
        heroes,
        enemies,
        dodging,
        *,
        label: str,
        accuracy_bonus: int = 0,
        poison_on_wound: int = 0,
    ) -> bool:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't use {label} while Charmed.")
            return False
        weapon_item = self.equipped_weapon_item(actor)
        try:
            target_number = self.effective_attack_target_number(target)
            advantage = self.attack_advantage_state(actor, target, heroes, enemies, dodging, ranged=actor.weapon.ranged)
            total_modifier = (
                actor.attack_bonus()
                + self.ally_pressure_bonus(actor, heroes, ranged=actor.weapon.ranged)
                + self.status_accuracy_modifier(actor)
                + self.attack_focus_modifier(actor, target)
                + self.weapon_master_style_accuracy_modifier(actor, target)
                + self.assassin_accuracy_modifier(actor, target, heroes)
                + self.target_accuracy_modifier(target)
                + accuracy_bonus
            )
            d20 = self.roll_check_d20(
                actor,
                advantage,
                target_number=target_number,
                target_label=self.attack_target_label(target_number),
                modifier=total_modifier,
                style="attack",
                outcome_kind="attack",
                context_label=f"{actor.name} uses {label} on {target.name}",
            )
            total = d20.kept + total_modifier
            critical_hit = d20.kept >= self.critical_threshold(actor)
            if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
                self.say(f"{self.style_name(actor)} sends {label} wide of the useful vein.")
                return False
            damage_bonus = actor.damage_bonus() + self.status_damage_modifier(actor)
            damage = max(
                1,
                self.roll_with_display_bonus(
                    actor.weapon.damage,
                    bonus=damage_bonus,
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{actor.name} {label} damage",
                    outcome_kind="damage",
                ).total
                + damage_bonus,
            )
            actual = self.apply_damage(
                target,
                damage,
                damage_type=weapon_item.damage_type if weapon_item is not None else "",
                source_actor=actor,
                apply_defense=True,
                armor_break_percent=self.weapon_master_hit_armor_break_percent(actor, target, critical_hit=critical_hit),
            )
            if poison_on_wound > 0 and self.last_damage_caused_wound() and target.is_conscious():
                stacks = self.add_rogue_poison_stack(actor, target, poison_on_wound, duration=3)
                self.say(f"{label} leaves Poison {stacks}.")
            self.say(f"{self.style_name(actor)} lands {label} for {self.style_damage(actual)} damage.")
            self.announce_downed_target(target)
            self.trigger_on_hit_hooks(
                actor,
                target,
                actual_damage=actual,
                margin=total - target_number,
                critical_hit=critical_hit,
                heroes=heroes,
                enemies=enemies,
            )
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_green_needle(self, actor, target, heroes, enemies, dodging) -> bool:
        if "green_needle" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Green Needle training.")
            return False
        return self.use_poisoner_weapon_technique(
            actor,
            target,
            heroes,
            enemies,
            dodging,
            label="Green Needle",
            accuracy_bonus=1,
            poison_on_wound=1,
        )

    def use_bitter_cloud(self, actor, target) -> bool:
        if "bitter_cloud" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Bitter Cloud training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't throw Bitter Cloud while Charmed.")
            return False
        if not self.spend_class_resource(actor, "toxin"):
            self.say(f"{self.style_name(actor)} needs 1 Toxin for Bitter Cloud.")
            return False
        try:
            save_success = self.saving_throw(
                target,
                "CON",
                self.poisoner_save_dc(actor),
                context=f"against {actor.name}'s Bitter Cloud",
                against_poison=True,
            )
            stacks = 1 if save_success else 2
            self.add_rogue_poison_stack(actor, target, stacks, duration=3)
            if not save_success:
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s Bitter Cloud")
            self.say(f"{self.style_name(actor)} breaks Bitter Cloud around {self.style_name(target)} and leaves Poison {stacks}.")
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_rot_thread(self, actor, target) -> bool:
        if "rot_thread" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Rot Thread training.")
            return False
        if self.rogue_poison_stacks(actor, target) <= 0:
            self.say(f"{self.style_name(target)} needs {self.style_name(actor)}'s poison before Rot Thread can bite.")
            return False
        if not self.spend_class_resource(actor, "toxin"):
            self.say(f"{self.style_name(actor)} needs 1 Toxin for Rot Thread.")
            return False
        self.apply_status(target, "rot_thread", 2, source=f"{actor.name}'s Rot Thread")
        self.apply_status(target, "armor_broken", 1, source=f"{actor.name}'s Rot Thread")
        self.say(f"{self.style_name(actor)} turns the poison sour under {self.style_name(target)}'s armor.")
        return True

    def use_bloom_in_the_blood(self, actor, target) -> bool:
        if "bloom_in_the_blood" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Bloom In The Blood training.")
            return False
        stacks = self.rogue_poison_stacks(actor, target)
        if stacks <= 0:
            self.say(f"{self.style_name(target)} has no poison for Bloom In The Blood.")
            return False
        if not self.spend_class_resource(actor, "toxin", 2):
            self.say(f"{self.style_name(actor)} needs 2 Toxin for Bloom In The Blood.")
            return False
        try:
            actual = self.apply_damage(target, stacks * 2, damage_type="poison", source_actor=actor)
            self.set_rogue_poison_stacks(actor, target, max(0, stacks - 2), duration=2)
            self.say(f"Bloom In The Blood turns Poison {stacks} into {self.style_damage(actual)} poison damage.")
            self.announce_downed_target(target)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def spend_rogue_satchel(self, actor, amount: int = 1) -> bool:
        return self.spend_class_resource(actor, "satchel", amount)

    def is_alchemist_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return bool(features & {"alchemist_quick_mix", "redcap_tonic", "smoke_jar", "bitter_acid", "field_stitch"})

    def alchemist_save_dc(self, actor) -> int:
        return 8 + actor.proficiency_bonus + max(actor.ability_mod("INT"), actor.ability_mod("DEX"))

    def alchemist_numbing_temp_hp(self, actor) -> int:
        return max(1, actor.proficiency_bonus + max(0, actor.ability_mod("INT")))

    def use_quick_mix(self, actor, rider: str = "numbed") -> bool:
        if "alchemist_quick_mix" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Quick Mix training.")
            return False
        if self.has_status(actor, "quick_mix"):
            self.say(f"{self.style_name(actor)} already has a Quick Mix ready.")
            return False
        rider_key = str(rider or "numbed").strip().lower().replace(" ", "_").replace("-", "_")
        if rider_key not in {"numbed", "smoke", "acid_cut"}:
            rider_key = "numbed"
        rider_labels = {
            "numbed": "numbing paste",
            "smoke": "clinging smoke",
            "acid_cut": "acid-cut solvent",
        }
        actor.bond_flags["alchemist_quick_mix_rider"] = rider_key
        self.apply_status(actor, "quick_mix", 2, source=f"{actor.name}'s satchel")
        self.say(f"{self.style_name(actor)} readies {rider_labels[rider_key]} for the next satchel mixture.")
        return True

    def consume_alchemist_quick_mix(self, actor) -> str:
        if not self.has_status(actor, "quick_mix"):
            actor.bond_flags.pop("alchemist_quick_mix_rider", None)
            return ""
        rider = str(actor.bond_flags.pop("alchemist_quick_mix_rider", "numbed"))
        self.clear_status(actor, "quick_mix")
        return rider

    def apply_alchemist_numbing(self, actor, target, *, source: str) -> int:
        temp_hp = self.alchemist_numbing_temp_hp(actor)
        target.grant_temp_hp(temp_hp)
        self.say(f"{source} leaves {self.style_name(target)} with {self.style_healing(temp_hp)} temporary hit points.")
        return temp_hp

    def use_redcap_tonic(self, actor, target) -> bool:
        if "redcap_tonic" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Redcap Tonic training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond Redcap Tonic.")
            return False
        if not self.spend_rogue_satchel(actor):
            self.say(f"{self.style_name(actor)} needs 1 Satchel for Redcap Tonic.")
            return False
        bonus = max(0, actor.ability_mod("INT"))
        roll = self.roll_with_display_bonus(
            "1d6",
            bonus=bonus,
            style="healing",
            context_label=f"{actor.name} Redcap Tonic",
            outcome_kind="healing",
        )
        healed = target.heal(max(1, roll.total + bonus))
        rider = self.consume_alchemist_quick_mix(actor)
        if rider == "numbed":
            self.apply_alchemist_numbing(actor, target, source="Quick Mix")
        elif rider == "smoke":
            self.apply_status(target, "smoke_jar", 1, source=f"{actor.name}'s smoky Redcap Tonic")
        play_heal_sound_for = getattr(self, "play_heal_sound_for", None)
        if healed > 0 and callable(play_heal_sound_for):
            play_heal_sound_for(actor)
        self.say(f"{self.style_name(actor)} uses Redcap Tonic on {self.style_name(target)}, restoring {self.style_healing(healed)} hit points.")
        return True

    def use_smoke_jar(self, actor, target, allies: list | None = None) -> bool:
        if "smoke_jar" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Smoke Jar training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} cannot use Smoke Jar cover.")
            return False
        if not self.spend_rogue_satchel(actor):
            self.say(f"{self.style_name(actor)} needs 1 Satchel for Smoke Jar.")
            return False
        rider = self.consume_alchemist_quick_mix(actor)
        duration = 2 if rider == "smoke" else 1
        smoke_targets = [ally for ally in (allies or [target]) if not getattr(ally, "dead", False)]
        if target not in smoke_targets:
            smoke_targets.append(target)
        for ally in smoke_targets:
            self.apply_status(ally, "smoke_jar", duration, source=f"{actor.name}'s Smoke Jar")
        self.apply_status(target, "invisible", 1, source=f"{actor.name}'s Smoke Jar")
        if rider == "numbed":
            self.apply_alchemist_numbing(actor, target, source="Quick Mix")
        self.grant_rogue_edge(actor, source="Smoke Jar cover")
        self.say(f"{self.style_name(actor)} cracks Smoke Jar and makes a short-lived cover lane.")
        return True

    def use_bitter_acid(self, actor, target) -> bool:
        if "bitter_acid" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Bitter Acid training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't throw Bitter Acid while Charmed.")
            return False
        if not self.spend_rogue_satchel(actor):
            self.say(f"{self.style_name(actor)} needs 1 Satchel for Bitter Acid.")
            return False
        rider = self.consume_alchemist_quick_mix(actor)
        try:
            bonus = max(0, actor.ability_mod("INT"))
            rolled = self.roll_with_display_bonus(
                "1d4",
                bonus=bonus,
                style="damage",
                context_label=f"{actor.name} Bitter Acid",
                outcome_kind="damage",
            )
            amount = max(1, rolled.total + bonus)
            save_success = self.saving_throw(
                target,
                "DEX",
                self.alchemist_save_dc(actor),
                context=f"against {actor.name}'s Bitter Acid",
            )
            actual = self.apply_damage(target, amount if not save_success else max(1, amount // 2), damage_type="acid", source_actor=actor)
            self.apply_status(target, "acid", 1 if save_success else 2, source=f"{actor.name}'s Bitter Acid")
            if not save_success:
                self.apply_status(target, "armor_broken", 1, source=f"{actor.name}'s Bitter Acid")
                if rider == "acid_cut":
                    self.apply_status(target, "reeling", 1, source=f"{actor.name}'s acid-cut solvent")
            elif rider == "acid_cut":
                self.apply_status(target, "exposed", 1, source=f"{actor.name}'s acid-cut solvent")
            self.say(f"{self.style_name(actor)} splashes Bitter Acid over {self.style_name(target)} for {self.style_damage(actual)} acid damage.")
            self.announce_downed_target(target)
            return True
        finally:
            self.break_invisibility_from_hostile_action(actor)

    def use_field_stitch(self, actor, target) -> bool:
        if "field_stitch" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Field Stitch training.")
            return False
        if getattr(target, "dead", False):
            self.say(f"{self.style_name(target)} is beyond Field Stitch.")
            return False
        if not self.spend_rogue_satchel(actor):
            self.say(f"{self.style_name(actor)} needs 1 Satchel for Field Stitch.")
            return False
        rider = self.consume_alchemist_quick_mix(actor)
        was_bleeding = self.has_status(target, "bleeding")
        if was_bleeding:
            self.clear_status(target, "bleeding")
        healed = 0
        if target.current_hp == 0:
            target.current_hp = 1
            target.stable = False
            target.death_successes = 0
            target.death_failures = 0
            healed = 1
        else:
            healed = target.heal(max(1, actor.proficiency_bonus + max(0, actor.ability_mod("INT"))))
        if rider == "numbed":
            self.apply_alchemist_numbing(actor, target, source="Quick Mix")
        elif rider == "smoke":
            self.apply_status(target, "smoke_jar", 1, source=f"{actor.name}'s smoky Field Stitch")
        play_heal_sound_for = getattr(self, "play_heal_sound_for", None)
        if healed > 0 and callable(play_heal_sound_for):
            play_heal_sound_for(actor)
        bleed_text = " and stops the bleeding" if was_bleeding else ""
        self.say(f"{self.style_name(actor)} uses Field Stitch on {self.style_name(target)}, restoring {self.style_healing(healed)} hit points{bleed_text}.")
        return True

    def rogue_target_is_exposed(self, actor, target, allies: list | None = None) -> bool:
        if self.has_status(actor, "invisible"):
            return True
        if self.target_is_marked_by(actor, target):
            return True
        if self.target_is_tool_read_by(actor, target):
            return True
        exposed_statuses = ("marked", "prone", "restrained", "reeling", "blinded", "poisoned", "armor_broken", "tool_read", "exposed")
        if any(self.has_status(target, status) for status in exposed_statuses):
            return True
        if allies is not None and any(ally is not actor and ally.is_conscious() for ally in allies):
            return True
        return False

    def use_rogue_feint(self, actor, target) -> bool:
        if "rogue_feint" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Feint training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't feint toward harm while Charmed.")
            return False
        success, margin = self.resolve_rogue_trick_check(
            actor,
            target,
            trick_kind="feint",
            context_label=f"{actor.name} feints {target.name}",
        )
        if not success:
            self.say(f"{self.style_name(actor)} sells a false step, but {self.style_name(target)} keeps the line.")
            return False
        self.apply_status(target, "reeling", 1, source=f"{actor.name}'s Feint")
        if margin >= 5:
            self.apply_status(target, "exposed", 1, source=f"{actor.name}'s Feint")
        self.grant_rogue_edge(actor, source="a clean Feint")
        self.say(f"{self.style_name(actor)} catches {self.style_name(target)} leaning the wrong way.")
        return True

    def use_dirty_trick(self, actor, target, trick_kind: str = "distract") -> bool:
        if "dirty_trick" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Dirty Trick training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't work a dirty angle while Charmed.")
            return False
        trick_kind = trick_kind.lower().strip()
        success, margin = self.resolve_rogue_trick_check(
            actor,
            target,
            trick_kind=trick_kind,
            context_label=f"{actor.name} uses Dirty Trick on {target.name}",
        )
        if not success:
            self.say(f"{self.style_name(actor)} reaches for a dirty trick, but {self.style_name(target)} sees enough of it.")
            return False
        if trick_kind in {"blind", "sand", "flash"}:
            self.apply_status(target, "blinded", 1, source=f"{actor.name}'s Dirty Trick")
        elif trick_kind in {"trip", "shove", "tangle"}:
            self.apply_status(target, "prone", 1, source=f"{actor.name}'s Dirty Trick")
        elif trick_kind in {"seam", "strap", "armor", "expose"}:
            self.apply_status(target, "armor_broken", 1, source=f"{actor.name}'s Dirty Trick")
        else:
            self.apply_status(target, "exposed", 1, source=f"{actor.name}'s Dirty Trick")
            if margin >= 5:
                self.apply_status(target, "reeling", 1, source=f"{actor.name}'s Dirty Trick")
        self.grant_rogue_edge(actor, source="a dirty opening")
        self.say(f"{self.style_name(actor)} turns a small tool and a bad angle into trouble for {self.style_name(target)}.")
        return True

    def use_rogue_skirmish(self, actor) -> bool:
        if "rogue_skirmish" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Skirmish training.")
            return False
        if not self.spend_class_resource(actor, "edge"):
            self.say(f"{self.style_name(actor)} needs 1 Edge to Skirmish.")
            return False
        self.set_combat_stance(actor, "mobile", announce=False)
        actor.bond_flags["rogue_skirmish_round"] = int(getattr(self, "_active_round_number", 0) or 0)
        self.say(f"{self.style_name(actor)} spends 1 Edge and skims into Mobile Stance.")
        return True

    def use_slip_away(self, actor, *, source: str = "Slip Away") -> bool:
        if "slip_away" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Slip Away training.")
            return False
        if not self.can_use_class_reaction(actor):
            return False
        if not self.spend_class_resource(actor, "edge"):
            return False
        self.spend_class_reaction(actor, source=source)
        self.apply_status(actor, "slip_away", 1, source=source)
        self.say(f"{self.style_name(actor)} spends 1 Edge and slips the strike line.")
        return True

    def maybe_use_slip_away(self, attacker, target, *, total: int, target_number: int, critical_hit: bool) -> bool:
        if critical_hit or total < target_number:
            return False
        if total >= target_number + 2:
            return False
        if self.use_slip_away(target, source=f"{attacker.name}'s attack"):
            self.say(f"{self.style_name(attacker)}'s hit turns into air as {self.style_name(target)} slips away.")
            return True
        return False

    def maybe_gain_rogue_edge_from_near_miss(self, attacker, target, *, total: int, target_number: int) -> None:
        if not self.actor_uses_class_resource(target, "edge"):
            return
        gap = target_number - total
        if gap < 1 or gap > 4:
            return
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        key = f"rogue_near_miss_edge_round_{id(attacker)}"
        if int(target.bond_flags.get(key, -1)) == current_round:
            return
        target.bond_flags[key] = current_round
        self.grant_rogue_edge(target, source="a near miss")

    def is_shadowguard_actor(self, actor) -> bool:
        features = set(getattr(actor, "features", []))
        return "shadowguard_shadow" in features or self.actor_uses_class_resource(actor, "shadow")

    def shadowguard_false_target_owner(self, protected):
        owner_id = protected.bond_flags.get("shadowguard_false_target_by_id")
        owner_name = str(protected.bond_flags.get("shadowguard_false_target_by", ""))
        candidates = []
        candidates.extend(getattr(self, "_active_combat_heroes", []) or [])
        candidates.extend(getattr(self, "_active_combat_enemies", []) or [])
        if self.state is not None:
            candidates.extend(self.state.party_members())
        for candidate in candidates:
            if owner_id is not None and id(candidate) == owner_id:
                return candidate
            if owner_id is None and owner_name and getattr(candidate, "name", "") == owner_name:
                return candidate
        return None

    def apply_false_target(self, actor, target, *, duration: int = 1) -> None:
        target.bond_flags["shadowguard_false_target_by"] = actor.name
        target.bond_flags["shadowguard_false_target_by_id"] = id(actor)
        self.apply_status(target, "false_target", duration, source=f"{actor.name}'s False Target")

    def clear_false_target(self, target) -> None:
        self.clear_status(target, "false_target")
        target.bond_flags.pop("shadowguard_false_target_by", None)
        target.bond_flags.pop("shadowguard_false_target_by_id", None)

    def use_false_target(self, actor, target) -> bool:
        if "false_target" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no False Target training.")
            return False
        if not self.spend_class_resource(actor, "edge"):
            self.say(f"{self.style_name(actor)} needs 1 Edge to set a False Target.")
            return False
        self.apply_false_target(actor, target)
        self.say(f"{self.style_name(actor)} throws a False Target around {self.style_name(target)}.")
        return True

    def use_cover_the_healer(self, actor, target) -> bool:
        if "cover_the_healer" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Cover The Healer training.")
            return False
        if not self.spend_class_resource(actor, "shadow", 2):
            self.say(f"{self.style_name(actor)} needs 2 Shadow to Cover The Healer.")
            return False
        self.apply_false_target(actor, target, duration=2)
        self.apply_status(target, "guarded", 1, source=f"{actor.name}'s Cover The Healer")
        self.apply_status(target, "shadow_lane", 1, source=f"{actor.name}'s Cover The Healer")
        self.say(f"{self.style_name(actor)} folds a Shadow lane around {self.style_name(target)}.")
        return True

    def use_smoke_pin(self, actor, target) -> bool:
        if "smoke_pin" not in getattr(actor, "features", []):
            self.say(f"{self.style_name(actor)} has no Smoke Pin training.")
            return False
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't throw smoke toward harm while Charmed.")
            return False
        if not self.spend_class_resource(actor, "shadow"):
            self.say(f"{self.style_name(actor)} needs 1 Shadow to Smoke Pin.")
            return False
        success, margin = self.resolve_rogue_trick_check(
            actor,
            target,
            trick_kind="blind",
            context_label=f"{actor.name} uses Smoke Pin on {target.name}",
        )
        if not success:
            self.say(f"{self.style_name(actor)} breaks smoke across the lane, but {self.style_name(target)} keeps the angle.")
            return False
        self.apply_status(target, "blinded", 1, source=f"{actor.name}'s Smoke Pin")
        self.apply_status(target, "exposed", 1, source=f"{actor.name}'s Smoke Pin")
        self.apply_status(actor, "invisible", 1, source="Smoke Pin")
        if margin >= 5:
            self.grant_rogue_edge(actor, source="Smoke Pin pressure")
        self.say(f"{self.style_name(actor)} pins {self.style_name(target)} behind a hard burst of smoke.")
        return True

    def maybe_gain_shadowguard_shadow_from_miss(self, attacker, target, *, total: int, target_number: int) -> None:
        if not self.actor_uses_class_resource(target, "shadow"):
            return
        if total >= target_number:
            return
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        key = f"shadowguard_miss_shadow_round_{id(attacker)}"
        if int(target.bond_flags.get(key, -1)) == current_round:
            return
        target.bond_flags[key] = current_round
        self.grant_shadowguard_shadow(target, source="an enemy miss")

    def maybe_trigger_false_target_miss(self, attacker, target, *, total: int, target_number: int) -> bool:
        if not self.has_status(target, "false_target"):
            return False
        owner = self.shadowguard_false_target_owner(target)
        self.clear_false_target(target)
        if owner is None or not owner.is_conscious():
            return True
        self.grant_shadowguard_shadow(owner, source="a False Target miss")
        if target_number - total <= 2 and attacker.is_conscious():
            self.apply_status(attacker, "reeling", 1, source=f"{owner.name}'s False Target")
        return True

    def can_use_class_reaction(self, actor) -> bool:
        current_round = int(getattr(self, "_active_round_number", 0) or 0)
        return int(actor.bond_flags.get("class_reaction_used_round", -1)) != current_round

    def spend_class_reaction(self, actor, *, source: str = "") -> bool:
        if not self.can_use_class_reaction(actor):
            return False
        actor.bond_flags["class_reaction_used_round"] = int(getattr(self, "_active_round_number", 0) or 0)
        if source:
            actor.bond_flags["class_reaction_source"] = source
        return True

    def trigger_on_hit_hooks(
        self,
        attacker,
        target,
        *,
        actual_damage: int,
        margin: int,
        critical_hit: bool,
        heroes: list | None = None,
        enemies: list | None = None,
    ) -> None:
        if self.actor_uses_class_resource(attacker, "edge") and self.rogue_target_is_exposed(attacker, target, heroes):
            self.grant_class_resource(attacker, "edge", source="an exposed hit")
        self.record_weapon_master_hit(attacker, target)
        if self.actor_uses_class_resource(attacker, "fury") and self.current_combat_stance_key(attacker) == "aggressive":
            self.grant_berserker_fury(attacker, source="an Aggressive hit")
        if (
            self.actor_uses_class_resource(attacker, "fury")
            and getattr(target, "current_hp", 0) <= 0
            and "enemy" in getattr(target, "tags", [])
        ):
            defeat_key = f"berserker_fury_defeat_{id(target)}"
            if not attacker.bond_flags.get(defeat_key):
                attacker.bond_flags[defeat_key] = True
                self.grant_berserker_fury(attacker, source=f"dropping {target.name}")
        if self.target_is_marked_by(attacker, target):
            target.bond_flags["class_mark_last_hit_by"] = attacker.name

    def trigger_on_wound_hooks(self, attacker, target, result: DamageResolution) -> None:
        if self.target_is_marked_by(attacker, target):
            target.bond_flags["class_mark_last_wounded_by"] = attacker.name
            self.grant_class_resource(attacker, "edge", source="a marked Wound")
        if self.actor_uses_class_resource(attacker, "toxin") and self.has_status(target, "poisoned"):
            self.grant_class_resource(attacker, "toxin", source="poison riding a Wound")
        self.maybe_deliver_black_drop(attacker, target)
        if self.actor_uses_class_resource(attacker, "blood_debt") and (
            self.target_is_red_marked_by(attacker, target) or self.has_status(target, "bleeding")
        ):
            self.grant_bloodreaver_debt(attacker, source="a useful Wound")
        self.maybe_trigger_red_mark_healing(attacker, target)
        if self.actor_uses_class_resource(attacker, "fury") and self.has_status(attacker, "redline"):
            heal_amount = attacker.proficiency_bonus
            healed = attacker.heal(heal_amount)
            if healed > 0:
                self.say(f"{self.style_name(attacker)} drinks the Redline back into breath and heals {self.style_healing(healed)}.")
        if self.actor_uses_class_resource(attacker, "fury") and self.has_status(attacker, "drink_the_hurt"):
            heal_roll = self.roll_with_display_bonus(
                "1d4",
                bonus=attacker.ability_mod("CON"),
                style="healing",
                context_label=f"{attacker.name} Drink The Hurt",
                outcome_kind="healing",
            )
            healed = attacker.heal(max(1, heal_roll.total + attacker.ability_mod("CON")))
            self.clear_status(attacker, "drink_the_hurt")
            if healed > 0:
                self.say(f"{self.style_name(attacker)} drinks the hurt clean and heals {self.style_healing(healed)}.")

    def trigger_damage_resolution_hooks(self, target, source_actor, *, damage_type: str) -> None:
        result = self.last_damage_resolution()
        if result.glance:
            self.grant_warrior_grit(target, source="turning a hit into a Glance")
        elif result.wound:
            self.grant_warrior_grit(target, source="taking a Wound")
            if self.actor_uses_class_resource(target, "fury"):
                self.grant_berserker_fury(target, source="taking a Wound")
                if self.has_status(target, "reeling") and not target.bond_flags.get("berserker_break_mood_used"):
                    target.bond_flags["berserker_break_mood_used"] = True
                    self.clear_status(target, "reeling")
                    self.say(f"{self.style_name(target)} breaks the mood and shakes off Reeling.")
            if self.actor_uses_class_resource(target, "blood_debt"):
                self.grant_bloodreaver_debt(target, source="taking a Wound")
            self.grant_blood_debt_for_ally_wound(target)
        if self.actor_uses_class_resource(target, "momentum") and self.damage_type_uses_defense(damage_type):
            defense_removed = max(0, result.resisted_damage - result.mitigated_damage)
            if result.glance:
                self.grant_juggernaut_momentum(target, source="a Glance")
            elif result.defense_percent >= 30 and defense_removed > 0:
                self.grant_juggernaut_momentum(target, source="armor taking the force")
            if source_actor is not None and self.target_is_fixated_by(target, source_actor):
                self.grant_juggernaut_momentum(target, source="a Fixated enemy pressing in")
        if source_actor is not None and result.wound:
            self.trigger_on_wound_hooks(source_actor, target, result)

    def trigger_post_hp_damage_hooks(self, target, source_actor, *, previous_hp: int, damage_type: str) -> None:
        if not self.actor_uses_class_resource(target, "fury") or target.max_hp <= 0:
            return
        if target.bond_flags.get("berserker_half_hp_fury_used"):
            return
        if previous_hp * 2 >= target.max_hp and target.current_hp * 2 < target.max_hp and target.current_hp > 0:
            target.bond_flags["berserker_half_hp_fury_used"] = True
            self.grant_berserker_fury(target, source="dropping below half HP")

    def use_warrior_shove(self, actor, target) -> None:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't force the issue while Charmed.")
            return
        self.record_opening_tutorial_combat_event("combat_warrior_shove", actor=actor, target=target)
        target_number = self.stability_target_number(target)
        total_modifier = (
                actor.ability_mod("STR")
                + actor.proficiency_bonus
                + actor.equipment_bonuses.get("attack", 0)
                + actor.gear_bonuses.get("attack", 0)
                + actor.relationship_bonuses.get("attack", 0)
                + self.status_accuracy_modifier(actor)
            )
        d20 = self.roll_check_d20(
            actor,
            self.d20_disadvantage_state(actor, attack=True),
            target_number=target_number,
            target_label=self.stability_target_label(target_number),
            modifier=total_modifier,
            style="attack",
            outcome_kind="attack",
            context_label=f"{actor.name} shoves {target.name}",
        )
        total = d20.kept + total_modifier
        if d20.kept == 1 or (d20.kept != 20 and total < target_number):
            self.say(f"{self.style_name(actor)} shoves into {self.style_name(target)}, but the footing holds.")
            return
        margin = total - target_number
        self.apply_status(target, "prone", 1, source=f"{actor.name}'s shove")
        self.say(f"{self.style_name(actor)} breaks {self.style_name(target)}'s footing with a shove.")
        if margin >= 5 and target.is_conscious():
            self.apply_status(target, "reeling", 1, source=f"{actor.name}'s shove")
            self.grant_warrior_grit(actor, source="a strong shove")

    def use_warrior_pin(self, actor, target, heroes, enemies, dodging) -> bool:
        if not self.can_make_hostile_action(actor):
            self.say(f"{self.style_name(actor)} can't pin a target while Charmed.")
            return False
        target_number = self.effective_attack_target_number(target)
        advantage = self.attack_advantage_state(actor, target, heroes, enemies, dodging, ranged=actor.weapon.ranged)
        total_modifier = (
            actor.attack_bonus()
            + self.ally_pressure_bonus(actor, heroes, ranged=actor.weapon.ranged)
            + self.status_accuracy_modifier(actor)
            + self.attack_focus_modifier(actor, target)
            + self.target_accuracy_modifier(target)
        )
        d20 = self.roll_check_d20(
            actor,
            advantage,
            target_number=target_number,
            target_label=self.attack_target_label(target_number),
            modifier=total_modifier,
            style="attack",
            outcome_kind="attack",
            context_label=f"{actor.name} pins {target.name}",
        )
        total = d20.kept + total_modifier
        critical_hit = d20.kept >= self.critical_threshold(actor)
        if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
            self.say(f"{self.style_name(actor)} tries to pin {self.style_name(target)}, but the angle slips.")
            return False
        self.maybe_gain_grit_from_strong_hit(actor, total - target_number)
        damage_bonus = actor.damage_bonus() + self.status_damage_modifier(actor)
        damage = max(
            1,
            self.roll_with_display_bonus(
                actor.weapon.damage,
                bonus=damage_bonus,
                critical=critical_hit,
                style="damage",
                context_label=f"{actor.name} pin damage",
                outcome_kind="damage",
            ).total
            + damage_bonus,
        )
        weapon_item = self.equipped_weapon_item(actor)
        actual = self.apply_damage(
            target,
            damage,
            damage_type=weapon_item.damage_type if weapon_item is not None else "",
            source_actor=actor,
            apply_defense=True,
        )
        if target.is_conscious():
            self.apply_status(target, "reeling", 1, source=f"{actor.name}'s pin")
            if total - target_number >= 5:
                self.fixate_target(actor, target, duration=1)
        self.say(f"{self.style_name(actor)} pins {self.style_name(target)} for {self.style_damage(actual)} damage.")
        self.announce_downed_target(target)
        self.trigger_on_hit_hooks(
            actor,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
            heroes=heroes,
            enemies=enemies,
        )
        return True

    def perform_weapon_attack(self, attacker, target, heroes, enemies, dodging) -> None:
        if not self.can_make_hostile_action(attacker):
            self.say(f"{self.style_name(attacker)} can't bring themselves to make a hostile move while Charmed.")
            return
        play_attack_sound_for = getattr(self, "play_attack_sound_for", None)
        if callable(play_attack_sound_for):
            play_attack_sound_for(attacker)
        weapon_item = self.equipped_weapon_item(attacker)
        try:
            advantage = self.attack_advantage_state(attacker, target, heroes, enemies, dodging, ranged=attacker.weapon.ranged)
            target_number = self.effective_attack_target_number(target)
            total_modifier = (
                attacker.attack_bonus()
                + self.ally_pressure_bonus(attacker, heroes, ranged=attacker.weapon.ranged)
                + self.status_accuracy_modifier(attacker)
                + self.attack_focus_modifier(attacker, target)
                + self.weapon_master_style_accuracy_modifier(attacker, target)
                + self.assassin_accuracy_modifier(attacker, target, heroes)
                + self.target_accuracy_modifier(target)
            )
            d20 = self.roll_check_d20(
                attacker,
                advantage,
                target_number=target_number,
                target_label=self.attack_target_label(target_number),
                modifier=total_modifier,
                style="attack",
                outcome_kind="attack",
                context_label=f"{attacker.name} attacks {target.name}",
            )
            total = d20.kept + total_modifier
            if d20.kept == 1:
                self.say(f"{self.style_name(attacker)} misses {self.style_name(target)} outright.")
                return
            critical_hit = d20.kept >= self.critical_threshold(attacker)
            if critical_hit and target.gear_bonuses.get("crit_immunity", 0):
                critical_hit = False
                self.say(f"{self.style_name(target)}'s armor turns a critical hit into a normal one.")
            if not critical_hit and total < target_number:
                self.say(f"{self.style_name(attacker)} attacks {self.style_name(target)} but misses {self.attack_target_label(target_number)}.")
                return
            self.maybe_gain_grit_from_strong_hit(attacker, total - target_number)
            damage_bonus = attacker.damage_bonus() + self.status_damage_modifier(attacker)
            damage_roll = self.roll_with_display_bonus(
                attacker.weapon.damage,
                bonus=damage_bonus,
                critical=critical_hit,
                style="damage",
                context_label=f"{attacker.name} weapon damage",
                outcome_kind="damage",
            )
            weapon_damage = damage_roll.total + damage_bonus
            weapon_damage_type = weapon_item.damage_type if weapon_item is not None else ""
            if attacker.class_name == "Rogue" and advantage >= 0 and self.can_sneak_attack(attacker, heroes, target):
                sneak = self.roll_with_animation_context(
                    self.rogue_sneak_attack_dice(attacker),
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{attacker.name} Veilstrike",
                    outcome_kind="damage",
                )
                weapon_damage += sneak.total
                self.say(f"Veilstrike adds {self.style_damage(sneak.total)} damage.")
                self.record_opening_tutorial_combat_event("combat_veilstrike", actor=attacker, target=target)
            martial_bonus = None
            if attacker.archetype == "rukhar" and any(enemy.is_conscious() and enemy is not attacker for enemy in enemies):
                martial_bonus = self.roll_with_animation_context(
                    "2d6",
                    style="damage",
                    context_label=f"{attacker.name} martial edge",
                    outcome_kind="damage",
                )
                weapon_damage += martial_bonus.total
                self.say(f"{self.style_name(attacker)}'s martial edge adds {self.style_damage(martial_bonus.total)} damage.")
            style_armor_break = self.weapon_master_hit_armor_break_percent(attacker, target, critical_hit=critical_hit)
            total_actual = self.apply_damage(
                target,
                max(1, weapon_damage),
                damage_type=weapon_damage_type,
                source_actor=attacker,
                apply_defense=True,
                armor_break_percent=style_armor_break,
            )
            if weapon_item is not None and weapon_item.extra_damage_dice:
                extra = self.roll_with_animation_context(
                    weapon_item.extra_damage_dice,
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{weapon_item.enchantment or weapon_item.name} bonus damage",
                    outcome_kind="damage",
                )
                extra_actual = self.apply_damage(target, extra.total, damage_type=weapon_item.extra_damage_type, source_actor=attacker, apply_defense=True)
                total_actual += extra_actual
                self.say(
                    f"{weapon_item.enchantment or weapon_item.name} adds {self.style_damage(extra_actual)} "
                    f"{weapon_item.extra_damage_type or 'magic'} damage."
                )
            if critical_hit and weapon_item is not None and weapon_item.crit_extra_damage_dice:
                vicious = self.roll_with_animation_context(
                    weapon_item.crit_extra_damage_dice,
                    style="damage",
                    context_label=f"{weapon_item.enchantment or weapon_item.name} critical damage",
                    outcome_kind="damage",
                )
                vicious_actual = self.apply_damage(target, vicious.total, damage_type=weapon_damage_type, source_actor=attacker, apply_defense=True)
                total_actual += vicious_actual
                self.say(f"{weapon_item.enchantment or weapon_item.name} tears in for {self.style_damage(vicious_actual)} extra critical damage.")
            if total_actual <= 0 and self.last_damage_was_glance():
                self.say(f"{self.style_name(attacker)} hits {self.style_name(target)}, but the blow glances off their Defense.")
            else:
                self.say(f"{self.style_name(attacker)} hits {self.style_name(target)} for {self.style_damage(total_actual)} damage.")
            self.apply_weapon_master_style_rider(
                attacker,
                target,
                actual_damage=total_actual,
                margin=total - target_number,
                critical_hit=critical_hit,
            )
            self.announce_downed_target(target)
            self.trigger_on_hit_hooks(
                attacker,
                target,
                actual_damage=total_actual,
                margin=total - target_number,
                critical_hit=critical_hit,
                heroes=heroes,
                enemies=enemies,
            )
            if total_actual > 0 and attacker.archetype in {"rukhar", "varyn"}:
                self.apply_poison_on_hit(attacker, target)
            if attacker.weapon.ranged or "bow" in attacker.weapon.name.lower():
                self.trigger_blacklake_adjudicator_reflection(attacker, target, source=attacker.weapon.name)
                return
            if d20.kept >= 18 and target.is_conscious():
                self.apply_status(target, "reeling", 1, source=attacker.name)
        finally:
            self.break_invisibility_from_hostile_action(attacker)

    def perform_enemy_attack(self, attacker, target, heroes, enemies, dodging) -> bool:
        play_attack_sound_for = getattr(self, "play_attack_sound_for", None)
        if callable(play_attack_sound_for):
            play_attack_sound_for(attacker)
        weapon_item = self.equipped_weapon_item(attacker)
        target_had_positive_status = self.hero_has_positive_combat_status(target)
        target_had_blessing = any(self.has_status(target, status) for status in ("blessed", "emboldened"))
        advantage = self.attack_advantage_state(attacker, target, heroes, enemies, dodging, ranged=attacker.weapon.ranged)
        target_number = self.effective_attack_target_number(target)
        total_modifier = (
            attacker.attack_bonus()
            + self.ally_pressure_bonus(attacker, enemies, ranged=attacker.weapon.ranged)
            + self.status_accuracy_modifier(attacker)
            + self.attack_focus_modifier(attacker, target)
            + self.target_accuracy_modifier(target)
        )
        d20 = self.roll_check_d20(
            attacker,
            advantage,
            target_number=target_number,
            target_label=self.attack_target_label(target_number),
            modifier=total_modifier,
            style="attack",
            outcome_kind="attack",
            context_label=f"{attacker.name} attacks {target.name}",
        )
        total = d20.kept + total_modifier
        critical_hit = d20.kept == 20 and not target.gear_bonuses.get("crit_immunity", 0)
        if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
            false_target_triggered = self.maybe_trigger_false_target_miss(
                attacker,
                target,
                total=total,
                target_number=target_number,
            )
            if d20.kept != 1:
                self.maybe_gain_rogue_edge_from_near_miss(
                    attacker,
                    target,
                    total=total,
                    target_number=target_number,
                )
            if not false_target_triggered:
                self.maybe_gain_shadowguard_shadow_from_miss(
                    attacker,
                    target,
                    total=total,
                    target_number=target_number,
                )
            self.say(f"{self.style_name(attacker)} fails to land a hit on {self.style_name(target)}.")
            return False
        if d20.kept == 20 and not critical_hit:
            self.say(f"{self.style_name(target)}'s armor blunts what would have been a critical strike.")
        if self.maybe_use_slip_away(
            attacker,
            target,
            total=total,
            target_number=target_number,
            critical_hit=critical_hit,
        ):
            return False
        if self.has_status(target, "false_target"):
            self.clear_false_target(target)
        damage_bonus = attacker.damage_bonus() + self.status_damage_modifier(attacker)
        damage_roll = self.roll_with_display_bonus(
            attacker.weapon.damage,
            bonus=damage_bonus,
            critical=critical_hit,
            style="damage",
            context_label=f"{attacker.name} weapon damage",
            outcome_kind="damage",
        )
        damage = max(1, damage_roll.total + damage_bonus)
        if self.has_status(target, "marked"):
            damage += 2
            self.say(f"The ember mark on {target.name} flares and gives {attacker.name} a cleaner wound to drive into.")
        actual = self.apply_damage(
            target,
            damage,
            damage_type=weapon_item.damage_type if weapon_item is not None else "",
            source_actor=attacker,
            apply_defense=True,
        )
        if actual <= 0 and self.last_damage_was_glance():
            self.say(f"{self.style_name(attacker)} hits {self.style_name(target)}, but the blow glances off their Defense.")
        else:
            self.say(f"{self.style_name(attacker)} hits {self.style_name(target)} for {self.style_damage(actual)} damage.")
        self.announce_downed_target(target)
        self.trigger_on_hit_hooks(
            attacker,
            target,
            actual_damage=actual,
            margin=total - target_number,
            critical_hit=critical_hit,
            heroes=enemies,
            enemies=heroes,
        )
        if attacker.archetype == "resonance_leech" and target.is_conscious():
            if any(self.has_status(target, status) for status in ("frightened", "reeling", "deafened")):
                extra = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "1d6",
                        style="damage",
                        context_label=f"{attacker.name}'s echo feast",
                        outcome_kind="damage",
                    ).total,
                    damage_type="psychic",
                )
                self.say(f"{attacker.name} feeds on the broken cadence for {self.style_damage(extra)} extra psychic damage.")
                self.announce_downed_target(target)
        if attacker.archetype == "pact_archive_warden":
            self.apply_status(attacker, "guarded", 1, source=f"{attacker.name}'s custody protocol")
        if attacker.archetype == "survey_chain_revenant" and target.is_conscious() and self.has_status(target, "grappled"):
            self.apply_status(attacker, "guarded", 1, source=f"{attacker.name}'s unfinished shift")
        if attacker.archetype == "censer_horror" and target.is_conscious() and self.has_status(target, "frightened"):
            extra = self.apply_damage(
                target,
                self.roll_with_display_bonus(
                    "1d4",
                    style="damage",
                    context_label=f"{attacker.name}'s cinder liturgy",
                    outcome_kind="damage",
                ).total,
                damage_type="fire",
            )
            self.say(f"{attacker.name}'s cinder liturgy bites into the panic for {self.style_damage(extra)} extra fire damage.")
            self.announce_downed_target(target)
        if attacker.archetype == "memory_taker_adept" and target_had_positive_status and not attacker.bond_flags.get("borrowed_instinct_used"):
            attacker.bond_flags["borrowed_instinct_used"] = True
            self.apply_status(attacker, "emboldened", 2, source=f"{attacker.name}'s borrowed instinct")
        if attacker.archetype == "covenant_breaker_wight" and target_had_blessing:
            current_round = int(getattr(self, "_active_round_number", 0) or 0)
            if int(attacker.bond_flags.get("life_levy_round", -1)) != current_round:
                attacker.bond_flags["life_levy_round"] = current_round
                healed = attacker.heal(6)
                if healed > 0:
                    self.say(f"{attacker.name} levies life from the broken vow and regains {self.style_healing(healed)} hit points.")
        if attacker.archetype == "hollowed_survey_titan" and attacker.current_hp * 2 > attacker.max_hp:
            self.apply_status(attacker, "guarded", 1, source=f"{attacker.name}'s loadbearing frame")
        if attacker.archetype == "ashstone_percher" and attacker.resources.get("drop_strike", 0) > 0 and target.is_conscious():
            attacker.resources["drop_strike"] = 0
            extra = self.apply_damage(
                target,
                self.roll_with_display_bonus(
                    "1d4",
                    style="damage",
                    context_label=f"{attacker.name} drop strike",
                    outcome_kind="damage",
                ).total,
                damage_type="slashing",
            )
            self.say(f"{attacker.name} crashes down from above for {self.style_damage(extra)} extra slashing damage.")
            self.announce_downed_target(target)
        if attacker.archetype == "bugbear_reaver" and attacker.resources.get("surprise_attack", 0) > 0 and target.is_conscious():
            attacker.resources["surprise_attack"] = 0
            extra = self.apply_damage(
                target,
                self.roll_with_display_bonus(
                    "2d6",
                    critical=critical_hit,
                    style="damage",
                    context_label=f"{attacker.name} ambush damage",
                    outcome_kind="damage",
                ).total,
                damage_type="bludgeoning",
            )
            self.say(f"{attacker.name} turns the first clean opening into {self.style_damage(extra)} extra ambush damage.")
            self.announce_downed_target(target)
        if attacker.archetype in {"wolf", "worg"} and target.is_conscious():
            if not self.saving_throw(target, "STR", 11, context=f"against {attacker.name}'s mauling rush"):
                self.apply_status(target, "prone", 1, source=attacker.name)
        if attacker.archetype == "briar_twig" and target.is_conscious():
            if not self.saving_throw(target, "STR", 11, context=f"against {attacker.name}'s snagging thorns"):
                self.apply_status(target, "reeling", 2, source=f"{attacker.name}'s snagging thorns")
        if actual > 0 and attacker.archetype == "carrion_stalker" and target.is_conscious():
            self.apply_status(target, "bleeding", 2, source=f"{attacker.name}'s serrated talons")
        if attacker.archetype == "bandit" and d20.kept >= 18 and target.is_conscious():
            if not self.saving_throw(target, "STR", 11, context=f"against {attacker.name}'s clinch"):
                self.apply_status(target, "grappled", 1, source=attacker.name)
        if attacker.archetype == "acidmaw_burrower" and target.is_conscious():
            if not self.saving_throw(target, "STR", 12, context=f"against {attacker.name}'s burrowing clamp"):
                self.apply_status(target, "grappled", 1, source=f"{attacker.name}'s burrowing clamp")
        if attacker.archetype == "rust_shell_scuttler" and target.is_conscious():
            if self.has_status(target, "acid"):
                extra = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "1d4",
                        style="damage",
                        context_label=f"{attacker.name} acid bite",
                        outcome_kind="damage",
                    ).total,
                    damage_type="acid",
                )
                self.say(f"{attacker.name} worries an already-corroded weak point for {self.style_damage(extra)} extra acid damage.")
                self.announce_downed_target(target)
            self.apply_status(target, "acid", 2, source=f"{attacker.name}'s rust-bite")
        if attacker.archetype == "ogre_brute" and d20.kept >= 18 and target.is_conscious():
            if not self.saving_throw(target, "STR", 12, context=f"against {attacker.name}'s club smash"):
                self.apply_status(target, "prone", 1, source=attacker.name)
        if attacker.archetype == "nothic" and d20.kept >= 18 and target.is_conscious():
            if not self.saving_throw(target, "WIS", 12, context=f"against {attacker.name}'s invasive whisper"):
                self.apply_status(target, "frightened", 1, source=attacker.name)
        if actual > 0 and attacker.archetype in {"rukhar", "varyn", "mireweb_spider", "ettervine_webherd", "duskmire_matriarch"}:
            self.apply_poison_on_hit(attacker, target)
        if attacker.archetype == "cache_mimic" and target.is_conscious():
            if attacker.resources.get("adhesive_grab", 0) > 0:
                attacker.resources["adhesive_grab"] = 0
            if not self.saving_throw(target, "STR", 13, context=f"against {attacker.name}'s adhesive bite"):
                self.apply_status(target, "grappled", 2, source=f"{attacker.name}'s adhesive bite")
        if attacker.archetype == "stonegaze_skulker" and target.is_conscious() and self.has_status(target, "restrained"):
            extra = self.apply_damage(
                target,
                self.roll_with_display_bonus(
                    "1d4",
                    style="damage",
                    context_label=f"{attacker.name} venom",
                    outcome_kind="damage",
                ).total,
                damage_type="poison",
            )
            self.say(f"{attacker.name}'s mineral venom bites deeper for {self.style_damage(extra)} poison damage.")
            self.announce_downed_target(target)
        if attacker.archetype == "grimlock_tunneler" and target.is_conscious():
            if self.has_status(target, "reeling") or d20.kept >= 18:
                if not self.saving_throw(target, "STR", 12, context=f"against {attacker.name}'s hooked drag"):
                    self.apply_status(target, "grappled", 2, source=f"{attacker.name}'s hooked drag")
        if attacker.archetype == "hookclaw_burrower" and target.is_conscious():
            if not self.saving_throw(target, "STR", 14, context=f"against {attacker.name}'s cave drag"):
                already_grappled = self.has_status(target, "grappled")
                self.apply_status(target, "grappled", 2, source=f"{attacker.name}'s cave drag")
                if already_grappled:
                    self.apply_status(target, "prone", 1, source=f"{attacker.name}'s cave drag")
        if attacker.archetype == "stirge_swarm" and target.is_conscious():
            attacker.bond_flags["attached_to"] = target.name
            self.apply_status(target, "grappled", 2, source=f"{attacker.name}'s feeding swarm")
            self.say(f"{attacker.name} latches onto {target.name} and begins feeding.")
        if attacker.archetype == "ochre_slime" and target.is_conscious():
            acid = self.apply_damage(
                target,
                self.roll_with_display_bonus(
                    "1d4",
                    style="damage",
                    context_label=f"{attacker.name} corrosive slime",
                    outcome_kind="damage",
                ).total,
                damage_type="acid",
            )
            self.say(f"{attacker.name}'s dripping pseudopod burns for an extra {self.style_damage(acid)} acid damage.")
            self.apply_status(target, "acid", 2, source=f"{attacker.name}'s corrosive slime")
            self.announce_downed_target(target)
        if attacker.archetype == "animated_armor" and target.is_conscious() and d20.kept >= 18:
            if not self.saving_throw(target, "STR", 13, context=f"against {attacker.name}'s driving slam"):
                self.apply_status(target, "prone", 1, source=f"{attacker.name}'s driving slam")
        if attacker.archetype == "cliff_harpy" and target.is_conscious() and attacker.resources.get("swoop", 0) > 0:
            attacker.resources["swoop"] = 0
            if not self.saving_throw(target, "STR", 12, context=f"against {attacker.name}'s swooping pass"):
                self.apply_status(target, "prone", 1, source=f"{attacker.name}'s swoop")
        if attacker.archetype == "whispermaw_blob" and target.is_conscious() and d20.kept >= 18:
            if not self.saving_throw(target, "STR", 13, context=f"against {attacker.name}'s warped bulk"):
                self.apply_status(target, "prone", 1, source=f"{attacker.name}'s warped bulk")
        if attacker.archetype == "blacklake_pincerling" and target.is_conscious():
            if not self.saving_throw(target, "STR", 13, context=f"against {attacker.name}'s pincer hold"):
                self.apply_status(target, "grappled", 2, source=f"{attacker.name}'s pincer hold")
        if attacker.archetype == "thunderroot_mound" and target.is_conscious():
            if not self.saving_throw(target, "STR", 14, context=f"against {attacker.name}'s grasping roots"):
                self.apply_status(target, "restrained", 2, source=f"{attacker.name}'s grasping roots")
        if attacker.archetype == "oathbroken_revenant" and target.is_conscious():
            if target.name == str(attacker.bond_flags.get("marked_target", "")):
                extra = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "1d6",
                        style="damage",
                        context_label=f"{attacker.name}'s vendetta",
                        outcome_kind="damage",
                    ).total,
                    damage_type="necrotic",
                )
                self.say(f"{attacker.name}'s vendetta cuts deeper for {self.style_damage(extra)} necrotic damage.")
                self.announce_downed_target(target)
        if attacker.archetype == "choir_executioner" and target.is_conscious():
            if any(self.has_status(target, status) for status in ("frightened", "restrained", "incapacitated")):
                extra = self.apply_damage(
                    target,
                    self.roll_with_display_bonus(
                        "2d6",
                        style="damage",
                        context_label=f"{attacker.name}'s execution strike",
                        outcome_kind="damage",
                    ).total,
                    damage_type="slashing",
                )
                self.say(f"{attacker.name} turns the opening into {self.style_damage(extra)} extra execution damage.")
                self.announce_downed_target(target)
        if attacker.archetype == "lantern_fen_wisp" and target.is_conscious() and attacker.resources.get("vanish", 0) > 0 and attacker.current_hp <= attacker.max_hp // 2:
            attacker.resources["vanish"] = 0
            self.apply_status(attacker, "invisible", 1, source=f"{attacker.name}'s vanish")
        return True

    def perform_offhand_attack(self, attacker, target, heroes, enemies, dodging) -> None:
        if not self.can_make_hostile_action(attacker):
            self.say(f"{self.style_name(attacker)} cannot lash out with an off-hand strike while Charmed.")
            return
        play_attack_sound_for = getattr(self, "play_attack_sound_for", None)
        if callable(play_attack_sound_for):
            play_attack_sound_for(attacker)
        off_hand_item = self.equipped_off_hand_weapon_item(attacker)
        if off_hand_item is None:
            self.say(f"{self.style_name(attacker)} has no off-hand weapon ready.")
            return
        weapon = off_hand_item.weapon
        try:
            advantage = self.attack_advantage_state(attacker, target, heroes, enemies, dodging, ranged=weapon.ranged)
            target_number = self.effective_attack_target_number(target)
            total_modifier = (
                self.weapon_attack_bonus_for(attacker, weapon)
                + self.ally_pressure_bonus(attacker, heroes, ranged=weapon.ranged)
                + self.status_accuracy_modifier(attacker)
                + self.attack_focus_modifier(attacker, target)
                + self.target_accuracy_modifier(target)
            )
            d20 = self.roll_check_d20(
                attacker,
                advantage,
                target_number=target_number,
                target_label=self.attack_target_label(target_number),
                modifier=total_modifier,
                style="attack",
                outcome_kind="attack",
                context_label=f"{attacker.name} off-hand attack",
            )
            total = d20.kept + total_modifier
            critical_hit = d20.kept >= self.critical_threshold(attacker)
            if d20.kept == 1 or (not critical_hit and d20.kept != 20 and total < target_number):
                self.say(f"{self.style_name(attacker)}'s off-hand attack misses {self.style_name(target)}.")
                return
            self.maybe_gain_grit_from_strong_hit(attacker, total - target_number)
            damage_bonus = self.weapon_damage_bonus_for(attacker, weapon, include_ability_mod=False) + self.status_damage_modifier(attacker)
            actual = self.apply_damage(
                target,
                max(
                    1,
                    self.roll_with_display_bonus(
                        weapon.damage,
                        bonus=damage_bonus,
                        critical=critical_hit,
                        style="damage",
                        context_label=f"{attacker.name} off-hand damage",
                        outcome_kind="damage",
                    ).total
                    + damage_bonus,
                ),
                damage_type=off_hand_item.damage_type,
                source_actor=attacker,
                apply_defense=True,
            )
            self.say(f"{self.style_name(attacker)} strikes with {off_hand_item.name} for {self.style_damage(actual)} damage.")
            self.announce_downed_target(target)
        finally:
            self.break_invisibility_from_hostile_action(attacker)

    def help_downed_ally(self, actor, target) -> None:
        success = self.skill_check(actor, "Medicine", 10, context=f"to haul {target.name} back into the fight")
        if success:
            target.current_hp = 1
            target.stable = False
            target.death_successes = 0
            target.death_failures = 0
            play_heal_sound_for = getattr(self, "play_heal_sound_for", None)
            if callable(play_heal_sound_for):
                play_heal_sound_for(actor)
            self.say(
                f"{self.style_name(actor)} gets {self.style_name(target)} back to their feet at "
                f"{self.style_healing(1)} hit point."
            )
            return
        target.stable = True
        target.death_successes = 0
        target.death_failures = 0
        self.say(f"{self.style_name(actor)} stabilizes {self.style_name(target)}, but they cannot stand yet.")

    def use_healing_potion(self, user, target) -> None:
        healing_potion = ITEMS["potion_healing"]
        if not (user.spend_item("Healing Potion") or user.spend_item(healing_potion.name)):
            self.say(f"{self.style_name(user)} fumbles for a healing potion that is no longer there.")
            return
        healed = target.heal(
            self.roll_with_animation_context(
                healing_potion.heal_dice,
                style="healing",
                context_label=healing_potion.name,
                outcome_kind="healing",
            ).total
            + healing_potion.heal_bonus
            + target.gear_bonuses.get("healing_received", 0)
        )
        play_heal_sound_for = getattr(self, "play_heal_sound_for", None)
        if healed > 0 and callable(play_heal_sound_for):
            play_heal_sound_for(user)
        self.say(
            f"{self.style_name(user)} uses {healing_potion.name} on {self.style_name(target)}, "
            f"restoring {self.style_healing(healed)} hit points."
        )

    def attempt_parley(self, actor, enemies, dc: int) -> None:
        skill = "Persuasion" if actor.skill_bonus("Persuasion") >= actor.skill_bonus("Intimidation") else "Intimidation"
        success = self.skill_check(actor, skill, dc, context="to force a break in the enemy's morale")
        if not success:
            for enemy in enemies:
                if enemy.is_conscious():
                    self.apply_status(enemy, "emboldened", 1, source="defying the parley")
            self.say("The enemy line hardens instead of yielding.")
            return
        leader = next((enemy for enemy in enemies if enemy.is_conscious() and "leader" in enemy.tags), None)
        if leader is not None and leader.current_hp <= leader.max_hp // 2:
            for enemy in enemies:
                if enemy.is_conscious():
                    enemy.current_hp = 0
                    enemy.dead = True
            self.say("The leader's nerve breaks and the rest of the encounter collapses with it.")
            return
        weakest = min((enemy for enemy in enemies if enemy.is_conscious()), key=lambda enemy: enemy.current_hp)
        weakest.current_hp = 0
        weakest.dead = True
        for enemy in enemies:
            if enemy.is_conscious():
                self.apply_status(enemy, "frightened", 1, source="the collapsing line")
        self.say(f"{self.style_name(weakest)} decides this pay is not worth dying for and flees.")

    def attack_advantage_state(self, attacker, target, heroes, enemies, dodging, *, ranged: bool = False) -> int:
        state = 0
        if self.dodge_applies_against_attacker(target, attacker):
            state -= 1
        if "pack_tactics" in getattr(attacker, "features", []) and any(enemy.is_conscious() and enemy is not attacker for enemy in enemies):
            state += 1
        state += self.d20_disadvantage_state(attacker, attack=True)
        if self.has_status(attacker, "prone"):
            state -= 1
        if self.has_status(attacker, "invisible"):
            state += 1
        if self.has_status(target, "blinded"):
            state += 1
        if self.has_status(target, "restrained") or self.has_status(target, "stunned") or self.has_status(target, "paralyzed"):
            state += 1
        if self.has_status(target, "invisible") and "blind_sense" not in getattr(attacker, "features", []):
            state -= 1
        if self.has_status(target, "prone"):
            state += -1 if ranged else 1
        if self.has_status(target, "petrified") or self.has_status(target, "unconscious"):
            state += 1
        return 1 if state > 0 else -1 if state < 0 else 0

    def can_sneak_attack(self, attacker, heroes, target) -> bool:
        return target.is_conscious() and self.rogue_target_is_exposed(attacker, target, heroes)

    def apply_poison_on_hit(self, attacker, target) -> None:
        dc = 12
        damage_roll = "1d4"
        condition_duration = 2
        always_damage = False
        source_text = f"{attacker.name}'s strike"
        if attacker.archetype == "mireweb_spider":
            dc = 11
            condition_duration = 1
            always_damage = True
            source_text = f"{attacker.name}'s venom"
        elif attacker.archetype == "ettervine_webherd":
            dc = 12
            condition_duration = 2
            always_damage = True
            source_text = f"{attacker.name}'s hooked fangs"
        elif attacker.archetype == "duskmire_matriarch":
            dc = 15
            damage_roll = "1d6"
            condition_duration = 2
            source_text = f"{attacker.name}'s widow venom"
        was_poisoned = self.has_status(target, "poisoned")
        save_success = self.saving_throw(target, "CON", dc, context=f"against {attacker.name}'s poisoned strike", against_poison=True)
        if save_success and not always_damage:
            return
        actual = self.apply_damage(
            target,
            self.roll_with_animation_context(
                damage_roll,
                style="damage",
                context_label=f"{attacker.name} poison damage",
                outcome_kind="damage",
            ).total,
            damage_type="poison",
        )
        self.say(f"{self.style_name(target)} suffers {self.style_damage(actual)} poison damage.")
        if not save_success:
            self.apply_status(target, "poisoned", condition_duration, source=source_text)
        if attacker.archetype == "rukhar" and not save_success and not self.saving_throw(target, "CON", 12, context=f"against {attacker.name}'s numbing poison", against_poison=True):
            self.apply_status(target, "paralyzed", 1, source=f"{attacker.name}'s numbing poison")
        if attacker.archetype == "varyn" and not save_success and not self.saving_throw(target, "CON", 12, context=f"against {attacker.name}'s draining toxin", against_poison=True):
            self.apply_status(target, "exhaustion", 2, source=f"{attacker.name}'s draining toxin")
        if attacker.archetype == "duskmire_matriarch" and not save_success and was_poisoned:
            if not self.saving_throw(target, "CON", 15, context=f"against {attacker.name}'s follow-up venom", against_poison=True):
                self.apply_status(target, "paralyzed", 1, source=f"{attacker.name}'s widow venom")
        self.announce_downed_target(target)

    def apply_damage(
        self,
        target,
        amount: int,
        *,
        damage_type: str = "",
        source_actor=None,
        apply_defense: bool = False,
        armor_break_percent: int = 0,
        armor_break: int = 0,
    ) -> int:
        self._last_damage_resolution = DamageResolution(raw_damage=max(0, amount))
        if target.dead:
            return 0
        if self.god_mode_enabled() and self.is_party_member_actor(target):
            return 0
        previous_hp = target.current_hp
        if (
            source_actor is not None
            and self.instant_kill_enabled()
            and self.is_party_member_actor(source_actor)
            and "enemy" in getattr(target, "tags", [])
        ):
            damage = 1000
            target.temp_hp = 0
            target.current_hp = 0
            target.dead = True
            self._last_damage_resolution = DamageResolution(
                raw_damage=max(0, amount),
                resisted_damage=damage,
                mitigated_damage=damage,
                hp_damage=damage,
                wound=damage > 0,
            )
            if previous_hp > 0:
                self.animate_health_bar_loss(target, previous_hp, target.current_hp)
                damage_hook = getattr(self, "after_actor_damaged", None)
                if callable(damage_hook):
                    damage_hook(target, previous_hp=previous_hp, damage=damage, damage_type=damage_type)
            return damage
        damage = max(0, amount)
        raw_damage = damage
        if self.has_status(target, "petrified"):
            damage //= 2
        resisted = False
        if damage_type == "poison" and "dwarven_resilience" in target.features:
            resisted = True
        if damage_type == "fire" and "hellish_resistance" in target.features:
            resisted = True
        if self.has_damage_resistance(target, damage_type):
            resisted = True
        if resisted:
            damage //= 2
        resisted_damage = damage
        defense_percent = 0
        total_armor_break_percent = 0
        if apply_defense and self.damage_type_uses_defense(damage_type):
            total_armor_break_percent = self.total_armor_break_percent(
                target,
                source_actor=source_actor,
                incoming_percent=armor_break_percent,
                incoming_steps=armor_break,
            )
            defense_percent = self.effective_defense_percent(
                target,
                damage_type=damage_type,
                armor_break_percent=total_armor_break_percent,
            )
            damage = damage * (100 - defense_percent) // 100
        mitigated_damage = damage
        ward_shell_absorbed = self.maybe_use_ward_shell(target, damage, source_actor=source_actor, damage_type=damage_type)
        damage -= ward_shell_absorbed
        resource_ward_absorbed = self.absorb_ward_damage(
            target,
            damage,
            source_actor=source_actor,
            damage_type=damage_type,
        )
        damage -= resource_ward_absorbed
        ward_absorbed = ward_shell_absorbed + resource_ward_absorbed
        temp_hp_absorbed = 0
        if target.temp_hp > 0:
            absorbed = min(target.temp_hp, damage)
            target.temp_hp -= absorbed
            damage -= absorbed
            temp_hp_absorbed = absorbed
        self._last_damage_resolution = DamageResolution(
            raw_damage=raw_damage,
            resisted_damage=resisted_damage,
            defense_percent=defense_percent,
            armor_break_percent=total_armor_break_percent,
            mitigated_damage=mitigated_damage,
            ward_absorbed=ward_absorbed,
            temp_hp_absorbed=temp_hp_absorbed,
            hp_damage=max(0, damage),
            glance=apply_defense and raw_damage > 0 and resisted_damage > 0 and mitigated_damage <= 0,
            wound=damage > 0,
        )
        self.trigger_damage_resolution_hooks(target, source_actor, damage_type=damage_type)
        if damage <= 0:
            return 0
        if target.current_hp == 0 and "enemy" not in target.tags:
            target.death_failures += 1
            if target.death_failures >= 3:
                target.dead = True
                if self.is_player_actor(target):
                    self.clear_liars_blessing_on_player_death()
            return damage
        target.current_hp = max(0, target.current_hp - damage)
        self.trigger_post_hp_damage_hooks(target, source_actor, previous_hp=previous_hp, damage_type=damage_type)
        if target.current_hp == 0:
            if "enemy" in target.tags:
                if target.archetype == "cinderflame_skull" and target.resources.get("rekindle", 0) > 0:
                    target.resources["rekindle"] = 0
                    target.current_hp = 10
                    target.dead = False
                    self.say(f"{self.style_name(target)} collapses into ash, then flares back together with 10 hit points.")
                    return damage
                if target.archetype == "oathbroken_revenant" and target.resources.get("relentless_return", 0) > 0:
                    if str(target.bond_flags.get("marked_target", "")).strip():
                        target.resources["relentless_return"] = 0
                        target.current_hp = 12
                        target.dead = False
                        self.say(f"{self.style_name(target)} drags itself back upright on unfinished hatred with 12 hit points.")
                        return damage
                target.dead = True
            else:
                target.stable = False
                target.death_successes = 0
                target.death_failures = 0
        if target.current_hp < previous_hp:
            self.animate_health_bar_loss(target, previous_hp, target.current_hp)
            damage_hook = getattr(self, "after_actor_damaged", None)
            if callable(damage_hook):
                damage_hook(target, previous_hp=previous_hp, damage=damage, damage_type=damage_type)
        return damage

    def announce_downed_target(self, target) -> None:
        if target.current_hp == 0 and not target.dead and "enemy" not in target.tags:
            self.say(f"{self.style_name(target)} falls unconscious and begins making death resist checks.")

    def recover_after_battle(self) -> None:
        assert self.state is not None
        recovered: list[str] = []
        for member in self.state.party_members():
            if member.dead:
                continue
            if member.current_hp == 0:
                member.current_hp = 1
                member.stable = False
                member.death_successes = 0
                member.death_failures = 0
                recovered.append(member.name)
        if recovered:
            self.say("Once the danger passes, the party drags " + ", ".join(recovered) + " back to consciousness at 1 hit point.")

    def resolve_death_save(self, actor) -> None:
        d20 = self.roll_check_d20(
            actor,
            0,
            target_number=10,
            target_label="DC 10",
            modifier=0,
            style="save",
            outcome_kind="save",
            context_label=f"{actor.name} death resist",
        )
        if d20.kept == 1:
            actor.death_failures += 2
            self.say(f"{self.style_name(actor)} rolls a natural 1 on a death resist check and suffers two failures.")
        elif d20.kept == 20:
            actor.current_hp = 1
            actor.death_successes = 0
            actor.death_failures = 0
            self.say(f"{self.style_name(actor)} rolls a natural 20 and staggers back to {self.style_healing(1)} hit point.")
            return
        elif d20.kept >= 10:
            actor.death_successes += 1
            self.say(f"{self.style_name(actor)} succeeds on a death resist check.")
        else:
            actor.death_failures += 1
            self.say(f"{self.style_name(actor)} fails a death resist check.")
        if actor.death_successes >= 3:
            actor.stable = True
            actor.death_successes = 0
            actor.death_failures = 0
            self.say(f"{self.style_name(actor)} stabilizes at 0 hit points.")
        if actor.death_failures >= 3:
            actor.dead = True
            if self.is_player_actor(actor):
                self.clear_liars_blessing_on_player_death()

    def skill_check(self, actor, skill: str, dc: int, *, context: str) -> bool:
        commit_pending_story_check_choice_attempt = getattr(self, "commit_pending_story_check_choice_attempt", None)
        if callable(commit_pending_story_check_choice_attempt):
            commit_pending_story_check_choice_attempt()
        dc = self.effective_skill_dc(dc, context=context)
        if self.always_fail_dice_checks_enabled() and self.is_party_member_actor(actor):
            self.set_pending_scaled_check_reward(False)
            self.say(f"{self.style_name(actor)} automatically fails the {self.style_skill_label(skill)} check {context}.")
            self.say("")
            return False
        advantage = self.d20_disadvantage_state(actor, skill=skill, context=context)
        companion_modifier = 0
        companion_lines: list[str] = []
        companion_assist = getattr(self, "companion_skill_check_assist", None)
        if callable(companion_assist):
            companion_modifier, companion_lines = companion_assist(actor, skill, context)
        for line in companion_lines:
            self.say(line)
        total_modifier = actor.skill_bonus(skill) + companion_modifier
        d20 = self.roll_check_d20(
            actor,
            advantage,
            target_number=dc,
            target_label=f"DC {dc}",
            modifier=total_modifier,
            style="skill",
            outcome_kind="check",
            context_label=f"{actor.name} {skill} check",
        )
        total = d20.kept + total_modifier
        self.say(
            f"{self.style_name(actor)} makes a {self.style_skill_label(skill)} check {context}: {total} vs DC {dc}."
        )
        success = total >= dc
        play_sound_effect = getattr(self, "play_sound_effect", None)
        if callable(play_sound_effect):
            play_sound_effect("skill_success" if success else "skill_fail")
        self.set_pending_scaled_check_reward(success and self.is_party_member_actor(actor))
        if not success:
            self.say("")
        return success

    def saving_throw(self, actor, ability: str, dc: int, *, context: str, against_poison: bool = False) -> bool:
        resist_label = f"{ability_label(ability, include_code=True)} resist"
        if self.always_fail_dice_checks_enabled() and self.is_party_member_actor(actor):
            self.say(f"{self.style_name(actor)} automatically fails the {resist_label} {context}.")
            return False
        if self.always_pass_dice_checks_enabled() and self.is_party_member_actor(actor):
            self.say(f"{self.style_name(actor)} automatically clears the {resist_label} {context}.")
            return True
        if self.auto_fail_save(actor, ability):
            self.say(f"{self.style_name(actor)} automatically fails the {resist_label} {context}.")
            return False
        advantage = 1 if against_poison and "dwarven_resilience" in actor.features else 0
        if ability == "DEX" and self.actor_is_dodging(actor):
            advantage += 1
        if self.has_status(actor, "restrained") and ability == "DEX":
            advantage -= 1
        exhaustion = max(0, int(actor.conditions.get("exhaustion", 0)))
        if exhaustion >= 3:
            advantage -= 1
        total_modifier = (
            actor.save_bonus(ability)
            + self.status_value(actor, "save_bonus")
            - self.status_value(actor, "save_penalty")
        )
        d20 = self.roll_check_d20(
            actor,
            advantage,
            target_number=dc,
            target_label=f"DC {dc}",
            modifier=total_modifier,
            style="save",
            outcome_kind="save",
            context_label=f"{actor.name} {resist_label}",
        )
        total = d20.kept + total_modifier
        self.say(f"{self.style_name(actor)} makes a {resist_label} {context}: {total} vs DC {dc}.")
        return total >= dc

    def roll_with_advantage(self, actor, advantage_state: int) -> D20Outcome:
        return roll_d20(self.rng, advantage_state=advantage_state, lucky="lucky" in actor.features)

    def roll_check_d20(
        self,
        actor,
        advantage_state: int,
        *,
        target_number: int | None = None,
        target_label: str | None = None,
        modifier: int = 0,
        context_label: str | None = None,
        style: str | None = None,
        outcome_kind: str | None = None,
    ) -> D20Outcome:
        if self.always_fail_dice_checks_enabled() and self.is_party_member_actor(actor):
            forced_rolls = [1, 1] if advantage_state != 0 else [1]
            return D20Outcome(kept=1, rolls=forced_rolls, rerolls=[], advantage_state=advantage_state)
        if self.always_pass_dice_checks_enabled() and self.is_party_member_actor(actor):
            kept = 20
            if target_number is not None:
                kept = max(2, target_number - modifier)
            forced_rolls = [kept, kept] if advantage_state != 0 else [kept]
            return D20Outcome(kept=kept, rolls=forced_rolls, rerolls=[], advantage_state=advantage_state)
        with self.temporary_roll_animation_metadata(
            target_number=target_number,
            target_label=target_label,
            total_modifier=modifier,
            context_label=context_label,
            style=style,
            outcome_kind=outcome_kind,
        ):
            return self.roll_with_advantage(actor, advantage_state)

    def roll_initiative(self, heroes, enemies, *, hero_bonus: int = 0, enemy_bonus: int = 0) -> list:
        entries: list[dict[str, object]] = []
        with self.suspend_dice_roll_animation():
            for index, actor in enumerate(heroes):
                if actor.dead:
                    continue
                modifier = actor.ability_mod("DEX") + hero_bonus + self.initiative_bonus(actor)
                outcome = self.roll_check_d20(
                    actor,
                    0,
                    modifier=modifier,
                    context_label=f"{actor.name} rolls initiative",
                    style="initiative",
                    outcome_kind="initiative",
                )
                entries.append(
                    {
                        "actor": actor,
                        "outcome": outcome,
                        "modifier": modifier,
                        "total": outcome.kept + modifier,
                        "dex_mod": actor.ability_mod("DEX"),
                        "side_priority": 1,
                        "tie_index": -index,
                    }
                )
            for index, actor in enumerate(enemies):
                modifier = actor.ability_mod("DEX") + enemy_bonus + self.initiative_bonus(actor)
                outcome = self.roll_check_d20(
                    actor,
                    0,
                    modifier=modifier,
                    context_label=f"{actor.name} rolls initiative",
                    style="initiative",
                    outcome_kind="initiative",
                )
                entries.append(
                    {
                        "actor": actor,
                        "outcome": outcome,
                        "modifier": modifier,
                        "total": outcome.kept + modifier,
                        "dex_mod": actor.ability_mod("DEX"),
                        "side_priority": 0,
                        "tie_index": -index,
                    }
                )
        entries.sort(
            key=lambda entry: (entry["total"], entry["dex_mod"], entry["side_priority"], entry["tie_index"]),
            reverse=True,
        )
        self.animate_initiative_rolls(entries)
        return [entry["actor"] for entry in entries]

    def describe_living_combatants(self, combatants) -> list[str]:
        living = [combatant for combatant in combatants if not combatant.dead]
        name_width = max((len(strip_ansi(self.style_name(combatant))) for combatant in living), default=0)
        return [self.describe_combatant(combatant, name_width=name_width) for combatant in living]

    def combat_roster_panel(self, title: str, color: str, lines: list[str], *, empty_message: str):
        return Panel(
            Group(*(self.rich_from_ansi(line) for line in (lines or [empty_message]))),
            title=self.rich_text(title, color, bold=True),
            border_style=rich_style_name(color),
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def combat_battlefield_row_renderable(self, hero_lines: list[str], enemy_lines: list[str]):
        if not self.rich_enabled() or Panel is None or Group is None or box is None:
            return None
        party_panel = self.combat_roster_panel(
            "Party",
            "light_aqua",
            hero_lines,
            empty_message="No one is still standing.",
        )
        enemy_panel = self.combat_roster_panel(
            "Enemies",
            "light_red",
            enemy_lines,
            empty_message="Enemies routed.",
        )
        return self.rich_panel_row_renderable([party_panel, enemy_panel], ratios=[1, 1], padding=(0, 1))

    def print_battlefield(self, heroes, enemies) -> None:
        hero_lines = self.describe_living_combatants(heroes)
        enemy_lines = self.describe_living_combatants(enemies)
        battlefield_row = self.combat_battlefield_row_renderable(hero_lines, enemy_lines)
        if battlefield_row is not None and self.emit_rich(battlefield_row, width=self.safe_rich_render_width()):
            return
        if any("\n" in line for line in (*hero_lines, *enemy_lines)):
            self.say("Party:")
            for line in hero_lines:
                self.say(line)
            self.say("Enemies:")
            for line in enemy_lines:
                self.say(line)
            return
        self.say("Party: " + " | ".join(hero_lines))
        self.say("Enemies: " + " | ".join(enemy_lines))

    def describe_combatant(self, creature, *, name_width: int | None = None) -> str:
        active_conditions = []
        for name, value in creature.conditions.items():
            if value == 0:
                continue
            if name == "pattern_charge":
                charge_count = self.total_arcanist_pattern_charges(creature)
                active_conditions.append(f"Pattern Charge {charge_count}" if charge_count else self.status_name(name))
            else:
                active_conditions.append(self.status_name(name))
        conditions = f" ({', '.join(active_conditions)})" if active_conditions else ""
        temp = f", temp {creature.temp_hp}" if creature.temp_hp else ""
        name = self.style_name(creature)
        plain_name = strip_ansi(name)
        if name_width is None:
            prefix = f"{name}: "
            indent_width = len(plain_name) + 2
        else:
            prefix = f"{name}:{' ' * (max(0, name_width - len(plain_name)) + 1)}"
            indent_width = name_width + 2
        if creature.dead:
            return f"{prefix}{self.format_health_bar(0, creature.max_hp)} (dead){conditions}"
        if creature.current_hp == 0 and not creature.dead:
            return f"{prefix}{self.format_health_bar(0, creature.max_hp)} (down){conditions}"
        line = (
            f"{prefix}{self.format_health_bar(creature.current_hp, creature.max_hp)}, "
            f"{self.combat_defense_summary(creature)}{temp}{conditions}"
        )
        resource_lines = [
            line
            for line in (
                self.format_member_magic_bar(creature),
                self.combat_resource_summary_line(creature),
            )
            if line is not None
        ]
        if not resource_lines:
            return line
        indent = " " * indent_width
        return f"{line}\n" + "\n".join(f"{indent}{resource_line}" for resource_line in resource_lines)

    def handle_defeat(self, reason: str) -> None:
        play_sound_effect = getattr(self, "play_sound_effect", None)
        if callable(play_sound_effect):
            play_sound_effect("game_over")
        self.banner("Defeat")
        self.say(reason)
        choice = self.choose(
            "What do you want to do?",
            [
                "Return to the title screen",
                "Open Save Files",
            ],
            allow_meta=False,
        )
        if choice == 2:
            loaded = self.open_save_files_menu()
            if loaded:
                return
        self.state = None
