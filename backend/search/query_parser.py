"""Query parser: extracts keyword terms and simple intent from a query.

Lightweight and deterministic — no LLM. Strips filler phrases like "find
clips where" and "show me" and returns the salient terms for keyword and
semantic search.
"""
from __future__ import annotations

import re

from backend.ai.embedding.provider import tokenize

FILLER_PATTERNS = [
    r"^find\s+(clips|shots|footage|videos|moments)\s+(where|of|with|showing|that)\s+",
    r"^find\s+(clips|shots|footage|videos|moments)\s+",
    r"^show\s+me\s+(all\s+)?",
    r"^find\s+",
    r"^(clips|shots|footage|videos|moments)\s+(where|of|with|showing|that)\s+",
]


def clean_query(query: str) -> str:
    q = query.strip().lower()
    for pat in FILLER_PATTERNS:
        q = re.sub(pat, "", q)
    return q.strip()


def extract_keywords(query: str) -> list[str]:
    """Return salient keyword tokens (deduplicated, length > 2)."""
    cleaned = clean_query(query)
    tokens = tokenize(cleaned)
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if len(t) > 2 and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def fts_query(query: str) -> str:
    """Build an FTS5 MATCH query from keywords (AND of terms)."""
    kws = extract_keywords(query)
    if not kws:
        return ""
    # Quote each term to avoid FTS5 syntax errors.
    return " ".join(f'"{kw}"' for kw in kws)
