"""Project routes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.deps import get_container, get_project_context
from backend.core import ProjectContext

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    folder_path: str
    description: str = ""
    default_platform: str = "youtube"
    editing_style: str = "balanced"


class IndexResponse(BaseModel):
    job_id: str
    discovered: int
    added: int
    updated: int
    unchanged: int
    skipped: int
    failed: list[str]


@router.post("/projects")
def create_project(payload: ProjectCreate,
                   container=Depends(get_container)) -> dict[str, Any]:
    if not Path(payload.folder_path).exists():
        raise HTTPException(status_code=400, detail="Folder does not exist")
    ctx = container.project_manager.create_project(
        name=payload.name, folder_path=payload.folder_path,
        description=payload.description, default_platform=payload.default_platform,
        editing_style=payload.editing_style)
    return ctx.repo.get_project(ctx.project_id)


@router.get("/projects")
def list_projects(container=Depends(get_container)) -> list[dict[str, Any]]:
    return container.project_manager.list_projects()


@router.get("/projects/{project_id}")
def get_project(ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    return ctx.repo.get_project(ctx.project_id)


@router.delete("/projects/{project_id}")
def delete_project(project_id: str,
                   container=Depends(get_container)) -> dict:
    container.project_manager.delete_project(project_id)
    return {"deleted": True, "project_id": project_id}


@router.post("/projects/{project_id}/index")
def index_project(run_async: bool = True,
                  ctx: ProjectContext = Depends(get_project_context),
                  container=Depends(get_container)) -> dict[str, Any]:
    """Enqueue (or run synchronously) indexing for the project folder."""
    if not run_async:
        from backend.indexing import VideoIndexer
        result = VideoIndexer(ctx).index_project()
        return result.__dict__ | {"job_id": None}
    job_id = ctx.repo.create_job(
        project_id=ctx.project_id, job_type="index")
    container.worker.start_background(ctx.project_id)
    return {"job_id": job_id, "status": "pending"}
