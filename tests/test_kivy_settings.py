from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import uuid

try:
    from dnd_game.gui import ClickableTextDnDGame
except Exception as exc:  # pragma: no cover - depends on optional Kivy runtime
    ClickableTextDnDGame = None
    KIVY_IMPORT_ERROR = exc
else:
    KIVY_IMPORT_ERROR = None


class FakeKivyBridge:
    def __init__(self) -> None:
        self.screen = SimpleNamespace(kivy_dark_mode_enabled=True, kivy_fullscreen_enabled=False)
        self.outputs: list[str] = []

    def post_output(self, text: object = "") -> None:
        self.outputs.append(str(text))

    def set_kivy_dark_mode(self, enabled: bool) -> None:
        self.screen.kivy_dark_mode_enabled = bool(enabled)

    def set_kivy_fullscreen(self, enabled: bool) -> None:
        self.screen.kivy_fullscreen_enabled = bool(enabled)


@unittest.skipIf(ClickableTextDnDGame is None, f"Kivy unavailable: {KIVY_IMPORT_ERROR}")
class KivySettingsTests(unittest.TestCase):
    def make_save_dir(self) -> Path:
        save_dir = Path.cwd() / "tests_output" / f"kivy_settings_{uuid.uuid4().hex}"
        save_dir.mkdir(parents=True)
        self.addCleanup(lambda: (save_dir / "settings.json").unlink(missing_ok=True))
        self.addCleanup(lambda: save_dir.rmdir() if save_dir.exists() else None)
        return save_dir

    def test_fullscreen_setting_loads_applies_and_persists(self) -> None:
        save_dir = self.make_save_dir()
        settings_path = save_dir / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "kivy_dark_mode_enabled": False,
                    "kivy_fullscreen_enabled": True,
                }
            ),
            encoding="utf-8",
        )
        bridge = FakeKivyBridge()

        game = ClickableTextDnDGame(bridge, save_dir=save_dir)

        self.assertTrue(game.current_settings_payload()["kivy_fullscreen_enabled"])
        self.assertTrue(bridge.screen.kivy_fullscreen_enabled)
        self.assertFalse(game.current_settings_payload()["kivy_dark_mode_enabled"])

        game.set_kivy_fullscreen_enabled(False)

        stored_settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertFalse(stored_settings["kivy_fullscreen_enabled"])
        self.assertFalse(bridge.screen.kivy_fullscreen_enabled)


if __name__ == "__main__":
    unittest.main()
