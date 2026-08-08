````md
# 02 - Project Structure

**Version:** 1.0.0

---

# Purpose

This document defines the complete directory structure for the AI Video Post-Production Assistant.

The directory layout is designed to satisfy the following goals:

- Easy navigation
- Strict separation of concerns
- Modular architecture
- AI-agent friendly organization
- Incremental development
- Easy testing
- Future scalability

This structure should remain stable throughout the lifetime of the project.

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- TailwindCSS
- Tauri

---

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- OpenCV
- FFmpeg
- Faster-Whisper
- FAISS
- SQLite

---

## AI

- Faster Whisper Small
- Qwen2.5-VL-3B
- Qwen3-4B (future planning)
- BGE Small Embeddings
- YOLO Nano

---

# Repository Structure

```text
ai-video-editor/

│
├── app/
│
├── backend/
│
├── models/
│
├── cache/
│
├── projects/
│
├── docs/
│
├── scripts/
│
├── tests/
│
├── assets/
│
├── config/
│
├── logs/
│
├── .github/
│
│
├── README.md
├── LICENSE
├── pyproject.toml
├── package.json
├── tauri.conf.json
└── .gitignore
```

---

# Root Folder Responsibilities

## app/

Contains the desktop application.

```text
app/

├── components/
├── pages/
├── layouts/
├── hooks/
├── services/
├── stores/
├── styles/
├── lib/
├── types/
└── utils/
```

Never place AI logic here.

Only UI.

---

# backend/

Contains every backend module.

```text
backend/

├── api/
├── core/
├── database/
├── pipeline/
├── ai/
├── export/
├── search/
├── indexing/
├── planner/
├── timeline/
├── jobs/
├── monitoring/
├── logging/
├── config/
└── utils/
```

This is the heart of the application.

---

# models/

Stores downloadable AI models.

Never commit model weights.

```text
models/

├── whisper/
├── qwen/
├── embeddings/
├── yolo/
└── vision/
```

The application downloads models automatically if missing.

---

# cache/

Global cache.

Contains temporary data.

```text
cache/

├── transcripts/
├── scenes/
├── thumbnails/
├── embeddings/
├── frames/
├── audio/
├── analysis/
└── temp/
```

This folder can safely be deleted.

The application rebuilds it automatically.

---

# projects/

Contains user projects.

```text
projects/

Project_A/

Project_B/

Project_C/
```

Each project is completely isolated.

---

# docs/

All documentation.

```text
docs/

00-overview.md

01-system-architecture.md

02-project-structure.md

...

13-roadmap.md

AGENT.md
```

---

# scripts/

Developer utilities.

```text
scripts/

download_models.py

benchmark.py

clean_cache.py

reset_database.py

generate_icons.py

dev_environment.py
```

These scripts are never imported by production code.

---

# tests/

```text
tests/

unit/

integration/

performance/

fixtures/

mock_data/
```

Every backend module must have tests.

---

# assets/

Application assets.

```text
assets/

icons/

logos/

fonts/

images/

animations/
```

---

# config/

Configuration files.

```text
config/

development.yaml

production.yaml

models.yaml

logging.yaml

pipeline.yaml
```

Never hardcode configuration values.

---

# logs/

Application logs.

```text
logs/

application.log

errors.log

pipeline.log

performance.log
```

Automatically rotated.

---

# Backend Structure

```text
backend/

│
├── api/
│
├── ai/
│
├── database/
│
├── pipeline/
│
├── planner/
│
├── indexing/
│
├── search/
│
├── timeline/
│
├── export/
│
├── monitoring/
│
├── jobs/
│
├── logging/
│
├── config/
│
└── utils/
```

---

# backend/api/

REST API exposed to the frontend.

```text
api/

projects.py

videos.py

search.py

planner.py

timeline.py

settings.py
```

Contains only HTTP endpoints.

No business logic.

---

# backend/ai/

Contains wrappers around AI models.

```text
ai/

speech/

vision/

planner/

embedding/

objects/

faces/

emotion/
```

Each model has its own folder.

Example

```text
speech/

transcriber.py

loader.py

config.py

types.py
```

No module knows about other AI modules.

---

# backend/database/

```text
database/

connection.py

repository.py

schema.py

migrations/

models/

queries/
```

Responsible only for persistence.

---

# backend/pipeline/

Coordinates processing.

```text
pipeline/

pipeline.py

scheduler.py

orchestrator.py

cache.py

progress.py
```

No AI model implementation belongs here.

Only orchestration.

---

# backend/indexing/

Responsible for media discovery.

```text
indexing/

scanner.py

metadata.py

hash.py

validator.py
```

---

# backend/planner/

Responsible for edit planning.

```text
planner/

planner.py

prompt_builder.py

story_analysis.py

editing_rules.py
```

---

# backend/search/

```text
search/

semantic.py

metadata.py

ranking.py

query_parser.py
```

---

# backend/timeline/

```text
timeline/

builder.py

clips.py

effects.py

transitions.py

generator.py
```

Produces internal timeline representation.

---

# backend/export/

```text
export/

otio.py

davinci.py

xml.py

edl.py
```

Exports timeline formats.

---

# backend/jobs/

```text
jobs/

queue.py

worker.py

state.py

retry.py
```

Only one heavy job executes at once on minimum hardware.

---

# backend/monitoring/

Tracks system performance.

```text
monitoring/

cpu.py

memory.py

disk.py

performance.py
```

---

# backend/logging/

```text
logging/

logger.py

formatter.py

rotation.py
```

---

# backend/config/

```text
config/

settings.py

models.py

constants.py
```

Centralized configuration access.

---

# backend/utils/

Shared helper functions.

```text
utils/

files.py

video.py

image.py

math.py

strings.py

time.py
```

Utilities must remain generic.

No business logic.

---

# Project Structure

Each user project has the following layout.

```text
projects/

MyProject/

│
├── project.json
├── database.sqlite
│
├── videos/
│
│   ├── raw/
│   ├── broll/
│   ├── podcast/
│   └── archive/
│
├── cache/
│
│   ├── transcripts/
│   ├── scenes/
│   ├── thumbnails/
│   ├── frames/
│   ├── embeddings/
│   ├── objects/
│   ├── faces/
│   ├── quality/
│   └── audio/
│
├── exports/
│
│   ├── otio/
│   ├── xml/
│   ├── edl/
│   └── reports/
│
└── backups/
```

---

# Naming Conventions

Python

snake_case

```python
video_indexer.py
```

Classes

PascalCase

```python
VideoIndexer
```

React Components

PascalCase

```text
SearchPanel.tsx
```

Hooks

```text
useProject.ts
```

Types

```text
VideoMetadata.ts
```

Constants

```python
MAX_QUEUE_SIZE
```

---

# Import Rules

Allowed

```text
UI

↓

API

↓

Pipeline

↓

AI

↓

Database
```

Forbidden

```text
UI

↓

Database
```

Forbidden

```text
AI

↓

UI
```

Forbidden

```text
Database

↓

Frontend
```

Dependencies must always flow downward.

---

# File Size Guidelines

Maximum recommended file sizes.

```text
Python

400 lines

TypeScript

400 lines

React Components

300 lines
```

Split larger files.

---

# Module Rules

Each folder should expose a single public entry point.

Example

```text
search/

__init__.py

semantic.py

ranking.py

query.py
```

External modules import only from `search`.

Internal files remain private.

---

# Dependency Rules

Allowed

Pipeline

↓

AI

Allowed

Planner

↓

Search

Allowed

Timeline

↓

Database

Not Allowed

Search

↓

Timeline

Not Allowed

Database

↓

Planner

Keep dependencies acyclic.

---

# Future Expansion

The structure reserves space for future modules.

Potential additions

```text
plugins/

sdk/

cloud/

analytics/

collaboration/

extensions/

marketplace/

training/

mobile/
```

Adding these modules must not require reorganizing the existing directory structure.

---

# Architectural Principle

Every file in the repository should answer one question:

> "What is this file responsible for?"

If the answer contains "and", the file likely has more than one responsibility and should be split.
````
