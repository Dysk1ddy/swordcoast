# OpenAI Story Writer

This project now includes an optional OpenAI-backed drafting tool for story work:

- module: `dnd_game/ai/story_writer.py`
- CLI wrapper: `tools/story_writer.py`
- desktop studio: `story_writer_studio.py`
- Windows launcher: `Launch Story Writer Studio.bat`

It is designed as a writing assistant, not as runtime story control. That fits this codebase much better because scene logic, flags, quest state, and route outcomes are currently authored directly in Python scene files.

## Why this shape

For Roads That Remember, the safest AI workflow is:

1. keep plot logic deterministic in code
2. let the model draft or revise dialogue and scene prose
3. paste the parts you like back into the relevant source file or story reference
4. run tests after each accepted change

That avoids the biggest failure mode of live AI narrative systems in games like this: beautiful text that quietly contradicts flags, quest outcomes, companion state, or future scenes.

## Setup

Install the official Python SDK:

```powershell
pip install openai
```

Provide an API key either through your shell or a local `.env` file in the project root.

PowerShell example:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Optional environment variables:

```text
OPENAI_MODEL=gpt-5.4
OPENAI_REASONING_EFFORT=minimal
```

The CLI automatically reads a project-local `.env` file if one exists.

If you prefer a form-based workflow, launch the desktop studio from the project root:

```powershell
python story_writer_studio.py
```

The studio lets you:

- paste or save your `OPENAI_API_KEY`
- choose the model, reasoning level, and rewrite mode
- attach story reference files and scene source files
- write the brief you want to send to `story_writer.py`
- watch the live command output in an embedded console
- review the rewritten text in a dedicated draft pane
- save the rewritten markdown into `information/Story/generated` with the `Save Draft` button
- optionally install or upgrade `openai` from the same window

## Recommended workflow

- Use `gpt-5.4` when you want the strongest pass on difficult scene rewrites.
- Use `gpt-5.4-mini` when you want faster, cheaper iteration.
- Feed the tool the exact scene file you plan to edit plus the relevant story reference markdown.
- Keep briefs concrete: who is speaking, what must stay true, and what emotional effect you want.

Good brief ingredients:

- the scene key or chapter
- which NPC voices matter
- what canon facts must not change
- what should improve: tension, pacing, subtext, clarity, menace, tenderness, or payoff

## Example commands

Revise an implemented scene while keeping Act II canon in view:

```powershell
python tools/story_writer.py `
  --mode revision `
  --scene-key conyberry_agatha `
  --title "Agatha first meeting rewrite" `
  --speaker "Agatha" `
  --speaker "Bryn Underbough" `
  --brief "Rewrite Agatha's opening exchange so she feels colder, stranger, and more deliberate without changing the route logic or revelations." `
  --context information/Story/ACT2_CONTENT_REFERENCE.md `
  --context dnd_game/gameplay/act2/conyberry.py `
  --save information/Story/generated/agatha_first_meeting.md
```

Draft a fresh camp banter packet:

```powershell
python tools/story_writer.py `
  --mode banter `
  --speaker "Elira Dawnmantle" `
  --speaker "Bryn Underbough" `
  --brief "Write 6 short campfire lines after a costly road fight. Keep Bryn defensive and Elira steady without making either sentimental." `
  --context information/Story/ACT1_DIALOGUE_REFERENCE.md
```

Draft a new scene skeleton:

```powershell
python tools/story_writer.py `
  --mode scene `
  --scene-key blackwake_crossing `
  --title "Blackwake consequence scene" `
  --brief "Draft a follow-up scene that shows the cost of exposing the Blackwake cell. Keep the tone tense and administrative rather than heroic." `
  --context information/Story/STORY_CONTENT_SUMMARY.md
```

## Notes on defaults

If you pass a `--scene-key`, the tool automatically adds:

- `information/Story/STORY_CONTENT_SUMMARY.md`
- the matching act reference file when available

You can disable that with `--no-default-context` and provide only the files you want.

## Best practices for this repo

- Treat generated text as draft material, not source of truth.
- Keep gameplay effects in Python and data files, not in model output.
- When revising an existing scene, include the actual source file as context.
- When inventing new content, route the first pass into `information/Story/` before moving it into runtime code.
- After accepting a draft into code, run the relevant tests:

```powershell
python -m pytest tests/test_core.py
```

or a smaller focused test target.
