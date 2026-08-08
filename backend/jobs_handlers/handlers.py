"""Concrete job handlers executed by the worker."""
from __future__ import annotations

from backend.indexing import VideoIndexer
from backend.logging import get_logger
from backend.pipeline import AnalysisPipeline
from backend.planner import AIPlanner, PlanInput

log = get_logger("jobs")


def handle_index(job: dict, ctx) -> None:
    """Index a project's video folder."""
    indexer = VideoIndexer(ctx)
    result = indexer.index_project()
    log.info("index job done", extra={
        "job_id": job["id"], "project_id": ctx.project_id,
        "added": result.added, "updated": result.updated,
        "unchanged": result.unchanged, "failed": len(result.failed)})


def handle_analyze_video(job: dict, ctx) -> None:
    """Run the analysis pipeline for a single video."""
    video_id = job.get("video_id")
    if not video_id:
        raise RuntimeError("analyze_video job missing video_id")
    pipeline = AnalysisPipeline(ctx)
    pipeline.analyze(video_id)


def handle_plan(job: dict, ctx) -> None:
    """Run the AI planner from a job payload."""
    payload = job.get("payload") or {}
    plan_input = PlanInput(
        brief=payload.get("brief", ""),
        script=payload.get("script", ""),
        audience=payload.get("audience", ""),
        platform=payload.get("platform", "youtube"),
        target_length=payload.get("target_length", ""),
        style=payload.get("style", ""),
    )
    planner = AIPlanner(ctx)
    planner.create_plan(plan_input)
