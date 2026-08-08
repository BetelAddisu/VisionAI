"""Job type and status enumerations."""
from __future__ import annotations

from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    INDEX = "index"
    THUMBNAIL = "thumbnail"
    SCENE_DETECT = "scene_detect"
    AUDIO_EXTRACT = "audio_extract"
    TRANSCRIBE = "transcribe"
    AUDIO_ANALYSIS = "audio_analysis"
    FRAME_SAMPLE = "frame_sample"
    VISION_ANALYSIS = "vision_analysis"
    QUALITY_ANALYSIS = "quality_analysis"
    EMBEDDINGS = "embeddings"
    ANALYZE_VIDEO = "analyze_video"
    PROXY_GENERATE = "proxy_generate"
    PLAN = "plan"
    BUILD_TIMELINE = "build_timeline"
    EXPORT = "export"
