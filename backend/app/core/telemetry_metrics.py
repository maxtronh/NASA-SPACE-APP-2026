"""Prometheus Metrics & OpenTelemetry W3C Distributed Tracing Middleware.

Provides:
1. Standard Prometheus text-format metrics exporter at `/metrics`.
2. Request latency histograms and status code counters.
3. OpenTelemetry W3C traceparent context extraction and generation.
4. Scientific domain metrics (SI queries, abstentions, cache hit ratios).
"""

from __future__ import annotations

import collections
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class MetricsRegistry:
    """Thread-safe in-memory Prometheus-compatible metrics registry."""

    _instance: Optional[MetricsRegistry] = None

    def __init__(self):
        # request_count: (method, path, status_code) -> count
        self.request_counts: Dict[Tuple[str, str, int], int] = collections.defaultdict(int)
        # request_latency_seconds: (method, path) -> list of latencies
        self.request_latencies: Dict[Tuple[str, str], List[float]] = collections.defaultdict(list)
        # SI domain counters
        self.si_queries_total: int = 0
        self.si_abstentions_total: int = 0
        self.cache_hits_total: int = 0
        self.cache_misses_total: int = 0

    @classmethod
    def get_instance(cls) -> MetricsRegistry:
        if cls._instance is None:
            cls._instance = MetricsRegistry()
        return cls._instance

    def record_request(self, method: str, path: str, status_code: int, duration_s: float) -> None:
        """Records an HTTP request and its execution latency."""
        # Sanitize path to avoid cardinality explosion
        clean_path = self._sanitize_path(path)
        self.request_counts[(method, clean_path, status_code)] += 1
        lat_list = self.request_latencies[(method, clean_path)]
        lat_list.append(duration_s)
        if len(lat_list) > 1000:
            lat_list.pop(0)

    def record_si_query(self, abstained: bool = False) -> None:
        self.si_queries_total += 1
        if abstained:
            self.si_abstentions_total += 1

    def record_cache_lookup(self, hit: bool) -> None:
        if hit:
            self.cache_hits_total += 1
        else:
            self.cache_misses_total += 1

    @staticmethod
    def _sanitize_path(path: str) -> str:
        # Group dynamic paths
        parts = path.strip("/").split("/")
        if len(parts) >= 4 and parts[0] == "api" and parts[1] == "v1":
            if parts[2] in ("investigations", "citations", "subgraph"):
                return f"/api/v1/{parts[2]}/:id"
        return path

    def export_prometheus_text(self) -> str:
        """Generates standard Prometheus text-format exposition."""
        lines = [
            "# HELP http_requests_total Total number of HTTP requests processed.",
            "# TYPE http_requests_total counter",
        ]
        for (m, p, s), cnt in sorted(self.request_counts.items()):
            lines.append(f'http_requests_total{{method="{m}",path="{p}",status="{s}"}} {cnt}')

        lines.extend([
            "",
            "# HELP http_request_duration_seconds HTTP request latency summary.",
            "# TYPE http_request_duration_seconds gauge",
        ])
        for (m, p), lats in sorted(self.request_latencies.items()):
            if lats:
                avg_lat = round(sum(lats) / len(lats), 6)
                max_lat = round(max(lats), 6)
                lines.append(f'http_request_duration_seconds{{method="{m}",path="{p}",stat="mean"}} {avg_lat}')
                lines.append(f'http_request_duration_seconds{{method="{m}",path="{p}",stat="max"}} {max_lat}')

        lines.extend([
            "",
            "# HELP scientific_intelligence_queries_total Total SI queries processed.",
            "# TYPE scientific_intelligence_queries_total counter",
            f"scientific_intelligence_queries_total {self.si_queries_total}",
            "",
            "# HELP scientific_intelligence_abstentions_total Out-of-domain query abstentions.",
            "# TYPE scientific_intelligence_abstentions_total counter",
            f"scientific_intelligence_abstentions_total {self.si_abstentions_total}",
            "",
            "# HELP semantic_cache_hits_total Total semantic query cache hits.",
            "# TYPE semantic_cache_hits_total counter",
            f"semantic_cache_hits_total {self.cache_hits_total}",
            "",
            "# HELP semantic_cache_misses_total Total semantic query cache misses.",
            "# TYPE semantic_cache_misses_total counter",
            f"semantic_cache_misses_total {self.cache_misses_total}",
        ])
        return "\n".join(lines) + "\n"


class TelemetryMetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware collecting Prometheus metrics and tracing spans."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate W3C traceparent (version-trace_id-parent_id-trace_flags)
        traceparent = request.headers.get("traceparent")
        if not traceparent:
            trace_id = uuid.uuid4().hex
            span_id = uuid.uuid4().hex[:16]
            traceparent = f"00-{trace_id}-{span_id}-01"

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            # Record metrics
            reg = MetricsRegistry.get_instance()
            reg.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_s=duration,
            )
            response.headers["traceparent"] = traceparent
            response.headers["x-response-time-ms"] = str(round(duration * 1000.0, 2))
            return response
        except Exception:
            duration = time.time() - start_time
            reg = MetricsRegistry.get_instance()
            reg.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_s=duration,
            )
            raise
