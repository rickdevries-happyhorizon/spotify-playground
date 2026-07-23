import traceback
from datetime import datetime, timedelta
from typing import Any, Callable

from db_store import (
    load_tracking_start_date,
    save_new_tracks,
    save_tracking_start_date,
    upsert_playlist,
)
from normalize_track_name import normalize_track_name

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_playlist_tracks_since_date import get_playlist_tracks_since_date
from spotify_playlist.loading_progress import loading_bar
from spotify_playlist.spotify_track_energy import fetch_track_energies

ProgressCallback = Callable[[dict[str, Any]], None]


def _report(on_progress: ProgressCallback | None, **payload: Any) -> None:
    if on_progress:
        on_progress(payload)


def export_new_tracks_since_date(
    sp,
    playlist_ids,
    since_date=None,
    on_progress: ProgressCallback | None = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """Import new tracks added to playlists since a specific date into the database.

    Args:
        sp: Spotify client
        playlist_ids: List of playlist IDs to check
        since_date: datetime object - if None, uses the saved start date or today - 7 days
        on_progress: Optional callback invoked with progress event dicts
        quiet: When True, suppress terminal output and action sounds

    Returns:
        Summary dict with inserted, skipped, total_processed, playlist_count, etc.
    """
    result: dict[str, Any] = {
        "inserted": 0,
        "skipped": 0,
        "total_processed": 0,
        "tracks_found": 0,
        "playlist_count": len(playlist_ids),
        "playlists_checked": 0,
        "since_date": None,
        "until_date": None,
    }

    def log(message: str = "", **style) -> None:
        if quiet:
            return
        print(message)

    try:
        saved_start_date = load_tracking_start_date()

        if since_date is None:
            if saved_start_date:
                since_date = saved_start_date
            else:
                since_date = datetime.now() - timedelta(days=7)
                log(
                    f"{Colors.BRIGHT_YELLOW}⚠️  No start date found. Using default: {since_date.strftime('%Y-%m-%d')}{Colors.RESET}"
                )

        today = datetime.now()
        result["since_date"] = since_date.strftime("%Y-%m-%d")
        result["until_date"] = today.strftime("%Y-%m-%d")

        if since_date.date() == today.date():
            log(
                f"{Colors.BRIGHT_YELLOW}⚠️  Start date is today. Only tracks from today will be checked.{Colors.RESET}"
            )
            log(f"{Colors.DIM}   To see tracks from earlier days, set an earlier start date.{Colors.RESET}\n")

        log(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
        log(
            f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🔍  New Tracks From {since_date.strftime('%Y-%m-%d')} To {today.strftime('%Y-%m-%d')}  🔍{Colors.RESET}"
        )
        log(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

        _report(
            on_progress,
            phase="starting",
            message=f"Scanning playlists from {result['since_date']} to {result['until_date']}",
            playlist_total=len(playlist_ids),
            **{k: result[k] for k in ("since_date", "until_date")},
        )

        track_entries: list[tuple[dict, str]] = []
        playlist_total = len(playlist_ids)

        for playlist_index, playlist_id in enumerate(playlist_ids, start=1):
            try:
                playlist_info = sp.playlist(playlist_id, fields='name,images')
                playlist_name = playlist_info['name']
                playlist_images = playlist_info.get('images') or []
                playlist_image_url = playlist_images[0].get('url') if playlist_images else None
                playlist_row_id = upsert_playlist(
                    playlist_name,
                    playlist_image_url,
                    spotify_id=playlist_id,
                )

                result["playlists_checked"] += 1

                _report(
                    on_progress,
                    phase="playlist_start",
                    message=f"Checking {playlist_name}",
                    playlist_index=playlist_index,
                    playlist_total=playlist_total,
                    playlist_name=playlist_name,
                    playlist_image_url=playlist_image_url,
                )

                log(f"{Colors.BRIGHT_CYAN}📋 Checking playlist: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                log(
                    f"{Colors.DIM}   Period: {since_date.strftime('%Y-%m-%d %H:%M:%S')} to {today.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
                )

                try:
                    test_results = sp.playlist_items(playlist_id, fields='items.added_at,items.track.uri', limit=1)
                    has_added_at_access = False
                    if test_results and 'items' in test_results and len(test_results['items']) > 0:
                        first_item = test_results['items'][0]
                        if 'added_at' in first_item and first_item['added_at'] is not None:
                            has_added_at_access = True

                    if not has_added_at_access:
                        log(f"{Colors.BRIGHT_RED}   ❌ NO ACCESS TO added_at FIELD!{Colors.RESET}")
                        log(
                            f"{Colors.BRIGHT_YELLOW}   ⚠️  The Spotify API does not provide 'added_at' information for this playlist.{Colors.RESET}"
                        )
                        _report(
                            on_progress,
                            phase="playlist_skipped",
                            message=f"No access to added_at for {playlist_name}",
                            playlist_index=playlist_index,
                            playlist_total=playlist_total,
                            playlist_name=playlist_name,
                        )
                        continue
                except Exception as e:
                    log(f"{Colors.BRIGHT_YELLOW}   ⚠️  Could not verify access to added_at: {e}{Colors.RESET}")

                since_date_only = since_date.date()
                today_date_only = today.date()
                since_date_for_query = since_date.replace(hour=0, minute=0, second=0, microsecond=0)

                _report(
                    on_progress,
                    phase="fetching_tracks",
                    message=f"Fetching tracks from {playlist_name}",
                    playlist_index=playlist_index,
                    playlist_total=playlist_total,
                    playlist_name=playlist_name,
                )

                if quiet:
                    new_tracks = get_playlist_tracks_since_date(
                        sp, playlist_id, since_date_for_query, return_track_info=True
                    )
                else:
                    with loading_bar("Fetching tracks in period..."):
                        new_tracks = get_playlist_tracks_since_date(
                            sp, playlist_id, since_date_for_query, return_track_info=True
                        )

                log(f"{Colors.DIM}   Total tracks found after {since_date_only}: {len(new_tracks)}{Colors.RESET}")

                filtered_tracks = {}

                for uri, track_info in new_tracks.items():
                    added_at_str = track_info.get('added_at', '')
                    if added_at_str:
                        try:
                            added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                            if added_at.tzinfo:
                                added_at = added_at.astimezone().replace(tzinfo=None)

                            added_at_date_only = added_at.date()

                            if since_date_only <= added_at_date_only <= today_date_only:
                                filtered_tracks[uri] = track_info
                        except (ValueError, AttributeError) as e:
                            log(
                                f"{Colors.BRIGHT_YELLOW}      ⚠️  Could not parse date for track {track_info.get('name', 'Unknown')}: {e}{Colors.RESET}"
                            )
                            filtered_tracks[uri] = track_info
                    else:
                        filtered_tracks[uri] = track_info

                playlist_track_count = len(filtered_tracks)
                result["tracks_found"] += playlist_track_count

                if filtered_tracks:
                    log(f"{Colors.BRIGHT_GREEN}   ✅ {len(filtered_tracks)} new tracks found in range{Colors.RESET}")
                    for uri, track_info in list(filtered_tracks.items())[:5]:
                        track_display = f"{track_info['artists']} - {track_info['name']}"
                        if len(track_display) > 60:
                            track_display = track_display[:57] + "..."
                        log(f"{Colors.DIM}      • {track_display}{Colors.RESET}")
                    if len(filtered_tracks) > 5:
                        log(f"{Colors.DIM}      ... and {len(filtered_tracks) - 5} more{Colors.RESET}")

                    for uri, track_info in filtered_tracks.items():
                        track_entries.append((
                            {
                                'track': normalize_track_name(
                                    f"{track_info['artists']} - {track_info['name']}"
                                ),
                                'reference_url': None,
                                'playlist_id': playlist_row_id,
                                'genre': playlist_name,
                                'release_year': track_info.get('release_year'),
                                'image_url': track_info.get('image_url'),
                            },
                            uri,
                        ))
                else:
                    log(f"{Colors.DIM}   🤷 No new tracks in this period{Colors.RESET}")
                    if len(new_tracks) > 0:
                        log(
                            f"{Colors.BRIGHT_YELLOW}   ⚠️  But {len(new_tracks)} tracks found outside the range{Colors.RESET}"
                        )

                _report(
                    on_progress,
                    phase="playlist_done",
                    message=f"Found {playlist_track_count} track{'s' if playlist_track_count != 1 else ''} in {playlist_name}",
                    playlist_index=playlist_index,
                    playlist_total=playlist_total,
                    playlist_name=playlist_name,
                    tracks_found=playlist_track_count,
                    total_tracks_found=result["tracks_found"],
                )

            except SpotifyException as e:
                log(f"{Colors.BRIGHT_RED}   ❌ Error fetching playlist {playlist_id}: {e}{Colors.RESET}")
                _report(
                    on_progress,
                    phase="playlist_error",
                    message=f"Error checking playlist: {e}",
                    playlist_index=playlist_index,
                    playlist_total=playlist_total,
                )
                if e.http_status == 404:
                    log(f"{Colors.BRIGHT_YELLOW}      Playlist not found{Colors.RESET}")
                elif e.http_status == 403:
                    log(f"{Colors.BRIGHT_YELLOW}      No access to this playlist{Colors.RESET}")
                continue
            except Exception as e:
                log(f"{Colors.BRIGHT_RED}   ❌ Unexpected error: {e}{Colors.RESET}")
                _report(
                    on_progress,
                    phase="playlist_error",
                    message=f"Unexpected error: {e}",
                    playlist_index=playlist_index,
                    playlist_total=playlist_total,
                )
                continue

        if track_entries:
            track_entries.sort(key=lambda pair: pair[0]['track'].lower())
            all_new_tracks = [entry for entry, _uri in track_entries]
            track_uris = [uri for _entry, uri in track_entries]
            result["total_processed"] = len(all_new_tracks)

            _report(
                on_progress,
                phase="fetching_energy",
                message=f"Fetching energy for {len(all_new_tracks)} tracks",
                total_processed=len(all_new_tracks),
            )

            if quiet:
                energies = fetch_track_energies(sp, track_uris)
            else:
                with loading_bar("Fetching track energy from Spotify..."):
                    energies = fetch_track_energies(sp, track_uris)

            found = 0
            for entry, uri in zip(all_new_tracks, track_uris):
                entry['energy'] = energies.get(uri)
                if entry['energy'] is not None:
                    found += 1

            log(f"{Colors.DIM}   Energy fetched for {found}/{len(all_new_tracks)} tracks{Colors.RESET}")

            _report(
                on_progress,
                phase="saving",
                message=f"Saving {len(all_new_tracks)} tracks to database",
                total_processed=len(all_new_tracks),
            )

            inserted, skipped = save_new_tracks(all_new_tracks)
            result["inserted"] = inserted
            result["skipped"] = skipped

            if inserted:
                log(f"\n{Colors.BRIGHT_GREEN}✅ {inserted} new tracks saved to database{Colors.RESET}")
            if skipped:
                log(f"{Colors.DIM}   {skipped} tracks skipped (already exist in database){Colors.RESET}")

            log(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
            log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ {len(all_new_tracks)} new tracks processed{Colors.RESET}")
            log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
        else:
            log(f"\n{Colors.BRIGHT_YELLOW}⚠️  No new tracks found to import.{Colors.RESET}")

        today = datetime.now()
        save_tracking_start_date(today)
        result["tracking_start_date_updated"] = today.strftime("%Y-%m-%d")
        log(f"\n{Colors.BRIGHT_GREEN}✅ Start date updated to today ({today.strftime('%Y-%m-%d')}){Colors.RESET}")
        log(f"{Colors.DIM}   Next time, tracks will be checked from this date onward.{Colors.RESET}")

        if not track_entries and not quiet:
            log(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
            log(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}ℹ️  IMPORTANT INFORMATION ABOUT THE SPOTIFY API{Colors.RESET}")
            log(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
            log(f"{Colors.BRIGHT_WHITE}The Spotify API only provides 'added_at' information for:{Colors.RESET}")
            log(f"{Colors.DIM}  ✓ Playlists you own{Colors.RESET}")
            log(f"{Colors.DIM}  ✓ Collaborative playlists where you are a collaborator{Colors.RESET}")
            log(f"\n{Colors.BRIGHT_YELLOW}For other playlists (e.g. public playlists owned by others):{Colors.RESET}")
            log(f"{Colors.DIM}  ✗ No 'added_at' information available{Colors.RESET}")
            log(f"{Colors.DIM}  ✗ Cannot determine when tracks were added{Colors.RESET}")
            log(f"\n{Colors.BRIGHT_CYAN}Solution:{Colors.RESET}")
            log(f"{Colors.DIM}  • Make sure you are the owner or a collaborator of the playlists{Colors.RESET}")
            log(f"{Colors.DIM}  • Or use another method (e.g. compare with previous state){Colors.RESET}")
            log(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}\n")

        _report(on_progress, phase="done", message="Import complete", **result)

        if not quiet:
            play_action_done()

        return result

    except Exception as e:
        log(f"{Colors.BRIGHT_RED}❌ Unexpected error while importing new tracks: {e}{Colors.RESET}")
        log(f"{Colors.DIM}   Traceback: {traceback.format_exc()}{Colors.RESET}")
        _report(on_progress, phase="error", message=str(e))
        raise
