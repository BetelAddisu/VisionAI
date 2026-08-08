"""Planner routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_project_context
from backend.core import ProjectContext
from backend.planner import AIPlanner, PlanInput

router = APIRouter()


class PlanRequest(BaseModel):
    brief: str
    script: str = ""
    audience: str = ""
    platform: str = "youtube"
    target_length: str = ""
    style: str = ""


@router.post("/projects/{project_id}/plan")
def create_plan(payload: PlanRequest,
                ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    planner = AIPlanner(ctx)
    session_id, plan = planner.create_plan(PlanInput(
        brief=payload.brief, script=payload.script, audience=payload.audience,
        platform=payload.platform, target_length=payload.target_length,
        style=payload.style))
    return {"session_id": session_id, "plan": plan.to_dict()}


@router.get("/projects/{project_id}/plans")
def list_plans(ctx: ProjectContext = Depends(get_project_context)) -> list[dict[str, Any]]:
    return ctx.repo.list_planner_sessions(ctx.project_id)


@router.get("/projects/{project_id}/plans/{session_id}")
def get_plan(session_id: str,
             ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    session = ctx.repo.get_planner_session(session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Plan session not found")
    return session
