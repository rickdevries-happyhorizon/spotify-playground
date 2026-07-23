import spotify_playlist.config as config
from db_store import load_historical_data, load_playlists_config, save_historical_data

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.add_tracks_to_playlist import add_tracks_to_playlist
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_recent_playlist_tracks import get_recent_playlist_tracks
from spotify_playlist.get_track_info import get_track_info
from spotify_playlist.loading_progress import loading_bar


def sync_playlists(sp):
    """Checks source playlists for new tracks and adds them to the destination playlist."""
    # Reload configuration (may have been changed)
    playlists_config = load_playlists_config()
    config.MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
    config.BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

    # Validate configuration
    if not config.BRON_PLAYLISTS:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  No source playlists configured in the database.{Colors.RESET}")
        print(f"{Colors.DIM}   Add source playlists via the menu (playlist configuration) or populate playlist_source.{Colors.RESET}")
        return

    if not config.MIJN_DOEL_PLAYLIST_ID:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  No destination playlist configured in the database.{Colors.RESET}")
        print(f"{Colors.DIM}   Set a destination playlist via the menu or populate destination_config.{Colors.RESET}")
        return

    historische_nummers = load_historical_data(config.BRON_PLAYLISTS)
    nieuwe_nummers_uris = []

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🎵  Start Playlist Sync  🎵{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

    # Process each source playlist
    for idx, pl_id in enumerate(config.BRON_PLAYLISTS, 1):
        try:
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}║{Colors.RESET}  {Colors.BRIGHT_WHITE}📋 Playlist {idx}/{len(config.BRON_PLAYLISTS)}{Colors.RESET}  {Colors.DIM}ID: {pl_id[:20]}...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-45)}║{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╠{'═'*68}╣{Colors.RESET}")

            # Fetch playlist name for better feedback
            try:
                playlist_info = sp.playlist(pl_id, fields='name')
                playlist_name = playlist_info['name']
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎼 {playlist_name}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(playlist_name)-6)}║{Colors.RESET}")
            except Exception:
                playlist_name = "Unknown"
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}Playlist name unavailable{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}")

            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")

            # Fetch only recently added tracks (last 7 days) for speed
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_YELLOW}⏳{Colors.RESET} {Colors.DIM}Checking tracks added in the last 7 days...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-50)}║{Colors.RESET}")
            with loading_bar("Fetching recent tracks..."):
                recent_tracks = get_recent_playlist_tracks(sp, pl_id, days_back=7, return_track_info=True)
            recent_uris = set(recent_tracks.keys())
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_GREEN}✅{Colors.RESET} {Colors.BRIGHT_WHITE}Found {Colors.BOLD}{len(recent_uris)}{Colors.RESET}{Colors.BRIGHT_WHITE} tracks added in the last 7 days{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-60)}║{Colors.RESET}")

            # Show recently added tracks
            if recent_tracks:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}📀 Recently added tracks:{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-25)}║{Colors.RESET}")
                for uri, track_info in sorted(recent_tracks.items(), key=lambda x: x[1]['name']):
                    track_display = f"{track_info['name']} - {track_info['artists']}"
                    # Truncate if too long
                    if len(track_display) > 60:
                        track_display = track_display[:57] + "..."
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.CYAN}•{Colors.RESET} {Colors.WHITE}{track_display}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(track_display)-8)}║{Colors.RESET}")

            # Determine which tracks are new (compare with historical data)
            laatst_bekende_uris = historische_nummers.get(pl_id, set())
            nieuwe_uris = recent_uris - laatst_bekende_uris

            # Update historical data: add new tracks to existing set
            # This preserves all historical tracks, not just the last 7 days
            if nieuwe_uris:
                historische_nummers[pl_id] = laatst_bekende_uris.union(recent_uris)
            else:
                # If there are no new tracks, update only when we have no historical data yet
                if pl_id not in historische_nummers:
                    historische_nummers[pl_id] = recent_uris

            if nieuwe_uris:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 {len(nieuwe_uris)} new tracks found!{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 New tracks:{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-18)}║{Colors.RESET}")
                for uri in sorted(nieuwe_uris, key=lambda u: recent_tracks.get(u, {}).get('name', '')):
                    track_info = recent_tracks.get(uri, {})
                    if track_info:
                        track_display = f"{track_info['name']} - {track_info['artists']}"
                        if len(track_display) > 60:
                            track_display = track_display[:57] + "..."
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{track_display}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(track_display)-8)}║{Colors.RESET}")
                    else:
                        # Fallback when track info is unavailable
                        fallback_info = get_track_info(sp, uri)
                        if len(fallback_info) > 60:
                            fallback_info = fallback_info[:57] + "..."
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.WHITE}{fallback_info}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(fallback_info)-8)}║{Colors.RESET}")
                nieuwe_nummers_uris.extend(list(nieuwe_uris))
            else:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}🤷 No new additions found.{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-35)}║{Colors.RESET}")

            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╚{'═'*68}╝{Colors.RESET}\n")

        except SpotifyException as e:
            print(f"{Colors.BRIGHT_RED}❌ Spotify API error while processing playlist {pl_id}: {e}{Colors.RESET}")
            if e.http_status == 404:
                print(f"{Colors.BRIGHT_YELLOW}   Playlist not found. Check whether the ID is correct.{Colors.RESET}")
            elif e.http_status == 403:
                print(f"{Colors.BRIGHT_YELLOW}   No access to this playlist. Check your permissions.{Colors.RESET}")
            continue
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Error while processing playlist {pl_id}: {e}{Colors.RESET}")
            continue

    # Add new tracks to destination playlist
    add_tracks_to_playlist(sp, nieuwe_nummers_uris, config.MIJN_DOEL_PLAYLIST_ID)

    # Save state for next time
    save_historical_data(historische_nummers)
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Playlist sync completed!{Colors.RESET}\n")
    play_action_done()
