"""File hashing for change detection.

Two-stage strategy (04-video-indexer.md):
- Stage 1: a fast fingerprint from filename + size + mtime. If unchanged,
  the expensive full hash can be skipped.
- Stage 2: SHA-256 of file contents, computed in streaming chunks so we
  never load a multi-GB video into memory.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from backend.config import Settings, get_settings


@dataclass
class FileIdentity:
    fingerprint: str
    hash: str


def compute_fingerprint(path: str | Path) -> str:
    """Fast fingerprint: filename, size, mtime."""
    p = Path(path)
    stat = p.stat()
    return f"{p.name}|{stat.st_size}|{int(stat.st_mtime)}"


def compute_hash(path: str | Path, settings: Settings | None = None) -> str:
    """Streaming SHA-256 hash of the file contents."""
    settings = settings or get_settings()
    chunk_size = settings.indexing.hash_chunk_size_mb * 1024 * 1024
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def identity_changed(stored_fingerprint: str | None, stored_hash: str | None,
                     path: str | Path) -> bool:
    """Return True if the file changed since it was indexed.

    If only the fingerprint matches we can skip the full hash comparison.
    """
    if not stored_fingerprint:
        return True
    current_fp = compute_fingerprint(path)
    if current_fp != stored_fingerprint:
        return True
    # Fingerprint unchanged and we have a stored hash -> treat as unchanged.
    return False


def resolve_identity(path: str | Path, stored_fingerprint: str | None,
                     settings: Settings | None = None) -> FileIdentity:
    """Compute fingerprint always; compute full hash only when needed."""
    settings = settings or get_settings()
    fingerprint = compute_fingerprint(path)
    if stored_fingerprint and stored_fingerprint == fingerprint:
        # Reuse: we cannot recompute the stored hash cheaply, so return a
        # marker indicating the hash is unchanged by passing the fingerprint.
        return FileIdentity(fingerprint=fingerprint, hash=stored_fingerprint or "")
    full_hash = compute_hash(path, settings)
    return FileIdentity(fingerprint=fingerprint, hash=full_hash)


def is_likely_duplicate(path: str | Path, known_hashes: set[str],
                        settings: Settings | None = None) -> bool:
    """Check whether a file's hash matches a known hash (duplicate detection)."""
    full_hash = compute_hash(path, settings)
    return full_hash in known_hashes
