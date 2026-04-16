from __future__ import annotations

from .gameplay.base import GameBase, GameInterrupted
from .gameplay.camp import CampMixin
from .gameplay.combat_flow import CombatFlowMixin
from .gameplay.combat_resolution import CombatResolutionMixin
from .gameplay.companions import CompanionSystemMixin
from .gameplay.creation import CharacterCreationMixin
from .gameplay.creation_point_buy import PointBuyCreationMixin
from .gameplay.encounter import Encounter
from .gameplay.interaction_actions import InteractionActionsMixin
from .gameplay.inventory_core import InventoryCoreMixin
from .gameplay.inventory_management import InventoryManagementMixin
from .gameplay.io import GameIOMixin
from .gameplay.journal import JournalMixin
from .gameplay.progression import ProgressionMixin
from .gameplay.quests import QuestMixin
from .gameplay.random_encounters import RandomEncounterMixin
from .gameplay.status_effects import StatusEffectMixin
from .gameplay.story_endgame import StoryEndgameMixin
from .gameplay.story_intro import StoryIntroMixin
from .gameplay.story_town_hub import StoryTownHubMixin
from .gameplay.story_town_services import StoryTownServicesMixin


class TextDnDGame(
    CampMixin,
    CompanionSystemMixin,
    InteractionActionsMixin,
    StoryEndgameMixin,
    StoryTownServicesMixin,
    StoryTownHubMixin,
    StoryIntroMixin,
    StatusEffectMixin,
    CombatResolutionMixin,
    RandomEncounterMixin,
    CombatFlowMixin,
    InventoryManagementMixin,
    InventoryCoreMixin,
    ProgressionMixin,
    PointBuyCreationMixin,
    CharacterCreationMixin,
    QuestMixin,
    JournalMixin,
    GameIOMixin,
    GameBase,
):
    """Primary game class composed from focused gameplay modules."""


__all__ = ["Encounter", "GameInterrupted", "TextDnDGame"]
