import pytest
from fastapi.testclient import TestClient


def test_compare_two_investigations(client: TestClient):
    """Verifies comparative grid generation for two valid investigations."""
    payload = {
        "investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]
    }
    res = client.post("/api/v1/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "comparison_grid" in data
    assert "equivalence_assessment" in data

    grid = data["comparison_grid"]
    assert "flex-2-heptane-droplet" in grid
    assert "acme-cld-flame" in grid
    assert grid["flex-2-heptane-droplet"]["fuel"] == "n-Heptane"
    assert grid["acme-cld-flame"]["fuel"] == "Methane (CH4)"


def test_compare_gravity_non_equivalence(client: TestClient):
    """Verifies system warns that microgravity vs 1g terrestrial conditions are not equivalent."""
    payload = {
        "investigation_ids": ["acme-cld-flame", "acme-cld-ground-1g"]
    }
    res = client.post("/api/v1/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assessment = data["equivalence_assessment"]
    assert assessment["equivalent"] is False
    assert any("gravity" in r.lower() or "gravitational" in r.lower() for r in assessment["reasons"])


def test_compare_regime_non_equivalence(client: TestClient):
    """Verifies system detects droplet vs laminar diffusion regime mismatch."""
    payload = {
        "investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]
    }
    res = client.post("/api/v1/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assessment = data["equivalence_assessment"]
    assert assessment["equivalent"] is False
    assert any("regime" in r.lower() for r in assessment["reasons"])


def test_compare_fewer_than_two_ids_returns_422(client: TestClient):
    """Verifies comparison requires at least 2 IDs."""
    assert client.post("/api/v1/compare", json={"investigation_ids": []}).status_code == 422
    assert client.post("/api/v1/compare", json={"investigation_ids": ["flex-2-heptane-droplet"]}).status_code == 422


def test_compare_nonexistent_id_returns_404(client: TestClient):
    """Verifies comparison with a missing ID returns HTTP 404."""
    payload = {
        "investigation_ids": ["flex-2-heptane-droplet", "non-existent-experiment-id"]
    }
    res = client.post("/api/v1/compare", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
