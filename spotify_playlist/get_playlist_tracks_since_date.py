from datetime import datetime

from spotify_playlist.colors import Colors
from spotify_playlist.release_year import normalize_release_year
from spotify_playlist.deps import SpotifyException


def album_art_url(album: dict) -> str | None:
    images = album.get('images') or []
    if not images:
        return None
    return images[0].get('url')


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
    image_url = album_art_url(album)
    if image_url:
        info['image_url'] = image_url
    return info


def get_playlist_tracks_since_date(sp, playlist_id, since_date, return_track_info=False):
    """Fetches tracks added to the playlist since a specific date.

    Args:
        sp: Spotify client
        playlist_id: Playlist ID
        since_date: datetime object - only tracks added after this date
        return_track_info: If True, also returns track information (name, artists, added_at)

    Returns:
        If return_track_info=False: set of track URIs
        If return_track_info=True: dict with URI as key and {'name': ..., 'artists': ..., 'added_at': ...} as value
    """
    track_data = {} if return_track_info else set()

    try:
        # Fetch playlist items with added_at date
        # Note: added_at is only available for playlists you own or collaborate on
        results = sp.playlist_items(
            playlist_id,
            fields=(
                'items.added_at,items.track.uri,items.track.name,items.track.artists,'
                'items.track.id,items.track.album.release_date,items.track.album.images,next'
            ),
            limit=100,
        )

        while results:
            for item in results['items']:
                # Check that track exists
                track = item.get('track')
                if not track or not track.get('uri'):
                    continue

                # Check when the track was added
                added_at_str = item.get('added_at')

                if not added_at_str:
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

                except (ValueError, AttributeError):
                    # If parsing fails, skip this track
                    continue

            if results:
                results = sp.next(results) if results.get('next') else None

        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching tracks: {e}")
        if e.http_status == 403:
            print(f"{Colors.BRIGHT_YELLOW}   ⚠️  No access to added_at information. You may not have permission for this playlist.{Colors.RESET}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error fetching tracks: {e}")
        raise
