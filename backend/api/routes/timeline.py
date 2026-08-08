"""Timeline routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.deps import get_project_context
from backend.core import ProjectContext
from backend.export import export_davinci_xml, export_srt
from backend.planner import AIPlanner, PlanInput
from backend.timeline import TimelineBuilder

router = APIRouter()


class BuildTimelineRequest(BaseModel):
    session_id: str
    name: str | None = None


@router.post("/projects/{project_id}/timelines")
def build_timeline(payload: BuildTimelineRequest,
                   ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    session = ctx.repo.get_planner_session(payload.session_id)
    if not session or not session.get("plan"):
        raise HTTPException(status_code=404, detail="Plan session not found")
    from backend.planner.types import EditPlan, PlanClip, PlanSection
    plan_dict = session["plan"]
    sections = []
    for s in plan_dict.get("sections", []):
        clips = [PlanClip(**c) for c in s.get("clips", [])]
        sections.append(PlanSection(
            type=s["type"], label=s["label"], target_start=s.get("target_start", 0),
            target_duration=s.get("target_duration", 0), clips=clips,
            instructions=s.get("instructions", [])))
    plan = EditPlan(
        title=plan_dict.get("title", "AI Edit"),
        platform=plan_dict.get("platform", "youtube"),
        target_length=plan_dict.get("target_length", ""),
        sections=sections,
        recommendations=plan_dict.get("recommendations", []),
        color_recommendation=plan_dict.get("color_recommendation", {}),
        music_recommendation=plan_dict.get("music_recommendation", {}),
        unresolved=plan_dict.get("unresolved", []),
    )
    builder = TimelineBuilder(ctx)
    timeline = builder.build(plan, session_id=payload.session_id, name=payload.name)
    return {"timeline_id": timeline.id, "timeline": timeline.to_dict()}


@router.get("/projects/{project_id}/timelines")
def list_timelines(ctx: ProjectContext = Depends(get_project_context)) -> list[dict[str, Any]]:
    return ctx.repo.list_timelines(ctx.project_id)


@router.get("/projects/{project_id}/timelines/{timeline_id}")
def get_timeline(timeline_id: str,
                 ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    timeline = ctx.repo.get_timeline(timeline_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return timeline


@router.post("/projects/{project_id}/timelines/{timeline_id}/export")
def export_timeline(timeline_id: str, version: int = 1,
                    ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    tl_dict = ctx.repo.get_timeline(timeline_id)
    if not tl_dict:
        raise HTTPException(status_code=404, detail="Timeline not found")
    from backend.timeline.models import Timeline, TimelineClip
    tl_json = tl_dict["timeline"] or {"clips": []}
    clips = [TimelineClip(
        id=c["id"], video_id=c["video_id"], filename=c.get("filename", ""),
        source_path=c.get("source_path", ""), track=c["track"],
        source_start=c["source_start"], source_end=c["source_end"],
        timeline_start=c["timeline_start"], timeline_end=c["timeline_end"],
        clip_type=c.get("clip_type", "video"), transition=c.get("transition", "hard_cut"),
        label=c.get("label", "")) for c in tl_json.get("clips", [])]
    timeline = Timeline(
        id=tl_dict["id"], name=tl_dict["name"], fps=tl_dict.get("fps", 30),
        clips=clips, subtitles=tl_json.get("subtitles", []))
    result = export_davinci_xml(ctx, timeline, version=version)
    return result


@router.post("/projects/{project_id}/timelines/{timeline_id}/export-srt")
def export_timeline_srt(timeline_id: str,
                        ctx: ProjectContext = Depends(get_project_context)) -> dict:
    tl_dict = ctx.repo.get_timeline(timeline_id)
    if not tl_dict:
        raise HTTPException(status_code=404, detail="Timeline not found")
    from backend.timeline.models import Timeline
    tl_json = tl_dict["timeline"] or {"subtitles": []}
    timeline = Timeline(id=tl_dict["id"], name=tl_dict["name"],
                        fps=tl_dict.get("fps", 30), subtitles=tl_json.get("subtitles", []))
    path = export_srt(ctx, timeline)
    return {"srt": path}
