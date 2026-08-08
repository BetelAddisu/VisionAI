"""Speech provider package."""
from backend.ai.speech.provider import (
    LocalWhisperProvider,
    NoneSpeechProvider,
    get_speech_provider,
)

__all__ = ["get_speech_provider", "LocalWhisperProvider", "NoneSpeechProvider"]
