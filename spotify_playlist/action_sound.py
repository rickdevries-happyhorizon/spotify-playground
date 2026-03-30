"""Completion vs menu-selection sounds (opt-out via env).

**Completion** (``play_action_done``) — default Glass on macOS.

**Selection** (``play_selection``) — lighter sound when you pick a menu option;
default Tink on macOS.

macOS examples::

    export SPOTIFY_PLAYGROUND_SOUND_FILE=/System/Library/Sounds/Glass.aiff
    export SPOTIFY_PLAYGROUND_SOUND_VOLUME=0.48

    export SPOTIFY_PLAYGROUND_SELECTION_SOUND_FILE=/System/Library/Sounds/Tink.aiff
    export SPOTIFY_PLAYGROUND_SELECTION_SOUND_VOLUME=0.18

Linux: ``SPOTIFY_PLAYGROUND_SOUND_FILE`` / ``SPOTIFY_PLAYGROUND_SELECTION_SOUND_FILE``
point at files for ``paplay``/``aplay``.

Disable::

    export SPOTIFY_PLAYGROUND_NO_SOUND=1
"""

from __future__ import annotations

import os
import subprocess
import sys

_DEFAULT_MACOS_ACTION_SOUND = "/System/Library/Sounds/Glass.aiff"
_DEFAULT_MACOS_ACTION_VOLUME = 0.48

_DEFAULT_MACOS_SELECTION_SOUND = "/System/Library/Sounds/Tink.aiff"
_DEFAULT_MACOS_SELECTION_VOLUME = 0.16

_LINUX_ACTION_FALLBACKS = (
    "/usr/share/sounds/freedesktop/stereo/complete.oga",
    "/usr/share/sounds/freedesktop/stereo/message.oga",
    "/usr/share/sounds/alsa/Front_Left.wav",
    "/usr/share/sounds/alsa/Front.wav",
)

_LINUX_SELECTION_FALLBACKS = (
    "/usr/share/sounds/freedesktop/stereo/message.oga",
    "/usr/share/sounds/freedesktop/stereo/dialog-information.oga",
    "/usr/share/sounds/freedesktop/stereo/complete.oga",
    "/usr/share/sounds/alsa/Front_Left.wav",
)


def _sound_disabled() -> bool:
    v = os.environ.get("SPOTIFY_PLAYGROUND_NO_SOUND", "").strip().lower()
    return v in ("1", "true", "yes")


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        return max(0.0, min(1.0, float(str(raw).strip())))
    except ValueError:
        return default


def _env_path(key: str) -> str | None:
    path = os.environ.get(key, "").strip()
    if path and os.path.isfile(path):
        return path
    return None


def _afplay(path: str, volume: float) -> None:
    if not os.path.isfile(path):
        return
    try:
        subprocess.run(
            ["afplay", "-v", f"{volume:.3f}", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def _linux_play(path: str) -> bool:
    for cmd in (["paplay", path], ["aplay", "-q", path]):
        try:
            r = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
            )
            if r.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def _linux_first_available(paths: tuple[str, ...]) -> str | None:
    for candidate in paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def play_selection() -> None:
    """Short cue when the user picks a menu option (distinct from action completion)."""
    if _sound_disabled():
        return

    if sys.platform == "darwin":
        path = _env_path("SPOTIFY_PLAYGROUND_SELECTION_SOUND_FILE") or (
            _DEFAULT_MACOS_SELECTION_SOUND
            if os.path.isfile(_DEFAULT_MACOS_SELECTION_SOUND)
            else "/System/Library/Sounds/Pop.aiff"
        )
        vol = _env_float("SPOTIFY_PLAYGROUND_SELECTION_SOUND_VOLUME", _DEFAULT_MACOS_SELECTION_VOLUME)
        _afplay(path, vol)
    elif sys.platform == "win32":
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
    else:
        path = _env_path("SPOTIFY_PLAYGROUND_SELECTION_SOUND_FILE") or _linux_first_available(
            _LINUX_SELECTION_FALLBACKS
        )
        if path:
            _linux_play(path)


def play_action_done() -> None:
    """Sound when a background action finishes (sync, export, etc.)."""
    if _sound_disabled():
        return

    if sys.platform == "darwin":
        path = _env_path("SPOTIFY_PLAYGROUND_SOUND_FILE") or (
            _DEFAULT_MACOS_ACTION_SOUND if os.path.isfile(_DEFAULT_MACOS_ACTION_SOUND) else "/System/Library/Sounds/Pop.aiff"
        )
        vol = _env_float("SPOTIFY_PLAYGROUND_SOUND_VOLUME", _DEFAULT_MACOS_ACTION_VOLUME)
        _afplay(path, vol)
    elif sys.platform == "win32":
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
    else:
        path = _env_path("SPOTIFY_PLAYGROUND_SOUND_FILE") or _linux_first_available(_LINUX_ACTION_FALLBACKS)
        if path:
            _linux_play(path)
