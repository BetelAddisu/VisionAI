"""Unit tests for the ranking engine."""
from backend.search.ranking import rank


def test_rank_combines_signals_with_weights(tmp_settings):
    scores = {"semantic": 1.0, "keyword": 1.0, "visual": 1.0,
              "quality": 1.0, "recency": 1.0}
    weights = tmp_settings.search.ranking_weights
    expected = sum(weights.values())
    assert abs(rank(scores, tmp_settings) - expected) < 1e-6


def test_rank_clamps_out_of_range(tmp_settings):
    scores = {"semantic": 5.0}
    assert rank(scores, tmp_settings) == tmp_settings.search.ranking_weights["semantic"]


def test_rank_ignores_unknown_signal(tmp_settings):
    scores = {"semantic": 1.0, "bogus": 1.0}
    assert abs(rank(scores, tmp_settings) - tmp_settings.search.ranking_weights["semantic"]) < 1e-6
