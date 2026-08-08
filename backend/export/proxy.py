"""Proxy generation: low-res H.264 proxies for editing on weak hardware.

The AI analyzes proxies; the final DaVinci timeline retains the original
media path. Never modifies or deletes the original footage.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.config import Settings, get_settings
from backend.logging import get_logger

log = get_logger("proxy")


def generate_proxy(video_path: str | Path, output_path: str | Path,
                   *, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    cfg = settings.proxy
    if not cfg.enabled:
        # Proxying disabled: return the original path (no copy made).
        return Path(video_path)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-y", "-i", str(video_path),
        "-vf", f"scale={cfg.width}:{cfg.height}",
        "-c:v", "libx264", "-b:v", cfg.bitrate,
        "-c:a", "aac", "-b:a", "128k",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"proxy generation timed out for {Path(video_path).name}") from exc
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"proxy generation failed: {result.stderr.strip()[-300:]}")
    log.info("proxy generated", extra={
        "action": "proxy", "status": "done", "path": str(output_path)})
    return output_path
