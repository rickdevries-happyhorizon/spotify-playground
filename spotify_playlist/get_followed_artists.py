from spotify_playlist.deps import SpotifyException


def get_followed_artists(sp):
    """Haalt alle gevolgde artiesten op."""
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
        print(f"❌ Spotify API fout bij ophalen gevolgde artiesten: {e}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen gevolgde artiesten: {e}")
        raise
