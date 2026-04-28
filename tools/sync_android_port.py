from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "dnd_game"
DEFAULT_TARGET_ROOT = REPO_ROOT / "android_port" / "dnd_game"
SYNC_SUFFIXES = {".py", ".json", ".md", ".txt"}
EXCLUDED_DIR_NAMES = {"__pycache__", "ai", "assets", "drafts"}
EXCLUDED_FILE_NAMES = {"cli.py", "gui.py"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
DRIFT_KIND_ORDER = {"changed": 0, "missing": 1, "stale": 2}


@dataclass(frozen=True)
class DriftItem:
    kind: str
    relative_path: Path
    source_path: Path | None
    target_path: Path | None

    @property
    def label(self) -> str:
        return self.relative_path.as_posix()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sync_candidate(path: Path, package_root: Path) -> bool:
    if not path.is_file():
        return False
    relative_path = path.relative_to(package_root)
    if any(part in EXCLUDED_DIR_NAMES for part in relative_path.parts[:-1]):
        return False
    if path.name in EXCLUDED_FILE_NAMES:
        return False
    suffix = path.suffix.lower()
    if suffix in EXCLUDED_SUFFIXES:
        return False
    return suffix in SYNC_SUFFIXES


def collect_package_files(package_root: Path) -> dict[Path, Path]:
    if not package_root.exists():
        return {}
    files: dict[Path, Path] = {}
    for path in package_root.rglob("*"):
        if is_sync_candidate(path, package_root):
            files[path.relative_to(package_root)] = path
    return dict(sorted(files.items(), key=lambda item: item[0].as_posix()))


def compare_trees(source_root: Path, target_root: Path) -> list[DriftItem]:
    source_files = collect_package_files(source_root)
    target_files = collect_package_files(target_root)
    drift: list[DriftItem] = []

    for relative_path, source_path in source_files.items():
        target_path = target_files.get(relative_path)
        if target_path is None:
            drift.append(DriftItem("missing", relative_path, source_path, target_root / relative_path))
            continue
        if file_digest(source_path) != file_digest(target_path):
            drift.append(DriftItem("changed", relative_path, source_path, target_path))

    for relative_path, target_path in target_files.items():
        if relative_path not in source_files:
            drift.append(DriftItem("stale", relative_path, None, target_path))

    return sorted(drift, key=lambda item: (DRIFT_KIND_ORDER.get(item.kind, 99), item.label))


def apply_drift(drift: list[DriftItem]) -> list[DriftItem]:
    applied: list[DriftItem] = []
    for item in drift:
        if item.kind not in {"changed", "missing"} or item.source_path is None or item.target_path is None:
            continue
        item.target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.source_path, item.target_path)
        applied.append(item)
    return applied


def format_drift_report(drift: list[DriftItem]) -> str:
    if not drift:
        return "Android package copy is current for synced files."
    lines = ["Android package drift:"]
    for item in drift:
        lines.append(f"- {item.kind}: {item.label}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check or copy shared dnd_game files into android_port/dnd_game.",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROOT, help="desktop dnd_game package root")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET_ROOT, help="Android dnd_game package copy")
    parser.add_argument("--apply", action="store_true", help="copy changed and missing files into the Android package")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_root = args.source.resolve()
    target_root = args.target.resolve()
    drift = compare_trees(source_root, target_root)

    if args.apply:
        applied = apply_drift(drift)
        if applied:
            print(f"Copied {len(applied)} shared file(s) into {target_root}.")
        remaining = compare_trees(source_root, target_root)
        print(format_drift_report(remaining))
        return 1 if remaining else 0

    print(format_drift_report(drift))
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
