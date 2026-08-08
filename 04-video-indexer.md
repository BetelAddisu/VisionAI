````md
# 04 - Video Indexer

**Version:** 1.0.0

---

# Purpose

The Video Indexer is the first processing stage of the AI Video Post-Production Assistant.

Its responsibility is to discover, validate, and register all video assets inside a project.

The Video Indexer does not analyze video content.

It does not run AI models.

It does not create transcripts.

It only creates a reliable inventory of available media.

---

# Core Responsibility

The Video Indexer converts:

```
Raw Files On Disk
```

into:

```
Structured Video Records In Database
```

Example:

Input:

```
D:/Videos/MyChannel/

    vlog001.mp4

    interview.mov

    broll/drone01.mp4
```

Output:

```
Videos Table

vlog001.mp4

interview.mov

drone01.mp4
```

---

# Design Principles

## 1. Never Modify Original Files

The indexer only reads files.

It must never:

- rename videos
- move videos
- compress videos
- convert formats
- delete files

---

## 2. Detect Changes Automatically

The system must know when:

- a new video appears
- a video was removed
- a video was modified

This prevents unnecessary reprocessing.

---

## 3. Fast Metadata Extraction

The indexer should not decode entire videos.

It only reads:

- file information
- container information
- codec information

---

## 4. Incremental Processing

The indexer should support:

```
First Run

↓

Scan 1000 videos


Later Run

↓

Scan only changes
```

---

# Technology

## Required Tools

FFmpeg

Used for:

- metadata extraction
- codec information
- duration
- resolution


Python

Used for:

- filesystem operations
- hashing
- database communication


SQLite

Used for:

- storing video records

---

# Supported Video Formats

Initial support:

```
.mp4

.mov

.mkv

.webm

.avi

.m4v

.flv
```

Future:

```
.mxf

.braw

.r3d
```

---

# Input

The indexer receives:

```json
{
    "project_id": "abc123",

    "folder_path": "D:/Videos/MyProject"
}
```

---

# Output

Creates:

```json
{
    "video_id": "video001",

    "filename": "intro.mp4",

    "duration": 120.5,

    "width": 1920,

    "height": 1080,

    "fps": 30
}
```

---

# Indexing Workflow

```
User Selects Folder

        |

        v

Validate Folder

        |

        v

Find Video Files

        |

        v

Calculate File Hash

        |

        v

Extract Metadata

        |

        v

Check Existing Database Record

        |

        v

Insert Or Update Record

        |

        v

Create Analysis Jobs
```

---

# Module Structure

Location:

```
backend/indexing/
```

Structure:

```
indexing/

├── scanner.py

├── metadata.py

├── hash.py

├── validator.py

├── indexer.py

└── types.py
```

---

# Scanner Module

File:

```
scanner.py
```

Responsibility:

Find video files.

Example:

```python
scan_directory(
    "D:/Videos"
)
```

Returns:

```python
[
    "video1.mp4",
    "video2.mov"
]
```

---

# Scanner Rules

The scanner must:

Include supported formats.

Ignore hidden files.

Ignore temporary files.

Ignore cache folders.

Ignore exports.

Ignore system folders.

Example ignored:

```
.cache/

.tmp/

exports/

.git/
```

---

# Metadata Extractor

File:

```
metadata.py
```

Uses:

```
ffprobe
```

Extract:

- duration
- width
- height
- fps
- codec
- bitrate
- audio streams
- video streams

Example:

Input:

```
video.mp4
```

Output:

```json
{
 "duration":245.2,

 "width":1920,

 "height":1080,

 "fps":30,

 "codec":"h264"
}
```

---

# File Hashing

File:

```
hash.py
```

Purpose:

Detect file changes.

Algorithm:

SHA-256

Example:

```
video.mp4

↓

hash

↓

a83f92ab91...
```

Database:

```
videos.hash
```

---

# Why Hash Files?

Scenario:

```
video.mp4

Already analyzed
```

User replaces it.

Filename stays identical.

Without hashing:

```
System thinks:

Same file
```

With hashing:

```
Different hash

↓

Re-analyze
```

---

# Hash Optimization

Large videos can be several GB.

Full hashing is slow on HDD.

Use two-stage hashing.

## Stage 1

Fast fingerprint:

```
filename

file size

modified date
```

If unchanged:

Skip full hash.

---

## Stage 2

Only changed files:

Calculate SHA-256.

---

# Validator Module

File:

```
validator.py
```

Checks:

- File exists
- File readable
- Format supported
- Metadata extraction successful

---

# Indexer Controller

File:

```
indexer.py
```

Coordinates:

```
Scanner

↓

Validator

↓

Hash Generator

↓

Metadata Extractor

↓

Database Repository
```

---

# Database Interaction

The indexer communicates only through:

```
VideoRepository
```

Never:

```
Indexer

↓

SQL Query
```

---

# Duplicate Detection

Two files may contain the same video.

Example:

```
video.mp4

copy_of_video.mp4
```

Same hash:

```
a82ff9
```

Database stores:

```
duplicate_of
```

Future feature.

Initial version:

Warn user.

---

# Folder Categories

The indexer should recognize optional folders:

```
videos/

├── raw/

├── broll/

├── audio/

├── exports/

└── archive/
```

Store:

```
media_category
```

Example:

```
raw

broll

podcast
```

---

# Progress Tracking

Large libraries require progress reporting.

Example:

```
Scanning:

340 / 2000 videos

17%
```

Database:

Jobs table.

---

# Error Handling

Possible errors:

## Unsupported File

Action:

Skip.

Log warning.

---

## Corrupt Video

Action:

Mark:

```
status = failed
```

Continue.

---

## Permission Error

Action:

Log.

Notify user.

---

## Missing File

Action:

Mark:

```
available=false
```

Do not delete metadata.

---

# Performance Requirements

Target hardware:

```
Intel i3-7020U

12GB RAM

HDD
```

Requirements:

- Never load video into memory.
- Process one file at a time.
- Avoid unnecessary hashing.
- Allow pause/resume.

---

# Indexing Queue

After indexing:

Create analysis jobs.

Example:

```
Video Added

↓

Job:

Extract Audio

↓

Job:

Detect Scenes

↓

Job:

Generate Transcript

↓

Job:

Generate Embeddings
```

---

# API Interface

Example:

```python
class VideoIndexer:

    def index_project(
        self,
        project_id: str,
        folder: str
    ):
        pass
```

---

# Events

The indexer emits:

```
VIDEO_DISCOVERED

VIDEO_UPDATED

VIDEO_REMOVED

INDEX_STARTED

INDEX_COMPLETED

INDEX_FAILED
```

---

# Testing Requirements

## Unit Tests

Test:

- File detection
- Format filtering
- Hash generation
- Metadata parsing

---

## Integration Tests

Test:

```
Folder

↓

Indexer

↓

Database
```

---

# Acceptance Criteria

The Video Indexer is complete when:

## Requirement 1

A user can select a folder.

---

## Requirement 2

All supported videos appear in the database.

---

## Requirement 3

Metadata is correctly extracted.

---

## Requirement 4

Re-running indexing does not duplicate records.

---

## Requirement 5

Modified videos are detected.

---

## Requirement 6

Large libraries can resume after interruption.

---

# Future Improvements

Possible additions:

- Watch folders
- Automatic synchronization
- External drive support
- Network storage support
- Cloud backup
- Duplicate video cleanup
- Proxy generation
- Automatic folder organization

---

# Final Rule

The Video Indexer is the foundation of the entire system.

If the index is incorrect, every AI feature built on top of it will produce incorrect results.

Accuracy and reliability are more important than speed.
````
