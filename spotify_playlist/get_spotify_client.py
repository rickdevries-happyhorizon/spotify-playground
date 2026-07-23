import os
import sys
import warnings

from spotify_playlist.config import CACHE_FILE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE
from spotify_playlist.deps import SpotifyException, SpotifyOAuth, require_spotipy, spotipy
from spotify_playlist.is_port_available import is_port_available
from spotify_playlist.loading_progress import loading_bar


def _clear_spotify_cache() -> None:
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)


def _is_revoked_token_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "invalid_grant" in message or "refresh token revoked" in message


def get_spotify_client():
    """Authenticates and returns a Spotify client."""
    require_spotipy()

    # Authentication
    print("\n🔐 Authenticating with Spotify...")

    # Check if the redirect URI port is available
    redirect_port = int(REDIRECT_URI.split(':')[-1].rstrip('/'))
    if not is_port_available(redirect_port):
        print(f"⚠️  Warning: Port {redirect_port} is already in use.")
        print(f"   Make sure port {redirect_port} is free, or change REDIRECT_URI in the script")
        print(f"   (and also update your Spotify Developer Dashboard with the new redirect URI)")
        print(f"   Current redirect URI: {REDIRECT_URI}\n")

    try:
        # First check if a cached token already exists
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=CACHE_FILE,
            open_browser=False  # Do not open browser by default
        )

        # Try to get a token from the cache
        token_info = auth_manager.get_cached_token()

        # Check if the cached token has the correct scope
        # If the scope has changed, we need to re-authenticate
        if token_info and 'scope' in token_info:
            cached_scope = set(token_info.get('scope', '').split())
            required_scope = set(SCOPE.split())
            if not required_scope.issubset(cached_scope):
                print("⚠️  Scope has changed. Clearing cache for new authentication...")
                if os.path.exists(CACHE_FILE):
                    os.remove(CACHE_FILE)
                token_info = None

        # Determine whether we need to open the browser
        needs_browser = False
        if not token_info:
            needs_browser = True
            print("No cached token found. Opening browser for authentication...")
        elif auth_manager.is_token_expired(token_info):
            # Try refreshing first without the browser
            try:
                print("Token expired, attempting to refresh...")
                with loading_bar("Refreshing token..."):
                    token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
            except Exception as e:
                if _is_revoked_token_error(e):
                    print("⚠️  Refresh token revoked. Clearing cache for new login...")
                    _clear_spotify_cache()
                    token_info = None
                    auth_manager = SpotifyOAuth(
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=CACHE_FILE,
                        open_browser=False,
                    )
                needs_browser = True
                print("Opening browser for new authentication...")

        # If browser is needed, trigger the OAuth flow
        if needs_browser:
            auth_manager.open_browser = True
            try:
                # Suppress deprecation warning for get_access_token()
                # The result is automatically cached by auth_manager
                with loading_bar("Authenticating in browser..."):
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*get_access_token.*")
                        auth_manager.get_access_token()  # Trigger OAuth flow
            except OSError as e:
                if "Address already in use" in str(e) or e.errno == 48:
                    print(f"\n❌ Error: Port {REDIRECT_URI.split(':')[-1].rstrip('/')} is already in use.")
                    print("Possible solutions:")
                    print("  1. Close other applications using this port")
                    print("  2. Change REDIRECT_URI in the script to a different port (e.g. 8889)")
                    print("  3. Also update the redirect URI in your Spotify Developer Dashboard")
                    print(f"\nCurrent redirect URI: {REDIRECT_URI}")
                    sys.exit(1)
                else:
                    raise

        # Create Spotify client with the auth manager
        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Test authentication by fetching user info
        try:
            with loading_bar("Connecting to Spotify..."):
                user = sp.current_user()
        except Exception as e:
            if _is_revoked_token_error(e):
                print("⚠️  Spotify session expired. Logging in again via browser...")
                _clear_spotify_cache()
                auth_manager = SpotifyOAuth(
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET,
                    redirect_uri=REDIRECT_URI,
                    scope=SCOPE,
                    cache_path=CACHE_FILE,
                    open_browser=True,
                )
                with loading_bar("Authenticating in browser..."):
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            category=DeprecationWarning,
                            message=".*get_access_token.*",
                        )
                        auth_manager.get_access_token()
                sp = spotipy.Spotify(auth_manager=auth_manager)
                with loading_bar("Connecting to Spotify..."):
                    user = sp.current_user()
            else:
                raise
        print(f"✅ Logged in as: {user['display_name']} ({user['id']})")
        return sp

    except SpotifyException as e:
        error_msg = str(e)
        print(f"❌ Authentication failed: {error_msg}")

        if "INVALID_CLIENT" in error_msg or "Invalid redirect URI" in error_msg:
            print("\n⚠️  Redirect URI does not match Spotify settings!")
            print(f"   Current redirect URI in script: {REDIRECT_URI}")
            print("\n   Solution:")
            print("   1. Go to: https://developer.spotify.com/dashboard")
            print("   2. Select your app")
            print("   3. Click 'Settings'")
            print("   4. Add this redirect URI to 'Redirect URIs':")
            print(f"      {REDIRECT_URI}")
            print("   5. Click 'Add' and then 'Save'")
            print("   6. Run the script again")
        else:
            print("Check your CLIENT_ID, CLIENT_SECRET, and REDIRECT_URI.")
        sys.exit(1)
    except OSError as e:
        if "Address already in use" in str(e) or e.errno == 48:
            port = REDIRECT_URI.split(':')[-1].rstrip('/')
            print(f"\n❌ Error: Port {port} is already in use.")
            print("Possible solutions:")
            print("  1. Close other applications using this port")
            print("  2. Change REDIRECT_URI in the script to a different port (e.g. 8889)")
            print("  3. Also update the redirect URI in your Spotify Developer Dashboard")
            print(f"\nCurrent redirect URI: {REDIRECT_URI}")
        else:
            print(f"❌ Unexpected error during authentication: {e}")
        sys.exit(1)
    except Exception as e:
        if _is_revoked_token_error(e):
            print("❌ Spotify refresh token has been revoked.")
            print("   Delete .spotipy_cache and restart the app to log in again.")
            _clear_spotify_cache()
        else:
            print(f"❌ Unexpected error during authentication: {e}")
        sys.exit(1)
