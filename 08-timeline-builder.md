```md id="r82kf"
# 08 - Timeline Builder

**Version:** 1.0.0

---

# Purpose

The Timeline Builder converts the AI Planner's creative decisions into an actual editable video timeline.

The AI Planner decides:

```

What should happen?

```

The Timeline Builder decides:

```

How should it be arranged technically?

```

The output is a structured timeline that can be:

- Exported to DaVinci Resolve
- Rendered through FFmpeg
- Modified manually by the creator

---

# Core Responsibility

The Timeline Builder creates:

- Video tracks
- Audio tracks
- Clip positions
- Cut points
- Transitions
- Subtitle timing
- Effects metadata
- B-roll placement
- Audio arrangement

---

# Non Responsibilities

The Timeline Builder does NOT:

- Analyze videos
- Understand storytelling
- Search footage
- Decide what clips are interesting
- Generate AI recommendations

It only executes the editing plan.

---

# Architecture

```

AI Planner

```
 |

 ▼
```

Editing Plan JSON

```
 |

 ▼
```

Timeline Builder

```
 |

 ▼
```

Timeline Database

```
 |

 ▼
```

Export Layer

```
 |

 ▼
```

DaVinci Resolve

```

---

# Technology

## Timeline Format

Primary internal format:

```

OpenTimelineIO (OTIO)

```

Reason:

- Open standard
- Supported by professional editing workflows
- Can convert to multiple formats

---

## Export Targets

Initial:

```

DaVinci Resolve XML

```

Future:

```

Adobe Premiere XML

Final Cut XML

EDL

```

---

# Module Structure

Location:

```

backend/timeline/

```

Structure:

```

timeline/

├── builder.py

├── models.py

├── clips.py

├── tracks.py

├── transitions.py

├── effects.py

├── subtitles.py

├── validator.py

└── generator.py

```

---

# Timeline Data Model

A timeline consists of:

```

Timeline

```
|

├── Video Tracks

|

├── Audio Tracks

|

├── Clips

|

├── Effects

|

└── Metadata
```

```

---

# Timeline Example

```

Timeline: My AI Story

Video Track 1

00:00 ───────── Hook Clip

00:05 ───────── Talking Head

00:20 ───────── B-roll

Video Track 2

00:00 ───────── Subtitle Layer

Audio Track 1

00:00 ───────── Voice

Audio Track 2

00:00 ───────── Music

````

---

# Internal Timeline Schema

Example:

```json
{
"name":"AI Journey",

"fps":30,

"duration":420,

"tracks":[

{
"type":"video",

"id":"V1",

"clips":[

{
"source":"video123.mp4",

"source_start":12.4,

"source_end":20.5,

"timeline_start":0
}

]

}

]
}
````

---

# Clip Object

Every clip contains:

```json
{
"id":"clip001",

"source_video":"video123",

"source_start":20.5,

"source_end":35.2,

"timeline_start":40,

"track":1
}
```

---

# Clip Processing

The Timeline Builder must:

1. Validate clip exists.
2. Validate timestamps.
3. Convert source time to timeline position.
4. Add clip to correct track.
5. Apply effects.

---

# Track System

Initial tracks:

```
V1

Main video


V2

B-roll


V3

Graphics


V4

Subtitles


A1

Voice


A2

Music


A3

Sound effects
```

---

# Track Rules

## Main Video

Contains:

* Talking head
* Primary footage
* Interviews

---

## B-roll

Contains:

* Supporting visuals
* Screen recordings
* Environment shots

---

## Graphics

Contains:

* Logos
* Animations
* Lower thirds

---

## Subtitle Track

Contains:

* Captions
* Highlighted words

---

# Automatic Clip Placement

Example:

Planner output:

```
Use coding B-roll during explanation.
```

Timeline Builder:

```
Find clip timestamp

↓

Place on B-roll track

↓

Align with narration
```

---

# Cut Handling

The system supports:

## Hard Cut

Default.

```
Clip A

|

Clip B
```

---

## Cross Dissolve

Used for:

* Time changes
* Emotional moments

---

## Fade

Used for:

* Beginning
* Ending

---

# Transition Rules

Avoid excessive transitions.

Default:

```
80%

Hard cuts
```

```
15%

Dissolve
```

```
5%

Special transitions
```

---

# Subtitle System

The Timeline Builder creates subtitle instructions.

Input:

Transcript:

```
"I built my first AI application"
```

Output:

```json
{
"text":"I built my first AI application",

"start":2.3,

"end":5.1,

"style":"highlight"
}
```

---

# Subtitle Styles

Presets:

```
clean

youtube

shorts

cinematic

minimal
```

---

# Subtitle Emphasis

Important words can be highlighted.

Example:

Sentence:

```
I built my first AI application
```

Highlight:

```
AI application
```

---

# Audio Timeline

Audio arrangement:

```
Voice

+

Music

+

Effects
```

---

# Voice Rules

Voice always has priority.

If music conflicts:

Reduce music volume.

---

# Audio Ducking

Example:

Voice:

```
-6 dB
```

Music:

```
-25 dB
```

During speech.

---

# Music Placement

The Timeline Builder receives:

```
Music recommendation
```

Creates:

```
Music track

↓

Fade in

↓

Fade out
```

---

# Effects System

Effects are metadata instructions.

Examples:

```json
{
"type":"zoom",

"amount":1.05,

"start":20,

"end":25
}
```

---

# Supported Effects

Initial:

```
Zoom

Crop

Fade

Blur

Speed change

Text overlay
```

---

# Color Metadata

The Timeline Builder stores:

```
color_profile
```

Example:

```json
{
"style":"cinematic",

"contrast":"+10",

"temperature":"+5"
}
```

Actual grading happens in:

* DaVinci Resolve
* FFmpeg renderer

---

# Timeline Validation

Before export:

Check:

## Missing Files

```
Does every clip exist?
```

---

## Invalid Timecodes

```
End time > start time
```

---

## Overlapping Tracks

```
Are clips conflicting?
```

---

## Empty Timeline

```
Does timeline contain content?
```

---

# Database Storage

Tables:

```
timeline

timeline_clips
```

---

# Timeline Generation Flow

```
Planner JSON

↓

Validate Schema

↓

Create Timeline Object

↓

Add Tracks

↓

Insert Clips

↓

Add Effects

↓

Add Subtitles

↓

Save Database

↓

Export
```

---

# DaVinci Resolve Integration

Primary export:

```
DaVinci Resolve XML
```

The XML should preserve:

* Timeline structure
* Clip references
* Cuts
* Audio tracks
* Basic effects

---

# Proxy Workflow

Important for weak hardware.

Original:

```
4K footage
```

Proxy:

```
720p / 1080p compressed copy
```

Editing uses:

```
Proxy
```

Final render uses:

```
Original
```

---

# Low Hardware Strategy

Target:

```
Intel i3-7020U

12GB RAM

Intel Graphics 620

HDD
```

Rules:

* Never decode all videos simultaneously.
* Use proxies.
* Generate timeline before rendering.
* Avoid real-time previews.
* Render sequentially.

---

# API Interface

Example:

```python
class TimelineBuilder:

    def build(
        self,
        edit_plan
    ):
        pass
```

---

# Error Handling

## Missing Clip

Action:

Replace with closest match.

---

## Export Failure

Action:

Save timeline locally.

Retry export.

---

## Invalid Planner Output

Action:

Reject.

Request regeneration.

---

# Testing Requirements

## Unit Tests

Test:

* Clip placement
* Track assignment
* Time calculations
* Subtitle generation

## Integration Tests

Test:

```
Planner

↓

Timeline Builder

↓

XML Export
```

---

# Acceptance Criteria

Timeline Builder is complete when:

## Requirement 1

AI plans can become timelines.

---

## Requirement 2

Generated timelines open in DaVinci Resolve.

---

## Requirement 3

Cuts and clip positions are correct.

---

## Requirement 4

Subtitles are correctly timed.

---

## Requirement 5

Audio tracks are organized.

---

# Future Improvements

Possible additions:

* Automatic multicam editing
* Beat-synchronized cuts
* Advanced transitions
* Motion graphics generation
* DaVinci API integration
* Smart reframing
* Automatic vertical video conversion
* Automatic Shorts creation
* Multiple edit versions

---

# Final Rule

The Timeline Builder is the execution layer between AI creativity and professional editing software.

The goal is not to replace DaVinci Resolve.

The goal is to open DaVinci Resolve with 80% of the editing work already completed.

```
```
