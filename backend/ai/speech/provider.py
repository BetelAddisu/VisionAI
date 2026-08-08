"""Local speech transcription via faster-whisper.

The model is loaded lazily on first use and released after use to respect
the RAM constraint (never keep multiple large models loaded). Model choice
is configurable (tiny/base/small/medium).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.ai.base import ProviderUnavailable, SpeechProvider, TranscriptSegment
from backend.config import Settings, get_settings
from backend.logging import get_logger

log = get_logger("speech")


class LocalWhisperProvider(SpeechProvider):
    """Wraps faster-whisper. Models download on first use (HuggingFace cache)."""

    def __init__(self, model: str = "small", device: str = "cpu",
                 compute_type: str = "int8") -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._model: Any | None = None
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                import faster_whisper  # noqa: F401
                self._available = True
            except ImportError:
                self._available = False
        return self._available

    @property
    def model_version(self) -> str:
        return f"faster-whisper:{self._model_name}"

    def _load(self) -> Any:
        if not self.available:
            raise ProviderUnavailable("faster-whisper is not installed")
        if self._model is None:
            from faster_whisper import WhisperModel
            log.info("loading whisper model", extra={
                "action": "load_model", "status": "start", "model": self._model_name})
            self._model = WhisperModel(
                self._model_name, device=self._device, compute_type=self._compute_type)
            log.info("whisper model loaded", extra={
                "action": "load_model", "status": "done", "model": self._model_name})
        return self._model

    def unload(self) -> None:
        if self._model is not None:
            self._model = None
            log.info("whisper model unloaded", extra={"action": "unload_model"})

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        model = self._load()
        try:
            segments_iter, info = model.transcribe(
                audio_path, beam_size=5, vad_filter=True)
            language = info.language if hasattr(info, "language") else ""
            segments: list[TranscriptSegment] = []
            for seg in segments_iter:
                text = (seg.text or "").strip()
                if not text:
                    continue
                segments.append(TranscriptSegment(
                    start=float(seg.start), end=float(seg.end),
                    text=text, confidence=float(getattr(seg, "avg_logprob", 0)),
                    language=language,
                ))
            return segments
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailable(f"transcription failed: {exc}") from exc


class NoneSpeechProvider(SpeechProvider):
    """No-op provider used when speech is unconfigured."""

    @property
    def available(self) -> bool:
        return False

    @property
    def model_version(self) -> str:
        return "none"

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        raise ProviderUnavailable("No speech provider configured")


def get_speech_provider(settings: Settings | None = None) -> SpeechProvider:
    settings = settings or get_settings()
    cfg = settings.models.speech
    if cfg.provider == "local":
        return LocalWhisperProvider(
            model=cfg.model or "small", device=cfg.device,
            compute_type=cfg.compute_type)
    return NoneSpeechProvider()
