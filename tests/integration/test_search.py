"""Integration test: search engine returns real indexed footage."""
from __future__ import annotations

import pytest

from backend.ai.base import SpeechProvider, TranscriptSegment
from backend.search import SearchEngine, SearchFilters


class StubSpeech(SpeechProvider):
    def __init__(self, segments):
        self._segments = segments

    @property
    def available(self):
        return True

    @property
    def model_version(self):
        return "stub-v1"

    def transcribe(self, audio_path):
        return self._segments


@pytest.fixture
def searchable_project(indexed_project, tmp_settings):
    """An indexed project with transcribed + embedded segments."""
    from backend.pipeline import AnalysisPipeline
    from backend.ai.embedding.provider import HashingEmbeddingProvider
    ctx = indexed_project
    segments = [
        TranscriptSegment(0.0, 1.0, "Today we deploy an application to AWS", 0.9, "en"),
        TranscriptSegment(1.0, 2.0, "The cloud infrastructure is reliable", 0.85, "en"),
        TranscriptSegment(2.0, 3.0, "Cooking pasta is fun and easy", 0.8, "en"),
    ]
    pipeline = AnalysisPipeline(
        ctx, settings=tmp_settings, speech=StubSpeech(segments),
        embeddings=HashingEmbeddingProvider(dimension=64))
    for video in ctx.repo.list_videos(ctx.project_id):
        pipeline.analyze(video["id"])
    return ctx


def test_search_returns_relevant_clips(searchable_project, tmp_settings):
    ctx = searchable_project
    engine = SearchEngine(ctx, settings=tmp_settings)
    results = engine.search("find clips where I explain AWS deployment")
    assert len(results) > 0
    # Top result should mention AWS / cloud, not pasta.
    top = results[0]
    assert top.score > 0
    assert top.video_id
    assert top.start_time < top.end_time
    snippet = (top.transcript_snippet or "").lower()
    assert "aws" in snippet or "deploy" in snippet or "cloud" in snippet


def test_search_never_invents_clips(searchable_project, tmp_settings):
    ctx = searchable_project
    engine = SearchEngine(ctx, settings=tmp_settings)
    results = engine.search("something with no matches whatsoever banana")
    # Results may be empty or low-scored, but never reference nonexistent videos.
    valid_ids = {v["id"] for v in ctx.repo.list_videos(ctx.project_id)}
    for r in results:
        assert r.video_id in valid_ids


def test_search_with_metadata_filter(searchable_project, tmp_settings):
    ctx = searchable_project
    engine = SearchEngine(ctx, settings=tmp_settings)
    video = ctx.repo.list_videos(ctx.project_id)[0]
    filters = SearchFilters(video_id=video["id"])
    results = engine.search("cloud", filters=filters)
    for r in results:
        assert r.video_id == video["id"]


def test_search_records_history(searchable_project, tmp_settings):
    ctx = searchable_project
    engine = SearchEngine(ctx, settings=tmp_settings)
    engine.search("AWS deployment")
    from backend.database.connection import Database
    # search_history is populated via repo.add_search_history.
    rows = ctx.repo.query_all(
        "SELECT * FROM search_history WHERE project_id = ?;", (ctx.project_id,))
    assert len(rows) >= 1
