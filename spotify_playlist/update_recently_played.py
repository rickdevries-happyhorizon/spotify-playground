from datetime import datetime

from db_store import load_play_counts, save_play_counts


def update_recently_played(sp):
    """Update de play counts met recent afgespeelde tracks."""
    try:
        play_counts = load_play_counts()
        current_time = datetime.now().isoformat()

        # Haal recent afgespeelde tracks op (laatste 50)
        results = sp.current_user_recently_played(limit=50)

        for item in results['items']:
            track = item['track']
            if track and track.get('uri'):
                uri = track['uri']
                played_at = item.get('played_at', current_time)

                # Initialiseer track entry als deze niet bestaat
                if uri not in play_counts:
                    play_counts[uri] = {
                        'name': track.get('name', 'Unknown'),
                        'artists': ', '.join([artist['name'] for artist in track.get('artists', [])]),
                        'play_count': 0,
                        'first_played': played_at,
                        'last_played': played_at
                    }

                # Update play count en laatste afspeeldatum
                play_counts[uri]['play_count'] += 1
                play_counts[uri]['last_played'] = played_at

        save_play_counts(play_counts)
        return play_counts
    except Exception as e:
        print(f"⚠️  Fout bij updaten play counts: {e}")
        return load_play_counts()
