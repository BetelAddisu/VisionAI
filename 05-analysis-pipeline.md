````md id="8a4x2q"
# 05 - Analysis Pipeline

**Version:** 1.0.0

---

# Purpose

The Analysis Pipeline is the intelligence foundation of the AI Video Post-Production Assistant.

Its responsibility is to transform raw video files into structured information that the rest of the system can understand.

The pipeline converts:

```
Video Files
```

into:

```
Searchable Knowledge About The Video
```

The output enables:

- AI-powered search
- Clip recommendations
- Editing decisions
- Story planning
- Automatic timeline generation
- Quality improvement suggestions

---

# Core Responsibility

The Analysis Pipeline performs:

- Scene detection
- Audio extraction
- Speech recognition
- Frame extraction
- Visual understanding
- Object detection
- Face detection
- Quality analysis
- Embedding generation
- Metadata storage

---

# Non Responsibilities

The Analysis Pipeline does NOT:

- Edit videos
- Generate timelines
- Decide storytelling structure
- Modify original media
- Render final videos

Those belong to other systems.

---

# Design Principles

## 1. Process Once

Video analysis is expensive.

Every stage must produce reusable results.

Example:

```
Video

↓

Transcript

↓

Stored Permanently

↓

Future searches use stored transcript
```

Never transcribe the same video repeatedly.

---

## 2. Pipeline Must Be Resumable

The user may have:

- Laptop shutdown
- Power outage
- Application crash
- Storage interruption

The pipeline must continue from the last completed stage.

Example:

```
Completed

✓ Metadata

✓ Scenes

✓ Audio

✓ Transcript


Interrupted


Restart


Continue:

Frames
```

---

## 3. Low Hardware Priority

Target device:

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

The pipeline must prioritize:

- low memory usage
- sequential processing
- disk caching
- CPU efficiency

---

# Pipeline Overview

```
Video

│

▼

Metadata Validation

│

▼

Scene Detection

│

▼

Audio Extraction

│

▼

Speech Recognition

│

▼

Frame Sampling

│

▼

Vision Analysis

│

▼

Object Detection

│

▼

Face Detection

│

▼

Quality Analysis

│

▼

Embedding Generation

│

▼

Database Update
```

---

# Pipeline Components

```
backend/pipeline/

├── orchestrator.py

├── scheduler.py

├── processor.py

├── stages/

│   ├── metadata.py

│   ├── scenes.py

│   ├── audio.py

│   ├── transcription.py

│   ├── frames.py

│   ├── vision.py

│   ├── objects.py

│   ├── faces.py

│   ├── quality.py

│   └── embeddings.py

└── cache.py
```

---

# Stage 1: Metadata Validation

Purpose:

Confirm the video is usable.

Input:

```
video_id
```

Checks:

- File exists
- File readable
- Codec supported
- Duration available

Output:

```json
{
 "valid": true,

 "duration": 300
}
```

---

# Stage 2: Scene Detection

Purpose:

Split video into meaningful sections.

Technology:

PySceneDetect

Input:

```
video.mp4
```

Output:

```json
[
 {
  "start":0,

  "end":12.4,

  "scene":1
 },

 {
  "start":12.4,

  "end":32.1,

  "scene":2
 }
]
```

---

# Scene Detection Strategy

Do not analyze every frame.

Use:

```
content-aware detection
```

Detect:

- camera cuts
- major visual changes
- lighting changes

---

# Storage

Database:

```
scenes
```

Cache:

```
cache/scenes/
```

---

# Stage 3: Audio Extraction

Purpose:

Separate audio for processing.

Technology:

FFmpeg

Command concept:

```
video

↓

audio.wav
```

Settings:

```
Sample Rate:

16000Hz


Channels:

Mono
```

Reason:

Speech models do not need high-quality audio.

---

# Storage

```
cache/audio/
```

Example:

```
video123.wav
```

---

# Stage 4: Speech Recognition

Purpose:

Convert speech into searchable text.

Model:

Primary:

```
Faster Whisper Small
```

Future upgrade:

```
Whisper Large-v3
```

---

# Input

```
audio.wav
```

Output:

```json
[
{
"start":0.4,

"end":4.2,

"text":"Today I built an application"
}
]
```

---

# Processing Rules

The system should store:

- text
- timestamps
- confidence
- language
- speaker information (future)

---

# Storage

Database:

```
transcript_segments
```

---

# Stage 5: Frame Sampling

Purpose:

Create visual understanding without processing every frame.

---

# Sampling Strategy

Default:

```
1 frame every 2 seconds
```

For important scenes:

Increase sampling.

Example:

Talking head:

```
Every 3 seconds
```

Fast action:

```
Every 0.5 seconds
```

---

# Output

```
frame_001.jpg

frame_002.jpg

frame_003.jpg
```

---

# Storage

```
cache/frames/
```

---

# Stage 6: Vision Analysis

Purpose:

Understand visual content.

Model:

Primary:

```
Qwen2.5-VL-3B
```

Alternative:

```
Gemma Vision
```

---

# Input

Frame:

```
image.jpg
```

Prompt:

```
Describe this video frame.

Analyze:

- objects
- environment
- composition
- camera angle
- quality
- important details
```

---

# Output Example

```json
{
"scene":

"person coding at desk",

"objects":

[
"laptop",
"monitor",
"keyboard"
],

"shot":

"medium close-up",

"lighting":

"warm",

"composition":

"centered subject"
}
```

---

# Stage 7: Object Detection

Purpose:

Fast object recognition.

Model:

```
YOLO Nano
```

---

# Detect:

Examples:

```
Laptop

Phone

Camera

Car

Person

Microphone

Coffee

Monitor
```

---

# Output

```json
{
"object":"laptop",

"confidence":0.94
}
```

---

# Stage 8: Face Detection

Purpose:

Understand people presence.

Technology:

```
InsightFace
```

---

# Detect:

```
Face location

Face presence

Looking direction

Eyes open

Smile
```

---

# Output

```json
{
"face_detected":true,

"smiling":true,

"looking_camera":true
}
```

---

# Future

Person recognition:

```
Betel

Guest

Speaker
```

---

# Stage 9: Quality Analysis

Purpose:

Evaluate footage quality.

No AI model required.

Technology:

OpenCV.

---

# Metrics

## Brightness

Detect:

- underexposure
- overexposure


## Sharpness

Detect:

- blurry footage


## Noise

Detect:

- low-light noise


## Contrast

Detect:

- flat image


## Stability

Detect:

- camera shake

---

# Output

```json
{
"brightness":0.72,

"sharpness":0.88,

"noise":0.15
}
```

---

# Stage 10: Embedding Generation

Purpose:

Enable semantic search.

Example:

User:

```
Find clips where I explain cloud computing
```

System:

```
Search embeddings

↓

Find matching clips
```

---

# Model

Primary:

```
BGE Small
```

---

# Generate Embeddings For:

Transcript:

```
"What I said"
```

Visual:

```
"What is shown"
```

Combined:

```
Meaning of clip
```

---

# Storage

SQLite:

```
embedding_id

source_id

faiss_index
```

FAISS:

```
vector data
```

---

# Pipeline Orchestration

The orchestrator controls execution.

Example:

```python
analyze_video(video_id)
```

runs:

```
metadata

↓

scenes

↓

audio

↓

transcript

↓

frames

↓

vision

↓

objects

↓

faces

↓

quality

↓

embeddings
```

---

# Job System

Every stage creates a job.

Example:

```
JOB-001

type:

TRANSCRIPTION


status:

RUNNING


progress:

65%
```

---

# Job States

```
QUEUED

RUNNING

PAUSED

FAILED

COMPLETED
```

---

# Hardware Optimization

## CPU

Only one heavy AI process.

Never run:

```
Whisper

+

Vision

+

YOLO

```

simultaneously.

---

## RAM

Maximum memory target:

```
< 4GB
```

for pipeline process.

---

## Disk

Because HDD is slow:

- avoid random reads
- process sequentially
- cache outputs
- avoid duplicate decoding

---

# Model Loading Strategy

Do not keep every model loaded.

Bad:

```
Whisper

Vision

YOLO

Embeddings

all loaded
```

Good:

```
Load Whisper

Process

Unload


Load Vision

Process

Unload
```

---

# Failure Handling

Every stage must record:

```
started_at

completed_at

error

retry_count
```

Example:

```
Vision Analysis Failed

Retry:

3 times

Then mark failed.
```

---

# API Interface

Example:

```python
class AnalysisPipeline:

    def analyze(
        self,
        video_id:str
    ):
        pass
```

---

# Testing Requirements

## Unit Tests

Test:

- frame extraction
- transcript parsing
- metadata handling
- cache validation


## Integration Tests

Test:

```
Video

↓

Pipeline

↓

Database
```

---

# Acceptance Criteria

The pipeline is complete when:

## Requirement 1

A video can be analyzed from start to finish.

---

## Requirement 2

The process can resume after interruption.

---

## Requirement 3

Results are stored permanently.

---

## Requirement 4

Running analysis twice does not duplicate work.

---

## Requirement 5

Search can retrieve clips based on meaning.

---

# Future Improvements

Possible additions:

- Automatic color grading analysis
- Audio cleanup recommendations
- Music beat detection
- Emotion timeline
- Viral retention prediction
- Camera quality scoring
- Automatic B-roll matching
- Multi-camera synchronization
- Speaker diarization
- Advanced cinematic analysis

---

# Final Rule

The Analysis Pipeline creates the intelligence layer of the entire application.

Every later feature depends on its accuracy.

A fast but incorrect analysis system creates a bad editor.

A slower but reliable analysis system creates a powerful editor.
````
