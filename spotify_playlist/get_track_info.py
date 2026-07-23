def get_track_info(sp, track_uri):
    """Fetches track information for display."""
    try:
        track = sp.track(track_uri)
        artists = ', '.join([artist['name'] for artist in track['artists']])
        return f"{track['name']} - {artists}"
    except Exception:
        return track_uri
