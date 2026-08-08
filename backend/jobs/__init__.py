"""Job queue and worker.

On the minimum target hardware only one heavy AI job runs at a time. Jobs
have id, project_id, type, status, progress, timestamps, error and
retry_count. The worker processes pending jobs sequentially and keeps the UI
responsive by running off the request thread.
"""
from backend.jobs.queue import JobQueue, queue_for
from backend.jobs.types import JobStatus, JobType
from backend.jobs.worker import JobWorker

__all__ = ["JobQueue", "queue_for", "JobWorker", "JobStatus", "JobType"]
