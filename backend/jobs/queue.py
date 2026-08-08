"""Job queue: thin wrapper over the repository job table."""
from __future__ import annotations

from typing import Any

from backend.core import ProjectContext
from backend.database import Repository


class JobQueue:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def enqueue(self, *, project_id: str, job_type: str, video_id: str | None = None,
                payload: dict | None = None) -> str:
        return self.repo.create_job(
            project_id=project_id, job_type=job_type, video_id=video_id, payload=payload)

    def claim_next(self, project_id: str) -> dict[str, Any] | None:
        return self.repo.claim_next_job(project_id)

    def update(self, job_id: str, *, status: str | None = None,
               progress: float | None = None, error: str | None = None) -> None:
        self.repo.update_job(job_id, status=status, progress=progress, error=error)

    def list(self, project_id: str, status: str | None = None) -> list[dict[str, Any]]:
        return self.repo.list_jobs(project_id, status=status)

    def cancel(self, job_id: str) -> None:
        self.repo.update_job(job_id, status="cancelled")


def queue_for(ctx: ProjectContext) -> JobQueue:
    return JobQueue(ctx.repo)
