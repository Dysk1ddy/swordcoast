from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import shutil
import sys
import unittest
from uuid import uuid4

from dnd_game.ai.story_writer_studio_support import (
    ENV_API_KEY,
    ENV_MODEL,
    ENV_REASONING_EFFORT,
    StoryWriterLaunchOptions,
    build_story_writer_command,
    generated_story_output_dir,
    load_dotenv_values,
    slugify_story_filename,
    split_multivalue_text,
    suggested_story_output_path,
    update_dotenv_file,
)


class StoryWriterStudioSupportTests(unittest.TestCase):
    @contextmanager
    def make_tempdir(self):
        base = Path.cwd() / "tests_output"
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"story_writer_studio_tmp_{uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        try:
            yield path
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def test_split_multivalue_text_accepts_commas_and_lines(self) -> None:
        values = split_multivalue_text("Agatha, Bryn Underbough\nElira Dawnmantle")
        self.assertEqual(values, ("Agatha", "Bryn Underbough", "Elira Dawnmantle"))

    def test_update_dotenv_file_preserves_unknown_lines_and_updates_known_keys(self) -> None:
        with self.make_tempdir() as temp_dir:
            env_path = temp_dir / ".env"
            env_path.write_text(
                "# existing comment\nOTHER_SETTING=keep\nOPENAI_MODEL=gpt-5.4-mini\n",
                encoding="utf-8",
            )

            update_dotenv_file(
                env_path,
                {
                    ENV_API_KEY: "abc123",
                    ENV_MODEL: "gpt-5.4",
                    ENV_REASONING_EFFORT: "minimal",
                },
            )

            payload = env_path.read_text(encoding="utf-8")
            self.assertIn("# existing comment", payload)
            self.assertIn("OTHER_SETTING=keep", payload)
            self.assertIn("OPENAI_API_KEY=abc123", payload)
            self.assertIn("OPENAI_MODEL=gpt-5.4", payload)
            self.assertIn("OPENAI_REASONING_EFFORT=minimal", payload)

    def test_load_dotenv_values_filters_keys(self) -> None:
        with self.make_tempdir() as temp_dir:
            env_path = temp_dir / ".env"
            env_path.write_text(
                "OPENAI_API_KEY=secret\nOPENAI_MODEL=gpt-5.4\nIGNORED=value\n",
                encoding="utf-8",
            )

            values = load_dotenv_values(env_path, (ENV_API_KEY, ENV_MODEL))

            self.assertEqual(values, {ENV_API_KEY: "secret", ENV_MODEL: "gpt-5.4"})

    def test_build_story_writer_command_maps_fields_to_cli_flags(self) -> None:
        root = Path.cwd()
        options = StoryWriterLaunchOptions(
            brief="Tighten the Agatha exchange.",
            mode="revision",
            title="Agatha rewrite",
            scene_key="conyberry_agatha",
            speakers=("Agatha", "Bryn Underbough"),
            tone_notes="Sharper and colder.",
            context_paths=(root / "information" / "Story" / "ACT2_CONTENT_REFERENCE.md",),
            no_default_context=True,
            model="gpt-5.4",
            reasoning_effort="minimal",
            save_path=root / "information" / "Story" / "generated" / "agatha.md",
        )

        command = build_story_writer_command(sys.executable, project_root=root, options=options)

        self.assertIn("--brief", command)
        self.assertIn("Tighten the Agatha exchange.", command)
        self.assertIn("--speaker", command)
        self.assertIn("Agatha", command)
        self.assertIn("--scene-key", command)
        self.assertIn("conyberry_agatha", command)
        self.assertIn("--no-default-context", command)
        self.assertIn("information\\Story\\generated\\agatha.md", " ".join(command))

    def test_generated_story_output_dir_points_to_story_generated_folder(self) -> None:
        expected = (Path.cwd() / "information" / "Story" / "generated").resolve()
        self.assertEqual(generated_story_output_dir(Path.cwd()), expected)

    def test_slugify_story_filename_normalizes_freeform_title(self) -> None:
        self.assertEqual(slugify_story_filename("Agatha First Meeting Rewrite"), "agatha_first_meeting_rewrite")
        self.assertEqual(slugify_story_filename(""), "story_writer_draft")

    def test_suggested_story_output_path_prefers_title_then_scene_key(self) -> None:
        root = Path.cwd()
        path_from_title = suggested_story_output_path(
            root,
            title="Agatha First Meeting Rewrite",
            scene_key="conyberry_agatha",
            mode="revision",
        )
        path_from_scene = suggested_story_output_path(
            root,
            title="",
            scene_key="conyberry_agatha",
            mode="revision",
        )

        self.assertEqual(path_from_title.name, "agatha_first_meeting_rewrite.md")
        self.assertEqual(path_from_scene.name, "conyberry_agatha.md")


if __name__ == "__main__":
    unittest.main()
