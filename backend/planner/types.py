"""Planner types: structured edit plan schema.

The plan is validated JSON. Sections follow a story structure (hook,
setup, problem, development, resolution, conclusion, cta). Each clip
references a real video_id + source time range.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanClip:
    video_id: str
    filename: str
    source_start: float
    source_end: float
    purpose: str = ""
    score: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id, "filename": self.filename,
            "source_start": self.source_start, "source_end": self.source_end,
            "purpose": self.purpose, "score": round(self.score, 4),
            "reason": self.reason,
        }


@dataclass
class PlanSection:
    type: str               # hook | setup | problem | development | resolution | conclusion | cta
    label: str
    target_start: float
    target_duration: float
    clips: list[PlanClip] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type, "label": self.label,
            "target_start": self.target_start,
            "target_duration": self.target_duration,
            "clips": [c.to_dict() for c in self.clips],
            "instructions": list(self.instructions),
        }


@dataclass
class EditPlan:
    title: str
    platform: str
    target_length: str
    sections: list[PlanSection] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    color_recommendation: dict[str, Any] = field(default_factory=dict)
    music_recommendation: dict[str, Any] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "platform": self.platform,
            "target_length": self.target_length,
            "sections": [s.to_dict() for s in self.sections],
            "recommendations": list(self.recommendations),
            "color_recommendation": dict(self.color_recommendation),
            "music_recommendation": dict(self.music_recommendation),
            "unresolved": list(self.unresolved),
        }

    def all_clips(self) -> list[PlanClip]:
        clips: list[PlanClip] = []
        for section in self.sections:
            clips.extend(section.clips)
        return clips

    def validate_grounding(self, valid_video_ids: set[str]) -> list[str]:
        """Return list of clips referencing unknown footage (should be empty)."""
        bad = []
        for clip in self.all_clips():
            if clip.video_id not in valid_video_ids:
                bad.append(clip.video_id)
        return bad
