"""Spotify app settings and cached playlist config from the database."""

APP_NAME = "Short Jack's Release Finder"

from db_store import load_playlists_config

# VUL DIT AAN MET JE EIGEN GEGEVENS!
# Haal deze op van je Spotify Developer Dashboard.
CLIENT_ID = '2e5f7852da3b41f9b42e41ab0659625e'
CLIENT_SECRET = '4ab3ec205047427e9f9d9828287513a6'
# BELANGRIJK: Deze redirect URI MOET exact overeenkomen met wat je hebt ingesteld in je Spotify Developer Dashboard
# Ga naar: https://developer.spotify.com/dashboard -> Je App -> Settings -> Redirect URIs
REDIRECT_URI = 'http://127.0.0.1:8888/'  # Wijzig dit alleen als je het ook in Spotify aanpast!
# Scope moet zowel private als public playlist modificatie rechten bevatten
# user-follow-read is nodig om gevolgde artiesten op te halen
# user-top-read is nodig om meest beluisterde tracks op te halen
# user-read-recently-played is nodig om recent afgespeelde tracks op te halen
SCOPE = (
    'playlist-read-private playlist-read-collaborative playlist-modify-private '
    'playlist-modify-public user-follow-read user-top-read user-read-recently-played'
)
CACHE_FILE = ".spotipy_cache"

playlists_config = load_playlists_config()
MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

# Schakel dit in om nieuwe releases van gevolgde artiesten op te halen
CHECK_ARTIST_RELEASES = True

# Aantal dagen terug om nieuwe releases te zoeken (bijv. laatste 7 dagen = 1 week)
ARTIST_RELEASES_DAYS_BACK = 7
