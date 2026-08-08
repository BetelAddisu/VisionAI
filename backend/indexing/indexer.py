"""Video Indexer controller.

Coordinates scanner -> validator -> hasher -> metadata extractor ->
repository. It is incremental: unchanged files are skipped, modified files
trigger analysis invalidation, and missing files are marked unavailable.

After indexing, it enqueues analysis jobs for new/changed videos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from backend.config import Settings, get_settings
from backend.core import ProjectContext
from backend.indexing.hasher import compute_fingerprint, compute_hash
from backend.indexing.metadata import extract_metadata
from backend.indexing.scanner import scan_directory
from backend.indexing.thumbnails import generate_thumbnail
from backend.indexing.validator import validate_video_file
from backend.jobs import JobType
from backend.logging import get_logger

log = get_logger("indexer")

# Folder names that map to media categories.
CATEGORY_DIRS = {"raw": "raw", "broll": "broll", "b-roll": "broll",
                 "podcast": "podcast", "audio": "audio",
                 "archive": "archive", "interview": "interview"}


@dataclass
class IndexResult:
    discovered: int = 0
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    failed: list[str] = field(default_factory=list)


class VideoIndexer:
    def __init__(self, ctx: ProjectContext, settings: Settings | None = None) -> None:
        self.ctx = ctx
        self.settings = settings or get_settings()

    def index_project(self, *, generate_thumbnails: bool = True) -> IndexResult:
        folder = self.ctx.folder_path
        result = IndexResult()
        log.info("indexing started", extra={
            "project_id": self.ctx.project_id, "action": "index", "status": "start"})
        files = scan_directory(folder, self.settings)
        result.discovered = len(files)
        for path in files:
            try:
                self._index_one(path, result, generate_thumbnails=generate_thumbnails)
            except Exception as exc:  # noqa: BLE001
                result.failed.append(f"{path.name}: {exc}")
                log.warning("index file failed", extra={
                    "video_path": str(path), "error": str(exc)})
        # Mark DB records whose files disappeared as unavailable.
        self._mark_missing(files)
        log.info("indexing completed", extra={
            "project_id": self.ctx.project_id, "action": "index", "status": "done",
            "added": result.added, "updated": result.updated,
            "unchanged": result.unchanged, "failed": len(result.failed)})
        return result

    def _index_one(self, path: Path, result: IndexResult, *,
                   generate_thumbnails: bool) -> None:
        rel = path.relative_to(self.ctx.folder_path)
        category = "raw"
        if rel.parts:
            top = str(rel.parts[0]).lower()
            category = CATEGORY_DIRS.get(top, "raw")

        validation = validate_video_file(path, self.settings)
        if not validation["valid"]:
            result.skipped += 1
            if validation["error"]:
                result.failed.append(f"{path.name}: {validation['error']}")
            return

        existing = self.ctx.repo.get_video_by_path(self.ctx.project_id, str(path))
        fingerprint = compute_fingerprint(path)

        if existing:
            if existing.get("fingerprint") == fingerprint and existing.get("available"):
                result.unchanged += 1
                return
            # File changed (or was unavailable) — re-extract and invalidate.
            metadata = validation["metadata"]
            new_hash = compute_hash(path, self.settings)
            self.ctx.repo.update_video(
                existing["id"],
                hash=new_hash, fingerprint=fingerprint,
                duration=metadata["duration"], fps=metadata["fps"],
                width=metadata["width"], height=metadata["height"],
                bitrate=metadata["bitrate"], codec=metadata["codec"],
                audio_codec=metadata["audio_codec"],
                has_audio=metadata["has_audio"], file_size=metadata["file_size"],
                media_category=category, available=1, analyzed=0,
            )
            self._invalidate_analysis(existing["id"])
            self._enqueue_analysis(existing["id"])
            result.updated += 1
            return

        # New video.
        metadata = validation["metadata"]
        full_hash = compute_hash(path, self.settings)
        video = self.ctx.repo.upsert_video(
            project_id=self.ctx.project_id, path=str(path), filename=path.name,
            extension=path.suffix.lower(), hash=full_hash, fingerprint=fingerprint,
            media_category=category, **metadata,
        )
        if generate_thumbnails:
            thumb_dir = Path(self.ctx.cache_path) / "thumbnails"
            thumb_path = thumb_dir / f"{video['id']}.jpg"
            try:
                generate_thumbnail(path, thumb_path, settings=self.settings)
                self.ctx.repo.update_video(video["id"], thumbnail_path=str(thumb_path))
            except Exception as exc:  # noqa: BLE001
                log.warning("thumbnail failed", extra={
                    "video_id": video["id"], "error": str(exc)})
        self._enqueue_analysis(video["id"])
        result.added += 1

    def _invalidate_analysis(self, video_id: str) -> None:
        """Clear downstream analysis when a video changes."""
        self.ctx.repo.clear_transcript(video_id)
        self.ctx.repo.clear_scenes(video_id)
        self.ctx.repo.clear_frames(video_id)
        self.ctx.repo.clear_audio_analysis(video_id)

    def _enqueue_analysis(self, video_id: str) -> None:
        self.ctx.repo.create_job(
            project_id=self.ctx.project_id, job_type=JobType.ANALYZE_VIDEO.value,
            video_id=video_id)

    def _mark_missing(self, current_files: list[Path]) -> None:
        current = {str(p) for p in current_files}
        for video in self.ctx.repo.list_videos(self.ctx.project_id):
            if video["path"] not in current and video.get("available"):
                self.ctx.repo.set_video_unavailable(video["id"])
                log.info("video missing on disk", extra={
                    "video_id": video["id"], "action": "mark_missing"})
