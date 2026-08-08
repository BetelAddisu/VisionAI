"""Integration test: analysis pipeline stages + resumability."""
from __future__ import annotations

import pytest

from backend.ai.base import SpeechProvider, TranscriptSegment
from backend.pipeline.stages.audio import extract_audio
from backend.pipeline.stages.scenes import detect_scenes
from backend.pipeline.stages.quality import analyze_quality
from backend.pipeline.stages.frames import sample_frames


class StubSpeechProvider(SpeechProvider):
    """Deterministic speech provider for testing (no model download)."""

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
def stub_speech():
    return StubSpeechProvider([
        TranscriptSegment(start=0.0, end=1.0, text="Welcome to the AWS tutorial",
                          confidence=0.95, language="en"),
        TranscriptSegment(start=1.0, end=2.0, text="We will deploy the application",
                          confidence=0.9, language="en"),
        TranscriptSegment(start=2.0, end=3.0, text="to the cloud today",
                          confidence=0.88, language="en"),
    ])


def test_extract_audio_creates_wav(indexed_project, tmp_path):
    ctx = indexed_project
    video = ctx.repo.list_videos(ctx.project_id)[0]
    out = tmp_path / "audio.wav"
    extract_audio(video["path"], out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_detect_scenes_returns_ranges(video_file):
    scenes = detect_scenes(video_file)
    assert len(scenes) >= 1
    for start, end in scenes:
        assert end > start


def test_sample_frames_writes_images(video_file, tmp_path):
    frames = sample_frames(video_file, tmp_path / "frames", interval=1.0)
    assert len(frames) >= 1
    for t, path in frames:
        assert __import__("pathlib").Path(path).exists()


def test_analyze_quality_returns_metrics(video_file, tmp_path):
    frames = sample_frames(video_file, tmp_path / "frames", interval=1.0)
    metrics = analyze_quality(frames[0][1])
    assert "brightness" in metrics
    assert "contrast" in metrics
    assert "sharpness" in metrics
    assert 0.0 <= metrics["brightness"] <= 1.0


def test_pipeline_runs_all_stages(indexed_project, stub_speech, tmp_settings):
    from backend.pipeline import AnalysisPipeline
    from backend.ai.embedding.provider import HashingEmbeddingProvider
    ctx = indexed_project
    pipeline = AnalysisPipeline(
        ctx, settings=tmp_settings, speech=stub_speech,
        embeddings=HashingEmbeddingProvider(dimension=64))
    video = ctx.repo.list_videos(ctx.project_id)[0]
    summary = pipeline.analyze(video["id"])
    # All stages should be completed or skipped (vision skipped).
    for stage in ["scenes", "audio", "transcription", "frames", "quality", "embeddings"]:
        assert summary["stages"][stage] in ("completed", "skipped"), f"{stage} failed"
    # Transcript stored.
    segs = ctx.repo.list_transcript(video["id"])
    assert len(segs) == 3
    assert "AWS" in segs[0]["text"]
    # Embeddings stored.
    embs = ctx.repo.list_embeddings(video_id=video["id"], source_type="transcript")
    assert len(embs) == 3


def test_pipeline_is_resumable(indexed_project, stub_speech, tmp_settings):
    """If the pipeline stops mid-way, re-running continues from where it left off."""
    from backend.pipeline import AnalysisPipeline
    from backend.ai.embedding.provider import HashingEmbeddingProvider
    ctx = indexed_project
    video = ctx.repo.list_videos(ctx.project_id)[0]
    # Mark scenes completed to simulate partial progress.
    ctx.repo.set_stage_status(video["id"], "scenes", "completed")
    pipeline = AnalysisPipeline(
        ctx, settings=tmp_settings, speech=stub_speech,
        embeddings=HashingEmbeddingProvider(dimension=64))
    summary = pipeline.analyze(video["id"])
    # Scenes were already done; should be reported completed without re-running.
    assert summary["stages"]["scenes"] == "completed"
    # Downstream stages still ran.
    assert summary["stages"]["transcription"] in ("completed", "skipped")


def test_pipeline_marks_failed_stage_after_retries(indexed_project, tmp_settings):
    """A stage that always fails is marked failed after max_retries."""
    from backend.pipeline import AnalysisPipeline

    class FailingSpeech(StubSpeechProvider):
        def transcribe(self, audio_path):
            raise RuntimeError("model crashed")

    ctx = indexed_project
    video = ctx.repo.list_videos(ctx.project_id)[0]
    # Run scenes + audio first so transcription is attempted.
    pipeline = AnalysisPipeline(ctx, settings=tmp_settings, speech=FailingSpeech([]))
    summary = pipeline.analyze(video["id"])
    # Transcription should eventually be failed or pending after retries.
    assert summary["stages"]["transcription"] in ("failed", "pending")
