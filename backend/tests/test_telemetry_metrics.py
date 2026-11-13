"""Unit and API integration tests for OpenTelemetry Tracing and Prometheus Metrics."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.app.core.telemetry_metrics import MetricsRegistry
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_metrics_registry_record_and_export():
    reg = MetricsRegistry.get_instance()
    reg.record_request("GET", "/api/v1/investigations", 200, 0.042)
    reg.record_si_query(abstained=False)
    reg.record_si_query(abstained=True)
    reg.record_cache_lookup(hit=True)

    text = reg.export_prometheus_text()
    assert "# HELP http_requests_total" in text
    assert 'http_requests_total{method="GET",path="/api/v1/investigations",status="200"}' in text
    assert "scientific_intelligence_queries_total" in text
    assert "scientific_intelligence_abstentions_total" in text
    assert "semantic_cache_hits_total" in text


def test_api_w3c_traceparent_header_injection(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "traceparent" in response.headers
    traceparent = response.headers["traceparent"]
    assert traceparent.startswith("00-")
    assert len(traceparent.split("-")) == 4
    assert "x-response-time-ms" in response.headers


def test_api_prometheus_metrics_endpoint(client):
    # Perform a request first to generate telemetry
    client.get("/health")

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "# HELP http_requests_total" in body
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
