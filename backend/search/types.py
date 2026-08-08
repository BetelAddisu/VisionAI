"""Search types."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchFilters:
    category: str | None = None
    min_duration: float | None = None
    max_duration: float | None = None
    video_id: str | None = None
    min_quality: float | None = None


@dataclass
class SearchResult:
    video_id: str
    filename: str
    path: str
    start_time: float
    end_time: float
    score: float
    reason: str
    transcript_snippet: str = ""
    thumbnail_path: str | None = None
    matched_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "filename": self.filename,
            "path": self.path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "score": round(self.score, 4),
            "reason": self.reason,
            "transcript_snippet": self.transcript_snippet,
            "thumbnail_path": self.thumbnail_path,
            "matched_terms": self.matched_terms,
        }
