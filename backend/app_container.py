"""Application container: wires together services and registers job handlers.

Holds a ProjectManager and a JobWorker with handlers for indexing and
analysis. This is the composition root — the only place that knows how the
modules fit together.
"""
from __future__ import annotations

from fastapi import FastAPI

from backend.api import create_app
from backend.core import ProjectManager
from backend.jobs import JobWorker
from backend.jobs.types import JobType

__all__ = ["AppContainer", "create_app", "create_container"]


class AppContainer:
    def __init__(self) -> None:
        self.project_manager = ProjectManager()
        self.worker = JobWorker(self.project_manager)
        self._register_handlers()

    def _register_handlers(self) -> None:
        from backend.jobs_handlers import register_all
        register_all(self.worker)

    def get_app(self) -> FastAPI:
        return create_app(self)


def create_container() -> AppContainer:
    return AppContainer()
