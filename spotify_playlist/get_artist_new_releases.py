from datetime import datetime, timedelta

from spotify_playlist.deps import SpotifyException


def get_artist_new_releases(sp, artist_id, days_back=30):
    """Haalt nieuwe releases van een artiest op binnen het opgegeven aantal dagen."""
    new_tracks = {}
    try:
        # Bereken de datum X dagen geleden
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Haal albums van de artiest op
        albums = sp.artist_albums(artist_id, album_type='album,single', limit=50)

        for album in albums['items']:
            # Controleer release datum
            release_date = album.get('release_date', '')
            if not release_date:
                continue

            # Parse release datum (kan YYYY, YYYY-MM, of YYYY-MM-DD zijn)
            try:
                if len(release_date) == 4:  # Alleen jaar
                    release_dt = datetime(int(release_date), 1, 1)
                elif len(release_date) == 7:  # YYYY-MM
                    year, month = release_date.split('-')
                    release_dt = datetime(int(year), int(month), 1)
                else:  # YYYY-MM-DD
                    release_dt = datetime.strptime(release_date, '%Y-%m-%d')

                # Alleen albums die recent zijn uitgebracht
                if release_dt >= cutoff_date:
                    # Haal tracks van het album op
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
                # Skip albums met ongeldige datum
                continue

        return new_tracks
    except SpotifyException as e:
        print(f"❌ Spotify API fout bij ophalen releases voor artiest {artist_id}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen releases: {e}")
        return {}
