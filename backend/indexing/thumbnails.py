"""Thumbnail generation via ffmpeg.

Generates a single small JPEG thumbnail (default 320px wide) from a frame
near the start of the video. Never loads the whole video into memory — uses
ffmpeg's seek-and-extract.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.config import Settings, get_settings
from backend.logging import get_logger

log = get_logger("thumbnail")


def generate_thumbnail(video_path: str | Path, output_path: str | Path,
                       *, seek_seconds: float = 1.0,
                       settings: Settings | None = None) -> Path:
    """Generate a thumbnail JPEG at ``output_path``.

    Seeks to ``seek_seconds`` (clamped to a small value to avoid scanning
    the whole file) and extracts one frame scaled to the configured width.
    """
    settings = settings or get_settings()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width = settings.pipeline.thumbnail_width
    # Use fast seek; -ss before -i is fast for most containers.
    cmd = [
        ffmpeg, "-y", "-ss", f"{max(0.0, seek_seconds):.2f}",
        "-i", str(video_path),
        "-frames:v", "1",
        "-vf", f"scale={width}:-2",
        "-q:v", "3",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"thumbnail timed out for {video_path.name}") from exc
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"thumbnail failed for {video_path.name}: {result.stderr.strip()[-300:]}")
    return output_path


def generate_scene_thumbnail(video_path: str | Path, output_path: str | Path,
                              *, at_seconds: float,
                              settings: Settings | None = None) -> Path:
    """Generate a thumbnail at a specific timestamp (for a scene)."""
    return generate_thumbnail(video_path, output_path, seek_seconds=at_seconds, settings=settings)
