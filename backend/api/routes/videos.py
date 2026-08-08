"""Video routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_project_context
from backend.core import ProjectContext
from backend.pipeline import AnalysisPipeline

router = APIRouter()


@router.get("/projects/{project_id}/videos")
def list_videos(ctx: ProjectContext = Depends(get_project_context)) -> list[dict[str, Any]]:
    return ctx.repo.list_videos(ctx.project_id)


@router.get("/projects/{project_id}/videos/{video_id}")
def get_video(video_id: str,
              ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    video = ctx.repo.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video["scenes"] = ctx.repo.list_scenes(video_id)
    video["transcript"] = ctx.repo.list_transcript(video_id)
    video["analysis_state"] = ctx.repo.get_analysis_state(video_id)
    return video


@router.post("/projects/{project_id}/videos/{video_id}/analyze")
def analyze_video(video_id: str, force: bool = False,
                  ctx: ProjectContext = Depends(get_project_context),
                  container=Depends(lambda: None)) -> dict[str, Any]:
    # Run synchronously for direct API use; background jobs use the worker.
    pipeline = AnalysisPipeline(ctx)
    return pipeline.analyze(video_id, force=force)


@router.get("/projects/{project_id}/videos/{video_id}/transcript")
def get_transcript(video_id: str,
                   ctx: ProjectContext = Depends(get_project_context)) -> list[dict[str, Any]]:
    return ctx.repo.list_transcript(video_id)


@router.get("/projects/{project_id}/videos/{video_id}/scenes")
def get_scenes(video_id: str,
               ctx: ProjectContext = Depends(get_project_context)) -> list[dict[str, Any]]:
    return ctx.repo.list_scenes(video_id)
