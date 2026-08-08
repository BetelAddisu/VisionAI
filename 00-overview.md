I'll structure this like a real software design document rather than a README. The purpose of `00-overview.md` is to give both humans and AI coding agents a complete understanding of the project before implementation.

```md
# AI Video Post-Production Assistant

**Version:** 1.0.0

**Status:** Design Phase

---

# Project Vision

AI Video Post-Production Assistant is a desktop-first application that assists content creators throughout the post-production workflow.

Unlike AI video generators, this application does **not** create new videos.

Instead, it analyzes existing footage, understands the creator's intent, searches through video libraries, builds editing plans, and generates editable DaVinci Resolve timelines.

The system acts as an intelligent assistant rather than replacing the editor.

The creator remains in full control of every creative decision.

---

# Primary Goals

The application should be capable of:

- Indexing large local video libraries.
- Understanding spoken dialogue.
- Understanding visual content.
- Understanding story structure.
- Finding relevant clips.
- Suggesting edits.
- Removing mistakes.
- Improving pacing.
- Suggesting B-roll.
- Suggesting transitions.
- Suggesting music placement.
- Suggesting subtitles.
- Suggesting thumbnail frames.
- Suggesting color grading.
- Exporting complete DaVinci Resolve timelines.

---

# Non Goals

The application will NOT:

- Generate AI videos.
- Replace DaVinci Resolve.
- Replace professional editors.
- Upload videos to cloud services by default.
- Modify original media files.
- Require subscriptions.
- Depend on paid APIs.

---

# Design Philosophy

The software follows six core principles.

## 1. Local First

All user videos remain on the user's computer.

No footage should be uploaded unless the user explicitly enables a cloud feature.

Large media libraries make cloud processing expensive and slow.

Every core feature must work completely offline.

---

## 2. Cache Everything

Video analysis is expensive.

Every expensive operation must be cached.

Examples:

- transcripts
- scene detection
- object detection
- embeddings
- thumbnails
- face recognition

If analysis already exists, it should never be recomputed unless the source file changes.

---

## 3. Non Destructive Editing

Original media is sacred.

The application never edits original files.

Instead it produces:

- metadata
- caches
- timelines
- suggestions

The user can always return to the untouched footage.

---

## 4. Modular AI

No single AI model performs every task.

Each AI model has one responsibility.

Examples:

Speech Model

↓

Transcript

Vision Model

↓

Visual Understanding

Embedding Model

↓

Semantic Search

Planner Model

↓

Editing Decisions

Timeline Builder

↓

DaVinci Timeline

This architecture allows future model upgrades without rewriting the application.

---

## 5. Human In Control

The AI never performs irreversible edits.

Instead it provides:

Suggestions

Recommendations

Plans

Timeline Drafts

The editor always makes the final decision.

---

## 6. Hardware Aware

The application must operate on modest hardware.

Target specification:

CPU

Intel i3 Dual Core

RAM

12 GB

Storage

HDD

GPU

Integrated Intel Graphics

The software must degrade gracefully on slower hardware.

---

# Intended Users

Primary audience:

- YouTubers
- Developers creating tutorials
- Streamers
- Educational creators
- Technical educators
- Solo creators
- Small production teams

---

# Supported Content

The system should understand:

Talking Head Videos

Podcasts

Coding Tutorials

Travel Videos

Lifestyle Vlogs

Screen Recordings

Gaming

Educational Videos

B-roll

Interviews

---

# Supported Platforms

Desktop only.

Windows

Primary target.

Linux

Secondary target.

macOS

Future support.

---

# Primary Workflow

User imports folder.

↓

System scans videos.

↓

Metadata generated.

↓

Transcripts generated.

↓

Scenes detected.

↓

Objects detected.

↓

Embeddings generated.

↓

Database updated.

↓

User writes script.

↓

Planner creates edit.

↓

Timeline generated.

↓

Timeline imported into DaVinci Resolve.

↓

User reviews.

↓

User renders.

---

# High Level Architecture

                 Desktop Application

                         │

                Project Manager

                         │

      ┌─────────────────────────────────┐

      │                                 │

Video Processing                  AI Planning

      │                                 │

      ▼                                 ▼

Metadata Database              Editing Planner

      │                                 │

      └──────────────┬──────────────────┘

                     ▼

              Timeline Generator

                     ▼

             DaVinci Resolve

---

# Core Components

The application consists of the following modules.

Project Manager

Responsible for project creation and lifecycle.

Video Indexer

Scans media libraries.

Analysis Pipeline

Extracts metadata.

Metadata Database

Stores all information.

Embedding Engine

Enables semantic search.

Search Engine

Retrieves relevant clips.

Planner

Creates editing plans.

Timeline Builder

Creates DaVinci timelines.

Export Engine

Exports timelines and assets.

Settings Manager

Stores user preferences.

Logging System

Tracks every operation.

---

# AI Responsibilities

The AI should understand:

Speech

Scenes

People

Objects

Camera Movement

Lighting

Composition

Emotion

Story Progression

Dialogue

Pacing

Audience

Platform

Creator Intent

---

# Performance Goals

The application prioritizes responsiveness over maximum throughput.

Goals:

Startup under 5 seconds.

Incremental indexing.

Resume interrupted jobs.

Memory efficient processing.

Streaming video decoding.

No duplicate analysis.

---

# Storage Strategy

Original videos remain untouched.

Generated assets stored separately.

Project/

    videos/

    cache/

        transcripts/

        scenes/

        thumbnails/

        embeddings/

        analysis/

    exports/

    database.sqlite

---

# Error Recovery

Every pipeline stage must be restartable.

If processing stops after transcript generation:

Restart

↓

Continue from scene detection.

Never restart completed work.

---

# Scalability

The architecture must support:

100 videos

1,000 videos

10,000 videos

without requiring architectural changes.

---

# Security

No user footage leaves the device.

No telemetry by default.

No hidden uploads.

No cloud dependency.

User owns all generated metadata.

---

# Future Features

Future versions may include:

Automatic highlight reels

Multi-camera synchronization

Speaker identification

Voice cloning

Music synchronization

Sponsor detection

Automatic chapter generation

Automatic short-form content generation

Batch editing

Cloud synchronization

Collaborative editing

---

# Success Criteria

The project is considered successful when a user can:

Import a folder containing hundreds of videos.

Search using natural language.

Receive relevant clip recommendations.

Generate an edit plan from a script.

Export an editable DaVinci Resolve timeline.

Complete an edit significantly faster than a manual workflow.

---

# Guiding Principle

The application is not designed to replace creativity.

It is designed to eliminate repetitive, mechanical work so creators can focus on storytelling, pacing, and creative decisions.
```
