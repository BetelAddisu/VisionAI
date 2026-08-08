"""Unit tests for the search query parser."""
from backend.search.query_parser import (
    clean_query,
    extract_keywords,
    fts_query,
)


def test_clean_query_strips_filler_phrases():
    assert clean_query("Find clips where I explain AWS") == "i explain aws"
    assert clean_query("show me all clips of the beach") == "the beach"
    assert clean_query("Find footage with drone shots") == "drone shots"


def test_extract_keywords_dedupes_and_filters_short():
    kws = extract_keywords("find clips where I explain AWS and aws again")
    assert "aws" in kws
    # Short tokens (i, find) are excluded.
    assert "i" not in kws
    assert "find" not in kws
    # Deduplicated.
    assert kws.count("aws") == 1


def test_fts_query_quotes_terms():
    q = fts_query("find clips about deployment")
    assert q == '"about" "deployment"'


def test_clean_query_handles_empty():
    assert clean_query("") == ""
    assert extract_keywords("") == []
    assert fts_query("") == ""
