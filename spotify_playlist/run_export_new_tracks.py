from db_store import load_playlists_config

from spotify_playlist.colors import Colors
from spotify_playlist.export_new_tracks_since_date import export_new_tracks_since_date
from spotify_playlist.get_spotify_client import get_spotify_client


def run_export_new_tracks():
    """Voert de export nieuwe tracks functie direct uit (voor command-line gebruik)."""
    sp = get_spotify_client()

    # Laad configuratie
    playlists_config = load_playlists_config()
    tracking_playlists = playlists_config.get('tracking_playlists', [])

    if not tracking_playlists:
        print(f"{Colors.BRIGHT_RED}❌ Geen tracking playlists geconfigureerd.{Colors.RESET}")
        print(f"{Colors.DIM}   Voeg eerst playlists toe via het menu (optie 7) of via de configuratie.{Colors.RESET}")
        return

    print(f"{Colors.BRIGHT_CYAN}Gebruik {len(tracking_playlists)} opgeslagen tracking playlists{Colors.RESET}")

    # Laad start datum
    since_date = None  # Wordt in functie geladen

    # Genereer automatische bestandsnaam
    output_file = None

    # Exporteer nieuwe tracks
    export_new_tracks_since_date(sp, tracking_playlists, since_date, output_file)
