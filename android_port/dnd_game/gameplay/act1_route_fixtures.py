from __future__ import annotations

from dataclasses import dataclass
import random

from ..content import (
    build_character,
    create_bryn_underbough,
    create_elira_dawnmantle,
    create_enemy,
    create_kaelis_starling,
    create_rhogar_valeguard,
    create_tolan_ironshield,
)
from ..game import TextDnDGame
from ..models import GameState
from .combat_simulator import RouteChainEncounterSpec


PLAYER_ID = "player"
CANONICAL_ACT1_ROUTE_KEY = "canonical_full_clear"
ACT1_BASELINE_INVENTORY = {"potion_healing": 2, "bread_round": 4, "camp_stew_jar": 3}


@dataclass(frozen=True, slots=True)
class EnemyFixture:
    template: str
    name: str | None = None
    max_hp: int | None = None
    current_hp: int | None = None
    hp_delta: int = 0

    def build(self):
        enemy = create_enemy(self.template, name=self.name)
        if self.hp_delta:
            enemy.max_hp += self.hp_delta
            enemy.current_hp += self.hp_delta
        if self.max_hp is not None:
            enemy.max_hp = max(1, self.max_hp)
            enemy.current_hp = enemy.max_hp
        if self.current_hp is not None:
            enemy.current_hp = max(1, min(enemy.max_hp, self.current_hp))
        return enemy


@dataclass(frozen=True, slots=True)
class Act1RouteEncounterFixture:
    key: str
    title: str
    enemies: tuple[EnemyFixture, ...]
    source_scene: str
    wave_group: str | None = None
    party_armor_break_percent: int = 0

    def build_route_spec(self) -> RouteChainEncounterSpec:
        return RouteChainEncounterSpec(
            self.title,
            tuple(enemy.build() for enemy in self.enemies),
            wave_group=self.wave_group,
            party_armor_break_percent=self.party_armor_break_percent,
        )


@dataclass(frozen=True, slots=True)
class Act1RouteSegmentFixture:
    key: str
    title: str
    party_member_ids: tuple[str, ...]
    party_level: int
    encounters: tuple[Act1RouteEncounterFixture, ...]
    joins_before: tuple[str, ...] = ()
    joins_after: tuple[str, ...] = ()

    @property
    def expected_party_size(self) -> int:
        return len(self.party_member_ids)

    def build_route_specs(self) -> tuple[RouteChainEncounterSpec, ...]:
        return tuple(encounter.build_route_spec() for encounter in self.encounters)


@dataclass(frozen=True, slots=True)
class Act1RouteFixture:
    key: str
    title: str
    segments: tuple[Act1RouteSegmentFixture, ...]
    starting_inventory: dict[str, int]
    starting_gold: int = 0

    @property
    def encounter_count(self) -> int:
        return sum(len(segment.encounters) for segment in self.segments)

    @property
    def segment_keys(self) -> tuple[str, ...]:
        return tuple(segment.key for segment in self.segments)


def enemy(template: str, name: str | None = None, *, max_hp: int | None = None, current_hp: int | None = None, hp_delta: int = 0) -> EnemyFixture:
    return EnemyFixture(template, name=name, max_hp=max_hp, current_hp=current_hp, hp_delta=hp_delta)


def encounter(
    key: str,
    title: str,
    source_scene: str,
    *enemies: EnemyFixture,
    wave_group: str | None = None,
    party_armor_break_percent: int = 0,
) -> Act1RouteEncounterFixture:
    return Act1RouteEncounterFixture(
        key=key,
        title=title,
        source_scene=source_scene,
        enemies=tuple(enemies),
        wave_group=wave_group,
        party_armor_break_percent=party_armor_break_percent,
    )


CANONICAL_ACT1_ROUTE = Act1RouteFixture(
    key=CANONICAL_ACT1_ROUTE_KEY,
    title="Canonical Act 1 Full Clear",
    starting_inventory=dict(ACT1_BASELINE_INVENTORY),
    starting_gold=0,
    segments=(
        Act1RouteSegmentFixture(
            key="opening_soldier_solo",
            title="Opening Background Fight",
            party_member_ids=(PLAYER_ID,),
            party_level=1,
            encounters=(
                encounter(
                    "south_barracks_breakout",
                    "South Barracks Breakout",
                    "prologue_soldier",
                    enemy("bandit", "Ashen Brand Runner", max_hp=11),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="greywake_elira_breakout",
            title="Greywake Breakout With Elira",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle"),
            party_level=1,
            joins_before=("elira_dawnmantle",),
            encounters=(
                encounter(
                    "greywake_road_breakout",
                    "Greywake Road Breakout",
                    "greywake_road_breakout",
                    enemy("bandit", max_hp=11),
                    enemy("bandit_archer"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="greywake_departure_company",
            title="Greywake Departure Checks",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling"),
            party_level=2,
            joins_before=("kaelis_starling",),
            encounters=(
                encounter(
                    "emberway_milehouse_intercept",
                    "Emberway Milehouse Intercept",
                    "greywake_emberway_milehouse",
                    enemy("brand_saboteur"),
                    enemy("bandit"),
                ),
                encounter(
                    "greywake_wood_signal_cairn",
                    "Greywake Wood Signal Cairn",
                    "greywake_signal_cairn",
                    enemy("goblin_skirmisher"),
                    enemy("bandit_archer"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="blackwake_crossing",
            title="Blackwake Crossing",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling"),
            party_level=2,
            encounters=(
                encounter(
                    "blackwake_charred_tollhouse",
                    "Charred Tollhouse Breakout",
                    "blackwake_charred_tollhouse",
                    enemy("brand_saboteur"),
                    enemy("bandit"),
                ),
                encounter(
                    "blackwake_millers_ford",
                    "Miller's Ford Ledger Post",
                    "blackwake_ford_ledger_post",
                    enemy("brand_saboteur"),
                    enemy("bandit"),
                    enemy("bandit_archer"),
                ),
                encounter(
                    "blackwake_outer_cache",
                    "Blackwake Outer Cache",
                    "blackwake_outer_cache",
                    enemy("brand_saboteur"),
                    enemy("bandit_archer"),
                    enemy("bandit"),
                ),
                encounter(
                    "blackwake_sereth_vane",
                    "Boss: Sereth Vane",
                    "blackwake_floodgate_chamber",
                    enemy("sereth_vane"),
                    enemy("brand_saboteur"),
                    enemy("bandit_archer"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="emberway_first_wave",
            title="Emberway First Wave",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling"),
            party_level=2,
            encounters=(
                encounter(
                    "roadside_ambush_first_wave",
                    "Roadside Ambush: First Wave",
                    "road_ambush",
                    enemy("goblin_skirmisher"),
                    enemy("cinder_kobold"),
                    enemy("wolf"),
                    wave_group="emberway_ambush",
                ),
            ),
            joins_after=("tolan_ironshield",),
        ),
        Act1RouteSegmentFixture(
            key="emberway_second_wave",
            title="Emberway Second Wave With Tolan",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield"),
            party_level=2,
            joins_before=("tolan_ironshield",),
            encounters=(
                encounter(
                    "emberway_second_wave",
                    "Emberway Second Wave",
                    "road_ambush",
                    enemy("ash_brand_enforcer"),
                    enemy("bandit_archer"),
                    enemy("goblin_skirmisher"),
                    wave_group="emberway_ambush",
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="iron_hollow_side_content",
            title="Iron Hollow Side Content",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=3,
            joins_before=("bryn_underbough",),
            encounters=(
                encounter(
                    "orchard_wall_watchers",
                    "Orchard Wall Watchers",
                    "edermath_old_cache",
                    enemy("brand_saboteur"),
                    enemy("bandit_archer"),
                    enemy("bandit"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="blackglass_well",
            title="Blackglass Well",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=3,
            encounters=(
                encounter(
                    "blackglass_dig_ring",
                    "Blackglass Well Dig Ring",
                    "blackglass_well",
                    enemy("skeletal_sentry"),
                    enemy("bandit", "Ashen Brand Fixer"),
                    enemy("ashstone_percher"),
                ),
                encounter(
                    "blackglass_vaelith_marr",
                    "Miniboss: Vaelith Marr",
                    "blackglass_well",
                    enemy("vaelith_marr"),
                    enemy("carrion_lash_crawler"),
                    enemy("graveblade_wight"),
                    enemy("skeletal_sentry", "Corpse-Salt Sentry"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="red_mesa_hold",
            title="Red Mesa Hold",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=3,
            encounters=(
                encounter(
                    "red_mesa_shelf",
                    "Red Mesa Hold Shelf Fight",
                    "red_mesa_hold",
                    enemy("orc_raider"),
                    enemy("worg"),
                    enemy("bugbear_reaver"),
                ),
                encounter(
                    "red_mesa_brughor",
                    "Miniboss: Brughor Skullcleaver",
                    "red_mesa_hold",
                    enemy("orc_bloodchief", "Brughor Skullcleaver"),
                    enemy("ogre_brute"),
                    enemy("orc_raider"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="cinderfall_ruins",
            title="Cinderfall Ruins",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=4,
            encounters=(
                encounter(
                    "cinderfall_gate",
                    "Cinderfall Gate",
                    "cinderfall_ruins",
                    enemy("bandit", "Relay Cutout"),
                    enemy("carrion_stalker"),
                    enemy("ashstone_percher"),
                ),
                encounter(
                    "cinderfall_ember_relay",
                    "Cinderfall Ember Relay",
                    "cinderfall_ruins",
                    enemy("ember_channeler", "Ember Relay Keeper"),
                    enemy("ash_brand_enforcer", "Ashen Brand Runner"),
                    enemy("carrion_stalker"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="ashfall_watch",
            title="Ashfall Watch",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=4,
            encounters=(
                encounter(
                    "ashfall_gate",
                    "Ashfall Gate",
                    "ashfall_watch",
                    enemy("bandit"),
                    enemy("bandit_archer"),
                ),
                encounter(
                    "ashfall_lower_barracks",
                    "Ashfall Lower Barracks",
                    "ashfall_watch",
                    enemy("ash_brand_enforcer"),
                    enemy("bandit_archer", "Ashen Brand Barracks Archer"),
                ),
                encounter(
                    "ashfall_rukhar",
                    "Miniboss: Rukhar Cinderfang",
                    "ashfall_watch",
                    enemy("rukhar"),
                    enemy("ash_brand_enforcer"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="duskmere_manor",
            title="Duskmere Manor",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=4,
            encounters=(
                encounter(
                    "duskmere_cellars",
                    "Duskmere Cellars",
                    "duskmere_manor",
                    enemy("bandit", "Ashen Brand Collector"),
                    enemy("bandit_archer", "Archive Cutout"),
                ),
                encounter(
                    "duskmere_cistern_eye",
                    "The Cistern Eye",
                    "duskmere_manor",
                    enemy("nothic", "Cistern Eye"),
                    enemy("stonegaze_skulker"),
                ),
            ),
        ),
        Act1RouteSegmentFixture(
            key="emberhall_cellars",
            title="Emberhall Cellars",
            party_member_ids=(PLAYER_ID, "elira_dawnmantle", "kaelis_starling", "tolan_ironshield", "bryn_underbough"),
            party_level=5,
            encounters=(
                encounter(
                    "emberhall_antechamber",
                    "Emberhall Antechamber",
                    "emberhall_cellars",
                    enemy("bandit", "Ashen Brand Fixer"),
                    enemy("bandit_archer", "Cellar Sniper"),
                    enemy("cinderflame_skull"),
                    enemy("gutter_zealot"),
                ),
                encounter(
                    "emberhall_black_reserve",
                    "Emberhall Black Reserve",
                    "emberhall_cellars",
                    enemy("bandit", "Ashen Brand Enforcer"),
                    enemy("bandit_archer", "Reserve Sniper"),
                    enemy("whispermaw_blob"),
                    enemy("cinderflame_skull"),
                ),
                encounter(
                    "emberhall_varyn",
                    "Boss: Varyn Sable",
                    "emberhall_cellars",
                    enemy("varyn", hp_delta=8),
                    enemy("ash_brand_enforcer"),
                    enemy("ember_channeler"),
                    enemy("cinderflame_skull"),
                    enemy("gutter_zealot"),
                ),
            ),
        ),
    ),
)

ACT1_ROUTE_FIXTURES = {CANONICAL_ACT1_ROUTE.key: CANONICAL_ACT1_ROUTE}


def act1_route_fixture(key: str = CANONICAL_ACT1_ROUTE_KEY) -> Act1RouteFixture:
    return ACT1_ROUTE_FIXTURES[key]


def act1_route_fixtures() -> tuple[Act1RouteFixture, ...]:
    return tuple(ACT1_ROUTE_FIXTURES.values())


def build_act1_route_player():
    return build_character(
        name="Vale",
        race="Human",
        class_name="Warrior",
        background="Soldier",
        base_ability_scores={"STR": 15, "DEX": 12, "CON": 14, "INT": 8, "WIS": 12, "CHA": 10},
        class_skill_choices=["Athletics", "Survival"],
    )


def build_act1_route_party(member_ids: tuple[str, ...], *, level: int, game: TextDnDGame | None = None) -> list:
    builders = {
        PLAYER_ID: build_act1_route_player,
        "elira_dawnmantle": create_elira_dawnmantle,
        "kaelis_starling": create_kaelis_starling,
        "rhogar_valeguard": create_rhogar_valeguard,
        "tolan_ironshield": create_tolan_ironshield,
        "bryn_underbough": create_bryn_underbough,
    }
    party = [builders[member_id]() for member_id in member_ids]
    if game is None:
        game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(0))
    for member in party:
        for next_level in range(2, max(1, level) + 1):
            game.level_up_character_automatically(member, next_level, announce=False)
        game.prepare_class_resources_for_combat(member)
    return party


def build_act1_route_game(segment: Act1RouteSegmentFixture, route: Act1RouteFixture | None = None, *, seed: int = 49217) -> tuple[TextDnDGame, list]:
    route = route or CANONICAL_ACT1_ROUTE
    game = TextDnDGame(input_fn=lambda _: "1", output_fn=lambda _: None, rng=random.Random(seed))
    party = build_act1_route_party(segment.party_member_ids, level=segment.party_level, game=game)
    game.state = GameState(
        player=party[0],
        companions=party[1:],
        current_scene=segment.key,
        current_act=1,
        gold=route.starting_gold,
        inventory=dict(route.starting_inventory),
        short_rests_remaining=2,
    )
    game._in_combat = True
    game._active_round_number = 1
    game._active_combat_heroes = party
    return game, party


__all__ = [
    "ACT1_BASELINE_INVENTORY",
    "ACT1_ROUTE_FIXTURES",
    "CANONICAL_ACT1_ROUTE",
    "CANONICAL_ACT1_ROUTE_KEY",
    "PLAYER_ID",
    "Act1RouteEncounterFixture",
    "Act1RouteFixture",
    "Act1RouteSegmentFixture",
    "EnemyFixture",
    "act1_route_fixture",
    "act1_route_fixtures",
    "build_act1_route_game",
    "build_act1_route_party",
    "build_act1_route_player",
]
