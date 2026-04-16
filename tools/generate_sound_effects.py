from __future__ import annotations

from array import array
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import wave


SAMPLE_RATE = 22050
MASTER_GAIN = 0.9
SFX_DIR = Path(__file__).resolve().parents[1] / "dnd_game" / "assets" / "sfx"
README_PATH = SFX_DIR / "README.md"
MANIFEST_PATH = SFX_DIR / "manifest.json"
NOISE_RNG = random.Random(4242)
NOISE_TABLE = [NOISE_RNG.uniform(-1.0, 1.0) for _ in range(32768)]
NOISE_MASK = len(NOISE_TABLE) - 1


@dataclass(frozen=True, slots=True)
class SoundEffectSpec:
    key: str
    filename: str
    title: str
    duration_seconds: float
    description: str


SOUND_EFFECT_SPECS: tuple[SoundEffectSpec, ...] = (
    SoundEffectSpec("fight_victory", "fight_victory.wav", "Triumph Stinger", 1.45, "Bright rising fanfare for winning a fight."),
    SoundEffectSpec("dice_roll", "dice_roll.wav", "Bone Dice Rattle", 1.05, "A rattling dice tumble with a firm final stop."),
    SoundEffectSpec("game_over", "game_over.wav", "Fallen Banner", 1.9, "A dark descending sting for defeat and game over."),
    SoundEffectSpec("skill_success", "skill_success.wav", "Surefooted Success", 0.8, "A confident upward chime for a passed skill check."),
    SoundEffectSpec("skill_fail", "skill_fail.wav", "Misstep", 0.85, "A short sinking sting for a failed skill check."),
    SoundEffectSpec("buy_item", "buy_item.wav", "Coin Purse", 0.75, "A bright coin-and-ledger purchase cue."),
    SoundEffectSpec("sell_item", "sell_item.wav", "Merchant Sale", 0.7, "A lower coin clink for a completed sale."),
    SoundEffectSpec("player_attack", "player_attack.wav", "Heroic Slash", 0.55, "A sharp heroic weapon swing impact."),
    SoundEffectSpec("enemy_attack", "enemy_attack.wav", "Hostile Strike", 0.62, "A rougher hostile hit with more weight."),
    SoundEffectSpec("player_heal", "player_heal.wav", "Restorative Light", 1.1, "A warm magical swell for player-side healing."),
    SoundEffectSpec("enemy_heal", "enemy_heal.wav", "Unsettling Renewal", 1.1, "A colder eerie swell for enemy healing."),
)


def envelope(index: int, duration_samples: int, attack_ratio: float, release_ratio: float) -> float:
    if duration_samples <= 1:
        return 1.0
    attack = max(1, int(duration_samples * attack_ratio))
    release = max(1, int(duration_samples * release_ratio))
    if index < attack:
        return index / attack
    if index >= duration_samples - release:
        return max(0.0, (duration_samples - index) / release)
    return 1.0


def add_tone(
    buffer: array,
    *,
    start_seconds: float,
    duration_seconds: float,
    frequency: float,
    amplitude: float,
    waveform: str = "sine",
    attack_ratio: float = 0.02,
    release_ratio: float = 0.2,
    vibrato_hz: float = 0.0,
    pitch_fall: float = 0.0,
) -> None:
    start = int(start_seconds * SAMPLE_RATE)
    total = int(duration_seconds * SAMPLE_RATE)
    phase = 0.0
    vibrato_phase = 0.0
    for index in range(total):
        destination = start + index
        if destination >= len(buffer):
            break
        time_seconds = index / SAMPLE_RATE
        env = envelope(index, total, attack_ratio, release_ratio)
        current_frequency = max(20.0, frequency - (pitch_fall * time_seconds))
        if vibrato_hz:
            vibrato_phase += vibrato_hz / SAMPLE_RATE
            current_frequency *= 1.0 + 0.01 * math.sin(2.0 * math.pi * vibrato_phase)
        phase += current_frequency / SAMPLE_RATE
        if waveform == "sine":
            value = math.sin(2.0 * math.pi * phase)
        elif waveform == "triangle":
            value = 1.0 - 4.0 * abs((phase % 1.0) - 0.5)
        elif waveform == "saw":
            value = 2.0 * (phase % 1.0) - 1.0
        else:
            value = 1.0 if math.sin(2.0 * math.pi * phase) >= 0 else -1.0
        buffer[destination] += env * value * amplitude


def add_noise(
    buffer: array,
    *,
    start_seconds: float,
    duration_seconds: float,
    amplitude: float,
    attack_ratio: float = 0.01,
    release_ratio: float = 0.2,
    color: float = 0.0,
) -> None:
    start = int(start_seconds * SAMPLE_RATE)
    total = int(duration_seconds * SAMPLE_RATE)
    cursor = int(start_seconds * SAMPLE_RATE * 7) & NOISE_MASK
    previous = 0.0
    for index in range(total):
        destination = start + index
        if destination >= len(buffer):
            break
        env = envelope(index, total, attack_ratio, release_ratio)
        cursor = (cursor + 29) & NOISE_MASK
        value = NOISE_TABLE[cursor]
        if color:
            previous = previous * color + value * (1.0 - color)
            value = previous
        buffer[destination] += env * value * amplitude


def add_chime_cluster(buffer: array, *, start_seconds: float, root_hz: float, major: bool = True, amplitude: float = 0.2) -> None:
    third = 1.25 if major else 1.2
    for offset, interval in enumerate((1.0, third, 1.5)):
        add_tone(
            buffer,
            start_seconds=start_seconds + (offset * 0.05),
            duration_seconds=0.35,
            frequency=root_hz * interval,
            amplitude=amplitude - (offset * 0.03),
            waveform="sine",
            attack_ratio=0.01,
            release_ratio=0.55,
            vibrato_hz=5.0,
        )


def render_effect(spec: SoundEffectSpec) -> dict[str, object]:
    total_samples = int(spec.duration_seconds * SAMPLE_RATE)
    buffer = array("f", [0.0]) * total_samples

    if spec.key == "dice_roll":
        rng = random.Random(1200)
        for index in range(10):
            start = 0.03 + index * 0.07
            pitch = 720 - index * 38 + rng.uniform(-25, 25)
            add_noise(buffer, start_seconds=start, duration_seconds=0.05, amplitude=0.13, color=0.25)
            add_tone(buffer, start_seconds=start, duration_seconds=0.06, frequency=pitch, amplitude=0.12, waveform="triangle", attack_ratio=0.01, release_ratio=0.5, pitch_fall=180)
        add_noise(buffer, start_seconds=0.78, duration_seconds=0.11, amplitude=0.11, color=0.1)
        add_tone(buffer, start_seconds=0.77, duration_seconds=0.14, frequency=180, amplitude=0.2, waveform="sine", release_ratio=0.7)

    elif spec.key == "fight_victory":
        for index, frequency in enumerate((392, 494, 587, 784)):
            add_tone(buffer, start_seconds=0.05 + index * 0.12, duration_seconds=0.34, frequency=frequency, amplitude=0.22, waveform="triangle", release_ratio=0.45)
        add_chime_cluster(buffer, start_seconds=0.55, root_hz=523, major=True, amplitude=0.19)
        add_chime_cluster(buffer, start_seconds=0.82, root_hz=659, major=True, amplitude=0.17)

    elif spec.key == "game_over":
        for index, frequency in enumerate((392, 330, 262, 196)):
            add_tone(buffer, start_seconds=0.08 + index * 0.28, duration_seconds=0.48, frequency=frequency, amplitude=0.21, waveform="saw", release_ratio=0.52, vibrato_hz=2.0, pitch_fall=20)
        add_noise(buffer, start_seconds=0.15, duration_seconds=1.4, amplitude=0.08, color=0.86)
        add_tone(buffer, start_seconds=0.18, duration_seconds=1.35, frequency=82, amplitude=0.16, waveform="sine", release_ratio=0.4)

    elif spec.key == "skill_success":
        add_tone(buffer, start_seconds=0.02, duration_seconds=0.18, frequency=523, amplitude=0.18, waveform="triangle", release_ratio=0.45)
        add_tone(buffer, start_seconds=0.12, duration_seconds=0.18, frequency=659, amplitude=0.2, waveform="triangle", release_ratio=0.45)
        add_chime_cluster(buffer, start_seconds=0.24, root_hz=784, major=True, amplitude=0.16)

    elif spec.key == "skill_fail":
        add_tone(buffer, start_seconds=0.03, duration_seconds=0.2, frequency=330, amplitude=0.16, waveform="saw", release_ratio=0.35, pitch_fall=50)
        add_tone(buffer, start_seconds=0.16, duration_seconds=0.28, frequency=247, amplitude=0.18, waveform="saw", release_ratio=0.45, pitch_fall=70)
        add_noise(buffer, start_seconds=0.12, duration_seconds=0.25, amplitude=0.05, color=0.4)

    elif spec.key == "buy_item":
        add_tone(buffer, start_seconds=0.05, duration_seconds=0.11, frequency=1100, amplitude=0.15, waveform="sine", release_ratio=0.65)
        add_tone(buffer, start_seconds=0.1, duration_seconds=0.1, frequency=1450, amplitude=0.12, waveform="sine", release_ratio=0.6)
        add_tone(buffer, start_seconds=0.2, duration_seconds=0.1, frequency=1320, amplitude=0.11, waveform="sine", release_ratio=0.6)
        add_noise(buffer, start_seconds=0.04, duration_seconds=0.08, amplitude=0.03)

    elif spec.key == "sell_item":
        add_tone(buffer, start_seconds=0.05, duration_seconds=0.12, frequency=760, amplitude=0.14, waveform="triangle", release_ratio=0.55)
        add_tone(buffer, start_seconds=0.18, duration_seconds=0.12, frequency=640, amplitude=0.12, waveform="triangle", release_ratio=0.55)
        add_noise(buffer, start_seconds=0.04, duration_seconds=0.08, amplitude=0.035, color=0.2)

    elif spec.key == "player_attack":
        add_noise(buffer, start_seconds=0.02, duration_seconds=0.16, amplitude=0.1, color=0.08)
        add_tone(buffer, start_seconds=0.01, duration_seconds=0.18, frequency=920, amplitude=0.12, waveform="saw", release_ratio=0.55, pitch_fall=900)
        add_tone(buffer, start_seconds=0.16, duration_seconds=0.12, frequency=220, amplitude=0.15, waveform="sine", release_ratio=0.5, pitch_fall=140)

    elif spec.key == "enemy_attack":
        add_noise(buffer, start_seconds=0.02, duration_seconds=0.2, amplitude=0.12, color=0.03)
        add_tone(buffer, start_seconds=0.01, duration_seconds=0.22, frequency=540, amplitude=0.15, waveform="saw", release_ratio=0.52, pitch_fall=620)
        add_tone(buffer, start_seconds=0.18, duration_seconds=0.16, frequency=120, amplitude=0.16, waveform="sine", release_ratio=0.55, pitch_fall=60)

    elif spec.key == "player_heal":
        for index, frequency in enumerate((349, 440, 523, 659)):
            add_tone(buffer, start_seconds=0.08 + index * 0.12, duration_seconds=0.5, frequency=frequency, amplitude=0.12, waveform="sine", attack_ratio=0.08, release_ratio=0.5, vibrato_hz=4.0)
        add_chime_cluster(buffer, start_seconds=0.52, root_hz=523, major=True, amplitude=0.16)

    elif spec.key == "enemy_heal":
        for index, frequency in enumerate((220, 277, 330, 415)):
            add_tone(buffer, start_seconds=0.06 + index * 0.11, duration_seconds=0.56, frequency=frequency, amplitude=0.13, waveform="triangle", attack_ratio=0.08, release_ratio=0.54, vibrato_hz=2.0)
        add_noise(buffer, start_seconds=0.12, duration_seconds=0.72, amplitude=0.04, color=0.9)
        add_chime_cluster(buffer, start_seconds=0.5, root_hz=330, major=False, amplitude=0.14)

    peak = max(max(buffer, default=0.0), -min(buffer, default=0.0), 1.0)
    scale = min(MASTER_GAIN / peak, MASTER_GAIN)
    frames = bytearray()
    for sample in buffer:
        value = int(max(-32767, min(32767, round(sample * scale * 32767.0))))
        frames.extend(value.to_bytes(2, byteorder="little", signed=True))
    path = SFX_DIR / spec.filename
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(bytes(frames))
    return {
        "key": spec.key,
        "filename": spec.filename,
        "title": spec.title,
        "duration_seconds": round(spec.duration_seconds, 2),
        "sample_rate": SAMPLE_RATE,
        "description": spec.description,
    }


def write_manifest(entries: list[dict[str, object]]) -> None:
    manifest = {"sample_rate": SAMPLE_RATE, "generator": "tools/generate_sound_effects.py", "effects": entries}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_readme(entries: list[dict[str, object]]) -> None:
    lines = [
        "# Generated Sound Effects",
        "",
        "These WAV files are short procedural sound effects for gameplay events.",
        "",
        f"- Sample rate: `{SAMPLE_RATE} Hz` mono PCM",
        f"- Effect count: `{len(entries)}`",
        "",
        "## Effects",
        "",
    ]
    for entry in entries:
        lines.append(f"- `{entry['filename']}` | `{entry['key']}` | {entry['duration_seconds']}s")
        lines.append(f"  {entry['description']}")
    README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    entries = [render_effect(spec) for spec in SOUND_EFFECT_SPECS]
    write_manifest(entries)
    write_readme(entries)
    print(f"Generated {len(entries)} sound effects in {SFX_DIR}")


if __name__ == "__main__":
    main()
