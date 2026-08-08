"""Frame sampling stage: extract representative frames via ffmpeg/OpenCV.

Samples one frame every N seconds and stores small JPEGs. Never loads the
whole video into memory.
"""
from __future__ import annotations

from pathlib import Path

import cv2

from backend.logging import get_logger

log = get_logger("frames")


def sample_frames(video_path: str | Path, output_dir: str | Path,
                  *, interval: float = 2.0, width: int = 320) -> list[tuple[float, str]]:
    """Sample frames at ``interval`` seconds.

    Returns a list of (timestamp, image_path) tuples.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video for frame sampling: {video_path.name}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step_frames = max(1, int(round(fps * interval)))
    results: list[tuple[float, str]] = []
    frame_idx = 0
    try:
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok:
                break
            t = frame_idx / fps
            if width and frame.shape[1] > width:
                scale = width / frame.shape[1]
                frame = cv2.resize(frame, (width, int(frame.shape[0] * scale)))
            stamp = f"{int(t * 1000):08d}"
            img_path = output_dir / f"frame_{stamp}.jpg"
            cv2.imwrite(str(img_path), frame)
            results.append((t, str(img_path)))
            frame_idx += step_frames
            if total and frame_idx >= total:
                break
    finally:
        cap.release()
    return results
