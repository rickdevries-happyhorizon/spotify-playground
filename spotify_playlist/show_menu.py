import sys

from spotify_playlist.action_sound import play_selection
from spotify_playlist.colors import Colors


def show_menu():
    """Displays the main menu and returns the user's choice."""
    print(f"\n{Colors.DIM}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}Main menu{Colors.RESET} {Colors.DIM}— choose an option{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")
    print("\nChoose an option:")
    print("  1. Sync playlists, artist releases, and discovery")
    print("  2. Import new tracks since specified date into database")
    print("  3. Download tracks to AIFF")
    print("  4. Manage playlist configuration")
    print("  5. Manage UI skin")
    print("  0. Exit")
    print("\n" + "-"*60)

    while True:
        try:
            choice = input("Enter your choice (0-5): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5']:
                play_selection()
                return int(choice)
            else:
                print("❌ Invalid choice. Enter 0 through 5.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
