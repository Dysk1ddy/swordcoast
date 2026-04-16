from __future__ import annotations

from pathlib import Path

try:
    import pygame
except ImportError:  # pragma: no cover - optional dependency
    pygame = None


_MIXER_INIT_FAILED = False
_SOUND_CACHE: dict[str, object] = {}
_MIXER_FREQUENCY = 44_100
_MIXER_SAMPLE_SIZE = -16
_MIXER_CHANNELS = 2
_MIXER_BUFFER = 512
_MIXER_SOUND_CHANNEL_COUNT = 16


def pygame_is_available() -> bool:
    return pygame is not None


def mixer_is_ready() -> bool:
    return pygame is not None and pygame.mixer.get_init() is not None


def ensure_mixer() -> bool:
    global _MIXER_INIT_FAILED
    if pygame is None or _MIXER_INIT_FAILED:
        return False
    if mixer_is_ready():
        return True
    try:
        pygame.mixer.init(
            frequency=_MIXER_FREQUENCY,
            size=_MIXER_SAMPLE_SIZE,
            channels=_MIXER_CHANNELS,
            buffer=_MIXER_BUFFER,
        )
        pygame.mixer.set_num_channels(_MIXER_SOUND_CHANNEL_COUNT)
    except pygame.error:
        _MIXER_INIT_FAILED = True
        return False
    return True


def load_sound(path: Path):
    if not ensure_mixer():
        return None
    cache_key = str(path.resolve())
    cached = _SOUND_CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        sound = pygame.mixer.Sound(str(path))
    except (pygame.error, FileNotFoundError):
        return None
    _SOUND_CACHE[cache_key] = sound
    return sound


def play_sound(path: Path) -> bool:
    sound = load_sound(path)
    if sound is None:
        return False
    channel = sound.play()
    return channel is not None


def play_music(path: Path, *, loops: int = -1) -> bool:
    if not ensure_mixer():
        return False
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play(loops=loops)
    except (pygame.error, FileNotFoundError):
        return False
    return True


def stop_music() -> None:
    if not mixer_is_ready():
        return
    try:
        pygame.mixer.music.stop()
        if hasattr(pygame.mixer.music, "unload"):
            pygame.mixer.music.unload()
    except pygame.error:
        return
