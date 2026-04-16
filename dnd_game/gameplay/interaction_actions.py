from __future__ import annotations

from ..data.story.interaction_actions import CLASS_INTERACTIONS, RACE_INTERACTIONS, IdentityInteraction


class InteractionActionsMixin:
    def scene_identity_options(self, scene_key: str) -> list[tuple[str, str]]:
        assert self.state is not None
        options: list[tuple[str, str]] = []
        class_action = CLASS_INTERACTIONS.get(scene_key, {}).get(self.state.player.class_name)
        if class_action is not None and not self.state.flags.get(self.identity_flag(scene_key, "class", class_action.key)):
            options.append((f"class:{class_action.key}", self.format_identity_option(class_action)))
        race_action = RACE_INTERACTIONS.get(scene_key, {}).get(self.state.player.race)
        if race_action is not None and not self.state.flags.get(self.identity_flag(scene_key, "race", race_action.key)):
            options.append((f"race:{race_action.key}", self.format_identity_option(race_action)))
        return options

    def handle_scene_identity_action(self, scene_key: str, option_key: str) -> bool:
        assert self.state is not None
        kind, action_key = option_key.split(":", 1)
        table = CLASS_INTERACTIONS if kind == "class" else RACE_INTERACTIONS
        actor_key = self.state.player.class_name if kind == "class" else self.state.player.race
        action = table.get(scene_key, {}).get(actor_key)
        if action is None or action.key != action_key:
            return False
        self.state.flags[self.identity_flag(scene_key, kind, action.key)] = True
        self.play_identity_line(action)
        success = True
        if action.skill is not None and action.dc is not None:
            success = self.skill_check(self.state.player, action.skill, action.dc, context=action.context)
        text = action.success_text if success else action.failure_text
        if text:
            self.say(text)
        if success:
            if action.clue:
                self.add_clue(action.clue)
            if action.xp or action.gold:
                self.reward_party(xp=action.xp, gold=action.gold, reason=f"{self.state.player.class_name if kind == 'class' else self.state.player.race} identity choice")
        if action.journal:
            self.add_journal(action.journal)
        return True

    def identity_flag(self, scene_key: str, kind: str, action_key: str) -> str:
        return f"identity_{scene_key}_{kind}_{action_key}"

    def format_identity_option(self, action: IdentityInteraction) -> str:
        if action.style == "action":
            text = self.action_option(action.line)
        else:
            text = f"\"{action.line}\""
        return self.skill_tag(action.skill_tag, text) if action.skill_tag else text

    def play_identity_line(self, action: IdentityInteraction) -> None:
        if action.style == "action":
            self.player_action(action.line)
        else:
            self.player_speaker(action.line)
