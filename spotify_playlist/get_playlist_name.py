def get_playlist_name(sp, playlist_id):
    """Fetches the name of a playlist."""
    try:
        playlist_info = sp.playlist(playlist_id, fields='name')
        return playlist_info.get('name', 'Unknown')
    except Exception:
        return None
