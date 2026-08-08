"""Base provider interfaces and shared types.

Providers are tools, not the application. The pipeline prepares context,
calls a provider, validates the response, and stores the result. Every
provider method is typed and may raise ``ProviderUnavailable`` when its
backing model is not configured/installed.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderUnavailable(RuntimeError):
    """Raised when a provider's backing model is not available.

    Callers must handle this and fall back gracefully (e.g. search falls
    back to keyword-only when embeddings are unavailable). This must never
    be hidden behind a fake result.
    """


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float = 0.0
    language: str = ""
    speaker: str = ""


@dataclass
class VisionDescription:
    description: str
    objects: list[str]
    shot_type: str = ""
    lighting: str = ""
    composition: str = ""


@dataclass
class LLMResponse:
    text: str
    valid: bool = True
    error: str = ""


class SpeechProvider(ABC):
    """Converts audio into timestamped transcript segments."""

    @property
    @abstractmethod
    def available(self) -> bool: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @abstractmethod
    def transcribe(self, audio_path: str) -> list[TranscriptSegment]: ...


class VisionProvider(ABC):
    """Describes a single image frame."""

    @property
    @abstractmethod
    def available(self) -> bool: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @abstractmethod
    def describe_frame(self, image_path: str) -> VisionDescription: ...


class EmbeddingProvider(ABC):
    """Embeds text into a fixed-dimension vector."""

    @property
    @abstractmethod
    def available(self) -> bool: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    def embed_many(self, texts: list[str]) -> list[list[float]]: ...


class LLMProvider(ABC):
    """Generates text from a prompt (used by the planner)."""

    @property
    @abstractmethod
    def available(self) -> bool: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 *, max_tokens: int = 2048, temperature: float = 0.3) -> LLMResponse: ...
