"""Timeline Builder: converts an EditPlan into a deterministic timeline.

Deterministic: same plan + library -> same timeline. Validates every clip
against the library, assigns tracks (V1 main, V2 broll), and places clips
sequentially with hard cuts by default.
"""
from __future__ import annotations

import uuid

from backend.core import ProjectContext
from backend.logging import get_logger
from backend.planner.types import EditPlan
from backend.timeline.models import Timeline, TimelineClip
from backend.timeline.subtitles import build_subtitles
from backend.timeline.validator import validate_timeline

log = get_logger("timeline_builder")


class TimelineBuilder:
    def __init__(self, ctx: ProjectContext, fps: float = 30.0) -> None:
        self.ctx = ctx
        self.fps = fps

    def build(self, plan: EditPlan, *, session_id: str | None = None,
              name: str | None = None) -> Timeline:
        timeline = Timeline(
            id=uuid.uuid4().hex,
            name=name or plan.title,
            fps=self.fps,
        )
        cursor = 0.0
        for section in plan.sections:
            for clip in section.clips:
                video = self.ctx.repo.get_video(clip.video_id)
                if not video:
                    log.warning("clip skipped: unknown video", extra={
                        "video_id": clip.video_id})
                    continue
                # Clamp source range to video duration.
                src_end = min(clip.source_end, video["duration"] or clip.source_end)
                src_start = min(clip.source_start, src_end - 0.1)
                duration = max(0.5, src_end - src_start)
                track = "V2" if clip.purpose.lower().startswith(("b-roll", "broll")) else "V1"
                timeline.clips.append(TimelineClip(
                    id=uuid.uuid4().hex,
                    video_id=clip.video_id,
                    filename=video["filename"],
                    source_path=video["path"],
                    track=track,
                    source_start=src_start,
                    source_end=src_end,
                    timeline_start=cursor,
                    timeline_end=cursor + duration,
                    clip_type="broll" if track == "V2" else "video",
                    transition="hard_cut",
                    label=section.type,
                ))
                cursor += duration

        # Build subtitles from the selected clips' transcripts.
        segs: list[dict] = []
        for clip in timeline.clips:
            rows = self.ctx.repo.query_all(
                """SELECT start_time, end_time, text FROM transcript_segments
                   WHERE video_id = ? AND start_time >= ? AND end_time <= ?
                   ORDER BY start_time;""",
                (clip.video_id, clip.source_start, clip.source_end))
            # Offset transcript times to timeline position.
            offset = clip.timeline_start - clip.source_start
            for r in rows:
                segs.append({
                    "start_time": r["start_time"] + offset,
                    "end_time": r["end_time"] + offset,
                    "text": r["text"],
                })
        timeline.subtitles = build_subtitles(segs, style="clean")

        errors = validate_timeline(self.ctx, timeline)
        if errors:
            log.warning("timeline validation issues", extra={
                "timeline_id": timeline.id, "errors": errors})

        # Persist to database.
        self._persist(timeline, plan, session_id)
        return timeline

    def _persist(self, timeline: Timeline, plan: EditPlan,
                 session_id: str | None) -> None:
        timeline_id = self.ctx.repo.create_timeline(
            project_id=self.ctx.project_id, name=timeline.name,
            fps=timeline.fps, duration=timeline.duration,
            timeline_json=timeline.to_dict(), session_id=session_id)
        timeline.id = timeline_id
        for i, clip in enumerate(timeline.clips):
            self.ctx.repo.add_timeline_clip(
                timeline_id=timeline_id, video_id=clip.video_id, track=clip.track,
                source_start=clip.source_start, source_end=clip.source_end,
                timeline_start=clip.timeline_start, timeline_end=clip.timeline_end,
                order_index=i, clip_type=clip.clip_type,
                transition=clip.transition, label=clip.label)
        log.info("timeline built", extra={
            "project_id": self.ctx.project_id, "timeline_id": timeline_id,
            "clips": len(timeline.clips), "duration": timeline.duration})
