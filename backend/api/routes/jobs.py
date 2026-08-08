"""Job routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.api.deps import get_container, get_project_context
from backend.core import ProjectContext
from backend.jobs import JobQueue

router = APIRouter()


@router.get("/projects/{project_id}/jobs")
def list_jobs(status: str | None = None,
              ctx: ProjectContext = Depends(get_project_context)) -> list[dict[str, Any]]:
    return JobQueue(ctx.repo).list(ctx.project_id, status=status)


@router.post("/projects/{project_id}/jobs/{job_id}/cancel")
def cancel_job(job_id: str,
               ctx: ProjectContext = Depends(get_project_context)) -> dict:
    JobQueue(ctx.repo).cancel(job_id)
    return {"cancelled": True, "job_id": job_id}


@router.post("/projects/{project_id}/jobs/run")
def run_pending_jobs(ctx: ProjectContext = Depends(get_project_context),
                     container=Depends(get_container)) -> dict:
    """Drain pending jobs synchronously (useful for testing / headless)."""
    count = container.worker.drain(ctx.project_id)
    return {"processed": count}


@router.get("/projects/{project_id}/jobs/{job_id}")
def get_job(job_id: str,
            ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    job = ctx.repo.get_job(job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job
