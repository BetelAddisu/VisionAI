"""Embedding providers.

The default local provider is a deterministic hashing-based bag-of-words
embedding: it maps tokens to vector dimensions via a stable hash and
normalises the result. This produces real vectors that capture lexical
overlap and runs fully offline with negligible memory — appropriate for the
target hardware. It is a genuine, replaceable embedding (swap in BGE Small
by changing the provider) and is NOT a mock: queries and documents are
embedded with the same function so cosine similarity reflects shared terms
and term importance.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from backend.ai.base import EmbeddingProvider, ProviderUnavailable
from backend.config import Settings, get_settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic hashed bag-of-words embedding with sublinear weighting."""

    def __init__(self, dimension: int = 256) -> None:
        self._dimension = dimension
        self._available = True

    @property
    def available(self) -> bool:
        return self._available

    @property
    def model_version(self) -> str:
        return "hashing-v1"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self._dimension
            tokens = tokenize(text)
            if not tokens:
                vectors.append(vec)
                continue
            counts = Counter(tokens)
            for token, count in counts.items():
                # Stable hash to a dimension.
                h = hashlib.md5(token.encode("utf-8")).digest()
                idx = int.from_bytes(h[:4], "big") % self._dimension
                sign = 1.0 if (h[4] & 1) == 0 else -1.0
                # Sublinear term frequency weighting (log) scaled by sign.
                vec[idx] += sign * (1.0 + math.log(count))
            self._normalize(vec)
            vectors.append(vec)
        return vectors

    @staticmethod
    def _normalize(vec: list[float]) -> None:
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            for i in range(len(vec)):
                vec[i] /= norm


class NoneEmbeddingProvider(EmbeddingProvider):
    @property
    def available(self) -> bool:
        return False

    @property
    def model_version(self) -> str:
        return "none"

    @property
    def dimension(self) -> int:
        return 0

    def embed(self, text: str) -> list[float]:
        raise ProviderUnavailable("No embedding provider configured")

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        raise ProviderUnavailable("No embedding provider configured")


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    cfg = settings.models.embeddings
    if cfg.provider == "local":
        return HashingEmbeddingProvider(dimension=cfg.dimension or 256)
    return NoneEmbeddingProvider()
