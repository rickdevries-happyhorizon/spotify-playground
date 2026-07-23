from datetime import datetime, timedelta

from spotify_playlist.deps import SpotifyException


def get_artist_new_releases(sp, artist_id, days_back=30):
    """Fetches new releases from an artist within the specified number of days."""
    new_tracks = {}
    try:
        # Calculate the date X days ago
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Fetch albums from the artist
        albums = sp.artist_albums(artist_id, album_type='album,single', limit=50)

        for album in albums['items']:
            # Check release date
            release_date = album.get('release_date', '')
            if not release_date:
                continue

            # Parse release date (can be YYYY, YYYY-MM, or YYYY-MM-DD)
            try:
                if len(release_date) == 4:  # Year only
                    release_dt = datetime(int(release_date), 1, 1)
                elif len(release_date) == 7:  # YYYY-MM
                    year, month = release_date.split('-')
                    release_dt = datetime(int(year), int(month), 1)
                else:  # YYYY-MM-DD
                    release_dt = datetime.strptime(release_date, '%Y-%m-%d')

                # Only albums released recently
                if release_dt >= cutoff_date:
                    # Fetch tracks from the album
                    album_tracks = sp.album_tracks(album['id'])
                    for track_item in album_tracks['items']:
                        if track_item and track_item.get('uri'):
                            uri = track_item['uri']
                            artists = ', '.join([artist['name'] for artist in track_item.get('artists', [])])
                            new_tracks[uri] = {
                                'name': track_item.get('name', 'Unknown'),
                                'artists': artists,
                                'album': album.get('name', 'Unknown'),
                                'release_date': release_date
                            }
            except (ValueError, TypeError):
                # Skip albums with invalid dates
                continue

        return new_tracks
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching releases for artist {artist_id}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error fetching releases: {e}")
        return {}
