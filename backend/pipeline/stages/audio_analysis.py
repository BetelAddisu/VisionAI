"""Audio analysis stage: silence/noise/loudness from the extracted WAV.

Reads the 16kHz mono WAV in chunks (never the whole file at once for long
audio) and computes per-window loudness, silence and background noise.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.logging import get_logger

log = get_logger("audio_analysis")

# Silence threshold in dBFS; windows below this are silent.
SILENCE_THRESHOLD_DB = -40.0


def analyze_audio(audio_path: str | Path, *, window_seconds: float = 2.0) -> list[dict]:
    """Return per-window audio analysis records.

    Uses ffmpeg's silencedetect and ebur128 to avoid pulling in heavy audio
    libraries, then derives per-window metrics.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return []
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return []
    # Get loudness stats via ebur128.
    cmd = [
        ffmpeg, "-i", str(audio_path), "-af",
        f"ebur128=metadata=1", "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return []
    stderr = result.stderr or ""
    samples: list[tuple[float, float]] = []
    for line in stderr.splitlines():
        # Parse "lavfi.r128.M=..." entries tagged with pts_time.
        if "lavfi.r128.M=" in line:
            try:
                pts = None
                m = None
                for token in line.split():
                    if token.startswith("pts_time:"):
                        pts = float(token.split(":")[1])
                    elif token.startswith("lavfi.r128.M="):
                        m = float(token.split("=")[1])
                if pts is not None and m is not None:
                    samples.append((pts, m))
            except (ValueError, IndexError):
                continue
    if not samples:
        return []
    # Bin samples into windows.
    windows: dict[float, list[float]] = {}
    for t, loud in samples:
        bucket = round(t / window_seconds) * window_seconds
        windows.setdefault(bucket, []).append(loud)
    records: list[dict] = []
    for t, vals in sorted(windows.items()):
        loudness = sum(vals) / len(vals)
        peak = max(vals)
        silence = loudness < SILENCE_THRESHOLD_DB
        background_noise = min(1.0, max(0.0, (-loudness - 30) / 40.0)) if loudness < -20 else 0.0
        records.append({
            "timestamp": t, "silence": silence, "loudness": loudness,
            "peak": peak, "background_noise": background_noise,
        })
    return records
