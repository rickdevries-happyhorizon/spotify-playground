"""Write RIFF INFO metadata (INAM/IART/IPRD) for Rekordbox-compatible WAV files."""

import struct


def _encode_zstr(text: str) -> bytes:
    # RIFF INFO uses single-byte strings; latin-1 keeps Rekordbox compatibility.
    return text.encode('latin-1', errors='replace') + b'\x00'


def _build_info_subchunk(field_id: str, text: str) -> bytes:
    zstr = _encode_zstr(text)
    chunk = field_id.encode('ascii') + struct.pack('<I', len(zstr)) + zstr
    if len(zstr) % 2:
        chunk += b'\x00'
    return chunk


def _build_list_info_chunk(
    title: str,
    artist: str,
    genre: str | None = None,
    year: int | None = None,
    album: str | None = None,
) -> bytes:
    list_data = b'INFO'
    list_data += _build_info_subchunk('INAM', title)
    list_data += _build_info_subchunk('IART', artist)
    if genre:
        list_data += _build_info_subchunk('IGNR', genre)
    if album:
        list_data += _build_info_subchunk('IPRD', album)
    if year is not None:
        list_data += _build_info_subchunk('ICRD', str(year))
    chunk = b'LIST' + struct.pack('<I', len(list_data)) + list_data
    if len(chunk) % 2:
        chunk += b'\x00'
    return chunk


def _is_info_list_chunk(chunk: bytes) -> bool:
    return len(chunk) >= 12 and chunk[:4] == b'LIST' and chunk[8:12] == b'INFO'


def _iter_wave_chunks(data: bytes, start: int = 12):
    """Walk top-level WAVE chunks, tolerating incorrect declared sizes."""
    pos = start
    end = len(data)

    while pos + 8 <= end:
        chunk_id = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        data_start = pos + 8
        available = end - data_start
        actual_size = min(size, available)
        chunk_end = data_start + actual_size + (actual_size % 2)
        chunk_end = min(chunk_end, end)

        if chunk_end <= pos:
            break

        yield data[pos:chunk_end]
        pos = chunk_end


def apply_riff_info(
    path: str,
    title: str,
    artist: str,
    genre: str | None = None,
    year: int | None = None,
    album: str | None = None,
) -> None:
    """
    Write Rekordbox-readable RIFF INFO tags to a WAV file.

    Rekordbox ignores ID3 in WAV files and only reads LIST/INFO fields:
    INAM (title), IART (artist), IPRD (album), IGNR (genre), ICRD (year).
    """
    with open(path, 'rb') as fileobj:
        data = fileobj.read()

    if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError('Geen geldig RIFF/WAVE bestand')

    rebuilt = bytearray(data[:12])
    info_chunk = _build_list_info_chunk(title, artist, genre, year, album)
    info_inserted = False

    for chunk in _iter_wave_chunks(data):
        if _is_info_list_chunk(chunk):
            continue
        rebuilt.extend(chunk)
        if not info_inserted and chunk[:4] == b'fmt ':
            rebuilt.extend(info_chunk)
            info_inserted = True

    if not info_inserted:
        rebuilt.extend(info_chunk)

    struct.pack_into('<I', rebuilt, 4, len(rebuilt) - 8)

    with open(path, 'wb') as fileobj:
        fileobj.write(rebuilt)
