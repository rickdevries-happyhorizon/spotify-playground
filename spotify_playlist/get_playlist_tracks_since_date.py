from datetime import datetime

from spotify_playlist.colors import Colors
from spotify_playlist.release_year import normalize_release_year
from spotify_playlist.deps import SpotifyException


def _track_info_from_item(track: dict) -> dict:
    artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
    album = track.get('album') or {}
    release_year = normalize_release_year(album.get('release_date'))
    info = {
        'name': track.get('name', 'Unknown'),
        'artists': artists,
    }
    if release_year is not None:
        info['release_year'] = release_year
    return info


def get_playlist_tracks_since_date(sp, playlist_id, since_date, return_track_info=False, debug=False):
    """Fetches tracks added to the playlist since a specific date.

    Args:
        sp: Spotify client
        playlist_id: Playlist ID
        since_date: datetime object - only tracks added after this date
        return_track_info: If True, also returns track information (name, artists, added_at)
        debug: If True, show debug information

    Returns:
        If return_track_info=False: set of track URIs
        If return_track_info=True: dict with URI as key and {'name': ..., 'artists': ..., 'added_at': ...} as value
    """
    track_data = {} if return_track_info else set()
    items_without_added_at = 0
    items_processed = 0

    try:
        # Fetch playlist items with added_at date
        # Note: added_at is only available for playlists you own or collaborate on
        results = sp.playlist_items(
            playlist_id,
            fields=(
                'items.added_at,items.track.uri,items.track.name,items.track.artists,'
                'items.track.id,items.track.album.release_date,next'
            ),
            limit=100,
        )

        if debug:
            print(f"{Colors.DIM}   Debug: API response keys: {list(results.keys()) if results else 'None'}{Colors.RESET}")
            if results and 'items' in results:
                print(f"{Colors.DIM}   Debug: Number of items in first batch: {len(results['items'])}{Colors.RESET}")
                if len(results['items']) > 0:
                    first_item = results['items'][0]
                    print(f"{Colors.DIM}   Debug: First item keys: {list(first_item.keys())}{Colors.RESET}")
                    print(f"{Colors.DIM}   Debug: First item added_at: {first_item.get('added_at', 'NOT PRESENT')}{Colors.RESET}")

        while results:
            for item in results['items']:
                items_processed += 1

                # Check that track exists
                track = item.get('track')
                if not track or not track.get('uri'):
                    if debug:
                        print(f"{Colors.DIM}   Debug: Item {items_processed} has no track or URI{Colors.RESET}")
                    continue

                # Check when the track was added
                added_at_str = item.get('added_at')

                if not added_at_str:
                    items_without_added_at += 1
                    if debug and items_without_added_at <= 3:
                        track_name = track.get('name', 'Unknown')
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Track '{track_name}' has no added_at field{Colors.RESET}")
                        print(f"{Colors.DIM}      This may mean you do not have permission to view this information{Colors.RESET}")
                    # If no added_at, include the track (for safety)
                    uri = track['uri']
                    if return_track_info:
                        track_data[uri] = {
                            **_track_info_from_item(track),
                            'added_at': None,  # No date available
                        }
                    else:
                        track_data.add(uri)
                    continue

                try:
                    # Parse ISO 8601 date
                    added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                    # Convert to local timezone for comparison
                    if added_at.tzinfo:
                        added_at = added_at.astimezone().replace(tzinfo=None)

                    if debug and len(track_data) < 5:
                        track_name = track.get('name', 'Unknown')
                        print(
                            f"{Colors.DIM}   Debug: Track '{track_name}' - added_at: "
                            f"{added_at.strftime('%Y-%m-%d %H:%M:%S')}, since_date: "
                            f"{since_date.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
                        )

                    # Only tracks added on or after since_date
                    # Note: we do NOT stop early because order is not always perfect
                    if added_at >= since_date:
                        uri = track['uri']
                        if return_track_info:
                            track_data[uri] = {
                                **_track_info_from_item(track),
                                'added_at': added_at_str,
                            }
                        else:
                            track_data.add(uri)

                except (ValueError, AttributeError) as e:
                    if debug:
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Could not parse date: {added_at_str} - {e}{Colors.RESET}")
                    # If parsing fails, skip this track
                    continue

            if results:
                results = sp.next(results) if results.get('next') else None

        if debug:
            print(f"{Colors.DIM}   Debug: Total items processed: {items_processed}, without added_at: {items_without_added_at}{Colors.RESET}")

        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching tracks: {e}")
        if e.http_status == 403:
            print(f"{Colors.BRIGHT_YELLOW}   ⚠️  No access to added_at information. You may not have permission for this playlist.{Colors.RESET}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error fetching tracks: {e}")
        raise
