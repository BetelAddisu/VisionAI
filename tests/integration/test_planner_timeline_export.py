"""Integration test: planner grounding and timeline export end-to-end."""
from __future__ import annotations

import pytest

from backend.ai.base import SpeechProvider, TranscriptSegment
from backend.export import export_davinci_xml
from backend.planner import AIPlanner, PlanInput
from backend.timeline import TimelineBuilder


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
def analyzed_project(indexed_project, tmp_settings):
    from backend.pipeline import AnalysisPipeline
    from backend.ai.embedding.provider import HashingEmbeddingProvider
    ctx = indexed_project
    segments = [
        TranscriptSegment(0.0, 1.0, "Welcome to the tutorial on AWS deployment", 0.9, "en"),
        TranscriptSegment(1.0, 2.0, "We will build a cloud application step by step", 0.85, "en"),
        TranscriptSegment(2.0, 3.0, "First we set up the problem and environment", 0.8, "en"),
    ]
    pipeline = AnalysisPipeline(
        ctx, settings=tmp_settings, speech=StubSpeech(segments),
        embeddings=HashingEmbeddingProvider(dimension=64))
    for video in ctx.repo.list_videos(ctx.project_id):
        pipeline.analyze(video["id"])
    return ctx


def test_planner_produces_grounded_plan(analyzed_project, tmp_settings):
    ctx = analyzed_project
    planner = AIPlanner(ctx, settings=tmp_settings)
    session_id, plan = planner.create_plan(PlanInput(
        brief="A tutorial about AWS cloud deployment",
        platform="youtube", target_length="short"))
    valid_ids = {v["id"] for v in ctx.repo.list_videos(ctx.project_id)}
    # Every clip must reference real footage.
    bad = plan.validate_grounding(valid_ids)
    assert bad == [], f"Plan references unknown videos: {bad}"
    assert len(plan.sections) >= 5
    assert plan.title
    assert plan.color_recommendation  # recommendations present


def test_planner_records_unresolved_when_no_footage(analyzed_project, tmp_settings):
    ctx = analyzed_project
    planner = AIPlanner(ctx, settings=tmp_settings)
    _, plan = planner.create_plan(PlanInput(
        brief="quantum physics lecture",  # no matching footage
        platform="youtube"))
    # Plan still produced but clips may be empty / unresolved recorded.
    assert isinstance(plan.unresolved, list)


def test_timeline_builder_creates_valid_timeline(analyzed_project, tmp_settings):
    ctx = analyzed_project
    planner = AIPlanner(ctx, settings=tmp_settings)
    session_id, plan = planner.create_plan(PlanInput(
        brief="AWS cloud deployment tutorial", platform="youtube"))
    builder = TimelineBuilder(ctx)
    timeline = builder.build(plan, session_id=session_id)
    assert timeline.duration > 0
    assert len(timeline.clips) > 0
    # All clips reference real videos.
    valid_ids = {v["id"] for v in ctx.repo.list_videos(ctx.project_id)}
    for clip in timeline.clips:
        assert clip.video_id in valid_ids
    # Timeline persisted.
    assert ctx.repo.get_timeline(timeline.id) is not None


def test_davinci_xml_export(analyzed_project, tmp_settings):
    ctx = analyzed_project
    planner = AIPlanner(ctx, settings=tmp_settings)
    session_id, plan = planner.create_plan(PlanInput(
        brief="AWS cloud deployment", platform="youtube"))
    builder = TimelineBuilder(ctx)
    timeline = builder.build(plan, session_id=session_id)
    result = export_davinci_xml(ctx, timeline)
    from pathlib import Path
    assert Path(result["xml"]).exists()
    content = Path(result["xml"]).read_text()
    assert "xmeml" in content
    # SRT may be None if no subtitles, otherwise a path.
    if result["srt"]:
        assert Path(result["srt"]).exists()
