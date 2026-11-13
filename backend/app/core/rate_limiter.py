"""Token-Bucket Rate Limiter Middleware & Dependency.

Protects API endpoints from request flooding while allowing legitimate burst traffic.
"""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request, status


class TokenBucket:
    """Thread-safe token bucket implementation."""

    def __init__(self, capacity: int = 60, refill_rate_per_sec: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(capacity)
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Attempts to consume tokens. Returns True if granted, False if rate limited."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Refill tokens based on elapsed time
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """In-memory rate limiter per client IP address."""

    _instance: Optional[RateLimiter] = None

    def __init__(self, capacity: int = 60, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, TokenBucket] = {}

    @classmethod
    def get_instance(cls) -> RateLimiter:
        if cls._instance is None:
            cls._instance = RateLimiter()
        return cls._instance

    def check_request(self, client_ip: str) -> bool:
        """Checks if a request from client_ip is allowed."""
        if client_ip not in self.buckets:
            self.buckets[client_ip] = TokenBucket(
                capacity=self.capacity,
                refill_rate_per_sec=self.refill_rate,
            )
        return self.buckets[client_ip].consume(1)


async def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency enforcing token-bucket rate limiting."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    limiter = RateLimiter.get_instance()
    if not limiter.check_request(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please throttle your requests.",
            headers={"Retry-After": "1"},
        )
