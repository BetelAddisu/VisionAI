"""Validator: checks file existence, readability, format and metadata."""
from __future__ import annotations

from pathlib import Path

from backend.config import Settings, get_settings
from backend.indexing.metadata import extract_metadata


def is_supported_format(path: str | Path, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return Path(path).suffix.lower() in {e.lower() for e in settings.indexing.supported_extensions}


def validate_video_file(path: str | Path, settings: Settings | None = None) -> dict:
    """Return a validation result dict.

    {
      "valid": bool,
      "exists": bool,
      "readable": bool,
      "supported": bool,
      "metadata": dict | None,
      "error": str | None,
    }
    """
    settings = settings or get_settings()
    p = Path(path)
    result = {
        "valid": False, "exists": p.exists(), "readable": False,
        "supported": is_supported_format(p, settings), "metadata": None, "error": None,
    }
    if not p.exists():
        result["error"] = "File does not exist"
        return result
    try:
        with p.open("rb"):
            result["readable"] = True
    except PermissionError:
        result["error"] = "Permission denied"
        return result
    if not result["supported"]:
        result["error"] = f"Unsupported format: {p.suffix}"
        return result
    try:
        metadata = extract_metadata(p)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"Metadata extraction failed: {exc}"
        return result
    if metadata["duration"] <= 0 and metadata["width"] == 0:
        result["error"] = "No playable video stream detected (possibly corrupted)"
        return result
    result["metadata"] = metadata
    result["valid"] = True
    return result
