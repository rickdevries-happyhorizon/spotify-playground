"""Analyze track energy from audio files using librosa."""

from __future__ import annotations


def _require_librosa():
    try:
        import librosa
        import numpy as np
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "librosa is niet geïnstalleerd. Voer uit: pip install -r requirements.txt"
        ) from exc
    return librosa, np


def analyze_track_energy(path: str) -> float:
    """
    Estimate track energy on a 0.0–1.0 scale from frame RMS loudness.

    Uses the 95th percentile of frame RMS values so quiet intros/outros
    do not dominate the score.
    """
    librosa, np = _require_librosa()

    audio, _sample_rate = librosa.load(path, sr=None, mono=True)
    if audio.size == 0:
        raise ValueError('Leeg audiobestand')

    rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
    peak_rms = float(np.percentile(rms, 95))
    energy = float(np.clip(peak_rms / 0.5, 0.0, 1.0))
    return round(energy, 2)


def format_energy_label(energy: float) -> str:
    """Format energy for Rekordbox Label (TPUB) field."""
    return f'{energy:.2f}'
