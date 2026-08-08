"""Job handler registrations.

Kept at the top level (not inside backend/jobs) to avoid circular imports
between the worker and the pipeline/indexer/planner modules.
"""
from __future__ import annotations


def register_all(worker) -> None:
    from backend.jobs_handlers.handlers import (
        handle_analyze_video,
        handle_index,
        handle_plan,
    )
    worker.register("index", handle_index)
    worker.register("analyze_video", handle_analyze_video)
    worker.register("plan", handle_plan)
