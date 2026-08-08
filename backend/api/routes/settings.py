"""Settings routes: project + app configuration."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_project_context
from backend.config import get_settings
from backend.core import ProjectContext

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("/projects/{project_id}/settings")
def list_settings(ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    return ctx.repo.get_all_settings()


@router.put("/projects/{project_id}/settings")
def set_setting(payload: SettingUpdate,
                ctx: ProjectContext = Depends(get_project_context)) -> dict:
    ctx.repo.set_setting(payload.key, payload.value)
    return {"ok": True, "key": payload.key}


@router.get("/settings/app")
def app_settings() -> dict[str, Any]:
    settings = get_settings()
    return {
        "app": settings.app.model_dump(),
        "indexing": settings.indexing.model_dump(),
        "pipeline": settings.pipeline.model_dump(),
        "proxy": settings.proxy.model_dump(),
        "models": settings.models.model_dump(),
        "search": settings.search.model_dump(),
    }
