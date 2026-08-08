"""Unit tests for the embedding provider."""
from backend.ai.embedding.provider import HashingEmbeddingProvider, tokenize


def test_tokenize_lowercases_and_splits():
    assert tokenize("Hello, World 123!") == ["hello", "world", "123"]


def test_embed_returns_fixed_dimension():
    emb = HashingEmbeddingProvider(dimension=64)
    vec = emb.embed("hello world")
    assert len(vec) == 64


def test_embed_is_normalized():
    import math
    emb = HashingEmbeddingProvider(dimension=64)
    vec = emb.embed("some meaningful text about video editing")
    norm = math.sqrt(sum(v * v for v in vec))
    assert abs(norm - 1.0) < 1e-6


def test_similar_texts_have_higher_similarity_than_unrelated():
    import math
    emb = HashingEmbeddingProvider(dimension=256)
    a = emb.embed("deploying an application to the cloud")
    b = embed_cos = emb.embed("cloud application deployment")
    c = embed_other = emb.embed("cooking pasta recipe")

    def cos(x, y):
        return sum(i * j for i, j in zip(x, y))

    assert cos(a, b) > cos(a, c)


def test_embed_many_consistent_with_embed():
    emb = HashingEmbeddingProvider(dimension=64)
    single = emb.embed("hello world")
    many = emb.embed_many(["hello world"])
    assert single == many[0]
