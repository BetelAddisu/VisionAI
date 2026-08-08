"""Timeline validator: checks source files, timecodes and track overlaps."""
from __future__ import annotations

from pathlib import Path

from backend.core import ProjectContext
from backend.logging import get_logger
from backend.timeline.models import Timeline

log = get_logger("timeline_validator")


def validate_timeline(ctx: ProjectContext, timeline: Timeline) -> list[str]:
    """Return a list of validation errors (empty list = valid)."""
    errors: list[str] = []
    if not timeline.clips:
        errors.append("Timeline contains no clips")
        return errors

    for clip in timeline.clips:
        video = ctx.repo.get_video(clip.video_id)
        if not video:
            errors.append(f"Clip {clip.id} references unknown video {clip.video_id}")
            continue
        if not Path(video["path"]).exists():
            errors.append(f"Clip {clip.id} source file missing: {video['path']}")
        if clip.source_end <= clip.source_start:
            errors.append(
                f"Clip {clip.id} invalid source timecode "
                f"({clip.source_start}-{clip.source_end})")
        if clip.timeline_end <= clip.timeline_start:
            errors.append(
                f"Clip {clip.id} invalid timeline position "
                f"({clip.timeline_start}-{clip.timeline_end})")
        if clip.source_end > video["duration"] + 0.5:
            errors.append(
                f"Clip {clip.id} source end {clip.source_end} exceeds video duration "
                f"{video['duration']}")

    # Check for overlaps within each track.
    for track in {c.track for c in timeline.clips}:
        clips = timeline.clips_on(track)
        for a, b in zip(clips, clips[1:]):
            if b.timeline_start < a.timeline_end - 1e-6:
                errors.append(
                    f"Track {track} overlap: clip {b.id} starts at "
                    f"{b.timeline_start} before {a.id} ends at {a.timeline_end}")
    return errors
