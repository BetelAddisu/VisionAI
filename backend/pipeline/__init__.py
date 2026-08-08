"""Analysis pipeline: resumable, per-stage processing.

Each stage records status in analysis_state so processing resumes from the
last incomplete stage after a crash. Only one heavy AI job runs at a time.
"""
from backend.pipeline.orchestrator import AnalysisPipeline, STAGES

__all__ = ["AnalysisPipeline", "STAGES"]
