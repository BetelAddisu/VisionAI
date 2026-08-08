"""Subtitle generator: builds timed subtitle cues from transcript segments."""
from __future__ import annotations

from backend.utils.video import format_timestamp


def build_subtitles(segments: list[dict], style: str = "clean") -> list[dict]:
    """Return subtitle cues with start/end/text/style."""
    cues: list[dict] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        cues.append({
            "start": float(seg["start_time"]),
            "end": float(seg["end_time"]),
            "text": text,
            "style": style,
        })
    return cues


def to_srt(subtitles: list[dict]) -> str:
    """Render subtitles to SRT format."""
    lines: list[str] = []
    for i, cue in enumerate(subtitles, 1):
        lines.append(str(i))
        lines.append(f"{_srt_time(cue['start'])} --> {_srt_time(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    return "\n".join(lines)


def _srt_time(seconds: float) -> str:
    # SRT uses comma as decimal separator.
    return format_timestamp(seconds).replace(".", ",")
