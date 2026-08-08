"""API routes aggregator."""
from fastapi import APIRouter

from backend.api.routes import (
    jobs,
    planner,
    projects,
    search,
    settings as settings_routes,
    timeline,
    videos,
)

router = APIRouter()
router.include_router(projects.router, tags=["projects"])
router.include_router(videos.router, tags=["videos"])
router.include_router(jobs.router, tags=["jobs"])
router.include_router(search.router, tags=["search"])
router.include_router(planner.router, tags=["planner"])
router.include_router(timeline.router, tags=["timeline"])
router.include_router(settings_routes.router, tags=["settings"])
