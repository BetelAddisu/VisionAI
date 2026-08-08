# VisionAI — Repository Knowledge

## Overview
Local-first AI video post-production assistant for DaVinci Resolve. Python/FastAPI backend, SQLite database, vanilla JS frontend (no build step).

## Architecture
- `backend/config/` — Settings (pydantic-settings), YAML config loading
- `backend/core/` — ProjectContext, ProjectManager
- `backend/database/` — Connection, migrations, repository
- `backend/indexing/` — VideoIndexer (scanner, validator, hasher, metadata, thumbnails)
- `backend/pipeline/` — AnalysisPipeline orchestrator + stages (scenes, audio, transcription, frames, quality, embeddings)
- `backend/ai/` — Provider interfaces (SpeechProvider, VisionProvider, EmbeddingProvider, LLMProvider) + implementations
- `backend/search/` — SearchEngine (FTS5 keyword + semantic + metadata + ranking)
- `backend/planner/` — AIPlanner (grounded, rule-based + optional LLM refinement)
- `backend/timeline/` — TimelineBuilder, models, validator, subtitles
- `backend/export/` — DaVinci XML generator, SRT export, proxy workflow
- `backend/jobs/` — JobQueue, JobHandler, worker, recovery
- `backend/api/` — FastAPI app, routes, deps
- `frontend/static/` — SPA (index.html, css/app.css, js/api.js, js/app.js)

## Key Commands
- Run server: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 12000`
- Run tests: `python -m pytest tests/ -q`
- UI: served at `/` by the FastAPI app (static files, no separate frontend server)

## Config
- Default config: `config/default.yaml`
- Override via `VISIONAI_CONFIG` env var pointing to a YAML file
- AI providers default to local; `speech.provider: none` skips transcription cleanly

## Hardware Constraints
Target: Intel Core i3-7020U, 12GB RAM, Intel UHD 620, HDD. Default: 1 heavy AI job at a time, sequential pipeline stages, model unloading between stages, proxy media support.

## Testing
- 51 tests: unit (query_parser, ranking, embedding_provider, planner_rules, timeline), integration (indexing, analysis_pipeline, search, planner_timeline_export, jobs, frontend), e2e (api_workflow)
- Test videos generated via ffmpeg in conftest.py
- `tmp_settings` fixture isolates data to temp dir, sets speech provider to "none"

## API Surface
All routes under `/api`. Key endpoints:
- Projects: CRUD + index
- Videos: list/get/analyze + transcript/scenes
- Jobs: list/get/cancel/run
- Search: POST `/projects/{id}/search`
- Planner: POST `/projects/{id}/plan`, list/get plans
- Timeline: build/list/get + export XML + export SRT
- Settings: app + project
- Thumbnail: GET `/api/projects/{id}/videos/{vid}/thumbnail`
