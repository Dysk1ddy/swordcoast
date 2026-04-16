"""Core character-option data split by category for easier maintenance."""

from .backgrounds import BACKGROUNDS
from .classes import CLASSES, CLASS_LEVEL_PROGRESSION, format_class_selection
from .races import RACES, format_race_selection, format_racial_bonuses
from .shared import ACTS, POINT_BUY_COSTS, STANDARD_ARRAY, point_buy_total

__all__ = [
    "ACTS",
    "BACKGROUNDS",
    "CLASS_LEVEL_PROGRESSION",
    "CLASSES",
    "POINT_BUY_COSTS",
    "RACES",
    "STANDARD_ARRAY",
    "format_class_selection",
    "format_race_selection",
    "format_racial_bonuses",
    "point_buy_total",
]
