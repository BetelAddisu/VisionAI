"""Transcription stage: delegates to the configured speech provider."""
from __future__ import annotations

from pathlib import Path

from backend.ai import SpeechProvider, TranscriptSegment


def transcribe_audio(audio_path: str | Path, speech: SpeechProvider) -> list[TranscriptSegment]:
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    return speech.transcribe(str(audio_path))
