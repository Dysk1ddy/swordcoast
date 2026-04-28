from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from .game import TextDnDGame
from .ui.colors import strip_ansi


PLAIN_CHARACTER_REPLACEMENTS = str.maketrans(
    {
        "█": "#",
        "─": "-",
        "━": "-",
        "│": "|",
        "┃": "|",
        "┌": "+",
        "┐": "+",
        "└": "+",
        "┘": "+",
        "╭": "+",
        "╮": "+",
        "╰": "+",
        "╯": "+",
        "├": "+",
        "┤": "+",
        "┬": "+",
        "┴": "+",
        "┼": "+",
        "╞": "+",
        "╡": "+",
        "╪": "+",
        "═": "=",
        "║": "|",
        "╔": "+",
        "╗": "+",
        "╚": "+",
        "╝": "+",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
    }
)


class ScriptedInput:
    def __init__(self, lines: Sequence[str]) -> None:
        self._lines = iter(lines)

    def __call__(self, prompt: str = "") -> str:
        try:
            return next(self._lines).rstrip("\r\n")
        except StopIteration as exc:
            raise EOFError("Scripted input exhausted.") from exc


def plain_output_text(text: object) -> str:
    rendered = strip_ansi(str(text)).translate(PLAIN_CHARACTER_REPLACEMENTS)
    return rendered.encode("ascii", "replace").decode("ascii")


def plain_print(text: object = "") -> None:
    print(plain_output_text(text))


def configure_standard_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                continue


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Play Aethrune from the terminal.",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Use ASCII-safe output and disable Rich terminal panels.",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable dice animation, typed text, pauses, and staggered reveals.",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable music and sound effects for this run.",
    )
    parser.add_argument(
        "--load-save",
        metavar="SLOT",
        help="Load a save slot, save filename, or save path and start from it.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open a mouse-clickable Kivy window with choice buttons.",
    )
    parser.add_argument(
        "--scripted-input",
        metavar="FILE",
        type=Path,
        help="Read newline-separated commands from a text file.",
    )
    return parser


def load_scripted_input(path: Path) -> ScriptedInput:
    return ScriptedInput(path.read_text(encoding="utf-8").splitlines())


def resolve_save_path(game: TextDnDGame, token: str) -> Path | None:
    raw_path = Path(token)
    candidates: list[Path] = []
    if raw_path.suffix.lower() == ".json":
        candidates.append(raw_path)
        candidates.append(game.save_dir / raw_path.name)
    else:
        candidates.append(game.save_path_for_slot_name(token))
        candidates.append(game.save_dir / f"{token}.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    normalized = token.strip().lower()
    for path in game.loadable_save_paths():
        if path.stem.lower() == normalized:
            return path
        if path.name.lower() == normalized:
            return path
        if game.save_display_label(path).lower() == normalized:
            return path
    return None


def create_game_from_args(args: argparse.Namespace) -> TextDnDGame:
    input_fn = load_scripted_input(args.scripted_input) if args.scripted_input else input
    output_fn = plain_print if args.plain else print
    disable_animation = bool(args.no_animation)
    disable_audio = bool(args.no_audio)
    return TextDnDGame(
        input_fn=input_fn,
        output_fn=output_fn,
        animate_dice=False if disable_animation else None,
        pace_output=False if disable_animation else None,
        type_dialogue=False if disable_animation else None,
        staggered_reveals=False if disable_animation else None,
        play_music=False if disable_audio else None,
        play_sfx=False if disable_audio else None,
        plain_output=bool(args.plain),
    )


def run_game_from_args(args: argparse.Namespace) -> int:
    configure_standard_streams()
    if args.gui:
        if sys.version_info >= (3, 14):
            print(
                "The clickable game window uses Kivy, which currently supports Python 3.13 for this project.\n"
                "Keep Python 3.14 installed, then run the GUI with:\n"
                "    py -3.13 -m pip install -r requirements-gui.txt\n"
                "    py -3.13 main.py --gui",
                file=sys.stderr,
            )
            return 2
        try:
            from .gui import run_gui
        except ModuleNotFoundError as exc:
            if (exc.name or "").split(".")[0] == "kivy":
                print(
                    "The clickable game window needs Kivy installed for this Python version. Install it with:\n"
                    "    py -3.13 -m pip install -r requirements-gui.txt",
                    file=sys.stderr,
                )
                return 2
            raise
        return run_gui(load_save=args.load_save)

    game = create_game_from_args(args)
    if args.load_save:
        save_path = resolve_save_path(game, args.load_save)
        if save_path is None:
            print(f"Save not found: {args.load_save}", file=sys.stderr)
            return 2
        game.load_save_path(save_path)
        game.play_current_state()
        return 0
    game.run()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        return run_game_from_args(args)
    except KeyboardInterrupt:
        print("\nInput interrupted. Exiting cleanly.")
        return 130
    except EOFError:
        print("\nInput exhausted. Exiting cleanly.")
        return 0
