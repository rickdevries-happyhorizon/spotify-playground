from spotify_playlist.deps import SpotifyException


def get_followed_artists(sp):
    """Fetches all followed artists."""
    artist_ids = []
    try:
        results = sp.current_user_followed_artists(limit=50)

        while results:
            for artist in results['artists']['items']:
                artist_ids.append(artist['id'])

            # Check if there are more artists to fetch
            if results['artists'].get('next'):
                # Get the cursor for pagination
                after = results['artists']['cursors'].get('after')
                if after:
                    results = sp.current_user_followed_artists(limit=50, after=after)
                else:
                    break
            else:
                break

        return artist_ids
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching followed artists: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error fetching followed artists: {e}")
        raise
