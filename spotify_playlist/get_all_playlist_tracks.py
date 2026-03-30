from spotify_playlist.deps import SpotifyException


def get_all_playlist_tracks(sp, playlist_id, return_track_info=False):
    """Haalt alle nummers (tracks) URI's van een afspeellijst op (houdt rekening met paginering).

    Args:
        sp: Spotify client
        playlist_id: ID van de playlist
        return_track_info: Als True, retourneert ook track informatie (naam, artiesten)

    Returns:
        Als return_track_info=False: set van track URIs
        Als return_track_info=True: dict met URI als key en {'name': ..., 'artists': ...} als value
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
                # Controleer of 'track' bestaat om te filteren op potentieel lege items
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
        print(f"❌ Spotify API fout bij ophalen tracks: {e}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen tracks: {e}")
        raise
