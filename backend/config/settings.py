"""Centralized application configuration.

Configuration is loaded once from YAML files and exposed through a typed
``Settings`` object. No other module should hardcode configuration values.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

# Repository root (backend/config/settings.py -> repo root is 3 levels up).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "default.yaml"


class AppCfg(BaseModel):
    name: str = "VisionAI"
    version: str = "0.1.0"
    data_dir: str = "./data"
    max_parallel_heavy_jobs: int = 1
    performance_mode: str = "balanced"


class StorageCfg(BaseModel):
    projects_dir: str = "./data/projects"
    cache_dir: str = "./data/cache"
    models_dir: str = "./data/models"
    logs_dir: str = "./data/logs"


class DatabaseCfg(BaseModel):
    filename: str = "database.sqlite"
    wal_mode: bool = True


class IndexingCfg(BaseModel):
    supported_extensions: list[str] = Field(default_factory=lambda: [
        ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".flv"
    ])
    ignore_dirs: list[str] = Field(default_factory=lambda: [
        ".cache", ".tmp", "exports", ".git", "__pycache__", "node_modules"
    ])
    hash_chunk_size_mb: int = 8


class PipelineCfg(BaseModel):
    frame_sample_interval: float = 2.0
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    scene_threshold: float = 0.4
    max_retries: int = 3
    thumbnail_width: int = 320


class ProxyCfg(BaseModel):
    enabled: bool = False
    width: int = 1280
    height: int = 720
    codec: str = "h264"
    bitrate: str = "1.5M"


class ModelCfg(BaseModel):
    provider: str = "none"
    model: str = ""
    device: str = "cpu"
    compute_type: str = "int8"
    dimension: int | None = None
    # Optional fields for OpenAI-compatible local LLM servers.
    base_url: str = ""
    api_key: str = ""


class ModelsCfg(BaseModel):
    speech: ModelCfg = Field(default_factory=ModelCfg)
    vision: ModelCfg = Field(default_factory=ModelCfg)
    embeddings: ModelCfg = Field(default_factory=ModelCfg)
    llm: ModelCfg = Field(default_factory=ModelCfg)


class SearchCfg(BaseModel):
    ranking_weights: dict[str, float] = Field(default_factory=lambda: {
        "semantic": 0.45, "keyword": 0.25, "visual": 0.15,
        "quality": 0.10, "recency": 0.05,
    })
    result_context_padding: float = 3.0


class LoggingCfg(BaseModel):
    level: str = "INFO"
    format: str = "json"


class ServerCfg(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


class Settings(BaseModel):
    app: AppCfg = Field(default_factory=AppCfg)
    storage: StorageCfg = Field(default_factory=StorageCfg)
    database: DatabaseCfg = Field(default_factory=DatabaseCfg)
    indexing: IndexingCfg = Field(default_factory=IndexingCfg)
    pipeline: PipelineCfg = Field(default_factory=PipelineCfg)
    proxy: ProxyCfg = Field(default_factory=ProxyCfg)
    models: ModelsCfg = Field(default_factory=ModelsCfg)
    search: SearchCfg = Field(default_factory=SearchCfg)
    logging: LoggingCfg = Field(default_factory=LoggingCfg)
    server: ServerCfg = Field(default_factory=ServerCfg)

    # Derived paths, resolved against the repo root.
    @property
    def repo_root(self) -> Path:
        return REPO_ROOT

    def resolve(self, path: str) -> Path:
        p = Path(path)
        return p if p.is_absolute() else (REPO_ROOT / p).resolve()

    @property
    def projects_path(self) -> Path:
        return self.resolve(self.storage.projects_dir)

    @property
    def cache_path(self) -> Path:
        return self.resolve(self.storage.cache_dir)

    @property
    def models_path(self) -> Path:
        return self.resolve(self.storage.models_dir)

    @property
    def logs_path(self) -> Path:
        return self.resolve(self.storage.logs_dir)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_settings(config_path: str | os.PathLike[str] | None = None) -> Settings:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    # Allow an environment variable to point at an override config.
    env_override = os.environ.get("VISIONAI_CONFIG")
    if env_override and Path(env_override).exists():
        with Path(env_override).open("r", encoding="utf-8") as f:
            data = _deep_merge(data, yaml.safe_load(f) or {})
    return Settings.model_validate(data)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
