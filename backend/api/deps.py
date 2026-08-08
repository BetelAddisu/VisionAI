"""Shared API dependencies."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request

from backend.core import ProjectContext

if TYPE_CHECKING:
    from backend.app_container import AppContainer


def get_container(request: Request):
    return request.app.state.container


def get_project_context(project_id: str,
                        container=Depends(get_container)) -> ProjectContext:
    try:
        return container.project_manager.open_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
