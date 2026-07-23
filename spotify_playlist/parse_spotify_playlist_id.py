def parse_spotify_playlist_id(text: str) -> str:
    """Extract playlist ID from raw input: plain ID, spotify:playlist:…, or open.spotify.com/playlist/…"""
    s = (text or "").strip()
    if not s:
        return ""
    if s.startswith("spotify:playlist:"):
        return s.replace("spotify:playlist:", "").split("?")[0].strip()
    if "open.spotify.com" in s and "/playlist/" in s:
        tail = s.split("/playlist/", 1)[-1]
        return tail.split("?")[0].split("/")[0].strip()
    return s
