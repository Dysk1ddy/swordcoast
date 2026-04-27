from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from uuid import uuid4

from dnd_game.ai.story_writer import (
    StoryContextDocument,
    StoryWriterClient,
    StoryWriterRequest,
    build_story_writer_input,
    build_story_writer_instructions,
    default_context_paths,
    load_context_documents,
    load_local_env_file,
)


class StoryWriterPromptTests(unittest.TestCase):
    @contextmanager
    def make_tempdir(self):
        base = Path.cwd() / "tests_output"
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"story_writer_tmp_{uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        try:
            yield str(path)
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def test_default_context_paths_pick_act2_reference(self) -> None:
        with self.make_tempdir() as tmp_dir:
            root = Path(tmp_dir)
            (root / "README.md").write_text("demo", encoding="utf-8")
            (root / "dnd_game").mkdir()
            story_dir = root / "information" / "Story"
            story_dir.mkdir(parents=True)
            summary = story_dir / "STORY_CONTENT_SUMMARY.md"
            act2 = story_dir / "ACT2_CONTENT_REFERENCE.md"
            summary.write_text("summary", encoding="utf-8")
            act2.write_text("act2", encoding="utf-8")

            paths = default_context_paths(root, "hushfen_pale_circuit")

            self.assertEqual(paths, (summary.resolve(), act2.resolve()))

    def test_load_context_documents_truncates_large_files(self) -> None:
        with self.make_tempdir() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("a" * 64, encoding="utf-8")

            documents = load_context_documents([path], max_chars_per_file=20)

            self.assertEqual(len(documents), 1)
            self.assertTrue(documents[0].truncated)
            self.assertEqual(documents[0].original_length, 64)
            self.assertLessEqual(len(documents[0].text), 20)

    def test_build_story_writer_input_includes_metadata_and_context_labels(self) -> None:
        request = StoryWriterRequest(
            brief="Tighten the scene.",
            mode="revision",
            title="Pale Witness opener",
            scene_key="hushfen_pale_circuit",
            speakers=("Pale Witness", "Bryn Underbough"),
            tone_notes="Keep the Pale Witness restrained and eerie.",
            model="gpt-5.4",
        )
        document = StoryContextDocument(
            path=Path("information/Story/ACT2_CONTENT_REFERENCE.md"),
            text="Act II summary",
            truncated=False,
            original_length=14,
        )

        payload = build_story_writer_input(request, [document], root=Path.cwd())

        self.assertIn("Mode: revision", payload)
        self.assertIn("Scene key: hushfen_pale_circuit", payload)
        self.assertIn("Speakers: Pale Witness, Bryn Underbough", payload)
        self.assertIn("--- BEGIN CONTEXT:", payload)
        self.assertIn("Act II summary", payload)

    def test_build_story_writer_instructions_mentions_dialogue_format(self) -> None:
        request = StoryWriterRequest(
            brief="Rewrite the dialogue.",
            mode="dialogue",
            speakers=("Mira Thann",),
        )

        instructions = build_story_writer_instructions(request)

        self.assertIn("Mira Thann", instructions)
        self.assertIn("Speaker: line", instructions)

    def test_load_local_env_file_sets_missing_keys_only(self) -> None:
        with self.make_tempdir() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "OPENAI_API_KEY=test-key\nOPENAI_MODEL=gpt-5.4-mini\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"OPENAI_MODEL": "keep-me"}, clear=True):
                load_local_env_file(env_path)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key")
                self.assertEqual(os.environ["OPENAI_MODEL"], "keep-me")

    def test_client_resolves_explicit_relative_context_paths(self) -> None:
        with self.make_tempdir() as tmp_dir:
            root = Path(tmp_dir)
            (root / "README.md").write_text("demo", encoding="utf-8")
            (root / "dnd_game").mkdir()
            context_path = root / "notes.md"
            context_path.write_text("notes", encoding="utf-8")
            client = StoryWriterClient(root=root)
            request = StoryWriterRequest(
                brief="Draft notes.",
                context_paths=(Path("notes.md"),),
            )

            resolved = client.resolve_context_paths(request, include_default_context=False)

            self.assertEqual(resolved, (context_path.resolve(),))


if __name__ == "__main__":
    unittest.main()
