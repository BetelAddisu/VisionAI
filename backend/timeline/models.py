"""Timeline models: internal timeline schema (OTIO-like).

A timeline has tracks (V1 main, V2 broll, V3 graphics, V4 subtitles, A1
voice, A2 music). Clips carry source video, source in/out, timeline
position, track and transition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Canonical track ids.
TRACKS = ["V1", "V2", "V3", "V4", "A1", "A2", "A3"]


@dataclass
class TimelineClip:
    id: str
    video_id: str
    filename: str
    source_path: str
    track: str
    source_start: float
    source_end: float
    timeline_start: float
    timeline_end: float
    clip_type: str = "video"          # video | broll | audio | subtitle
    transition: str = "hard_cut"
    label: str = ""

    @property
    def duration(self) -> float:
        return self.source_end - self.source_start

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "video_id": self.video_id, "filename": self.filename,
            "source_path": self.source_path, "track": self.track,
            "source_start": self.source_start, "source_end": self.source_end,
            "timeline_start": self.timeline_start, "timeline_end": self.timeline_end,
            "clip_type": self.clip_type, "transition": self.transition,
            "label": self.label,
        }


@dataclass
class Timeline:
    id: str
    name: str
    fps: float = 30.0
    clips: list[TimelineClip] = field(default_factory=list)
    subtitles: list[dict] = field(default_factory=list)

    @property
    def duration(self) -> float:
        if not self.clips:
            return 0.0
        return max(c.timeline_end for c in self.clips)

    def clips_on(self, track: str) -> list[TimelineClip]:
        return sorted([c for c in self.clips if c.track == track],
                      key=lambda c: c.timeline_start)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "fps": self.fps,
            "duration": self.duration,
            "clips": [c.to_dict() for c in self.clips],
            "subtitles": list(self.subtitles),
        }
