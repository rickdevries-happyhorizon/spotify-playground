import os

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors
from spotify_playlist.parse_wav_filename import parse_wav_filename
from spotify_playlist.write_riff_info import apply_riff_info


def _require_mutagen():
    try:
        from mutagen.id3 import TIT2, TPE1
        from mutagen.wave import WAVE
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "mutagen is niet geïnstalleerd. Voer uit: pip install -r requirements.txt"
        ) from exc
    return TIT2, TPE1, WAVE


def apply_wav_metadata(path: str, artists: list[str], title: str) -> None:
    """Write ID3 and RIFF INFO tags to a WAV file and clear any album field."""
    TIT2, TPE1, WAVE = _require_mutagen()
    artist = ', '.join(artists)

    apply_riff_info(path, title, artist)

    audio = WAVE(path)
    if audio.tags is None:
        audio.add_tags()

    audio.tags.delall('TIT2')
    audio.tags.delall('TPE1')
    audio.tags.delall('TALB')
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))
    audio.save()


def tag_wavs_in_directory(directory: str, *, dry_run: bool = False) -> tuple[int, int]:
    """
    Tag all WAV files in a directory based on their filenames.

    Returns (success_count, error_count).
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Map niet gevonden: {directory}")

    wav_files = sorted(
        filename
        for filename in os.listdir(directory)
        if filename.lower().endswith('.wav')
    )

    if not wav_files:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen WAV bestanden gevonden in: {directory}{Colors.RESET}")
        return 0, 0

    print(f"\n{Colors.BRIGHT_WHITE}Gevonden WAV bestanden ({len(wav_files)}):{Colors.RESET}\n")

    success_count = 0
    error_count = 0

    for filename in wav_files:
        path = os.path.join(directory, filename)
        stem = os.path.splitext(filename)[0]

        try:
            artists, title = parse_wav_filename(stem)
            artists_display = ', '.join(artists)
            print(f"  {Colors.BRIGHT_CYAN}{filename}{Colors.RESET}")
            print(f"    Artiesten: {Colors.BRIGHT_WHITE}{artists_display}{Colors.RESET}")
            print(f"    Titel:     {Colors.BRIGHT_WHITE}{title}{Colors.RESET}")
            print(f"    Album:     {Colors.DIM}(leeg){Colors.RESET}")

            if not dry_run:
                apply_wav_metadata(path, artists, title)
                print(f"    {Colors.BRIGHT_GREEN}✅ Metadata bijgewerkt{Colors.RESET}\n")
            else:
                print(f"    {Colors.DIM}(preview only){Colors.RESET}\n")

            success_count += 1
        except Exception as exc:
            print(f"  {Colors.BRIGHT_RED}❌ {filename}: {exc}{Colors.RESET}\n")
            error_count += 1

    if not dry_run and success_count:
        play_action_done()

    return success_count, error_count


def run_tag_wav_metadata(default_directory: str = '') -> None:
    """Interactive flow to tag WAV files from the menu."""
    try:
        _require_mutagen()
    except ModuleNotFoundError as exc:
        print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
        return

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🏷️  WAV Metadata Toevoegen  🏷️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")

    if default_directory:
        print(f"{Colors.DIM}Standaard map: {default_directory}{Colors.RESET}")

    directory = input(
        f"{Colors.BRIGHT_CYAN}Map met WAV bestanden (Enter voor standaard, 'q' om terug): {Colors.RESET}"
    ).strip()

    if directory.lower() == 'q':
        return

    if not directory:
        directory = default_directory

    if not directory:
        print(f"{Colors.BRIGHT_RED}❌ Geen map opgegeven.{Colors.RESET}")
        return

    directory = os.path.expanduser(directory)

    try:
        success_count, error_count = tag_wavs_in_directory(directory, dry_run=True)
    except Exception as exc:
        print(f"{Colors.BRIGHT_RED}❌ Fout: {exc}{Colors.RESET}")
        return

    if success_count == 0:
        return

    confirm = input(
        f"\n{Colors.BRIGHT_CYAN}Metadata toepassen op {success_count} bestand(en)? (j/n): {Colors.RESET}"
    ).strip().lower()

    if confirm != 'j':
        print(f"{Colors.DIM}Geannuleerd.{Colors.RESET}")
        return

    success_count, error_count = tag_wavs_in_directory(directory, dry_run=False)

    print(f"\n{Colors.BRIGHT_GREEN}Klaar: {success_count} bijgewerkt, {error_count} mislukt.{Colors.RESET}")
    if success_count:
        print(
            f"{Colors.DIM}Tip: in Rekordbox rechtsklik op de tracks → Reload Tag om de metadata te laden.{Colors.RESET}"
        )
