import re


def parse_wav_filename(stem: str) -> tuple[list[str], str]:
    """
    Parse a WAV filename stem into artists and track title.

    Example:
        Ultra Naté, Tedd Patterson - RESTLESS (Analu Andrade Remix)
        -> artists: Ultra Naté, Tedd Patterson, Analu Andrade
        -> title: RESTLESS (Analu Andrade Remix)
    """
    if ' - ' not in stem:
        raise ValueError(f"Bestandsnaam mist ' - ' scheiding: {stem!r}")

    artists_part, title = stem.split(' - ', 1)
    artists = [artist.strip() for artist in artists_part.split(',') if artist.strip()]
    title = title.strip()

    if not artists:
        raise ValueError(f"Geen artiesten gevonden in bestandsnaam: {stem!r}")
    if not title:
        raise ValueError(f"Geen tracktitel gevonden in bestandsnaam: {stem!r}")

    remix_match = re.search(r'\(([^)]+)\)\s*$', title)
    if remix_match and re.search(r'\bremix\b', remix_match.group(1), flags=re.IGNORECASE):
        remix_artist = re.sub(
            r'\bremix\b',
            '',
            remix_match.group(1),
            flags=re.IGNORECASE,
        ).strip()
        if remix_artist and remix_artist not in artists:
            artists.append(remix_artist)

    return artists, title
