"""Editing rules: deterministic principles applied by the planner.

These encode professional editing heuristics (talking-head variety, pacing,
silence/filler removal) as data so the planner's reasoning is transparent
and testable, not hidden in prompt text.
"""
from __future__ import annotations

# Maximum seconds of static talking head before B-roll should be inserted.
MAX_TALKING_HEAD_SECONDS = 30

# Pacing: target visual change interval by platform form.
PACING = {
    "short": (2.0, 5.0),     # shorts/tiktok
    "long": (5.0, 15.0),     # youtube long-form
    "default": (4.0, 10.0),
}

# Filler words / phrases to flag for removal.
FILLER_WORDS = {
    "um", "uh", "er", "ah", "like", "basically", "literally",
    "you know", "i mean", "sort of", "kind of",
}

# Transition distribution defaults (per 08-timeline-builder.md).
TRANSITION_DISTRIBUTION = {"hard_cut": 0.80, "dissolve": 0.15, "special": 0.05}


def pacing_for(platform: str, target_length: str) -> tuple[float, float]:
    key = "short" if platform in ("tiktok", "shorts", "reels") or target_length == "short" else "long"
    return PACING.get(key, PACING["default"])


def detect_filler_phrases(text: str) -> list[str]:
    lower = (text or "").lower()
    return [w for w in FILLER_WORDS if w in lower]
