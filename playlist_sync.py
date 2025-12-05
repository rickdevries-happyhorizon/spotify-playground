import json
import os
import sys
import socket
import warnings
import csv
import time
from datetime import datetime, timedelta

# Controleer of spotipy geïnstalleerd is
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from spotipy.exceptions import SpotifyException
except ImportError as e:
    print("❌ Fout: spotipy module niet gevonden!")
    print("\n   Oplossing:")
    print("   1. Gebruik het shell script: ./run_sync.sh")
    print("   2. Of activeer eerst de virtual environment:")
    print("      source path/to/venv/bin/activate")
    print("      python3 playlist_sync.py")
    print("   3. Of installeer spotipy:")
    print("      pip install spotipy")
    sys.exit(1)

# =========================================================================
# 1. Configuratie
# =========================================================================

# VUL DIT AAN MET JE EIGEN GEGEVENS!
# Haal deze op van je Spotify Developer Dashboard.
CLIENT_ID = '2e5f7852da3b41f9b42e41ab0659625e'
CLIENT_SECRET = '4ab3ec205047427e9f9d9828287513a6'
# BELANGRIJK: Deze redirect URI MOET exact overeenkomen met wat je hebt ingesteld in je Spotify Developer Dashboard
# Ga naar: https://developer.spotify.com/dashboard -> Je App -> Settings -> Redirect URIs
REDIRECT_URI = 'http://127.0.0.1:8888/' # Wijzig dit alleen als je het ook in Spotify aanpast!
# Scope moet zowel private als public playlist modificatie rechten bevatten
# user-follow-read is nodig om gevolgde artiesten op te halen
# user-top-read is nodig om meest beluisterde tracks op te halen
# user-read-recently-played is nodig om recent afgespeelde tracks op te halen
SCOPE = 'playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-follow-read user-top-read user-read-recently-played'
CACHE_FILE = ".spotipy_cache"

# Configuratie bestand voor playlists
PLAYLISTS_CONFIG_FILE = 'playlists_config.json'

def load_playlists_config():
    """Laadt de playlist configuratie uit het JSON-bestand."""
    if not os.path.exists(PLAYLISTS_CONFIG_FILE):
        # Maak een standaard configuratie bestand aan met huidige waarden
        default_config = {
            "source_playlists": [
                "0GeM8Z4TU46H9DwlQ2R6Jy",
                "6Pbk82RPOKWD7k6dNcqq9f",
                "0HoiaN3OGkIZLJc7OhcCaG",
                "69j6wZIJgNvmllNqK6FLK7",
                "85f96f89b95848ba",
                "49jfZzu0Zk8zz2SyJnsbMW",
                "6zOWXbfnmNcR5ms1hOpLOQ",
                "4zqyutXjSPo9KoJ3XnWR0J",
                "27a5auxbr7BIYtCe67GMPy"
            ],
            "destination_playlist": "276Ghex8uAA30DmuQoMzhg"
        }
        with open(PLAYLISTS_CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"⚠️  Configuratie bestand {PLAYLISTS_CONFIG_FILE} aangemaakt.")
        print(f"   Je kunt nu playlist ID's beheren via dit bestand.")
        return default_config
    
    try:
        with open(PLAYLISTS_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Valideer configuratie
            if 'source_playlists' not in config:
                config['source_playlists'] = []
            if 'destination_playlist' not in config:
                config['destination_playlist'] = ''
            return config
    except Exception as e:
        print(f"❌ Fout bij laden playlist configuratie: {e}")
        return {"source_playlists": [], "destination_playlist": ""}

# Laad playlist configuratie bij start
playlists_config = load_playlists_config()
MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

# Bestand waarin de status van de laatst gesynchroniseerde nummers wordt opgeslagen
HISTORISCHE_DATA_FILE = 'historische_data.json'

# Bestand voor het bijhouden van afspeelgeschiedenis en play counts
PLAY_COUNTS_FILE = 'play_counts.json'

# Schakel dit in om nieuwe releases van gevolgde artiesten op te halen
CHECK_ARTIST_RELEASES = True

# Aantal dagen terug om nieuwe releases te zoeken (bijv. laatste 7 dagen = 1 week)
ARTIST_RELEASES_DAYS_BACK = 7

def is_port_available(port):
    """Controleer of een poort beschikbaar is."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False

def load_historical_data():
    """Laadt de eerder opgeslagen nummers uit het JSON-bestand."""
    if not os.path.exists(HISTORISCHE_DATA_FILE):
        print("Geen historisch bestand gevonden. Start met lege gegevens.")
        return {pl_id: set() for pl_id in BRON_PLAYLISTS}

    try:
        with open(HISTORISCHE_DATA_FILE, 'r') as f:
            geladen_data = json.load(f)
            # Converteer de opgeslagen lijsten terug naar sets
            return {k: set(v) for k, v in geladen_data.items()}
    except Exception as e:
        print(f"Fout bij laden historisch bestand: {e}")
        return {pl_id: set() for pl_id in BRON_PLAYLISTS}

def save_historical_data(data):
    """Slaat de huidige nummers op in het JSON-bestand."""
    # Converteer sets naar lijsten voor JSON-serialisatie
    op_te_slaan_data = {k: list(v) for k, v in data.items()}
    with open(HISTORISCHE_DATA_FILE, 'w') as f:
        json.dump(op_te_slaan_data, f, indent=4)
    print(f"\n✅ Historische gegevens opgeslagen in {HISTORISCHE_DATA_FILE}")

def get_recent_playlist_tracks(sp, playlist_id, days_back=7, return_track_info=False):
    """Haalt alleen tracks op die in de laatste X dagen zijn toegevoegd aan de playlist.
    
    Args:
        sp: Spotify client
        playlist_id: ID van de playlist
        days_back: Aantal dagen terug om te kijken (standaard 7)
        return_track_info: Als True, retourneert ook track informatie (naam, artiesten)
    
    Returns:
        Als return_track_info=False: set van track URIs
        Als return_track_info=True: dict met URI als key en {'name': ..., 'artists': ...} als value
    """
    track_data = {} if return_track_info else set()
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        # Haal playlist items op met added_at datum
        results = sp.playlist_items(playlist_id, fields='items.added_at,items.track.uri,items.track.name,items.track.artists,next', limit=100)
        
        while results:
            for item in results['items']:
                # Controleer of track bestaat
                track = item.get('track')
                if not track or not track.get('uri'):
                    continue
                
                # Controleer wanneer de track is toegevoegd
                added_at_str = item.get('added_at')
                if added_at_str:
                    try:
                        # Parse de ISO 8601 datum
                        added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                        # Converteer naar local timezone voor vergelijking
                        if added_at.tzinfo:
                            added_at = added_at.astimezone().replace(tzinfo=None)
                        
                        # Alleen tracks die in de laatste X dagen zijn toegevoegd
                        if added_at < cutoff_date:
                            # Stop met itereren als we voorbij de cutoff datum zijn
                            # (tracks zijn gesorteerd van nieuw naar oud)
                            results = None
                            break
                    except (ValueError, AttributeError):
                        # Als parsing mislukt, negeer deze track
                        continue
                
                uri = track['uri']
                if return_track_info:
                    artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                    track_data[uri] = {
                        'name': track.get('name', 'Unknown'),
                        'artists': artists
                    }
                else:
                    track_data.add(uri)
            
            if results:
                results = sp.next(results) if results.get('next') else None
        
        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API fout bij ophalen tracks: {e}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen tracks: {e}")
        raise

def get_all_playlist_tracks(sp, playlist_id, return_track_info=False):
    """Haalt alle nummers (tracks) URI's van een afspeellijst op (houdt rekening met paginering).
    
    Args:
        sp: Spotify client
        playlist_id: ID van de playlist
        return_track_info: Als True, retourneert ook track informatie (naam, artiesten)
    
    Returns:
        Als return_track_info=False: set van track URIs
        Als return_track_info=True: dict met URI als key en {'name': ..., 'artists': ...} als value
    """
    track_data = {} if return_track_info else set()
    try:
        results = sp.playlist_items(playlist_id, fields='items.track.uri,items.track.name,items.track.artists,next', limit=100)
        
        while results:
            for item in results['items']:
                # Controleer of 'track' bestaat om te filteren op potentieel lege items
                track = item.get('track')
                if track and track.get('uri'):
                    uri = track['uri']
                    if return_track_info:
                        artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                        track_data[uri] = {
                            'name': track.get('name', 'Unknown'),
                            'artists': artists
                        }
                    else:
                        track_data.add(uri)
            
            results = sp.next(results) if results.get('next') else None
        
        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API fout bij ophalen tracks: {e}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen tracks: {e}")
        raise

def get_track_info(sp, track_uri):
    """Haalt track informatie op voor weergave."""
    try:
        track = sp.track(track_uri)
        artists = ', '.join([artist['name'] for artist in track['artists']])
        return f"{track['name']} - {artists}"
    except:
        return track_uri

def get_followed_artists(sp):
    """Haalt alle gevolgde artiesten op."""
    artist_ids = []
    try:
        results = sp.current_user_followed_artists(limit=50)
        
        while results:
            for artist in results['artists']['items']:
                artist_ids.append(artist['id'])
            
            # Check if there are more artists to fetch
            if results['artists'].get('next'):
                # Get the cursor for pagination
                after = results['artists']['cursors'].get('after')
                if after:
                    results = sp.current_user_followed_artists(limit=50, after=after)
                else:
                    break
            else:
                break
        
        return artist_ids
    except SpotifyException as e:
        print(f"❌ Spotify API fout bij ophalen gevolgde artiesten: {e}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen gevolgde artiesten: {e}")
        raise

def get_artist_new_releases(sp, artist_id, days_back=30):
    """Haalt nieuwe releases van een artiest op binnen het opgegeven aantal dagen."""
    new_tracks = {}
    try:
        # Bereken de datum X dagen geleden
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Haal albums van de artiest op
        albums = sp.artist_albums(artist_id, album_type='album,single', limit=50)
        
        for album in albums['items']:
            # Controleer release datum
            release_date = album.get('release_date', '')
            if not release_date:
                continue
            
            # Parse release datum (kan YYYY, YYYY-MM, of YYYY-MM-DD zijn)
            try:
                if len(release_date) == 4:  # Alleen jaar
                    release_dt = datetime(int(release_date), 1, 1)
                elif len(release_date) == 7:  # YYYY-MM
                    year, month = release_date.split('-')
                    release_dt = datetime(int(year), int(month), 1)
                else:  # YYYY-MM-DD
                    release_dt = datetime.strptime(release_date, '%Y-%m-%d')
                
                # Alleen albums die recent zijn uitgebracht
                if release_dt >= cutoff_date:
                    # Haal tracks van het album op
                    album_tracks = sp.album_tracks(album['id'])
                    for track_item in album_tracks['items']:
                        if track_item and track_item.get('uri'):
                            uri = track_item['uri']
                            artists = ', '.join([artist['name'] for artist in track_item.get('artists', [])])
                            new_tracks[uri] = {
                                'name': track_item.get('name', 'Unknown'),
                                'artists': artists,
                                'album': album.get('name', 'Unknown'),
                                'release_date': release_date
                            }
            except (ValueError, TypeError) as e:
                # Skip albums met ongeldige datum
                continue
        
        return new_tracks
    except SpotifyException as e:
        print(f"❌ Spotify API fout bij ophalen releases voor artiest {artist_id}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen releases: {e}")
        return {}

def get_all_artist_releases(sp, days_back=30):
    """Haalt nieuwe releases op van alle gevolgde artiesten."""
    print(f"\n🎵 Controleer nieuwe releases van gevolgde artiesten (laatste {days_back} dagen)...")
    
    # Haal gevolgde artiesten op
    try:
        artist_ids = get_followed_artists(sp)
        print(f"   Gevonden {len(artist_ids)} gevolgde artiesten")
    except Exception as e:
        print(f"❌ Kon gevolgde artiesten niet ophalen: {e}")
        return {}
    
    all_new_releases = {}
    checked_count = 0
    
    # Haal nieuwe releases op voor elke artiest
    for artist_id in artist_ids:
        try:
            artist_info = sp.artist(artist_id)
            artist_name = artist_info['name']
            checked_count += 1
            
            if checked_count % 10 == 0:
                print(f"   Gecontroleerd {checked_count}/{len(artist_ids)} artiesten...")
            
            releases = get_artist_new_releases(sp, artist_id, days_back)
            if releases:
                print(f"   ✅ {artist_name}: {len(releases)} nieuwe releases gevonden")
                all_new_releases.update(releases)
        except Exception as e:
            print(f"   ⚠️  Fout bij controleren artiest {artist_id}: {e}")
            continue
    
    print(f"\n   Totaal {len(all_new_releases)} nieuwe releases gevonden van {checked_count} artiesten")
    return all_new_releases

def load_play_counts():
    """Laadt de play counts uit het JSON-bestand."""
    if not os.path.exists(PLAY_COUNTS_FILE):
        return {}
    
    try:
        with open(PLAY_COUNTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Fout bij laden play counts: {e}")
        return {}

def save_play_counts(play_counts):
    """Slaat de play counts op in het JSON-bestand."""
    try:
        with open(PLAY_COUNTS_FILE, 'w') as f:
            json.dump(play_counts, f, indent=4)
    except Exception as e:
        print(f"Fout bij opslaan play counts: {e}")

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

# ANSI color codes voor terminal kleuren
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def get_rank_color(rank):
    """Retourneert een kleur gebaseerd op de ranking."""
    if rank == 1:
        return f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}🥇"
    elif rank == 2:
        return f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🥈"
    elif rank == 3:
        return f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🥉"
    elif rank <= 5:
        return f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{rank}"
    elif rank <= 7:
        return f"{Colors.BOLD}{Colors.CYAN}{rank}"
    else:
        return f"{Colors.BRIGHT_BLUE}{rank}"

def get_popularity_bar(popularity):
    """Maakt een visuele balk voor populariteit."""
    bar_length = 20
    filled = int((popularity / 100) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    if popularity >= 80:
        color = Colors.BRIGHT_GREEN
    elif popularity >= 60:
        color = Colors.BRIGHT_YELLOW
    elif popularity >= 40:
        color = Colors.YELLOW
    else:
        color = Colors.BRIGHT_RED
    
    return f"{color}{bar}{Colors.RESET}"

def show_top_tracks(sp):
    """Toont meest beluisterde tracks voor verschillende periodes."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎵  Meest Beluisterde Tracks  🎵{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*70}{Colors.RESET}")
    
    print(f"\n{Colors.BRIGHT_WHITE}Kies een periode:{Colors.RESET}")
    print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Deze week {Colors.DIM}(laatste 4 weken){Colors.RESET}")
    print(f"  {Colors.BRIGHT_BLUE}2.{Colors.RESET} Deze maand {Colors.DIM}(laatste 6 maanden){Colors.RESET}")
    print(f"  {Colors.BRIGHT_MAGENTA}3.{Colors.RESET} Dit jaar {Colors.DIM}(meerdere jaren){Colors.RESET}")
    print(f"  {Colors.BRIGHT_RED}0.{Colors.RESET} Terug naar hoofdmenu")
    print(f"\n{Colors.DIM}{'-'*70}{Colors.RESET}")
    
    while True:
        try:
            choice = input(f"{Colors.BRIGHT_CYAN}Voer je keuze in (0-3): {Colors.RESET}").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                time_range = 'short_term'
                period_name = "Deze week"
                period_subtitle = "Laatste 4 weken"
                period_emoji = "📅"
                period_color = Colors.BRIGHT_GREEN
            elif choice == '2':
                time_range = 'medium_term'
                period_name = "Deze maand"
                period_subtitle = "Laatste 6 maanden"
                period_emoji = "📆"
                period_color = Colors.BRIGHT_BLUE
            elif choice == '3':
                time_range = 'long_term'
                period_name = "Dit jaar"
                period_subtitle = "Meerdere jaren"
                period_emoji = "🎯"
                period_color = Colors.BRIGHT_MAGENTA
            else:
                print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze. Voer 0, 1, 2 of 3 in.{Colors.RESET}")
                continue
            
            print(f"\n{period_color}{Colors.BOLD}{'═'*70}{Colors.RESET}")
            print(f"{period_color}{Colors.BOLD}  {period_emoji}  {period_name}  {Colors.DIM}({period_subtitle}){Colors.RESET}")
            print(f"{period_color}{Colors.BOLD}{'═'*70}{Colors.RESET}")
            print(f"{Colors.DIM}⏳ Tracks ophalen...{Colors.RESET}")
            
            tracks, elapsed_time = get_top_tracks_with_counts(sp, time_range=time_range, limit=10)
            
            if tracks:
                print(f"{Colors.BRIGHT_GREEN}✅ Tracks opgehaald in {Colors.BOLD}{elapsed_time:.2f}{Colors.RESET}{Colors.BRIGHT_GREEN} seconden{Colors.RESET}\n")
                
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╔{'═'*68}╗{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🏆  TOP {len(tracks)} TRACKS  🏆{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-20)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╠{'═'*68}╣{Colors.RESET}")
                
                for track in tracks:
                    rank_icon = get_rank_color(track['rank'])
                    play_count_str = f"{Colors.BRIGHT_GREEN}{track['play_count']}x{Colors.RESET}" if track['play_count'] > 0 else f"{Colors.DIM}Niet getrackt{Colors.RESET}"
                    popularity_bar = get_popularity_bar(track['popularity'])
                    
                    # Track info
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {rank_icon}{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}{track['artists']}{Colors.RESET}")
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_CYAN}└─{Colors.RESET} {Colors.CYAN}{track['name']}{Colors.RESET}")
                    
                    # Stats
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.DIM}├─{Colors.RESET} Afspeelcount: {play_count_str}")
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.DIM}└─{Colors.RESET} Populariteit: {popularity_bar} {Colors.BRIGHT_WHITE}{track['popularity']}/100{Colors.RESET}")
                    
                    if track != tracks[-1]:
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╚{'═'*68}╝{Colors.RESET}\n")
            else:
                print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen tracks gevonden {Colors.DIM}(opgehaald in {elapsed_time:.2f} seconden){Colors.RESET}.")
            
            # Vraag of gebruiker nog een periode wil zien
            again = input(f"{Colors.BRIGHT_CYAN}Nog een periode bekijken? {Colors.DIM}(j/n): {Colors.RESET}").strip().lower()
            if again != 'j':
                break
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Terug naar hoofdmenu...{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout: {e}{Colors.RESET}")

def export_playlist_to_csv(sp, playlist_id, output_file=None):
    """Exporteert een playlist naar een CSV bestand."""
    try:
        # Haal playlist informatie op
        playlist_info = sp.playlist(playlist_id, fields='name,owner')
        playlist_name = playlist_info['name']
        print(f"\n📋 Exporteer playlist: {playlist_name}")
        
        # Genereer bestandsnaam als niet opgegeven
        if not output_file:
            # Maak bestandsnaam veilig voor bestandssysteem
            safe_name = "".join(c for c in playlist_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            output_file = f"playlist_{safe_name}_{playlist_id[:8]}.csv"
        
        # Haal alle tracks op met volledige informatie
        tracks_data = []
        results = sp.playlist_items(playlist_id, fields='items.track,next', limit=100)
        
        while results:
            for item in results['items']:
                track = item.get('track')
                if track and track.get('uri'):
                    # Haal volledige track informatie op
                    try:
                        full_track = sp.track(track['id'])
                        artists = ', '.join([artist['name'] for artist in full_track.get('artists', [])])
                        track_name = full_track.get('name', 'Unknown')
                        
                        tracks_data.append({
                            'Track': f"{artists} - {track_name}"
                        })
                    except Exception as e:
                        # Fallback als volledige track info niet beschikbaar is
                        artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                        track_name = track.get('name', 'Unknown')
                        
                        tracks_data.append({
                            'Track': f"{artists} - {track_name}"
                        })
            
            results = sp.next(results) if results.get('next') else None
        
        # Schrijf naar CSV
        if tracks_data:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Track']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tracks_data)
            
            print(f"✅ {len(tracks_data)} tracks geëxporteerd naar: {output_file}")
            print(f"   Bestandslocatie: {os.path.abspath(output_file)}")
        else:
            print("⚠️  Geen tracks gevonden in deze playlist.")
        
    except SpotifyException as e:
        print(f"❌ Fout bij exporteren playlist: {e}")
        if e.http_status == 404:
            print("   Playlist niet gevonden. Controleer of de playlist ID correct is.")
        elif e.http_status == 403:
            print("   Geen toegang tot deze playlist. Controleer je rechten.")
    except Exception as e:
        print(f"❌ Onverwachte fout bij exporteren: {e}")

def show_menu():
    """Toont het hoofdmenu en retourneert de keuze van de gebruiker."""
    print("\n" + "="*60)
    print("🎵 Spotify Playlist Manager")
    print("="*60)
    print("\nKies een optie:")
    print("  1. Synchroniseer playlists (check bron-playlists)")
    print("  2. Haal nieuwe releases op van gevolgde artiesten")
    print("  3. Synchroniseer alles (playlists + artiest releases)")
    print("  4. Exporteer playlist naar CSV")
    print("  5. Toon meest beluisterde tracks (week/maand/jaar)")
    print("  6. Beheer playlist configuratie")
    print("  0. Afsluiten")
    print("\n" + "-"*60)
    
    while True:
        try:
            choice = input("Voer je keuze in (0-6): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6']:
                return int(choice)
            else:
                print("❌ Ongeldige keuze. Voer 0, 1, 2, 3, 4, 5 of 6 in.")
        except KeyboardInterrupt:
            print("\n\nAfsluiten...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Fout: {e}")

def get_playlist_name(sp, playlist_id):
    """Haalt de naam van een playlist op."""
    try:
        playlist_info = sp.playlist(playlist_id, fields='name')
        return playlist_info.get('name', 'Onbekend')
    except:
        return None

def manage_playlists_config():
    """Beheert de playlist configuratie via een interactief menu."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}⚙️  Playlist Configuratie Beheer  ⚙️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")
    
    # Authenticeer voor het ophalen van playlist namen
    sp = None
    try:
        sp = get_spotify_client()
    except:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Kan niet authenticeren. Playlist namen worden niet getoond.{Colors.RESET}\n")
    
    while True:
        # Laad huidige configuratie
        config = load_playlists_config()
        source_playlists = config.get('source_playlists', [])
        destination_playlist = config.get('destination_playlist', '')
        
        print(f"{Colors.BRIGHT_WHITE}Huidige configuratie:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_CYAN}Bron-playlists ({len(source_playlists)}):{Colors.RESET}")
        if source_playlists:
            for idx, pl_id in enumerate(source_playlists, 1):
                if sp:
                    playlist_name = get_playlist_name(sp, pl_id)
                    if playlist_name:
                        print(f"    {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                    else:
                        print(f"    {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                else:
                    print(f"    {idx}. {pl_id}")
        else:
            print(f"    {Colors.DIM}(geen){Colors.RESET}")
        
        print(f"\n  {Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET}")
        if destination_playlist:
            if sp:
                playlist_name = get_playlist_name(sp, destination_playlist)
                if playlist_name:
                    print(f"    {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({destination_playlist}){Colors.RESET}")
                else:
                    print(f"    {Colors.DIM}{destination_playlist} (niet gevonden){Colors.RESET}")
            else:
                print(f"    {destination_playlist}")
        else:
            print(f"    {Colors.DIM}(niet ingesteld){Colors.RESET}")
        
        print(f"\n{Colors.BRIGHT_WHITE}Wat wil je doen?{Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Voeg bron-playlist toe")
        print(f"  {Colors.BRIGHT_RED}2.{Colors.RESET} Verwijder bron-playlist")
        print(f"  {Colors.BRIGHT_BLUE}3.{Colors.RESET} Stel doel-playlist in")
        print(f"  {Colors.BRIGHT_YELLOW}4.{Colors.RESET} Toon alle playlists")
        print(f"  {Colors.DIM}0.{Colors.RESET} Terug naar hoofdmenu")
        print(f"\n{Colors.DIM}{'-'*70}{Colors.RESET}")
        
        try:
            action = input(f"{Colors.BRIGHT_CYAN}Voer je keuze in (0-4): {Colors.RESET}").strip()
            
            if action == '0':
                break
            elif action == '1':
                # Voeg bron-playlist toe
                playlist_id = input(f"{Colors.BRIGHT_GREEN}Voer playlist ID in om toe te voegen: {Colors.RESET}").strip()
                if playlist_id and playlist_id not in source_playlists:
                    # Probeer playlist naam op te halen
                    playlist_name = None
                    if sp:
                        print(f"{Colors.DIM}⏳ Playlist informatie ophalen...{Colors.RESET}")
                        playlist_name = get_playlist_name(sp, playlist_id)
                    
                    if playlist_name:
                        print(f"{Colors.BRIGHT_CYAN}   Gevonden: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                        confirm = input(f"{Colors.BRIGHT_GREEN}Toevoegen? (j/n): {Colors.RESET}").strip().lower()
                        if confirm != 'j':
                            print(f"{Colors.DIM}Geannuleerd.{Colors.RESET}\n")
                            continue
                    
                    source_playlists.append(playlist_id)
                    config['source_playlists'] = source_playlists
                    with open(PLAYLISTS_CONFIG_FILE, 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    if playlist_name:
                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{playlist_name}' toegevoegd!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist toegevoegd!{Colors.RESET}\n")
                elif playlist_id in source_playlists:
                    playlist_name = None
                    if sp:
                        playlist_name = get_playlist_name(sp, playlist_id)
                    if playlist_name:
                        print(f"{Colors.BRIGHT_YELLOW}⚠️  Deze playlist ({playlist_name}) staat al in de lijst.{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_YELLOW}⚠️  Deze playlist staat al in de lijst.{Colors.RESET}\n")
                else:
                    print(f"{Colors.BRIGHT_RED}❌ Ongeldige playlist ID.{Colors.RESET}\n")
            
            elif action == '2':
                # Verwijder bron-playlist
                if not source_playlists:
                    print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen playlists om te verwijderen.{Colors.RESET}\n")
                    continue
                
                print(f"{Colors.BRIGHT_RED}Welke playlist wil je verwijderen?{Colors.RESET}")
                playlist_names = {}
                for idx, pl_id in enumerate(source_playlists, 1):
                    if sp:
                        playlist_name = get_playlist_name(sp, pl_id)
                        if playlist_name:
                            playlist_names[pl_id] = playlist_name
                            print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                        else:
                            print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                    else:
                        print(f"  {idx}. {pl_id}")
                
                try:
                    idx = int(input(f"{Colors.BRIGHT_RED}Voer nummer in (1-{len(source_playlists)}): {Colors.RESET}").strip())
                    if 1 <= idx <= len(source_playlists):
                        removed_id = source_playlists.pop(idx - 1)
                        removed_name = playlist_names.get(removed_id, removed_id)
                        config['source_playlists'] = source_playlists
                        with open(PLAYLISTS_CONFIG_FILE, 'w') as f:
                            json.dump(config, f, indent=4)
                        if removed_name != removed_id:
                            print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_name}' verwijderd!{Colors.RESET}\n")
                        else:
                            print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_id}' verwijderd!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_RED}❌ Ongeldig nummer.{Colors.RESET}\n")
                except ValueError:
                    print(f"{Colors.BRIGHT_RED}❌ Voer een geldig nummer in.{Colors.RESET}\n")
            
            elif action == '3':
                # Stel doel-playlist in
                playlist_id = input(f"{Colors.BRIGHT_BLUE}Voer doel-playlist ID in: {Colors.RESET}").strip()
                if playlist_id:
                    # Probeer playlist naam op te halen
                    playlist_name = None
                    if sp:
                        print(f"{Colors.DIM}⏳ Playlist informatie ophalen...{Colors.RESET}")
                        playlist_name = get_playlist_name(sp, playlist_id)
                        if playlist_name:
                            print(f"{Colors.BRIGHT_CYAN}   Gevonden: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                    
                    config['destination_playlist'] = playlist_id
                    with open(PLAYLISTS_CONFIG_FILE, 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    if playlist_name:
                        print(f"{Colors.BRIGHT_GREEN}✅ Doel-playlist ingesteld: '{playlist_name}'!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}✅ Doel-playlist ingesteld!{Colors.RESET}\n")
                else:
                    print(f"{Colors.BRIGHT_RED}❌ Ongeldige playlist ID.{Colors.RESET}\n")
            
            elif action == '4':
                # Toon alle playlists (met namen als mogelijk)
                print(f"\n{Colors.BRIGHT_CYAN}Alle geconfigureerde playlists:{Colors.RESET}\n")
                
                if destination_playlist:
                    if sp:
                        dest_name = get_playlist_name(sp, destination_playlist)
                        if dest_name:
                            print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {Colors.BRIGHT_WHITE}{dest_name}{Colors.RESET} {Colors.DIM}({destination_playlist}){Colors.RESET}")
                        else:
                            print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {Colors.DIM}{destination_playlist} (niet gevonden){Colors.RESET}")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {destination_playlist}")
                else:
                    print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {Colors.DIM}(niet ingesteld){Colors.RESET}")
                
                print(f"\n{Colors.BRIGHT_CYAN}Bron-playlists ({len(source_playlists)}):{Colors.RESET}")
                if source_playlists:
                    for idx, pl_id in enumerate(source_playlists, 1):
                        if sp:
                            playlist_name = get_playlist_name(sp, pl_id)
                            if playlist_name:
                                print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                            else:
                                print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                        else:
                            print(f"  {idx}. {pl_id}")
                else:
                    print(f"  {Colors.DIM}(geen){Colors.RESET}")
                
                input(f"\n{Colors.DIM}Druk Enter om door te gaan...{Colors.RESET}")
                print()
            
            else:
                print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze.{Colors.RESET}\n")
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Terug naar hoofdmenu...{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout: {e}{Colors.RESET}\n")

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
            except:
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

# =========================================================================
# 2. Hoofdfunctie
# =========================================================================

def add_tracks_to_playlist(sp, nieuwe_nummers_uris, doel_playlist_id):
    """Voegt tracks toe aan de doel-playlist na duplicaten controle."""
    if not nieuwe_nummers_uris:
        return
    
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}🔍  Duplicaten Controleren  🔍{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}\n")
    
    # Verwijder eerst duplicaten binnen de nieuwe tracks lijst zelf
    # (bijv. als dezelfde track in meerdere bron-playlists voorkomt)
    original_count = len(nieuwe_nummers_uris)
    nieuwe_nummers_uris = list(dict.fromkeys(nieuwe_nummers_uris))  # Behoudt volgorde, verwijdert duplicaten
    if len(nieuwe_nummers_uris) < original_count:
        internal_duplicates = original_count - len(nieuwe_nummers_uris)
        print(f"{Colors.BRIGHT_YELLOW}⚠️  {internal_duplicates} duplicaten verwijderd uit nieuwe tracks lijst.{Colors.RESET}")
    
    print(f"{Colors.DIM}⏳ Controleer {len(nieuwe_nummers_uris)} unieke nieuwe tracks tegen doel-playlist...{Colors.RESET}")
    try:
        doel_playlist_tracks = get_all_playlist_tracks(sp, doel_playlist_id)
        print(f"{Colors.BRIGHT_CYAN}   Doel-playlist bevat momenteel {Colors.BOLD}{len(doel_playlist_tracks)}{Colors.RESET}{Colors.BRIGHT_CYAN} tracks{Colors.RESET}")
        
        unieke_nieuwe_uris = [uri for uri in nieuwe_nummers_uris if uri not in doel_playlist_tracks]
        
        if len(unieke_nieuwe_uris) < len(nieuwe_nummers_uris):
            duplicates = len(nieuwe_nummers_uris) - len(unieke_nieuwe_uris)
            print(f"{Colors.BRIGHT_YELLOW}⚠️  {duplicates} nummers zitten al in de doel-playlist en worden overgeslagen.{Colors.RESET}")
        else:
            print(f"{Colors.BRIGHT_GREEN}✅ Alle {len(nieuwe_nummers_uris)} tracks zijn nieuw voor de doel-playlist{Colors.RESET}")
        
        nieuwe_nummers_uris = unieke_nieuwe_uris
    except Exception as e:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Kon duplicaten niet controleren: {e}{Colors.RESET}")
        print(f"{Colors.DIM}   Traceback: {type(e).__name__}: {str(e)}{Colors.RESET}")
        print(f"{Colors.DIM}   Voegt alle nummers toe (mogelijk duplicaten)...{Colors.RESET}")

    # Nummers toevoegen aan de doel-afspeellijst
    if nieuwe_nummers_uris:
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}➕  Nummers Toevoegen  ➕{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}\n")
        try:
            doel_playlist_info = sp.playlist(doel_playlist_id, fields='name')
            playlist_name = doel_playlist_info['name']
            print(f"{Colors.BRIGHT_CYAN}📝 Voegt {Colors.BOLD}{Colors.BRIGHT_WHITE}{len(nieuwe_nummers_uris)}{Colors.RESET}{Colors.BRIGHT_CYAN} unieke nummers toe aan:{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}   🎵 {playlist_name}{Colors.RESET}\n")
        except:
            print(f"{Colors.BRIGHT_CYAN}📝 Voegt {Colors.BOLD}{Colors.BRIGHT_WHITE}{len(nieuwe_nummers_uris)}{Colors.RESET}{Colors.BRIGHT_CYAN} unieke nummers toe aan playlist ID: {doel_playlist_id}{Colors.RESET}\n")
        
        # De API kan maximaal 100 nummers per keer toevoegen
        try:
            total_added = 0
            for i in range(0, len(nieuwe_nummers_uris), 100):
                batch = nieuwe_nummers_uris[i:i + 100]
                print(f"{Colors.DIM}  ⏳ Voegt batch toe ({i+1}-{min(i+100, len(nieuwe_nummers_uris))} van {len(nieuwe_nummers_uris)})...{Colors.RESET}")
                sp.playlist_add_items(doel_playlist_id, batch)
                total_added += len(batch)
                print(f"{Colors.BRIGHT_GREEN}  ✅ Batch van {Colors.BOLD}{len(batch)}{Colors.RESET}{Colors.BRIGHT_GREEN} nummers toegevoegd.{Colors.RESET}")
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 Totaal {total_added} nummers succesvol toegevoegd! 🎉{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-40)}║{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")
        except SpotifyException as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout bij toevoegen nummers: {e}{Colors.RESET}")
            print(f"{Colors.DIM}   HTTP Status: {e.http_status}{Colors.RESET}")
            print(f"{Colors.DIM}   Error Code: {e.code}{Colors.RESET}")
            if e.http_status == 404:
                print(f"{Colors.BRIGHT_YELLOW}   Doel-playlist niet gevonden. Controleer de playlist ID.{Colors.RESET}")
            elif e.http_status == 403:
                print(f"{Colors.BRIGHT_YELLOW}   Geen rechten om nummers toe te voegen aan deze playlist.{Colors.RESET}")
                print(f"{Colors.DIM}   Controleer of je de juiste scope hebt (playlist-modify-public en/of playlist-modify-private){Colors.RESET}")
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Onverwachte fout bij toevoegen: {e}{Colors.RESET}")
            import traceback
            print(f"{Colors.DIM}   Traceback: {traceback.format_exc()}{Colors.RESET}")
    else:
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}✅  Geen Nieuwe Tracks  ✅{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")
        print(f"{Colors.DIM}Geen nieuwe nummers gevonden om toe te voegen aan de doel-afspeellijst.{Colors.RESET}\n")

def sync_playlists(sp):
    """Controleert bron-playlists op nieuwe tracks en voegt deze toe aan de doel-playlist."""
    # Laad configuratie opnieuw (kan zijn aangepast)
    playlists_config = load_playlists_config()
    global MIJN_DOEL_PLAYLIST_ID, BRON_PLAYLISTS
    MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
    BRON_PLAYLISTS = playlists_config.get('source_playlists', [])
    
    # Valideer configuratie
    if not BRON_PLAYLISTS:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen bron-playlists geconfigureerd in {PLAYLISTS_CONFIG_FILE}{Colors.RESET}")
        print(f"{Colors.DIM}   Voeg playlist ID's toe aan 'source_playlists' in het configuratie bestand.{Colors.RESET}")
        return
    
    if not MIJN_DOEL_PLAYLIST_ID:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen doel-playlist geconfigureerd in {PLAYLISTS_CONFIG_FILE}{Colors.RESET}")
        print(f"{Colors.DIM}   Voeg een playlist ID toe aan 'destination_playlist' in het configuratie bestand.{Colors.RESET}")
        return
    
    historische_nummers = load_historical_data()
    nieuwe_nummers_uris = []
    
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🎵  Start Playlist Synchronisatie  🎵{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

    # Doorloop elke bron-afspeellijst
    for idx, pl_id in enumerate(BRON_PLAYLISTS, 1):
        try:
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}║{Colors.RESET}  {Colors.BRIGHT_WHITE}📋 Playlist {idx}/{len(BRON_PLAYLISTS)}{Colors.RESET}  {Colors.DIM}ID: {pl_id[:20]}...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-45)}║{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╠{'═'*68}╣{Colors.RESET}")
            
            # Haal playlist naam op voor betere feedback
            try:
                playlist_info = sp.playlist(pl_id, fields='name')
                playlist_name = playlist_info['name']
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎼 {playlist_name}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(playlist_name)-6)}║{Colors.RESET}")
            except:
                playlist_name = "Onbekend"
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}Playlist naam niet beschikbaar{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}")
            
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
            
            # Haal alleen recent toegevoegde tracks op (laatste 7 dagen) voor snelheid
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_YELLOW}⏳{Colors.RESET} {Colors.DIM}Controleer tracks toegevoegd in de laatste 7 dagen...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-50)}║{Colors.RESET}")
            recent_tracks = get_recent_playlist_tracks(sp, pl_id, days_back=7, return_track_info=True)
            recent_uris = set(recent_tracks.keys())
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_GREEN}✅{Colors.RESET} {Colors.BRIGHT_WHITE}Gevonden {Colors.BOLD}{len(recent_uris)}{Colors.RESET}{Colors.BRIGHT_WHITE} tracks toegevoegd in de laatste 7 dagen{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-60)}║{Colors.RESET}")
            
            # Toon recent toegevoegde tracks
            if recent_tracks:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}📀 Recent toegevoegde tracks:{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-25)}║{Colors.RESET}")
                for uri, track_info in sorted(recent_tracks.items(), key=lambda x: x[1]['name']):
                    track_display = f"{track_info['name']} - {track_info['artists']}"
                    # Truncate if too long
                    if len(track_display) > 60:
                        track_display = track_display[:57] + "..."
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.CYAN}•{Colors.RESET} {Colors.WHITE}{track_display}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(track_display)-8)}║{Colors.RESET}")
            
            # Bepaal welke nummers nieuw zijn (vergelijk met historische data)
            laatst_bekende_uris = historische_nummers.get(pl_id, set())
            nieuwe_uris = recent_uris - laatst_bekende_uris
            
            # Update historische data: voeg nieuwe tracks toe aan bestaande set
            # Dit behoudt alle historische tracks, niet alleen de laatste 7 dagen
            if nieuwe_uris:
                historische_nummers[pl_id] = laatst_bekende_uris.union(recent_uris)
            else:
                # Als er geen nieuwe tracks zijn, update alleen als we nog geen historische data hebben
                if pl_id not in historische_nummers:
                    historische_nummers[pl_id] = recent_uris
            
            if nieuwe_uris:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 {len(nieuwe_uris)} nieuwe nummers gevonden!{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 Nieuwe tracks:{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-18)}║{Colors.RESET}")
                for uri in sorted(nieuwe_uris, key=lambda u: recent_tracks.get(u, {}).get('name', '')):
                    track_info = recent_tracks.get(uri, {})
                    if track_info:
                        track_display = f"{track_info['name']} - {track_info['artists']}"
                        if len(track_display) > 60:
                            track_display = track_display[:57] + "..."
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{track_display}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(track_display)-8)}║{Colors.RESET}")
                    else:
                        # Fallback als track info niet beschikbaar is
                        fallback_info = get_track_info(sp, uri)
                        if len(fallback_info) > 60:
                            fallback_info = fallback_info[:57] + "..."
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.WHITE}{fallback_info}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(fallback_info)-8)}║{Colors.RESET}")
                nieuwe_nummers_uris.extend(list(nieuwe_uris))
            else:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}🤷 Geen nieuwe toevoegingen gevonden.{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-35)}║{Colors.RESET}")
            
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╚{'═'*68}╝{Colors.RESET}\n")
            
        except SpotifyException as e:
            print(f"{Colors.BRIGHT_RED}❌ Spotify API fout bij verwerken afspeellijst {pl_id}: {e}{Colors.RESET}")
            if e.http_status == 404:
                print(f"{Colors.BRIGHT_YELLOW}   Playlist niet gevonden. Controleer of de ID correct is.{Colors.RESET}")
            elif e.http_status == 403:
                print(f"{Colors.BRIGHT_YELLOW}   Geen toegang tot deze playlist. Controleer je rechten.{Colors.RESET}")
            continue
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout bij verwerken afspeellijst {pl_id}: {e}{Colors.RESET}")
            continue

    # Voeg nieuwe tracks toe aan doel-playlist
    add_tracks_to_playlist(sp, nieuwe_nummers_uris, MIJN_DOEL_PLAYLIST_ID)
    
    # Sla de status op voor de volgende keer
    save_historical_data(historische_nummers)
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Playlist synchronisatie voltooid!{Colors.RESET}\n")

def sync_artist_releases(sp):
    """Controleert gevolgde artiesten op nieuwe releases en voegt deze toe aan de doel-playlist."""
    # Laad configuratie opnieuw (kan zijn aangepast)
    playlists_config = load_playlists_config()
    global MIJN_DOEL_PLAYLIST_ID
    MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
    
    # Valideer configuratie
    if not MIJN_DOEL_PLAYLIST_ID:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen doel-playlist geconfigureerd in {PLAYLISTS_CONFIG_FILE}{Colors.RESET}")
        print(f"{Colors.DIM}   Voeg een playlist ID toe aan 'destination_playlist' in het configuratie bestand.{Colors.RESET}")
        return
    
    historische_nummers = load_historical_data()
    nieuwe_nummers_uris = []
    
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎤  Nieuwe Releases van Gevolgde Artiesten  🎤{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}\n")
    
    try:
        # Haal nieuwe releases op
        print(f"{Colors.DIM}⏳ Zoek naar nieuwe releases...{Colors.RESET}")
        artist_releases = get_all_artist_releases(sp, ARTIST_RELEASES_DAYS_BACK)
        
        if artist_releases:
            # Controleer welke releases nieuw zijn (niet al in historische data)
            artist_releases_key = '__artist_releases__'
            laatst_bekende_artist_releases = historische_nummers.get(artist_releases_key, set())
            nieuwe_artist_uris = set(artist_releases.keys()) - laatst_bekende_artist_releases
            
            if nieuwe_artist_uris:
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 {len(nieuwe_artist_uris)} nieuwe releases gevonden!{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-30)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╠{'═'*68}╣{Colors.RESET}")
                print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 Nieuwe releases:{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-18)}║{Colors.RESET}")
                for uri in sorted(nieuwe_artist_uris, key=lambda u: artist_releases.get(u, {}).get('name', '')):
                    release_info = artist_releases.get(uri, {})
                    if release_info:
                        release_display = f"{release_info['name']} - {release_info['artists']} ({release_info.get('album', 'Unknown')}) - {release_info.get('release_date', '')}"
                        if len(release_display) > 60:
                            release_display = release_display[:57] + "..."
                        print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{release_display}{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-len(release_display)-8)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")
                
                # Voeg toe aan lijst van nieuwe nummers
                nieuwe_nummers_uris.extend(list(nieuwe_artist_uris))
                
                # Update historische data
                historische_nummers[artist_releases_key] = set(artist_releases.keys())
            else:
                print(f"{Colors.DIM}🤷 Geen nieuwe releases van gevolgde artiesten gevonden.{Colors.RESET}\n")
        else:
            print(f"{Colors.DIM}🤷 Geen nieuwe releases gevonden van gevolgde artiesten.{Colors.RESET}\n")
    except SpotifyException as e:
        print(f"{Colors.BRIGHT_RED}❌ Fout bij ophalen artiest releases: {e}{Colors.RESET}")
        if e.http_status == 403:
            print(f"{Colors.BRIGHT_YELLOW}   Geen rechten om gevolgde artiesten op te halen. Controleer je scope (user-follow-read).{Colors.RESET}")
        return
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}❌ Onverwachte fout bij ophalen artiest releases: {e}{Colors.RESET}")
        return

    # Voeg nieuwe releases toe aan doel-playlist
    add_tracks_to_playlist(sp, nieuwe_nummers_uris, MIJN_DOEL_PLAYLIST_ID)
    
    # Sla de status op voor de volgende keer
    save_historical_data(historische_nummers)
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Artiest releases synchronisatie voltooid!{Colors.RESET}\n")

def main():
    """Hoofdfunctie met menu systeem."""
    while True:
        choice = show_menu()
        
        if choice == 0:
            print("\n👋 Tot ziens!")
            break
        elif choice == 1:
            # Synchroniseer alleen playlists
            sp = get_spotify_client()
            sync_playlists(sp)
        elif choice == 2:
            # Haal alleen nieuwe releases op van gevolgde artiesten
            sp = get_spotify_client()
            sync_artist_releases(sp)
        elif choice == 3:
            # Synchroniseer alles (playlists + artiest releases)
            sp = get_spotify_client()
            sync_playlists(sp)
            if CHECK_ARTIST_RELEASES:
                sync_artist_releases(sp)
        elif choice == 4:
            # Exporteer playlist naar CSV
            sp = get_spotify_client()
            
            print("\n📥 Exporteer Playlist naar CSV")
            print("-" * 60)
            
            while True:
                try:
                    playlist_id = input("\nVoer de playlist ID in (of 'q' om terug te gaan): ").strip()
                    
                    if playlist_id.lower() == 'q':
                        break
                    
                    if not playlist_id:
                        print("❌ Playlist ID mag niet leeg zijn.")
                        continue
                    
                    # Optioneel: vraag om bestandsnaam
                    output_file = input("Bestandsnaam (Enter voor automatisch): ").strip()
                    if not output_file:
                        output_file = None
                    
                    export_playlist_to_csv(sp, playlist_id, output_file)
                    
                    # Vraag of gebruiker nog een playlist wil exporteren
                    again = input("\nNog een playlist exporteren? (j/n): ").strip().lower()
                    if again != 'j':
                        break
                        
                except KeyboardInterrupt:
                    print("\n\nTerug naar hoofdmenu...")
                    break
                except Exception as e:
                    print(f"❌ Fout: {e}")
        elif choice == 5:
            # Toon meest beluisterde tracks
            sp = get_spotify_client()
            show_top_tracks(sp)
        elif choice == 6:
            # Beheer playlist configuratie
            manage_playlists_config()

if __name__ == "__main__":
    main()