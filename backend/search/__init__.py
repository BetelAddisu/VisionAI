"""Search engine: combines keyword, semantic, visual and metadata search.

Per 06-search-engine.md no single method is enough. Results are ranked with
configurable weights and always reference real indexed footage — the engine
never invents clips.
"""
from backend.search.engine import SearchEngine
from backend.search.query_parser import clean_query, extract_keywords, fts_query
from backend.search.ranking import rank
from backend.search.types import SearchFilters, SearchResult

__all__ = [
    "SearchEngine",
    "SearchResult",
    "SearchFilters",
    "clean_query",
    "extract_keywords",
    "fts_query",
    "rank",
]
