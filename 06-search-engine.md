````md id="m7q2kf"
# 06 - Search Engine

**Version:** 1.0.0

---

# Purpose

The Search Engine is the retrieval system of the AI Video Post-Production Assistant.

Its responsibility is to allow users and AI agents to find relevant footage using natural language, metadata, and visual understanding.

The Search Engine converts:

```
Human Intent
```

into:

```
Relevant Video Clips
```

---

# Core Responsibility

The Search Engine enables queries such as:

```
Find clips where I explain Docker.

Find every shot with coffee.

Find my best talking-head moments.

Find clips where I look excited.

Find all drone footage.

Find footage with bad lighting.

Find clips where I mention AWS.
```

The user does not need to remember filenames or timestamps.

---

# Non Responsibilities

The Search Engine does NOT:

- Edit videos.
- Generate timelines.
- Analyze new videos.
- Run heavy AI processing.
- Modify metadata.

It only retrieves existing knowledge.

---

# Design Philosophy

The Search Engine combines multiple retrieval methods.

No single search method is enough.

The system uses:

```
Keyword Search

+

Semantic Search

+

Visual Search

+

Metadata Filtering

+

Ranking
```

---

# High-Level Architecture

```
                 User Query

                     │

                     ▼

              Query Processor

                     │

        ┌────────────┼────────────┐

        ▼            ▼            ▼

 Keyword Search  Semantic Search  Metadata Search

        │            │            │

        └────────────┼────────────┘

                     ▼

               Ranking Engine

                     │

                     ▼

              Search Results
```

---

# Search Components

Location:

```
backend/search/
```

Structure:

```
search/

├── engine.py

├── semantic.py

├── keyword.py

├── metadata.py

├── ranking.py

├── query_parser.py

├── filters.py

└── types.py
```

---

# Search Flow

Example:

User:

```
Find clips where I am coding and explaining cloud.
```

Pipeline:

```
Query

↓

Understand intent

↓

Create embedding

↓

Search FAISS

↓

Search transcript

↓

Filter metadata

↓

Rank results

↓

Return clips
```

---

# Query Processor

File:

```
query_parser.py
```

Purpose:

Understand user intent.

Input:

```
Find videos where I explain Kubernetes.
```

Output:

```json
{
"objects":
[
"kubernetes",
"computer"
],

"activity":
"explaining",

"category":
"tutorial"
}
```

---

# Query Types

The engine supports:

## Text Query

Example:

```
Find React tutorial clips
```

---

## Visual Query

Example:

```
Find clips showing a laptop
```

---

## Emotional Query

Example:

```
Find energetic moments
```

---

## Quality Query

Example:

```
Find clips with cinematic lighting
```

---

## Timeline Query

Example:

```
Find my introduction clips
```

---

# Keyword Search

Technology:

SQLite FTS5

Used for:

- transcripts
- object names
- metadata

Example:

Query:

```
Docker
```

Matches:

```
"I installed Docker yesterday"
```

---

# Semantic Search

Technology:

FAISS

Purpose:

Understand meaning.

Example:

Query:

```
Cloud infrastructure explanation
```

Can find:

```
"I deployed my backend on AWS"
```

Even if the word "cloud" is never spoken.

---

# Embedding Process

User query:

```
How I built my application
```

↓

Embedding Model

↓

Vector

↓

FAISS Search

↓

Similar clips

---

# Embedding Model

Primary:

```
BGE Small
```

Future:

```
BGE Large
```

---

# Stored Embeddings

FAISS contains:

```
Vector

↓

Clip ID
```

SQLite stores:

```
Clip ID

Source

Timestamp

FAISS index
```

---

# Visual Search

Visual search uses:

- frame embeddings
- object detection
- vision descriptions

Example:

Query:

```
Show me all coffee shots
```

Searches:

```
Objects:

coffee


Vision descriptions:

"person holding coffee cup"
```

---

# Metadata Search

Filters:

```
Duration

Resolution

Date

Folder

Camera

People

Objects

Quality
```

Example:

```
Find:

1080p

Drone

After January
```

---

# Ranking System

Search results must be ranked.

A result score combines:

```
Semantic similarity

+

Keyword relevance

+

Visual match

+

Quality score

+

User preference
```

---

# Ranking Formula

Initial implementation:

```
Score =

0.45 Semantic

+

0.25 Keyword

+

0.15 Visual

+

0.10 Quality

+

0.05 Recency
```

Weights should be configurable.

---

# Search Result Object

Example:

```json
{
"video_id":"video123",

"start_time":32.5,

"end_time":41.2,

"score":0.91,

"reason":

"Matches coding explanation"
}
```

---

# Result Preview

The UI should display:

```
Thumbnail

Video name

Timestamp

Transcript snippet

Detected objects

Confidence score
```

---

# Clip Context

Results should include surrounding context.

Example:

Match:

```
03:20-03:35
```

Return:

```
03:15-03:40
```

Reason:

Editors need context.

---

# Search Cache

Repeated searches should be cached.

Example:

```
Query:

"coding clips"

↓

Cached result

↓

Instant response
```

---

# Search Performance Goals

Target:

```
Keyword search

<100ms


Semantic search

<500ms


Combined search

<1 second
```

On minimum hardware.

---

# API Interface

Example:

```python
class SearchEngine:

    def search(
        self,
        query:str,

        filters=None
    ):
        pass
```

---

# Search Filters

Example:

```json
{
"category":"broll",

"duration":

{
"min":5,

"max":30
},

"quality":

"high"
}
```

---

# AI Agent Usage

The Planner uses Search Engine internally.

Example:

Planner:

```
Need B-roll of coding
```

Calls:

```
Search Engine

↓

Returns:

Laptop clips

Coding clips

Desk shots
```

---

# User Feedback Loop

Future versions should learn:

If user:

```
Uses result
```

Increase ranking.

If user:

```
Rejects result
```

Decrease ranking.

---

# Offline Requirement

Search must work without internet.

Required:

- Local embeddings
- Local database
- Local models

---

# Error Handling

## Missing Embedding

Action:

Fallback to keyword search.

---

## Corrupted Metadata

Action:

Ignore invalid record.

Log issue.

---

## Empty Results

Return:

- closest matches
- suggestions
- related clips

Example:

```
No exact match.

Similar clips:
```

---

# Testing Requirements

## Unit Tests

Test:

- Query parsing
- Ranking
- Filtering
- Score calculation


## Integration Tests

Test:

```
Video Database

↓

Search

↓

Results
```

---

# Acceptance Criteria

The Search Engine is complete when:

## Requirement 1

Users can search footage naturally.

---

## Requirement 2

Semantic meaning works.

Example:

```
"programming"

finds

"coding"
```

---

## Requirement 3

Visual searches work.

Example:

```
coffee

finds

coffee shots
```

---

## Requirement 4

Results include timestamps.

---

## Requirement 5

Search works completely offline.

---

# Future Improvements

Potential features:

- Voice search
- Image-based search
- Search by uploaded reference image
- Automatic B-roll matching
- Editor behavior learning
- Multi-language search
- Advanced cinematic scoring
- Viral moment detection
- Story similarity search

---

# Final Rule

The Search Engine is the bridge between raw footage and creative decisions.

The AI editor cannot create good edits if it cannot reliably find the right moments.

Search accuracy is more important than search speed.
````
