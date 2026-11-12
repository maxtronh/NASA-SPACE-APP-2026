import pytest
from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient):
    """Verifies GET /health endpoint returns healthy status and database connection."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["pgvector_ready"] is True
    assert "version" in data


def test_api_v1_health_endpoint(client: TestClient):
    """Verifies GET /api/v1/health endpoint adheres to health contract."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["pgvector_ready"] is True
    assert "version" in data


def test_root_index_endpoint(client: TestClient):
    """Verifies GET / index endpoint returns operational telemetry."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "Flame in Freefall" in data["name"]
    assert data["api_v1"] == "/api/v1"
