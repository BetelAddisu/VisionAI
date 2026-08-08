"""End-to-end API test: full workflow via FastAPI TestClient."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.app_container import AppContainer


def test_full_workflow_via_api(tmp_settings, video_folder):
    container = AppContainer()
    # Patch the project manager to use tmp settings.
    from backend.core import ProjectManager
    container.project_manager = ProjectManager(settings=tmp_settings)
    app = create_app(container)
    client = TestClient(app)

    # Health.
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Create project.
    r = client.post("/api/projects", json={
        "name": "E2E Project", "folder_path": str(video_folder)})
    assert r.status_code == 200, r.text
    project_id = r.json()["id"]

    # Index synchronously.
    r = client.post(f"/api/projects/{project_id}/index?run_async=false")
    assert r.status_code == 200
    assert r.json()["added"] == 2

    # List videos.
    r = client.get(f"/api/projects/{project_id}/videos")
    assert r.status_code == 200
    assert len(r.json()) == 2

    # Search (no transcript yet, so empty results are acceptable).
    r = client.post(f"/api/projects/{project_id}/search", json={
        "query": "AWS deployment", "limit": 10})
    assert r.status_code == 200
    assert r.json()["count"] >= 0

    # App settings endpoint.
    r = client.get("/api/settings/app")
    assert r.status_code == 200
    assert r.json()["app"]["name"] == "VisionAI"

    # List projects.
    r = client.get("/api/projects")
    assert r.status_code == 200
    assert any(p["id"] == project_id for p in r.json())
