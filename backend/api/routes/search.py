"""Search routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_project_context
from backend.core import ProjectContext
from backend.search import SearchEngine, SearchFilters

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    category: str | None = None
    min_duration: float | None = None
    max_duration: float | None = None
    video_id: str | None = None
    min_quality: float | None = None
    limit: int = 20


@router.post("/projects/{project_id}/search")
def search(payload: SearchRequest,
           ctx: ProjectContext = Depends(get_project_context)) -> dict[str, Any]:
    engine = SearchEngine(ctx)
    filters = SearchFilters(
        category=payload.category, min_duration=payload.min_duration,
        max_duration=payload.max_duration, video_id=payload.video_id,
        min_quality=payload.min_quality)
    results = engine.search(payload.query, filters=filters, limit=payload.limit)
    return {"query": payload.query, "count": len(results),
            "results": [r.to_dict() for r in results]}
