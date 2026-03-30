import sys

from spotify_playlist.action_sound import play_selection
from spotify_playlist.colors import Colors


def show_menu():
    """Toont het hoofdmenu en retourneert de keuze van de gebruiker."""
    print(f"\n{Colors.DIM}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}Hoofdmenu{Colors.RESET} {Colors.DIM}— kies een optie{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")
    print("\nKies een optie:")
    print("  1. Synchroniseer playlists (check bron-playlists)")
    print("  2. Haal nieuwe releases op van gevolgde artiesten")
    print("  3. Synchroniseer alles (playlists + artiest releases)")
    print("  4. Exporteer playlist naar CSV")
    print("  5. Toon meest beluisterde tracks (week/maand/jaar)")
    print("  6. Beheer playlist configuratie")
    print("  7. Exporteer nieuwe tracks sinds datum naar CSV")
    print("  0. Afsluiten")
    print("\n" + "-"*60)

    while True:
        try:
            choice = input("Voer je keuze in (0-7): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7']:
                play_selection()
                return int(choice)
            else:
                print("❌ Ongeldige keuze. Voer 0, 1, 2, 3, 4, 5, 6 of 7 in.")
        except KeyboardInterrupt:
            print("\n\nAfsluiten...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Fout: {e}")
