"""Scanner: find supported video files in a directory tree.

Rules (04-video-indexer.md):
- Include supported formats only.
- Ignore hidden files, temp/cache/exports/system folders.
- Never read file contents; only enumerate paths.
"""
from __future__ import annotations

from pathlib import Path

from backend.config import Settings, get_settings


def scan_directory(folder: str | Path, settings: Settings | None = None) -> list[Path]:
    """Return supported video file paths under ``folder``, sorted.

    Recursively walks the tree, skipping ignored directory names. Hidden
    files and files in ignored directories are excluded.
    """
    settings = settings or get_settings()
    supported = {ext.lower() for ext in settings.indexing.supported_extensions}
    ignore = {name.lower() for name in settings.indexing.ignore_dirs}
    root = Path(folder)
    if not root.exists() or not root.is_dir():
        return []

    results: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip if any parent directory component is in the ignore set.
        if any(part.lower() in ignore for part in path.relative_to(root).parts[:-1]):
            continue
        # Skip hidden files.
        if path.name.startswith(".") or path.name.startswith("~"):
            continue
        # Skip temp files.
        if path.suffix.lower() in (".tmp", ".temp", ".bak"):
            continue
        if path.suffix.lower() in supported:
            results.append(path)
    return sorted(results)
