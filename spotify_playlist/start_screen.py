"""Startup banner for the terminal."""

import spotify_playlist.config as config
from spotify_playlist.colors import Colors


def show_start_screen() -> None:
    """Print a compact app header once at startup."""
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}♪ {config.APP_NAME} ♪{Colors.RESET}")
    print()
