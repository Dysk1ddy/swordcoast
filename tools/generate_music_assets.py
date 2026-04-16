from __future__ import annotations

from array import array
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import wave


SAMPLE_RATE = 11025
MASTER_GAIN = 0.82
MUSIC_DIR = Path(__file__).resolve().parents[1] / "dnd_game" / "assets" / "music"
README_PATH = MUSIC_DIR / "README.md"
MANIFEST_PATH = MUSIC_DIR / "manifest.json"
NOISE_TABLE_SIZE = 8192
NOISE_TABLE_MASK = NOISE_TABLE_SIZE - 1
NOISE_RNG = random.Random(1337)
NOISE_TABLE = [NOISE_RNG.uniform(-1.0, 1.0) for _ in range(NOISE_TABLE_SIZE)]
NOTE_CACHE: dict[tuple[str, int, int], array] = {}

SCALES: dict[str, tuple[int, ...]] = {
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "ionian": (0, 2, 4, 5, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
}


@dataclass(frozen=True, slots=True)
class TrackSpec:
    filename: str
    title: str
    context: str
    style: str
    bpm: int
    measures: int
    root_midi: int
    scale: str
    progression: tuple[int, ...]
    description: str

    @property
    def duration_seconds(self) -> float:
        return (240.0 / self.bpm) * self.measures


TRACK_SPECS: tuple[TrackSpec, ...] = (
    TrackSpec("main_menu.wav", "Crown of the Northwind", "main_menu", "main_menu", 80, 32, 57, "dorian", (1, 6, 4, 5), "Heroic menu music with patient strings, clear bells, and a frontier-campaign cadence."),
    TrackSpec("character_creation.wav", "Ink and Embers", "character_creation", "creation", 76, 32, 60, "ionian", (1, 4, 6, 5), "Curious, hopeful music for building a new adventurer beside candlelight and old maps."),
    TrackSpec("camp.wav", "Low Fire Beneath the Pines", "camp", "camp", 72, 32, 55, "dorian", (1, 5, 6, 4), "Warm campfire ambience with gentle plucked strings and a steady low drone."),
    TrackSpec("city_01.wav", "Market Under Stone", "city", "city", 92, 36, 62, "mixolydian", (1, 5, 4, 1), "Brisk town music for trading posts, busy streets, and guarded optimism."),
    TrackSpec("city_02.wav", "Lanterns on the High Street", "city", "city", 88, 36, 64, "ionian", (1, 6, 2, 5), "A brighter city cue with lifted strings and a walking-rhythm pulse."),
    TrackSpec("inn.wav", "Stonehill Hearthstep", "inn", "inn", 104, 40, 67, "mixolydian", (1, 4, 5, 1), "Tavern music with hand-drum bounce, looping fiddled figures, and a warm room feel."),
    TrackSpec("combat_01.wav", "Blades in the Bracken", "combat", "combat", 148, 60, 48, "phrygian", (1, 2, 1, 7), "Aggressive skirmish music with hammering drums, sharp ostinatos, and a relentless chase pulse."),
    TrackSpec("combat_02.wav", "Ash on Iron", "combat", "combat", 154, 62, 46, "phrygian", (1, 2, 6, 2), "A harsher battle cue driven by rapid percussion, dark low strings, and cutting rhythmic attacks."),
    TrackSpec("combat_03.wav", "Red Banner Charge", "combat", "combat", 156, 60, 50, "aeolian", (1, 6, 7, 1), "Fast charge music with pounding war drums and stabbing melodic figures built for open combat."),
    TrackSpec("combat_04.wav", "Broken Shield Pursuit", "combat", "combat", 142, 58, 44, "aeolian", (1, 7, 6, 7), "Heavy pursuit combat music with urgent bass pulses and rough battlefield momentum."),
    TrackSpec("combat_05.wav", "Sparks Before Dawn", "combat", "combat", 150, 60, 49, "dorian", (1, 5, 4, 2), "Relentless frontier battle music that keeps the pressure high from first clash to cleanup."),
    TrackSpec("miniboss_01.wav", "Siegebell Oath", "miniboss_combat", "miniboss", 124, 52, 44, "phrygian", (1, 7, 2, 6), "A heavier lieutenant battle cue with iron-bell accents, war drums, and looming authority."),
    TrackSpec("miniboss_02.wav", "Cinder Crown Duel", "miniboss_combat", "miniboss", 118, 52, 48, "aeolian", (1, 6, 4, 2), "Brooding duel music with wider low-end weight and more deliberate killing pressure."),
    TrackSpec("boss_combat.wav", "Throne of Ashen Glass", "boss_combat", "boss", 108, 48, 42, "phrygian", (1, 7, 6, 2), "Large-scale boss music with ceremonial menace, grinding low drones, and punishing drum cadence."),
    TrackSpec("random_encounter_01.wav", "Milestone Secrets", "random_encounter", "random_encounter", 78, 32, 52, "phrygian", (1, 2, 1, 7), "Suspense-heavy roadside music with low drones, sparse bells, and a sense of being watched."),
    TrackSpec("random_encounter_02.wav", "Road Through Ruin", "random_encounter", "random_encounter", 82, 34, 49, "aeolian", (1, 7, 6, 7), "Tense travel suspense built around uneasy pulses, distant impacts, and little bursts of danger."),
    TrackSpec("random_encounter_03.wav", "Whispering Tree Line", "random_encounter", "random_encounter", 74, 32, 55, "phrygian", (1, 2, 1, 2), "Slow-burn suspense with breathing drones, thin metallic accents, and creeping uncertainty."),
    TrackSpec("random_encounter_04.wav", "A Lock Beneath Moss", "random_encounter", "random_encounter", 80, 34, 57, "dorian", (1, 4, 2, 1), "An investigative suspense cue for hidden caches, old shrines, and choices that might go wrong."),
    TrackSpec("random_encounter_05.wav", "Weather on the Trade Way", "random_encounter", "random_encounter", 76, 34, 51, "aeolian", (1, 6, 7, 2), "Open-road suspense music with storm-bent atmosphere and a constant feeling that trouble is close."),
)


def midi_to_frequency(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def triangle_wave(phase: float) -> float:
    return 1.0 - 4.0 * abs((phase % 1.0) - 0.5)


def saw_wave(phase: float) -> float:
    return 2.0 * (phase % 1.0) - 1.0


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


def scale_note(root_midi: int, scale_name: str, degree: int, octave_shift: int = 0) -> int:
    intervals = SCALES[scale_name]
    index = degree - 1
    octave = index // len(intervals)
    interval = intervals[index % len(intervals)]
    return root_midi + interval + 12 * (octave + octave_shift)


def degree_triad(root_midi: int, scale_name: str, degree: int, octave_shift: int = 0) -> tuple[int, int, int]:
    return (
        scale_note(root_midi, scale_name, degree, octave_shift),
        scale_note(root_midi, scale_name, degree + 2, octave_shift),
        scale_note(root_midi, scale_name, degree + 4, octave_shift),
    )


def waveform_for_event(instrument: str, midi_note: int, duration_samples: int) -> array:
    key = (instrument, midi_note, duration_samples)
    cached = NOTE_CACHE.get(key)
    if cached is not None:
        return cached

    frequency = midi_to_frequency(midi_note)
    data = array("f", [0.0]) * duration_samples
    phase = 0.0
    vibrato_phase = 0.0
    noise_phase = 0
    for index in range(duration_samples):
        time_seconds = index / SAMPLE_RATE
        if instrument == "pad":
            env = envelope(index, duration_samples, 0.08, 0.14)
            vibrato_phase += 5.0 / SAMPLE_RATE
            phase += (frequency * (1.0 + 0.0035 * math.sin(2.0 * math.pi * vibrato_phase))) / SAMPLE_RATE
            value = (
                0.62 * math.sin(2.0 * math.pi * phase)
                + 0.22 * math.sin(4.0 * math.pi * phase)
                + 0.16 * triangle_wave(phase * 0.5)
            )
            data[index] = env * value * 0.52
        elif instrument == "pluck":
            env = envelope(index, duration_samples, 0.01, 0.35) * math.exp(-4.8 * time_seconds)
            phase += frequency / SAMPLE_RATE
            value = 0.55 * triangle_wave(phase) + 0.3 * math.sin(4.0 * math.pi * phase) + 0.15 * saw_wave(phase)
            data[index] = env * value * 0.64
        elif instrument == "lead":
            env = envelope(index, duration_samples, 0.04, 0.18)
            vibrato_phase += 4.0 / SAMPLE_RATE
            phase += (frequency * (1.0 + 0.0022 * math.sin(2.0 * math.pi * vibrato_phase))) / SAMPLE_RATE
            value = 0.5 * triangle_wave(phase) + 0.35 * math.sin(2.0 * math.pi * phase) + 0.15 * math.sin(6.0 * math.pi * phase)
            data[index] = env * value * 0.6
        elif instrument == "bass":
            env = envelope(index, duration_samples, 0.01, 0.2)
            phase += frequency / SAMPLE_RATE
            value = 0.72 * math.sin(2.0 * math.pi * phase) + 0.28 * math.sin(4.0 * math.pi * phase)
            data[index] = env * value * 0.66
        elif instrument == "bell":
            env = envelope(index, duration_samples, 0.005, 0.45) * math.exp(-2.9 * time_seconds)
            phase += frequency / SAMPLE_RATE
            value = (
                0.55 * math.sin(2.0 * math.pi * phase)
                + 0.24 * math.sin(2.0 * math.pi * phase * 2.4)
                + 0.14 * math.sin(2.0 * math.pi * phase * 3.8)
                + 0.07 * math.sin(2.0 * math.pi * phase * 5.1)
            )
            data[index] = env * value * 0.7
        elif instrument == "kick":
            env = math.exp(-10.0 * time_seconds)
            sweep = 115.0 - 75.0 * min(1.0, time_seconds * 5.0)
            phase += sweep / SAMPLE_RATE
            data[index] = env * math.sin(2.0 * math.pi * phase) * 0.95
        elif instrument == "snare":
            env = math.exp(-17.0 * time_seconds)
            phase += 180.0 / SAMPLE_RATE
            noise_phase = (noise_phase + 47) & NOISE_TABLE_MASK
            noise = NOISE_TABLE[noise_phase]
            data[index] = env * (noise * 0.78 + math.sin(2.0 * math.pi * phase) * 0.22) * 0.85
        elif instrument == "shaker":
            env = math.exp(-25.0 * time_seconds)
            noise_phase = (noise_phase + 83) & NOISE_TABLE_MASK
            noise = NOISE_TABLE[noise_phase]
            data[index] = env * noise * 0.48
        elif instrument == "drone":
            env = envelope(index, duration_samples, 0.18, 0.22)
            phase += frequency / SAMPLE_RATE
            value = (
                0.58 * math.sin(2.0 * math.pi * phase)
                + 0.24 * math.sin(math.pi * phase)
                + 0.18 * saw_wave(phase * 0.25)
            )
            data[index] = env * value * 0.58
        elif instrument == "pulse":
            env = envelope(index, duration_samples, 0.01, 0.12)
            phase += frequency / SAMPLE_RATE
            square = 1.0 if math.sin(2.0 * math.pi * phase) >= 0 else -1.0
            value = 0.7 * square + 0.2 * triangle_wave(phase * 2.0) + 0.1 * math.sin(4.0 * math.pi * phase)
            data[index] = env * value * 0.48
        elif instrument == "tom":
            env = math.exp(-8.5 * time_seconds)
            sweep = 150.0 - 70.0 * min(1.0, time_seconds * 3.8)
            phase += sweep / SAMPLE_RATE
            noise_phase = (noise_phase + 29) & NOISE_TABLE_MASK
            value = 0.82 * math.sin(2.0 * math.pi * phase) + 0.18 * NOISE_TABLE[noise_phase]
            data[index] = env * value * 0.86
        elif instrument == "air":
            env = envelope(index, duration_samples, 0.08, 0.25)
            phase += frequency / SAMPLE_RATE
            noise_phase = (noise_phase + 19) & NOISE_TABLE_MASK
            noise = NOISE_TABLE[noise_phase]
            value = 0.62 * noise + 0.38 * math.sin(2.0 * math.pi * phase)
            data[index] = env * value * 0.28
        else:
            raise ValueError(f"Unknown instrument '{instrument}'.")

    NOTE_CACHE[key] = data
    return data


def add_event(buffer: array, start_sample: int, instrument: str, midi_note: int, duration_samples: int, amplitude: float) -> None:
    if duration_samples <= 0 or start_sample >= len(buffer):
        return
    waveform = waveform_for_event(instrument, midi_note, duration_samples)
    end_sample = min(len(buffer), start_sample + duration_samples)
    for offset in range(end_sample - start_sample):
        buffer[start_sample + offset] += waveform[offset] * amplitude


def choose_melody_offsets(style: str, measure_index: int) -> tuple[tuple[float, int], ...]:
    if style in {"main_menu", "creation", "camp"}:
        phrases = (
            ((0.5, 0), (2.0, 2), (3.0, 4)),
            ((1.0, 4), (2.5, 2)),
            ((0.0, 2), (1.5, 4), (3.0, 1)),
        )
    elif style in {"city", "inn"}:
        phrases = (
            ((0.0, 0), (1.0, 2), (2.5, 4), (3.5, 2)),
            ((0.5, 2), (1.5, 4), (3.0, 5)),
            ((0.0, 4), (2.0, 5), (3.0, 2)),
        )
    elif style == "random_encounter":
        phrases = (
            ((1.5, 0), (3.25, 1)),
            ((0.75, 4), (2.75, 1)),
            ((2.0, 2),),
        )
    elif style == "combat":
        phrases = (
            ((0.25, 0), (1.0, 2), (1.75, 4), (2.5, 2), (3.25, 5)),
            ((0.0, 4), (0.75, 5), (1.5, 2), (2.25, 1), (3.0, 4)),
            ((0.5, 2), (1.25, 4), (2.0, 5), (2.75, 4), (3.5, 6)),
        )
    else:
        phrases = (
            ((0.0, 0), (1.0, 2), (2.0, 4), (3.0, 6)),
            ((0.5, 4), (1.5, 2), (2.5, 5), (3.5, 1)),
            ((0.0, 2), (2.0, 6), (3.0, 4)),
        )
    return phrases[measure_index % len(phrases)]


def schedule_track_events(spec: TrackSpec, buffer: array) -> None:
    beat_samples = SAMPLE_RATE * 60.0 / spec.bpm
    measure_samples = int(round(beat_samples * 4.0))
    rng_seed = int(hashlib.sha1(spec.filename.encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(rng_seed)

    for measure_index in range(spec.measures):
        degree = spec.progression[measure_index % len(spec.progression)]
        measure_start = measure_index * measure_samples
        low_chord = degree_triad(spec.root_midi - 12, spec.scale, degree)
        mid_chord = degree_triad(spec.root_midi, spec.scale, degree)
        high_chord = degree_triad(spec.root_midi + 12, spec.scale, degree)
        arp_pattern = (0, 1, 2, 1, 0, 2, 1, 2)
        combat_pattern = (0, 2, 1, 2, 0, 2, 1, 0)

        if spec.style in {"main_menu", "creation", "camp"}:
            for note in mid_chord:
                add_event(buffer, measure_start, "pad", note, measure_samples, 0.17)
            for beat_index, note in ((0.0, low_chord[0]), (2.0, low_chord[2])):
                add_event(buffer, int(measure_start + beat_index * beat_samples), "bass", note, int(beat_samples * 1.8), 0.28)
            for step_index in range(8):
                start_sample = int(measure_start + step_index * (beat_samples / 2.0))
                chord_note = high_chord[arp_pattern[step_index]]
                instrument = "bell" if spec.style != "camp" and step_index % 2 == 0 else "pluck"
                add_event(buffer, start_sample, instrument, chord_note, int(beat_samples * 0.55), 0.14 if instrument == "bell" else 0.17)
            if measure_index % 2 == 0:
                for beat_position, offset in choose_melody_offsets(spec.style, measure_index):
                    melody_note = scale_note(spec.root_midi + 12, spec.scale, degree + offset)
                    add_event(buffer, int(measure_start + beat_position * beat_samples), "lead", melody_note, int(beat_samples * 0.95), 0.2)

        elif spec.style in {"city", "inn"}:
            for note in (mid_chord[0], mid_chord[2]):
                add_event(buffer, measure_start, "pad", note, measure_samples, 0.11)
            for beat_index in range(4):
                bass_note = low_chord[0] if beat_index % 2 == 0 else low_chord[2]
                add_event(buffer, int(measure_start + beat_index * beat_samples), "bass", bass_note, int(beat_samples * 0.85), 0.22)
                add_event(buffer, int(measure_start + beat_index * beat_samples), "kick", 36, int(beat_samples * 0.45), 0.36 if spec.style == "inn" else 0.26)
            for beat_index in (1, 3):
                add_event(buffer, int(measure_start + beat_index * beat_samples), "snare", 38, int(beat_samples * 0.4), 0.18 if spec.style == "city" else 0.28)
            for step_index in range(8):
                start_sample = int(measure_start + step_index * (beat_samples / 2.0))
                note = high_chord[arp_pattern[(step_index + measure_index) % len(arp_pattern)]]
                add_event(buffer, start_sample, "pluck", note, int(beat_samples * 0.45), 0.22 if spec.style == "inn" else 0.18)
                add_event(buffer, start_sample, "shaker", 82, int(beat_samples * 0.2), 0.12)
            for beat_position, offset in choose_melody_offsets(spec.style, measure_index):
                melody_note = scale_note(spec.root_midi + 12, spec.scale, degree + offset)
                instrument = "lead" if spec.style == "city" else "bell"
                add_event(buffer, int(measure_start + beat_position * beat_samples), instrument, melody_note, int(beat_samples * 0.8), 0.17)

        elif spec.style == "random_encounter":
            suspicious_degree = 2 if spec.scale == "phrygian" else 7
            drone_notes = (
                scale_note(spec.root_midi - 12, spec.scale, degree),
                scale_note(spec.root_midi - 12, spec.scale, suspicious_degree),
            )
            for note in drone_notes:
                add_event(buffer, measure_start, "drone", note, measure_samples, 0.16)
            add_event(buffer, measure_start, "pad", mid_chord[0], measure_samples, 0.08)
            add_event(buffer, int(measure_start + beat_samples * 2), "pad", mid_chord[1], int(beat_samples * 2.0), 0.06)

            suspense_beats = (0.0, 2.5) if measure_index % 2 == 0 else (1.0, 3.0)
            for beat_position in suspense_beats:
                bass_note = low_chord[0] if beat_position < 2.0 else low_chord[1]
                add_event(buffer, int(measure_start + beat_position * beat_samples), "bass", bass_note, int(beat_samples * 1.2), 0.2)

            if measure_index % 2 == 0:
                add_event(buffer, int(measure_start + beat_samples * 3.0), "tom", 45, int(beat_samples * 0.55), 0.18)
            if measure_index % 4 in {1, 3}:
                add_event(buffer, int(measure_start + beat_samples * 1.5), "air", spec.root_midi + 12, int(beat_samples * 2.0), 0.14)
            if measure_index % 3 == 0:
                add_event(buffer, int(measure_start + beat_samples * 0.75), "bell", high_chord[1], int(beat_samples * 1.0), 0.1)

            for step_index, chord_index in enumerate((0, 2, 1, 2)):
                start_sample = int(measure_start + (step_index * beat_samples))
                note = scale_note(spec.root_midi + 12, spec.scale, degree + chord_index)
                add_event(buffer, start_sample, "pulse", note, int(beat_samples * 0.32), 0.09)

            if measure_index % 2 == 0:
                for beat_position, offset in choose_melody_offsets(spec.style, measure_index):
                    melody_note = scale_note(spec.root_midi + 12, spec.scale, degree + offset)
                    add_event(buffer, int(measure_start + beat_position * beat_samples), "bell", melody_note, int(beat_samples * 0.85), 0.12)

        elif spec.style == "combat":
            sixteenth = beat_samples / 4.0
            kick_steps = (0, 3, 4, 8, 11, 12)
            snare_steps = (4, 12)
            pulse_pattern = (0, 2, 1, 2, 0, 2, 1, 2, 0, 1, 2, 1, 0, 2, 1, 0)

            for half_start in (0.0, 2.0):
                for note in (mid_chord[0], mid_chord[2]):
                    add_event(buffer, int(measure_start + half_start * beat_samples), "pad", note, int(beat_samples * 2.0), 0.06)
            add_event(buffer, measure_start, "drone", low_chord[0], measure_samples, 0.08)

            for beat_index in range(4):
                bass_note = low_chord[0] if beat_index in {0, 2} else low_chord[2]
                add_event(buffer, int(measure_start + beat_index * beat_samples), "bass", bass_note, int(beat_samples * 0.92), 0.32)

            for step_index in range(16):
                start_sample = int(measure_start + step_index * sixteenth)
                if step_index in kick_steps:
                    add_event(buffer, start_sample, "kick", 36, int(beat_samples * 0.4), 0.46)
                if step_index in snare_steps:
                    add_event(buffer, start_sample, "snare", 38, int(beat_samples * 0.34), 0.36)
                if step_index % 2 == 1:
                    add_event(buffer, start_sample, "shaker", 82, int(sixteenth * 0.9), 0.08)
                if step_index in {7, 15}:
                    add_event(buffer, start_sample, "tom", 45, int(beat_samples * 0.3), 0.22)
                note = high_chord[pulse_pattern[step_index] % len(high_chord)]
                add_event(buffer, start_sample, "pulse", note, int(sixteenth * 0.95), 0.18)
                if step_index in {2, 6, 10, 14}:
                    add_event(buffer, start_sample, "pluck", note, int(sixteenth * 0.8), 0.13)

            if measure_index % 2 == 0:
                for beat_position, offset in choose_melody_offsets(spec.style, measure_index):
                    melody_note = scale_note(spec.root_midi + 12, spec.scale, degree + offset)
                    add_event(buffer, int(measure_start + beat_position * beat_samples), "lead", melody_note, int(beat_samples * 0.52), 0.18)

        elif spec.style == "miniboss":
            sixteenth = beat_samples / 4.0
            for note in mid_chord:
                add_event(buffer, measure_start, "drone", note, measure_samples, 0.1)
            for beat_index in range(4):
                bass_note = low_chord[0] if beat_index in {0, 2} else low_chord[2]
                add_event(buffer, int(measure_start + beat_index * beat_samples), "bass", bass_note, int(beat_samples * 0.95), 0.31)
                add_event(buffer, int(measure_start + beat_index * beat_samples), "kick", 36, int(beat_samples * 0.48), 0.44)
            for beat_index in (1, 3):
                start_sample = int(measure_start + beat_index * beat_samples)
                add_event(buffer, start_sample, "snare", 38, int(beat_samples * 0.42), 0.34)
                add_event(buffer, start_sample, "bell", high_chord[1], int(beat_samples * 0.85), 0.12)
            for step_index in range(8):
                start_sample = int(measure_start + step_index * (beat_samples / 2.0))
                note = high_chord[combat_pattern[(step_index + measure_index + 1) % len(combat_pattern)]]
                add_event(buffer, start_sample, "pulse", note, int(beat_samples * 0.28), 0.16)
                add_event(buffer, start_sample, "pluck", note, int(beat_samples * 0.26), 0.11)
                if step_index in {3, 7}:
                    add_event(buffer, start_sample, "tom", 45, int(beat_samples * 0.38), 0.18)
                elif step_index % 2 == 0:
                    add_event(buffer, start_sample, "shaker", 82, int(sixteenth * 1.2), 0.07)
            for beat_position, offset in choose_melody_offsets(spec.style, measure_index):
                melody_note = scale_note(spec.root_midi + 12, spec.scale, degree + offset)
                add_event(buffer, int(measure_start + beat_position * beat_samples), "lead", melody_note, int(beat_samples * 0.66), 0.18)

        elif spec.style == "boss":
            sixteenth = beat_samples / 4.0
            for note in mid_chord:
                add_event(buffer, measure_start, "drone", note, measure_samples, 0.14)
            add_event(buffer, measure_start, "pad", mid_chord[0], measure_samples, 0.08)
            for beat_index in range(4):
                bass_note = low_chord[0] if beat_index in {0, 2} else low_chord[1]
                add_event(buffer, int(measure_start + beat_index * beat_samples), "bass", bass_note, int(beat_samples * 0.95), 0.35)
            for step_index in range(16):
                start_sample = int(measure_start + step_index * sixteenth)
                if step_index in {0, 4, 8, 12}:
                    add_event(buffer, start_sample, "kick", 36, int(beat_samples * 0.52), 0.48 if step_index in {0, 8} else 0.34)
                if step_index in {4, 12}:
                    add_event(buffer, start_sample, "snare", 38, int(beat_samples * 0.42), 0.36)
                if step_index in {7, 15}:
                    add_event(buffer, start_sample, "tom", 45, int(beat_samples * 0.4), 0.24)
                if step_index % 2 == 0:
                    note = high_chord[combat_pattern[step_index % len(combat_pattern)]]
                    add_event(buffer, start_sample, "pulse", note, int(sixteenth * 0.95), 0.14)
            accent_note = scale_note(spec.root_midi + 12, spec.scale, degree + (rng.choice((0, 2, 4, 5))))
            add_event(buffer, measure_start, "bell", accent_note, int(beat_samples * 1.15), 0.19)
            for beat_position, offset in choose_melody_offsets(spec.style, measure_index):
                melody_note = scale_note(spec.root_midi + 12, spec.scale, degree + offset)
                add_event(buffer, int(measure_start + beat_position * beat_samples), "lead", melody_note, int(beat_samples * 0.74), 0.2)


def finalize_buffer(buffer: array) -> bytes:
    fade_samples = min(int(SAMPLE_RATE * 0.4), len(buffer) // 8)
    for index in range(fade_samples):
        fade = index / max(1, fade_samples)
        buffer[index] *= fade
        buffer[-(index + 1)] *= fade
    peak = max(max(buffer, default=0.0), -min(buffer, default=0.0), 1.0)
    scale = min(MASTER_GAIN / peak, MASTER_GAIN)
    frames = bytearray()
    for sample in buffer:
        value = int(max(-32767, min(32767, round(sample * scale * 32767.0))))
        frames.extend(value.to_bytes(2, byteorder="little", signed=True))
    return bytes(frames)


def render_track(spec: TrackSpec) -> dict[str, object]:
    total_samples = int(round(spec.duration_seconds * SAMPLE_RATE))
    buffer = array("f", [0.0]) * total_samples
    schedule_track_events(spec, buffer)
    frames = finalize_buffer(buffer)
    track_path = MUSIC_DIR / spec.filename
    with wave.open(str(track_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(frames)
    return {
        "filename": spec.filename,
        "title": spec.title,
        "context": spec.context,
        "style": spec.style,
        "bpm": spec.bpm,
        "duration_seconds": round(spec.duration_seconds, 2),
        "sample_rate": SAMPLE_RATE,
        "description": spec.description,
    }


def write_manifest(track_entries: list[dict[str, object]]) -> None:
    manifest = {
        "sample_rate": SAMPLE_RATE,
        "generator": "tools/generate_music_assets.py",
        "tracks": track_entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_readme(track_entries: list[dict[str, object]]) -> None:
    lines = [
        "# Generated Music Library",
        "",
        "These tracks are original procedurally generated WAV files for the terminal RPG soundtrack.",
        "",
        f"- Sample rate: `{SAMPLE_RATE} Hz` mono PCM",
        f"- Track count: `{len(track_entries)}`",
        "- Playback: looped by scene or combat context through the in-game music system",
        "",
        "## Tracks",
        "",
    ]
    for entry in track_entries:
        lines.append(
            f"- `{entry['filename']}` | {entry['title']} | {entry['context']} | {entry['bpm']} BPM | {entry['duration_seconds']}s"
        )
        lines.append(f"  {entry['description']}")
    README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    rendered = [render_track(spec) for spec in TRACK_SPECS]
    write_manifest(rendered)
    write_readme(rendered)
    print(f"Generated {len(rendered)} tracks in {MUSIC_DIR}")


if __name__ == "__main__":
    main()
