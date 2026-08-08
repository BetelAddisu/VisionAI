```md id="c8m5q"
# AGENT.md

# AI Video Post-Production Assistant - Development Agent Instructions

**Version:** 1.0.0

---

# Role

You are an autonomous software engineering agent responsible for building the AI Video Post-Production Assistant.

Your goal is to implement a local-first AI video editing assistant that helps creators transform raw footage into professional edits.

You must follow this document together with:

```

00-overview.md

01-system-architecture.md

02-project-structure.md

03-database.md

04-video-indexer.md

05-analysis-pipeline.md

06-search-engine.md

07-ai-planner.md

08-timeline-builder.md

09-davinci-integration.md

10-ui.md

11-performance.md

12-testing.md

13-roadmap.md

```

These documents define the system architecture and development requirements.

---

# Primary Objective

Build a system that can:

```

Import local videos

↓

Understand footage

↓

Search footage using natural language

↓

Understand scripts

↓

Create editing plans

↓

Generate timelines

↓

Export to DaVinci Resolve

```

---

# Development Rules

## Rule 1 - Local First

The system must prioritize local execution.

Do not introduce cloud dependencies unless explicitly required.

Default:

```

Videos stay on user's machine.

AI processing happens locally.

```

---

## Rule 2 - Respect Hardware Limitations

Target machine:

```

CPU:

Intel Core i3-7020U

RAM:

12GB

GPU:

Intel UHD Graphics 620

Storage:

HDD

```

Every implementation decision must consider:

- Memory usage
- CPU load
- Disk speed
- Model size

---

# Rule 3 - Build Incrementally

Never attempt to implement the entire system at once.

Follow roadmap order:

```

Foundation

↓

Indexing

↓

Analysis

↓

Search

↓

Planning

↓

Timeline

↓

DaVinci Integration

```

---

# Rule 4 - Avoid Overengineering

Prefer:

```

Simple working solution

```

over:

```

Complex perfect architecture

```

---

# Rule 5 - Production Quality

Even MVP code must include:

- Error handling
- Logging
- Documentation
- Type safety
- Tests

---

# Architecture Rules

The system must maintain separation:

```

Frontend

↓

API Layer

↓

Business Logic

↓

AI Services

↓

Database

```

Do not create:

```

Frontend

↓

Database

```

or:

```

Frontend

↓

AI Model

```

---

# Backend Guidelines

Technology:

```

Python

FastAPI

SQLite

```

---

## Backend Requirements

Every module should have:

```

Clear responsibility

Small functions

Typed inputs

Typed outputs

Tests

```

---

# AI Model Guidelines

AI models are tools.

They are not the application.

The application should:

```

Prepare context

↓

Call model

↓

Validate response

↓

Store result

```

---

# Model Selection Rules

Prefer:

- Smaller models
- Quantized models
- CPU-friendly models

Avoid:

- Huge models
- Unnecessary GPU requirements
- Constant model loading

---

# AI Output Validation

Never trust model output.

Every AI response must be:

```

Generated

↓

Validated

↓

Parsed

↓

Stored

```

---

# Video Processing Rules

Never load entire videos into memory.

Bad:

```

Load 20GB video

Process

```

Good:

```

Stream

Analyze

Cache results

```

---

# File Handling Rules

Always:

- Validate file existence
- Validate file type
- Handle corrupted files
- Never overwrite originals

Original footage is immutable.

---

# Database Rules

Database:

```

SQLite

```

Requirements:

- Use migrations
- Add indexes
- Avoid unnecessary duplication
- Store metadata instead of raw files

---

# Cache Rules

Cache expensive operations:

Examples:

```

Transcription

Embeddings

Thumbnails

Scene detection

```

Every cache entry should include:

```

Source hash

Model version

Creation timestamp

```

---

# Search Engine Rules

Search must combine:

```

Keyword

*

Semantic

*

Metadata

```

Never rely on one method.

---

# AI Planner Rules

The planner must:

- Never invent footage
- Use available metadata
- Produce structured JSON
- Follow platform requirements

Bad:

```

Use drone footage

```

if no drone footage exists.

Correct:

```

Search for drone footage.

If unavailable, suggest alternative.

```

---

# Timeline Rules

The Timeline Builder must:

- Generate deterministic output
- Preserve timestamps
- Validate clips
- Maintain track structure

The timeline is an instruction set, not the final video.

---

# DaVinci Rules

Primary integration:

```

XML Export

```

Do not attempt to replace Resolve.

The workflow:

```

AI creates draft

↓

Resolve finishes production

```

---

# UI Rules

The UI should hide complexity.

The user should see:

```

Projects

Videos

Search

AI Suggestions

Timeline

Export

```

Not:

```

Models

Vectors

Embeddings

Workers

```

---

# Performance Rules

Always:

- Use background workers
- Avoid blocking UI
- Limit concurrency
- Cache results
- Release unused models

---

# Testing Rules

Every feature requires:

```

Implementation

↓

Unit Test

↓

Integration Test

```

AI features require:

```

Quality evaluation

```

not only correctness testing.

---

# Code Style Rules

## Python

Use:

```

PEP8

Type hints

Docstrings

Async where appropriate

```

---

## TypeScript

Use:

```

Strict mode

Interfaces

Reusable components

```

---

# Git Rules

Commit messages:

Format:

```

type: description

```

Examples:

```

feat: add video metadata extraction

fix: handle missing video files

test: add search engine tests

```

---

# Documentation Rules

Every major feature requires:

```

Purpose

Architecture

Usage

Testing

Limitations

```

---

# Error Handling Rules

Never silently fail.

Every error must include:

```

Error message

Cause

Recovery action

```

---

# Logging Rules

Important operations must log:

```

Timestamp

Component

Action

Status

```

---

# Development Workflow

For every task:

## Step 1

Understand requirement.

---

## Step 2

Check existing architecture.

---

## Step 3

Implement smallest working version.

---

## Step 4

Write tests.

---

## Step 5

Document changes.

---

## Step 6

Verify against hardware limitations.

---

# Feature Completion Checklist

A feature is complete only when:

```

[ ] Code implemented

[ ] Tests added

[ ] Error handling added

[ ] Documentation updated

[ ] Performance considered

[ ] Works offline

```

---

# Debugging Process

When something fails:

Follow:

```

Reproduce

↓

Read logs

↓

Identify layer

↓

Fix root cause

↓

Add regression test

```

Do not patch symptoms.

---

# Security Rules

Protect:

- User files
- Local paths
- Project data

Never:

- Upload videos automatically
- Execute unknown files
- Modify original footage

---

# AI Ethics Rules

The AI assists creativity.

It does not:

- Remove creator control
- Claim ownership
- Replace human decisions

---

# Final Implementation Principle

Build a reliable assistant, not a collection of AI demos.

The system succeeds when a creator can:

```

Open application

↓

Import footage

↓

Explain their idea

↓

Receive a professional editing draft

↓

Finish in DaVinci Resolve

```

The priority is reliability, privacy, and creative usefulness.
```
