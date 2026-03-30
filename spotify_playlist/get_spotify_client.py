import os
import sys
import warnings

from spotify_playlist.config import CACHE_FILE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE
from spotify_playlist.deps import SpotifyException, SpotifyOAuth, spotipy
from spotify_playlist.is_port_available import is_port_available


def get_spotify_client():
    """Authenticeert en retourneert een Spotify client."""
    # Authenticatie
    print("\n🔐 Authenticatie met Spotify...")

    # Controleer of de redirect URI poort beschikbaar is
    redirect_port = int(REDIRECT_URI.split(':')[-1].rstrip('/'))
    if not is_port_available(redirect_port):
        print(f"⚠️  Waarschuwing: Poort {redirect_port} is al in gebruik.")
        print(f"   Zorg dat poort {redirect_port} vrij is, of wijzig REDIRECT_URI in het script")
        print(f"   (en update ook je Spotify Developer Dashboard met de nieuwe redirect URI)")
        print(f"   Huidige redirect URI: {REDIRECT_URI}\n")

    try:
        # Controleer eerst of er al een cached token bestaat
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=CACHE_FILE,
            open_browser=False  # Standaard geen browser openen
        )

        # Probeer een token uit de cache te halen
        token_info = auth_manager.get_cached_token()

        # Controleer of de cached token de juiste scope heeft
        # Als de scope is gewijzigd, moeten we opnieuw authenticeren
        if token_info and 'scope' in token_info:
            cached_scope = set(token_info.get('scope', '').split())
            required_scope = set(SCOPE.split())
            if not required_scope.issubset(cached_scope):
                print("⚠️  Scope is gewijzigd. Cache wordt verwijderd voor nieuwe authenticatie...")
                if os.path.exists(CACHE_FILE):
                    os.remove(CACHE_FILE)
                token_info = None

        # Bepaal of we de browser moeten openen
        needs_browser = False
        if not token_info:
            needs_browser = True
            print("Geen cached token gevonden. Browser wordt geopend voor authenticatie...")
        elif auth_manager.is_token_expired(token_info):
            # Probeer eerst te refreshen zonder browser
            try:
                print("Token verlopen, probeer te refreshen...")
                token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
            except Exception:
                # Refresh mislukt, browser nodig
                needs_browser = True
                print("Token refresh mislukt. Browser wordt geopend voor nieuwe authenticatie...")

        # Als browser nodig is, trigger de OAuth flow
        if needs_browser:
            auth_manager.open_browser = True
            try:
                # Onderdruk deprecation warning voor get_access_token()
                # Het resultaat wordt automatisch gecached door auth_manager
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*get_access_token.*")
                    auth_manager.get_access_token()  # Trigger OAuth flow
            except OSError as e:
                if "Address already in use" in str(e) or e.errno == 48:
                    print(f"\n❌ Fout: Poort {REDIRECT_URI.split(':')[-1].rstrip('/')} is al in gebruik.")
                    print("Mogelijke oplossingen:")
                    print("  1. Sluit andere applicaties die deze poort gebruiken")
                    print("  2. Wijzig REDIRECT_URI in het script naar een andere poort (bijv. 8889)")
                    print("  3. Update ook de redirect URI in je Spotify Developer Dashboard")
                    print(f"\nHuidige redirect URI: {REDIRECT_URI}")
                    sys.exit(1)
                else:
                    raise

        # Maak Spotify client met de auth manager
        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Test authenticatie door gebruikersinfo op te halen
        user = sp.current_user()
        print(f"✅ Ingelogd als: {user['display_name']} ({user['id']})")
        return sp

    except SpotifyException as e:
        error_msg = str(e)
        print(f"❌ Authenticatie mislukt: {error_msg}")

        if "INVALID_CLIENT" in error_msg or "Invalid redirect URI" in error_msg:
            print("\n⚠️  Redirect URI komt niet overeen met Spotify instellingen!")
            print(f"   Huidige redirect URI in script: {REDIRECT_URI}")
            print("\n   Oplossing:")
            print("   1. Ga naar: https://developer.spotify.com/dashboard")
            print("   2. Selecteer je app")
            print("   3. Klik op 'Settings'")
            print("   4. Voeg deze redirect URI toe aan 'Redirect URIs':")
            print(f"      {REDIRECT_URI}")
            print("   5. Klik op 'Add' en dan 'Save'")
            print("   6. Voer het script opnieuw uit")
        else:
            print("Controleer je CLIENT_ID, CLIENT_SECRET en REDIRECT_URI.")
        sys.exit(1)
    except OSError as e:
        if "Address already in use" in str(e) or e.errno == 48:
            port = REDIRECT_URI.split(':')[-1].rstrip('/')
            print(f"\n❌ Fout: Poort {port} is al in gebruik.")
            print("Mogelijke oplossingen:")
            print("  1. Sluit andere applicaties die deze poort gebruiken")
            print("  2. Wijzig REDIRECT_URI in het script naar een andere poort (bijv. 8889)")
            print("  3. Update ook de redirect URI in je Spotify Developer Dashboard")
            print(f"\nHuidige redirect URI: {REDIRECT_URI}")
        else:
            print(f"❌ Onverwachte fout bij authenticatie: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Onverwachte fout bij authenticatie: {e}")
        sys.exit(1)
