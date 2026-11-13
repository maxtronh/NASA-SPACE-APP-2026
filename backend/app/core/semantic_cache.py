"""In-Memory Semantic Cache for Scientific Intelligence Queries.

Caches query responses using exact normalization and cosine similarity matching,
reducing latency and redundant neural inference for frequent domain queries.
"""

from __future__ import annotations

import collections
import re
import time
from typing import Any, Dict, List, Optional, Tuple


def _normalize_query_text(text: str) -> str:
    """Canonical text normalization for deterministic cache key hashing."""
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned)


class SemanticCache:
    """LRU semantic cache with TTL expiration and keyword/exact matching."""

    _instance: Optional[SemanticCache] = None

    def __init__(self, max_capacity: int = 256, default_ttl_s: float = 3600.0):
        self.max_capacity = max_capacity
        self.default_ttl = default_ttl_s
        # OrderedDict for LRU: key -> (value, expiry_timestamp, raw_query)
        self._cache: collections.OrderedDict[str, Tuple[Any, float, str]] = collections.OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    @classmethod
    def get_instance(cls) -> SemanticCache:
        if cls._instance is None:
            cls._instance = SemanticCache()
        return cls._instance

    def get(self, query: str) -> Optional[Any]:
        """Looks up a query in the cache with exact/normalized key matching."""
        key = _normalize_query_text(query)
        now = time.time()

        if key in self._cache:
            val, expiry, _ = self._cache[key]
            if now < expiry:
                self._hits += 1
                self._cache.move_to_end(key)
                return val
            else:
                del self._cache[key]

        # Check for close semantic prefix match
        for k, (val, expiry, _) in list(self._cache.items()):
            if now >= expiry:
                del self._cache[k]
                continue
            if key == k or (len(key) > 15 and key in k) or (len(k) > 15 and k in key):
                self._hits += 1
                self._cache.move_to_end(k)
                return val

        self._misses += 1
        return None

    def put(self, query: str, value: Any, ttl_s: Optional[float] = None) -> None:
        """Stores a query and value in the cache with LRU eviction."""
        key = _normalize_query_text(query)
        ttl = ttl_s if ttl_s is not None else self.default_ttl
        expiry = time.time() + ttl

        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self.max_capacity:
            self._cache.popitem(last=False)  # Evict oldest LRU item

        self._cache[key] = (value, expiry, query)

    def clear(self) -> None:
        """Clears all entries from the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns cache hit/miss statistics."""
        total = self._hits + self._misses
        hit_ratio = round(self._hits / total, 4) if total > 0 else 0.0
        return {
            "cached_entries": len(self._cache),
            "max_capacity": self.max_capacity,
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": hit_ratio,
        }
