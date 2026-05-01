from __future__ import annotations

from dataclasses import dataclass, field

from ..items import (
    equipment_slot_label,
    get_item,
    item_category_label,
    item_rules_text,
    item_type_label,
    marks_label,
)
from ..ui.colors import strip_ansi


def _plain(value: object) -> str:
    return strip_ansi(str(value or "")).strip()


def _plain_health_summary(member) -> str:
    current_hp = max(0, int(getattr(member, "current_hp", 0)))
    max_hp = max(0, int(getattr(member, "max_hp", 0)))
    temp_hp = max(0, int(getattr(member, "temp_hp", 0)))
    suffix = ""
    if getattr(member, "dead", False):
        suffix = " (dead)"
    elif current_hp == 0:
        suffix = " (down)"
    temp = f", temp {temp_hp}" if temp_hp else ""
    return f"HP {current_hp}/{max_hp}{temp}{suffix}"


@dataclass(frozen=True)
class InventoryFilterSnapshot:
    key: str
    label: str
    count: int


@dataclass(frozen=True)
class InventoryItemSnapshot:
    item_id: str
    name: str
    rarity: str
    rarity_title: str
    category: str
    category_label: str
    item_type: str
    item_type_label: str
    kind_label: str
    quantity: int
    available: int
    equipped: int
    value: int
    value_label: str
    supply_points: int
    supply_label: str
    rules: str
    description: str
    source: str
    equippable: bool
    usable: bool
    slot: str
    slot_label: str


@dataclass(frozen=True)
class InventorySnapshot:
    filter_key: str
    filter_label: str
    filters: tuple[InventoryFilterSnapshot, ...]
    items: tuple[InventoryItemSnapshot, ...]
    selected_item_id: str | None
    selected_item: InventoryItemSnapshot | None
    gold: int
    gold_label: str
    supply_points: int
    total_quantity: int
    total_available: int
    empty_message: str


@dataclass(frozen=True)
class GearCandidateSnapshot:
    item_id: str
    name: str
    rarity: str
    rarity_title: str
    available: int
    rules: str
    comparison: str


@dataclass(frozen=True)
class GearSlotSnapshot:
    slot: str
    label: str
    current_item_id: str | None
    current_name: str
    current_rarity: str
    current_rules: str
    unequip_comparison: str
    candidates: tuple[GearCandidateSnapshot, ...]


@dataclass(frozen=True)
class GearMemberSnapshot:
    index: int
    name: str
    public_identity: str
    health: str
    combat: str
    conditions: str
    resources: str
    slots: tuple[GearSlotSnapshot, ...]


@dataclass(frozen=True)
class GearSnapshot:
    members: tuple[GearMemberSnapshot, ...]
    selected_member_index: int
    selected_slot: str | None
    combat_locked: bool
    message: str


@dataclass(frozen=True)
class JournalQuestSnapshot:
    quest_id: str
    title: str
    giver: str
    summary: str
    objective: str
    turn_in: str
    rewards: str
    latest_note: str


@dataclass(frozen=True)
class JournalSnapshot:
    location: str
    objective: str
    quest_load: str
    lead_count: str
    extra_snapshot_lines: tuple[str, ...]
    ready_quests: tuple[JournalQuestSnapshot, ...]
    active_quests: tuple[JournalQuestSnapshot, ...]
    completed_quests: tuple[JournalQuestSnapshot, ...]
    major_choices: tuple[str, ...]
    consequences: tuple[str, ...]
    faction_pressure: tuple[str, ...]
    companion_disposition: tuple[str, ...]
    unresolved_clues: tuple[str, ...]
    recent_updates: tuple[str, ...]
    older_note_count: int
    empty_message: str


@dataclass(frozen=True)
class CampActionSnapshot:
    key: str
    label: str
    enabled: bool = True
    reason: str = ""


@dataclass(frozen=True)
class CampSnapshot:
    gold_label: str
    short_rests_remaining: int
    supply_points: int
    active_party_count: int
    camp_roster_count: int
    digest_lines: tuple[str, ...]
    active_party: tuple[str, ...]
    camp_roster: tuple[str, ...]
    actions: tuple[CampActionSnapshot, ...]


def build_inventory_item_snapshot(game, item_id: str, quantity: int) -> InventoryItemSnapshot:
    item = get_item(item_id)
    available = int(game.available_inventory_count(item_id))
    equipped = int(game.count_equipped(item_id))
    slot = item.slot or ""
    return InventoryItemSnapshot(
        item_id=item.item_id,
        name=item.name,
        rarity=item.rarity,
        rarity_title=item.rarity_title,
        category=item.category,
        category_label=item_category_label(item.category).title(),
        item_type=item.item_type,
        item_type_label=item_type_label(item.item_type).title(),
        kind_label=game.inventory_item_kind_label(item),
        quantity=int(quantity),
        available=available,
        equipped=equipped,
        value=int(item.value),
        value_label=marks_label(item.value),
        supply_points=int(item.supply_points),
        supply_label=item.supply_label(),
        rules=_plain(game.inventory_item_rules_summary(item)),
        description=_plain(item.description),
        source=_plain(item.source),
        equippable=bool(item.is_equippable()),
        usable=bool(item.is_combat_usable()),
        slot=slot,
        slot_label=equipment_slot_label(slot) if slot else "",
    )


def build_inventory_snapshot(
    game,
    *,
    filter_key: str = "all",
    selected_item_id: str | None = None,
) -> InventorySnapshot:
    if game.state is None:
        raise ValueError("Inventory snapshots require an active game state.")
    inventory = game.inventory_dict()
    filter_keys = {key for key, _label in game.inventory_filter_options()}
    if filter_key not in filter_keys:
        filter_key = "all"
    filters = tuple(
        InventoryFilterSnapshot(
            key=key,
            label=label,
            count=len(game.inventory_item_ids_for_filter(key)),
        )
        for key, label in game.inventory_filter_options()
    )
    item_ids = game.inventory_item_ids_for_filter(filter_key)
    items = tuple(build_inventory_item_snapshot(game, item_id, inventory[item_id]) for item_id in item_ids)
    selected_item = None
    if selected_item_id is not None:
        selected_item = next((item for item in items if item.item_id == selected_item_id), None)
    if selected_item is None and items:
        selected_item = items[0]
    return InventorySnapshot(
        filter_key=filter_key,
        filter_label=game.inventory_filter_label(filter_key),
        filters=filters,
        items=items,
        selected_item_id=selected_item.item_id if selected_item is not None else None,
        selected_item=selected_item,
        gold=int(game.state.gold),
        gold_label=marks_label(game.state.gold),
        supply_points=int(game.current_supply_points()),
        total_quantity=sum(max(0, int(quantity)) for quantity in inventory.values()),
        total_available=sum(game.available_inventory_count(item_id) for item_id in inventory),
        empty_message=(
            "The shared inventory is empty."
            if not inventory
            else f"No items match the {game.inventory_filter_label(filter_key).lower()} filter right now."
        ),
    )


def _gear_candidate_snapshot(game, member, slot: str, item_id: str, base_state) -> GearCandidateSnapshot:
    item = get_item(item_id)
    preview = game.preview_member_after_slot_change(member, slot, item_id)
    return GearCandidateSnapshot(
        item_id=item.item_id,
        name=item.name,
        rarity=item.rarity,
        rarity_title=item.rarity_title,
        available=int(game.available_inventory_count(item_id)),
        rules=_plain(game.inventory_item_rules_summary(item)),
        comparison=_plain(game.equipment_comparison_summary(base_state, preview)),
    )


def build_gear_snapshot(
    game,
    *,
    selected_member_index: int = 0,
    selected_slot: str | None = None,
) -> GearSnapshot:
    if game.state is None:
        raise ValueError("Gear snapshots require an active game state.")
    members = game.state.party_members()
    selected_member_index = max(0, min(int(selected_member_index or 0), max(0, len(members) - 1)))
    member_snapshots: list[GearMemberSnapshot] = []
    for member_index, member in enumerate(members):
        game.sync_equipment(member)
        slot_snapshots: list[GearSlotSnapshot] = []
        for slot in member.equipment_slots:
            current_item_id = member.equipment_slots.get(slot)
            current_name = "Empty"
            current_rarity = ""
            current_rules = ""
            if current_item_id is not None:
                current_item = get_item(current_item_id)
                current_name = current_item.name
                current_rarity = current_item.rarity
                current_rules = _plain(game.inventory_item_rules_summary(current_item))
            base_state = game.preview_member_after_slot_change(member, slot, current_item_id)
            unequip_comparison = ""
            if current_item_id is not None:
                unequipped_state = game.preview_member_after_slot_change(member, slot, None)
                unequip_comparison = _plain(game.equipment_comparison_summary(base_state, unequipped_state))
            candidates = tuple(
                _gear_candidate_snapshot(game, member, slot, item_id, base_state)
                for item_id in game.compatible_inventory_items_for_slot(member, slot)
            )
            slot_snapshots.append(
                GearSlotSnapshot(
                    slot=slot,
                    label=equipment_slot_label(slot),
                    current_item_id=current_item_id,
                    current_name=current_name,
                    current_rarity=current_rarity,
                    current_rules=current_rules,
                    unequip_comparison=unequip_comparison,
                    candidates=candidates,
                )
            )
        member_snapshots.append(
            GearMemberSnapshot(
                index=member_index,
                name=_plain(member.name),
                public_identity=_plain(member.public_identity),
                health=_plain_health_summary(member),
                combat=_plain(game.combat_defense_summary(member)),
                conditions=_plain(game.character_condition_summary(member)),
                resources=_plain(game.member_resource_summary(member)),
                slots=tuple(slot_snapshots),
            )
        )
    if selected_slot is None and member_snapshots:
        selected_slot = member_snapshots[selected_member_index].slots[0].slot if member_snapshots[selected_member_index].slots else None
    return GearSnapshot(
        members=tuple(member_snapshots),
        selected_member_index=selected_member_index,
        selected_slot=selected_slot,
        combat_locked=bool(getattr(game, "_in_combat", False)),
        message="You cannot reorganize equipment in the middle of combat."
        if bool(getattr(game, "_in_combat", False))
        else "",
    )


def _quest_snapshot(game, definition, entry) -> JournalQuestSnapshot:
    latest_note = ""
    if getattr(entry, "notes", None):
        latest_note = str(entry.notes[-1])
    return JournalQuestSnapshot(
        quest_id=str(getattr(definition, "quest_id", "")),
        title=str(getattr(definition, "title", "")),
        giver=str(getattr(definition, "giver", "")),
        summary=str(getattr(definition, "summary", "")),
        objective=str(getattr(definition, "objective", "")),
        turn_in=str(getattr(definition, "turn_in", "")),
        rewards=str(game.quest_reward_summary(definition.quest_id)),
        latest_note=latest_note,
    )


def build_journal_snapshot(game) -> JournalSnapshot:
    if game.state is None:
        raise ValueError("Journal snapshots require an active game state.")
    refresh_quest_statuses = getattr(game, "refresh_quest_statuses", None)
    if callable(refresh_quest_statuses):
        refresh_quest_statuses(announce=False)
    ready_quests = getattr(game, "quest_entries_by_status", lambda status: [])("ready_to_turn_in")
    active_quests = getattr(game, "quest_entries_by_status", lambda status: [])("active")
    completed_quests = getattr(game, "quest_entries_by_status", lambda status: [])("completed")
    story_notes = game.story_journal_entries()
    recent_notes = tuple(reversed(story_notes[-8:]))
    extra_snapshot_lines_getter = getattr(game, "journal_snapshot_lines", None)
    extra_snapshot_lines = tuple(extra_snapshot_lines_getter() if callable(extra_snapshot_lines_getter) else [])
    empty = not (
        ready_quests
        or active_quests
        or completed_quests
        or game.state.clues
        or story_notes
        or extra_snapshot_lines
    )
    return JournalSnapshot(
        location=str(game.hud_location_label()),
        objective=str(game.hud_objective_label()),
        quest_load=f"{len(active_quests)} active | {len(ready_quests)} ready | {len(completed_quests)} completed",
        lead_count=f"{len(game.state.clues)} clues | {len(story_notes)} journal notes",
        extra_snapshot_lines=tuple(str(line) for line in extra_snapshot_lines),
        ready_quests=tuple(_quest_snapshot(game, definition, entry) for definition, entry in ready_quests),
        active_quests=tuple(_quest_snapshot(game, definition, entry) for definition, entry in active_quests),
        completed_quests=tuple(_quest_snapshot(game, definition, entry) for definition, entry in completed_quests),
        major_choices=tuple(game.decision_ledger_major_choice_lines(story_notes)),
        consequences=tuple(game.decision_ledger_consequence_lines(
            ready_quests=ready_quests,
            active_quests=active_quests,
            completed_quests=completed_quests,
        )),
        faction_pressure=tuple(game.faction_pressure_lines()),
        companion_disposition=tuple(game.companion_disposition_ledger_lines()),
        unresolved_clues=tuple(game.unresolved_clue_lines()),
        recent_updates=recent_notes,
        older_note_count=max(0, len(story_notes) - len(recent_notes)),
        empty_message="Your journal is empty." if empty else "",
    )


def build_camp_snapshot(game) -> CampSnapshot:
    if game.state is None:
        raise ValueError("Camp snapshots require an active game state.")
    digest_lines = tuple(str(line) for line in game.camp_digest_lines())
    active_party = tuple(
        _plain(
            f"{member.name}: {_plain_health_summary(member)} | "
            f"{game.combat_defense_summary(member)} | {game.character_condition_summary(member)}"
        )
        for member in game.state.party_members()
    )
    camp_roster = tuple(_plain(game.companion_status_line(companion)) for companion in game.state.camp_companions)
    has_banter = bool(game.available_camp_banters())
    actions = [
        CampActionSnapshot("recovery", "Rest and recovery"),
        CampActionSnapshot("talk", "Talk to a companion"),
        CampActionSnapshot(
            "mirror",
            "Respec",
            enabled=game.state.gold >= 100,
            reason="" if game.state.gold >= 100 else "Need 100 gold.",
        ),
    ]
    if has_banter:
        actions.append(CampActionSnapshot("banter", "Listen around the campfire"))
    return CampSnapshot(
        gold_label=marks_label(game.state.gold),
        short_rests_remaining=int(game.state.short_rests_remaining),
        supply_points=int(game.current_supply_points()),
        active_party_count=len(game.state.party_members()),
        camp_roster_count=len(game.state.camp_companions),
        digest_lines=digest_lines,
        active_party=active_party,
        camp_roster=camp_roster,
        actions=tuple(actions),
    )
