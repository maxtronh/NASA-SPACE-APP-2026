"""Unit tests for Semantic Cache and Token-Bucket Rate Limiter."""

from __future__ import annotations

import time
import pytest
from starlette.testclient import TestClient

from backend.app.core.rate_limiter import RateLimiter, TokenBucket
from backend.app.core.semantic_cache import SemanticCache
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_semantic_cache_put_and_get():
    cache = SemanticCache(max_capacity=10, default_ttl_s=10.0)
    cache.put("How does n-heptane burn in microgravity?", {"answer": "Spherical burning"})

    res = cache.get("How does n-heptane burn in microgravity?")
    assert res is not None
    assert res["answer"] == "Spherical burning"

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["cached_entries"] == 1


def test_semantic_cache_normalized_query():
    cache = SemanticCache(max_capacity=10, default_ttl_s=10.0)
    cache.put("What is cool flame kinetics?", {"result": "Low-temperature oxidation"})

    # Queries with different casing, whitespace, or trailing question marks
    res = cache.get("what is cool flame kinetics")
    assert res is not None
    assert res["result"] == "Low-temperature oxidation"


def test_semantic_cache_lru_eviction():
    cache = SemanticCache(max_capacity=2, default_ttl_s=10.0)
    cache.put("query 1", {"id": 1})
    cache.put("query 2", {"id": 2})
    cache.put("query 3", {"id": 3})  # Should evict query 1

    assert cache.get("query 1") is None
    assert cache.get("query 2") is not None
    assert cache.get("query 3") is not None
    assert cache.get_stats()["cached_entries"] == 2


def test_semantic_cache_ttl_expiration():
    cache = SemanticCache(max_capacity=10, default_ttl_s=0.1)
    cache.put("ephemeral query", {"data": 123}, ttl_s=0.05)

    time.sleep(0.06)
    assert cache.get("ephemeral query") is None


def test_token_bucket_rate_limiter():
    bucket = TokenBucket(capacity=3, refill_rate_per_sec=1.0)
    assert bucket.consume(1) is True
    assert bucket.consume(1) is True
    assert bucket.consume(1) is True
    assert bucket.consume(1) is False  # Exhausted

    # Wait for refill
    time.sleep(1.05)
    assert bucket.consume(1) is True


def test_api_si_cache_stats_endpoint(client):
    response = client.get("/api/v1/si/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cached_entries" in data
    assert "hits" in data
    assert "misses" in data
    assert "hit_ratio" in data
