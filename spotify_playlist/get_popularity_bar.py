from spotify_playlist.colors import Colors


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
