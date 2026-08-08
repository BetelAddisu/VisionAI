"""Quality analysis stage: OpenCV-based footage metrics (no AI model)."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def analyze_quality(image_path: str | Path) -> dict[str, float]:
    """Compute brightness, contrast, blur (sharpness), noise for a frame.

    - brightness: mean pixel intensity (0-255) normalized to 0-1.
    - contrast: std dev of intensity normalized to 0-1.
    - blur_score: Laplacian variance (higher = sharper); normalized.
    - sharpness: 1 - (blur_score inverted), 0-1.
    - noise: high-frequency energy estimate, 0-1 (lower = cleaner).
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {"brightness": 0.0, "contrast": 0.0, "blur_score": 0.0,
                "noise_score": 0.0, "sharpness": 0.0}
    brightness = float(np.mean(img)) / 255.0
    contrast = float(np.std(img)) / 127.5
    laplacian_var = float(cv2.Laplacian(img, cv2.CV_64F).var())
    # Normalize laplacian variance: typical sharp images > 100, blurry < 50.
    sharpness = min(1.0, laplacian_var / 500.0)
    blur_score = max(0.0, 1.0 - sharpness)
    # Noise estimate: mean of high-pass filtered residual.
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    residual = cv2.absdiff(img, blur)
    noise = float(np.mean(residual)) / 50.0
    noise = min(1.0, noise)
    return {
        "brightness": brightness,
        "contrast": min(1.0, contrast),
        "blur_score": blur_score,
        "noise_score": noise,
        "sharpness": sharpness,
    }
