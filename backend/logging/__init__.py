"""Structured logging for VisionAI.

Every important operation records timestamp, component, action, status,
duration and error context. Logging is JSON-structured by default so it can
be ingested/machine-parsed, with a plain-text fallback.
"""
from backend.logging.logger import get_logger, configure_logging

__all__ = ["get_logger", "configure_logging"]
