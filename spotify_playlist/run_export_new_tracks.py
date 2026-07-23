from db_store import load_playlists_config

from spotify_playlist.colors import Colors
from spotify_playlist.export_new_tracks_since_date import export_new_tracks_since_date
from spotify_playlist.get_spotify_client import get_spotify_client


def run_export_new_tracks():
    """Imports new tracks directly into the database (for command-line use)."""
    sp = get_spotify_client()

    # Load configuration
    playlists_config = load_playlists_config()
    tracking_playlists = playlists_config.get('tracking_playlists', [])

    if not tracking_playlists:
        print(f"{Colors.BRIGHT_RED}❌ No tracking playlists configured.{Colors.RESET}")
        print(f"{Colors.DIM}   Add playlists first via the menu (option 2) or via the configuration.{Colors.RESET}")
        return

    print(f"{Colors.BRIGHT_CYAN}Using {len(tracking_playlists)} saved tracking playlists{Colors.RESET}")

    # Load start date
    since_date = None  # Loaded inside the function

    export_new_tracks_since_date(sp, tracking_playlists, since_date)
