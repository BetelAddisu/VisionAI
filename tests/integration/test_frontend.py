"""Tests for the frontend SPA serving and static assets."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import create_app
from backend.app_container import create_container


def _client() -> TestClient:
    return TestClient(create_app())


def test_index_html_served():
    client = _client()
    res = client.get("/")
    assert res.status_code == 200
    assert "<html" in res.text
    assert "VisionAI" in res.text


def test_static_assets_served():
    client = _client()
    for path in ["/static/css/app.css", "/static/js/api.js", "/static/js/app.js"]:
        res = client.get(path)
        assert res.status_code == 200, f"{path} not served"
        assert len(res.text) > 0


def test_spa_fallback():
    client = _client()
    # Unknown /app/ paths should fall back to index.html for client routing.
    res = client.get("/app/some/deep/route")
    assert res.status_code == 200
    assert "<html" in res.text


def test_health_endpoint():
    client = _client()
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["app"] == "VisionAI"


def test_thumbnail_route_returns_image(indexed_project):
    ctx = indexed_project
    videos = ctx.repo.list_videos(ctx.project_id)
    assert videos, "no videos indexed"
    video = videos[0]
    assert video["thumbnail_path"], "thumbnail not generated"
    assert Path(video["thumbnail_path"]).exists()

    # The container reads the same test config (env var set by tmp_settings),
    # so its project_manager can open the fixture's project.
    container = create_container()
    client = TestClient(create_app(container=container))
    res = client.get(f"/api/projects/{ctx.project_id}/videos/{video['id']}/thumbnail")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image")


def test_thumbnail_404_for_missing(indexed_project):
    ctx = indexed_project
    client = _client()
    res = client.get(f"/api/projects/{ctx.project_id}/videos/nonexistent-id/thumbnail")
    assert res.status_code == 404

