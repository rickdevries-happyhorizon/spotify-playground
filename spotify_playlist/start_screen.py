"""Retro 8-bit style splash banner for the terminal."""

import spotify_playlist.config as config
from spotify_playlist.colors import Colors

# 5×5 block letters (█ = pixel on, space = off). One space between letters when rendered.
_FONT = {
    "A": [
        " ██ ",
        "█  █",
        "████",
        "█  █",
        "█  █",
    ],
    "B": [
        "███ ",
        "█  █",
        "███ ",
        "█  █",
        "███ ",
    ],
    "C": [
        " ██ ",
        "█  ",
        "█   ",
        "█  ",
        " ██ ",
    ],
    "D": [
        "███ ",
        "█  █",
        "█  █",
        "█  █",
        "███ ",
    ],
    "E": [
        "████",
        "█   ",
        "███ ",
        "█   ",
        "████",
    ],
    "F": [
        "████",
        "█   ",
        "███ ",
        "█   ",
        "█   ",
    ],
    "G": [
        " ██ ",
        "█   ",
        "█ ██",
        "█  █",
        " ██ ",
    ],
    "H": [
        "█  █",
        "█  █",
        "████",
        "█  █",
        "█  █",
    ],
    "I": [
        "███",
        " █ ",
        " █ ",
        " █ ",
        "███",
    ],
    "J": [
        "███",
        "  █",
        "  █",
        "  █",
        "███",
    ],
    "K": [
        "█  █",
        "█ █ ",
        "██  ",
        "█ █ ",
        "█  █",
    ],
    "L": [
        "█   ",
        "█   ",
        "█   ",
        "█   ",
        "████",
    ],
    "M": [
        "█   █",
        "██ ██",
        "█ █ █",
        "█   █",
        "█   █",
    ],
    "N": [
        "█  █",
        "██ █",
        "█ ██",
        "█  █",
        "█  █",
    ],
    "O": [
        " ██ ",
        "█  █",
        "█  █",
        "█  █",
        " ██ ",
    ],
    "P": [
        "███ ",
        "█  █",
        "███ ",
        "█   ",
        "█   ",
    ],
    "R": [
        "███ ",
        "█  █",
        "███ ",
        "█ █ ",
        "█  █",
    ],
    "S": [
        "████",
        "█   ",
        " ██ ",
        "   █",
        "████",
    ],
    "T": [
        "█████",
        "  █  ",
        "  █  ",
        "  █  ",
        "  █  ",
    ],
    "U": [
        "█  █",
        "█  █",
        "█  █",
        "█  █",
        " ██ ",
    ],
    "Y": [
        "█  █",
        "█  █",
        " ██ ",
        "  █ ",
        "  █ ",
    ],
    " ": [
        "  ",
        "  ",
        "  ",
        "  ",
        "  ",
    ],
}


def _row_width(glyph: list[str]) -> int:
    return max(len(row) for row in glyph) if glyph else 0


def _normalize_glyph(glyph: list[str]) -> list[str]:
    w = _row_width(glyph)
    return [row.ljust(w) for row in glyph]


def _render_word(word: str) -> list[str]:
    """Return 5 lines of monospace art for word (uppercase A-Z and space)."""
    upper = word.upper()
    glyphs = [_normalize_glyph(_FONT.get(ch, _FONT[" "])) for ch in upper]
    if not glyphs:
        return ["", "", "", "", ""]
    lines = []
    for row in range(5):
        parts = []
        for g in glyphs:
            parts.append(g[row])
        lines.append(" ".join(parts))
    return lines


# Arcade palette for scanline-style rows
_ROW_COLORS = (
    Colors.BRIGHT_GREEN,
    Colors.BRIGHT_CYAN,
    Colors.BRIGHT_MAGENTA,
    Colors.BRIGHT_YELLOW,
    Colors.BRIGHT_GREEN,
)


def show_start_screen() -> None:
    """Print fancy 8-bit style banner once at startup."""
    line1 = _render_word("SHORT JACK")
    line2 = _render_word("RELEASE")
    sub = f"♪ {config.APP_NAME} ♪"

    pixel_w = max(len(line1[0]), len(line2[0])) if line1 and line2 else 0
    width = max(pixel_w, len(sub))
    pad = lambda s: s.center(width) if width else s

    top = f"{Colors.DIM}{Colors.BRIGHT_BLACK}╔{'═' * (width + 2)}╗{Colors.RESET}"
    bot = f"{Colors.DIM}{Colors.BRIGHT_BLACK}╚{'═' * (width + 2)}╝{Colors.RESET}"

    print()
    print(top)
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET} {' ' * width} {Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET}")
    for row in range(5):
        c = _ROW_COLORS[row % len(_ROW_COLORS)]
        print(
            f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET} "
            f"{Colors.BOLD}{c}{pad(line1[row])}{Colors.RESET} "
            f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET}"
        )
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET} {' ' * width} {Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET}")
    for row in range(5):
        c = _ROW_COLORS[(row + 2) % len(_ROW_COLORS)]
        print(
            f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET} "
            f"{Colors.BOLD}{c}{pad(line2[row])}{Colors.RESET} "
            f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET}"
        )
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET} {' ' * width} {Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET}")
    print(
        f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET} "
        f"{Colors.DIM}{Colors.BRIGHT_WHITE}{sub.center(width)}{Colors.RESET} "
        f"{Colors.DIM}{Colors.BRIGHT_BLACK}║{Colors.RESET}"
    )
    print(bot)
    print()
