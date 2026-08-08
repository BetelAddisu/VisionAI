"""Integration test: video indexing end-to-end."""
from __future__ import annotations

from backend.indexing import VideoIndexer
from backend.indexing.hasher import compute_fingerprint
from backend.indexing.metadata import extract_metadata


def test_index_project_registers_videos(indexed_project):
    ctx = indexed_project
    videos = ctx.repo.list_videos(ctx.project_id)
    assert len(videos) == 2
    for v in videos:
        assert v["duration"] > 0
        assert v["width"] > 0
        assert v["fps"] > 0
        assert v["available"] == 1
        assert v["hash"]
        assert v["fingerprint"]


def test_indexing_is_incremental(indexed_project):
    ctx = indexed_project
    result = VideoIndexer(ctx).index_project()
    assert result.added == 0
    assert result.unchanged == 2


def test_metadata_extraction(video_file):
    meta = extract_metadata(video_file)
    assert meta["duration"] > 0
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["has_audio"] is True


def test_fingerprint_is_stable(video_file):
    assert compute_fingerprint(video_file) == compute_fingerprint(video_file)


def test_index_enqueues_analysis_jobs(indexed_project):
    ctx = indexed_project
    jobs = ctx.repo.list_jobs(ctx.project_id)
    # One analyze_video job per video.
    assert len(jobs) == 2
    assert all(j["job_type"] == "analyze_video" for j in jobs)
