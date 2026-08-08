"""Video Indexer: discovers, validates and registers video assets.

Per 04-video-indexer.md this module only creates a reliable inventory — it
does not analyze content or run AI models. It delegates to the repository
for all database writes.
"""
from backend.indexing.hasher import compute_fingerprint, compute_hash
from backend.indexing.indexer import IndexResult, VideoIndexer
from backend.indexing.metadata import extract_metadata
from backend.indexing.scanner import scan_directory
from backend.indexing.thumbnails import generate_thumbnail
from backend.indexing.validator import validate_video_file

__all__ = [
    "VideoIndexer",
    "IndexResult",
    "scan_directory",
    "extract_metadata",
    "compute_fingerprint",
    "compute_hash",
    "validate_video_file",
    "generate_thumbnail",
]
