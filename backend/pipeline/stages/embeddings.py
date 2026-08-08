"""Embeddings stage: embed transcript segments and store vectors.

Vectors are stored as blobs in SQLite (the embeddings table) so the search
engine can compute similarity directly. This keeps a single source of truth
while remaining dependency-light (no FAISS required on minimal hardware);
FAISS can be added later as an index optimization.
"""
from __future__ import annotations

import struct

from backend.ai import EmbeddingProvider, TranscriptSegment
from backend.core import ProjectContext


def vector_to_blob(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def blob_to_vector(blob: bytes, dimension: int) -> list[float]:
    if not blob:
        return [0.0] * dimension
    return list(struct.unpack(f"{dimension}f", blob))


def embed_transcript_segments(ctx: ProjectContext, video_id: str,
                              segments: list[TranscriptSegment],
                              embeddings: EmbeddingProvider) -> int:
    """Embed each transcript segment and store it. Returns count stored."""
    if not embeddings.available:
        return 0
    # Delete old transcript embeddings for this video.
    ctx.repo.execute(
        "DELETE FROM embeddings WHERE video_id = ? AND source_type = 'transcript';",
        (video_id,),
    )
    texts = [seg.text for seg in segments]
    if not texts:
        return 0
    vectors = embeddings.embed_many(texts)
    count = 0
    for seg, vec in zip(segments, vectors):
        # The segment row must exist; store its id. We look it up by time.
        row = ctx.repo.query_one(
            "SELECT id FROM transcript_segments WHERE video_id = ? AND start_time = ? LIMIT 1;",
            (video_id, seg.start),
        )
        source_id = row["id"] if row else ""
        ctx.repo.add_embedding(
            source_type="transcript", source_id=source_id, video_id=video_id,
            vector=vector_to_blob(vec), model_version=embeddings.model_version)
        count += 1
    return count
