from db_store import load_ui_skin, save_ui_skin

from spotify_playlist.action_sound import play_action_done, play_selection
from spotify_playlist.colors import Colors


def manage_ui_skin():
    """Manage the New Tracks To-Do web UI skin."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎨  UI Skin Configuration  🎨{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")

    while True:
        current = load_ui_skin()
        print(f"{Colors.BRIGHT_WHITE}Current skin:{Colors.RESET} {Colors.BRIGHT_CYAN}{current}{Colors.RESET}")
        print(f"\n{Colors.BRIGHT_WHITE}Choose a skin:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} light  {Colors.DIM}(clean black and white){Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}2.{Colors.RESET} dark  {Colors.DIM}(flat dark mode){Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}3.{Colors.RESET} colorful  {Colors.DIM}(animated gradients and glow effects){Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}4.{Colors.RESET} retroui  {Colors.DIM}(neo-brutalism: bold borders, hard shadows){Colors.RESET}")
        print(f"  {Colors.DIM}0.{Colors.RESET} Back to main menu")
        print(f"\n{Colors.DIM}{'-' * 70}{Colors.RESET}")

        try:
            choice = input(f"{Colors.BRIGHT_CYAN}Enter your choice (0-4): {Colors.RESET}").strip()
        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Back to main menu...{Colors.RESET}")
            return

        if choice == "0":
            return

        if choice == "1":
            skin = "light"
        elif choice == "2":
            skin = "dark"
        elif choice == "3":
            skin = "colorful"
        elif choice == "4":
            skin = "retroui"
        else:
            print(f"{Colors.BRIGHT_RED}❌ Invalid choice.{Colors.RESET}\n")
            continue

        if skin == current:
            print(f"{Colors.BRIGHT_YELLOW}⚠️  Skin is already set to '{skin}'.{Colors.RESET}\n")
            continue

        save_ui_skin(skin)
        play_action_done()
        print(f"{Colors.BRIGHT_GREEN}✅ UI skin set to '{skin}'.{Colors.RESET}\n")
