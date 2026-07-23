import traceback
from datetime import datetime, timedelta

from db_store import load_tracking_start_date, save_tracking_start_date, save_new_tracks
from normalize_track_name import normalize_track_name

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_playlist_tracks_since_date import get_playlist_tracks_since_date
from spotify_playlist.loading_progress import loading_bar
from spotify_playlist.spotify_track_energy import fetch_track_energies


def export_new_tracks_since_date(sp, playlist_ids, since_date=None):
    """Import new tracks added to playlists since a specific date into the database.

    Args:
        sp: Spotify client
        playlist_ids: List of playlist IDs to check
        since_date: datetime object - if None, uses the saved start date or today - 7 days
    """
    try:
        # Load saved start date
        saved_start_date = load_tracking_start_date()

        # Determine which date to start from
        if since_date is None:
            # Use saved start date, or default to 7 days ago
            if saved_start_date:
                since_date = saved_start_date
            else:
                since_date = datetime.now() - timedelta(days=7)
                print(f"{Colors.BRIGHT_YELLOW}⚠️  No start date found. Using default: {since_date.strftime('%Y-%m-%d')}{Colors.RESET}")

        # Today is the end date
        today = datetime.now()

        # Warning if start date equals today (no range)
        if since_date.date() == today.date():
            print(f"{Colors.BRIGHT_YELLOW}⚠️  Start date is today. Only tracks from today will be checked.{Colors.RESET}")
            print(f"{Colors.DIM}   To see tracks from earlier days, set an earlier start date.{Colors.RESET}\n")

        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🔍  New Tracks From {since_date.strftime('%Y-%m-%d')} To {today.strftime('%Y-%m-%d')}  🔍{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

        track_entries: list[tuple[dict, str]] = []
        playlist_info_map = {}

        # Loop through each playlist
        for playlist_id in playlist_ids:
            try:
                # Fetch playlist name
                playlist_info = sp.playlist(playlist_id, fields='name')
                playlist_name = playlist_info['name']
                playlist_info_map[playlist_id] = playlist_name

                print(f"{Colors.BRIGHT_CYAN}📋 Checking playlist: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                print(f"{Colors.DIM}   Period: {since_date.strftime('%Y-%m-%d %H:%M:%S')} to {today.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

                # First check if we have access to added_at via a test query
                try:
                    test_results = sp.playlist_items(playlist_id, fields='items.added_at,items.track.uri', limit=1)
                    has_added_at_access = False
                    if test_results and 'items' in test_results and len(test_results['items']) > 0:
                        first_item = test_results['items'][0]
                        if 'added_at' in first_item and first_item['added_at'] is not None:
                            has_added_at_access = True

                    if not has_added_at_access:
                        print(f"{Colors.BRIGHT_RED}   ❌ NO ACCESS TO added_at FIELD!{Colors.RESET}")
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  The Spotify API does not provide 'added_at' information for this playlist.{Colors.RESET}")
                        print(f"{Colors.DIM}   Possible causes:{Colors.RESET}")
                        print(f"{Colors.DIM}   - You are not the owner of this playlist{Colors.RESET}")
                        print(f"{Colors.DIM}   - You do not have collaborator rights{Colors.RESET}")
                        print(f"{Colors.DIM}   - The playlist is public but you do not have write access{Colors.RESET}")
                        print(f"{Colors.DIM}   Solution: Make sure you are the owner or a collaborator of the playlist.{Colors.RESET}")
                        continue
                except Exception as e:
                    print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Could not verify access to added_at: {e}{Colors.RESET}")

                # Use date only (no time) for comparison
                since_date_only = since_date.date()
                today_date_only = today.date()

                # Fetch new tracks since the start date (use start of day for query)
                since_date_for_query = since_date.replace(hour=0, minute=0, second=0, microsecond=0)
                with loading_bar("Fetching tracks in period..."):
                    new_tracks = get_playlist_tracks_since_date(
                        sp, playlist_id, since_date_for_query, return_track_info=True
                    )

                print(f"{Colors.DIM}   Total tracks found after {since_date_only}: {len(new_tracks)}{Colors.RESET}")

                # Filter tracks added between start_date and today
                filtered_tracks = {}

                for uri, track_info in new_tracks.items():
                    added_at_str = track_info.get('added_at', '')
                    if added_at_str:
                        try:
                            added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                            if added_at.tzinfo:
                                added_at = added_at.astimezone().replace(tzinfo=None)

                            # Use date only for comparison
                            added_at_date_only = added_at.date()

                            # Only tracks between start_date and today (both dates inclusive)
                            if since_date_only <= added_at_date_only <= today_date_only:
                                filtered_tracks[uri] = track_info
                        except (ValueError, AttributeError) as e:
                            # If parsing fails, include the track (for safety)
                            print(f"{Colors.BRIGHT_YELLOW}      ⚠️  Could not parse date for track {track_info.get('name', 'Unknown')}: {e}{Colors.RESET}")
                            filtered_tracks[uri] = track_info
                    else:
                        # If no added_at, include the track
                        filtered_tracks[uri] = track_info

                if filtered_tracks:
                    print(f"{Colors.BRIGHT_GREEN}   ✅ {len(filtered_tracks)} new tracks found in range{Colors.RESET}")
                    for uri, track_info in list(filtered_tracks.items())[:5]:  # Show first 5
                        track_display = f"{track_info['artists']} - {track_info['name']}"
                        if len(track_display) > 60:
                            track_display = track_display[:57] + "..."
                        print(f"{Colors.DIM}      • {track_display}{Colors.RESET}")
                    if len(filtered_tracks) > 5:
                        print(f"{Colors.DIM}      ... and {len(filtered_tracks) - 5} more{Colors.RESET}")

                    for uri, track_info in filtered_tracks.items():
                        track_entries.append((
                            {
                                'track': normalize_track_name(
                                    f"{track_info['artists']} - {track_info['name']}"
                                ),
                                'reference_url': None,
                                'genre': playlist_name,
                                'release_year': track_info.get('release_year'),
                            },
                            uri,
                        ))
                else:
                    print(f"{Colors.DIM}   🤷 No new tracks in this period{Colors.RESET}")
                    if len(new_tracks) > 0:
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  But {len(new_tracks)} tracks found outside the range{Colors.RESET}")

            except SpotifyException as e:
                print(f"{Colors.BRIGHT_RED}   ❌ Error fetching playlist {playlist_id}: {e}{Colors.RESET}")
                if e.http_status == 404:
                    print(f"{Colors.BRIGHT_YELLOW}      Playlist not found{Colors.RESET}")
                elif e.http_status == 403:
                    print(f"{Colors.BRIGHT_YELLOW}      No access to this playlist{Colors.RESET}")
                continue
            except Exception as e:
                print(f"{Colors.BRIGHT_RED}   ❌ Unexpected error: {e}{Colors.RESET}")
                continue

        # Save to database
        if track_entries:
            track_entries.sort(key=lambda pair: pair[0]['track'].lower())
            all_new_tracks = [entry for entry, _uri in track_entries]
            track_uris = [uri for _entry, uri in track_entries]

            with loading_bar("Fetching track energy from Spotify..."):
                energies = fetch_track_energies(sp, track_uris)

            found = 0
            for entry, uri in zip(all_new_tracks, track_uris):
                entry['energy'] = energies.get(uri)
                if entry['energy'] is not None:
                    found += 1

            print(
                f"{Colors.DIM}   Energy fetched for {found}/{len(all_new_tracks)} tracks{Colors.RESET}"
            )

            inserted, skipped = save_new_tracks(all_new_tracks)
            if inserted:
                print(
                    f"\n{Colors.BRIGHT_GREEN}✅ {inserted} new tracks saved to database{Colors.RESET}"
                )
            if skipped:
                print(
                    f"{Colors.DIM}   {skipped} tracks skipped (already exist in database){Colors.RESET}"
                )

            print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
            print(
                f"{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ {len(all_new_tracks)} new tracks processed{Colors.RESET}"
            )
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
        else:
            print(f"\n{Colors.BRIGHT_YELLOW}⚠️  No new tracks found to import.{Colors.RESET}")

        # Update start date to today (for next time)
        today = datetime.now()
        save_tracking_start_date(today)
        print(f"\n{Colors.BRIGHT_GREEN}✅ Start date updated to today ({today.strftime('%Y-%m-%d')}){Colors.RESET}")
        print(f"{Colors.DIM}   Next time, tracks will be checked from this date onward.{Colors.RESET}")

        # Important information about Spotify API limitations
        if not track_entries:
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}ℹ️  IMPORTANT INFORMATION ABOUT THE SPOTIFY API{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BRIGHT_WHITE}The Spotify API only provides 'added_at' information for:{Colors.RESET}")
            print(f"{Colors.DIM}  ✓ Playlists you own{Colors.RESET}")
            print(f"{Colors.DIM}  ✓ Collaborative playlists where you are a collaborator{Colors.RESET}")
            print(f"\n{Colors.BRIGHT_YELLOW}For other playlists (e.g. public playlists owned by others):{Colors.RESET}")
            print(f"{Colors.DIM}  ✗ No 'added_at' information available{Colors.RESET}")
            print(f"{Colors.DIM}  ✗ Cannot determine when tracks were added{Colors.RESET}")
            print(f"\n{Colors.BRIGHT_CYAN}Solution:{Colors.RESET}")
            print(f"{Colors.DIM}  • Make sure you are the owner or a collaborator of the playlists{Colors.RESET}")
            print(f"{Colors.DIM}  • Or use another method (e.g. compare with previous state){Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}\n")

        play_action_done()

    except Exception as e:
        print(f"{Colors.BRIGHT_RED}❌ Unexpected error while importing new tracks: {e}{Colors.RESET}")
        print(f"{Colors.DIM}   Traceback: {traceback.format_exc()}{Colors.RESET}")
