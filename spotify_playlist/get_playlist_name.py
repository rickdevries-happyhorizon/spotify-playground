def get_playlist_name(sp, playlist_id):
    """Haalt de naam van een playlist op."""
    try:
        playlist_info = sp.playlist(playlist_id, fields='name')
        return playlist_info.get('name', 'Onbekend')
    except Exception:
        return None
