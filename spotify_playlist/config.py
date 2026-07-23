"""Spotify app settings and cached playlist config from the database."""

APP_NAME = "Short Jack's Release Finder"

from db_store import load_playlists_config

# FILL IN YOUR OWN CREDENTIALS!
# Get these from your Spotify Developer Dashboard.
CLIENT_ID = '2e5f7852da3b41f9b42e41ab0659625e'
CLIENT_SECRET = '4ab3ec205047427e9f9d9828287513a6'
# IMPORTANT: This redirect URI MUST exactly match what you set in your Spotify Developer Dashboard
# Go to: https://developer.spotify.com/dashboard -> Your App -> Settings -> Redirect URIs
REDIRECT_URI = 'http://127.0.0.1:8888/'  # Only change this if you also update it in Spotify!
# Scope must include both private and public playlist modification permissions
# user-follow-read is needed to fetch followed artists
# user-top-read is needed to fetch most listened tracks
# user-read-recently-played is needed to fetch recently played tracks
SCOPE = (
    'playlist-read-private playlist-read-collaborative playlist-modify-private '
    'playlist-modify-public user-follow-read user-top-read user-read-recently-played'
)
CACHE_FILE = ".spotipy_cache"

playlists_config = load_playlists_config()
MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

# Enable this to fetch new releases from followed artists
CHECK_ARTIST_RELEASES = True

# Number of days back to search for new releases (e.g. last 7 days = 1 week)
ARTIST_RELEASES_DAYS_BACK = 7

# Directory with WAV/AIFF files for metadata tagging (optional)
WAV_METADATA_DIR = '/Volumes/ShortJack/music'

# Directory with WAV/AIFF files for Spotify cover art (optional)
SPOTIFY_COVER_ART_DIR = '/Volumes/ShortJack/music'

# Directory for YouTube to AIFF downloads (optional)
YOUTUBE_DOWNLOAD_DIR = '/Users/rickdevries/downloads'

# Text file with YouTube URLs, one per line (optional)
YOUTUBE_URLS_FILE = 'youtube_urls.txt'
