import time

from spotify_playlist.deps import SpotifyException
from spotify_playlist.update_recently_played import update_recently_played


def get_top_tracks_with_counts(sp, time_range='short_term', limit=50):
    """
    Haalt top tracks op met play counts.

    Args:
        sp: Spotify client
        time_range: 'short_term' (laatste 4 weken), 'medium_term' (laatste 6 maanden), 'long_term' (meerdere jaren)
        limit: Aantal tracks om op te halen (max 50)

    Returns:
        tuple: (tracks_with_counts list, elapsed_time in seconds)
    """
    start_time = time.time()
    try:
        # Update eerst de play counts met recent afgespeelde tracks
        play_counts = update_recently_played(sp)

        # Haal top tracks op van Spotify
        top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)

        tracks_with_counts = []
        for idx, track in enumerate(top_tracks['items'], 1):
            uri = track['uri']
            artists = ', '.join([artist['name'] for artist in track.get('artists', [])])

            # Haal play count op uit onze tracking
            play_count = play_counts.get(uri, {}).get('play_count', 0)

            tracks_with_counts.append({
                'rank': idx,
                'name': track.get('name', 'Unknown'),
                'artists': artists,
                'uri': uri,
                'play_count': play_count,
                'popularity': track.get('popularity', 0)
            })

        elapsed_time = time.time() - start_time
        return tracks_with_counts, elapsed_time
    except SpotifyException as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Fout bij ophalen top tracks: {e}")
        if e.http_status == 403:
            print("   Geen rechten om top tracks op te halen. Controleer je scope (user-top-read).")
        return [], elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Onverwachte fout bij ophalen top tracks: {e}")
        return [], elapsed_time
