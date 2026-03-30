from spotify_playlist.colors import Colors


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
