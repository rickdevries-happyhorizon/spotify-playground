import sys

import spotify_playlist.config as config
from spotify_playlist.get_spotify_client import get_spotify_client
from spotify_playlist.manage_playlists_config import manage_playlists_config
from spotify_playlist.import_new_tracks_menu import run_import_new_tracks_menu
from spotify_playlist.run_export_new_tracks import run_export_new_tracks
from spotify_playlist.show_menu import show_menu
from spotify_playlist.start_screen import show_start_screen
from spotify_playlist.sync_artist_releases import sync_artist_releases
from spotify_playlist.sync_playlists import sync_playlists
from spotify_playlist.download_youtube_wav import run_download_youtube_wav


def main():
    """Main function with menu system."""
    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--export' or sys.argv[1] == '-e':
            # Run export directly
            run_export_new_tracks()
            return
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print(f"\n🎵 {config.APP_NAME}")
            print("=" * 60)
            print("\nUsage:")
            print("  python playlist_sync.py              - Start interactive menu")
            print("  python playlist_sync.py --export    - Export new tracks directly")
            print("  python playlist_sync.py -e          - Same as --export")
            print("  python playlist_sync.py --help      - Show this help")
            print("\nOptions:")
            print("  --export, -e    Export new tracks using saved settings")
            print("  --help, -h      Show this help text")
            print()
            return

    show_start_screen()
    while True:
        choice = show_menu()

        if choice == 0:
            print("\n👋 Goodbye!")
            break
        elif choice == 1:
            # Sync everything (playlists + artist releases)
            sp = get_spotify_client()
            sync_playlists(sp)
            if config.CHECK_ARTIST_RELEASES:
                sync_artist_releases(sp)
        elif choice == 2:
            sp = get_spotify_client()
            run_import_new_tracks_menu(sp)
        elif choice == 3:
            run_download_youtube_wav(
                config.YOUTUBE_DOWNLOAD_DIR,
                config.YOUTUBE_URLS_FILE,
            )
        elif choice == 4:
            manage_playlists_config()
