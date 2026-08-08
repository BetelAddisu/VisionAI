"""FastAPI application factory."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.config import get_settings
from backend.logging import configure_logging, get_logger

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "static"


def create_app(container=None) -> FastAPI:
    settings = get_settings()
    configure_logging(level=settings.logging.level, fmt=settings.logging.format,
                      log_dir=str(settings.logs_path))
    log = get_logger("api")

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="Local-first AI video post-production assistant.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if container is None:
        from backend.app_container import AppContainer
        container = AppContainer()

    app.state.container = container
    app.include_router(router, prefix="/api")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app.name,
                "version": settings.app.version}

    @app.get("/api/projects/{project_id}/videos/{video_id}/thumbnail")
    def video_thumbnail(project_id: str, video_id: str):
        ctx = container.project_manager.open_project(project_id)
        video = ctx.repo.get_video(video_id)
        if not video or not video.get("thumbnail_path"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        thumb = Path(video["thumbnail_path"])
        if not thumb.exists():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Thumbnail file missing")
        return FileResponse(thumb)

    # Serve the frontend SPA (static files, no build step).
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/")
        def index():
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/app/{full_path:path}")
        def spa(full_path: str):
            # Client-side routing fallback.
            return FileResponse(STATIC_DIR / "index.html")

    log.info("application created", extra={"action": "startup", "status": "done"})
    return app
