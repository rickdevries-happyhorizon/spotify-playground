from datetime import datetime, timedelta

from spotify_playlist.deps import SpotifyException


def get_recent_playlist_tracks(sp, playlist_id, days_back=7, return_track_info=False):
    """Haalt alleen tracks op die in de laatste X dagen zijn toegevoegd aan de playlist.

    Args:
        sp: Spotify client
        playlist_id: ID van de playlist
        days_back: Aantal dagen terug om te kijken (standaard 7)
        return_track_info: Als True, retourneert ook track informatie (naam, artiesten)

    Returns:
        Als return_track_info=False: set van track URIs
        Als return_track_info=True: dict met URI als key en {'name': ..., 'artists': ...} als value
    """
    track_data = {} if return_track_info else set()
    cutoff_date = datetime.now() - timedelta(days=days_back)

    try:
        # Haal playlist items op met added_at datum
        results = sp.playlist_items(
            playlist_id,
            fields='items.added_at,items.track.uri,items.track.name,items.track.artists,next',
            limit=100,
        )

        while results:
            for item in results['items']:
                # Controleer of track bestaat
                track = item.get('track')
                if not track or not track.get('uri'):
                    continue

                # Controleer wanneer de track is toegevoegd
                added_at_str = item.get('added_at')
                if added_at_str:
                    try:
                        # Parse de ISO 8601 datum
                        added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                        # Converteer naar local timezone voor vergelijking
                        if added_at.tzinfo:
                            added_at = added_at.astimezone().replace(tzinfo=None)

                        # Alleen tracks die in de laatste X dagen zijn toegevoegd
                        if added_at < cutoff_date:
                            # Stop met itereren als we voorbij de cutoff datum zijn
                            # (tracks zijn gesorteerd van nieuw naar oud)
                            results = None
                            break
                    except (ValueError, AttributeError):
                        # Als parsing mislukt, negeer deze track
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
        print(f"❌ Spotify API fout bij ophalen tracks: {e}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen tracks: {e}")
        raise
