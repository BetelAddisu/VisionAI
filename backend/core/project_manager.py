"""Project Manager.

Creates, opens, lists and deletes isolated user projects. Each project owns
a directory on disk containing its SQLite database, cache and exports. The
Project Manager never performs AI processing — it only manages lifecycle and
paths, per 01-system-architecture.md.
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from backend.config import Settings, get_settings
from backend.database import Database, Repository, get_project_db_path
from backend.logging import get_logger

log = get_logger("project_manager")


@dataclass
class ProjectContext:
    """A loaded project with its database and repository ready to use."""

    project_id: str
    name: str
    folder_path: str
    cache_path: str
    exports_path: str
    db: Database
    repo: Repository

    def close(self) -> None:
        self.db.close()


class ProjectManager:
    """Manages project lifecycle and per-project database instances."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.projects_path = self.settings.projects_path
        self.projects_path.mkdir(parents=True, exist_ok=True)
        # Cache of opened project contexts.
        self._open: dict[str, ProjectContext] = {}

    # ---- Path helpers ---------------------------------------------------
    def project_dir(self, project_id: str) -> Path:
        return self.projects_path / project_id

    def _project_json_path(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "project.json"

    # ---- Lifecycle ------------------------------------------------------
    def create_project(self, name: str, folder_path: str, *,
                        description: str = "",
                        default_platform: str = "youtube",
                        editing_style: str = "balanced") -> ProjectContext:
        if not Path(folder_path).exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")
        project_id = uuid.uuid4().hex
        pdir = self.project_dir(project_id)
        cache_path = pdir / "cache"
        exports_path = pdir / "exports"
        for sub in (pdir, cache_path, exports_path,
                    cache_path / "thumbnails", cache_path / "audio",
                    cache_path / "frames", cache_path / "scenes",
                    cache_path / "embeddings", cache_path / "analysis",
                    exports_path / "xml", exports_path / "srt", exports_path / "otio"):
            sub.mkdir(parents=True, exist_ok=True)

        db = Database(get_project_db_path(pdir), wal_mode=self.settings.database.wal_mode)
        db.run_migrations()
        repo = Repository(db)
        repo.create_project(
            id=project_id, name=name, description=description,
            folder_path=str(Path(folder_path).resolve()),
            cache_path=str(cache_path), exports_path=str(exports_path),
            default_platform=default_platform, editing_style=editing_style,
        )
        self._write_project_json(project_id, name, folder_path)
        ctx = ProjectContext(
            project_id=project_id, name=name,
            folder_path=str(Path(folder_path).resolve()),
            cache_path=str(cache_path), exports_path=str(exports_path),
            db=db, repo=repo,
        )
        self._open[project_id] = ctx
        log.info("project created", extra={
            "action": "create_project", "status": "done", "project_id": project_id})
        return ctx

    def open_project(self, project_id: str) -> ProjectContext:
        if project_id in self._open:
            return self._open[project_id]
        pdir = self.project_dir(project_id)
        if not pdir.exists():
            raise FileNotFoundError(f"Project not found: {project_id}")
        db = Database(get_project_db_path(pdir), wal_mode=self.settings.database.wal_mode)
        db.run_migrations()
        repo = Repository(db)
        project = repo.get_project(project_id)
        if not project:
            raise FileNotFoundError(f"Project record missing: {project_id}")
        ctx = ProjectContext(
            project_id=project_id, name=project["name"],
            folder_path=project["folder_path"], cache_path=project["cache_path"],
            exports_path=project["exports_path"], db=db, repo=repo,
        )
        self._open[project_id] = ctx
        log.info("project opened", extra={
            "action": "open_project", "status": "done", "project_id": project_id})
        return ctx

    def get_context(self, project_id: str) -> ProjectContext:
        return self.open_project(project_id)

    def close_project(self, project_id: str) -> None:
        ctx = self._open.pop(project_id, None)
        if ctx:
            ctx.close()

    def list_projects(self) -> list[dict]:
        projects = []
        for entry in sorted(self.projects_path.iterdir()):
            if not entry.is_dir():
                continue
            try:
                db = Database(get_project_db_path(entry), wal_mode=self.settings.database.wal_mode)
                repo = Repository(db)
                project = repo.get_project(entry.name)
                db.close()
                if project:
                    projects.append(project)
            except Exception as exc:  # noqa: BLE001
                log.warning("failed to read project", extra={
                    "project_id": entry.name, "error": str(exc)})
        return projects

    def delete_project(self, project_id: str) -> None:
        self.close_project(project_id)
        pdir = self.project_dir(project_id)
        if pdir.exists():
            shutil.rmtree(pdir)
            log.info("project deleted", extra={
                "action": "delete_project", "status": "done", "project_id": project_id})

    def _write_project_json(self, project_id: str, name: str, folder_path: str) -> None:
        payload = {"id": project_id, "name": name, "folder_path": folder_path}
        self._project_json_path(project_id).write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
