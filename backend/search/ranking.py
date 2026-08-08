"""Ranking engine: combines signals into a final score.

Score = w.semantic * semantic + w.keyword * keyword + w.visual * visual +
w.quality * quality + w.recency * recency. Weights are configurable.
"""
from __future__ import annotations

from backend.config import Settings, get_settings


def rank(scores: dict[str, float], settings: Settings | None = None) -> float:
    settings = settings or get_settings()
    weights = settings.search.ranking_weights
    total = 0.0
    for key, value in scores.items():
        total += weights.get(key, 0.0) * max(0.0, min(1.0, value))
    return total
