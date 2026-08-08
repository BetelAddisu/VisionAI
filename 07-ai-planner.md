```md
# 07 - AI Planner

**Version:** 1.0.0

---

# Purpose

The AI Planner is the creative reasoning layer of the AI Video Post-Production Assistant.

Its responsibility is to transform:

```

Creator Intent + Script + Available Footage Knowledge

```

into:

```

Structured Editing Instructions

```

The AI Planner acts as a virtual editor who understands:

- storytelling
- pacing
- audience retention
- platform requirements
- visual composition
- B-roll placement
- emotional progression

The AI Planner does not directly edit videos.

It creates an editing blueprint that other systems execute.

---

# Core Responsibility

The AI Planner should answer:

- What clips should be used?
- In what order?
- Where should cuts happen?
- Where should B-roll appear?
- Where should subtitles emphasize words?
- Where should music change?
- Where should the pacing increase or slow down?
- What moments should be removed?
- How should the story flow?

---

# Non Responsibilities

The AI Planner does NOT:

- Render videos.
- Modify original files.
- Generate effects directly.
- Search raw files manually.
- Replace DaVinci Resolve.
- Perform computer vision analysis.

It depends on:

- Search Engine
- Analysis Pipeline
- Metadata Database

---

# Design Philosophy

The planner should behave like a professional editor.

The workflow:

```

Understand Story

↓

Understand Audience

↓

Understand Available Footage

↓

Create Editing Strategy

↓

Select Clips

↓

Create Timeline Instructions

```

---

# Architecture

```

```
             User Input

                 │

                 ▼

         Story Understanding

                 │

                 ▼

          Editing Strategy

                 │

                 ▼

          Search Requests

                 │

                 ▼

          Clip Selection

                 │

                 ▼

         Timeline Instructions

                 │

                 ▼

         Timeline Builder
```

```

---

# Module Structure

Location:

```

backend/planner/

```

Structure:

```

planner/

├── planner.py

├── prompt_builder.py

├── story_analysis.py

├── editing_rules.py

├── platform_rules.py

├── clip_selector.py

├── scoring.py

└── types.py

```

---

# AI Model

Primary:

```

Qwen3-4B

```

Reason:

- Runs locally.
- Good reasoning ability.
- Suitable for limited hardware.

Future upgrades:

```

Qwen3-14B

Llama 3.3

Claude/Gemini API (optional)

````

---

# Planner Input

The planner receives:

```json
{
"topic":
"How I built my first SaaS",

"script":
"I started learning programming..."

"platform":
"YouTube",

"target_length":
"8 minutes",

"audience":
"developers",

"style":
"educational cinematic"
}
````

---

# Additional Context

The planner also receives:

```
Available footage

Transcript database

Scene information

Visual metadata

User preferences
```

---

# Planner Pipeline

```
User Brief

↓

Story Analysis

↓

Structure Generation

↓

Clip Requirements

↓

Search Engine Queries

↓

Clip Matching

↓

Edit Plan Creation

↓

Timeline Output
```

---

# Story Analysis

Purpose:

Understand narrative structure.

The planner identifies:

## Hook

First seconds.

Goal:

Capture attention.

Example:

```
"Most developers waste months learning this..."
```

---

## Setup

Introduce context.

---

## Problem

Explain challenge.

---

## Journey

Show progress.

---

## Resolution

Show result.

---

## Call To Action

End interaction.

---

# Example Story Structure

Input:

```
Building my AI application
```

Output:

```
0:00

Hook

Show final result


0:15

Problem

Why I built it


1:00

Process

Development footage


6:00

Result

Final application


7:30

Conclusion
```

---

# Editing Rules Engine

The planner uses predefined editing principles.

Location:

```
editing_rules.py
```

---

# Talking Head Rules

Example:

Avoid:

```
30 seconds static talking
```

Prefer:

```
Talking head

+

B-roll

+

Zoom

+

Text emphasis
```

---

# Retention Rules

For short-form:

```
Visual change every 2-5 seconds
```

For long-form:

```
Visual change every 5-15 seconds
```

---

# Silence Rules

Detect:

```
Long pause

Filler words

Repeated sentences
```

Suggest:

```
Remove
```

---

# Platform Rules

Different platforms require different strategies.

---

# YouTube

Focus:

* storytelling
* retention
* chapters
* pacing

---

# TikTok / Shorts

Focus:

* immediate hook
* fast pacing
* subtitles
* visual changes

---

# LinkedIn

Focus:

* professional storytelling
* credibility
* clear message

---

# Clip Requirement Generation

The planner should not immediately choose clips.

It should define requirements.

Example:

```
Need:

Person coding

Duration:

5 seconds

Purpose:

Explain development process
```

---

# Search Integration

Planner sends requests:

Example:

```json
{
"query":
"person coding laptop",

"duration":
"3-8 seconds",

"purpose":
"B-roll"
}
```

---

# Clip Evaluation

Returned clips are scored.

Factors:

```
Visual quality

↓

Story relevance

↓

Transcript relevance

↓

Emotion

↓

Composition
```

---

# Edit Plan Format

The planner output must be structured JSON.

Example:

```json
{
"title":
"My AI Journey",

"sections":

[
{
"type":"hook",

"start":0,

"duration":5,

"clips":
[
"video123"
],

"instructions":

[
"fast cut",
"subtitle emphasis"
]
}
]
}
```

---

# Timeline Instructions

Each instruction contains:

```
Clip

Start Time

End Time

Track

Effect

Transition

Subtitle

Audio
```

Example:

```json
{
"clip":
"video123",

"source_start":
12.4,

"source_end":
18.7,

"timeline_position":
30,

"transition":
"hard_cut"
}
```

---

# Editing Intelligence Features

## Automatic Cut Suggestions

The planner receives:

```
Transcript

↓

Detect:

- filler words
- repetition
- weak sentences
```

Suggest:

```
Remove section
```

---

## B-roll Suggestions

Example:

Narration:

"I deployed my backend to AWS."

Planner:

```
Search:

AWS dashboard

Server

Cloud animation

Coding
```

---

## Visual Variety

Planner checks:

```
Current sequence:

Talking head

Talking head

Talking head

```

Suggestion:

```
Insert B-roll
```

---

# Color Suggestions

Planner does not directly color grade.

It creates recommendations.

Example:

```json
{
"style":
"cinematic tech",

"recommendation":
"Increase contrast and add cooler shadows"
}
```

---

# Music Suggestions

Planner outputs:

```json
{
"music_style":
"ambient technology",

"energy":
"medium",

"start":
"00:15"
}
```

---

# Thumbnail Suggestions

Planner identifies:

* strongest frame
* emotional moment
* clear subject
* visual curiosity

Output:

```json
{
"frame":
"frame_182.jpg",

"reason":
"Strong facial expression"
}
```

---

# Prompt Engineering

Prompts must be version controlled.

Location:

```
prompts/

planner_system.txt

editing_rules.txt

platform_rules.txt
```

---

# Prompt Structure

Every planner request contains:

```
Role

↓

Context

↓

Available Data

↓

Rules

↓

Expected Output Format
```

---

# Hallucination Prevention

The planner must never invent footage.

Bad:

```
Use drone shot of city
```

when no drone footage exists.

Correct:

```
Search database first.

If unavailable:

suggest alternative.
```

---

# Hardware Optimization

Because target hardware is limited:

Rules:

* Load planner model only when needed.
* Use quantized models.
* Do not keep vision models loaded.
* Limit context size.
* Use retrieved metadata instead of raw video.

---

# Planner Memory

The planner should remember:

Project preferences:

* editing style
* preferred pacing
* subtitle style
* music style

Stored in:

```
settings
```

Not inside the model.

---

# API Interface

Example:

```python
class AIPlanner:

    def create_plan(
        self,
        project_id:str,
        brief:str
    ):
        pass
```

---

# Error Handling

## No Matching Clips

Response:

```
No footage found.

Suggest alternatives.
```

---

## Invalid Plan

Validation:

```
Check JSON schema.

Reject invalid output.

Retry.
```

---

## Model Failure

Fallback:

```
Retry smaller context.

Reduce request.

Log error.
```

---

# Testing Requirements

## Unit Tests

Test:

* prompt generation
* JSON validation
* rule application
* score calculation

## Integration Tests

Test:

```
Brief

↓

Planner

↓

Search

↓

Edit Plan
```

---

# Acceptance Criteria

The AI Planner is complete when:

## Requirement 1

A user can provide a script.

---

## Requirement 2

The system creates a structured editing plan.

---

## Requirement 3

The plan references real footage only.

---

## Requirement 4

The plan can be converted into a timeline.

---

## Requirement 5

Different platforms create different editing strategies.

---

# Future Improvements

Potential additions:

* Learn creator editing style.
* Analyze successful videos.
* Predict retention drops.
* Automatically create Shorts.
* Generate multiple edit variations.
* Learn audience preferences.
* AI director mode.
* Real-time editing assistant.

---

# Final Rule

The AI Planner is the creative brain of the system.

It should not make videos.

It should make excellent editing decisions that can be executed reliably by the rest of the pipeline.

```
```
