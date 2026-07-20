import os
import struct

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors
from spotify_playlist.audio_energy import analyze_track_energy, format_energy_label
from spotify_playlist.parse_wav_filename import parse_wav_filename
from spotify_playlist.release_year import normalize_release_year
from spotify_playlist.write_riff_info import apply_riff_info

AUDIO_EXTENSIONS = ('.wav', '.aiff', '.aif')


def _require_mutagen():
    try:
        from mutagen.aiff import AIFF
        from mutagen.id3 import APIC, TCON, TDRC, TIT2, TPE1, TPUB, TYER
        from mutagen.wave import WAVE
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "mutagen is niet geïnstalleerd. Voer uit: pip install -r requirements.txt"
        ) from exc
    return APIC, TCON, TDRC, TIT2, TPE1, TPUB, TYER, WAVE, AIFF


def _apply_label_tag(audio, TPUB, label: str) -> None:
    audio.tags.delall('TPUB')
    audio.tags.add(TPUB(encoding=3, text=label))


def _apply_year_tags(audio, TDRC, TYER, year: int) -> None:
    year_text = str(year)
    audio.tags.delall('TDRC')
    audio.tags.delall('TYER')
    audio.tags.add(TDRC(encoding=3, text=year_text))
    audio.tags.add(TYER(encoding=3, text=year_text))


def apply_cover_art(path: str, image_bytes: bytes, *, mime: str = 'image/jpeg') -> None:
    """Embed cover art in a WAV or AIFF file via an ID3 APIC frame."""
    APIC, _TCON, _TDRC, _TIT2, _TPE1, _TPUB, _TYER, WAVE, AIFF = _require_mutagen()
    extension = os.path.splitext(path)[1].lower()

    if extension == '.wav':
        audio = WAVE(path)
    elif extension in ('.aiff', '.aif'):
        audio = AIFF(path)
    else:
        raise ValueError(f'Niet ondersteund bestandstype: {extension}')

    if audio.tags is None:
        audio.add_tags()

    audio.tags.delall('APIC')
    audio.tags.add(
        APIC(
            encoding=3,
            mime=mime,
            type=3,
            desc='Cover',
            data=image_bytes,
        )
    )
    audio.save()


def apply_wav_metadata(
    path: str,
    artists: list[str],
    title: str,
    genre: str | None = None,
    year: int | str | None = None,
    label: str | None = None,
) -> None:
    """Write ID3 and RIFF INFO tags to a WAV file and clear any album field."""
    _APIC, TCON, TDRC, TIT2, TPE1, TPUB, TYER, WAVE, _AIFF = _require_mutagen()
    artist = ', '.join(artists)
    release_year = normalize_release_year(year)

    # Many DJ WAV exports have invalid RIFF headers. Rebuild the file first so
    # mutagen can insert/update the ID3 chunk without struct errors.
    apply_riff_info(path, title, artist, genre, release_year)

    try:
        audio = WAVE(path)
        if audio.tags is None:
            audio.add_tags()

        audio.tags.delall('TIT2')
        audio.tags.delall('TPE1')
        audio.tags.delall('TALB')
        audio.tags.delall('TCON')
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        if genre:
            audio.tags.add(TCON(encoding=3, text=genre))
        if release_year is not None:
            _apply_year_tags(audio, TDRC, TYER, release_year)
        if label:
            _apply_label_tag(audio, TPUB, label)
        audio.save()
    except struct.error:
        # Rekordbox only reads RIFF INFO; ID3 is optional for other players.
        pass

    # Write RIFF INFO last so Rekordbox always sees the final metadata.
    apply_riff_info(path, title, artist, genre, release_year)


def apply_aiff_metadata(
    path: str,
    artists: list[str],
    title: str,
    genre: str | None = None,
    year: int | str | None = None,
    label: str | None = None,
) -> None:
    """Write ID3 tags to an AIFF file and clear any album field."""
    _APIC, TCON, TDRC, TIT2, TPE1, TPUB, TYER, _WAVE, AIFF = _require_mutagen()
    artist = ', '.join(artists)
    release_year = normalize_release_year(year)

    audio = AIFF(path)
    if audio.tags is None:
        audio.add_tags()

    audio.tags.delall('TIT2')
    audio.tags.delall('TPE1')
    audio.tags.delall('TALB')
    audio.tags.delall('TCON')
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))
    if genre:
        audio.tags.add(TCON(encoding=3, text=genre))
    if release_year is not None:
        _apply_year_tags(audio, TDRC, TYER, release_year)
    if label:
        _apply_label_tag(audio, TPUB, label)
    audio.save()


def apply_audio_metadata(
    path: str,
    artists: list[str],
    title: str,
    genre: str | None = None,
    year: int | str | None = None,
    label: str | None = None,
) -> None:
    """Write metadata tags based on the audio file extension."""
    extension = os.path.splitext(path)[1].lower()
    if extension == '.wav':
        apply_wav_metadata(path, artists, title, genre, year, label)
    elif extension in ('.aiff', '.aif'):
        apply_aiff_metadata(path, artists, title, genre, year, label)
    else:
        raise ValueError(f'Niet ondersteund bestandstype: {extension}')


def tag_wavs_in_directory(directory: str, *, dry_run: bool = False) -> tuple[int, int]:
    """
    Tag all WAV and AIFF files in a directory based on their filenames.

    Returns (success_count, error_count).
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Map niet gevonden: {directory}")

    audio_files = sorted(
        filename
        for filename in os.listdir(directory)
        if filename.lower().endswith(AUDIO_EXTENSIONS)
    )

    if not audio_files:
        print(
            f"{Colors.BRIGHT_YELLOW}⚠️  Geen WAV/AIFF bestanden gevonden in: {directory}{Colors.RESET}"
        )
        return 0, 0

    print(f"\n{Colors.BRIGHT_WHITE}Gevonden audio bestanden ({len(audio_files)}):{Colors.RESET}\n")

    success_count = 0
    error_count = 0

    for filename in audio_files:
        path = os.path.join(directory, filename)
        stem = os.path.splitext(filename)[0]

        try:
            artists, title = parse_wav_filename(stem)
            artists_display = ', '.join(artists)
            print(f"  {Colors.BRIGHT_CYAN}{filename}{Colors.RESET}")
            print(f"    Artiesten: {Colors.BRIGHT_WHITE}{artists_display}{Colors.RESET}")
            print(f"    Titel:     {Colors.BRIGHT_WHITE}{title}{Colors.RESET}")
            print(f"    Album:     {Colors.DIM}(leeg){Colors.RESET}")
            print(f"    Jaar:      {Colors.DIM}(leeg){Colors.RESET}")
            print(f"    Label:     {Colors.DIM}(energy){Colors.RESET}")

            if not dry_run:
                energy_label = None
                try:
                    energy_label = format_energy_label(analyze_track_energy(path))
                except Exception as exc:
                    print(
                        f"    {Colors.BRIGHT_YELLOW}⚠️  Energy niet geanalyseerd: {exc}{Colors.RESET}"
                    )

                apply_audio_metadata(path, artists, title, label=energy_label)
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
    """Interactive flow to tag WAV and AIFF files from the menu."""
    try:
        _require_mutagen()
    except ModuleNotFoundError as exc:
        print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
        return

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🏷️  WAV/AIFF Metadata Toevoegen  🏷️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")

    if default_directory:
        print(f"{Colors.DIM}Standaard map: {default_directory}{Colors.RESET}")

    directory = input(
        f"{Colors.BRIGHT_CYAN}Map met WAV/AIFF bestanden (Enter voor standaard, 'q' om terug): {Colors.RESET}"
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
