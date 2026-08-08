"""Metadata extraction via ffprobe.

Reads container/codec information only — never decodes video content. Uses
the ffprobe binary via subprocess and parses JSON output.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from backend.logging import get_logger

log = get_logger("metadata")


def _find_ffprobe() -> str:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found. Install FFmpeg to extract video metadata.")
    return ffprobe


def _find_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found. Install FFmpeg for media processing.")
    return ffmpeg


def extract_metadata(path: str | Path) -> dict[str, Any]:
    """Extract video metadata using ffprobe.

    Returns a dict with duration, fps, width, height, codec, bitrate,
    audio_codec, has_audio and file_size. Raises RuntimeError on failure.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")
    ffprobe = _find_ffprobe()
    cmd = [
        ffprobe, "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"ffprobe timed out for {path.name}") from exc
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path.name}: {result.stderr.strip()}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON for {path.name}") from exc

    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})

    fps = 0.0
    if video_stream:
        fps_num = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "0/1"
        try:
            num, den = fps_num.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0.0
        except (ValueError, ZeroDivisionError):
            fps = 0.0

    bitrate = 0
    try:
        bitrate = int(fmt.get("bit_rate") or video_stream.get("bit_rate") or 0)
    except (TypeError, ValueError):
        bitrate = 0

    file_size = 0
    try:
        file_size = int(fmt.get("size") or path.stat().st_size)
    except (TypeError, ValueError, OSError):
        file_size = path.stat().st_size if path.exists() else 0

    return {
        "duration": float(fmt.get("duration") or video_stream.get("duration") or 0),
        "fps": round(fps, 3),
        "width": int(video_stream.get("width") or 0) if video_stream else 0,
        "height": int(video_stream.get("height") or 0) if video_stream else 0,
        "codec": (video_stream.get("codec_name") or "") if video_stream else "",
        "bitrate": bitrate,
        "audio_codec": (audio_stream.get("codec_name") or "") if audio_stream else "",
        "has_audio": bool(audio_stream),
        "file_size": file_size,
    }
