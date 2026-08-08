````md
# 03 - Database Design

**Version:** 1.0.0

---

# Purpose

This document defines the complete database architecture for the AI Video Post-Production Assistant.

The database is the central source of truth for the application.

Every AI model, processing pipeline, search engine, and timeline generator must retrieve information from the database rather than reading raw files repeatedly.

The database should never store video files.

Only metadata.

---

# Design Principles

## Single Source of Truth

Every piece of generated information must exist only once.

Example

❌ Wrong

```
Transcript saved in JSON

Transcript saved in SQLite

Transcript saved in Memory
```

Three different copies eventually become inconsistent.

Correct

```
Transcript

↓

SQLite

↓

Everything else reads from SQLite
```

---

## Read Often

Write Once

Analysis is expensive.

Reading is cheap.

The application should analyze media once and read the results thousands of times.

---

## Metadata Only

The database never stores

- Videos
- Images
- Audio
- Thumbnails

Instead it stores references.

Example

```
thumbnail_path

cache/thumbnails/frame_120.jpg
```

---

## Normalize First

Avoid duplicated information.

Incorrect

```
Video

↓

Stores 1,000 transcript rows
```

Correct

```
Video

↓

Transcript Table
```

---

# Database Technology

Database

SQLite

Reason

- Fast
- Embedded
- Zero configuration
- ACID compliant
- Easy backup
- Cross-platform

---

# Vector Database

Technology

FAISS

Purpose

Semantic search.

SQLite stores metadata.

FAISS stores vectors.

They work together.

---

# Database Overview

```
Projects

│

├── Videos

│      │

│      ├── Scenes

│      ├── Frames

│      ├── Transcript

│      ├── Objects

│      ├── Faces

│      ├── Audio

│      ├── Quality

│      └── Embeddings

│

├── Search History

├── Timeline

├── Planner

├── Jobs

└── Logs
```

---

# Entity Relationship Diagram

```
Project
    │
    ├──────── Videos
    │             │
    │             ├──────── Scenes
    │             ├──────── TranscriptSegments
    │             ├──────── Frames
    │             ├──────── Objects
    │             ├──────── Faces
    │             ├──────── AudioAnalysis
    │             ├──────── QualityMetrics
    │             └──────── Embeddings

Timeline
    │
    └──────── TimelineClips

Planner
    │
    └──────── PlannerSuggestions

Jobs

Settings

Logs
```

---

# Table List

The application contains the following primary tables.

```
projects

videos

scenes

transcript_segments

frames

objects

faces

quality_metrics

audio_analysis

embeddings

timeline

timeline_clips

planner_sessions

planner_recommendations

jobs

logs

settings
```

---

# projects

Stores project metadata.

Fields

| Field | Type |
|--------|------|
| id | UUID |
| name | TEXT |
| description | TEXT |
| created_at | DATETIME |
| updated_at | DATETIME |
| version | TEXT |

---

# videos

Stores imported videos.

Fields

| Field | Type |
|--------|------|
| id | UUID |
| project_id | UUID |
| path | TEXT |
| filename | TEXT |
| extension | TEXT |
| hash | TEXT |
| duration | REAL |
| fps | REAL |
| width | INTEGER |
| height | INTEGER |
| bitrate | INTEGER |
| codec | TEXT |
| file_size | INTEGER |
| analyzed | BOOLEAN |
| created_at | DATETIME |

---

# scenes

Each detected scene.

| Field | Type |
|--------|------|
| id | UUID |
| video_id | UUID |
| scene_number | INTEGER |
| start_time | REAL |
| end_time | REAL |
| duration | REAL |
| thumbnail_path | TEXT |

---

# transcript_segments

Stores Whisper output.

| Field | Type |
|--------|------|
| id | UUID |
| video_id | UUID |
| start_time | REAL |
| end_time | REAL |
| speaker | TEXT |
| confidence | REAL |
| text | TEXT |

---

# frames

Representative frames.

| Field | Type |
|--------|------|
| id | UUID |
| video_id | UUID |
| timestamp | REAL |
| image_path | TEXT |

---

# objects

Detected objects.

| Field | Type |
|--------|------|
| id | UUID |
| frame_id | UUID |
| label | TEXT |
| confidence | REAL |
| x | REAL |
| y | REAL |
| width | REAL |
| height | REAL |

Coordinates are normalized.

0.0–1.0

---

# faces

Detected faces.

| Field | Type |
|--------|------|
| id | UUID |
| frame_id | UUID |
| confidence | REAL |
| smiling | BOOLEAN |
| eyes_open | BOOLEAN |
| looking_camera | BOOLEAN |

Future versions

```
person_id

emotion

age_estimate
```

---

# quality_metrics

Computer vision metrics.

| Field | Type |
|--------|------|
| id | UUID |
| frame_id | UUID |
| brightness | REAL |
| contrast | REAL |
| blur_score | REAL |
| noise_score | REAL |
| exposure_score | REAL |
| sharpness | REAL |

---

# audio_analysis

Stores non-transcript audio features.

| Field | Type |
|--------|------|
| id | UUID |
| video_id | UUID |
| timestamp | REAL |
| silence | BOOLEAN |
| loudness | REAL |
| peak | REAL |
| background_noise | REAL |

---

# embeddings

Links metadata to FAISS.

| Field | Type |
|--------|------|
| id | UUID |
| source_type | TEXT |
| source_id | UUID |
| faiss_index | INTEGER |

Embedding vectors themselves are stored inside FAISS.

SQLite stores only references.

---

# planner_sessions

Each AI planning request.

| Field | Type |
|--------|------|
| id | UUID |
| project_id | UUID |
| prompt | TEXT |
| audience | TEXT |
| platform | TEXT |
| created_at | DATETIME |

---

# planner_recommendations

Stores planner output.

| Field | Type |
|--------|------|
| id | UUID |
| session_id | UUID |
| recommendation | TEXT |
| priority | INTEGER |
| accepted | BOOLEAN |

---

# timeline

Generated timelines.

| Field | Type |
|--------|------|
| id | UUID |
| project_id | UUID |
| created_at | DATETIME |
| exported | BOOLEAN |

---

# timeline_clips

Timeline contents.

| Field | Type |
|--------|------|
| id | UUID |
| timeline_id | UUID |
| video_id | UUID |
| start_time | REAL |
| end_time | REAL |
| track | INTEGER |
| order_index | INTEGER |

---

# jobs

Pipeline jobs.

| Field | Type |
|--------|------|
| id | UUID |
| job_type | TEXT |
| status | TEXT |
| progress | REAL |
| started_at | DATETIME |
| completed_at | DATETIME |

Status values

```
Queued

Running

Paused

Failed

Completed
```

---

# logs

Application log index.

| Field | Type |
|--------|------|
| id | UUID |
| level | TEXT |
| module | TEXT |
| message | TEXT |
| timestamp | DATETIME |

---

# settings

Project settings.

| Field | Type |
|--------|------|
| key | TEXT |
| value | TEXT |

---

# Relationships

```
Project

↓

Videos

↓

Scenes

↓

Frames

↓

Objects

↓

Embeddings
```

Transcript

```
Video

↓

Transcript Segments
```

Timeline

```
Timeline

↓

Timeline Clips

↓

Video
```

---

# Index Strategy

Indexes should exist on

```
video hash

video path

scene start

scene end

transcript text

transcript timestamp

object label

planner session

job status

timeline id
```

These fields are queried frequently.

---

# Full Text Search

SQLite FTS5 should index

- Transcript text
- Planner recommendations
- Object labels
- Search history

This enables fast keyword search.

Semantic search remains in FAISS.

---

# Data Access Rules

Modules never execute SQL directly.

Instead

```
Pipeline

↓

Repository

↓

SQLite
```

Every table has a dedicated repository.

Example

```
VideoRepository

TranscriptRepository

SceneRepository

TimelineRepository
```

---

# Cache Rules

SQLite stores metadata.

Large artifacts remain on disk.

Examples

```
Transcript

SQLite

Embedding

FAISS

Thumbnail

JPEG

Audio

WAV

Frame

JPEG
```

Never store binary blobs inside SQLite.

---

# Backup Strategy

Each project is self-contained.

```
Project/

database.sqlite

videos/

cache/

exports/
```

Backing up the project folder backs up everything.

---

# Migration Strategy

Use Alembic for schema migrations.

Rules

- Never modify existing tables manually.
- Every schema change requires a migration.
- Migrations must be reversible.
- Preserve user data.

---

# Performance Targets

Typical expectations

- Open project: <1 second
- Insert metadata: <20 ms
- Transcript search: <100 ms
- Video lookup: <20 ms
- Timeline save: <100 ms

These targets should be met on the minimum supported hardware.

---

# Future Tables

Reserved for future versions

```
people

music

captions

voiceprints

luts

plugins

analytics

cloud_sync

collaboration

render_history

shorts

chapters

multi_camera

user_feedback
```

---

# Guiding Principle

The database should answer every question about a project without reopening the original video files.

Raw videos should only be accessed when frames, audio, or exports are actually required.
````
