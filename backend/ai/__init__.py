"""AI provider interfaces.

Each provider has one responsibility and is independently replaceable
(01-system-architecture.md, Layer 4). Providers report unavailable cleanly
rather than faking results: when provider == "none" they raise
``ProviderUnavailable`` so callers can handle the missing capability.
"""
from backend.ai.base import (
    EmbeddingProvider,
    LLMProvider,
    LLMResponse,
    ProviderUnavailable,
    SpeechProvider,
    TranscriptSegment,
    VisionDescription,
    VisionProvider,
)
from backend.ai.embedding import get_embedding_provider
from backend.ai.planner import get_llm_provider
from backend.ai.speech import get_speech_provider
from backend.ai.vision import get_vision_provider

__all__ = [
    "ProviderUnavailable",
    "TranscriptSegment",
    "SpeechProvider",
    "VisionProvider",
    "EmbeddingProvider",
    "LLMProvider",
    "VisionDescription",
    "LLMResponse",
    "get_speech_provider",
    "get_vision_provider",
    "get_embedding_provider",
    "get_llm_provider",
]
