from __future__ import annotations

from pathlib import Path
import time

from . import audio_backend


SFX_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "sfx"

SOUND_EFFECT_FILES: dict[str, str] = {
    "fight_victory": "fight_victory.wav",
    "dice_roll": "dice_roll.wav",
    "game_over": "game_over.wav",
    "skill_success": "skill_success.wav",
    "skill_fail": "skill_fail.wav",
    "buy_item": "buy_item.wav",
    "sell_item": "sell_item.wav",
    "player_attack": "player_attack.wav",
    "enemy_attack": "enemy_attack.wav",
    "player_heal": "player_heal.wav",
    "enemy_heal": "enemy_heal.wav",
}


class SoundEffectsMixin:
    def initialize_sound_effects_system(self, play_sfx: bool | None = None) -> None:
        wants_sfx = self._interactive_output if play_sfx is None else play_sfx
        self._sound_effects_enabled_preference = bool(wants_sfx)
        self.sound_effects_enabled = bool(wants_sfx and self.output_fn is print)
        self._sfx_supported = audio_backend.pygame_is_available()
        self._sfx_asset_dir = SFX_ASSET_DIR
        self._last_sfx_at: dict[str, float] = {}
        self._sfx_assets_ready = self._sfx_supported and all(
            (self._sfx_asset_dir / filename).exists() for filename in SOUND_EFFECT_FILES.values()
        )
        if not self._sfx_assets_ready:
            self.sound_effects_enabled = False

    def sound_effect_path(self, effect_name: str) -> Path | None:
        filename = SOUND_EFFECT_FILES.get(effect_name)
        if filename is None:
            return None
        path = self._sfx_asset_dir / filename
        return path if path.exists() else None

    def play_sound_effect(self, effect_name: str, *, cooldown: float = 0.0) -> None:
        if not self.sound_effects_enabled or not self._sfx_supported or not self._sfx_assets_ready:
            return
        path = self.sound_effect_path(effect_name)
        if path is None:
            return
        now = time.perf_counter()
        last_played = self._last_sfx_at.get(effect_name, 0.0)
        if cooldown > 0.0 and now - last_played < cooldown:
            return
        if not audio_backend.play_sound(path):
            return
        self._last_sfx_at[effect_name] = now

    def set_sound_effects_enabled(self, enabled: bool) -> None:
        self._sound_effects_enabled_preference = bool(enabled)
        persist_settings = getattr(self, "persist_settings", None)
        if enabled and not self._sfx_assets_ready:
            self.sound_effects_enabled = False
            if callable(persist_settings):
                persist_settings()
            self.say("Sound effects are not available yet.")
            return
        if enabled and not self._sfx_supported:
            self.sound_effects_enabled = False
            if callable(persist_settings):
                persist_settings()
            self.say("Sound effects are not supported in this build.")
            return
        self.sound_effects_enabled = bool(enabled and self.output_fn is print and self._sfx_supported)
        if callable(persist_settings):
            persist_settings()
        self.say("Sound effects enabled." if self.sound_effects_enabled else "Sound effects muted.")

    def toggle_sound_effects(self) -> None:
        self.set_sound_effects_enabled(not self.sound_effects_enabled)

    def is_enemy_combatant(self, actor) -> bool:
        return actor is not None and "enemy" in getattr(actor, "tags", [])

    def play_attack_sound_for(self, actor) -> None:
        self.play_sound_effect("enemy_attack" if self.is_enemy_combatant(actor) else "player_attack", cooldown=0.05)

    def play_heal_sound_for(self, actor) -> None:
        self.play_sound_effect("enemy_heal" if self.is_enemy_combatant(actor) else "player_heal", cooldown=0.05)
