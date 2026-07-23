import spotify_playlist.config as config
from db_store import (
    load_historical_data,
    load_playlists_config,
    resolve_sync_days_back,
    save_historical_data,
)

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.add_tracks_to_playlist import add_tracks_to_playlist
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_all_artist_releases import get_all_artist_releases


def sync_artist_releases(sp):
    """Checks followed artists for new releases and adds them to the destination playlist."""
    # Reload configuration (may have been changed)
    playlists_config = load_playlists_config()
    config.MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
    config.BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

    # Validate configuration
    if not config.MIJN_DOEL_PLAYLIST_ID:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  No destination playlist configured in the database.{Colors.RESET}")
        print(f"{Colors.DIM}   Set a destination playlist via the settings page or populate app_config.{Colors.RESET}")
        return

    historische_nummers = load_historical_data(config.BRON_PLAYLISTS)
    nieuwe_nummers_uris = []

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎤  New Releases from Followed Artists  🎤{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}\n")

    try:
        # Fetch new releases (progress shown in get_all_artist_releases)
        days_back = resolve_sync_days_back()
        artist_releases = get_all_artist_releases(sp, days_back)

        if artist_releases:
            # Check which releases are new (not already in historical data)
            artist_releases_key = '__artist_releases__'
            laatst_bekende_artist_releases = historische_nummers.get(artist_releases_key, set())
            nieuwe_artist_uris = set(artist_releases.keys()) - laatst_bekende_artist_releases

            if nieuwe_artist_uris:
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 {len(nieuwe_artist_uris)} new releases found!{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-30)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╠{'═'*68}╣{Colors.RESET}")
                print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 New releases:{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-18)}║{Colors.RESET}")
                for uri in sorted(nieuwe_artist_uris, key=lambda u: artist_releases.get(u, {}).get('name', '')):
                    release_info = artist_releases.get(uri, {})
                    if release_info:
                        release_display = (
                            f"{release_info['name']} - {release_info['artists']} "
                            f"({release_info.get('album', 'Unknown')}) - {release_info.get('release_date', '')}"
                        )
                        if len(release_display) > 60:
                            release_display = release_display[:57] + "..."
                        print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{release_display}{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-len(release_display)-8)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")

                # Add to list of new tracks
                nieuwe_nummers_uris.extend(list(nieuwe_artist_uris))

                # Update historical data
                historische_nummers[artist_releases_key] = set(artist_releases.keys())
            else:
                print(f"{Colors.DIM}🤷 No new releases from followed artists found.{Colors.RESET}\n")
        else:
            print(f"{Colors.DIM}🤷 No new releases found from followed artists.{Colors.RESET}\n")
    except SpotifyException as e:
        print(f"{Colors.BRIGHT_RED}❌ Error fetching artist releases: {e}{Colors.RESET}")
        if e.http_status == 403:
            print(f"{Colors.BRIGHT_YELLOW}   No permission to fetch followed artists. Check your scope (user-follow-read).{Colors.RESET}")
        return
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}❌ Unexpected error fetching artist releases: {e}{Colors.RESET}")
        return

    # Add new releases to destination playlist
    add_tracks_to_playlist(sp, nieuwe_nummers_uris, config.MIJN_DOEL_PLAYLIST_ID)

    # Save state for next time
    save_historical_data(historische_nummers)
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Artist releases sync completed!{Colors.RESET}\n")
    play_action_done()
