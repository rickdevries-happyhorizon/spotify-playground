"""Spotipy dependency check — lazy so the menu works before packages are installed."""
from __future__ import annotations

import sys

SPOTIPY_AVAILABLE = False
spotipy = None
SpotifyOAuth = None


class SpotifyException(Exception):
    """Fallback when spotipy is not installed."""


try:
    import spotipy as _spotipy
    from spotipy.exceptions import SpotifyException as _SpotifyException
    from spotipy.oauth2 import SpotifyOAuth as _SpotifyOAuth

    spotipy = _spotipy
    SpotifyOAuth = _SpotifyOAuth
    SpotifyException = _SpotifyException
    SPOTIPY_AVAILABLE = True
except ImportError:
    pass


def require_spotipy() -> None:
    if SPOTIPY_AVAILABLE:
        return

    print("❌ Fout: spotipy module niet gevonden!")
    print("\n   Oplossing:")
    print("   Kies menu-optie 10 om alle packages te installeren.")
    sys.exit(1)
