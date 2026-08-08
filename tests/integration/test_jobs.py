"""Integration test: job recovery and individual retries."""
from __future__ import annotations

from backend.app_container import AppContainer


def test_job_drain_processes_pending(indexed_project, tmp_settings):
    ctx = indexed_project
    container = AppContainer()
    # The indexed_project fixture enqueued analyze_video jobs.
    count = container.worker.drain(ctx.project_id)
    # analyze_video jobs will fail (no speech provider / audio) but they run.
    assert count >= 2
    jobs = ctx.repo.list_jobs(ctx.project_id)
    for job in jobs:
        assert job["status"] in ("completed", "failed", "skipped", "pending")


def test_failed_job_does_not_block_others(indexed_project, tmp_settings):
    """If one job fails, subsequent jobs still process."""
    ctx = indexed_project
    container = AppContainer()
    count = container.worker.drain(ctx.project_id)
    assert count >= 2
    statuses = {j["status"] for j in ctx.repo.list_jobs(ctx.project_id)}
    # Not all stuck in pending.
    assert statuses != {"pending"}
