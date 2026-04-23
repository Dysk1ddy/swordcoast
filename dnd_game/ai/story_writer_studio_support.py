from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable

from .story_writer import DEFAULT_MODEL, DEFAULT_REASONING_EFFORT, STORY_WRITER_MODES

ENV_API_KEY = "OPENAI_API_KEY"
ENV_MODEL = "OPENAI_MODEL"
ENV_REASONING_EFFORT = "OPENAI_REASONING_EFFORT"
STORY_WRITER_STUDIO_ENV_KEYS = (ENV_API_KEY, ENV_MODEL, ENV_REASONING_EFFORT)
STORY_WRITER_STUDIO_MODEL_OPTIONS = ("gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano")
STORY_WRITER_STUDIO_REASONING_OPTIONS = ("minimal", "low", "medium", "high")
STORY_WRITER_STUDIO_MODE_OPTIONS = STORY_WRITER_MODES


@dataclass(frozen=True)
class StoryWriterLaunchOptions:
    brief: str
    mode: str = "revision"
    title: str = ""
    scene_key: str = ""
    speakers: tuple[str, ...] = ()
    tone_notes: str = ""
    context_paths: tuple[Path, ...] = ()
    no_default_context: bool = False
    model: str = DEFAULT_MODEL
    reasoning_effort: str = DEFAULT_REASONING_EFFORT
    save_path: Path | None = None


def load_dotenv_values(path: Path, keys: Iterable[str] | None = None) -> dict[str, str]:
    key_filter = set(keys) if keys is not None else None
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        normalized_key = key.strip()
        if key_filter is not None and normalized_key not in key_filter:
            continue
        values[normalized_key] = value.strip().strip('"').strip("'")
    return values


def format_env_assignment(key: str, value: str) -> str:
    normalized = value.strip()
    if any(character.isspace() for character in normalized) or "#" in normalized:
        escaped = normalized.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key}="{escaped}"'
    return f"{key}={normalized}"


def update_dotenv_file(path: Path, updates: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []
    remaining = dict(updates)
    written_keys: set[str] = set()
    new_lines: list[str] = []

    for raw_line in existing_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(raw_line)
            continue
        key, _ = stripped.split("=", 1)
        normalized_key = key.strip()
        if normalized_key not in remaining or normalized_key in written_keys:
            new_lines.append(raw_line)
            continue
        replacement_value = remaining.pop(normalized_key)
        written_keys.add(normalized_key)
        if replacement_value.strip():
            new_lines.append(format_env_assignment(normalized_key, replacement_value))

    for key, value in remaining.items():
        if value.strip():
            new_lines.append(format_env_assignment(key, value))

    payload = "\n".join(new_lines).rstrip()
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8")


def split_multivalue_text(text: str) -> tuple[str, ...]:
    parts: list[str] = []
    for line in text.replace(",", "\n").splitlines():
        item = line.strip()
        if item:
            parts.append(item)
    return tuple(parts)


def relative_or_absolute_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return str(resolved)


def generated_story_output_dir(project_root: Path) -> Path:
    return (project_root / "information" / "Story" / "generated").resolve()


def slugify_story_filename(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "story_writer_draft"


def suggested_story_output_path(
    project_root: Path,
    *,
    title: str = "",
    scene_key: str = "",
    mode: str = "revision",
) -> Path:
    base_name = title.strip() or scene_key.strip() or mode.strip() or "story_writer_draft"
    directory = generated_story_output_dir(project_root)
    return (directory / f"{slugify_story_filename(base_name)}.md").resolve()


def build_story_writer_command(
    python_executable: str,
    *,
    project_root: Path,
    options: StoryWriterLaunchOptions,
) -> list[str]:
    command = [python_executable, str((project_root / "tools" / "story_writer.py").resolve())]
    command.extend(["--brief", options.brief])
    command.extend(["--mode", options.mode])
    if options.title.strip():
        command.extend(["--title", options.title.strip()])
    if options.scene_key.strip():
        command.extend(["--scene-key", options.scene_key.strip()])
    for speaker in options.speakers:
        if speaker.strip():
            command.extend(["--speaker", speaker.strip()])
    if options.tone_notes.strip():
        command.extend(["--tone", options.tone_notes.strip()])
    if options.no_default_context:
        command.append("--no-default-context")
    if options.model.strip():
        command.extend(["--model", options.model.strip()])
    if options.reasoning_effort.strip():
        command.extend(["--reasoning-effort", options.reasoning_effort.strip()])
    for context_path in options.context_paths:
        command.extend(["--context", relative_or_absolute_path(context_path, project_root)])
    if options.save_path is not None:
        command.extend(["--save", relative_or_absolute_path(options.save_path, project_root)])
    return command


def display_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)
