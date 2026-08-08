````md
# 01 - System Architecture

**Version:** 1.0.0

---

# Purpose

This document defines the complete system architecture for the AI Video Post-Production Assistant.

It serves as the source of truth for every subsystem in the application.

No implementation should contradict this document.

Every module should be independently replaceable without affecting the rest of the application.

---

# Architecture Philosophy

The application follows a modular pipeline architecture.

Every component has exactly one responsibility.

Modules communicate through well-defined interfaces.

No module should directly depend on the internal implementation of another module.

The architecture is intentionally designed to support replacing AI models without rewriting business logic.

---

# High-Level Architecture

```text
                         Desktop Application
                    (Tauri + Next.js + React)

                               │

                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼

              Project Manager        Settings Manager
                    │
                    ▼
              Video Indexer
                    │
                    ▼
             Analysis Pipeline
                    │
                    ▼
            Metadata Repository
                    │
        ┌───────────┼────────────┐
        │           │            │
        ▼           ▼            ▼

 Search Engine  AI Planner  Timeline Builder
        │           │            │
        └───────────┼────────────┘
                    ▼
             Export Engine
                    │
                    ▼
             DaVinci Resolve
```

---

# Architectural Layers

The system is divided into six layers.

## Layer 1

User Interface

Responsibilities

- Project creation
- Import videos
- Search
- Timeline preview
- Settings
- Progress display

Technology

- React
- Next.js
- Tailwind

The UI never performs AI processing.

---

## Layer 2

Application Layer

Responsibilities

- Project management
- Job scheduling
- Pipeline orchestration
- Error recovery

This layer controls every workflow.

Example

```text
Import Folder

↓

Index Videos

↓

Analyze Videos

↓

Update Database

↓

Notify UI
```

---

## Layer 3

Processing Layer

Contains every processing engine.

Modules

Video Scanner

Scene Detector

Audio Extractor

Speech Recognition

Vision Analysis

Face Detection

Object Detection

Embedding Generator

Quality Analyzer

This layer performs all heavy computation.

---

## Layer 4

AI Layer

Contains every AI model.

Examples

Speech Model

Vision Model

Planner LLM

Embedding Model

Each model performs only one task.

No model communicates directly with another model.

Only the Processing Layer coordinates them.

---

## Layer 5

Data Layer

Responsible for storing:

Projects

Videos

Scenes

Frames

Embeddings

Transcripts

People

Objects

Logs

Preferences

Technology

SQLite

FAISS

JSON cache

---

## Layer 6

Export Layer

Responsible for

Timeline Generation

OTIO

DaVinci Resolve

Future

Premiere

Final Cut

EDL

---

# Module Overview

## Project Manager

Responsibilities

Create project

Open project

Save project

Close project

Delete project

Manage paths

Track project state

Never performs AI processing.

---

## Video Indexer

Responsibilities

Scan folders

Detect videos

Compute file hash

Read metadata

Determine if analysis already exists

Schedule new jobs

Outputs

Video records

Analysis queue

---

## Analysis Pipeline

Responsibilities

Scene detection

Audio extraction

Transcription

Vision analysis

Embeddings

Object detection

Face detection

Quality metrics

Stores every result.

Never edits videos.

---

## Metadata Repository

Acts as the central source of truth.

Stores

Video metadata

Transcripts

Scenes

Objects

People

Embeddings

Statistics

Logs

No module stores metadata independently.

---

## Search Engine

Responsibilities

Natural language search

Semantic search

Metadata search

Combined search

Returns ranked results.

---

## AI Planner

Responsibilities

Interpret script

Interpret audience

Interpret platform

Interpret editing style

Generate edit plan

Never edits media directly.

---

## Timeline Builder

Consumes

Edit Plan

Clip References

Transitions

Effects

Outputs

OpenTimelineIO

DaVinci Timeline

---

## Export Engine

Creates

OTIO

XML

EDL

Future

Rendered MP4

Archive

---

# Processing Pipeline

```text
Import Folder

↓

Video Discovery

↓

Metadata Extraction

↓

Scene Detection

↓

Audio Extraction

↓

Speech Recognition

↓

Frame Sampling

↓

Vision Analysis

↓

Object Detection

↓

Embedding Generation

↓

Database Update

↓

Search Ready
```

---

# AI Processing Pipeline

```text
Video

↓

Frames

↓

Vision Model

↓

Objects

People

Composition

Lighting

↓

Metadata

↓

Embedding Model

↓

Vector Database
```

---

# Editing Pipeline

```text
User Script

↓

Planner

↓

Editing Plan

↓

Search Engine

↓

Matching Clips

↓

Timeline Builder

↓

OTIO

↓

DaVinci Resolve
```

---

# Search Pipeline

```text
User Query

↓

Embedding

↓

Vector Search

↓

Candidate Clips

↓

Metadata Ranking

↓

Final Results
```

---

# Component Communication

Allowed communication

```text
UI

↓

Application Layer

↓

Processing Layer

↓

Database
```

Not allowed

```text
UI

↓

AI Model
```

Never bypass the application layer.

---

# Event Flow

Example

Import Folder

```text
UI

↓

Project Manager

↓

Video Indexer

↓

Queue Job

↓

Analysis Pipeline

↓

Database

↓

UI Refresh
```

---

# Job Queue

The application processes jobs sequentially.

Example

```text
Job 1

Analyze Video A

↓

Completed

↓

Job 2

Analyze Video B

↓

Completed

↓

Job 3

Generate Embeddings

↓

Completed
```

Only one heavy AI job should execute at a time on low-end hardware.

---

# Cache Strategy

Every expensive operation is cached.

Examples

```text
Transcript

↓

Exists?

YES

↓

Reuse

NO

↓

Generate
```

Same logic applies to

Scenes

Embeddings

Objects

Faces

Frame analysis

Never recompute unless source hash changes.

---

# Memory Strategy

Never load an entire video.

Correct

```text
Open Video

↓

Seek

↓

Decode Frame

↓

Process

↓

Release Memory

↓

Next Frame
```

Incorrect

```text
Load Entire Video

↓

Run AI
```

This must never occur.

---

# Database Ownership

Only the Repository Layer may write to SQLite.

Other modules must use repository APIs.

Never execute raw SQL outside the repository.

---

# Error Recovery

Every stage is restartable.

Example

```text
Completed

✓ Metadata

✓ Scenes

✓ Transcript

×

Embeddings
```

Restart

↓

Begin from Embeddings

Never restart the previous stages.

---

# Logging

Every module logs:

Start

Progress

Completion

Failure

Duration

Memory usage

Example

```text
[SceneDetector]

Started

video_021.mp4

Time

14:22:31

Finished

14:22:39

Duration

8.1 sec
```

---

# Configuration

Every configurable value belongs in configuration files.

Examples

Frame sampling interval

Whisper model

Embedding model

Maximum workers

Database path

Cache path

Never hardcode configuration values.

---

# Scalability Goals

The architecture must support

- multiple projects
- multiple drives
- external SSDs
- network storage (future)
- plugin modules
- AI model replacement
- cloud synchronization (future)

without architectural redesign.

---

# Design Constraints

The architecture must operate on the minimum supported hardware.

Target hardware

CPU

Intel Core i3-7020U

RAM

12 GB

Storage

HDD

GPU

Intel UHD Graphics 620

Requirements

- Single AI job at a time.
- Sequential processing.
- Resume after interruption.
- Disk-based caching.
- Low memory footprint.
- No duplicate processing.
- No requirement for dedicated GPU.

---

# Architectural Principles

Every implementation must satisfy these rules.

1. Original videos are immutable.

2. Every expensive computation is cached.

3. Every module has one responsibility.

4. Every module exposes a public interface.

5. Modules communicate only through defined interfaces.

6. AI models are interchangeable.

7. Processing is resumable.

8. Metadata is the single source of truth.

9. Timeline generation is deterministic.

10. DaVinci Resolve remains the final editing environment.

---

# Future Extension Points

The architecture intentionally leaves extension points for future modules.

Potential additions

- Automatic Shorts Generator
- Multi-camera Synchronization
- AI Voice Cleanup
- Music Beat Detection
- LUT Recommendation Engine
- Sponsor Detection
- Caption Styling Engine
- AI Thumbnail Composer
- Plugin SDK
- Cloud Rendering
- Team Collaboration
- Mobile Companion Application

These features should be addable without changing the existing architecture.
````
