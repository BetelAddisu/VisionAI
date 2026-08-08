"""Unit tests for timeline models, validator, subtitles and XML export."""
from __future__ import annotations

from pathlib import Path

from backend.timeline.models import Timeline, TimelineClip
from backend.timeline.subtitles import build_subtitles, to_srt
from backend.timeline.validator import validate_timeline
from backend.export.xml_generator import generate_davinci_xml


def _clip(video_id="v1", track="V1", start=0, end=5, tl_start=0):
    return TimelineClip(
        id="c1", video_id=video_id, filename="a.mp4", source_path="/tmp/a.mp4",
        track=track, source_start=start, source_end=end,
        timeline_start=tl_start, timeline_end=tl_start + (end - start))


def test_timeline_duration_and_clips_on():
    # clip1: timeline 0..5, clip2: timeline 5..10
    tl = Timeline(id="t1", name="Test", clips=[
        TimelineClip(id="c1", video_id="v1", filename="a.mp4", source_path="/tmp/a.mp4",
                     track="V1", source_start=0, source_end=5,
                     timeline_start=0, timeline_end=5),
        TimelineClip(id="c2", video_id="v1", filename="a.mp4", source_path="/tmp/a.mp4",
                     track="V1", source_start=0, source_end=5,
                     timeline_start=5, timeline_end=10),
    ])
    assert tl.duration == 10.0
    assert len(tl.clips_on("V1")) == 2


def test_subtitles_to_srt():
    subs = build_subtitles([
        {"start_time": 0.0, "end_time": 1.5, "text": "Hello"},
        {"start_time": 2.0, "end_time": 3.0, "text": "World"},
    ])
    srt = to_srt(subs)
    assert "1" in srt
    assert "Hello" in srt
    assert "World" in srt
    assert "-->" in srt


def test_validate_timeline_detects_overlap(monkeypatch, indexed_project):
    ctx = indexed_project
    video = ctx.repo.list_videos(ctx.project_id)[0]
    c1 = TimelineClip(id="c1", video_id=video["id"], filename=video["filename"],
                      source_path=video["path"], track="V1",
                      source_start=0, source_end=2, timeline_start=0, timeline_end=2)
    c2 = TimelineClip(id="c2", video_id=video["id"], filename=video["filename"],
                      source_path=video["path"], track="V1",
                      source_start=0, source_end=2, timeline_start=1, timeline_end=3)
    tl = Timeline(id="t1", name="Test", clips=[c1, c2])
    errors = validate_timeline(ctx, tl)
    assert any("overlap" in e for e in errors)


def test_generate_davinci_xml(tmp_path):
    tl = Timeline(id="t1", name="Test", fps=30, clips=[_clip()])
    out = generate_davinci_xml(tl, tmp_path / "out.xml")
    assert out.exists()
    content = out.read_text()
    assert "<?xml" in content
    assert "xmeml" in content
    assert "clipitem" in content
    assert "a.mp4" in content
