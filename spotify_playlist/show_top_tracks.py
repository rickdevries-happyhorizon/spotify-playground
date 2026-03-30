from spotify_playlist.action_sound import play_action_done, play_selection
from spotify_playlist.colors import Colors
from spotify_playlist.get_popularity_bar import get_popularity_bar
from spotify_playlist.get_rank_color import get_rank_color
from spotify_playlist.get_top_tracks_with_counts import get_top_tracks_with_counts
from spotify_playlist.loading_progress import loading_bar


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

            play_selection()

            print(f"\n{period_color}{Colors.BOLD}{'═'*70}{Colors.RESET}")
            print(f"{period_color}{Colors.BOLD}  {period_emoji}  {period_name}  {Colors.DIM}({period_subtitle}){Colors.RESET}")
            print(f"{period_color}{Colors.BOLD}{'═'*70}{Colors.RESET}")

            with loading_bar("Tracks ophalen..."):
                tracks, elapsed_time = get_top_tracks_with_counts(sp, time_range=time_range, limit=10)

            if tracks:
                print(f"{Colors.BRIGHT_GREEN}✅ Tracks opgehaald in {Colors.BOLD}{elapsed_time:.2f}{Colors.RESET}{Colors.BRIGHT_GREEN} seconden{Colors.RESET}\n")

                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╔{'═'*68}╗{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🏆  TOP {len(tracks)} TRACKS  🏆{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-20)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╠{'═'*68}╣{Colors.RESET}")

                for track in tracks:
                    rank_icon = get_rank_color(track['rank'])
                    play_count_str = (
                        f"{Colors.BRIGHT_GREEN}{track['play_count']}x{Colors.RESET}"
                        if track['play_count'] > 0
                        else f"{Colors.DIM}Niet getrackt{Colors.RESET}"
                    )
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

            play_action_done()

            # Vraag of gebruiker nog een periode wil zien
            again = input(f"{Colors.BRIGHT_CYAN}Nog een periode bekijken? {Colors.DIM}(j/n): {Colors.RESET}").strip().lower()
            if again != 'j':
                break

        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Terug naar hoofdmenu...{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout: {e}{Colors.RESET}")
