from __future__ import annotations

from dataclasses import dataclass

from ..dice import roll
from ..items import choose_supply_items_to_consume, equipment_slot_label, get_item, marks_label
from ..gameplay.magic_points import restore_magic_points, spell_slot_restore_units_to_mp


@dataclass(frozen=True)
class CommandActionResult:
    ok: bool
    message: str


def _member_by_index(game, index: int):
    if game is None:
        return None
    assert game.state is not None
    members = game.state.party_members()
    if not members:
        return None
    try:
        index = int(index)
    except (TypeError, ValueError):
        index = 0
    if not 0 <= index < len(members):
        return None
    return members[index]


def equip_item_for_member(game, member_index: int, slot: str, item_id: str) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no active party gear to manage yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no active party gear to manage yet.")
    if bool(getattr(game, "_in_combat", False)):
        return CommandActionResult(False, "You cannot reorganize equipment in the middle of combat.")
    member = _member_by_index(game, member_index)
    if member is None:
        return CommandActionResult(False, "Choose a valid party member.")
    item = get_item(item_id)
    if game.available_inventory_count(item.item_id) <= 0:
        return CommandActionResult(False, f"{item.name} is not free in the shared inventory.")
    if not game.item_can_fit_slot(member, item, slot):
        return CommandActionResult(False, f"{item.name} does not fit {equipment_slot_label(slot)}.")
    if slot == "off_hand":
        main_hand_id = member.equipment_slots.get("main_hand")
        if main_hand_id is not None:
            main_hand_item = get_item(main_hand_id)
            if main_hand_item.weapon is not None and main_hand_item.weapon.hands_required >= 2:
                return CommandActionResult(False, f"{member.name} cannot use an off-hand item while wielding a two-handed weapon.")
        if item.weapon is not None and item.weapon.hands_required >= 2:
            return CommandActionResult(False, f"{item.name} needs two hands and cannot be equipped off-hand.")
    if slot == "main_hand" and item.weapon is not None and item.weapon.hands_required >= 2:
        member.equipment_slots["off_hand"] = None
    member.equipment_slots[slot] = item.legacy_id or item.item_id
    game.sync_equipment(member)
    return CommandActionResult(True, f"{member.name} equips {item.name} in {equipment_slot_label(slot)}.")


def unequip_member_slot(game, member_index: int, slot: str) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no active party gear to manage yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no active party gear to manage yet.")
    if bool(getattr(game, "_in_combat", False)):
        return CommandActionResult(False, "You cannot reorganize equipment in the middle of combat.")
    member = _member_by_index(game, member_index)
    if member is None:
        return CommandActionResult(False, "Choose a valid party member.")
    current_item_id = member.equipment_slots.get(slot)
    if current_item_id is None:
        return CommandActionResult(False, f"{equipment_slot_label(slot)} is already empty.")
    current_item = get_item(current_item_id)
    member.equipment_slots[slot] = None
    game.sync_equipment(member)
    return CommandActionResult(True, f"{member.name} clears {equipment_slot_label(slot)}. {current_item.name} returns to the shared inventory.")


def drop_inventory_item(game, item_id: str, quantity: int = 1) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no shared inventory yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no shared inventory yet.")
    item = get_item(item_id)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1
    available = game.available_inventory_count(item.item_id)
    if available < quantity:
        return CommandActionResult(False, f"Only {available} unequipped {item.name} available.")
    if not game.remove_inventory_item(item.item_id, quantity):
        return CommandActionResult(False, f"{item.name} is no longer in the shared inventory.")
    suffix = f" x{quantity}" if quantity > 1 else ""
    return CommandActionResult(True, f"You drop {item.name}{suffix}.")


def usable_inventory_targets(game, item_id: str) -> list[tuple[int, object]]:
    if game is None:
        return []
    if game.state is None:
        return []
    item = get_item(item_id)
    if not item.is_combat_usable():
        return []
    return [
        (index, member)
        for index, member in enumerate(game.state.party_members())
        if not member.dead
    ]


def _apply_condition_direct(target, condition: str, duration: int) -> None:
    current = target.conditions.get(condition, 0)
    if condition == "exhaustion" and duration > 0:
        target.conditions[condition] = current + duration
    elif current < 0 or duration < 0:
        target.conditions[condition] = -1
    else:
        target.conditions[condition] = max(current, duration)


def use_inventory_item_on_target(game, item_id: str, target_index: int) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no shared inventory yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no shared inventory yet.")
    item = get_item(item_id)
    if not item.is_combat_usable():
        return CommandActionResult(False, f"{item.name} has no direct use from the inventory panel.")
    target = _member_by_index(game, target_index)
    if target is None or target.dead:
        return CommandActionResult(False, "Choose a living party member.")
    if game.inventory_dict().get(item.item_id, 0) <= 0:
        return CommandActionResult(False, f"{item.name} is no longer in the shared inventory.")
    if not game.remove_inventory_item(item.item_id):
        return CommandActionResult(False, f"{item.name} is no longer in the shared inventory.")

    effects: list[str] = []
    if item.heal_dice is not None:
        heal_amount = roll(item.heal_dice, game.rng).total + item.heal_bonus + target.gear_bonuses.get("healing_received", 0)
        healed = target.heal(heal_amount)
        effects.append(f"restores {healed} hit points")
    if item.revive_hp and target.current_hp == 0 and not target.dead:
        target.current_hp = max(target.current_hp, item.revive_hp)
        target.stable = False
        target.death_successes = 0
        target.death_failures = 0
        effects.append(f"brings {target.name} back to {target.current_hp} HP")
    if item.temp_hp:
        gained = target.grant_temp_hp(item.temp_hp)
        effects.append(f"sets temporary hit points to {gained}")
    if item.spell_slot_restore and target.spellcasting_ability is not None:
        restored_mp = restore_magic_points(target, spell_slot_restore_units_to_mp(item.spell_slot_restore))
        if restored_mp:
            effects.append(f"restores {restored_mp} MP")
    if item.cure_poison and "poisoned" in target.conditions:
        target.conditions.pop("poisoned", None)
        effects.append("cures poison")
    if item.clear_conditions:
        cleared: list[str] = []
        for condition in item.clear_conditions:
            if condition == "exhaustion":
                current = max(0, int(target.conditions.get("exhaustion", 0)))
                if current > 0:
                    target.conditions["exhaustion"] = current - 1
                    if target.conditions["exhaustion"] <= 0:
                        target.conditions.pop("exhaustion", None)
                    cleared.append("Exhaustion")
                continue
            if condition in target.conditions or (condition == "unconscious" and target.current_hp == 0):
                target.conditions.pop(condition, None)
                cleared.append(game.status_name(condition))
        if cleared:
            effects.append("clears " + ", ".join(cleared))
    if item.apply_conditions:
        applied: list[str] = []
        for condition, duration in item.apply_conditions.items():
            _apply_condition_direct(target, str(condition), int(duration))
            applied.append(game.status_name(str(condition)))
        if applied:
            effects.append("applies " + ", ".join(applied))
    if not effects:
        effects.append("has no immediate effect")
    return CommandActionResult(True, f"{target.name} uses {item.name}; it " + ", ".join(effects) + ".")


def take_short_rest(game) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no active adventure yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no active adventure yet.")
    if game.state.short_rests_remaining <= 0:
        return CommandActionResult(False, "No short rests remain before a long rest.")
    game.state.short_rests_remaining -= 1
    for member in game.state.party_members():
        if member.dead:
            continue
        if member.current_hp == 0:
            member.current_hp = 1
            member.stable = False
            member.death_successes = 0
            member.death_failures = 0
        heal_amount = max(1, (member.max_hp + 1) // 2)
        member.heal(heal_amount)
        game.restore_short_rest_resources(member)
    return CommandActionResult(True, f"The party takes a short rest. Short rests remaining: {game.state.short_rests_remaining}.")


def take_long_rest(game) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no active adventure yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no active adventure yet.")
    required_points = game.long_rest_supply_cost()
    consumed, missing = choose_supply_items_to_consume(game.inventory_dict(), required_points)
    if missing > 0:
        available = required_points - missing
        return CommandActionResult(False, f"Need {required_points} supply points to long rest; only {available} available.")
    for item_id, quantity in consumed.items():
        game.remove_inventory_item(item_id, quantity)
    game.complete_long_rest_recovery()
    consumed_text = ", ".join(f"{get_item(item_id).name} x{quantity}" for item_id, quantity in consumed.items())
    return CommandActionResult(True, f"The party completes a long rest after using {consumed_text}.")


def revive_dead_ally(game, companion_index: int) -> CommandActionResult:
    if game is None:
        return CommandActionResult(False, "There is no active adventure yet.")
    if game.state is None:
        return CommandActionResult(False, "There is no active adventure yet.")
    dead_allies = game.dead_allies_in_company()
    if not dead_allies:
        return CommandActionResult(False, "No fallen ally in camp can be reached by revivify right now.")
    try:
        companion_index = int(companion_index)
    except (TypeError, ValueError):
        companion_index = 0
    if not 0 <= companion_index < len(dead_allies):
        return CommandActionResult(False, "Choose a valid fallen ally.")
    item = get_item("scroll_revivify")
    if game.inventory_dict().get(item.item_id, 0) <= 0:
        return CommandActionResult(False, f"You need {item.name} in the shared inventory before you can attempt the rite.")
    target = dead_allies[companion_index]
    if not game.remove_inventory_item(item.item_id):
        return CommandActionResult(False, f"{item.name} is no longer in the shared inventory.")
    target.dead = False
    target.current_hp = min(target.max_hp, max(1, item.revive_hp))
    target.stable = False
    target.death_successes = 0
    target.death_failures = 0
    target.temp_hp = 0
    target.conditions.clear()
    game.add_journal(f"{target.name} was restored to life at camp with {item.name}.")
    return CommandActionResult(True, f"{target.name} returns to life at {target.current_hp} HP.")


def magic_mirror_unavailable_reason(game) -> str:
    if game is None:
        return "There is no active adventure yet."
    if game.state is None:
        return "There is no active adventure yet."
    if game.state.gold < 100:
        return f"Need 100 gold; the party has {marks_label(game.state.gold)}."
    return "Respec still uses the character-creation prompt flow."
