from __future__ import annotations

from ..content import POINT_BUY_COSTS
from ..data.story.public_terms import ability_label
from ..models import ABILITY_ORDER


POINT_BUY_BUDGET = 27
BACK_OPTION = "Back"


class PointBuyCreationMixin:
    def choose_point_buy_scores(self, *, allow_back: bool = False) -> dict[str, int] | None:
        while True:
            self.banner("Point Buy")
            scores: dict[str, int] = {}
            spent = 0
            index = 0
            while index < len(ABILITY_ORDER):
                ability = ABILITY_ORDER[index]
                score = self.prompt_point_buy_score(ability, points_left=POINT_BUY_BUDGET - spent, allow_back=allow_back)
                if score is None:
                    if index == 0:
                        return None
                    previous_ability = ABILITY_ORDER[index - 1]
                    spent -= POINT_BUY_COSTS[scores.pop(previous_ability)]
                    index -= 1
                    continue
                scores[ability] = score
                spent += POINT_BUY_COSTS[score]
                self.say(f"{ability_label(ability, include_code=True)} set to {score}. Points left: {POINT_BUY_BUDGET - spent}.")
                index += 1

            summary = ", ".join(f"{ability_label(ability, include_code=True)} {scores[ability]}" for ability in ABILITY_ORDER)
            self.say(f"Point-buy draft: {summary}.")
            self.say(f"Total spent: {spent} of {POINT_BUY_BUDGET}. Points left: {POINT_BUY_BUDGET - spent}.")
            if self.confirm("Keep these point-buy scores?"):
                return scores
            self.say("Let's repick the full stat spread.")

    def prompt_point_buy_score(self, ability: str, *, points_left: int, allow_back: bool = False) -> int | None:
        while True:
            self.output_fn("")
            back_text = f" Type {BACK_OPTION} to return to the previous ability." if allow_back else ""
            self.say(
                f"Set {ability_label(ability, include_code=True)}. Enter a score from 8 to 15. "
                f"Points left before this pick: {points_left}.{back_text}"
            )
            raw = self.read_input("> ").strip()
            if self.handle_meta_command(raw):
                continue
            if allow_back and raw.lower() == BACK_OPTION.lower():
                return None
            if raw.isdigit():
                score = int(raw)
                if score not in POINT_BUY_COSTS:
                    self.say("Point-buy scores must be between 8 and 15.")
                    continue
                cost = POINT_BUY_COSTS[score]
                if cost > points_left:
                    self.say(f"{score} costs {cost} points, but you only have {points_left} left.")
                    continue
                return score
            self.say("Enter a number from 8 to 15.")
