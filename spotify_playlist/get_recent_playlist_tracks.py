from datetime import datetime, timedelta

from spotify_playlist.deps import SpotifyException


def get_recent_playlist_tracks(
    sp,
    playlist_id,
    days_back=7,
    since_date=None,
    return_track_info=False,
):
    """Fetches tracks added to the playlist since a cutoff date.

    Args:
        sp: Spotify client
        playlist_id: Playlist ID
        days_back: Number of days to look back when since_date is not set (default 7)
        since_date: Only include tracks added on or after this datetime (overrides days_back)
        return_track_info: If True, also returns track information (name, artists)

    Returns:
        If return_track_info=False: set of track URIs
        If return_track_info=True: dict with URI as key and {'name': ..., 'artists': ...} as value
    """
    track_data = {} if return_track_info else set()
    if since_date is not None:
        cutoff_date = since_date
        if isinstance(cutoff_date, datetime) and cutoff_date.tzinfo is not None:
            cutoff_date = cutoff_date.astimezone().replace(tzinfo=None)
        if isinstance(cutoff_date, datetime):
            cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        cutoff_date = datetime.now() - timedelta(days=days_back)

    try:
        # Fetch playlist items with added_at date
        results = sp.playlist_items(
            playlist_id,
            fields='items.added_at,items.track.uri,items.track.name,items.track.artists,next',
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
                if added_at_str:
                    try:
                        # Parse ISO 8601 date
                        added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                        # Convert to local timezone for comparison
                        if added_at.tzinfo:
                            added_at = added_at.astimezone().replace(tzinfo=None)

                        # Only tracks added in the last X days
                        if added_at < cutoff_date:
                            # Stop iterating once we pass the cutoff date
                            # (tracks are sorted newest to oldest)
                            results = None
                            break
                    except (ValueError, AttributeError):
                        # If parsing fails, skip this track
                        continue

                uri = track['uri']
                if return_track_info:
                    artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                    track_data[uri] = {
                        'name': track.get('name', 'Unknown'),
                        'artists': artists
                    }
                else:
                    track_data.add(uri)

            if results:
                results = sp.next(results) if results.get('next') else None

        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching tracks: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error fetching tracks: {e}")
        raise
