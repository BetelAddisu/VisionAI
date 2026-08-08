"""Single-worker job processor.

Handlers are registered against job types. The worker claims one pending job
at a time, runs its handler, and records the outcome. This enforces the
hardware rule: only one heavy AI job executes at once.
"""
from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Callable

from backend.core import ProjectManager
from backend.jobs.queue import JobQueue
from backend.logging import get_logger

log = get_logger("worker")

JobHandler = Callable[[dict[str, Any], Any], None]


class JobWorker:
    def __init__(self, project_manager: ProjectManager) -> None:
        self.project_manager = project_manager
        self._handlers: dict[str, JobHandler] = {}
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._running_project: str | None = None

    def register(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    def handlers(self) -> dict[str, JobHandler]:
        return dict(self._handlers)

    def process_one(self, project_id: str) -> bool:
        """Claim and run a single pending job. Returns True if a job ran."""
        ctx = self.project_manager.open_project(project_id)
        queue = JobQueue(ctx.repo)
        job = queue.claim_next(project_id)
        if not job:
            return False
        self._running_project = project_id
        log.info("job started", extra={
            "job_id": job["id"], "project_id": project_id,
            "action": job["job_type"], "status": "running"})
        handler = self._handlers.get(job["job_type"])
        try:
            if handler is None:
                raise RuntimeError(f"No handler registered for job type {job['job_type']}")
            handler(job, ctx)
            queue.update(job["id"], status="completed", progress=1.0)
            log.info("job completed", extra={
                "job_id": job["id"], "project_id": project_id,
                "action": job["job_type"], "status": "done"})
        except Exception as exc:  # noqa: BLE001
            tb = traceback.format_exc()
            queue.update(job["id"], status="failed", error=str(exc))
            log.error("job failed", extra={
                "job_id": job["id"], "project_id": project_id,
                "action": job["job_type"], "status": "failed", "error": str(exc)})
            log.debug(tb)
        finally:
            self._running_project = None
        return True

    def drain(self, project_id: str, max_iterations: int = 1000) -> int:
        """Run all pending jobs for a project synchronously. Returns count."""
        count = 0
        for _ in range(max_iterations):
            if not self.process_one(project_id):
                break
            count += 1
        return count

    def start_background(self, project_id: str, poll_interval: float = 1.0) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop() -> None:
            while not self._stop.is_set():
                try:
                    if not self.process_one(project_id):
                        time.sleep(poll_interval)
                except Exception as exc:  # noqa: BLE001
                    log.error("worker loop error", extra={"error": str(exc)})
                    time.sleep(poll_interval)

        self._stop.clear()
        self._thread = threading.Thread(target=_loop, daemon=True, name="visionai-worker")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5.0)

    @property
    def is_running(self) -> bool:
        return self._running_project is not None
