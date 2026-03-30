"""Spotipy dependency check — must import before other package modules use the API."""
import sys

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from spotipy.exceptions import SpotifyException
except ImportError:
    print("❌ Fout: spotipy module niet gevonden!")
    print("\n   Oplossing:")
    print("   1. Gebruik het shell script: ./run_sync.sh")
    print("   2. Of activeer eerst de virtual environment:")
    print("      source path/to/venv/bin/activate")
    print("      python3 playlist_sync.py")
    print("   3. Of installeer spotipy:")
    print("      pip install spotipy")
    sys.exit(1)
