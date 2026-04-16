from __future__ import annotations

from typing import Callable


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]

MENU_PAGE_SIZE = 9
LEVEL_XP_THRESHOLDS = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
}
