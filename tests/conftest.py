"""Shared pytest fixtures.

Generates tiny synthetic test videos with ffmpeg so tests run offline and
deterministically without needing real footage.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from backend.config import load_settings
from backend.core import ProjectManager


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _make_video(path: Path, *, duration: int = 3, text: str = "test") -> None:
    """Create a tiny test video with a sine-wave audio track."""
    ffmpeg = shutil.which("ffmpeg")
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s=320x240:d={duration}:r=15",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-shortest",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, check=True, timeout=60)


@pytest.fixture
def tmp_settings(tmp_path: Path):
    """Settings isolated to a temp directory."""
    data_dir = tmp_path / "data"
    (data_dir / "projects").mkdir(parents=True)
    (data_dir / "cache").mkdir(parents=True)
    (data_dir / "models").mkdir(parents=True)
    (data_dir / "logs").mkdir(parents=True)
    overrides = {
        "storage": {
            "projects_dir": str(data_dir / "projects"),
            "cache_dir": str(data_dir / "cache"),
            "models_dir": str(data_dir / "models"),
            "logs_dir": str(data_dir / "logs"),
        },
        "models": {
            "speech": {"provider": "none"},
            "embeddings": {"provider": "local", "dimension": 64},
        },
        "logging": {"level": "WARNING", "format": "text"},
    }
    import yaml
    cfg_path = tmp_path / "test_config.yaml"
    cfg_path.write_text(yaml.safe_dump(overrides))
    # Reset the lru_cache so the new settings take effect.
    from backend.config import settings as settings_module
    import os
    os.environ["VISIONAI_CONFIG"] = str(cfg_path)
    settings_module.get_settings.cache_clear()
    settings = load_settings(str(cfg_path))
    yield settings
    del os.environ["VISIONAI_CONFIG"]
    settings_module.get_settings.cache_clear()


@pytest.fixture
def project_manager(tmp_settings):
    return ProjectManager(settings=tmp_settings)


@pytest.fixture
def video_file(tmp_path: Path):
    """A single tiny test video."""
    if not _has_ffmpeg():
        pytest.skip("ffmpeg not available")
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    path = media_dir / "clip1.mp4"
    _make_video(path, duration=3)
    return path


@pytest.fixture
def video_folder(tmp_path: Path):
    """A folder with two test videos."""
    if not _has_ffmpeg():
        pytest.skip("ffmpeg not available")
    media_dir = tmp_path / "library"
    media_dir.mkdir()
    _make_video(media_dir / "clip1.mp4", duration=3)
    _make_video(media_dir / "clip2.mp4", duration=2)
    return media_dir


@pytest.fixture
def indexed_project(project_manager, video_folder):
    """A project with videos already indexed."""
    ctx = project_manager.create_project(
        name="Test Project", folder_path=str(video_folder))
    from backend.indexing import VideoIndexer
    VideoIndexer(ctx).index_project(generate_thumbnails=True)
    yield ctx
