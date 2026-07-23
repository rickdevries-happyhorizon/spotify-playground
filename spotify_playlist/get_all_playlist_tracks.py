from spotify_playlist.deps import SpotifyException


def get_all_playlist_tracks(sp, playlist_id, return_track_info=False):
    """Fetches all track URIs from a playlist (handles pagination).

    Args:
        sp: Spotify client
        playlist_id: Playlist ID
        return_track_info: If True, also returns track information (name, artists)

    Returns:
        If return_track_info=False: set of track URIs
        If return_track_info=True: dict with URI as key and {'name': ..., 'artists': ...} as value
    """
    track_data = {} if return_track_info else set()
    try:
        results = sp.playlist_items(
            playlist_id,
            fields='items.track.uri,items.track.name,items.track.artists,next',
            limit=100,
        )

        while results:
            for item in results['items']:
                # Check that 'track' exists to filter out potentially empty items
                track = item.get('track')
                if track and track.get('uri'):
                    uri = track['uri']
                    if return_track_info:
                        artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                        track_data[uri] = {
                            'name': track.get('name', 'Unknown'),
                            'artists': artists
                        }
                    else:
                        track_data.add(uri)

            results = sp.next(results) if results.get('next') else None

        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching tracks: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error fetching tracks: {e}")
        raise
