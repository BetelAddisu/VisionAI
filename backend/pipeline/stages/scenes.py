"""Scene detection stage.

Uses OpenCV to detect content-aware scene boundaries by comparing
histograms of sampled frames. This avoids heavy dependencies (PySceneDetect)
while still detecting camera cuts and major visual changes. Frames are
decoded one at a time — never the whole video into memory.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from backend.logging import get_logger

log = get_logger("scenes")


def detect_scenes(video_path: str | Path, *, threshold: float = 0.4,
                  sample_interval: float = 1.0) -> list[tuple[float, float]]:
    """Return a list of (start_time, end_time) scene boundaries.

    ``threshold`` is the histogram difference (0-1) above which a new scene
    is considered to start. The video is opened with OpenCV and frames are
    seeked sequentially in small steps.
    """
    video_path = Path(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video for scene detection: {video_path.name}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, int(round(fps * sample_interval)))

    scene_starts: list[float] = [0.0]
    prev_hist: np.ndarray | None = None
    frame_idx = 0
    try:
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
            cv2.normalize(hist, hist)
            if prev_hist is not None:
                diff = float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA))
                if diff > threshold:
                    t = frame_idx / fps
                    if t - scene_starts[-1] > 0.5:
                        scene_starts.append(t)
            prev_hist = hist
            frame_idx += step
    finally:
        cap.release()

    duration = (total_frames / fps) if (total_frames and fps) else (frame_idx / fps)
    if duration <= 0:
        duration = frame_idx / fps if fps else 0.0
    if not scene_starts or scene_starts[-1] < duration:
        scene_starts.append(max(duration, scene_starts[-1] if scene_starts else 0.0))

    scenes: list[tuple[float, float]] = []
    for i in range(len(scene_starts) - 1):
        start = scene_starts[i]
        end = scene_starts[i + 1]
        if end > start:
            scenes.append((start, end))
    if not scenes:
        scenes.append((0.0, max(duration, 0.0)))
    return scenes
