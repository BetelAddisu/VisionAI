"""Audio extraction stage: extract 16kHz mono WAV via ffmpeg."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.config import Settings, get_settings


def extract_audio(video_path: str | Path, output_path: str | Path,
                  *, sample_rate: int = 16000, channels: int = 1,
                  timeout: int = 600) -> Path:
    """Extract mono WAV audio suitable for speech models."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-y", "-i", str(video_path),
        "-vn", "-ac", str(channels), "-ar", str(sample_rate),
        "-acodec", "pcm_s16le", str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"audio extraction timed out for {Path(video_path).name}") from exc
    if result.returncode != 0 or not output_path.exists():
        # Some videos have no audio stream — that is not fatal.
        if "No audio streams" in result.stderr or "does not contain any stream" in result.stderr:
            raise FileNotFoundError("Video has no audio stream")
        raise RuntimeError(f"audio extraction failed: {result.stderr.strip()[-300:]}")
    return output_path
