"""Unit tests for planner rules and types."""
from backend.planner.editing_rules import (
    detect_filler_phrases,
    pacing_for,
)
from backend.planner.platform_rules import profile_for
from backend.planner.types import EditPlan, PlanClip, PlanSection


def test_pacing_for_short_platform():
    lo, hi = pacing_for("tiktok", "short")
    assert lo < hi
    assert hi <= 5.0


def test_pacing_for_long_platform():
    lo, hi = pacing_for("youtube", "long")
    assert hi >= 5.0


def test_detect_filler_phrases():
    assert "um" in detect_filler_phrases("so um I was like thinking")
    assert "basically" in detect_filler_phrases("it basically works")


def test_profile_for_unknown_falls_back_to_default():
    prof = profile_for("nonexistent")
    assert prof["subtitle_style"]


def test_plan_grounding_detects_unknown_clips():
    plan = EditPlan(title="t", platform="youtube", target_length="long",
                    sections=[PlanSection(
                        type="hook", label="Hook", target_start=0,
                        target_duration=5,
                        clips=[PlanClip(video_id="real", filename="a.mp4",
                                        source_start=0, source_end=1),
                               PlanClip(video_id="fake", filename="b.mp4",
                                        source_start=0, source_end=1)])])
    bad = plan.validate_grounding({"real"})
    assert bad == ["fake"]


def test_plan_to_dict_roundtrip():
    plan = EditPlan(title="t", platform="youtube", target_length="long",
                    sections=[PlanSection(type="hook", label="Hook",
                                          target_start=0, target_duration=5)])
    d = plan.to_dict()
    assert d["title"] == "t"
    assert d["sections"][0]["type"] == "hook"
