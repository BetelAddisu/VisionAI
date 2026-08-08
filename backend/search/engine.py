"""Search engine combining keyword, semantic, visual and metadata retrieval.

Never invents footage: every result references a real transcript segment /
scene / video in the database. Falls back to keyword-only search when
embeddings are unavailable.
"""
from __future__ import annotations

import math
import struct
from collections import defaultdict

from backend.ai import EmbeddingProvider, ProviderUnavailable, get_embedding_provider
from backend.config import Settings, get_settings
from backend.core import ProjectContext
from backend.logging import get_logger
from backend.search.query_parser import clean_query, extract_keywords, fts_query
from backend.search.ranking import rank
from backend.search.types import SearchFilters, SearchResult

log = get_logger("search")


class SearchEngine:
    def __init__(self, ctx: ProjectContext, settings: Settings | None = None,
                 embeddings: EmbeddingProvider | None = None) -> None:
        self.ctx = ctx
        self.settings = settings or get_settings()
        self.embeddings = embeddings or get_embedding_provider(self.settings)

    def search(self, query: str, filters: SearchFilters | None = None,
               limit: int = 20) -> list[SearchResult]:
        filters = filters or SearchFilters()
        keywords = extract_keywords(query)
        cleaned = clean_query(query)
        log.info("search", extra={
            "project_id": self.ctx.project_id, "action": "search",
            "query": query, "keywords": keywords})

        # Gather candidate segments with per-signal scores.
        candidates: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        meta: dict[str, dict] = {}

        # 1. Keyword search via FTS5.
        fts = fts_query(query)
        if fts:
            for row in self.ctx.repo.search_transcript_fts(self.ctx.project_id, fts, limit=200):
                key = row["id"]
                # BM25-ish rank: FTS5 rank is negative (lower = better).
                keyword_score = 1.0 / (1.0 + abs(row["rank"]))
                candidates[key]["keyword"] = max(candidates[key]["keyword"], keyword_score)
                meta[key] = dict(row)

        # 2. Semantic search over stored embeddings.
        semantic_hits: dict[str, float] = {}
        if self.embeddings.available and cleaned:
            try:
                query_vec = self.embeddings.embed(cleaned)
                semantic_hits = self._semantic_search(query_vec, limit=200)
            except ProviderUnavailable as exc:
                log.info("semantic search unavailable, falling back to keyword", extra={
                    "error": str(exc)})

        # Map semantic hits (source_id) to transcript segments.
        for source_id, score in semantic_hits.items():
            seg = self.ctx.repo.query_one(
                "SELECT * FROM transcript_segments WHERE id = ?;", (source_id,))
            if seg:
                key = seg["id"]
                candidates[key]["semantic"] = max(candidates[key]["semantic"], float(score))
                if key not in meta:
                    meta[key] = dict(seg)

        # If no candidates from FTS or semantic, try a broad LIKE fallback on text.
        if not candidates and keywords:
            like = "%" + "%".join(keywords) + "%"
            rows = self.ctx.repo.query_all(
                """SELECT * FROM transcript_segments
                   WHERE text LIKE ? LIMIT 200;""", (like,))
            for row in rows:
                key = row["id"]
                # Count matched keywords as a weak signal.
                text_lower = (row["text"] or "").lower()
                matched = sum(1 for k in keywords if k in text_lower)
                candidates[key]["keyword"] = matched / max(1, len(keywords))
                meta[key] = dict(row)

        # 3. Build results with metadata filters and ranking.
        results: list[SearchResult] = []
        for key, scores in candidates.items():
            row = meta.get(key)
            if not row:
                continue
            video = self.ctx.repo.get_video(row["video_id"])
            if not video:
                continue
            if filters.video_id and video["id"] != filters.video_id:
                continue
            if filters.category and video.get("media_category") != filters.category:
                continue
            if filters.min_duration and video["duration"] < filters.min_duration:
                continue
            if filters.max_duration and video["duration"] > filters.max_duration:
                continue
            # Quality score from quality_metrics aggregated for the video.
            quality = self._video_quality(video["id"])
            if filters.min_quality and quality < filters.min_quality:
                continue
            scores["quality"] = quality
            scores.setdefault("visual", 0.0)
            scores.setdefault("recency", self._recency(video))
            final = rank(scores, self.settings)
            snippet = self._snippet(row["text"], keywords)
            padding = self.settings.search.result_context_padding
            start = max(0.0, float(row["start_time"]) - padding)
            end = float(row["end_time"]) + padding
            results.append(SearchResult(
                video_id=video["id"], filename=video["filename"], path=video["path"],
                start_time=start, end_time=end, score=final,
                reason=self._reason(row["text"], scores),
                transcript_snippet=snippet, thumbnail_path=video.get("thumbnail_path"),
                matched_terms=[k for k in keywords if k in (row["text"] or "").lower()],
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:limit]
        self.ctx.repo.add_search_history(
            project_id=self.ctx.project_id, query=query, result_count=len(results))
        return results

    def _semantic_search(self, query_vec: list[float], limit: int) -> dict[str, float]:
        dim = len(query_vec)
        qmag = math.sqrt(sum(v * v for v in query_vec)) or 1.0
        hits: dict[str, float] = {}
        for emb in self.ctx.repo.list_embeddings(source_type="transcript"):
            vec = self._blob_to_vector(emb["vector"], dim)
            if not any(vec):
                continue
            dot = sum(a * b for a, b in zip(query_vec, vec))
            vmag = math.sqrt(sum(v * v for v in vec)) or 1.0
            cos = dot / (qmag * vmag)
            # Cosine in [-1,1]; map to [0,1].
            score = (cos + 1.0) / 2.0
            hits[emb["source_id"]] = max(hits.get(emb["source_id"], 0.0), score)
        return dict(sorted(hits.items(), key=lambda kv: kv[1], reverse=True)[:limit])

    @staticmethod
    def _blob_to_vector(blob: bytes, dimension: int) -> list[float]:
        if not blob:
            return [0.0] * dimension
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob[: count * 4]))

    def _video_quality(self, video_id: str) -> float:
        rows = self.ctx.repo.query_all(
            """SELECT q.sharpness, q.contrast, (1 - q.noise_score) AS clean
               FROM quality_metrics q JOIN frames f ON f.id = q.frame_id
               WHERE f.video_id = ?;""", (video_id,))
        if not rows:
            return 0.5
        total = sum((r["sharpness"] + r["contrast"] + r["clean"]) / 3.0 for r in rows)
        return total / len(rows)

    @staticmethod
    def _recency(video: dict) -> float:
        """Recency score 0-1 based on modified_at (newer -> higher).."""
        created = video.get("modified_at") or video.get("created_at") or ""
        if not created:
            return 0.0
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).days
            return max(0.0, 1.0 - age_days / 365.0)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _snippet(text: str, keywords: list[str], max_len: int = 160) -> str:
        text = (text or "").strip()
        if len(text) <= max_len:
            return text
        # Try to center on the first matched keyword.
        lower = text.lower()
        pos = -1
        for k in keywords:
            p = lower.find(k)
            if p >= 0:
                pos = p
                break
        if pos < 0:
            return text[:max_len] + "…"
        start = max(0, pos - max_len // 3)
        end = min(len(text), start + max_len)
        snippet = text[start:end]
        if start > 0:
            snippet = "…" + snippet
        if end < len(text):
            snippet = snippet + "…"
        return snippet

    @staticmethod
    def _reason(text: str, scores: dict[str, float]) -> str:
        parts = []
        if scores.get("keyword", 0) > 0:
            parts.append("keyword match")
        if scores.get("semantic", 0) > 0.5:
            parts.append("semantic similarity")
        if scores.get("visual", 0) > 0:
            parts.append("visual match")
        if not parts:
            parts.append("transcript relevance")
        return "Matches via " + " + ".join(parts)
