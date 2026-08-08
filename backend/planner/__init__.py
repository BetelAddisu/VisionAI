"""AI Planner: creative reasoning layer.

Transforms creator intent + available footage knowledge into a structured
editing plan. The planner NEVER invents footage — every clip reference is
validated against the indexed library via the search engine.
"""
from backend.planner.editing_rules import (
    FILLER_WORDS,
    PACING,
    detect_filler_phrases,
    pacing_for,
)
from backend.planner.platform_rules import profile_for
from backend.planner.planner import AIPlanner, PlanInput
from backend.planner.types import EditPlan, PlanClip, PlanSection

__all__ = [
    "AIPlanner",
    "PlanInput",
    "EditPlan",
    "PlanSection",
    "PlanClip",
    "pacing_for",
    "detect_filler_phrases",
    "profile_for",
    "FILLER_WORDS",
    "PACING",
]
