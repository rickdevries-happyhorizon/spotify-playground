"""Fetch Spotify audio feature energy for tracks."""

from __future__ import annotations

from typing import Any

from spotify_playlist.audio_batch import spotify_call_with_retry


def normalize_energy(value: Any) -> float | None:
    """Normalize Spotify energy (0.0–1.0) for database storage."""
    if value is None:
        return None
    try:
        energy = float(value)
    except (TypeError, ValueError):
        return None
    if not 0.0 <= energy <= 1.0:
        return None
    return round(energy, 3)


def fetch_track_energies(sp, track_uris: list[str]) -> dict[str, float | None]:
    """Map Spotify track URI to energy score, or None when unavailable."""
    result: dict[str, float | None] = {uri: None for uri in track_uris}
    unique_uris = list(dict.fromkeys(uri for uri in track_uris if uri))
    if not unique_uris:
        return result

    batch_size = 100
    for offset in range(0, len(unique_uris), batch_size):
        batch = unique_uris[offset : offset + batch_size]
        features_list = spotify_call_with_retry(lambda b=batch: sp.audio_features(b))
        if not features_list:
            continue
        for uri, features in zip(batch, features_list):
            if features and features.get('energy') is not None:
                result[uri] = normalize_energy(features['energy'])
    return result
