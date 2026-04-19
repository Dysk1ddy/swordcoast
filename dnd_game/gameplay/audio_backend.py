from __future__ import annotations

import ctypes
import math
from pathlib import Path
import threading
import time

try:
    import pygame
except ImportError:  # pragma: no cover - optional dependency
    pygame = None

try:
    import winsound
except ImportError:  # pragma: no cover - Windows-only fallback
    winsound = None


_MIXER_INIT_FAILED = False
_SOUND_CACHE: dict[str, object] = {}
_MIXER_FREQUENCY = 44_100
_MIXER_SAMPLE_SIZE = -16
_MIXER_CHANNELS = 2
_MIXER_BUFFER = 512
_MIXER_SOUND_CHANNEL_COUNT = 16
_MIXER_MUSIC_CHANNEL_COUNT = 2
_MIXER_MUSIC_CHANNEL_START = 0
_MIXER_TOTAL_CHANNEL_COUNT = _MIXER_SOUND_CHANNEL_COUNT + _MIXER_MUSIC_CHANNEL_COUNT
_MCI_MUSIC_ALIAS = "dnd_game_music"
_MCI_MUSIC_EXTENSIONS = frozenset({".mp3", ".wav"})
_MCI_MUSIC_OPEN = False
_WINMM = None
_MUSIC_SOUND_CACHE: dict[str, object] = {}
_MUSIC_LOCK = threading.RLock()
_MUSIC_TRANSITION_TOKEN = 0
_MUSIC_ACTIVE_CHANNEL_INDEX: int | None = None
_MUSIC_CHANNEL_MODE = False
_MUSIC_FADE_STEP_SECONDS = 0.02
_MUSIC_SILENCE_GAP_SECONDS = 0.18


def pygame_is_available() -> bool:
    return pygame is not None


def _winmm():
    global _WINMM
    if _WINMM is not None:
        return _WINMM
    try:
        _WINMM = ctypes.windll.winmm
    except (AttributeError, OSError):
        return None
    return _WINMM


def mci_music_is_available() -> bool:
    return _winmm() is not None


def music_is_available() -> bool:
    return pygame is not None or mci_music_is_available()


def music_file_is_supported(path: Path) -> bool:
    if pygame is not None:
        return True
    return mci_music_is_available() and path.suffix.lower() in _MCI_MUSIC_EXTENSIONS


def sound_effects_are_available() -> bool:
    return pygame is not None or winsound is not None


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
        pygame.mixer.set_num_channels(_MIXER_TOTAL_CHANNEL_COUNT)
        if hasattr(pygame.mixer, "set_reserved"):
            pygame.mixer.set_reserved(_MIXER_MUSIC_CHANNEL_COUNT)
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
    if sound is not None:
        channel = sound.play()
        return channel is not None
    if winsound is None:
        return False
    try:
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except (RuntimeError, OSError):
        return False
    return True


def _mci_send(command: str) -> bool:
    winmm = _winmm()
    if winmm is None:
        return False
    return winmm.mciSendStringW(command, None, 0, None) == 0


def _mci_file_type(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".mp3":
        return "mpegvideo"
    if extension == ".wav":
        return "waveaudio"
    return ""


def _transition_volume(progress: float, curve: str, *, fade_in: bool) -> float:
    progress = max(0.0, min(1.0, progress))
    normalized_curve = curve.lower().replace("-", "_")
    if normalized_curve in {"equal_power", "audio"}:
        angle = progress * math.pi / 2.0
        return math.sin(angle) if fade_in else math.cos(angle)
    if normalized_curve in {"ease", "ease_in_out", "smoothstep"}:
        eased = progress * progress * (3.0 - 2.0 * progress)
    elif normalized_curve in {"exponential", "exp"}:
        eased = 0.0 if progress <= 0.0 else math.pow(progress, 2.0)
    else:
        eased = progress
    return eased if fade_in else 1.0 - eased


def _music_channel(index: int):
    return pygame.mixer.Channel(_MIXER_MUSIC_CHANNEL_START + index)


def load_music_sound(path: Path):
    if not ensure_mixer():
        return None
    cache_key = str(path.resolve())
    cached = _MUSIC_SOUND_CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        sound = pygame.mixer.Sound(str(path))
    except (pygame.error, FileNotFoundError):
        return None
    _MUSIC_SOUND_CACHE[cache_key] = sound
    return sound


def _cancel_music_transition() -> int:
    global _MUSIC_TRANSITION_TOKEN
    _MUSIC_TRANSITION_TOKEN += 1
    return _MUSIC_TRANSITION_TOKEN


def _stop_channel_music_unlocked() -> None:
    global _MUSIC_ACTIVE_CHANNEL_INDEX, _MUSIC_CHANNEL_MODE
    if pygame is None or not mixer_is_ready():
        _MUSIC_ACTIVE_CHANNEL_INDEX = None
        _MUSIC_CHANNEL_MODE = False
        return
    for index in range(_MIXER_MUSIC_CHANNEL_COUNT):
        try:
            _music_channel(index).stop()
        except pygame.error:
            pass
    _MUSIC_ACTIVE_CHANNEL_INDEX = None
    _MUSIC_CHANNEL_MODE = False


def _fade_channel(token: int, channel_index: int, fade_ms: int, curve: str, *, fade_in: bool) -> bool:
    duration = max(0.001, fade_ms / 1000.0)
    started_at = time.perf_counter()
    while True:
        progress = min(1.0, (time.perf_counter() - started_at) / duration)
        with _MUSIC_LOCK:
            if token != _MUSIC_TRANSITION_TOKEN or pygame is None or not mixer_is_ready():
                return False
            try:
                _music_channel(channel_index).set_volume(_transition_volume(progress, curve, fade_in=fade_in))
            except pygame.error:
                return False
        if progress >= 1.0:
            break
        time.sleep(_MUSIC_FADE_STEP_SECONDS)
    return True


def _finish_sequential_transition(token: int, old_index: int | None, new_index: int, sound, loops: int, fade_ms: int, curve: str) -> None:
    global _MUSIC_ACTIVE_CHANNEL_INDEX, _MUSIC_CHANNEL_MODE
    if old_index is not None:
        if not _fade_channel(token, old_index, fade_ms, curve, fade_in=False):
            return
        with _MUSIC_LOCK:
            if token != _MUSIC_TRANSITION_TOKEN or pygame is None or not mixer_is_ready():
                return
        try:
            _music_channel(old_index).stop()
        except pygame.error:
            return
        time.sleep(_MUSIC_SILENCE_GAP_SECONDS)
    with _MUSIC_LOCK:
        if token != _MUSIC_TRANSITION_TOKEN or pygame is None or not mixer_is_ready():
            return
        try:
            new_channel = _music_channel(new_index)
            new_channel.set_volume(0.0)
            new_channel.play(sound, loops=loops)
            _MUSIC_ACTIVE_CHANNEL_INDEX = new_index
            _MUSIC_CHANNEL_MODE = True
        except pygame.error:
            return
    if not _fade_channel(token, new_index, fade_ms, curve, fade_in=True):
        return
    with _MUSIC_LOCK:
        if token != _MUSIC_TRANSITION_TOKEN or pygame is None or not mixer_is_ready():
            return
        try:
            _music_channel(new_index).set_volume(1.0)
        except pygame.error:
            return


def _finish_fadeout(token: int, channel_index: int, fade_ms: int, curve: str) -> None:
    duration = max(0.001, fade_ms / 1000.0)
    started_at = time.perf_counter()
    while True:
        progress = min(1.0, (time.perf_counter() - started_at) / duration)
        with _MUSIC_LOCK:
            if token != _MUSIC_TRANSITION_TOKEN or pygame is None or not mixer_is_ready():
                return
            try:
                _music_channel(channel_index).set_volume(_transition_volume(progress, curve, fade_in=False))
            except pygame.error:
                return
        if progress >= 1.0:
            break
        time.sleep(_MUSIC_FADE_STEP_SECONDS)
    with _MUSIC_LOCK:
        if token != _MUSIC_TRANSITION_TOKEN or pygame is None or not mixer_is_ready():
            return
        try:
            _music_channel(channel_index).stop()
        except pygame.error:
            pass


def play_pygame_channel_music(path: Path, *, loops: int = -1, fade_ms: int = 0, curve: str = "equal_power") -> bool:
    global _MUSIC_ACTIVE_CHANNEL_INDEX, _MUSIC_CHANNEL_MODE
    sound = load_music_sound(path)
    if sound is None:
        return False
    fade_ms = max(0, int(fade_ms))
    with _MUSIC_LOCK:
        token = _cancel_music_transition()
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
        except pygame.error:
            pass
        old_index = _MUSIC_ACTIVE_CHANNEL_INDEX
        old_channel = _music_channel(old_index) if old_index is not None else None
        if old_channel is not None and not old_channel.get_busy():
            old_index = None
            old_channel = None
        new_index = 0 if old_index != 0 else 1
        new_channel = _music_channel(new_index)
        try:
            new_channel.stop()
            new_channel.set_volume(0.0 if fade_ms > 0 else 1.0)
        except pygame.error:
            return False
        _MUSIC_CHANNEL_MODE = True
        if fade_ms <= 0:
            try:
                new_channel.play(sound, loops=loops)
            except pygame.error:
                return False
            _MUSIC_ACTIVE_CHANNEL_INDEX = new_index
            if old_channel is not None:
                old_channel.stop()
            new_channel.set_volume(1.0)
            return True
        if old_index is None:
            _MUSIC_ACTIVE_CHANNEL_INDEX = new_index
        thread = threading.Thread(
            target=_finish_sequential_transition,
            args=(token, old_index, new_index, sound, loops, fade_ms, curve),
            daemon=True,
        )
        thread.start()
        return True


def play_pygame_music(path: Path, *, loops: int = -1, fade_ms: int = 0, curve: str = "equal_power") -> bool:
    if pygame is None or not ensure_mixer():
        return False
    fade_ms = max(0, int(fade_ms))
    token: int
    should_wait_for_fadeout = False
    try:
        with _MUSIC_LOCK:
            token = _cancel_music_transition()
            _stop_channel_music_unlocked()
            if pygame.mixer.music.get_busy():
                if fade_ms > 0:
                    pygame.mixer.music.fadeout(fade_ms)
                    should_wait_for_fadeout = True
                else:
                    pygame.mixer.music.stop()
                    if hasattr(pygame.mixer.music, "unload"):
                        pygame.mixer.music.unload()
    except pygame.error:
        return False
    if should_wait_for_fadeout:
        time.sleep((fade_ms / 1000.0) + _MUSIC_SILENCE_GAP_SECONDS)
        with _MUSIC_LOCK:
            if token != _MUSIC_TRANSITION_TOKEN:
                return True
            try:
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
            except pygame.error:
                return False
    try:
        with _MUSIC_LOCK:
            if token != _MUSIC_TRANSITION_TOKEN:
                return True
            pygame.mixer.music.load(str(path))
            kwargs = {"loops": loops}
            if fade_ms > 0:
                kwargs["fade_ms"] = fade_ms
            pygame.mixer.music.play(**kwargs)
    except (pygame.error, FileNotFoundError):
        return False
    return True


def play_mci_music(path: Path, *, loops: int = -1) -> bool:
    global _MCI_MUSIC_OPEN
    if not path.exists() or path.suffix.lower() not in _MCI_MUSIC_EXTENSIONS:
        return False
    stop_mci_music()
    file_type = _mci_file_type(path)
    type_clause = f" type {file_type}" if file_type else ""
    if not _mci_send(f'open "{path.resolve()}"{type_clause} alias {_MCI_MUSIC_ALIAS}'):
        return False
    _MCI_MUSIC_OPEN = True
    play_command = f"play {_MCI_MUSIC_ALIAS}"
    if loops == -1:
        play_command += " repeat"
    if _mci_send(play_command):
        return True
    stop_mci_music()
    return False


def stop_mci_music() -> None:
    global _MCI_MUSIC_OPEN
    if not _MCI_MUSIC_OPEN:
        return
    _mci_send(f"stop {_MCI_MUSIC_ALIAS}")
    _mci_send(f"close {_MCI_MUSIC_ALIAS}")
    _MCI_MUSIC_OPEN = False


def play_music(path: Path, *, loops: int = -1, fade_ms: int = 0, curve: str = "equal_power") -> bool:
    if ensure_mixer():
        if play_pygame_music(path, loops=loops, fade_ms=fade_ms, curve=curve):
            return True
    return play_mci_music(path, loops=loops)


def stop_music(*, fade_ms: int = 0, curve: str = "equal_power") -> None:
    global _MUSIC_ACTIVE_CHANNEL_INDEX, _MUSIC_CHANNEL_MODE
    if mixer_is_ready():
        with _MUSIC_LOCK:
            token = _cancel_music_transition()
            active_index = _MUSIC_ACTIVE_CHANNEL_INDEX
            if _MUSIC_CHANNEL_MODE and active_index is not None and fade_ms > 0:
                thread = threading.Thread(
                    target=_finish_fadeout,
                    args=(token, active_index, max(0, int(fade_ms)), curve),
                    daemon=True,
                )
                thread.start()
                _MUSIC_ACTIVE_CHANNEL_INDEX = None
                _MUSIC_CHANNEL_MODE = False
            else:
                _stop_channel_music_unlocked()
            try:
                if fade_ms > 0:
                    pygame.mixer.music.fadeout(max(0, int(fade_ms)))
                else:
                    pygame.mixer.music.stop()
                if fade_ms <= 0 and hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
            except pygame.error:
                pass
    stop_mci_music()
